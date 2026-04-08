import io
import json
import os
import re
import zipfile
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote_plus
from xml.sax.saxutils import escape as xml_escape

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from openai import OpenAI
from sqlalchemy import Float as SAFloat
from sqlalchemy import cast, func
from sqlalchemy.orm import Session

from db import SessionLocal
from models import (
    DEFAULT_PERMISSIONS,
    Department,
    DepartmentView,
    DepartmentPolicy,
    Indicator,
    IndicatorText,
    IndicatorValue,
    Permission,
)
router = APIRouter()
templates = Jinja2Templates(directory="templates")

api_key = os.getenv("OPENAI_API_KEY")
query_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
client = OpenAI(api_key=api_key) if api_key else None

DEFAULT_DEPARTMENTS = [
    {
        "code": "employment",
        "name": "Employment",
        "description": "Labour market indicators, jobs, unemployment, participation, and related people-focused data.",
        "data_context": "Use this space for labour market, employment, unemployment, wages, participation, and workforce trends.",
    },
    {
        "code": "national-accounts",
        "name": "National Accounts",
        "description": "GDP, growth, production, expenditure, and macroeconomic accounting views.",
        "data_context": "Use this space for GDP, growth, accounts, output, inflation-linked context, and macro trends.",
    },
    {
        "code": "industry",
        "name": "Industry",
        "description": "Industrial production, value added, manufacturing, and sector performance.",
        "data_context": "Use this space for industrial performance, manufacturing, output, firm activity, and sectoral output.",
    },
    {
        "code": "mining",
        "name": "Mining",
        "description": "Mining activity, extractive sector performance, resources, and related statistics.",
        "data_context": "Use this space for mining, extractives, mineral output, production, and sector monitoring.",
    },
    {
        "code": "innovation",
        "name": "Innovation",
        "description": "R&D, patents, technology adoption, productivity, and innovation ecosystem views.",
        "data_context": "Use this space for innovation, R&D, productivity, patents, technology, and digital transformation.",
    },
]

DEFAULT_OUTPUT_COLUMNS = [
    "indicator_id",
    "indicator_name",
    "year",
    "region",
    "province",
    "gender",
    "value",
    "unit",
    "tracking_status",
    "tracking_message",
]

ALLOWED_OUTPUT_COLUMNS = {
    "indicator_id",
    "indicator_name",
    "year",
    "region",
    "province",
    "gender",
    "value",
    "unit",
    "tracking_status",
    "tracking_message",
    "status",
    "type",
    "priority",
    "dimension",
    "sector",
    "owner",
    "source",
    "record_count",
    "average_value",
}

ALLOWED_FILTER_KEYS = {
    "year_from",
    "year_to",
    "region",
    "province",
    "gender",
    "tracking_status",
    "status",
    "type",
    "priority",
    "sector",
    "dimension",
}

DEFAULT_POLICIES = {
    "employment": {
        "max_views": 12,
        "max_indicators_per_view": 3,
        "max_group_by_fields": 2,
        "max_filters_per_view": 4,
        "max_rows": 500,
        "allowed_view_types": ["trend", "comparison", "summary"],
        "allowed_filters": ["year_from", "year_to", "region", "province", "gender", "tracking_status", "status", "type", "priority", "sector", "dimension"],
        "allowed_dimensions": ["year", "region", "province", "gender", "sector", "dimension"],
        "allowed_output_columns": DEFAULT_OUTPUT_COLUMNS,
        "notes": "Focus on labour market indicators and time-based comparisons.",
    },
    "national-accounts": {
        "max_views": 10,
        "max_indicators_per_view": 4,
        "max_group_by_fields": 2,
        "max_filters_per_view": 4,
        "max_rows": 500,
        "allowed_view_types": ["trend", "comparison", "summary"],
        "allowed_filters": ["year_from", "year_to", "region", "province", "status", "type", "priority", "sector", "dimension"],
        "allowed_dimensions": ["year", "region", "sector", "dimension"],
        "allowed_output_columns": DEFAULT_OUTPUT_COLUMNS,
        "notes": "Use for national accounts, GDP, production, and macro series.",
    },
    "industry": {
        "max_views": 10,
        "max_indicators_per_view": 4,
        "max_group_by_fields": 2,
        "max_filters_per_view": 4,
        "max_rows": 500,
        "allowed_view_types": ["trend", "comparison", "summary", "coverage"],
        "allowed_filters": ["year_from", "year_to", "region", "province", "status", "type", "priority", "sector", "dimension"],
        "allowed_dimensions": ["year", "region", "province", "sector", "dimension"],
        "allowed_output_columns": DEFAULT_OUTPUT_COLUMNS,
        "notes": "Use for industrial performance and sector comparisons.",
    },
    "mining": {
        "max_views": 8,
        "max_indicators_per_view": 3,
        "max_group_by_fields": 2,
        "max_filters_per_view": 4,
        "max_rows": 500,
        "allowed_view_types": ["trend", "comparison", "summary"],
        "allowed_filters": ["year_from", "year_to", "region", "province", "status", "type", "priority", "sector", "dimension"],
        "allowed_dimensions": ["year", "region", "province", "sector", "dimension"],
        "allowed_output_columns": DEFAULT_OUTPUT_COLUMNS,
        "notes": "Use for extractives and mining-sector monitoring.",
    },
    "innovation": {
        "max_views": 8,
        "max_indicators_per_view": 3,
        "max_group_by_fields": 2,
        "max_filters_per_view": 4,
        "max_rows": 500,
        "allowed_view_types": ["trend", "comparison", "summary", "coverage"],
        "allowed_filters": ["year_from", "year_to", "region", "province", "status", "type", "priority", "sector", "dimension"],
        "allowed_dimensions": ["year", "region", "sector", "dimension"],
        "allowed_output_columns": DEFAULT_OUTPUT_COLUMNS,
        "notes": "Use for R&D, patents, productivity, and technology adoption.",
    },
}


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _slugify(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "-", (value or "").strip().lower()).strip("-")
    return value or "department"


def _ensure_unique_code(db: Session, base_code: str) -> str:
    code = base_code
    counter = 2
    while db.query(Department).filter(Department.code == code).first():
        code = f"{base_code}-{counter}"
        counter += 1
    return code


def ensure_reference_data(db: Session) -> None:
    existing_permissions = {perm.name for perm in db.query(Permission).all()}
    for perm in DEFAULT_PERMISSIONS:
        if perm["name"] not in existing_permissions:
            db.add(Permission(name=perm["name"], description=perm["description"]))

    if db.query(Department).count() == 0:
        for dept in DEFAULT_DEPARTMENTS:
            db.add(
                Department(
                    code=dept["code"],
                    name=dept["name"],
                    description=dept["description"],
                    data_context=dept["data_context"],
                )
            )

    db.commit()

    departments = db.query(Department).all()
    policy_codes = {dept.code for dept in departments if dept.policy}
    for department in departments:
        if department.code in policy_codes:
            continue
        defaults = DEFAULT_POLICIES.get(department.code, {})
        db.add(
            DepartmentPolicy(
                department_id=department.id,
                max_views=defaults.get("max_views", 10),
                max_indicators_per_view=defaults.get("max_indicators_per_view", 3),
                max_group_by_fields=defaults.get("max_group_by_fields", 2),
                max_filters_per_view=defaults.get("max_filters_per_view", 4),
                max_rows=defaults.get("max_rows", 500),
                allowed_view_types=json.dumps(defaults.get("allowed_view_types", ["trend", "comparison", "summary"])),
                allowed_filters=json.dumps(defaults.get("allowed_filters", list(ALLOWED_FILTER_KEYS))),
                allowed_dimensions=json.dumps(defaults.get("allowed_dimensions", ["year", "region"])),
                allowed_output_columns=json.dumps(defaults.get("allowed_output_columns", DEFAULT_OUTPUT_COLUMNS)),
                notes=defaults.get("notes"),
            )
        )

    db.commit()


def _indicator_catalog(db: Session) -> List[Dict[str, str]]:
    rows = (
        db.query(Indicator, IndicatorText)
        .join(IndicatorText, IndicatorText.indicator_id == Indicator.id)
        .filter(IndicatorText.language == "en")
        .all()
    )
    catalog = []
    for indicator, text in rows:
        catalog.append(
            {
                "id": indicator.id,
                "name": text.name or indicator.name or indicator.id,
                "sector": text.sector or indicator.sector or "",
                "dimension": text.dimension or indicator.dimension or "",
                "status": indicator.status or "",
                "type": indicator.type or "",
                "priority": indicator.priority or "",
                "owner": indicator.owner or "",
            }
        )
    return catalog


def _tokenize(text: str) -> set[str]:
    return {token for token in re.split(r"[^a-zA-Z0-9]+", (text or "").lower()) if token}


def _score_indicator(request_text: str, department_context: str, indicator: Dict[str, str]) -> int:
    query_tokens = _tokenize(request_text) | _tokenize(department_context)
    if not query_tokens:
        return 0

    indicator_text = " ".join(
        [
            indicator.get("id", ""),
            indicator.get("name", ""),
            indicator.get("sector", ""),
            indicator.get("dimension", ""),
            indicator.get("owner", ""),
        ]
    )
    indicator_tokens = _tokenize(indicator_text)
    return len(query_tokens & indicator_tokens)


def _fallback_spec(
    department: Department,
    request_text: str,
    view_name: str,
    catalog: List[Dict[str, str]],
    latest_year: Optional[int],
    policy: DepartmentPolicy,
) -> Dict:
    ranked = sorted(
        catalog,
        key=lambda indicator: _score_indicator(request_text, department.data_context or department.description or "", indicator),
        reverse=True,
    )
    chosen_ids = list(dict.fromkeys(item["id"] for item in ranked[:3] if item))
    if not chosen_ids and catalog:
        chosen_ids = [catalog[0]["id"]]

    year_from = latest_year - 4 if latest_year else None
    spec = {
        "view_name": view_name,
        "summary": request_text.strip() or department.description or department.name,
        "indicator_ids": chosen_ids,
        "filters": {
            "year_from": year_from,
            "year_to": latest_year,
        },
        "group_by": [],
        "output_columns": DEFAULT_OUTPUT_COLUMNS,
        "limit": policy.max_rows,
        "sort_by": [{"field": "year", "direction": "desc"}],
        "query_type": "raw",
        "generation_mode": "fallback",
    }
    return spec


def _extract_json_object(text: str) -> Dict:
    if not text:
        raise ValueError("Empty AI response")

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.S)
        if not match:
            raise
        return json.loads(match.group(0))


def _sanitize_spec(raw_spec: Dict, catalog: List[Dict[str, str]]) -> Dict:
    allowed_ids = {item["id"] for item in catalog}
    indicator_ids = list(dict.fromkeys(iid for iid in raw_spec.get("indicator_ids", []) if iid in allowed_ids))

    filters = raw_spec.get("filters") or {}
    sanitized_filters = {key: filters.get(key) for key in ALLOWED_FILTER_KEYS if filters.get(key) not in ("", None)}

    output_columns = [
        column for column in (raw_spec.get("output_columns") or DEFAULT_OUTPUT_COLUMNS)
        if column in ALLOWED_OUTPUT_COLUMNS
    ]
    if not output_columns:
        output_columns = DEFAULT_OUTPUT_COLUMNS

    group_by = [
        column for column in (raw_spec.get("group_by") or [])
        if column in ALLOWED_OUTPUT_COLUMNS
    ]

    sort_by = []
    for item in raw_spec.get("sort_by", []):
        field = item.get("field")
        direction = (item.get("direction") or "asc").lower()
        if field in ALLOWED_OUTPUT_COLUMNS and direction in {"asc", "desc"}:
            sort_by.append({"field": field, "direction": direction})

    spec = {
        "view_name": (raw_spec.get("view_name") or "").strip(),
        "summary": (raw_spec.get("summary") or "").strip(),
        "indicator_ids": indicator_ids,
        "filters": sanitized_filters,
        "group_by": group_by,
        "output_columns": output_columns,
        "limit": int(raw_spec.get("limit") or 500),
        "sort_by": sort_by or [{"field": "year", "direction": "desc"}],
        "query_type": raw_spec.get("query_type") or ("aggregated" if group_by else "raw"),
        "generation_mode": raw_spec.get("generation_mode") or "ai",
    }
    return spec


def _generate_spec_with_ai(
    department: Department,
    view_name: str,
    request_text: str,
    catalog: List[Dict[str, str]],
    latest_year: Optional[int],
    policy: DepartmentPolicy,
) -> Dict:
    if not client:
        return _fallback_spec(department, request_text, view_name, catalog, latest_year, policy)

    indicator_catalog = "\n".join(
        f"- {item['id']}: {item['name']} | sector={item['sector']} | dimension={item['dimension']} | status={item['status']} | type={item['type']} | priority={item['priority']}"
        for item in catalog
    )

    year_hint = f"The latest available year in the dataset is {latest_year}." if latest_year else "No year metadata is available."
    prompt = f"""
You convert a business request into a SAFE JSON query specification for a statistics dashboard.
Return ONLY valid JSON. Do not wrap it in markdown.

Department:
- name: {department.name}
- description: {department.description or ""}
- data_context: {department.data_context or ""}

User request:
{request_text}

Default view name suggestion:
{view_name}

Available indicators:
{indicator_catalog}

{year_hint}

{policy_prompt_block(policy)}

Rules:
- Only use indicator_ids that appear in the available indicators list.
- Prefer the smallest set of indicators that satisfies the request.
- If the request asks for trends, use group_by with year and any requested geographic dimensions.
- If the request asks for a summary, you can set query_type to aggregated and use group_by.
- If you cannot infer a filter, omit it.
- Include a short summary of what the view does.
- Never exceed the policy limits.
- Use only allowed view types, filters, dimensions, and output columns.

JSON shape:
{{
  "view_name": "string",
  "summary": "string",
  "indicator_ids": ["IND001"],
  "filters": {{
    "year_from": 2020,
    "year_to": 2024,
    "region": "Nationwide",
    "province": null,
    "gender": null,
    "tracking_status": null,
    "status": null,
    "type": null,
    "priority": null,
    "sector": null,
    "dimension": null
  }},
  "group_by": ["year", "region"],
  "output_columns": ["indicator_id", "indicator_name", "year", "region", "value"],
  "limit": 500,
  "sort_by": [{{"field": "year", "direction": "desc"}}],
  "query_type": "raw or aggregated"
}}
""".strip()

    response = client.chat.completions.create(
        model=query_model,
        messages=[
            {
                "role": "system",
                "content": "You generate structured query specifications for a statistics application. Output JSON only.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0,
    )
    content = response.choices[0].message.content or "{}"
    raw_spec = _extract_json_object(content)
    raw_spec.setdefault("generation_mode", "ai")
    raw_spec.setdefault("view_name", view_name)
    raw_spec.setdefault("summary", request_text.strip())
    raw_spec["limit"] = min(int(raw_spec.get("limit") or policy.max_rows), policy.max_rows)
    return _sanitize_spec(raw_spec, catalog)


def _latest_year(db: Session) -> Optional[int]:
    return db.query(func.max(IndicatorValue.year)).scalar()


def _parse_json_list(value: Optional[str], fallback: List[str]) -> List[str]:
    try:
        if not value:
            return list(fallback)
        parsed = json.loads(value)
        if isinstance(parsed, list):
            return [str(item) for item in parsed if str(item).strip()]
    except Exception:
        pass
    return list(fallback)


def get_department_policy(db: Session, department_id: int) -> DepartmentPolicy:
    policy = db.query(DepartmentPolicy).filter(DepartmentPolicy.department_id == department_id).first()
    if policy:
        return policy

    department = db.query(Department).filter(Department.id == department_id).first()
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")

    defaults = DEFAULT_POLICIES.get(department.code, {})
    policy = DepartmentPolicy(
        department_id=department.id,
        max_views=defaults.get("max_views", 10),
        max_indicators_per_view=defaults.get("max_indicators_per_view", 3),
        max_group_by_fields=defaults.get("max_group_by_fields", 2),
        max_filters_per_view=defaults.get("max_filters_per_view", 4),
        max_rows=defaults.get("max_rows", 500),
        allowed_view_types=json.dumps(defaults.get("allowed_view_types", ["trend", "comparison", "summary"])),
        allowed_filters=json.dumps(defaults.get("allowed_filters", list(ALLOWED_FILTER_KEYS))),
        allowed_dimensions=json.dumps(defaults.get("allowed_dimensions", ["year", "region"])),
        allowed_output_columns=json.dumps(defaults.get("allowed_output_columns", DEFAULT_OUTPUT_COLUMNS)),
        notes=defaults.get("notes"),
    )
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return policy


def policy_view_types(policy: DepartmentPolicy) -> List[str]:
    return _parse_json_list(policy.allowed_view_types, ["trend", "comparison", "summary"])


def policy_filters(policy: DepartmentPolicy) -> List[str]:
    return _parse_json_list(policy.allowed_filters, list(ALLOWED_FILTER_KEYS))


def policy_dimensions(policy: DepartmentPolicy) -> List[str]:
    return _parse_json_list(policy.allowed_dimensions, ["year", "region"])


def policy_output_columns(policy: DepartmentPolicy) -> List[str]:
    return _parse_json_list(policy.allowed_output_columns, DEFAULT_OUTPUT_COLUMNS)


def _allowed_view_type_from_spec(spec: Dict) -> str:
    group_by = spec.get("group_by") or []
    filters = spec.get("filters") or {}
    indicator_ids = spec.get("indicator_ids") or []
    if len(group_by) > 1:
        return "comparison"
    if len(indicator_ids) > 1:
        return "comparison"
    if "year_from" in filters or "year_to" in filters:
        return "trend"
    if len(group_by) == 1:
        return "coverage"
    return "summary"


def validate_view_spec(policy: DepartmentPolicy, spec: Dict) -> List[str]:
    errors = []
    policy_view_types_set = set(policy_view_types(policy))
    policy_filters_set = set(policy_filters(policy))
    policy_dimensions_set = set(policy_dimensions(policy))
    policy_output_columns_set = set(policy_output_columns(policy))

    requested_type = _allowed_view_type_from_spec(spec)
    if requested_type not in policy_view_types_set:
        errors.append(f"View type '{requested_type}' is not allowed for this department.")

    indicator_ids = spec.get("indicator_ids") or []
    if len(indicator_ids) > policy.max_indicators_per_view:
        errors.append(
            f"This department allows at most {policy.max_indicators_per_view} indicators per view."
        )

    group_by = spec.get("group_by") or []
    if len(group_by) > policy.max_group_by_fields:
        errors.append(f"This department allows at most {policy.max_group_by_fields} grouping fields per view.")
    for field in group_by:
        if field not in policy_dimensions_set:
            errors.append(f"Grouping field '{field}' is not allowed.")

    filters = spec.get("filters") or {}
    if len([k for k, v in filters.items() if v not in (None, "")]) > policy.max_filters_per_view:
        errors.append(f"This department allows at most {policy.max_filters_per_view} filters per view.")
    for key in filters.keys():
        if key not in policy_filters_set:
            errors.append(f"Filter '{key}' is not allowed.")

    output_columns = spec.get("output_columns") or []
    for column in output_columns:
        if column not in policy_output_columns_set:
            errors.append(f"Output column '{column}' is not allowed.")

    if spec.get("limit") and int(spec["limit"]) > policy.max_rows:
        errors.append(f"This department allows at most {policy.max_rows} rows per preview/export.")

    return errors


def policy_summary(policy: DepartmentPolicy) -> Dict[str, object]:
    return {
        "max_views": policy.max_views,
        "max_indicators_per_view": policy.max_indicators_per_view,
        "max_group_by_fields": policy.max_group_by_fields,
        "max_filters_per_view": policy.max_filters_per_view,
        "max_rows": policy.max_rows,
        "allowed_view_types": policy_view_types(policy),
        "allowed_filters": policy_filters(policy),
        "allowed_dimensions": policy_dimensions(policy),
        "allowed_output_columns": policy_output_columns(policy),
        "notes": policy.notes or "",
    }


def policy_prompt_block(policy: DepartmentPolicy) -> str:
    return (
        f"Policy limits:\n"
        f"- max_views: {policy.max_views}\n"
        f"- max_indicators_per_view: {policy.max_indicators_per_view}\n"
        f"- max_group_by_fields: {policy.max_group_by_fields}\n"
        f"- max_filters_per_view: {policy.max_filters_per_view}\n"
        f"- max_rows: {policy.max_rows}\n"
        f"- allowed_view_types: {', '.join(policy_view_types(policy))}\n"
        f"- allowed_filters: {', '.join(policy_filters(policy))}\n"
        f"- allowed_dimensions: {', '.join(policy_dimensions(policy))}\n"
        f"- allowed_output_columns: {', '.join(policy_output_columns(policy))}\n"
        f"- notes: {policy.notes or 'None'}"
    )


def _csv_to_json_list(value: Optional[str], fallback: List[str]) -> str:
    if value is None:
        return json.dumps(fallback)
    items = [item.strip() for item in value.split(",") if item.strip()]
    return json.dumps(items or fallback)


def _redirect_with_error(url: str, message: str) -> RedirectResponse:
    separator = "&" if "?" in url else "?"
    return RedirectResponse(f"{url}{separator}error={quote_plus(message)}", status_code=303)


def _column_map():
    return {
        "indicator_id": IndicatorValue.indicator_id,
        "indicator_name": IndicatorText.name,
        "year": IndicatorValue.year,
        "region": IndicatorValue.region,
        "province": IndicatorValue.province,
        "gender": IndicatorValue.gender,
        "value": IndicatorValue.value,
        "unit": IndicatorValue.unit,
        "tracking_status": IndicatorValue.tracking_status,
        "tracking_message": IndicatorValue.tracking_message,
        "status": Indicator.status,
        "type": Indicator.type,
        "priority": Indicator.priority,
        "dimension": IndicatorText.dimension,
        "sector": IndicatorText.sector,
        "owner": Indicator.owner,
        "source": IndicatorValue.source,
    }


def _sort_query(query, sort_by: List[Dict[str, str]], column_map: Dict[str, object]):
    order_clauses = []
    for item in sort_by:
        column = column_map.get(item["field"])
        if column is None:
            continue
        order_clauses.append(column.desc() if item["direction"] == "desc" else column.asc())
    if order_clauses:
        query = query.order_by(*order_clauses)
    return query


def execute_view_spec(db: Session, spec: Dict) -> Tuple[List[Dict], List[str]]:
    column_map = _column_map()
    output_columns = spec.get("output_columns") or DEFAULT_OUTPUT_COLUMNS
    group_by = spec.get("group_by") or []

    selected_columns = []
    result_columns = []
    if group_by:
        for key in group_by:
            if key in column_map:
                selected_columns.append(column_map[key].label(key))
                result_columns.append(key)
        if "average_value" in output_columns or "value" in output_columns or not output_columns:
            selected_columns.append(func.avg(cast(IndicatorValue.value, SAFloat)).label("average_value"))
            result_columns.append("average_value")
        if "record_count" in output_columns:
            selected_columns.append(func.count(IndicatorValue.record_id).label("record_count"))
            result_columns.append("record_count")
        if not selected_columns:
            selected_columns = [column_map.get("year", IndicatorValue.year).label("year")]
            result_columns = ["year"]
    else:
        for column_name in output_columns:
            column = column_map.get(column_name)
            if column is not None:
                selected_columns.append(column.label(column_name))
                result_columns.append(column_name)
        if not selected_columns:
            for column_name in DEFAULT_OUTPUT_COLUMNS:
                column = column_map.get(column_name)
                if column is not None:
                    selected_columns.append(column.label(column_name))
                    result_columns.append(column_name)

    base_query = (
        db.query(*selected_columns)
        .select_from(IndicatorValue)
        .join(Indicator, Indicator.id == IndicatorValue.indicator_id)
        .join(IndicatorText, IndicatorText.indicator_id == Indicator.id)
        .filter(IndicatorText.language == "en")
    )

    indicator_ids = spec.get("indicator_ids") or []
    if indicator_ids:
        base_query = base_query.filter(IndicatorValue.indicator_id.in_(indicator_ids))

    filters = spec.get("filters") or {}
    if filters.get("year_from") is not None:
        base_query = base_query.filter(IndicatorValue.year >= int(filters["year_from"]))
    if filters.get("year_to") is not None:
        base_query = base_query.filter(IndicatorValue.year <= int(filters["year_to"]))
    if filters.get("region"):
        base_query = base_query.filter(IndicatorValue.region == filters["region"])
    if filters.get("province"):
        base_query = base_query.filter(IndicatorValue.province == filters["province"])
    if filters.get("gender"):
        base_query = base_query.filter(IndicatorValue.gender == filters["gender"])
    if filters.get("tracking_status"):
        base_query = base_query.filter(IndicatorValue.tracking_status == filters["tracking_status"])
    if filters.get("status"):
        base_query = base_query.filter(Indicator.status == filters["status"])
    if filters.get("type"):
        base_query = base_query.filter(Indicator.type == filters["type"])
    if filters.get("priority"):
        base_query = base_query.filter(Indicator.priority == filters["priority"])
    if filters.get("sector"):
        base_query = base_query.filter(IndicatorText.sector == filters["sector"])
    if filters.get("dimension"):
        base_query = base_query.filter(IndicatorText.dimension == filters["dimension"])

    if group_by:
        base_query = base_query.group_by(*[column_map[key] for key in group_by if key in column_map])

    base_query = _sort_query(base_query, spec.get("sort_by") or [], column_map)

    limit = int(spec.get("limit") or 500)
    if limit > 0:
        base_query = base_query.limit(limit)

    rows = base_query.all()
    columns = result_columns
    result = [dict(zip(columns, row)) for row in rows]
    return result, columns


def _build_preview_sheet(rows: List[Dict], columns: List[str]) -> bytes:
    def column_letter(index: int) -> str:
        result = ""
        while index >= 0:
            result = chr(index % 26 + ord("A")) + result
            index = index // 26 - 1
        return result

    def cell(value, ref: str) -> str:
        if value is None:
            return ""
        if isinstance(value, bool):
            value = "true" if value else "false"
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return f'<c r="{ref}"><v>{value}</v></c>'
        text = xml_escape(str(value))
        return f'<c r="{ref}" t="inlineStr"><is><t>{text}</t></is></c>'

    sheet_rows = []
    header_cells = []
    for index, column in enumerate(columns):
        ref = f"{column_letter(index)}1"
        header_cells.append(
            f'<c r="{ref}" t="inlineStr"><is><t>{xml_escape(column.replace("_", " ").title())}</t></is></c>'
        )
    sheet_rows.append(f'<row r="1">{"".join(header_cells)}</row>')

    for row_index, row in enumerate(rows, start=2):
        cells = []
        for column_index, column in enumerate(columns):
            ref = f"{column_letter(column_index)}{row_index}"
            cells.append(cell(row.get(column), ref))
        sheet_rows.append(f'<row r="{row_index}">{"".join(cells)}</row>')

    sheet_data = "".join(sheet_rows)
    worksheet = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
           xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheetData>{sheet_data}</sheetData>
</worksheet>"""

    workbook = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
          xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
    <sheet name="View" sheetId="1" r:id="rId1"/>
  </sheets>
</workbook>"""

    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
</Types>"""

    root_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>"""

    workbook_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
</Relationships>"""

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", root_rels)
        archive.writestr("xl/workbook.xml", workbook)
        archive.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
        archive.writestr("xl/worksheets/sheet1.xml", worksheet)

    return buffer.getvalue()


@router.get("/departments", response_class=HTMLResponse)
def departments_page(
    request: Request,
    department_id: Optional[int] = Query(default=None),
    view_id: Optional[int] = Query(default=None),
    error: Optional[str] = Query(default=None),
    message: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    ensure_reference_data(db)

    departments = db.query(Department).order_by(Department.name.asc()).all()
    selected_department = None
    if department_id is not None:
        selected_department = db.query(Department).filter(Department.id == department_id).first()
    if selected_department is None and departments:
        selected_department = departments[0]

    selected_view = None
    if view_id is not None:
        selected_view = db.query(DepartmentView).filter(DepartmentView.id == view_id).first()

    if selected_view is None and selected_department and selected_department.views:
        selected_view = sorted(selected_department.views, key=lambda item: item.updated_at or item.created_at, reverse=True)[0]

    department_views = []
    view_rows: List[Dict] = []
    view_columns: List[str] = []
    view_spec = {}
    if selected_department is not None:
        department_views = (
            db.query(DepartmentView)
            .filter(DepartmentView.department_id == selected_department.id)
            .order_by(DepartmentView.updated_at.desc(), DepartmentView.created_at.desc())
            .all()
        )
    if selected_view is not None:
        try:
            view_spec = json.loads(selected_view.query_spec)
        except Exception:
            view_spec = {}
        view_rows, view_columns = execute_view_spec(db, view_spec)

    latest_year = _latest_year(db)
    indicator_catalog = _indicator_catalog(db)
    selected_policy = get_department_policy(db, selected_department.id) if selected_department else None

    preview_row_count = len(view_rows)
    return templates.TemplateResponse(
        "departments.html",
        {
            "request": request,
            "departments": departments,
            "selected_department": selected_department,
            "department_views": department_views,
            "selected_view": selected_view,
            "selected_view_spec": view_spec,
            "selected_view_rows": view_rows,
            "selected_view_columns": view_columns,
            "preview_row_count": preview_row_count,
            "indicator_catalog": indicator_catalog,
            "latest_year": latest_year,
            "selected_policy": selected_policy,
            "policy_summary": policy_summary(selected_policy) if selected_policy else None,
            "error": error,
            "message": message,
        },
    )


@router.post("/departments")
def create_department(
    name: str = Form(...),
    code: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    data_context: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    ensure_reference_data(db)

    department_code = _slugify(code or name)
    department_code = _ensure_unique_code(db, department_code)
    department = Department(
        name=name.strip(),
        code=department_code,
        description=(description or "").strip() or None,
        data_context=(data_context or "").strip() or None,
    )
    db.add(department)
    db.commit()
    defaults = DEFAULT_POLICIES.get(department.code, {})
    db.add(
        DepartmentPolicy(
            department_id=department.id,
            max_views=defaults.get("max_views", 10),
            max_indicators_per_view=defaults.get("max_indicators_per_view", 3),
            max_group_by_fields=defaults.get("max_group_by_fields", 2),
            max_filters_per_view=defaults.get("max_filters_per_view", 4),
            max_rows=defaults.get("max_rows", 500),
            allowed_view_types=json.dumps(defaults.get("allowed_view_types", ["trend", "comparison", "summary"])),
            allowed_filters=json.dumps(defaults.get("allowed_filters", list(ALLOWED_FILTER_KEYS))),
            allowed_dimensions=json.dumps(defaults.get("allowed_dimensions", ["year", "region"])),
            allowed_output_columns=json.dumps(defaults.get("allowed_output_columns", DEFAULT_OUTPUT_COLUMNS)),
            notes=defaults.get("notes"),
        )
    )
    db.commit()
    return RedirectResponse(url="/indicator-library/departments?department_id={}".format(department.id), status_code=303)


@router.post("/departments/{department_id}/policy")
def update_department_policy(
    department_id: int,
    max_views: int = Form(...),
    max_indicators_per_view: int = Form(...),
    max_group_by_fields: int = Form(...),
    max_filters_per_view: int = Form(...),
    max_rows: int = Form(...),
    allowed_view_types: str = Form(...),
    allowed_filters: str = Form(...),
    allowed_dimensions: str = Form(...),
    allowed_output_columns: str = Form(...),
    notes: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    ensure_reference_data(db)
    department = db.query(Department).filter(Department.id == department_id).first()
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")

    policy = get_department_policy(db, department_id)
    policy.max_views = max(1, max_views)
    policy.max_indicators_per_view = max(1, max_indicators_per_view)
    policy.max_group_by_fields = max(1, max_group_by_fields)
    policy.max_filters_per_view = max(1, max_filters_per_view)
    policy.max_rows = max(1, max_rows)
    policy.allowed_view_types = _csv_to_json_list(allowed_view_types, ["trend", "comparison", "summary"])
    policy.allowed_filters = _csv_to_json_list(allowed_filters, list(ALLOWED_FILTER_KEYS))
    policy.allowed_dimensions = _csv_to_json_list(allowed_dimensions, ["year", "region"])
    policy.allowed_output_columns = _csv_to_json_list(allowed_output_columns, DEFAULT_OUTPUT_COLUMNS)
    policy.notes = (notes or "").strip() or None
    db.commit()

    return RedirectResponse(
        url=f"/indicator-library/departments?department_id={department.id}&message={quote_plus('Policy updated successfully.')}",
        status_code=303,
    )


@router.post("/departments/{department_id}/views")
def create_department_view(
    department_id: int,
    view_name: Optional[str] = Form(None),
    request_text: str = Form(...),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    ensure_reference_data(db)
    department = db.query(Department).filter(Department.id == department_id).first()
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")
    policy = get_department_policy(db, department.id)

    current_views = db.query(DepartmentView).filter(DepartmentView.department_id == department.id).count()
    if current_views >= policy.max_views:
        return _redirect_with_error(
            f"/indicator-library/departments?department_id={department.id}",
            f"This department already reached its limit of {policy.max_views} views.",
        )

    catalog = _indicator_catalog(db)
    latest_year = _latest_year(db)
    generated_name = (view_name or "").strip() or request_text.strip()[:80] or f"{department.name} view"
    spec = _generate_spec_with_ai(department, generated_name, request_text, catalog, latest_year, policy)
    spec["view_name"] = spec.get("view_name") or generated_name
    spec["summary"] = spec.get("summary") or (description or request_text.strip())
    spec["limit"] = min(int(spec.get("limit") or policy.max_rows), policy.max_rows)

    errors = validate_view_spec(policy, spec)
    if errors:
        return _redirect_with_error(
            f"/indicator-library/departments?department_id={department.id}",
            " ".join(errors),
        )

    rows, _ = execute_view_spec(db, spec)
    view = DepartmentView(
        department_id=department.id,
        name=spec["view_name"],
        description=(description or spec.get("summary") or request_text).strip() or None,
        request_text=request_text.strip(),
        query_spec=json.dumps(spec, ensure_ascii=False, indent=2),
        query_status=spec.get("generation_mode", "ai"),
        last_result_count=len(rows),
        last_refreshed_at=datetime.utcnow(),
    )
    db.add(view)
    db.commit()

    return RedirectResponse(
        url=f"/indicator-library/departments?department_id={department.id}&view_id={view.id}",
        status_code=303,
    )


@router.post("/departments/views/{view_id}/refresh")
def refresh_department_view(
    view_id: int,
    request_text: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    ensure_reference_data(db)
    view = db.query(DepartmentView).filter(DepartmentView.id == view_id).first()
    if not view:
        raise HTTPException(status_code=404, detail="View not found")

    department = db.query(Department).filter(Department.id == view.department_id).first()
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")
    policy = get_department_policy(db, department.id)

    catalog = _indicator_catalog(db)
    latest_year = _latest_year(db)
    if not isinstance(request_text, str):
        request_text = None
    request_text = (request_text or view.request_text or view.description or view.name).strip()
    spec = _generate_spec_with_ai(department, view.name, request_text, catalog, latest_year, policy)
    spec["limit"] = min(int(spec.get("limit") or policy.max_rows), policy.max_rows)
    errors = validate_view_spec(policy, spec)
    if errors:
        return _redirect_with_error(
            f"/indicator-library/departments?department_id={department.id}&view_id={view.id}",
            " ".join(errors),
        )
    rows, _ = execute_view_spec(db, spec)

    view.request_text = request_text
    view.query_spec = json.dumps(spec, ensure_ascii=False, indent=2)
    view.query_status = spec.get("generation_mode", "ai")
    view.last_result_count = len(rows)
    view.last_refreshed_at = datetime.utcnow()
    db.commit()

    return RedirectResponse(
        url=f"/indicator-library/departments?department_id={department.id}&view_id={view.id}",
        status_code=303,
    )


@router.get("/departments/views/{view_id}/export.xlsx")
def export_department_view(view_id: int, db: Session = Depends(get_db)):
    ensure_reference_data(db)
    view = db.query(DepartmentView).filter(DepartmentView.id == view_id).first()
    if not view:
        raise HTTPException(status_code=404, detail="View not found")

    try:
        spec = json.loads(view.query_spec)
    except Exception:
        spec = {}
    rows, columns = execute_view_spec(db, spec)
    xlsx_bytes = _build_preview_sheet(rows, columns)
    filename = re.sub(r"[^a-zA-Z0-9_-]+", "_", view.name.strip().lower()) or f"view_{view.id}"
    headers = {"Content-Disposition": f'attachment; filename="{filename}.xlsx"'}
    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )

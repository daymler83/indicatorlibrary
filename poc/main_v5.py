import pandas as pd
from numpy import nan
import os
from datetime import datetime
from openai import OpenAI
import io
import math
from fastapi import FastAPI, Request, HTTPException, Depends, UploadFile, Form, File, Body
from pydantic import BaseModel
from typing import Optional, List
from db import SessionLocal
from models import Indicator, IndicatorValue, IndicatorHistory, ValueHistory
from sqlalchemy.orm import Session
from sqlalchemy import text, func, distinct, literal
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from typing import Dict, List, Tuple
import time
from collections import deque



app = FastAPI()

api_times = deque(maxlen=100)

@app.middleware("http")
async def measure_api_time(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start
    api_times.append(duration)
    return response


templates = Jinja2Templates(directory="templates")

class IndicatorCreate(BaseModel):
    id: str
    name: str
    owner: str
    status: str
    version: float
    dimension: Optional[str] = None
    sector: Optional[str] = None
    type: Optional[str]="operational"
    priority: Optional[str]="medium"

class IndicatorValueCreate(BaseModel):
    indicator_id: str
    year: int
    region: Optional[str] = None
    province: Optional[str] = None
    gender: Optional[str] = None
    value: Optional[str] = None
    tracking_status: Optional[str] = None
    tracking_message: Optional[str] = None

class GPTQuery(BaseModel):
    question: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/indicators/")
def create_indicator(indicator_data: IndicatorCreate, db: Session = Depends(get_db)):
    existing = db.query(Indicator).filter(Indicator.id == indicator_data.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Indicator ID already exists.")
    new_indicator = Indicator(**indicator_data.dict())
    db.add(new_indicator)

    history = IndicatorHistory(
        indicator_id=new_indicator.id,
        name=new_indicator.name,
        owner=new_indicator.owner,
        status=new_indicator.status,
        version=new_indicator.version,
        dimension=new_indicator.dimension,
        sector=new_indicator.sector,
        type=new_indicator.type,
        priority=new_indicator.priority,
        definition=getattr(new_indicator, "definition", None),
        changed_by="system_create"
    )

    db.add(history)
    db.commit()
    db.refresh(new_indicator)
    return {"message": "Indicator created", "indicator": new_indicator.id}

@app.get("/indicators/{indicator_id}")
def get_indicator(indicator_id: str, db: Session = Depends(get_db)):
    indicator = db.query(Indicator).filter(Indicator.id == indicator_id).first()
    if not indicator:
        raise HTTPException(status_code=404, detail="Indicator not found.")
    return indicator

@app.put("/indicators/{indicator_id}")
def update_indicator(indicator_id: str, data: IndicatorCreate, db: Session = Depends(get_db)):
    indicator = db.query(Indicator).filter(Indicator.id == indicator_id).first()
    if not indicator:
        raise HTTPException(status_code=404, detail="Indicator not found.")
    
    for key, value in data.dict().items():
        setattr(indicator, key, value)

    history = IndicatorHistory(
        indicator_id=indicator.id,
        name=indicator.name,
        owner=indicator.owner,
        status=indicator.status,
        version=indicator.version,
        dimension=indicator.dimension,
        sector=indicator.sector,
        definition=getattr(indicator, "definition", None),
        changed_by="system_update"
    )
    db.add(history)

    db.commit()
    db.refresh(indicator)
    return {"message": "Indicator updated", "indicator": indicator.id}

@app.get("/indicators/{indicator_id}/history")
def get_indicator_history(indicator_id: str, db: Session = Depends(get_db)):
    return db.query(IndicatorHistory)\
             .filter_by(indicator_id=indicator_id)\
             .order_by(IndicatorHistory.changed_at.desc())\
             .all()

@app.post("/values/")
def create_indicator_value(value_data: IndicatorValueCreate, db: Session = Depends(get_db)):
    indicator = db.query(Indicator).filter(Indicator.id == value_data.indicator_id).first()
    if not indicator:
        raise HTTPException(status_code=404, detail="Indicator not found.")
    new_value = IndicatorValue(**value_data.dict())
    db.add(new_value)
    db.commit()
    db.refresh(new_value)
    return {"message": "Indicator value created", "record_id": new_value.record_id}

@app.get("/values/{indicator_id}")
def get_values_by_indicator(indicator_id: str, db: Session = Depends(get_db)):
    values = db.query(IndicatorValue).filter(IndicatorValue.indicator_id == indicator_id).all()
    return values

@app.get("/")
def home():
    return RedirectResponse("/dashboard")

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(
    request: Request, 
    db: Session = Depends(get_db),
    sector: Optional[str] = None,
    dimension: Optional[str] = None,
    status: Optional[str] = None,
    type: Optional[str] = None,
    priority: Optional[str] = None,
    search: Optional[str] = None
):
    # Start with base query
    query = db.query(Indicator)
    
    # Apply filters if they exist
    if search:
        query = query.filter(Indicator.name.ilike(f"%{search}%"))
    if sector:
        query = query.filter(Indicator.sector == sector)
    if dimension:
        query = query.filter(Indicator.dimension == dimension)
    if status:
        query = query.filter(Indicator.status == status)
    if type:
        query = query.filter(Indicator.type == type)
    if priority:
        query = query.filter(Indicator.priority == priority)

    indicators = query.all()
    
    # Get all indicator values for tracking dashboard
    indicator_values = db.query(IndicatorValue).all()
    
    # Get unique values for filter dropdowns from ALL indicators (not filtered)
    all_indicators = db.query(Indicator).all()
    
    sectors = list({ind.sector for ind in all_indicators if ind.sector})
    statuses = list({ind.status for ind in all_indicators})
    dimensions = list({ind.dimension for ind in all_indicators if ind.dimension})
    types = list({ind.type for ind in all_indicators if ind.type})
    priorities = list({ind.priority for ind in all_indicators if ind.priority})

    
    # Group by dimension for accordion (using filtered indicators)
    dimension_groups = {}
    for ind in indicators:
        key = ind.dimension or "Uncategorized"
        dimension_groups.setdefault(key, []).append(ind)

    # Group values by indicator for tracking
    tracking_by_indicator = {}
    for value in indicator_values:
        tracking_by_indicator.setdefault(value.indicator_id, []).append(value)

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "indicators": indicators,
        "indicator_values": indicator_values,
        "dimensions": dimension_groups,
        "tracking_by_indicator": tracking_by_indicator,
        "all_sectors": sectors,
        "all_statuses": statuses,
        "all_dimensions": dimensions,
        "all_types": types,
        "all_priorities": priorities,
        "selected_sector": sector,
        "selected_status": status,
        "selected_dimension": dimension,
        "selected_type": type,
        "selected_priority": priority,
        "search_query": search or ""
    })

@app.get("/upload", response_class=HTMLResponse)
def upload_form(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})

@app.post("/upload/")
async def upload_csv(
    request: Request,
    file_type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    contents = await file.read()
    df = pd.read_csv(io.StringIO(contents.decode()))

    if file_type == "indicators":
        for _, row in df.iterrows():
            if db.query(Indicator).filter_by(id=row["id"]).first():
                continue
            ind = Indicator(**row.to_dict())
            db.add(ind)

    elif file_type == "values":
        if "indicator_id" not in df.columns:
            raise HTTPException(status_code=400, detail="Missing 'indicator_id' column in values CSV.")

        df = df.where(pd.notnull(df), None)
        uploader = "csv_upload"

        def normalize_str(val):
            return None if val is None or str(val).lower() in ["nan", "none"] else str(val).strip()

        def safe_int(val):
            try:
                return int(val) if pd.notnull(val) else None
            except (ValueError, TypeError):
                return None

        for _, row in df.iterrows():
            if pd.isna(row['indicator_id']) or pd.isna(row['year']):
                continue

            row_data = row.where(pd.notnull(row), None).to_dict()
            row_data["imported_by"] = uploader

            indicator_id = normalize_str(row_data.get("indicator_id"))
            region = normalize_str(row_data.get("region"))
            province = normalize_str(row_data.get("province"))
            gender = normalize_str(row_data.get("gender"))
            year = safe_int(row_data.get("year"))

            existing = db.query(IndicatorValue).filter_by(
                indicator_id=indicator_id,
                year=year,
                region=region,
                province=province,
                gender=gender
            ).first()

            if existing:
                if str(existing.value) != str(row.get("value")):
                    db.execute(
                        text("""
                        INSERT INTO value_history (
                            indicator_id, year, region, province, gender, value,
                            tracking_status, tracking_message, changed_by, imported_by
                        )
                        VALUES (:indicator_id, :year, :region, :province, :gender, :value,
                                :tracking_status, :tracking_message, :changed_by, :imported_by)
                        """),
                        {
                            "indicator_id": existing.indicator_id,
                            "year": existing.year,
                            "region": existing.region,
                            "province": existing.province,
                            "gender": existing.gender,
                            "value": existing.value,
                            "tracking_status": existing.tracking_status,
                            "tracking_message": existing.tracking_message,
                            "changed_by": "csv_upload",
                            "imported_by": uploader
                        }
                    )
                    for key in row.keys():
                        if hasattr(existing, key):
                            setattr(existing, key, row[key])
                    existing.imported_by = uploader
            else:
                row_data["region"] = region
                row_data["province"] = province
                row_data["gender"] = gender
                row_data["year"] = year
                row_data["indicator_id"] = indicator_id
                val = IndicatorValue(**row_data)
                db.add(val)

    db.commit()
    return RedirectResponse("/", status_code=303)

@app.get("/tracking", response_class=HTMLResponse)
def tracking_dashboard(request: Request, db: Session = Depends(get_db)):
    values = db.query(IndicatorValue).filter(IndicatorValue.tracking_status != None).all()
    
    tracking_by_indicator = {}
    for value in values:
        tracking_by_indicator.setdefault(value.indicator_id, []).append(value)

    return templates.TemplateResponse("tracking.html", {
        "request": request,
        "tracking_by_indicator": tracking_by_indicator
    })

@app.get("/trends/{indicator_id}", response_class=HTMLResponse)
def show_trend(indicator_id: str, request: Request, db: Session = Depends(get_db)):
    indicator = db.query(Indicator).filter(Indicator.id == indicator_id).first()
    if not indicator:
        raise HTTPException(status_code=404, detail="Indicator not found")
    
    values = (
        db.query(IndicatorValue)
        .filter(IndicatorValue.indicator_id == indicator_id)
        .order_by(IndicatorValue.year)
        .all()
    )

    years = [v.year for v in values]
    data = [float(v.value) if v.value else None for v in values]

    return templates.TemplateResponse("trends.html", {
        "request": request,
        "indicator": indicator,
        "years": years,
        "data": data
    })

class IndicatorRequest(BaseModel):
    indicator_ids: List[str]

@app.post("/api/trends")
def get_trends(request: IndicatorRequest, db: Session = Depends(get_db)):
    result = []
    for ind_id in request.indicator_ids:
        indicator = db.query(Indicator).filter(Indicator.id == ind_id).first()
        if not indicator:
            continue
            
        values = db.query(IndicatorValue).filter(IndicatorValue.indicator_id == ind_id).order_by(IndicatorValue.year).all()
        data = []
        for v in values:
            try:
                val = float(v.value)
                if math.isfinite(val):
                    data.append({"year": v.year, "value": val})
            except (ValueError, TypeError):
                continue
                
        result.append({
            "label": indicator.name,
            "data": data,
            "sector": indicator.sector
        })
    return {"series": result}

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.post("/api/prioritize")
def prioritize_indicators(query: GPTQuery, db: Session = Depends(get_db)):
    indicators = db.query(Indicator).all()

    descriptions = [
        f"{ind.name}: {ind.dimension or ''} Dimension: {ind.dimension or ''}. Sector: {ind.sector or ''}. Owner: {ind.owner or ''}. Version: {ind.version}. Status: {ind.status}."
        for ind in indicators
    ]
    context = "\n".join(descriptions)

    prompt = (
        f"Based on the following indicator metadata, answer the question: '{query.question}'. "
        f"Return the most relevant indicators and a short reason for each.\n\n"
        f"{context}"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an assistant that prioritizes development indicators based on task-related metadata."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )

        answer = response.choices[0].message.content

        lines = answer.strip().split("\n")
        recommendations = []
        for line in lines:
            if line.strip():
                parts = line.lstrip("1234567890.- ").split(":", 1)
                if len(parts) == 2:
                    name, reason = parts
                    recommendations.append({"name": name.strip(), "reason": reason.strip()})
        return {"recommendations": recommendations or [{"name": "Result", "reason": answer}]}

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})
    
# Including a dashboard and on the left  side

@app.get("/overview", response_class=HTMLResponse)
def overview(request: Request, db: Session = Depends(get_db)):
    # Basic counts
    total_indicators = db.query(Indicator).count()
    total_values = db.query(IndicatorValue).count()
    
    # Get all distinct dimensions (excluding None)
    dimensions = [i.dimension for i in db.query(Indicator).all() if i.dimension]
    total_dimensions = len(set(dimensions))
    
    # Count indicators by dimension
    indicators_by_dimension = {}
    for i in db.query(Indicator).all():
        if i.dimension:
            indicators_by_dimension.setdefault(i.dimension, 0)
            indicators_by_dimension[i.dimension] += 1
    
    # Count database tables
    table_count = db.execute(text("SELECT count(*) FROM information_schema.tables WHERE table_schema='public'")).scalar()
    
    # Status distribution
    status_counts = db.query(
        Indicator.status,
        func.count(Indicator.id).label('count')
    ).group_by(Indicator.status).all()
    status_distribution = {status: count for status, count in status_counts}
    
    # Sector distribution
    sector_counts = db.query(
        Indicator.sector,
        func.count(Indicator.id).label('count')
    ).filter(Indicator.sector.isnot(None)).group_by(Indicator.sector).all()
    sector_distribution = {sector: count for sector, count in sector_counts}
    
    # Data completeness score
    indicators_with_values = db.query(
        func.count(distinct(IndicatorValue.indicator_id))
    ).scalar()
    data_completeness = round((indicators_with_values / total_indicators) * 100, 1) if total_indicators > 0 else 0
    
    # Average values per indicator
    avg_values_per_indicator = round(total_values / total_indicators, 1) if total_indicators > 0 else 0
    
    # Tracking status summary
    tracking_summary = (
        db.query(
        IndicatorValue.tracking_status,
        func.count(IndicatorValue.record_id).label('count')
    ).filter(IndicatorValue.tracking_status.isnot(None))
    .group_by(IndicatorValue.tracking_status).all()
    )
    tracking_statuses = {status: count for status, count in tracking_summary if status}
    
    # Recent activity - combine indicator changes and value updates
    recent_indicator_changes = (
        db.query(
        IndicatorHistory.indicator_id,
        IndicatorHistory.name,
        IndicatorHistory.changed_at,
        IndicatorHistory.changed_by,
        literal("indicator").label("change_type")
    ).order_by(IndicatorHistory.changed_at.desc()).limit(5).all()
    )

    recent_value_changes = db.query(
        ValueHistory.indicator_id,
        Indicator.name,
        ValueHistory.changed_at,
        ValueHistory.changed_by,
        literal("value").label("change_type")
    ).join(Indicator, Indicator.id == ValueHistory.indicator_id)\
     .order_by(ValueHistory.changed_at.desc()).limit(5).all()

    # Combine and sort all changes
    all_changes = recent_indicator_changes + recent_value_changes
    recent_changes = sorted(all_changes, key=lambda x: x.changed_at, reverse=True)[:5]

    # Format the changes for display
    formatted_changes = []
    for change in recent_changes:
        time_ago = (datetime.now() - change.changed_at).total_seconds()
        
        if time_ago < 60:
            time_str = "just now"
        elif time_ago < 3600:
            minutes = int(time_ago // 60)
            time_str = f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif time_ago < 86400:
            hours = int(time_ago // 3600)
            time_str = f"{hours} hour{'s' if hours != 1 else ''} ago"
        else:
            days = int(time_ago // 86400)
            time_str = f"{days} day{'s' if days != 1 else ''} ago"

        if change.change_type == "indicator":
            action = "Indicator updated"
            details = f"{change.name} was modified"
        else:
            action = "Data updated"
            details = f"New values for {change.name}"

        formatted_changes.append({
            "time": time_str,
            "action": action,
            "details": details,
            "changed_by": change.changed_by or "system"
        })
    
    # Value coverage by year
    year_coverage = db.query(
        IndicatorValue.year,
        func.count(distinct(IndicatorValue.indicator_id)).label('count')
    ).group_by(IndicatorValue.year).order_by(IndicatorValue.year).all()
    year_coverage = [(year, count) for year, count in year_coverage if year]
    
    # Indicator types distribution
    type_distribution = db.query(
        Indicator.type,
        func.count(Indicator.id).label('count')
    ).group_by(Indicator.type).all()
    type_distribution = {typ: count for typ, count in type_distribution if typ}
    
    # Priority distribution
    priority_distribution = db.query(
        Indicator.priority,
        func.count(Indicator.id).label('count')
    ).group_by(Indicator.priority).all()
    priority_distribution = {priority: count for priority, count in priority_distribution if priority}
    
    # Average update frequency
    update_freq_query = """
    SELECT AVG(days_between) as avg_days
    FROM (
        SELECT indicator_id, 
               EXTRACT(DAY FROM (MAX(imported_at) - MIN(imported_at)))/COUNT(*) as days_between
        FROM indicator_values
        GROUP BY indicator_id
        HAVING COUNT(*) > 1
    ) as freq
    """
    avg_update_freq = db.execute(text(update_freq_query)).scalar() or 0
    
    # Calculate latest year with data
    latest_year_result = db.query(func.max(IndicatorValue.year)).scalar()
    latest_year = latest_year_result if latest_year_result else datetime.now().year

    # === Real System Status Metrics ===

    # Estimate DB performance: based on total rows per table
    total_rows = total_indicators + total_values
    db_performance = round(min(100, (total_rows / (table_count * 1000)) * 100), 1) if table_count else 0


    # Actual API latency from rolling buffer
    avg_response_time = round(sum(api_times) / len(api_times) * 1000, 2) if api_times else 0  # in ms
    api_health = min(100, max(0, 100 - (avg_response_time - 100)))  # degrade above 100ms


    # Estimate storage capacity as a function of total values (simulate a 100k row warning threshold)

    storage_used = db.execute(text("""
        SELECT SUM(pg_total_relation_size(quote_ident(tablename))) as total
        FROM pg_tables WHERE schemaname = 'public'
    """)).scalar() or 0

    storage_capacity = round(min(100, (storage_used / (500 * 1024 * 1024)) * 100), 1)  # Assume 500MB = full

    def human_readable(bytes_val):
        for unit in ['B','KB','MB','GB','TB']:
            if bytes_val < 1024:
                return f"{bytes_val:.1f} {unit}"
            bytes_val /= 1024


    # Bundle system status
    
    system_status = {
    "db_performance": db_performance,
    "api_response_time": avg_response_time,
    "api_health": round(api_health, 1),
    "storage_capacity": storage_capacity,
    "storage_readable": human_readable(storage_used),
    "status": "All systems operational",
    "status_detail": "No issues detected"
    }
    
    return templates.TemplateResponse("overview.html", {
        "request": request,
        "total_indicators": total_indicators,
        "total_values": total_values,
        "total_dimensions": total_dimensions,
        "indicators_by_dimension": indicators_by_dimension,
        "table_count": table_count,
        "status_distribution": status_distribution,
        "sector_distribution": sector_distribution,
        "data_completeness": data_completeness,
        "avg_values_per_indicator": avg_values_per_indicator,
        "tracking_statuses": tracking_statuses,
        "recent_activity": formatted_changes,
        "year_coverage": year_coverage,
        "type_distribution": type_distribution,
        "priority_distribution": priority_distribution,
        "avg_update_freq": round(avg_update_freq, 1),
        "total_active_indicators": status_distribution.get('Active', 0),
        "total_inactive_indicators": status_distribution.get('Inactive', 0),
        "top_dimensions": sorted(indicators_by_dimension.items(), key=lambda x: x[1], reverse=True)[:5],
        "latest_year": latest_year,
        "system_status": system_status
    })
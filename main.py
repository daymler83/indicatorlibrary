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
from models import Indicator, IndicatorValue, IndicatorHistory
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse

app = FastAPI()

templates = Jinja2Templates(directory="templates")

class IndicatorCreate(BaseModel):
    id: str
    name: str
    owner: str
    status: str
    version: float
    dimension: Optional[str] = None
    sector: Optional[str] = None

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
    status: Optional[str] = None,
    dimension: Optional[str] = None,
    search: Optional[str] = None
):
    # Start with base query
    query = db.query(Indicator)
    
    # Apply filters if they exist
    if search:
        query = query.filter(Indicator.name.ilike(f"%{search}%"))
    if sector:
        query = query.filter(Indicator.sector == sector)
    if status:
        query = query.filter(Indicator.status == status)
    if dimension:
        query = query.filter(Indicator.dimension == dimension)
    
    indicators = query.all()
    
    # Get all indicator values for tracking dashboard
    indicator_values = db.query(IndicatorValue).all()
    
    # Get unique values for filter dropdowns from ALL indicators (not filtered)
    all_indicators = db.query(Indicator).all()
    
    sectors = list({ind.sector for ind in all_indicators if ind.sector})
    statuses = list({ind.status for ind in all_indicators})
    dimensions = list({ind.dimension for ind in all_indicators if ind.dimension})
    
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
        "selected_sector": sector,
        "selected_status": status,
        "selected_dimension": dimension,
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
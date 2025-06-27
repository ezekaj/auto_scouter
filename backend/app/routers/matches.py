from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.models.base import get_db
from app.models.scout import Match, ScoutReport
from app.schemas.scout import (
    Match as MatchSchema, 
    MatchCreate, 
    MatchUpdate,
    ScoutReport as ScoutReportSchema,
    ScoutReportCreate,
    ScoutReportUpdate
)

router = APIRouter()


@router.get("/", response_model=List[MatchSchema])
def read_matches(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    matches = db.query(Match).offset(skip).limit(limit).all()
    return matches


@router.post("/", response_model=MatchSchema)
def create_match(match: MatchCreate, db: Session = Depends(get_db)):
    db_match = Match(**match.dict())
    db.add(db_match)
    db.commit()
    db.refresh(db_match)
    return db_match


@router.get("/{match_id}", response_model=MatchSchema)
def read_match(match_id: int, db: Session = Depends(get_db)):
    match = db.query(Match).filter(Match.id == match_id).first()
    if match is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found"
        )
    return match


@router.put("/{match_id}", response_model=MatchSchema)
def update_match(match_id: int, match_update: MatchUpdate, db: Session = Depends(get_db)):
    match = db.query(Match).filter(Match.id == match_id).first()
    if match is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found"
        )
    
    update_data = match_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(match, field, value)
    
    db.commit()
    db.refresh(match)
    return match


@router.delete("/{match_id}")
def delete_match(match_id: int, db: Session = Depends(get_db)):
    match = db.query(Match).filter(Match.id == match_id).first()
    if match is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found"
        )
    
    db.delete(match)
    db.commit()
    return {"message": "Match deleted successfully"}


# Scout Report endpoints
@router.get("/{match_id}/reports", response_model=List[ScoutReportSchema])
def read_match_reports(match_id: int, db: Session = Depends(get_db)):
    reports = db.query(ScoutReport).filter(ScoutReport.match_id == match_id).all()
    return reports


@router.post("/{match_id}/reports", response_model=ScoutReportSchema)
def create_scout_report(match_id: int, report: ScoutReportCreate, db: Session = Depends(get_db)):
    # Verify match exists
    match = db.query(Match).filter(Match.id == match_id).first()
    if match is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found"
        )
    
    # Ensure the report is for the correct match
    report_data = report.dict()
    report_data["match_id"] = match_id
    
    db_report = ScoutReport(**report_data)
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return db_report


@router.get("/reports/{report_id}", response_model=ScoutReportSchema)
def read_scout_report(report_id: int, db: Session = Depends(get_db)):
    report = db.query(ScoutReport).filter(ScoutReport.id == report_id).first()
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scout report not found"
        )
    return report


@router.put("/reports/{report_id}", response_model=ScoutReportSchema)
def update_scout_report(report_id: int, report_update: ScoutReportUpdate, db: Session = Depends(get_db)):
    report = db.query(ScoutReport).filter(ScoutReport.id == report_id).first()
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scout report not found"
        )
    
    update_data = report_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(report, field, value)
    
    db.commit()
    db.refresh(report)
    return report


@router.delete("/reports/{report_id}")
def delete_scout_report(report_id: int, db: Session = Depends(get_db)):
    report = db.query(ScoutReport).filter(ScoutReport.id == report_id).first()
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scout report not found"
        )
    
    db.delete(report)
    db.commit()
    return {"message": "Scout report deleted successfully"}

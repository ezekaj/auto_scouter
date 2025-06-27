from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.models.base import get_db
from app.models.scout import Scout
from app.schemas.scout import Scout as ScoutSchema, ScoutCreate, ScoutUpdate

router = APIRouter()


@router.get("/", response_model=List[ScoutSchema])
def read_scouts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    scouts = db.query(Scout).offset(skip).limit(limit).all()
    return scouts


@router.post("/", response_model=ScoutSchema)
def create_scout(scout: ScoutCreate, db: Session = Depends(get_db)):
    # Check if scout with email already exists
    db_scout = db.query(Scout).filter(Scout.email == scout.email).first()
    if db_scout:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Scout with this email already exists"
        )
    
    db_scout = Scout(**scout.dict())
    db.add(db_scout)
    db.commit()
    db.refresh(db_scout)
    return db_scout


@router.get("/{scout_id}", response_model=ScoutSchema)
def read_scout(scout_id: int, db: Session = Depends(get_db)):
    scout = db.query(Scout).filter(Scout.id == scout_id).first()
    if scout is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scout not found"
        )
    return scout


@router.put("/{scout_id}", response_model=ScoutSchema)
def update_scout(scout_id: int, scout_update: ScoutUpdate, db: Session = Depends(get_db)):
    scout = db.query(Scout).filter(Scout.id == scout_id).first()
    if scout is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scout not found"
        )
    
    update_data = scout_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(scout, field, value)
    
    db.commit()
    db.refresh(scout)
    return scout


@router.delete("/{scout_id}")
def delete_scout(scout_id: int, db: Session = Depends(get_db)):
    scout = db.query(Scout).filter(Scout.id == scout_id).first()
    if scout is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scout not found"
        )
    
    db.delete(scout)
    db.commit()
    return {"message": "Scout deleted successfully"}

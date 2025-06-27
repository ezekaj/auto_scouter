from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.models.base import get_db
from app.models.scout import Team
from app.schemas.scout import Team as TeamSchema, TeamCreate, TeamUpdate

router = APIRouter()


@router.get("/", response_model=List[TeamSchema])
def read_teams(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    teams = db.query(Team).offset(skip).limit(limit).all()
    return teams


@router.post("/", response_model=TeamSchema)
def create_team(team: TeamCreate, db: Session = Depends(get_db)):
    # Check if team with number already exists
    db_team = db.query(Team).filter(Team.team_number == team.team_number).first()
    if db_team:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Team with this number already exists"
        )
    
    db_team = Team(**team.dict())
    db.add(db_team)
    db.commit()
    db.refresh(db_team)
    return db_team


@router.get("/{team_id}", response_model=TeamSchema)
def read_team(team_id: int, db: Session = Depends(get_db)):
    team = db.query(Team).filter(Team.id == team_id).first()
    if team is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    return team


@router.get("/number/{team_number}", response_model=TeamSchema)
def read_team_by_number(team_number: int, db: Session = Depends(get_db)):
    team = db.query(Team).filter(Team.team_number == team_number).first()
    if team is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    return team


@router.put("/{team_id}", response_model=TeamSchema)
def update_team(team_id: int, team_update: TeamUpdate, db: Session = Depends(get_db)):
    team = db.query(Team).filter(Team.id == team_id).first()
    if team is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    update_data = team_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(team, field, value)
    
    db.commit()
    db.refresh(team)
    return team


@router.delete("/{team_id}")
def delete_team(team_id: int, db: Session = Depends(get_db)):
    team = db.query(Team).filter(Team.id == team_id).first()
    if team is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    db.delete(team)
    db.commit()
    return {"message": "Team deleted successfully"}

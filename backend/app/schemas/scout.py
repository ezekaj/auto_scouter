from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ScoutBase(BaseModel):
    name: str
    email: str


class ScoutCreate(ScoutBase):
    pass


class ScoutUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    is_active: Optional[bool] = None


class Scout(ScoutBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TeamBase(BaseModel):
    team_number: int
    team_name: str
    school: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None


class TeamCreate(TeamBase):
    pass


class TeamUpdate(BaseModel):
    team_name: Optional[str] = None
    school: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None


class Team(TeamBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MatchBase(BaseModel):
    match_number: int
    competition_level: Optional[str] = None
    red_alliance: str
    blue_alliance: str
    red_score: Optional[int] = None
    blue_score: Optional[int] = None
    match_date: Optional[datetime] = None


class MatchCreate(MatchBase):
    pass


class MatchUpdate(BaseModel):
    competition_level: Optional[str] = None
    red_alliance: Optional[str] = None
    blue_alliance: Optional[str] = None
    red_score: Optional[int] = None
    blue_score: Optional[int] = None
    match_date: Optional[datetime] = None


class Match(MatchBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ScoutReportBase(BaseModel):
    scout_id: int
    team_id: int
    match_id: int
    auto_mobility: bool = False
    auto_high_goals: int = 0
    auto_low_goals: int = 0
    teleop_high_goals: int = 0
    teleop_low_goals: int = 0
    climb_attempted: bool = False
    climb_successful: bool = False
    notes: Optional[str] = None


class ScoutReportCreate(ScoutReportBase):
    pass


class ScoutReportUpdate(BaseModel):
    auto_mobility: Optional[bool] = None
    auto_high_goals: Optional[int] = None
    auto_low_goals: Optional[int] = None
    teleop_high_goals: Optional[int] = None
    teleop_low_goals: Optional[int] = None
    climb_attempted: Optional[bool] = None
    climb_successful: Optional[bool] = None
    notes: Optional[str] = None


class ScoutReport(ScoutReportBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

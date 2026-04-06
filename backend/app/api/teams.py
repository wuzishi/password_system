from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.user import User
from app.schemas.team import (
    TeamCreate, TeamUpdate, TeamResponse, TeamDetailResponse,
    TeamMemberAdd, TeamMemberResponse,
)
from app.services.audit_service import log_action
from app.api.deps import get_current_user, require_role
from app.core.security import Role

router = APIRouter(prefix="/api/teams", tags=["团队管理"])


def _team_response(team: Team) -> dict:
    return {
        "id": team.id,
        "name": team.name,
        "description": team.description,
        "created_by": team.created_by,
        "created_at": team.created_at,
        "member_count": len(team.members),
    }


@router.get("", response_model=List[TeamResponse])
def list_teams(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == Role.ADMIN:
        teams = db.query(Team).all()
    else:
        team_ids = [m.team_id for m in current_user.team_memberships]
        teams = db.query(Team).filter(Team.id.in_(team_ids)).all()
    return [_team_response(t) for t in teams]


@router.post("", response_model=TeamResponse)
def create_team(
    req: TeamCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    if db.query(Team).filter(Team.name == req.name).first():
        raise HTTPException(status_code=400, detail="团队名已存在")
    team = Team(name=req.name, description=req.description, created_by=current_user.id)
    db.add(team)
    db.commit()
    db.refresh(team)
    log_action(db, current_user.id, "team.create", "team", team.id, f"创建团队 {team.name}")
    return _team_response(team)


@router.get("/{team_id}", response_model=TeamDetailResponse)
def get_team(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="团队不存在")
    if current_user.role != Role.ADMIN:
        if not any(m.team_id == team_id for m in current_user.team_memberships):
            raise HTTPException(status_code=403, detail="无权访问此团队")
    members = []
    for m in team.members:
        user = db.query(User).filter(User.id == m.user_id).first()
        if user:
            members.append(TeamMemberResponse(
                id=m.id, user_id=user.id, username=user.username,
                email=user.email, role=user.role.value, joined_at=m.joined_at,
            ))
    resp = _team_response(team)
    resp["members"] = members
    return resp


@router.put("/{team_id}", response_model=TeamResponse)
def update_team(
    team_id: int,
    req: TeamUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="团队不存在")
    if req.name is not None:
        team.name = req.name
    if req.description is not None:
        team.description = req.description
    db.commit()
    db.refresh(team)
    log_action(db, current_user.id, "team.update", "team", team.id, f"更新团队 {team.name}")
    return _team_response(team)


@router.delete("/{team_id}")
def delete_team(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="团队不存在")
    log_action(db, current_user.id, "team.delete", "team", team.id, f"删除团队 {team.name}")
    db.delete(team)
    db.commit()
    return {"message": "已删除"}


@router.post("/{team_id}/members")
def add_member(
    team_id: int,
    req: TeamMemberAdd,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="团队不存在")
    user = db.query(User).filter(User.id == req.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    existing = db.query(TeamMember).filter(
        TeamMember.team_id == team_id, TeamMember.user_id == req.user_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户已在团队中")
    member = TeamMember(team_id=team_id, user_id=req.user_id)
    db.add(member)
    db.commit()
    log_action(db, current_user.id, "team.add_member", "team", team_id,
               f"添加成员 {user.username} 到团队 {team.name}")
    return {"message": "已添加"}


@router.delete("/{team_id}/members/{user_id}")
def remove_member(
    team_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    member = db.query(TeamMember).filter(
        TeamMember.team_id == team_id, TeamMember.user_id == user_id
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="成员不存在")
    team = db.query(Team).filter(Team.id == team_id).first()
    user = db.query(User).filter(User.id == user_id).first()
    log_action(db, current_user.id, "team.remove_member", "team", team_id,
               f"从团队 {team.name} 移除成员 {user.username}")
    db.delete(member)
    db.commit()
    return {"message": "已移除"}

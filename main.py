from fastapi import FastAPI, HTTPException, Security, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.api_key import APIKeyHeader
import uvicorn
from pydantic import BaseModel
from typing import List
import uuid

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, Session

SQLALCHEMY_DATABASE_URL = "sqlite:///./soldering_projects.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
sessionlocal = sessionmaker(autocommmit=False, autoflush=False, bind=engine)

Base = declarative_base()

class DBProject(Base):
     __tablename__ = "projects"
     id = Column(String, primary_key=True, index=True)
     name = Column(String)
     components = relationship("DBComponent", back_populates="project", cascade="all, delete-orphan")

class DBComponent(Base):
     __tablename__ = "components"
     id = Column(Integer, primary_key=True, index=True)
     project_id = Column(String, ForeignKey("projects.id"))
     designator = Column(String)
     value = Column(String)
     description = Column(String)
     is_soldered = Column(Boolean, default=False)
     project = relationship("DBProject", back_populates="components")

Base.metadata.create_all(bind=engine)

def get_db():
     db = sessionlocal()
     try:
          yield db
     finally:
          db.close()

API_KEY = "Pass@123"
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def verify_api_key(api_key: str = Security(api_key_header)):
     if api_key != API_KEY:
          raise HTTPException(status_code=403, detail="Unauthorized: Invalid API Key")
     return api_key

app = FastAPI(title="Soldering Assistant API")

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/")
def welcome():
    return {
        "message": "Welcome to the Soldering Assistant API!",
        "documentation": "Go to /docs to view the interactive API documentation.",
        "status": "Online"
    }

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class Component(BaseModel):
    designator: str
    value: str
    description: str
    is_soldered: bool = False

class NewProject(BaseModel):
     project_name: str
     components: List[Component]


@app.post("/addproject")
@limiter.limit("10/minute")
def add_project(request: Request, project: NewProject, db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    project_id = str(uuid.uuid4())[:8]
    
    db_project = DBProject(id=project_id, name=project.project_name)
    db.add(db_project)

    for comp in project.components:
        db_comp = DBComponent(
            project_id=project_id, designator=comp.designator, 
            value=comp.value, description=comp.description
        )
        db.add(db_comp)
        
    db.commit()

    return {
       "message": "project added successfully !",
       "project_name": project.project_name,
       "project_id": project_id
    }

@app.get("/projects")
@limiter.limit("30/minute")
def get_all_projects(request: Request, skip: int = 0, limit: int = 10, db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
  
    projects = db.query(DBProject).offset(skip).limit(limit).all()

    result = []
    
    for p in projects:
        result.append({"project_id": p.id, "project_name": p.name})
        
    return {"total_returned": len(result), "all_projects": result}

@app.get("/project/{project_id}/next")
@limiter.limit("100/minute")
def get_next(request: Request, project_id: str, db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    project = db.query(DBProject).filter(DBProject.id == project_id).first()
    if not project:
         
         raise HTTPException(status_code=404, detail="Project not found")
    
    next_comp = db.query(DBComponent).filter(
        DBComponent.project_id == project_id, 
        DBComponent.is_soldered == False
    ).first()

    if not next_comp:
        return {"message": "The Soldering is Complete", "Percentage": 100}

    return {
        "Project Name": project.name,
        "Project ID": project_id,
        "Status": "Under Process",
        "Next Component": {
            "designator": next_comp.designator,
            "value": next_comp.value,
            "description": next_comp.description
        }
    }

@app.patch("/projects/{project_id}/components/{designator}/done")
@limiter.limit("100/minute")
def mark_done(request: Request, project_id: str, designator: str, db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    comp = db.query(DBComponent).filter(
        DBComponent.project_id == project_id, 
        DBComponent.designator == designator
    ).first()
     
    if not comp:
        raise HTTPException(status_code=404, detail="Component or Project not found")
     
    comp.is_soldered = True
    db.commit()

    return {"message": f"The component {designator} is marked soldered successfully !"}
     

@app.patch("/projects/{project_id}/components/{designator}/undo")
@limiter.limit("100/minute")
def mark_undo(request: Request, project_id: str, designator: str, db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    comp = db.query(DBComponent).filter(
        DBComponent.project_id == project_id, 
        DBComponent.designator == designator
    ).first()
     
    if not comp:
        raise HTTPException(status_code=404, detail="Component or Project not found")
     
    comp.is_soldered = False
    db.commit()

    return {"message": f"The component {designator} is marked not soldered successfully !"}
     
@app.delete("/projects/{project_id}")
@limiter.limit("10/minute")
def delete_project(request: Request, project_id: str, db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    project = db.query(DBProject).filter(DBProject.id == project_id).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    db.delete(project)
    db.commit()

    return {"message": f"The project {project_id} is deleted successfully !"}

if __name__ == "__main__":
    uvicorn.run(app)
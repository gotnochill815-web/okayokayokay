from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import hashlib
import jwt
from emergentintegrations.llm.chat import LlmChat, UserMessage
import json
import re

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="Smart Productivity Assistant", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer()
JWT_SECRET = "your-secret-key-change-this-in-production"
JWT_ALGORITHM = "HS256"

# AI Configuration
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')

def hash_password(password: str) -> str:
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return hash_password(password) == hashed

def create_jwt_token(user_data: dict) -> str:
    """Create JWT token"""
    payload = {
        "user_id": user_data["id"],
        "email": user_data["email"],
        "exp": datetime.now(timezone.utc).timestamp() + 86400  # 24 hours
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user"""
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        
        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        
        return User(**user)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

# Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    user: User
    token: str
    message: str

class Note(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    title: str
    content: str
    summary: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    is_favorite: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class NoteCreate(BaseModel):
    title: str
    content: str
    tags: Optional[List[str]] = Field(default_factory=list)

class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None
    is_favorite: Optional[bool] = None

class AIRequest(BaseModel):
    action: str  # "summarize", "suggest_tags", "insights"
    note_id: str

class AIResponse(BaseModel):
    result: str
    action: str

# Helper functions
def prepare_for_mongo(data: dict) -> dict:
    """Prepare data for MongoDB storage"""
    if isinstance(data.get('created_at'), datetime):
        data['created_at'] = data['created_at'].isoformat()
    if isinstance(data.get('updated_at'), datetime):
        data['updated_at'] = data['updated_at'].isoformat()
    return data

def parse_from_mongo(item: dict) -> dict:
    """Parse data from MongoDB"""
    if isinstance(item.get('created_at'), str):
        item['created_at'] = datetime.fromisoformat(item['created_at'])
    if isinstance(item.get('updated_at'), str):
        item['updated_at'] = datetime.fromisoformat(item['updated_at'])
    return item

async def generate_ai_summary(content: str) -> str:
    """Generate AI summary for note content"""
    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"summary_{uuid.uuid4()}",
            system_message="You are a helpful assistant that creates concise, meaningful summaries of notes. Focus on key points and important information."
        ).with_model("openai", "gpt-4o-mini")
        
        user_message = UserMessage(
            text=f"Please provide a concise summary of the following note content:\n\n{content}"
        )
        
        response = await chat.send_message(user_message)
        return response
    except Exception as e:
        logging.error(f"Error generating AI summary: {e}")
        return "Summary generation failed"

async def generate_tag_suggestions(content: str) -> List[str]:
    """Generate AI tag suggestions for note content"""
    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"tags_{uuid.uuid4()}",
            system_message="You are a helpful assistant that suggests relevant tags for note content. Return only a JSON array of 3-5 relevant tags, no additional text."
        ).with_model("openai", "gpt-4o-mini")
        
        user_message = UserMessage(
            text=f"Suggest 3-5 relevant tags for this note content. Return only a JSON array of strings:\n\n{content}"
        )
        
        response = await chat.send_message(user_message)
        
        # Extract JSON from response
        json_match = re.search(r'\[.*\]', response)
        if json_match:
            tags = json.loads(json_match.group())
            return [tag.lower().strip() for tag in tags if isinstance(tag, str)]
        
        return []
    except Exception as e:
        logging.error(f"Error generating tag suggestions: {e}")
        return []

async def generate_insights(content: str) -> str:
    """Generate AI insights for note content"""
    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"insights_{uuid.uuid4()}",
            system_message="You are a productivity coach that provides insightful analysis of notes. Identify patterns, suggest improvements, and provide actionable advice."
        ).with_model("openai", "gpt-4o-mini")
        
        user_message = UserMessage(
            text=f"Analyze this note and provide insights, patterns, and productivity suggestions:\n\n{content}"
        )
        
        response = await chat.send_message(user_message)
        return response
    except Exception as e:
        logging.error(f"Error generating insights: {e}")
        return "Insight generation failed"

# Authentication routes
@api_router.post("/auth/register", response_model=LoginResponse)
async def register(user_data: UserCreate):
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    user = User(
        email=user_data.email,
        name=user_data.name
    )
    
    # Store user with hashed password
    user_dict = user.dict()
    user_dict["password_hash"] = hash_password(user_data.password)
    user_dict = prepare_for_mongo(user_dict)
    
    await db.users.insert_one(user_dict)
    
    # Create token
    token = create_jwt_token(user.dict())
    
    return LoginResponse(
        user=user,
        token=token,
        message="Registration successful"
    )

@api_router.post("/auth/login", response_model=LoginResponse)
async def login(login_data: UserLogin):
    # Find user
    user_doc = await db.users.find_one({"email": login_data.email})
    if not user_doc:
        raise HTTPException(status_code=400, detail="Invalid email or password")
    
    # Verify password
    if not verify_password(login_data.password, user_doc["password_hash"]):
        raise HTTPException(status_code=400, detail="Invalid email or password")
    
    # Parse user data
    user_doc = parse_from_mongo(user_doc)
    user = User(**{k: v for k, v in user_doc.items() if k != "password_hash"})
    
    # Create token
    token = create_jwt_token(user.dict())
    
    return LoginResponse(
        user=user,
        token=token,
        message="Login successful"
    )

# Notes routes
@api_router.post("/notes", response_model=Note)
async def create_note(note_data: NoteCreate, current_user: User = Depends(get_current_user)):
    # Generate AI summary if content is substantial
    summary = None
    if len(note_data.content) > 100:
        summary = await generate_ai_summary(note_data.content)
    
    # Create note
    note = Note(
        user_id=current_user.id,
        title=note_data.title,
        content=note_data.content,
        summary=summary,
        tags=note_data.tags or []
    )
    
    # Store note
    note_dict = prepare_for_mongo(note.dict())
    await db.notes.insert_one(note_dict)
    
    return note

@api_router.get("/notes", response_model=List[Note])
async def get_notes(
    current_user: User = Depends(get_current_user),
    search: Optional[str] = None,
    tags: Optional[str] = None,
    favorites_only: Optional[bool] = False
):
    # Build filter
    filter_query = {"user_id": current_user.id}
    
    if search:
        filter_query["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"content": {"$regex": search, "$options": "i"}}
        ]
    
    if tags:
        tag_list = [tag.strip() for tag in tags.split(",")]
        filter_query["tags"] = {"$in": tag_list}
    
    if favorites_only:
        filter_query["is_favorite"] = True
    
    # Get notes
    notes_cursor = db.notes.find(filter_query).sort("updated_at", -1)
    notes = []
    
    async for note_doc in notes_cursor:
        note_doc = parse_from_mongo(note_doc)
        notes.append(Note(**note_doc))
    
    return notes

@api_router.get("/notes/{note_id}", response_model=Note)
async def get_note(note_id: str, current_user: User = Depends(get_current_user)):
    note_doc = await db.notes.find_one({"id": note_id, "user_id": current_user.id})
    if not note_doc:
        raise HTTPException(status_code=404, detail="Note not found")
    
    note_doc = parse_from_mongo(note_doc)
    return Note(**note_doc)

@api_router.put("/notes/{note_id}", response_model=Note)
async def update_note(
    note_id: str, 
    note_update: NoteUpdate, 
    current_user: User = Depends(get_current_user)
):
    # Find note
    note_doc = await db.notes.find_one({"id": note_id, "user_id": current_user.id})
    if not note_doc:
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Prepare update data
    update_data = {k: v for k, v in note_update.dict().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc)
    
    # Generate new summary if content changed
    if note_update.content and len(note_update.content) > 100:
        update_data["summary"] = await generate_ai_summary(note_update.content)
    
    # Update note
    update_data = prepare_for_mongo(update_data)
    await db.notes.update_one(
        {"id": note_id, "user_id": current_user.id},
        {"$set": update_data}
    )
    
    # Get updated note
    updated_doc = await db.notes.find_one({"id": note_id, "user_id": current_user.id})
    updated_doc = parse_from_mongo(updated_doc)
    return Note(**updated_doc)

@api_router.delete("/notes/{note_id}")
async def delete_note(note_id: str, current_user: User = Depends(get_current_user)):
    result = await db.notes.delete_one({"id": note_id, "user_id": current_user.id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Note not found")
    
    return {"message": "Note deleted successfully"}

# AI routes
@api_router.post("/ai/process", response_model=AIResponse)
async def process_ai_request(request: AIRequest, current_user: User = Depends(get_current_user)):
    # Get note
    note_doc = await db.notes.find_one({"id": request.note_id, "user_id": current_user.id})
    if not note_doc:
        raise HTTPException(status_code=404, detail="Note not found")
    
    content = note_doc["content"]
    
    # Process based on action
    if request.action == "summarize":
        result = await generate_ai_summary(content)
    elif request.action == "suggest_tags":
        tags = await generate_tag_suggestions(content)
        result = json.dumps(tags)
    elif request.action == "insights":
        result = await generate_insights(content)
    else:
        raise HTTPException(status_code=400, detail="Invalid action")
    
    return AIResponse(result=result, action=request.action)

# Tags routes
@api_router.get("/tags")
async def get_user_tags(current_user: User = Depends(get_current_user)):
    """Get all unique tags for the current user"""
    pipeline = [
        {"$match": {"user_id": current_user.id}},
        {"$unwind": "$tags"},
        {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    
    tags = []
    async for doc in db.notes.aggregate(pipeline):
        tags.append({"tag": doc["_id"], "count": doc["count"]})
    
    return tags

# Stats routes
@api_router.get("/stats")
async def get_user_stats(current_user: User = Depends(get_current_user)):
    """Get user statistics"""
    total_notes = await db.notes.count_documents({"user_id": current_user.id})
    favorite_notes = await db.notes.count_documents({"user_id": current_user.id, "is_favorite": True})
    
    # Get recent activity (notes created in last 7 days)
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    recent_notes = await db.notes.count_documents({
        "user_id": current_user.id,
        "created_at": {"$gte": seven_days_ago.isoformat()}
    })
    
    return {
        "total_notes": total_notes,
        "favorite_notes": favorite_notes,
        "recent_notes": recent_notes,
        "total_tags": len(await get_user_tags(current_user))
    }

# Health check
@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Smart Productivity Assistant API"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
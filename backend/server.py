from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timezone
import re
from emergentintegrations.llm.chat import LlmChat, UserMessage


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# LLM setup
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')

# Pydantic Models
class NoteCreate(BaseModel):
    title: str
    content: str

class Note(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    content: str
    summary: Optional[str] = None
    keywords: List[str] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class NoteSummaryResponse(BaseModel):
    summary: str
    keywords: List[str]

class ScheduleRequest(BaseModel):
    natural_language: str

class ScheduleEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    date: str
    time: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TaskExtractionRequest(BaseModel):
    conversation_text: str

class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: Optional[str] = None
    deadline: Optional[str] = None
    priority: str = "medium"
    completed: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TaskExtractionResponse(BaseModel):
    tasks: List[Task]

# Helper functions
def prepare_for_mongo(data):
    """Convert datetime objects to ISO strings for MongoDB storage"""
    if isinstance(data.get('created_at'), datetime):
        data['created_at'] = data['created_at'].isoformat()
    return data

def parse_from_mongo(item):
    """Convert ISO strings back to datetime objects from MongoDB"""
    if isinstance(item.get('created_at'), str):
        item['created_at'] = datetime.fromisoformat(item['created_at'])
    return item

async def get_llm_response(prompt: str, session_id: str = "orbi-session") -> str:
    """Get response from LLM using emergentintegrations"""
    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=session_id,
            system_message="You are Orbi, a smart productivity assistant for students."
        ).with_model("openai", "gpt-4o-mini")
        
        user_message = UserMessage(text=prompt)
        response = await chat.send_message(user_message)
        return response
    except Exception as e:
        logger.error(f"LLM Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI processing failed: {str(e)}")

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Welcome to Orbi - Your Smart Productivity Assistant!"}

# Note Summarizer & Keyword Extractor
@api_router.post("/notes/summarize", response_model=NoteSummaryResponse)
async def summarize_note(note_data: NoteCreate):
    prompt = f"""
    Please analyze this note and provide:
    1. A concise summary (2-3 sentences max)
    2. Key keywords/tags (5-8 relevant terms)
    
    Note Title: {note_data.title}
    Note Content: {note_data.content}
    
    Format your response as:
    SUMMARY: [your summary here]
    KEYWORDS: [keyword1, keyword2, keyword3, ...]
    """
    
    response = await get_llm_response(prompt)
    
    # Parse the response
    summary_match = re.search(r'SUMMARY:\s*(.+?)(?=KEYWORDS:|$)', response, re.DOTALL)
    keywords_match = re.search(r'KEYWORDS:\s*(.+)', response, re.DOTALL)
    
    summary = summary_match.group(1).strip() if summary_match else "Summary not available"
    keywords_text = keywords_match.group(1).strip() if keywords_match else ""
    
    # Extract keywords from the text
    keywords = [kw.strip().strip('[]') for kw in keywords_text.split(',') if kw.strip()]
    keywords = [kw for kw in keywords if kw and len(kw) > 1][:8]  # Limit to 8 keywords
    
    return NoteSummaryResponse(summary=summary, keywords=keywords)

@api_router.post("/notes", response_model=Note)
async def create_note(note_data: NoteCreate):
    # First, get AI summary and keywords
    summary_response = await summarize_note(note_data)
    
    # Create note with AI-generated summary and keywords
    note = Note(
        title=note_data.title,
        content=note_data.content,
        summary=summary_response.summary,
        keywords=summary_response.keywords
    )
    
    # Store in MongoDB
    note_dict = prepare_for_mongo(note.dict())
    await db.notes.insert_one(note_dict)
    
    return note

@api_router.get("/notes", response_model=List[Note])
async def get_notes():
    notes = await db.notes.find().to_list(1000)
    return [Note(**parse_from_mongo(note)) for note in notes]

@api_router.delete("/notes/{note_id}")
async def delete_note(note_id: str):
    result = await db.notes.delete_one({"id": note_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Note not found")
    return {"message": "Note deleted successfully"}

# Natural Language Scheduling
@api_router.post("/schedule/parse", response_model=ScheduleEvent)
async def parse_schedule(request: ScheduleRequest):
    prompt = f"""
    Parse this natural language scheduling request and extract:
    1. Event title/subject
    2. Date (in YYYY-MM-DD format)
    3. Time (in HH:MM format, 24-hour)
    4. Brief description
    
    Input: "{request.natural_language}"
    
    Format your response as:
    TITLE: [event title]
    DATE: [YYYY-MM-DD]
    TIME: [HH:MM]
    DESCRIPTION: [brief description]
    """
    
    response = await get_llm_response(prompt)
    
    # Parse the response
    title_match = re.search(r'TITLE:\s*(.+)', response)
    date_match = re.search(r'DATE:\s*(.+)', response)
    time_match = re.search(r'TIME:\s*(.+)', response)
    desc_match = re.search(r'DESCRIPTION:\s*(.+)', response)
    
    title = title_match.group(1).strip() if title_match else "Scheduled Event"
    date = date_match.group(1).strip() if date_match else datetime.now().strftime("%Y-%m-%d")
    time = time_match.group(1).strip() if time_match else "09:00"
    description = desc_match.group(1).strip() if desc_match else ""
    
    event = ScheduleEvent(
        title=title,
        date=date,
        time=time,
        description=description
    )
    
    # Store in MongoDB
    event_dict = prepare_for_mongo(event.dict())
    await db.schedule_events.insert_one(event_dict)
    
    return event

@api_router.get("/schedule", response_model=List[ScheduleEvent])
async def get_schedule():
    events = await db.schedule_events.find().to_list(1000)
    return [ScheduleEvent(**parse_from_mongo(event)) for event in events]

# Task Extraction from Conversations
@api_router.post("/tasks/extract", response_model=TaskExtractionResponse)
async def extract_tasks(request: TaskExtractionRequest):
    prompt = f"""
    Analyze this conversation and extract any tasks, assignments, or actionable items.
    For each task found, provide:
    1. Task title
    2. Brief description
    3. Deadline (if mentioned, in YYYY-MM-DD format)
    4. Priority level (high/medium/low)
    
    Conversation: "{request.conversation_text}"
    
    Format your response as:
    TASK1:
    TITLE: [task title]
    DESCRIPTION: [description]
    DEADLINE: [YYYY-MM-DD or "none"]
    PRIORITY: [high/medium/low]
    
    TASK2:
    [continue for each task...]
    """
    
    response = await get_llm_response(prompt)
    
    # Parse tasks from response
    tasks = []
    task_blocks = response.split('TASK')[1:]  # Split by TASK markers
    
    for block in task_blocks:
        if not block.strip():
            continue
            
        title_match = re.search(r'TITLE:\s*(.+)', block)
        desc_match = re.search(r'DESCRIPTION:\s*(.+)', block)
        deadline_match = re.search(r'DEADLINE:\s*(.+)', block)
        priority_match = re.search(r'PRIORITY:\s*(.+)', block)
        
        if title_match:
            title = title_match.group(1).strip()
            description = desc_match.group(1).strip() if desc_match else ""
            deadline = deadline_match.group(1).strip() if deadline_match else None
            priority = priority_match.group(1).strip() if priority_match else "medium"
            
            if deadline and deadline.lower() == "none":
                deadline = None
                
            task = Task(
                title=title,
                description=description,
                deadline=deadline,
                priority=priority
            )
            tasks.append(task)
    
    # Store tasks in MongoDB
    for task in tasks:
        task_dict = prepare_for_mongo(task.dict())
        await db.tasks.insert_one(task_dict)
    
    return TaskExtractionResponse(tasks=tasks)

@api_router.get("/tasks", response_model=List[Task])
async def get_tasks():
    tasks = await db.tasks.find().to_list(1000)
    return [Task(**parse_from_mongo(task)) for task in tasks]

@api_router.put("/tasks/{task_id}/complete")
async def complete_task(task_id: str):
    result = await db.tasks.update_one(
        {"id": task_id},
        {"$set": {"completed": True}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task marked as complete"}

@api_router.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    result = await db.tasks.delete_one({"id": task_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task deleted successfully"}

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
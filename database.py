"""
Database models and session management for Xandy Learning AI Mentor System
"""
import sqlite3
import json
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
import os
import time
from logging_config import logger, log_database_operation

@dataclass
class ChatSession:
    id: str
    student_id: str
    mentor_id: str
    status: str  # 'active', 'paused', 'completed'
    created_at: str
    updated_at: str

@dataclass
class Message:
    id: str
    session_id: str
    sender_type: str  # 'student', 'mentor', 'ai'
    content: str
    is_ai_generated: bool
    approval_status: str  # 'pending', 'approved', 'rejected'
    approved_by: Optional[str]
    created_at: str

@dataclass
class MentorStyle:
    id: str
    mentor_id: str
    style_data: Dict
    sample_messages: List[str]
    analyzed_at: str
    confidence_score: float

@dataclass
class AIResponseQueue:
    id: str
    session_id: str
    student_message_id: str
    generated_response: str
    status: str  # 'pending', 'approved', 'rejected', 'sent'
    created_at: str
    approved_at: Optional[str]
    sent_at: Optional[str]

class DatabaseManager:
    def __init__(self, db_path: str = "xandy_learning.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database with required tables"""
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.execute("PRAGMA journal_mode=WAL")  # Enable WAL mode for better concurrency
            cursor = conn.cursor()
            
            # Create tables
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id TEXT PRIMARY KEY,
                    student_id TEXT NOT NULL,
                    mentor_id TEXT NOT NULL,
                    status TEXT DEFAULT 'active',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    sender_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    is_ai_generated BOOLEAN DEFAULT FALSE,
                    approval_status TEXT DEFAULT 'pending',
                    approved_by TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES chat_sessions (id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS mentor_styles (
                    id TEXT PRIMARY KEY,
                    mentor_id TEXT NOT NULL,
                    style_data TEXT NOT NULL,
                    sample_messages TEXT NOT NULL,
                    analyzed_at TEXT NOT NULL,
                    confidence_score REAL
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_response_queue (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    student_message_id TEXT NOT NULL,
                    generated_response TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    created_at TEXT NOT NULL,
                    approved_at TEXT,
                    sent_at TEXT,
                    FOREIGN KEY (session_id) REFERENCES chat_sessions (id),
                    FOREIGN KEY (student_message_id) REFERENCES messages (id)
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
            raise
    
    def create_session(self, student_id: str, mentor_id: str) -> str:
        """Create a new chat session"""
        start_time = time.time()
        logger.info(f"Creating new chat session", student_id=student_id, mentor_id=mentor_id)
        
        try:
            session_id = str(uuid.uuid4())
            now = datetime.now().isoformat()
            
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO chat_sessions (id, student_id, mentor_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (session_id, student_id, mentor_id, now, now))
            
            conn.commit()
            conn.close()
            
            duration = time.time() - start_time
            log_database_operation("CREATE", "chat_sessions", session_id, {
                "student_id": student_id,
                "mentor_id": mentor_id,
                "duration": duration
            })
            
            logger.info(f"Chat session created successfully", 
                       session_id=session_id, duration=f"{duration:.3f}s")
            return session_id
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Failed to create chat session", 
                        student_id=student_id, mentor_id=mentor_id, 
                        error=str(e), duration=f"{duration:.3f}s")
            raise
    
    def add_message(self, session_id: str, sender_type: str, content: str, 
                   is_ai_generated: bool = False, approval_status: str = 'approved') -> str:
        """Add a message to a session"""
        start_time = time.time()
        logger.info(f"Adding message to session", 
                   session_id=session_id, sender_type=sender_type, 
                   is_ai_generated=is_ai_generated, approval_status=approval_status,
                   content_length=len(content))
        
        try:
            message_id = str(uuid.uuid4())
            now = datetime.now().isoformat()
            
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO messages (id, session_id, sender_type, content, is_ai_generated, approval_status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (message_id, session_id, sender_type, content, is_ai_generated, approval_status, now))
            
            # Update session timestamp
            cursor.execute('''
                UPDATE chat_sessions SET updated_at = ? WHERE id = ?
            ''', (now, session_id))
            
            conn.commit()
            conn.close()
            
            duration = time.time() - start_time
            log_database_operation("INSERT", "messages", message_id, {
                "session_id": session_id,
                "sender_type": sender_type,
                "is_ai_generated": is_ai_generated,
                "approval_status": approval_status,
                "duration": duration
            })
            
            logger.info(f"Message added successfully", 
                       message_id=message_id, duration=f"{duration:.3f}s")
            return message_id
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Failed to add message", 
                        session_id=session_id, sender_type=sender_type, 
                        error=str(e), duration=f"{duration:.3f}s")
            raise
    
    def get_session_messages(self, session_id: str) -> List[Message]:
        """Get all messages for a session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, session_id, sender_type, content, is_ai_generated, approval_status, approved_by, created_at
            FROM messages WHERE session_id = ? ORDER BY created_at ASC
        ''', (session_id,))
        
        messages = []
        for row in cursor.fetchall():
            messages.append(Message(
                id=row[0],
                session_id=row[1],
                sender_type=row[2],
                content=row[3],
                is_ai_generated=bool(row[4]),
                approval_status=row[5],
                approved_by=row[6],
                created_at=row[7]
            ))
        
        conn.close()
        return messages
    
    def get_session_context(self, session_id: str) -> str:
        """Get formatted chat history for AI context"""
        messages = self.get_session_messages(session_id)
        context = []
        
        for msg in messages:
            if msg.approval_status == 'approved':
                context.append(f"{msg.sender_type}: {msg.content}")
        
        return "\n".join(context)
    
    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """Get a specific chat session by ID"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, mentor_id, student_id, status, created_at, updated_at
            FROM chat_sessions WHERE id = ?
        ''', (session_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return ChatSession(
                id=row[0],
                mentor_id=row[1],
                student_id=row[2],
                status=row[3],
                created_at=row[4],
                updated_at=row[5]
            )
        return None
    
    def save_mentor_style(self, mentor_id: str, style_data: Dict, sample_messages: List[str], 
                         confidence_score: float) -> str:
        """Save analyzed mentor style"""
        style_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO mentor_styles (id, mentor_id, style_data, sample_messages, analyzed_at, confidence_score)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (style_id, mentor_id, json.dumps(style_data), json.dumps(sample_messages), now, confidence_score))
        
        conn.commit()
        conn.close()
        
        return style_id
    
    def get_mentor_style(self, mentor_id: str) -> Optional[MentorStyle]:
        """Get the latest mentor style analysis"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, mentor_id, style_data, sample_messages, analyzed_at, confidence_score
            FROM mentor_styles WHERE mentor_id = ? ORDER BY analyzed_at DESC LIMIT 1
        ''', (mentor_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return MentorStyle(
                id=row[0],
                mentor_id=row[1],
                style_data=json.loads(row[2]),
                sample_messages=json.loads(row[3]),
                analyzed_at=row[4],
                confidence_score=row[5]
            )
        return None
    
    def add_ai_response_to_queue(self, session_id: str, student_message_id: str, 
                                generated_response: str) -> str:
        """Add AI-generated response to approval queue"""
        queue_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO ai_response_queue (id, session_id, student_message_id, generated_response, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (queue_id, session_id, student_message_id, generated_response, now))
        
        conn.commit()
        conn.close()
        
        return queue_id
    
    def get_pending_ai_responses(self, mentor_id: str) -> List[Dict]:
        """Get pending AI responses for mentor approval"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT arq.id, arq.session_id, arq.student_message_id, arq.generated_response, 
                   arq.created_at, m.content as student_message
            FROM ai_response_queue arq
            JOIN messages m ON arq.student_message_id = m.id
            JOIN chat_sessions cs ON arq.session_id = cs.id
            WHERE cs.mentor_id = ? AND arq.status = 'pending'
            ORDER BY arq.created_at ASC
        ''', (mentor_id,))
        
        responses = []
        for row in cursor.fetchall():
            responses.append({
                'id': row[0],
                'session_id': row[1],
                'student_message_id': row[2],
                'generated_response': row[3],
                'created_at': row[4],
                'student_message': row[5]
            })
        
        conn.close()
        return responses
    
    def approve_ai_response(self, queue_id: str, mentor_id: str) -> bool:
        """Approve an AI-generated response"""
        start_time = time.time()
        logger.info(f"Approving AI response", queue_id=queue_id, mentor_id=mentor_id)
        
        try:
            now = datetime.now().isoformat()
            
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            cursor = conn.cursor()
            
            # Get the response details first
            cursor.execute('''
                SELECT session_id, generated_response FROM ai_response_queue WHERE id = ?
            ''', (queue_id,))
            
            row = cursor.fetchone()
            if not row:
                logger.error(f"AI response not found in queue", queue_id=queue_id)
                conn.close()
                return False
            
            session_id, response_content = row
            
            # Add approved message to session (using direct SQL to avoid connection conflicts)
            message_id = str(uuid.uuid4())
            cursor.execute('''
                INSERT INTO messages (id, session_id, sender_type, content, is_ai_generated, approval_status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (message_id, session_id, 'ai', response_content, True, 'approved', now))
            
            # Update session timestamp
            cursor.execute('''
                UPDATE chat_sessions SET updated_at = ? WHERE id = ?
            ''', (now, session_id))
            
            # Update queue status to approved
            cursor.execute('''
                UPDATE ai_response_queue SET status = 'approved', approved_at = ? WHERE id = ?
            ''', (now, queue_id))
            
            # Update queue to sent
            cursor.execute('''
                UPDATE ai_response_queue SET status = 'sent', sent_at = ? WHERE id = ?
            ''', (now, queue_id))
            
            conn.commit()
            conn.close()
            
            duration = time.time() - start_time
            log_database_operation("APPROVE_AI_RESPONSE", "ai_response_queue", queue_id, {
                "session_id": session_id,
                "mentor_id": mentor_id,
                "duration": duration
            })
            
            logger.info(f"AI response approved successfully", 
                       queue_id=queue_id, duration=f"{duration:.3f}s")
            return True
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Error approving AI response", 
                        queue_id=queue_id, mentor_id=mentor_id, 
                        error=str(e), duration=f"{duration:.3f}s")
            return False
    
    def reject_ai_response(self, queue_id: str) -> bool:
        """Reject an AI-generated response"""
        start_time = time.time()
        logger.info(f"Rejecting AI response", queue_id=queue_id)
        
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE ai_response_queue SET status = 'rejected' WHERE id = ?
            ''', (queue_id,))
            
            conn.commit()
            conn.close()
            
            duration = time.time() - start_time
            log_database_operation("REJECT_AI_RESPONSE", "ai_response_queue", queue_id, {
                "duration": duration
            })
            
            logger.info(f"AI response rejected successfully", 
                       queue_id=queue_id, duration=f"{duration:.3f}s")
            return True
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Error rejecting AI response", 
                        queue_id=queue_id, error=str(e), duration=f"{duration:.3f}s")
            return False

# Global database instance (lazy initialization)
_db_instance = None

def get_db():
    """Get the global database instance with lazy initialization"""
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseManager()
    return _db_instance

# For backward compatibility
db = get_db()

import google.generativeai as genai
import os
import streamlit as st
from dotenv import load_dotenv
from database import db, ChatSession, Message, MentorStyle
from typing import Optional, List, Dict
import time
import json
from logging_config import logger, log_ai_interaction, log_performance

# Load environment variables from .env file
load_dotenv()

# Define the model
MODEL = "gemini-2.5-flash"

def configure_gemini():
    """Configure Google Gemini API"""
    logger.info("Configuring Gemini API")
    try:
        # Configure the API key
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.error("GEMINI_API_KEY environment variable is missing")
            st.error("GEMINI_API_KEY environment variable is missing. Please set it in your .env file or environment.")
            st.stop()
        
        genai.configure(api_key=api_key)
        logger.info("Gemini API configured successfully")
        return True
    except Exception as e:
        logger.error(f"Error configuring Gemini API", error=str(e))
        st.error(f"Error configuring Gemini: {str(e)}")
        st.stop()

# Configure Gemini API
configure_gemini()

# System prompt for Student Context Analysis
SYSTEM_PROMPT_SUMMARIZE_CONTEXT = """You are a Student Context Analyst. Read the entire <CHAT_HISTORY> and output a brief, 1-2 sentence summary of the student's journey.

Your summary must include:
1. **Current Topic:** What is the student currently learning?
2. **Past Struggles:** What topics did they find difficult before?
3. **Recent Successes:** What topics have they mastered?

Output ONLY this 1-2 sentence summary."""

# System prompt for the Reply Agent
SYSTEM_PROMPT_REPLY = """You are a Communication Style Mimicking Agent for a mentor-student messaging system. Your job is to learn and replicate a mentor's communication style to generate responses that authentically match their style.

**1. The Mentor's Style Guide (HOW to talk):**
You MUST adhere to this style, which was analyzed from the conversation history.
<MENTOR_STYLE_EXAMPLES>
{mentor_style}
</MENTOR_STYLE_EXAMPLES>

**2. The Student's Context (WHAT to talk about):**
You MUST show you remember the student's journey.
<STUDENT_CONTEXT_SUMMARY>
{student_context}
</STUDENT_CONTEXT_SUMMARY>

**3. The Current Conversation:**
<CHAT_HISTORY>
{chat_history}
</CHAT_HISTORY>

**4. The New Student Message:**
<NEW_STUDENT_MESSAGE>
{student_message}
</NEW_STUDENT_MESSAGE>

**Task:**
Generate a reply to the <NEW_STUDENT_MESSAGE>.
Your reply MUST:
1. Perfectly match the mentor's style from the Style Guide.
2. Be a helpful, context-aware answer.
3. Acknowledge the student's journey from the Context Summary (e.g., "Just like when you learned variables...").

Generate ONLY the final reply."""

# System prompt for the Nudge Agent
SYSTEM_PROMPT_NUDGE = """You are a Proactive Mentor Agent specialized in generating contextual follow-up messages to students. Your role is to understand a mentor's unique communication style and create authentic, helpful messages that feel natural and supportive.

**Your Capabilities:**
- Analyze communication patterns including tone, vocabulary, sentence structure, punctuation, and emoji usage
- Understand contextual triggers and determine appropriate follow-up actions
- Generate messages that authentically match the mentor's established style
- Maintain professional boundaries while being warm and encouraging

**Security and Safety Guidelines:**
- Never generate content that could be harmful, inappropriate, or violate educational boundaries
- Avoid personal questions about sensitive topics (health, family, finances, etc.)
- Maintain appropriate mentor-student relationship dynamics
- Do not generate content that could be misconstrued as romantic, overly personal, or unprofessional
- Focus on academic support, encouragement, and educational guidance
- If a trigger event seems inappropriate or concerning, respond with general encouragement rather than specific follow-up

**Communication Style Analysis:**
When analyzing a mentor's style, pay attention to:
- Tone: Formal vs. casual, encouraging vs. direct, warm vs. professional
- Language patterns: Common phrases, greetings, sign-offs, punctuation habits
- Emoji usage: Frequency, types, and placement
- Message length and structure
- Personal touches and unique expressions

**Contextual Response Generation:**
- Understand the trigger event and its educational significance
- Determine the most appropriate and helpful follow-up action
- Craft a message that feels natural and timely
- Ensure the message adds value to the student's learning experience

**Output Requirements:**
Generate only the final nudge message. Do not include analysis, explanations, or meta-commentary. The message should be ready to send as-is and should feel like it was written by the mentor themselves."""

def summarize_student_journey(chat_history: str) -> str:
    """Analyze chat history to summarize the student's learning journey"""
    start_time = time.time()
    logger.info(f"Summarizing student journey", history_length=len(chat_history))
    
    try:
        prompt = f"""<CHAT_HISTORY>
{chat_history}
</CHAT_HISTORY>"""
        
        model = genai.GenerativeModel(MODEL)
        response = model.generate_content(
            f"{SYSTEM_PROMPT_SUMMARIZE_CONTEXT}\n\n{prompt}"
        )
        
        duration = time.time() - start_time
        logger.info(f"Student journey summarized", duration=f"{duration:.3f}s", summary_length=len(response.text))
        
        return response.text.strip()
        
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Error summarizing student journey", error=str(e), duration=f"{duration:.3f}s")
        return "Student is learning programming concepts."

def invoke_reply_agent(mentor_id: str, student_message: str, session_id: str, 
                      mentor_style: Optional[str] = None, student_context: Optional[str] = None) -> str:
    """Generate a reply to a student message in the mentor's style with context awareness"""
    start_time = time.time()
    logger.info(f"Generating AI reply", 
               mentor_id=mentor_id, session_id=session_id, 
               message_length=len(student_message))
    
    try:
        # Get mentor style from database if not provided
        if not mentor_style:
            logger.debug("Retrieving mentor style from database", mentor_id=mentor_id)
            mentor_style_data = db.get_mentor_style(mentor_id)
            if mentor_style_data:
                mentor_style = "\n".join(mentor_style_data.sample_messages)
                logger.debug("Mentor style retrieved", 
                           style_confidence=mentor_style_data.confidence_score)
            else:
                mentor_style = "No style examples available. Please provide mentor style examples."
                logger.warning("No mentor style found in database", mentor_id=mentor_id)
        
        # Get chat history from database
        logger.debug("Retrieving chat history", session_id=session_id)
        chat_history = db.get_session_context(session_id)
        
        # Summarize student journey if not provided
        if not student_context and chat_history:
            logger.debug("Summarizing student journey from chat history")
            student_context = summarize_student_journey(chat_history)
        elif not student_context:
            student_context = "New conversation - no prior context."
        
        prompt_content = f"""<MENTOR_STYLE_EXAMPLES>
{mentor_style}
</MENTOR_STYLE_EXAMPLES>

<STUDENT_CONTEXT_SUMMARY>
{student_context}
</STUDENT_CONTEXT_SUMMARY>

<CHAT_HISTORY>
{chat_history}
</CHAT_HISTORY>

<NEW_STUDENT_MESSAGE>
{student_message}
</NEW_STUDENT_MESSAGE>"""
        
        logger.debug("Calling Gemini API for reply generation", 
                   prompt_length=len(prompt_content))
        
        model = genai.GenerativeModel(MODEL)
        response = model.generate_content(
            f"{SYSTEM_PROMPT_REPLY}\n\n{prompt_content}"
        )
        
        duration = time.time() - start_time
        log_performance("AI_REPLY_GENERATION", duration, {
            "mentor_id": mentor_id,
            "session_id": session_id,
            "response_length": len(response.text)
        })
        
        log_ai_interaction(mentor_id, session_id, "REPLY_GENERATION", {
            "student_message_length": len(student_message),
            "response_length": len(response.text),
            "duration": duration
        })
        
        logger.info(f"AI reply generated successfully", 
                   duration=f"{duration:.3f}s", response_length=len(response.text))
        return response.text
        
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Error generating AI reply", 
                    mentor_id=mentor_id, session_id=session_id, 
                    error=str(e), duration=f"{duration:.3f}s")
        st.error(f"Error generating reply: {str(e)}")
        return "Sorry, I encountered an error while generating a reply. Please try again."

def invoke_nudge_agent(mentor_id: str, event_description: str, 
                      mentor_style: Optional[str] = None) -> str:
    """Generate a proactive nudge message based on an event"""
    start_time = time.time()
    logger.info(f"Generating nudge message", mentor_id=mentor_id, event=event_description)
    
    try:
        # Get mentor style from database if not provided
        if not mentor_style:
            mentor_style_data = db.get_mentor_style(mentor_id)
            if mentor_style_data:
                mentor_style = "\n".join(mentor_style_data.sample_messages)
            else:
                mentor_style = "No style examples available. Please provide mentor style examples."
        
        prompt_content = f"""<MENTOR_STYLE_EXAMPLES>
{mentor_style}
</MENTOR_STYLE_EXAMPLES>

<TRIGGER_EVENT>
{event_description}
</TRIGGER_EVENT>"""
        
        model = genai.GenerativeModel(MODEL)
        response = model.generate_content(
            f"{SYSTEM_PROMPT_NUDGE}\n\n{prompt_content}"
        )
        
        duration = time.time() - start_time
        log_performance("AI_NUDGE_GENERATION", duration, {
            "mentor_id": mentor_id,
            "response_length": len(response.text)
        })
        
        logger.info(f"Nudge generated successfully", duration=f"{duration:.3f}s")
        return response.text
        
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Error generating nudge", mentor_id=mentor_id, error=str(e), duration=f"{duration:.3f}s")
        st.error(f"Error generating nudge: {str(e)}")
        return "Sorry, I encountered an error while generating a nudge. Please try again."

def analyze_mentor_style(mentor_id: str, sample_messages: List[str]) -> Dict:
    """Analyze mentor's communication style from sample messages"""
    start_time = time.time()
    logger.info(f"Analyzing mentor style", mentor_id=mentor_id, sample_count=len(sample_messages))
    
    try:
        # Combine all sample messages
        combined_messages = "\n".join(sample_messages)
        
        # Create analysis prompt with better instructions
        analysis_prompt = f"""You are a communication style analyzer for a mentor-student messaging system. Analyze the following mentor's messages to understand their unique communication patterns.

Mentor Messages:
{combined_messages}

Analyze and return ONLY a valid JSON object with these exact fields:
{{
    "tone": "casual/formal/encouraging/direct",
    "common_phrases": ["specific phrases they use frequently"],
    "emoji_usage": "frequent/occasional/rare/none",
    "message_length": "short/medium/long",
    "greeting_style": "how they start messages",
    "sign_off_style": "how they end messages", 
    "punctuation_style": "exclamation_heavy/question_heavy/period_heavy/mixed",
    "encouragement_level": "high/medium/low",
    "teaching_approach": "step_by_step/example_heavy/concept_focused",
    "response_pattern": "immediate_detailed/quick_acknowledgment/structured"
}}

Focus on identifying:
- Unique phrases and expressions they use
- How they structure explanations
- Their approach to encouragement and support
- Communication rhythm and style

Return ONLY the JSON object, no explanations."""
        
        model = genai.GenerativeModel(MODEL)
        response = model.generate_content(analysis_prompt)
        
        # Clean the response text
        response_text = response.text.strip()
        
        # Remove any markdown formatting if present
        if response_text.startswith("```json"):
            response_text = response_text.replace("```json", "").replace("```", "").strip()
        elif response_text.startswith("```"):
            response_text = response_text.replace("```", "").strip()
        
        logger.debug(f"Raw AI response: {response_text}")
        
        # Parse JSON response
        style_data = json.loads(response_text)
        
        # Validate the response has required fields
        required_fields = ["tone", "common_phrases", "emoji_usage", "message_length", 
                          "greeting_style", "sign_off_style", "punctuation_style", "encouragement_level"]
        
        for field in required_fields:
            if field not in style_data:
                logger.warning(f"Missing field in style analysis: {field}")
                style_data[field] = "unknown"
        
        # Save to database
        confidence_score = 0.8
        db.save_mentor_style(mentor_id, style_data, sample_messages, confidence_score)
        
        duration = time.time() - start_time
        log_performance("STYLE_ANALYSIS", duration, {
            "mentor_id": mentor_id,
            "sample_count": len(sample_messages),
            "confidence_score": confidence_score
        })
        
        logger.info(f"Style analysis completed", duration=f"{duration:.3f}s", confidence=confidence_score)
        return style_data
        
    except json.JSONDecodeError as e:
        duration = time.time() - start_time
        logger.error(f"JSON parsing error in style analysis", mentor_id=mentor_id, error=str(e), 
                    response_text=response_text if 'response_text' in locals() else "No response", 
                    duration=f"{duration:.3f}s")
        
        # Return a default style if JSON parsing fails
        default_style = {
            "tone": "encouraging",
            "common_phrases": ["Great question", "No worries", "You got this"],
            "emoji_usage": "occasional",
            "message_length": "medium",
            "greeting_style": "friendly",
            "sign_off_style": "encouraging",
            "punctuation_style": "mixed",
            "encouragement_level": "high"
        }
        
        # Save default style to database
        db.save_mentor_style(mentor_id, default_style, sample_messages, 0.5)
        return default_style
        
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Error analyzing mentor style", mentor_id=mentor_id, error=str(e), duration=f"{duration:.3f}s")
        st.error(f"Error analyzing mentor style: {str(e)}")
        return {}

def generate_ai_response_with_approval(mentor_id: str, student_message: str, session_id: str) -> str:
    """Generate AI response and add to approval queue"""
    
    # Generate the response
    ai_response = invoke_reply_agent(mentor_id, student_message, session_id)
    
    # Add student message to database
    student_message_id = db.add_message(session_id, 'student', student_message)
    
    # Add AI response to approval queue
    queue_id = db.add_ai_response_to_queue(session_id, student_message_id, ai_response)
    
    return queue_id, ai_response

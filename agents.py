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

# System prompt for the Reply Agent (Generator)
SYSTEM_PROMPT_REPLY = """You are an AI Mentor's Assistant. Your ONLY task is to write a reply to a student.
You MUST write the reply in the exact style of the mentor.

A previous agent has analyzed the mentor's style. Your reply MUST strictly follow all rules in this style guide.

<STYLE_GUIDE_JSON>
{mentor_style}
</STYLE_GUIDE_JSON>

<STUDENT_CONTEXT_SUMMARY>
{student_context}
</STUDENT_CONTEXT_SUMMARY>

<RECENT_CHAT_HISTORY>
{chat_history}
</RECENT_CHAT_HISTORY>

<NEW_STUDENT_MESSAGE>
{student_message}
</NEW_STUDENT_MESSAGE>

Task:
1. Read the <NEW_STUDENT_MESSAGE>.
2. Read the <RECENT_CHAT_HISTORY> and <STUDENT_CONTEXT_SUMMARY> to understand what to talk about.
3. Write a helpful, relevant reply.
4. **Crucially:** Re-write your reply to perfectly match all the rules in the <STYLE_GUIDE_JSON>.
   - Match the `formality` and `tone`.
   - Use emojis ONLY as specified by `emoji_usage`.
   - Use punctuation as specified by `punctuation_style`.
   - Try to use phrases from `common_phrases` and `greeting_examples` if it sounds natural.
   - Reference the student's journey from the context summary when relevant.

Generate ONLY the final reply to the student."""

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
    """Analyze mentor's communication style from sample messages using concrete text patterns"""
    start_time = time.time()
    logger.info(f"Analyzing mentor style", mentor_id=mentor_id, sample_count=len(sample_messages))
    
    try:
        # Combine all sample messages
        combined_messages = "\n".join(sample_messages)
        
        # Step 1: The "Analyst" Agent - Extract CONCRETE patterns
        analysis_prompt = f"""You are a meticulous Communication Pattern Analyzer. Your only job is to read the <MENTOR_MESSAGES> and output a valid JSON object that captures the mentor's literal communication patterns.

<MENTOR_MESSAGES>
{combined_messages}
</MENTOR_MESSAGES>

Analyze and return ONLY a valid JSON object with these exact fields:

{{
  "formality": "casual (uses 'hey', 'yeah', 'gonna') or formal (uses 'greetings', 'acknowledged', 'proceed')",
  "tone": "encouraging (uses praise, 'you got this!') or direct (no-nonsense, factual) or socratic (asks guiding questions)",
  "emoji_usage": "none, rare (1-2 per message), or frequent (in almost every message)",
  "punctuation_style": "Uses exclamation points frequently! or Uses periods only. or Uses ellipses... often. or Mixed punctuation",
  "greeting_examples": ["exact greetings found in text", "e.g., 'Hey there!'", "'Hi,'"],
  "sign_off_examples": ["exact sign-offs found", "e.g., 'You got this!'", "'Keep it up!'"],
  "common_phrases": ["unique recurring words or phrases", "e.g., 'No worries'", "'Think of it like...'", "'Let's break it down'"]
}}

Focus ONLY on what you literally see in the text. Do not interpret or abstract.
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


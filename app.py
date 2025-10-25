"""
AI Agent Intern - Technical Assessment Solution
Communication Style Mimicking Agent for Mentor-Student Messaging System
"""
import streamlit as st
import os
from datetime import datetime
from agents import (
    invoke_reply_agent, 
    analyze_mentor_style
)
from database import db
from logging_config import logger, log_user_action, log_ai_interaction

# Page configuration
st.set_page_config(
    page_title="AI Agent Assessment - Style Mimicking System",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
def init_session_state():
    """Initialize session state variables"""
    defaults = {
        "current_session_id": None,
        "current_mentor_id": "mentor_001",
        "student_id": "student_001"
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def render_sidebar():
    """Render simplified sidebar"""
    with st.sidebar:
        st.header("🎯 AI Style Mimicking System")
        
        # Mentor ID
        mentor_id = st.text_input(
            "Mentor ID", 
            value=st.session_state.get("current_mentor_id", "mentor_001"),
            help="Your unique mentor identifier"
        )
        st.session_state.current_mentor_id = mentor_id
        
        st.divider()
        
        # Style Analysis
        st.subheader("🎨 Style Analysis")
        
        # Mentor personality selection
        mentor_type = st.selectbox(
            "Choose Mentor Personality:",
            ["Encouraging Mentor", "Direct Mentor", "Academic Mentor", "Casual Mentor"],
            help="Select a mentor personality type to analyze"
        )
        
        if st.button("Analyze Style", help="Analyze the selected mentor's communication patterns"):
            analyze_mentor_style_ui(mentor_id, mentor_type)
        
        st.divider()
        
        # Session Management
        st.subheader("💬 Session Management")
        if st.button("🆕 New Session", help="Start a new chat session"):
            create_new_session()
        
        # Show current session info
        if st.session_state.get("current_session_id"):
            session = db.get_session(st.session_state.get("current_session_id"))
            if session:
                st.info(f"**Active Session:** {session.student_id}")
        
        st.divider()
        
        # Event Simulation
        st.subheader("🎯 Event Simulation")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🐍 Python", help="Simulate Python exam"):
                simulate_exam(mentor_id, "Python Basics Final")
        
        with col2:
            if st.button("📐 Math", help="Simulate Math exam"):
                simulate_exam(mentor_id, "Algebra Fundamentals")
        
        # Show generated nudge if available
        if 'generated_nudge' in st.session_state and st.session_state.generated_nudge:
            st.divider()
            st.subheader("💬 Generated Nudge")
            st.write(st.session_state.generated_nudge)
            
            if st.session_state.get("current_session_id"):
                if st.button("✅ Add to Session"):
                    db.add_message(
                        st.session_state.get("current_session_id"), 
                        'ai', 
                        st.session_state.generated_nudge, 
                        is_ai_generated=True, 
                        approval_status='approved'
                    )
                    st.success("✅ Nudge added!")
                    del st.session_state.generated_nudge
                    st.rerun()
            else:
                st.warning("⚠️ No active session")

def analyze_mentor_style_ui(mentor_id: str, mentor_type: str):
    """UI for mentor style analysis"""
    log_user_action(mentor_id, "STYLE_ANALYSIS_REQUEST", {"mentor_type": mentor_type})
    
    with st.spinner(f"Analyzing {mentor_type} communication style..."):
        # Get sample messages based on mentor type
        sample_messages = get_mentor_sample_messages(mentor_type)
        
        style_data = analyze_mentor_style(mentor_id, sample_messages)
        
        if style_data:
            log_user_action(mentor_id, "STYLE_ANALYSIS_SUCCESS", {
                "mentor_type": mentor_type,
                "style_characteristics": list(style_data.keys())
            })
            st.success(f"✅ {mentor_type} style analyzed successfully!")
            st.json(style_data)
        else:
            log_user_action(mentor_id, "STYLE_ANALYSIS_FAILED", {"mentor_type": mentor_type})
            st.error("❌ Failed to analyze style")

def get_mentor_sample_messages(mentor_type: str) -> list:
    """Get sample messages for different mentor personality types based on best teaching methodologies"""
    
    mentor_samples = {
        "Encouraging Mentor": [
            "Great question! This shows you're thinking critically. Let me build on what you already know - can you tell me what you've tried so far?",
            "You're making excellent progress! I can see you understand the foundation. Now, let's connect this to the next concept.",
            "I appreciate your effort here. Let's use the Socratic method - what do you think might happen if we approach it this way?",
            "This is a common challenge, and asking about it shows real learning. Let's break it into smaller, manageable pieces.",
            "You've demonstrated good understanding of the basics. Now let's scaffold up to the more complex parts together."
        ],
        
        "Direct Mentor": [
            "Let's apply Bloom's Taxonomy here. First, understand the concept. Then, we'll apply it to solve real problems.",
            "Here's the core principle. Practice this pattern: understand, apply, analyze. Let's start with a concrete example.",
            "Focus on mastery learning - we won't move forward until you've fully grasped this foundation. Let's verify your understanding.",
            "Let me demonstrate this using worked examples. Watch how I approach it, then you'll try with guided practice.",
            "The key is deliberate practice with immediate feedback. Try this problem, and I'll show you exactly where to improve."
        ],
        
        "Academic Mentor": [
            "Let's apply constructivist principles here. What prior knowledge can we activate to build upon?",
            "Consider the zone of proximal development - this challenge is slightly beyond your current level, which means optimal growth.",
            "Let's use metacognitive strategies. As we work through this, I'll model my thinking process explicitly.",
            "From a pedagogical perspective, we should employ spaced repetition. Let's review the foundation before adding complexity.",
            "Using cognitive load theory, let's chunk this information. We'll tackle each piece sequentially to avoid overwhelm."
        ],
        
        "Casual Mentor": [
            "Let's think about this together. What's your intuition telling you? Often your first instinct points us in the right direction.",
            "Makes sense? Let's use an analogy you already know - think of it like [familiar concept]. Now apply that logic here.",
            "I'll show you a real-world example first. Once you see it in action, the abstract concept will click.",
            "Let's do some active learning. Instead of me explaining, try it yourself and I'll guide you if you get stuck.",
            "Good question! Before I answer, let me ask you something that'll help you discover it yourself - what patterns do you notice?"
        ]
    }
    
    return mentor_samples.get(mentor_type, mentor_samples["Encouraging Mentor"])

def simulate_exam(mentor_id: str, exam_type: str):
    """Simulate a student taking an exam and generate a nudge"""
    log_user_action(mentor_id, "EXAM_SIMULATION_REQUEST", {"exam_type": exam_type})
    
    with st.spinner(f"Simulating {exam_type} exam..."):
        # Create exam event description
        event_description = f"Event: 'student took exam', Exam: '{exam_type}', Date: '2024-10-23', Student: 'student_001', Score: 'Pending'"
        
        # Generate nudge using the nudge agent
        from agents import invoke_nudge_agent
        nudge_message = invoke_nudge_agent(mentor_id, event_description)
        
        if nudge_message and not nudge_message.startswith("Sorry, I encountered an error"):
            log_user_action(mentor_id, "EXAM_SIMULATION_SUCCESS", {
                "exam_type": exam_type,
                "nudge_length": len(nudge_message)
            })
            
            st.success(f"🎯 {exam_type} exam simulation completed!")
            st.session_state.generated_nudge = nudge_message
            st.rerun()
        else:
            log_user_action(mentor_id, "EXAM_SIMULATION_FAILED", {"exam_type": exam_type})
            st.error("❌ Failed to generate nudge message")

def create_new_session():
    """Create a new chat session"""
    mentor_id = st.session_state.current_mentor_id
    student_id = st.session_state.student_id
    
    log_user_action(mentor_id, "SESSION_CREATED", {"student_id": student_id})
    
    session_id = db.create_session(mentor_id, student_id)
    st.session_state.current_session_id = session_id
    
    st.success("✅ New session created!")
    st.rerun()

def render_chat_messages():
    """Render chat messages for current session"""
    if not st.session_state.get("current_session_id"):
        st.info("👆 Create a session in the sidebar to start chatting")
        return
    
    messages = db.get_session_messages(st.session_state.get("current_session_id"))
    
    if not messages:
        st.info("💬 No messages yet. Start the conversation!")
        return
    
    for message in messages:
        if message.sender_type == "student":
            with st.chat_message("user"):
                st.write(message.content)
        else:
            with st.chat_message("assistant"):
                st.write(message.content)
                if message.is_ai_generated:
                    st.caption("🤖 AI Generated")

def render_chat_input():
    """Render chat input and handle messages"""
    if prompt := st.chat_input("Type your message..."):
        handle_student_message(prompt)

def handle_student_message(message: str):
    """Handle incoming student message"""
    session_id = st.session_state.get("current_session_id")
    mentor_id = st.session_state.current_mentor_id
    student_id = st.session_state.student_id
    
    # Check if we have a valid session
    if not session_id:
        st.error("⚠️ Please create a session first before sending messages.")
        return
    
    # Log student message
    log_user_action(student_id, "MESSAGE_SENT", {
        "session_id": session_id,
        "message_length": len(message)
    })
    
    # Store student message
    db.add_message(session_id, "student", message)
    
    # Display student message
    with st.chat_message("user"):
        st.write(message)
    
    # Generate AI-assisted response
    handle_ai_response(session_id, student_id, mentor_id, message)
    
    st.rerun()

def handle_ai_response(session_id: str, student_id: str, mentor_id: str, message: str):
    """Handle AI response - direct response"""
    log_ai_interaction(mentor_id, student_id, "AI_RESPONSE_GENERATED", {
        "session_id": session_id
    })
    
    with st.chat_message("assistant"):
        with st.spinner("AI is generating response..."):
            ai_response = invoke_reply_agent(mentor_id, message, session_id)
            
            if ai_response and not ai_response.startswith("Sorry, I encountered an error"):
                st.write(ai_response)
                st.caption("🤖 AI Generated")
                
                # Store AI response directly
                db.add_message(session_id, "ai", ai_response, is_ai_generated=True, approval_status="approved")
            else:
                st.error("❌ Failed to generate AI response")


def main():
    """Main application function"""
    # Initialize
    init_session_state()
    db.init_database()
    
    # Header
    st.title("🎓 AI Agent Intern - Technical Assessment")
    st.markdown("**Communication Style Mimicking Agent for Mentor-Student Messaging System**")
    
    # Layout
    col1, col2 = st.columns([1, 2])
    
    with col1:
        render_sidebar()
    
    with col2:
        st.subheader("💬 Chat Interface")
        render_chat_messages()
        render_chat_input()
        

if __name__ == "__main__":
    main()

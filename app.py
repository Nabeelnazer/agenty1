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
        if st.button("Analyze My Style", help="Analyze your communication patterns"):
            analyze_mentor_style_ui(mentor_id)
        
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

def analyze_mentor_style_ui(mentor_id: str):
    """UI for mentor style analysis"""
    log_user_action(mentor_id, "STYLE_ANALYSIS_REQUEST", {})
    
    with st.spinner("Analyzing your communication style..."):
        sample_messages = [
            "Hey! Great question 👍 So basically, you need to focus on the fundamentals first. Don't worry about advanced stuff yet... master the basics!",
            "Yep, that's exactly right! You're getting it. Keep practicing and you'll be solid.",
            "No worries if you're stuck! 😅 happens to everyone. Take a break and come back to it with fresh eyes. You got this! 💪",
            "Hey! No worries, recursion can be tricky at first 😊 So basically, think of it like a function calling itself. Start with simple examples like factorial - that'll help you get the concept. Don't stress, you'll get it with practice! 💪",
            "Perfect! You're on the right track. Just remember to always have a base case - that's the key to recursion not going on forever. You got this! 🎯"
        ]
        
        style_data = analyze_mentor_style(mentor_id, sample_messages)
        
        if style_data:
            log_user_action(mentor_id, "STYLE_ANALYSIS_SUCCESS", {
                "style_characteristics": list(style_data.keys())
            })
            st.success("✅ Style analyzed successfully!")
            st.json(style_data)
        else:
            log_user_action(mentor_id, "STYLE_ANALYSIS_FAILED", {})
            st.error("❌ Failed to analyze style")

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

def render_demo_section():
    """Render the style mimicking demo section"""
    st.subheader("🎭 Style Mimicking Demo")
    
    st.markdown("""
    **This system demonstrates AI communication style mimicking:**
    
    **Mentor's Style (from sample messages):**
    - **Tone**: Casual and encouraging
    - **Common Phrases**: "Hey!", "So basically", "No worries", "You got this!"
    - **Emoji Usage**: Frequent (👍, 😅, 💪, 😊, 🎯)
    - **Teaching Approach**: Step-by-step with examples
    
    **Example Student Message:**
    > "I'm having trouble understanding recursion. Can you help?"
    
    **Expected AI Response (mimicking mentor's style):**
    > "Hey! No worries, recursion can be tricky at first 😊 So basically, think of it like a function calling itself. Start with simple examples like factorial - that'll help you get the concept. Don't stress, you'll get it with practice! 💪"
    
    **The AI captures:**
    - ✅ Casual, encouraging tone
    - ✅ Use of phrases like "Hey!", "So basically", "No worries"
    - ✅ Emoji usage (😊, 💪)
    - ✅ Shorter sentences with reassuring language
    - ✅ The mentor's supportive teaching style
    """)

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
        
        st.divider()
        render_demo_section()

if __name__ == "__main__":
    main()
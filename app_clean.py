"""
Xandy Learning AI Mentor System - Clean Production Version
Optimized for performance and maintainability
"""
import streamlit as st
import os
from datetime import datetime
from agents import (
    invoke_reply_agent, 
    analyze_mentor_style,
    generate_ai_response_with_approval
)
from database import db
from logging_config import logger, log_user_action, log_ai_interaction

# Page configuration
st.set_page_config(
    page_title="Xandy Learning - AI Mentor",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
def init_session_state():
    """Initialize session state variables"""
    defaults = {
        "current_session_id": None,
        "current_mentor_id": "mentor_001",
        "mentor_online": False,
        "student_id": "student_001"
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def render_mentor_controls():
    """Render mentor control panel"""
    with st.sidebar:
        st.header("🎯 Mentor Controls")
        
        # Mentor ID
        mentor_id = st.text_input(
            "Mentor ID", 
            value=st.session_state.current_mentor_id,
            help="Your unique mentor identifier"
        )
        st.session_state.current_mentor_id = mentor_id
        
        # Status toggle
        st.subheader("📡 Status")
        mentor_online = st.toggle(
            "I'm Online", 
            value=st.session_state.mentor_online,
            help="Toggle your availability"
        )
        
        # Log status change
        if mentor_online != st.session_state.mentor_online:
            log_user_action(mentor_id, "STATUS_CHANGE", {
                "old_status": "online" if st.session_state.mentor_online else "offline",
                "new_status": "online" if mentor_online else "offline"
            })
            st.session_state.mentor_online = mentor_online
        
        # Status indicator
        if mentor_online:
            st.success("🟢 Online - Direct responses")
        else:
            st.warning("🔴 Offline - AI responses with approval")
        
        # Style analysis
        st.subheader("🎨 Style Management")
        if st.button("Analyze My Style", help="Analyze your communication patterns"):
            analyze_mentor_style_ui(mentor_id)
        
        # Event simulation
        st.subheader("🎯 Event Simulation")
        if st.button("Simulate Student Exam", help="Simulate a student taking an exam to test nudge generation"):
            simulate_student_exam(mentor_id)
        
        # Pending approvals
        if not mentor_online:
            render_pending_approvals(mentor_id)

def analyze_mentor_style_ui(mentor_id: str):
    """UI for mentor style analysis"""
    log_user_action(mentor_id, "STYLE_ANALYSIS_REQUEST", {})
    
    with st.spinner("Analyzing your communication style..."):
        sample_messages = [
            "Hey! Great question 👍 So basically, you need to focus on the fundamentals first. Don't worry about advanced stuff yet... master the basics!",
            "Yep, that's exactly right! You're getting it. Keep practicing and you'll be solid.",
            "No worries if you're stuck! 😅 happens to everyone. Take a break and come back to it with fresh eyes. You got this! 💪"
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

def simulate_student_exam(mentor_id: str):
    """Simulate a student taking an exam and generate a nudge"""
    log_user_action(mentor_id, "EXAM_SIMULATION_REQUEST", {})
    
    with st.spinner("Simulating student exam and generating nudge..."):
        # Create exam event description
        event_description = "Event: 'student took exam', Exam: 'Python Basics Final', Date: '2024-10-23', Student: 'student_001', Score: 'Pending'"
        
        # Generate nudge using the nudge agent
        from agents import invoke_nudge_agent
        nudge_message = invoke_nudge_agent(mentor_id, event_description)
        
        if nudge_message and not nudge_message.startswith("Sorry, I encountered an error"):
            log_user_action(mentor_id, "EXAM_SIMULATION_SUCCESS", {
                "event_type": "student_exam",
                "nudge_length": len(nudge_message)
            })
            
            st.success("🎯 Exam simulation completed!")
            st.info("**Generated Nudge Message:**")
            st.write(nudge_message)
            
            # Option to add this nudge to the current session
            if st.session_state.current_session_id:
                if st.button("Add Nudge to Current Session"):
                    # Add the nudge as an AI message to the current session
                    db.add_message(
                        st.session_state.current_session_id, 
                        'ai', 
                        nudge_message, 
                        is_ai_generated=True, 
                        approval_status='approved'
                    )
                    st.success("✅ Nudge added to current session!")
                    st.rerun()
        else:
            log_user_action(mentor_id, "EXAM_SIMULATION_FAILED", {})
            st.error("❌ Failed to generate nudge message")

def render_pending_approvals(mentor_id: str):
    """Render pending AI response approvals"""
    st.subheader("⏳ Pending Approvals")
    pending_responses = db.get_pending_ai_responses(mentor_id)
    
    if pending_responses:
        st.write(f"**{len(pending_responses)} responses pending approval**")
        
        for response in pending_responses[:3]:  # Show max 3
            with st.expander(f"Response from {response['created_at'][:19]}"):
                st.write("**Student:**", response['student_message'])
                st.write("**AI Response:**", response['generated_response'])
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Approve", key=f"approve_{response['id']}"):
                        approve_response(mentor_id, response)
                
                with col2:
                    if st.button("❌ Reject", key=f"reject_{response['id']}"):
                        reject_response(mentor_id, response)
    else:
        st.info("No pending responses")

def approve_response(mentor_id: str, response: dict):
    """Approve an AI response"""
    log_user_action(mentor_id, "AI_RESPONSE_APPROVED", {
        "response_id": response['id'],
        "session_id": response['session_id']
    })
    db.approve_ai_response(response['id'], mentor_id)
    st.success("Response approved and sent!")
    st.rerun()

def reject_response(mentor_id: str, response: dict):
    """Reject an AI response"""
    log_user_action(mentor_id, "AI_RESPONSE_REJECTED", {
        "response_id": response['id'],
        "session_id": response['session_id']
    })
    db.reject_ai_response(response['id'])
    st.error("Response rejected")
    st.rerun()

def render_chat_interface():
    """Render main chat interface"""
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("💬 Chat Interface")
        
        # Student ID
        student_id = st.text_input("Student ID", value=st.session_state.student_id)
        st.session_state.student_id = student_id
        
        # Session management
        if st.button("Start New Session"):
            create_new_session(student_id, st.session_state.current_mentor_id)
        
        # Chat display
        if st.session_state.current_session_id:
            render_chat_messages()
            render_chat_input(student_id)
        else:
            st.warning("Please start a new session to begin chatting.")
    
    with col2:
        render_analytics()

def create_new_session(student_id: str, mentor_id: str):
    """Create a new chat session"""
    log_user_action(mentor_id, "SESSION_CREATE_REQUEST", {"student_id": student_id})
    
    session_id = db.create_session(student_id, mentor_id)
    st.session_state.current_session_id = session_id
    
    log_user_action(mentor_id, "SESSION_CREATED", {
        "session_id": session_id,
        "student_id": student_id
    })
    
    st.success(f"New session created: {session_id[:8]}...")

def render_chat_messages():
    """Render chat message history"""
    st.info(f"Active Session: {st.session_state.current_session_id[:8]}...")
    
    messages = db.get_session_messages(st.session_state.current_session_id)
    
    for message in messages:
        if message.sender_type == "student":
            with st.chat_message("user"):
                st.write(message.content)
        else:
            with st.chat_message("assistant"):
                st.write(message.content)
                if message.is_ai_generated:
                    st.caption("🤖 AI Generated")

def render_chat_input(student_id: str):
    """Render chat input and handle messages"""
    if prompt := st.chat_input("Type your message..."):
        handle_student_message(student_id, prompt)

def handle_student_message(student_id: str, message: str):
    """Handle incoming student message"""
    session_id = st.session_state.current_session_id
    mentor_id = st.session_state.current_mentor_id
    
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
    
    # Generate response
    if st.session_state.mentor_online:
        handle_mentor_response(session_id, student_id, mentor_id)
    else:
        handle_ai_response(session_id, student_id, mentor_id, message)
    
    st.rerun()

def handle_mentor_response(session_id: str, student_id: str, mentor_id: str):
    """Handle direct mentor response"""
    log_user_action(mentor_id, "MENTOR_RESPONSE_GENERATED", {
        "session_id": session_id,
        "student_id": student_id
    })
    
    with st.chat_message("assistant"):
        with st.spinner("Mentor is typing..."):
            # Simulated mentor response
            mentor_response = "Thanks for your message! I'm here to help. Let me think about this..."
            st.write(mentor_response)
            st.caption("👨‍🏫 Mentor Response")
    
    # Store mentor response
    db.add_message(session_id, "mentor", mentor_response)

def handle_ai_response(session_id: str, student_id: str, mentor_id: str, message: str):
    """Handle AI response with approval workflow"""
    log_ai_interaction(mentor_id, student_id, "AI_RESPONSE_QUEUED", {
        "session_id": session_id
    })
    
    with st.chat_message("assistant"):
        with st.spinner("AI is generating response..."):
            queue_id, ai_response = generate_ai_response_with_approval(
                mentor_id, message, session_id
            )
            
            st.write(ai_response)
            st.caption("🤖 AI Generated - Pending Approval")
            st.info("This response is waiting for mentor approval before being sent to the student.")

def render_analytics():
    """Render session analytics"""
    st.subheader("📊 Session Analytics")
    
    if st.session_state.current_session_id:
        messages = db.get_session_messages(st.session_state.current_session_id)
        
        # Basic metrics
        student_messages = len([m for m in messages if m.sender_type == "student"])
        mentor_messages = len([m for m in messages if m.sender_type == "mentor"])
        ai_messages = len([m for m in messages if m.sender_type == "ai"])
        
        st.metric("Student Messages", student_messages)
        st.metric("Mentor Messages", mentor_messages)
        st.metric("AI Messages", ai_messages)
        
        # Message timeline
        if messages:
            st.subheader("📈 Recent Messages")
            for msg in messages[-5:]:
                timestamp = msg.created_at[:19]
                sender = "👤" if msg.sender_type == "student" else "🤖" if msg.is_ai_generated else "👨‍🏫"
                st.write(f"{sender} {timestamp}: {msg.content[:50]}...")
    
    # System status
    st.subheader("🔧 System Status")
    st.info("Database: Connected")
    st.info(f"Mentor Status: {'Online' if st.session_state.mentor_online else 'Offline'}")
    st.info("AI Model: Gemini 2.5 Flash")

def main():
    """Main application entry point"""
    logger.info("Starting Xandy Learning AI Mentor System")
    
    # Initialize session state
    init_session_state()
    
    # Render UI
    st.title("🎓 Xandy Learning - AI Mentor System")
    st.caption("Hybrid AI-Human mentor system with session management and approval workflow")
    
    # Render components
    render_mentor_controls()
    render_chat_interface()

if __name__ == "__main__":
    main()



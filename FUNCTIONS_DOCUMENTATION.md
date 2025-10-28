# Function Documentation - AI Agent Assessment System

## 📋 Complete Function Reference

This document explains every function in the system, its purpose, scope, and how it fits into the overall architecture.

---

## 🧠 `agents.py` - AI Agent Functions

### 1. `configure_gemini()`
**Purpose:** Initialize and configure the Google Gemini API  
**Scope:** System initialization  
**What it does:**
- Loads the `GEMINI_API_KEY` from environment variables
- Configures the Gemini API client
- Validates the API key exists
- Logs initialization status
- Stops execution if API key is missing

**Called by:** Module initialization (runs automatically when agents.py is imported)  
**Returns:** `True` if successful, stops execution if fails

---

### 2. `summarize_student_journey(chat_history: str) -> str`
**Purpose:** Analyze chat history to understand the student's learning journey  
**Scope:** Context awareness and memory  
**What it does:**
- Takes the entire conversation history as input
- Uses AI to analyze:
  - Current topic student is learning
  - Past struggles they've had
  - Recent successes they've achieved
- Returns a 1-2 sentence summary of the student's journey
- Logs performance metrics

**Called by:** `invoke_reply_agent()` when generating context-aware responses  
**Returns:** String summary of student's learning journey  
**Example output:** *"Student started with variables, struggled with indexing, but mastered list creation. Now learning functions."*

---

### 3. `invoke_reply_agent(mentor_id, student_message, session_id, mentor_style=None, student_context=None) -> str`
**Purpose:** Generate AI responses that mimic mentor's style AND remember context  
**Scope:** Core AI response generation with dual-analysis  
**What it does:**
1. Retrieves mentor's communication style from database (if not provided)
2. Gets conversation history from session
3. **Dual-Analysis:**
   - Analyzes HOW to talk (style)
   - Summarizes WHAT to remember (context)
4. Generates response using both style and context
5. Logs performance metrics

**Called by:** `handle_ai_response()` in app.py  
**Returns:** String response from AI  
**Key Feature:** Can reference previous topics (e.g., "Just like when you learned variables...")

---

### 4. `invoke_nudge_agent(mentor_id, event_description, mentor_style=None) -> str`
**Purpose:** Generate proactive follow-up messages based on events  
**Scope:** Event-based nudging system  
**What it does:**
- Takes an event description (e.g., "student took exam")
- Retrieves mentor's communication style
- Generates a proactive message in mentor's style
- Logs performance metrics

**Called by:** `simulate_exam()` in app.py  
**Returns:** String nudge message  
**Example:** *"Hey! How did the Python exam go? I hope the variables we covered made sense! 😊"*

---

### 5. `analyze_mentor_style(mentor_id, sample_messages: List[str]) -> Dict`
**Purpose:** Analyze communication patterns from sample messages  
**Scope:** Style learning and analysis  
**What it does:**
1. Takes list of mentor's sample messages
2. Uses AI to extract communication patterns:
   - Tone (casual/formal/encouraging/direct)
   - Common phrases
   - Emoji usage
   - Message length and structure
   - Teaching approach
   - Punctuation style
3. Saves style profile to database
4. Returns analysis as JSON dictionary

**Called by:** `analyze_mentor_style_ui()` in app.py  
**Returns:** Dictionary with style characteristics  
**Example output:** 
```json
{
  "tone": "encouraging",
  "common_phrases": ["Great question!", "Let's work through it"],
  "emoji_usage": "frequent",
  "teaching_approach": "socratic"
}
```

---

## 🖥️ `app.py` - User Interface Functions

### 1. `init_session_state()`
**Purpose:** Initialize Streamlit session state variables  
**Scope:** Application initialization  
**What it does:**
- Sets up default values for:
  - `current_session_id` - Tracks active chat session
  - `current_mentor_id` - Mentor identifier
  - `student_id` - Student identifier
- Prevents errors by ensuring variables exist before use

**Called by:** `main()` at startup  
**Returns:** None (modifies session state)

---

### 2. `render_sidebar()`
**Purpose:** Display the sidebar controls and options  
**Scope:** UI rendering  
**What it does:**
- Renders mentor ID input
- Shows mentor personality type selector
- Displays "Analyze Style" button
- Shows session management buttons (New Session, Load Demo)
- Displays event simulation buttons (Python/Math exam)
- Shows generated nudges if available

**Called by:** `main()` to render sidebar  
**Returns:** None (renders UI)

---

### 3. `analyze_mentor_style_ui(mentor_id, mentor_type)`
**Purpose:** UI wrapper for mentor style analysis  
**Scope:** Style analysis interface  
**What it does:**
- Gets sample messages for selected mentor type
- Calls `analyze_mentor_style()` from agents.py
- Displays analysis results as JSON
- Shows success/failure messages
- Logs user actions

**Called by:** "Analyze Style" button click  
**Returns:** None (displays results in UI)

---

### 4. `get_mentor_sample_messages(mentor_type: str) -> list`
**Purpose:** Provide sample messages for each mentor personality type  
**Scope:** Data provision for style analysis  
**What it does:**
- Returns 5 sample messages for selected mentor type
- Each type has distinct characteristics:
  - **Encouraging**: Warm, emojis, Socratic questions
  - **Direct**: No emojis, concise, mastery learning
  - **Academic**: Formal language, pedagogical terms
  - **Casual**: Conversational, analogies, informal

**Called by:** `analyze_mentor_style_ui()`  
**Returns:** List of 5 sample messages

---

### 5. `simulate_exam(mentor_id, exam_type)`
**Purpose:** Simulate student exam completion and generate nudge  
**Scope:** Event-based nudging demonstration  
**What it does:**
- Creates exam event description
- Calls `invoke_nudge_agent()` to generate follow-up message
- Stores nudge in session state
- Logs simulation events

**Called by:** Python/Math exam buttons  
**Returns:** None (stores nudge for display)

---

### 6. `get_demo_conversations(mentor_type: str) -> list`
**Purpose:** Provide pre-loaded demo conversations  
**Scope:** Demo data for showing context awareness  
**What it does:**
- Returns realistic multi-turn conversations
- Each conversation shows mentor's unique style
- Demonstrates student's learning journey
- Shows progression from struggle to success

**Called by:** `load_demo_conversation()`  
**Returns:** List of message dictionaries

---

### 7. `load_demo_conversation(mentor_id, mentor_type)`
**Purpose:** Load pre-built conversation into database  
**Scope:** Demo feature for showcasing system capabilities  
**What it does:**
1. Creates new chat session
2. Gets demo conversation for mentor type
3. Loads all messages into database
4. User can then ask new questions
5. AI responds using:
   - Style learned from conversation
   - Context from conversation history

**Called by:** "Load Demo" button click  
**Returns:** None (creates session with demo messages)  
**Key Benefit:** Shows AI analyzing REAL conversations, not just hardcoded examples

---

### 8. `create_new_session()`
**Purpose:** Create a new empty chat session  
**Scope:** Session management  
**What it does:**
- Creates new session in database
- Stores session ID in session state
- Logs session creation
- Displays success message

**Called by:** "New Session" button click  
**Returns:** None (creates session and reruns app)

---

### 9. `render_chat_messages()`
**Purpose:** Display all messages in current session  
**Scope:** Chat UI rendering  
**What it does:**
- Retrieves all messages from current session
- Displays student messages on right (user bubble)
- Displays mentor/AI messages on left (assistant bubble)
- Shows "🤖 AI Generated" label for AI messages

**Called by:** `main()` to render chat history  
**Returns:** None (renders messages)

---

### 10. `render_chat_input()`
**Purpose:** Display chat input field and handle user input  
**Scope:** Message handling  
**What it does:**
- Shows text input field at bottom
- Captures user's message
- Calls `handle_student_message()` when user submits

**Called by:** `main()` to render input field  
**Returns:** None (handles input)

---

### 11. `handle_student_message(message: str)`
**Purpose:** Process incoming student messages  
**Scope:** Message processing and AI response triggering  
**What it does:**
1. Validates session exists
2. Logs student message
3. Stores message in database
4. Displays message in chat
5. Triggers AI response generation
6. Reruns app to show new messages

**Called by:** `render_chat_input()` when user sends message  
**Returns:** None (processes message and generates response)

---

### 12. `handle_ai_response(session_id, student_id, mentor_id, message)`
**Purpose:** Generate and store AI response  
**Scope:** AI response generation  
**What it does:**
1. Calls `invoke_reply_agent()` with dual-analysis
2. Generates response using:
   - Mentor's communication style
   - Student's learning journey context
3. Displays response in chat
4. Stores response in database
5. Shows error if generation fails

**Called by:** `handle_student_message()`  
**Returns:** None (generates and displays response)

---

### 13. `main()`
**Purpose:** Main application entry point  
**Scope:** Application orchestration  
**What it does:**
- Initializes session state
- Initializes database
- Sets up page layout
- Calls all render functions:
  - `render_sidebar()`
  - `render_chat_messages()`
  - `render_chat_input()`

**Called by:** Streamlit when app runs  
**Returns:** None (runs entire application)

---

## 🗄️ `database.py` - Database Functions (Key Ones)

### 1. `create_session(student_id, mentor_id) -> str`
**Purpose:** Create new chat session in database  
**Returns:** Session ID

### 2. `add_message(session_id, sender_type, content, is_ai_generated, approval_status) -> str`
**Purpose:** Store a message in database  
**Returns:** Message ID

### 3. `get_session_messages(session_id) -> List[Message]`
**Purpose:** Retrieve all messages from a session  
**Returns:** List of Message objects

### 4. `get_session_context(session_id) -> str`
**Purpose:** Get formatted chat history for AI context  
**Returns:** String of formatted messages

### 5. `get_session(session_id) -> ChatSession`
**Purpose:** Retrieve session details  
**Returns:** ChatSession object

### 6. `get_mentor_style(mentor_id) -> MentorStyle`
**Purpose:** Retrieve saved mentor communication style  
**Returns:** MentorStyle object with analysis

### 7. `save_mentor_style(mentor_id, style_data, sample_messages, confidence_score) -> str`
**Purpose:** Save analyzed mentor style to database  
**Returns:** Style ID

---

## 🔄 System Flow - How Functions Work Together

### **Scenario 1: Loading Demo Conversation**
```
User clicks "Load Demo"
  → load_demo_conversation()
  → create_session()
  → get_demo_conversations()
  → add_message() [for each demo message]
  → Display loaded conversation
```

### **Scenario 2: Student Sends Message**
```
Student types message
  → handle_student_message()
  → add_message() [store student message]
  → handle_ai_response()
  → invoke_reply_agent()
      → get_mentor_style() [retrieve style]
      → get_session_context() [retrieve history]
      → summarize_student_journey() [analyze context]
      → Generate AI response [with style + context]
  → add_message() [store AI response]
  → Display in chat
```

### **Scenario 3: Exam Simulation**
```
User clicks "Python Exam"
  → simulate_exam()
  → invoke_nudge_agent()
      → get_mentor_style() [retrieve style]
      → Generate nudge message [in mentor's style]
  → Store nudge in session state
  → Display in sidebar
```

---

## 🎯 Key System Capabilities

### **Dual-Analysis System** 🧠
- **Style Analysis** (HOW to talk) - Uses `analyze_mentor_style()`
- **Context Analysis** (WHAT to remember) - Uses `summarize_student_journey()`

### **Context Awareness** 📚
- AI remembers student's journey through conversations
- References previous topics and successes
- Builds on past struggles

### **Style Mimicking** 🎭
- 4 distinct mentor personalities
- Learns tone, phrases, emoji usage, structure
- Generates authentic responses

### **Event-Based Nudging** 🎯
- Proactive follow-up messages
- Context-aware nudges
- Maintains mentor's style

---

## 📊 For Interview Questions

### **"What does your system do?"**
*"It's a communication style mimicking agent that learns from mentor-student conversations and generates responses that match the mentor's unique style while maintaining context awareness of the student's learning journey."*

### **"How does it work?"**
*"It uses a dual-analysis system: first, it analyzes HOW the mentor communicates (style), then WHAT the student has been learning (context). It combines both to generate authentic, context-aware responses."*

### **"What's special about your approach?"**
*"Unlike simple chatbots, my system separates style from content. It can learn 4 distinct mentor personalities - from emoji-heavy encouraging mentors to formal academic mentors - and adapts accordingly while remembering the entire student journey."*

### **"How do you handle context?"**
*"I implemented a context summarization function that analyzes the entire conversation history and extracts the student's current topic, past struggles, and recent successes. This allows the AI to reference previous topics naturally."*

### **"Can you show me it working?"**
*"Yes! Click 'Load Demo' to see pre-loaded conversations for each mentor type. Then ask a question and watch the AI respond in that exact style while referencing the conversation context."*

---

## 🎓 Technical Terms You Should Know

- **Dual-Analysis:** Separating style analysis from context analysis
- **Style Fingerprinting:** Creating a unique profile of communication patterns
- **Context Awareness:** Remembering and referencing conversation history
- **Session Management:** Tracking conversations and maintaining state
- **Event-Based Nudging:** Proactive messages triggered by student actions
- **Socratic Method:** Teaching through questions rather than direct answers
- **Scaffolding:** Building from simple to complex concepts progressively
- **Zone of Proximal Development:** Teaching at the optimal challenge level

---

## 💡 Key Differentiators

1. **Multiple Personality Types** - Not just one generic style
2. **Real Context Memory** - Not just recent messages, but entire journey
3. **Evidence-Based Teaching** - Grounded in actual pedagogical theory
4. **Demo Conversations** - Immediate demonstration without setup
5. **Production-Ready** - Clean code, logging, error handling

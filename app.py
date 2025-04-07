import os
import json
import streamlit as st
from datetime import datetime
import time

from agent_marketplace.agents.personal_ai import PersonalAI
from agent_marketplace.agents.health_agent import HealthAgent
from agent_marketplace.schemas.agents import Message
from agent_marketplace.config import setup_streamlit, response_generator

# Set up the page configuration with a wider layout
st.set_page_config(
    page_title="AI Health Assistant",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for modern styling
st.markdown("""
<style>
    /* Global theme colors */
    :root {
        --primary: #3B82F6;
        --primary-light: #60A5FA;
        --success: #10B981;
        --warning: #F59E0B;
        --danger: #EF4444;
        --dark: #111827;
        --dark-lighter: #1F2937;
        --gray: #6B7280;
        --light: #F3F4F6;
    }

    /* Main container styling */
    .main {
        background-color: var(--dark);
        color: var(--light);
        padding: 2rem;
        max-width: 1200px;
        margin: 0 auto;
    }
    
    /* Header styling */
    .stTitle {
        color: white !important;
        font-size: 2.5rem !important;
        font-weight: 800 !important;
        letter-spacing: -0.025em !important;
        line-height: 1.25 !important;
        margin-bottom: 0.5rem !important;
        font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    
    .stSubheader {
        color: var(--primary-light) !important;
        font-size: 1.25rem !important;
        font-weight: 500 !important;
        margin-bottom: 2rem !important;
        opacity: 0.9;
    }
    
    /* Chat container styling */
    .stChatMessage {
        background-color: var(--dark-lighter) !important;
        border-radius: 16px !important;
        padding: 1.25rem !important;
        margin: 1rem 0 !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06) !important;
        backdrop-filter: blur(10px) !important;
    }
    
    /* Message content styling */
    .stChatMessage p {
        color: var(--light) !important;
        line-height: 1.6 !important;
        margin: 0 !important;
    }
    
    /* User message styling */
    .stChatMessage [data-testid="chatAvatarIcon-user"] {
        background-color: var(--primary) !important;
        border: 2px solid rgba(255, 255, 255, 0.1) !important;
    }
    
    /* Assistant message styling */
    .stChatMessage [data-testid="chatAvatarIcon-assistant"] {
        background-color: var(--success) !important;
        border: 2px solid rgba(255, 255, 255, 0.1) !important;
    }
    
    /* Input box styling */
    .stChatInputContainer {
        padding: 1rem !important;
        background-color: var(--dark-lighter) !important;
        border-radius: 16px !important;
        margin-top: 1rem !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }
    
    .stTextInput > div > div > input {
        background-color: var(--dark) !important;
        color: white !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        padding: 1rem !important;
        font-size: 1rem !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1) !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2) !important;
    }
    
    .stTextInput > div > div > input::placeholder {
        color: var(--gray) !important;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: var(--dark-lighter) !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: white !important;
        font-weight: 500 !important;
    }
    
    .streamlit-expanderContent {
        background-color: var(--dark) !important;
        border-radius: 0 0 12px 12px !important;
    }
    
    /* Status badges */
    .status-badge {
        padding: 0.5rem 1rem !important;
        border-radius: 9999px !important;
        font-size: 0.875rem !important;
        font-weight: 500 !important;
        display: inline-flex !important;
        align-items: center !important;
        gap: 0.5rem !important;
        margin: 0.25rem !important;
        background-color: rgba(255, 255, 255, 0.1) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: white !important;
        backdrop-filter: blur(10px) !important;
    }
    
    /* Welcome box styling */
    .welcome-box {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(16, 185, 129, 0.1)) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 16px !important;
        padding: 1.5rem !important;
        margin-bottom: 2rem !important;
        backdrop-filter: blur(10px) !important;
    }
    
    .welcome-box h4 {
        color: white !important;
        font-size: 1.25rem !important;
        font-weight: 600 !important;
        margin-bottom: 0.75rem !important;
    }
    
    .welcome-box p {
        color: var(--light) !important;
        font-size: 1rem !important;
        line-height: 1.6 !important;
        margin: 0 !important;
        opacity: 0.9;
    }
    
    /* Consultation history styling */
    .consultation-message {
        background-color: rgba(255, 255, 255, 0.05) !important;
        border-radius: 12px !important;
        padding: 1rem !important;
        margin: 0.75rem 0 !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }
    
    .consultation-message strong {
        color: var(--primary-light) !important;
        font-weight: 600 !important;
    }
    
    .consultation-message p {
        color: var(--light) !important;
        margin-top: 0.5rem !important;
        line-height: 1.6 !important;
        opacity: 0.9;
    }
    
    /* Footer styling */
    .footer {
        text-align: center !important;
        padding: 2rem !important;
        color: var(--gray) !important;
        font-size: 0.875rem !important;
        border-top: 1px solid rgba(255, 255, 255, 0.1) !important;
        margin-top: 2rem !important;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Scrollbar styling */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--dark);
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--dark-lighter);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--gray);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "health_chat" not in st.session_state:
    st.session_state.health_chat = []

# Load Nicholas's health data
def load_health_data():
    try:
        # Path to Nicholas's health data
        health_data_path = "data/personal_data/Nicholas Richmond/sample_health_data.json"
        if os.path.exists(health_data_path):
            with open(health_data_path, 'r') as file:
                return json.load(file)
        else:
            st.error(f"Health data file not found at {health_data_path}")
            return None
    except Exception as e:
        st.error(f"Error loading health data: {str(e)}")
        return None

# Get the health data
health_data = load_health_data()

# Create a modern header with status indicators
col1, col2 = st.columns([2, 1])
with col1:
    st.title("🏥 Vitality - Your AI Health Assistant")
    st.subheader("Your Personal AI Health Companion")

with col2:
    if st.session_state.get("agents_initialized"):
        st.markdown("""
            <div style='text-align: right; padding: 1rem;'>
                <div class='status-badge'>
                    <span style='color: #10B981;'>●</span> AI Agents Ready
                </div>
                <div class='status-badge'>
                    <span style='color: #3B82F6;'>●</span> Health Data Loaded
                </div>
            </div>
        """, unsafe_allow_html=True)

# Create a modern info box
if not st.session_state.get("intro_dismissed"):
    with st.container():
        col1, col2, col3 = st.columns([0.85, 0.1, 0.05])
        with col1:
            st.markdown("""
                <div class='welcome-box'>
                    <h4>👋 Welcome to Your Health Assistant</h4>
                    <p>
                        I'm your personal AI assistant, and I work with a specialized health expert to help you understand and improve your health. 
                        Feel free to ask me anything about your health data!
                    </p>
                </div>
            """, unsafe_allow_html=True)
        with col3:
            if st.button("×", key="dismiss_intro"):
                st.session_state.intro_dismissed = True
                st.rerun()

# Get the health data
health_data = load_health_data()

if "agents_initialized" not in st.session_state:
    # Initialize the agents only once
    try:
        # Create Personal AI Agent
        personal_ai = PersonalAI(
            name="Nicholas's Personal AI",
            owner="Nicholas Richmond",
            description="A personal AI assistant that helps Nicholas with his needs and communicates with specialized agents on his behalf.",
            user_intent="Help Nicholas understand his health data and provide recommendations."
        )
        
        # Create Health Agent
        health_agent = HealthAgent(
            name="Health Specialist",
            owner="Health Services",
            description="A specialized health assistant that can analyze health data and provide personalized recommendations.",
            user_intent="Analyze Nicholas's health data and provide actionable insights and recommendations."
        )
        
        # If health data is loaded, update the health agent's profile
        if health_data:
            # Extract relevant health data for the agent
            try:
                # Get the latest blood tests
                latest_blood_test = health_data.get("bloodTests", [])[0] if health_data.get("bloodTests") else {}
                latest_glucose = latest_blood_test.get("results", {}).get("glucose", {})
                
                # Get the latest vitals
                latest_vitals = health_data.get("vitals", [])[0] if health_data.get("vitals") else {}
                
                # Get medical history
                medical_history = health_data.get("medicalHistory", {})
                
                # Update health agent's health profile
                health_agent.health_profile = {
                    "goals": [],
                    "dietary_restrictions": [],
                    "current_metrics": {
                        "glucose": latest_glucose,
                        "cholesterol": {
                            "total": latest_blood_test.get("results", {}).get("cholesterolTotal", {}),
                            "hdl": latest_blood_test.get("results", {}).get("cholesterolHDL", {}),
                            "ldl": latest_blood_test.get("results", {}).get("cholesterolLDL", {})
                        },
                        "blood_pressure": latest_vitals.get("bloodPressure", {}),
                        "heart_rate": latest_vitals.get("heartRate", {}),
                        "vitaminD": latest_blood_test.get("results", {}).get("vitaminD", {})
                    },
                    "medical_history": {
                        "conditions": medical_history.get("conditions", []),
                        "medications": medical_history.get("medications", [])
                    },
                    "complete_health_data": health_data  # Store the complete health data
                }
                
                st.write("Health data loaded successfully!")
            except Exception as e:
                st.error(f"Error processing health data: {str(e)}")
        
        st.session_state.personal_ai = personal_ai
        st.session_state.health_agent = health_agent
        st.session_state.agents_initialized = True
    except Exception as e:
        st.error(f"Error initializing agents: {str(e)}")
        st.session_state.agents_initialized = False

# Display chat history with modern styling
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Modern input area
user_query = st.chat_input("💬 Ask me about your health data...")

# Process user input
if user_query and st.session_state.agents_initialized:
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)
    
    # Create a container for the livestream conversation
    livestream_container = st.container()
    
    # Create a container for the final response
    response_container = st.container()
    
    try:
        # Get our agents from session state
        personal_ai = st.session_state.personal_ai
        health_agent = st.session_state.health_agent
        
        # Initialize chat between agents
        personal_ai.init_chat(guest_agent=health_agent)
        health_agent.init_chat(guest_agent=personal_ai)
        
        # Clear previous health chat
        st.session_state.health_chat = []
        
        # Ensure health data is available in each query
        if health_data:
            # Create a specific prompt based on the query
            specific_health_data = ""
            
            # Add relevant health data based on query keywords
            if "glucose" in user_query.lower() or "sugar" in user_query.lower() or "diabetes" in user_query.lower():
                try:
                    latest_blood_test = health_data.get("bloodTests", [])[0]
                    previous_blood_test = health_data.get("bloodTests", [])[1] if len(health_data.get("bloodTests", [])) > 1 else None
                    
                    latest_glucose = latest_blood_test.get("results", {}).get("glucose", {})
                    previous_glucose = previous_blood_test.get("results", {}).get("glucose", {}) if previous_blood_test else None
                    
                    specific_health_data += f"""
                    IMPORTANT: Please use Nicholas's actual glucose data in your response:
                    
                    Latest Glucose Reading (Date: {latest_blood_test.get('date')}):
                    - Value: {latest_glucose.get('value')} {latest_glucose.get('unit')}
                    - Normal Range: {latest_glucose.get('normalRange')}
                    - Status: {latest_glucose.get('status')}
                    """
                    
                    if previous_glucose:
                        specific_health_data += f"""
                        Previous Glucose Reading (Date: {previous_blood_test.get('date')}):
                        - Value: {previous_glucose.get('value')} {previous_glucose.get('unit')}
                        - Normal Range: {previous_glucose.get('normalRange')}
                        - Status: {previous_glucose.get('status')}
                        """
                    
                    # Add family history of diabetes if available
                    family_history = health_data.get("medicalHistory", {}).get("familyHistory", {})
                    if family_history:
                        for parent, conditions in family_history.items():
                            for condition in conditions:
                                if "diabetes" in condition.get("condition", "").lower():
                                    specific_health_data += f"\nFamily History: {parent.capitalize()} has {condition.get('condition')} (onset age: {condition.get('onsetAge')})"
                except Exception as e:
                    st.error(f"Error extracting glucose data: {str(e)}")
            
            # Add analogous sections for other health metrics (cholesterol, blood pressure, etc.)
            elif "cholesterol" in user_query.lower() or "lipid" in user_query.lower():
                try:
                    latest_blood_test = health_data.get("bloodTests", [])[0]
                    
                    cholesterol_total = latest_blood_test.get("results", {}).get("cholesterolTotal", {})
                    cholesterol_hdl = latest_blood_test.get("results", {}).get("cholesterolHDL", {})
                    cholesterol_ldl = latest_blood_test.get("results", {}).get("cholesterolLDL", {})
                    triglycerides = latest_blood_test.get("results", {}).get("triglycerides", {})
                    
                    specific_health_data += f"""
                    IMPORTANT: Please use Nicholas's actual cholesterol data in your response:
                    
                    Latest Cholesterol Readings (Date: {latest_blood_test.get('date')}):
                    - Total Cholesterol: {cholesterol_total.get('value')} {cholesterol_total.get('unit')} (Normal Range: {cholesterol_total.get('normalRange')}, Status: {cholesterol_total.get('status')})
                    - HDL Cholesterol: {cholesterol_hdl.get('value')} {cholesterol_hdl.get('unit')} (Normal Range: {cholesterol_hdl.get('normalRange')}, Status: {cholesterol_hdl.get('status')})
                    - LDL Cholesterol: {cholesterol_ldl.get('value')} {cholesterol_ldl.get('unit')} (Normal Range: {cholesterol_ldl.get('normalRange')}, Status: {cholesterol_ldl.get('status')})
                    - Triglycerides: {triglycerides.get('value')} {triglycerides.get('unit')} (Normal Range: {triglycerides.get('normalRange')}, Status: {triglycerides.get('status')})
                    """
                except Exception as e:
                    st.error(f"Error extracting cholesterol data: {str(e)}")
            
            elif "blood pressure" in user_query.lower() or "hypertension" in user_query.lower():
                try:
                    latest_vitals = health_data.get("vitals", [])[0]
                    blood_pressure = latest_vitals.get("bloodPressure", {})
                    
                    specific_health_data += f"""
                    IMPORTANT: Please use Nicholas's actual blood pressure data in your response:
                    
                    Latest Blood Pressure Reading (Date: {latest_vitals.get('date')}):
                    - Systolic: {blood_pressure.get('systolic')} mmHg
                    - Diastolic: {blood_pressure.get('diastolic')} mmHg
                    - Status: {blood_pressure.get('status')}
                    
                    Medical Condition:
                    """
                    
                    # Add hypertension status if available
                    for condition in health_data.get("medicalHistory", {}).get("conditions", []):
                        if "hypertension" in condition.get("name", "").lower():
                            specific_health_data += f"- {condition.get('name')} (Diagnosed: {condition.get('diagnosedDate')}, Status: {condition.get('status')})"
                            
                    # Add medications
                    for medication in health_data.get("medicalHistory", {}).get("medications", []):
                        if "hypertension" in medication.get("purpose", "").lower():
                            specific_health_data += f"\n- Medication: {medication.get('name')} {medication.get('dosage')} {medication.get('frequency')}"
                except Exception as e:
                    st.error(f"Error extracting blood pressure data: {str(e)}")
            
            elif "vitamin d" in user_query.lower():
                try:
                    latest_blood_test = health_data.get("bloodTests", [])[0]
                    vitamin_d = latest_blood_test.get("results", {}).get("vitaminD", {})
                    
                    specific_health_data += f"""
                    IMPORTANT: Please use Nicholas's actual Vitamin D data in your response:
                    
                    Latest Vitamin D Reading (Date: {latest_blood_test.get('date')}):
                    - Value: {vitamin_d.get('value')} {vitamin_d.get('unit')}
                    - Normal Range: {vitamin_d.get('normalRange')}
                    - Status: {vitamin_d.get('status')}
                    """
                    
                    # Add vitamin D supplement if available
                    for medication in health_data.get("medicalHistory", {}).get("medications", []):
                        if "vitamin d" in medication.get("name", "").lower():
                            specific_health_data += f"\n- Supplement: {medication.get('name')} {medication.get('dosage')} {medication.get('frequency')} (Started: {medication.get('startDate')})"
                except Exception as e:
                    st.error(f"Error extracting Vitamin D data: {str(e)}")
            
            else:
                # For general health queries, include a comprehensive overview
                specific_health_data += """
                IMPORTANT: Please use Nicholas's actual health data in your response, including:
                
                1. Latest glucose levels (value, normal range, and status)
                2. Cholesterol levels (total, HDL, LDL, triglycerides)
                3. Blood pressure readings
                4. Vitamin D levels
                5. Any medical conditions like hypertension
                6. Current medications and supplements
                
                Based on this data, provide specific, actionable health recommendations.
                """
        
        # Personal AI sends the first message to Health Agent with specific health data
        initial_message = Message(
            role="user", 
            content=f"I need help with the following health query from my owner: {user_query}\n\n{specific_health_data if health_data else ''}", 
            sender=personal_ai.name, 
            receiver=health_agent.name, 
            timestamp=datetime.now()
        )
        
        # Save the message to health chat history
        st.session_state.health_chat.append({
            "sender": initial_message.sender,
            "content": initial_message.content,
            "timestamp": str(initial_message.timestamp)
        })
        
        # Show the first message in the livestream
        with livestream_container:
            st.markdown("""
                <div class='welcome-box' style='margin-bottom: 1rem;'>
                    <h4>🔄 Live Consultation</h4>
                    <p>Watch as I consult with the health specialist in real-time</p>
                </div>
            """, unsafe_allow_html=True)
            st.markdown(f"**{initial_message.sender}**: {initial_message.content}")
        
        # Start the conversation between agents
        current_message = initial_message
        current_sender = personal_ai
        current_receiver = health_agent
        
        # Exchange messages between agents (max 5 rounds)
        max_rounds = 5
        round_count = 0
        
        while round_count < max_rounds:
            # Get response from current receiver
            response = current_receiver.on_message(current_message, sender=current_sender)
            
            # Save response to health chat history
            st.session_state.health_chat.append({
                "sender": response.sender,
                "content": response.content,
                "timestamp": str(response.timestamp)
            })
            
            # Show the response in the livestream
            with livestream_container:
                st.markdown(f"**{response.sender}**: {response.content}")
                # Add a small delay to simulate the conversation happening
                time.sleep(0.5)
            
            # Check if task is complete
            if current_receiver.task_complete or "[CONVERSATION_ENDS]" in response.content:
                break
            
            # Swap sender and receiver for next round
            current_message = response
            temp = current_sender
            current_sender = current_receiver
            current_receiver = temp
            
            round_count += 1
        
        # Generate a summary response for the user based on the AI conversation
        summary_prompt = f"""
        As the personal AI assistant for Nicholas Richmond, provide a helpful summary of your consultation with the health specialist.
        The original user query was: "{user_query}"
        
        Health chat transcript:
        {json.dumps(st.session_state.health_chat, indent=2)}
        
        Provide a helpful, conversational summary of the health information and advice to answer the user's query.
        Make the response sound like you are Nicholas's helpful personal AI assistant.
        """
        
        # Generate a response using the personal AI's LLM
        summary_response = personal_ai.llm.generate(prompt=summary_prompt)
        final_response = summary_response["content"]
        
        # Display the final response in chat
        with st.chat_message("assistant"):
            st.markdown(final_response)
        
        # Save assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": final_response})
        
    except Exception as e:
        # Handle any errors
        error_message = f"I encountered an issue while processing your request: {str(e)}"
        with st.chat_message("assistant"):
            st.markdown(error_message)
        st.session_state.messages.append({"role": "assistant", "content": error_message})
elif user_query and not st.session_state.agents_initialized:
    st.error("Unable to process your request. Agents could not be initialized.")

# Update the expander styling
with st.expander("📋 View Full AI Consultation History"):
    if st.session_state.health_chat:
        for msg in st.session_state.health_chat:
            st.markdown(f"""
                <div class='consultation-message'>
                    <strong>{msg["sender"]}</strong>
                    <p>{msg["content"]}</p>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No health consultation yet. Start by asking a question!")

# Add a footer
st.markdown("""
    <div class='footer'>
        <p>Your health data is private and secure. Consultations are end-to-end encrypted.</p>
        <p style='margin-top: 0.5rem; opacity: 0.7;'>© 2024 AI Health Assistant | Privacy Policy | Terms of Service</p>
    </div>
""", unsafe_allow_html=True) 
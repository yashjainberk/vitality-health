"""
Demo simulation for user chat with a Personal AI agent that then chats with a Health agent.

This simulates the entire interaction in a Streamlit UI without requiring user input.
"""
import os
import json
from typing import List, Dict, Any
import streamlit as st

from agent_marketplace.marketplace import AgentMarketplace
from agent_marketplace.agents.personal_ai import PersonalAI
from agent_marketplace.agents.health_agent import HealthAgent
from agent_marketplace.schemas.agents import Message
from agent_marketplace.config import response_generator


def run_chat(user_name: str, user_message: str):
    """Run the simulated chat with the given parameters."""
    # Check for sample health data
    health_data_file = os.path.join(os.path.dirname(__file__), "..", "data", "personal_data", user_name, "sample_health_data.json")
    if os.path.exists(health_data_file):
        st.sidebar.success(f"Found sample health data for {user_name}")
    else:
        st.sidebar.warning(f"No sample health data found for {user_name}. Creating directory if needed.")
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(health_data_file), exist_ok=True)

    # Placeholder for agent chat log
    agent_chat_container = st.container()

    # 1. Initialize personal AI agent
    personal_ai = PersonalAI(
        name=f"{user_name}'s Personal AI",
        owner=user_name,
        description="A personal AI agent that can help with tasks and provide information",
        user_intent=user_message,  # Set from the beginning
        model_config={
            "model": "openai:gpt-4o-mini",
        }
    )

    # 2. Initialize health agent
    health_agent = HealthAgent(
        name="Vitality Health Coach",
        owner="Health AI Inc.",
        description="A health and fitness advisor that can create personalized workout plans, offer nutrition advice, and track fitness goals.",
        user_intent=f"Request from {user_name} via Personal AI: {user_message}",
        model_config={
            "model": "openai:gpt-4o-mini",
        }
    )

    # User chat section
    st.subheader(f"Chat between {user_name} and {personal_ai.name}")
    
    # Display user message
    with st.chat_message("user", avatar="👤"):
        st.write(user_message)
    
    # Personal AI responds to user message
    personal_ai_response = personal_ai.respond_to_user(user_message)
    
    with st.chat_message("assistant", avatar="🤖"):
        st.write(personal_ai_response)
    
    # Divider before agent chat
    st.divider()
    st.subheader(f"{personal_ai.name} consulting with {health_agent.name}...")
    
    # Manual implementation of agent-to-agent chat
    with st.spinner("Agents are communicating..."):
        # Initialize agent marketplace
        agent_marketplace = AgentMarketplace()
        
        # Add agents to marketplace
        agent_marketplace.add_agent(personal_ai)
        agent_marketplace.add_agent(health_agent)
        
        # Start the agent-to-agent chat and capture messages
        try:
            agent_chat_messages = agent_marketplace.start_agent_chat(
                agent_name_1=personal_ai.name,
                agent_name_2=health_agent.name,
                return_messages=True  # Return messages instead of printing
            )
        except Exception as e:
            st.error(f"Error in agent chat: {str(e)}")
            agent_chat_messages = []
    
    # Display the agent-to-agent conversation summary
    if agent_chat_messages:
        # Prepare the summary
        health_consultation_summary = "\n".join([f"{msg['sender']}: {msg['content']}" for msg in agent_chat_messages])
        
        # Display summary of agent conversation
        with st.expander("View Agent Conversation Details", expanded=False):
            for msg in agent_chat_messages:
                sender = msg['sender']
                content = msg['content']
                if sender == personal_ai.name:
                    st.markdown(f"**{sender}**: {content}")
                else:
                    st.markdown(f"**{sender}**: {content}")
    
        # Personal AI summarizes the health agent consultation and responds to user
        st.divider()
        st.subheader(f"Final response from {personal_ai.name}")
        
        final_response = personal_ai.summarize_agent_chat(health_consultation_summary, user_message)
        with st.chat_message("assistant", avatar="🤖"):
            st.write(final_response)
    else:
        st.error("No conversation occurred between the agents.")


def main():
    """Main function to run the Streamlit app."""
    st.set_page_config(
        page_title="Agent Marketplace - Health Chat Demo",
        page_icon="🤖",
        layout="wide"
    )
    
    st.title("Agent Marketplace - Health Chat Demo")
    st.caption("A demo of personal AI agent consulting with a health agent")
    
    # Sidebar for input parameters
    st.sidebar.title("Demo Settings")
    user_name = st.sidebar.text_input("User Name", value="Nicholas Richmond")
    user_message = st.sidebar.text_area(
        "User Message", 
        value="I'd like to know if my cholesterol levels are concerning and what I should do about them.",
        height=100
    )
    
    if st.sidebar.button("Run Chat Simulation"):
        st.sidebar.success("Starting chat simulation...")
        run_chat(user_name, user_message)


if __name__ == "__main__":
    main() 
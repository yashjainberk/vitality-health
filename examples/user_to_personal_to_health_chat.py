"""
Demo for user chat with a Personal AI agent that then chats with a Health agent.

This module initializes a chat interface between the user and a Personal AI agent.
The Personal AI agent then creates a separate chat with a Health agent and
relays information back to the user.
"""
import argparse
import os
import json
import time
from textwrap import dedent

from agent_marketplace.marketplace import AgentMarketplace
from agent_marketplace.agents.personal_ai import PersonalAI
from agent_marketplace.agents.health_agent import HealthAgent


def main():
    # Add argument parser
    parser = argparse.ArgumentParser(description='User to Personal to Health Agent Chat Demo')
    parser.add_argument('--user_name', type=str, default="Nicholas Richmond",
                       help='The name of the user')
    args = parser.parse_args()

    # Check for sample health data
    health_data_file = os.path.join(os.path.dirname(__file__), "..", "data", "personal_data", args.user_name, "sample_health_data.json")
    if os.path.exists(health_data_file):
        print(f"Found sample health data for {args.user_name}.")
    else:
        print(f"No sample health data found for {args.user_name}. Creating directory if needed.")
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(health_data_file), exist_ok=True)

    # 1. Initialize personal AI agent
    personal_ai = PersonalAI(
        name=f"{args.user_name}'s Personal AI",
        owner=args.user_name,
        description="A personal AI agent that can help with tasks and provide information",
        user_intent="",  # Will be set during conversation
        model_config={
            "model": "openai:gpt-4o-mini",
        }
    )

    # 2. Initialize health agent
    health_agent = HealthAgent(
        name="Vitality Health Coach",
        owner="Health AI Inc.",
        description="A health and fitness advisor that can create personalized workout plans, offer nutrition advice, and track fitness goals.",
        user_intent="",  # Will be set during conversation with personal AI
        model_config={
            "model": "openai:gpt-4o-mini",
        }
    )

    # 3. Initialize agent marketplace
    agent_marketplace = AgentMarketplace()

    # 4. Add agents to marketplace
    agent_marketplace.add_agent(personal_ai)
    agent_marketplace.add_agent(health_agent)

    # 5. Start user chat with Personal AI
    print(f"\n{'-'*80}")
    print(f"Chat with {personal_ai.name}")
    print(f"{'-'*80}")
    
    # Initial user message
    user_message = input(f"\n{args.user_name}: ")
    
    # Personal AI responds to user message
    personal_ai.user_intent = user_message  # Set the user intent for the personal AI
    personal_ai_response = personal_ai.respond_to_user(user_message)
    print(f"\n{personal_ai.name}: {personal_ai_response}")
    
    # Now personal AI initiates chat with health agent
    print(f"\n{'-'*80}")
    print(f"{personal_ai.name} is now consulting with {health_agent.name}...")
    print(f"{'-'*80}")
    
    # Set up the initial message from personal AI to health agent
    health_agent.user_intent = f"Request from {args.user_name} via Personal AI: {user_message}"
    
    # Start the agent-to-agent chat
    agent_chat_messages = agent_marketplace.start_agent_chat(
        agent_name_1=personal_ai.name,
        agent_name_2=health_agent.name,
        return_messages=True  # Return messages instead of printing them
    )
    
    # Personal AI summarizes the consultation with health agent and responds to user
    print(f"\n{'-'*80}")
    print(f"Back to chat with {personal_ai.name}")
    print(f"{'-'*80}")
    
    # Prepare a summary of the conversation with the health agent for the personal AI
    health_consultation_summary = "\n".join([f"{msg['sender']}: {msg['content']}" for msg in agent_chat_messages])
    
    # Personal AI summarizes the health agent consultation and responds to user
    final_response = personal_ai.summarize_agent_chat(health_consultation_summary, user_message)
    print(f"\n{personal_ai.name}: {final_response}")


if __name__ == "__main__":
    main() 
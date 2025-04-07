"""
Demo for the health agent chat.

This module initializes and runs a chat between a Personal AI agent and a Health AI agent
to demonstrate health and fitness assistance.
"""
import argparse
from textwrap import dedent

from agent_marketplace.marketplace import AgentMarketplace
from agent_marketplace.agents.personal_ai import PersonalAI
from agent_marketplace.agents.health_agent import HealthAgent


def main():
    # Add argument parser
    parser = argparse.ArgumentParser(description='Health Agent Demo')
    parser.add_argument('--user_name', type=str, default="Nicholas Richmond",
                       help='The name of the user')
    parser.add_argument('--user_intent', type=str, default="I want to improve my fitness and establish a healthier diet.",
                       help='The health-related intent/task that the user wants to accomplish')
    args = parser.parse_args()

    # 1. Initialize personal AI agent
    personal_ai = PersonalAI(
        name=f"{args.user_name}'s Personal AI",
        owner=args.user_name,
        description="A personal AI agent that can help with tasks and provide information",
        user_intent=args.user_intent,
        model_config={
            "model": "openai:gpt-4o-mini",
        }
    )

    # 2. Initialize health agent
    health_agent = HealthAgent(
        name="Vitality Health Coach",
        owner="Health AI Inc.",
        description="A health and fitness advisor that can create personalized workout plans, offer nutrition advice, and track fitness goals.",
        user_intent=args.user_intent,
        model_config={
            "model": "openai:gpt-4o-mini",
        }
    )

    # 3. Initialize agent marketplace
    agent_marketplace = AgentMarketplace()

    # 4. Add agents to marketplace
    agent_marketplace.add_agent(personal_ai)
    agent_marketplace.add_agent(health_agent)

    # 5. Start agent chat
    agent_marketplace.start_agent_chat(
        agent_name_1=personal_ai.name,
        agent_name_2=health_agent.name,
    )


if __name__ == "__main__":
    main() 
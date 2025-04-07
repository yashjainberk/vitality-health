import json
from datetime import datetime
from typing import Dict, Any, List, Optional

from agent_marketplace.agents.ai_agent import AI_Agent
from agent_marketplace.services.llm import OpenAILLMProvider
from agent_marketplace.agents.personal_ai import CHECK_CHAT_STATE_PROMPT
from agent_marketplace.schemas.agents import Message
from agent_marketplace.config import get_settings

class HealthAgent(AI_Agent):
    def __init__(self, name: str, owner: str, description: str, user_intent: str, model_config: dict = {}):
        super().__init__(name, owner, description, model_config)
        self.user_intent: str = user_intent
        self.llm = OpenAILLMProvider()
        self.health_profile = {
            "goals": [],
            "dietary_restrictions": [],
            "current_metrics": {},
            "workout_history": [],
            "meal_plan": {}
        }

    def on_message(self, message: Message, sender: AI_Agent) -> Message:
        # Update context
        if message:
            self.context.history.append(message)

        # Generate response
        response = self.generate_response(message, sender)

        # Create return message
        return_message = Message(
            role="assistant", 
            content=response["content"], 
            sender=self.name, 
            receiver=sender.name, 
            timestamp=datetime.now(),
            metadata={}
        )

        # Update context
        self.context.history.append(return_message)

        # Check if the task is complete
        if response["content"] == "[CONVERSATION_ENDS]":
            self.task_complete = True

        return return_message
    
    def generate_response(self, message: Message, sender: AI_Agent) -> Dict[str, Any]:
        """Generate response for the incoming message."""
        # Check if we should update health profile
        self.update_health_profile(message.content)
        
        # Check if the chat should end at this turn
        chat_state = self.llm_call_to_check_chat_state()
        if chat_state["content"] == "[CONVERSATION_ENDS]":
            self.task_complete = True
            return {"content": "[CONVERSATION_ENDS]"}

        # Generate a health-focused response
        response = self.llm_call_to_generate_health_response(message, sender)
        return response

    def update_health_profile(self, message_content: str) -> None:
        """Update health profile based on user message content."""
        # Extract health goals
        goals_prompt = f"""
        Based on the user's message below, extract any health or fitness goals they mention.
        If no goals are mentioned, return an empty list.
        
        User message: {message_content}
        
        Return ONLY a valid JSON array of strings, each representing a goal. Example: ["lose weight", "build muscle"]
        """
        
        try:
            goals_response = self.llm.generate(prompt=goals_prompt)
            if goals_response["content"]:
                # Try to parse the response as JSON
                try:
                    extracted_goals = json.loads(goals_response["content"])
                    if isinstance(extracted_goals, list) and extracted_goals:
                        for goal in extracted_goals:
                            if goal not in self.health_profile["goals"]:
                                self.health_profile["goals"].append(goal)
                except:
                    pass  # Ignore parsing errors
        except:
            pass  # Ignore any errors in LLM call
        
        # Extract dietary restrictions
        dietary_prompt = f"""
        Based on the user's message below, extract any dietary restrictions or preferences they mention.
        If none are mentioned, return an empty list.
        
        User message: {message_content}
        
        Return ONLY a valid JSON array of strings. Example: ["vegetarian", "no nuts", "low carb"]
        """
        
        try:
            dietary_response = self.llm.generate(prompt=dietary_prompt)
            if dietary_response["content"]:
                try:
                    extracted_restrictions = json.loads(dietary_response["content"])
                    if isinstance(extracted_restrictions, list) and extracted_restrictions:
                        for restriction in extracted_restrictions:
                            if restriction not in self.health_profile["dietary_restrictions"]:
                                self.health_profile["dietary_restrictions"].append(restriction)
                except:
                    pass
        except:
            pass

    def llm_call_to_generate_health_response(self, message: Message, sender: AI_Agent) -> Dict[str, str]:
        """Generate a health-focused response based on the user's message."""
        # Format health profile as string
        health_profile_str = json.dumps(self.health_profile, indent=2)
        
        # Create the prompt for health response
        prompt = f"""
        You are a professional health and fitness advisor named {self.name}. You are chatting with {sender.name}, 
        which is the personal AI assistant of {sender.owner}.

        # User Task
        {self.user_intent}

        # Health Profile
        {health_profile_str}

        # Conversation History
        {self.format_conversation_history()}

        # Latest Message
        {message.content}

        # Your Task
        Generate a helpful, informative response about health, fitness, nutrition, or wellness
        based on the conversation history and the user's health profile. Be supportive,
        encouraging, and provide actionable advice. Do not make up specific medical claims 
        or diagnoses. When in doubt, suggest consulting a healthcare professional.

        If the user is asking for a workout plan, meal plan, or tracking feature, you can offer 
        to create one based on their goals and preferences.
        """

        response = self.llm.generate(prompt=prompt)
        return response

    def format_conversation_history(self) -> str:
        """Format conversation history for prompt context."""
        # Get last 10 messages to avoid hitting token limits
        recent_messages = self.context.history[-10:] if len(self.context.history) > 10 else self.context.history
        return "\n".join([f"{msg.sender}: {msg.content}" for msg in recent_messages])

    def llm_call_to_check_chat_state(self) -> Dict[str, str]:
        """Check if the chat should end."""
        conversation_history = self.format_conversation_history()

        if "[PAYMENT_SUCCEEDED]" in conversation_history or "[CONVERSATION_ENDS]" in conversation_history:
            return {"content": "[CONVERSATION_ENDS]"}

        prompt = CHECK_CHAT_STATE_PROMPT.format(
            agent_name=self.name,
            owner=self.owner,
            user_intent=self.user_intent,
            service_agent_description=self.description,
            conversation_history=conversation_history,
        )

        response = self.llm.generate(prompt=prompt)
        return response 
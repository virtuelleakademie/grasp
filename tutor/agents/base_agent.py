import os
from pydantic import BaseModel
from pydantic_ai import Agent
from dotenv import load_dotenv
from tutor.models.context import TutorContext

# Load environment variables
load_dotenv()

class BaseAgentConfig(BaseModel):
    model: str = os.getenv("TUTOR_MODEL", "openai:gpt-4o")
    temperature: float = 0.5
    max_tokens: int = 1000
    timeout: int = 30

def create_base_agent(
    output_type: type,
    system_prompt: str,
    config: BaseAgentConfig = None
) -> Agent:
    """Factory function for creating standardized agents"""
    config = config or BaseAgentConfig()
    
    return Agent(
        config.model,
        deps_type=TutorContext,
        output_type=output_type,
        system_prompt=system_prompt,
        model_settings={
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "timeout": config.timeout
        }
    )
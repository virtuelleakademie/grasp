# Implementation Guide: PydanticAI Migration

## Phase-by-Phase Implementation

### Phase 1: Foundation Setup (Week 1)

#### Day 1-2: Environment Setup
```bash
# Update requirements.txt
echo "pydantic-ai>=0.0.14" >> requirements.txt
echo "pydantic>=2.0.0" >> requirements.txt
pip install -r requirements.txt

# Create new directory structure
mkdir -p tutor/{agents,services,models,session,handlers,config,utils}
touch tutor/{agents,services,models,session,handlers,config,utils}/__init__.py
```

#### Day 3-4: Core Models Implementation

**Step 1**: Create base models
```python
# tutor/models/state.py
from pydantic import BaseModel
from datetime import datetime

class IterationState(BaseModel):
    total_interactions: int = 0
    step_interactions: int = 0
    checkpoint_interactions: int = 0
    finished: bool = False
    last_updated: datetime = datetime.utcnow()
    
    def increment(self):
        self.total_interactions += 1
        self.step_interactions += 1
        self.checkpoint_interactions += 1
        self.last_updated = datetime.utcnow()
    
    def reset_step(self):
        self.step_interactions = 0
        self.last_updated = datetime.utcnow()
    
    def reset_checkpoint(self):
        self.checkpoint_interactions = 0
        self.reset_step()
    
    def has_step_iterations_left(self, max_step: int = 2) -> bool:
        return self.step_interactions < max_step
    
    def has_checkpoint_iterations_left(self, max_checkpoint: int = 6) -> bool:
        return self.checkpoint_interactions < max_checkpoint
```

**Step 2**: Create response models
```python
# tutor/models/responses.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class Understanding(BaseModel):
    main_question_answered: bool = False
    guiding_question_answered: bool = False
    confidence_score: float = Field(ge=0.0, le=1.0, default=0.5)
    identified_concepts: List[str] = Field(default_factory=list)
    misconceptions: List[str] = Field(default_factory=list)
    summary: List[str] = Field(default_factory=list)
    reasoning: str = ""
    
    # For backward compatibility with existing output_structure
    chain_of_thought: str = ""
    
    @classmethod
    def empty(cls) -> "Understanding":
        return cls()
    
    def context(self) -> str:
        """Format for agent context - matches existing interface"""
        if not self.summary:
            return "No previous understanding recorded."
        return f"""
        Current Understanding:
        - Main question answered: {self.main_question_answered}
        - Guiding question answered: {self.guiding_question_answered}
        - Summary: {'; '.join(self.summary)}
        """
    
    def view_chain_of_thought(self) -> str:
        """For backward compatibility with existing debugging"""
        return self.reasoning or self.chain_of_thought

class Feedback(BaseModel):
    feedback: str
    positive_aspects: List[str] = Field(default_factory=list)
    areas_for_improvement: List[str] = Field(default_factory=list)
    encouragement_level: str = Field(default="moderate")
    reasoning: str = ""
    
    # For backward compatibility
    chain_of_thought: str = ""
    prompt: str = ""
    
    def view_chain_of_thought(self) -> str:
        return self.reasoning or self.chain_of_thought

class Instructions(BaseModel):
    instructions: str
    instruction_type: str = "guidance"
    follow_up_questions: List[str] = Field(default_factory=list)
    reasoning: str = ""
    
    # For backward compatibility
    chain_of_thought: str = ""
    prompt: str = ""
    
    def view_chain_of_thought(self) -> str:
        return self.reasoning or self.chain_of_thought
```

#### Day 5-7: Testing Foundation
```python
# tests/test_models.py
import pytest
from tutor.models.state import IterationState
from tutor.models.responses import Understanding, Feedback, Instructions

def test_iteration_state():
    state = IterationState()
    assert state.total_interactions == 0
    
    state.increment()
    assert state.total_interactions == 1
    assert state.step_interactions == 1
    
    state.reset_step()
    assert state.step_interactions == 0
    assert state.total_interactions == 1

def test_understanding_compatibility():
    understanding = Understanding.empty()
    assert understanding.main_question_answered == False
    assert understanding.context() is not None
    assert understanding.view_chain_of_thought() == ""

# Run tests
python -m pytest tests/test_models.py -v
```

### Phase 2: Agent Implementation (Week 2)

#### Day 1-3: Create Base Agent Infrastructure
```python
# tutor/config/agent_config.py
from pydantic import BaseModel
import os

class AgentConfig(BaseModel):
    model: str = os.getenv("TUTOR_MODEL", "openai:gpt-4o")
    temperature: float = 0.5
    max_tokens: int = 1000
    timeout: int = 30
    max_retries: int = 3

# tutor/agents/base_agent.py
from pydantic_ai import Agent
from tutor.config.agent_config import AgentConfig

def create_base_agent(result_type: type, system_prompt: str) -> Agent:
    config = AgentConfig()
    
    return Agent(
        config.model,
        deps_type=None,  # Will be set when we implement TutorContext
        result_type=result_type,
        system_prompt=system_prompt,
        model_settings={
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "timeout": config.timeout
        }
    )
```

#### Day 4-5: Implement Understanding Agent
```python
# tutor/agents/understanding_agent.py
from pydantic_ai import Agent, RunContext
from tutor.models.responses import Understanding
from tutor.agents.base_agent import create_base_agent

UNDERSTANDING_PROMPT = """
You are a statistical tutor evaluating student understanding.
Analyze the student's response and determine if they have answered
the current questions correctly.
"""

understanding_agent = create_base_agent(
    result_type=Understanding,
    system_prompt=UNDERSTANDING_PROMPT
)

# Simple test without full context first
async def test_understanding_agent():
    result = await understanding_agent.run(
        "I think the answer is that we need to use a t-test because the sample size is small."
    )
    assert isinstance(result, Understanding)
    print(f"Understanding result: {result}")

# Run basic test
import asyncio
asyncio.run(test_understanding_agent())
```

#### Day 6-7: Implement Feedback and Instruction Agents
```python
# tutor/agents/feedback_agent.py
from tutor.models.responses import Feedback
from tutor.agents.base_agent import create_base_agent

FEEDBACK_PROMPT = """
You are a supportive statistical tutor providing constructive feedback.
Give encouraging feedback that acknowledges understanding and addresses gaps.
"""

feedback_agent = create_base_agent(
    result_type=Feedback,
    system_prompt=FEEDBACK_PROMPT
)

# tutor/agents/instruction_agent.py
from tutor.models.responses import Instructions
from tutor.agents.base_agent import create_base_agent

INSTRUCTION_PROMPT = """
You are a statistical tutor providing guidance.
Give helpful instructions that guide students toward understanding
without revealing answers directly.
"""

instruction_agent = create_base_agent(
    result_type=Instructions,
    system_prompt=INSTRUCTION_PROMPT
)

# Test all agents
async def test_all_agents():
    test_input = "I'm not sure about the difference between t-test and z-test"
    
    understanding = await understanding_agent.run(test_input)
    feedback = await feedback_agent.run(test_input)
    instructions = await instruction_agent.run(test_input)
    
    print(f"Understanding: {understanding.main_question_answered}")
    print(f"Feedback: {feedback.feedback[:50]}...")
    print(f"Instructions: {instructions.instructions[:50]}...")

asyncio.run(test_all_agents())
```

### Phase 3: Service Layer (Week 3)

#### Day 1-2: Context Integration
```python
# tutor/models/context.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from tutor.exercise_model import Exercise
from tutor.models.state import IterationState
from tutor.models.responses import Understanding

class TutorContext(BaseModel):
    exercise: Exercise
    current_checkpoint: int = Field(ge=1)
    current_step: int = Field(ge=1)
    tutor_mode: str = Field(pattern="^(socratic|instructional)$")
    user_id: str
    session_id: str
    iterations: IterationState = Field(default_factory=IterationState)
    current_understanding: Understanding = Field(default_factory=Understanding.empty)
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list)
    max_step_iterations: int = 2
    max_checkpoint_iterations: int = 6
    
    @property
    def current_main_question(self) -> str:
        return self.exercise.checkpoints[self.current_checkpoint - 1].main_question
    
    @property
    def current_guiding_question(self) -> str:
        checkpoint = self.exercise.checkpoints[self.current_checkpoint - 1]
        if self.current_step <= len(checkpoint.steps):
            return checkpoint.steps[self.current_step - 1].guiding_question
        return self.current_main_question

# Update agents to use TutorContext
# tutor/agents/understanding_agent.py (updated)
from tutor.models.context import TutorContext

understanding_agent = Agent(
    'openai:gpt-4o',
    deps_type=TutorContext,
    result_type=Understanding
)

@understanding_agent.system_prompt
def get_understanding_prompt(ctx: RunContext[TutorContext]) -> str:
    return f"""
    You are evaluating student understanding.
    
    Current Context:
    - Main Question: {ctx.deps.current_main_question}
    - Guiding Question: {ctx.deps.current_guiding_question}
    - Previous Understanding: {ctx.deps.current_understanding.context()}
    
    Determine if the student has answered these questions.
    """
```

#### Day 3-4: Tutor Coordinator
```python
# tutor/services/tutor_coordinator.py
from tutor.agents.understanding_agent import understanding_agent
from tutor.agents.feedback_agent import feedback_agent
from tutor.agents.instruction_agent import instruction_agent
from tutor.models.context import TutorContext
from tutor.models.responses import TutorResponse

class TutorCoordinator:
    def __init__(self):
        self.understanding_agent = understanding_agent
        self.feedback_agent = feedback_agent
        self.instruction_agent = instruction_agent
    
    async def process_student_message(
        self, 
        message: str, 
        context: TutorContext
    ) -> TutorResponse:
        # Phase 1: Check Understanding
        understanding = await self.understanding_agent.run(message, deps=context)
        context.current_understanding = understanding
        
        # Phase 2: Generate Feedback
        feedback = await self.feedback_agent.run(message, deps=context)
        
        # Phase 3: Determine Next Action
        if understanding.main_question_answered:
            action = "advance_checkpoint"
        elif understanding.guiding_question_answered:
            action = "advance_step"
        else:
            action = "continue_question"
            
        # Phase 4: Generate Instructions if needed
        instructions = None
        if action == "continue_question":
            instructions = await self.instruction_agent.run(message, deps=context)
        
        return TutorResponse(
            feedback_text=feedback.feedback,
            instruction_text=instructions.instructions if instructions else None,
            action=action,
            next_checkpoint=context.current_checkpoint,
            next_step=context.current_step
        )

# Test coordinator
async def test_coordinator():
    from tutor.exercise_loader import ExerciseLoader
    
    # Load test exercise
    exercise = ExerciseLoader.load("exercises/t-test/exercise.yaml")
    
    context = TutorContext(
        exercise=exercise,
        current_checkpoint=1,
        current_step=1,
        tutor_mode="socratic",
        user_id="test_user",
        session_id="test_session"
    )
    
    coordinator = TutorCoordinator()
    response = await coordinator.process_student_message(
        "I think we need to use a t-test",
        context
    )
    
    print(f"Action: {response.action}")
    print(f"Feedback: {response.feedback_text[:50]}...")

asyncio.run(test_coordinator())
```

#### Day 5-7: Service Integration
```python
# tutor/services/session_service.py
from tutor.services.tutor_coordinator import TutorCoordinator
from tutor.services.exercise_service import ExerciseService
from tutor.models.context import TutorContext

class SessionService:
    def __init__(self):
        self.tutor_coordinator = TutorCoordinator()
        self.exercise_service = ExerciseService()
    
    async def create_session(
        self,
        exercise_name: str,
        tutor_mode: str,
        user_id: str
    ) -> TutorContext:
        exercise = self.exercise_service.load_exercise(exercise_name)
        
        return TutorContext(
            exercise=exercise,
            current_checkpoint=1,
            current_step=1,
            tutor_mode=tutor_mode,
            user_id=user_id,
            session_id=str(uuid.uuid4())
        )
    
    async def process_message(
        self,
        message: str,
        context: TutorContext
    ) -> tuple[TutorResponse, TutorContext]:
        context.iterations.increment()
        response = await self.tutor_coordinator.process_student_message(message, context)
        
        # Update context based on response
        if response.action == "advance_step":
            context.current_step += 1
            context.iterations.reset_step()
        elif response.action == "advance_checkpoint":
            context.current_checkpoint += 1
            context.current_step = 1
            context.iterations.reset_checkpoint()
        
        return response, context
```

### Phase 4: Application Integration (Week 4)

#### Day 1-3: Backward Compatibility Layer
```python
# tutor/compatibility/legacy_adapter.py
"""
Adapter to maintain compatibility with existing Chainlit integration
while gradually migrating to new architecture
"""

from tutor.services.session_service import SessionService
from tutor.models.context import TutorContext
import chainlit as cl

class LegacyAdapter:
    def __init__(self):
        self.session_service = SessionService()
    
    async def initialize_session(self, exercise_name: str, tutor_mode: str, user_id: str):
        """Initialize session and store in Chainlit session"""
        context = await self.session_service.create_session(
            exercise_name, tutor_mode, user_id
        )
        
        # Store in Chainlit session for compatibility
        cl.user_session.set("tutor_context", context)
        
        # Also maintain legacy state for gradual migration
        cl.user_session.set("agent_state", {
            "messages": [],
            "log": context.conversation_history,  # Link to new system
            "tutor_mode": tutor_mode,
            "current_checkpoint": context.current_checkpoint,
            "current_step": context.current_step,
            "iterations": context.iterations,
            "exercise": context.exercise,
            "current_understanding": context.current_understanding,
            "debugging": False,
            "show_prompts": False,
            "show_reasoning": False,
        })
    
    async def process_message(self, message: str):
        """Process message using new system but maintain legacy interface"""
        context = cl.user_session.get("tutor_context")
        
        response, updated_context = await self.session_service.process_message(
            message, context
        )
        
        # Update both new and legacy state
        cl.user_session.set("tutor_context", updated_context)
        
        # Update legacy state
        agent_state = cl.user_session.get("agent_state")
        agent_state["current_checkpoint"] = updated_context.current_checkpoint
        agent_state["current_step"] = updated_context.current_step
        agent_state["iterations"] = updated_context.iterations
        agent_state["current_understanding"] = updated_context.current_understanding
        cl.user_session.set("agent_state", agent_state)
        
        return response
```

#### Day 4-5: App.py Integration
```python
# app.py (updated to use new system gradually)
import chainlit as cl
from tutor.compatibility.legacy_adapter import LegacyAdapter

# Initialize adapter
adapter = LegacyAdapter()

@cl.on_chat_start
async def start():
    # Get configuration (existing logic)
    exercise_name = os.getenv("EXERCISE_NAME", "t-test")
    tutor_mode = get_tutor_mode()  # Existing function
    user_id = get_user_id()      # Existing function
    
    # Use new system through adapter
    await adapter.initialize_session(exercise_name, tutor_mode, user_id)
    
    # Send initial message (existing logic can be gradually migrated)
    await starting_message()

@cl.on_message
async def handle_message(message: cl.Message):
    if message.content.startswith("/goto"):
        # Keep existing goto logic for now
        await handle_goto_command(message.content)
    else:
        # Use new system
        response = await adapter.process_message(message.content)
        
        # Convert response to legacy Message format
        from tutor.agent import Message
        msg = Message(response.feedback_text)
        if response.instruction_text:
            msg += f"\n\n{response.instruction_text}"
        
        # Handle images
        if response.image_path:
            msg.image = response.image_path
        
        await msg.send()
```

#### Day 6-7: Testing Integration
```python
# tests/test_integration.py
import pytest
import asyncio
from tutor.compatibility.legacy_adapter import LegacyAdapter

@pytest.mark.asyncio
async def test_full_integration():
    adapter = LegacyAdapter()
    
    # Test session creation
    # Note: This would need mocking of Chainlit session
    # await adapter.initialize_session("t-test", "socratic", "test_user")
    
    # Test message processing
    # response = await adapter.process_message("I think we need a t-test")
    # assert response.feedback_text is not None
    
    pass  # Placeholder for now

# Manual testing script
# python -c "
# import asyncio
# from tutor.services.session_service import SessionService
# 
# async def test():
#     service = SessionService()
#     context = await service.create_session('t-test', 'socratic', 'test')
#     response, updated_context = await service.process_message('Hello', context)
#     print(f'Response: {response.feedback_text[:50]}...')
# 
# asyncio.run(test())
# "
```

### Phase 5: Full Migration (Week 5)

#### Day 1-2: Remove Legacy Dependencies
```python
# Remove @with_agent_state decorator usage
# Update all remaining functions to use TutorContext directly

# tutor/handlers/message_handler.py
class MessageHandler:
    def __init__(self, tutor_coordinator):
        self.tutor_coordinator = tutor_coordinator
    
    async def handle_message(self, message: str, context: TutorContext) -> TutorContext:
        """Replace the large chat() function with clean handler"""
        context.add_to_conversation("user", message)
        context.iterations.increment()
        
        response = await self.tutor_coordinator.process_student_message(message, context)
        
        # Handle progression
        if response.action == "advance_step":
            context.advance_step()
        elif response.action == "advance_checkpoint":
            context.advance_checkpoint()
        
        # Send UI response
        await self._send_response(response, context)
        
        return context
    
    async def _send_response(self, response: TutorResponse, context: TutorContext):
        """Send response to UI"""
        message_text = response.feedback_text
        if response.instruction_text:
            message_text += f"\n\n{response.instruction_text}"
        
        elements = []
        if response.image_path:
            elements.append(cl.Image(name="step_image", path=response.image_path))
        
        await cl.Message(content=message_text, elements=elements).send()
```

#### Day 3-4: Clean Up Legacy Code
```bash
# Remove old files
rm tutor/helper.py  # @with_agent_state decorator
# mv tutor/reasoning.py tutor/legacy/reasoning.py  # Keep for reference

# Update imports throughout codebase
find tutor/ -name "*.py" -exec sed -i 's/from tutor.helper import with_agent_state//g' {} \;
find tutor/ -name "*.py" -exec sed -i 's/@with_agent_state//g' {} \;

# Update agent.py to use new architecture
# Keep Message and Iterations classes but remove LLM logic
```

#### Day 5-7: Optimization and Documentation
```python
# tutor/config/settings.py
class Settings(BaseModel):
    # Centralize all configuration
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    tutor_model: str = Field("openai:gpt-4o", env="TUTOR_MODEL")
    exercise_dir: str = Field("exercises", env="EXERCISES_DIR")
    default_exercise: str = Field("t-test", env="EXERCISE_NAME")
    
    max_step_iterations: int = 2
    max_checkpoint_iterations: int = 6
    
    # PydanticAI specific settings
    agent_timeout: int = 30
    agent_temperature: float = 0.5
    agent_max_tokens: int = 1000

# Update CLAUDE.md with new development commands
```

## Testing Strategy

### Unit Tests
```python
# tests/test_agents.py
@pytest.mark.asyncio
async def test_understanding_agent():
    context = create_test_context()
    result = await understanding_agent.run("I think we use t-test", deps=context)
    assert isinstance(result, Understanding)

# tests/test_services.py
@pytest.mark.asyncio
async def test_tutor_coordinator():
    coordinator = TutorCoordinator()
    context = create_test_context()
    response = await coordinator.process_student_message("test", context)
    assert isinstance(response, TutorResponse)

# tests/test_integration.py
@pytest.mark.asyncio
async def test_full_workflow():
    session_service = SessionService()
    context = await session_service.create_session("t-test", "socratic", "test")
    response, updated_context = await session_service.process_message("hello", context)
    assert response.feedback_text is not None
```

### Performance Testing
```python
# scripts/benchmark.py
import time
import asyncio
from tutor.services.session_service import SessionService

async def benchmark_session():
    service = SessionService()
    
    start_time = time.time()
    context = await service.create_session("t-test", "socratic", "test")
    
    for i in range(10):
        message = f"Test message {i}"
        response, context = await service.process_message(message, context)
        print(f"Message {i}: {time.time() - start_time:.2f}s")
    
    total_time = time.time() - start_time
    print(f"Total time for 10 messages: {total_time:.2f}s")
    print(f"Average per message: {total_time/10:.2f}s")

asyncio.run(benchmark_session())
```

## Migration Checklist

### Pre-Migration
- [ ] Backup current codebase
- [ ] Set up development branch
- [ ] Install PydanticAI dependencies
- [ ] Create basic test framework

### Phase 1 Checklist
- [ ] Create new directory structure
- [ ] Implement core models (state, responses, context)
- [ ] Write unit tests for models
- [ ] Verify backward compatibility interfaces

### Phase 2 Checklist
- [ ] Implement base agent infrastructure
- [ ] Create understanding agent
- [ ] Create feedback agent
- [ ] Create instruction agent
- [ ] Test individual agents

### Phase 3 Checklist
- [ ] Integrate agents with TutorContext
- [ ] Implement TutorCoordinator
- [ ] Create service layer
- [ ] Test agent coordination

### Phase 4 Checklist
- [ ] Create compatibility adapter
- [ ] Integrate with existing app.py
- [ ] Test full application flow
- [ ] Verify UI functionality

### Phase 5 Checklist
- [ ] Remove legacy code
- [ ] Clean up imports and dependencies
- [ ] Update documentation
- [ ] Performance optimization
- [ ] Final testing

### Post-Migration
- [ ] Monitor performance metrics
- [ ] Update deployment procedures
- [ ] Train team on new architecture
- [ ] Create troubleshooting guides

This implementation guide provides a detailed, step-by-step approach to migrating to PydanticAI while maintaining system functionality throughout the process.
# New Architecture with PydanticAI

## Architecture Overview

The new architecture follows a layered approach with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────── │
│  │   Chainlit UI   │  │  Web Interface  │  │  API Endpoints │
│  └─────────────────┘  └─────────────────┘  └─────────────── │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                   Application Layer                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────── │
│  │ Session Manager │  │ Message Handler │  │ Command Router │
│  └─────────────────┘  └─────────────────┘  └─────────────── │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                     Service Layer                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────── │
│  │TutorCoordinator │  │ Exercise Service│  │   UI Service   │
│  └─────────────────┘  └─────────────────┘  └─────────────── │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                     Agent Layer                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────── │
│  │Understanding AG │  │  Feedback AG    │  │Instruction AG  │
│  └─────────────────┘  └─────────────────┘  └─────────────── │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                      Data Layer                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────── │
│  │   Exercise      │  │    Context      │  │    Models      │
│  │   Repository    │  │    Storage      │  │   & Schemas    │
│  └─────────────────┘  └─────────────────┘  └─────────────── │
└─────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
tutor/
├── agents/                          # PydanticAI Agent Definitions
│   ├── __init__.py
│   ├── understanding_agent.py       # Evaluates student comprehension
│   ├── feedback_agent.py           # Provides constructive feedback
│   ├── instruction_agent.py        # Generates next guidance
│   └── base_agent.py               # Shared agent configuration
│
├── services/                        # Business Logic Layer
│   ├── __init__.py
│   ├── tutor_coordinator.py        # Orchestrates agent workflow
│   ├── exercise_service.py         # Exercise operations
│   ├── ui_service.py               # UI abstraction layer
│   └── progression_service.py      # Handles step/checkpoint logic
│
├── models/                          # Data Models & Schemas
│   ├── __init__.py
│   ├── context.py                  # TutorContext and dependencies
│   ├── responses.py                # Agent response models
│   ├── state.py                    # Session and iteration state
│   └── content.py                  # Exercise content models
│
├── session/                         # Session Management
│   ├── __init__.py
│   ├── session_manager.py          # High-level session coordination
│   └── state_manager.py            # State persistence and retrieval
│
├── handlers/                        # Request/Message Handlers
│   ├── __init__.py
│   ├── message_handler.py          # Process student messages
│   ├── command_handler.py          # Handle special commands (/goto)
│   └── error_handler.py            # Error handling and recovery
│
├── config/                          # Configuration Management
│   ├── __init__.py
│   ├── agent_config.py             # Agent-specific configuration
│   ├── app_config.py               # Application configuration
│   └── prompts.py                  # Centralized prompt templates
│
└── utils/                           # Utilities and Helpers
    ├── __init__.py
    ├── validators.py               # Input validation
    ├── formatters.py               # Response formatting
    └── logging_utils.py            # Enhanced logging utilities
```

## Component Specifications

### 1. Agent Layer

#### Base Agent Configuration
**File**: `tutor/agents/base_agent.py`

```python
from pydantic import BaseModel
from pydantic_ai import Agent
from tutor.config.agent_config import AgentConfig
from tutor.models.context import TutorContext

class BaseAgentConfig(BaseModel):
    model: str = "openai:gpt-4o"
    temperature: float = 0.5
    max_tokens: int = 1000
    timeout: int = 30

def create_base_agent(
    result_type: type,
    system_prompt: str,
    config: BaseAgentConfig = None
) -> Agent:
    """Factory function for creating standardized agents"""
    config = config or BaseAgentConfig()
    
    return Agent(
        config.model,
        deps_type=TutorContext,
        result_type=result_type,
        system_prompt=system_prompt,
        model_settings={
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "timeout": config.timeout
        }
    )
```

#### Understanding Agent
**File**: `tutor/agents/understanding_agent.py`

```python
from pydantic_ai import RunContext
from tutor.models.responses import Understanding
from tutor.models.context import TutorContext
from tutor.agents.base_agent import create_base_agent
from tutor.config.prompts import UNDERSTANDING_SYSTEM_PROMPT

understanding_agent = create_base_agent(
    result_type=Understanding,
    system_prompt=UNDERSTANDING_SYSTEM_PROMPT
)

@understanding_agent.system_prompt
def get_understanding_prompt(ctx: RunContext[TutorContext]) -> str:
    """Dynamic system prompt based on current context"""
    return f"""
    {UNDERSTANDING_SYSTEM_PROMPT}
    
    Current Context:
    - Exercise: {ctx.deps.exercise.metadata.title}
    - Checkpoint {ctx.deps.current_checkpoint}: {ctx.deps.current_main_question}
    - Step {ctx.deps.current_step}: {ctx.deps.current_guiding_question}
    - Iteration: {ctx.deps.iterations.step_interactions}/{ctx.deps.max_step_iterations}
    
    Previous Understanding:
    {ctx.deps.current_understanding.summary_text()}
    """

@understanding_agent.tool
def get_reference_answer(ctx: RunContext[TutorContext]) -> str:
    """Tool to access reference answers for comparison"""
    if ctx.deps.current_step <= len(ctx.deps.current_checkpoint_steps):
        return ctx.deps.current_guiding_answer
    return ctx.deps.current_main_answer
```

### 2. Service Layer

#### Tutor Coordinator
**File**: `tutor/services/tutor_coordinator.py`

```python
from typing import Optional
from pydantic import BaseModel
from tutor.agents import understanding_agent, feedback_agent, instruction_agent
from tutor.models.context import TutorContext
from tutor.models.responses import TutorResponse, Understanding, Feedback, Instructions
from tutor.services.progression_service import ProgressionService

class TutorCoordinator:
    """Orchestrates the multi-agent tutoring workflow"""
    
    def __init__(self):
        self.understanding_agent = understanding_agent
        self.feedback_agent = feedback_agent
        self.instruction_agent = instruction_agent
        self.progression_service = ProgressionService()
    
    async def process_student_input(
        self,
        message: str,
        context: TutorContext
    ) -> TutorResponse:
        """
        Main coordination method that processes student input through
        the three-agent pipeline and determines next actions
        """
        try:
            # Phase 1: Evaluate Understanding
            understanding = await self._evaluate_understanding(message, context)
            context.current_understanding = understanding
            
            # Phase 2: Generate Feedback
            feedback = await self._generate_feedback(message, context)
            
            # Phase 3: Determine Progression
            progression_action = self.progression_service.determine_next_action(
                understanding, context
            )
            
            # Phase 4: Generate Response Based on Action
            response = await self._create_response(
                feedback, understanding, progression_action, message, context
            )
            
            return response
            
        except Exception as e:
            return self._create_error_response(str(e))
    
    async def _evaluate_understanding(
        self, 
        message: str, 
        context: TutorContext
    ) -> Understanding:
        """Evaluate student understanding using PydanticAI agent"""
        return await self.understanding_agent.run(message, deps=context)
    
    async def _generate_feedback(
        self, 
        message: str, 
        context: TutorContext
    ) -> Feedback:
        """Generate constructive feedback using PydanticAI agent"""
        return await self.feedback_agent.run(message, deps=context)
    
    async def _create_response(
        self,
        feedback: Feedback,
        understanding: Understanding,
        action: str,
        message: str,
        context: TutorContext
    ) -> TutorResponse:
        """Create the final response based on determined action"""
        
        if action == "continue_question":
            instructions = await self.instruction_agent.run(message, deps=context)
            return TutorResponse(
                feedback_text=feedback.feedback,
                instruction_text=instructions.instructions,
                action=action,
                next_checkpoint=context.current_checkpoint,
                next_step=context.current_step
            )
        
        elif action == "advance_step":
            solution_text = context.current_guiding_answer
            next_step_content = self.progression_service.get_next_step_content(context)
            
            return TutorResponse(
                feedback_text=feedback.feedback,
                solution_text=solution_text,
                next_question=next_step_content.question,
                image_path=next_step_content.image_path,
                action=action,
                next_checkpoint=context.current_checkpoint,
                next_step=context.current_step + 1
            )
        
        elif action == "advance_checkpoint":
            solution_text = context.current_main_answer
            next_checkpoint_content = self.progression_service.get_next_checkpoint_content(context)
            
            return TutorResponse(
                feedback_text=feedback.feedback,
                solution_text=solution_text,
                solution_image_path=context.current_solution_image_path,
                next_question=next_checkpoint_content.main_question,
                action=action,
                next_checkpoint=context.current_checkpoint + 1,
                next_step=1
            )
        
        else:  # finish
            return TutorResponse(
                feedback_text=feedback.feedback,
                action="finish",
                completion_message=context.exercise.end_message
            )
```

#### Progression Service
**File**: `tutor/services/progression_service.py`

```python
from tutor.models.context import TutorContext
from tutor.models.responses import Understanding
from tutor.models.content import StepContent, CheckpointContent

class ProgressionService:
    """Handles progression logic through exercises"""
    
    def determine_next_action(
        self, 
        understanding: Understanding, 
        context: TutorContext
    ) -> str:
        """
        Determine the next action based on understanding and iteration limits
        
        Returns:
            - "continue_question": Stay on current question
            - "advance_step": Move to next guiding question
            - "advance_checkpoint": Move to next checkpoint
            - "finish": Complete the exercise
        """
        iterations = context.iterations
        
        # Check if main question is answered or checkpoint limit reached
        if (understanding.main_question_answered or 
            not iterations.has_checkpoint_iterations_left()):
            
            if self._has_next_checkpoint(context):
                return "advance_checkpoint"
            else:
                return "finish"
        
        # Check if guiding question is answered or step limit reached
        elif (understanding.guiding_question_answered or 
              not iterations.has_step_iterations_left()):
            
            if self._has_next_step(context):
                return "advance_step"
            else:
                # No more steps, show main question
                return "show_main_question"
        
        else:
            return "continue_question"
    
    def get_next_step_content(self, context: TutorContext) -> StepContent:
        """Get content for the next step"""
        checkpoint = context.exercise.checkpoints[context.current_checkpoint - 1]
        next_step_idx = context.current_step  # current_step will be incremented
        
        if next_step_idx < len(checkpoint.steps):
            step = checkpoint.steps[next_step_idx]
            return StepContent(
                question=step.guiding_question,
                answer=step.guiding_answer,
                image_path=step.image
            )
        else:
            # Return main question if no more steps
            return StepContent(
                question=checkpoint.main_question,
                answer=checkpoint.main_answer,
                image_path=None
            )
    
    def get_next_checkpoint_content(self, context: TutorContext) -> CheckpointContent:
        """Get content for the next checkpoint"""
        next_checkpoint_idx = context.current_checkpoint  # will be incremented
        
        if next_checkpoint_idx < len(context.exercise.checkpoints):
            checkpoint = context.exercise.checkpoints[next_checkpoint_idx]
            first_step = checkpoint.steps[0] if checkpoint.steps else None
            
            return CheckpointContent(
                main_question=checkpoint.main_question,
                main_answer=checkpoint.main_answer,
                first_guiding_question=first_step.guiding_question if first_step else None,
                first_image_path=first_step.image if first_step else None,
                solution_image_path=checkpoint.image_solution
            )
        
        return None
    
    def _has_next_step(self, context: TutorContext) -> bool:
        """Check if there's another step in current checkpoint"""
        checkpoint = context.exercise.checkpoints[context.current_checkpoint - 1]
        return context.current_step < len(checkpoint.steps)
    
    def _has_next_checkpoint(self, context: TutorContext) -> bool:
        """Check if there's another checkpoint"""
        return context.current_checkpoint < len(context.exercise.checkpoints)
```

### 3. Models Layer

#### Enhanced Context Model
**File**: `tutor/models/context.py`

```python
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from tutor.exercise_model import Exercise
from tutor.models.state import IterationState
from tutor.models.responses import Understanding

class TutorContext(BaseModel):
    """
    Central context object that contains all state needed by agents
    and services throughout the tutoring session
    """
    
    # Exercise Information
    exercise: Exercise
    current_checkpoint: int = Field(ge=1)
    current_step: int = Field(ge=1)
    
    # Session Configuration
    tutor_mode: str = Field(pattern="^(socratic|instructional)$")
    user_id: str
    session_id: str
    
    # State Management
    iterations: IterationState = Field(default_factory=IterationState)
    current_understanding: Understanding = Field(default_factory=Understanding.empty)
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Configuration
    max_step_iterations: int = 2
    max_checkpoint_iterations: int = 6
    
    # Computed Properties
    @property
    def current_main_question(self) -> str:
        """Get the main question for current checkpoint"""
        return self.exercise.checkpoints[self.current_checkpoint - 1].main_question
    
    @property
    def current_guiding_question(self) -> str:
        """Get the guiding question for current step"""
        checkpoint = self.exercise.checkpoints[self.current_checkpoint - 1]
        if self.current_step <= len(checkpoint.steps):
            return checkpoint.steps[self.current_step - 1].guiding_question
        return self.current_main_question
    
    @property
    def current_main_answer(self) -> str:
        """Get the main answer for current checkpoint"""
        return self.exercise.checkpoints[self.current_checkpoint - 1].main_answer
    
    @property
    def current_guiding_answer(self) -> str:
        """Get the guiding answer for current step"""
        checkpoint = self.exercise.checkpoints[self.current_checkpoint - 1]
        if self.current_step <= len(checkpoint.steps):
            return checkpoint.steps[self.current_step - 1].guiding_answer
        return ""
    
    @property
    def current_image_path(self) -> Optional[str]:
        """Get image path for current step"""
        checkpoint = self.exercise.checkpoints[self.current_checkpoint - 1]
        if self.current_step <= len(checkpoint.steps):
            return checkpoint.steps[self.current_step - 1].image
        return None
    
    @property
    def current_solution_image_path(self) -> Optional[str]:
        """Get solution image path for current checkpoint"""
        return self.exercise.checkpoints[self.current_checkpoint - 1].image_solution
    
    @property
    def current_checkpoint_steps(self) -> List[Any]:
        """Get all steps for current checkpoint"""
        return self.exercise.checkpoints[self.current_checkpoint - 1].steps
    
    def add_to_conversation(self, role: str, content: str):
        """Add message to conversation history"""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "checkpoint": self.current_checkpoint,
            "step": self.current_step
        })
    
    def advance_step(self):
        """Advance to next step and reset step iterations"""
        self.current_step += 1
        self.iterations.reset_step()
    
    def advance_checkpoint(self):
        """Advance to next checkpoint and reset all counters"""
        self.current_checkpoint += 1
        self.current_step = 1
        self.iterations.reset_checkpoint()
        self.current_understanding = Understanding.empty()
    
    def is_exercise_complete(self) -> bool:
        """Check if the exercise is complete"""
        return (self.current_checkpoint > len(self.exercise.checkpoints) or
                self.iterations.finished)
    
    class Config:
        # Allow additional fields for future extensibility
        extra = "forbid"
        # Validate assignments to catch errors early
        validate_assignment = True
```

#### Response Models
**File**: `tutor/models/responses.py`

```python
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class Understanding(BaseModel):
    """Response model for understanding evaluation"""
    main_question_answered: bool = False
    guiding_question_answered: bool = False
    confidence_score: float = Field(ge=0.0, le=1.0, default=0.5)
    identified_concepts: List[str] = Field(default_factory=list)
    misconceptions: List[str] = Field(default_factory=list)
    summary: List[str] = Field(default_factory=list)
    reasoning: str = ""
    
    @classmethod
    def empty(cls) -> "Understanding":
        """Create empty understanding state"""
        return cls()
    
    def summary_text(self) -> str:
        """Get formatted summary text"""
        if not self.summary:
            return "No previous understanding recorded."
        return "\n".join(f"- {item}" for item in self.summary)

class Feedback(BaseModel):
    """Response model for feedback generation"""
    feedback: str
    positive_aspects: List[str] = Field(default_factory=list)
    areas_for_improvement: List[str] = Field(default_factory=list)
    encouragement_level: str = Field(default="moderate")  # low, moderate, high
    reasoning: str = ""

class Instructions(BaseModel):
    """Response model for instruction generation"""
    instructions: str
    instruction_type: str  # "question", "hint", "explanation", "redirect"
    follow_up_questions: List[str] = Field(default_factory=list)
    reasoning: str = ""

class TutorResponse(BaseModel):
    """Comprehensive response from tutor coordinator"""
    feedback_text: str
    instruction_text: Optional[str] = None
    solution_text: Optional[str] = None
    next_question: Optional[str] = None
    
    # Media and Visual Elements
    image_path: Optional[str] = None
    solution_image_path: Optional[str] = None
    
    # Navigation and State
    action: str  # "continue_question", "advance_step", "advance_checkpoint", "finish"
    next_checkpoint: int
    next_step: int
    
    # Additional Information
    completion_message: Optional[str] = None
    error_message: Optional[str] = None
    
    # Metadata
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    def has_media(self) -> bool:
        """Check if response contains media elements"""
        return bool(self.image_path or self.solution_image_path)
    
    def is_progression(self) -> bool:
        """Check if response involves progression to next step/checkpoint"""
        return self.action in ["advance_step", "advance_checkpoint"]
```

### 4. Session Management

#### Session Manager
**File**: `tutor/session/session_manager.py`

```python
from typing import Optional
import uuid
from tutor.models.context import TutorContext
from tutor.models.state import IterationState
from tutor.models.responses import Understanding, TutorResponse
from tutor.services.tutor_coordinator import TutorCoordinator
from tutor.services.exercise_service import ExerciseService
from tutor.services.ui_service import UIService
from tutor.handlers.message_handler import MessageHandler
from tutor.handlers.command_handler import CommandHandler

class SessionManager:
    """
    High-level session management coordinating all services
    and maintaining session state
    """
    
    def __init__(self):
        self.exercise_service = ExerciseService()
        self.tutor_coordinator = TutorCoordinator()
        self.ui_service = UIService()
        self.message_handler = MessageHandler(self.tutor_coordinator)
        self.command_handler = CommandHandler()
    
    async def create_session(
        self,
        exercise_name: str,
        tutor_mode: str,
        user_id: str
    ) -> TutorContext:
        """Create a new tutoring session"""
        
        # Load exercise
        exercise = self.exercise_service.load_exercise(exercise_name)
        
        # Create session context
        context = TutorContext(
            exercise=exercise,
            current_checkpoint=1,
            current_step=1,
            tutor_mode=tutor_mode,
            user_id=user_id,
            session_id=str(uuid.uuid4()),
            iterations=IterationState(),
            current_understanding=Understanding.empty(),
            conversation_history=[]
        )
        
        # Send initial welcome message
        await self._send_welcome_message(context)
        
        return context
    
    async def process_input(
        self,
        user_input: str,
        context: TutorContext
    ) -> TutorContext:
        """Process user input and return updated context"""
        
        # Handle special commands
        if user_input.startswith('/'):
            return await self.command_handler.handle_command(user_input, context)
        
        # Handle regular messages
        return await self.message_handler.handle_message(user_input, context)
    
    async def _send_welcome_message(self, context: TutorContext):
        """Send initial welcome message to start the session"""
        welcome_text = f"""
        Gruezi! Ich bin heute dein Tutor für Statistik.
        
        {context.exercise.first_message}
        
        Wir werden nun einige Fragen durchgehen, die dir helfen sollen, 
        das Konzept besser zu verstehen. Ich werde dir Rückmeldungen und 
        Anleitungen geben, damit du die Aufgaben selbstständig bearbeiten kannst.
        
        Viel Erfolg beim Lernen!
        
        Die Hauptfrage ist:
        {context.current_main_question}
        
        Lass uns zuerst über diese Frage nachdenken:
        {context.current_guiding_question}
        """
        
        response = TutorResponse(
            feedback_text=welcome_text,
            image_path=context.current_image_path,
            action="continue_question",
            next_checkpoint=context.current_checkpoint,
            next_step=context.current_step
        )
        
        await self.ui_service.send_response(response, context)
    
    def get_session_summary(self, context: TutorContext) -> dict:
        """Get summary of current session state"""
        return {
            "session_id": context.session_id,
            "user_id": context.user_id,
            "exercise": context.exercise.metadata.title,
            "tutor_mode": context.tutor_mode,
            "current_checkpoint": context.current_checkpoint,
            "current_step": context.current_step,
            "total_interactions": context.iterations.total_interactions,
            "exercise_complete": context.is_exercise_complete(),
            "conversation_length": len(context.conversation_history)
        }
```

### 5. Configuration Management

#### Centralized Prompts
**File**: `tutor/config/prompts.py`

```python
# System prompts for different agents

UNDERSTANDING_SYSTEM_PROMPT = """
You are a statistical tutor evaluating student understanding.

Your task is to analyze student responses and determine:
1. Whether they have answered the current guiding question
2. Whether they have answered the main question
3. Their level of understanding and any misconceptions

Guidelines:
- Be generous with partial understanding
- Focus on core concepts rather than perfect explanations
- Identify specific misconceptions for targeted feedback
- Consider the student's learning progression
"""

FEEDBACK_SYSTEM_PROMPT = """
You are a supportive statistical tutor providing constructive feedback.

Your feedback should:
1. Start with positive acknowledgment of understanding
2. Address specific misconceptions or gaps
3. Encourage continued learning
4. Never reveal answers directly

Adapt your style based on tutor mode:
- Socratic: Use questions to guide discovery
- Instructional: Provide explanations followed by application
"""

INSTRUCTION_SYSTEM_PROMPT = """
You are a statistical tutor providing guidance to help students discover answers.

Your instructions should:
1. Guide students toward understanding without giving away answers
2. Break complex concepts into manageable steps
3. Use appropriate examples and analogies
4. Adapt to the student's current level of understanding

Never:
- Provide direct answers
- Ask students to perform calculations
- Introduce concepts beyond the current scope
"""

def get_mode_specific_instructions(mode: str) -> str:
    """Get tutor mode specific instructions"""
    if mode == "socratic":
        return """
        Socratic Mode Instructions:
        - Use questions to guide discovery
        - Help students identify their own misconceptions
        - Encourage critical thinking through inquiry
        - Build understanding through guided questioning
        """
    elif mode == "instructional":
        return """
        Instructional Mode Instructions:
        - Provide clear explanations of concepts
        - Use examples to illustrate abstract ideas
        - Break down complex topics into steps
        - Help students apply concepts to specific problems
        """
    return ""
```

This new architecture provides:

1. **Clear Separation of Concerns**: Each layer has distinct responsibilities
2. **Type Safety**: Full Pydantic validation throughout
3. **Testability**: Dependency injection enables easy testing
4. **Maintainability**: Modular structure with clear interfaces
5. **Extensibility**: Easy to add new agents, services, or features
6. **Performance**: Efficient agent coordination and state management

The migration to this architecture would result in a more robust, maintainable, and feature-rich tutoring system.
# PydanticAI Migration & Modularization Specification

## Overview

This document outlines the detailed specifications for migrating the tutoring system from the current OpenAI direct integration to PydanticAI framework while implementing a modular architecture.

## Current Architecture Analysis

### Pain Points
1. **State Management**: Manual state passing via `@with_agent_state` decorator (15+ occurrences)
2. **Monolithic Agent Function**: `chat()` function in `tutor/agent.py:343-572` (230+ lines)
3. **Tight Coupling**: Direct dependencies between UI, business logic, and LLM calls
4. **Manual Error Handling**: Custom retry logic and error management
5. **Hard-coded Agent Coordination**: Sequential agent calls without workflow management

### Current Component Responsibilities
- `tutor/agent.py`: Message handling, progression logic, UI coordination
- `tutor/reasoning.py`: LLM agent implementations and prompt engineering
- `tutor/exercise_loader.py`: Exercise loading and validation
- `app.py`: Application initialization and session management

## Target Architecture

### 1. Core PydanticAI Agents

#### 1.1 Understanding Agent
**File**: `tutor/agents/understanding_agent.py`
**Responsibility**: Evaluate student comprehension of current questions

```python
from pydantic_ai import Agent
from tutor.models import Understanding, TutorContext

understanding_agent = Agent(
    'openai:gpt-4o',
    deps_type=TutorContext,
    result_type=Understanding,
    system_prompt="""
    You are a statistical tutor evaluating student understanding.
    Check if the student has answered the current guiding and main questions.
    """
)

@understanding_agent.system_prompt
def get_system_prompt(ctx: RunContext[TutorContext]) -> str:
    return f"""
    Statistical Tutor - Understanding Evaluation

    Current Exercise: {ctx.deps.exercise.metadata.title}
    Checkpoint {ctx.deps.current_checkpoint}: {ctx.deps.current_main_question}
    Current Step {ctx.deps.current_step}: {ctx.deps.current_guiding_question}

    Evaluate if the student has demonstrated understanding of:
    1. The current guiding question concept
    2. The main question if all guiding questions are complete
    """
```

#### 1.2 Feedback Agent
**File**: `tutor/agents/feedback_agent.py`
**Responsibility**: Provide constructive feedback on student responses

```python
feedback_agent = Agent(
    'openai:gpt-4o',
    deps_type=TutorContext,
    result_type=Feedback,
)

@feedback_agent.system_prompt
def get_feedback_prompt(ctx: RunContext[TutorContext]) -> str:
    mode_instructions = get_mode_instructions(ctx.deps.tutor_mode)
    return f"""
    Statistical Tutor - Feedback Generation

    Mode: {ctx.deps.tutor_mode}
    {mode_instructions}

    Provide constructive feedback following these principles:
    1. Start with positive acknowledgment
    2. Address misconceptions or gaps
    3. Never reveal answers directly
    """
```

#### 1.3 Instruction Agent
**File**: `tutor/agents/instruction_agent.py`
**Responsibility**: Generate next steps and guidance based on tutor mode

```python
instruction_agent = Agent(
    'openai:gpt-4o',
    deps_type=TutorContext,
    result_type=Instructions,
)

@instruction_agent.system_prompt
def get_instruction_prompt(ctx: RunContext[TutorContext]) -> str:
    return f"""
    Statistical Tutor - Instruction Generation

    Mode: {ctx.deps.tutor_mode}
    Generate the next instruction to help the student answer the current question.
    Never give away answers, guide discovery instead.
    """
```

### 2. Dependency Models

#### 2.1 Tutor Context
**File**: `tutor/models/context.py`

```python
from pydantic import BaseModel
from typing import List, Optional
from tutor.exercise_model import Exercise

class TutorContext(BaseModel):
    # Exercise Information
    exercise: Exercise
    current_checkpoint: int
    current_step: int

    # Session State
    tutor_mode: str  # 'socratic' | 'instructional'
    conversation_history: List[dict]
    current_understanding: Understanding

    # Progression State
    iterations: IterationState

    # Configuration
    max_step_iterations: int = 2
    max_checkpoint_iterations: int = 6

    @property
    def current_main_question(self) -> str:
        return self.exercise.checkpoints[self.current_checkpoint - 1].main_question

    @property
    def current_guiding_question(self) -> str:
        checkpoint = self.exercise.checkpoints[self.current_checkpoint - 1]
        return checkpoint.steps[self.current_step - 1].guiding_question

    @property
    def current_main_answer(self) -> str:
        return self.exercise.checkpoints[self.current_checkpoint - 1].main_answer
```

#### 2.2 Iteration State
**File**: `tutor/models/state.py`

```python
class IterationState(BaseModel):
    total_interactions: int = 0
    step_interactions: int = 0
    checkpoint_interactions: int = 0
    finished: bool = False

    def increment(self):
        self.total_interactions += 1
        self.step_interactions += 1
        self.checkpoint_interactions += 1

    def reset_step(self):
        self.step_interactions = 0

    def reset_checkpoint(self):
        self.checkpoint_interactions = 0
        self.reset_step()
```

### 3. Service Layer

#### 3.1 Tutor Coordinator Service
**File**: `tutor/services/tutor_coordinator.py`

```python
from pydantic_ai import Agent
from tutor.agents import understanding_agent, feedback_agent, instruction_agent
from tutor.models import TutorContext, TutorResponse

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
        """
        Coordinate the three-agent workflow to process student input
        """
        # Phase 1: Check Understanding
        understanding = await self.understanding_agent.run(
            message,
            deps=context
        )
        context.current_understanding = understanding

        # Phase 2: Generate Feedback
        feedback = await self.feedback_agent.run(
            message,
            deps=context
        )

        # Phase 3: Determine Next Action
        next_action = self._determine_progression(understanding, context)

        if next_action == "continue_question":
            instructions = await self.instruction_agent.run(
                message,
                deps=context
            )
            return TutorResponse(
                feedback=feedback.feedback,
                instructions=instructions.instructions,
                action=next_action
            )

        elif next_action in ["next_step", "next_checkpoint"]:
            return TutorResponse(
                feedback=feedback.feedback,
                action=next_action,
                solution_text=self._get_solution_text(context, next_action)
            )

        return TutorResponse(feedback=feedback.feedback, action="finish")

    def _determine_progression(
        self,
        understanding: Understanding,
        context: TutorContext
    ) -> str:
        """Determine the next action based on understanding and iteration limits"""
        if understanding.main_question_answered or not context.iterations.has_checkpoint_iterations_left():
            return "next_checkpoint"
        elif understanding.guiding_question_answered or not context.iterations.has_step_iterations_left():
            return "next_step"
        else:
            return "continue_question"
```

#### 3.2 Exercise Service
**File**: `tutor/services/exercise_service.py`

```python
class ExerciseService:
    def __init__(self, exercises_dir: str = "exercises"):
        self.exercises_dir = exercises_dir
        self.loader = ExerciseLoader()

    def load_exercise(self, exercise_name: str) -> Exercise:
        """Load and validate exercise"""
        exercise_path = os.path.join(self.exercises_dir, exercise_name, "exercise.yaml")
        return self.loader.load(exercise_path)

    def get_checkpoint_content(
        self,
        exercise: Exercise,
        checkpoint_num: int,
        step_num: int
    ) -> CheckpointContent:
        """Get structured content for current checkpoint/step"""
        checkpoint = exercise.checkpoints[checkpoint_num - 1]
        step = checkpoint.steps[step_num - 1] if step_num <= len(checkpoint.steps) else None

        return CheckpointContent(
            main_question=checkpoint.main_question,
            main_answer=checkpoint.main_answer,
            guiding_question=step.guiding_question if step else None,
            guiding_answer=step.guiding_answer if step else None,
            image_path=step.image if step else None,
            solution_image_path=checkpoint.image_solution
        )
```

#### 3.3 UI Service
**File**: `tutor/services/ui_service.py`

```python
import chainlit as cl
from tutor.models import TutorResponse, TutorContext

class UIService:
    @staticmethod
    async def send_tutor_response(response: TutorResponse, context: TutorContext):
        """Send tutor response to Chainlit UI"""
        message_text = response.feedback

        if response.instructions:
            message_text += f"\n\n{response.instructions}"

        if response.solution_text:
            message_text += f"\n\n{response.solution_text}"

        # Handle images
        elements = []
        if response.image_path and os.path.exists(response.image_path):
            elements.append(cl.Image(
                name=f"Step-{context.current_step}",
                path=response.image_path
            ))

        await cl.Message(content=message_text, elements=elements).send()

        # Update sidebar if needed
        if response.solution_image_path:
            await UIService.update_sidebar(response.solution_image_path, context)

    @staticmethod
    async def update_sidebar(image_path: str, context: TutorContext):
        """Update sidebar with solution image"""
        if os.path.exists(image_path):
            element = cl.Image(
                name=f"Solution-CP{context.current_checkpoint}",
                path=image_path
            )
            await cl.ElementSidebar.set_elements([element])
            await cl.ElementSidebar.set_title(f"Checkpoint {context.current_checkpoint} Solution")
```

### 4. Application Layer

#### 4.1 Session Manager
**File**: `tutor/session/session_manager.py`

```python
class SessionManager:
    def __init__(self):
        self.exercise_service = ExerciseService()
        self.tutor_coordinator = TutorCoordinator()
        self.ui_service = UIService()

    async def initialize_session(
        self,
        exercise_name: str,
        tutor_mode: str,
        user_id: str
    ) -> TutorContext:
        """Initialize a new tutoring session"""
        exercise = self.exercise_service.load_exercise(exercise_name)

        context = TutorContext(
            exercise=exercise,
            current_checkpoint=1,
            current_step=1,
            tutor_mode=tutor_mode,
            conversation_history=[],
            current_understanding=Understanding.empty(),
            iterations=IterationState()
        )

        # Send initial message
        await self._send_initial_message(context)
        return context

    async def process_message(
        self,
        message: str,
        context: TutorContext
    ) -> TutorContext:
        """Process student message and update context"""
        # Update conversation history
        context.conversation_history.append({
            "role": "user",
            "content": message
        })

        # Increment iterations
        context.iterations.increment()

        # Get tutor response
        response = await self.tutor_coordinator.process_student_message(
            message,
            context
        )

        # Update context based on response
        updated_context = self._update_context_from_response(context, response)

        # Send UI response
        await self.ui_service.send_tutor_response(response, updated_context)

        return updated_context
```

#### 4.2 Refactored App Entry Point
**File**: `app.py`

```python
import chainlit as cl
from tutor.session.session_manager import SessionManager
from tutor.models import TutorContext

session_manager = SessionManager()

@cl.on_chat_start
async def start():
    """Initialize tutoring session"""
    # Get configuration
    exercise_name = os.getenv("EXERCISE_NAME", "t-test")
    tutor_mode = get_tutor_mode()  # From headers/params/random
    user_id = get_user_id()

    # Initialize session
    context = await session_manager.initialize_session(
        exercise_name,
        tutor_mode,
        user_id
    )

    # Store in Chainlit session
    cl.user_session.set("tutor_context", context)

@cl.on_message
async def handle_message(message: cl.Message):
    """Handle student messages"""
    context = cl.user_session.get("tutor_context")

    # Handle special commands
    if message.content.startswith("/goto"):
        context = await handle_goto_command(message.content, context)
    else:
        context = await session_manager.process_message(
            message.content,
            context
        )

    # Update session
    cl.user_session.set("tutor_context", context)
```

## Migration Phases

### Phase 1: Foundation (Week 1)
1. **Install PydanticAI**: Add to requirements.txt
2. **Create Models**: Implement `TutorContext`, `IterationState`, response models
3. **Create Agent Skeleton**: Basic agent structure without full implementation
4. **Unit Tests**: Test models and basic agent instantiation

### Phase 2: Agent Migration (Week 2)
1. **Migrate Understanding Agent**: Replace `TutorCheckUnderstanding`
2. **Migrate Feedback Agent**: Replace `TutorFeedback`
3. **Migrate Instruction Agent**: Replace `TutorInstructions`
4. **Integration Tests**: Test agent coordination

### Phase 3: Service Layer (Week 3)
1. **Implement TutorCoordinator**: Replace manual agent orchestration
2. **Create ExerciseService**: Extract exercise operations
3. **Create UIService**: Separate UI concerns
4. **End-to-End Tests**: Test complete workflow

### Phase 4: Application Refactor (Week 4)
1. **Implement SessionManager**: Replace current session handling
2. **Refactor app.py**: Use new architecture
3. **Remove Legacy Code**: Clean up old implementations
4. **Performance Testing**: Ensure no regression

### Phase 5: Optimization (Week 5)
1. **Error Handling**: Implement comprehensive error handling
2. **Logging Integration**: Integrate with existing logging system
3. **Configuration**: Make agents configurable
4. **Documentation**: Update documentation and examples

## Breaking Changes

### Removed Components
- `@with_agent_state` decorator and `tutor/helper.py`
- `TutorBasic`, `TutorCheckUnderstanding`, `TutorFeedback`, `TutorInstructions` classes
- Manual state management in `agent.py`
- Direct OpenAI client usage

### Modified Components
- `app.py`: Simplified to use SessionManager
- Exercise models: Enhanced with better type safety
- Logging: Adapted to work with PydanticAI conversation history

## Testing Strategy

### Unit Tests
- **Agent Tests**: Mock dependencies, test individual agent responses
- **Model Tests**: Validate Pydantic models and serialization
- **Service Tests**: Test business logic without UI dependencies

### Integration Tests
- **Agent Coordination**: Test multi-agent workflows
- **Session Management**: Test complete session lifecycle
- **Exercise Loading**: Test exercise compatibility

### End-to-End Tests
- **Complete Workflows**: Test full tutoring sessions
- **Error Scenarios**: Test error handling and recovery
- **Performance**: Measure response times and resource usage

## Configuration

### Environment Variables
```bash
# PydanticAI Configuration
PYDANTIC_AI_MODEL=openai:gpt-4o
PYDANTIC_AI_TEMPERATURE=0.5
PYDANTIC_AI_MAX_TOKENS=1000

# Application Configuration
EXERCISE_NAME=t-test
TUTOR_MODE=socratic
EXERCISES_DIR=exercises
```

### Agent Configuration
```python
# tutor/config/agent_config.py
class AgentConfig(BaseModel):
    model: str = "openai:gpt-4o"
    temperature: float = 0.5
    max_tokens: int = 1000
    timeout: int = 30
    max_retries: int = 3
```

## Benefits Summary

1. **Reduced Complexity**: ~40% reduction in codebase size
2. **Type Safety**: Full type checking with mypy/pyright
3. **Better Testing**: Dependency injection enables easier mocking
4. **Improved Maintainability**: Clear separation of concerns
5. **Enhanced Error Handling**: Built-in retry and error management
6. **Future-Proof**: Model-agnostic design for easy provider switching

## Risk Mitigation

1. **Gradual Migration**: Phase-by-phase approach minimizes risk
2. **Comprehensive Testing**: Extensive test coverage ensures reliability
3. **Backward Compatibility**: Exercise format remains unchanged
4. **Rollback Plan**: Keep current implementation until migration complete
5. **Performance Monitoring**: Track metrics throughout migration

This specification provides a comprehensive roadmap for migrating to PydanticAI while achieving a more modular, maintainable architecture.

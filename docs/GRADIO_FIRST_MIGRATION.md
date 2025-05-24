# Gradio-First Migration Strategy: PydanticAI + Multi-Tab Interface

## Revised Migration Approach

**Why Gradio First?**
- Gradio's tab system perfectly matches your evaluation requirements
- Simpler state management across UI components
- Better form handling for user feedback
- Faster development with less UI complexity
- Can implement PydanticAI agents AND Gradio UI simultaneously

## New Migration Timeline (4 Weeks Total)

### Phase 1: Foundation + Gradio Setup (Week 1)
**Day 1-2: Environment & Models**
```bash
# Install dependencies
pip install pydantic-ai gradio>=4.36.1

# Create structure
mkdir -p tutor/{agents,services,models,ui}
```

**Day 3-4: Core Models + Basic Gradio Shell**
```python
# tutor/models/responses.py (same as before)
# tutor/models/context.py (same as before)

# tutor/ui/gradio_app.py - Basic shell
import gradio as gr

def create_basic_app():
    with gr.Blocks(title="Statistical Tutor") as app:
        with gr.Tab("📚 Tutoring"):
            gr.Markdown("Tutoring interface coming soon...")
        
        with gr.Tab("📊 Evaluations"):
            gr.Markdown("Evaluation interface coming soon...")
    
    return app

if __name__ == "__main__":
    app = create_basic_app()
    app.launch()
```

**Day 5-7: PydanticAI Agents (Simplified)**
```python
# tutor/agents/understanding_agent.py
from pydantic_ai import Agent
from tutor.models.responses import Understanding

# Start simple without full context integration
understanding_agent = Agent(
    'openai:gpt-4o',
    result_type=Understanding,
    system_prompt="""
    You are evaluating student understanding of statistical concepts.
    Determine if they answered the current question correctly.
    """
)

# Test agents work independently first
async def test_agent():
    result = await understanding_agent.run("I think we need a t-test")
    print(f"Result: {result}")
```

### Phase 2: Gradio Chat Interface + Agent Integration (Week 2)

**Day 1-3: Implement Chat Tab**
```python
# tutor/ui/chat_interface.py
import gradio as gr
from tutor.agents import understanding_agent, feedback_agent, instruction_agent

class ChatInterface:
    def __init__(self):
        self.understanding_agent = understanding_agent
        self.feedback_agent = feedback_agent
        self.instruction_agent = instruction_agent
    
    def create_chat_tab(self):
        with gr.Tab("📚 Tutoring Session"):
            with gr.Row():
                with gr.Column(scale=2):
                    chatbot = gr.Chatbot(
                        label="Statistical Tutor",
                        height=500,
                        type="messages",
                        show_copy_button=True
                    )
                    
                    with gr.Row():
                        msg = gr.Textbox(
                            placeholder="Type your response...",
                            scale=4,
                            container=False,
                            show_label=False
                        )
                        send_btn = gr.Button("Send", scale=1, variant="primary")
                        clear_btn = gr.Button("Clear", scale=1)
                
                with gr.Column(scale=1):
                    # Exercise context panel
                    with gr.Accordion("Current Exercise", open=True):
                        exercise_title = gr.Markdown("## T-Test Exercise")
                        current_question = gr.Markdown("### Loading question...")
                        progress_info = gr.Markdown("**Progress:** Checkpoint 1, Step 1")
                    
                    # Visual aids
                    with gr.Accordion("Visual Aid", open=False):
                        step_image = gr.Image(
                            label="Step Diagram",
                            visible=False,
                            height=300
                        )
                        solution_image = gr.Image(
                            label="Solution",
                            visible=False,
                            height=300
                        )
                    
                    # Quick actions
                    with gr.Accordion("Actions", open=False):
                        goto_input = gr.Textbox(
                            label="Jump to Checkpoint",
                            placeholder="Enter checkpoint number"
                        )
                        goto_btn = gr.Button("Go", size="sm")
                        
                        tutor_mode = gr.Radio(
                            choices=["socratic", "instructional"],
                            label="Tutor Mode",
                            value="socratic"
                        )
        
        # Return components for event binding
        return {
            'chatbot': chatbot,
            'msg': msg,
            'send_btn': send_btn,
            'clear_btn': clear_btn,
            'exercise_title': exercise_title,
            'current_question': current_question,
            'progress_info': progress_info,
            'step_image': step_image,
            'solution_image': solution_image,
            'goto_input': goto_input,
            'goto_btn': goto_btn,
            'tutor_mode': tutor_mode
        }
    
    async def process_message(self, message, history, session_state):
        """Process student message through PydanticAI agents"""
        try:
            # Simple agent coordination (will enhance in Phase 3)
            understanding = await self.understanding_agent.run(message)
            feedback = await self.feedback_agent.run(message)
            
            # Basic response for now
            response_text = feedback.feedback
            
            if not understanding.main_question_answered and not understanding.guiding_question_answered:
                instructions = await self.instruction_agent.run(message)
                response_text += f"\n\n{instructions.instructions}"
            
            # Update history
            history = history or []
            history.append({"role": "user", "content": message})
            history.append({"role": "assistant", "content": response_text})
            
            return history, ""  # Clear input
            
        except Exception as e:
            error_msg = f"Sorry, I encountered an error: {str(e)}"
            history = history or []
            history.append({"role": "user", "content": message})
            history.append({"role": "assistant", "content": error_msg})
            return history, ""

# tutor/ui/gradio_app.py (updated)
from tutor.ui.chat_interface import ChatInterface

class TutorApp:
    def __init__(self):
        self.chat_interface = ChatInterface()
    
    def create_app(self):
        with gr.Blocks(
            title="Statistical Tutor",
            theme=gr.themes.Soft(),
            css=self._get_custom_css()
        ) as app:
            
            # Global state
            session_state = gr.State(value={})
            
            # Create tabs
            chat_components = self.chat_interface.create_chat_tab()
            self._create_evaluation_tab()
            self._create_progress_tab()
            self._create_settings_tab()
            
            # Wire up chat events
            self._setup_chat_events(chat_components, session_state)
        
        return app
    
    def _setup_chat_events(self, components, session_state):
        """Setup event handlers for chat interface"""
        
        def handle_message(message, history, state):
            return self.chat_interface.process_message(message, history, state)
        
        def clear_chat():
            return [], ""
        
        # Send button
        components['send_btn'].click(
            handle_message,
            inputs=[components['msg'], components['chatbot'], session_state],
            outputs=[components['chatbot'], components['msg']]
        )
        
        # Enter key
        components['msg'].submit(
            handle_message,
            inputs=[components['msg'], components['chatbot'], session_state],
            outputs=[components['chatbot'], components['msg']]
        )
        
        # Clear button
        components['clear_btn'].click(
            clear_chat,
            outputs=[components['chatbot'], components['msg']]
        )
```

**Day 4-5: Basic Context Integration**
```python
# tutor/services/simple_coordinator.py
from tutor.models.context import SimpleTutorContext
from tutor.agents import understanding_agent, feedback_agent, instruction_agent

class SimpleTutorCoordinator:
    """Simplified coordinator for initial Gradio integration"""
    
    def __init__(self):
        self.understanding_agent = understanding_agent
        self.feedback_agent = feedback_agent
        self.instruction_agent = instruction_agent
    
    async def process_message(self, message: str, context: dict) -> dict:
        """Process message and return response with updated context"""
        
        # Create simple context for agents
        simple_context = SimpleTutorContext(
            current_question=context.get('current_question', 'What is a t-test?'),
            current_answer=context.get('current_answer', 'A statistical test...'),
            tutor_mode=context.get('tutor_mode', 'socratic'),
            step_number=context.get('step', 1)
        )
        
        # Run agents
        understanding = await self.understanding_agent.run(message, deps=simple_context)
        feedback = await self.feedback_agent.run(message, deps=simple_context)
        
        response = {
            'feedback': feedback.feedback,
            'instructions': None,
            'action': 'continue',
            'understanding': understanding
        }
        
        # Generate instructions if needed
        if not understanding.main_question_answered:
            instructions = await self.instruction_agent.run(message, deps=simple_context)
            response['instructions'] = instructions.instructions
        
        # Update context
        updated_context = context.copy()
        updated_context['last_understanding'] = understanding
        updated_context['message_count'] = context.get('message_count', 0) + 1
        
        return response, updated_context
```

**Day 6-7: Exercise Loading Integration**
```python
# Integrate existing ExerciseLoader with Gradio
# Update chat interface to load real exercise content
# Test with actual t-test exercise
```

### Phase 3: Evaluation Tab + Full Context (Week 3)

**Day 1-3: Evaluation Interface**
```python
# tutor/ui/evaluation_interface.py
import gradio as gr
from datetime import datetime
import pandas as pd

class EvaluationInterface:
    def create_evaluation_tab(self):
        with gr.Tab("📊 Exercise Evaluation"):
            gr.Markdown("## Evaluate Your Learning Experience")
            
            with gr.Row():
                with gr.Column(scale=1):
                    # Exercise selection
                    exercise_selector = gr.Dropdown(
                        choices=["t-test", "anova", "regression", "chi-square"],
                        label="Exercise Evaluated",
                        value="t-test"
                    )
                    
                    # Rating sections
                    with gr.Group():
                        gr.Markdown("### Content Quality")
                        clarity_rating = gr.Slider(
                            minimum=1, maximum=5, step=1, value=3,
                            label="Question Clarity"
                        )
                        difficulty_rating = gr.Slider(
                            minimum=1, maximum=5, step=1, value=3,
                            label="Appropriate Difficulty"
                        )
                        coverage_rating = gr.Slider(
                            minimum=1, maximum=5, step=1, value=3,
                            label="Topic Coverage"
                        )
                    
                    with gr.Group():
                        gr.Markdown("### Tutoring Experience")
                        engagement_rating = gr.Slider(
                            minimum=1, maximum=5, step=1, value=3,
                            label="Engagement Level"
                        )
                        feedback_quality = gr.Slider(
                            minimum=1, maximum=5, step=1, value=3,
                            label="Feedback Quality"
                        )
                        pacing_rating = gr.Slider(
                            minimum=1, maximum=5, step=1, value=3,
                            label="Learning Pace"
                        )
                    
                    # Text feedback
                    with gr.Group():
                        gr.Markdown("### Additional Feedback")
                        positive_feedback = gr.Textbox(
                            label="What worked well?",
                            lines=3,
                            placeholder="Describe positive aspects..."
                        )
                        improvement_feedback = gr.Textbox(
                            label="What could be improved?",
                            lines=3,
                            placeholder="Suggest improvements..."
                        )
                        general_comments = gr.Textbox(
                            label="General Comments",
                            lines=3,
                            placeholder="Any other thoughts..."
                        )
                    
                    # Submission
                    submit_btn = gr.Button("Submit Evaluation", variant="primary")
                    status_msg = gr.Textbox(label="Status", interactive=False)
                
                with gr.Column(scale=1):
                    # Results visualization
                    gr.Markdown("### Evaluation Summary")
                    
                    # Recent evaluations table
                    evaluations_df = gr.DataFrame(
                        label="Recent Evaluations",
                        headers=["Date", "Exercise", "Clarity", "Difficulty", "Engagement"],
                        datatype=["str", "str", "number", "number", "number"],
                        row_count=10
                    )
                    
                    # Summary statistics
                    summary_stats = gr.Plot(label="Rating Trends")
                    
                    # Export options
                    with gr.Group():
                        gr.Markdown("### Export Data")
                        date_range = gr.DateRange(label="Date Range")
                        export_btn = gr.Button("Export to CSV", size="sm")
                        download_file = gr.File(label="Download", visible=False)
        
        return {
            'exercise_selector': exercise_selector,
            'ratings': {
                'clarity': clarity_rating,
                'difficulty': difficulty_rating,
                'coverage': coverage_rating,
                'engagement': engagement_rating,
                'feedback_quality': feedback_quality,
                'pacing': pacing_rating
            },
            'feedback': {
                'positive': positive_feedback,
                'improvement': improvement_feedback,
                'general': general_comments
            },
            'submit_btn': submit_btn,
            'status_msg': status_msg,
            'evaluations_df': evaluations_df,
            'summary_stats': summary_stats,
            'export_btn': export_btn,
            'download_file': download_file
        }
    
    async def submit_evaluation(self, exercise, ratings, feedback_texts):
        """Handle evaluation submission"""
        try:
            evaluation_data = {
                'timestamp': datetime.now().isoformat(),
                'exercise': exercise,
                'ratings': ratings,
                'feedback': feedback_texts,
                'user_id': 'gradio_user'  # Will be dynamic later
            }
            
            # Save to database/file
            await self._save_evaluation(evaluation_data)
            
            # Update summary display
            updated_df = await self._get_recent_evaluations()
            
            return "Evaluation submitted successfully!", updated_df
            
        except Exception as e:
            return f"Error submitting evaluation: {str(e)}", None
    
    async def _save_evaluation(self, data):
        """Save evaluation data (implement based on your storage needs)"""
        # Could save to JSON, CSV, database, etc.
        import json
        import os
        
        eval_file = "data/evaluations.json"
        os.makedirs(os.path.dirname(eval_file), exist_ok=True)
        
        # Load existing data
        evaluations = []
        if os.path.exists(eval_file):
            with open(eval_file, 'r') as f:
                evaluations = json.load(f)
        
        # Add new evaluation
        evaluations.append(data)
        
        # Save back
        with open(eval_file, 'w') as f:
            json.dump(evaluations, f, indent=2)
    
    async def _get_recent_evaluations(self):
        """Get recent evaluations for display"""
        try:
            import json
            with open("data/evaluations.json", 'r') as f:
                evaluations = json.load(f)
            
            # Convert to DataFrame format
            df_data = []
            for eval_data in evaluations[-10:]:  # Last 10 evaluations
                df_data.append([
                    eval_data['timestamp'][:10],  # Date only
                    eval_data['exercise'],
                    eval_data['ratings']['clarity'],
                    eval_data['ratings']['difficulty'],
                    eval_data['ratings']['engagement']
                ])
            
            return df_data
            
        except Exception:
            return []  # Return empty if no data
```

**Day 4-5: Progress Dashboard**
```python
# tutor/ui/progress_interface.py
import gradio as gr
import plotly.graph_objects as go
import plotly.express as px

class ProgressInterface:
    def create_progress_tab(self):
        with gr.Tab("📈 Progress Dashboard"):
            with gr.Row():
                with gr.Column():
                    gr.Markdown("## Learning Progress")
                    
                    # Session overview
                    with gr.Group():
                        gr.Markdown("### Current Session")
                        session_info = gr.Markdown("Loading session data...")
                        
                        session_stats = gr.DataFrame(
                            label="Session Statistics",
                            headers=["Metric", "Value"],
                            row_count=5
                        )
                    
                    # Exercise completion
                    with gr.Group():
                        gr.Markdown("### Exercise Completion")
                        completion_chart = gr.Plot(label="Completion Rate by Exercise")
                    
                    # Performance trends
                    with gr.Group():
                        gr.Markdown("### Performance Trends")
                        performance_chart = gr.Plot(label="Understanding Over Time")
                
                with gr.Column():
                    # Detailed analytics
                    gr.Markdown("## Detailed Analytics")
                    
                    # Time analysis
                    with gr.Group():
                        gr.Markdown("### Time Analysis")
                        time_chart = gr.Plot(label="Time Spent per Checkpoint")
                    
                    # Interaction patterns
                    with gr.Group():
                        gr.Markdown("### Interaction Patterns")
                        interaction_chart = gr.Plot(label="Questions vs Iterations")
                    
                    # Learning insights
                    with gr.Group():
                        gr.Markdown("### Learning Insights")
                        insights_text = gr.Markdown("Generating insights...")
                        
                        # Recommendations
                        recommendations = gr.DataFrame(
                            label="Recommended Next Steps",
                            headers=["Recommendation", "Priority"],
                            row_count=3
                        )
        
        return {
            'session_info': session_info,
            'session_stats': session_stats,
            'completion_chart': completion_chart,
            'performance_chart': performance_chart,
            'time_chart': time_chart,
            'interaction_chart': interaction_chart,
            'insights_text': insights_text,
            'recommendations': recommendations
        }
```

**Day 6-7: Full Context Integration**
```python
# Integrate full TutorContext with all tabs
# Add state synchronization between tabs
# Implement session persistence
```

### Phase 4: Polish + Advanced Features (Week 4)

**Day 1-2: Settings & Configuration**
```python
# tutor/ui/settings_interface.py
class SettingsInterface:
    def create_settings_tab(self):
        with gr.Tab("⚙️ Settings"):
            with gr.Row():
                with gr.Column():
                    gr.Markdown("## Exercise Settings")
                    
                    exercise_selection = gr.Dropdown(
                        choices=["t-test", "anova", "regression"],
                        label="Current Exercise",
                        value="t-test"
                    )
                    
                    tutor_mode_setting = gr.Radio(
                        choices=["socratic", "instructional"],
                        label="Tutor Mode",
                        value="socratic"
                    )
                    
                    difficulty_level = gr.Slider(
                        minimum=1, maximum=5, step=1, value=3,
                        label="Difficulty Level"
                    )
                
                with gr.Column():
                    gr.Markdown("## User Preferences")
                    
                    language_setting = gr.Radio(
                        choices=["German", "English"],
                        label="Interface Language",
                        value="German"
                    )
                    
                    feedback_verbosity = gr.Slider(
                        minimum=1, maximum=5, step=1, value=3,
                        label="Feedback Detail Level"
                    )
                    
                    enable_hints = gr.Checkbox(
                        label="Enable Hints",
                        value=True
                    )
            
            # Save/Reset buttons
            with gr.Row():
                save_settings_btn = gr.Button("Save Settings", variant="primary")
                reset_settings_btn = gr.Button("Reset to Defaults")
                export_settings_btn = gr.Button("Export Settings")
        
        return {
            'exercise_selection': exercise_selection,
            'tutor_mode_setting': tutor_mode_setting,
            'difficulty_level': difficulty_level,
            'language_setting': language_setting,
            'feedback_verbosity': feedback_verbosity,
            'enable_hints': enable_hints,
            'save_settings_btn': save_settings_btn,
            'reset_settings_btn': reset_settings_btn,
            'export_settings_btn': export_settings_btn
        }
```

**Day 3-4: Advanced Chat Features**
```python
# Add features to chat interface:
# - Message export
# - Session save/load
# - Conversation branching
# - Multi-language support
# - Accessibility features
```

**Day 5-7: Testing & Deployment**
```python
# tutor/ui/gradio_app.py (Final version)
import gradio as gr
from tutor.ui.chat_interface import ChatInterface
from tutor.ui.evaluation_interface import EvaluationInterface
from tutor.ui.progress_interface import ProgressInterface
from tutor.ui.settings_interface import SettingsInterface
from tutor.services.session_service import SessionService

class TutorApp:
    def __init__(self):
        self.chat_interface = ChatInterface()
        self.evaluation_interface = EvaluationInterface()
        self.progress_interface = ProgressInterface()
        self.settings_interface = SettingsInterface()
        self.session_service = SessionService()
    
    def create_app(self):
        with gr.Blocks(
            title="Statistical Tutor - Interactive Learning Platform",
            theme=gr.themes.Soft(
                primary_hue="blue",
                secondary_hue="cyan",
                neutral_hue="slate"
            ),
            css=self._get_custom_css(),
            head=self._get_custom_head()
        ) as app:
            
            # Global state
            session_state = gr.State(value=self._initialize_session())
            
            # Header
            with gr.Row():
                gr.Markdown("# 📊 Statistical Tutor", elem_id="header")
                
                with gr.Column(scale=1):
                    user_info = gr.Markdown("👤 User: Student", elem_id="user-info")
            
            # Main tabs
            chat_components = self.chat_interface.create_chat_tab()
            eval_components = self.evaluation_interface.create_evaluation_tab()
            progress_components = self.progress_interface.create_progress_tab()
            settings_components = self.settings_interface.create_settings_tab()
            
            # Event bindings
            self._setup_all_events(
                chat_components, eval_components, 
                progress_components, settings_components, 
                session_state
            )
        
        return app
    
    def launch(self, **kwargs):
        """Launch the Gradio app"""
        app = self.create_app()
        return app.launch(
            server_name="0.0.0.0",
            server_port=7860,
            share=False,
            **kwargs
        )

# Launch script
if __name__ == "__main__":
    app = TutorApp()
    app.launch()
```

## Key Benefits of Gradio-First Approach

**1. Faster Development**
- Tab system ready out-of-the-box
- Built-in form components for evaluations
- Simple state management across tabs

**2. Better User Experience**
- Evaluation forms alongside tutoring
- Progress dashboard with real-time updates
- Settings that persist across sessions

**3. Easier Testing**
- Can test UI and agents independently
- Gradio's built-in sharing for demos
- Component-level testing possible

**4. Future-Proof Architecture**
- PydanticAI agents work with any UI
- Modular design allows UI swapping
- API endpoints for external integrations

This approach gets you a working multi-tab application with PydanticAI integration in 4 weeks instead of 5+, while delivering the evaluation features you need from day one.
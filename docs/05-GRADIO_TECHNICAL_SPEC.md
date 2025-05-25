# Gradio Technical Integration Specification

## Technical Architecture: Gradio + PydanticAI

### Core Integration Pattern

```python
# tutor/ui/gradio_bridge.py
"""
Bridge between Gradio UI components and PydanticAI service layer
"""

from typing import Dict, Any, Tuple, Optional
from tutor.services.session_service import SessionService
from tutor.models.context import TutorContext
from tutor.models.responses import TutorResponse

class GradioTutorBridge:
    """Handles conversion between Gradio state and PydanticAI context"""
    
    def __init__(self):
        self.session_service = SessionService()
    
    def gradio_to_context(self, gradio_state: Dict) -> TutorContext:
        """Convert Gradio state to TutorContext"""
        return TutorContext(
            exercise=gradio_state['exercise'],
            current_checkpoint=gradio_state['current_checkpoint'],
            current_step=gradio_state['current_step'],
            tutor_mode=gradio_state['tutor_mode'],
            user_id=gradio_state['user_id'],
            session_id=gradio_state['session_id'],
            iterations=gradio_state['iterations'],
            current_understanding=gradio_state['current_understanding'],
            conversation_history=gradio_state['conversation_history']
        )
    
    def context_to_gradio(self, context: TutorContext) -> Dict:
        """Convert TutorContext back to Gradio state"""
        return {
            'exercise': context.exercise,
            'current_checkpoint': context.current_checkpoint,
            'current_step': context.current_step,
            'tutor_mode': context.tutor_mode,
            'user_id': context.user_id,
            'session_id': context.session_id,
            'iterations': context.iterations,
            'current_understanding': context.current_understanding,
            'conversation_history': context.conversation_history,
            'last_updated': datetime.utcnow().isoformat()
        }
    
    def tutor_response_to_gradio(self, response: TutorResponse) -> Dict:
        """Convert TutorResponse to Gradio-compatible format"""
        return {
            'message': response.feedback_text,
            'instructions': response.instruction_text,
            'image_path': response.image_path,
            'solution_image_path': response.solution_image_path,
            'action': response.action,
            'metadata': {
                'next_checkpoint': response.next_checkpoint,
                'next_step': response.next_step,
                'has_progression': response.is_progression(),
                'has_media': response.has_media()
            }
        }
```

## State Management Strategy

### Global State Schema
```python
# tutor/models/gradio_state.py
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from datetime import datetime

class GradioSessionState(BaseModel):
    """Comprehensive state model for Gradio interface"""
    
    # Session metadata
    session_id: str
    user_id: str
    created_at: datetime
    last_activity: datetime
    
    # Tutoring state
    tutor_context: Optional[TutorContext] = None
    chat_history: List[Dict[str, Any]] = []
    
    # UI state
    active_tab: str = "tutoring"
    chat_input: str = ""
    
    # Settings
    settings: Dict[str, Any] = {
        'exercise_name': 't-test',
        'tutor_mode': 'socratic',
        'language': 'german',
        'difficulty_level': 3,
        'enable_hints': True,
        'feedback_verbosity': 3
    }
    
    # Evaluation data
    evaluations: List[Dict[str, Any]] = []
    
    # Progress tracking
    progress_data: Dict[str, Any] = {
        'exercises_completed': [],
        'time_spent': {},
        'performance_metrics': {}
    }
    
    class Config:
        arbitrary_types_allowed = True

# State management functions
def initialize_gradio_state(user_id: str = "gradio_user") -> GradioSessionState:
    """Initialize fresh Gradio session state"""
    return GradioSessionState(
        session_id=str(uuid.uuid4()),
        user_id=user_id,
        created_at=datetime.utcnow(),
        last_activity=datetime.utcnow()
    )

def update_state_activity(state: GradioSessionState) -> GradioSessionState:
    """Update last activity timestamp"""
    state.last_activity = datetime.utcnow()
    return state
```

### Tab-Specific Components

#### 1. Chat Tab Implementation
```python
# tutor/ui/components/chat_tab.py
import gradio as gr
from tutor.ui.gradio_bridge import GradioTutorBridge

class ChatTab:
    def __init__(self):
        self.bridge = GradioTutorBridge()
    
    def create_interface(self) -> Dict[str, Any]:
        """Create chat tab interface components"""
        
        with gr.Tab("📚 Tutoring Session") as tab:
            with gr.Row():
                # Main chat area
                with gr.Column(scale=3):
                    chatbot = gr.Chatbot(
                        label="Statistical Tutor",
                        height=600,
                        type="messages",
                        show_copy_button=True,
                        bubble_full_width=False,
                        render_markdown=True,
                        latex_delimiters=[
                            {"left": "$$", "right": "$$", "display": True},
                            {"left": "$", "right": "$", "display": False}
                        ]
                    )
                    
                    with gr.Row():
                        msg_input = gr.Textbox(
                            placeholder="Schreibe deine Antwort hier...",
                            scale=4,
                            container=False,
                            show_label=False,
                            max_lines=3
                        )
                        send_btn = gr.Button(
                            "Senden", 
                            scale=1, 
                            variant="primary",
                            size="lg"
                        )
                    
                    with gr.Row():
                        clear_btn = gr.Button("Chat löschen", size="sm")
                        export_btn = gr.Button("Konversation exportieren", size="sm")
                        goto_btn = gr.Button("Zu Checkpoint springen", size="sm")
                
                # Sidebar
                with gr.Column(scale=1):
                    # Exercise context
                    with gr.Accordion("Aktuelle Aufgabe", open=True):
                        exercise_title = gr.Markdown("## Lade Aufgabe...")
                        checkpoint_info = gr.Markdown("**Checkpoint:** 1")
                        step_info = gr.Markdown("**Schritt:** 1")
                        progress_bar = gr.Progress(
                            label="Fortschritt",
                            track_tqdm=True
                        )
                    
                    # Current question display
                    with gr.Accordion("Aktuelle Frage", open=True):
                        current_question = gr.Markdown("Lade Frage...")
                        question_type = gr.Markdown("**Typ:** Leitfrage")
                    
                    # Visual aids
                    with gr.Accordion("Visuelle Hilfen", open=False):
                        step_image = gr.Image(
                            label="Schritt-Diagramm",
                            height=250,
                            visible=False
                        )
                        solution_image = gr.Image(
                            label="Lösung",
                            height=250,
                            visible=False
                        )
                    
                    # Quick actions
                    with gr.Accordion("Aktionen", open=False):
                        goto_input = gr.Number(
                            label="Checkpoint Nummer",
                            minimum=1,
                            maximum=10,
                            step=1,
                            value=1
                        )
                        goto_execute = gr.Button("Springen", size="sm")
                        
                        hint_btn = gr.Button("Hinweis anzeigen", size="sm")
                        skip_btn = gr.Button("Frage überspringen", size="sm")
                    
                    # Session info
                    with gr.Accordion("Session Info", open=False):
                        session_stats = gr.DataFrame(
                            label="Statistiken",
                            headers=["Metrik", "Wert"],
                            datatype=["str", "str"],
                            row_count=5,
                            interactive=False
                        )
        
        return {
            'tab': tab,
            'chatbot': chatbot,
            'msg_input': msg_input,
            'send_btn': send_btn,
            'clear_btn': clear_btn,
            'export_btn': export_btn,
            'goto_btn': goto_btn,
            'exercise_title': exercise_title,
            'checkpoint_info': checkpoint_info,
            'step_info': step_info,
            'progress_bar': progress_bar,
            'current_question': current_question,
            'question_type': question_type,
            'step_image': step_image,
            'solution_image': solution_image,
            'goto_input': goto_input,
            'goto_execute': goto_execute,
            'hint_btn': hint_btn,
            'skip_btn': skip_btn,
            'session_stats': session_stats
        }
    
    async def handle_message(
        self, 
        message: str, 
        history: List[Dict], 
        state: GradioSessionState
    ) -> Tuple[List[Dict], str, GradioSessionState]:
        """Handle user message through PydanticAI"""
        
        try:
            # Convert to TutorContext
            context = self.bridge.gradio_to_context(state.dict())
            
            # Process through service layer
            response, updated_context = await self.bridge.session_service.process_message(
                message, context
            )
            
            # Convert response for Gradio
            gradio_response = self.bridge.tutor_response_to_gradio(response)
            
            # Update chat history
            history = history or []
            history.append({"role": "user", "content": message})
            
            # Format assistant response
            assistant_message = gradio_response['message']
            if gradio_response['instructions']:
                assistant_message += f"\n\n**Nächste Schritte:**\n{gradio_response['instructions']}"
            
            history.append({"role": "assistant", "content": assistant_message})
            
            # Update state
            updated_state = state.copy()
            updated_state.tutor_context = updated_context
            updated_state.chat_history = history
            updated_state = update_state_activity(updated_state)
            
            return history, "", updated_state  # Clear input
            
        except Exception as e:
            error_msg = f"Entschuldigung, es ist ein Fehler aufgetreten: {str(e)}"
            history = history or []
            history.append({"role": "user", "content": message})
            history.append({"role": "assistant", "content": error_msg})
            
            return history, "", state
    
    def handle_goto(
        self, 
        checkpoint_num: int, 
        state: GradioSessionState
    ) -> Tuple[List[Dict], GradioSessionState]:
        """Handle checkpoint navigation"""
        
        try:
            if not state.tutor_context:
                return [], state
            
            # Validate checkpoint number
            max_checkpoints = len(state.tutor_context.exercise.checkpoints)
            if checkpoint_num < 1 or checkpoint_num > max_checkpoints:
                error_msg = f"Checkpoint {checkpoint_num} existiert nicht. Verfügbar: 1-{max_checkpoints}"
                history = state.chat_history.copy()
                history.append({"role": "system", "content": error_msg})
                return history, state
            
            # Update context
            context = state.tutor_context
            context.current_checkpoint = checkpoint_num
            context.current_step = 1
            context.iterations.reset_checkpoint()
            
            # Create navigation message
            checkpoint = context.exercise.checkpoints[checkpoint_num - 1]
            nav_message = f"""
            **Sprung zu Checkpoint {checkpoint_num}**
            
            **Hauptfrage:** {checkpoint.main_question}
            
            **Erste Leitfrage:** {checkpoint.steps[0].guiding_question if checkpoint.steps else "Keine Leitfragen verfügbar"}
            """
            
            # Update history
            history = state.chat_history.copy()
            history.append({"role": "system", "content": nav_message})
            
            # Update state
            updated_state = state.copy()
            updated_state.tutor_context = context
            updated_state.chat_history = history
            updated_state = update_state_activity(updated_state)
            
            return history, updated_state
            
        except Exception as e:
            error_msg = f"Fehler beim Navigieren: {str(e)}"
            history = state.chat_history.copy()
            history.append({"role": "system", "content": error_msg})
            return history, state
```

#### 2. Evaluation Tab Implementation
```python
# tutor/ui/components/evaluation_tab.py
import gradio as gr
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

class EvaluationTab:
    def create_interface(self) -> Dict[str, Any]:
        """Create evaluation tab interface"""
        
        with gr.Tab("📊 Bewertung der Aufgaben") as tab:
            gr.Markdown("## Bewerte deine Lernerfahrung")
            
            with gr.Row():
                # Evaluation form
                with gr.Column(scale=1):
                    # Exercise selection
                    exercise_dropdown = gr.Dropdown(
                        choices=self._get_available_exercises(),
                        label="Bewertete Aufgabe",
                        value="t-test",
                        info="Wähle die Aufgabe, die du bewerten möchtest"
                    )
                    
                    # Content quality ratings
                    with gr.Group():
                        gr.Markdown("### 📝 Inhaltsqualität")
                        
                        clarity_rating = gr.Slider(
                            minimum=1, maximum=5, step=1, value=3,
                            label="Klarheit der Fragen",
                            info="Waren die Fragen verständlich formuliert?"
                        )
                        
                        difficulty_rating = gr.Slider(
                            minimum=1, maximum=5, step=1, value=3,
                            label="Angemessene Schwierigkeit",
                            info="War der Schwierigkeitsgrad passend?"
                        )
                        
                        coverage_rating = gr.Slider(
                            minimum=1, maximum=5, step=1, value=3,
                            label="Themenabdeckung",
                            info="Wurden alle wichtigen Aspekte behandelt?"
                        )
                        
                        accuracy_rating = gr.Slider(
                            minimum=1, maximum=5, step=1, value=3,
                            label="Fachliche Korrektheit",
                            info="Waren die Inhalte fachlich korrekt?"
                        )
                    
                    # Tutoring experience ratings
                    with gr.Group():
                        gr.Markdown("### 🤖 Tutor-Erfahrung")
                        
                        engagement_rating = gr.Slider(
                            minimum=1, maximum=5, step=1, value=3,
                            label="Engagement",
                            info="War die Interaktion motivierend?"
                        )
                        
                        feedback_quality = gr.Slider(
                            minimum=1, maximum=5, step=1, value=3,
                            label="Qualität des Feedbacks",
                            info="War das Feedback hilfreich und konstruktiv?"
                        )
                        
                        pacing_rating = gr.Slider(
                            minimum=1, maximum=5, step=1, value=3,
                            label="Lerntempo",
                            info="War das Tempo angemessen?"
                        )
                        
                        adaptivity_rating = gr.Slider(
                            minimum=1, maximum=5, step=1, value=3,
                            label="Anpassungsfähigkeit",
                            info="Hat sich der Tutor an dein Niveau angepasst?"
                        )
                    
                    # Technical aspects
                    with gr.Group():
                        gr.Markdown("### 💻 Technische Aspekte")
                        
                        usability_rating = gr.Slider(
                            minimum=1, maximum=5, step=1, value=3,
                            label="Benutzerfreundlichkeit",
                            info="War die Benutzeroberfläche intuitiv?"
                        )
                        
                        performance_rating = gr.Slider(
                            minimum=1, maximum=5, step=1, value=3,
                            label="Performance",
                            info="Funktionierte alles reibungslos?"
                        )
                    
                    # Text feedback sections
                    with gr.Group():
                        gr.Markdown("### 💬 Zusätzliches Feedback")
                        
                        positive_feedback = gr.Textbox(
                            label="Was hat gut funktioniert?",
                            lines=3,
                            placeholder="Beschreibe positive Aspekte der Lernerfahrung..."
                        )
                        
                        improvement_feedback = gr.Textbox(
                            label="Was könnte verbessert werden?",
                            lines=3,
                            placeholder="Schlage Verbesserungen vor..."
                        )
                        
                        feature_requests = gr.Textbox(
                            label="Gewünschte neue Features",
                            lines=2,
                            placeholder="Welche Features würdest du dir wünschen?"
                        )
                        
                        general_comments = gr.Textbox(
                            label="Allgemeine Kommentare",
                            lines=3,
                            placeholder="Weitere Gedanken oder Anregungen..."
                        )
                    
                    # Submission
                    with gr.Row():
                        submit_btn = gr.Button(
                            "Bewertung abschicken", 
                            variant="primary",
                            size="lg"
                        )
                        reset_btn = gr.Button(
                            "Formular zurücksetzen",
                            size="lg"
                        )
                    
                    status_msg = gr.Textbox(
                        label="Status",
                        interactive=False,
                        visible=False
                    )
                
                # Results and analytics
                with gr.Column(scale=1):
                    gr.Markdown("### 📈 Bewertungsübersicht")
                    
                    # Summary statistics
                    with gr.Group():
                        summary_stats = gr.DataFrame(
                            label="Zusammenfassung der Bewertungen",
                            headers=["Metrik", "Durchschnitt", "Anzahl"],
                            datatype=["str", "number", "number"],
                            row_count=8,
                            interactive=False
                        )
                    
                    # Recent evaluations
                    with gr.Group():
                        recent_evaluations = gr.DataFrame(
                            label="Letzte Bewertungen",
                            headers=["Datum", "Aufgabe", "Gesamtbewertung", "Kommentar"],
                            datatype=["str", "str", "number", "str"],
                            row_count=10,
                            interactive=False
                        )
                    
                    # Visualization
                    with gr.Group():
                        evaluation_chart = gr.Plot(
                            label="Bewertungstrends",
                            height=300
                        )
                        
                        comparison_chart = gr.Plot(
                            label="Vergleich nach Aufgaben",
                            height=300
                        )
                    
                    # Export options
                    with gr.Group():
                        gr.Markdown("### 📤 Daten exportieren")
                        
                        with gr.Row():
                            date_from = gr.Date(
                                label="Von Datum",
                                value=datetime.now() - timedelta(days=30)
                            )
                            date_to = gr.Date(
                                label="Bis Datum",
                                value=datetime.now()
                            )
                        
                        with gr.Row():
                            export_csv_btn = gr.Button("CSV Export", size="sm")
                            export_json_btn = gr.Button("JSON Export", size="sm")
                        
                        download_file = gr.File(
                            label="Download",
                            visible=False
                        )
        
        return {
            'tab': tab,
            'exercise_dropdown': exercise_dropdown,
            'ratings': {
                'clarity': clarity_rating,
                'difficulty': difficulty_rating,
                'coverage': coverage_rating,
                'accuracy': accuracy_rating,
                'engagement': engagement_rating,
                'feedback_quality': feedback_quality,
                'pacing': pacing_rating,
                'adaptivity': adaptivity_rating,
                'usability': usability_rating,
                'performance': performance_rating
            },
            'feedback_texts': {
                'positive': positive_feedback,
                'improvement': improvement_feedback,
                'features': feature_requests,
                'general': general_comments
            },
            'submit_btn': submit_btn,
            'reset_btn': reset_btn,
            'status_msg': status_msg,
            'summary_stats': summary_stats,
            'recent_evaluations': recent_evaluations,
            'evaluation_chart': evaluation_chart,
            'comparison_chart': comparison_chart,
            'date_from': date_from,
            'date_to': date_to,
            'export_csv_btn': export_csv_btn,
            'export_json_btn': export_json_btn,
            'download_file': download_file
        }
    
    def _get_available_exercises(self) -> List[str]:
        """Get list of available exercises for evaluation"""
        return ["t-test", "anova", "regression", "chi-square", "correlation"]
    
    async def submit_evaluation(
        self,
        exercise: str,
        ratings: Dict[str, int],
        feedback_texts: Dict[str, str],
        state: GradioSessionState
    ) -> Tuple[str, pd.DataFrame, pd.DataFrame, Any, Any]:
        """Handle evaluation submission"""
        
        try:
            # Create evaluation record
            evaluation = {
                'timestamp': datetime.now().isoformat(),
                'exercise': exercise,
                'user_id': state.user_id,
                'session_id': state.session_id,
                'ratings': ratings,
                'feedback': feedback_texts,
                'overall_rating': sum(ratings.values()) / len(ratings),
                'completion_status': 'completed' if state.tutor_context and state.tutor_context.is_exercise_complete() else 'partial'
            }
            
            # Save evaluation
            await self._save_evaluation(evaluation)
            
            # Update state
            state.evaluations.append(evaluation)
            
            # Generate updated displays
            summary_df = self._generate_summary_stats(state.evaluations)
            recent_df = self._generate_recent_evaluations(state.evaluations)
            trend_chart = self._generate_trend_chart(state.evaluations)
            comparison_chart = self._generate_comparison_chart(state.evaluations)
            
            status_message = f"✅ Bewertung für '{exercise}' erfolgreich gespeichert!"
            
            return status_message, summary_df, recent_df, trend_chart, comparison_chart
            
        except Exception as e:
            error_message = f"❌ Fehler beim Speichern der Bewertung: {str(e)}"
            return error_message, None, None, None, None
```

## Event Handling Architecture

```python
# tutor/ui/event_coordinator.py
class EventCoordinator:
    """Coordinates events across all tabs and components"""
    
    def __init__(self, app_components: Dict[str, Any]):
        self.components = app_components
        self.bridge = GradioTutorBridge()
    
    def setup_all_events(self, global_state: gr.State):
        """Setup all event handlers across tabs"""
        
        # Chat tab events
        self._setup_chat_events(global_state)
        
        # Evaluation tab events
        self._setup_evaluation_events(global_state)
        
        # Progress tab events
        self._setup_progress_events(global_state)
        
        # Settings tab events
        self._setup_settings_events(global_state)
        
        # Cross-tab events
        self._setup_cross_tab_events(global_state)
    
    def _setup_chat_events(self, state: gr.State):
        """Setup chat-specific events"""
        chat = self.components['chat']
        
        # Message sending
        chat['send_btn'].click(
            fn=chat['handler'].handle_message,
            inputs=[chat['msg_input'], chat['chatbot'], state],
            outputs=[chat['chatbot'], chat['msg_input'], state],
            api_name="send_message"
        )
        
        chat['msg_input'].submit(
            fn=chat['handler'].handle_message,
            inputs=[chat['msg_input'], chat['chatbot'], state],
            outputs=[chat['chatbot'], chat['msg_input'], state]
        )
        
        # Goto functionality
        chat['goto_execute'].click(
            fn=chat['handler'].handle_goto,
            inputs=[chat['goto_input'], state],
            outputs=[chat['chatbot'], state]
        )
        
        # Clear chat
        chat['clear_btn'].click(
            fn=lambda: ([], ""),
            outputs=[chat['chatbot'], chat['msg_input']]
        )
    
    def _setup_evaluation_events(self, state: gr.State):
        """Setup evaluation-specific events"""
        eval_tab = self.components['evaluation']
        
        # Evaluation submission
        eval_tab['submit_btn'].click(
            fn=eval_tab['handler'].submit_evaluation,
            inputs=[
                eval_tab['exercise_dropdown'],
                *eval_tab['ratings'].values(),
                *eval_tab['feedback_texts'].values(),
                state
            ],
            outputs=[
                eval_tab['status_msg'],
                eval_tab['summary_stats'],
                eval_tab['recent_evaluations'],
                eval_tab['evaluation_chart'],
                eval_tab['comparison_chart']
            ]
        )
    
    def _setup_cross_tab_events(self, state: gr.State):
        """Setup events that affect multiple tabs"""
        
        # Settings changes that affect chat
        settings = self.components['settings']
        chat = self.components['chat']
        
        settings['tutor_mode'].change(
            fn=self._update_tutor_mode,
            inputs=[settings['tutor_mode'], state],
            outputs=[state, chat['exercise_title']]
        )
        
        settings['exercise_selection'].change(
            fn=self._change_exercise,
            inputs=[settings['exercise_selection'], state],
            outputs=[state, chat['chatbot'], chat['current_question']]
        )
    
    async def _update_tutor_mode(self, mode: str, state: GradioSessionState):
        """Update tutor mode across the application"""
        state.settings['tutor_mode'] = mode
        if state.tutor_context:
            state.tutor_context.tutor_mode = mode
        
        update_message = f"Tutor-Modus geändert zu: {mode}"
        return state, update_message
    
    async def _change_exercise(self, exercise: str, state: GradioSessionState):
        """Change current exercise"""
        try:
            # Load new exercise
            new_context = await self.bridge.session_service.create_session(
                exercise_name=exercise,
                tutor_mode=state.settings['tutor_mode'],
                user_id=state.user_id
            )
            
            # Update state
            state.tutor_context = new_context
            state.settings['exercise_name'] = exercise
            state.chat_history = []
            
            # Create initial message
            initial_message = f"""
            **Neue Aufgabe geladen: {exercise}**
            
            {new_context.exercise.first_message}
            
            **Hauptfrage:** {new_context.current_main_question}
            
            **Erste Leitfrage:** {new_context.current_guiding_question}
            """
            
            history = [{"role": "assistant", "content": initial_message}]
            question_display = f"**Aktuelle Frage:** {new_context.current_guiding_question}"
            
            return state, history, question_display
            
        except Exception as e:
            error_msg = f"Fehler beim Laden der Aufgabe: {str(e)}"
            return state, [], error_msg
```

This technical specification provides the complete integration between Gradio's UI system and your PydanticAI service layer, with proper state management, event coordination, and component isolation for maintainability.
import gradio as gr
import os
import asyncio
from typing import Dict, Any, Tuple, List
from tutor.ui.gradio_bridge import GradioTutorBridge
from tutor.ui.components.chat_tab import ChatTab
from tutor.ui.components.evaluation_tab import EvaluationTab
from tutor.models.gradio_state import GradioSessionState, initialize_gradio_state

class TutorApp:
    def __init__(self):
        self.bridge = GradioTutorBridge()
        self.chat_tab = ChatTab()
        self.evaluation_tab = EvaluationTab()
    
    def create_app(self):
        with gr.Blocks(
            title="Statistical Tutor - Interactive Learning Platform",
            theme=gr.themes.Soft(
                primary_hue="blue",
                secondary_hue="cyan",
                neutral_hue="slate"
            ),
            css=self._get_custom_css()
        ) as app:
            
            # Global state
            session_state = gr.State(value=initialize_gradio_state())
            
            # Header
            with gr.Row():
                gr.Markdown("# 📊 Statistical Tutor", elem_id="header")
                
                with gr.Column(scale=1):
                    user_info = gr.Markdown("👤 User: Student", elem_id="user-info")
            
            # Settings row for exercise and mode selection
            with gr.Row():
                with gr.Column(scale=1):
                    exercise_selector = gr.Dropdown(
                        choices=["exercise-12", "t-test", "anova", "regression"],
                        label="Aufgabe auswählen",
                        value="exercise-12",
                        info="Wähle eine Übungsaufgabe"
                    )
                
                with gr.Column(scale=1):
                    mode_selector = gr.Radio(
                        choices=["socratic", "instructional"],
                        label="Tutor Modus",
                        value="socratic",
                        info="Wähle den Lehrstil"
                    )
                
                with gr.Column(scale=1):
                    start_session_btn = gr.Button(
                        "Session starten",
                        variant="primary",
                        size="lg"
                    )
            
            # Status message
            session_status = gr.Markdown("**Status:** Bereit zum Starten", elem_id="status")
            
            # Main tabs
            chat_components = self.chat_tab.create_interface()
            eval_components = self.evaluation_tab.create_interface()
            
            # Progress tab placeholder
            with gr.Tab("📈 Fortschritt"):
                gr.Markdown("## Lernfortschritt")
                gr.Markdown("*Fortschritts-Dashboard wird in Phase 3 implementiert*")
            
            # Settings tab placeholder  
            with gr.Tab("⚙️ Einstellungen"):
                gr.Markdown("## Einstellungen")
                gr.Markdown("*Erweiterte Einstellungen werden in Phase 4 implementiert*")
            
            # Event bindings
            self._setup_events(
                session_state,
                exercise_selector,
                mode_selector, 
                start_session_btn,
                session_status,
                chat_components,
                eval_components
            )
        
        return app
    
    def _setup_events(
        self,
        session_state: gr.State,
        exercise_selector: gr.Dropdown,
        mode_selector: gr.Radio,
        start_session_btn: gr.Button,
        session_status: gr.Markdown,
        chat_components: Dict[str, Any],
        eval_components: Dict[str, Any]
    ):
        """Setup all event handlers"""
        
        # Session initialization
        start_session_btn.click(
            fn=self._initialize_session,
            inputs=[exercise_selector, mode_selector, session_state],
            outputs=[
                session_status,
                chat_components['chatbot'],
                chat_components['exercise_title'],
                chat_components['checkpoint_info'],
                chat_components['step_info'],
                chat_components['progress_bar'],
                chat_components['current_question'],
                session_state
            ]
        )
        
        # Chat events
        chat_components['send_btn'].click(
            fn=self._handle_chat_message,
            inputs=[chat_components['msg_input'], chat_components['chatbot'], session_state],
            outputs=[chat_components['chatbot'], chat_components['msg_input'], session_state]
        )
        
        chat_components['msg_input'].submit(
            fn=self._handle_chat_message,
            inputs=[chat_components['msg_input'], chat_components['chatbot'], session_state],
            outputs=[chat_components['chatbot'], chat_components['msg_input'], session_state]
        )
        
        # Goto functionality
        chat_components['goto_execute'].click(
            fn=self._handle_goto,
            inputs=[chat_components['goto_input'], session_state],
            outputs=[chat_components['chatbot'], session_state]
        )
        
        # Clear chat
        chat_components['clear_btn'].click(
            fn=self._clear_chat,
            inputs=[session_state],
            outputs=[chat_components['chatbot'], chat_components['msg_input'], session_state]
        )
        
        # Update UI elements when state changes
        session_state.change(
            fn=self._update_ui_elements,
            inputs=[session_state],
            outputs=[
                chat_components['exercise_title'],
                chat_components['checkpoint_info'], 
                chat_components['step_info'],
                chat_components['progress_bar'],
                chat_components['current_question'],
                chat_components['session_stats']
            ]
        )
        
        # Evaluation events
        eval_components['submit_btn'].click(
            fn=self._submit_evaluation,
            inputs=[
                eval_components['exercise_dropdown'],
                eval_components['ratings']['clarity'],
                eval_components['ratings']['difficulty'],
                eval_components['ratings']['coverage'],
                eval_components['ratings']['accuracy'],
                eval_components['ratings']['engagement'],
                eval_components['ratings']['feedback_quality'],
                eval_components['ratings']['pacing'],
                eval_components['ratings']['adaptivity'],
                eval_components['ratings']['usability'],
                eval_components['ratings']['performance'],
                eval_components['feedback_texts']['positive'],
                eval_components['feedback_texts']['improvement'],
                eval_components['feedback_texts']['general'],
                session_state
            ],
            outputs=[
                eval_components['status_msg'],
                eval_components['summary_stats'],
                eval_components['recent_evaluations']
            ]
        )
    
    async def _initialize_session_async(
        self,
        exercise_name: str,
        tutor_mode: str,
        state: GradioSessionState
    ) -> Tuple[str, List[Dict], str, str, str, float, str, GradioSessionState]:
        """Async session initialization"""
        try:
            welcome_text, updated_state = await self.bridge.initialize_session(
                exercise_name=exercise_name,
                tutor_mode=tutor_mode,
                user_id="gradio_user"
            )
            
            # Format chat history
            chat_history = self.bridge.format_chat_history(updated_state)
            
            # Get UI updates
            exercise_info = self.bridge.get_exercise_info(updated_state)
            
            status = f"**Status:** Session aktiv - {exercise_info['title']}"
            title = f"## {exercise_info['title']}"
            checkpoint = f"**Checkpoint:** {exercise_info['checkpoint']}"
            step = f"**Schritt:** {exercise_info['step']}"
            progress = float(exercise_info['progress'].replace('%', ''))
            question = f"**Aktuelle Frage:** {exercise_info['current_question']}"
            
            return status, chat_history, title, checkpoint, step, progress, question, updated_state
            
        except Exception as e:
            error_status = f"**Status:** Fehler beim Starten der Session: {str(e)}"
            return error_status, [], "## Fehler", "**Checkpoint:** --", "**Schritt:** --", 0, "**Frage:** Fehler", state
    
    def _initialize_session(
        self,
        exercise_name: str,
        tutor_mode: str,
        state: GradioSessionState
    ) -> Tuple[str, List[Dict], str, str, str, float, str, GradioSessionState]:
        """Initialize new tutoring session"""
        return asyncio.run(self._initialize_session_async(exercise_name, tutor_mode, state))
    
    def _handle_chat_message(
        self,
        message: str,
        history: List[Dict],
        state: GradioSessionState
    ) -> Tuple[List[Dict], str, GradioSessionState]:
        """Handle chat message"""
        if not message.strip():
            return history, message, state
        
        return asyncio.run(self.chat_tab.handle_message(message, history, state))
    
    def _handle_goto(
        self,
        checkpoint_num: int,
        state: GradioSessionState
    ) -> Tuple[List[Dict], GradioSessionState]:
        """Handle goto command"""
        return self.chat_tab.handle_goto(checkpoint_num, state)
    
    def _clear_chat(
        self,
        state: GradioSessionState
    ) -> Tuple[List[Dict], str, GradioSessionState]:
        """Clear chat history"""
        return self.chat_tab.clear_chat(state)
    
    def _update_ui_elements(
        self,
        state: GradioSessionState
    ) -> Tuple[str, str, str, float, str, List[List[str]]]:
        """Update UI elements based on state"""
        title, checkpoint, step, progress, question = self.chat_tab.update_ui_elements(state)
        session_stats = self.chat_tab.get_session_stats(state)
        return title, checkpoint, step, progress, question, session_stats
    
    def _submit_evaluation(
        self,
        exercise: str,
        clarity: int,
        difficulty: int,
        coverage: int,
        accuracy: int,
        engagement: int,
        feedback_quality: int,
        pacing: int,
        adaptivity: int,
        usability: int,
        performance: int,
        positive: str,
        improvement: str,
        general: str,
        state: GradioSessionState
    ) -> Tuple[str, List[List], List[List]]:
        """Submit evaluation"""
        ratings = {
            'clarity': clarity,
            'difficulty': difficulty,
            'coverage': coverage,
            'accuracy': accuracy,
            'engagement': engagement,
            'feedback_quality': feedback_quality,
            'pacing': pacing,
            'adaptivity': adaptivity,
            'usability': usability,
            'performance': performance
        }
        
        feedback_texts = {
            'positive': positive,
            'improvement': improvement,
            'general': general
        }
        
        return self.evaluation_tab.submit_evaluation(exercise, ratings, feedback_texts, state)
    
    def _get_custom_css(self) -> str:
        """Custom CSS for the application"""
        return """
        #header {
            text-align: center;
            background: linear-gradient(90deg, #1e3a8a, #3b82f6);
            color: white;
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
        }
        
        #user-info {
            text-align: right;
            padding: 0.5rem;
        }
        
        #status {
            text-align: center;
            padding: 0.5rem;
            background: #f0f9ff;
            border-radius: 0.25rem;
            margin-bottom: 1rem;
        }
        
        .gradio-container {
            max-width: 1400px !important;
        }
        
        .gr-button {
            border-radius: 0.375rem;
        }
        
        .gr-button-primary {
            background: linear-gradient(90deg, #1e3a8a, #3b82f6);
            border: none;
        }
        
        .gr-textbox {
            border-radius: 0.375rem;
        }
        
        .gr-accordion {
            border-radius: 0.375rem;
        }
        """
    
    def launch(self, **kwargs):
        """Launch the Gradio app"""
        app = self.create_app()
        return app.launch(
            server_name="0.0.0.0",
            server_port=7860,
            share=False,
            show_error=True,
            **kwargs
        )

def main():
    """Main entry point"""
    app = TutorApp()
    app.launch()

if __name__ == "__main__":
    main()
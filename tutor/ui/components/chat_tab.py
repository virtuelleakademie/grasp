import gradio as gr
import os
from typing import Dict, Any, Tuple, List
from tutor.ui.gradio_bridge import GradioTutorBridge
from tutor.models.gradio_state import GradioSessionState

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
                        progress_bar = gr.Slider(
                            label="Fortschritt",
                            minimum=0,
                            maximum=100,
                            value=0,
                            interactive=False
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
            # Process message through bridge
            response_text, cleared_input, updated_state = await self.bridge.process_chat_message(
                message, state
            )
            
            # Update chat history
            updated_history = self.bridge.format_chat_history(updated_state)
            
            return updated_history, cleared_input, updated_state
            
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
            
            # Create goto command
            goto_command = f"/goto {int(checkpoint_num)}"
            
            # Process through bridge
            import asyncio
            response_text, _, updated_state = asyncio.run(
                self.bridge.process_chat_message(goto_command, state)
            )
            
            # Update history
            updated_history = self.bridge.format_chat_history(updated_state)
            
            return updated_history, updated_state
            
        except Exception as e:
            error_msg = f"Fehler beim Navigieren: {str(e)}"
            history = state.chat_history.copy()
            history.append({"role": "system", "content": error_msg})
            return history, state
    
    def clear_chat(self, state: GradioSessionState) -> Tuple[List[Dict], str, GradioSessionState]:
        """Clear chat history"""
        state.clear_chat()
        return [], "", state
    
    def update_ui_elements(self, state: GradioSessionState) -> Tuple[str, str, str, float, str]:
        """Update UI elements based on current state"""
        exercise_info = self.bridge.get_exercise_info(state)
        
        title = f"## {exercise_info['title']}"
        checkpoint = f"**Checkpoint:** {exercise_info['checkpoint']}"
        step = f"**Schritt:** {exercise_info['step']}"
        progress = float(exercise_info['progress'].replace('%', ''))
        question = f"**Aktuelle Frage:** {exercise_info['current_question']}"
        
        return title, checkpoint, step, progress, question
    
    def get_session_stats(self, state: GradioSessionState) -> List[List[str]]:
        """Get session statistics for display"""
        if not state.tutor_context:
            return [["Status", "Keine Session aktiv"]]
        
        summary = state.get_session_summary()
        
        return [
            ["Nachrichten", str(summary['total_messages'])],
            ["Checkpoint", str(summary['current_checkpoint'])], 
            ["Schritt", str(summary['current_step'])],
            ["Session Dauer", f"{summary['session_duration_minutes']:.1f} min"],
            ["Aufgabe abgeschlossen", "Ja" if summary['exercise_complete'] else "Nein"]
        ]
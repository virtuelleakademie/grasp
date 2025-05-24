import gradio as gr
from typing import Dict, Any, List, Tuple
from datetime import datetime
from tutor.models.gradio_state import GradioSessionState

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
                        choices=["t-test", "anova", "regression", "chi-square"],
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
                    
                    # Placeholder for charts
                    with gr.Group():
                        gr.Markdown("### 📊 Visualisierungen")
                        chart_placeholder = gr.Markdown("*Diagramme werden nach Bewertungsabgabe angezeigt*")
                    
                    # Export options
                    with gr.Group():
                        gr.Markdown("### 📤 Daten exportieren")
                        
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
                'general': general_comments
            },
            'submit_btn': submit_btn,
            'reset_btn': reset_btn,
            'status_msg': status_msg,
            'summary_stats': summary_stats,
            'recent_evaluations': recent_evaluations,
            'chart_placeholder': chart_placeholder,
            'export_csv_btn': export_csv_btn,
            'export_json_btn': export_json_btn,
            'download_file': download_file
        }
    
    def submit_evaluation(
        self,
        exercise: str,
        ratings: Dict[str, int],
        feedback_texts: Dict[str, str],
        state: GradioSessionState
    ) -> Tuple[str, List[List], List[List]]:
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
                'overall_rating': sum(ratings.values()) / len(ratings)
            }
            
            # Save evaluation to state
            state.evaluations.append(evaluation)
            
            # Generate updated displays
            summary_df = self._generate_summary_stats(state.evaluations)
            recent_df = self._generate_recent_evaluations(state.evaluations)
            
            status_message = f"✅ Bewertung für '{exercise}' erfolgreich gespeichert!"
            
            return status_message, summary_df, recent_df
            
        except Exception as e:
            error_message = f"❌ Fehler beim Speichern der Bewertung: {str(e)}"
            return error_message, [], []
    
    def _generate_summary_stats(self, evaluations: List[Dict]) -> List[List]:
        """Generate summary statistics from evaluations"""
        if not evaluations:
            return [["Keine Bewertungen", "0", "0"]]
        
        # Calculate averages
        all_ratings = []
        for eval_data in evaluations:
            all_ratings.extend(eval_data['ratings'].values())
        
        avg_rating = sum(all_ratings) / len(all_ratings) if all_ratings else 0
        
        return [
            ["Durchschnittsbewertung", f"{avg_rating:.1f}", str(len(evaluations))],
            ["Anzahl Bewertungen", str(len(evaluations)), ""],
            ["Letzte Bewertung", evaluations[-1]['timestamp'][:10], ""],
        ]
    
    def _generate_recent_evaluations(self, evaluations: List[Dict]) -> List[List]:
        """Generate recent evaluations display"""
        if not evaluations:
            return []
        
        recent = evaluations[-5:]  # Last 5 evaluations
        result = []
        
        for eval_data in recent:
            result.append([
                eval_data['timestamp'][:10],  # Date only
                eval_data['exercise'],
                f"{eval_data['overall_rating']:.1f}",
                eval_data['feedback']['general'][:50] + "..." if len(eval_data['feedback']['general']) > 50 else eval_data['feedback']['general']
            ])
        
        return result
#!/usr/bin/env python3
"""
Launch script for the Statistical Tutor Gradio application.

This script provides a simple way to start the new Gradio-based interface
for the statistical tutoring system.
"""

import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    parser = argparse.ArgumentParser(description="Launch Statistical Tutor Gradio App")
    parser.add_argument(
        "--host", 
        default="0.0.0.0", 
        help="Host to bind to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=7860, 
        help="Port to bind to (default: 7860)"
    )
    parser.add_argument(
        "--share", 
        action="store_true", 
        help="Create public shareable link"
    )
    parser.add_argument(
        "--debug", 
        action="store_true", 
        help="Enable debug mode"
    )
    parser.add_argument(
        "--reload", 
        action="store_true", 
        help="Enable auto-reload on file changes"
    )
    
    args = parser.parse_args()
    
    # Check for required environment variables
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not found!")
        print("Please ensure you have a .env file with your OpenAI API key:")
        print("OPENAI_API_KEY=your_api_key_here")
        sys.exit(1)
    else:
        print("✓ OPENAI_API_KEY loaded from environment")
    
    # Import and launch the app
    try:
        from tutor.ui.gradio_app import TutorApp
        
        print(f"Starting Statistical Tutor on {args.host}:{args.port}")
        print(f"Debug mode: {'ON' if args.debug else 'OFF'}")
        print(f"Share mode: {'ON' if args.share else 'OFF'}")
        print("Press Ctrl+C to stop the server")
        
        app = TutorApp()
        app.launch(
            server_name=args.host,
            server_port=args.port,
            share=args.share,
            debug=args.debug,
            show_error=True,
            reload=args.reload
        )
        
    except ImportError as e:
        print(f"Error importing application: {e}")
        print("Make sure all dependencies are installed:")
        print("pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
## How to launch

```shell
# Install new dependencies
pip install -r requirements.txt

# Launch the new Gradio interface
python launch_gradio.py

# Or with options
python launch_gradio.py --debug --host 127.0.0.1 --port 8080
```

## Ready for Retirement:**

The legacy files can now be safely deleted:

```shell
rm tutor/helper.py          # @with_agent_state decorator
rm tutor/reasoning.py       # Old LLM agents
rm tutor/output_structure.py # Old response models
rm app.py                   # Chainlit entry point
# tutor/agent.py can be retired after extracting any remaining utilities
```

import argparse
import os
import threading
import sys
import logging
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr

from dotenv import load_dotenv
from huggingface_hub import login
from scripts.text_inspector_tool import TextInspectorTool
from scripts.text_web_browser import (
    ArchiveSearchTool,
    FinderTool,
    FindNextTool,
    PageDownTool,
    PageUpTool,
    SimpleTextBrowser,
    VisitTool,
)
from scripts.visual_qa import visualizer

from smolagents import (
    CodeAgent,
    ToolCallingAgent,
    LiteLLMModel,
    DuckDuckGoSearchTool,
    Tool,
)

AUTHORIZED_IMPORTS = [
    "shell_gpt", "sgpt", "openai", "requests", "zipfile", "os", "pandas", "numpy", "sympy", "json", "bs4",
    "pubchempy", "xml", "yahoo_finance", "Bio", "sklearn", "scipy", "pydub",
    "yaml", "string", "secrets", "io", "PIL", "chess", "PyPDF2", "pptx", "torch", "datetime", "fractions", "csv",
]

append_answer_lock = threading.Lock()


class StreamingHandler(logging.Handler):
    """Custom logging handler that captures agent logs"""
    def __init__(self):
        super().__init__()
        self.callbacks = []
        self.buffer = []
    
    def add_callback(self, callback):
        self.callbacks.append(callback)
    
    def emit(self, record):
        msg = self.format(record)
        self.buffer.append(msg + '\n')
        for callback in self.callbacks:
            callback(msg + '\n')


class StreamingCapture:
    """Captures stdout/stderr and yields content in real-time"""
    def __init__(self):
        self.content = []
        self.callbacks = []
    
    def add_callback(self, callback):
        self.callbacks.append(callback)
    
    def write(self, text):
        if text.strip():
            self.content.append(text)
            for callback in self.callbacks:
                callback(text)
        return len(text)
    
    def flush(self):
        pass


def create_agent(
    model_id="gpt-4o-mini",
    hf_token=None,
    openai_api_key=None,
    serpapi_key=None,
    api_endpoint=None,
    custom_api_endpoint=None,
    custom_api_key=None,
    search_provider="serper",
    search_api_key=None,
    custom_search_url=None
):
    print("[DEBUG] Creating agent with model_id:", model_id)

    if hf_token:
        print("[DEBUG] Logging into HuggingFace")
        login(hf_token)

    model_params = {
        "model_id": model_id,
        "custom_role_conversions": {"tool-call": "assistant", "tool-response": "user"},
        "max_completion_tokens": 8192,
    }

    if model_id == "gpt-4o-mini":
        model_params["reasoning_effort"] = "high"

    if custom_api_endpoint and custom_api_key:
        print("[DEBUG] Using custom API endpoint:", custom_api_endpoint)
        model_params["base_url"] = custom_api_endpoint
        model_params["api_key"] = custom_api_key

    model = LiteLLMModel(**model_params)
    print("[DEBUG] Model initialized")

    text_limit = 100000
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0"

    browser_config = {
        "viewport_size": 1024 * 5,
        "downloads_folder": "downloads_folder",
        "request_kwargs": {
            "headers": {"User-Agent": user_agent},
            "timeout": 300,
        },
        "serpapi_key": serpapi_key,
    }

    os.makedirs(f"./{browser_config['downloads_folder']}", exist_ok=True)
    browser = SimpleTextBrowser(**browser_config)
    print("[DEBUG] Browser initialized")

    # Correct tool selection
    if search_provider == "searxng":
        print("[DEBUG] Using SearxNG-compatible DuckDuckGoSearchTool with base_url override")
        search_tool = DuckDuckGoSearchTool()
        if custom_search_url:
            search_tool.base_url = custom_search_url  # Override default DuckDuckGo URL (only if supported)
    else:
        print("[DEBUG] Using default DuckDuckGoSearchTool for Serper/standard search")
        search_tool = DuckDuckGoSearchTool()

    WEB_TOOLS = [
        search_tool,
        VisitTool(browser),
        PageUpTool(browser),
        PageDownTool(browser),
        FinderTool(browser),
        FindNextTool(browser),
        ArchiveSearchTool(browser),
        TextInspectorTool(model, text_limit),
    ]

    text_webbrowser_agent = ToolCallingAgent(
        model=model,
        tools=WEB_TOOLS,
        max_steps=20,
        verbosity_level=3,
        planning_interval=4,
        name="search_agent",
        description="A team member that will search the internet to answer your question.",
        provide_run_summary=True,
    )

    text_webbrowser_agent.prompt_templates["managed_agent"]["task"] += """You can navigate to .txt online files.
If a non-html page is in another format, especially .pdf or a Youtube video, use tool 'inspect_file_as_text' to inspect it.
Additionally, if after some searching you find out that you need more information to answer the question, you can use `final_answer` with your request for clarification as argument to request for more information."""

    manager_agent = CodeAgent(
        model=model,
        tools=[visualizer, TextInspectorTool(model, text_limit)],
        max_steps=16,
        verbosity_level=3,
        additional_authorized_imports=AUTHORIZED_IMPORTS,
        planning_interval=4,
        managed_agents=[text_webbrowser_agent],
    )

    print("[DEBUG] Agent fully initialized")
    return manager_agent


def run_agent_with_streaming(agent, question, stream_callback=None):
    """Run agent and stream output in real-time"""
    
    # Set up logging capture
    log_handler = StreamingHandler()
    if stream_callback:
        log_handler.add_callback(stream_callback)
    
    # Add handler to root logger and smolagents loggers
    root_logger = logging.getLogger()
    smolagents_logger = logging.getLogger('smolagents')
    
    # Store original handlers
    original_handlers = root_logger.handlers[:]
    original_level = root_logger.level
    
    try:
        # Configure logging to capture everything
        root_logger.setLevel(logging.DEBUG)
        root_logger.addHandler(log_handler)
        smolagents_logger.setLevel(logging.DEBUG)
        smolagents_logger.addHandler(log_handler)
        
        # Also capture stdout/stderr
        stdout_capture = StreamingCapture()
        stderr_capture = StreamingCapture()
        
        if stream_callback:
            stdout_capture.add_callback(stream_callback)
            stderr_capture.add_callback(stream_callback)
        
        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            if stream_callback:
                stream_callback(f"[STARTING] Running agent with question: {question}\n")
            
            answer = agent.run(question)
            
            if stream_callback:
                stream_callback(f"[COMPLETED] Final answer: {answer}\n")
            
            return answer
            
    except Exception as e:
        error_msg = f"[ERROR] Exception occurred: {str(e)}\n"
        if stream_callback:
            stream_callback(error_msg)
        raise
    finally:
        # Restore original logging configuration
        root_logger.handlers = original_handlers
        root_logger.setLevel(original_level)
        smolagents_logger.removeHandler(log_handler)


def create_gradio_interface():
    """Create Gradio interface with streaming support"""
    import gradio as gr
    import time
    import threading
    
    def process_question(question, model_id, hf_token, serpapi_key, custom_api_endpoint, 
                        custom_api_key, search_provider, search_api_key, custom_search_url):
        
        # Create agent
        agent = create_agent(
            model_id=model_id,
            hf_token=hf_token,
            openai_api_key=None,
            serpapi_key=serpapi_key,
            api_endpoint=None,
            custom_api_endpoint=custom_api_endpoint,
            custom_api_key=custom_api_key,
            search_provider=search_provider,
            search_api_key=search_api_key,
            custom_search_url=custom_search_url,
        )
        
        # Shared state for streaming
        output_buffer = []
        is_complete = False
        
        def stream_callback(text):
            output_buffer.append(text)
        
        def run_agent_async():
            nonlocal is_complete
            try:
                answer = run_agent_with_streaming(agent, question, stream_callback)
                output_buffer.append(f"\n\n**FINAL ANSWER:** {answer}")
            except Exception as e:
                output_buffer.append(f"\n\n**ERROR:** {str(e)}")
            finally:
                is_complete = True
        
        # Start agent in background thread
        agent_thread = threading.Thread(target=run_agent_async)
        agent_thread.start()
        
        # Generator that yields updates
        last_length = 0
        while not is_complete or agent_thread.is_alive():
            current_output = "".join(output_buffer)
            if len(current_output) > last_length:
                yield current_output
                last_length = len(current_output)
            time.sleep(0.1)  # Small delay to prevent excessive updates
        
        # Final yield to ensure everything is captured
        final_output = "".join(output_buffer)
        if len(final_output) > last_length:
            yield final_output
    
    # Create Gradio interface
    with gr.Blocks(title="Streaming Agent Chat") as demo:
        gr.Markdown("# Streaming Agent Chat Interface")
        
        with gr.Row():
            with gr.Column():
                question_input = gr.Textbox(label="Question", placeholder="Enter your question here...")
                model_id_input = gr.Textbox(label="Model ID", value="gpt-4o-mini")
                hf_token_input = gr.Textbox(label="HuggingFace Token", type="password")
                serpapi_key_input = gr.Textbox(label="SerpAPI Key", type="password")
                custom_api_endpoint_input = gr.Textbox(label="Custom API Endpoint")
                custom_api_key_input = gr.Textbox(label="Custom API Key", type="password")
                search_provider_input = gr.Dropdown(
                    choices=["serper", "searxng"], 
                    value="serper", 
                    label="Search Provider"
                )
                search_api_key_input = gr.Textbox(label="Search API Key", type="password")
                custom_search_url_input = gr.Textbox(label="Custom Search URL")
                
                submit_btn = gr.Button("Submit", variant="primary")
            
            with gr.Column():
                output = gr.Textbox(
                    label="Agent Output (Streaming)", 
                    lines=30, 
                    max_lines=50,
                    interactive=False
                )
        
        submit_btn.click(
            fn=process_question,
            inputs=[
                question_input, model_id_input, hf_token_input, serpapi_key_input,
                custom_api_endpoint_input, custom_api_key_input, search_provider_input,
                search_api_key_input, custom_search_url_input
            ],
            outputs=output,
            show_progress=True
        )
    
    return demo


def main():
    print("[DEBUG] Loading environment variables")
    load_dotenv(override=True)

    parser = argparse.ArgumentParser()
    parser.add_argument("--gradio", action="store_true", help="Launch Gradio interface")
    parser.add_argument("question", type=str, nargs='?', help="Question to ask (CLI mode)")
    parser.add_argument("--model-id", type=str, default="gpt-4o-mini")
    parser.add_argument("--hf-token", type=str, default=os.getenv("HF_TOKEN"))
    parser.add_argument("--serpapi-key", type=str, default=os.getenv("SERPAPI_API_KEY"))
    parser.add_argument("--custom-api-endpoint", type=str, default=None)
    parser.add_argument("--custom-api-key", type=str, default=None)
    parser.add_argument("--search-provider", type=str, default="serper")
    parser.add_argument("--search-api-key", type=str, default=None)
    parser.add_argument("--custom-search-url", type=str, default=None)
    args = parser.parse_args()

    print("[DEBUG] CLI arguments parsed:", args)

    if args.gradio:
        # Launch Gradio interface
        demo = create_gradio_interface()
        demo.launch(share=True)
    else:
        # CLI mode
        if not args.question:
            print("Error: Question required for CLI mode")
            return
        
        agent = create_agent(
            model_id=args.model_id,
            hf_token=args.hf_token,
            openai_api_key=None,  # Fix: was openai_api_token
            serpapi_key=args.serpapi_key,
            api_endpoint=None,  # Fix: was api_endpoint
            custom_api_endpoint=args.custom_api_endpoint,
            custom_api_key=args.custom_api_key,
            search_provider=args.search_provider,
            search_api_key=args.search_api_key,
            custom_search_url=args.custom_search_url,
        )

        print("[DEBUG] Running agent...")
        
        def print_stream(text):
            print(text, end='', flush=True)
        
        answer = run_agent_with_streaming(agent, args.question, print_stream)
        print(f"\n\nGot this answer: {answer}")


if __name__ == "__main__":
    main()
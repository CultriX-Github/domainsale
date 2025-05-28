from run import create_agent, run_agent_with_streaming
import gradio as gr
import os
import threading
import time
from dotenv import load_dotenv

load_dotenv()
CONFIG_FILE = ".user_config.env"

def save_env_vars_to_file(env_vars):
    print("[DEBUG] Saving user config to file")
    with open(CONFIG_FILE, "w") as f:
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")

def launch_interface():
    def setup_agent_streaming(question, model_id, hf_token, openai_api_key, serpapi_key, api_endpoint, use_custom_endpoint,
                    custom_api_endpoint, custom_api_key, search_provider, search_api_key, custom_search_url):
        print("[DEBUG] Setting up agent with input question:", question)

        if question.strip() == "":
            yield "Please enter a question.", ""
            return

        endpoint = custom_api_endpoint if use_custom_endpoint else api_endpoint
        api_key = custom_api_key if use_custom_endpoint else openai_api_key

        save_env_vars_to_file({
            "HF_TOKEN": hf_token,
            "SERPAPI_API_KEY": serpapi_key,
            "API_ENDPOINT": api_endpoint,
            "OPENAI_API_KEY": openai_api_key
        })

        print("[DEBUG] Instantiating agent with UI configuration")
        agent = create_agent(
            model_id=model_id,
            hf_token=hf_token,
            serpapi_key=serpapi_key,
            openai_api_key=openai_api_key,
            api_endpoint=api_endpoint,
            custom_api_endpoint=endpoint,
            custom_api_key=api_key,
            search_provider=search_provider,
            search_api_key=search_api_key,
            custom_search_url=custom_search_url
        )

        output_buffer = []
        final_answer = ""
        is_complete = False

        def highlight_text(text):
            if "[COMPLETED] Final answer:" in text:
                return f"<span style='color:#10b981;font-weight:bold;'>[FINAL]</span> <mark>{text.split(':', 1)[1].strip()}</mark>"
            elif "[ERROR]" in text:
                return f"<span style='color:#ef4444;font-weight:bold;'>[ERROR]</span> <pre>{text.strip()}</pre>"
            elif "[STARTING]" in text:
                return f"<span style='color:#f59e0b;font-weight:bold;'>[STEP]</span> {text.strip()}"
            elif text.strip():
                return f"<details><summary><span style='color:#f59e0b;'>Step</span></summary>\n<pre>{text.strip()}</pre>\n</details>"
            return ""

        def stream_callback(text):
            nonlocal final_answer
            if "[COMPLETED] Final answer:" in text:
                final_answer = text.split("[COMPLETED] Final answer:", 1)[1].strip()
            formatted = highlight_text(text)
            if formatted:
                output_buffer.append(formatted)

        def run_agent_async():
            nonlocal is_complete
            try:
                _ = run_agent_with_streaming(agent, question, stream_callback)
            except Exception as e:
                output_buffer.append(highlight_text(f"[ERROR] {str(e)}"))
            finally:
                is_complete = True

        agent_thread = threading.Thread(target=run_agent_async)
        agent_thread.start()

        last_length = 0
        while not is_complete or agent_thread.is_alive():
            current_output = "\n".join(output_buffer)
            if len(current_output) > last_length:
                yield current_output, ""
                last_length = len(current_output)
            time.sleep(0.1)

        final_output = "\n".join(output_buffer)
        yield final_output, final_answer

    with gr.Blocks(title="SmolAgent - Streaming AI", theme="CultriX/gradio-theme") as demo:
        gr.Markdown("# SmolAgent - Intelligent AI with Web Tools")

        with gr.Row():
            with gr.Column(scale=1):
                question = gr.Textbox(label="Your Question", lines=3, placeholder="Enter your question or task for the AI agent...")
                model_id = gr.Textbox(label="Model ID", value="gpt-4.1-nano", placeholder="e.g., gpt-4, claude-3-opus-20240229")

                with gr.Accordion("API Configuration", open=False):
                    hf_token = gr.Textbox(label="Hugging Face Token (Optional)", type="password", value=os.getenv("HF_TOKEN", ""), placeholder="Your Hugging Face token if using HF models")
                    openai_api_key = gr.Textbox(label="OpenAI API Key (Optional)", type="password", value=os.getenv("OPENAI_API_KEY", ""), placeholder="Your OpenAI API key")
                    api_endpoint = gr.Textbox(label="Default API Endpoint", value=os.getenv("API_ENDPOINT", "https://api.openai.com/v1"), placeholder="e.g., https://api.openai.com/v1")
                    with gr.Group():
                        use_custom_endpoint = gr.Checkbox(label="Use Custom API Endpoint")
                        custom_api_endpoint = gr.Textbox(label="Custom API URL", visible=False, placeholder="URL for your custom API endpoint")
                        custom_api_key = gr.Textbox(label="Custom API Key (Optional)", type="password", visible=False, placeholder="API key for the custom endpoint")
                
                with gr.Accordion("Search Configuration", open=False):
                    serpapi_key = gr.Textbox(label="SerpAPI Key (Optional)", type="password", value=os.getenv("SERPAPI_API_KEY", ""), placeholder="Your SerpAPI key for web searches")
                    search_provider = gr.Dropdown(choices=["serper", "searxng"], value="searxng", label="Search Provider")
                    # search_api_key is for Serper, custom_search_url is for SearxNG.
                    # Default is searxng, so custom_search_url is visible, search_api_key is not.
                    search_api_key = gr.Textbox(label="Serper API Key", type="password", visible=False, placeholder="API key for Serper.dev if selected") 
                    custom_search_url = gr.Textbox(label="Custom SearxNG URL", value="https://search.endorisk.nl/search", visible=True, placeholder="URL for your SearxNG instance")

                submit_btn = gr.Button("Run Agent", variant="primary")

            with gr.Column(scale=2):
                output = gr.Markdown(label="Live Agent Output")
                final = gr.Textbox(label="Final Answer", interactive=False)
                copy_btn = gr.Button("Copy Final Answer")

        def update_visibility(provider):
            is_searxng = (provider == "searxng")
            is_serper = (provider == "serper")
            return {
                custom_search_url: gr.update(visible=is_searxng),
                search_api_key: gr.update(visible=is_serper) 
            }

        def update_custom_fields(checked):
            return {
                custom_api_endpoint: gr.update(visible=checked),
                custom_api_key: gr.update(visible=checked)
            }

        search_provider.change(fn=update_visibility, inputs=search_provider, outputs=[custom_search_url, search_api_key])
        use_custom_endpoint.change(fn=update_custom_fields, inputs=use_custom_endpoint, outputs=[custom_api_endpoint, custom_api_key])

        submit_btn.click(
            fn=setup_agent_streaming,
            inputs=[question, model_id, hf_token, openai_api_key, serpapi_key, api_endpoint, use_custom_endpoint, custom_api_endpoint, custom_api_key, search_provider, search_api_key, custom_search_url],
            outputs=[output, final],
            show_progress=True
        )

        # Output actions
        copy_btn.click(
            fn=None,
            inputs=final,
            outputs=None,
            js="(text) => { if (text) { navigator.clipboard.writeText(text); return 'Copied!'; } return ''; }"
        )
        # Removed the non-existent export_md.click call that was here

    print("[DEBUG] Launching updated Gradio interface")
    demo.launch()

if __name__ == "__main__":
    launch_interface()

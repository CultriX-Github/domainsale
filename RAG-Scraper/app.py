import gradio as gr
import os
import re
import subprocess
import tempfile
import json
import zipfile
import shutil
import time
import requests
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional, Union
import pandas as pd
import PyPDF2
import io

from rag_scraper.scraper import Scraper
from rag_scraper.converter import Converter
from rag_scraper.link_extractor import LinkExtractor, LinkType
from rag_scraper.utils import URLUtils

# Constants
MAX_REPO_SIZE_MB = 100  # Maximum repository size in MB
MAX_PROCESSING_TIME = 300  # Maximum processing time in seconds (5 minutes)
RATE_LIMIT_REQUESTS = 10  # Maximum number of requests per minute
RATE_LIMIT_WINDOW = 60  # Rate limit window in seconds

# Rate limiting
request_timestamps = []

def is_rate_limited() -> bool:
    """Check if the current request is rate limited."""
    global request_timestamps
    current_time = time.time()
    
    # Remove timestamps older than the window
    request_timestamps = [ts for ts in request_timestamps if current_time - ts < RATE_LIMIT_WINDOW]
    
    # Check if we've exceeded the limit
    if len(request_timestamps) >= RATE_LIMIT_REQUESTS:
        return True
    
    # Add current timestamp
    request_timestamps.append(current_time)
    return False

def is_github_repo(url_or_id: str) -> bool:
    """Check if the input is a GitHub repository URL or ID."""
    # Check for GitHub URL
    if "github.com" in url_or_id:
        return True
    
    # Check for shorthand notation (username/repo)
    if re.match(r'^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+$', url_or_id):
        return True
    
    return False

def extract_repo_info(url_or_id: str) -> Tuple[Optional[str], Optional[str]]:
    """Extract repository owner and name from URL or ID."""
    # Handle GitHub URLs
    github_url_pattern = r'github\.com/([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+)'
    match = re.search(github_url_pattern, url_or_id)
    if match:
        return match.group(1), match.group(2)
    
    # Handle shorthand notation (username/repo)
    if '/' in url_or_id and not url_or_id.startswith('http'):
        parts = url_or_id.split('/')
        if len(parts) == 2:
            return parts[0], parts[1]
    
    return None, None

def is_running_on_huggingface() -> bool:
    """Check if the app is running on HuggingFace Spaces."""
    return os.environ.get('SPACE_ID') is not None

def check_repomix_installed() -> bool:
    """Check if Repomix is installed."""
    try:
        result = subprocess.run(["repomix", "--version"], 
                               capture_output=True, text=True, check=False)
        return result.returncode == 0
    except Exception:
        return False

def run_repomix(
    repo_path: str, 
    output_format: str = "markdown",
    compress: bool = False,
    include_patterns: str = None,
    ignore_patterns: str = None
) -> str:
    """Run Repomix on the repository and return the content."""
    try:
        # Create a temporary directory for the output
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = os.path.join(temp_dir, f"repomix-output.{output_format}")
            
            # Prepare the command
            cmd = [
                "repomix",
                "--output", output_file,
                "--style", output_format
            ]
            
            # Add optional parameters
            if compress:
                cmd.append("--compress")
                
            if include_patterns:
                cmd.extend(["--include", include_patterns])
                
            if ignore_patterns:
                cmd.extend(["--ignore", ignore_patterns])
            
            # Add the repository path
            cmd.append(repo_path)
            
            # Run Repomix with timeout
            process = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                check=False,
                timeout=MAX_PROCESSING_TIME
            )
            
            if process.returncode != 0:
                return f"Error running Repomix: {process.stderr}"
            
            # Read the output file
            if os.path.exists(output_file):
                with open(output_file, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                return f"Error: Repomix did not generate an output file."
    
    except subprocess.TimeoutExpired:
        return "Error: Processing timed out. The repository may be too large or complex."
    except Exception as e:
        return f"Error processing repository: {str(e)}"

def run_repomix_remote(
    repo_url_or_id: str, 
    output_format: str = "markdown",
    compress: bool = False,
    include_patterns: str = None,
    ignore_patterns: str = None,
    auth_token: str = None
) -> str:
    """Run Repomix on a remote GitHub repository and return the content."""
    try:
        # Create a temporary directory for the output
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = os.path.join(temp_dir, f"repomix-output.{output_format}")
            
            # Prepare the command
            if '/' in repo_url_or_id and not repo_url_or_id.startswith('http'):
                # Handle shorthand notation
                repo_url = f"https://github.com/{repo_url_or_id}"
            else:
                repo_url = repo_url_or_id
            
            cmd = [
                "repomix",
                "--remote", repo_url,
                "--output", output_file,
                "--style", output_format
            ]
            
            # Add optional parameters
            if compress:
                cmd.append("--compress")
                
            if include_patterns:
                cmd.extend(["--include", include_patterns])
                
            if ignore_patterns:
                cmd.extend(["--ignore", ignore_patterns])
            
            # Set up environment for authentication if token is provided
            env = os.environ.copy()
            if auth_token:
                # For private repositories, we need to include the token in the URL
                # This is a common pattern for Git authentication
                parsed_url = repo_url.replace("https://", f"https://{auth_token}@")
                cmd[cmd.index("--remote") + 1] = parsed_url
            
            # Run Repomix with timeout
            process = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                check=False,
                timeout=MAX_PROCESSING_TIME,
                env=env
            )
            
            if process.returncode != 0:
                error_msg = process.stderr
                # Remove any sensitive information like tokens from the error message
                if auth_token:
                    error_msg = error_msg.replace(auth_token, "***")
                return f"Error running Repomix: {error_msg}"
            
            # Read the output file
            if os.path.exists(output_file):
                with open(output_file, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                return f"Error: Repomix did not generate an output file."
    
    except subprocess.TimeoutExpired:
        return "Error: Processing timed out. The repository may be too large or complex."
    except Exception as e:
        error_msg = str(e)
        # Remove any sensitive information like tokens from the error message
        if auth_token:
            error_msg = error_msg.replace(auth_token, "***")
        return f"Error processing repository: {error_msg}"

def process_zip_file(zip_file: tempfile._TemporaryFileWrapper) -> Tuple[str, str]:
    """Process a ZIP file containing a repository."""
    try:
        # Create a temporary directory to extract the ZIP file
        with tempfile.TemporaryDirectory() as temp_dir:
            # Check file size
            zip_file.seek(0, os.SEEK_END)
            file_size = zip_file.tell() / (1024 * 1024)  # Convert to MB
            if file_size > MAX_REPO_SIZE_MB:
                return None, f"Error: ZIP file size ({file_size:.2f} MB) exceeds the maximum allowed size ({MAX_REPO_SIZE_MB} MB)."
            
            zip_file.seek(0)
            
            # Extract the ZIP file
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Find the root directory of the repository
            contents = os.listdir(temp_dir)
            repo_dir = temp_dir
            
            # If there's only one directory and it contains the repository, use that
            if len(contents) == 1 and os.path.isdir(os.path.join(temp_dir, contents[0])):
                repo_dir = os.path.join(temp_dir, contents[0])
            
            return repo_dir, None
    
    except zipfile.BadZipFile:
        return None, "Error: Invalid ZIP file."
    except Exception as e:
        return None, f"Error processing ZIP file: {str(e)}"

def scrape_and_convert(url: str, depth: int) -> str:
    """Fetch HTML content, extract links recursively (up to given depth), and convert to Markdown."""
    try:
        visited_urls = set()

        def recursive_scrape(url: str, current_depth: int) -> str:
            """Recursively scrape and convert pages up to the given depth."""
            if url in visited_urls or current_depth < 0:
                return ""
            
            visited_urls.add(url)

            # Fetch HTML content
            try:
                html_content = Scraper.fetch_html(url)
            except Exception as e:
                return f"Error fetching {url}: {str(e)}\n"

            # Convert to Markdown
            markdown_content = f"## Extracted from: {url}\n\n"
            markdown_content += Converter.html_to_markdown(
                html=html_content,
                base_url=url,
                parser_features='html.parser',
                ignore_links=True
            )

            # If depth > 0, extract links and process them
            if current_depth > 0:
                links = LinkExtractor.scrape_url(url, link_type=LinkType.INTERNAL)

                for link in links:
                    if link not in visited_urls:
                        markdown_content += f"\n\n### Extracted from: {link}\n"  
                        markdown_content += recursive_scrape(link, current_depth - 1)

            return markdown_content

        # Start the recursive scraping process
        result = recursive_scrape(url, depth)
        return result

    except Exception as e:
        return f"Error: {str(e)}"

def process_text_input(text: str) -> str:
    """Process plain text input."""
    return text

def process_pdf_file(pdf_file: tempfile._TemporaryFileWrapper) -> str:
    """Extract text from a PDF file."""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        
        for page_num in range(len(pdf_reader.pages)):
            text += pdf_reader.pages[page_num].extract_text() + "\n\n"
        
        return text
    except Exception as e:
        return f"Error processing PDF file: {str(e)}"

def process_csv_file(csv_file: tempfile._TemporaryFileWrapper) -> str:
    """Process a CSV file and convert to markdown table."""
    try:
        df = pd.read_csv(csv_file)
        return df.to_markdown(index=False)
    except Exception as e:
        return f"Error processing CSV file: {str(e)}"

def process_json_file(json_file: tempfile._TemporaryFileWrapper) -> str:
    """Process a JSON file and format it."""
    try:
        json_data = json.load(json_file)
        return json.dumps(json_data, indent=2)
    except Exception as e:
        return f"Error processing JSON file: {str(e)}"

def process_url_content(url: str) -> str:
    """Fetch content from a URL."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        content_type = response.headers.get('Content-Type', '').lower()
        
        if 'text/html' in content_type:
            return Converter.html_to_markdown(
                html=response.text,
                base_url=url,
                parser_features='html.parser',
                ignore_links=True
            )
        elif 'application/json' in content_type:
            return json.dumps(response.json(), indent=2)
        elif 'text/' in content_type:
            return response.text
        else:
            return f"Unsupported content type: {content_type}"
    except Exception as e:
        return f"Error fetching URL content: {str(e)}"

def process_repository_input(
    repo_input: Union[str, tempfile._TemporaryFileWrapper],
    input_type: str,
    output_format: str,
    compress: bool,
    include_patterns: str,
    ignore_patterns: str,
    auth_token: str
) -> str:
    """Process repository input (URL or ZIP file)."""
    if is_rate_limited():
        return "Rate limit exceeded. Please try again later."
    
    # Check if repomix is installed
    if not check_repomix_installed():
        return (
            "Repomix is not installed or not accessible. "
            "Please check the Dockerfile to ensure it's properly installed."
        )
    
    # Process based on input type
    if input_type == "url":
        if not is_github_repo(repo_input):
            return "Error: The provided URL is not a valid GitHub repository."
        
        return run_repomix_remote(
            repo_input,
            output_format=output_format,
            compress=compress,
            include_patterns=include_patterns,
            ignore_patterns=ignore_patterns,
            auth_token=auth_token
        )
    elif input_type == "zip":
        repo_dir, error = process_zip_file(repo_input)
        if error:
            return error
        
        return run_repomix(
            repo_dir,
            output_format=output_format,
            compress=compress,
            include_patterns=include_patterns,
            ignore_patterns=ignore_patterns
        )
    else:
        return "Error: Invalid input type."

def process_content_input(
    content_input: Union[str, tempfile._TemporaryFileWrapper],
    input_type: str,
    depth: int
) -> str:
    """Process content input (URL, text, PDF, CSV, JSON)."""
    if is_rate_limited():
        return "Rate limit exceeded. Please try again later."
    
    if input_type == "url":
        if depth > 0:
            return scrape_and_convert(content_input, depth)
        else:
            return process_url_content(content_input)
    elif input_type == "text":
        return process_text_input(content_input)
    elif input_type == "pdf":
        return process_pdf_file(content_input)
    elif input_type == "csv":
        return process_csv_file(content_input)
    elif input_type == "json":
        return process_json_file(content_input)
    else:
        return "Error: Invalid input type."

# Example prompts for using the output with AI assistants
EXAMPLE_PROMPTS = {
    "code_review": """
I'm sharing a codebase with you for review. This file contains all the code from my repository.
Please analyze it and provide:
1. An overview of the architecture and main components
2. Potential issues or code smells
3. Suggestions for improvements in terms of performance, readability, and maintainability
""",
    "documentation": """
This file contains my entire codebase. Please help me create comprehensive documentation for it, including:
1. A high-level overview of the project structure
2. Explanation of key components and their interactions
3. API documentation (if applicable)
4. Setup and usage instructions
""",
    "feature_implementation": """
I'm sharing my codebase with you. I want to implement a new feature:
[DESCRIBE YOUR FEATURE HERE]

Please help me understand:
1. Where and how this feature should be implemented
2. What changes are needed to existing code
3. Any potential challenges or considerations
""",
    "bug_fixing": """
I'm experiencing the following bug in my code:
[DESCRIBE THE BUG HERE]

Here's my entire codebase. Please help me:
1. Identify the root cause of the bug
2. Suggest a fix
3. Explain why the bug is occurring
""",
    "web_content_analysis": """
I've provided content from a website. Please help me:
1. Summarize the key information
2. Extract important concepts and terminology
3. Organize the information into a structured format
4. Identify any gaps or areas that need clarification
"""
}

# Define Gradio interface
with gr.Blocks(title="RAG-Scraper + Repomix") as app:
    gr.Markdown("""
    # RAG-Scraper + Repomix
    
    This tool combines two powerful utilities for preparing content for Retrieval-Augmented Generation (RAG):
    
    1. **Repomix**: Process GitHub repositories or code ZIP files into AI-friendly formats
    2. **RAG-Scraper**: Extract and process content from websites, PDFs, CSVs, and more
    
    Choose the appropriate tab for your use case.
    """)
    
    with gr.Tabs():
        # Repository Processing Tab (Repomix)
        with gr.TabItem("Repository Processing"):
            gr.Markdown("""
            ## Process Code Repositories
            
            Use this tab to convert GitHub repositories or ZIP files containing code into AI-friendly formats.
            """)
            
            with gr.Row():
                with gr.Column():
                    repo_input_type = gr.Radio(
                        choices=["url", "zip"],
                        value="url",
                        label="Input Type",
                        info="Choose between GitHub URL or ZIP file upload"
                    )
                    
                    repo_url = gr.Textbox(
                        label="GitHub Repository URL",
                        placeholder="https://github.com/username/repo or username/repo",
                        visible=True
                    )
                    
                    repo_zip = gr.File(
                        label="Upload Repository ZIP",
                        file_types=[".zip"],
                        visible=False
                    )
                    
                    auth_token = gr.Textbox(
                        label="GitHub Auth Token (for private repositories)",
                        placeholder="Optional: Your GitHub personal access token",
                        type="password"
                    )
                    
                    output_format = gr.Radio(
                        choices=["xml", "markdown", "plain", "json"],
                        value="markdown",
                        label="Output Format",
                        info="Choose the format for the processed output"
                    )
                    
                    with gr.Accordion("Advanced Options", open=False):
                        compress = gr.Checkbox(
                            label="Compress Output",
                            value=True,
                            info="Reduce token count by focusing on essential code elements"
                        )
                        
                        include_patterns = gr.Textbox(
                            label="Include Patterns",
                            placeholder="Optional: Comma-separated glob patterns (e.g., src/**/*.js,*.md)",
                            info="Specify files to include"
                        )
                        
                        ignore_patterns = gr.Textbox(
                            label="Ignore Patterns",
                            placeholder="Optional: Comma-separated glob patterns (e.g., tests/**,*.log)",
                            info="Specify files to ignore"
                        )
                    
                    repo_submit = gr.Button("Process Repository")
            
            repo_output = gr.Code(
                label="Processed Repository",
                language="markdown",
                lines=20
            )
            
            with gr.Accordion("Example Prompts for AI Assistants", open=False):
                repo_prompts = gr.Dataframe(
                    headers=["Use Case", "Prompt"],
                    datatype=["str", "str"],
                    value=[
                        ["Code Review", EXAMPLE_PROMPTS["code_review"]],
                        ["Documentation", EXAMPLE_PROMPTS["documentation"]],
                        ["Feature Implementation", EXAMPLE_PROMPTS["feature_implementation"]],
                        ["Bug Fixing", EXAMPLE_PROMPTS["bug_fixing"]]
                    ],
                    interactive=False
                )
        
        # Content Processing Tab (RAG-Scraper)
        with gr.TabItem("Content Processing"):
            gr.Markdown("""
            ## Process Web Content
            
            Use this tab to extract and process content from websites, text, PDFs, CSVs, and JSON files.
            """)
            
            with gr.Row():
                with gr.Column():
                    content_input_type = gr.Radio(
                        choices=["url", "text", "pdf", "csv", "json"],
                        value="url",
                        label="Input Type",
                        info="Choose the type of content to process"
                    )
                    
                    content_url = gr.Textbox(
                        label="URL",
                        placeholder="https://example.com",
                        visible=True
                    )
                    
                    content_text = gr.Textbox(
                        label="Text",
                        placeholder="Enter your text here...",
                        lines=5,
                        visible=False
                    )
                    
                    content_file = gr.File(
                        label="Upload File",
                        visible=False
                    )
                    
                    depth = gr.Slider(
                        minimum=0,
                        maximum=3,
                        step=1,
                        value=0,
                        label="Search Depth (for URLs)",
                        info="0 = Only main page, 1-3 = Follow links recursively",
                        visible=True
                    )
                    
                    content_submit = gr.Button("Process Content")
            
            content_output = gr.Code(
                label="Processed Content",
                language="markdown",
                lines=20
            )
            
            with gr.Accordion("Example Prompts for AI Assistants", open=False):
                content_prompts = gr.Dataframe(
                    headers=["Use Case", "Prompt"],
                    datatype=["str", "str"],
                    value=[
                        ["Web Content Analysis", EXAMPLE_PROMPTS["web_content_analysis"]]
                    ],
                    interactive=False
                )
    
    # Handle visibility changes for input types
    def update_repo_input_visibility(input_type):
        return {
            repo_url: input_type == "url",
            repo_zip: input_type == "zip"
        }
    
    def update_content_input_visibility(input_type):
        return {
            content_url: input_type == "url",
            content_text: input_type == "text",
            content_file: input_type in ["pdf", "csv", "json"],
            depth: input_type == "url"
        }
    
    # Connect visibility change functions
    repo_input_type.change(
        fn=update_repo_input_visibility,
        inputs=repo_input_type,
        outputs=[repo_url, repo_zip]
    )
    
    content_input_type.change(
        fn=update_content_input_visibility,
        inputs=content_input_type,
        outputs=[content_url, content_text, content_file, depth]
    )
    
    # Handle repository processing
    def handle_repo_processing(
        input_type, url, zip_file, output_format, compress, include_patterns, ignore_patterns, auth_token
    ):
        if input_type == "url":
            return process_repository_input(
                url,
                input_type,
                output_format,
                compress,
                include_patterns,
                ignore_patterns,
                auth_token
            )
        else:
            return process_repository_input(
                zip_file,
                input_type,
                output_format,
                compress,
                include_patterns,
                ignore_patterns,
                None
            )
    
    # Handle content processing
    def handle_content_processing(input_type, url, text, file, depth):
        if input_type == "url":
            return process_content_input(url, input_type, depth)
        elif input_type == "text":
            return process_content_input(text, input_type, 0)
        else:
            return process_content_input(file, input_type, 0)
    
    # Connect submit buttons
    repo_submit.click(
        fn=handle_repo_processing,
        inputs=[
            repo_input_type,
            repo_url,
            repo_zip,
            output_format,
            compress,
            include_patterns,
            ignore_patterns,
            auth_token
        ],
        outputs=repo_output
    )
    
    content_submit.click(
        fn=handle_content_processing,
        inputs=[
            content_input_type,
            content_url,
            content_text,
            content_file,
            depth
        ],
        outputs=content_output
    )

# Launch the Gradio app
if __name__ == "__main__":
    # Check if repomix is installed
    repomix_installed = check_repomix_installed()
    
    if not repomix_installed and not is_running_on_huggingface():
        print("Warning: Repomix is not installed. Repository processing will not work.")
        print("Please install repomix using: npm install -g repomix")
    
    app.launch()

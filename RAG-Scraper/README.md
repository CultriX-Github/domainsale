---
title: RAG-Scraper + Repomix
emoji: 🧠
colorFrom: blue
colorTo: green
sdk: gradio
sdk_version: 4.44.1
app_file: app.py
pinned: false
license: mit
---

# RAG-Scraper + Repomix

A powerful HuggingFace Space that combines two essential tools for Retrieval-Augmented Generation (RAG):

1. **Repomix**: Process GitHub repositories or code ZIP files into AI-friendly formats
2. **RAG-Scraper**: Extract and process content from websites, PDFs, CSVs, and more

## Features

### Repository Processing (Repomix)

- **Input Methods**:
  - GitHub repository URL (public or private with authentication)
  - ZIP file upload containing code
  
- **Output Formats**:
  - XML (optimized for AI consumption)
  - Markdown (human-readable)
  - Plain text
  - JSON
  
- **Advanced Options**:
  - Code compression (reduces token count while preserving structure)
  - Include/ignore patterns for selective processing
  - Private repository access with GitHub tokens

### Content Processing (RAG-Scraper)

- **Input Methods**:
  - Website URLs with recursive link following
  - Plain text input
  - PDF document upload
  - CSV file upload (converted to markdown tables)
  - JSON file upload (formatted for readability)
  
- **Processing Options**:
  - Configurable search depth for web scraping
  - Automatic content type detection
  - Markdown conversion for optimal AI consumption

## How It Works

### Repository Processing

1. Enter a GitHub repository URL or upload a ZIP file containing your code
2. Configure output format and options
3. Click "Process Repository"
4. The tool will:
   - Download or extract the repository
   - Process it using Repomix
   - Return the formatted code ready for AI consumption

### Content Processing

1. Enter a URL or upload a file (PDF, CSV, JSON)
2. Configure processing options
3. Click "Process Content"
4. The tool will:
   - Fetch and extract the content
   - Convert it to a suitable format
   - Return the processed content ready for AI consumption

## Example Use Cases

- **Code Understanding**: Process a GitHub repository to help AI understand its structure and functionality
- **Documentation Generation**: Extract code and have AI generate comprehensive documentation
- **Bug Fixing**: Share your codebase with AI to help identify and fix bugs
- **Feature Implementation**: Get AI assistance in implementing new features
- **Web Content Analysis**: Extract content from websites for summarization or analysis
- **Data Processing**: Convert PDFs, CSVs, and JSON files into formats suitable for AI consumption

## Security and Rate Limiting

- **Security**:
  - Private repository support with GitHub tokens
  - Secure handling of authentication credentials
  - Size limits on uploaded files

- **Rate Limiting**:
  - Processing time limits to prevent abuse
  - Request rate limiting to ensure fair usage

## Technical Details

This Space combines:

- **Repomix**: A Node.js tool for packing code repositories into AI-friendly formats
- **RAG-Scraper**: A Python tool for scraping and processing web content
- **Gradio**: For the web interface
- **Docker**: For the environment with both Python and Node.js

## Example Prompts

The interface includes example prompts for different use cases to help you get started with using the processed output with AI assistants.

## Local Installation

If you want to run this tool locally:

1. Clone the repository:
   ```bash
   git clone https://huggingface.co/spaces/[your-username]/rag-scraper-repomix
   cd rag-scraper-repomix
   ```

2. Build and run with Docker:
   ```bash
   docker build -t rag-scraper-repomix .
   docker run -p 7860:7860 rag-scraper-repomix
   ```

3. Access the interface at http://localhost:7860

## Credits

- [Repomix](https://github.com/yamadashy/repomix) by yamadashy
- [RAG-Scraper](https://github.com/yourusername/RAG-Scraper) for web content processing

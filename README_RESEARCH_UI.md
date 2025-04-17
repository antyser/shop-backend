# AI Research Assistant - Streamlit UI

## Overview

The AI Research Assistant is a Streamlit-based user interface for conducting comprehensive AI-powered research on any topic. It leverages powerful language models and internet search to generate detailed, well-structured research reports automatically.

## Features

- **Automated Research Planning**: Generate a comprehensive research plan for any query.
- **Concurrent Web Searches**: Execute multiple searches simultaneously to gather diverse information.
- **Report Synthesis**: Automatically compile and organize findings into a cohesive report.
- **Interactive UI**: User-friendly interface for submitting queries and viewing results.
- **Progress Tracking**: Real-time updates on research progress.
- **Download Reports**: Save reports as text files for later reference.
- **Error Handling**: Robust error management with helpful troubleshooting tips.

## Installation

### Prerequisites
- Python 3.9 or higher
- Git

### Setup
1. Clone the repository:
   ```bash
   git clone [repository-url]
   cd shop-backend
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   - Create a `.env` file in the project root
   - Add the following variables:
     ```
     OPENAI_API_KEY=your_openai_api_key
     SEARCHAPI_API_KEY=your_searchapi_key
     ```

## Usage

### Starting the Application

You can start the application in two ways:

1. **Using the script (recommended)**:
   ```bash
   ./run_research_ui.sh
   ```
   This script checks for required API keys and starts the Streamlit app.

2. **Direct Streamlit command**:
   ```bash
   streamlit run app/streamlit_research_ui.py
   ```

### Using the Research Assistant

1. Open your browser and navigate to `http://localhost:8503`
2. Enter your research query in the text input field
3. Click the "Start Research" button
4. The system will:
   - Generate a research plan
   - Execute searches based on the plan
   - Synthesize the findings into a structured report
5. Once complete, you can:
   - Review the research plan, search results, and final report
   - Download the report as a text file

### Example Queries

Here are some example research queries to try:

- "What are the environmental impacts of electric vehicles compared to conventional cars?"
- "How has artificial intelligence transformed healthcare in the last decade?"
- "What are the most effective strategies for reducing plastic pollution in oceans?"
- "What is the current state of quantum computing and its potential applications?"
- "How do different diet types affect long-term health outcomes?"

## How It Works

The AI Research Assistant follows a structured workflow:

1. **Planning Phase**: The system analyzes your query and creates a detailed research plan with specific search instructions.

2. **Search Phase**: Multiple search operations are executed concurrently based on the research plan.

3. **Synthesis Phase**: The system aggregates search results and generates a coherent, structured report that addresses your query.

4. **Output Phase**: The final report is presented in the UI and made available for download.

## Troubleshooting

If you encounter issues:

1. **API Key Errors**: Ensure your API keys are correctly set in the `.env` file.

2. **Connection Issues**: Check your internet connection. The tool requires internet access to perform searches.

3. **Timeout Errors**: For complex queries, the system may take longer to respond. Try simplifying your query.

4. **Quality Issues**: If results are not satisfactory, try rephrasing your query to be more specific or providing additional context.

5. **Logs**: Check the terminal where you started the application for detailed logs and error messages.

## Technical Details

- Backend: Python with FastAPI
- Frontend: Streamlit
- Language Model: OpenAI GPT models
- Search: SearchAPI (powered by Google)
- Asynchronous processing for concurrent searches

## Limitations

- Searches are limited by the rate limits of the underlying search and language model APIs.
- The system works best with factual queries rather than opinion-based questions.
- Reports are generated based on available search results, which may not be exhaustive for all topics.

## Privacy and Data Usage

- Queries and research results are not stored permanently by default.
- Your API keys are used only for the intended services and are not shared.
- Search results reflect what's available online and may contain biases present in the source material.

## Development

For those interested in contributing or customizing:

1. The main UI file is located at `app/streamlit_research_ui.py`
2. Core research logic is in `app/llm/agents/research_manager.py`
3. Search functionality is implemented in `app/llm/agents/search_agent.py`
4. Planning is handled by `app/llm/agents/planner_agent.py`

## License

This project is licensed under the terms of the MIT license. 
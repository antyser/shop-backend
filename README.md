# AI Research Assistant

![Status](https://img.shields.io/badge/status-active-success.svg)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)

## 🔍 Overview

A powerful AI-powered research assistant that helps you generate comprehensive reports on any topic using advanced language models and internet search capabilities.

## ✨ Features

- **AI-Powered Research**: Generate detailed reports from any query
- **Web Search Integration**: Leverage internet data for up-to-date information
- **Intelligent Planning**: AI creates optimized research plans
- **User-Friendly Interface**: Easy-to-use Streamlit UI
- **Concurrent Processing**: Parallel execution for faster results

## 🚀 Getting Started

### 1. Prerequisites

- Python 3.9+
- Internet connection
- OpenAI API key
- SearchAPI key

### 2. Installation

```bash
# Clone the repository
git clone [repository-url]
cd shop-backend

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
# Create a .env file with:
# OPENAI_API_KEY=your_openai_api_key
# SEARCHAPI_API_KEY=your_searchapi_key
```

### 3. Launch

```bash
# Use the provided script
./run_research_ui.sh

# Or run directly with Streamlit
streamlit run app/streamlit_research_ui.py
```

The UI will be available at: http://localhost:8503

## 📚 Documentation

For detailed information about the Research UI, installation, usage, and technical details, please see:

- [Research UI Documentation](README_RESEARCH_UI.md)

## 🔄 Workflow

1. **Input Query**: Specify your research topic
2. **AI Planning**: Generate a research strategy
3. **Execute Searches**: Gather relevant information
4. **Synthesize Report**: Compile findings into a coherent document
5. **Download**: Save your report for later use

## 🛡️ License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔗 Related Projects

- [Search Agent](app/llm/agents/search_agent.py) - Handles web search functionality
- [Planner Agent](app/llm/agents/planner_agent.py) - Creates research strategies
- [Research Manager](app/llm/agents/research_manager.py) - Coordinates the research workflow

## 📝 Note

This is a research tool that relies on external search APIs and language models. The quality of results may vary based on the availability and accuracy of these services.
# Smolagents with OpenAI o3-mini

This project demonstrates how to use the [smolagents](https://github.com/huggingface/smolagents) library with OpenAI's o3-mini model to create powerful AI agents.

## Setup

1. Make sure you have Python 3.8+ installed.

2. Install the required packages:
   ```bash
   pip install smolagents python-dotenv
   ```

3. Create a `.env` file in the project root with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

## Available Scripts

### Basic Example

Run the basic example with:

```bash
python smolagent_demo.py
```

This script creates a simple CodeAgent with the DuckDuckGoSearchTool and uses it to answer a question about France.

### Advanced Example

Run the advanced example with:

```bash
python smolagent_advanced.py
```

This script demonstrates using multiple tools (web search, Python code execution, and web browsing) to find weather information and create a visualization.

### ToolCallingAgent Example

Run the ToolCallingAgent example with:

```bash
python smolagent_toolcalling.py
```

This script shows how to use the ToolCallingAgent (which uses JSON/text blobs for actions instead of code) with web search and user input tools.

## Key Features of smolagents

- **Code Agents**: Agents write their actions in Python code, which is more efficient than traditional tool-calling approaches.
- **Multiple Model Support**: Works with various LLM providers including OpenAI, Anthropic, and open-source models.
- **Tool Integration**: Easily integrate with various tools for web search, code execution, web browsing, and more.
- **Modality Support**: Handles text, vision, video, and audio inputs.

## Documentation

For more information, visit the [smolagents GitHub repository](https://github.com/huggingface/smolagents).
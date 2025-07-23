# LLM Catalyst Agent Project

🧪 **AI-Driven Catalyst Discovery System using DFT Surrogate Models**

This project implements an intelligent system where Large Language Models (LLMs) autonomously explore optimal catalyst compositions using Model Context Protocol (MCP) based Density Functional Theory (DFT) tools.

## 🎯 Project Overview

The LLM Catalyst Agent is designed to discover optimal catalyst compositions with hydrogen adsorption energy close to 0 eV through intelligent exploration. The system leverages:

- **LLM Reasoning**: Advanced language models for intelligent composition exploration
- **MCP Tools**: Model Context Protocol integration for seamless tool usage
- **DFT Surrogate Models**: Fast prediction of adsorption energies
- **Automated Pipeline**: End-to-end workflow from context loading to result analysis

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   LLM Agent     │───▶│   MCP Server     │───▶│  DFT Surrogate  │
│                 │    │                  │    │     Model       │
│ - Context Mgmt  │    │ - Tool Registry  │    │ - Energy Pred.  │
│ - Prompt Gen.   │    │ - Tool Calling   │    │ - Composition   │
│ - Reasoning     │    │ - Result Format  │    │   Analysis      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 📁 Project Structure

```
.
├── agent/                          # LLM Agent Core Components
│   ├── llm_agent.py               # Main LLM agent implementation
│   ├── prompt_manager.py          # Prompt generation and management
│   └── context_manager.py         # Context handling utilities
├── dft/                           # DFT Related Modules
│   ├── dft_surrogate_model.py     # Core surrogate model
│   ├── mcp_dft_surrogate_model.py # MCP wrapper for DFT tools
│   └── parse_last_system_composition.py # Composition parsing utilities
├── data/                          # Dataset and Data Files
│   └── hydrogen/                  # Hydrogen adsorption datasets
├── context/                       # Project Context Files
│   └── sample_context.json        # Sample context configuration
├── prompts/                       # Prompt Templates
├── results/                       # Execution Results and Logs
├── MCP_tools/                     # MCP Tool Configurations
├── main.py                        # Main execution pipeline
├── mcp_dft_surrogate_model.py     # Standalone MCP server
└── eval_results.py                # Result evaluation utilities
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- OpenAI API key (for LLM access)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd llm-catalyst-agent
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   # Create .env file with your OpenAI API key
   echo "OPENAI_API_KEY=your_api_key_here" > .env
   ```

### Running the System

#### Basic Usage
```bash
python main.py
```

#### MCP Server Mode
```bash
python mcp_dft_surrogate_model.py
```

## 🔧 Core Components

### 1. LLM Agent (`agent/llm_agent.py`)
- **Tool Integration**: Seamless MCP tool calling
- **Context Management**: Intelligent context handling
- **Composition Parsing**: Extract and validate catalyst compositions
- **Usage Tracking**: Monitor tool usage and performance

### 2. DFT Surrogate Model (`dft/dft_surrogate_model.py`)
- **Energy Prediction**: Fast adsorption energy calculations
- **Composition Validation**: Ensure valid catalyst compositions
- **Performance Optimization**: Efficient surrogate model implementation

### 3. MCP Server (`mcp_dft_surrogate_model.py`)
- **Tool Registry**: Available DFT tools for LLM
- **Request Handling**: Process tool calls from LLM agents
- **Result Formatting**: Structure results for LLM consumption

### 4. Pipeline Management (`main.py`)
- **Context Loading**: Initialize project context
- **Search Group Preparation**: Prepare candidate compositions
- **Prompt Generation**: Create effective prompts for LLM
- **Result Analysis**: Evaluate tool usage and effectiveness

## 📊 Features

### 🎯 Intelligent Exploration
- **Context-Aware Reasoning**: LLM considers project context and goals
- **Iterative Refinement**: Progressive improvement of catalyst compositions
- **Multi-Objective Optimization**: Balance multiple catalyst properties

### 🔧 MCP Tool Integration
- **Seamless Tool Calling**: Natural language to tool execution
- **Tool Usage Tracking**: Monitor and analyze tool utilization
- **Error Handling**: Robust error handling for tool failures

### 📈 Performance Monitoring
- **Usage Statistics**: Track tool call frequency and success rates
- **Result Logging**: Comprehensive logging of all operations
- **Performance Analysis**: Evaluate system effectiveness

## 🧮 Usage Examples

### Basic Composition Discovery
```python
from agent.llm_agent import LLMAgent
from agent.prompt_manager import PromptManager

# Initialize components
agent = LLMAgent(use_mcp_tools=True)
prompt_manager = PromptManager()

# Create prompt with context
context = {"target": "hydrogen adsorption energy close to 0 eV"}
search_group = {"compositions": ["Pt0.5Ru0.5", "Pt0.7Pd0.3"]}
prompt = prompt_manager.build_prompt(context, search_group)

# Get LLM recommendation
result = agent.ask(prompt)
composition = agent.parse_composition(result)
```

### Tool Usage Analysis
```python
# Get tool usage statistics
tool_summary = agent.get_tool_usage_summary()
print(f"Total calls: {tool_summary['total_calls']}")
print(f"Success rate: {tool_summary['successful_calls']/tool_summary['total_calls']:.2%}")
```

## 📋 Dependencies

### Core Requirements
- `openai>=1.0.0` - OpenAI API integration
- `mcp>=1.0.0` - Model Context Protocol
- `pandas>=1.5.0` - Data manipulation
- `numpy>=1.21.0` - Numerical computing

### Optional Dependencies
- `scikit-learn>=1.1.0` - Machine learning utilities
- `matplotlib>=3.5.0` - Visualization
- `seaborn>=0.12.0` - Statistical visualization

See `requirements.txt` for complete dependency list.

## 📈 Results and Evaluation

### Output Structure
```json
{
  "prompt": "Generated prompt for LLM",
  "llm_output": "LLM response with recommendations",
  "extracted_composition": {"Pt": 0.5, "Ru": 0.5},
  "mcp_tool_usage": {
    "total_calls": 5,
    "successful_calls": 5,
    "functions_used": {"get_adsorp_energy": 3}
  },
  "timestamp": "2024-01-01T12:00:00"
}
```

### Evaluation Metrics
- **Tool Utilization Rate**: Percentage of successful MCP tool calls
- **Composition Quality**: Adsorption energy proximity to target (0 eV)
- **Exploration Efficiency**: Number of evaluations to find optimal composition

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- DFT community for theoretical foundations
- MCP developers for tool integration framework
- OpenAI for language model capabilities

## 📞 Contact

For questions and support, please open an issue in the repository.

---

**Note**: This project is part of ongoing research in AI-driven materials discovery. Results should be validated through experimental verification.
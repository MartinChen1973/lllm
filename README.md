# lllm
Learn Large Language Model

## About This Project

This project is a comprehensive learning resource for Large Language Model (LLM) programming and applications. It contains tutorials, examples, and hands-on exercises covering various aspects of LLM development using LangChain, LangGraph, and other modern LLM frameworks.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Attribution

This project is **primarily based on** the [LangChain Documentation](https://github.com/langchain-ai/docs) project (MIT License), with significant modifications and additions for educational purposes.

A **smaller portion** of the code and materials is derived from the [Alibaba Cloud ACP Learning](https://github.com/AlibabaCloudDocs/aliyun_acp_learning) project (Apache License 2.0).

We gratefully acknowledge both projects for their excellent educational materials and examples. For detailed attribution information, see the [NOTICE](NOTICE) file.

### Source Attribution:

- **Primary Source (Majority)**: [LangChain Docs](https://github.com/langchain-ai/docs) - MIT License  
  Copyright (c) 2025 LangChain

- **Secondary Source (Partial)**: [Alibaba Cloud ACP Learning](https://github.com/AlibabaCloudDocs/aliyun_acp_learning) - Apache License 2.0  
  Copyright Alibaba Cloud

All modifications and derivative works maintain compatibility with both licenses.

## Project Structure

- `src/` - Source code for lessons and examples
  - `lesson00_Cursor/` - Cursor AI guide
  - `lesson10_Dev/` - Development lessons
    - `1010_Langchain/` - LangChain examples and tutorials
    - `1020_DeepAgents/` - Deep learning agents
  - `lesson20_Ops/` - Operations lessons
    - `lesson30_Testing/` - Testing strategies
    - `lesson31_Production/` - Production deployment
    - `lesson32_Evaluation/` - Model evaluation
    - `lesson33_Compliance/` - Compliance and safety
    - `lesson34_Pricing/` - Cost optimization
  - `utilities/` - Utility functions and helpers
  - `before_enrol/` - Pre-enrollment materials
  - `legacy_v0.3/` - Legacy code from previous versions

- `tests/` - Test suite for the project
- `docs/` - Documentation and course materials
- `mist/` - Additional utilities

## Setup

1. Clone this repository:
   ```bash
   git clone <your-repo-url>
   cd lllm
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Install Node.js dependencies (for Marp slides):
   ```bash
   npm install
   ```

4. Set up your API keys:
   - Copy `_example.env` to `.env`
   - Fill in your API keys for OpenAI, Anthropic, or other LLM providers

## Usage

Explore the lessons in the `src/` directory. Each lesson contains:
- Markdown documentation explaining concepts
- Python code examples
- Hands-on exercises

## Contributing

Contributions are welcome! Please ensure that:
- Your contributions comply with the MIT License
- You properly attribute any third-party code or resources
- You follow the existing code style and structure

## Acknowledgments

Special thanks to:
- The [LangChain team](https://github.com/langchain-ai) for their excellent documentation and examples
- [Alibaba Cloud](https://github.com/AlibabaCloudDocs) for their educational materials on LLM applications

## Contact

For questions, feedback, or issues, please open an issue in this repository.

## Legal

This project complies with the license requirements of all source materials. See [NOTICE](NOTICE) for detailed attribution and [LICENSING_NOTES.md](LICENSING_NOTES.md) for comprehensive licensing information.
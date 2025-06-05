---

# Darwin Gödel Machine

**An open-ended, self-improving AI system that evolves its own source code using a local LLM.**
Built for autonomy, reflection, and code evolution — all running locally via [Ollama](https://ollama.com) and models like Llama 3.

---

## Overview

The Darwin Gödel Machine (DGM) is a system that:

* Initializes with a basic coding agent
* Uses a local large language model (LLM) to propose self-modifications
* Evaluates modified agents via tests or benchmarks
* Retains improved agents in an evolving archive
* Runs completely offline with no API keys or cloud access

---

## Features

* Fully local inference via Ollama + Llama3
* Code-editing agents powered by foundation models
* Archive of evolving agents (each with performance and full source)
* Open-ended exploration and branching from past agents
* Modular, inspectable components (tools, logs, test scoring)

---

## Requirements

* Python 3.10+
* Ubuntu/Linux recommended
* [Ollama](https://ollama.com/) installed and running locally
* `llama3` or similar model pulled:

  ```bash
  ollama pull llama3
  ```

---

## Setup

1. **Clone the repo**

   ```bash
   git clone https://github.com/yourusername/darwin-godel-machine.git
   cd darwin-godel-machine
   ```

2. **Create virtual environment**

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Export environment variables (optional)**

   ```bash
   export OLLAMA_MODEL=llama3
   export OLLAMA_API_URL=http://localhost:11434/v1
   ```

5. **Run the Darwin Gödel Machine**

   ```bash
   python dgm.py --benchmark_name SWE-bench --iterations 10
   ```

---

## Project Structure

```
Darwin-Godel-Machine/
├── dgm.py                # Main DGM loop
├── coding_agent.py       # Agent logic (self-editing, benchmarking)
├── llm_withtools.py      # LLM interface (Ollama chat)
├── tools/                # Tool definitions (editor, bash, etc.)
├── utils/                # Logging, Git utils, scoring
├── archive/              # Stores all discovered agents
├── chat_history.md       # (Optional) conversation log
└── tests/                # Test infrastructure
```

---

## Archive Output

Each run produces a growing `archive/` of agents:

```
archive/
├── initial_agent/
│   ├── code/
│   └── performance.txt
├── child_1f43b2c3_perf_0.450/
└── child_a92fbbc2_perf_0.681/
```

Each subdirectory contains:

* The full working code of the agent
* Its performance score on the benchmark

---

## Customization

* Modify `evaluate_agent()` in `eval_utils.py` to use your own tasks, metrics, or test suites.
* Add new tools in `tools/` and expose them via prompt or callable interfaces.
* Replace the seed `agent.py` with your own scaffolding or language-specific agents.
* Extend scoring to include safety, diversity, or explainability.

---

## Roadmap

* Long-term memory for agents
* Multi-agent competition
* UI for archive browsing
* Plugin-style tool framework
* Language support beyond Python

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---
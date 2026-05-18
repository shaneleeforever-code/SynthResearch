# SynthResearch

SynthResearch is a Streamlit application for running synthetic user research. It helps product teams create diverse AI personas, conduct qualitative interviews or focus groups, run quantitative concept scoring, and generate structured research reports.

The project is inspired by the idea behind synthetic populations and simulated social research: use carefully designed agents to explore early product hypotheses before investing in expensive fieldwork. It is not a replacement for real user research, but it can help teams sharpen questions, compare concepts, and surface likely objections faster.

## What It Can Do

- Generate diverse synthetic personas from a target audience description.
- Support qualitative 1:1 interviews with multiple AI participants.
- Support focus group discussions with persona-specific interaction styles.
- Support quantitative concept scoring across configurable dimensions.
- Generate qualitative and quantitative research reports.
- Save research projects locally and reopen them from the homepage.
- Switch between Chinese and English UI/output.

## Typical Use Cases

- Early product discovery.
- Concept testing before building a prototype.
- Comparing multiple product concepts.
- Exploring pains, goals, and objections across user segments.
- Preparing better real-world interview guides.
- Simulating directional market feedback for internal discussion.

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/shaneleeforever-code/SynthResearch.git
cd SynthResearch
```

### 2. Create a virtual environment

```bash
python -m venv .venv
.venv\Scripts\activate
```

On macOS or Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure your model provider

Copy the example environment file:

```bash
copy config\.env.example config\.env
```

On macOS or Linux:

```bash
cp config/.env.example config/.env
```

Then edit `config/.env`:

```env
OPENAI_API_KEY=sk-your-api-key-here
BASE_URL=https://api.openai.com/v1
MODEL_NAME=gpt-4o
```

The app uses the OpenAI-compatible Chat Completions API. You can point `BASE_URL` and `MODEL_NAME` to another compatible provider if needed.

Testing note: during development, SynthResearch was tested primarily with the Volcengine Ark OpenAI-compatible API. No test API key is included in this repository. To use Volcengine, keep `OPENAI_API_KEY` as the environment variable name and set `BASE_URL` / `MODEL_NAME` to your own Volcengine endpoint and model ID.

### 5. Run the app

```bash
streamlit run app/main.py --server.port 8502
```

Then open:

```text
http://localhost:8502
```

On Windows, you can also run:

```bash
run.bat
```

## Workflow

1. Create a research project.
2. Choose qualitative research or quantitative concept validation.
3. Define the target audience, sample size, concept, and questions or scoring dimensions.
4. Generate synthetic personas.
5. Run interviews, focus groups, or scoring.
6. Generate and export the research report.

## Project Structure

```text
app/
  main.py            # Streamlit entry point
  pages.py           # Main product workflow pages
  persona.py         # Persona generation and interview prompt logic
  interview.py       # 1:1 interview engine
  focus_group.py     # Focus group engine
  quantitative.py    # Quantitative scoring logic
  report.py          # Report generation and export
  engine.py          # OpenAI-compatible model wrapper
  components.py      # Reusable UI components
  styles.py          # Streamlit CSS
  i18n.py            # Chinese / English UI and prompt text
  project_store.py   # Local project persistence
config/
  .env.example       # Example model configuration
tests/
  test_*.py          # Regression tests
```

## Local Storage

SynthResearch stores local project data in:

```text
config/projects_store.json
```

Runtime session cache is stored in:

```text
config/session_cache.json
```

Both files are ignored by Git because they may contain private research data.

## Running Tests

```bash
python -m unittest discover tests
```

## Notes on Synthetic Research

Synthetic personas are useful for exploration, internal alignment, and hypothesis generation. Their output depends on the quality of the prompt, the model, and the assumptions in the target audience description.

For high-stakes product, medical, legal, financial, or policy decisions, validate findings with real users and domain experts.

## License

This project is released under the MIT License.

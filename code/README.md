# Support Triage Agent

This directory contains the code for the support triage agent.

## Setup

1. Create and activate a virtual environment using [uv](https://github.com/astral-sh/uv):
	```sh
	uv venv .venv
	# On Windows:
	.venv\Scripts\activate
	# On macOS/Linux:
	source .venv/bin/activate
	```

2. Install dependencies:
	```sh
	uv pip install -r requirements.txt
	```

3. Configure environment:
	Copy `.env.example` to `.env` and add your API keys.

## Run

Run the agent on the support tickets:
```sh
python main.py
```

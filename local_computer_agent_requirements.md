# Local Computer Agent System (IronClaw + Ollama + Fara)

Project Requirements Document

------------------------------------------------------------------------

## 1. Project Background

Recent advances in LLM-based agents have enabled systems that can:

-   understand user goals
-   plan actions
-   execute tools
-   interact with operating systems and web applications

However, most existing solutions rely heavily on cloud APIs for:

-   vision understanding
-   screen analysis
-   browser control

This creates several problems:

-   high token cost
-   latency
-   privacy concerns
-   dependency on external APIs

To address this, this project proposes a **local-first computer agent
architecture** built around:

-   **IronClaw** as the tool runtime
-   **Ollama** for running local models
-   **Fara** as the vision decision model
-   **Python automation** for controlling the operating system and
    browser

The system will allow an AI planner to operate the computer locally
without sending screenshots to cloud APIs.

------------------------------------------------------------------------

## 2. Project Goals

The project aims to build a **local computer-use agent MVP** with the
following capabilities:

1.  Accept user tasks through an LLM planner.
2.  Translate tasks into tool calls (skills).
3.  Execute skills locally through IronClaw.
4.  Use a **local vision model (Fara)** to interpret screen content.
5.  Control the operating system using mouse and keyboard automation.
6.  Optionally automate web browsing using a headless browser.
7.  Maintain a modular architecture for future expansion.

The system should support:

-   local inference
-   modular skills
-   minimal external API usage
-   future integration with advanced agent frameworks.

------------------------------------------------------------------------

## 3. System Architecture

High level architecture:

    User Task
       ↓
    Planner LLM
       ↓
    IronClaw Runtime
       ↓
    Skill Layer
       ↓
    Local Agent Service (Python)
       ↓
    Automation / Vision
       ├ Screenshot
       ├ Fara Vision Model
       ├ Mouse / Keyboard
       └ Browser Automation

Key design principles:

-   Planner handles reasoning
-   Skills handle execution
-   Vision model handles screen understanding
-   Automation layer handles OS interaction

------------------------------------------------------------------------

## 4. Core Components

### 4.1 Planner LLM

Responsible for:

-   task understanding
-   deciding which skill to use
-   generating tool calls

Planner models may include:

-   local LLM
-   cloud fallback LLM

Configuration placeholder:

    PLANNER_MODEL = ____________________
    PLANNER_FALLBACK_MODEL = ____________________

------------------------------------------------------------------------

### 4.2 IronClaw Runtime

IronClaw provides:

-   tool schema definition
-   capability control
-   skill invocation
-   tool execution sandbox

Configuration placeholder:

    IRONCLAW_INSTALL_PATH = ____________________
    IRONCLAW_PROJECT_DIR = ____________________

------------------------------------------------------------------------

### 4.3 Local Agent Service

A local Python service responsible for:

-   implementing skills
-   calling Ollama models
-   controlling the OS
-   managing automation tools

Suggested framework:

    FastAPI

Service endpoint example:

    http://localhost:8000

------------------------------------------------------------------------

### 4.4 Vision Model (Fara)

Fara is used to:

-   interpret screenshots
-   determine GUI actions
-   identify UI elements

Example pipeline:

    Screenshot
       ↓
    Fara model
       ↓
    Action JSON

Configuration placeholder:

    FARA_MODEL_NAME = hf.co\bartowski\microsoft_Fara-7B-GGUF

------------------------------------------------------------------------

### 4.5 Automation Layer

Automation modules provide:

  Function             Suggested Library
  -------------------- -------------------
  Screenshot           mss
  Mouse control        pyautogui
  Keyboard control     pyautogui
  Browser automation   playwright

------------------------------------------------------------------------

## 5. Skill System

The agent exposes capabilities through **skills**.

Each skill represents a tool callable by the planner.

### Skill Structure

Each skill should include:

-   name
-   description
-   parameters
-   execution logic

------------------------------------------------------------------------

## 6. Required Skills

### 6.1 computer_use

Purpose:

Operate the computer to accomplish a goal.

Example:

    computer_use("click the login button")

Execution pipeline:

    screenshot
       ↓
    Fara model
       ↓
    action prediction
       ↓
    mouse/keyboard execution

Parameters:

  Parameter   Type     Description
  ----------- -------- --------------------------------------
  goal        string   description of desired screen action

------------------------------------------------------------------------

### 6.2 browser_use

Purpose:

Interact with web pages.

Actions may include:

-   open URL
-   click element
-   type text
-   extract content

Browser engine:

    Playwright

Parameters:

  Parameter   Type
  ----------- --------
  action      string
  url         string
  selector    string
  text        string

------------------------------------------------------------------------

### 6.3 read_screen

Purpose:

Understand current screen content.

Pipeline:

    Screenshot → Fara → description

Parameters:

  Parameter   Type
  ----------- --------
  question    string

------------------------------------------------------------------------

### 6.4 run_code

Purpose:

Execute local code.

Supported languages:

-   Python
-   Bash

Parameters:

  Parameter   Type
  ----------- --------
  language    string
  code        string

------------------------------------------------------------------------

### 6.5 search_web

Purpose:

Search the internet and return results.

Parameters:

  Parameter   Type
  ----------- --------
  query       string

------------------------------------------------------------------------

## 7. Configuration Section (To Be Filled)

### Ollama

    OLLAMA_BASE_URL = ____________________
    FARA_MODEL_NAME = ____________________
    PLANNER_MODEL_NAME = ____________________

------------------------------------------------------------------------

### IronClaw

    IRONCLAW_ROOT = ____________________
    IRONCLAW_AGENT_PROJECT = ____________________

------------------------------------------------------------------------

### Agent Service

    AGENT_SERVICE_PORT = ____________________
    SCREEN_CAPTURE_MONITOR = ____________________

------------------------------------------------------------------------

## 8. Future Extensions

Possible extensions include:

-   multi-agent workflows
-   distributed browser workers
-   memory / RAG integration
-   task graph planning
-   remote desktop control
-   reinforcement learning for action policies

------------------------------------------------------------------------

## 9. Deliverables

The initial MVP should include:

-   Local Python agent service
-   IronClaw skill definitions
-   Fara integration via Ollama
-   Basic automation layer
-   Example planner prompts

------------------------------------------------------------------------

## 10. Project Directory Example

    agent-project/

    ├ agent_service
    │   ├ main.py
    │   ├ skills
    │   ├ controller
    │   └ vision
    │
    ├ ironclaw_skills
    │
    ├ config
    │
    └ docs

------------------------------------------------------------------------

End of document.

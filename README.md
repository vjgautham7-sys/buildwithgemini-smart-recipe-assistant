# Smart Recipe Assistant 🍳🤖

Smart Recipe Assistant is an AI-powered culinary companion built with Google's Agent Development Kit (ADK). It provides interactive recipe discovery, image/video dish generation, international recipe searches, and sandbox code execution for culinary math and nutrition scaling.

---

## 🌟 Implemented Features & Capabilities

The agent is built with ADK and `gemini-flash-latest`, integrating the following tools and Google Cloud services:

### 🗄️ 1. Local Firestore Database (`(default)`)
- **`search_recipes`**: Queries local recipes stored in Google Cloud Firestore by keyword, dish name, or cuisine.
- **`add_recipe`**: Saves new user-contributed recipes into the `recipes` collection in Firestore.
- **`get_recipe_details`**: Retrieves complete recipe data (ingredients, prep time, instructions, dietary tags) by document ID.

### 🖼️ 2. Dish Photo Generation (`gemini-2.5-flash-image` + Cloud Storage)
- **`generate_recipe_image`**: Generates photorealistic dish food photos using Vertex AI `gemini-2.5-flash-image` and uploads them to a public Cloud Storage bucket (`smart-recipe-assistant-qwiklabs-gcp-01-26a2a5aa51e9`), returning a public HTTPS URL.

### 🎥 3. Dish Video Clips (`gemini-omni-flash-preview` + Cloud Storage)
- **`generate_recipe_video`**: Generates short food preparation video clips using Google's Omni model (`gemini-omni-flash-preview`) in the `global` Vertex AI region. Saves the video as an ADK session artifact (`tool_context.save_artifact`) and uploads it to public Cloud Storage, returning a public HTTPS URL.

### 🌐 4. Global Recipe Search (TheMealDB API)
- **`search_global_recipes`**: Searches real-world international recipes using TheMealDB public API. Returns recipe instructions, area/cuisine, ingredients, thumbnail URLs, and YouTube video links.

### 🐍 5. Agent Engine Sandbox Code Executor
- **`AgentEngineSandboxCodeExecutor`**: Safely executes Python code blocks in an isolated Vertex AI Agent Engine Sandbox (`projects/172056128991/locations/us-east1/reasoningEngines/523673199053897728`) for serving size scaling, nutritional math, and data processing.

### 📱 6. Rich UI Rendering (A2UI v0.8)
- **A2UI Schema Manager & Callback**: Emits structured A2UI v0.8 cards rendered inline in `adk web` via `after_model_callback=a2ui_callback`.

---

## 🚧 Status of Planned Features

- **Vertex AI Memory Bank (Cross-session Memory)**: *Planned, not yet implemented.*
- **Custom Production Web Frontend**: *Planned, not yet implemented.*

---

## 🚀 Local Setup & Execution Instructions

### Prerequisites
- Python 3.10+
- [`uv`](https://docs.astral.sh/uv/) package manager
- Google Cloud SDK & `agents-cli`

### Installation
1. Install project dependencies:
   ```bash
   uv sync
   ```

2. Seed the Firestore database with sample recipes:
   ```bash
   uv run python seed_db.py
   ```

### Running the Agent Locally

- **Command Line Interface (CLI)**:
  ```bash
  agents-cli run "Search recipes for Tuscan Chicken"
  ```

- **ADK Web UI Playground**:
  ```bash
  uv run adk web --port 8080 --allow_origins "*" --reload_agents
  ```
  *(Note: Turn Token Streaming OFF in the dev UI settings gear so A2UI cards render inline).*

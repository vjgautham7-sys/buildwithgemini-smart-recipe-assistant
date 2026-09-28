# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
from pathlib import Path
from a2ui.basic_catalog.provider import BasicCatalog
from a2ui.schema.manager import A2uiSchemaManager
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.code_executors.agent_engine_sandbox_code_executor import (
    AgentEngineSandboxCodeExecutor,
)
from google.adk.models import Gemini
from google.genai import types

from app.a2ui_utils import a2ui_callback
from app.tools import (
    add_recipe,
    generate_recipe_image,
    generate_recipe_video,
    get_recipe_details,
    search_global_recipes,
    search_recipes,
)


def _get_agent_engine_resource_name() -> str | None:
    metadata_path = Path(__file__).parent.parent / "deployment_metadata.json"
    if metadata_path.exists():
        try:
            data = json.loads(metadata_path.read_text())
            return data.get("remote_agent_runtime_id")
        except Exception:
            pass
    return None


agent_engine_name = _get_agent_engine_resource_name()
code_executor = AgentEngineSandboxCodeExecutor(
    agent_engine_resource_name=agent_engine_name
)

schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

instruction = schema_manager.generate_system_prompt(
    role_description=(
        "You are Smart Recipe Assistant, an expert culinary AI guide. You help users search local and global recipes, "
        "discover dish ideas, view ingredients & preparation steps, add new recipes to the shared catalog, "
        "generate realistic photo images and short video clips of dishes, and execute Python code for calculations."
    ),
    workflow_description=(
        "Analyze the request and return structured UI when appropriate. "
        "Use search_recipes for local Firestore queries, search_global_recipes for international recipe searches, "
        "generate_recipe_image to create dish photos, generate_recipe_video to create dish video demonstrations, "
        "and your Python code executor for calculations and sandbox tasks."
    ),
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        '{"Image": {"url": {"literalString": "https://..."}}}. Never point an '
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)

root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-flash-latest",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=instruction,
    code_executor=code_executor,
    tools=[
        search_recipes,
        search_global_recipes,
        add_recipe,
        get_recipe_details,
        generate_recipe_image,
        generate_recipe_video,
    ],
    after_model_callback=a2ui_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)

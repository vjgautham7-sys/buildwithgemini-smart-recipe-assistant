import base64
import json
import logging
import os
import urllib.parse
import urllib.request
import uuid
from typing import Any
from google import genai
from google.adk.tools import ToolContext
from google.cloud import firestore, storage
from google.genai import types

logger = logging.getLogger(__name__)

# Hardcoded project ID as required to avoid Agent Platform project number resolution issues
FIRESTORE_PROJECT_ID = "qwiklabs-gcp-01-26a2a5aa51e9"
GCS_BUCKET_NAME = "smart-recipe-assistant-qwiklabs-gcp-01-26a2a5aa51e9"

_db = None


def get_firestore_client() -> firestore.Client:
    """Gets or initializes the Firestore client with hardcoded project ID."""
    global _db
    if _db is None:
        _db = firestore.Client(project=FIRESTORE_PROJECT_ID, database="(default)")
    return _db


def search_recipes(query: str = "", cuisine: str = "") -> list[dict[str, Any]]:
    """Searches for recipes in the Firestore database by query keyword or cuisine.

    Args:
        query: Search term to match against recipe names or ingredients (e.g. "pasta", "chicken", "avocado").
        cuisine: Optional filter for cuisine type (e.g. "Italian", "Mexican", "Japanese").

    Returns:
        A list of matching recipe dictionaries.
    """
    db = get_firestore_client()
    recipes_ref = db.collection("recipes")

    results = []
    docs = recipes_ref.stream()

    q_lower = query.lower().strip()
    c_lower = cuisine.lower().strip()

    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id

        name = data.get("name", "").lower()
        doc_cuisine = data.get("cuisine", "").lower()
        ingredients = [ing.lower() for ing in data.get("ingredients", [])]
        tags = [t.lower() for t in data.get("dietary_tags", [])]

        match = True
        if c_lower and c_lower not in doc_cuisine:
            match = False

        if q_lower:
            in_name = q_lower in name
            in_ing = any(q_lower in ing for ing in ingredients)
            in_tags = any(q_lower in tag for tag in tags)
            if not (in_name or in_ing or in_tags):
                match = False

        if match:
            results.append(data)

    return results


def add_recipe(
    name: str,
    cuisine: str,
    ingredients: list[str],
    instructions: str,
    prep_time_minutes: int,
    dietary_tags: list[str] = None,
) -> dict[str, Any]:
    """Adds a new recipe to the Firestore database.

    Args:
        name: Name of the recipe (e.g. "Tuscan Garlic Pasta").
        cuisine: Cuisine type (e.g. "Italian").
        ingredients: List of ingredients (e.g. ["pasta", "garlic", "olive oil", "parmesan"]).
        instructions: Step-by-step preparation instructions.
        prep_time_minutes: Preparation and cooking time in minutes.
        dietary_tags: Optional tags (e.g. ["Vegetarian", "Quick", "Gluten-Free"]).

    Returns:
        A dictionary containing the added recipe details including its generated ID.
    """
    if dietary_tags is None:
        dietary_tags = []

    db = get_firestore_client()
    recipes_ref = db.collection("recipes")

    recipe_data = {
        "name": name,
        "cuisine": cuisine,
        "ingredients": ingredients,
        "instructions": instructions,
        "prep_time_minutes": prep_time_minutes,
        "dietary_tags": dietary_tags,
    }

    doc_ref = recipes_ref.add(recipe_data)[1]
    recipe_data["id"] = doc_ref.id
    return {"status": "success", "recipe": recipe_data}


def get_recipe_details(recipe_id: str) -> dict[str, Any]:
    """Retrieves full details for a specific recipe by ID.

    Args:
        recipe_id: Unique document ID of the recipe.

    Returns:
        Recipe details dictionary if found, or an error dictionary.
    """
    db = get_firestore_client()
    doc_ref = db.collection("recipes").document(recipe_id)
    doc = doc_ref.get()

    if doc.exists:
        data = doc.to_dict()
        data["id"] = doc.id
        return data
    return {"error": f"Recipe with ID '{recipe_id}' not found."}


def generate_recipe_image(dish_name: str, description: str = "") -> dict[str, Any]:
    """Generates a realistic photo of a recipe dish using AI and uploads it to Cloud Storage.

    Args:
        dish_name: Name of the dish (e.g. "Tuscan Garlic Chicken", "Avocado Bowl").
        description: Optional brief description or visual details to include in the image prompt.

    Returns:
        A dictionary with the generation status and public image URL.
    """
    try:
        genai_client = genai.Client(
            vertexai=True,
            project=FIRESTORE_PROJECT_ID,
            location="us-central1",
        )
        prompt = f"Generate a realistic, appetizing food photograph of {dish_name}."
        if description:
            prompt += f" Details: {description}"

        response = genai_client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=prompt,
        )

        image_bytes = None
        mime_type = "image/png"

        for part in response.candidates[0].content.parts:
            if part.inline_data and part.inline_data.data:
                image_bytes = part.inline_data.data
                if part.inline_data.mime_type:
                    mime_type = part.inline_data.mime_type
                break

        if not image_bytes:
            return {"status": "error", "message": "Failed to generate image bytes."}

        ext = "png" if "png" in mime_type else "jpg"
        clean_name = dish_name.lower().replace(" ", "_")
        filename = f"recipe_{clean_name}_{uuid.uuid4().hex[:6]}.{ext}"

        storage_client = storage.Client(project=FIRESTORE_PROJECT_ID)
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(image_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/{filename}"
        return {
            "status": "success",
            "dish_name": dish_name,
            "image_url": public_url,
        }
    except Exception as e:
        logger.exception("Error generating recipe image: %s", e)
        return {"status": "error", "message": str(e)}


def search_global_recipes(query: str = "") -> list[dict[str, Any]]:
    """Searches real-world international recipes from TheMealDB public API.

    Args:
        query: Name or ingredient term to search for (e.g. "pasta", "curry", "pie", "chicken").

    Returns:
        A list of matching recipe dictionaries with instructions, ingredients, area, and thumbnail.
    """
    api_key = os.getenv("MEALDB_API_KEY", "1")
    endpoint = f"https://www.themealdb.com/api/json/v1/{api_key}/search.php?s={urllib.parse.quote(query)}"

    try:
        req = urllib.request.Request(
            endpoint, headers={"User-Agent": "SmartRecipeAssistant/1.0"}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())

        meals = data.get("meals")
        if not meals:
            return []

        results = []
        for meal in meals[:5]:
            ingredients = []
            for i in range(1, 21):
                ing = meal.get(f"strIngredient{i}")
                measure = meal.get(f"strMeasure{i}")
                if ing and ing.strip():
                    ing_str = f"{measure.strip() if measure else ''} {ing.strip()}".strip()
                    ingredients.append(ing_str)

            results.append({
                "name": meal.get("strMeal"),
                "category": meal.get("strCategory"),
                "area": meal.get("strArea"),
                "instructions": meal.get("strInstructions"),
                "thumbnail_url": meal.get("strMealThumb"),
                "youtube_url": meal.get("strYoutube"),
                "ingredients": ingredients,
            })
        return results
    except Exception as e:
        logger.exception("Error searching global recipes from TheMealDB: %s", e)
        return []


async def generate_recipe_video(
    dish_name: str,
    description: str = "",
    tool_context: ToolContext | None = None,
) -> dict[str, Any]:
    """Generates a short video for a dish using Google's Omni model (gemini-omni-flash-preview) in the global region.

    Saves the video as an artifact for the session and uploads it to public Cloud Storage.

    Args:
        dish_name: Name of the dish (e.g. "Tuscan Garlic Chicken").
        description: Optional motion or visual details for the video.
        tool_context: Injected ADK ToolContext.

    Returns:
        Dict with status, artifact filename, and public video URL.
    """
    try:
        omni_client = genai.Client(
            vertexai=True,
            project=FIRESTORE_PROJECT_ID,
            location="global",
        )
        prompt = f"A realistic 5-second food video demonstrating the preparation of {dish_name}."
        if description:
            prompt += f" Details: {description}"

        interaction = omni_client.interactions.create(
            model="gemini-omni-flash-preview",
            input=prompt,
        )

        video_bytes = None
        if (
            hasattr(interaction, "output_video")
            and interaction.output_video
            and hasattr(interaction.output_video, "data")
        ):
            raw_data = interaction.output_video.data
            if isinstance(raw_data, bytes):
                video_bytes = raw_data
            elif isinstance(raw_data, str):
                video_bytes = base64.b64decode(raw_data)

        if not video_bytes:
            return {"status": "error", "message": "No video data returned from Omni model."}

        clean_name = dish_name.lower().replace(" ", "_")
        filename = f"recipe_video_{clean_name}_{uuid.uuid4().hex[:6]}.mp4"

        # 1. Save artifact for Playground Artifacts panel
        if tool_context:
            await tool_context.save_artifact(
                filename=filename,
                artifact=types.Part.from_bytes(data=video_bytes, mime_type="video/mp4"),
            )

        # 2. Upload video bytes to public Cloud Storage bucket
        storage_client = storage.Client(project=FIRESTORE_PROJECT_ID)
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(video_bytes, content_type="video/mp4")

        public_url = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/{filename}"
        return {
            "status": "success",
            "dish_name": dish_name,
            "artifact_filename": filename,
            "video_url": public_url,
        }
    except Exception as e:
        logger.exception("Error generating recipe video: %s", e)
        return {"status": "error", "message": str(e)}




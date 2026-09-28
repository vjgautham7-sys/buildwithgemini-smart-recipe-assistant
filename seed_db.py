"""Seed script to populate Firestore database with initial recipe items."""

from google.cloud import firestore

# Hardcoded project ID as required to avoid Agent Platform project number resolution issues
FIRESTORE_PROJECT_ID = "qwiklabs-gcp-01-26a2a5aa51e9"

SAMPLE_RECIPES = [
    {
        "name": "Creamy Tuscan Garlic Chicken",
        "cuisine": "Italian",
        "ingredients": [
            "chicken breast",
            "heavy cream",
            "spinach",
            "sun-dried tomatoes",
            "garlic",
            "parmesan cheese",
            "olive oil",
        ],
        "instructions": "Pan-sear chicken breasts until golden. Sauté garlic, sun-dried tomatoes, and spinach. Stir in heavy cream and parmesan. Simmer chicken in sauce for 10 mins.",
        "prep_time_minutes": 25,
        "dietary_tags": ["Keto", "High-Protein", "Gluten-Free"],
    },
    {
        "name": "Avocado & Black Bean Fiesta Bowl",
        "cuisine": "Mexican",
        "ingredients": [
            "black beans",
            "avocado",
            "brown rice",
            "corn",
            "lime",
            "cilantro",
            "salsa",
        ],
        "instructions": "Cook brown rice. Warm black beans and corn with cumin. Assemble bowls with rice, beans, corn, sliced avocado, cilantro, and fresh lime juice.",
        "prep_time_minutes": 15,
        "dietary_tags": ["Vegan", "Vegetarian", "Gluten-Free", "High-Fiber"],
    },
    {
        "name": "Teriyaki Salmon Rice Bowl",
        "cuisine": "Japanese",
        "ingredients": [
            "salmon fillet",
            "teriyaki sauce",
            "jasmine rice",
            "steamed broccoli",
            "sesame seeds",
            "green onion",
        ],
        "instructions": "Glaze salmon with teriyaki sauce and bake at 400°F (200°C) for 12-15 mins. Serve over warm jasmine rice with steamed broccoli and garnish with sesame seeds.",
        "prep_time_minutes": 20,
        "dietary_tags": ["Pescatarian", "High-Protein"],
    },
    {
        "name": "Classic Mediterranean Greek Salad",
        "cuisine": "Greek",
        "ingredients": [
            "cucumber",
            "cherry tomatoes",
            "feta cheese",
            "kalamata olives",
            "red onion",
            "extra virgin olive oil",
            "oregano",
        ],
        "instructions": "Chop cucumbers, tomatoes, and red onion. Combine in a large bowl with kalamata olives and cubed feta. Drizzle generously with olive oil and sprinkle dried oregano.",
        "prep_time_minutes": 10,
        "dietary_tags": ["Vegetarian", "Gluten-Free", "Quick", "Low-Carb"],
    },
]


def seed_database():
    """Seeds the Firestore database with sample recipes."""
    print(f"Connecting to Firestore with project ID: {FIRESTORE_PROJECT_ID}...")
    db = firestore.Client(project=FIRESTORE_PROJECT_ID, database="(default)")
    recipes_ref = db.collection("recipes")

    print("Seeding initial recipes collection...")
    for recipe in SAMPLE_RECIPES:
        # Query existing to avoid duplicates by name
        existing = recipes_ref.where("name", "==", recipe["name"]).get()
        if existing:
            print(f"  - '{recipe['name']}' already exists, skipping.")
        else:
            doc_ref = recipes_ref.add(recipe)[1]
            print(f"  + Added '{recipe['name']}' with ID: {doc_ref.id}")

    print("Database seeding completed successfully! ✅")


if __name__ == "__main__":
    seed_database()

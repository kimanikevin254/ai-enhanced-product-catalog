import os
import base64
from flask import Blueprint, request, render_template, request
from app.extensions import db
from openai import OpenAI
from sqlalchemy import text

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

product_bp = Blueprint("product", __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_text_embedding(text):
    response = openai_client.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )

    return response.data[0].embedding

def encode_image(image_data):
    return base64.b64encode(image_data).decode("utf-8")

def generate_image_caption(image_data):
    base64_image = encode_image(image_data)

    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Provide a descriptive caption for this image",
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                    },
                ],
            }
        ],
    )

    return response.choices[0].message.content

def find_similar_products(embedding, limit=2, match_threshold=0.5):
    query = text("""
        SELECT
            id,
            name,
            description,
            price,
            image_url,
            1 - (embedding::vector <=> (:embedding)::vector) AS similarity
        FROM products
        WHERE (embedding::vector <=> (:embedding)::vector) < 1 - :match_threshold
        ORDER BY (embedding::vector <=> (:embedding)::vector)
        LIMIT :limit
    """)

    results = list(db.session.execute(query, {
        "embedding": embedding,
        "limit": limit,
        "match_threshold": match_threshold
    }))

    return [{
        "id": row.id,
        "name": row.name,
        "description": row.description,
        "price": row.price,
        "image_url": row.image_url,
        "similarity": row.similarity
    } for row in results]

@product_bp.route("/search", methods=["GET", "POST"])
def search_product():
    if request.method == "POST":
        products = []

        query = request.form.get("query")
        image = request.files.get("image")

        if query:
            # Text-based search
            embedding = generate_text_embedding(query)
            products = find_similar_products(embedding)
        
        elif image:
            # Image-based search
            # Generate caption for the image
            caption = generate_image_caption(image.read())

            # Generate embedding for the caption
            embedding = generate_text_embedding(caption)

            # Find similar products
            products = find_similar_products(embedding)

        return render_template("search_product.html", products=products)


    return render_template("search_product.html")
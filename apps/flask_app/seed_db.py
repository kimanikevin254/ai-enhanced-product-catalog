import os
import requests
import re
import boto3
import logging
from app.models import Product
from app.extensions import db
from app import create_app
from urllib.parse import urlparse, unquote
from botocore.exceptions import NoCredentialsError

# API URL
DUMMYJSON_URL = "https://dummyjson.com/products"

# AWS S3 Configuration
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET")
AWS_REGION = os.getenv("AWS_REGION")

# Ensure all AWS credentials are set
if not all([AWS_ACCESS_KEY, AWS_SECRET_KEY, AWS_S3_BUCKET, AWS_REGION]):
    raise ValueError("Missing AWS credentials in environment variables!")

# Initialize S3 client
s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION,
)

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger()

def fetch_products():
    """Fetch products from DummyJSON API."""
    logger.info("Fetching products from DummyJSON API...")
    response = requests.get(f"{DUMMYJSON_URL}?limit=5")
    if response.status_code == 200:
        logger.info("Successfully fetched products.")
        return response.json().get("products", [])
    logger.error(f"Failed to fetch products. Status code: {response.status_code}")
    return []

def format_filename(image_url):
    parsed_url = urlparse(image_url)
    filename = os.path.basename(parsed_url.path)
    
    path_parts = parsed_url.path.split("/") 
    if len(path_parts) > 2:
        product_name = path_parts[-2]
    else:
        product_name = "product"
    
    product_name = unquote(product_name)
    product_name = re.sub(r'\s+', '-', product_name.lower())  
    formatted_filename = f"{product_name}-{filename}"
    
    logger.debug(f"Formatted filename: {formatted_filename}")
    return formatted_filename

def upload_to_s3(image_url):
    """Download an image to upload it to S3."""
    try:
        logger.info(f"Downloading image from {image_url}...")
        # Extract filename
        filename = format_filename(image_url)

        # Download image
        response = requests.get(image_url, stream=True)
        if response.status_code != 200:
            logger.error(f"Failed to download image: {image_url}")
            return None
        
        # Upload image to S3
        logger.info(f"Uploading image {filename} to S3...")
        s3_client.upload_fileobj(response.raw, AWS_S3_BUCKET, filename, ExtraArgs={ 'ContentType': 'image/png' })

        # Generate public S3 URL
        s3_url = f"https://{AWS_S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{filename}"
        logger.info(f"Image successfully uploaded to {s3_url}")
        return s3_url
    except NoCredentialsError:
        logger.error("AWS credentials not found!")
        return None
    except Exception as e:
        logger.error(f"Error uploading image {image_url} to S3: {e}")
        return None


def seed_database():
    """Seed the database with products from DummyJSON API."""
    app = create_app()
    with app.app_context():
        logger.info("Starting the product seeding process...")
        products = fetch_products()
        if not products:
            logger.error("No products found to seed!")
            return
                
        for product in products:
            logger.info(f"Processing product: {product['title']}")

            # Upload first image if available
            image_url = None
            if product.get("images"):
                logger.info(f"Uploading image for product {product['title']}")
                image_url = upload_to_s3(product["images"][0])  # Take the first image

            new_product = Product(
                name=product["title"],
                price=product["price"],
                image_url=image_url
            )

            db.session.add(new_product)

        db.session.commit()
        logger.info(f"Successfully seeded {len(products)} products!")

if __name__ == "__main__":
    seed_database()
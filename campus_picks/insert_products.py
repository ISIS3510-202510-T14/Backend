# insert_products.py

import os
import django

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "campus_picks.settings")
django.setup()

from acid_db.models import Product
import uuid

# Sample products to insert
products = [
    {
        "name": "Wireless Headphones",
        "description": "Noise-cancelling over-ear headphones",
        "price": 99.99,
        "image_url": "https://picsum.photos/seed/headphones/300/300",
        "category": "Electronics",
    },
    {
        "name": "Running Shoes",
        "description": "Lightweight sneakers for daily running",
        "price": 79.50,
        "image_url": "https://loremflickr.com/320/240/shoes",
        "category": "Sportswear",
    },
    {
        "name": "Coffee Mug",
        "description": "Ceramic mug with ergonomic handle",
        "price": 12.00,
        "image_url": "https://placehold.co/300x300?text=Coffee+Mug",
        "category": "Home",
    },
    {
        "name": "E-Book Reader",
        "description": "6'' e-ink display with adjustable backlight",
        "price": 129.99,
        "image_url": "https://picsum.photos/seed/ebook/300/300",
        "category": "Electronics",
    },
    {
        "name": "Blender",
        "description": "High-speed kitchen blender, 1.5 L",
        "price": 49.95,
        "image_url": "https://loremflickr.com/320/240/blender",
        "category": "Kitchen",
    },
    {
        "name": "Classic Novel",
        "description": "Paperback edition of a timeless classic",
        "price": 15.00,
        "image_url": "https://placehold.co/300x300/CCCCCC/000000/png?text=Book",
        "category": "Books",
    },
    {
        "name": "Yoga Mat",
        "description": "Non-slip exercise mat, 6 mm thick",
        "price": 25.00,
        "image_url": "https://picsum.photos/seed/yoga/300/300",
        "category": "Sportswear",
    },
    {
        "name": "Desk Lamp",
        "description": "LED desk lamp with adjustable arm",
        "price": 30.49,
        "image_url": "https://loremflickr.com/320/240/desklamp",
        "category": "Office",
    },
    {
        "name": "Water Bottle",
        "description": "Insulated stainless steel bottle, 500 ml",
        "price": 18.75,
        "image_url": "https://placehold.co/300x300?text=Bottle",
        "category": "Outdoors",
    },
    {
        "name": "Gaming Mouse",
        "description": "Ergonomic mouse with RGB lighting",
        "price": 45.99,
        "image_url": "https://picsum.photos/seed/mouse/300/300",
        "category": "Electronics",
    },
]

# Insert products
for p in products:
    Product.objects.create(
        product_id=uuid.uuid4(),
        name=p["name"],
        description=p["description"],
        price=p["price"],
        image_url=p["image_url"],
        category=p["category"],
    )

print(f"Inserted {len(products)} products.")

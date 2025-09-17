from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from catalog.models import Category, Product
from io import BytesIO
try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class Command(BaseCommand):
    help = 'Create sample products with images for testing'

    def handle(self, *args, **options):
        # Create categories first
        categories_data = [
            {'name': 'Electronics', 'slug': 'electronics', 'description': 'Latest electronic gadgets'},
            {'name': 'Fashion', 'slug': 'fashion', 'description': 'Trendy clothing and accessories'},
            {'name': 'Home & Garden', 'slug': 'home-garden', 'description': 'Home decor and garden supplies'},
            {'name': 'Sports', 'slug': 'sports', 'description': 'Sports equipment and accessories'},
        ]

        categories = {}
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                slug=cat_data['slug'],
                defaults=cat_data
            )
            categories[cat_data['slug']] = category
            if created:
                self.stdout.write(f"Created category: {category.name}")

        # Sample products data
        products_data = [
            {
                'title': 'Wireless Bluetooth Headphones',
                'slug': 'wireless-bluetooth-headphones',
                'category': 'electronics',
                'price': 89.99,
                'sale_price': 69.99,
                'description': 'Premium wireless headphones with noise cancellation and 30-hour battery life. Perfect for music lovers and professionals.',
                'short_description': 'Premium wireless headphones with noise cancellation',
                'stock_quantity': 25,
                'featured': True,
                'sku': 'WBH-001',
                'image_color': (52, 152, 219)  # Blue
            },
            {
                'title': 'Organic Cotton T-Shirt',
                'slug': 'organic-cotton-t-shirt',
                'category': 'fashion',
                'price': 29.99,
                'description': 'Comfortable and sustainable organic cotton t-shirt. Available in multiple colors and sizes.',
                'short_description': 'Comfortable and sustainable organic cotton t-shirt',
                'stock_quantity': 50,
                'featured': True,
                'sku': 'OCT-002',
                'image_color': (46, 204, 113)  # Green
            },
            {
                'title': 'Smart Home Security Camera',
                'slug': 'smart-home-security-camera',
                'category': 'electronics',
                'price': 149.99,
                'sale_price': 119.99,
                'description': 'WiFi-enabled security camera with 1080p HD video, night vision, and mobile app control.',
                'short_description': 'WiFi security camera with 1080p HD and night vision',
                'stock_quantity': 15,
                'sku': 'SHSC-003',
                'image_color': (155, 89, 182)  # Purple
            },
            {
                'title': 'Ceramic Plant Pot Set',
                'slug': 'ceramic-plant-pot-set',
                'category': 'home-garden',
                'price': 45.99,
                'description': 'Beautiful set of 3 ceramic plant pots with drainage holes. Perfect for indoor plants and herbs.',
                'short_description': 'Set of 3 ceramic plant pots with drainage',
                'stock_quantity': 30,
                'sku': 'CPP-004',
                'image_color': (230, 126, 34)  # Orange
            },
            {
                'title': 'Professional Yoga Mat',
                'slug': 'professional-yoga-mat',
                'category': 'sports',
                'price': 79.99,
                'sale_price': 59.99,
                'description': 'Non-slip professional yoga mat made from eco-friendly materials. Perfect grip and cushioning for all yoga practices.',
                'short_description': 'Non-slip eco-friendly yoga mat with perfect grip',
                'stock_quantity': 20,
                'featured': True,
                'sku': 'PYM-005',
                'image_color': (231, 76, 60)  # Red
            },
        ]

        for product_data in products_data:
            # Check if product already exists
            if Product.objects.filter(slug=product_data['slug']).exists():
                self.stdout.write(f"Product {product_data['title']} already exists, skipping...")
                continue

            # Create product
            category = categories[product_data['category']]
            product = Product.objects.create(
                title=product_data['title'],
                slug=product_data['slug'],
                category=category,
                price=product_data['price'],
                sale_price=product_data.get('sale_price'),
                description=product_data['description'],
                short_description=product_data['short_description'],
                stock_quantity=product_data['stock_quantity'],
                featured=product_data.get('featured', False),
                sku=product_data['sku'],
                is_active=True
            )

            # Create a simple colored image as placeholder if PIL is available
            if PIL_AVAILABLE:
                try:
                    image = Image.new('RGB', (400, 400), product_data['image_color'])
                    draw = ImageDraw.Draw(image)

                    # Try to use a default font, fallback to basic if not available
                    try:
                        font = ImageFont.truetype("arial.ttf", 24)
                    except:
                        try:
                            font = ImageFont.load_default()
                        except:
                            font = None

                    # Add product name text if font is available
                    if font:
                        text = product_data['title'][:20] + "..." if len(product_data['title']) > 20 else product_data['title']
                        try:
                            bbox = draw.textbbox((0, 0), text, font=font)
                            text_width = bbox[2] - bbox[0]
                            text_height = bbox[3] - bbox[1]
                        except:
                            text_width, text_height = 200, 30

                        x = (400 - text_width) // 2
                        y = (400 - text_height) // 2
                        draw.text((x, y), text, fill='white', font=font)

                    # Save image to BytesIO
                    img_buffer = BytesIO()
                    image.save(img_buffer, format='PNG')
                    img_buffer.seek(0)

                    # Add image to product
                    image_name = f"{product_data['slug']}.png"
                    product.image.save(
                        image_name,
                        ContentFile(img_buffer.getvalue()),
                        save=True
                    )
                except Exception as e:
                    self.stdout.write(f"Could not create image for {product.title}: {e}")

            self.stdout.write(f"Created product: {product.title}")

        self.stdout.write(
            self.style.SUCCESS('Successfully created sample products!')
        )
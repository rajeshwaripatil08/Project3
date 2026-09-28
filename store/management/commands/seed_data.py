from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from store.models import Category, Product, Order, OrderItem


class Command(BaseCommand):
    help = 'Seeds database with initial categories, products, demo users, and a sample order'

    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding ShopSphere data...")

        # 1. Create or retrieve Admin User
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@shopsphere.local',
                'first_name': 'Admin',
                'last_name': 'Superuser',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("Created admin user: admin / admin123"))
        else:
            self.stdout.write("Admin user already exists.")

        # 2. Create or retrieve Customer User
        customer_user, created = User.objects.get_or_create(
            username='customer',
            defaults={
                'email': 'customer@example.com',
                'first_name': 'Sarah',
                'last_name': 'Jenkins',
                'is_staff': False,
                'is_superuser': False,
            }
        )
        if created:
            customer_user.set_password('customer123')
            customer_user.save()
            self.stdout.write(self.style.SUCCESS("Created demo customer user: customer / customer123"))
        else:
            self.stdout.write("Customer user already exists.")

        # 3. Create Categories
        categories_data = [
            {'name': 'Electronics', 'slug': 'electronics', 'icon_name': 'bi-laptop', 'description': 'Laptops, headphones, smartphones, and cutting-edge tech gadgets.'},
            {'name': 'Fashion & Apparel', 'slug': 'fashion-apparel', 'icon_name': 'bi-bag-heart', 'description': 'Modern clothing, shoes, premium watches, and accessories.'},
            {'name': 'Home & Living', 'slug': 'home-living', 'icon_name': 'bi-house-check', 'description': 'Kitchen appliances, smart lighting, decor, and ergonomic furniture.'},
            {'name': 'Books & Stationery', 'slug': 'books-stationery', 'icon_name': 'bi-book', 'description': 'Bestsellers, technical guides, notebooks, and writing essentials.'},
        ]

        cat_objs = {}
        for cat_data in categories_data:
            cat, _ = Category.objects.get_or_create(
                slug=cat_data['slug'],
                defaults={
                    'name': cat_data['name'],
                    'icon_name': cat_data['icon_name'],
                    'description': cat_data['description'],
                }
            )
            cat_objs[cat.slug] = cat

        self.stdout.write(self.style.SUCCESS(f"Categories ready: {len(cat_objs)} categories."))

        # 4. Products Data
        products_data = [
            {
                'category': cat_objs['electronics'],
                'name': 'Wireless Noise-Cancelling Headphones Pro',
                'slug': 'wireless-noise-cancelling-headphones-pro',
                'description': 'Engineered with active noise cancellation, 40-hour battery life, high-fidelity dynamic drivers, and memory-foam earcups for all-day comfort.',
                'price': Decimal('249.99'),
                'discount_price': Decimal('199.99'),
                'stock': 25,
                'is_featured': True,
                'image_url': 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800&auto=format&fit=crop&q=80',
            },
            {
                'category': cat_objs['electronics'],
                'name': 'Ultra-Slim Mechanical Mechanical Keyboard',
                'slug': 'ultra-slim-mechanical-keyboard',
                'description': 'Tactile mechanical switches with per-key RGB backlighting, durable aircraft-grade aluminum frame, and wireless Bluetooth 5.2 connectivity.',
                'price': Decimal('129.50'),
                'discount_price': Decimal('99.00'),
                'stock': 18,
                'is_featured': True,
                'image_url': 'https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=800&auto=format&fit=crop&q=80',
            },
            {
                'category': cat_objs['electronics'],
                'name': 'Smart Fitness Watch Series 5',
                'slug': 'smart-fitness-watch-series-5',
                'description': 'Water-resistant smartwatch featuring OLED touchscreen, heart-rate tracking, GPS tracking, sleep monitoring, and multi-day battery endurance.',
                'price': Decimal('179.00'),
                'discount_price': None,
                'stock': 30,
                'is_featured': False,
                'image_url': 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=800&auto=format&fit=crop&q=80',
            },
            {
                'category': cat_objs['fashion-apparel'],
                'name': 'Classic Minimalist Leather Chrono Watch',
                'slug': 'classic-minimalist-leather-chrono-watch',
                'description': 'Handcrafted genuine leather strap with stainless steel casing, Japanese quartz movement, and scratch-resistant sapphire crystal glass.',
                'price': Decimal('159.00'),
                'discount_price': Decimal('119.00'),
                'stock': 12,
                'is_featured': True,
                'image_url': 'https://images.unsplash.com/photo-1524805444758-089113d48a6d?w=800&auto=format&fit=crop&q=80',
            },
            {
                'category': cat_objs['fashion-apparel'],
                'name': 'Everyday Urban Canvas Backpack',
                'slug': 'everyday-urban-canvas-backpack',
                'description': 'Water-repellent rugged canvas backpack with a dedicated padded 15.6-inch laptop compartment, hidden anti-theft pocket, and USB charging port.',
                'price': Decimal('79.99'),
                'discount_price': Decimal('59.99'),
                'stock': 22,
                'is_featured': False,
                'image_url': 'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=800&auto=format&fit=crop&q=80',
            },
            {
                'category': cat_objs['fashion-apparel'],
                'name': 'Premium Polarized Aviator Sunglasses',
                'slug': 'premium-polarized-aviator-sunglasses',
                'description': 'UV400 protection with glare-reducing polarized lenses, lightweight metal frame, and protective hard shell travel case.',
                'price': Decimal('89.00'),
                'discount_price': None,
                'stock': 40,
                'is_featured': False,
                'image_url': 'https://images.unsplash.com/photo-1511499767150-a48a237f0083?w=800&auto=format&fit=crop&q=80',
            },
            {
                'category': cat_objs['home-living'],
                'name': 'Ceramic Pour-Over Coffee Maker & Carafe',
                'slug': 'ceramic-pour-over-coffee-maker',
                'description': 'Artisan ceramic dripper with heat-resistant borosilicate glass carafe. Brew barista-grade specialty pour-over coffee right at home.',
                'price': Decimal('49.95'),
                'discount_price': Decimal('39.95'),
                'stock': 15,
                'is_featured': False,
                'image_url': 'https://images.unsplash.com/photo-1517668808822-9ebb02f2a0e6?w=800&auto=format&fit=crop&q=80',
            },
            {
                'category': cat_objs['home-living'],
                'name': 'Aroma Ultrasonic Essential Oil Diffuser',
                'slug': 'aroma-ultrasonic-diffuser',
                'description': 'Sleek wood-grain ultrasonic diffuser with 7 ambient LED lighting modes, whisper-quiet operation, and automatic safety shut-off.',
                'price': Decimal('42.00'),
                'discount_price': Decimal('32.00'),
                'stock': 20,
                'is_featured': True,
                'image_url': 'https://images.unsplash.com/photo-1608571423902-eed4a5ad8108?w=800&auto=format&fit=crop&q=80',
            },
            {
                'category': cat_objs['books-stationery'],
                'name': 'Refillable Hardcover Leather Journal',
                'slug': 'refillable-leather-journal',
                'description': 'Genuine distress-look leather cover with 240 pages of 120gsm bleed-proof archival paper. Perfect for journaling, sketching, or meeting notes.',
                'price': Decimal('34.90'),
                'discount_price': None,
                'stock': 35,
                'is_featured': False,
                'image_url': 'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=800&auto=format&fit=crop&q=80',
            },
            {
                'category': cat_objs['books-stationery'],
                'name': 'Precision Fountain Pen & Ink Bottle Set',
                'slug': 'precision-fountain-pen-set',
                'description': 'Medium nib brass fountain pen with smooth ink feed, piston converter, and 50ml bottle of rich black pigment ink.',
                'price': Decimal('65.00'),
                'discount_price': Decimal('48.00'),
                'stock': 8,
                'is_featured': False,
                'image_url': 'https://images.unsplash.com/photo-1585336261026-7f5117961b7b?w=800&auto=format&fit=crop&q=80',
            },
        ]

        for p_data in products_data:
            Product.objects.get_or_create(
                slug=p_data['slug'],
                defaults=p_data
            )

        self.stdout.write(self.style.SUCCESS(f"Products ready: {len(products_data)} products."))

        # 5. Create a sample order for Customer to test Order Tracking
        sample_order, o_created = Order.objects.get_or_create(
            order_number='ORD-DEMO2026',
            defaults={
                'user': customer_user,
                'full_name': 'Sarah Jenkins',
                'email': 'customer@example.com',
                'phone': '+1 (555) 382-9912',
                'address': '742 Evergreen Terrace, Suite 4B',
                'city': 'Springfield',
                'state': 'Oregon',
                'postal_code': '97477',
                'payment_method': 'card',
                'payment_status': 'Completed',
                'subtotal': Decimal('239.94'),
                'shipping_cost': Decimal('0.00'),
                'total_amount': Decimal('239.94'),
                'status': 'Shipped',
                'tracking_number': 'TRK-FEDEX-99882211',
                'admin_notes': 'Package dispatched via FedEx Express Ground.',
            }
        )
        if o_created:
            prod1 = Product.objects.get(slug='wireless-noise-cancelling-headphones-pro')
            prod2 = Product.objects.get(slug='ceramic-pour-over-coffee-maker')
            OrderItem.objects.create(
                order=sample_order,
                product=prod1,
                product_name=prod1.name,
                product_price=prod1.effective_price,
                quantity=1,
                total_price=prod1.effective_price
            )
            OrderItem.objects.create(
                order=sample_order,
                product=prod2,
                product_name=prod2.name,
                product_price=prod2.effective_price,
                quantity=1,
                total_price=prod2.effective_price
            )
            self.stdout.write(self.style.SUCCESS("Created demo order: ORD-DEMO2026 with 'Shipped' status!"))

        self.stdout.write(self.style.SUCCESS("All seed data successfully generated!"))

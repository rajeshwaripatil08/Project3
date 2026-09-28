from decimal import Decimal
import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Category, Product, Cart, CartItem, Order, OrderItem


class ECommerceTestCase(TestCase):
    def setUp(self):
        self.client = Client()

        # Users
        self.admin_user = User.objects.create_user(
            username='adminuser',
            email='admin@example.com',
            password='Password123!',
            is_staff=True,
            is_superuser=True
        )
        self.customer = User.objects.create_user(
            username='testcustomer',
            email='customer@example.com',
            password='Password123!'
        )

        # Category
        self.category = Category.objects.create(
            name='Test Electronics',
            slug='test-electronics',
            icon_name='bi-laptop',
            description='Test category description'
        )

        # Products
        self.product = Product.objects.create(
            category=self.category,
            name='Test Smartphone Pro',
            slug='test-smartphone-pro',
            description='A flagship phone for testing.',
            price=Decimal('500.00'),
            discount_price=Decimal('450.00'),
            stock=10,
            is_featured=True,
            is_active=True
        )

        self.out_of_stock_product = Product.objects.create(
            category=self.category,
            name='Sold Out Widget',
            slug='sold-out-widget',
            description='Zero inventory.',
            price=Decimal('50.00'),
            stock=0,
            is_active=True
        )

    def test_catalog_and_product_detail(self):
        """Catalog page renders products and filters work."""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Smartphone Pro')

        # Filter by category
        response = self.client.get(reverse('home'), {'category': 'test-electronics'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Smartphone Pro')

        # Search
        response = self.client.get(reverse('home'), {'q': 'Smartphone'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Smartphone Pro')

        # Product detail
        response = self.client.get(reverse('product_detail', kwargs={'slug': self.product.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Smartphone Pro')
        self.assertContains(response, '$450.00')

    def test_cart_operations(self):
        """Add to cart, update quantity, and remove item."""
        self.client.login(username='testcustomer', password='Password123!')

        # Add to cart
        response = self.client.post(reverse('add_to_cart', kwargs={'product_id': self.product.id}), {'quantity': 2})
        self.assertEqual(response.status_code, 302)

        cart = Cart.objects.get(user=self.customer)
        self.assertEqual(cart.total_items, 2)
        self.assertEqual(cart.total_price, Decimal('900.00'))

        item = cart.items.first()

        # Increment quantity
        self.client.post(reverse('update_cart_item', kwargs={'item_id': item.id}), {'action': 'increment'})
        item.refresh_from_db()
        self.assertEqual(item.quantity, 3)

        # Decrement quantity
        self.client.post(reverse('update_cart_item', kwargs={'item_id': item.id}), {'action': 'decrement'})
        item.refresh_from_db()
        self.assertEqual(item.quantity, 2)

        # Remove item
        self.client.post(reverse('remove_cart_item', kwargs={'item_id': item.id}))
        self.assertEqual(cart.items.count(), 0)

    def test_checkout_and_order_creation(self):
        """Placing an order creates an order, deducts stock, and clears cart."""
        self.client.login(username='testcustomer', password='Password123!')

        # Add 2 items
        self.client.post(reverse('add_to_cart', kwargs={'product_id': self.product.id}), {'quantity': 2})
        cart = Cart.objects.get(user=self.customer)
        self.assertEqual(cart.items.count(), 1)

        initial_stock = self.product.stock

        checkout_data = {
            'full_name': 'Test Customer',
            'email': 'customer@example.com',
            'phone': '1234567890',
            'address': '123 Test Street',
            'city': 'Sample City',
            'state': 'Sample State',
            'postal_code': '12345',
            'payment_method': 'card',
        }

        response = self.client.post(reverse('checkout'), checkout_data)
        self.assertEqual(response.status_code, 302)

        order = Order.objects.filter(user=self.customer).first()
        self.assertIsNotNone(order)
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.payment_status, 'Completed')

        # Stock should be reduced by 2
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, initial_stock - 2)

        # Cart should be cleared
        cart.refresh_from_db()
        self.assertEqual(cart.items.count(), 0)

        # Test customer order tracking view
        tracking_resp = self.client.get(reverse('order_tracking', kwargs={'order_number': order.order_number}))
        self.assertEqual(tracking_resp.status_code, 200)
        self.assertContains(tracking_resp, order.order_number)

    def test_role_based_access(self):
        """Staff can access admin pages; normal user is redirected or blocked."""
        # Unauthenticated user
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 302)

        # Regular customer user
        self.client.login(username='testcustomer', password='Password123!')
        response = self.client.get(reverse('admin_dashboard'))
        # Should redirect away from staff-only area
        self.assertEqual(response.status_code, 302)
        self.client.logout()

        # Admin / Staff user
        self.client.login(username='adminuser', password='Password123!')
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Store Administration Portal')

        # Admin product list
        prod_resp = self.client.get(reverse('admin_product_list'))
        self.assertEqual(prod_resp.status_code, 200)
        self.assertContains(prod_resp, 'Test Smartphone Pro')

    def test_rest_api_endpoints(self):
        """Test JSON REST APIs for products, cart, and orders."""
        # 1. GET /api/products/
        response = self.client.get(reverse('api_products_list'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('products', data)
        self.assertTrue(len(data['products']) >= 2)

        # 2. GET /api/products/<id>/
        response = self.client.get(reverse('api_product_detail', kwargs={'product_id': self.product.id}))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['product']['name'], 'Test Smartphone Pro')

        # 3. POST /api/cart/add/
        add_resp = self.client.post(
            reverse('api_cart_add'),
            data=json.dumps({'product_id': self.product.id, 'quantity': 1}),
            content_type='application/json'
        )
        self.assertEqual(add_resp.status_code, 200)
        self.assertTrue(add_resp.json()['success'])

        # 4. GET /api/cart/
        cart_resp = self.client.get(reverse('api_cart_detail'))
        self.assertEqual(cart_resp.status_code, 200)
        self.assertEqual(cart_resp.json()['total_items'], 1)

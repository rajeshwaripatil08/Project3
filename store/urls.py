from django.urls import path
from . import views
from . import api_views

urlpatterns = [
    # Storefront & Catalog
    path('', views.home, name='home'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),

    # Shopping Cart
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('cart/remove/<int:item_id>/', views.remove_cart_item, name='remove_cart_item'),

    # Checkout & Customer Orders
    path('checkout/', views.checkout, name='checkout'),
    path('order/success/<str:order_number>/', views.order_success, name='order_success'),
    path('orders/', views.order_history, name='order_history'),
    path('orders/<str:order_number>/track/', views.order_tracking, name='order_tracking'),

    # User Authentication & Profile
    path('register/', views.user_register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('profile/', views.user_profile, name='profile'),

    # Admin Management Portal (Role-based: Staff/Admin)
    path('store-admin/', views.admin_dashboard, name='admin_dashboard'),
    path('store-admin/products/', views.admin_product_list, name='admin_product_list'),
    path('store-admin/products/add/', views.admin_product_add, name='admin_product_add'),
    path('store-admin/products/<int:product_id>/edit/', views.admin_product_edit, name='admin_product_edit'),
    path('store-admin/products/<int:product_id>/delete/', views.admin_product_delete, name='admin_product_delete'),
    path('store-admin/orders/', views.admin_order_list, name='admin_order_list'),
    path('store-admin/orders/<str:order_number>/', views.admin_order_detail, name='admin_order_detail'),
    path('store-admin/categories/', views.admin_category_list, name='admin_category_list'),

    # Backend RESTful JSON APIs
    path('api/products/', api_views.api_products_list, name='api_products_list'),
    path('api/products/<int:product_id>/', api_views.api_product_detail, name='api_product_detail'),
    path('api/cart/', api_views.api_cart_detail, name='api_cart_detail'),
    path('api/cart/add/', api_views.api_cart_add, name='api_cart_add'),
    path('api/cart/update/', api_views.api_cart_update, name='api_cart_update'),
    path('api/orders/', api_views.api_orders_list, name='api_orders_list'),
    path('api/orders/<str:order_number>/', api_views.api_order_detail, name='api_order_detail'),
    path('api/orders/<str:order_number>/status/', api_views.api_order_update_status, name='api_order_update_status'),
]

# ShopSphere - Full-Stack E-Commerce Web Application

A full-stack, production-grade E-Commerce Web Application built with **HTML5 & CSS3** frontend and **Django** backend with comprehensive product management, user authentication, role-based access control (Admin / Customer), shopping cart, checkout, live order tracking with step-by-step progress, and RESTful APIs.

---

## 🌟 Key Features

1. **Product Catalog & Browsing**:
   - Dynamic product showcase with category filtering, search keyword matching, and sorting (price low-to-high, high-to-low, newest).
   - Product detail page with image display, stock availability indicators, discount calculation badges, and related items.

2. **Cart & Checkout Functionality**:
   - Persistent shopping cart supporting both guest sessions and authenticated users (auto-merges upon login).
   - Quantity increments, decrements, real-time total calculations, free shipping threshold bar ($100+).
   - Checkout flow with shipping address form, payment options (Cash on Delivery, simulated Card / UPI), stock deduction, and instant order creation.

3. **Live Order Tracking**:
   - 4-stage visual progress timeline: **Order Placed &rarr; Processing &rarr; Shipped &rarr; Delivered** (or **Cancelled**).
   - Carrier tracking numbers and administrative courier notes.
   - Customer Order History page showing past orders, statuses, dates, and order numbers.

4. **User Authentication & Role-Based Access Control**:
   - Customer registration, login, logout, and user profile management.
   - Dedicated **Store Administration Portal** (`/store-admin/`) accessible exclusively by staff/admin users.
   - Admin features: Sales revenue metric cards, inventory stock monitoring, product creation/editing/deletion, and order status updates.
   - Built-in Django Admin (`/admin/`) with inline models and filter controls.

5. **Backend RESTful JSON APIs**:
   - `GET /api/products/` - Filterable product catalog.
   - `GET /api/products/<id>/` - Product details.
   - `GET /api/cart/` - Current user/session cart contents.
   - `POST /api/cart/add/` - Add item to cart.
   - `POST /api/cart/update/` - Update quantity or remove.
   - `GET /api/orders/` - List user orders (or all if admin).
   - `GET /api/orders/<order_number>/` - Order tracking status.
   - `POST /api/orders/<order_number>/status/` - Admin status updater.

6. **Database Integration**:
   - **SQLite** configured out of the box (zero configuration needed).
   - Pre-configured settings to switch to **PostgreSQL** or **MySQL** in `ecommerce_project/settings.py`.

---

## 🚀 How to Run in Visual Studio Code (VS Code)

### Option A: 1-Click Run / Debug (Recommended)
1. Open this project folder (`thiranex3`) in VS Code:
   - File &rarr; Open Folder &rarr; Select `thiranex3`
2. Press **`F5`** (or go to the **Run & Debug** tab on the left and click **"Django: Run Server"**).
3. Open your browser and navigate to:
   ```
   http://127.0.0.1:8000/
   ```

---

### Option B: Using VS Code Terminal
1. Open the integrated terminal in VS Code (`Ctrl + ` ` ` or Terminal &rarr; New Terminal).
2. Activate the virtual environment:
   - **Windows (PowerShell)**:
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```
   - **Windows (Command Prompt)**:
     ```cmd
     .\venv\Scripts\activate.bat
     ```
3. (Optional - already performed) Apply migrations and seed sample data:
   ```bash
   python manage.py migrate
   python manage.py seed_data
   ```
4. Start the Django development server:
   ```bash
   python manage.py runserver
   ```
5. Visit `http://127.0.0.1:8000/` in your browser.

---

## 🔑 Demo Login Credentials

The database has already been seeded with test accounts:

| Role | Username | Password | Access Privileges |
| :--- | :--- | :--- | :--- |
| **Administrator / Staff** | `admin` | `admin123` | Full Admin Dashboard (`/store-admin/`), Django Admin (`/admin/`), Product CRUD, Order Status Updates |
| **Customer** | `customer` | `customer123` | Catalog browsing, Cart, Checkout, Order Tracking, Profile |

*(You can also click **Register** to create any new customer account!)*

---

## 🗄️ Database Integration Options

The application uses Django ORM and comes with SQLite ready to run. To connect to PostgreSQL or MySQL:

Open `ecommerce_project/settings.py` and replace the `DATABASES` block:

### For PostgreSQL:
```python
# Install driver: pip install psycopg2-binary
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'ecommerce_db',
        'USER': 'postgres',
        'PASSWORD': 'your_postgres_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### For MySQL:
```python
# Install driver: pip install pymysql mysqlclient
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'ecommerce_db',
        'USER': 'root',
        'PASSWORD': 'your_mysql_password',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```
After changing the database settings, run:
```bash
python manage.py migrate
python manage.py seed_data
```

---

## 🧪 Running Automated Tests

A complete automated test suite is included in `store/tests.py`. Run it via:
```bash
python manage.py test
```
All tests verify catalog listing, cart manipulation, checkout, role-based security, and REST APIs.

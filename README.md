# 📚 BookShop

A full-featured Django bookstore application: catalog browsing, categories, a session-based shopping cart, order management, Stripe payments, Google OAuth login, and Ukrainian/English localization.

Educational project (Django 6.0.4).

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Option A: Docker (recommended)](#option-a-docker-recommended)
  - [Option B: Local (without Docker)](#option-b-local-without-docker)
- [Environment Variables](#environment-variables)
- [Apps Overview](#apps-overview)
- [The Shopping Cart](#the-shopping-cart)
- [Authentication](#authentication)
- [Permissions](#permissions)
- [Internationalization](#internationalization)
- [Payments (Stripe)](#payments-stripe)
- [Async Views](#async-views)
- [Testing](#testing)
- [Logging](#logging)
- [Profiling](#profiling)
- [Known Limitations / Roadmap](#known-limitations--roadmap)
- [Changelog](#changelog)

---

## Features

- 📖 **Book catalog** — search by title, filter by category, pagination, book detail pages
- 🗂️ **Categories** — CRUD for categories with permission-gated actions, auto-slug generation
- 🛒 **Shopping cart** — session-based cart (works for anonymous users), add/remove/increment via AJAX, self-cleaning if a cart item's book is later deleted
- 📦 **Orders** — order history and detail pages, tied to authenticated users only
- 💳 **Payments** — Stripe Checkout integration (session creation, webhook handling, success/cancel pages, order status updates, email receipts)
- 🔐 **Authentication** — classic username/password (Django `UserCreationForm`-based) **and** Google OAuth via `django-allauth`
- 🌍 **i18n** — Ukrainian (default) and English, with `.po`/`.mo` translation files and a language switcher
- 📊 **Profiling** — `django-silk` integrated for request/query profiling
- 🧪 **Tests** — `pytest` + `pytest-django` covering cart flow, checkout, permissions, payments, and category management

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 6.0.4 (async views in `books` and `categories`) |
| Database | PostgreSQL |
| Payments | Stripe (Checkout Sessions + Webhooks) |
| Auth | `django-allauth` (Google OAuth) + Django's built-in auth |
| Profiling | `django-silk` |
| Testing | `pytest`, `pytest-django`, `pytest-asyncio`, `factory_boy` |
| i18n | Django's built-in `gettext` / `LocaleMiddleware` |
| Containerization | Docker + Docker Compose |
| Frontend | Django templates + Bootstrap 5 (via CDN) |

## Project Structure

```
HW6/
└── bookshop/
    ├── bookshop/          # Project config (settings, urls, wsgi/asgi, test factories)
    ├── books/              # Book catalog: models, views, forms, templates
    ├── categories/         # Category CRUD
    ├── basket/              # Session cart: services.py (SessionCart), context_processors.py, AJAX views
    ├── order/               # Order & OrderItem models, order history views
    ├── payments/            # Stripe checkout, webhooks, success/cancel views
    ├── user/                 # Custom user model, registration/login/logout, Google adapter
    ├── templates/            # Shared base template (base.html)
    ├── locale/                # .po/.mo translation files (en, uk)
    ├── logs/                   # App-generated log files (orders.log, users.log)
    ├── manage.py
    ├── Dockerfile
    ├── docker-compose.yml
    ├── docker-entrypoint.sh
    ├── AI_REVIEW.md
    └── pytest.ini
```

## Getting Started

### Option A: Docker (recommended)

**Requirements:** Docker, Docker Compose.

1. Copy the environment template and fill in your values (see [Environment Variables](#environment-variables)):
   ```bash
   cd HW6/bookshop
   cp .env.example .env   # create this if it doesn't exist yet — see variables below
   ```
2. Build and start the containers:
   ```bash
   docker-compose up --build
   ```
3. The entrypoint script automatically runs migrations and collects static files. The app will be available at:
   ```
   http://localhost:8000/
   ```
4. Create a superuser (in a separate terminal, while containers are running):
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

### Option B: Local (without Docker)

**Requirements:** Python 3.12+, PostgreSQL running locally.

1. Create and activate a virtual environment:
   ```bash
   cd HW6/bookshop
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file (see [Environment Variables](#environment-variables)) with `DB_HOST=localhost`.
4. Run migrations:
   ```bash
   python manage.py migrate
   ```
5. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```
6. Compile translation files (if you've changed any `.po` files):
   ```bash
   python manage.py compilemessages
   ```
7. Run the dev server:
   ```bash
   python manage.py runserver
   ```

## Environment Variables

The project loads a `.env` file via `python-dotenv`. Create `HW6/bookshop/.env` with:

```env
# Django
SECRET_KEY=your-secret-key-here

# PostgreSQL
POSTGRES_DB=bookshop
POSTGRES_USER=bookshop_user
POSTGRES_PASSWORD=your-db-password
DB_HOST=localhost           # use `db` if running via docker-compose network, or host.docker.internal per docker-compose.yml
POSTGRES_PORT=5432

# Stripe
STRIPE_CLIENT_API=sk_test_your_stripe_secret_key

# Email (used for order receipts)
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

> ⚠️ **Security note:** `settings.py` currently has `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` hardcoded and a Stripe **webhook secret** hardcoded directly in `payments/views.py`. Before deploying anywhere beyond local development, move both into environment variables (the project already has `python-dotenv` wired up for this) and rotate any credentials that were previously committed to source control.

## Apps Overview

| App | Responsibility |
|---|---|
| **`user`** | Custom user model (`CustomUser`, extends `AbstractUser` with `phone` and `role`), registration/login/logout views, Google OAuth adapter (`user/adapter.py`), auth-related logging |
| **`books`** | `Book` model, catalog listing (search + category filter + pagination), book detail page, CRUD views gated by `books.add_book` / `books.update_book` / `books.delete_book` permissions |
| **`categories`** | `Category` model (auto-slugified name), category list/detail/CRUD views gated by `categories.*` permissions |
| **`basket`** | `SessionCart` service class managing an anonymous/authenticated user's cart in the Django session (self-cleans if a cart item's book is deleted); a global `cart_count` context processor exposes an accurate, always-fresh cart count to every template; AJAX endpoints for add/remove/increment/decrement |
| **`order`** | `Order` and `OrderItem` models; order history and detail views (login required, users can only see their own orders); auto-recalculates `total_price` on item save |
| **`payments`** | Stripe Checkout session creation, webhook receiver, success/cancel pages; marks orders `paid` and emails a receipt on successful payment |

## The Shopping Cart

The cart is **session-based** (`basket/services.py::SessionCart`) — no `Basket`/`BasketItem` database models are used (those exist in `basket/models.py` but are commented out/dead code). This means:

- Carts work for anonymous (not-logged-in) users.
- A cart is tied to a browser session, not a user account — it won't follow a logged-in user across devices.
- **Self-cleaning:** if a book is deleted from the catalog while it's sitting in someone's cart, `SessionCart` strips that stale entry out automatically the next time the cart is loaded, so counts and totals never reference a book that no longer exists.
- **Global cart badge:** the navbar cart count (`base.html`) is supplied by `basket.context_processors.cart_count`, registered in `TEMPLATES['OPTIONS']['context_processors']` in `settings.py`. This ensures the badge is accurate on *every* page — not just pages that happen to pass their own `cart_count` into context.

> ℹ️ Because this context processor queries the database on every template render, the `books` and `categories` apps' **async** views (`books_view`, `one_book_view`, `categories_list_view`, `one_category_view`) wrap their final `render()` call in `sync_to_async(render)(...)` rather than calling `render()` directly — otherwise Django raises `SynchronousOnlyOperation`. See [Async Views](#async-views).

## Authentication

Two login paths are supported:

1. **Standard registration** — `/user/register/` using `CustomUserCreationForm` (username, email, password, optional phone).
2. **Google OAuth** — via `django-allauth`, configured with `SOCIALACCOUNT_AUTO_SIGNUP = True`. New Google sign-ups get a fallback username derived from their email (see `user/adapter.py`) if none is provided.

Both paths log authentication events to `logs/users.log` via the `user_logger`.

## Permissions

Django's built-in permission system (`app_label.codename`) gates catalog/category management:

| Action | Permission |
|---|---|
| Add book | `books.add_book` |
| Update book | `books.update_book` |
| Delete book | `books.delete_book` |
| Add category | `categories.add_category` |
| Update category | `categories.update_category` |
| Delete category | `categories.delete_category` |

Assign these via the Django admin (`/admin/`) to staff users/groups as needed. Templates conditionally render management UI (`+ Add`, ✏️ Edit, 🗑️ Delete buttons) based on `perms.<app>.<codename>` checks.

> ⚠️ Always double-check permission strings in views against the actual `app_label` and `permission_required` codename declared on the corresponding `CreateView`/`UpdateView`/`DeleteView`. A typo here (e.g. wrong app label, or a codename that doesn't match `permission_required` elsewhere) fails silently — `has_perm()` just returns `False`, it doesn't raise an error — so management buttons quietly disappear for everyone, including superusers, with no error in the logs. See `AI_REVIEW.md` for two real examples of this bug and how they were caught.

## Internationalization

- Default language: **Ukrainian** (`uk`)
- Also supported: **English** (`en`)
- Language switcher lives in the navbar (`base.html`), posts to Django's built-in `set_language` view
- Translation source files: `locale/en/LC_MESSAGES/django.po`

To update translations after changing template/view text:
```bash
python manage.py makemessages -l en
# edit locale/en/LC_MESSAGES/django.po
python manage.py compilemessages
```

## Payments (Stripe)

Flow:
1. User places an order (status `new`) via checkout in the basket app.
2. `payments.views.CheckoutSession` creates a Stripe Checkout Session for the order total (in UAH) and redirects the user to Stripe.
3. On success, Stripe redirects to `/payments/success/?session_id=...`, which:
   - retrieves the session,
   - marks the `Order` as `paid`,
   - emails the customer a receipt.
4. On cancellation, the user is redirected to `/payments/cancel/`.
5. `payments.views.WebhookReceivedView` handles Stripe webhook events for server-to-server confirmation.

You'll need a Stripe account and test API key (`STRIPE_CLIENT_API`) to exercise this flow locally; use [Stripe CLI](https://stripe.com/docs/stripe-cli) to forward webhook events to `localhost:8000/payments/webhook/` during development.

Order checkout (`basket.views.SubmitCartView`) locks the relevant `Book` rows with `select_for_update()` inside `transaction.atomic()` during stock validation and deduction, to prevent two concurrent checkouts from overselling the same low-stock book.

## Async Views

`books.views` and `categories.views` use `async def` views (`books_view`, `one_book_view`, `categories_list_view`, `one_category_view`) that query the database with `async for` / `.aget()` and bridge any remaining synchronous calls (like `request.user.has_perm(...)`) via `sync_to_async`.

Because template rendering can trigger database-touching context processors (notably `basket.context_processors.cart_count`), these views wrap their final template render as:

```python
return await sync_to_async(render)(request, 'template.html', context)
```

instead of calling `render()` directly. Omitting this wrapper causes Django to raise `SynchronousOnlyOperation: You cannot call this from an async context` as soon as any DB-touching context processor runs during rendering.

## Testing

Run the full suite with:
```bash
pytest
```

Configuration (`pytest.ini`):
- `DJANGO_SETTINGS_MODULE = bookshop.settings`
- Auto-discovers `tests.py`, `test_*.py`, `*_tests.py`
- `asyncio_mode = auto` (supports the project's async views/tests)

Test data is generated via `factory_boy` factories in `bookshop/factories.py` (`UserFactory`, `CategoryFactory`, `BookFactory`, `OrderFactory`, `OrderItemFactory`).

Coverage includes:
- Cart add/remove/view flows (`basket/tests.py`)
- Full purchase flow, stock validation, total price calculation, cart clearing (`order/tests.py`)
- Category CRUD and detail views, including async views (`categories/tests.py`)
- Book form validation, search, permission-gated CRUD (`books/tests.py`)
- Registration, login/logout, cross-user order access restrictions (`user/tests.py`)
- Stripe payment success flow with mocked Stripe client (`payments/tests.py`)

> ⚠️ **Gap to be aware of:** the automated suite does not currently cover (1) concurrent checkout requests against the same low-stock book, or (2) a cart referencing a book that gets deleted mid-session. Both scenarios were found and fixed manually during development — see `AI_REVIEW.md`. If you're extending this project, adding regression tests for these two cases is a good next step.

## Logging

Two dedicated file loggers write to `logs/`:

| Logger | File | Logs |
|---|---|---|
| `order_logger` | `logs/orders.log` | Successful order creation |
| `user_logger` | `logs/users.log` | Login, logout, registration (form + Google) events |

Both also log to console. Configured in `bookshop/settings.py` under `LOGGING`.

## Profiling

[`django-silk`](https://github.com/jazzband/django-silk) is enabled for request/SQL profiling. Once running, visit:
```
http://localhost:8000/silk/
```
(Requires `SILK_AUTHENTICATION`/`SILK_AUTHORIZATION` — log in as a staff user first.)

## Known Limitations / Roadmap

- `basket/models.py` (a DB-backed `Basket`/`BasketItem` design) is fully commented out and unused — the cart is currently session-only via `basket/services.py::SessionCart`. This means carts don't persist across devices/browsers for the same logged-in user.
- No automated CI configuration is currently included in the repo.
- Stripe webhook secret and email credentials should be moved to environment variables before any non-local deployment (see [Environment Variables](#environment-variables) note above).
- No regression tests yet for the checkout race condition or the deleted-book cart cleanup (see [Testing](#testing)).
- See `AI_REVIEW.md` for a detailed code review (covering `books`, `categories`, and `basket` view layers).

## Changelog

Notable fixes applied on top of the original project (see `AI_REVIEW.md` for full before/after diffs):

- **Fixed:** wrong permission codenames in `categories/views.py` (`all_categories.*` → `categories.*`) and `books/views.py` (`books.edit_book` → `books.update_book`), which silently hid admin management buttons from everyone, including superusers.
- **Fixed:** checkout race condition in `basket/views.py::SubmitCartView` — stock check-and-deduct is now wrapped in `transaction.atomic()` with `select_for_update()` to prevent overselling under concurrent requests.
- **Fixed:** stale/"phantom" cart entries — `SessionCart` now removes cart items pointing to books that have been deleted from the catalog, and a new `cart_count` context processor keeps the navbar badge accurate on every page (previously it read the raw, uncleaned session dict directly).
- **Fixed:** `SynchronousOnlyOperation` crash introduced by the above — async views in `books`/`categories` now wrap `render()` in `sync_to_async(...)`.
- **Refactored:** `BookForm` moved from `books/views.py` into its own `books/forms.py`, matching the pattern already used by `user/forms.py`.

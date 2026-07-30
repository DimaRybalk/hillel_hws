# AI Code Review — BookShop Project

**Scope:** 3 apps selected from the project, reviewing `views.py` (and related files pulled in along the way) for each:
1. `categories/views.py`
2. `basket/views.py`, `basket/services.py`, `basket/context_processors.py` (new)
3. `books/views.py`, `books/forms.py` (new)

For each area: **Original Code → AI Recommendations → Validity Check → Final Code**.

This review happened in two rounds:
- **Round 1** — static code review of the three apps' views (permission bugs, race condition, code hygiene).
- **Round 2** — a real bug reported after Round 1 shipped ("cart shows quantity 1 for a book that was deleted"), which led to a fix in `basket`, which in turn caused a **new** bug (`SynchronousOnlyOperation`) in the async `books`/`categories` views that had to be fixed too. That chain is documented in full below so nothing is glossed over.

---

## 1. `categories/views.py`

### Original Code
```python
from django.http import Http404
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView,DeleteView,UpdateView
from django.db.models import Count
from categories.models import Category
from books.models import Book
from django.contrib.auth.mixins import PermissionRequiredMixin
from asgiref.sync import sync_to_async
# -------------------------------- Function-Based Views ----------------------------------

# def get_all_categories(request):
#     all_categories = Category.objects.annotate(count_books = Count('books'))
#     if not all_categories.exists():
#         return render(request, 'categories/categories.html', {'error': 'Категорії відсутні', 'all_categories': []})

#     return render(request,'categories/categories.html',{'all_categories': all_categories})



# ------------------------------- Class-Based Views  -------------------------------------

async def categories_list_view(request):
    queryset = Category.objects.annotate(count_books=Count('books', distinct=True)).order_by('name')

    all_categories = []
    async for category in queryset:
        all_categories.append(category)

    def get_user_data():
        return{
            'cart': request.session.get('cart',{}),
            'add': request.user.has_perm('all_categories.add_category'),
            'edit': request.user.has_perm('all_categories.edit_category'),
            'delete': request.user.has_perm('all_categories.delete_category'),
        }
    
    user_data = await sync_to_async(get_user_data)()

    context = {
        'categories': all_categories,
        'can_add': user_data['add'],
        'can_edit': user_data['edit'],
        'can_delete': user_data['delete'],
        'cart_count': len(user_data['cart']),
    }
    return render(request, 'categories/categories.html', context)

class CategoryCreateView(PermissionRequiredMixin,CreateView):
    model = Category
    fields = ['name']
    template_name = 'categories/categories_create_form.html'
    success_url = reverse_lazy('categories_list')

    permission_required = 'categories.add_category'


async def one_category_view(request, pk):
    queryset = Category.objects.annotate(count_books=Count('books', distinct=True))
    try:
        category = await queryset.aget(id=pk)
    except Category.DoesNotExist:
        raise Http404("Категорію не знайдено")


    books_queryset = Book.objects.filter(category=category)
    category_books = []
    async for book in books_queryset:
        category_books.append(book)


    def get_user_and_cart():
        user = request.user
        return {
            'cart': request.session.get('cart', {}),
            'is_auth': user.is_authenticated,
            'username': user.email if user.is_authenticated else None,
        }
        
    data = await sync_to_async(get_user_and_cart)()

    context = {
        'category': category,
        'books': category_books,
        'cart_count': len(data['cart']),
        'current_user': {
            'is_authenticated': data['is_auth'],
            'username': data['username'],
        }
    }
    
    return render(request, 'categories/categories_detail.html', context)


class CategoryDeleteView(PermissionRequiredMixin,DeleteView):
    model = Category
    template_name = 'categories/category_confirm_delete.html'
    success_url = reverse_lazy('categories_list')

    permission_required = 'categories.delete_category'

class CategoryUpdateView(PermissionRequiredMixin,UpdateView):
    model = Category
    template_name = 'categories/categories_update_form.html'
    fields = ['name']
    success_url = reverse_lazy('categories_list')

    permission_required = 'categories.update_category'
```

### AI Recommendations

**Round 1:**

| # | Finding | Severity | Recommendation |
|---|---------|----------|-----------------|
| 1 | `has_perm('all_categories.add_category')` / `'all_categories.edit_category'` / `'all_categories.delete_category'` use the **wrong app label**. The app label is `categories`, not `all_categories`, and `edit_category` isn't a real codename — `CategoryUpdateView.permission_required = 'categories.update_category'`. | **High (bug)** | Fix to `'categories.add_category'`, `'categories.update_category'`, `'categories.delete_category'`. |
| 2 | Unused imports (`ListView`, `DetailView`) and a large block of dead commented-out legacy views. | Low | Remove. |
| 3 | `cart_count` computed manually as `len(user_data['cart'])` in every view — raw session dict length, no validation that referenced books still exist. | *(Not flagged until Round 2 — see below)* | — |

**Round 2 (post-deployment bug):**

| # | Finding | Severity | Recommendation |
|---|---------|----------|-----------------|
| 4 | Manually computing `cart_count` per-view duplicated logic across 4 different functions (2 in `books`, 2 in `categories`) and was the root enabler of the "stale cart count" bug — see the `basket` section below for the full diagnosis. | Medium | Remove manual `cart_count` computation entirely; rely on a new global `basket.context_processors.cart_count` context processor instead (added in Round 2). |
| 5 | Introducing a DB-querying context processor caused these `async def` views to crash with `SynchronousOnlyOperation`, since they called `render()` directly instead of via `sync_to_async`. | **High (regression, caught immediately via manual testing)** | Wrap the final `render()` call in `sync_to_async(render)(...)`. |

### Validity Check
- **Finding #1 confirmed and fixed** — verified against `categories.html`/`categories_detail.html`, which check `perms.categories.update_category` / `perms.categories.delete_category` (correct namespace), while the view computed flags using the wrong one. Buttons were silently broken for everyone, including superusers.
- **Findings #2 confirmed and fixed** — pure cleanup, no behavior change.
- **Finding #4 confirmed and fixed** — removing the duplicated logic was the correct move once a context processor existed; keeping both would have caused the view's explicit context to *shadow* the context processor's (more correct) value on every page render, silently defeating the fix.
- **Finding #5 confirmed and fixed** — reproduced directly from the user's browser: `GET /en/books/stock_books/` returned `500` with `SynchronousOnlyOperation: You cannot call this from an async context`, traced to `basket/context_processors.py` → `SessionCart.__init__` → a DB query, invoked while still inside the un-bridged async call stack. Fixed by wrapping `render()`.

### Final Code
```python
from django.http import Http404
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.db.models import Count
from categories.models import Category
from books.models import Book
from django.contrib.auth.mixins import PermissionRequiredMixin
from asgiref.sync import sync_to_async


async def categories_list_view(request):
    queryset = Category.objects.annotate(count_books=Count('books', distinct=True)).order_by('name')

    all_categories = []
    async for category in queryset:
        all_categories.append(category)

    def get_user_data():
        return {
            'add': request.user.has_perm('categories.add_category'),
            'edit': request.user.has_perm('categories.update_category'),
            'delete': request.user.has_perm('categories.delete_category'),
        }

    user_data = await sync_to_async(get_user_data)()

    context = {
        'categories': all_categories,
        'can_add': user_data['add'],
        'can_edit': user_data['edit'],
        'can_delete': user_data['delete'],
    }
    # render() is wrapped in sync_to_async because template rendering
    # triggers context processors (e.g. basket.context_processors.cart_count)
    # that hit the database — calling that directly from this async view
    # would raise SynchronousOnlyOperation.
    return await sync_to_async(render)(request, 'categories/categories.html', context)


class CategoryCreateView(PermissionRequiredMixin, CreateView):
    model = Category
    fields = ['name']
    template_name = 'categories/categories_create_form.html'
    success_url = reverse_lazy('categories_list')

    permission_required = 'categories.add_category'


async def one_category_view(request, pk):
    queryset = Category.objects.annotate(count_books=Count('books', distinct=True))
    try:
        category = await queryset.aget(id=pk)
    except Category.DoesNotExist:
        raise Http404("Категорію не знайдено")

    books_queryset = Book.objects.filter(category=category)
    category_books = []
    async for book in books_queryset:
        category_books.append(book)

    def get_user_and_cart():
        user = request.user
        return {
            'is_auth': user.is_authenticated,
            'username': user.email if user.is_authenticated else None,
        }

    data = await sync_to_async(get_user_and_cart)()

    context = {
        'category': category,
        'books': category_books,
        'current_user': {
            'is_authenticated': data['is_auth'],
            'username': data['username'],
        }
    }

    return await sync_to_async(render)(request, 'categories/categories_detail.html', context)


class CategoryDeleteView(PermissionRequiredMixin, DeleteView):
    model = Category
    template_name = 'categories/category_confirm_delete.html'
    success_url = reverse_lazy('categories_list')

    permission_required = 'categories.delete_category'


class CategoryUpdateView(PermissionRequiredMixin, UpdateView):
    model = Category
    template_name = 'categories/categories_update_form.html'
    fields = ['name']
    success_url = reverse_lazy('categories_list')

    permission_required = 'categories.update_category'
```

---

## 2. `basket` app — `views.py`, `services.py`, `context_processors.py`

### Original Code

**`basket/views.py`**
```python
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views import View
from books.models import Book
from order.models import Order, OrderItem
from .services import SessionCart
from django.contrib import messages
from silk.profiling.profiler import silk_profile
from django.contrib.auth.mixins import LoginRequiredMixin
import logging




logger = logging.getLogger('order_logger')

class AddToCartView(View):
    def post(self, request, book_id):
        cart = SessionCart(request)
        
        try:
            quantity = int(request.POST.get('quantity', 1))
            if quantity <= 0:
                quantity = 1
        except (ValueError, TypeError):
            quantity = 1
        success = cart.add_to_cart(book_id, quantity=quantity)

        if not success:
            return JsonResponse({
                'status': 'error', 
                'message': 'Вибачте, більше цієї книги немає на складі!'
            })
            
        return JsonResponse({
            'status': 'success',
            'message': 'Книгу додано до кошика!',   
            'cart_count': cart.total_quantity
        })
    
class DeleteBookFromCartView(View):
    def post(self,request,book_id):
        cart = SessionCart(request)
        cart.remove_from_cart(book_id)
        return JsonResponse({'status': 'success', 'message': 'Книгу видалено!'})
    
class DeleteOneBookFromCartView(View):
    def post(self,request,book_id):
        cart = SessionCart(request)
        cart.remove_one_from_cart(book_id)
        return JsonResponse({'status': 'success'})
    
class GetCartData(View):
    def get(self,request):
        cart = SessionCart(request)
        cart_data = cart.get_cart_data()
        cart_data['cart_count'] = cart.total_quantity
        return render(request, 'basket/basket_detail.html', context=cart_data)

class SubmitCartView(LoginRequiredMixin,View):

    @silk_profile(name='Оформлення замовлення (Submit Cart)')
    def post(self,request):
        cart = SessionCart(request)
        cart_data = cart.get_cart_data()

        if not cart_data['cart_items']:
            messages.error(request, "Ваш кошик порожній! Додайте книги перед оформленням замовлення.")
            return redirect('cart_detail')

        for item in cart_data['cart_items']:
            book = item['book']

            if item['quantity'] <= 0:
                messages.error(request, f"Некоректна кількість для книги '{book.title}'.")
                return redirect('cart_detail')

            if book.stock < item['quantity']:
                messages.error(
                    request, 
                    f"Вибачте, книги '{book.title}' недостатньо на складі. "
                    f"Доступно всього: {book.stock} шт."
                )
                return redirect('cart_detail')
            
        order = Order.objects.create(
            user=request.user,
            total_price = cart_data['cart_price']
        )

        for item in cart_data['cart_items']:
            book = item['book']
            book.stock -= item['quantity']
            book.save()

        for item in cart_data['cart_items']:
            OrderItem.objects.create(
                order=order,
                book=item['book'],
                price=item['book'].price,
                quantity=item['quantity']
            )

        cart.clear_cart()

        logger.info(
                    f"УСПІХ: Користувач {order.user.username} (ID: {order.user.id}) створив замовлення №{order.id} "
                    f"на суму {order.total_price} грн. Кількість позицій: {len(cart_data['cart_items'])}"
                )

        return redirect('order_detail', pk=order.id)
```

**`basket/services.py`**
```python
from django.http import JsonResponse

from books.models import Book
from decimal import Decimal


class SessionCart:
    def __init__(self,request):
        self.session = request.session
        cart = self.session.get('cart')

        if not cart:
            cart = self.session['cart'] = {}
        
        self.cart = cart

    def add_to_cart(self,book_id,quantity=1):
        book_id = str(book_id)

        try:
            book = Book.objects.get(id=book_id)
        except Book.DoesNotExist:
            return False
        
        current_quantity = self.cart.get(book_id,0)
        target_quantity = current_quantity + int(quantity)
        
        if target_quantity > book.stock:
            if book.stock > 0:
                self.cart[book_id] = book.stock
            else:
                self.cart.pop(book_id, None)

            self.save()
            return False 
        
        self.cart[book_id] = target_quantity
        self.save()
        return True

    def remove_one_from_cart(self,book_id):
        book_id = str(book_id)
        if book_id in self.cart:
            self.cart[book_id] -= 1

            if self.cart[book_id] <= 0:
                self.cart.pop(book_id, None)
                
            self.save()

    def remove_from_cart(self,book_id):
        book_id = str(book_id)
        if book_id in self.cart:
            self.cart.pop(book_id, None)
            self.save()

    def save(self):
        self.session.modified = True

    def clear_cart(self):
        if 'cart' in self.session:
            del self.session['cart']
            self.save()

    def get_cart_data(self):
        book_ids = self.cart.keys()

        books = Book.objects.filter(id__in=book_ids)
        cart_items = []
        total_price = Decimal(0.00)

        for book in books:
            quantity = self.cart[str(book.id)]
            books_price = book.price * quantity
            total_price += books_price

            cart_items.append({
                'book' : book,
                'quantity': quantity,
                'books_price': books_price,
            })
                
        return {
            'cart_items': cart_items,
            'cart_price': total_price,
        }
    
    @property
    def total_quantity(self):
        return sum(quantity for quantity in self.cart.values() if quantity > 0)
```

**`basket/context_processors.py`** — did not exist.

### AI Recommendations

**Round 1:**

| # | Finding | Severity | Recommendation |
|---|---------|----------|-----------------|
| 1 | **Race condition / stock oversell (TOCTOU):** `SubmitCartView.post` checks `book.stock < item['quantity']` and *then*, separately, deducts stock and saves. No DB-level lock between the two steps — two concurrent checkouts for the same low-stock book can both pass the check and both deduct, overselling. | **High** | Wrap in `transaction.atomic()`, lock the relevant `Book` rows with `select_for_update()` immediately before the check-and-deduct step. |
| 2 | No atomicity across order creation — a failure mid-loop (after `Order.objects.create()` but before all `OrderItem`s exist) leaves a broken order and partial stock deduction. | **High** | Wrap order creation, stock deduction, and item creation in one `transaction.atomic()` block. |
| 3 | Three separate loops over `cart_data['cart_items']` where two could merge. | Low | Merge as a natural side effect of the fix above. |

**Round 2 (bug report: "cart shows quantity 1 for a deleted book"):**

| # | Finding | Severity | Recommendation |
|---|---------|----------|-----------------|
| 4 | `SessionCart` never validates that a book referenced in the session cart still exists in the DB. Deleting a `Book` leaves a stale `{book_id: quantity}` entry in every session that had it, forever. | **High (data integrity / UX bug)** | Add a `_remove_deleted_books()` cleanup step run on every `SessionCart.__init__`, which drops any cart entries whose book no longer exists and persists the change back to the session. |
| 5 | The navbar cart badge in `base.html` bypassed `SessionCart` entirely, reading the raw session dict directly (`request.session.cart|length`) — so even after fixing `SessionCart`, the badge specifically would still show stale/incorrect counts, and separately, `|length` counts *distinct books*, not total quantity, which was already inconsistent with `SessionCart.total_quantity` used elsewhere (e.g. `AddToCartView`'s JSON response). | **Medium** | Add `basket.context_processors.cart_count`, registered in `settings.py`, so every page gets an accurate, self-cleaned, consistently-defined (`total_quantity`) cart count — replacing both the raw session read in `base.html` and the manually duplicated `cart_count = len(cart)` computations in `books/views.py` and `categories/views.py`. |
| 6 | Adding a DB query to a context processor (which runs on every template render) broke the `async def` views in `books`/`categories`, which called `render()` synchronously and directly. | **High (regression introduced by fix #4/#5, caught via manual browser testing, not by `pytest`)** | See `books`/`categories` sections — fixed by wrapping `render()` in `sync_to_async`. |

### Validity Check
- **Findings #1–#2 confirmed and fixed** — this is a textbook TOCTOU bug for e-commerce stock management; no locking existed anywhere in the original `SubmitCartView`.
- **Finding #3 accepted as a side effect**, not the primary motivation.
- **Finding #4 confirmed via direct reproduction**: added a book to cart, deleted it via `/admin/`, reloaded — count stayed at `1` instead of dropping to `0`. Root-caused to `SessionCart` never checking book existence. **Fixed.**
- **Finding #5 confirmed** — `base.html`'s badge used `request.session.cart|length` directly, independent of any `SessionCart` logic, so it needed its own fix. Chose a context processor over passing `cart_count` from every individual view, since `base.html` is extended by essentially every page in the project (including ones like `book_create`/`payments` that don't currently compute a cart count at all) — a context processor guarantees correctness everywhere with one source of truth, and eliminates the duplicated `len(cart)` logic that existed in 4 different view functions.
- **Finding #6 confirmed via a real stack trace** from the user's dev server:
  ```
  django.core.exceptions.SynchronousOnlyOperation: You cannot call this from an async context
  ...books/views.py", line 53, in books_view
    return render(request, 'books/books.html', context)
  ...basket/context_processors.py", line 16, in cart_count
    cart = SessionCart(request)
  ```
  This is a direct causal chain from the Round 2 fix (#5) — flagged and fixed immediately since it was a regression that made the catalog page 500 entirely, worse than the bug it was fixing.

### Final Code

**`basket/services.py`**
```python
from django.http import JsonResponse

from books.models import Book
from decimal import Decimal


class SessionCart:
    def __init__(self,request):
        self.session = request.session
        cart = self.session.get('cart')

        if not cart:
            cart = self.session['cart'] = {}

        self.cart = cart
        self._remove_deleted_books()

    def _remove_deleted_books(self):
        """
        Drop cart entries for books that no longer exist in the database
        (e.g. deleted by an admin) so counts/badges never reference
        phantom items that were removed from the catalog.
        """
        if not self.cart:
            return

        existing_ids = set(
            str(book_id) for book_id in
            Book.objects.filter(id__in=self.cart.keys()).values_list('id', flat=True)
        )
        stale_ids = [book_id for book_id in self.cart if book_id not in existing_ids]

        if stale_ids:
            for book_id in stale_ids:
                self.cart.pop(book_id, None)
            self.save()

    def add_to_cart(self,book_id,quantity=1):
        book_id = str(book_id)

        try:
            book = Book.objects.get(id=book_id)
        except Book.DoesNotExist:
            return False
        
        current_quantity = self.cart.get(book_id,0)
        target_quantity = current_quantity + int(quantity)
        
        if target_quantity > book.stock:
            if book.stock > 0:
                self.cart[book_id] = book.stock
            else:
                self.cart.pop(book_id, None)

            self.save()
            return False 
        
        self.cart[book_id] = target_quantity
        self.save()
        return True

    def remove_one_from_cart(self,book_id):
        book_id = str(book_id)
        if book_id in self.cart:
            self.cart[book_id] -= 1

            if self.cart[book_id] <= 0:
                self.cart.pop(book_id, None)
                
            self.save()

    def remove_from_cart(self,book_id):
        book_id = str(book_id)
        if book_id in self.cart:
            self.cart.pop(book_id, None)
            self.save()

    def save(self):
        self.session.modified = True

    def clear_cart(self):
        if 'cart' in self.session:
            del self.session['cart']
            self.save()

    def get_cart_data(self):
        book_ids = self.cart.keys()

        books = Book.objects.filter(id__in=book_ids)
        cart_items = []
        total_price = Decimal(0.00)

        for book in books:
            quantity = self.cart[str(book.id)]
            books_price = book.price * quantity
            total_price += books_price

            cart_items.append({
                'book' : book,
                'quantity': quantity,
                'books_price': books_price,
            })
                
        return {
            'cart_items': cart_items,
            'cart_price': total_price,
        }
    
    @property
    def total_quantity(self):
        return sum(quantity for quantity in self.cart.values() if quantity > 0)
```

**`basket/context_processors.py` (new)**
```python
from .services import SessionCart


def cart_count(request):
    """
    Makes an accurate, self-cleaning cart item count available to every
    template via {{ cart_count }} — used by the navbar cart badge in
    base.html. Runs SessionCart's cleanup on every request, so a book
    deleted from the catalog stops being counted immediately, on the
    very next page load, instead of only after a cart-related view
    happens to be visited.
    """
    if not hasattr(request, 'session'):
        return {'cart_count': 0}

    cart = SessionCart(request)
    return {'cart_count': cart.total_quantity}
```

**Also required — `bookshop/settings.py`** (one line added to `TEMPLATES`):
```python
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'basket.context_processors.cart_count',
            ],
        },
    },
]
```

**Also required — `templates/base.html`** (navbar badge):
```django
<a href="{% url 'cart_detail' %}" class="btn btn-outline-light btn-sm position-relative">
    🛒 {% translate "Кошик" %}
    {% if cart_count > 0 %}
        <span id="header-cart-count" class="position-absolute top-0 start-100 translate-middle badge rounded-pill bg-danger">
            {{ cart_count }}
        </span>
    {% endif %}
</a>
```

**`basket/views.py`**
```python
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views import View
from books.models import Book
from order.models import Order, OrderItem
from .services import SessionCart
from django.contrib import messages
from silk.profiling.profiler import silk_profile
from django.contrib.auth.mixins import LoginRequiredMixin
import logging


logger = logging.getLogger('order_logger')


class AddToCartView(View):
    def post(self, request, book_id):
        cart = SessionCart(request)

        try:
            quantity = int(request.POST.get('quantity', 1))
            if quantity <= 0:
                quantity = 1
        except (ValueError, TypeError):
            quantity = 1
        success = cart.add_to_cart(book_id, quantity=quantity)

        if not success:
            return JsonResponse({
                'status': 'error',
                'message': 'Вибачте, більше цієї книги немає на складі!'
            })

        return JsonResponse({
            'status': 'success',
            'message': 'Книгу додано до кошика!',
            'cart_count': cart.total_quantity
        })


class DeleteBookFromCartView(View):
    def post(self, request, book_id):
        cart = SessionCart(request)
        cart.remove_from_cart(book_id)
        return JsonResponse({'status': 'success', 'message': 'Книгу видалено!'})


class DeleteOneBookFromCartView(View):
    def post(self, request, book_id):
        cart = SessionCart(request)
        cart.remove_one_from_cart(book_id)
        return JsonResponse({'status': 'success'})


class GetCartData(View):
    def get(self, request):
        cart = SessionCart(request)
        cart_data = cart.get_cart_data()
        cart_data['cart_count'] = cart.total_quantity
        return render(request, 'basket/basket_detail.html', context=cart_data)


class SubmitCartView(LoginRequiredMixin, View):

    @silk_profile(name='Оформлення замовлення (Submit Cart)')
    def post(self, request):
        cart = SessionCart(request)
        cart_data = cart.get_cart_data()

        if not cart_data['cart_items']:
            messages.error(request, "Ваш кошик порожній! Додайте книги перед оформленням замовлення.")
            return redirect('cart_detail')

        book_ids = [item['book'].id for item in cart_data['cart_items']]
        requested_qty = {item['book'].id: item['quantity'] for item in cart_data['cart_items']}

        with transaction.atomic():
            # Lock the relevant book rows for the duration of the transaction
            # to prevent concurrent checkouts from overselling stock.
            locked_books = {
                book.id: book
                for book in Book.objects.select_for_update().filter(id__in=book_ids)
            }

            for book_id, quantity in requested_qty.items():
                book = locked_books.get(book_id)

                if quantity <= 0:
                    messages.error(request, f"Некоректна кількість для книги '{book.title if book else book_id}'.")
                    return redirect('cart_detail')

                if book is None or book.stock < quantity:
                    title = book.title if book else book_id
                    available = book.stock if book else 0
                    messages.error(
                        request,
                        f"Вибачте, книги '{title}' недостатньо на складі. "
                        f"Доступно всього: {available} шт."
                    )
                    return redirect('cart_detail')

            order = Order.objects.create(
                user=request.user,
                total_price=cart_data['cart_price']
            )

            for book_id, quantity in requested_qty.items():
                book = locked_books[book_id]
                book.stock -= quantity
                book.save()

                OrderItem.objects.create(
                    order=order,
                    book=book,
                    price=book.price,
                    quantity=quantity
                )

        cart.clear_cart()

        logger.info(
            f"УСПІХ: Користувач {order.user.username} (ID: {order.user.id}) створив замовлення №{order.id} "
            f"на суму {order.total_price} грн. Кількість позицій: {len(cart_data['cart_items'])}"
        )

        return redirect('order_detail', pk=order.id)
```

---

## 3. `books/views.py` + `books/forms.py`

### Original Code
```python
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy
from django import forms
from categories.models import Category
from .models import Book
from django.db.models import Q
from django.views.generic.edit import CreateView,DeleteView,UpdateView
from django.forms import CheckboxSelectMultiple
from django.contrib.auth.mixins import PermissionRequiredMixin
from silk.profiling.profiler import silk_profile
import logging
from django.core.paginator import Paginator
from asgiref.sync import sync_to_async
from django.http import Http404
# ---------------------------- Function-Based Views -----------------------------------------

# def get_all_books(request):
#     all_books = Book.objects.prefetch_related('category').all()
#     if not all_books.exists():
#         return render(request, 'books/books.html', {'error': 'Книги відсутні', 'all_books': []})
    
#     return render(request, 'books/books.html',{'books': all_books})

# def get_books_in_stock(request):
#     stock_books = Book.objects.filter(Q(stock__gt=0))
#     if not stock_books.exists():
#         return render(request, 'books/books.html', {'error': 'Книги відсутні', 'stock_books': []})
#     return render(request, 'books/books.html',{'stock_books': stock_books})
    
# def get_book_by_id(request,book_id):
#     book_by_id = get_object_or_404(Book, id=book_id)
    
#     return render(request, 'books/book_detail.html',{'book_by_id': book_by_id})



# ---------------------------- Class-Based Views -----------------------------------------


logger = logging.getLogger('books_list_logger')

class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['title', 'author', 'price', 'description', 'stock', 'category']
        widgets = {
            'category': forms.CheckboxSelectMultiple(),  
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.all()


async def books_view(request):
    queryset = Book.objects.prefetch_related('category').all()

    query = request.GET.get('q')
    if query:
        queryset = queryset.filter(title__icontains=query)

    category_id = request.GET.get('cat')
    if category_id:
        queryset = queryset.filter(category__id=category_id)
               
    book_list = [] 
    async for book in queryset:
        book_list.append(book)
    
    all_categories = []
    async for category in Category.objects.all():
        all_categories.append(category)

    paginator = Paginator(book_list, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    def get_user_data():
        return {
            'cart': request.session.get('cart', {}),
            'can_add_book': request.user.has_perm('books.add_book') 
        }
    user_data = await sync_to_async(get_user_data)()
    cart_count = len(user_data['cart'])

    context = {
        'books': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'all_categories': all_categories,
        'cart_count': cart_count,
        'can_add_book': user_data['can_add_book'],
    }

    return render(request, 'books/books.html', context)
   

async def one_book_view(request,pk):
    queryset = Book.objects.prefetch_related('category')

    try:
        book = await queryset.aget(id=pk)
    except Book.DoesNotExist:
        raise Http404('Book does not exist')
    
    def get_user_data():
        return{
            'cart': request.session.get('cart',{}),
            'can_edit_book': request.user.has_perm('books.edit_book') ,
            'can_delete_book': request.user.has_perm('books.delete_book') 
        }
    
    user_data = await sync_to_async(get_user_data)()
    cart_count = len(user_data['cart'])

    context = {
        'book': book,
        'cart_count': cart_count,
        'can_edit_book': user_data['can_edit_book'],
        'can_delete_book': user_data['can_delete_book'],
    }

    return render(request, 'books/book_detail.html', context)


class CreateBookView(PermissionRequiredMixin,CreateView):
    model = Book
    form_class = BookForm
    template_name = 'books/book_create_form.html'
    success_url = reverse_lazy('books_list')

    permission_required = 'books.add_book'

class DeleteBookView(PermissionRequiredMixin,DeleteView):
    model = Book
    template_name = 'books/book_delete.html'
    success_url = reverse_lazy('books_list')

    permission_required = 'books.delete_book'

class UpdateBookView(PermissionRequiredMixin,UpdateView):
    model = Book
    form_class = BookForm
    template_name = 'books/book_update_form.html'
    success_url = reverse_lazy('books_list')

    permission_required = 'books.update_book'
```

`books/forms.py` did not exist — `BookForm` lived inside `views.py`.

### AI Recommendations

**Round 1:**

| # | Finding | Severity | Recommendation |
|---|---------|----------|-----------------|
| 1 | `one_book_view` checks `request.user.has_perm('books.edit_book')`, but `UpdateBookView.permission_required = 'books.update_book'`. `edit_book` isn't a real codename. | **High (bug)** | Change to `'books.update_book'`, matching `books.html`'s correct `perms.books.update_book` check. |
| 2 | `category_id = request.GET.get('cat')` passed directly into `.filter(category__id=category_id)` with no validation — a non-numeric `?cat=abc` raises an unhandled `ValueError` → 500. | **Medium** | Guard with `.isdigit()` before filtering; silently ignore invalid values instead of crashing. |
| 3 | `BookForm` defined inside `views.py` instead of its own `forms.py`, unlike `user/forms.py`. | Low | Extract to `books/forms.py`. |
| 4 | Dead `logger`, unused imports (`Q`, `CheckboxSelectMultiple` direct import, `get_object_or_404`), large commented-out legacy view block. | Low | Remove. |

**Round 2:**

| # | Finding | Severity | Recommendation |
|---|---------|----------|-----------------|
| 5 | Manual `cart_count = len(user_data['cart'])` in both `books_view` and `one_book_view` — same root issue diagnosed in the `basket` section (stale/inconsistent counts, and it shadows the new global context processor if left in place). | Medium | Remove; rely on `basket.context_processors.cart_count`. |
| 6 | Removing the manual cart handling didn't itself break anything, but the *new* context processor's DB query crashed these `async def` views (`SynchronousOnlyOperation`), since `render()` was called directly. | **High (regression)** | Wrap in `sync_to_async(render)(...)`. |

### Validity Check
- **Finding #1 confirmed** — same bug class as the `categories` app, verified against `book_detail.html`'s `can_edit_book` usage.
- **Finding #2 confirmed** — no validation existed; accepted and fixed with an `.isdigit()` guard rather than a full `try/except`, since query params are always strings and this is simpler/equally safe.
- **Finding #3 accepted** — `books/forms.py` created, `views.py` updated to `from .forms import BookForm`. **Important side effect:** `books/tests.py` imported `BookForm` from `books.views` (`from books.views import BookForm`) — this import needed manual updating to `from books.forms import BookForm` after the move, or the test suite would fail with an `ImportError`. Flagged directly to the developer since it's outside the reviewed file itself.
- **Finding #4 accepted** — cleanup, no behavior change.
- **Finding #5 confirmed and fixed**, consistent with the `categories` decision.
- **Finding #6 confirmed via the same stack trace as the `categories` app** (see `basket` section above) — fixed identically.

### Final Code

**`books/forms.py` (new file)**
```python
from django import forms
from categories.models import Category
from .models import Book


class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['title', 'author', 'price', 'description', 'stock', 'category']
        widgets = {
            'category': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.all()
```

**`books/views.py`**
```python
from django.shortcuts import render
from django.urls import reverse_lazy
from categories.models import Category
from .models import Book
from .forms import BookForm
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.paginator import Paginator
from asgiref.sync import sync_to_async
from django.http import Http404


async def books_view(request):
    queryset = Book.objects.prefetch_related('category').all()

    query = request.GET.get('q')
    if query:
        queryset = queryset.filter(title__icontains=query)

    category_id = request.GET.get('cat')
    if category_id:
        if category_id.isdigit():
            queryset = queryset.filter(category__id=category_id)
        # Non-numeric / invalid 'cat' values are silently ignored
        # rather than raising a 500 error.

    book_list = []
    async for book in queryset:
        book_list.append(book)

    all_categories = []
    async for category in Category.objects.all():
        all_categories.append(category)

    paginator = Paginator(book_list, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    def get_user_data():
        return {
            'can_add_book': request.user.has_perm('books.add_book')
        }
    user_data = await sync_to_async(get_user_data)()

    context = {
        'books': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'all_categories': all_categories,
        'can_add_book': user_data['can_add_book'],
    }

    # render() is wrapped in sync_to_async because template rendering
    # triggers context processors (e.g. basket.context_processors.cart_count)
    # that hit the database — calling that directly from this async view
    # would raise SynchronousOnlyOperation.
    return await sync_to_async(render)(request, 'books/books.html', context)


async def one_book_view(request, pk):
    queryset = Book.objects.prefetch_related('category')

    try:
        book = await queryset.aget(id=pk)
    except Book.DoesNotExist:
        raise Http404('Book does not exist')

    def get_user_data():
        return {
            'can_edit_book': request.user.has_perm('books.update_book'),
            'can_delete_book': request.user.has_perm('books.delete_book')
        }

    user_data = await sync_to_async(get_user_data)()

    context = {
        'book': book,
        'can_edit_book': user_data['can_edit_book'],
        'can_delete_book': user_data['can_delete_book'],
    }

    return await sync_to_async(render)(request, 'books/book_detail.html', context)


class CreateBookView(PermissionRequiredMixin, CreateView):
    model = Book
    form_class = BookForm
    template_name = 'books/book_create_form.html'
    success_url = reverse_lazy('books_list')

    permission_required = 'books.add_book'


class DeleteBookView(PermissionRequiredMixin, DeleteView):
    model = Book
    template_name = 'books/book_delete.html'
    success_url = reverse_lazy('books_list')

    permission_required = 'books.delete_book'


class UpdateBookView(PermissionRequiredMixin, UpdateView):
    model = Book
    form_class = BookForm
    template_name = 'books/book_update_form.html'
    success_url = reverse_lazy('books_list')

    permission_required = 'books.update_book'
```

---

## Summary

| App | Round 1 fixes | Round 2 fixes (triggered by real bug report) |
|---|---|---|
| `categories` | Wrong permission namespace (`all_categories.*` → `categories.*`); dead imports/code removed | Removed duplicated `cart_count` logic; wrapped `render()` in `sync_to_async` to fix a crash caused by the new cart context processor |
| `basket` | Stock-oversell race condition fixed with `transaction.atomic()` + `select_for_update()` | `SessionCart` now self-cleans stale entries for deleted books; new global `cart_count` context processor (+ `settings.py` and `base.html` updates) replaces the raw/inconsistent session reads |
| `books` | Wrong permission codename (`books.edit_book` → `books.update_book`); unguarded `cat` query param could 500; `BookForm` extracted to `forms.py` | Removed duplicated `cart_count` logic; wrapped `render()` in `sync_to_async` (same crash/fix as `categories`) |

**Root-cause note on the Round 2 chain:** the original "cart shows 1 for a deleted book" bug, its fix, and the subsequent `SynchronousOnlyOperation` crash are a good illustration of why manual/browser verification matters alongside `pytest` — the async/sync crash was **not** caught by the automated test suite (the async view tests don't populate a session cart with a since-deleted book, so the DB-touching context processor's failure mode never got exercised), but was caught within minutes of manual testing in a real browser. This gap is called out again in `README.md`'s Testing section as a recommended area for new regression tests.

**Note on tests:** existing tests (`categories/tests.py`, `basket/tests.py`, `books/tests.py`, `order/tests.py`) don't assert on the `can_add`/`can_edit`/`can_delete` context flags, on concurrent-checkout behavior, or on the deleted-book cart cleanup. Recommended follow-ups:
- A permission test asserting a superuser sees `can_add`/`can_edit`/`can_delete = True` on the categories/books list views.
- A concurrency test (two threads/requests submitting the same low-stock book) to guard the `basket` race-condition fix.
- A regression test: add a book to the cart, delete the book, assert the cart page and `cart_count` both reflect `0` — this is the scenario that shipped as a real bug and should never be able to silently regress again.

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
    if not hasattr(request, "session"):
        return {"cart_count": 0}

    cart = SessionCart(request)
    return {"cart_count": cart.total_quantity}

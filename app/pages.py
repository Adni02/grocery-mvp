"""Page routes for server-rendered templates."""

from pathlib import Path
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.dependencies import CurrentUser, CurrentUserOptional, DbSession
from app.services.address_service import AddressService
from app.services.cart_service import CartService
from app.services.order_service import OrderService
from app.services.product_service import ProductService

# Set up templates
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Add custom template globals
templates.env.globals["app_name"] = settings.app_name
templates.env.globals["currency"] = settings.currency

router = APIRouter()


def get_base_context(request: Request, user: Optional[object] = None) -> dict:
    """Get base context for all templates."""
    return {
        "request": request,
        "user": user,
        "app_name": settings.app_name,
        "currency": settings.currency,
    }


# ============================================================================
# Home Page
# ============================================================================


@router.get("/", response_class=HTMLResponse)
async def home(
    request: Request,
    db: DbSession,
    user: CurrentUserOptional,
):
    """Home page with featured products and categories."""
    product_service = ProductService(db)

    # Get featured products
    featured_products, _ = await product_service.list_products(
        page=1,
        limit=8,
        is_featured=True,
    )

    # Get categories
    categories = await product_service.list_categories()

    context = get_base_context(request, user)
    context.update({
        "featured_products": featured_products,
        "categories": categories,
    })

    return templates.TemplateResponse("home.html", context)


# ============================================================================
# Product Pages
# ============================================================================


@router.get("/products", response_class=HTMLResponse)
async def products_list(
    request: Request,
    db: DbSession,
    user: CurrentUserOptional,
    page: int = 1,
    category: Optional[str] = None,
    q: Optional[str] = None,
):
    """Product listing page with filters."""
    product_service = ProductService(db)

    products, total = await product_service.list_products(
        page=page,
        limit=20,
        category_slug=category,
        search=q,
    )

    categories = await product_service.list_categories()
    current_category = None
    if category:
        current_category = await product_service.get_category_by_slug(category)

    context = get_base_context(request, user)
    context.update({
        "products": products,
        "total": total,
        "page": page,
        "pages": product_service.calculate_pages(total, 20),
        "categories": categories,
        "current_category": current_category,
        "search_query": q,
    })

    return templates.TemplateResponse("products/list.html", context)


@router.get("/products/{slug}", response_class=HTMLResponse)
async def product_detail(
    slug: str,
    request: Request,
    db: DbSession,
    user: CurrentUserOptional,
):
    """Single product detail page."""
    product_service = ProductService(db)
    product = await product_service.get_product_by_slug(slug)

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    context = get_base_context(request, user)
    context["product"] = product

    return templates.TemplateResponse("products/detail.html", context)


# ============================================================================
# Cart & Checkout
# ============================================================================


@router.get("/cart", response_class=HTMLResponse)
async def cart_page(
    request: Request,
    db: DbSession,
    user: CurrentUserOptional,
):
    """Shopping cart page."""
    cart_response = None
    if user:
        cart_service = CartService(db)
        cart_response = await cart_service.get_cart_response(user.id)

    context = get_base_context(request, user)
    context["cart"] = cart_response
    context["delivery_fee"] = settings.delivery_fee

    return templates.TemplateResponse("cart.html", context)


@router.get("/checkout", response_class=HTMLResponse)
async def checkout_page(
    request: Request,
    db: DbSession,
    user: CurrentUser,
):
    """Checkout page - requires authentication."""
    cart_service = CartService(db)
    cart_response = await cart_service.get_cart_response(user.id)

    if not cart_response.items:
        return RedirectResponse("/cart", status_code=302)

    address_service = AddressService(db)
    addresses = await address_service.get_user_addresses(user.id)

    # Filter to only verified addresses
    verified_addresses = [a for a in addresses if a.is_verified]

    context = get_base_context(request, user)
    context.update({
        "cart": cart_response,
        "addresses": verified_addresses,
        "delivery_fee": settings.delivery_fee,
        "total": cart_response.subtotal + settings.delivery_fee,
    })

    return templates.TemplateResponse("checkout.html", context)


# ============================================================================
# Orders
# ============================================================================


@router.get("/orders", response_class=HTMLResponse)
async def orders_list(
    request: Request,
    db: DbSession,
    user: CurrentUser,
    page: int = 1,
):
    """Order history page."""
    order_service = OrderService(db)
    orders, total = await order_service.list_orders(user.id, page=page, limit=20)

    context = get_base_context(request, user)
    context.update({
        "orders": orders,
        "total": total,
        "page": page,
    })

    return templates.TemplateResponse("orders/list.html", context)


@router.get("/orders/{order_id}", response_class=HTMLResponse)
async def order_detail(
    order_id: UUID,
    request: Request,
    db: DbSession,
    user: CurrentUser,
):
    """Order detail page."""
    order_service = OrderService(db)
    order = await order_service.get_order(order_id, user.id)

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    context = get_base_context(request, user)
    context["order"] = order

    return templates.TemplateResponse("orders/detail.html", context)


# ============================================================================
# Profile & Addresses
# ============================================================================


@router.get("/profile", response_class=HTMLResponse)
async def profile_page(
    request: Request,
    db: DbSession,
    user: CurrentUser,
):
    """User profile page."""
    address_service = AddressService(db)
    addresses = await address_service.get_user_addresses(user.id)

    context = get_base_context(request, user)
    context["addresses"] = addresses

    return templates.TemplateResponse("profile/index.html", context)


@router.get("/profile/addresses/new", response_class=HTMLResponse)
async def new_address_page(
    request: Request,
    user: CurrentUser,
):
    """Add new address page."""
    context = get_base_context(request, user)
    return templates.TemplateResponse("profile/address_form.html", context)


# ============================================================================
# Authentication
# ============================================================================


@router.get("/login", response_class=HTMLResponse)
async def login_page(
    request: Request,
    user: CurrentUserOptional,
    redirect: Optional[str] = None,
):
    """Login page with Firebase Auth."""
    if user:
        return RedirectResponse(redirect or "/", status_code=302)

    context = get_base_context(request, user)
    context["redirect_url"] = redirect or "/"

    return templates.TemplateResponse("auth/login.html", context)


# Create the page router
page_router = router

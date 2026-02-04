"""Order API routes."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy.orm import selectinload

from app.dependencies import CurrentUser, DbSession
from app.schemas.order import (
    OrderCreate,
    OrderListItem,
    OrderListResponse,
    OrderResponse,
)
from app.services.invoice_service import InvoiceService
from app.services.order_service import OrderService

router = APIRouter()


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    data: OrderCreate,
    db: DbSession,
    user: CurrentUser,
):
    """
    Create a new order (checkout).

    Requirements:
    - User must have items in their cart
    - User must have a verified address
    - Selected address must belong to the user and be verified

    On success:
    - Order is created with status PLACED
    - Cart is cleared
    - Invoice number is generated
    """
    order_service = OrderService(db)

    try:
        order = await order_service.create_order(user.id, data)
        return OrderResponse.model_validate(order)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("", response_model=OrderListResponse)
async def list_orders(
    db: DbSession,
    user: CurrentUser,
    page: int = 1,
    limit: int = 20,
):
    """
    List the current user's orders with pagination.
    """
    if page < 1:
        page = 1
    if limit < 1 or limit > 50:
        limit = 20

    order_service = OrderService(db)
    orders, total = await order_service.list_orders(user.id, page, limit)

    items = []
    for order in orders:
        items.append(
            OrderListItem(
                id=order.id,
                invoice_number=order.invoice_number,
                status=order.status,
                total=order.total,
                item_count=sum(item.quantity for item in order.items),
                created_at=order.created_at,
            )
        )

    return OrderListResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
    )


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: UUID,
    db: DbSession,
    user: CurrentUser,
):
    """
    Get details of a specific order.
    """
    order_service = OrderService(db)
    order = await order_service.get_order(order_id, user.id)

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    return OrderResponse.model_validate(order)


@router.get("/{order_id}/invoice")
async def get_invoice(
    order_id: UUID,
    db: DbSession,
    user: CurrentUser,
):
    """
    Download the invoice PDF for an order.
    """
    order_service = OrderService(db)
    order = await order_service.get_order(order_id, user.id)

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    invoice_service = InvoiceService(db)
    pdf_bytes = await invoice_service.generate_invoice_pdf(order)

    if pdf_bytes:
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=invoice-{order.invoice_number}.pdf"
            },
        )

    # Fallback to HTML if PDF generation fails
    html_content = invoice_service._generate_invoice_html(order)
    return Response(
        content=html_content,
        media_type="text/html",
    )

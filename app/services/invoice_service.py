"""Invoice generation service."""

import io
import logging
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.order import Invoice, Order

logger = logging.getLogger(__name__)


class InvoiceService:
    """Service for invoice generation and management."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.invoices_dir = Path("invoices")

    async def get_invoice(self, order_id: UUID) -> Optional[Invoice]:
        """Get invoice for an order."""
        stmt = select(Invoice).where(Invoice.order_id == order_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def generate_invoice_pdf(self, order: Order) -> Optional[bytes]:
        """Generate a PDF invoice for an order."""
        try:
            from weasyprint import HTML

            html_content = self._generate_invoice_html(order)
            pdf_bytes = HTML(string=html_content).write_pdf()
            return pdf_bytes
        except ImportError:
            logger.warning("WeasyPrint not available, falling back to HTML invoice")
            return None
        except Exception as e:
            logger.error(f"Failed to generate PDF invoice: {e}")
            return None

    def _generate_invoice_html(self, order: Order) -> str:
        """Generate HTML content for invoice."""
        address = order.address_snapshot

        # Format address
        address_lines = [address.get("street", "")]
        if address.get("building"):
            address_lines[0] += f" {address['building']}"
        if address.get("floor"):
            address_lines.append(f"Floor: {address['floor']}")
        if address.get("apartment"):
            address_lines.append(f"Apt: {address['apartment']}")
        address_lines.append(f"{address.get('postcode', '')} {address.get('city', '')}")

        # Format items
        items_html = ""
        for item in order.items:
            product_name = item.product_snapshot.get("name", "Unknown Product")
            items_html += f"""
            <tr>
                <td>{product_name}</td>
                <td class="center">{item.quantity}</td>
                <td class="right">{item.price_at_purchase:.2f} {settings.currency}</td>
                <td class="right">{item.line_total:.2f} {settings.currency}</td>
            </tr>
            """

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Invoice {order.invoice_number}</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    font-size: 12px;
                    line-height: 1.4;
                    color: #333;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    border-bottom: 2px solid #333;
                    padding-bottom: 20px;
                    margin-bottom: 20px;
                }}
                .company-name {{
                    font-size: 24px;
                    font-weight: bold;
                    color: #2c5530;
                }}
                .invoice-title {{
                    font-size: 20px;
                    margin-top: 10px;
                }}
                .invoice-meta {{
                    margin-top: 10px;
                }}
                .addresses {{
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 30px;
                }}
                .address-block {{
                    width: 45%;
                }}
                .address-block h3 {{
                    margin-bottom: 10px;
                    color: #666;
                    font-size: 12px;
                    text-transform: uppercase;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 20px;
                }}
                th {{
                    background-color: #f5f5f5;
                    padding: 10px;
                    text-align: left;
                    border-bottom: 2px solid #ddd;
                }}
                td {{
                    padding: 10px;
                    border-bottom: 1px solid #eee;
                }}
                .right {{ text-align: right; }}
                .center {{ text-align: center; }}
                .totals {{
                    margin-top: 20px;
                    text-align: right;
                }}
                .totals table {{
                    width: 300px;
                    margin-left: auto;
                }}
                .totals td {{
                    padding: 5px 10px;
                }}
                .total-row {{
                    font-weight: bold;
                    font-size: 14px;
                    border-top: 2px solid #333;
                }}
                .footer {{
                    margin-top: 40px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                    text-align: center;
                    color: #666;
                    font-size: 10px;
                }}
                .payment-info {{
                    background-color: #f9f9f9;
                    padding: 15px;
                    margin-top: 30px;
                    border-radius: 5px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <div class="company-name">{settings.app_name}</div>
                <div class="invoice-title">INVOICE</div>
                <div class="invoice-meta">
                    <strong>Invoice Number:</strong> {order.invoice_number}<br>
                    <strong>Date:</strong> {order.created_at.strftime('%d %B %Y')}<br>
                    <strong>Order ID:</strong> {str(order.id)[:8]}...
                </div>
            </div>

            <div class="addresses">
                <div class="address-block">
                    <h3>Delivery Address</h3>
                    {'<br>'.join(address_lines)}
                </div>
                <div class="address-block">
                    <h3>Payment Method</h3>
                    Cash on Delivery (COD)
                </div>
            </div>

            <table>
                <thead>
                    <tr>
                        <th>Product</th>
                        <th class="center">Qty</th>
                        <th class="right">Unit Price</th>
                        <th class="right">Total</th>
                    </tr>
                </thead>
                <tbody>
                    {items_html}
                </tbody>
            </table>

            <div class="totals">
                <table>
                    <tr>
                        <td>Subtotal:</td>
                        <td class="right">{order.subtotal:.2f} {settings.currency}</td>
                    </tr>
                    <tr>
                        <td>Delivery Fee:</td>
                        <td class="right">{order.delivery_fee:.2f} {settings.currency}</td>
                    </tr>
                    <tr class="total-row">
                        <td>Total:</td>
                        <td class="right">{order.total:.2f} {settings.currency}</td>
                    </tr>
                </table>
            </div>

            <div class="payment-info">
                <strong>Payment Instructions:</strong><br>
                Please have the exact amount of <strong>{order.total:.2f} {settings.currency}</strong> ready for the delivery person.
            </div>

            <div class="footer">
                Thank you for your order!<br>
                {settings.app_name} | {settings.app_url}
            </div>
        </body>
        </html>
        """

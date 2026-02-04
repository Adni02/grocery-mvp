"""
Tests for product API endpoints.
"""
import pytest
from httpx import AsyncClient


class TestProductAPI:
    """Test product endpoints."""
    
    @pytest.mark.asyncio
    async def test_list_products(self, client: AsyncClient, sample_product):
        """Test listing products."""
        response = await client.get("/api/products")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert len(data["items"]) >= 1
    
    @pytest.mark.asyncio
    async def test_get_product_by_slug(self, client: AsyncClient, sample_product):
        """Test getting product by slug."""
        response = await client.get(f"/api/products/{sample_product.slug}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["slug"] == sample_product.slug
        assert data["name"] == sample_product.name
    
    @pytest.mark.asyncio
    async def test_get_product_not_found(self, client: AsyncClient):
        """Test getting non-existent product."""
        response = await client.get("/api/products/non-existent-slug")
        
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_list_categories(self, client: AsyncClient, sample_category):
        """Test listing categories."""
        response = await client.get("/api/categories")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
    
    @pytest.mark.asyncio
    async def test_filter_products_by_category(
        self, client: AsyncClient, sample_product, sample_category
    ):
        """Test filtering products by category."""
        response = await client.get(
            "/api/products",
            params={"category_slug": sample_category.slug}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1
        for item in data["items"]:
            assert item["category"]["slug"] == sample_category.slug


class TestAddressAPI:
    """Test address endpoints."""
    
    @pytest.mark.asyncio
    async def test_verify_serviceable_postcode(
        self, client: AsyncClient, sample_postcode
    ):
        """Test verifying a serviceable postcode."""
        response = await client.post(
            "/api/addresses/verify-postcode",
            json={"postcode": sample_postcode.postcode}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["serviceable"] is True
        assert data["city"] == sample_postcode.city
    
    @pytest.mark.asyncio
    async def test_verify_non_serviceable_postcode(self, client: AsyncClient):
        """Test verifying a non-serviceable postcode."""
        response = await client.post(
            "/api/addresses/verify-postcode",
            json={"postcode": "9999"}  # Non-existent postcode
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["serviceable"] is False


class TestCartAPI:
    """Test cart endpoints."""
    
    @pytest.mark.asyncio
    async def test_get_empty_cart(self, client: AsyncClient):
        """Test getting an empty cart."""
        response = await client.get("/api/cart")
        
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["item_count"] == 0
        assert float(data["subtotal"]) == 0
    
    @pytest.mark.asyncio
    async def test_add_item_to_cart(self, client: AsyncClient, sample_product):
        """Test adding item to cart."""
        response = await client.post(
            "/api/cart/items",
            json={
                "product_id": str(sample_product.id),
                "quantity": 2
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["item_count"] == 2
        assert len(data["items"]) == 1
        assert data["items"][0]["quantity"] == 2


class TestAdminAPI:
    """Test admin endpoints."""
    
    @pytest.mark.asyncio
    async def test_admin_create_product(
        self, client: AsyncClient, admin_headers, sample_category
    ):
        """Test creating product via admin API."""
        response = await client.post(
            "/api/admin/products",
            headers=admin_headers,
            json={
                "name": "Admin Test Product",
                "slug": "admin-test-product",
                "price": 49.99,
                "unit": "stk",
                "category_id": str(sample_category.id),
                "stock_quantity": 50,
                "is_active": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Admin Test Product"
        assert float(data["price"]) == 49.99
    
    @pytest.mark.asyncio
    async def test_admin_without_api_key(self, client: AsyncClient):
        """Test admin endpoint without API key."""
        response = await client.get("/api/admin/orders")
        
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_admin_with_invalid_api_key(self, client: AsyncClient):
        """Test admin endpoint with invalid API key."""
        response = await client.get(
            "/api/admin/orders",
            headers={"X-Admin-API-Key": "invalid-key"}
        )
        
        assert response.status_code == 403

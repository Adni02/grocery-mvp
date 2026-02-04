# TASKS.md - Phase-1 MVP Implementation Checklist

## Project Setup
- [x] Initialize project structure
- [x] Create pyproject.toml with dependencies
- [x] Create Docker Compose configuration
- [x] Create Dockerfile
- [x] Create .env.example
- [x] Create .gitignore

## Database Layer
- [x] Create SQLAlchemy base and mixins
- [x] Create User model
- [x] Create Product model
- [x] Create Category model
- [x] Create Address model
- [x] Create ServicePostcode model
- [x] Create ServiceAddress model
- [x] Create Cart model
- [x] Create CartItem model
- [x] Create Order model
- [x] Create OrderItem model
- [x] Create OrderStatusHistory model
- [x] Create Invoice model
- [x] Configure Alembic
- [x] Create initial migration

## Pydantic Schemas
- [x] Auth schemas (token verification, user response)
- [x] Product schemas (list, detail, create, update)
- [x] Address schemas (create, update, verify postcode)
- [x] Cart schemas (item, cart response)
- [x] Order schemas (create, response, status update)

## Services Layer
- [x] AuthService (Firebase verification, JWT sessions)
- [x] ProductService (CRUD, search, pagination)
- [x] AddressService (CRUD, postcode verification)
- [x] CartService (add, update, remove, sync)
- [x] OrderService (checkout, status updates)
- [x] InvoiceService (HTML/PDF generation)

## API Endpoints
- [x] Auth routes (verify, logout, me)
- [x] Product routes (list, detail, categories)
- [x] Address routes (CRUD, verify postcode)
- [x] Cart routes (get, add, update, remove, sync)
- [x] Order routes (create, list, detail, invoice)
- [x] Admin routes (products, orders, postcodes)

## Frontend Templates
- [x] Base layout template
- [x] Header component
- [x] Footer component
- [x] Cart drawer component
- [x] Product card component
- [x] Status badge component
- [x] Home page
- [x] Product list page
- [x] Product detail page
- [x] Cart page
- [x] Checkout page
- [x] Order list page
- [x] Order detail page
- [x] Profile page
- [x] Address form page
- [x] Login page
- [x] 404 error page
- [x] 500 error page

## Data & Seeds
- [x] Seed script for postcodes
- [x] Seed script for products/categories

## Documentation
- [x] README.md with setup instructions
- [x] TASKS.md checklist

## Testing (TODO)
- [ ] Test configuration (conftest.py)
- [ ] Auth service tests
- [ ] Product service tests
- [ ] Address service tests
- [ ] Cart service tests
- [ ] Order service tests
- [ ] API endpoint tests
- [ ] Integration tests

## Polish & Edge Cases (TODO)
- [ ] Rate limiting on API
- [ ] Request validation error handling
- [ ] Logging configuration
- [ ] Health check endpoint
- [ ] CORS configuration
- [ ] Security headers
- [ ] Input sanitization

## Phase-2 Future Features (Out of Scope)
- [ ] Mobile Money integration
- [ ] Push notifications
- [ ] Delivery slot picker
- [ ] Order rating/reviews
- [ ] Promo codes
- [ ] Inventory management
- [ ] Admin dashboard UI
- [ ] Analytics dashboard

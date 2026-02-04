# Danish Grocery Marketplace MVP

A Phase-1 MVP for an online grocery marketplace targeting Copenhagen, Denmark. Built with FastAPI, Jinja2, Alpine.js, Firebase Auth, and PostgreSQL.

## Features

### Customer Features
- 🔐 Firebase Authentication (Google + Phone OTP)
- 🏠 Address verification with postcode allowlist
- 🛒 Persistent shopping cart (guest & authenticated)
- 📦 Order placement with Cash-on-Delivery
- 📄 PDF invoice generation
- 📱 Mobile-responsive design

### Admin Features (via API)
- Product & category management
- Order status updates
- Service area management

## Tech Stack

- **Backend**: FastAPI (async), SQLAlchemy 2.0, Alembic
- **Frontend**: Jinja2 templates, Tailwind CSS (CDN), Alpine.js (CDN)
- **Auth**: Firebase Admin SDK
- **Database**: PostgreSQL 15
- **PDF**: WeasyPrint
- **Container**: Docker & Docker Compose

## Project Structure

```
grocery-mvp/
├── app/
│   ├── api/              # API endpoints
│   ├── models/           # SQLAlchemy models
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # Business logic
│   ├── templates/        # Jinja2 templates
│   ├── config.py         # Settings
│   ├── database.py       # DB connection
│   ├── dependencies.py   # FastAPI deps
│   ├── main.py          # App factory
│   └── pages.py         # Page routes
├── alembic/             # DB migrations
├── scripts/             # Seed scripts
├── tests/               # Test suite
├── docker-compose.yml
├── Dockerfile
└── pyproject.toml
```

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 15 (or Docker)
- Firebase project (for production auth)

### Development Setup

1. **Clone and setup environment**:
   ```bash
   cd grocery-mvp
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   pip install -e ".[dev]"
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

3. **Start PostgreSQL** (using Docker):
   ```bash
   docker-compose up -d db
   ```

4. **Run migrations**:
   ```bash
   alembic upgrade head
   ```

5. **Seed data**:
   ```bash
   python scripts/seed_postcodes.py
   python scripts/seed_products.py
   ```

6. **Start development server**:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

7. **Open browser**: http://localhost:8000

### Using Docker Compose (Full Stack)

```bash
docker-compose up --build
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `SECRET_KEY` | JWT signing key | Required |
| `ADMIN_API_KEY` | Admin API authentication | Required |
| `FIREBASE_CREDENTIALS_PATH` | Path to Firebase service account JSON | Optional in dev |
| `DEV_MODE` | Enable dev mode (mock auth) | `false` |
| `DEFAULT_DELIVERY_FEE` | Default delivery fee in DKK | `0` |
| `MIN_ORDER_AMOUNT` | Minimum order amount in DKK | `100` |

## API Documentation

Once running, access:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/verify` | Verify Firebase token |
| `GET` | `/api/products` | List products |
| `GET` | `/api/categories` | List categories |
| `POST` | `/api/addresses/verify-postcode` | Check if postcode is serviceable |
| `POST` | `/api/cart/items` | Add item to cart |
| `POST` | `/api/orders` | Create order (checkout) |
| `GET` | `/api/orders/{id}/invoice` | Download invoice PDF |

### Admin Endpoints (requires `X-Admin-API-Key` header)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/admin/products` | Create product |
| `PUT` | `/api/admin/orders/{id}/status` | Update order status |
| `POST` | `/api/admin/postcodes` | Add service postcode |

## Development Mode

Set `DEV_MODE=true` to:
- Skip Firebase token verification
- Use mock tokens: `dev_email:test@example.com` or `dev_phone:+4512345678`

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_orders.py -v
```

## Deployment

### Production Checklist

- [ ] Set `DEV_MODE=false`
- [ ] Configure Firebase credentials
- [ ] Set strong `SECRET_KEY` and `ADMIN_API_KEY`
- [ ] Use managed PostgreSQL (e.g., Supabase, RDS)
- [ ] Configure HTTPS
- [ ] Set up monitoring and logging
- [ ] Configure backups

### Deploy to Cloud Run

```bash
gcloud run deploy grocery-mvp \
  --source . \
  --region europe-north1 \
  --allow-unauthenticated
```

## License

MIT License - See LICENSE file for details.

## Support

For issues and questions, please open a GitHub issue.

# PlayTrade API Documentation

Comprehensive documentation for the PlayTrade REST API.

## Table of Contents

1. [Overview](#overview)
2. [Base URL](#base-url)
3. [Authentication](#authentication)
4. [Interactive Documentation](#interactive-documentation)
5. [API Endpoints](#api-endpoints)
   - [Developers](#developers)
   - [Genres](#genres)
   - [Games](#games)
   - [Reviews](#reviews)
6. [Data Models](#data-models)
7. [Error Handling](#error-handling)
8. [Usage Examples](#usage-examples)
9. [Frontend Components](#frontend-components)
10. [Performance Considerations](#performance-considerations)

---

## Overview

PlayTrade API is a RESTful API built with Django REST Framework (DRF) for managing a digital game marketplace. The API provides endpoints for:

- **Games**: CRUD operations for game listings
- **Developers**: Manage game developers/studios
- **Genres**: Game genre classification
- **Reviews**: User reviews and ratings

### Key Features

- RESTful design principles
- JSON response format
- Auto-generated OpenAPI schema (via drf-spectacular)
- Swagger UI and ReDoc documentation
- Database normalized to 3NF

---

## Base URL

```
http://localhost:8000/api/v1/
```

For production deployments, replace `localhost:8000` with your domain.

---

## Authentication

Currently, the API operates in **public mode** without authentication for read operations. Write operations (POST, PUT, DELETE) should be protected in production environments.

### Recommended Authentication Methods

For production, consider implementing:

```python
# settings.py
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
}
```

---

## Interactive Documentation

### Swagger UI

Access interactive API documentation:

```
GET /api/v1/docs/swagger-ui/
```

### ReDoc

Access alternative documentation format:

```
GET /api/v1/docs/redoc/
```

### OpenAPI Schema

Raw JSON schema:

```
GET /api/v1/docs/
```

---

## API Endpoints

### Developers

Manage game developer information.

#### List All Developers

```http
GET /api/v1/developers/
```

**Response (200 OK):**

```json
[
  {
    "id": 1,
    "name": "Valve Corporation",
    "email": "contact@valvesoftware.com",
    "bio": "American video game developer and publisher based in Bellevue, Washington.",
    "founded_date": "1996-08-24"
  }
]
```

#### Create Developer

```http
POST /api/v1/developers/
Content-Type: application/json

{
  "name": "CD Projekt RED",
  "email": "contact@cdprojektred.com",
  "bio": "Polish video game developer known for The Witcher series.",
  "founded_date": "1994-05-01"
}
```

**Response (201 Created):**

```json
{
  "id": 2,
  "name": "CD Projekt RED",
  "email": "contact@cdprojektred.com",
  "bio": "Polish video game developer known for The Witcher series.",
  "founded_date": "1994-05-01"
}
```

#### Get Developer Details

```http
GET /api/v1/developers/{id}/
```

**Response (200 OK):**

```json
{
  "id": 1,
  "name": "Valve Corporation",
  "email": "contact@valvesoftware.com",
  "bio": "American video game developer and publisher.",
  "founded_date": "1996-08-24"
}
```

#### Delete Developer

```http
DELETE /api/v1/developers/{id}/
```

**Response (204 No Content)**

---

### Genres

Manage game genre categories.

#### List All Genres

```http
GET /api/v1/genres/
```

**Response (200 OK):**

```json
[
  {
    "id": 1,
    "name": "Action",
    "description": "Fast-paced games with combat and physical challenges."
  },
  {
    "id": 2,
    "name": "RPG",
    "description": "Role-playing games with character progression."
  }
]
```

#### Create Genre

```http
POST /api/v1/genres/
Content-Type: application/json

{
  "name": "Strategy",
  "description": "Games requiring tactical thinking and resource management."
}
```

**Response (201 Created):**

```json
{
  "id": 3,
  "name": "Strategy",
  "description": "Games requiring tactical thinking and resource management."
}
```

---

### Games

Core game management endpoints.

#### List All Games

```http
GET /api/v1/games/
```

**Response (200 OK):**

```json
[
  {
    "id": 1,
    "title": "Half-Life 2",
    "developer": 1,
    "genre": 1,
    "release_date": "2004-11-16",
    "price": "399.00",
    "discount_price": "199.00",
    "in_stock": true,
    "image": "/media/games/hl2.jpg",
    "rating": "4.9",
    "platform": "PC",
    "is_bestseller": true,
    "is_new": false,
    "is_discount": true,
    "sold_count": 1500,
    "seller": 1,
    "seller_username": "valve_official"
  }
]
```

#### Create Game

```http
POST /api/v1/games/
Content-Type: application/json

{
  "title": "New Game",
  "developer": 1,
  "genre": 2,
  "release_date": "2024-01-15",
  "price": "1999.00",
  "in_stock": true,
  "platform": "PC",
  "is_new": true
}
```

**Response (201 Created)**

#### Get Game Details

```http
GET /api/v1/games/{id}/
```

#### Update Game

```http
PUT /api/v1/games/{id}/
Content-Type: application/json

{
  "title": "Updated Game Title",
  "price": "1499.00",
  "is_discount": true,
  "discount_price": "999.00"
}
```

**Response (200 OK)**

#### Partial Update Game

```http
PATCH /api/v1/games/{id}/
Content-Type: application/json

{
  "price": "1299.00"
}
```

#### Delete Game

```http
DELETE /api/v1/games/{id}/
```

**Response (204 No Content)**

---

### Reviews

Manage game reviews and ratings.

#### List All Reviews

```http
GET /api/v1/reviews/
```

**Response (200 OK):**

```json
[
  {
    "id": 1,
    "game": 1,
    "reviewer_name": "GameFan123",
    "rating": 5,
    "comment": "Amazing game! The physics engine is revolutionary.",
    "created_at": "2024-01-20T14:30:00Z"
  }
]
```

#### Get Reviews for Specific Game

```http
GET /api/v1/games/{game_id}/reviews/
```

**Response (200 OK):**

```json
[
  {
    "id": 1,
    "game": 1,
    "reviewer_name": "Player1",
    "rating": 5,
    "comment": "Best game ever!",
    "created_at": "2024-01-20T14:30:00Z"
  }
]
```

#### Create Review

```http
POST /api/v1/reviews/
Content-Type: application/json

{
  "game": 1,
  "reviewer_name": "NewReviewer",
  "rating": 4,
  "comment": "Great game with minor issues."
}
```

**Response (201 Created)**

#### Delete Review

```http
DELETE /api/v1/reviews/{id}/
```

**Response (204 No Content)**

---

## Data Models

### Developer

| Field | Type | Description |
|-------|------|-------------|
| `id` | Integer | Unique identifier (auto-generated) |
| `name` | String(100) | Developer/studio name |
| `email` | Email | Contact email (unique) |
| `bio` | Text | Company biography |
| `founded_date` | Date | Foundation date |

### Genre

| Field | Type | Description |
|-------|------|-------------|
| `id` | Integer | Unique identifier |
| `name` | String(50) | Genre name (unique) |
| `description` | Text | Genre description |
| `icon` | String(50) | Optional icon class |

### Game

| Field | Type | Description |
|-------|------|-------------|
| `id` | Integer | Unique identifier |
| `title` | String(200) | Game title |
| `developer` | FK(Developer) | Related developer |
| `genre` | FK(Genre) | Game genre |
| `release_date` | Date | Release date |
| `price` | Decimal(8,2) | Regular price |
| `discount_price` | Decimal(8,2) | Sale price (nullable) |
| `in_stock` | Boolean | Availability status |
| `image` | ImageField | Game cover image |
| `rating` | Decimal(3,1) | Average rating (0.0-5.0) |
| `platform` | Choice | PC/PS/XBOX/NINTENDO |
| `is_bestseller` | Boolean | Bestseller flag |
| `is_new` | Boolean | New release flag |
| `is_discount` | Boolean | On sale flag |
| `sold_count` | Integer | Units sold |
| `seller` | FK(SellUser) | Seller reference |

### Review

| Field | Type | Description |
|-------|------|-------------|
| `id` | Integer | Unique identifier |
| `game` | FK(Game) | Related game |
| `reviewer_name` | String(100) | Reviewer name |
| `rating` | Integer | Rating (1-5) |
| `comment` | Text | Review text |
| `created_at` | DateTime | Creation timestamp |

---

## Error Handling

### HTTP Status Codes

| Code | Description |
|------|-------------|
| `200 OK` | Request successful |
| `201 Created` | Resource created |
| `204 No Content` | Resource deleted |
| `400 Bad Request` | Invalid request data |
| `404 Not Found` | Resource not found |
| `500 Internal Server Error` | Server error |

### Error Response Format

```json
{
  "field_name": [
    "Error message describing the issue."
  ]
}
```

### Validation Error Example

```json
{
  "email": [
    "Enter a valid email address."
  ],
  "name": [
    "This field is required."
  ]
}
```

---

## Usage Examples

### Python (requests)

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# List all games
response = requests.get(f"{BASE_URL}/games/")
games = response.json()
print(f"Found {len(games)} games")

# Create a new game
new_game = {
    "title": "My New Game",
    "developer": 1,
    "genre": 2,
    "release_date": "2024-12-01",
    "price": "999.00",
    "platform": "PC",
    "in_stock": True
}
response = requests.post(f"{BASE_URL}/games/", json=new_game)
if response.status_code == 201:
    print(f"Created game: {response.json()['title']}")

# Get reviews for a game
game_id = 1
response = requests.get(f"{BASE_URL}/games/{game_id}/reviews/")
reviews = response.json()
for review in reviews:
    print(f"{review['reviewer_name']}: {review['rating']}/5")
```

### JavaScript (fetch)

```javascript
const BASE_URL = 'http://localhost:8000/api/v1';

// List all genres
async function getGenres() {
    const response = await fetch(`${BASE_URL}/genres/`);
    const genres = await response.json();
    console.log('Genres:', genres);
    return genres;
}

// Create a review
async function createReview(gameId, reviewData) {
    const response = await fetch(`${BASE_URL}/reviews/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            game: gameId,
            reviewer_name: reviewData.name,
            rating: reviewData.rating,
            comment: reviewData.comment
        })
    });
    
    if (response.ok) {
        return await response.json();
    }
    throw new Error('Failed to create review');
}

// Usage
getGenres().then(genres => {
    genres.forEach(g => console.log(g.name));
});
```

### cURL

```bash
# List developers
curl -X GET http://localhost:8000/api/v1/developers/

# Create developer
curl -X POST http://localhost:8000/api/v1/developers/ \
  -H "Content-Type: application/json" \
  -d '{"name": "New Studio", "email": "info@newstudio.com", "bio": "Indie game studio", "founded_date": "2020-01-01"}'

# Get specific game
curl -X GET http://localhost:8000/api/v1/games/1/

# Delete review
curl -X DELETE http://localhost:8000/api/v1/reviews/5/
```

---

## Frontend Components

### CSS Design System

The frontend uses a centralized CSS file (`static/web/css/main.css`) with design tokens:

```css
:root {
    /* Primary Gradient */
    --primary-gradient: linear-gradient(45deg, #667eea, #764ba2);
    
    /* Accent Colors */
    --gold: #ffd700;
    --cta-gradient: linear-gradient(45deg, #ff6b35, #f7931e);
    --success-gradient: linear-gradient(45deg, #28a745, #20c997);
    
    /* Glass Effect */
    --glass-bg: rgba(255, 255, 255, 0.1);
    --glass-border: rgba(255, 255, 255, 0.2);
}
```

### Template Structure

All templates extend `base.html` using Django's template inheritance:

```html
{% extends 'base.html' %}

{% block title %}Page Title{% endblock %}

{% block content %}
    <!-- Page content here -->
{% endblock %}

{% block extra_css %}
    <!-- Additional styles -->
{% endblock %}

{% block extra_js %}
    <!-- Additional scripts -->
{% endblock %}
```

### Available CSS Classes

| Class | Description |
|-------|-------------|
| `.glass-card` | Frosted glass effect container |
| `.glass-card-dark` | Darker glass variant |
| `.title-gold` | Gold colored heading |
| `.text-gold` | Gold text color |
| `.btn-primary` | Primary action button (orange) |
| `.btn-success` | Success/confirm button (green) |
| `.btn-secondary` | Secondary action button |
| `.form-control` | Styled form input |
| `.product-card` | Game card component |
| `.badge-*` | Status badges |

---

## Performance Considerations

### Database Optimization (3NF)

The database follows Third Normal Form (3NF):

1. **No calculated fields stored** - Totals computed via `SUM()` aggregations
2. **Proper foreign keys** - Relationships normalized
3. **Reference tables** - OrderStatus, PaymentMethod as lookups

### Computed Properties

```python
# Example: Order total computed dynamically
class Order(models.Model):
    @property
    def total_amount(self):
        return sum(item.total_price for item in self.items.all())
```

### Frontend Optimizations

- **Lazy loading images**: `loading="lazy"` attribute
- **Consolidated CSS**: Single `main.css` file
- **Template inheritance**: Reduced HTML duplication
- **Bootstrap CDN**: Efficient external loading

### Recommended Optimizations

```python
# Use select_related for FK joins
games = Game.objects.select_related('developer', 'genre', 'seller').all()

# Use prefetch_related for reverse FK
games = Game.objects.prefetch_related('reviews').all()

# Pagination for large datasets
from rest_framework.pagination import PageNumberPagination

class StandardPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
```

---

## Quick Reference

| Endpoint | Methods | Description |
|----------|---------|-------------|
| `/api/v1/developers/` | GET, POST | List/create developers |
| `/api/v1/developers/{id}/` | GET, DELETE | Retrieve/delete developer |
| `/api/v1/genres/` | GET, POST | List/create genres |
| `/api/v1/games/` | GET, POST | List/create games |
| `/api/v1/games/{id}/` | GET, PUT, PATCH, DELETE | Game CRUD |
| `/api/v1/reviews/` | GET, POST | List/create reviews |
| `/api/v1/reviews/{id}/` | DELETE | Delete review |
| `/api/v1/games/{id}/reviews/` | GET | Game's reviews |
| `/api/v1/docs/swagger-ui/` | GET | Swagger documentation |
| `/api/v1/docs/redoc/` | GET | ReDoc documentation |

---

## Support

For technical support or API issues:
- Email: info@playtrade.com
- Phone: +7 (999) 123-45-67

---

*Last updated: December 2024*
*API Version: 1.0*

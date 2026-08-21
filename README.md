# Tech Blogs

A full-featured blogging platform built with Django. Users can sign up, publish posts with images, comment and reply in nested threads, like posts and comments, and manage their profile — including OTP-based password recovery via email.

## Features

- **Authentication** — signup, login/logout, profile update, password change, and account deletion
- **Password recovery** — forgot password flow with OTP verification sent by email
- **Posts** — create, update, delete, and view blog posts with image uploads
- **Comments** — add, update, delete, like, and reply to comments (nested/threaded replies)
- **Likes** — like/unlike posts and comments
- **Static pages** — render arbitrary content pages via a slug (`/page/<slug>/`)
- **Media & static files** — image uploads via Cloudinary, static assets served with WhiteNoise

## Tech Stack

- **Backend:** Django (Python)
- **Database:** PostgreSQL in production (via `dj-database-url` / `psycopg`), SQLite for local development
- **Static files:** WhiteNoise
- **Media storage:** Cloudinary (`django-cloudinary-storage`)
- **Email:** Anymail (Brevo/Sendinblue backend) — used for OTP and password-reset emails
- **Server:** Gunicorn
- **Deployment:** Render (see `render.yaml`)

## Project Structure

```
Blog-main/
├── Blog/                  # Django project (settings, root URLs, WSGI/ASGI)
├── Tech_Blogs/             # Main app
│   ├── models.py           # User, Post, Comment models
│   ├── views.py             # App views
│   ├── urls.py               # App URL routes
│   ├── admin.py
│   ├── migrations/
│   ├── Templates/          # HTML templates
│   └── static/              # CSS/JS/static assets
├── manage.py
├── requirements.txt
├── build.sh                # Render build script (install, collectstatic, migrate)
└── render.yaml              # Render deployment configuration
```

## Getting Started

### Prerequisites

- Python 3.12+
- pip

### Installation

1. Clone the repository
   ```bash
   git clone <repository-url>
   cd Blog-main
   ```

2. Create and activate a virtual environment
   ```bash
   python -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   ```

3. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root with the following variables:
   ```env
   SECRET_KEY=your-secret-key
   DATABASE_URL=postgres://user:password@host:port/dbname   # optional locally, defaults to SQLite
   CLOUDINARY_CLOUD_NAME=your-cloud-name
   CLOUDINARY_API_KEY=your-api-key
   CLOUDINARY_API_SECRET=your-api-secret
   BREVO_API_KEY=your-brevo-api-key
   DEFAULT_FROM_EMAIL=your-from-email@example.com
   ```

5. Apply migrations
   ```bash
   python manage.py migrate
   ```

6. Create a superuser (optional, for admin access)
   ```bash
   python manage.py createsuperuser
   ```

7. Run the development server
   ```bash
   python manage.py runserver
   ```

The app will be available at `http://127.0.0.1:8000/`.

## Deployment

This project is configured for deployment on [Render](https://render.com) using `render.yaml`:

- Build command: `./build.sh` (installs dependencies, collects static files, runs migrations)
- Start command: `gunicorn Blog.wsgi:application`
- A free PostgreSQL database (`blog-db`) is provisioned automatically
- The following environment variables must be set in the Render dashboard: `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET` (`SECRET_KEY` and `DATABASE_URL` are generated/linked automatically)

## Key Routes

| Route | Description |
|---|---|
| `/` | Home — list of posts |
| `/signup/`, `/login/`, `/logout/` | Authentication |
| `/post/add/` | Create a post |
| `/post/<id>/` | View a post |
| `/post/<id>/update/`, `/post/<id>/delete/` | Edit/delete a post |
| `/post/<id>/like/` | Like a post |
| `/post/<id>/comment/` | Add a comment |
| `/comment/<id>/update/`, `/comment/<id>/delete/` | Edit/delete a comment |
| `/comment/<id>/like/`, `/comment/<id>/reply/` | Like/reply to a comment |
| `/profile/` | View profile |
| `/profile/update/`, `/profile/password/`, `/profile/delete/` | Manage account |
| `/forgot-password/`, `/verify-otp/`, `/resend-otp/`, `/reset-password/` | Password recovery flow |
| `/page/<slug>/` | Static content page |
| `/admin/` | Django admin |

## License

Add license details here.

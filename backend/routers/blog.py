from typing import Optional
from fastapi import APIRouter, HTTPException
from database import get_connection

router = APIRouter(prefix="/blog", tags=["blog"])


@router.get("/posts")
async def list_blog_posts(page: int = 1, limit: int = 10, category: str = ""):
    """List published blog posts for the public blog page."""
    conn = get_connection()
    cur = conn.cursor()
    offset = (page - 1) * limit

    if category:
        cur.execute("""
            SELECT id, slug, title, meta_description, category, tags, views, published_at
            FROM blog_posts WHERE status = 'published' AND category = %s
            ORDER BY published_at DESC LIMIT %s OFFSET %s
        """, (category, limit, offset))
    else:
        cur.execute("""
            SELECT id, slug, title, meta_description, category, tags, views, published_at
            FROM blog_posts WHERE status = 'published'
            ORDER BY published_at DESC LIMIT %s OFFSET %s
        """, (limit, offset))

    posts = cur.fetchall()

    cur.execute("SELECT COUNT(*) as total FROM blog_posts WHERE status = 'published'")
    total = cur.fetchone()["total"]

    cur.close()
    conn.close()

    return {
        "posts": [{**p, "id": str(p["id"])} for p in posts],
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit,
    }


@router.get("/posts/{slug}")
async def get_blog_post(slug: str):
    """Get a single blog post by slug."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM blog_posts WHERE slug = %s AND status = 'published'", (slug,))
    post = cur.fetchone()

    if not post:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Artigo nao encontrado")

    # Increment views
    cur.execute("UPDATE blog_posts SET views = views + 1 WHERE slug = %s", (slug,))
    conn.commit()

    cur.close()
    conn.close()

    return {**post, "id": str(post["id"])}


@router.get("/sitemap")
async def blog_sitemap():
    """Return all published post slugs for SEO sitemap."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT slug, published_at FROM blog_posts WHERE status = 'published' ORDER BY published_at DESC")
    posts = cur.fetchall()
    cur.close()
    conn.close()
    return [{"slug": p["slug"], "published_at": str(p["published_at"])} for p in posts]

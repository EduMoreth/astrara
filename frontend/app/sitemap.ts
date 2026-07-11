import type { MetadataRoute } from 'next'

const BASE = 'https://www.astrara.online'
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://astrara-production.up.railway.app'

export const revalidate = 3600 // refresh hourly so new blog posts get indexed

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const staticRoutes: MetadataRoute.Sitemap = [
    { url: `${BASE}/`, changeFrequency: 'weekly', priority: 1 },
    { url: `${BASE}/chart`, changeFrequency: 'weekly', priority: 0.9 },
    { url: `${BASE}/sinastria`, changeFrequency: 'weekly', priority: 0.9 },
    { url: `${BASE}/blog`, changeFrequency: 'daily', priority: 0.8 },
    { url: `${BASE}/privacidade`, changeFrequency: 'yearly', priority: 0.2 },
    { url: `${BASE}/termos`, changeFrequency: 'yearly', priority: 0.2 },
  ]

  // Blog posts — resilient: if the API is unreachable at build/revalidate time,
  // the static routes still ship
  try {
    const res = await fetch(`${API_URL}/blog/posts?page=1&limit=50`, {
      next: { revalidate: 3600 },
      signal: AbortSignal.timeout(8000),
    })
    if (res.ok) {
      const data = await res.json()
      const posts = Array.isArray(data.posts) ? data.posts : []
      const postRoutes: MetadataRoute.Sitemap = posts
        .filter((p: { slug?: string }) => p.slug)
        .map((p: { slug: string; published_at?: string }) => ({
          url: `${BASE}/blog/post?slug=${encodeURIComponent(p.slug)}`,
          lastModified: p.published_at ? new Date(p.published_at) : undefined,
          changeFrequency: 'monthly' as const,
          priority: 0.6,
        }))
      return [...staticRoutes, ...postRoutes]
    }
  } catch { /* API unreachable: ship static routes */ }

  return staticRoutes
}

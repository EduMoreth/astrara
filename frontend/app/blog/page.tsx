'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import StarBackground from '@/components/StarBackground'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://astrara-production.up.railway.app'

interface BlogPost {
  id: string
  slug: string
  title: string
  meta_description: string
  category: string
  views: number
  published_at: string
}

export default function BlogPage() {
  const [posts, setPosts] = useState<BlogPost[]>([])
  const [page, setPage] = useState(1)
  const [pages, setPages] = useState(1)

  useEffect(() => {
    fetch(`${API_URL}/blog/posts?page=${page}&limit=12`)
      .then(r => r.json())
      .then(data => { setPosts(data.posts); setPages(data.pages) })
      .catch(() => {})
  }, [page])

  return (
    <main className="relative min-h-screen">
      <StarBackground />

      <nav className="relative z-10 flex items-center justify-between px-4 sm:px-6 py-4 sm:py-5 max-w-7xl mx-auto">
        <Link href="/" className="font-display text-xl sm:text-2xl font-semibold text-gradient-gold">Astrara</Link>
        <Link href="/chart" className="btn-primary !text-xs sm:!text-sm !py-2 !px-4 !w-auto">Criar meu mapa</Link>
      </nav>

      <div className="relative z-10 px-4 sm:px-6 max-w-5xl mx-auto py-8 sm:py-12">
        <h1 className="font-display text-3xl sm:text-4xl text-stardust mb-2">Blog Astrara</h1>
        <p className="text-muted mb-8 sm:mb-12">Artigos sobre astrologia, signos, planetas e autoconhecimento.</p>

        {posts.length === 0 ? (
          <div className="glass-card p-12 text-center">
            <p className="text-muted">Novos artigos em breve!</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
            {posts.map(post => (
              <Link key={post.id} href={`/blog/post?slug=${post.slug}`} className="glass-card p-5 sm:p-6 hover:border-gold/30 transition-all group">
                {post.category && (
                  <span className="text-xs text-gold bg-gold/10 px-2 py-0.5 rounded-full">{post.category}</span>
                )}
                <h2 className="font-display text-lg sm:text-xl text-stardust mt-3 mb-2 group-hover:text-gold transition-colors line-clamp-2">
                  {post.title}
                </h2>
                <p className="text-muted text-sm line-clamp-3">{post.meta_description}</p>
                <div className="flex items-center justify-between mt-4 text-xs text-muted">
                  <span>{new Date(post.published_at).toLocaleDateString('pt-BR')}</span>
                  <span>{post.views} visualizacoes</span>
                </div>
              </Link>
            ))}
          </div>
        )}

        {pages > 1 && (
          <div className="flex justify-center gap-2 mt-8">
            {Array.from({ length: pages }, (_, i) => (
              <button key={i} onClick={() => setPage(i + 1)}
                className={`px-3 py-1 text-sm rounded ${page === i + 1 ? 'bg-gold text-cosmos' : 'text-muted'}`}>
                {i + 1}
              </button>
            ))}
          </div>
        )}
      </div>
    </main>
  )
}

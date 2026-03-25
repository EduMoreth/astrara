'use client'

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import StarBackground from '@/components/StarBackground'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://astrara-production.up.railway.app'

export default function BlogPostPage() {
  const params = useParams()
  const slug = params.slug as string
  const [post, setPost] = useState<Record<string, unknown> | null>(null)
  const [error, setError] = useState(false)

  useEffect(() => {
    fetch(`${API_URL}/blog/posts/${slug}`)
      .then(r => { if (!r.ok) throw new Error(); return r.json() })
      .then(setPost)
      .catch(() => setError(true))
  }, [slug])

  if (error) return (
    <main className="relative min-h-screen flex items-center justify-center">
      <StarBackground />
      <div className="glass-card p-12 text-center relative z-10">
        <h1 className="text-2xl text-stardust mb-4">Artigo nao encontrado</h1>
        <Link href="/blog" className="text-gold hover:underline">Voltar ao blog</Link>
      </div>
    </main>
  )

  if (!post) return (
    <main className="relative min-h-screen flex items-center justify-center">
      <StarBackground />
      <div className="text-muted relative z-10">Carregando...</div>
    </main>
  )

  return (
    <main className="relative min-h-screen">
      <StarBackground />

      <nav className="relative z-10 flex items-center justify-between px-4 sm:px-6 py-4 sm:py-5 max-w-7xl mx-auto">
        <Link href="/" className="font-display text-xl sm:text-2xl font-semibold text-gradient-gold">Astrara</Link>
        <div className="flex items-center gap-3">
          <Link href="/blog" className="text-muted hover:text-stardust text-sm">Blog</Link>
          <Link href="/chart" className="btn-primary !text-xs !py-2 !px-4 !w-auto">Criar meu mapa</Link>
        </div>
      </nav>

      <article className="relative z-10 px-4 sm:px-6 max-w-3xl mx-auto py-8 sm:py-12">
        {post.category && (
          <span className="text-xs text-gold bg-gold/10 px-2 py-0.5 rounded-full">{post.category as string}</span>
        )}
        <h1 className="font-display text-3xl sm:text-4xl lg:text-5xl text-stardust mt-4 mb-4 leading-tight">
          {post.title as string}
        </h1>
        <div className="flex items-center gap-4 text-muted text-sm mb-8">
          <span>{new Date(post.published_at as string).toLocaleDateString('pt-BR', { year: 'numeric', month: 'long', day: 'numeric' })}</span>
          <span>{post.views as number} visualizacoes</span>
        </div>

        <div
          className="prose prose-invert prose-gold max-w-none
            [&_h2]:font-display [&_h2]:text-2xl [&_h2]:text-gold [&_h2]:mt-10 [&_h2]:mb-4
            [&_h3]:font-display [&_h3]:text-xl [&_h3]:text-stardust [&_h3]:mt-8 [&_h3]:mb-3
            [&_p]:text-stardust/80 [&_p]:leading-relaxed [&_p]:mb-4
            [&_strong]:text-gold
            [&_a]:text-gold [&_a]:underline
            [&_ul]:list-disc [&_ul]:ml-6 [&_ul]:text-stardust/80
            [&_ol]:list-decimal [&_ol]:ml-6 [&_ol]:text-stardust/80
            [&_li]:mb-2
            [&_blockquote]:border-l-2 [&_blockquote]:border-gold/30 [&_blockquote]:pl-4 [&_blockquote]:italic [&_blockquote]:text-muted"
          dangerouslySetInnerHTML={{
            __html: (post.content as string)
              .replace(/^### (.*$)/gm, '<h3>$1</h3>')
              .replace(/^## (.*$)/gm, '<h2>$1</h2>')
              .replace(/^# (.*$)/gm, '<h1>$1</h1>')
              .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
              .replace(/\*(.*?)\*/g, '<em>$1</em>')
              .replace(/\n\n/g, '</p><p>')
              .replace(/^(?!<[hpuo])/gm, '<p>')
          }}
        />

        {/* CTA */}
        <div className="glass-card p-8 mt-12 text-center border-gold/20">
          <p className="text-stardust/80 text-lg font-display mb-4">Descubra o que os astros revelam sobre voce</p>
          <Link href="/chart" className="btn-primary text-sm">Calcular meu mapa astral gratuitamente →</Link>
        </div>

        <div className="mt-8">
          <Link href="/blog" className="text-muted hover:text-gold text-sm">← Voltar ao blog</Link>
        </div>
      </article>
    </main>
  )
}

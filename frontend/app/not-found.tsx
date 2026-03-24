import Link from 'next/link'

export default function NotFound() {
  return (
    <main className="min-h-screen bg-cosmos flex items-center justify-center">
      <div className="text-center">
        <h1 className="font-display text-6xl text-gold mb-4">404</h1>
        <p className="text-stardust text-lg mb-2">Pagina nao encontrada</p>
        <p className="text-muted text-sm mb-8">Os astros nao encontraram o que voce procura.</p>
        <Link href="/" className="btn-primary text-sm">Voltar ao inicio</Link>
      </div>
    </main>
  )
}

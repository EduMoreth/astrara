import Link from 'next/link'

export const metadata = {
  title: 'Termos de Uso — Astrara',
}

export default function TermsPage() {
  return (
    <main className="min-h-screen bg-cosmos">
      <nav className="flex items-center justify-between px-6 py-5 max-w-4xl mx-auto">
        <Link href="/" className="font-display text-2xl font-semibold text-gradient-gold">Astrara</Link>
      </nav>

      <article className="max-w-4xl mx-auto px-6 py-12">
        <h1 className="font-display text-4xl text-gold mb-2">Termos de Uso</h1>
        <p className="text-muted text-sm mb-8">Ultima atualizacao: 24 de marco de 2026</p>

        <div className="space-y-8 text-stardust/80 text-sm leading-relaxed">
          <section>
            <h2 className="text-gold text-lg font-display mb-3">1. Aceitacao dos Termos</h2>
            <p>Ao acessar e utilizar o site www.astrara.online (&quot;Servico&quot;), voce concorda com estes Termos de Uso e com nossa <Link href="/privacidade" className="text-gold hover:underline">Politica de Privacidade</Link>. Se nao concordar, nao utilize o Servico.</p>
          </section>

          <section>
            <h2 className="text-gold text-lg font-display mb-3">2. Descricao do Servico</h2>
            <p>A Astrara oferece servicos de calculo de mapas astrais natais e interpretacoes geradas por inteligencia artificial. O servico e fornecido pela Brain Legal LTDA, CNPJ [CNPJ].</p>
          </section>

          <section>
            <h2 className="text-gold text-lg font-display mb-3">3. Cadastro e Conta</h2>
            <ul className="list-disc pl-6 space-y-1">
              <li>O cadastro requer nome, email e senha.</li>
              <li>Voce e responsavel por manter a confidencialidade da sua senha.</li>
              <li>Voce deve fornecer informacoes verdadeiras e atualizadas.</li>
              <li>O uso e pessoal e intransferivel.</li>
              <li>Menores de 18 anos devem ter autorizacao dos responsaveis legais.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-gold text-lg font-display mb-3">4. Servico Gratuito e Pago</h2>
            <ul className="list-disc pl-6 space-y-1">
              <li><strong className="text-stardust">Gratuito:</strong> calculo do mapa astral natal com posicoes planetarias e mandala.</li>
              <li><strong className="text-stardust">Pago:</strong> interpretacao completa gerada por IA com PDF para download.</li>
              <li>Pagamentos sao processados pelo Stripe e sujeitos aos termos do Stripe.</li>
              <li>Creditos adquiridos nao expiram enquanto a conta estiver ativa.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-gold text-lg font-display mb-3">5. Politica de Reembolso</h2>
            <ul className="list-disc pl-6 space-y-1">
              <li>Reembolsos podem ser solicitados em ate 7 dias apos a compra.</li>
              <li>Solicitacoes devem ser feitas via sistema de suporte ou email.</li>
              <li>Reembolsos sao processados em ate 10 dias uteis na forma de pagamento original.</li>
              <li>Creditos utilizados antes do reembolso serao descontados.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-gold text-lg font-display mb-3">6. Propriedade Intelectual</h2>
            <p>Todo o conteudo do site (design, textos, codigo, marcas) e propriedade da Brain Legal LTDA. As interpretacoes geradas sao licenciadas ao usuario para uso pessoal.</p>
          </section>

          <section>
            <h2 className="text-gold text-lg font-display mb-3">7. Limitacao de Responsabilidade</h2>
            <ul className="list-disc pl-6 space-y-1">
              <li>As interpretacoes astrologicas sao geradas por IA e tem carater de entretenimento e autoconhecimento.</li>
              <li>Nao substituem aconselhamento profissional medico, psicologico, juridico ou financeiro.</li>
              <li>A Astrara nao garante a exatidao ou aplicabilidade das interpretacoes.</li>
              <li>O servico e fornecido &quot;como esta&quot; (as is).</li>
            </ul>
          </section>

          <section>
            <h2 className="text-gold text-lg font-display mb-3">8. Conduta do Usuario</h2>
            <p>E proibido:</p>
            <ul className="list-disc pl-6 space-y-1 mt-2">
              <li>Usar o servico para fins ilegais ou nao autorizados.</li>
              <li>Tentar acessar areas restritas do sistema.</li>
              <li>Revender ou redistribuir o conteudo sem autorizacao.</li>
              <li>Usar bots ou scripts automatizados para acessar o servico.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-gold text-lg font-display mb-3">9. Disponibilidade</h2>
            <p>A Astrara se esforça para manter o servico disponivel 24/7, mas nao garante disponibilidade ininterrupta. Manutencoes programadas serao comunicadas com antecedencia quando possivel.</p>
          </section>

          <section>
            <h2 className="text-gold text-lg font-display mb-3">10. Alteracoes nos Termos</h2>
            <p>Podemos alterar estes termos a qualquer momento. Alteracoes significativas serao comunicadas por email ou aviso no site. O uso continuado apos alteracoes constitui aceitacao.</p>
          </section>

          <section>
            <h2 className="text-gold text-lg font-display mb-3">11. Legislacao Aplicavel</h2>
            <p>Estes termos sao regidos pelas leis da Republica Federativa do Brasil. Fica eleito o foro da comarca de [cidade/estado] para dirimir quaisquer controversias.</p>
          </section>

          <section>
            <h2 className="text-gold text-lg font-display mb-3">12. Contato</h2>
            <p>Email: contato@astrara.online<br />Brain Legal LTDA</p>
          </section>
        </div>
      </article>
    </main>
  )
}

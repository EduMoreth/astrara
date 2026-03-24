import Link from 'next/link'

export const metadata = {
  title: 'Politica de Privacidade — Astrara',
}

export default function PrivacyPolicyPage() {
  return (
    <main className="min-h-screen bg-cosmos">
      <nav className="flex items-center justify-between px-6 py-5 max-w-4xl mx-auto">
        <Link href="/" className="font-display text-2xl font-semibold text-gradient-gold">Astrara</Link>
      </nav>

      <article className="max-w-4xl mx-auto px-6 py-12 prose-invert">
        <h1 className="font-display text-4xl text-gold mb-2">Politica de Privacidade</h1>
        <p className="text-muted text-sm mb-8">Ultima atualizacao: 24 de marco de 2026</p>

        <div className="space-y-8 text-stardust/80 text-sm leading-relaxed">
          <section>
            <h2 className="text-gold text-lg font-display mb-3">1. Controlador dos Dados</h2>
            <p>A <strong className="text-stardust">Brain Legal LTDA</strong> (&quot;Astrara&quot;, &quot;nos&quot;), inscrita no CNPJ sob o numero 51.560.460/0001-05, com sede em Avenida Paulista 1136, 16o andar, Sao Paulo/SP, e a controladora dos dados pessoais coletados por meio do site www.astrara.online.</p>
            <p className="mt-2">Encarregado de Protecao de Dados (DPO): Eduardo Moreth Loquez — contato: dpo@astrara.online</p>
          </section>

          <section>
            <h2 className="text-gold text-lg font-display mb-3">2. Dados Pessoais Coletados</h2>
            <p>Coletamos os seguintes dados:</p>
            <ul className="list-disc pl-6 space-y-1 mt-2">
              <li><strong className="text-stardust">Dados de cadastro:</strong> nome completo e endereco de email.</li>
              <li><strong className="text-stardust">Dados de nascimento:</strong> data, hora e cidade de nascimento (para calculo do mapa astral).</li>
              <li><strong className="text-stardust">Dados de pagamento:</strong> processados diretamente pelo Stripe Inc. Nao armazenamos dados de cartao de credito.</li>
              <li><strong className="text-stardust">Dados de uso:</strong> logs de acesso, endereco IP, tipo de navegador.</li>
              <li><strong className="text-stardust">Cookies:</strong> cookies essenciais para funcionamento do site e token de autenticacao.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-gold text-lg font-display mb-3">3. Finalidade do Tratamento</h2>
            <ul className="list-disc pl-6 space-y-1">
              <li>Prestacao do servico de calculo e interpretacao de mapas astrais.</li>
              <li>Criacao e gerenciamento de conta do usuario.</li>
              <li>Processamento de pagamentos e emissao de creditos.</li>
              <li>Comunicacao sobre o servico (emails transacionais).</li>
              <li>Suporte ao cliente via sistema de tickets.</li>
              <li>Melhoria continua do servico e analise de uso agregada.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-gold text-lg font-display mb-3">4. Base Legal (LGPD Art. 7)</h2>
            <ul className="list-disc pl-6 space-y-1">
              <li><strong className="text-stardust">Consentimento (Art. 7, I):</strong> para o tratamento de dados de nascimento e envio de comunicacoes.</li>
              <li><strong className="text-stardust">Execucao de contrato (Art. 7, V):</strong> para prestacao do servico contratado.</li>
              <li><strong className="text-stardust">Interesse legitimo (Art. 7, IX):</strong> para melhoria do servico e seguranca.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-gold text-lg font-display mb-3">5. Compartilhamento de Dados</h2>
            <p>Seus dados podem ser compartilhados com:</p>
            <ul className="list-disc pl-6 space-y-1 mt-2">
              <li><strong className="text-stardust">Stripe Inc.:</strong> processamento de pagamentos (EUA, com clausulas contratuais padrao).</li>
              <li><strong className="text-stardust">Anthropic:</strong> geracao de interpretacoes por IA (dados anonimizados, sem identificacao pessoal).</li>
              <li><strong className="text-stardust">Resend:</strong> envio de emails transacionais.</li>
              <li><strong className="text-stardust">Railway:</strong> hospedagem de infraestrutura.</li>
            </ul>
            <p className="mt-2">Nao vendemos, alugamos ou compartilhamos seus dados pessoais com terceiros para fins de marketing.</p>
          </section>

          <section>
            <h2 className="text-gold text-lg font-display mb-3">6. Transferencia Internacional</h2>
            <p>Seus dados podem ser processados fora do Brasil pelos prestadores de servicos listados acima. Estas transferencias sao protegidas por clausulas contratuais padrao conforme LGPD Art. 33.</p>
          </section>

          <section>
            <h2 className="text-gold text-lg font-display mb-3">7. Retencao de Dados</h2>
            <ul className="list-disc pl-6 space-y-1">
              <li>Dados de conta: mantidos enquanto a conta estiver ativa.</li>
              <li>Dados de mapas astrais: mantidos enquanto a conta estiver ativa.</li>
              <li>Dados de transacoes: mantidos por 5 anos (obrigacao fiscal).</li>
              <li>Logs de acesso: mantidos por 6 meses (Marco Civil da Internet, Art. 15).</li>
              <li>Apos exclusao da conta: dados anonimizados ou excluidos em ate 30 dias.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-gold text-lg font-display mb-3">8. Direitos do Titular (LGPD Art. 18)</h2>
            <p>Voce tem direito a:</p>
            <ul className="list-disc pl-6 space-y-1 mt-2">
              <li>Confirmar a existencia de tratamento dos seus dados.</li>
              <li>Acessar seus dados pessoais.</li>
              <li>Corrigir dados incompletos ou desatualizados.</li>
              <li>Solicitar anonimizacao, bloqueio ou eliminacao de dados.</li>
              <li>Solicitar portabilidade dos dados.</li>
              <li>Revogar o consentimento a qualquer momento.</li>
              <li>Obter informacoes sobre compartilhamento com terceiros.</li>
            </ul>
            <p className="mt-2">Para exercer seus direitos, acesse <Link href="/conta" className="text-gold hover:underline">Minha Conta</Link> ou envie email para dpo@astrara.online.</p>
          </section>

          <section>
            <h2 className="text-gold text-lg font-display mb-3">9. Seguranca</h2>
            <p>Adotamos medidas tecnicas e organizacionais para proteger seus dados, incluindo: criptografia de senhas (bcrypt), conexoes HTTPS, tokens JWT com expiracao, e controle de acesso baseado em funcoes.</p>
          </section>

          <section>
            <h2 className="text-gold text-lg font-display mb-3">10. Cookies</h2>
            <p>Utilizamos apenas cookies essenciais para funcionamento do site (token de autenticacao armazenado em localStorage). Nao utilizamos cookies de rastreamento ou publicidade.</p>
          </section>

          <section>
            <h2 className="text-gold text-lg font-display mb-3">11. Alteracoes</h2>
            <p>Esta politica pode ser atualizada periodicamente. Notificaremos alteracoes significativas por email ou aviso no site.</p>
          </section>

          <section>
            <h2 className="text-gold text-lg font-display mb-3">12. Contato</h2>
            <p>Para duvidas sobre esta politica ou sobre o tratamento de seus dados:</p>
            <p className="mt-2">Email: dpo@astrara.online<br />Controlador: Brain Legal LTDA<br />Encarregado (DPO): Eduardo Moreth Loquez</p>
          </section>
        </div>
      </article>
    </main>
  )
}

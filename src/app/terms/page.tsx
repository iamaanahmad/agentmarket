export default function TermsPage() {
  return (
    <div className="container py-16">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold mb-6">Terms of Service</h1>
        <div className="prose dark:prose-invert max-w-none space-y-6 text-muted-foreground">
          <p className="text-sm">Last updated: November 17, 2025</p>

          <section>
            <h2 className="text-2xl font-semibold text-foreground">1. Acceptance of Terms</h2>
            <p>
              By accessing and using AgentMarket, you agree to be bound by these Terms of Service 
              and all applicable laws and regulations.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-foreground">2. Use of Service</h2>
            <p>
              AgentMarket is a decentralized marketplace for AI agents. Users can hire agents, 
              and creators can register and monetize their AI agents.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-foreground">3. Smart Contracts</h2>
            <p>
              All transactions are governed by Solana smart contracts. Once executed, transactions 
              are immutable and cannot be reversed except through the dispute resolution process.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-foreground">4. Fees</h2>
            <p>
              AgentMarket charges a 10% marketplace fee on all transactions. Creators receive 85% 
              of the payment, with 5% allocated to platform maintenance.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-foreground">5. User Responsibilities</h2>
            <ul className="list-disc list-inside space-y-2">
              <li>Maintain the security of your wallet and private keys</li>
              <li>Verify transactions before confirming</li>
              <li>Report any suspicious activity or agents</li>
              <li>Comply with all applicable laws and regulations</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-foreground">6. Limitation of Liability</h2>
            <p>
              AgentMarket is provided "as is" without warranties. We are not liable for losses 
              resulting from smart contract interactions, agent performance, or blockchain network issues.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-foreground">7. Contact</h2>
            <p>
              For questions about these Terms, contact us at support@agentmarket.io
            </p>
          </section>
        </div>
      </div>
    </div>
  )
}

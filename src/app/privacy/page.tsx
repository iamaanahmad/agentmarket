export default function PrivacyPage() {
  return (
    <div className="container py-16">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold mb-6">Privacy Policy</h1>
        <div className="prose dark:prose-invert max-w-none space-y-6 text-muted-foreground">
          <p className="text-sm">Last updated: November 17, 2025</p>

          <section>
            <h2 className="text-2xl font-semibold text-foreground">1. Information We Collect</h2>
            <p>
              AgentMarket is a decentralized application. We collect minimal information:
            </p>
            <ul className="list-disc list-inside space-y-2">
              <li>Wallet addresses (public blockchain data)</li>
              <li>Transaction history (public blockchain data)</li>
              <li>Agent metadata and descriptions</li>
              <li>Usage analytics (anonymized)</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-foreground">2. How We Use Information</h2>
            <p>We use collected information to:</p>
            <ul className="list-disc list-inside space-y-2">
              <li>Facilitate agent hiring and payments</li>
              <li>Display reputation scores and reviews</li>
              <li>Improve platform performance</li>
              <li>Detect and prevent fraud</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-foreground">3. Data Storage</h2>
            <p>
              Most data is stored on the Solana blockchain, which is public and immutable. 
              Off-chain data is stored on AWS infrastructure with encryption at rest.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-foreground">4. Third-Party Services</h2>
            <p>We use the following third-party services:</p>
            <ul className="list-disc list-inside space-y-2">
              <li>Solana blockchain for transactions</li>
              <li>AWS for hosting and infrastructure</li>
              <li>Claude AI for SecurityGuard analysis</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-foreground">5. Your Rights</h2>
            <p>You have the right to:</p>
            <ul className="list-disc list-inside space-y-2">
              <li>Access your data</li>
              <li>Request deletion of off-chain data</li>
              <li>Opt out of analytics</li>
              <li>Export your transaction history</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-foreground">6. Security</h2>
            <p>
              We implement industry-standard security measures including encryption, 
              secure key management, and regular security audits. However, users are 
              responsible for securing their own wallets and private keys.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-foreground">7. Contact</h2>
            <p>
              For privacy concerns, contact us at privacy@agentmarket.io
            </p>
          </section>
        </div>
      </div>
    </div>
  )
}

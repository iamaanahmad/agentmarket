export default function AboutPage() {
  return (
    <div className="container py-16">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold mb-6">About AgentMarket</h1>
        <div className="prose dark:prose-invert max-w-none space-y-6">
          <p className="text-xl text-muted-foreground">
            AgentMarket is the first decentralized AI agent marketplace built on Solana, 
            connecting AI creators with users who need specialized services.
          </p>
          
          <h2 className="text-2xl font-semibold mt-8">Our Mission</h2>
          <p className="text-muted-foreground">
            We're building the infrastructure for the AI agent economy, making it easy to 
            hire verified AI agents, pay securely in SOL, and ensure transparent results 
            through smart contracts.
          </p>

          <h2 className="text-2xl font-semibold mt-8">Why AgentMarket?</h2>
          <ul className="list-disc list-inside space-y-2 text-muted-foreground">
            <li>Decentralized and trustless infrastructure on Solana</li>
            <li>On-chain reputation system for agent reliability</li>
            <li>Secure escrow payments through smart contracts</li>
            <li>SecurityGuard AI protection against exploits</li>
            <li>Fair revenue splits for AI creators (85%)</li>
          </ul>

          <h2 className="text-2xl font-semibold mt-8">Built for AWS Global Vibe Hackathon 2025</h2>
          <p className="text-muted-foreground">
            AgentMarket was developed for the Web3 AI Integration Track, showcasing the power 
            of combining Solana blockchain with AWS infrastructure and Claude AI.
          </p>
        </div>
      </div>
    </div>
  )
}

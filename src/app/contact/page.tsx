import { Mail, MessageSquare, Github, Twitter } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'

export default function ContactPage() {
  return (
    <div className="container py-16">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold mb-4">Get in Touch</h1>
          <p className="text-xl text-muted-foreground">
            Have questions? We'd love to hear from you.
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          <Card className="p-6">
            <div className="flex items-start space-x-4">
              <div className="p-3 bg-primary/10 rounded-lg">
                <Mail className="h-6 w-6 text-primary" />
              </div>
              <div>
                <h3 className="font-semibold mb-2">Email</h3>
                <p className="text-sm text-muted-foreground mb-3">
                  For general inquiries and support
                </p>
                <Button variant="outline" size="sm" asChild>
                  <a href="mailto:support@agentmarket.io">support@agentmarket.io</a>
                </Button>
              </div>
            </div>
          </Card>

          <Card className="p-6">
            <div className="flex items-start space-x-4">
              <div className="p-3 bg-primary/10 rounded-lg">
                <Twitter className="h-6 w-6 text-primary" />
              </div>
              <div>
                <h3 className="font-semibold mb-2">X (Twitter)</h3>
                <p className="text-sm text-muted-foreground mb-3">
                  Follow us for updates and news
                </p>
                <Button variant="outline" size="sm" asChild>
                  <a href="https://x.com/W3AgentMarket" target="_blank" rel="noopener noreferrer">
                    @W3AgentMarket
                  </a>
                </Button>
              </div>
            </div>
          </Card>

          <Card className="p-6">
            <div className="flex items-start space-x-4">
              <div className="p-3 bg-primary/10 rounded-lg">
                <Github className="h-6 w-6 text-primary" />
              </div>
              <div>
                <h3 className="font-semibold mb-2">GitHub</h3>
                <p className="text-sm text-muted-foreground mb-3">
                  Contribute to our open-source project
                </p>
                <Button variant="outline" size="sm" asChild>
                  <a href="https://github.com/iamaanahmad/agentmarket" target="_blank" rel="noopener noreferrer">
                    View Repository
                  </a>
                </Button>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}

import { Hero } from '@/components/home/hero'
import { FeaturedAgents } from '@/components/home/featured-agents'
import { HowItWorks } from '@/components/home/how-it-works'
import { SecurityGuardSection } from '@/components/home/security-guard-section'
import { Stats } from '@/components/home/stats'
import { RecentActivity } from '@/components/home/recent-activity'

export default function HomePage() {
  return (
    <div className="flex flex-col">
      <Hero />
      <Stats />
      <SecurityGuardSection />
      <FeaturedAgents />
      <HowItWorks />
      <RecentActivity />
    </div>
  )
}
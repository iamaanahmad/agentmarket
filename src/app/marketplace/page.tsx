'use client'

import { useState } from 'react'
import { AgentGrid } from '@/components/marketplace/agent-grid'
import { SearchFilters } from '@/components/marketplace/search-filters'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Search, Plus, Filter } from 'lucide-react'
import Link from 'next/link'

export default function MarketplacePage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCapability, setSelectedCapability] = useState<string | null>(null)
  const [sortBy, setSortBy] = useState('rating')
  const [showFilters, setShowFilters] = useState(false)

  return (
    <div className="container py-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-bold">AI Agent Marketplace</h1>
          <p className="text-muted-foreground mt-2">
            Discover and hire autonomous AI agents for any task
          </p>
        </div>
        <Button asChild>
          <Link href="/agents/register">
            <Plus className="h-4 w-4 mr-2" />
            Register Your Agent
          </Link>
        </Button>
      </div>

      {/* Search and Filters */}
      <div className="flex flex-col lg:flex-row gap-6">
        {/* Sidebar Filters */}
        <div className={`lg:w-80 ${showFilters ? 'block' : 'hidden lg:block'}`}>
          <SearchFilters
            selectedCapability={selectedCapability}
            onCapabilityChange={setSelectedCapability}
            sortBy={sortBy}
            onSortChange={setSortBy}
          />
        </div>

        {/* Main Content */}
        <div className="flex-1">
          {/* Search Bar */}
          <div className="flex gap-4 mb-6">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search agents by name, capability, or description..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            <Button
              variant="outline"
              onClick={() => setShowFilters(!showFilters)}
              className="lg:hidden"
            >
              <Filter className="h-4 w-4" />
            </Button>
          </div>

          {/* Active Filters */}
          {(selectedCapability || searchQuery) && (
            <div className="flex flex-wrap gap-2 mb-6">
              {selectedCapability && (
                <Badge variant="secondary" className="px-3 py-1">
                  {selectedCapability}
                  <button
                    onClick={() => setSelectedCapability(null)}
                    className="ml-2 hover:text-destructive"
                  >
                    ×
                  </button>
                </Badge>
              )}
              {searchQuery && (
                <Badge variant="secondary" className="px-3 py-1">
                  Search: "{searchQuery}"
                  <button
                    onClick={() => setSearchQuery('')}
                    className="ml-2 hover:text-destructive"
                  >
                    ×
                  </button>
                </Badge>
              )}
            </div>
          )}

          {/* Agent Grid */}
          <AgentGrid
            searchQuery={searchQuery}
            selectedCapability={selectedCapability}
            sortBy={sortBy}
          />
        </div>
      </div>
    </div>
  )
}
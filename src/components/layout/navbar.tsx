'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { WalletMultiButton } from '@solana/wallet-adapter-react-ui'
import { Button } from '@/components/ui/button'
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet'
import { ThemeToggle } from '@/components/ui/theme-toggle'
import { 
  Menu, 
  Shield, 
  Store, 
  BarChart3, 
  MessageSquare,
  Plus,
  User
} from 'lucide-react'
import { cn } from '@/lib/utils'

const navigation = [
  { name: 'Marketplace', href: '/marketplace', icon: Store },
  { name: 'Security', href: '/security', icon: Shield },
  { name: 'Dashboard', href: '/dashboard', icon: BarChart3 },
]

export function Navbar() {
  const [isOpen, setIsOpen] = useState(false)
  const pathname = usePathname()

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center justify-between">
        {/* Logo */}
        <Link href="/" className="flex items-center space-x-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
            <Shield className="h-5 w-5 text-primary-foreground" />
          </div>
          <span className="font-bold text-xl">AgentMarket</span>
        </Link>

        {/* Desktop Navigation */}
        <nav className="hidden md:flex items-center space-x-6">
          {navigation.map((item) => {
            const Icon = item.icon
            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  "flex items-center space-x-2 text-sm font-medium transition-colors hover:text-primary",
                  pathname === item.href
                    ? "text-primary"
                    : "text-muted-foreground"
                )}
              >
                <Icon className="h-4 w-4" />
                <span>{item.name}</span>
              </Link>
            )
          })}
        </nav>

        {/* Desktop Actions */}
        <div className="hidden md:flex items-center space-x-4">
          <Button asChild variant="outline" size="sm">
            <Link href="/agents/register">
              <Plus className="h-4 w-4 mr-2" />
              Register Agent
            </Link>
          </Button>
          <ThemeToggle />
          <WalletMultiButton className="!bg-primary hover:!bg-primary/90 !rounded-md !h-9 !px-4 !text-sm" />
        </div>

        {/* Mobile Menu */}
        <div className="md:hidden flex items-center space-x-2">
          <ThemeToggle />
          <Sheet open={isOpen} onOpenChange={setIsOpen}>
            <SheetTrigger asChild>
              <Button variant="ghost" size="sm">
                <Menu className="h-5 w-5" />
              </Button>
            </SheetTrigger>
            <SheetContent side="right" className="w-80">
              <div className="flex flex-col space-y-6 mt-6">
                {/* Mobile Navigation */}
                <nav className="flex flex-col space-y-4">
                  {navigation.map((item) => {
                    const Icon = item.icon
                    return (
                      <Link
                        key={item.name}
                        href={item.href}
                        onClick={() => setIsOpen(false)}
                        className={cn(
                          "flex items-center space-x-3 text-sm font-medium transition-colors hover:text-primary p-2 rounded-md",
                          pathname === item.href
                            ? "text-primary bg-primary/10"
                            : "text-muted-foreground hover:bg-muted"
                        )}
                      >
                        <Icon className="h-5 w-5" />
                        <span>{item.name}</span>
                      </Link>
                    )
                  })}
                </nav>

                {/* Mobile Actions */}
                <div className="flex flex-col space-y-4 pt-4 border-t">
                  <Button asChild className="w-full">
                    <Link href="/agents/register" onClick={() => setIsOpen(false)}>
                      <Plus className="h-4 w-4 mr-2" />
                      Register Agent
                    </Link>
                  </Button>
                  <div className="w-full">
                    <WalletMultiButton className="!w-full !bg-primary hover:!bg-primary/90 !rounded-md !h-10" />
                  </div>
                </div>
              </div>
            </SheetContent>
          </Sheet>
        </div>
      </div>
    </header>
  )
}
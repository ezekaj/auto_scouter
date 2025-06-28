import React from 'react'
import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  Search,
  Bell,
  AlertTriangle
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { Badge } from '@/components/ui/badge'

const navigation = [
  {
    name: 'Dashboard',
    href: '/dashboard',
    icon: LayoutDashboard,
  },
  {
    name: 'Vehicle Search',
    href: '/search',
    icon: Search,
  },
  {
    name: 'My Alerts',
    href: '/alerts',
    icon: AlertTriangle,
    badge: '5',
  },
  {
    name: 'Notifications',
    href: '/notifications',
    icon: Bell,
    badge: '3',
  },
]

export const Sidebar: React.FC = () => {
  return (
    <aside
      className="w-64 border-r bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60"
      aria-label="Main navigation"
    >
      <nav className="flex flex-col space-y-1 p-4" role="navigation">
        {navigation.map((item) => {
          const Icon = item.icon
          return (
            <NavLink
              key={item.name}
              to={item.href}
              className={({ isActive }) =>
                cn(
                  'flex items-center justify-between rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                  'focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2',
                  isActive
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                )
              }

            >
              <div className="flex items-center space-x-3">
                <Icon className="h-4 w-4" aria-hidden="true" />
                <span>{item.name}</span>
              </div>
              {item.badge && (
                <Badge variant="secondary" className="ml-auto">
                  {item.badge}
                </Badge>
              )}
            </NavLink>
          )
        })}
      </nav>
    </aside>
  )
}

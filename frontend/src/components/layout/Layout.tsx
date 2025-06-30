import React, { useState } from 'react'
import { Sidebar } from './Sidebar'
import { Header } from './Header'
import { MobileSidebar } from './MobileSidebar'

interface LayoutProps {
  children: React.ReactNode
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  return (
    <div className="mobile-viewport bg-background mobile-safe-area">
      <Header onMenuClick={() => setSidebarOpen(true)} />

      {/* Desktop Layout */}
      <div className="flex">
        {/* Desktop Sidebar - Hidden on mobile */}
        <div className="hidden lg:block">
          <Sidebar />
        </div>

        {/* Mobile Sidebar */}
        <MobileSidebar
          isOpen={sidebarOpen}
          onClose={() => setSidebarOpen(false)}
        />

        {/* Main Content */}
        <main className="flex-1 p-4 lg:p-6 min-h-[calc(100vh-4rem)] mobile-scroll">
          <div className="max-w-7xl mx-auto">
            {children}
          </div>
        </main>
      </div>
    </div>
  )
}

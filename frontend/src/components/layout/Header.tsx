import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { clsx } from 'clsx'
import { TrendingUp, BarChart3, FileText, Settings, Menu, X, Briefcase, PieChart, User, Search, BookOpen } from 'lucide-react'

const navigation = [
  { name: 'Dashboard', href: '/', icon: TrendingUp, current: false },
  { name: 'Portfolio', href: '/portfolio', icon: Briefcase, current: false },
  { name: 'Screening', href: '/screening', icon: Search, current: false },
  { name: 'Education', href: '/education', icon: BookOpen, current: false },
  { name: 'Charts', href: '/charts', icon: PieChart, current: false },
  { name: 'Reports', href: '/reports', icon: FileText, current: false },
  { name: 'Account', href: '/account', icon: User, current: false },
  { name: 'Settings', href: '/settings', icon: Settings, current: false },
]

export const Header: React.FC = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false)
  const location = useLocation()

  // Update current navigation item based on location
  const currentNavigation = navigation.map(item => ({
    ...item,
    current: location.pathname === item.href
  }))

  return (
    <header className="bg-white shadow-sm border-b border-slate-200">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 justify-between items-center">
          {/* Logo and brand */}
          <div className="flex items-center">
            <Link to="/" className="flex items-center space-x-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary-600">
                <BarChart3 className="h-5 w-5 text-white" />
              </div>
              <div className="hidden sm:block">
                <h1 className="text-xl font-bold text-slate-900">
                  Options Calculator
                </h1>
                <p className="text-xs text-slate-500 -mt-1">
                  Professional Analysis
                </p>
              </div>
            </Link>
          </div>

          {/* Desktop navigation */}
          <nav className="hidden md:flex space-x-8">
            {currentNavigation.map((item) => {
              const Icon = item.icon
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={clsx(
                    "inline-flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors",
                    item.current
                      ? "bg-primary-100 text-primary-700"
                      : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
                  )}
                >
                  <Icon className="h-4 w-4 mr-2" />
                  {item.name}
                </Link>
              )
            })}
          </nav>

          {/* Mobile menu button */}
          <div className="md:hidden">
            <button
              type="button"
              className="inline-flex items-center justify-center rounded-md p-2 text-slate-600 hover:bg-slate-100 hover:text-slate-900 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              aria-expanded="false"
            >
              <span className="sr-only">Open main menu</span>
              {mobileMenuOpen ? (
                <X className="h-6 w-6" />
              ) : (
                <Menu className="h-6 w-6" />
              )}
            </button>
          </div>

          {/* Status indicator */}
          <div className="hidden lg:flex items-center space-x-4">
            <div className="flex items-center space-x-2 text-sm">
              <div className="h-2 w-2 bg-success-500 rounded-full"></div>
              <span className="text-slate-600">System Online</span>
            </div>
          </div>
        </div>
      </div>

      {/* Mobile navigation menu */}
      {mobileMenuOpen && (
        <div className="md:hidden">
          <div className="space-y-1 px-2 pb-3 pt-2 sm:px-3 border-t border-slate-200 bg-slate-50">
            {currentNavigation.map((item) => {
              const Icon = item.icon
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={clsx(
                    "flex items-center px-3 py-2 text-base font-medium rounded-md transition-colors",
                    item.current
                      ? "bg-primary-100 text-primary-700"
                      : "text-slate-600 hover:text-slate-900 hover:bg-white"
                  )}
                  onClick={() => setMobileMenuOpen(false)}
                >
                  <Icon className="h-5 w-5 mr-3" />
                  {item.name}
                </Link>
              )
            })}
            
            {/* Mobile status indicator */}
            <div className="flex items-center px-3 py-2 text-sm text-slate-600">
              <div className="h-2 w-2 bg-success-500 rounded-full mr-3"></div>
              System Online
            </div>
          </div>
        </div>
      )}
    </header>
  )
}
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { ErrorBoundary } from './components/layout/ErrorBoundary'
import { Layout } from './components/layout/Layout'
import Dashboard from './components/Dashboard'

// Phase 3 Chart Pages (Lazy loaded for performance)
import { lazy, Suspense } from 'react'
import { LoadingSpinner } from './components/ui/LoadingSpinner'

// Phase 4 PWA Features
import { PWAProvider } from './contexts/PWAContext'
import InstallPrompt from './components/pwa/InstallPrompt'
import PWAStatus from './components/pwa/PWAStatus'

const ChartsPage = lazy(() => import('./pages/ChartsPage'))
const ComparisonPage = lazy(() => import('./pages/ComparisonPage'))
const PortfolioPage = lazy(() => import('./pages/PortfolioPage'))
const UserPage = lazy(() => import('./pages/UserPage'))
const ScreeningPage = lazy(() => import('./pages/ScreeningPage'))
const EducationPage = lazy(() => import('./pages/EducationPage'))

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      retry: 2,
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: 1,
    },
  },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <PWAProvider>
        <ErrorBoundary>
          <Router>
            <Layout>
              {/* Phase 4 PWA Install Prompt */}
              <div className="mb-4">
                <InstallPrompt variant="banner" />
              </div>

              <Routes>
                <Route path="/" element={<Dashboard />} />
                
                {/* Phase 5 Portfolio Management */}
                <Route 
                  path="/portfolio" 
                  element={
                    <Suspense fallback={
                      <div className="flex justify-center items-center h-64">
                        <LoadingSpinner size="lg" />
                      </div>
                    }>
                      <PortfolioPage />
                    </Suspense>
                  } 
                />
                
                {/* Phase 5 User Profile & Account Management */}
                <Route 
                  path="/account" 
                  element={
                    <Suspense fallback={
                      <div className="flex justify-center items-center h-64">
                        <LoadingSpinner size="lg" />
                      </div>
                    }>
                      <UserPage />
                    </Suspense>
                  } 
                />
                
                {/* Phase 5 Market Screening Interface */}
                <Route 
                  path="/screening" 
                  element={
                    <Suspense fallback={
                      <div className="flex justify-center items-center h-64">
                        <LoadingSpinner size="lg" />
                      </div>
                    }>
                      <ScreeningPage />
                    </Suspense>
                  } 
                />
                
                {/* Phase 5 Educational Content Browser */}
                <Route 
                  path="/education" 
                  element={
                    <Suspense fallback={
                      <div className="flex justify-center items-center h-64">
                        <LoadingSpinner size="lg" />
                      </div>
                    }>
                      <EducationPage />
                    </Suspense>
                  } 
                />
                
                {/* Phase 3 Chart Routes */}
                <Route 
                  path="/charts" 
                  element={
                    <Suspense fallback={
                      <div className="flex justify-center items-center h-64">
                        <LoadingSpinner size="lg" />
                      </div>
                    }>
                      <ChartsPage />
                    </Suspense>
                  } 
                />
                <Route 
                  path="/charts/comparison" 
                  element={
                    <Suspense fallback={
                      <div className="flex justify-center items-center h-64">
                        <LoadingSpinner size="lg" />
                      </div>
                    }>
                      <ComparisonPage />
                    </Suspense>
                  } 
                />
                
                <Route path="/reports" element={
                  <div className="text-center py-12">
                    <h2 className="text-2xl font-bold text-slate-900 mb-4">
                      Analysis Reports
                    </h2>
                    <p className="text-slate-600">
                      Historical analysis and performance reports will be available here.
                    </p>
                  </div>
                } />
                <Route path="/settings" element={
                  <div className="space-y-6">
                    <div className="text-center py-12">
                      <h2 className="text-2xl font-bold text-slate-900 mb-4">
                        Settings
                      </h2>
                      <p className="text-slate-600 mb-8">
                        Application configuration and preferences
                      </p>
                    </div>
                    
                    {/* Phase 4 PWA Settings */}
                    <div className="max-w-2xl mx-auto space-y-6">
                      <PWAStatus variant="full" showDetails={true} />
                      <InstallPrompt variant="card" showAlways={true} />
                    </div>
                  </div>
                } />
                {/* Catch all route */}
                <Route path="*" element={<Dashboard />} />
              </Routes>
            </Layout>
          </Router>
        </ErrorBoundary>
        <ReactQueryDevtools initialIsOpen={false} />
      </PWAProvider>
    </QueryClientProvider>
  )
}

export default App
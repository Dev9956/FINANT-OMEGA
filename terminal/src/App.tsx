// FININT OMEGA — Terminal App Shell

import { AuthProvider, useAuth, LoginScreen } from './components/auth/AuthProvider'
import { Header } from './components/layout/Header'
import { Sidebar } from './components/layout/Sidebar'
import { WorkspaceGrid } from './components/workspace/WorkspaceGrid'
import { CommandPalette } from './components/common/CommandPalette'

function TerminalApp() {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="h-screen w-screen flex items-center justify-center" style={{ background: 'var(--bg-primary)' }}>
        <div className="text-center">
          <div className="w-8 h-8 border-2 rounded-full animate-spin mx-auto mb-3"
            style={{ borderColor: 'var(--accent-blue)', borderTopColor: 'transparent' }} />
          <div className="text-xs" style={{ color: 'var(--text-muted)' }}>Loading FININT OMEGA...</div>
        </div>
      </div>
    )
  }

  if (!user) {
    return <LoginScreen />
  }

  return (
    <div className="h-screen w-screen flex flex-col overflow-hidden"
      style={{ background: 'var(--bg-primary)' }}>
      <Header />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-hidden">
          <WorkspaceGrid />
        </main>
      </div>
      <CommandPalette />
    </div>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <TerminalApp />
    </AuthProvider>
  )
}

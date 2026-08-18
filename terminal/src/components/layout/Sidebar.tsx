// FININT OMEGA — Terminal sidebar with workspace navigation

import {
  BarChart3, FlaskConical, Search, Shield, Newspaper,
  ChevronLeft, ChevronRight, Plus, Target, FileText, Plug
} from 'lucide-react'
import { useWorkspaceStore } from '../../store/workspace'

const NAV_ITEMS = [
  { id: 'markets', label: 'Markets', icon: BarChart3 },
  { id: 'research', label: 'Research', icon: FlaskConical },
  { id: 'screener', label: 'Screener', icon: Search },
  { id: 'intelligence', label: 'Intelligence', icon: Target },
  { id: 'risk-portfolio', label: 'Risk & Portfolio', icon: Shield },
  { id: 'news-alerts', label: 'News & Alerts', icon: Newspaper },
  { id: 'memo', label: 'Investment Memo', icon: FileText },
  { id: 'integrations', label: 'Integrations', icon: Plug },
]

export function Sidebar() {
  const {
    workspaces, activeWorkspaceId, sidebarCollapsed,
    setActiveWorkspace, toggleSidebar, addWorkspace,
  } = useWorkspaceStore()

  const handleAddWorkspace = () => {
    const name = prompt('Workspace name:')
    if (!name) return
    const icons = ['📊', '📈', '🔬', '💼', '🔍', '📰', '⚡', '🎯']
    const icon = icons[Math.floor(Math.random() * icons.length)]
    const ws = addWorkspace(name, icon)
    setActiveWorkspace(ws.id)
  }

  return (
    <aside
      className="flex flex-col border-r shrink-0 transition-all duration-200"
      style={{
        width: sidebarCollapsed ? 48 : 180,
        background: 'var(--bg-secondary)',
        borderColor: 'var(--border-primary)',
      }}
    >
      {/* Workspace tabs */}
      <div className="flex-1 overflow-y-auto py-2">
        <div className="px-2 mb-2">
          <span className="text-[10px] font-semibold uppercase tracking-wider"
            style={{ color: 'var(--text-muted)' }}>
            {sidebarCollapsed ? '—' : 'Workspaces'}
          </span>
        </div>

        {workspaces.map((ws) => (
          <button
            key={ws.id}
            onClick={() => setActiveWorkspace(ws.id)}
            className="w-full flex items-center gap-2 px-3 py-1.5 text-xs transition-colors"
            style={{
              background: ws.id === activeWorkspaceId ? 'var(--bg-tertiary)' : 'transparent',
              color: ws.id === activeWorkspaceId ? 'var(--text-primary)' : 'var(--text-secondary)',
              borderLeft: ws.id === activeWorkspaceId ? '2px solid var(--accent-blue)' : '2px solid transparent',
            }}
            title={ws.name}
          >
            <span className="text-sm">{ws.icon}</span>
            {!sidebarCollapsed && <span className="truncate">{ws.name}</span>}
          </button>
        ))}

        {!sidebarCollapsed && (
          <button
            onClick={handleAddWorkspace}
            className="w-full flex items-center gap-2 px-3 py-1.5 text-xs"
            style={{ color: 'var(--text-muted)' }}
          >
            <Plus size={14} />
            <span>New Workspace</span>
          </button>
        )}

        {/* Divider */}
        <div className="mx-3 my-3 border-t" style={{ borderColor: 'var(--border-primary)' }} />

        {/* Quick nav */}
        <div className="px-2 mb-2">
          <span className="text-[10px] font-semibold uppercase tracking-wider"
            style={{ color: 'var(--text-muted)' }}>
            {sidebarCollapsed ? '—' : 'Quick Access'}
          </span>
        </div>

        {NAV_ITEMS.map((item) => (
          <button
            key={item.id}
            onClick={() => setActiveWorkspace(item.id)}
            className="w-full flex items-center gap-2 px-3 py-1.5 text-xs transition-colors hover:bg-white/5"
            style={{
              color: item.id === activeWorkspaceId ? 'var(--accent-blue)' : 'var(--text-secondary)',
              background: item.id === activeWorkspaceId ? 'var(--bg-tertiary)' : 'transparent',
            }}
            title={item.label}
          >
            <item.icon size={14} />
            {!sidebarCollapsed && <span>{item.label}</span>}
          </button>
        ))}
      </div>

      {/* Collapse toggle */}
      <div className="p-2 border-t" style={{ borderColor: 'var(--border-primary)' }}>
        <button
          onClick={toggleSidebar}
          className="w-full flex items-center justify-center p-1 rounded hover:bg-white/5"
        >
          {sidebarCollapsed ? (
            <ChevronRight size={14} style={{ color: 'var(--text-muted)' }} />
          ) : (
            <ChevronLeft size={14} style={{ color: 'var(--text-muted)' }} />
          )}
        </button>
      </div>
    </aside>
  )
}

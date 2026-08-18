// FININT OMEGA — Terminal header with search bar + auth

import { useState, useRef, useEffect } from 'react'
import { Search, Bell, Command, LogOut } from 'lucide-react'
import { useWorkspaceStore } from '../../store/workspace'
import { useAuth } from '../auth/AuthProvider'

export function Header() {
  const [searchQuery, setSearchQuery] = useState('')
  const searchRef = useRef<HTMLInputElement>(null)
  const { setCommandPalette } = useWorkspaceStore()
  const { user, logout } = useAuth()

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        setCommandPalette(true)
      }
      if (e.key === '/' && document.activeElement !== searchRef.current) {
        e.preventDefault()
        searchRef.current?.focus()
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [setCommandPalette])

  return (
    <header className="h-11 flex items-center px-3 gap-3 border-b"
      style={{ background: 'var(--bg-secondary)', borderColor: 'var(--border-primary)' }}>

      {/* Logo */}
      <div className="flex items-center gap-2 shrink-0">
        <span className="text-sm font-bold tracking-wider"
          style={{ color: 'var(--accent-blue)' }}>
          FININT
        </span>
        <span className="text-sm font-light"
          style={{ color: 'var(--text-muted)' }}>
          OMEGA
        </span>
      </div>

      {/* Search */}
      <div className="flex-1 max-w-xl mx-auto">
        <div className="relative">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2"
            style={{ color: 'var(--text-muted)' }} />
          <input
            ref={searchRef}
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search companies, ask questions, screen..."
            className="w-full h-8 pl-9 pr-16 text-xs rounded-md border outline-none"
            style={{
              background: 'var(--bg-primary)',
              borderColor: 'var(--border-primary)',
              color: 'var(--text-primary)',
            }}
          />
          <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
            <span className="kbd">⌘</span>
            <span className="kbd">K</span>
          </div>
        </div>
      </div>

      {/* Right actions */}
      <div className="flex items-center gap-2 shrink-0">
        <button
          onClick={() => setCommandPalette(true)}
          className="p-1.5 rounded hover:bg-white/5"
          title="Command palette"
        >
          <Command size={16} style={{ color: 'var(--text-muted)' }} />
        </button>
        <button className="relative p-1.5 rounded hover:bg-white/5" title="Alerts">
          <Bell size={16} style={{ color: 'var(--text-muted)' }} />
          <span className="absolute top-0.5 right-0.5 w-2 h-2 rounded-full"
            style={{ background: 'var(--accent-red)' }} />
        </button>

        {user ? (
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1.5 px-2 py-1 rounded"
              style={{ background: 'var(--bg-tertiary)' }}>
              <div className="w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold"
                style={{ background: 'var(--accent-blue)', color: 'white' }}>
                {user.email[0].toUpperCase()}
              </div>
              <div className="hidden md:block">
                <div className="text-[10px] font-medium" style={{ color: 'var(--text-primary)' }}>
                  {user.email.split('@')[0]}
                </div>
                <div className="text-[9px]" style={{ color: 'var(--text-muted)' }}>
                  {user.role}
                </div>
              </div>
            </div>
            <button onClick={logout} className="p-1.5 rounded hover:bg-white/5" title="Logout">
              <LogOut size={14} style={{ color: 'var(--text-muted)' }} />
            </button>
          </div>
        ) : null}
      </div>
    </header>
  )
}

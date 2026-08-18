// FININT OMEGA — Command palette (Cmd+K)

import { useEffect, useState, useRef } from 'react'
import {
  Search, BarChart3, FlaskConical, Briefcase, Newspaper,
  Plus, Shield, Target, GitBranch, Cpu, Network, Bell, MessageSquare, FileText, Award, Plug
} from 'lucide-react'
import { useWorkspaceStore } from '../../store/workspace'
import type { PanelType } from '../../types'

interface CommandItem {
  id: string
  label: string
  description?: string
  icon: React.ElementType
  category: 'navigation' | 'panel' | 'action'
  action: () => void
}

export function CommandPalette() {
  const { commandPaletteOpen, setCommandPalette, addPanel, setActiveWorkspace } = useWorkspaceStore()
  const [query, setQuery] = useState('')
  const [selectedIndex, setSelectedIndex] = useState(0)
  const inputRef = useRef<HTMLInputElement>(null)

  const commands: CommandItem[] = [
    // Navigation
    { id: 'nav-markets', label: 'Go to Markets', icon: BarChart3, category: 'navigation', action: () => { setActiveWorkspace('markets'); setCommandPalette(false) } },
    { id: 'nav-research', label: 'Go to Research', icon: FlaskConical, category: 'navigation', action: () => { setActiveWorkspace('research'); setCommandPalette(false) } },
    { id: 'nav-portfolio', label: 'Go to Risk & Portfolio', icon: Briefcase, category: 'navigation', action: () => { setActiveWorkspace('risk-portfolio'); setCommandPalette(false) } },
    { id: 'nav-screener', label: 'Go to Screener', icon: Search, category: 'navigation', action: () => { setActiveWorkspace('screener'); setCommandPalette(false) } },
    { id: 'nav-intelligence', label: 'Go to Intelligence', icon: Target, category: 'navigation', action: () => { setActiveWorkspace('intelligence'); setCommandPalette(false) } },
    { id: 'nav-news', label: 'Go to News & Alerts', icon: Newspaper, category: 'navigation', action: () => { setActiveWorkspace('news-alerts'); setCommandPalette(false) } },
    { id: 'nav-memo', label: 'Go to Investment Memo', icon: FileText, category: 'navigation', action: () => { setActiveWorkspace('memo'); setCommandPalette(false) } },
    { id: 'nav-integrations', label: 'Go to Integrations', icon: Plug, category: 'navigation', action: () => { setActiveWorkspace('integrations'); setCommandPalette(false) } },

    // Add panels
    { id: 'add-market', label: 'Add Market Overview', icon: Plus, category: 'panel', action: () => { addPanel('market-overview' as PanelType, 'Market Overview'); setCommandPalette(false) } },
    { id: 'add-research', label: 'Add AI Research', icon: Plus, category: 'panel', action: () => { addPanel('research' as PanelType, 'AI Research'); setCommandPalette(false) } },
    { id: 'add-evidence', label: 'Add Evidence Explorer', icon: Plus, category: 'panel', action: () => { addPanel('evidence' as PanelType, 'Evidence'); setCommandPalette(false) } },
    { id: 'add-chart', label: 'Add Chart', icon: Plus, category: 'panel', action: () => { addPanel('chart' as PanelType, 'Chart', { symbol: 'SPY' }); setCommandPalette(false) } },
    { id: 'add-news', label: 'Add News Feed', icon: Plus, category: 'panel', action: () => { addPanel('news' as PanelType, 'News'); setCommandPalette(false) } },
    { id: 'add-alerts', label: 'Add Alerts Panel', icon: Bell, category: 'panel', action: () => { addPanel('alerts' as PanelType, 'Alerts'); setCommandPalette(false) } },
    { id: 'add-thesis', label: 'Add Thesis Studio', icon: Target, category: 'panel', action: () => { addPanel('thesis' as PanelType, 'Thesis Studio', { symbol: 'NVDA' }); setCommandPalette(false) } },
    { id: 'add-screener', label: 'Add Screener', icon: Search, category: 'panel', action: () => { addPanel('screener' as PanelType, 'Screener'); setCommandPalette(false) } },
    { id: 'add-portfolio', label: 'Add Portfolio', icon: Plus, category: 'panel', action: () => { addPanel('portfolio' as PanelType, 'Portfolio'); setCommandPalette(false) } },
    { id: 'add-risk', label: 'Add Risk Center', icon: Shield, category: 'panel', action: () => { addPanel('risk' as PanelType, 'Risk Center'); setCommandPalette(false) } },
    { id: 'add-company', label: 'Add Company Intelligence', icon: Plus, category: 'panel', action: () => { addPanel('company-intelligence' as PanelType, 'Company Intelligence', { symbol: 'NVDA' }); setCommandPalette(false) } },
    { id: 'add-scenario', label: 'Add Scenario Lab', icon: GitBranch, category: 'panel', action: () => { addPanel('scenario' as PanelType, 'Scenario Lab', { symbol: 'NVDA' }); setCommandPalette(false) } },
    { id: 'add-ai-chat', label: 'Add AI Assistant', icon: MessageSquare, category: 'panel', action: () => { addPanel('ai-chat' as PanelType, 'AI Assistant'); setCommandPalette(false) } },
    { id: 'add-cross-entity', label: 'Add Cross-Entity Analysis', icon: Network, category: 'panel', action: () => { addPanel('cross-entity' as PanelType, 'Cross-Entity'); setCommandPalette(false) } },
    { id: 'add-predictions', label: 'Add Predictions Tracker', icon: Target, category: 'panel', action: () => { addPanel('predictions' as PanelType, 'Predictions'); setCommandPalette(false) } },
    { id: 'add-digital-twin', label: 'Add Digital Twin', icon: Cpu, category: 'panel', action: () => { addPanel('digital-twin' as PanelType, 'Digital Twin'); setCommandPalette(false) } },
    { id: 'add-quality', label: 'Add Quality Score', icon: Award, category: 'panel', action: () => { addPanel('quality' as PanelType, 'Quality Score'); setCommandPalette(false) } },
    { id: 'add-memo', label: 'Add Investment Memo', icon: FileText, category: 'panel', action: () => { addPanel('memo' as PanelType, 'Investment Memo', { symbol: 'NVDA' }); setCommandPalette(false) } },
    { id: 'add-integrations', label: 'Add Integration Center', icon: Plug, category: 'panel', action: () => { addPanel('integrations' as PanelType, 'Integration Center'); setCommandPalette(false) } },
  ]

  const filtered = commands.filter(cmd =>
    cmd.label.toLowerCase().includes(query.toLowerCase()) ||
    cmd.description?.toLowerCase().includes(query.toLowerCase())
  )

  useEffect(() => {
    if (commandPaletteOpen) {
      setQuery('')
      setSelectedIndex(0)
      setTimeout(() => inputRef.current?.focus(), 50)
    }
  }, [commandPaletteOpen])

  useEffect(() => {
    setSelectedIndex(0)
  }, [query])

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (!commandPaletteOpen) return

      if (e.key === 'Escape') {
        setCommandPalette(false)
      } else if (e.key === 'ArrowDown') {
        e.preventDefault()
        setSelectedIndex(i => Math.min(i + 1, filtered.length - 1))
      } else if (e.key === 'ArrowUp') {
        e.preventDefault()
        setSelectedIndex(i => Math.max(i - 1, 0))
      } else if (e.key === 'Enter' && filtered[selectedIndex]) {
        filtered[selectedIndex].action()
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [commandPaletteOpen, filtered, selectedIndex, setCommandPalette])

  if (!commandPaletteOpen) return null

  return (
    <div className="command-palette-overlay" onClick={() => setCommandPalette(false)}>
      <div className="command-palette" onClick={(e) => e.stopPropagation()}>
        {/* Search input */}
        <div className="flex items-center gap-2 px-4 py-3 border-b"
          style={{ borderColor: 'var(--border-primary)' }}>
          <Search size={16} style={{ color: 'var(--text-muted)' }} />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type a command or search..."
            className="flex-1 bg-transparent outline-none text-sm"
            style={{ color: 'var(--text-primary)' }}
          />
          <span className="kbd" style={{ fontSize: '9px' }}>ESC</span>
        </div>

        {/* Results */}
        <div className="overflow-y-auto max-h-[320px]">
          {filtered.length === 0 && (
            <div className="px-4 py-6 text-center text-xs" style={{ color: 'var(--text-muted)' }}>
              No commands found
            </div>
          )}

          {filtered.map((cmd, i) => {
            const Icon = cmd.icon
            return (
              <button
                key={cmd.id}
                onClick={cmd.action}
                className="w-full flex items-center gap-3 px-4 py-2 text-left text-xs transition-colors"
                style={{
                  background: i === selectedIndex ? 'var(--bg-tertiary)' : 'transparent',
                  color: 'var(--text-primary)',
                }}
                onMouseEnter={() => setSelectedIndex(i)}
              >
                <Icon size={14} style={{ color: 'var(--text-muted)' }} />
                <div>
                  <div>{cmd.label}</div>
                  {cmd.description && (
                    <div className="text-[10px]" style={{ color: 'var(--text-muted)' }}>
                      {cmd.description}
                    </div>
                  )}
                </div>
                <span className="ml-auto text-[10px] px-1.5 py-0.5 rounded"
                  style={{ background: 'var(--bg-primary)', color: 'var(--text-muted)' }}>
                  {cmd.category}
                </span>
              </button>
            )
          })}
        </div>
      </div>
    </div>
  )
}

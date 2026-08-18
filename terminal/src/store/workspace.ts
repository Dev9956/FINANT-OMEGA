// FININT OMEGA — Workspace state management (Zustand)

import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { Workspace, Panel, PanelType } from '../types'

// ── Default workspaces ──

const DEFAULT_WORKSPACES: Workspace[] = [
  {
    id: 'markets',
    name: 'Markets',
    icon: '📈',
    layout: [
      { id: 'p1', type: 'market-overview', title: 'Market Overview', props: {}, position: { x: 0, y: 0, w: 12, h: 4 } },
      { id: 'p2', type: 'chart', title: 'Chart', props: { symbol: 'SPY' }, position: { x: 0, y: 4, w: 8, h: 6 } },
      { id: 'p3', type: 'news', title: 'News', props: {}, position: { x: 8, y: 4, w: 4, h: 6 } },
    ],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  },
  {
    id: 'research',
    name: 'Research',
    icon: '🔬',
    layout: [
      { id: 'p1', type: 'research', title: 'AI Research', props: {}, position: { x: 0, y: 0, w: 8, h: 8 } },
      { id: 'p2', type: 'evidence', title: 'Evidence', props: {}, position: { x: 8, y: 0, w: 4, h: 8 } },
      { id: 'p3', type: 'thesis', title: 'Thesis', props: {}, position: { x: 0, y: 8, w: 6, h: 4 } },
    ],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  },
  {
    id: 'portfolio',
    name: 'Portfolio',
    icon: '💼',
    layout: [
      { id: 'p1', type: 'portfolio', title: 'Positions', props: {}, position: { x: 0, y: 0, w: 8, h: 6 } },
      { id: 'p2', type: 'risk', title: 'Risk', props: {}, position: { x: 8, y: 0, w: 4, h: 6 } },
      { id: 'p3', type: 'chart', title: 'Chart', props: { symbol: 'SPY' }, position: { x: 0, y: 6, w: 12, h: 6 } },
    ],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  },
  {
    id: 'screener',
    name: 'Screener',
    icon: '🔍',
    layout: [
      { id: 'p1', type: 'screener', title: 'Screener', props: {}, position: { x: 0, y: 0, w: 12, h: 12 } },
    ],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  },
  {
    id: 'intelligence',
    name: 'Intelligence',
    icon: '🧠',
    layout: [
      { id: 'p1', type: 'thesis', title: 'Thesis Studio', props: { symbol: 'NVDA' }, position: { x: 0, y: 0, w: 6, h: 6 } },
      { id: 'p2', type: 'scenario', title: 'Scenario Lab', props: { symbol: 'NVDA' }, position: { x: 6, y: 0, w: 6, h: 6 } },
      { id: 'p3', type: 'cross-entity', title: 'Cross-Entity', props: {}, position: { x: 0, y: 6, w: 6, h: 6 } },
      { id: 'p4', type: 'predictions', title: 'Predictions', props: {}, position: { x: 6, y: 6, w: 6, h: 6 } },
    ],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  },
  {
    id: 'risk-portfolio',
    name: 'Risk & Portfolio',
    icon: '🛡️',
    layout: [
      { id: 'p1', type: 'portfolio', title: 'Positions', props: {}, position: { x: 0, y: 0, w: 8, h: 6 } },
      { id: 'p2', type: 'risk', title: 'Risk Center', props: {}, position: { x: 8, y: 0, w: 4, h: 6 } },
      { id: 'p3', type: 'digital-twin', title: 'Digital Twin', props: {}, position: { x: 0, y: 6, w: 6, h: 6 } },
      { id: 'p4', type: 'quality', title: 'Quality Score', props: {}, position: { x: 6, y: 6, w: 6, h: 6 } },
    ],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  },
  {
    id: 'news-alerts',
    name: 'News & Alerts',
    icon: '🔔',
    layout: [
      { id: 'p1', type: 'news', title: 'News Feed', props: {}, position: { x: 0, y: 0, w: 8, h: 8 } },
      { id: 'p2', type: 'alerts', title: 'Alerts', props: {}, position: { x: 8, y: 0, w: 4, h: 8 } },
      { id: 'p3', type: 'ai-chat', title: 'AI Assistant', props: {}, position: { x: 0, y: 8, w: 12, h: 4 } },
    ],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  },
  {
    id: 'memo',
    name: 'Investment Memo',
    icon: '📝',
    layout: [
      { id: 'p1', type: 'memo', title: 'Investment Memo', props: { symbol: 'NVDA' }, position: { x: 0, y: 0, w: 8, h: 12 } },
      { id: 'p2', type: 'evidence', title: 'Evidence', props: {}, position: { x: 8, y: 0, w: 4, h: 12 } },
    ],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  },
  {
    id: 'integrations',
    name: 'Integrations',
    icon: '🔌',
    layout: [
      { id: 'p1', type: 'integrations', title: 'Integration Center', props: {}, position: { x: 0, y: 0, w: 12, h: 12 } },
    ],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  },
]

// ── Store types ──

interface WorkspaceStore {
  workspaces: Workspace[]
  activeWorkspaceId: string
  sidebarCollapsed: boolean
  commandPaletteOpen: boolean
  selectedSymbol: string | null

  // Actions
  getActiveWorkspace: () => Workspace
  setActiveWorkspace: (id: string) => void
  addWorkspace: (name: string, icon: string) => Workspace
  removeWorkspace: (id: string) => void
  renameWorkspace: (id: string, name: string) => void
  addPanel: (type: PanelType, title: string, props?: Record<string, unknown>) => void
  removePanel: (panelId: string) => void
  updatePanel: (panelId: string, updates: Partial<Panel>) => void
  setPanelProps: (panelId: string, props: Record<string, unknown>) => void
  toggleSidebar: () => void
  setCommandPalette: (open: boolean) => void
  setSelectedSymbol: (symbol: string | null) => void
}

// ── Store ──

export const useWorkspaceStore = create<WorkspaceStore>()(
  persist(
    (set, get) => ({
      workspaces: DEFAULT_WORKSPACES,
      activeWorkspaceId: 'markets',
      sidebarCollapsed: false,
      commandPaletteOpen: false,
      selectedSymbol: null,

      getActiveWorkspace: () => {
        const state = get()
        return state.workspaces.find(w => w.id === state.activeWorkspaceId) || state.workspaces[0]
      },

      setActiveWorkspace: (id) => set({ activeWorkspaceId: id }),

      addWorkspace: (name, icon) => {
        const ws: Workspace = {
          id: crypto.randomUUID(),
          name,
          icon,
          layout: [],
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        }
        set((s) => ({ workspaces: [...s.workspaces, ws] }))
        return ws
      },

      removeWorkspace: (id) => set((s) => ({
        workspaces: s.workspaces.filter(w => w.id !== id),
        activeWorkspaceId: s.activeWorkspaceId === id ? s.workspaces[0]?.id || '' : s.activeWorkspaceId,
      })),

      renameWorkspace: (id, name) => set((s) => ({
        workspaces: s.workspaces.map(w => w.id === id ? { ...w, name, updatedAt: new Date().toISOString() } : w),
      })),

      addPanel: (type, title, props = {}) => {
        const ws = get().getActiveWorkspace()
        const maxY = ws.layout.reduce((max, p) => Math.max(max, p.position.y + p.position.h), 0)
        const panel: Panel = {
          id: crypto.randomUUID(),
          type,
          title,
          props,
          position: { x: 0, y: maxY, w: 6, h: 4 },
        }
        set((s) => ({
          workspaces: s.workspaces.map(w =>
            w.id === s.activeWorkspaceId
              ? { ...w, layout: [...w.layout, panel], updatedAt: new Date().toISOString() }
              : w
          ),
        }))
      },

      removePanel: (panelId) => set((s) => ({
        workspaces: s.workspaces.map(w =>
          w.id === s.activeWorkspaceId
            ? { ...w, layout: w.layout.filter(p => p.id !== panelId), updatedAt: new Date().toISOString() }
            : w
        ),
      })),

      updatePanel: (panelId, updates) => set((s) => ({
        workspaces: s.workspaces.map(w =>
          w.id === s.activeWorkspaceId
            ? {
                ...w,
                layout: w.layout.map(p => p.id === panelId ? { ...p, ...updates } : p),
                updatedAt: new Date().toISOString(),
              }
            : w
        ),
      })),

      setPanelProps: (panelId, props) => set((s) => ({
        workspaces: s.workspaces.map(w =>
          w.id === s.activeWorkspaceId
            ? {
                ...w,
                layout: w.layout.map(p => p.id === panelId ? { ...p, props: { ...p.props, ...props } } : p),
                updatedAt: new Date().toISOString(),
              }
            : w
        ),
      })),

      toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
      setCommandPalette: (open) => set({ commandPaletteOpen: open }),
      setSelectedSymbol: (symbol) => set({ selectedSymbol: symbol }),
    }),
    {
      name: 'finint-workspace',
      partialize: (state) => ({
        workspaces: state.workspaces,
        activeWorkspaceId: state.activeWorkspaceId,
        sidebarCollapsed: state.sidebarCollapsed,
      }),
    }
  )
)

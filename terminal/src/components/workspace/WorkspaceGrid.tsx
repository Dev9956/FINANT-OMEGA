// FININT OMEGA — Workspace grid renderer

import React from 'react'
import { useWorkspaceStore } from '../../store/workspace'
import { MarketOverview } from '../market/MarketOverview'
import { ResearchPanel } from '../research/ResearchPanel'
import { EvidencePanel } from '../research/EvidencePanel'
import { CompanyIntelligence } from '../company/CompanyIntelligence'
import { ScreenerPanel } from '../screener/ScreenerPanel'
import { PortfolioPanel } from '../portfolio/PortfolioPanel'
import { RiskPanel } from '../risk/RiskPanel'
import { ThesisPanel } from '../research/ThesisPanel'
import { ScenarioPanel } from '../scenario/ScenarioPanel'
import { NewsAlertsPanel } from '../news/NewsAlertsPanel'
import { AIChatPanel } from '../common/AIChatPanel'
import { ChartPanel } from '../chart/ChartPanel'
import { CrossEntityPanel } from '../intelligence/CrossEntityPanel'
import { PredictionsPanel } from '../intelligence/PredictionsPanel'
import { DigitalTwinPanel } from '../intelligence/DigitalTwinPanel'
import { QualityPanel } from '../intelligence/QualityPanel'
import { MemoPanel } from '../intelligence/MemoPanel'
import { DebatePanel } from '../intelligence/DebatePanel'
import { IntegrationCenter } from '../integrations/IntegrationCenter'
import type { Panel } from '../../types'
import { X, Maximize2, Minimize2 } from 'lucide-react'
import { useState } from 'react'

function PanelWrapper({
  panel,
  children,
}: {
  panel: Panel
  children: React.ReactNode
}) {
  const { removePanel } = useWorkspaceStore()
  const [maximized, setMaximized] = useState(false)

  return (
    <div
      className={`terminal-panel flex flex-col overflow-hidden ${maximized ? 'fixed inset-11 z-40' : ''}`}
      style={{ height: '100%' }}
    >
      {/* Panel header */}
      <div
        className="flex items-center justify-between px-3 py-1.5 border-b shrink-0 cursor-move"
        style={{ borderColor: 'var(--border-primary)', background: 'var(--bg-secondary)' }}
      >
        <span className="text-[11px] font-medium" style={{ color: 'var(--text-secondary)' }}>
          {panel.title}
        </span>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setMaximized(!maximized)}
            className="p-0.5 rounded hover:bg-white/10"
            title={maximized ? 'Restore' : 'Maximize'}
          >
            {maximized ? (
              <Minimize2 size={12} style={{ color: 'var(--text-muted)' }} />
            ) : (
              <Maximize2 size={12} style={{ color: 'var(--text-muted)' }} />
            )}
          </button>
          <button
            onClick={() => removePanel(panel.id)}
            className="p-0.5 rounded hover:bg-white/10"
            title="Close"
          >
            <X size={12} style={{ color: 'var(--text-muted)' }} />
          </button>
        </div>
      </div>

      {/* Panel content */}
      <div className="flex-1 min-h-0 min-w-0 overflow-hidden relative">
        {children}
      </div>
    </div>
  )
}

function PanelContent({ panel }: { panel: Panel }): React.ReactNode {
  switch (panel.type) {
    case 'market-overview':
      return <MarketOverview />
    case 'company-intelligence':
      return <CompanyIntelligence symbol={String(panel.props.symbol || 'NVDA')} />
    case 'research':
      return <ResearchPanel />
    case 'evidence':
      return <EvidencePanel />
    case 'screener':
      return <ScreenerPanel />
    case 'portfolio':
      return <PortfolioPanel />
    case 'risk':
      return <RiskPanel />
    case 'thesis':
      return <ThesisPanel />
    case 'scenario':
      return <ScenarioPanel />
    case 'news':
      return <NewsAlertsPanel />
    case 'alerts':
      return <NewsAlertsPanel />
    case 'ai-chat':
      return <AIChatPanel />
    case 'cross-entity':
      return <CrossEntityPanel />
    case 'predictions':
      return <PredictionsPanel />
    case 'digital-twin':
      return <DigitalTwinPanel />
    case 'quality':
      return <QualityPanel />
    case 'memo':
      return <MemoPanel />
    case 'debate':
      return <DebatePanel />
    case 'integrations':
      return <IntegrationCenter />
    case 'chart':
      return <ChartPanel symbol={String(panel.props.symbol || 'SPY')} />
    default:
      return (
        <div className="h-full flex items-center justify-center" style={{ color: 'var(--text-muted)' }}>
          <div className="text-xs">Panel: {panel.type}</div>
        </div>
      )
  }
}

export function WorkspaceGrid() {
  const { getActiveWorkspace } = useWorkspaceStore()
  const workspace = getActiveWorkspace()

  if (!workspace || workspace.layout.length === 0) {
    return (
      <div className="h-full flex items-center justify-center" style={{ color: 'var(--text-muted)' }}>
        <div className="text-center">
          <div className="text-4xl mb-3">📊</div>
          <div className="text-sm mb-1">Empty Workspace</div>
          <div className="text-xs">Add panels from the sidebar or command palette</div>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full p-1 overflow-y-auto">
      <div className="grid grid-cols-12 gap-1 auto-rows-min" style={{ minHeight: '100%' }}>
        {workspace.layout.map((panel) => (
          <div
            key={panel.id}
            style={{
              gridColumn: `span ${Math.min(panel.position.w, 12)}`,
              gridRow: `span ${panel.position.h}`,
              minHeight: `${panel.position.h * 60}px`,
            }}
          >
            <PanelWrapper panel={panel}>
              <PanelContent panel={panel} />
            </PanelWrapper>
          </div>
        ))}
      </div>
    </div>
  )
}

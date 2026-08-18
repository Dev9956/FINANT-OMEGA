// FININT OMEGA — Evidence Explorer — wired to real evidence graph API

import { CheckCircle, XCircle, ChevronDown, RefreshCw, Search } from 'lucide-react'
import { useState, useEffect, useCallback } from 'react'
import { evidenceGraph } from '../../api/client'

interface EvidenceNode {
  node_id: string
  node_type: string
  label: string
  content: string
  confidence: number
  source_id: string
  created_at: string
}

interface GraphStats {
  total_nodes: number
  total_edges: number
  node_types: Record<string, number>
}

function EvidenceRow({ node }: { node: EvidenceNode }) {
  const [expanded, setExpanded] = useState(false)
  const isSupporting = node.node_type === 'claim' || node.node_type === 'fact'
  const Icon = isSupporting ? CheckCircle : XCircle
  const color = node.confidence > 0.7 ? 'var(--accent-green)' : node.confidence > 0.4 ? 'var(--accent-yellow)' : 'var(--accent-red)'

  return (
    <div
      className="border-b cursor-pointer transition-colors hover:bg-white/[0.02]"
      style={{ borderColor: 'var(--border-primary)' }}
      onClick={() => setExpanded(!expanded)}
    >
      <div className="flex items-start gap-2 p-2">
        <Icon size={14} className="shrink-0 mt-0.5" style={{ color }} />
        <div className="flex-1 min-w-0">
          <div className="text-xs" style={{ color: 'var(--text-primary)' }}>
            {node.label}
          </div>
          <div className="flex items-center gap-2 mt-1">
            <span className="text-[10px] px-1.5 py-0.5 rounded"
              style={{
                background: color + '15',
                color,
              }}>
              {node.node_type}
            </span>
            {node.source_id && (
              <span className="text-[10px]" style={{ color: 'var(--text-muted)' }}>
                {node.source_id}
              </span>
            )}
            <span className="text-[10px]" style={{ color: 'var(--text-muted)' }}>
              ({Math.round(node.confidence * 100)}%)
            </span>
          </div>
        </div>
        <ChevronDown
          size={14}
          className="shrink-0 transition-transform"
          style={{
            color: 'var(--text-muted)',
            transform: expanded ? 'rotate(180deg)' : 'rotate(0)',
          }}
        />
      </div>

      {expanded && (
        <div className="px-2 pb-2 pl-8">
          <div className="text-[10px] p-2 rounded" style={{ background: 'var(--bg-primary)' }}>
            <div className="mb-1 font-medium" style={{ color: 'var(--text-secondary)' }}>
              Detail
            </div>
            <div style={{ color: 'var(--text-muted)' }}>
              {node.content || 'No content'}
            </div>
            <div className="mt-1" style={{ color: 'var(--text-muted)' }}>
              ID: {node.node_id}
            </div>
            {node.created_at && (
              <div style={{ color: 'var(--text-muted)' }}>
                Created: {new Date(node.created_at).toLocaleString()}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export function EvidencePanel() {
  const [nodes, setNodes] = useState<EvidenceNode[]>([])
  const [stats, setStats] = useState<GraphStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<EvidenceNode[]>([])

  const fetchNodes = useCallback(async () => {
    setLoading(true)
    try {
      const s = await evidenceGraph.getStats() as any
      setStats({ total_nodes: s.node_count || 0, total_edges: s.edge_count || 0, node_types: {} })

      if ((s.node_count || 0) > 0) {
        const results = await evidenceGraph.search('') as any
        if (results && results.nodes) {
          setNodes(results.nodes)
        }
      }
    } catch {} finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchNodes()
  }, [fetchNodes])

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      setSearchResults([])
      return
    }
    try {
      const results = await evidenceGraph.search(searchQuery) as any
      setSearchResults(results?.nodes || [])
    } catch {
      setSearchResults([])
    }
  }

  const displayNodes = searchResults.length > 0 ? searchResults : nodes
  const supporting = displayNodes.filter(n => n.node_type === 'claim' || n.node_type === 'fact')
  const contradicting = displayNodes.filter(n => n.node_type === 'contradiction' || n.node_type === 'conflict')

  return (
    <div className="h-full flex flex-col">
      {/* Header with stats and search */}
      <div className="p-2 border-b" style={{ borderColor: 'var(--border-primary)' }}>
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-3 text-[10px]" style={{ color: 'var(--text-muted)' }}>
            <span>{stats?.total_nodes || 0} nodes</span>
            <span>{stats?.total_edges || 0} edges</span>
            <span className="flex items-center gap-1">
              <CheckCircle size={10} style={{ color: 'var(--accent-green)' }} />
              {supporting.length} supporting
            </span>
            <span className="flex items-center gap-1">
              <XCircle size={10} style={{ color: 'var(--accent-red)' }} />
              {contradicting.length} contradicting
            </span>
          </div>
          <button onClick={fetchNodes} className="p-1 rounded hover:bg-white/5" style={{ color: 'var(--text-muted)' }}>
            <RefreshCw size={12} />
          </button>
        </div>
        <div className="flex items-center gap-1">
          <Search size={12} style={{ color: 'var(--text-muted)' }} />
          <input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="Search evidence..."
            className="flex-1 h-7 px-2 text-[10px] rounded border outline-none"
            style={{ background: 'var(--bg-primary)', borderColor: 'var(--border-primary)', color: 'var(--text-primary)' }}
          />
        </div>
      </div>

      {/* Node list */}
      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="flex items-center justify-center h-24" style={{ color: 'var(--text-muted)' }}>
            <RefreshCw size={14} className="animate-spin mr-2" /> Loading evidence graph...
          </div>
        ) : displayNodes.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-24 text-center" style={{ color: 'var(--text-muted)' }}>
            <div className="text-xs mb-1">No evidence in graph yet</div>
            <div className="text-[10px]">Run a research query to populate the evidence graph</div>
          </div>
        ) : (
          <div>
            {supporting.length > 0 && (
              <div className="mb-2">
                <div className="text-[10px] font-semibold uppercase px-2 py-1"
                  style={{ color: 'var(--accent-green)' }}>
                  Supporting ({supporting.length})
                </div>
                <div className="rounded-md border mx-2" style={{ borderColor: 'var(--border-primary)' }}>
                  {supporting.map(n => <EvidenceRow key={n.node_id} node={n} />)}
                </div>
              </div>
            )}
            {contradicting.length > 0 && (
              <div>
                <div className="text-[10px] font-semibold uppercase px-2 py-1"
                  style={{ color: 'var(--accent-red)' }}>
                  Contradicting ({contradicting.length})
                </div>
                <div className="rounded-md border mx-2" style={{ borderColor: 'var(--border-primary)' }}>
                  {contradicting.map(n => <EvidenceRow key={n.node_id} node={n} />)}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

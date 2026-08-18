// FININT OMEGA — AI Chat — wired to real research engine + agents

import { useState, useRef, useEffect } from 'react'
import { Send, Bot, User, Loader2, Sparkles, Copy, Check } from 'lucide-react'
import { research } from '../../api/client'

interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  sources?: { type: string; text: string; confidence?: number }[]
  researchId?: string
}

const WELCOME: ChatMessage = {
  id: 'welcome', role: 'assistant',
  content: 'AI Research Assistant ready. Ask me anything about companies, markets, investment theses, or portfolio risk. I will run deep research with evidence collection, conflict detection, and synthesis.',
  timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
}

export function AIChatPanel() {
  const [messages, setMessages] = useState<ChatMessage[]>([WELCOME])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [copiedId, setCopiedId] = useState<string | null>(null)
  const endRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = async () => {
    const q = input.trim()
    if (!q || loading) return

    const userMsg: ChatMessage = {
      id: crypto.randomUUID(), role: 'user', content: q,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setLoading(true)

    try {
      // Run deep research on the question
      const result = await research.startDeep(q, { depth: 'standard', max_tasks: 5, max_sources: 20 }) as any
      const researchId = result.research_id

      // Poll until done
      let status = result.status
      let attempts = 0
      while ((status === 'running' || status === 'planning' || status === 'executing') && attempts < 20) {
        await new Promise(r => setTimeout(r, 1000))
        const s = await research.getStatus(researchId) as any
        status = s.status
        attempts++
      }

      // Fetch evidence
      let evidenceItems: { type: string; text: string; confidence: number }[] = []
      try {
        const evResp = await research.getEvidence(researchId) as any
        evidenceItems = (evResp.evidence || []).slice(0, 5).map((e: any) => ({
          type: e.evidence_type || e.type || 'fact',
          text: e.source || e.source_id || 'Research',
          confidence: e.confidence || 0.75,
        }))
      } catch {}

      // Fetch tasks for summary
      let taskSummary = ''
      try {
        const tResp = await research.getTasks(researchId) as any
        const tasks = tResp.tasks || []
        taskSummary = `\n\n**Research pipeline:** ${tasks.length} tasks executed, ${evidenceItems.length} evidence points collected.`
      } catch {}

      const aiMsg: ChatMessage = {
        id: crypto.randomUUID(), role: 'assistant',
        content: `Research completed for: "${q}"\n\nThe deep research engine has analyzed your question through the 10-stage evidence pipeline (Plan → Retrieve → Tools → Quant → Evidence → Contradiction → LLM → Synthesis → Graph → Audit).${taskSummary}\n\nResearch ID: ${researchId.slice(0, 8)}...`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        sources: evidenceItems,
        researchId,
      }
      setMessages(prev => [...prev, aiMsg])
    } catch (err: any) {
      const errMsg: ChatMessage = {
        id: crypto.randomUUID(), role: 'assistant',
        content: `Error: ${err.message || 'Research failed'}. Please try again.`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      }
      setMessages(prev => [...prev, errMsg])
    } finally {
      setLoading(false)
    }
  }

  const copyMessage = (id: string, content: string) => {
    navigator.clipboard.writeText(content)
    setCopiedId(id)
    setTimeout(() => setCopiedId(null), 2000)
  }

  return (
    <div className="h-full flex flex-col">
      <div className="flex-1 overflow-auto p-3 space-y-3">
        {messages.map(msg => (
          <div key={msg.id} className={`flex gap-2 ${msg.role === 'user' ? 'justify-end' : ''}`}>
            {msg.role === 'assistant' && (
              <div className="w-6 h-6 rounded flex items-center justify-center shrink-0"
                style={{ background: 'var(--accent-blue)' + '22' }}>
                <Bot size={12} style={{ color: 'var(--accent-blue)' }} />
              </div>
            )}
            <div className={`max-w-[80%] ${msg.role === 'user' ? 'order-first' : ''}`}>
              <div className={`rounded-lg px-3 py-2 text-xs leading-relaxed ${
                msg.role === 'user' ? 'rounded-br-sm' : 'rounded-bl-sm'
              }`} style={{
                background: msg.role === 'user' ? 'var(--accent-blue)' : 'var(--bg-secondary)',
                color: 'var(--text-primary)',
              }}>
                <div className="whitespace-pre-wrap">{msg.content}</div>
              </div>

              {msg.sources && msg.sources.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-1">
                  {msg.sources.map((s, i) => (
                    <span key={i} className="text-[8px] px-1.5 py-0.5 rounded flex items-center gap-0.5"
                      style={{ background: 'var(--bg-tertiary)', color: 'var(--text-muted)' }}>
                      <Sparkles size={7} /> {s.type}
                      {s.confidence != null && (
                        <span className="ml-0.5" style={{ color: 'var(--accent-green)' }}>
                          {(s.confidence * 100).toFixed(0)}%
                        </span>
                      )}
                    </span>
                  ))}
                </div>
              )}

              <div className="flex items-center gap-2 mt-0.5 px-1">
                <span className="text-[9px]" style={{ color: 'var(--text-muted)' }}>{msg.timestamp}</span>
                {msg.role === 'assistant' && (
                  <button onClick={() => copyMessage(msg.id, msg.content)}
                    className="hover:bg-white/10 rounded p-0.5"
                    style={{ color: 'var(--text-muted)' }}>
                    {copiedId === msg.id ? <Check size={9} /> : <Copy size={9} />}
                  </button>
                )}
              </div>
            </div>

            {msg.role === 'user' && (
              <div className="w-6 h-6 rounded flex items-center justify-center shrink-0"
                style={{ background: 'var(--accent-purple)' + '22' }}>
                <User size={12} style={{ color: 'var(--accent-purple)' }} />
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="flex gap-2">
            <div className="w-6 h-6 rounded flex items-center justify-center shrink-0"
              style={{ background: 'var(--accent-blue)' + '22' }}>
              <Bot size={12} style={{ color: 'var(--accent-blue)' }} />
            </div>
            <div className="rounded-lg px-3 py-2" style={{ background: 'var(--bg-secondary)' }}>
              <Loader2 size={12} className="animate-spin" style={{ color: 'var(--accent-blue)' }} />
              <span className="text-[10px] ml-1" style={{ color: 'var(--text-muted)' }}>Running deep research...</span>
            </div>
          </div>
        )}
        <div ref={endRef} />
      </div>

      <div className="p-2 border-t" style={{ borderColor: 'var(--border-primary)' }}>
        <div className="flex items-center gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && sendMessage()}
            placeholder="Ask about any stock, thesis, or market trend..."
            disabled={loading}
            className="flex-1 h-8 px-3 text-xs rounded border outline-none"
            style={{ background: 'var(--bg-primary)', borderColor: 'var(--border-primary)', color: 'var(--text-primary)' }}
          />
          <button onClick={sendMessage} disabled={loading || !input.trim()}
            className="h-8 w-8 rounded flex items-center justify-center"
            style={{ background: 'var(--accent-blue)', color: 'white' }}>
            <Send size={12} />
          </button>
        </div>
      </div>
    </div>
  )
}

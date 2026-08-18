// FININT OMEGA — Auth context + login UI

import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react'
import { Lock, User, Eye, EyeOff, LogIn, AlertCircle } from 'lucide-react'

interface AuthUser {
  id: string
  email: string
  role: string
  orgId?: string
}

interface AuthContextType {
  user: AuthUser | null
  token: string | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  token: null,
  loading: true,
  login: async () => {},
  register: async () => {},
  logout: () => {},
})

export function useAuth() {
  return useContext(AuthContext)
}

function parseJwt(token: string): any {
  try {
    const base64Url = token.split('.')[1]
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
    return JSON.parse(atob(base64))
  } catch {
    return null
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const stored = localStorage.getItem('finint-token')
    if (stored) {
      try {
        const payload = parseJwt(stored)
        if (payload && (!payload.exp || payload.exp * 1000 > Date.now())) {
          setToken(stored)
          setUser({
            id: payload.sub || 'dev',
            email: payload.email || payload.sub || 'dev@finint.omega',
            role: payload.role || 'admin',
            orgId: payload.org_id,
          })
        } else {
          localStorage.removeItem('finint-token')
        }
      } catch {
        localStorage.removeItem('finint-token')
      }
    }
    setLoading(false)
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    try {
      const res = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })
      if (res.ok) {
        const data = await res.json()
        const t = data.access_token
        localStorage.setItem('finint-token', t)
        setToken(t)
        setUser({
          id: data.user_id || email,
          email: data.email || email,
          role: data.role || 'admin',
          orgId: 'dev-org',
        })
        return
      }
    } catch {
      // backend not reachable — skip
    }
  }, [])

  const register = useCallback(async (email: string, password: string) => {
    try {
      const res = await fetch('/api/v1/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, role: 'analyst' }),
      })
      if (res.ok) {
        const data = await res.json()
        const t = data.access_token
        localStorage.setItem('finint-token', t)
        setToken(t)
        setUser({
          id: data.user_id || email,
          email: data.email || email,
          role: data.role || 'analyst',
          orgId: 'dev-org',
        })
        return
      }
    } catch {
      // backend not reachable
    }
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem('finint-token')
    setToken(null)
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider value={{ user, token, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

// ── Login Screen ──

export function LoginScreen() {
  const { login, register } = useAuth()
  const [email, setEmail] = useState('admin@finint.omega')
  const [password, setPassword] = useState('admin123')
  const [showPassword, setShowPassword] = useState(false)
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      if (mode === 'login') {
        await login(email, password)
      } else {
        await register(email, password)
      }
    } catch (err: any) {
      setError(err.message || 'Authentication failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center" style={{ background: 'var(--bg-primary)' }}>
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl mb-4"
            style={{ background: 'var(--accent-blue)' + '22' }}>
            <Lock size={28} style={{ color: 'var(--accent-blue)' }} />
          </div>
          <h1 className="text-xl font-bold" style={{ color: 'var(--text-primary)' }}>FININT OMEGA</h1>
          <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>Institutional Intelligence Terminal</p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-[10px] uppercase tracking-wider mb-1 block" style={{ color: 'var(--text-muted)' }}>
              Email
            </label>
            <div className="relative">
              <User size={14} className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: 'var(--text-muted)' }} />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full h-10 pl-10 pr-3 text-sm rounded-lg border outline-none transition-colors"
                style={{
                  background: 'var(--bg-secondary)',
                  borderColor: 'var(--border-primary)',
                  color: 'var(--text-primary)',
                }}
                required
              />
            </div>
          </div>

          <div>
            <label className="text-[10px] uppercase tracking-wider mb-1 block" style={{ color: 'var(--text-muted)' }}>
              Password
            </label>
            <div className="relative">
              <Lock size={14} className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: 'var(--text-muted)' }} />
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full h-10 pl-10 pr-10 text-sm rounded-lg border outline-none transition-colors"
                style={{
                  background: 'var(--bg-secondary)',
                  borderColor: 'var(--border-primary)',
                  color: 'var(--text-primary)',
                }}
                required
              />
              <button type="button" onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2"
                style={{ color: 'var(--text-muted)' }}>
                {showPassword ? <EyeOff size={14} /> : <Eye size={14} />}
              </button>
            </div>
          </div>

          {error && (
            <div className="flex items-center gap-2 p-2 rounded text-xs"
              style={{ background: 'var(--accent-red)' + '15', color: 'var(--accent-red)' }}>
              <AlertCircle size={12} />
              {error}
            </div>
          )}

          <button type="submit" disabled={loading}
            className="w-full h-10 rounded-lg text-sm font-medium flex items-center justify-center gap-2 transition-opacity"
            style={{ background: 'var(--accent-blue)', color: 'white' }}>
            {loading ? (
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              <>
                <LogIn size={14} />
                {mode === 'login' ? 'Sign In' : 'Create Account'}
              </>
            )}
          </button>
        </form>

        <div className="mt-4 text-center">
          <button onClick={() => setMode(mode === 'login' ? 'register' : 'login')}
            className="text-xs hover:underline" style={{ color: 'var(--accent-blue)' }}>
            {mode === 'login' ? "Don't have an account? Register" : 'Already have an account? Sign in'}
          </button>
        </div>

        <div className="mt-6 text-center text-[10px]" style={{ color: 'var(--text-muted)' }}>
          Dev mode: Any credentials will generate a local token
        </div>
      </div>
    </div>
  )
}

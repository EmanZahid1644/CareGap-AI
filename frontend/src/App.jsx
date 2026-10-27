import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  Activity, AlertCircle, ArrowRight, BrainCircuit, CalendarDays, CheckCircle2,
  ChevronDown, ChevronLeft, ChevronRight, ClipboardList, Database, FileUp,
  HeartPulse, LayoutDashboard, LogOut, Menu, RefreshCw, Search, ShieldCheck,
  Stethoscope, UploadCloud, Users, X,
} from 'lucide-react'
import {
  ResponsiveContainer, AreaChart, Area, CartesianGrid, XAxis, YAxis, Tooltip,
  BarChart, Bar,
} from 'recharts'
import PatientCreate from './PatientCreate'
import {
  api, TOKEN_KEY, errorMessage, extractItems, extractTotal,
  loginWithFallback, organizationPath, loadCareGapSummary,
} from './api'

const NAV = [
  { id: 'dashboard', label: 'Overview', icon: LayoutDashboard },
  { id: 'patients', label: 'Patients', icon: Users },
  { id: 'encounters', label: 'Encounters', icon: ClipboardList },
  { id: 'imports', label: 'CSV Imports', icon: FileUp },
  { id: 'gaps', label: 'Care-gap Flags', icon: AlertCircle },
  { id: 'risk', label: 'AI Risk Demo', icon: BrainCircuit },
]

function formatDate(value) {
  if (!value) return '—'
  const d = new Date(value)
  return Number.isNaN(d.getTime()) ? String(value) : d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
}
function shortId(value) { return value ? `${String(value).slice(0, 8)}…` : '—' }
function pretty(value) { return String(value || 'unknown').replaceAll('_', ' ').replace(/\b\w/g, (s) => s.toUpperCase()) }
function Status({ value }) {
  const v = String(value || 'unknown').toLowerCase()
  const kind = v.includes('error') || v.includes('rejected') || v.includes('failed') ? 'bad' :
    v.includes('pending') || v.includes('processing') || v.includes('review') ? 'warn' : 'good'
  return <span className={`status status-${kind}`}>{pretty(value)}</span>
}
function Notice({ type = 'error', children, onClose }) {
  if (!children) return null
  return <div className={`notice notice-${type}`} role="status"><AlertCircle size={17} /><span>{children}</span>{onClose && <button className="icon-button" onClick={onClose} aria-label="Dismiss"><X size={15} /></button>}</div>
}
function Empty({ text = 'No records found.' }) { return <div className="empty"><Database size={27} /><p>{text}</p></div> }
function Card({ title, children, right, className = '' }) {
  return <section className={`panel ${className}`}><div className="panel-heading"><h3>{title}</h3>{right}</div>{children}</section>
}
function Stat({ icon: Icon, label, value, sub, tone = 'blue' }) {
  return <div className="stat"><div className={`stat-icon tone-${tone}`}><Icon size={20} /></div><div className="stat-label">{label}</div><div className="stat-value">{value ?? '—'}</div><div className="stat-sub">{sub}</div></div>
}
function Pager({ page, setPage, count, pageSize = 20 }) {
  return <div className="pager"><span>Page {page}{Number.isFinite(count) ? ` · ${count} records` : ''}</span><div className="pager-buttons"><button disabled={page <= 1} onClick={() => setPage((p) => p - 1)}><ChevronLeft size={17} /></button><button disabled={count < page * pageSize} onClick={() => setPage((p) => p + 1)}><ChevronRight size={17} /></button></div></div>
}
function Login({ onLogin }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  async function submit(event) {
    event.preventDefault(); setError(''); setBusy(true)
    try {
      const data = await loginWithFallback(email.trim(), password)
      const token = data?.access_token || data?.token || data?.data?.access_token
      if (!token) throw new Error('Login succeeded but no access token was returned. Check the login response schema.')
      sessionStorage.setItem(TOKEN_KEY, token)
      onLogin()
    } catch (e) { setError(errorMessage(e)) }
    finally { setBusy(false) }
  }
  return <div className="auth-page"><div className="auth-aside"><div className="brand brand-light"><HeartPulse size={29} /><span>CareGap<span className="brand-accent">AI</span></span></div><div className="auth-message"><div className="eyebrow light">HOSPITAL INTELLIGENCE PLATFORM</div><h1>Better visibility.<br />Smarter workflows.</h1><p>Bring encounter analytics, data quality, follow-up flags, and prototype AI insights together in one workspace.</p></div><div className="auth-footer"><ShieldCheck size={18} /> Role-based access · Hospital-scoped data</div></div><div className="auth-form-wrap"><form className="auth-form" onSubmit={submit}><div className="eyebrow">WELCOME BACK</div><h2>Sign in to your workspace</h2><p className="muted">Use your existing CareGap-AI hospital account.</p><label>Email address<input type="email" autoComplete="username" required value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@hospital.com" /></label><label>Password<input type="password" autoComplete="current-password" required value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Enter password" /></label><Notice>{error}</Notice><button className="primary-btn auth-submit" disabled={busy}>{busy ? 'Signing in…' : 'Sign in'} <ArrowRight size={17} /></button><p className="auth-help">Need an account? Register through the backend Swagger UI at <code>/docs</code>.</p></form></div></div>
}
function Overview({ orgId, start, end, refresh }) {
  const [data, setData] = useState(null)
  const [imports, setImports] = useState([])
  const [gaps, setGaps] = useState(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(true)
  useEffect(() => {
    let alive = true; setBusy(true); setError('')
    const params = { ...(start ? { start_date: start } : {}), ...(end ? { end_date: end } : {}) }
    Promise.allSettled([
      api.get(organizationPath(orgId, '/analytics/overview'), { params }),
      api.get(organizationPath(orgId, '/imports'), { params: { page: 1, page_size: 5 } }),
      loadCareGapSummary(orgId, params),
    ]).then(([a, b, c]) => {
      if (!alive) return
      if (a.status === 'fulfilled') setData(a.value.data)
      else setError(errorMessage(a.reason))
      if (b.status === 'fulfilled') setImports(extractItems(b.value.data))
      if (c.status === 'fulfilled') setGaps(c.value)
      else setError((old) => [old, `Care-gap summary: ${errorMessage(c.reason)}`].filter(Boolean).join(' · '))
      setBusy(false)
    })
    return () => { alive = false }
  }, [orgId, start, end, refresh])
  const trend = (data?.admission_trends || []).map((r) => ({ date: String(r.date).slice(5), count: Number(r.count) }))
  const types = Object.entries(data?.encounter_types || {}).map(([name, count]) => ({ name: pretty(name), count }))
  const quality = Object.entries(data?.data_quality_breakdown || {})
  return <div className="page-stack"><Notice>{error}</Notice><div className="stats-grid"><Stat icon={Database} label="Total encounters" value={busy ? '…' : data?.total_encounters} sub="In selected period"/><Stat icon={ClipboardList} label="Pending review" value={busy ? '…' : data?.pending_review} sub="Records needing validation" tone="amber"/><Stat icon={AlertCircle} label="Flagged encounters" value={busy ? '…' : gaps?.flagged_encounters ?? '—'} sub={gaps?.complete ? `Across ${gaps.scanned_encounters} scanned` : `Partial scan: ${gaps?.scanned_encounters ?? 0} scanned`} tone="rose"/><Stat icon={CalendarDays} label="Average stay" value={busy ? '…' : data?.average_length_of_stay_days == null ? '—' : `${data.average_length_of_stay_days} d`} sub="Discharged encounters" tone="green"/></div><div className="two-col"><Card title="Admission trend" right={<span className="small-muted">By admission date</span>}>{trend.length ? <div className="chart"><ResponsiveContainer width="100%" height="100%"><AreaChart data={trend} margin={{ top: 12, right: 10, left: -23, bottom: 0 }}><defs><linearGradient id="areaBlue" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#2563eb" stopOpacity={0.2}/><stop offset="100%" stopColor="#2563eb" stopOpacity={0.01}/></linearGradient></defs><CartesianGrid strokeDasharray="4 4" vertical={false} stroke="#edf1f7"/><XAxis dataKey="date" tick={{ fill: '#8b98aa', fontSize: 11 }} axisLine={false} tickLine={false}/><YAxis allowDecimals={false} tick={{ fill: '#8b98aa', fontSize: 11 }} axisLine={false} tickLine={false}/><Tooltip/><Area type="monotone" dataKey="count" stroke="#2563eb" strokeWidth={2.5} fill="url(#areaBlue)"/></AreaChart></ResponsiveContainer></div> : <Empty text={busy ? 'Loading chart…' : 'No admissions in this period.'}/>}</Card><Card title="Encounter types">{types.length ? <div className="chart"><ResponsiveContainer width="100%" height="100%"><BarChart data={types} layout="vertical" margin={{ top: 8, right: 18, left: 15, bottom: 0 }}><CartesianGrid strokeDasharray="4 4" horizontal={false} stroke="#edf1f7"/><XAxis type="number" allowDecimals={false} tick={{ fill: '#8b98aa', fontSize: 11 }} axisLine={false} tickLine={false}/><YAxis dataKey="name" type="category" width={95} tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false}/><Tooltip/><Bar dataKey="count" fill="#38bdf8" radius={[0, 5, 5, 0]} maxBarSize={32}/></BarChart></ResponsiveContainer></div> : <Empty text="No encounter type data."/>}</Card></div><div className="two-col"><Card title="Data quality breakdown">{quality.length ? <div className="quality-list">{quality.map(([name, count]) => <div key={name} className="quality-item"><div><span>{pretty(name)}</span><strong>{count}</strong></div><div className="progress-track"><div className="progress-fill" style={{ width: `${data?.total_encounters ? count / data.total_encounters * 100 : 0}%` }}/></div></div>)}</div> : <Empty text="No data-quality records."/>}</Card><Card title="Recent CSV imports">{imports.length ? <div className="simple-list">{imports.slice(0, 5).map((item) => <div className="simple-row" key={item.id || item.import_job_id}><div><strong>{item.source_filename || 'CSV import'}</strong><span>{formatDate(item.created_at)}</span></div><Status value={item.status}/></div>)}</div> : <Empty text="No import history yet."/>}</Card></div><div className="disclaimer"><ShieldCheck size={18}/><span>Clinical analytics are descriptive. The readmission model is trained on synthetic data and is for technical demonstration only.</span></div></div>
}
function Records({ orgId, kind, refresh }) {
  const [page, setPage] = useState(1)
  const [data, setData] = useState([])
  const [total, setTotal] = useState(0)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(true)
  const [selected, setSelected] = useState(null)
  const [search, setSearch] = useState('')
  const [createOpen, setCreateOpen] = useState(false)
  const [localRefresh, setLocalRefresh] = useState(0)
  useEffect(() => { setPage(1); setSelected(null) }, [orgId, kind])
  useEffect(() => {
    let alive = true; setBusy(true); setError('')
    api.get(organizationPath(orgId, `/${kind}`), { params: { page, page_size: 20 } })
      .then(({ data: payload }) => { if (alive) { const items = extractItems(payload); setData(items); setTotal(extractTotal(payload, items)) } })
      .catch((e) => { if (alive) setError(errorMessage(e)) })
      .finally(() => { if (alive) setBusy(false) })
    return () => { alive = false }
  }, [orgId, kind, page, refresh, localRefresh])
  const shown = data.filter((item) => JSON.stringify(item).toLowerCase().includes(search.toLowerCase()))
  const patients = kind === 'patients'
  return <div className="page-stack"><div className="toolbar"><div className="search"><Search size={17}/><input placeholder={`Search loaded ${kind}…`} value={search} onChange={(e) => setSearch(e.target.value)}/></div><div className="toolbar-actions"><span className="small-muted">Search applies to current page</span>{patients && <button className="primary-btn" onClick={() => setCreateOpen(true)}>+ Add patient</button>}</div></div><Notice>{error}</Notice><Card title={patients ? 'Patient directory' : 'Encounter records'} right={<span className="small-muted">{busy ? 'Loading…' : `${total} records`}</span>}>{shown.length ? <div className="table-scroll"><table className="data-table"><thead><tr>{patients ? <><th>Patient</th><th>Record ID</th><th>Status</th><th>Created</th></> : <><th>Source ID</th><th>Admission</th><th>Discharge</th><th>Type</th><th>Data quality</th></>}<th></th></tr></thead><tbody>{shown.map((item, i) => <tr key={item.id || i}>{patients ? <><td><strong>{item.full_name || item.name || item.patient_name || `Patient ${i + 1}`}</strong></td><td className="mono">{shortId(item.id)}</td><td><Status value={item.is_active === false ? 'inactive' : item.status || 'active'}/></td><td>{formatDate(item.created_at)}</td></> : <><td className="mono">{item.source_record_id || shortId(item.id)}</td><td>{formatDate(item.admission_date)}</td><td>{formatDate(item.discharge_date)}</td><td>{pretty(item.encounter_type)}</td><td><Status value={item.data_quality_status}/></td></>}<td><button className="text-btn" onClick={() => setSelected(item)}>View <ArrowRight size={14}/></button></td></tr>)}</tbody></table></div> : <Empty text={busy ? 'Loading records…' : 'No records found on this page.'}/>}<Pager page={page} setPage={setPage} count={total}/></Card>{selected && <div className="modal-backdrop" onClick={() => setSelected(null)}><div className="modal" role="dialog" aria-modal="true" aria-label="Record details" onClick={(e) => e.stopPropagation()}><div className="modal-head"><h3>{patients ? 'Patient' : 'Encounter'} details</h3><button className="icon-button" onClick={() => setSelected(null)}><X size={20}/></button></div><div className="details-grid">{Object.entries(selected).filter(([key]) => key !== 'password_hash').map(([key, value]) => <div className="detail-item" key={key}><span>{pretty(key)}</span><strong>{value === null ? '—' : typeof value === 'object' ? JSON.stringify(value) : String(value)}</strong></div>)}</div></div></div>}{createOpen && <PatientCreate orgId={orgId} onClose={() => setCreateOpen(false)} onCreated={() => { setCreateOpen(false); setPage(1); setLocalRefresh((v) => v + 1) }}/>}</div>
}
function Imports({ orgId, refresh, onRefresh }) {
  const [file, setFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [page, setPage] = useState(1)
  const [items, setItems] = useState([])
  const [total, setTotal] = useState(0)
  useEffect(() => { setPage(1) }, [orgId])
  useEffect(() => {
    let alive = true
    api.get(organizationPath(orgId, '/imports'), { params: { page, page_size: 20 } })
      .then(({ data }) => { if (alive) { const rows = extractItems(data); setItems(rows); setTotal(extractTotal(data, rows)) } })
      .catch((e) => { if (alive) setError(errorMessage(e)) })
    return () => { alive = false }
  }, [orgId, page, refresh])
  async function upload(e) {
    e.preventDefault(); if (!file) return
    setUploading(true); setError(''); setMessage('')
    const body = new FormData(); body.append('file', file)
    try {
      const { data } = await api.post(organizationPath(orgId, '/imports/encounters'), body)
      setMessage(`Import ${pretty(data.status)} · ${data.valid_rows ?? 0} valid · ${data.invalid_rows ?? 0} invalid`)
      setFile(null); e.target.reset(); setPage(1); onRefresh()
    } catch (err) { setError(errorMessage(err)) }
    finally { setUploading(false) }
  }
  return <div className="page-stack"><Card title="Import encounter CSV"><p className="muted">Upload a UTF-8 CSV with the required columns: source_record_id, admission_date, discharge_date, encounter_type. Optional: age, prior_admissions, length_of_stay, diabetes.</p><form onSubmit={upload} className="upload-form"><label className="upload-box"><UploadCloud size={29}/><strong>{file ? file.name : 'Choose a CSV file'}</strong><span>Maximum 5 MB · up to 5,000 rows</span><input type="file" accept=".csv,text/csv" required onChange={(e) => setFile(e.target.files?.[0] || null)}/></label><button className="primary-btn" disabled={!file || uploading}>{uploading ? 'Uploading…' : 'Upload CSV'} <ArrowRight size={16}/></button></form><Notice>{error}</Notice><Notice type="success">{message}</Notice></Card><Card title="Import history">{items.length ? <div className="table-scroll"><table className="data-table"><thead><tr><th>Filename</th><th>Created</th><th>Total</th><th>Valid</th><th>Invalid</th><th>Status</th></tr></thead><tbody>{items.map((row, i) => <tr key={row.id || i}><td><strong>{row.source_filename || 'Import'}</strong></td><td>{formatDate(row.created_at)}</td><td>{row.total_rows ?? '—'}</td><td>{row.valid_rows ?? '—'}</td><td>{row.invalid_rows ?? '—'}</td><td><Status value={row.status}/></td></tr>)}</tbody></table></div> : <Empty text="No imports yet."/>}<Pager page={page} setPage={setPage} count={total}/></Card></div>
}
function Gaps({ orgId, start, end, refresh }) {
  const [page, setPage] = useState(1)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(true)
  useEffect(() => { setPage(1) }, [orgId, start, end])
  useEffect(() => {
    let alive = true; setBusy(true); setError('')
    const params = { page, page_size: 100, ...(start ? { start_date: start } : {}), ...(end ? { end_date: end } : {}) }
    api.get(organizationPath(orgId, '/care-gaps/encounters'), { params })
      .then(({ data }) => { if (alive) setResult(data) })
      .catch((e) => { if (alive) setError(errorMessage(e)) })
      .finally(() => { if (alive) setBusy(false) })
    return () => { alive = false }
  }, [orgId, page, start, end, refresh])
  function exportFlags() {
    const rows = [['source_record_id', 'flag_code', 'severity', 'description']]
    for (const item of result?.items || []) for (const gap of item.gaps || []) {
      rows.push([item.source_record_id || item.encounter_id, gap.code, gap.severity, gap.description])
    }
    const csv = rows.map((row) => row.map((value) => `"${String(value ?? '').replaceAll('"', '""')}"`).join(',')).join('\r\n')
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a'); a.href = url; a.download = `caregap-flags-page-${page}.csv`; a.click()
    URL.revokeObjectURL(url)
  }
  return <div className="page-stack"><div className="disclaimer"><ShieldCheck size={18}/><span>Flags describe documented follow-up scheduling and data-quality gaps, not diagnoses or treatment recommendations. Counts are for the current scanned page.</span></div><Notice>{error}</Notice><div className="stats-grid stats-three"><Stat icon={Database} label="Scanned encounters" value={busy ? '…' : result?.scanned_encounters ?? 0} sub="Current page"/><Stat icon={AlertCircle} label="Flagged encounters" value={busy ? '…' : result?.flagged_encounters ?? 0} sub="Current page" tone="amber"/><Stat icon={ClipboardList} label="Total flags" value={busy ? '…' : result?.total_gaps ?? 0} sub="Current page" tone="rose"/></div><Card title="Encounter flags" right={<button className="text-btn" disabled={!result?.items?.length} onClick={exportFlags}>Export page CSV</button>}>{result?.items?.length ? <div className="gap-list">{result.items.map((item) => <div className="gap-group" key={item.encounter_id}><div className="gap-group-head"><strong>{item.source_record_id || shortId(item.encounter_id)}</strong><span>{item.gap_count} flag(s)</span></div>{item.gaps.map((gap, i) => <div className="gap-entry" key={`${gap.code}-${i}`}><Status value={gap.severity}/><div><strong>{pretty(gap.code)}</strong><p>{gap.description}</p><small>{gap.recommendation}</small></div></div>)}</div>)}</div> : <Empty text={busy ? 'Scanning encounters…' : 'No flags found on this page.'}/>}<div className="pager"><span>Page {page} · Up to 100 encounters scanned per page</span><div className="pager-buttons"><button disabled={page <= 1} onClick={() => setPage((p) => p - 1)}><ChevronLeft size={17}/></button><button disabled={!result || result.scanned_encounters < 100} onClick={() => setPage((p) => p + 1)}><ChevronRight size={17}/></button></div></div></Card></div>
}
function Risk({ orgId }) {
  const [form, setForm] = useState({ age: 65, prior_admissions: 2, length_of_stay: 5, diabetes: false })
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  async function submit(e) {
    e.preventDefault(); setBusy(true); setError(''); setResult(null)
    try {
      const { data } = await api.post(organizationPath(orgId, '/analytics/readmission-risk'), {
        age: Number(form.age), prior_admissions: Number(form.prior_admissions),
        length_of_stay: Number(form.length_of_stay), diabetes: form.diabetes,
      })
      setResult(data)
    } catch (err) { setError(errorMessage(err)) }
    finally { setBusy(false) }
  }
  return <div className="page-stack"><div className="disclaimer disclaimer-strong"><AlertCircle size={19}/><span><strong>DEMO ONLY:</strong> This model was trained on synthetic outcomes. Its score is not a validated clinical probability and must not be used for patient care.</span></div><div className="two-col risk-layout"><Card title="Readmission risk demo"><p className="muted">Enter synthetic example inputs to test the model API. Do not enter real patient information.</p><form className="risk-form" onSubmit={submit}><label>Age (years)<input type="number" min="0" max="120" required value={form.age} onChange={(e) => setForm({ ...form, age: e.target.value })}/></label><label>Prior admissions<input type="number" min="0" required value={form.prior_admissions} onChange={(e) => setForm({ ...form, prior_admissions: e.target.value })}/></label><label>Length of stay (days)<input type="number" min="0" required value={form.length_of_stay} onChange={(e) => setForm({ ...form, length_of_stay: e.target.value })}/></label><label>Diabetes status<select value={String(form.diabetes)} onChange={(e) => setForm({ ...form, diabetes: e.target.value === 'true' })}><option value="false">No</option><option value="true">Yes</option></select></label><button className="primary-btn" disabled={busy}>{busy ? 'Calculating…' : 'Run demo prediction'} <BrainCircuit size={17}/></button></form><Notice>{error}</Notice></Card><Card title="Model output">{result ? <div className="risk-result"><div className="risk-circle"><span>{Number(result.risk_percentage).toFixed(1)}%</span><small>Synthetic score</small></div><div className="risk-meta"><div><span>Model version</span><strong>{result.model_version}</strong></div><div><span>Model type</span><strong>{pretty(result.model_type)}</strong></div><div><span>Raw score</span><strong>{result.risk_score}</strong></div></div><div className="disclaimer">{result.disclaimer}</div></div> : <div className="risk-placeholder"><BrainCircuit size={43}/><h3>Ready to run</h3><p>Submit the sample feature values to view a demo model output.</p></div>}</Card></div></div>
}
export default function App() {
  const [authenticated, setAuthenticated] = useState(Boolean(sessionStorage.getItem(TOKEN_KEY)))
  const [user, setUser] = useState(null)
  const [organizations, setOrganizations] = useState([])
  const [orgId, setOrgId] = useState('')
  const [active, setActive] = useState('dashboard')
  const [refresh, setRefresh] = useState(0)
  const [start, setStart] = useState('')
  const [end, setEnd] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [menuOpen, setMenuOpen] = useState(false)
  const logout = useCallback(() => { sessionStorage.removeItem(TOKEN_KEY); setAuthenticated(false); setUser(null); setOrganizations([]); setOrgId(''); setActive('dashboard') }, [])
  useEffect(() => {
    if (!authenticated) { setLoading(false); return }
    let alive = true; setLoading(true); setError('')
    Promise.allSettled([api.get('/auth/me'), api.get('/organizations')]).then(([me, orgs]) => {
      if (!alive) return
      if (me.status === 'rejected' && me.reason?.response?.status === 401) { logout(); return }
      if (me.status === 'fulfilled') setUser(me.value.data)
      if (orgs.status === 'fulfilled') {
        const list = extractItems(orgs.value.data)
        setOrganizations(list)
        setOrgId((current) => list.some((o) => String(o.id || o.organization_id) === current) ? current : String(list[0]?.id || list[0]?.organization_id || ''))
      } else setError(errorMessage(orgs.reason))
      setLoading(false)
    })
    return () => { alive = false }
  }, [authenticated, logout])
  const org = useMemo(() => organizations.find((o) => String(o.id || o.organization_id) === orgId), [organizations, orgId])
  const pageName = NAV.find((item) => item.id === active)?.label || 'Overview'
  if (!authenticated) return <Login onLogin={() => setAuthenticated(true)}/>
  if (loading) return <div className="center-loading"><HeartPulse size={36}/> Loading CareGap-AI…</div>
  return <div className="shell"><aside className={`sidebar ${menuOpen ? 'sidebar-open' : ''}`}><div className="brand"><HeartPulse size={28}/><span>CareGap<span className="brand-accent">AI</span></span></div><div className="sidebar-label">WORKSPACE</div><nav>{NAV.map(({ id, label, icon: Icon }) => <button key={id} className={`nav-link ${active === id ? 'nav-active' : ''}`} onClick={() => { setActive(id); setMenuOpen(false) }}><Icon size={19}/>{label}</button>)}</nav><div className="sidebar-bottom"><div className="sidebar-info"><ShieldCheck size={17}/> Hospital-scoped access</div><button className="nav-link" onClick={logout}><LogOut size={19}/> Sign out</button></div></aside>{menuOpen && <div className="sidebar-overlay" onClick={() => setMenuOpen(false)}/>}<div className="main-area"><header className="topbar"><div className="topbar-left"><button className="icon-button mobile-menu" onClick={() => setMenuOpen(true)} aria-label="Open navigation"><Menu size={22}/></button><div><div className="eyebrow">HOSPITAL WORKSPACE</div><h1>{pageName}</h1></div></div><div className="topbar-actions"><div className="org-picker"><Stethoscope size={17}/><select aria-label="Choose hospital" value={orgId} onChange={(e) => { setOrgId(e.target.value); setActive('dashboard') }}>{organizations.map((o) => <option key={o.id || o.organization_id} value={o.id || o.organization_id}>{o.name || o.organization_name || shortId(o.id || o.organization_id)}</option>)}</select><ChevronDown size={15}/></div><button className="refresh-button" onClick={() => setRefresh((v) => v + 1)} title="Refresh data"><RefreshCw size={17}/></button><div className="avatar" title={user?.email || 'Account'}>{(user?.email || 'U').charAt(0).toUpperCase()}</div></div></header><main className="content"><div className="page-intro"><div><div className="eyebrow">{org?.name || org?.organization_name || 'CareGap-AI'}</div><h2>{active === 'dashboard' ? 'Clinical overview' : pageName}</h2><p>{active === 'dashboard' ? 'Monitor operational signals across your hospital.' : active === 'risk' ? 'Technical demonstration using synthetic model training.' : 'Hospital-scoped records and operational insights.'}</p></div>{['dashboard', 'gaps'].includes(active) && <div className="date-controls"><label>From<input type="date" value={start} onChange={(e) => setStart(e.target.value)}/></label><label>To<input type="date" value={end} onChange={(e) => setEnd(e.target.value)}/></label>{(start || end) && <button className="text-btn" onClick={() => { setStart(''); setEnd('') }}>Clear</button>}</div>}</div><Notice>{error}</Notice>{!organizations.length ? <Card title="No hospital workspace available"><Empty text="Your account has no accessible organizations, or the organization response could not be read. Create or join a hospital using the backend API, then refresh."/><button className="primary-btn" onClick={() => window.location.reload()}>Reload organizations</button></Card> : !orgId ? <Empty text="Select a hospital to continue."/> : <>{active === 'dashboard' && <Overview orgId={orgId} start={start} end={end} refresh={refresh}/>}{active === 'patients' && <Records orgId={orgId} kind="patients" refresh={refresh}/>}{active === 'encounters' && <Records orgId={orgId} kind="encounters" refresh={refresh}/>}{active === 'imports' && <Imports orgId={orgId} refresh={refresh} onRefresh={() => setRefresh((v) => v + 1)}/>}{active === 'gaps' && <Gaps orgId={orgId} start={start} end={end} refresh={refresh}/>}{active === 'risk' && <Risk orgId={orgId}/>}</>}<footer className="footer">CareGap-AI · Hospital intelligence prototype · Synthetic AI scores are not for clinical use.</footer></main></div></div>
}

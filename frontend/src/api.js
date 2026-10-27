import axios from 'axios'

export const TOKEN_KEY = 'caregap_demo_session_token'

export const api = axios.create({
  baseURL: '/api/v1',
  timeout: 25000,
})

api.interceptors.request.use((config) => {
  const token = sessionStorage.getItem(TOKEN_KEY)
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

export function errorMessage(error) {
  const detail = error?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) return detail.map((item) => item.msg || JSON.stringify(item)).join('; ')
  if (detail && typeof detail === 'object') return JSON.stringify(detail)
  return error?.message || 'Request failed. Check that the backend is running.'
}

export function extractItems(payload) {
  if (Array.isArray(payload)) return payload
  if (!payload || typeof payload !== 'object') return []
  for (const key of ['items', 'results', 'organizations', 'patients', 'encounters', 'imports', 'data']) {
    if (Array.isArray(payload[key])) return payload[key]
    if (payload[key] && typeof payload[key] === 'object') {
      const nested = extractItems(payload[key])
      if (nested.length) return nested
    }
  }
  return []
}

export function extractTotal(payload, items) {
  return Number(payload?.total ?? payload?.count ?? payload?.pagination?.total ?? items.length)
}

export async function loginWithFallback(email, password) {
  try {
    const { data } = await api.post('/auth/login', { email, password })
    return data
  } catch (error) {
    if (error?.response?.status !== 422 && error?.response?.status !== 415) throw error
    const body = new URLSearchParams({ username: email, password })
    const { data } = await api.post('/auth/login', body, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
    return data
  }
}

export function organizationPath(orgId, suffix) {
  return `/organizations/${encodeURIComponent(orgId)}${suffix}`
}


// The care-gap endpoint reports counts per scanned page, not hospital-wide totals.
// Aggregate pages explicitly so the Overview never labels a 20-row sample as a hospital total.
export async function loadCareGapSummary(orgId, dateParams = {}, maxPages = 50) {
  const pageSize = 100
  const totals = { scanned_encounters: 0, flagged_encounters: 0, total_gaps: 0, complete: false }
  for (let page = 1; page <= maxPages; page += 1) {
    const { data } = await api.get(organizationPath(orgId, '/care-gaps/encounters'), {
      params: { ...dateParams, page, page_size: pageSize },
    })
    const scanned = Number(data?.scanned_encounters || 0)
    totals.scanned_encounters += scanned
    totals.flagged_encounters += Number(data?.flagged_encounters || 0)
    totals.total_gaps += Number(data?.total_gaps || 0)
    if (scanned < pageSize) {
      totals.complete = true
      return totals
    }
  }
  return totals // Deliberately marked incomplete when the scan cap is reached.
}

import { useEffect, useMemo, useState } from 'react'
import axios from 'axios'
import { AlertCircle, Plus, X } from 'lucide-react'
import { api, errorMessage, organizationPath } from './api'

function resolveSchema(schema, document, depth = 0) {
  if (!schema || depth > 8) return {}
  if (schema.$ref) {
    const target = schema.$ref.split('/').slice(1).reduce((obj, key) => obj?.[key.replaceAll('~1', '/').replaceAll('~0', '~')], document)
    return resolveSchema(target, document, depth + 1)
  }
  if (schema.allOf) {
    const parts = schema.allOf.map((part) => resolveSchema(part, document, depth + 1))
    return { ...schema, properties: Object.assign({}, ...parts.map((p) => p.properties || {})), required: [...new Set(parts.flatMap((p) => p.required || []))] }
  }
  if (schema.anyOf || schema.oneOf) {
    const options = schema.anyOf || schema.oneOf
    const nonNull = options.find((part) => part.type !== 'null') || options[0]
    return { ...resolveSchema(nonNull, document, depth + 1), description: schema.description || nonNull.description, nullable: options.some((part) => part.type === 'null') }
  }
  return schema
}

function defaultValue(schema) {
  if (schema.default !== undefined && schema.default !== null) return String(schema.default)
  return schema.type === 'boolean' ? false : ''
}

function convertValue(raw, schema) {
  if (schema.type === 'boolean') return Boolean(raw)
  if (raw === '') return undefined
  if (schema.type === 'integer' || schema.type === 'number') return Number(raw)
  if (schema.type === 'array' || schema.type === 'object') return JSON.parse(raw)
  return raw
}

export default function PatientCreate({ orgId, onClose, onCreated }) {
  const [schema, setSchema] = useState(null)
  const [values, setValues] = useState({})
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let alive = true
    setLoading(true)
    axios.get('/openapi.json').then(({ data }) => {
      const route = data?.paths?.['/api/v1/organizations/{organization_id}/patients']
      const requestSchema = route?.post?.requestBody?.content?.['application/json']?.schema
      if (!requestSchema) throw new Error('Patient creation schema was not found in OpenAPI.')
      const result = resolveSchema(requestSchema, data)
      if (!result.properties) throw new Error('Patient creation schema has no supported fields.')
      if (alive) {
        setSchema(result)
        setValues(Object.fromEntries(Object.entries(result.properties).map(([key, raw]) => [key, defaultValue(resolveSchema(raw, data))])))
      }
    }).catch((e) => { if (alive) setError(errorMessage(e)) })
      .finally(() => { if (alive) setLoading(false) })
    return () => { alive = false }
  }, [])

  const required = useMemo(() => new Set(schema?.required || []), [schema])
  const fields = Object.entries(schema?.properties || {})

  async function submit(event) {
    event.preventDefault()
    setBusy(true); setError('')
    try {
      const document = await axios.get('/openapi.json').then((r) => r.data)
      const payload = {}
      for (const [key, rawSchema] of fields) {
        const fieldSchema = resolveSchema(rawSchema, document)
        const value = convertValue(values[key], fieldSchema)
        if (value !== undefined) payload[key] = value
      }
      await api.post(organizationPath(orgId, '/patients'), payload)
      onCreated()
    } catch (e) {
      setError(e instanceof SyntaxError ? 'One of the JSON fields is not valid JSON.' : errorMessage(e))
    } finally { setBusy(false) }
  }

  return <div className="modal-backdrop" onClick={onClose}>
    <div className="modal patient-modal" role="dialog" aria-modal="true" aria-label="Add synthetic patient" onClick={(e) => e.stopPropagation()}>
      <div className="modal-head"><h3>Add patient</h3><button type="button" className="icon-button" onClick={onClose} aria-label="Close"><X size={20}/></button></div>
      <p className="muted">Fields are loaded from your FastAPI OpenAPI schema. Use fictional patient information for this demo.</p>
      {loading && <p className="muted">Loading patient form…</p>}
      {error && <div className="notice" role="alert"><AlertCircle size={17}/>{error}</div>}
      {!loading && schema && <form className="patient-form" onSubmit={submit}>
        {fields.map(([name, rawSchema]) => {
          // Most patient schemas use strings, numbers, dates, booleans, and enums.
          // Object/array fields remain available as JSON input rather than silently omitted.
          const type = rawSchema.type || (rawSchema.anyOf ? rawSchema.anyOf.find((s) => s.type !== 'null')?.type : undefined) || 'string'
          const label = name.replaceAll('_', ' ').replace(/\b\w/g, (c) => c.toUpperCase())
          const value = values[name] ?? ''
          const change = (next) => setValues((prev) => ({ ...prev, [name]: next }))
          return <label key={name} className="patient-field">
            <span>{label}{required.has(name) && <b className="required-star"> *</b>}</span>
            {rawSchema.enum ? <select value={value} required={required.has(name)} onChange={(e) => change(e.target.value)}><option value="">Select…</option>{rawSchema.enum.map((option) => <option key={String(option)} value={option}>{String(option)}</option>)}</select>
              : type === 'boolean' ? <span className="checkbox-row"><input type="checkbox" checked={Boolean(value)} onChange={(e) => change(e.target.checked)}/> Yes</span>
              : type === 'object' || type === 'array' ? <textarea rows={3} placeholder={type === 'array' ? '[]' : '{}'} required={required.has(name)} value={value} onChange={(e) => change(e.target.value)}/>
              : <input type={rawSchema.format === 'date' ? 'date' : rawSchema.format === 'date-time' ? 'datetime-local' : rawSchema.format === 'email' ? 'email' : type === 'integer' || type === 'number' ? 'number' : 'text'} step={type === 'number' ? 'any' : undefined} required={required.has(name)} value={value} onChange={(e) => change(e.target.value)} placeholder={rawSchema.description || label}/>}
            {rawSchema.description && <small>{rawSchema.description}</small>}
          </label>
        })}
        <button className="primary-btn" disabled={busy}>{busy ? 'Creating…' : 'Create patient'} <Plus size={16}/></button>
      </form>}
    </div>
  </div>
}

import React, { useEffect, useMemo, useRef, useState } from 'react'

const escapeCsv = (value) => {
  const raw = String(value ?? '')
  return /[",\n]/.test(raw) ? `"${raw.replace(/"/g, '""')}"` : raw
}

const flattenObject = (input, prefix = '') => {
  const rows = []
  if (Array.isArray(input)) {
    input.forEach((value, index) => {
      rows.push(...flattenObject(value, `${prefix}[${index}]`))
    })
    return rows
  }
  if (input && typeof input === 'object') {
    Object.entries(input).forEach(([key, value]) => {
      const path = prefix ? `${prefix}.${key}` : key
      rows.push(...flattenObject(value, path))
    })
    return rows
  }
  rows.push({ key: prefix || 'value', value: input })
  return rows
}

const rowsToCsv = (rows, headers) => {
  const head = headers.map(escapeCsv).join(',')
  const body = rows.map((row) => headers.map((h) => escapeCsv(row[h])).join(',')).join('\n')
  return `${head}\n${body}`
}

const downloadText = (filename, content) => {
  const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}

function App() {
  const [mode, setMode] = useState('json')
  const [version, setVersion] = useState('1')
  const [jsonText, setJsonText] = useState('')
  const [file, setFile] = useState(null)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [elapsedMs, setElapsedMs] = useState(0)
  const [startedAt, setStartedAt] = useState(null)
  const abortControllerRef = useRef(null)

  const endpoint = useMemo(() => `/classify/${version}`, [version])
  const elapsedLabel = useMemo(() => {
    const secs = Math.floor(elapsedMs / 1000)
    const mins = Math.floor(secs / 60)
    const rem = secs % 60
    return `${String(mins).padStart(2, '0')}:${String(rem).padStart(2, '0')}`
  }, [elapsedMs])
  const inputCsv = useMemo(() => {
    try {
      if (mode !== 'json' || !jsonText.trim()) return ''
      const payload = JSON.parse(jsonText)
      const rows = flattenObject(payload)
      return rowsToCsv(rows, ['key', 'value'])
    } catch {
      return ''
    }
  }, [mode, jsonText])
  const outputResultsCsv = useMemo(() => {
    if (!result?.results?.length) return ''
    return rowsToCsv(
      result.results.map((item) => ({
        tumor_type: item.tumor_type,
        confidence: Array.isArray(item.confidence) ? item.confidence[0] : item.confidence
      })),
      ['tumor_type', 'confidence']
    )
  }, [result])
  const outputFeaturesCsv = useMemo(() => {
    if (!result?.feature_list?.length) return ''
    return rowsToCsv(result.feature_list, ['variable_name', 'variable_imp'])
  }, [result])

  const loadBundledSample = async () => {
    const response = await fetch('/sample_request.json')
    if (!response.ok) {
      throw new Error('Could not load bundled sample JSON.')
    }
    const sampleText = await response.text()
    setJsonText(sampleText)
  }

  useEffect(() => {
    loadBundledSample().catch((err) => setError(err.message))
  }, [])

  useEffect(() => {
    if (!loading || !startedAt) return undefined
    const intervalId = setInterval(() => {
      setElapsedMs(Date.now() - startedAt)
    }, 250)
    return () => clearInterval(intervalId)
  }, [loading, startedAt])

  const handleJsonFile = async (event) => {
    const selected = event.target.files?.[0]
    if (!selected) return
    const text = await selected.text()
    setJsonText(text)
    setFile(selected)
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setLoading(true)
    setStartedAt(Date.now())
    setElapsedMs(0)
    setError('')
    setResult(null)

    try {
      const controller = new AbortController()
      abortControllerRef.current = controller
      let response

      if (mode === 'json') {
        const payload = JSON.parse(jsonText)
        response = await fetch(endpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
          signal: controller.signal
        })
      } else {
        if (!file) throw new Error('Please select a CSV feature file.')
        const formData = new FormData()
        formData.append('features', file)
        response = await fetch(endpoint, {
          method: 'POST',
          body: formData,
          signal: controller.signal
        })
      }

      const data = await response.json()
      if (!response.ok) {
        throw new Error(data.error || `Request failed with status ${response.status}`)
      }
      setResult(data)
    } catch (err) {
      if (err.name === 'AbortError') {
        setError('Inference request canceled.')
        return
      }
      setError(err.message || 'Request failed.')
    } finally {
      abortControllerRef.current = null
      setLoading(false)
      setStartedAt(null)
    }
  }

  const handleStop = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
  }

  return (
    <div className="page">
      <header className="hero">
        <p className="badge">OncoInfer</p>
        <h1>AI Deep Learning Inference Service for Precision Oncology</h1>
        <p className="subtitle">
          Deep-learning model for tumor-type prediction using oncology-targeted clinical genomic sequencing data.
        </p>
        <p className="model-note">
          Model references: <a href="https://github.com/mmdarmofal/GDD_ENS" target="_blank" rel="noreferrer">GDD_ENS</a> and{' '}
          <a href="https://pubmed.ncbi.nlm.nih.gov/38416134/" target="_blank" rel="noreferrer">associated publication</a>.
        </p>
      </header>

      <main className="panel">
        <form onSubmit={handleSubmit}>
          <div className="row">
            <label>
              Input Mode
              <select value={mode} onChange={(e) => setMode(e.target.value)}>
                <option value="json">JSON Payload</option>
                <option value="csv">CSV Feature File</option>
              </select>
            </label>

            <label>
              API Version
              <input value={version} onChange={(e) => setVersion(e.target.value)} />
            </label>
          </div>

          {mode === 'json' ? (
            <>
              <label>JSON Input</label>
              <textarea value={jsonText} onChange={(e) => setJsonText(e.target.value)} rows={16} />
              <button className="secondary-button" type="button" onClick={() => loadBundledSample().catch((err) => setError(err.message))}>
                Load OncoInfer Sample JSON
              </button>
              <label className="file-label">
                Optional: load JSON file
                <input type="file" accept=".json,application/json" onChange={handleJsonFile} />
              </label>
            </>
          ) : (
            <label className="file-label">
              CSV Feature File (field name: features)
              <input
                type="file"
                accept=".csv,text/csv"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
              />
            </label>
          )}

          <button type="submit" disabled={loading}>
            {loading ? 'Running Inference...' : 'Run Prediction'}
          </button>
          {loading ? (
            <>
              <p className="timer">Inference timer: {elapsedLabel}</p>
              <button className="stop-button" type="button" onClick={handleStop}>
                Stop Request
              </button>
            </>
          ) : null}
        </form>
      </main>

      <section className="panel">
        <h2>Prediction Response</h2>
        {error ? <p className="error">{error}</p> : null}
        <pre>{result ? JSON.stringify(result, null, 2) : 'No response yet.'}</pre>
      </section>

      <section className="panel">
        <h2>CSV Conversions</h2>
        {mode === 'json' ? (
          <>
            <p className="timer">Input JSON to flattened CSV</p>
            {inputCsv ? (
              <>
                <button className="secondary-button" type="button" onClick={() => downloadText('input_json_flattened.csv', inputCsv)}>
                  Download Input CSV
                </button>
                <pre className="csv-preview">{inputCsv}</pre>
              </>
            ) : (
              <p className="error">Input JSON is not valid yet.</p>
            )}
          </>
        ) : (
          <p className="timer">Switch to JSON mode to preview input JSON to CSV conversion.</p>
        )}

        <p className="timer">Output JSON to CSV tables</p>
        {outputResultsCsv ? (
          <>
            <button className="secondary-button" type="button" onClick={() => downloadText('prediction_results.csv', outputResultsCsv)}>
              Download Results CSV
            </button>
            <pre className="csv-preview">{outputResultsCsv}</pre>
          </>
        ) : null}
        {outputFeaturesCsv ? (
          <>
            <button className="secondary-button" type="button" onClick={() => downloadText('prediction_feature_importance.csv', outputFeaturesCsv)}>
              Download Feature CSV
            </button>
            <pre className="csv-preview">{outputFeaturesCsv}</pre>
          </>
        ) : null}
        {!outputResultsCsv && !outputFeaturesCsv ? <p className="timer">Run inference to generate output CSV previews.</p> : null}
      </section>

      <section className="panel">
        <h2>API Endpoints</h2>
        <pre>{`GET  /health\nPOST /classify/<version>\nGET  /docs\nGET  /openapi.json\nGET  /openapi`}</pre>
      </section>

      <footer className="footer">Developed by Shalabh Suman</footer>
    </div>
  )
}

export default App

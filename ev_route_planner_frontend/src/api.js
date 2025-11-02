// Simple API helper using fetch. No external deps required.
// Assumptions:
// - EV models available at GET http://127.0.0.1:8000/ev-models (returns array)
// - Prediction endpoint at POST http://127.0.0.1:8000/predict-route

const BASE = 'http://127.0.0.1:8000'

export async function getEvModels() {
  try {
    const res = await fetch(`${BASE}/ev-models`)
    if (!res.ok) {
      const text = await res.text()
      console.error('getEvModels failed', res.status, text)
      return { error: `Failed to load EV models: ${res.status}` }
    }
    const data = await res.json()
    return data.models || []
  } catch (err) {
    console.error('getEvModels error', err)
    return { error: 'Failed to fetch EV models' }
  }
}

export async function getPrediction(from_location, to_location, ev_model_id, battery_percent) {
  try {
    const payload = { from_location, to_location, ev_model_id, battery_percent }
    const res = await fetch(`${BASE}/predict-route`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })

    if (!res.ok) {
      const text = await res.text()
      console.error('Prediction API response not ok', res.status, text)
      return { error: `Prediction API failed: ${res.status}` }
    }

    const data = await res.json()
    return data
  } catch (error) {
    console.error('Prediction API Error:', error)
    return { error: 'Failed to fetch prediction' }
  }
}

// If you prefer axios, replace fetch calls above with axios and ensure it's in package.json
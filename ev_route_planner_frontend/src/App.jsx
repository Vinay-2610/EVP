import { useState, useEffect } from 'react'
import { getEvModels, getPrediction } from './api'
import Map from './Map'
import PlaceAutocomplete from './PlaceAutocomplete'

function App() {
  const [evModels, setEvModels] = useState([])
  const [selectedModel, setSelectedModel] = useState(null)
  const [batteryPercent, setBatteryPercent] = useState(80)
  const [fromLocation, setFromLocation] = useState('')
  const [toLocation, setToLocation] = useState('')
  const [fromCoords, setFromCoords] = useState(null)
  const [toCoords, setToCoords] = useState(null)
  const [routeResult, setRouteResult] = useState(null)
  const [previewRoute, setPreviewRoute] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [darkMode, setDarkMode] = useState(true)
  const [chargerFilter, setChargerFilter] = useState('all')

  useEffect(() => {
    async function loadModels() {
      const data = await getEvModels()
      if (data.error) {
        setError(data.error)
      } else {
        setEvModels(data)
        if (data.length > 0) setSelectedModel(data[0])
      }
    }
    loadModels()
  }, [])

  const handleGetRoute = async () => {
    if (!fromLocation || !toLocation || !selectedModel) {
      setError('Please fill all fields')
      return
    }
    setLoading(true)
    setError(null)
    const result = await getPrediction(fromLocation, toLocation, selectedModel.ev_model_id, batteryPercent)
    setLoading(false)
    if (result.error) {
      setError(result.error)
    } else {
      setRouteResult(result)
    }
  }

  const handleClear = () => {
    setFromLocation('')
    setToLocation('')
    setFromCoords(null)
    setToCoords(null)
    setRouteResult(null)
    setPreviewRoute(null)
    setError(null)
  }

  // Auto-fetch route preview when both locations are selected
  useEffect(() => {
    if (fromCoords && toCoords) {
      setPreviewRoute({
        path: [[fromCoords.lat, fromCoords.lng], [toCoords.lat, toCoords.lng]]
      })
    } else {
      setPreviewRoute(null)
    }
  }, [fromCoords, toCoords])

  return (
    <div className={`min-h-screen flex ${darkMode ? 'bg-gray-900 text-white' : 'bg-gray-50 text-gray-900'}`}>
      {/* Left Sidebar */}
      <div className={`w-80 ${darkMode ? 'bg-gray-800' : 'bg-white'} shadow-lg flex flex-col z-10`}>
        {/* Header */}
        <div className="p-6 border-b border-gray-700">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <img 
                src="/ev_route_planner.jpg" 
                alt="EV Route Planner Logo" 
                className="w-16 h-16 object-contain rounded-lg"
              />
              <span className="text-xl font-bold">EV Route Planner</span>
            </div>
            <button
              onClick={() => setDarkMode(!darkMode)}
              className="p-2 rounded-full hover:bg-gray-700 transition"
            > 
              {darkMode ? '☀️' : '🌙'}
            </button>
          </div>
        </div>

        {/* Controls */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Charger Type Filter */}
          <div>
            <label className="block text-sm font-medium mb-2">CHARGER TYPE</label>
            <div className="flex gap-2">
              <button
                onClick={() => setChargerFilter('all')}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                  chargerFilter === 'all'
                    ? 'bg-cyan-500 text-white'
                    : darkMode ? 'bg-gray-700 text-gray-300' : 'bg-gray-200 text-gray-700'
                }`}
              >
                ALL
              </button>
              <button
                onClick={() => setChargerFilter('mega')}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                  chargerFilter === 'mega'
                    ? 'bg-cyan-500 text-white'
                    : darkMode ? 'bg-gray-700 text-gray-300' : 'bg-gray-200 text-gray-700'
                }`}
              >
                mega
              </button>
            </div>
          </div>

          {/* EV Model Selection */}
          <div>
            <label className="block text-sm font-medium mb-2">EV Model</label>
            <select
              value={selectedModel?.ev_model_id || ''}
              onChange={(e) => {
                const model = evModels.find(m => m.ev_model_id === parseInt(e.target.value))
                setSelectedModel(model)
              }}
              className={`w-full px-4 py-3 rounded-lg ${
                darkMode ? 'bg-gray-700 text-white' : 'bg-gray-100 text-gray-900'
              } border-none focus:ring-2 focus:ring-cyan-500`}
            >
              {evModels.map(model => (
                <option key={model.ev_model_id} value={model.ev_model_id}>
                  {model.model_name} - {model.max_range}km
                </option>
              ))}
            </select>
          </div>

          {/* Battery Percentage */}
          <div>
            <label className="block text-sm font-medium mb-2">
              Battery: {batteryPercent}%
            </label>
            <input
              type="range"
              min="10"
              max="100"
              value={batteryPercent}
              onChange={(e) => setBatteryPercent(parseInt(e.target.value))}
              className="w-full accent-cyan-500"
            />
          </div>

          {/* Source */}
          <div>
            <label className="block text-sm font-medium mb-2">source</label>
            <PlaceAutocomplete
              value={fromLocation}
              onChange={setFromLocation}
              onSelect={setFromCoords}
              placeholder="Hyderabad, Telangana, India"
              darkMode={darkMode}
            />
          </div>

          {/* Destination */}
          <div>
            <label className="block text-sm font-medium mb-2">destination</label>
            <PlaceAutocomplete
              value={toLocation}
              onChange={setToLocation}
              onSelect={setToCoords}
              placeholder="Bengaluru, Karnataka, India"
              darkMode={darkMode}
            />
          </div>

          {/* Action Buttons */}
          <div className="space-y-3">
            <button
              onClick={handleGetRoute}
              disabled={loading}
              className="w-full bg-cyan-500 hover:bg-cyan-600 text-white font-medium py-3 rounded-lg transition disabled:opacity-50"
            >
              {loading ? 'Loading...' : 'get route'}
            </button>
            <button
              onClick={handleClear}
              className={`w-full ${
                darkMode ? 'bg-gray-700 hover:bg-gray-600' : 'bg-gray-200 hover:bg-gray-300'
              } font-medium py-3 rounded-lg transition`}
            >
              clear
            </button>
          </div>

          {/* Error Display */}
          {error && (
            <div className="p-4 bg-red-500 bg-opacity-20 border border-red-500 rounded-lg text-red-400 text-sm">
              {error}
            </div>
          )}
        </div>
      </div>

      {/* Map Area */}
      <div className="flex-1 relative">
        <Map result={routeResult || previewRoute} darkMode={darkMode} />
        
        {/* Back Button (top right) */}
        <button className="absolute top-4 right-4 bg-cyan-500 hover:bg-cyan-600 text-white px-6 py-2 rounded-lg font-medium shadow-lg transition flex items-center gap-2 z-10">
          back ↗
        </button>
      </div>

      {/* Right Sidebar - Trip Summary */}
      {routeResult && (
        <div className={`w-80 ${darkMode ? 'bg-gray-800' : 'bg-white'} shadow-lg p-6 z-10`}>
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold">trip summary</h2>
            <button
              onClick={() => setRouteResult(null)}
              className="text-gray-400 hover:text-white"
            >
              ✕
            </button>
          </div>

          <div className="space-y-4">
            <div className="flex justify-between items-center py-3 border-b border-gray-700">
              <span className="text-gray-400">total distance:</span>
              <span className="font-semibold">{routeResult.total_distance_km} km</span>
            </div>

            <div className="flex justify-between items-center py-3 border-b border-gray-700">
              <span className="text-gray-400">estimated range:</span>
              <span className="font-semibold">{routeResult.estimated_range_km} km</span>
            </div>

            <div className="flex justify-between items-center py-3 border-b border-gray-700">
              <span className="text-gray-400">total chargers nearby:</span>
              <span className="font-semibold">{routeResult.charging_suggestions?.count || 0}</span>
            </div>

            {routeResult.total_distance_km > routeResult.estimated_range_km && (
              <div className="p-4 bg-yellow-500 bg-opacity-20 border border-yellow-500 rounded-lg text-black-900 text-sm">
                ⚠️ Warning: Distance exceeds estimated range. Charging stops recommended.
              </div>
            )}

            {/* Charging Stations List */}
            {routeResult.charging_suggestions?.stations?.length > 0 && (
              <div className="mt-6">
                <h3 className="font-semibold mb-3">Charging Stations</h3>
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {routeResult.charging_suggestions.stations.slice(0, 10).map((station, idx) => (
                    <div
                      key={idx}
                      className={`p-3 rounded-lg ${
                        darkMode ? 'bg-gray-700' : 'bg-gray-100'
                      }`}
                    >
                      <div className="font-medium text-sm">{station.name}</div>
                      <div className="text-xs text-gray-400 mt-1">{station.address}</div>
                      {station.rating && (
                        <div className="text-xs text-cyan-400 mt-1">⭐ {station.rating}</div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default App

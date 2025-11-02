import { useState, useEffect, useRef } from 'react'

function PlaceAutocomplete({ value, onChange, placeholder, darkMode, onSelect }) {
  const [suggestions, setSuggestions] = useState([])
  const [showSuggestions, setShowSuggestions] = useState(false)
  const wrapperRef = useRef(null)

  useEffect(() => {
    function handleClickOutside(event) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target)) {
        setShowSuggestions(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  useEffect(() => {
    if (value.length < 3) {
      setSuggestions([])
      return
    }

    const timer = setTimeout(async () => {
      try {
        const response = await fetch(
          `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(value)}&countrycodes=in&limit=5&addressdetails=1`
        )
        const data = await response.json()
        setSuggestions(data)
        setShowSuggestions(true)
      } catch (error) {
        console.error('Error fetching suggestions:', error)
      }
    }, 300)

    return () => clearTimeout(timer)
  }, [value])

  const handleSelect = (place) => {
    onChange(place.display_name)
    if (onSelect) {
      onSelect({ lat: parseFloat(place.lat), lng: parseFloat(place.lon) })
    }
    setSuggestions([])
    setShowSuggestions(false)
  }

  return (
    <div ref={wrapperRef} className="relative">
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className={`w-full px-4 py-3 rounded-lg ${
          darkMode ? 'bg-gray-700 text-white placeholder-gray-400' : 'bg-gray-100 text-gray-900'
        } border-none focus:ring-2 focus:ring-cyan-500`}
      />
      
      {showSuggestions && suggestions.length > 0 && (
        <div className={`absolute z-50 w-full mt-1 rounded-lg shadow-lg max-h-60 overflow-y-auto ${
          darkMode ? 'bg-gray-700' : 'bg-white'
        }`}>
          {suggestions.map((place, idx) => (
            <div
              key={idx}
              onClick={() => handleSelect(place)}
              className={`px-4 py-3 cursor-pointer border-b ${
                darkMode ? 'border-gray-600 hover:bg-gray-600' : 'border-gray-200 hover:bg-gray-100'
              }`}
            >
              <div className="text-sm font-medium">{place.display_name}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default PlaceAutocomplete

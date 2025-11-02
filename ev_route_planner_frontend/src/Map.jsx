import { useEffect, useRef, useState } from 'react'

// Check if Google Maps is already loaded
const isGoogleMapsLoaded = () => {
  return typeof window !== 'undefined' && window.google && window.google.maps
}

// Load Google Maps script
const loadGoogleMapsScript = (apiKey) => {
  return new Promise((resolve, reject) => {
    // If already loaded, resolve immediately
    if (isGoogleMapsLoaded()) {
      resolve(window.google.maps)
      return
    }

    // Check if script is already being loaded
    const existingScript = document.querySelector('script[src*="maps.googleapis.com"]')
    if (existingScript) {
      existingScript.addEventListener('load', () => {
        if (isGoogleMapsLoaded()) {
          resolve(window.google.maps)
        } else {
          reject(new Error('Google Maps loaded but not available'))
        }
      })
      return
    }

    // Create callback
    const callbackName = 'initGoogleMaps'
    window[callbackName] = () => {
      if (isGoogleMapsLoaded()) {
        resolve(window.google.maps)
        delete window[callbackName]
      } else {
        reject(new Error('Google Maps callback fired but maps not available'))
      }
    }

    // Create and append script
    const script = document.createElement('script')
    script.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}&libraries=places&callback=${callbackName}`
    script.async = true
    script.defer = true
    script.onerror = () => {
      delete window[callbackName]
      reject(new Error('Failed to load Google Maps script'))
    }
    
    document.head.appendChild(script)
  })
}

const darkMapStyles = [
  { elementType: "geometry", stylers: [{ color: "#242f3e" }] },
  { elementType: "labels.text.stroke", stylers: [{ color: "#242f3e" }] },
  { elementType: "labels.text.fill", stylers: [{ color: "#746855" }] },
  {
    featureType: "administrative.locality",
    elementType: "labels.text.fill",
    stylers: [{ color: "#d59563" }],
  },
  {
    featureType: "poi",
    elementType: "labels.text.fill",
    stylers: [{ color: "#d59563" }],
  },
  {
    featureType: "poi.park",
    elementType: "geometry",
    stylers: [{ color: "#263c3f" }],
  },
  {
    featureType: "road",
    elementType: "geometry",
    stylers: [{ color: "#38414e" }],
  },
  {
    featureType: "road.highway",
    elementType: "geometry",
    stylers: [{ color: "#746855" }],
  },
  {
    featureType: "water",
    elementType: "geometry",
    stylers: [{ color: "#17263c" }],
  },
]

function Map({ result, darkMode = true }) {
  const mapContainerRef = useRef(null)
  const mapInstanceRef = useRef(null)
  const markersRef = useRef([])
  const polylineRef = useRef(null)
  const directionsRendererRef = useRef(null)
  const userLocationMarkerRef = useRef(null)
  
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)
  const [userLocation, setUserLocation] = useState(null)

  // Initialize map
  useEffect(() => {
    const apiKey = import.meta.env.VITE_GOOGLE_MAPS_KEY
    
    if (!apiKey) {
      setError('Google Maps API key not found')
      setIsLoading(false)
      return
    }

    let isMounted = true

    const initMap = async () => {
      try {
        await loadGoogleMapsScript(apiKey)
        
        if (!isMounted || !mapContainerRef.current) return

        // Create map
        mapInstanceRef.current = new window.google.maps.Map(mapContainerRef.current, {
          center: { lat: 20.5937, lng: 78.9629 }, // Center of India
          zoom: 5,
          styles: darkMode ? darkMapStyles : [],
          disableDefaultUI: false,
          zoomControl: true,
          mapTypeControl: false,
          streetViewControl: false,
          fullscreenControl: false,
        })

        if (isMounted) {
          setIsLoading(false)
          setError(null)
        }
      } catch (err) {
        console.error('Map initialization error:', err)
        if (isMounted) {
          setError(err.message || 'Failed to load map')
          setIsLoading(false)
        }
      }
    }

    initMap()

    return () => {
      isMounted = false
    }
  }, [darkMode])

  // Track user location
  useEffect(() => {
    if (!navigator.geolocation) return

    const watchId = navigator.geolocation.watchPosition(
      (position) => {
        const pos = {
          lat: position.coords.latitude,
          lng: position.coords.longitude
        }
        setUserLocation(pos)
      },
      (error) => {
        console.error('Error getting location:', error)
      },
      { enableHighAccuracy: true, maximumAge: 10000 }
    )

    return () => navigator.geolocation.clearWatch(watchId)
  }, [])

  // Update user location marker
  useEffect(() => {
    if (!userLocation || !mapInstanceRef.current || !window.google) return

    const map = mapInstanceRef.current

    if (userLocationMarkerRef.current) {
      userLocationMarkerRef.current.setPosition(userLocation)
    } else {
      userLocationMarkerRef.current = new window.google.maps.Marker({
        position: userLocation,
        map,
        icon: {
          path: window.google.maps.SymbolPath.CIRCLE,
          scale: 10,
          fillColor: '#3b82f6',
          fillOpacity: 1,
          strokeColor: 'white',
          strokeWeight: 3,
        },
        title: 'Your Location'
      })
    }
  }, [userLocation])

  // Update map with route result
  useEffect(() => {
    if (!result || !mapInstanceRef.current || !window.google) return

    const map = mapInstanceRef.current

    // Clear previous markers and polyline
    markersRef.current.forEach(marker => marker.setMap(null))
    markersRef.current = []
    
    if (polylineRef.current) {
      polylineRef.current.setMap(null)
      polylineRef.current = null
    }

    if (directionsRendererRef.current) {
      directionsRendererRef.current.setMap(null)
    }

    // If we have path data, use Google Directions API for real route
    if (Array.isArray(result.path) && result.path.length >= 2) {
      const origin = { lat: result.path[0][0], lng: result.path[0][1] }
      const destination = { lat: result.path[result.path.length - 1][0], lng: result.path[result.path.length - 1][1] }

      const directionsService = new window.google.maps.DirectionsService()
      
      directionsService.route(
        {
          origin,
          destination,
          travelMode: window.google.maps.TravelMode.DRIVING,
        },
        (response, status) => {
          if (status === 'OK') {
            // Create or update directions renderer
            if (!directionsRendererRef.current) {
              directionsRendererRef.current = new window.google.maps.DirectionsRenderer({
                suppressMarkers: false,
                polylineOptions: {
                  strokeColor: '#10b981',
                  strokeOpacity: 0.8,
                  strokeWeight: 6,
                }
              })
            }
            directionsRendererRef.current.setMap(map)
            directionsRendererRef.current.setDirections(response)
          } else {
            console.error('Directions request failed:', status)
            // Fallback to simple polyline
            const path = result.path.map(([lat, lng]) => ({ lat, lng }))
            polylineRef.current = new window.google.maps.Polyline({
              path,
              geodesic: true,
              strokeColor: '#10b981',
              strokeOpacity: 0.9,
              strokeWeight: 5,
            })
            polylineRef.current.setMap(map)
            
            const bounds = new window.google.maps.LatLngBounds()
            path.forEach(point => bounds.extend(point))
            map.fitBounds(bounds)
          }
        }
      )
    }

    // Add charging station markers with images
    const stations = result?.charging_suggestions?.stations || []
    const placesService = new window.google.maps.places.PlacesService(map)
    
    stations.forEach((station) => {
      if (!station.lat || !station.lng) return
      
      const marker = new window.google.maps.Marker({
        position: { lat: station.lat, lng: station.lng },
        map,
        title: station.name,
        icon: {
          path: window.google.maps.SymbolPath.CIRCLE,
          scale: 8,
          fillColor: '#06b6d4',
          fillOpacity: 1,
          strokeColor: 'white',
          strokeWeight: 2,
        }
      })
      
      marker.addListener('click', () => {
        // Search for place details to get photos
        const request = {
          location: { lat: station.lat, lng: station.lng },
          radius: 50,
          keyword: station.name
        }
        
        placesService.nearbySearch(request, (results, status) => {
          if (status === window.google.maps.places.PlacesServiceStatus.OK && results[0]) {
            const place = results[0]
            
            // Get place details for photos
            placesService.getDetails(
              { placeId: place.place_id, fields: ['photos', 'name', 'rating', 'formatted_address'] },
              (placeDetails, detailsStatus) => {
                let photoUrl = ''
                
                if (detailsStatus === window.google.maps.places.PlacesServiceStatus.OK && 
                    placeDetails.photos && placeDetails.photos.length > 0) {
                  photoUrl = placeDetails.photos[0].getUrl({ maxWidth: 300, maxHeight: 200 })
                }
                
                const infoWindow = new window.google.maps.InfoWindow({
                  content: `
                    <div style="color: #1f2937; padding: 8px; max-width: 300px;">
                      ${photoUrl ? `<img src="${photoUrl}" style="width: 100%; height: 150px; object-fit: cover; border-radius: 8px; margin-bottom: 8px;" alt="${station.name}"/>` : ''}
                      <strong style="font-size: 14px;">${station.name}</strong><br/>
                      <span style="font-size: 12px; color: #6b7280;">${station.address || ''}</span>
                      ${station.rating ? `<br/><span style="color: #06b6d4; font-size: 13px;">⭐ ${station.rating}</span>` : ''}
                    </div>
                  `
                })
                
                infoWindow.open(map, marker)
              }
            )
          } else {
            // Fallback without image
            const infoWindow = new window.google.maps.InfoWindow({
              content: `
                <div style="color: #1f2937; padding: 8px;">
                  <strong>${station.name}</strong><br/>
                  <span style="font-size: 12px;">${station.address || ''}</span>
                  ${station.rating ? `<br/><span style="color: #06b6d4;">⭐ ${station.rating}</span>` : ''}
                </div>
              `
            })
            infoWindow.open(map, marker)
          }
        })
      })
      
      markersRef.current.push(marker)
    })
  }, [result])

  if (error) {
    return (
      <div className="absolute inset-0 flex items-center justify-center bg-gray-800">
        <div className="text-center p-6">
          <p className="text-red-400 text-lg mb-2">Map failed to load</p>
          <p className="text-sm text-gray-400 mb-4">{error}</p>
          <button 
            onClick={() => window.location.reload()} 
            className="px-4 py-2 bg-cyan-500 hover:bg-cyan-600 text-white rounded-lg transition"
          >
            Refresh Page
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="absolute inset-0">
      <div 
        ref={mapContainerRef} 
        className="w-full h-full"
        style={{ minHeight: '400px' }}
      />
      
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-800 bg-opacity-90">
          <div className="text-center p-6">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500 mx-auto mb-4"></div>
            <p className="text-gray-300">Loading map...</p>
          </div>
        </div>
      )}
    </div>
  )
}

export default Map

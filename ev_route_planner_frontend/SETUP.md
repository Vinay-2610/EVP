# EV Route Planner Frontend Setup

## Prerequisites
- Node.js (v16 or higher)
- npm or yarn
- Google Maps API Key

## Installation

1. Install dependencies:
```bash
npm install
```

2. Create a `.env` file in the root directory:
```env
VITE_GOOGLE_MAPS_KEY=your_google_maps_api_key_here
```

3. Make sure your backend is running on `http://127.0.0.1:8000`

## Running the Application

Start the development server:
```bash
npm run dev
```

The application will be available at `http://localhost:5173`

## Features

- **Dark/Light Mode Toggle**: Switch between dark and light themes
- **EV Model Selection**: Choose from available EV models in your database
- **Battery Level Control**: Set your current battery percentage
- **Route Planning**: Enter source and destination to get optimal routes
- **Charging Station Finder**: Automatically finds charging stations along your route
- **Trip Summary**: View distance, estimated range, and charging options
- **Interactive Map**: Visualize your route with markers for start, end, and charging stations

## Design

The frontend is designed to match the TATA EV Maps interface with:
- Clean, modern dark theme
- Intuitive left sidebar for controls
- Large interactive map area
- Right sidebar for trip summary
- Responsive design elements
- Smooth animations and transitions

## API Endpoints Used

- `GET /ev-models` - Fetch available EV models
- `POST /predict-route` - Get route prediction with charging stations

## Troubleshooting

- If the map doesn't load, check your Google Maps API key in `.env`
- If no EV models appear, ensure your backend is running and database is populated
- If routes don't calculate, verify the backend A* algorithm is working correctly

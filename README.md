# EV Route Planner

An intelligent EV route planning application with charging station recommendations.

## Features
- Route planning with A* algorithm
- Real-time charging station suggestions
- Multiple EV model support
- Battery range calculations

## Tech Stack
- **Backend**: FastAPI, Python
- **Frontend**: React, TypeScript
- **Database**: Supabase
- **APIs**: Google Maps API

## Deployment on Railway

### Prerequisites
- GitHub account
- Google Maps API Key
- Supabase account

### Steps

1. **Fork/Clone this repository**

2. **Go to Railway**
   - Visit https://railway.app
   - Sign in with GitHub
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose this repository

3. **Add Environment Variables**
   In Railway dashboard, go to Variables tab and add:
   ```
   GOOGLE_MAPS_API_KEY=your_google_maps_api_key
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_anon_key
   PORT=8000
   ```

4. **Deploy**
   - Railway will automatically detect the configuration
   - Wait for deployment to complete
   - Your API will be available at the provided Railway URL

## Local Development

### Backend Setup

1. Navigate to backend directory:
   ```bash
   cd ev_route_planner_backend/backend
   ```

2. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create `.env` file:
   ```
   GOOGLE_MAPS_API_KEY=your_key
   SUPABASE_URL=your_url
   SUPABASE_KEY=your_key
   ```

5. Run the server:
   ```bash
   uvicorn main:app --reload
   ```

### Frontend Setup

1. Navigate to frontend directory:
   ```bash
   cd ev_route_planner_frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Run development server:
   ```bash
   npm run dev
   ```

## API Endpoints

- `GET /` - Health check
- `POST /trip` - Create a new trip
- `GET /trips` - Get all trips
- `GET /ev-models` - List available EV models
- `POST /predict-route` - Get route prediction with charging stations
- `GET /nearest-charging-stations` - Find nearby charging stations

## License
MIT

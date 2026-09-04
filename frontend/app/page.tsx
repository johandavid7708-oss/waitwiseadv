'use client';

import { useState, useEffect, useCallback } from 'react';
import WaitWiseDashboard from '@/components/WaitWiseDashboard';
import HeatmapMap from '@/components/HeatmapMap';
import PredictionPanel from '@/components/PredictionPanel';
import RecommendationEngine from '@/components/RecommendationEngine';
import RealTimeUpdates from '@/components/RealTimeUpdates';

interface Location {
  id: string;
  name: string;
  description: string;
  category: string;
  latitude: number;
  longitude: number;
  current_crowd_level?: number;
  capacity?: number;
}

interface Prediction {
  location_id: string;
  location_name: string;
  prediction: {
    predicted_crowd_level: number;
    crowd_level_text: string;
    predicted_wait_time: number;
    confidence_score: number;
    prediction_horizon_minutes: number;
    reasoning: string;
  };
}

export default function Home() {
  const [locations, setLocations] = useState<Location[]>([]);
  const [selectedLocation, setSelectedLocation] = useState<Location | null>(null);
  const [predictions, setPredictions] = useState<Map<string, Prediction>>(new Map());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  // Fetch locations on mount
  useEffect(() => {
    fetchLocations();
  }, []);

  // Auto-refresh predictions every 30 seconds
  useEffect(() => {
    if (!autoRefresh || locations.length === 0) return;

    const interval = setInterval(() => {
      locations.forEach(location => {
        fetchPrediction(location.id);
      });
    }, 30000);

    return () => clearInterval(interval);
  }, [autoRefresh, locations]);

  // Fetch predictions for selected location
  useEffect(() => {
    if (selectedLocation) {
      fetchPrediction(selectedLocation.id);
    }
  }, [selectedLocation]);

  const fetchLocations = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_URL}/api/v1/locations?include_crowd=true`);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch locations: ${response.status}`);
      }
      
      const data = await response.json();
      setLocations(data.locations || []);
      
      // Select first location by default
      if (data.locations && data.locations.length > 0) {
        setSelectedLocation(data.locations[0]);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch locations';
      setError(errorMessage);
      console.error('Error fetching locations:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchPrediction = async (locationId: string) => {
    try {
      const response = await fetch(
        `${API_URL}/api/v1/predictions/${locationId}?minutes_ahead=30`
      );
      
      if (!response.ok) {
        throw new Error(`Failed to fetch prediction for ${locationId}`);
      }
      
      const data: Prediction = await response.json();
      
      setPredictions(prev => {
        const newMap = new Map(prev);
        newMap.set(locationId, data);
        return newMap;
      });
    } catch (err) {
      console.error(`Error fetching prediction for ${locationId}:`, err);
    }
  };

  const submitCrowdReport = async (
    locationId: string,
    crowdLevel: number,
    waitTime?: number,
    comment?: string
  ) => {
    try {
      const response = await fetch(`${API_URL}/api/v1/reports`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          location_id: locationId,
          crowd_level: crowdLevel,
          wait_time_minutes: waitTime,
          comment: comment,
          confidence: 0.8,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to submit report');
      }

      // Refresh locations and predictions
      await fetchLocations();
      if (selectedLocation) {
        await fetchPrediction(selectedLocation.id);
      }

      return true;
    } catch (err) {
      console.error('Error submitting report:', err);
      return false;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-emerald-500 mx-auto mb-4"></div>
          <p className="text-white text-lg">Loading WaitWise...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 flex items-center justify-center">
        <div className="bg-red-900/50 border border-red-500 rounded-lg p-6 max-w-md">
          <h2 className="text-red-200 font-bold mb-2">Connection Error</h2>
          <p className="text-red-100 text-sm mb-4">{error}</p>
          <p className="text-red-200 text-sm mb-4">
            Make sure the backend is running at <code className="bg-black/30 px-2 py-1 rounded">{API_URL}</code>
          </p>
          <button
            onClick={fetchLocations}
            className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded transition"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const currentPrediction = selectedLocation 
    ? predictions.get(selectedLocation.id) 
    : null;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Header */}
      <div className="border-b border-slate-700 bg-slate-900/50 backdrop-blur-sm sticky top-0 z-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-emerald-400 to-emerald-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold">W</span>
              </div>
              <div>
                <h1 className="text-white font-bold text-xl">WaitWise</h1>
                <p className="text-slate-400 text-xs">Know Before You Go</p>
              </div>
            </div>
            
            <div className="flex items-center gap-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={autoRefresh}
                  onChange={(e) => setAutoRefresh(e.target.checked)}
                  className="w-4 h-4"
                />
                <span className="text-slate-300 text-sm">Auto-refresh</span>
              </label>
              <button
                onClick={fetchLocations}
                className="px-3 py-1 bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 rounded text-sm transition"
              >
                Refresh
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Sidebar - Location List */}
          <div className="lg:col-span-1">
            <div className="bg-slate-800 rounded-lg border border-slate-700 overflow-hidden">
              <div className="p-4 border-b border-slate-700 bg-slate-900/50">
                <h2 className="text-white font-semibold">Locations</h2>
                <p className="text-slate-400 text-xs mt-1">{locations.length} available</p>
              </div>
              <div className="divide-y divide-slate-700 max-h-96 overflow-y-auto">
                {locations.map(location => (
                  <button
                    key={location.id}
                    onClick={() => setSelectedLocation(location)}
                    className={`w-full text-left p-3 transition ${
                      selectedLocation?.id === location.id
                        ? 'bg-emerald-600/30 border-l-2 border-emerald-500'
                        : 'hover:bg-slate-700/50'
                    }`}
                  >
                    <div className="font-medium text-white text-sm">{location.name}</div>
                    <div className="text-slate-400 text-xs mt-1">{location.category}</div>
                    {location.current_crowd_level && (
                      <div className="mt-2 flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full bg-emerald-500"></div>
                        <span className="text-xs text-slate-300">
                          Level {Math.round(location.current_crowd_level)}/5
                        </span>
                      </div>
                    )}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Main Content Area */}
          <div className="lg:col-span-3 space-y-6">
            {selectedLocation && (
              <>
                {/* Map and Prediction */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  {/* Heatmap */}
                  <div className="md:col-span-2">
                    <HeatmapMap
                      locations={locations}
                      selectedLocationId={selectedLocation.id}
                      predictions={predictions}
                    />
                  </div>

                  {/* Prediction Panel */}
                  <div>
                    {currentPrediction ? (
                      <PredictionPanel
                        prediction={currentPrediction}
                        location={selectedLocation}
                      />
                    ) : (
                      <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
                        <p className="text-slate-400 text-sm">Loading prediction...</p>
                      </div>
                    )}
                  </div>
                </div>

                {/* Recommendations */}
                <RecommendationEngine
                  selectedLocationId={selectedLocation.id}
                  selectedLocationName={selectedLocation.name}
                  predictions={predictions}
                  apiUrl={API_URL}
                />

                {/* Dashboard with Report Submission */}
                <WaitWiseDashboard
                  selectedLocation={selectedLocation}
                  onSubmitReport={submitCrowdReport}
                  locations={locations}
                />

                {/* Real-time Updates */}
                <RealTimeUpdates
                  selectedLocationId={selectedLocation.id}
                  apiUrl={API_URL}
                />
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

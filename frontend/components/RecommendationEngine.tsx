'use client';

import { useState, useEffect } from 'react';

interface Recommendation {
  recommended_location_id: string;
  recommended_location_name: string;
  reason: string;
  wait_time_savings: number;
  distance_km: number;
  travel_time_minutes: number;
  recommendation_score: number;
}

interface Props {
  selectedLocationId: string;
  selectedLocationName: string;
  predictions: Map<string, any>;
  apiUrl: string;
}

export default function RecommendationEngine({
  selectedLocationId,
  selectedLocationName,
  predictions,
  apiUrl,
}: Props) {
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (selectedLocationId) {
      fetchRecommendations();
    }
  }, [selectedLocationId]);

  const fetchRecommendations = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `${apiUrl}/api/v1/recommendations?location_id=${selectedLocationId}&max_distance_km=2&limit=5`,
        { method: 'POST' }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch recommendations');
      }

      const data = await response.json();
      setRecommendations(data.recommendations || []);
    } catch (err) {
      console.error('Error fetching recommendations:', err);
      setRecommendations([]);
    } finally {
      setLoading(false);
    }
  };

  const getReasonIcon = (reason: string) => {
    switch (reason) {
      case 'less_crowded':
        return '👥';
      case 'closer':
        return '📍';
      case 'quicker_travel':
        return '🚗';
      case 'better_alternative':
        return '✨';
      default:
        return '→';
    }
  };

  const getReasonText = (reason: string) => {
    switch (reason) {
      case 'less_crowded':
        return 'Less crowded';
      case 'closer':
        return 'Closer to you';
      case 'quicker_travel':
        return 'Quicker travel';
      case 'better_alternative':
        return 'Better option';
      default:
        return 'Recommended';
    }
  };

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-lg overflow-hidden">
      <div className="p-4 border-b border-slate-700 bg-slate-900/50">
        <h2 className="text-white font-semibold">Smart Alternatives</h2>
        <p className="text-slate-400 text-xs mt-1">
          Instead of {selectedLocationName}
        </p>
      </div>

      <div className="p-4">
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-emerald-500"></div>
          </div>
        ) : recommendations.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-slate-400 text-sm">
              No better alternatives found within 2km
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {recommendations.map((rec) => (
              <div
                key={rec.recommended_location_id}
                className="bg-slate-700/50 border border-slate-600 rounded-lg p-3 hover:border-emerald-600/50 transition group cursor-pointer"
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1">
                    <div className="font-semibold text-white text-sm group-hover:text-emerald-300 transition">
                      {rec.recommended_location_name}
                    </div>
                    <div className="flex items-center gap-2 mt-1 text-xs">
                      <span className="text-2xl">{getReasonIcon(rec.reason)}</span>
                      <span className="text-slate-400">{getReasonText(rec.reason)}</span>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-emerald-400 font-bold text-sm">
                      {Math.round(rec.recommendation_score)}%
                    </div>
                    <div className="text-slate-500 text-xs">Score</div>
                  </div>
                </div>

                {/* Benefits */}
                <div className="grid grid-cols-3 gap-2 text-xs">
                  <div className="bg-slate-800/50 rounded p-2 text-center">
                    <div className="text-emerald-400 font-bold">{rec.wait_time_savings}</div>
                    <div className="text-slate-400">min saved</div>
                  </div>
                  <div className="bg-slate-800/50 rounded p-2 text-center">
                    <div className="text-blue-400 font-bold">{rec.distance_km.toFixed(1)}km</div>
                    <div className="text-slate-400">away</div>
                  </div>
                  <div className="bg-slate-800/50 rounded p-2 text-center">
                    <div className="text-purple-400 font-bold">{rec.travel_time_minutes}</div>
                    <div className="text-slate-400">travel</div>
                  </div>
                </div>

                {/* Choose Button */}
                <button className="w-full mt-3 px-3 py-2 bg-emerald-600/20 hover:bg-emerald-600/40 text-emerald-300 rounded text-xs font-medium transition">
                  View Alternative
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

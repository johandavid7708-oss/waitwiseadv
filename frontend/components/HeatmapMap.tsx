'use client';

import { useMemo } from 'react';

interface Location {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
  current_crowd_level?: number;
  category: string;
}

interface Prediction {
  location_id: string;
  prediction: {
    predicted_crowd_level: number;
  };
}

interface Props {
  locations: Location[];
  selectedLocationId?: string;
  predictions: Map<string, Prediction>;
}

export default function HeatmapMap({ locations, selectedLocationId, predictions }: Props) {
  const crowdColors = useMemo(() => ({
    1: '#10b981', // green - empty
    2: '#84cc16', // lime - quiet
    3: '#f59e0b', // amber - moderate
    4: '#ef4444', // red - crowded
    5: '#7c2d12', // dark red - packed
  }), []);

  // Calculate dynamic bounds from locations
  const bounds = useMemo(() => {
    if (locations.length === 0) {
      return { minLat: -85, maxLat: 85, minLng: -180, maxLng: 180, centerLat: 0, centerLng: 0 };
    }
    
    const lats = locations.map(l => l.latitude);
    const lngs = locations.map(l => l.longitude);
    
    const minLat = Math.min(...lats);
    const maxLat = Math.max(...lats);
    const minLng = Math.min(...lngs);
    const maxLng = Math.max(...lngs);
    
    // Add 10% padding
    const latPadding = (maxLat - minLat) * 0.1 || 1;
    const lngPadding = (maxLng - minLng) * 0.1 || 1;
    
    return {
      minLat: minLat - latPadding,
      maxLat: maxLat + latPadding,
      minLng: minLng - lngPadding,
      maxLng: maxLng + lngPadding,
      centerLat: (minLat + maxLat) / 2,
      centerLng: (minLng + maxLng) / 2,
    };
  }, [locations]);

  const getCrowdColor = (crowdLevel: number) => {
    const level = Math.ceil(crowdLevel);
    return crowdColors[level as keyof typeof crowdColors] || '#6b7280';
  };

  const getCrowdText = (crowdLevel: number) => {
    if (crowdLevel < 1.5) return 'Empty';
    if (crowdLevel < 2.5) return 'Quiet';
    if (crowdLevel < 3.5) return 'Moderate';
    if (crowdLevel < 4.5) return 'Crowded';
    return 'Packed';
  };

  // Convert lat/lng to SVG coordinates
  const latToY = (lat: number) => {
    return ((bounds.maxLat - lat) / (bounds.maxLat - bounds.minLat)) * 400;
  };

  const lngToX = (lng: number) => {
    return ((lng - bounds.minLng) / (bounds.maxLng - bounds.minLng)) * 800;
  };

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-lg overflow-hidden">
      <div className="p-4 border-b border-slate-700 bg-slate-900/50">
        <h2 className="text-white font-semibold">Crowd Heatmap</h2>
        <p className="text-slate-400 text-xs mt-1">Real-time crowd density visualization</p>
      </div>

      <div className="relative w-full h-96 bg-gradient-to-b from-slate-700 to-slate-800 overflow-hidden">
        {/* SVG Map Background */}
        <svg className="absolute inset-0 w-full h-full" viewBox="0 0 800 400">
          {/* Grid background */}
          <defs>
            <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#1e293b" strokeWidth="0.5" />
            </pattern>
            <radialGradient id="crowdGrad1" cx="50%" cy="50%" r="50%">
              <stop offset="0%" style={{ stopColor: '#10b981', stopOpacity: 0.4 }} />
              <stop offset="100%" style={{ stopColor: '#10b981', stopOpacity: 0 }} />
            </radialGradient>
            <radialGradient id="crowdGrad5" cx="50%" cy="50%" r="50%">
              <stop offset="0%" style={{ stopColor: '#7c2d12', stopOpacity: 0.6 }} />
              <stop offset="100%" style={{ stopColor: '#7c2d12', stopOpacity: 0 }} />
            </radialGradient>
          </defs>

          {/* Background grid */}
          <rect width="800" height="400" fill="url(#grid)" />

          {/* Render location heat circles */}
          {locations.map((location, idx) => {
            const x = lngToX(location.longitude);
            const y = latToY(location.latitude);
            
            const pred = predictions.get(location.id);
            const crowdLevel = pred
              ? pred.prediction.predicted_crowd_level
              : (location.current_crowd_level || 2.5);

            const radius = 30 + (crowdLevel * 15);
            const color = getCrowdColor(crowdLevel);
            const isSelected = location.id === selectedLocationId;

            return (
              <g key={location.id}>
                {/* Heat circle */}
                <circle
                  cx={x}
                  cy={y}
                  r={radius}
                  fill={color}
                  opacity={0.2}
                />
                {/* Inner circle */}
                <circle
                  cx={x}
                  cy={y}
                  r={radius * 0.5}
                  fill={color}
                  opacity={0.4}
                />
                {/* Location marker */}
                <circle
                  cx={x}
                  cy={y}
                  r={8}
                  fill={color}
                  stroke={isSelected ? '#fff' : 'none'}
                  strokeWidth={isSelected ? 3 : 0}
                  className="transition-all"
                />
              </g>
            );
          })}
        </svg>

        {/* Location Overlay Cards */}
        <div className="absolute inset-0 pointer-events-none">
          {locations.map((location) => {
            const pred = predictions.get(location.id);
            const crowdLevel = pred
              ? pred.prediction.predicted_crowd_level
              : (location.current_crowd_level || 2.5);
            
            const x = lngToX(location.longitude);
            const y = latToY(location.latitude);

            return (
              <div
                key={location.id}
                className="absolute transform -translate-x-1/2 -translate-y-full pointer-events-auto"
                style={{
                  left: `${(x / 800) * 100}%`,
                  top: `${(y / 400) * 100}%`,
                }}
              >
                <div className="bg-slate-900 border border-slate-600 rounded px-2 py-1 text-center whitespace-nowrap text-xs hover:border-emerald-400 transition cursor-pointer -mt-12">
                  <div className="font-semibold text-white">{location.name}</div>
                  <div className="text-slate-300 text-xs">
                    <span
                      style={{ color: getCrowdColor(crowdLevel) }}
                      className="font-bold"
                    >
                      {getCrowdText(crowdLevel)}
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Legend */}
      <div className="p-4 bg-slate-900/50 border-t border-slate-700">
        <div className="text-xs text-slate-400 mb-2">Crowd Levels:</div>
        <div className="grid grid-cols-5 gap-2">
          {[
            { level: 1, name: 'Empty', color: '#10b981' },
            { level: 2, name: 'Quiet', color: '#84cc16' },
            { level: 3, name: 'Moderate', color: '#f59e0b' },
            { level: 4, name: 'Crowded', color: '#ef4444' },
            { level: 5, name: 'Packed', color: '#7c2d12' },
          ].map(({ level, name, color }) => (
            <div key={level} className="flex items-center gap-2">
              <div
                style={{ backgroundColor: color }}
                className="w-3 h-3 rounded"
              ></div>
              <span className="text-slate-400 text-xs">{name}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

'use client';

import { useState, useEffect } from 'react';

interface Activity {
  id: string;
  type: string;
  location: string;
  time: string;
  icon: string;
}

interface Props {
  selectedLocationId: string;
  apiUrl: string;
}

export default function RealTimeUpdates({ selectedLocationId, apiUrl }: Props) {
  const [activities, setActivities] = useState<Activity[]>([
    {
      id: '1',
      type: 'report',
      location: 'Central Mall',
      time: '2 minutes ago',
      icon: '📍',
    },
    {
      id: '2',
      type: 'prediction',
      location: 'Central Mall',
      time: '1 minute ago',
      icon: '🤖',
    },
    {
      id: '3',
      type: 'report',
      location: 'Tech Store',
      time: '5 minutes ago',
      icon: '📍',
    },
    {
      id: '4',
      type: 'learning',
      location: 'Central Mall',
      time: '10 minutes ago',
      icon: '🧠',
    },
  ]);

  const getActivityText = (type: string) => {
    switch (type) {
      case 'report':
        return 'New crowd report submitted';
      case 'prediction':
        return 'AI prediction updated';
      case 'learning':
        return 'ML model improved from new data';
      case 'alert':
        return 'Alert triggered';
      default:
        return 'Activity detected';
    }
  };

  const getActivityColor = (type: string) => {
    switch (type) {
      case 'report':
        return 'border-blue-700/50';
      case 'prediction':
        return 'border-emerald-700/50';
      case 'learning':
        return 'border-purple-700/50';
      case 'alert':
        return 'border-red-700/50';
      default:
        return 'border-slate-700';
    }
  };

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-lg overflow-hidden">
      <div className="p-4 border-b border-slate-700 bg-slate-900/50">
        <h2 className="text-white font-semibold">Live Activity Feed</h2>
        <p className="text-slate-400 text-xs mt-1">Recent events across WaitWise</p>
      </div>

      <div className="divide-y divide-slate-700 max-h-64 overflow-y-auto">
        {activities.length === 0 ? (
          <div className="p-6 text-center">
            <p className="text-slate-400 text-sm">No recent activity</p>
          </div>
        ) : (
          activities.map((activity) => (
            <div
              key={activity.id}
              className={`p-3 hover:bg-slate-700/50 transition border-l-2 ${getActivityColor(
                activity.type
              )}`}
            >
              <div className="flex items-start gap-3">
                <span className="text-xl flex-shrink-0">{activity.icon}</span>
                <div className="flex-1 min-w-0">
                  <div className="text-white text-sm font-medium">
                    {getActivityText(activity.type)}
                  </div>
                  <div className="text-slate-400 text-xs mt-1">
                    {activity.location} · {activity.time}
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Stats Footer */}
      <div className="p-4 bg-slate-900/50 border-t border-slate-700 grid grid-cols-3 gap-4 text-center text-xs">
        <div>
          <div className="text-emerald-400 font-bold">2.4k</div>
          <div className="text-slate-400">Reports</div>
        </div>
        <div>
          <div className="text-blue-400 font-bold">94%</div>
          <div className="text-slate-400">Accuracy</div>
        </div>
        <div>
          <div className="text-purple-400 font-bold">Live</div>
          <div className="text-slate-400">Learning</div>
        </div>
      </div>
    </div>
  );
}

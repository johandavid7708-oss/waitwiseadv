'use client';

import { useState } from 'react';

interface Location {
  id: string;
  name: string;
  category: string;
}

interface Props {
  selectedLocation: Location;
  onSubmitReport: (
    locationId: string,
    crowdLevel: number,
    waitTime?: number,
    comment?: string
  ) => Promise<boolean>;
  locations: Location[];
}

export default function WaitWiseDashboard({
  selectedLocation,
  onSubmitReport,
  locations,
}: Props) {
  const [crowdLevel, setCrowdLevel] = useState(3);
  const [waitTime, setWaitTime] = useState<number | ''>('');
  const [comment, setComment] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);

    try {
      const success = await onSubmitReport(
        selectedLocation.id,
        crowdLevel,
        waitTime ? parseInt(waitTime as string) : undefined,
        comment || undefined
      );

      if (success) {
        setSubmitted(true);
        setCrowdLevel(3);
        setWaitTime('');
        setComment('');

        setTimeout(() => setSubmitted(false), 3000);
      }
    } catch (err) {
      console.error('Error submitting report:', err);
    } finally {
      setSubmitting(false);
    }
  };

  const crowdText = ['Empty', 'Quiet', 'Moderate', 'Crowded', 'Packed'][
    crowdLevel - 1
  ];
  const crowdColor = [
    'text-emerald-400',
    'text-lime-400',
    'text-amber-400',
    'text-red-400',
    'text-red-600',
  ][crowdLevel - 1];

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-lg overflow-hidden">
      <div className="p-4 border-b border-slate-700 bg-slate-900/50">
        <h2 className="text-white font-semibold">Help Us Learn</h2>
        <p className="text-slate-400 text-xs mt-1">
          Report what you see at {selectedLocation.name}
        </p>
      </div>

      <form onSubmit={handleSubmit} className="p-6 space-y-6">
        {/* Crowd Level Slider */}
        <div>
          <label className="block text-white font-medium mb-3">
            How crowded is it right now?
          </label>
          <div className="space-y-3">
            <input
              type="range"
              min="1"
              max="5"
              value={crowdLevel}
              onChange={(e) => setCrowdLevel(Number(e.target.value))}
              className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-emerald-500"
            />
            <div className="flex items-center justify-between">
              <div className="text-slate-400 text-sm">Empty</div>
              <div className={`text-2xl font-bold ${crowdColor}`}>{crowdText}</div>
              <div className="text-slate-400 text-sm">Packed</div>
            </div>

            {/* Visual Indicator */}
            <div className="grid grid-cols-5 gap-2 mt-4">
              {[1, 2, 3, 4, 5].map((level) => (
                <div
                  key={level}
                  className={`p-2 rounded text-center text-xs transition ${
                    level === crowdLevel
                      ? 'bg-emerald-600/40 border border-emerald-500 text-white'
                      : 'bg-slate-700/30 border border-slate-600 text-slate-400'
                  }`}
                >
                  {['😊', '🙂', '😐', '😕', '😞'][level - 1]}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Wait Time */}
        <div>
          <label className="block text-white font-medium mb-2">
            How long is the wait? (optional)
          </label>
          <div className="relative">
            <input
              type="number"
              min="0"
              max="300"
              placeholder="e.g., 15"
              value={waitTime}
              onChange={(e) => setWaitTime(e.target.value ? parseInt(e.target.value) : '')}
              className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white placeholder-slate-500 focus:border-emerald-500 focus:outline-none transition"
            />
            <span className="absolute right-3 top-2.5 text-slate-400 text-sm">min</span>
          </div>
        </div>

        {/* Comment */}
        <div>
          <label className="block text-white font-medium mb-2">
            Any comments? (optional)
          </label>
          <textarea
            placeholder="e.g., 'Just arrived', 'Clearing up', etc."
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            rows={3}
            className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white placeholder-slate-500 focus:border-emerald-500 focus:outline-none transition resize-none"
          />
        </div>

        {/* Success Message */}
        {submitted && (
          <div className="p-3 bg-emerald-900/40 border border-emerald-600/50 rounded-lg">
            <div className="text-emerald-300 text-sm font-medium">
              ✓ Thank you! Your report helps us learn.
            </div>
          </div>
        )}

        {/* Submit Button */}
        <button
          type="submit"
          disabled={submitting}
          className="w-full px-4 py-3 bg-gradient-to-r from-emerald-600 to-emerald-500 hover:from-emerald-500 hover:to-emerald-400 text-white font-semibold rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {submitting ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-white"></div>
              Submitting...
            </>
          ) : (
            <>
              <span>📍</span>
              Submit Report
            </>
          )}
        </button>

        {/* Learning Notice */}
        <div className="p-3 bg-blue-900/20 border border-blue-700/50 rounded-lg">
          <div className="text-blue-300 text-xs leading-relaxed">
            <strong>💡 AI Learning:</strong> Every report improves our prediction accuracy.
            Frequent, accurate reporters become trusted contributors.
          </div>
        </div>
      </form>
    </div>
  );
}

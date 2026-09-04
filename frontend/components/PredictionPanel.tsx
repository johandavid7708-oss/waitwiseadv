'use client';

interface Location {
  id: string;
  name: string;
  category: string;
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
  forecast_for: string;
  generated_at: string;
}

interface Props {
  prediction: Prediction;
  location: Location;
}

export default function PredictionPanel({ prediction, location }: Props) {
  const { prediction: pred } = prediction;
  const confidentPercent = Math.round(pred.confidence_score * 100);

  const getCrowdColor = (level: number) => {
    if (level < 1.5) return 'text-emerald-400';
    if (level < 2.5) return 'text-lime-400';
    if (level < 3.5) return 'text-amber-400';
    if (level < 4.5) return 'text-red-400';
    return 'text-red-600';
  };

  const getCrowdBg = (level: number) => {
    if (level < 1.5) return 'bg-emerald-900/20 border-emerald-700/50';
    if (level < 2.5) return 'bg-lime-900/20 border-lime-700/50';
    if (level < 3.5) return 'bg-amber-900/20 border-amber-700/50';
    if (level < 4.5) return 'bg-red-900/20 border-red-700/50';
    return 'bg-red-900/40 border-red-700/70';
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence > 0.8) return 'bg-emerald-500/20 border-emerald-600';
    if (confidence > 0.6) return 'bg-amber-500/20 border-amber-600';
    return 'bg-red-500/20 border-red-600';
  };

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-lg overflow-hidden">
      <div className="p-4 border-b border-slate-700 bg-slate-900/50">
        <h2 className="text-white font-semibold">Prediction</h2>
        <p className="text-slate-400 text-xs mt-1">Next {pred.prediction_horizon_minutes} minutes</p>
      </div>

      <div className="p-6 space-y-6">
        {/* Crowd Level Prediction */}
        <div className={`rounded-lg border p-4 ${getCrowdBg(pred.predicted_crowd_level)}`}>
          <div className="text-slate-400 text-sm mb-2">Expected Crowd</div>
          <div className={`text-3xl font-bold ${getCrowdColor(pred.predicted_crowd_level)}`}>
            {pred.crowd_level_text}
          </div>
          <div className="text-slate-400 text-xs mt-2">
            Level {Math.round(pred.predicted_crowd_level * 10) / 10}/5
          </div>

          {/* Visual Indicator */}
          <div className="mt-4 flex gap-1">
            {[1, 2, 3, 4, 5].map((level) => (
              <div
                key={level}
                className={`flex-1 h-2 rounded ${
                  level <= pred.predicted_crowd_level
                    ? 'bg-gradient-to-r from-emerald-500 to-red-500'
                    : 'bg-slate-600'
                }`}
              ></div>
            ))}
          </div>
        </div>

        {/* Wait Time */}
        <div className="bg-slate-700/50 rounded-lg p-4">
          <div className="text-slate-400 text-sm mb-1">Estimated Wait</div>
          <div className="text-2xl font-bold text-white">
            {pred.predicted_wait_time}
            <span className="text-sm text-slate-400 ml-1">min</span>
          </div>
        </div>

        {/* Confidence Score */}
        <div className={`rounded-lg border p-4 ${getConfidenceColor(pred.confidence_score)}`}>
          <div className="flex items-center justify-between mb-2">
            <span className="text-slate-300 text-sm">Confidence</span>
            <span className="text-white font-bold">{confidentPercent}%</span>
          </div>
          <div className="w-full h-2 bg-slate-600 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-emerald-500 to-amber-500 transition-all"
              style={{ width: `${confidentPercent}%` }}
            ></div>
          </div>
        </div>

        {/* Reasoning */}
        <div className="bg-slate-700/30 rounded-lg p-3 border border-slate-700">
          <div className="text-slate-300 text-xs leading-relaxed">
            <div className="font-semibold text-slate-200 mb-2">Why?</div>
            {pred.reasoning}
          </div>
        </div>

        {/* AI Learning Indicator */}
        <div className="flex items-center gap-2 p-3 bg-blue-900/20 border border-blue-700/50 rounded-lg">
          <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
          <span className="text-blue-300 text-xs">ML model continuously learning</span>
        </div>
      </div>
    </div>
  );
}

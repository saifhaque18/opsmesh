"use client";

import { useState } from "react";
import {
  type RuleResult,
  type ScoreHistoryEntry,
  type ScoringExplanation,
  fetchScoreHistory,
  fetchScoringExplanation,
  overrideSeverity,
} from "@/lib/api";

interface ScoringPanelProps {
  incidentId: string;
  currentScore: number | null;
  onScoreUpdated?: () => void;
}

function getSeverityColor(label: string): string {
  switch (label) {
    case "critical":
      return "text-red-600 bg-red-100";
    case "high":
      return "text-orange-600 bg-orange-100";
    case "medium":
      return "text-yellow-600 bg-yellow-100";
    case "low":
      return "text-blue-600 bg-blue-100";
    default:
      return "text-gray-600 bg-gray-100";
  }
}

function ScoreBar({ score, label }: { score: number; label: string }) {
  const percentage = Math.round(score * 100);
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-sm">
        <span className="font-medium">Severity Score</span>
        <span className={`px-2 py-0.5 rounded text-xs ${getSeverityColor(label)}`}>
          {label.toUpperCase()}
        </span>
      </div>
      <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
        <div
          className={`h-full transition-all duration-300 ${
            score >= 0.85
              ? "bg-red-500"
              : score >= 0.65
              ? "bg-orange-500"
              : score >= 0.4
              ? "bg-yellow-500"
              : "bg-blue-500"
          }`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      <div className="text-right text-xs text-gray-500">{score.toFixed(3)}</div>
    </div>
  );
}

function RuleBreakdown({ rules }: { rules: RuleResult[] }) {
  return (
    <div className="space-y-2">
      <h4 className="text-sm font-medium text-gray-700">Rule Breakdown</h4>
      <div className="space-y-1.5">
        {rules.map((rule) => (
          <div key={rule.rule} className="text-xs">
            <div className="flex justify-between">
              <span className="font-medium text-gray-600">
                {rule.rule.replace(/_/g, " ")}
              </span>
              <span className="text-gray-500">
                {rule.score.toFixed(2)} (w={rule.weight})
              </span>
            </div>
            <div className="text-gray-400 truncate">{rule.explanation}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function HistoryEntry({ entry }: { entry: ScoreHistoryEntry }) {
  const isOverride = entry.source === "manual";
  return (
    <div className="border-l-2 border-gray-200 pl-3 py-1 text-xs">
      <div className="flex justify-between">
        <span
          className={`px-1.5 py-0.5 rounded ${
            isOverride ? "bg-purple-100 text-purple-700" : "bg-gray-100 text-gray-600"
          }`}
        >
          {entry.source}
        </span>
        <span className="text-gray-400">
          {new Date(entry.scored_at).toLocaleString()}
        </span>
      </div>
      <div className="mt-1">
        <span className="font-medium">{entry.score.toFixed(3)}</span>
        {entry.previous_score !== null && (
          <span className="text-gray-400 ml-1">
            (was {entry.previous_score.toFixed(3)})
          </span>
        )}
        <span className={`ml-2 ${getSeverityColor(entry.severity_label)}`}>
          {entry.severity_label}
        </span>
      </div>
      {entry.scored_by && (
        <div className="text-gray-400">by {entry.scored_by}</div>
      )}
      {entry.override_reason && (
        <div className="text-gray-500 italic">&ldquo;{entry.override_reason}&rdquo;</div>
      )}
    </div>
  );
}

export default function ScoringPanel({
  incidentId,
  currentScore,
  onScoreUpdated,
}: ScoringPanelProps) {
  const [expanded, setExpanded] = useState(false);
  const [explanation, setExplanation] = useState<ScoringExplanation | null>(null);
  const [history, setHistory] = useState<ScoreHistoryEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [showOverride, setShowOverride] = useState(false);
  const [overrideScore, setOverrideScore] = useState(currentScore?.toString() || "0.5");
  const [overrideReason, setOverrideReason] = useState("");
  const [overrideLoading, setOverrideLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadDetails = async () => {
    if (explanation) {
      setExpanded(!expanded);
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const [scoringData, historyData] = await Promise.all([
        fetchScoringExplanation(incidentId),
        fetchScoreHistory(incidentId),
      ]);
      setExplanation(scoringData);
      setHistory(historyData.entries);
      setExpanded(true);
    } catch (err) {
      setError("Failed to load scoring details");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleOverride = async () => {
    const score = parseFloat(overrideScore);
    if (isNaN(score) || score < 0 || score > 1) {
      setError("Score must be between 0 and 1");
      return;
    }
    if (overrideReason.length < 5) {
      setError("Please provide a reason (min 5 characters)");
      return;
    }

    setOverrideLoading(true);
    setError(null);
    try {
      await overrideSeverity(incidentId, {
        score,
        reason: overrideReason,
      });
      setShowOverride(false);
      setOverrideReason("");
      // Reload data
      const [scoringData, historyData] = await Promise.all([
        fetchScoringExplanation(incidentId),
        fetchScoreHistory(incidentId),
      ]);
      setExplanation(scoringData);
      setHistory(historyData.entries);
      onScoreUpdated?.();
    } catch (err) {
      setError("Failed to override score");
      console.error(err);
    } finally {
      setOverrideLoading(false);
    }
  };

  return (
    <div className="border rounded-lg p-3 bg-white shadow-sm">
      <div
        className="flex justify-between items-center cursor-pointer"
        onClick={loadDetails}
      >
        <h3 className="font-medium text-gray-800">Severity Scoring</h3>
        <button className="text-sm text-blue-600 hover:text-blue-800">
          {loading ? "Loading..." : expanded ? "Hide" : "Show Details"}
        </button>
      </div>

      {currentScore !== null && (
        <div className="mt-2">
          <ScoreBar
            score={currentScore}
            label={explanation?.severity_label || "medium"}
          />
        </div>
      )}

      {error && (
        <div className="mt-2 text-sm text-red-600 bg-red-50 p-2 rounded">
          {error}
        </div>
      )}

      {expanded && explanation && (
        <div className="mt-4 space-y-4">
          <RuleBreakdown rules={explanation.rules} />

          <div className="pt-2 border-t">
            <div className="flex justify-between items-center mb-2">
              <h4 className="text-sm font-medium text-gray-700">Score History</h4>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setShowOverride(!showOverride);
                }}
                className="text-xs px-2 py-1 bg-purple-100 text-purple-700 rounded hover:bg-purple-200"
              >
                Override Score
              </button>
            </div>

            {showOverride && (
              <div className="mb-3 p-2 bg-purple-50 rounded space-y-2">
                <div>
                  <label className="text-xs text-gray-600">New Score (0-1)</label>
                  <input
                    type="number"
                    min="0"
                    max="1"
                    step="0.01"
                    value={overrideScore}
                    onChange={(e) => setOverrideScore(e.target.value)}
                    className="w-full px-2 py-1 text-sm border rounded"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-600">Reason</label>
                  <textarea
                    value={overrideReason}
                    onChange={(e) => setOverrideReason(e.target.value)}
                    className="w-full px-2 py-1 text-sm border rounded"
                    rows={2}
                    placeholder="Why are you overriding this score?"
                  />
                </div>
                <button
                  onClick={handleOverride}
                  disabled={overrideLoading}
                  className="w-full py-1 text-sm bg-purple-600 text-white rounded hover:bg-purple-700 disabled:opacity-50"
                >
                  {overrideLoading ? "Saving..." : "Apply Override"}
                </button>
              </div>
            )}

            {history.length > 0 ? (
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {history.map((entry) => (
                  <HistoryEntry key={entry.id} entry={entry} />
                ))}
              </div>
            ) : (
              <div className="text-xs text-gray-400">No history available</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

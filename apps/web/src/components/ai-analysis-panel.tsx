"use client";

import { useEffect, useState } from "react";
import {
  fetchAIAnalysis,
  submitAIReview,
  type AIAnalysis,
} from "@/lib/api";

interface AIAnalysisPanelProps {
  incidentId: string;
}

const priorityColors: Record<string, string> = {
  immediate: "border-red-300 bg-red-50 dark:border-red-800 dark:bg-red-900/20",
  high: "border-orange-300 bg-orange-50 dark:border-orange-800 dark:bg-orange-900/20",
  medium: "border-yellow-300 bg-yellow-50 dark:border-yellow-800 dark:bg-yellow-900/20",
  low: "border-blue-300 bg-blue-50 dark:border-blue-800 dark:bg-blue-900/20",
};

export function AIAnalysisPanel({ incidentId }: AIAnalysisPanelProps) {
  const [data, setData] = useState<AIAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [reviewing, setReviewing] = useState(false);

  useEffect(() => {
    setLoading(true);
    fetchAIAnalysis(incidentId)
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [incidentId]);

  const handleReview = async (rating: "accepted" | "rejected") => {
    setReviewing(true);
    try {
      await submitAIReview(incidentId, {
        rating,
        reviewed_by: "analyst@opsmesh.dev",
      });
      const updated = await fetchAIAnalysis(incidentId);
      setData(updated);
    } catch (err) {
      console.error("Review failed:", err);
    } finally {
      setReviewing(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-3">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="h-24 animate-pulse rounded-xl bg-gray-100 dark:bg-gray-800" />
        ))}
      </div>
    );
  }

  if (!data || (!data.root_cause && !data.suggested_actions)) {
    return (
      <div className="rounded-xl border border-gray-200 p-6 text-center dark:border-gray-700">
        <svg className="mx-auto h-8 w-8 text-gray-300 dark:text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
        </svg>
        <p className="mt-2 text-sm text-gray-400">
          AI analysis not yet available. Processing may still be in progress.
        </p>
      </div>
    );
  }

  const rootCause = data.root_cause;
  const actions = data.suggested_actions || [];
  const trace = data.trace;

  return (
    <div className="space-y-4">
      {/* Root cause analysis */}
      {rootCause && (
        <div className="rounded-xl border border-gray-200 bg-white p-5 dark:border-gray-700 dark:bg-gray-900">
          <div className="mb-3 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <svg className="h-4 w-4 text-purple-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
              <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                Root cause analysis
              </h3>
            </div>
            <div className="flex items-center gap-2">
              {rootCause.human_edited && (
                <span className="rounded-md bg-amber-100 px-1.5 py-0.5 text-xs text-amber-700 dark:bg-amber-900/30 dark:text-amber-300">
                  Edited
                </span>
              )}
              <span className="text-xs text-gray-400">
                {Math.round(rootCause.confidence * 100)}% confidence
              </span>
            </div>
          </div>

          <p className="text-sm text-gray-700 dark:text-gray-300">
            {rootCause.summary}
          </p>

          {rootCause.contributing_factors.length > 0 && (
            <div className="mt-3">
              <p className="text-xs font-medium uppercase tracking-wider text-gray-400">
                Contributing factors
              </p>
              <ul className="mt-1 space-y-1">
                {rootCause.contributing_factors.map((factor, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-gray-600 dark:text-gray-400">
                    <span className="mt-1.5 h-1 w-1 flex-shrink-0 rounded-full bg-gray-400" />
                    {factor}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {rootCause.escalation_needed && (
            <div className="mt-3 flex items-center gap-2 rounded-lg bg-red-50 p-2 dark:bg-red-900/20">
              <svg className="h-4 w-4 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <span className="text-xs font-medium text-red-700 dark:text-red-300">
                Escalation recommended
              </span>
            </div>
          )}
        </div>
      )}

      {/* Suggested actions */}
      {actions.length > 0 && (
        <div className="rounded-xl border border-gray-200 bg-white p-5 dark:border-gray-700 dark:bg-gray-900">
          <div className="mb-3 flex items-center gap-2">
            <svg className="h-4 w-4 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
              Suggested actions
            </h3>
          </div>

          <div className="space-y-2">
            {actions.map((action, i) => (
              <div
                key={i}
                className={`rounded-lg border p-3 ${priorityColors[action.priority] || priorityColors.medium}`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-start gap-2">
                    <span className="mt-0.5 flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-gray-200 text-xs font-medium text-gray-600 dark:bg-gray-700 dark:text-gray-300">
                      {action.step}
                    </span>
                    <div>
                      <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                        {action.action}
                      </p>
                      {action.rationale && (
                        <p className="mt-0.5 text-xs text-gray-500 dark:text-gray-400">
                          {action.rationale}
                        </p>
                      )}
                    </div>
                  </div>
                  <div className="flex flex-shrink-0 items-center gap-2 text-xs text-gray-500">
                    <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    {action.estimated_time}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Review actions */}
      {!data.ai_reviewed && (
        <div className="flex items-center justify-between rounded-xl border border-gray-200 bg-gray-50 p-4 dark:border-gray-700 dark:bg-gray-800/50">
          <span className="text-sm text-gray-500 dark:text-gray-400">
            Was this analysis helpful?
          </span>
          <div className="flex gap-2">
            <button
              onClick={() => handleReview("accepted")}
              disabled={reviewing}
              className="flex items-center gap-1.5 rounded-lg bg-green-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-green-700 disabled:opacity-50"
            >
              <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5" />
              </svg>
              Accept
            </button>
            <button
              onClick={() => handleReview("rejected")}
              disabled={reviewing}
              className="flex items-center gap-1.5 rounded-lg bg-red-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-red-700 disabled:opacity-50"
            >
              <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14H5.236a2 2 0 01-1.789-2.894l3.5-7A2 2 0 018.736 3h4.018a2 2 0 01.485.06l3.76.94m-7 10v5a2 2 0 002 2h.096c.5 0 .905-.405.905-.904 0-.715.211-1.413.608-2.008L17 13V4m-7 10h2m5-10h2a2 2 0 012 2v6a2 2 0 01-2 2h-2.5" />
              </svg>
              Reject
            </button>
          </div>
        </div>
      )}

      {data.ai_reviewed && (
        <div className="flex items-center gap-2 rounded-xl border border-green-200 bg-green-50 p-3 dark:border-green-800 dark:bg-green-900/20">
          <svg className="h-4 w-4 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span className="text-xs font-medium text-green-700 dark:text-green-300">
            Reviewed{trace?.human_rating ? ` - ${trace.human_rating}` : ""}
          </span>
        </div>
      )}

      {/* Trace metadata */}
      {trace && (
        <div className="flex flex-wrap items-center gap-3 text-xs text-gray-400">
          <span className="flex items-center gap-1">
            <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
            </svg>
            {trace.model}
          </span>
          <span>{trace.latency_ms}ms</span>
          {trace.tokens_total && <span>{trace.tokens_total} tokens</span>}
        </div>
      )}
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { formatDistanceToNow, format } from "date-fns";
import {
  fetchIncident,
  fetchIncidentTimeline,
  type Incident,
  type TimelineResponse,
} from "@/lib/api";
import { SeverityBadge } from "@/components/severity-badge";
import { StatusBadge } from "@/components/status-badge";
import { ProcessingBadge } from "@/components/processing-badge";
import { AIAnalysisPanel } from "@/components/ai-analysis-panel";
import { IncidentTimeline } from "@/components/incident-timeline";
import ScoringPanel from "@/components/scoring-panel";

export default function IncidentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;
  const [incident, setIncident] = useState<Incident | null>(null);
  const [timeline, setTimeline] = useState<TimelineResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [showScoring, setShowScoring] = useState(false);

  useEffect(() => {
    Promise.all([
      fetchIncident(id),
      fetchIncidentTimeline(id).catch(() => null),
    ])
      .then(([incidentData, timelineData]) => {
        setIncident(incidentData);
        setTimeline(timelineData);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-8 dark:bg-gray-950">
        <div className="mx-auto max-w-4xl">
          <div className="h-96 animate-pulse rounded-xl bg-gray-100 dark:bg-gray-800" />
        </div>
      </div>
    );
  }

  if (!incident) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50 dark:bg-gray-950">
        <p className="text-gray-400">Incident not found</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      {/* Header */}
      <header className="border-b border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900">
        <div className="mx-auto flex max-w-4xl items-center gap-4 px-6 py-4">
          <button
            onClick={() => router.push("/")}
            className="rounded-lg p-1.5 text-gray-400 hover:bg-gray-100 hover:text-gray-600 dark:hover:bg-gray-800"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
          </button>
          <div className="flex-1">
            <h1 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              {incident.title}
            </h1>
            <div className="mt-1 flex items-center gap-2">
              <SeverityBadge severity={incident.severity} />
              <StatusBadge status={incident.status} />
              <ProcessingBadge status={incident.processing_status} score={incident.severity_score} />
            </div>
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="mx-auto max-w-4xl px-6 py-8">
        <div className="grid gap-6 lg:grid-cols-5">
          {/* Left column: details */}
          <div className="lg:col-span-2 space-y-4">
            <div className="rounded-xl border border-gray-200 bg-white p-5 dark:border-gray-700 dark:bg-gray-900">
              <h3 className="mb-3 text-xs font-medium uppercase tracking-wider text-gray-400">
                Details
              </h3>
              <dl className="space-y-3 text-sm">
                {incident.description && (
                  <div>
                    <dt className="text-gray-400">Description</dt>
                    <dd className="mt-0.5 text-gray-700 dark:text-gray-300">{incident.description}</dd>
                  </div>
                )}
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <dt className="text-gray-400">Source</dt>
                    <dd className="text-gray-700 dark:text-gray-300">{incident.source}</dd>
                  </div>
                  <div>
                    <dt className="text-gray-400">Service</dt>
                    <dd className="text-gray-700 dark:text-gray-300">{incident.service || "—"}</dd>
                  </div>
                  <div>
                    <dt className="text-gray-400">Environment</dt>
                    <dd className="text-gray-700 dark:text-gray-300">{incident.environment || "—"}</dd>
                  </div>
                  <div>
                    <dt className="text-gray-400">Region</dt>
                    <dd className="text-gray-700 dark:text-gray-300">{incident.region || "—"}</dd>
                  </div>
                </div>
                {incident.assigned_to && (
                  <div>
                    <dt className="text-gray-400">Assigned to</dt>
                    <dd className="text-gray-700 dark:text-gray-300">{incident.assigned_to}</dd>
                  </div>
                )}
                {incident.detected_at && (
                  <div>
                    <dt className="text-gray-400">Detected</dt>
                    <dd className="text-gray-700 dark:text-gray-300">
                      {format(new Date(incident.detected_at), "PPp")}
                      <span className="ml-1 text-gray-400">
                        ({formatDistanceToNow(new Date(incident.detected_at), { addSuffix: true })})
                      </span>
                    </dd>
                  </div>
                )}
                {incident.fingerprint && (
                  <div>
                    <dt className="text-gray-400">Fingerprint</dt>
                    <dd className="font-mono text-xs text-gray-500">{incident.fingerprint}</dd>
                  </div>
                )}
              </dl>
            </div>

            {/* Scoring toggle */}
            <button
              onClick={() => setShowScoring(!showScoring)}
              className="w-full rounded-xl border border-gray-200 bg-white p-4 text-left text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-300 dark:hover:bg-gray-800"
            >
              {showScoring ? "Hide" : "View"} severity scoring breakdown
            </button>
            {showScoring && (
              <ScoringPanel
                incidentId={incident.id}
                currentScore={incident.severity_score}
              />
            )}
          </div>

          {/* Right column: AI analysis */}
          <div className="lg:col-span-3 space-y-6">
            <div>
              <h2 className="mb-4 text-sm font-semibold text-gray-900 dark:text-gray-100">
                AI analysis
              </h2>
              <AIAnalysisPanel incidentId={incident.id} />
            </div>
          </div>
        </div>

        {/* Timeline - full width */}
        <div className="mt-8">
          <IncidentTimeline incidentId={incident.id} initialTimeline={timeline} />
        </div>
      </main>
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";
import { formatDistanceToNow } from "date-fns";
import { Layers, ChevronRight } from "lucide-react";
import { fetchClusters, type Cluster } from "@/lib/api";

interface ClusterListProps {
  onSelectCluster?: (clusterId: string) => void;
}

function getSeverityFromScore(score: number | null): string {
  if (score === null) return "low";
  if (score >= 0.8) return "critical";
  if (score >= 0.6) return "high";
  if (score >= 0.4) return "medium";
  return "low";
}

const severityColors: Record<string, { bg: string; text: string }> = {
  critical: { bg: "bg-red-100 dark:bg-red-900/30", text: "text-red-700 dark:text-red-300" },
  high: { bg: "bg-orange-100 dark:bg-orange-900/30", text: "text-orange-700 dark:text-orange-300" },
  medium: { bg: "bg-yellow-100 dark:bg-yellow-900/30", text: "text-yellow-700 dark:text-yellow-300" },
  low: { bg: "bg-blue-100 dark:bg-blue-900/30", text: "text-blue-700 dark:text-blue-300" },
};

export function ClusterList({ onSelectCluster }: ClusterListProps) {
  const [clusters, setClusters] = useState<Cluster[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchClusters({ page_size: 20, status: "active" })
      .then((data) => setClusters(data.clusters))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="space-y-3">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-20 animate-pulse rounded-xl bg-gray-100 dark:bg-gray-800" />
        ))}
      </div>
    );
  }

  if (clusters.length === 0) {
    return (
      <div className="rounded-xl border border-gray-200 p-8 text-center dark:border-gray-700">
        <Layers className="mx-auto h-8 w-8 text-gray-300 dark:text-gray-600" />
        <p className="mt-2 text-sm text-gray-400">
          No clusters yet. Clusters form as similar incidents arrive.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {clusters.map((cluster) => {
        const severity = getSeverityFromScore(cluster.max_severity_score);
        const colors = severityColors[severity];

        return (
          <button
            key={cluster.id}
            onClick={() => onSelectCluster?.(cluster.id)}
            className="w-full rounded-xl border border-gray-200 p-4 text-left transition-all hover:border-blue-300 hover:shadow-sm dark:border-gray-700 dark:hover:border-blue-700"
          >
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <Layers className="h-4 w-4 flex-shrink-0 text-blue-500" />
                  <p className="truncate font-medium text-gray-900 dark:text-gray-100">
                    {cluster.title}
                  </p>
                </div>
                <div className="mt-1.5 flex flex-wrap items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
                  <span className="inline-flex items-center gap-1 rounded-md bg-blue-50 px-1.5 py-0.5 font-medium text-blue-700 dark:bg-blue-900/30 dark:text-blue-300">
                    {cluster.incident_count} incident{cluster.incident_count !== 1 ? "s" : ""}
                  </span>
                  {cluster.primary_service && <span>{cluster.primary_service}</span>}
                  {cluster.primary_source && <span>{cluster.primary_source}</span>}
                  {cluster.last_seen && (
                    <span>
                      Last seen {formatDistanceToNow(new Date(cluster.last_seen), { addSuffix: true })}
                    </span>
                  )}
                </div>
              </div>
              <div className="flex flex-shrink-0 items-center gap-2">
                {cluster.max_severity_score != null && (
                  <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${colors.bg} ${colors.text}`}>
                    {severity}
                  </span>
                )}
                <span className="text-xs text-gray-400">
                  {Math.round(cluster.confidence * 100)}% conf
                </span>
                <ChevronRight className="h-4 w-4 text-gray-300" />
              </div>
            </div>
          </button>
        );
      })}
    </div>
  );
}

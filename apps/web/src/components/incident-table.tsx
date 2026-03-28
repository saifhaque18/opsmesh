"use client";

import { useEffect, useState, useCallback } from "react";
import { formatDistanceToNow } from "date-fns";
import { Search, ChevronLeft, ChevronRight } from "lucide-react";
import { fetchIncidents, type Incident, type IncidentFilters } from "@/lib/api";
import { SeverityBadge } from "./severity-badge";
import { StatusBadge } from "./status-badge";
import { ProcessingBadge } from "./processing-badge";

export function IncidentTable() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState<IncidentFilters>({
    page: 1,
    page_size: 15,
  });

  const loadIncidents = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchIncidents(filters);
      setIncidents(data.incidents);
      setTotal(data.total);
      setTotalPages(data.total_pages);
    } catch (err) {
      console.error("Failed to fetch incidents:", err);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    loadIncidents();
  }, [loadIncidents]);

  const updateFilter = (key: string, value: string) => {
    setFilters((prev) => ({
      ...prev,
      [key]: value || undefined,
      page: 1, // reset to page 1 on filter change
    }));
  };

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            placeholder="Search incidents..."
            className="w-full rounded-lg border border-gray-200 bg-white py-2 pl-10 pr-4 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100"
            onChange={(e) => updateFilter("search", e.target.value)}
          />
        </div>
        <select
          className="rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100"
          onChange={(e) => updateFilter("severity", e.target.value)}
          defaultValue=""
        >
          <option value="">All severities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
        <select
          className="rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100"
          onChange={(e) => updateFilter("status", e.target.value)}
          defaultValue=""
        >
          <option value="">All statuses</option>
          <option value="open">Open</option>
          <option value="acknowledged">Acknowledged</option>
          <option value="investigating">Investigating</option>
          <option value="resolved">Resolved</option>
          <option value="closed">Closed</option>
        </select>
        <select
          className="rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100"
          onChange={(e) => updateFilter("environment", e.target.value)}
          defaultValue=""
        >
          <option value="">All environments</option>
          <option value="prod">Production</option>
          <option value="staging">Staging</option>
          <option value="dev">Development</option>
        </select>
      </div>

      {/* Table */}
      <div className="overflow-x-auto rounded-xl border border-gray-200 dark:border-gray-700">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-800/50">
              <th className="px-4 py-3 text-left font-medium text-gray-500 dark:text-gray-400">Incident</th>
              <th className="px-4 py-3 text-left font-medium text-gray-500 dark:text-gray-400">Severity</th>
              <th className="px-4 py-3 text-left font-medium text-gray-500 dark:text-gray-400">Status</th>
              <th className="px-4 py-3 text-left font-medium text-gray-500 dark:text-gray-400">Pipeline</th>
              <th className="px-4 py-3 text-left font-medium text-gray-500 dark:text-gray-400">Source</th>
              <th className="px-4 py-3 text-left font-medium text-gray-500 dark:text-gray-400">Service</th>
              <th className="px-4 py-3 text-left font-medium text-gray-500 dark:text-gray-400">Env</th>
              <th className="px-4 py-3 text-left font-medium text-gray-500 dark:text-gray-400">Detected</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
            {loading ? (
              [...Array(5)].map((_, i) => (
                <tr key={i}>
                  <td colSpan={8} className="px-4 py-4">
                    <div className="h-4 w-full animate-pulse rounded bg-gray-100 dark:bg-gray-800" />
                  </td>
                </tr>
              ))
            ) : incidents.length === 0 ? (
              <tr>
                <td colSpan={8} className="px-4 py-12 text-center text-gray-400">
                  No incidents found
                </td>
              </tr>
            ) : (
              incidents.map((incident) => (
                <tr
                  key={incident.id}
                  className="cursor-pointer transition-colors hover:bg-gray-50 dark:hover:bg-gray-800/50"
                >
                  <td className="max-w-xs px-4 py-3">
                    <p className="truncate font-medium text-gray-900 dark:text-gray-100">
                      {incident.title}
                    </p>
                    {incident.assigned_to && (
                      <p className="mt-0.5 truncate text-xs text-gray-400">
                        {incident.assigned_to}
                      </p>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <SeverityBadge severity={incident.severity} />
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge status={incident.status} />
                  </td>
                  <td className="px-4 py-3">
                    <ProcessingBadge
                      status={incident.processing_status}
                      score={incident.severity_score}
                    />
                  </td>
                  <td className="px-4 py-3 text-gray-500 dark:text-gray-400">
                    {incident.source}
                  </td>
                  <td className="px-4 py-3 text-gray-500 dark:text-gray-400">
                    {incident.service || "—"}
                  </td>
                  <td className="px-4 py-3 text-gray-500 dark:text-gray-400">
                    {incident.environment || "—"}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-gray-500 dark:text-gray-400">
                    {incident.detected_at
                      ? formatDistanceToNow(new Date(incident.detected_at), { addSuffix: true })
                      : "—"}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between text-sm text-gray-500 dark:text-gray-400">
        <span>
          {total} incident{total !== 1 ? "s" : ""} total
        </span>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setFilters((p) => ({ ...p, page: Math.max(1, (p.page || 1) - 1) }))}
            disabled={filters.page === 1}
            className="rounded-lg border border-gray-200 p-1.5 transition-colors hover:bg-gray-100 disabled:opacity-40 dark:border-gray-700 dark:hover:bg-gray-800"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
          <span>
            Page {filters.page} of {totalPages}
          </span>
          <button
            onClick={() =>
              setFilters((p) => ({
                ...p,
                page: Math.min(totalPages, (p.page || 1) + 1),
              }))
            }
            disabled={filters.page === totalPages}
            className="rounded-lg border border-gray-200 p-1.5 transition-colors hover:bg-gray-100 disabled:opacity-40 dark:border-gray-700 dark:hover:bg-gray-800"
          >
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}

"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { StatsCards } from "@/components/stats-cards";
import { IncidentTable } from "@/components/incident-table";
import { ClusterList } from "@/components/cluster-list";
import { useAuth } from "@/lib/auth-context";

const roleColors: Record<string, string> = {
  admin: "bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400",
  analyst: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400",
  viewer: "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400",
};

export default function Dashboard() {
  const router = useRouter();
  const { user, logout, isAuthenticated } = useAuth();
  const [activeTab, setActiveTab] = useState<"incidents" | "clusters">("incidents");

  useEffect(() => {
    if (!isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, router]);

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      {/* Header */}
      <header className="border-b border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600">
              <span className="text-sm font-bold text-white">O</span>
            </div>
            <h1 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              OpsMesh
            </h1>
          </div>
          <div className="flex items-center gap-4">
            <span className="inline-flex items-center gap-1.5 rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-700 dark:bg-green-900/30 dark:text-green-400">
              <span className="h-1.5 w-1.5 rounded-full bg-green-500" />
              System healthy
            </span>
            {/* User menu */}
            <div className="flex items-center gap-3">
              <div className="text-right">
                <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  {user?.name}
                </p>
                <span
                  className={`inline-block rounded px-1.5 py-0.5 text-xs font-medium ${roleColors[user?.role || "viewer"]}`}
                >
                  {user?.role}
                </span>
              </div>
              <button
                onClick={logout}
                className="rounded-md border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-800"
              >
                Sign out
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="mx-auto max-w-7xl px-6 py-8">
        <div className="mb-8">
          <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
            Incident dashboard
          </h2>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Monitor, triage, and resolve incidents across your infrastructure.
          </p>
        </div>

        {/* Stats */}
        <div className="mb-8">
          <StatsCards />
        </div>

        {/* Tab navigation */}
        <div className="mb-6 flex gap-1 rounded-lg border border-gray-200 bg-gray-100 p-1 dark:border-gray-700 dark:bg-gray-800">
          <button
            onClick={() => setActiveTab("incidents")}
            className={`rounded-md px-4 py-2 text-sm font-medium transition-colors ${
              activeTab === "incidents"
                ? "bg-white text-gray-900 shadow-sm dark:bg-gray-700 dark:text-gray-100"
                : "text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
            }`}
          >
            All incidents
          </button>
          <button
            onClick={() => setActiveTab("clusters")}
            className={`rounded-md px-4 py-2 text-sm font-medium transition-colors ${
              activeTab === "clusters"
                ? "bg-white text-gray-900 shadow-sm dark:bg-gray-700 dark:text-gray-100"
                : "text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
            }`}
          >
            Clusters
          </button>
        </div>

        {/* Tab content */}
        {activeTab === "incidents" ? <IncidentTable /> : <ClusterList />}
      </main>
    </div>
  );
}

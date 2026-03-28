import { Loader2, CheckCircle2, XCircle, Clock } from "lucide-react";

const statusConfig = {
  pending: {
    bg: "bg-gray-100 dark:bg-gray-800",
    text: "text-gray-600 dark:text-gray-400",
    icon: Clock,
    label: "Pending",
    animate: false,
  },
  processing: {
    bg: "bg-blue-100 dark:bg-blue-900/30",
    text: "text-blue-700 dark:text-blue-300",
    icon: Loader2,
    label: "Processing",
    animate: true,
  },
  completed: {
    bg: "bg-green-100 dark:bg-green-900/30",
    text: "text-green-700 dark:text-green-300",
    icon: CheckCircle2,
    label: "Completed",
    animate: false,
  },
  failed: {
    bg: "bg-red-100 dark:bg-red-900/30",
    text: "text-red-700 dark:text-red-300",
    icon: XCircle,
    label: "Failed",
    animate: false,
  },
};

export function ProcessingBadge({
  status,
  score,
}: {
  status: string | null;
  score?: number | null;
}) {
  const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.pending;
  const Icon = config.icon;

  return (
    <div className="flex flex-col gap-0.5">
      <span
        className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${config.bg} ${config.text}`}
      >
        <Icon className={`h-3 w-3 ${config.animate ? "animate-spin" : ""}`} />
        {config.label}
      </span>
      {score !== null && score !== undefined && (
        <span className="text-xs text-gray-500 dark:text-gray-400">
          Score: {(score * 100).toFixed(0)}%
        </span>
      )}
    </div>
  );
}

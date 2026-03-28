const statusConfig = {
  open: { bg: "bg-red-50 dark:bg-red-900/20", text: "text-red-700 dark:text-red-300", ring: "ring-red-200 dark:ring-red-800" },
  acknowledged: { bg: "bg-amber-50 dark:bg-amber-900/20", text: "text-amber-700 dark:text-amber-300", ring: "ring-amber-200 dark:ring-amber-800" },
  investigating: { bg: "bg-blue-50 dark:bg-blue-900/20", text: "text-blue-700 dark:text-blue-300", ring: "ring-blue-200 dark:ring-blue-800" },
  resolved: { bg: "bg-green-50 dark:bg-green-900/20", text: "text-green-700 dark:text-green-300", ring: "ring-green-200 dark:ring-green-800" },
  closed: { bg: "bg-gray-50 dark:bg-gray-800", text: "text-gray-600 dark:text-gray-400", ring: "ring-gray-200 dark:ring-gray-700" },
};

export function StatusBadge({ status }: { status: string }) {
  const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.open;
  return (
    <span className={`inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${config.bg} ${config.text} ${config.ring}`}>
      {status}
    </span>
  );
}

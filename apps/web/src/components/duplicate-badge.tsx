import { Copy } from "lucide-react";

interface DuplicateBadgeProps {
  isDuplicate: boolean;
  similarityScore?: number | null;
}

export function DuplicateBadge({ isDuplicate, similarityScore }: DuplicateBadgeProps) {
  if (!isDuplicate) return null;

  return (
    <span className="inline-flex items-center gap-1 rounded-md bg-purple-50 px-1.5 py-0.5 text-xs font-medium text-purple-700 ring-1 ring-inset ring-purple-200 dark:bg-purple-900/20 dark:text-purple-300 dark:ring-purple-800">
      <Copy className="h-3 w-3" />
      Dup{similarityScore != null && ` ${Math.round(similarityScore * 100)}%`}
    </span>
  );
}

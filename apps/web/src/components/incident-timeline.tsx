"use client";

import { useState } from "react";
import { formatDistanceToNow, format } from "date-fns";
import {
  TimelineEvent,
  TimelineResponse,
  fetchIncidentTimeline,
  addIncidentNote,
  NoteCreateRequest,
} from "@/lib/api";

interface IncidentTimelineProps {
  incidentId: string;
  initialTimeline: TimelineResponse | null;
}

const EVENT_ICONS: Record<string, string> = {
  created: "plus-circle",
  status_changed: "refresh-cw",
  severity_changed: "alert-triangle",
  assigned: "user-plus",
  unassigned: "user-minus",
  processing_started: "play",
  processing_completed: "check-circle",
  processing_failed: "x-circle",
  duplicate_detected: "copy",
  cluster_joined: "layers",
  cluster_created: "folder-plus",
  ai_analysis_completed: "cpu",
  ai_review_submitted: "user-check",
  severity_scored: "bar-chart",
  severity_overridden: "edit-3",
  note_added: "message-square",
  escalated: "arrow-up-circle",
  acknowledged: "eye",
  resolved: "check-square",
  reopened: "rotate-ccw",
};

const EVENT_COLORS: Record<string, string> = {
  created: "bg-blue-500",
  status_changed: "bg-purple-500",
  severity_changed: "bg-orange-500",
  assigned: "bg-green-500",
  unassigned: "bg-gray-500",
  processing_started: "bg-blue-400",
  processing_completed: "bg-green-500",
  processing_failed: "bg-red-500",
  duplicate_detected: "bg-yellow-500",
  cluster_joined: "bg-indigo-500",
  cluster_created: "bg-indigo-600",
  ai_analysis_completed: "bg-purple-600",
  ai_review_submitted: "bg-purple-400",
  severity_scored: "bg-blue-500",
  severity_overridden: "bg-orange-600",
  note_added: "bg-gray-600",
  escalated: "bg-red-600",
  acknowledged: "bg-blue-600",
  resolved: "bg-green-600",
  reopened: "bg-yellow-600",
};

function formatEventType(eventType: string): string {
  return eventType
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

export function IncidentTimeline({
  incidentId,
  initialTimeline,
}: IncidentTimelineProps) {
  const [timeline, setTimeline] = useState<TimelineResponse | null>(
    initialTimeline
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [noteContent, setNoteContent] = useState("");
  const [addingNote, setAddingNote] = useState(false);
  const [showNoteForm, setShowNoteForm] = useState(false);

  const refreshTimeline = async () => {
    setLoading(true);
    try {
      const data = await fetchIncidentTimeline(incidentId);
      setTimeline(data);
      setError(null);
    } catch (err) {
      setError("Failed to load timeline");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleAddNote = async () => {
    if (!noteContent.trim()) return;

    setAddingNote(true);
    try {
      const note: NoteCreateRequest = {
        content: noteContent.trim(),
        author: "analyst@example.com", // TODO: Get from auth
      };
      await addIncidentNote(incidentId, note);
      setNoteContent("");
      setShowNoteForm(false);
      await refreshTimeline();
    } catch (err) {
      console.error("Failed to add note:", err);
    } finally {
      setAddingNote(false);
    }
  };

  if (!timeline) {
    return (
      <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-zinc-100">Timeline</h3>
          <button
            onClick={refreshTimeline}
            disabled={loading}
            className="text-sm text-blue-400 hover:text-blue-300"
          >
            {loading ? "Loading..." : "Load Timeline"}
          </button>
        </div>
        {error && <p className="text-red-400 text-sm">{error}</p>}
      </div>
    );
  }

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-zinc-100">
          Timeline ({timeline.total} events)
        </h3>
        <div className="flex gap-2">
          <button
            onClick={() => setShowNoteForm(!showNoteForm)}
            className="text-sm px-3 py-1 bg-zinc-800 text-zinc-300 rounded \
hover:bg-zinc-700"
          >
            Add Note
          </button>
          <button
            onClick={refreshTimeline}
            disabled={loading}
            className="text-sm text-blue-400 hover:text-blue-300"
          >
            {loading ? "..." : "Refresh"}
          </button>
        </div>
      </div>

      {showNoteForm && (
        <div className="mb-4 p-4 bg-zinc-800 rounded-lg">
          <textarea
            value={noteContent}
            onChange={(e) => setNoteContent(e.target.value)}
            placeholder="Add a note..."
            className="w-full p-2 bg-zinc-900 border border-zinc-700 rounded \
text-zinc-100 placeholder-zinc-500 resize-none"
            rows={3}
          />
          <div className="flex justify-end gap-2 mt-2">
            <button
              onClick={() => setShowNoteForm(false)}
              className="px-3 py-1 text-sm text-zinc-400 hover:text-zinc-300"
            >
              Cancel
            </button>
            <button
              onClick={handleAddNote}
              disabled={addingNote || !noteContent.trim()}
              className="px-3 py-1 text-sm bg-blue-600 text-white rounded \
hover:bg-blue-500 disabled:opacity-50"
            >
              {addingNote ? "Adding..." : "Add Note"}
            </button>
          </div>
        </div>
      )}

      <div className="relative">
        {/* Timeline line */}
        <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-zinc-700" />

        {/* Events */}
        <div className="space-y-4">
          {timeline.events.map((event) => (
            <TimelineEventItem key={event.id} event={event} />
          ))}
        </div>

        {timeline.events.length === 0 && (
          <p className="text-zinc-500 text-sm ml-10">No events recorded yet.</p>
        )}
      </div>
    </div>
  );
}

function TimelineEventItem({ event }: { event: TimelineEvent }) {
  const [expanded, setExpanded] = useState(false);
  const colorClass = EVENT_COLORS[event.event_type] || "bg-zinc-500";

  return (
    <div className="relative flex items-start gap-4">
      {/* Icon dot */}
      <div
        className={`relative z-10 w-8 h-8 rounded-full ${colorClass} \
flex items-center justify-center flex-shrink-0`}
      >
        <span className="text-white text-xs font-bold">
          {event.event_type.charAt(0).toUpperCase()}
        </span>
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0 pb-2">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-zinc-100">
              {event.summary}
            </p>
            <div className="flex items-center gap-2 mt-0.5">
              <span className="text-xs text-zinc-500">
                {formatEventType(event.event_type)}
              </span>
              {event.actor && event.actor !== "system" && (
                <>
                  <span className="text-zinc-600">by</span>
                  <span className="text-xs text-zinc-400">{event.actor}</span>
                </>
              )}
            </div>
          </div>
          <span
            className="text-xs text-zinc-500 flex-shrink-0"
            title={format(new Date(event.occurred_at), "PPpp")}
          >
            {formatDistanceToNow(new Date(event.occurred_at), {
              addSuffix: true,
            })}
          </span>
        </div>

        {/* Detail or metadata */}
        {(event.detail || event.event_metadata) && (
          <button
            onClick={() => setExpanded(!expanded)}
            className="mt-1 text-xs text-zinc-500 hover:text-zinc-400"
          >
            {expanded ? "Hide details" : "Show details"}
          </button>
        )}

        {expanded && (
          <div className="mt-2 p-2 bg-zinc-800 rounded text-xs">
            {event.detail && (
              <p className="text-zinc-300 whitespace-pre-wrap mb-2">
                {event.detail}
              </p>
            )}
            {event.event_metadata && (
              <pre className="text-zinc-400 overflow-x-auto">
                {JSON.stringify(event.event_metadata, null, 2)}
              </pre>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default IncidentTimeline;

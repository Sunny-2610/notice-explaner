import { useEffect, useState } from 'react';
import { fetchResult, type DocumentResult } from '../lib/api';

const API_BASE = import.meta.env.VITE_API_BASE ?? '';
// Provisional-first: completed/failed are final. awaiting_review WITH an
// explanation (E-401 provisional) keeps polling/streaming for the later
// verified resolve. awaiting_review WITHOUT explanation (E-150/E-201) stops.
const FINAL = new Set(['completed', 'failed']);
// Poll fallback mirrors useJobPoll: 60 attempts at 1.5s ≈ 90s.
const MAX_ATTEMPTS = 60;
const INTERVAL_MS = 1500;

/** SSE job progress with transparent polling fallback.
 *
 * Same return shape as useJobPoll so callers change one line. Streams
 * stage updates only (never explanation tokens); on EventSource error or
 * unsupported browsers it falls back to polling, keeping the
 * timedOut/"taking longer" state.
 *
 * Provisional-first note: a `result` frame with provisional=true (escalated
 * job) does NOT close the stream — the reviewer resolve later emits a
 * second, verified frame for the same jobId. Only final frames
 * (completed/failed, or awaiting_review WITHOUT an explanation) close it.
 * The polling fallback mirrors this: it keeps polling on provisional jobs
 * so the verified upgrade arrives even where SSE is unavailable.
 */
export function useJobStream(jobId: string | null) {
  const [result, setResult] = useState<DocumentResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [timedOut, setTimedOut] = useState(false);

  useEffect(() => {
    if (!jobId) return;
    let stop = false;
    let es: EventSource | null = null;
    let pollTimer: ReturnType<typeof setTimeout> | null = null;

    const pollFallback = (attempts = 0) => {
      if (stop) return;
      fetchResult(jobId)
        .then((r) => {
          if (stop) return;
          setResult(r);
          if (FINAL.has(r.status)) return;
          // Blocked review with nothing to show yet — stop polling.
          if (r.status === 'awaiting_review' && !r.explanation) return;
          if (attempts + 1 >= MAX_ATTEMPTS) {
            setTimedOut(true);
            return;
          }
          pollTimer = setTimeout(() => pollFallback(attempts + 1), INTERVAL_MS);
        })
        .catch((e) => {
          if (!stop) setError((e as Error).message);
        });
    };

    if (typeof EventSource === 'undefined') {
      pollFallback();
      return () => {
        stop = true;
        if (pollTimer) clearTimeout(pollTimer);
      };
    }

    es = new EventSource(`${API_BASE}/api/v1/documents/${jobId}/events`);
    es.addEventListener('status', () => {
      // Refresh the full payload on each stage change.
      fetchResult(jobId)
        .then((r) => {
          if (!stop) setResult(r);
        })
        .catch(() => {});
    });
    es.addEventListener('result', (e) => {
      try {
        const payload = JSON.parse((e as MessageEvent).data) as DocumentResult;
        if (!stop) setResult(payload);
        // Provisional result (awaiting_review + explanation): keep the
        // stream open for the verified resolve. Final results close it.
        const isProvisional = Boolean(
          (payload as DocumentResult).provisional ||
          (payload.status === 'awaiting_review' && payload.explanation),
        );
        if (!isProvisional) es?.close();
      } catch {
        /* malformed frame — polling fallback below covers it */
      }
    });
    es.addEventListener('timeout', () => {
      if (!stop) setTimedOut(true);
      es?.close();
    });
    es.onerror = () => {
      es?.close();
      es = null;
      if (!stop) pollFallback();
    };

    return () => {
      stop = true;
      es?.close();
      if (pollTimer) clearTimeout(pollTimer);
    };
  }, [jobId]);

  return { result, error, timedOut };
}

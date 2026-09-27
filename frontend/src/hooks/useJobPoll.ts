import { useCallback, useEffect, useState } from 'react';
import { fetchResult, type DocumentResult } from '../lib/api';

const TERMINAL = new Set(['completed', 'awaiting_review', 'failed']);
// Cap polling so a stuck job surfaces a "taking longer" state instead of
// spinning forever: 60 attempts at 1.5s intervals ≈ 90s.
const MAX_ATTEMPTS = 60;
const INTERVAL_MS = 1500;

export function useJobPoll(jobId: string | null) {
  const [result, setResult] = useState<DocumentResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [timedOut, setTimedOut] = useState(false);
  const [round, setRound] = useState(0);

  const retry = useCallback(() => {
    setError(null);
    setTimedOut(false);
    setRound((r) => r + 1);
  }, []);

  useEffect(() => {
    if (!jobId) return;
    let stop = false;
    let attempts = 0;
    const tick = async () => {
      try {
        const r = await fetchResult(jobId);
        if (stop) return;
        setResult(r);
        if (TERMINAL.has(r.status)) return;
        attempts += 1;
        if (attempts >= MAX_ATTEMPTS) {
          setTimedOut(true);
          return;
        }
        setTimeout(tick, INTERVAL_MS);
      } catch (e) {
        if (!stop) setError((e as Error).message);
      }
    };
    tick();
    return () => {
      stop = true;
    };
  }, [jobId, round]);

  return { result, error, timedOut, retry };
}

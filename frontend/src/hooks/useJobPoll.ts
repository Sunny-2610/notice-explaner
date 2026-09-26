import { useEffect, useState } from 'react';
import { fetchResult, type DocumentResult } from '../lib/api';

const TERMINAL = new Set(['completed', 'awaiting_review', 'failed']);

export function useJobPoll(jobId: string | null) {
  const [result, setResult] = useState<DocumentResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!jobId) return;
    let stop = false;
    const tick = async () => {
      try {
        const r = await fetchResult(jobId);
        if (stop) return;
        setResult(r);
        if (!TERMINAL.has(r.status)) setTimeout(tick, 1500);
      } catch (e) {
        if (!stop) setError((e as Error).message);
      }
    };
    tick();
    return () => {
      stop = true;
    };
  }, [jobId]);

  return { result, error };
}

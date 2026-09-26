import { useState } from 'react';
import { fetchSpeech } from '../lib/voice';

export default function VoicePlayer({ jobId, lang }: { jobId: string; lang: string }) {
  const [url, setUrl] = useState<string | null>(null);
  const [state, setState] = useState<'idle' | 'loading' | 'unavailable'>('idle');

  const load = async () => {
    setState('loading');
    const objectUrl = await fetchSpeech(jobId, lang);
    if (!objectUrl) {
      setState('unavailable'); // E-302: continue text-only
      return;
    }
    setUrl(objectUrl);
    setState('idle');
  };

  if (state === 'unavailable') return null;

  return (
    <div>
      {!url ? (
        <button
          onClick={load}
          disabled={state === 'loading'}
          className="min-h-[52px] px-6 rounded-xl bg-green-700 text-white text-lg disabled:opacity-50"
        >
          {state === 'loading' ? '…' : '🔊 सुनें / ऐका'}
        </button>
      ) : (
        <audio controls src={url} className="w-full" />
      )}
    </div>
  );
}

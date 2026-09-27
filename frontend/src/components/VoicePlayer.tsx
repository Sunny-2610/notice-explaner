import { useState } from 'react';
import { Volume2 } from 'lucide-react';
import { STRINGS, type Lang } from '../i18n/strings';
import { fetchSpeech } from '../lib/voice';

export default function VoicePlayer({ jobId, lang }: { jobId: string; lang: Lang }) {
  const t = STRINGS[lang];
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
    <div className="card">
      {!url ? (
        <button
          onClick={load}
          disabled={state === 'loading'}
          className="btn-secondary inline-flex items-center gap-2 disabled:opacity-50"
        >
          <Volume2 size={20} strokeWidth={1.75} aria-hidden />
          {state === 'loading' ? '…' : t.listen}
        </button>
      ) : (
        <audio controls src={url} className="w-full" />
      )}
    </div>
  );
}

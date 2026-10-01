import { useEffect, useRef, useState } from 'react';
import { MessageSquare, Mic, Send } from 'lucide-react';
import { STRINGS, type Lang } from '../i18n/strings';
import { askQuestion } from '../lib/api';
import { useVoiceAsk } from '../hooks/useVoiceAsk';

// Follow-up Q&A card. Talks to POST /{jobId}/ask (max 10/job enforced
// server-side from the audit trail; the counter here is display-only).
// initialQuestion carries a home-screen voice transcript that auto-submits
// once, so the mic before upload never leads nowhere.
const MAX_Q = 10;

export default function FollowUpQA({
  jobId,
  lang,
  initialQuestion,
  onInitialConsumed,
}: {
  jobId: string;
  lang: Lang;
  initialQuestion?: string | null;
  onInitialConsumed?: () => void;
}) {
  const t = STRINGS[lang];
  const [input, setInput] = useState('');
  const [items, setItems] = useState<{ q: string; a: string }[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const consumedRef = useRef(false);
  const voice = useVoiceAsk(jobId, lang);

  const ask = async (raw: string) => {
    const q = raw.trim();
    if (!q || busy || items.length >= MAX_Q) return;
    setBusy(true);
    setError(null);
    try {
      const r = await askQuestion(jobId, q);
      setItems((prev) => [...prev, { q, a: r.answer }]);
      setInput('');
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  // Home-screen voice transcript: auto-submit once the job is ready.
  useEffect(() => {
    if (initialQuestion && !consumedRef.current) {
      consumedRef.current = true;
      void ask(initialQuestion);
      onInitialConsumed?.();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialQuestion]);

  const onMic = async () => {
    if (voice.busy || busy || items.length >= MAX_Q) return;
    if (voice.mode === 'server') {
      // Server mode needs raw audio via VoiceRecorder; handled there.
      return;
    }
    const r = await voice.browserAsk();
    if (r) {
      setItems((prev) => [...prev, { q: r.transcription, a: r.answer }]);
    } else if (voice.error) {
      setError(voice.error);
    }
  };

  const chips = [
    lang === 'mr'
      ? 'मला बँकेत जावे लागेल का?'
      : lang === 'en'
        ? 'Do I need to visit the office?'
        : 'क्या मुझे कार्यालय जाना पड़ेगा?',
    lang === 'mr'
      ? 'दुर्लक्ष केल्यास काय होईल?'
      : lang === 'en'
        ? 'What if I ignore it?'
        : 'अगर नजरअंदाज कर दूं तो क्या होगा?',
  ];

  return (
    <div className="card-elevated bg-white flex flex-col gap-4">
      <div className="flex items-center justify-between border-b border-gray-100 pb-3 mb-1">
        <div className="flex items-center gap-2">
          <MessageSquare size={18} className="text-primary" />
          <h3 className="font-bold text-gray-900 text-base">{t.askTitle}</h3>
        </div>
        <span className="text-xs text-gray-400">
          {t.askCounterLabel.replace('{count}', String(items.length))}
        </span>
      </div>

      {items.length > 0 && (
        <div className="flex flex-col gap-3 max-h-80 overflow-y-auto">
          {items.map((m, i) => (
            <div key={i} className="flex flex-col gap-1.5">
              <div className="self-end bg-primary/10 text-gray-900 text-sm rounded-xl rounded-br-sm px-3 py-2 max-w-[90%]">
                {m.q}
              </div>
              <div className="self-start bg-gray-50 border border-gray-100 text-gray-800 text-sm rounded-xl rounded-bl-sm px-3 py-2 max-w-[95%] whitespace-pre-wrap">
                {m.a}
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="flex flex-wrap gap-2 mb-1">
        {chips.map((c) => (
          <button
            key={c}
            onClick={() => void ask(c)}
            disabled={busy || items.length >= MAX_Q}
            className="text-xs border border-gray-300 text-gray-600 rounded-full px-3 py-1.5 hover:bg-gray-50 text-left leading-tight disabled:opacity-50"
          >
            {c}
          </button>
        ))}
      </div>

      {error && <p className="text-xs text-red-600">{error}</p>}
      {voice.error && <p className="text-xs text-red-600">{voice.error}</p>}

      <div className="relative mt-1">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') void ask(input);
          }}
          placeholder={t.askPlaceholder}
          disabled={busy || items.length >= MAX_Q}
          className="w-full border border-gray-300 rounded-xl pl-4 pr-32 sm:pr-36 py-3 text-sm focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary disabled:opacity-60"
        />
        <div className="absolute right-1.5 top-1.5 flex items-center gap-1">
          <button
            onClick={() => void onMic()}
            disabled={voice.busy || busy || voice.mode === 'none' || items.length >= MAX_Q}
            title={t.voiceTitle}
            className="min-w-[44px] min-h-[44px] p-2 text-gray-400 hover:text-gray-600 transition-colors disabled:opacity-40 flex items-center justify-center"
          >
            <Mic size={18} />
          </button>
          <button
            onClick={() => void ask(input)}
            disabled={busy || !input.trim() || items.length >= MAX_Q}
            className="bg-primary text-white rounded-lg px-3 py-2.5 min-h-[44px] flex items-center gap-1 text-sm font-medium hover:bg-primary-hover transition-colors disabled:opacity-50"
          >
            {busy ? '…' : t.askButton} <Send size={14} />
          </button>
        </div>
      </div>
    </div>
  );
}

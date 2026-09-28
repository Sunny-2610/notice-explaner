import { useEffect, useRef, useState } from 'react';
import { Mic, Volume2 } from 'lucide-react';
import { STRINGS, type Lang } from '../i18n/strings';
import { askQuestion } from '../lib/api';
import { useVoiceAsk } from '../hooks/useVoiceAsk';

const SUGGESTED: Record<Lang, string[]> = {
  hi: [
    'अगर मैं इसे नजरअंदाज कर दूं तो क्या होगा?',
    'मुझे कहाँ भुगतान करना है?',
    'समन का क्या मतलब है?',
  ],
  mr: [
    'दुर्लक्ष केल्यास काय होईल?',
    'मला कुठे भरणा करावा लागेल?',
    'समन्स म्हणजे काय?',
  ],
};

export default function FollowUpQA({
  jobId,
  lang,
  initialQuestion = null,
  onInitialConsumed,
}: {
  jobId: string;
  lang: Lang;
  initialQuestion?: string | null;
  onInitialConsumed?: () => void;
}) {
  const t = STRINGS[lang];
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [askedCount, setAskedCount] = useState(0);
  const [recording, setRecording] = useState(false);
  const consumedRef = useRef(false);
  const recRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const recordingRef = useRef(false);
  const downTimeRef = useRef(0);
  const tapArmedRef = useRef(false);
  const { mode, serverAsk, browserAsk, speak } = useVoiceAsk(jobId, lang);

  const submit = async (q: string) => {
    const text = q.trim();
    if (!text || busy) return;
    setBusy(true);
    setError(null);
    try {
      const r = await askQuestion(jobId, text);
      setAnswer(r.answer);
      setQuestion('');
      setAskedCount((c) => c + 1);
    } catch {
      setError(t.failed);
    } finally {
      setBusy(false);
    }
  };

  // Home-screen voice transcript auto-submits once the job is completed
  // (this component only renders on the completed screen).
  useEffect(() => {
    if (initialQuestion && !consumedRef.current) {
      consumedRef.current = true;
      onInitialConsumed?.();
      void submit(initialQuestion);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialQuestion]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      chunksRef.current = [];
      const rec = new MediaRecorder(stream);
      rec.ondataavailable = (e) => {
        if (e.data.size) chunksRef.current.push(e.data);
      };
      rec.onstop = async () => {
        const blob = new Blob(chunksRef.current, { type: rec.mimeType });
        rec.stream.getTracks().forEach((tr) => tr.stop());
        const r = await serverAsk(blob);
        if (r) {
          setAnswer(r.answer);
          setAskedCount((c) => c + 1);
        }
      };
      recRef.current = rec;
      rec.start();
      recordingRef.current = true;
      setRecording(true);
    } catch {
      setError(t.textOnly);
    }
  };

  const stopRecording = () => {
    recordingRef.current = false;
    tapArmedRef.current = false;
    setRecording(false);
    recRef.current?.stop();
  };

  const toggleRecording = () => {
    if (recordingRef.current) stopRecording();
    else void startRecording();
  };

  const onMic = async () => {
    if (mode === 'browser') {
      const r = await browserAsk();
      if (r) {
        setAnswer(r.answer);
        setAskedCount((c) => c + 1);
      }
      return;
    }
    if (mode !== 'server') return;
    toggleRecording();
  };

  const showMic = mode === 'server' || mode === 'browser';

  return (
    <section className="card space-y-3">
      <h3 className="text-base font-semibold">{t.askTitle}</h3>
      <div className="flex flex-wrap gap-2">
        {SUGGESTED[lang].map((s) => (
          <button
            key={s}
            onClick={() => submit(s)}
            disabled={busy}
            className="chip-info min-h-[48px] px-4 text-sm text-left disabled:opacity-40"
          >
            {s}
          </button>
        ))}
      </div>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          submit(question);
        }}
        className="flex gap-2"
      >
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder={t.askPlaceholder}
          aria-label={t.askTitle}
          className="flex-1 min-h-[48px] rounded-xl border-2 border-border px-4 text-base bg-white placeholder:text-text-muted"
        />
        {showMic && (
          <button
            type="button"
            // Tap toggles recording; hold records until release (server mode).
            // Browser mode uses a plain click (recognition handles its own stop).
            onClick={(e) => {
              if (mode === 'browser') {
                void onMic();
                return;
              }
              if (e.detail === 0) {
                // Keyboard activation — pointer handlers don't fire.
                toggleRecording();
                return;
              }
              if (tapArmedRef.current) {
                // Second tap of a tap-toggle pair: stop.
                stopRecording();
              }
              // Otherwise the pointer-up handler already stopped a hold.
            }}
            onPointerDown={(e) => {
              if (mode !== 'server') return;
              e.preventDefault();
              downTimeRef.current = Date.now();
              tapArmedRef.current = false;
              if (!recordingRef.current) void startRecording();
            }}
            onPointerUp={() => {
              if (mode !== 'server' || !recordingRef.current) return;
              const held = Date.now() - downTimeRef.current;
              if (held < 250) {
                // Short tap: keep recording (toggle-on); the next tap stops.
                tapArmedRef.current = true;
              } else {
                stopRecording();
              }
            }}
            onPointerCancel={() => {
              if (mode === 'server' && recordingRef.current) stopRecording();
            }}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                void onMic();
              }
            }}
            aria-label={t.voiceTitle}
            aria-pressed={recording}
            style={{ touchAction: 'none' }}
            className={`min-h-[48px] min-w-[48px] px-3 rounded-xl border-2 inline-flex items-center justify-center ${
              recording ? 'bg-error text-white border-error' : 'border-border bg-white'
            }`}
          >
            <Mic size={20} strokeWidth={1.75} aria-hidden />
          </button>
        )}
        <button type="submit" disabled={!question.trim() || busy} className="btn-primary disabled:opacity-40">
          {busy ? '…' : t.askButton}
        </button>
      </form>
      <p className="text-xs text-text-muted" aria-live="polite">
        {t.askCounterLabel.replace('{count}', String(askedCount))}
      </p>
      {error && <p className="text-sm text-error">{error}</p>}
      {answer && (
        <article className="rounded-xl bg-surface p-4 text-base leading-7 whitespace-pre-line">
          {answer}
          <div className="mt-2">
            <button
              onClick={() => void speak(answer)}
              className="btn-secondary inline-flex items-center gap-2"
            >
              <Volume2 size={20} strokeWidth={1.75} aria-hidden />
              {t.listen}
            </button>
          </div>
        </article>
      )}
    </section>
  );
}

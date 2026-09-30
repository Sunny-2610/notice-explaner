import { useEffect, useState } from 'react';
import type { Lang } from '../i18n/strings';
import { askQuestion } from '../lib/api';
import { blobTo16kWav } from '../lib/wav';

const API_BASE = import.meta.env.VITE_API_BASE ?? '';

export type VoiceMode = 'server' | 'browser' | 'none';

interface SRWindow extends Window {
  SpeechRecognition?: new () => SpeechRecognizer;
  webkitSpeechRecognition?: new () => SpeechRecognizer;
}

interface SpeechRecognizer {
  lang: string;
  onresult: ((e: { results: { transcript: string }[][] }) => void) | null;
  onerror: (() => void) | null;
  onend: (() => void) | null;
  start: () => void;
  stop: () => void;
}

function browserLocale(lang: Lang): string {
  return lang === 'mr' ? 'mr-IN' : lang === 'en' ? 'en-IN' : 'hi-IN';
}

function hasSpeechRecognition(): boolean {
  const w = window as SRWindow;
  return !!(w.SpeechRecognition ?? w.webkitSpeechRecognition);
}

/** Speak via server TTS (voice-speech text=answer); fall back to speechSynthesis on 204/failure. */
export async function speakAnswer(
  jobId: string | null,
  text: string,
  lang: Lang,
): Promise<void> {
  if (jobId) {
    try {
      const form = new FormData();
      form.append('lang', lang);
      form.append('text', text.slice(0, 1500));
      const res = await fetch(`${API_BASE}/api/v1/documents/${jobId}/voice-speech`, {
        method: 'POST',
        body: form,
      });
      if (res.ok && res.status !== 204) {
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        await new Promise<void>((resolve) => {
          const audio = new Audio(url);
          audio.onended = () => {
            URL.revokeObjectURL(url);
            resolve();
          };
          audio.onerror = () => {
            URL.revokeObjectURL(url);
            resolve();
          };
          void audio.play().catch(() => resolve());
        });
        return;
      }
    } catch {
      /* fall through to speechSynthesis */
    }
  }
  if ('speechSynthesis' in window) {
    window.speechSynthesis.cancel();
    const utter = new SpeechSynthesisUtterance(text);
    utter.lang = browserLocale(lang);
    window.speechSynthesis.speak(utter);
  }
}

export function useVoiceAsk(jobId: string | null, lang: Lang) {
  const [mode, setMode] = useState<VoiceMode | null>(null);
  const [busy, setBusy] = useState(false);
  const [transcript, setTranscript] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetch(`${API_BASE}/health`)
      .then((r) => (r.ok ? r.json() : { voiceEnabled: false }))
      .then((body) => {
        if (cancelled) return;
        if (body.voiceEnabled) setMode('server');
        else if (hasSpeechRecognition()) setMode('browser');
        else setMode('none');
      })
      .catch(() => {
        if (!cancelled) setMode(hasSpeechRecognition() ? 'browser' : 'none');
      });
    return () => {
      cancelled = true;
    };
  }, []);

  /** Server mode: WAV -> voice-ask -> {transcription, answer}. */
  const serverAsk = async (
    audio: Blob,
  ): Promise<{ transcription: string; answer: string } | null> => {
    if (!jobId) return null;
    setBusy(true);
    setError(null);
    try {
      const wav = await blobTo16kWav(audio);
      const form = new FormData();
      form.append('audio', wav, 'query.wav');
      form.append('lang', lang);
      const res = await fetch(`${API_BASE}/api/v1/documents/${jobId}/voice-ask`, {
        method: 'POST',
        body: form,
      });
      if (!res.ok) {
        setError(`Voice ask failed (${res.status})`);
        return null;
      }
      const body = await res.json();
      if (!body.voiceAvailable) return null;
      setTranscript(body.transcription ?? '');
      return {
        transcription: body.transcription ?? '',
        answer: body.answer ?? '',
      };
    } catch (e) {
      setError((e as Error).message);
      return null;
    } finally {
      setBusy(false);
    }
  };

  /** Browser mode: on-device/browser recognition -> existing askQuestion(). */
  const browserAsk = async (): Promise<{ transcription: string; answer: string } | null> => {
    if (!jobId || !hasSpeechRecognition()) return null;
    setBusy(true);
    setError(null);
    try {
      const w = window as SRWindow;
      const Ctor = w.SpeechRecognition ?? w.webkitSpeechRecognition;
      if (!Ctor) return null;
      const rec = new Ctor();
      rec.lang = browserLocale(lang);
      const text: string = await new Promise((resolve, reject) => {
        rec.onresult = (e) => {
          const last = e.results[e.results.length - 1];
          resolve(last[0].transcript);
        };
        rec.onerror = () => reject(new Error('recognition failed'));
        rec.onend = () => {};
        rec.start();
        // Stop after 8s so the mic never hangs open.
        setTimeout(() => {
          try {
            rec.stop();
          } catch {
            /* already stopped */
          }
        }, 8000);
      });
      setTranscript(text);
      const r = await askQuestion(jobId, text);
      return { transcription: text, answer: r.answer };
    } catch (e) {
      setError((e as Error).message);
      return null;
    } finally {
      setBusy(false);
    }
  };

  const speak = (text: string) => speakAnswer(jobId, text, lang);

  return { mode, busy, transcript, error, serverAsk, browserAsk, speak };
}

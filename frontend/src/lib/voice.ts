const API_BASE = import.meta.env.VITE_API_BASE ?? '';

/** Returns object URL for playback, or null when voice unavailable (E-302). */
export async function fetchSpeech(jobId: string, lang: string): Promise<string | null> {
  const form = new FormData();
  form.append('lang', lang);
  const res = await fetch(`${API_BASE}/api/v1/documents/${jobId}/voice-speech`, {
    method: 'POST',
    body: form,
  });
  if (res.status === 204) return null;
  if (!res.ok) return null;
  const blob = await res.blob();
  return URL.createObjectURL(blob);
}

export async function queryVoice(
  jobId: string,
  audio: Blob,
  lang: string,
): Promise<{ transcription: string; voiceAvailable: boolean }> {
  const form = new FormData();
  form.append('audio', audio, 'query.webm');
  form.append('lang', lang);
  const res = await fetch(`${API_BASE}/api/v1/documents/${jobId}/voice-query`, {
    method: 'POST',
    body: form,
  });
  if (!res.ok) return { transcription: '', voiceAvailable: false };
  return res.json();
}

import { ref } from 'vue';

const speakingRef = ref(false);

function buildSpeechPayload(text) {
  return {
    text,
    voice_settings: {
      stability: 0.5,
      similarity_boost: 0.5
    }
  };
}

export function useVoiceInsights() {
  const speaking = speakingRef;

  async function speakInsights(text) {
    const content = Array.isArray(text) ? text.filter(Boolean).join(' ') : text;
    const trimmed = (content || '').trim();
    const apiKey = import.meta.env.VITE_ELEVENLABS_API_KEY;
    const voiceId = import.meta.env.VITE_ELEVENLABS_VOICE_ID || '21m00Tcm4TlvDq8ikWAM';

    if (!apiKey) {
      alert('ElevenLabs API key not configured. Set VITE_ELEVENLABS_API_KEY in .env.');
      return;
    }
    if (!trimmed) {
      alert('No insights available to narrate.');
      return;
    }

    speaking.value = true;
    try {
      const url = `https://api.elevenlabs.io/v1/text-to-speech/${voiceId}`;
      const resp = await fetch(url, {
        method: 'POST',
        headers: {
          'xi-api-key': apiKey,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(buildSpeechPayload(trimmed))
      });

      if (!resp.ok) throw new Error('TTS request failed');

      const blob = await resp.blob();
      const audioUrl = URL.createObjectURL(blob);
      const audio = new Audio(audioUrl);
      await audio.play();
    } catch (err) {
      console.error('Voice insights failed', err);
      alert('Failed to generate voice insights.');
      throw err;
    } finally {
      speaking.value = false;
    }
  }

  return { speaking, speakInsights };
}


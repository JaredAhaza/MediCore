import os
import requests
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions


class TTSAudioView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """Generate TTS audio via ElevenLabs.

        Expects JSON body: { text: string, voice_id?: string, model_id?: string, voice_settings?: { stability?: float, similarity_boost?: float } }
        Returns: raw audio bytes with content-type 'audio/mpeg' on success, otherwise JSON error.
        """
        api_key = os.getenv('ELEVENLABS_API_KEY')
        default_voice = os.getenv('ELEVENLABS_VOICE_ID', 'EXAVITQu4vr4xnSDxMaL')
        if not api_key:
            return Response({'detail': 'ELEVENLABS_API_KEY not configured'}, status=status.HTTP_400_BAD_REQUEST)

        data = request.data or {}
        text = data.get('text')
        if not text or not isinstance(text, str):
            return Response({'detail': 'Invalid or missing "text"'}, status=status.HTTP_400_BAD_REQUEST)

        voice_id = data.get('voice_id') or default_voice
        model_id = data.get('model_id') or 'eleven_multilingual_v2'
        voice_settings = data.get('voice_settings') or { 'stability': 0.5, 'similarity_boost': 0.5 }

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        payload = {
            'text': text,
            'model_id': model_id,
            'voice_settings': voice_settings,
        }
        headers = {
            'xi-api-key': api_key,
            'Content-Type': 'application/json'
        }

        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=30)
        except requests.RequestException as e:
            return Response({'detail': f'Network error calling ElevenLabs: {str(e)}'}, status=status.HTTP_502_BAD_GATEWAY)

        if resp.status_code != 200:
            # Try to surface ElevenLabs error message if available
            try:
                err = resp.json()
            except Exception:
                err = {'detail': 'Non-200 from ElevenLabs', 'status_code': resp.status_code}
            return Response(err, status=status.HTTP_502_BAD_GATEWAY)

        # Return audio bytes
        return HttpResponse(resp.content, content_type='audio/mpeg')

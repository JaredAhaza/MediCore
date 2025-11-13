from django.urls import path
from .views import TTSAudioView

urlpatterns = [
    path('tts/', TTSAudioView.as_view(), name='tts'),
]
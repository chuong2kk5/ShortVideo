import { useState, useRef, useEffect } from 'react';

export function useAudioPreview() {
  const [playingVoiceId, setPlayingVoiceId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const stop = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      audioRef.current = null;
    }
    setPlayingVoiceId(null);
    setIsLoading(false);
  };

  const play = (voiceId: string, customText?: string) => {
    // If clicking the same voice that is currently playing, pause/stop it
    if (playingVoiceId === voiceId) {
      stop();
      return;
    }

    // Stop any previous audio
    stop();

    setIsLoading(true);
    setPlayingVoiceId(voiceId);

    const query = new URLSearchParams({ voice: voiceId });
    if (customText?.trim()) {
      query.set('text', customText.trim());
    }

    const audioUrl = `/api/tts/preview?${query.toString()}`;
    const audio = new Audio(audioUrl);
    audioRef.current = audio;

    audio.oncanplaythrough = () => {
      setIsLoading(false);
    };

    audio.play().catch((err) => {
      console.warn('Audio playback error (user interaction might be needed):', err);
      stop();
    });

    audio.onended = () => {
      stop();
    };

    audio.onerror = () => {
      console.error('Audio load error for voice:', voiceId);
      stop();
    };
  };

  useEffect(() => {
    return () => {
      stop();
    };
  }, []);

  return {
    playingVoiceId,
    isLoading,
    play,
    stop,
  };
}


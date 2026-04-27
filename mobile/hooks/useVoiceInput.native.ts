import { useCallback, useEffect, useRef, useState } from "react";

let Voice: any = null;
try {
  Voice = require("@react-native-voice/voice").default;
} catch {
  // Voice not available
}

interface UseVoiceInputReturn {
  listening: boolean;
  transcript: string;
  startListening: () => void;
  stopListening: () => void;
  supported: boolean;
}

export function useVoiceInput(): UseVoiceInputReturn {
  const [listening, setListening] = useState(false);
  const [transcript, setTranscript] = useState("");
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const supported = Voice != null;

  useEffect(() => {
    if (!Voice) return;

    Voice.onSpeechResults = (e: any) => {
      const text = e.value?.[0] ?? "";
      setTranscript(text);
      setListening(false);
    };

    Voice.onSpeechError = () => {
      setListening(false);
    };

    return () => {
      Voice.destroy().then(Voice.removeAllListeners);
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, []);

  const startListening = useCallback(async () => {
    if (!Voice) return;
    setTranscript("");
    setListening(true);
    try {
      await Voice.start("en-US");
      // Auto-stop after 3 seconds of silence
      timerRef.current = setTimeout(async () => {
        try {
          await Voice.stop();
        } catch {}
        setListening(false);
      }, 3000);
    } catch {
      setListening(false);
    }
  }, []);

  const stopListening = useCallback(async () => {
    if (!Voice) return;
    if (timerRef.current) clearTimeout(timerRef.current);
    try {
      await Voice.stop();
    } catch {}
    setListening(false);
  }, []);

  return { listening, transcript, startListening, stopListening, supported };
}

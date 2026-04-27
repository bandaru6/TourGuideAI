import { useCallback, useRef, useState } from "react";
import * as Speech from "expo-speech";

export function useNarrationQueue() {
  const [enabled, setEnabled] = useState(true);
  const queue = useRef<string[]>([]);
  const speaking = useRef(false);

  const processQueue = useCallback(() => {
    if (!enabled || speaking.current || queue.current.length === 0) return;

    const text = queue.current.shift()!;
    speaking.current = true;

    Speech.speak(text, {
      language: "en-US",
      rate: 0.95,
      onDone: () => {
        speaking.current = false;
        processQueue();
      },
      onError: () => {
        speaking.current = false;
        processQueue();
      },
    });
  }, [enabled]);

  const enqueue = useCallback(
    (text: string) => {
      if (!enabled) return;
      queue.current.push(text);
      processQueue();
    },
    [enabled, processQueue]
  );

  const stop = useCallback(() => {
    Speech.stop();
    queue.current = [];
    speaking.current = false;
  }, []);

  const toggle = useCallback(() => {
    setEnabled((prev) => {
      if (prev) {
        stop();
      }
      return !prev;
    });
  }, [stop]);

  return { enqueue, stop, toggle, enabled };
}

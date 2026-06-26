import { useEffect, useRef, useCallback } from "react";
import { useAuthStore } from "../store/authStore";

export interface NotifEvent {
  type: "nouveau_courrier";
  id: string;
  reference: string;
  objet: string;
  expediteur: string;
  priorite: string;
}

export function useNotifications(onEvent: (e: NotifEvent) => void) {
  const token = useAuthStore((s) => s.token);
  const esRef = useRef<EventSource | null>(null);
  const onEventRef = useRef(onEvent);
  onEventRef.current = onEvent;

  const connect = useCallback(() => {
    if (!token) return;
    const url = `${import.meta.env.VITE_API_URL ?? ""}/notifications/stream?token=${encodeURIComponent(token)}`;
    const es = new EventSource(url);

    es.onmessage = (ev) => {
      try {
        const data = JSON.parse(ev.data) as NotifEvent;
        onEventRef.current(data);
      } catch {
        // ignore ping ou JSON invalide
      }
    };

    es.onerror = () => {
      es.close();
      esRef.current = null;
      // Reconnexion après 10s en cas d'erreur réseau
      setTimeout(connect, 10_000);
    };

    esRef.current = es;
  }, [token]);

  useEffect(() => {
    connect();
    return () => {
      esRef.current?.close();
      esRef.current = null;
    };
  }, [connect]);
}

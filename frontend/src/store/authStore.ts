import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { Utilisateur } from "../types";

interface AuthState {
  token: string | null;
  utilisateur: Utilisateur | null;
  setAuth: (token: string, utilisateur: Utilisateur) => void;
  logout: () => void;
  isAuthenticated: () => boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      token: null,
      utilisateur: null,
      setAuth: (token, utilisateur) => set({ token, utilisateur }),
      logout: () => set({ token: null, utilisateur: null }),
      isAuthenticated: () => get().token !== null,
    }),
    { name: "gec-auth" }
  )
);

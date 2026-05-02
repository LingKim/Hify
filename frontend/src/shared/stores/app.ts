import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import type { NavigationMode, ThemeMode, ThemePreference } from "@/app/preferences/config";

interface AppStoreState {
  siderCollapsed: boolean;
  isPreferencesDrawerOpen: boolean;
  themePreference: ThemePreference;
  resolvedThemeMode: ThemeMode;
  navigationMode: NavigationMode;
  setSiderCollapsed: (collapsed: boolean) => void;
  toggleSiderCollapsed: () => void;
  openPreferencesDrawer: () => void;
  closePreferencesDrawer: () => void;
  setThemePreference: (preference: ThemePreference) => void;
  syncSystemTheme: () => void;
  setNavigationMode: (mode: NavigationMode) => void;
}

function getSystemThemeMode(): ThemeMode {
  if (typeof window === "undefined") {
    return "light";
  }

  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function resolveThemeMode(preference: ThemePreference): ThemeMode {
  if (preference === "system") {
    return getSystemThemeMode();
  }

  return preference;
}

export const useAppStore = create<AppStoreState>()(
  persist(
    (set, get) => ({
      siderCollapsed: false,
      isPreferencesDrawerOpen: false,
      themePreference: "system",
      resolvedThemeMode: getSystemThemeMode(),
      navigationMode: "side",
      setSiderCollapsed: (collapsed) => {
        set({ siderCollapsed: collapsed });
      },
      toggleSiderCollapsed: () => {
        set((state) => ({
          siderCollapsed: !state.siderCollapsed,
        }));
      },
      openPreferencesDrawer: () => {
        set({ isPreferencesDrawerOpen: true });
      },
      closePreferencesDrawer: () => {
        set({ isPreferencesDrawerOpen: false });
      },
      setThemePreference: (preference) => {
        set({
          themePreference: preference,
          resolvedThemeMode: resolveThemeMode(preference),
        });
      },
      syncSystemTheme: () => {
        const { themePreference } = get();

        if (themePreference === "system") {
          set({
            resolvedThemeMode: getSystemThemeMode(),
          });
        }
      },
      setNavigationMode: (mode) => {
        set({ navigationMode: mode });
      },
    }),
    {
      name: "hify-app-preferences",
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        themePreference: state.themePreference,
        navigationMode: state.navigationMode,
      }),
      onRehydrateStorage: () => (state) => {
        if (state !== undefined) {
          state.syncSystemTheme();
        }
      },
    },
  ),
);

import { useEffect, useMemo, type PropsWithChildren } from "react";
import { QueryClientProvider } from "@tanstack/react-query";
import { App as AntdApp, ConfigProvider } from "antd";
import { themeRegistry } from "@/app/theme/registry";
import { queryClient } from "@/shared/query/client";
import { useAppStore } from "@/shared/stores/app";

export function AppProviders({ children }: PropsWithChildren): JSX.Element {
  const resolvedThemeMode = useAppStore((state) => state.resolvedThemeMode);
  const syncSystemTheme = useAppStore((state) => state.syncSystemTheme);
  const activeTheme = useMemo(() => themeRegistry[resolvedThemeMode], [resolvedThemeMode]);

  useEffect(() => {
    document.documentElement.dataset.theme = activeTheme.dataTheme;

    Object.entries(activeTheme.cssVariables).forEach(([name, value]) => {
      document.documentElement.style.setProperty(name, value);
    });
  }, [activeTheme]);

  useEffect(() => {
    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
    const handleChange = () => {
      syncSystemTheme();
    };

    handleChange();
    mediaQuery.addEventListener("change", handleChange);

    return () => {
      mediaQuery.removeEventListener("change", handleChange);
    };
  }, [syncSystemTheme]);

  return (
    <QueryClientProvider client={queryClient}>
      <ConfigProvider theme={activeTheme.antdTheme}>
        <AntdApp>{children}</AntdApp>
      </ConfigProvider>
    </QueryClientProvider>
  );
}

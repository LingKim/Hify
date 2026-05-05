import { theme } from "antd";
import type { ThemeConfig } from "antd";
import type { ThemeMode } from "@/app/preferences/config";
import {
  buildLightVariables,
  buildDarkVariables,
  antdHex,
} from "@/app/theme/tokens";

export interface ThemeDefinition {
  mode: ThemeMode;
  dataTheme: ThemeMode;
  antdTheme: ThemeConfig;
  cssVariables: Record<string, string>;
}

export type ThemeRegistry = Record<ThemeMode, ThemeDefinition>;

const fontFamily =
  '"PingFang SC", "Hiragino Sans GB", "Source Han Sans SC", "Noto Sans SC", system-ui, sans-serif';

export const themeRegistry: ThemeRegistry = {
  light: {
    mode: "light",
    dataTheme: "light",
    antdTheme: {
      algorithm: theme.defaultAlgorithm,
      token: {
        colorPrimary: antdHex.primaryLight,
        colorBgLayout: "#f5f5f5",
        colorBgContainer: "#ffffff",
        colorBgElevated: "#ffffff",
        colorText: "#171717",
        colorTextSecondary: "#525252",
        colorTextTertiary: "#8a8a8a",
        colorBorder: "oklch(91% 0.002 0)",
        colorBorderSecondary: "oklch(94% 0.001 0)",
        borderRadius: 10,
        colorSuccess: "#22c55e",
        colorWarning: "#f59e0b",
        colorError: "#ef4444",
        colorInfo: antdHex.primaryLight,
        fontFamily,
      },
    },
    cssVariables: buildLightVariables(),
  },
  dark: {
    mode: "dark",
    dataTheme: "dark",
    antdTheme: {
      algorithm: theme.darkAlgorithm,
      token: {
        colorPrimary: antdHex.primaryDark,
        colorBgLayout: "#0a0a0a",
        colorBgContainer: "#171717",
        colorBgElevated: "#1f1f1f",
        colorText: "#ebebeb",
        colorTextSecondary: "#a0a0a0",
        colorTextTertiary: "#6b6b6b",
        colorBorder: "oklch(28% 0.003 0)",
        colorBorderSecondary: "oklch(24% 0.002 0)",
        borderRadius: 10,
        colorSuccess: "#34d399",
        colorWarning: "#fbbf24",
        colorError: "#f87171",
        colorInfo: antdHex.primaryDark,
        fontFamily,
      },
    },
    cssVariables: buildDarkVariables(),
  },
};

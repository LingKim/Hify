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
        colorBgLayout: "#f3f4f8",
        colorBgContainer: "#ffffff",
        colorBgElevated: "#ffffff",
        colorText: "#1a2035",
        colorTextSecondary: "#5b6580",
        colorTextTertiary: "#8a92a8",
        colorBorder: "oklch(91% 0.005 270)",
        colorBorderSecondary: "oklch(94% 0.004 260)",
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
        colorBgLayout: "#0f1420",
        colorBgContainer: "#181e2e",
        colorBgElevated: "#1e2538",
        colorText: "#e8ecf8",
        colorTextSecondary: "#9ea8c4",
        colorTextTertiary: "#6b7590",
        colorBorder: "oklch(28% 0.015 270)",
        colorBorderSecondary: "oklch(24% 0.012 270)",
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

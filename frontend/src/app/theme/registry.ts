import { theme } from "antd";
import type { ThemeConfig } from "antd";
import type { ThemeMode } from "@/app/preferences/config";

export interface ThemeDefinition {
  mode: ThemeMode;
  dataTheme: ThemeMode;
  antdTheme: ThemeConfig;
  cssVariables: Record<string, string>;
}

export type ThemeRegistry = Record<ThemeMode, ThemeDefinition>;

export const themeRegistry: ThemeRegistry = {
  light: {
    mode: "light",
    dataTheme: "light",
    antdTheme: {
      algorithm: theme.defaultAlgorithm,
      token: {
        colorPrimary: "#4f72c9",
        colorBgLayout: "#f2f5fb",
        colorBgContainer: "#ffffff",
        colorText: "#263249",
        colorTextSecondary: "#5b6780",
        borderRadius: 16,
      },
    },
    cssVariables: {
      "--page-bg": "oklch(96.9% 0.008 245)",
      "--panel-bg": "rgb(255 255 255 / 94%)",
      "--panel-border": "rgb(29 51 84 / 10%)",
      "--panel-shadow": "0 20px 60px rgb(19 34 58 / 7%)",
      "--text-strong": "oklch(24% 0.02 255)",
      "--text-body": "oklch(42% 0.02 255)",
      "--text-soft": "oklch(56% 0.02 255)",
      "--brand": "oklch(44% 0.06 248)",
      "--brand-strong": "oklch(31% 0.05 249)",
      "--brand-tint": "oklch(92% 0.02 246)",
      "--accent": "oklch(58% 0.09 226)",
      "--sider-bg": "linear-gradient(180deg, oklch(23% 0.026 255) 0%, oklch(19% 0.022 255) 100%)",
      "--sider-border": "rgb(255 255 255 / 8%)",
      "--top-nav-bg": "rgb(255 255 255 / 84%)",
      "--top-nav-border": "rgb(29 51 84 / 10%)",
      "--top-nav-item-hover": "rgb(79 114 201 / 10%)",
      "--top-nav-item-active":
        "linear-gradient(135deg, rgb(101 138 223 / 18%) 0%, rgb(58 90 157 / 28%) 100%)",
      "--drawer-surface":
        "linear-gradient(180deg, rgb(250 252 255 / 100%) 0%, rgb(245 248 253 / 100%) 100%)",
    },
  },
  dark: {
    mode: "dark",
    dataTheme: "dark",
    antdTheme: {
      algorithm: theme.darkAlgorithm,
      token: {
        colorPrimary: "#7f98dd",
        colorBgLayout: "#101722",
        colorBgContainer: "#151d2a",
        colorText: "#edf2ff",
        colorTextSecondary: "#9eacc8",
        borderRadius: 16,
      },
    },
    cssVariables: {
      "--page-bg": "oklch(18% 0.018 255)",
      "--panel-bg": "rgb(20 28 39 / 92%)",
      "--panel-border": "rgb(149 170 216 / 10%)",
      "--panel-shadow": "0 24px 80px rgb(0 0 0 / 24%)",
      "--text-strong": "oklch(94% 0.012 255)",
      "--text-body": "oklch(78% 0.02 255)",
      "--text-soft": "oklch(66% 0.018 255)",
      "--brand": "oklch(68% 0.07 248)",
      "--brand-strong": "oklch(58% 0.06 249)",
      "--brand-tint": "rgb(84 109 181 / 18%)",
      "--accent": "oklch(74% 0.08 228)",
      "--sider-bg": "linear-gradient(180deg, oklch(20% 0.02 255) 0%, oklch(15% 0.018 255) 100%)",
      "--sider-border": "rgb(255 255 255 / 6%)",
      "--top-nav-bg": "rgb(19 27 39 / 88%)",
      "--top-nav-border": "rgb(149 170 216 / 10%)",
      "--top-nav-item-hover": "rgb(127 152 221 / 14%)",
      "--top-nav-item-active":
        "linear-gradient(135deg, rgb(127 152 221 / 26%) 0%, rgb(85 110 179 / 32%) 100%)",
      "--drawer-surface":
        "linear-gradient(180deg, rgb(21 29 41 / 100%) 0%, rgb(17 24 34 / 100%) 100%)",
    },
  },
};

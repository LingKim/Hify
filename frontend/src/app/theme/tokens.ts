/**
 * Hify Design Tokens
 *
 * Visual identity: light surface + dark sidebar + blue-purple brand + teal accents.
 * Reference aesthetic: Linear / Supabase — clean precision with intentional color.
 *
 * Color space: OKLCH for perceptual uniformity.
 */

// ─── Color Scales ────────────────────────────────────────────────────────────

const primary = {
  50: "oklch(97.2% 0.011 270)",
  100: "oklch(94.0% 0.022 270)",
  200: "oklch(89.2% 0.038 270)",
  300: "oklch(81.8% 0.058 270)",
  400: "oklch(71.5% 0.088 270)",
  500: "oklch(58.0% 0.120 270)",
  600: "oklch(50.0% 0.115 270)",
  700: "oklch(42.5% 0.092 270)",
  800: "oklch(35.5% 0.072 270)",
  900: "oklch(28.0% 0.052 270)",
} as const;

const secondary = {
  50: "oklch(97.4% 0.014 185)",
  100: "oklch(93.8% 0.028 185)",
  200: "oklch(88.2% 0.048 185)",
  300: "oklch(80.0% 0.072 185)",
  400: "oklch(71.5% 0.100 185)",
  500: "oklch(64.0% 0.115 185)",
  600: "oklch(55.5% 0.100 185)",
  700: "oklch(47.5% 0.080 185)",
  800: "oklch(40.0% 0.060 185)",
  900: "oklch(32.5% 0.042 185)",
} as const;

// Blue-tinted grays — cohesive with the brand purple
const neutralLight = {
  50: "oklch(99.2% 0.002 260)",
  100: "oklch(97.5% 0.003 260)",
  200: "oklch(95.0% 0.004 260)",
  300: "oklch(91.0% 0.005 260)",
  400: "oklch(83.0% 0.005 260)",
  500: "oklch(68.0% 0.006 260)",
  600: "oklch(50.0% 0.007 260)",
  700: "oklch(38.0% 0.007 260)",
  800: "oklch(27.0% 0.008 260)",
  900: "oklch(18.0% 0.008 260)",
} as const;

// Purple-tinted dark grays — cohesive with dark sidebar
const neutralDark = {
  50: "oklch(14.0% 0.015 270)",
  100: "oklch(17.0% 0.015 270)",
  200: "oklch(20.5% 0.014 270)",
  300: "oklch(25.0% 0.013 270)",
  400: "oklch(32.0% 0.012 270)",
  500: "oklch(42.0% 0.010 270)",
  600: "oklch(55.0% 0.009 270)",
  700: "oklch(70.0% 0.008 270)",
  800: "oklch(82.0% 0.007 270)",
  900: "oklch(94.0% 0.006 270)",
} as const;

// ─── Semantic Colors ─────────────────────────────────────────────────────────

const semantic = {
  success: {
    light: { default: "oklch(55% 0.13 155)", subtle: "oklch(95% 0.03 155)" },
    dark: { default: "oklch(70% 0.11 155)", subtle: "oklch(25% 0.03 155)" },
  },
  warning: {
    light: { default: "oklch(68% 0.14 75)", subtle: "oklch(95% 0.04 75)" },
    dark: { default: "oklch(75% 0.12 75)", subtle: "oklch(25% 0.03 75)" },
  },
  error: {
    light: { default: "oklch(55% 0.16 25)", subtle: "oklch(95% 0.03 25)" },
    dark: { default: "oklch(65% 0.15 25)", subtle: "oklch(25% 0.04 25)" },
  },
  info: {
    light: { default: "oklch(55% 0.12 240)", subtle: "oklch(95% 0.03 240)" },
    dark: { default: "oklch(70% 0.10 240)", subtle: "oklch(25% 0.03 240)" },
  },
} as const;

// ─── Non-Color Tokens ────────────────────────────────────────────────────────

export const radius = {
  xs: "4px",
  sm: "6px",
  md: "10px",
  lg: "14px",
  xl: "18px",
  "2xl": "22px",
  full: "9999px",
} as const;

const shadows = {
  light: {
    sm: "0 1px 2px oklch(20% 0.01 270 / 4%)",
    md: "0 4px 12px oklch(20% 0.01 270 / 6%)",
    lg: "0 12px 32px oklch(20% 0.01 270 / 10%)",
    xl: "0 24px 60px oklch(20% 0.01 270 / 14%)",
  },
  dark: {
    sm: "0 1px 2px oklch(0% 0 0 / 16%)",
    md: "0 4px 12px oklch(0% 0 0 / 24%)",
    lg: "0 12px 32px oklch(0% 0 0 / 32%)",
    xl: "0 24px 60px oklch(0% 0 0 / 40%)",
  },
} as const;

export const transition = {
  fast: "120ms ease",
  normal: "200ms ease",
  slow: "320ms ease",
  spring: "500ms cubic-bezier(0.34, 1.56, 0.64, 1)",
} as const;

// ─── CSS Variable Maps ───────────────────────────────────────────────────────

function scaleVars(
  prefix: string,
  scale: Readonly<Record<string, string>>,
): Record<string, string> {
  const vars: Record<string, string> = {};
  for (const [step, value] of Object.entries(scale)) {
    vars[`--${prefix}-${step}`] = value;
  }
  return vars;
}

export function buildLightVariables(): Record<string, string> {
  return {
    // ── Color Scales ──
    ...scaleVars("primary", primary),
    ...scaleVars("secondary", secondary),
    ...scaleVars("neutral", neutralLight),

    // ── Brand (Primary Semantic) ──
    "--brand": primary[500],
    "--brand-hover": primary[400],
    "--brand-active": primary[600],
    "--brand-strong": primary[700],
    "--brand-tint": primary[100],
    "--brand-subtle": primary[50],

    // ── Accent (Secondary Semantic) ──
    "--accent": secondary[500],
    "--accent-hover": secondary[400],
    "--accent-active": secondary[600],
    "--accent-subtle": secondary[100],

    // ── Semantic ──
    "--color-success": semantic.success.light.default,
    "--color-success-subtle": semantic.success.light.subtle,
    "--color-warning": semantic.warning.light.default,
    "--color-warning-subtle": semantic.warning.light.subtle,
    "--color-error": semantic.error.light.default,
    "--color-error-subtle": semantic.error.light.subtle,
    "--color-info": semantic.info.light.default,
    "--color-info-subtle": semantic.info.light.subtle,

    // ── Surface ──
    "--color-bg-dark": "oklch(11% 0.012 270)",
    "--color-bg-secondary": neutralLight[200],
    "--page-bg": neutralLight[100],
    "--panel-bg": "rgb(255 255 255)",
    "--panel-border": neutralLight[300],
    "--panel-shadow": shadows.light.md,

    // ── Content ──
    "--text-strong": neutralLight[800],
    "--text-body": neutralLight[600],
    "--text-soft": neutralLight[400],
    "--text-disabled": neutralLight[300],

    // ── Boundary ──
    "--border-default": neutralLight[300],
    "--border-strong": neutralLight[400],
    "--border-focus": primary[500],

    // ── Tag ──
    "--tag-bg": neutralLight[200],
    "--tag-active-bg": "rgb(255 255 255 / 95%)",

    // ── Top Nav ──
    "--top-nav-bg": "rgb(255 255 255 / 85%)",
    "--top-nav-border": neutralLight[300],
    "--top-nav-item-hover": primary[50],
    "--top-nav-item-active": `linear-gradient(135deg, oklch(92% 0.03 270) 0%, oklch(85% 0.05 270) 100%)`,

    // ── Drawer ──
    "--drawer-surface": `linear-gradient(180deg, ${neutralLight[50]} 0%, ${neutralLight[100]} 100%)`,

    // ── Radius ──
    "--radius-xs": radius.xs,
    "--radius-sm": radius.sm,
    "--radius-md": radius.md,
    "--radius-lg": radius.lg,
    "--radius-xl": radius.xl,
    "--radius-2xl": radius["2xl"],
    "--radius-full": radius.full,

    // ── Shadow ──
    "--shadow-sm": shadows.light.sm,
    "--shadow-md": shadows.light.md,
    "--shadow-lg": shadows.light.lg,
    "--shadow-xl": shadows.light.xl,

    // ── Transition ──
    "--transition-fast": transition.fast,
    "--transition-normal": transition.normal,
    "--transition-slow": transition.slow,
    "--transition-spring": transition.spring,
  };
}

export function buildDarkVariables(): Record<string, string> {
  return {
    // ── Color Scales ──
    ...scaleVars("primary", primary),
    ...scaleVars("secondary", secondary),
    ...scaleVars("neutral", neutralDark),

    // ── Brand (Primary Semantic) ──
    "--brand": primary[400],
    "--brand-hover": primary[300],
    "--brand-active": primary[500],
    "--brand-strong": primary[500],
    "--brand-tint": "oklch(28% 0.03 270)",
    "--brand-subtle": "oklch(22% 0.02 270)",

    // ── Accent (Secondary Semantic) ──
    "--accent": secondary[400],
    "--accent-hover": secondary[300],
    "--accent-active": secondary[500],
    "--accent-subtle": "oklch(22% 0.02 185)",

    // ── Semantic ──
    "--color-success": semantic.success.dark.default,
    "--color-success-subtle": semantic.success.dark.subtle,
    "--color-warning": semantic.warning.dark.default,
    "--color-warning-subtle": semantic.warning.dark.subtle,
    "--color-error": semantic.error.dark.default,
    "--color-error-subtle": semantic.error.dark.subtle,
    "--color-info": semantic.info.dark.default,
    "--color-info-subtle": semantic.info.dark.subtle,

    // ── Surface ──
    "--color-bg-dark": "oklch(11% 0.012 270)",
    "--color-bg-secondary": neutralDark[100],
    "--page-bg": neutralDark[50],
    "--panel-bg": `oklch(19% 0.014 270 / 92%)`,
    "--panel-border": "oklch(28% 0.015 270)",
    "--panel-shadow": shadows.dark.lg,

    // ── Content ──
    "--text-strong": neutralDark[900],
    "--text-body": neutralDark[700],
    "--text-soft": neutralDark[500],
    "--text-disabled": neutralDark[400],

    // ── Boundary ──
    "--border-default": "oklch(28% 0.015 270)",
    "--border-strong": "oklch(35% 0.013 270)",
    "--border-focus": primary[400],

    // ── Tag ──
    "--tag-bg": "oklch(22% 0.012 270)",
    "--tag-active-bg": "oklch(20% 0.014 270 / 92%)",

    // ── Top Nav ──
    "--top-nav-bg": "oklch(18% 0.014 270 / 88%)",
    "--top-nav-border": "oklch(28% 0.015 270)",
    "--top-nav-item-hover": "oklch(25% 0.02 270)",
    "--top-nav-item-active": `linear-gradient(135deg, oklch(30% 0.03 270) 0%, oklch(25% 0.04 270) 100%)`,

    // ── Drawer ──
    "--drawer-surface": `linear-gradient(180deg, ${neutralDark[100]} 0%, ${neutralDark[50]} 100%)`,

    // ── Radius (same in both themes) ──
    "--radius-xs": radius.xs,
    "--radius-sm": radius.sm,
    "--radius-md": radius.md,
    "--radius-lg": radius.lg,
    "--radius-xl": radius.xl,
    "--radius-2xl": radius["2xl"],
    "--radius-full": radius.full,

    // ── Shadow ──
    "--shadow-sm": shadows.dark.sm,
    "--shadow-md": shadows.dark.md,
    "--shadow-lg": shadows.dark.lg,
    "--shadow-xl": shadows.dark.xl,

    // ── Transition (same in both themes) ──
    "--transition-fast": transition.fast,
    "--transition-normal": transition.normal,
    "--transition-slow": transition.slow,
    "--transition-spring": transition.spring,
  };
}

// ─── Ant Design Hex Values ───────────────────────────────────────────────────
// Ant Design requires hex for colorPrimary; these match the OKLCH primary scale.

export const antdHex = {
  primaryLight: "#5E6AD2",
  primaryDark: "#8B93E6",
} as const;

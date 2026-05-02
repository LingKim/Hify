export type ThemeMode = "light" | "dark";
export type ThemePreference = "system" | ThemeMode;
export type NavigationMode = "side" | "top";
export type PreferenceControlType = "segmented";

export interface PreferenceOption<TValue extends string> {
  label: string;
  value: TValue;
  description: string;
}

export interface PreferenceItem<TValue extends string> {
  id: string;
  title: string;
  description: string;
  controlType: PreferenceControlType;
  defaultBehavior: string;
  options: PreferenceOption<TValue>[];
}

export interface PreferenceSection {
  id: string;
  title: string;
  items: PreferenceItem<string>[];
}

export const themePreferenceItem: PreferenceItem<ThemePreference> = {
  id: "themePreference",
  title: "主题模式",
  description: "控制系统配色。首次进入默认跟随操作系统主题。",
  controlType: "segmented",
  defaultBehavior: "默认跟随系统主题，手动切换后会记住选择。",
  options: [
    {
      label: "跟随系统",
      value: "system",
      description: "根据操作系统当前主题自动切换。",
    },
    {
      label: "普通主题",
      value: "light",
      description: "适合日间运营与内容查看。",
    },
    {
      label: "暗黑主题",
      value: "dark",
      description: "适合低光环境与长时间值守。",
    },
  ],
};

export const navigationModeItem: PreferenceItem<NavigationMode> = {
  id: "navigationMode",
  title: "菜单模式",
  description: "控制主导航出现在左侧还是顶部。",
  controlType: "segmented",
  defaultBehavior: "默认使用左侧菜单，切换后会记住选择。",
  options: [
    {
      label: "左侧菜单",
      value: "side",
      description: "适合信息密度较高的运营中台。",
    },
    {
      label: "顶部菜单",
      value: "top",
      description: "适合横向导航较强、页面标题更突出的布局。",
    },
  ],
};

export const preferencesSections: PreferenceSection[] = [
  {
    id: "appearance",
    title: "外观",
    items: [themePreferenceItem],
  },
  {
    id: "navigation",
    title: "导航",
    items: [navigationModeItem],
  },
];

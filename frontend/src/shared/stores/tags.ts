import { create } from "zustand";

export interface TabItem {
  key: string;
  title: string;
  closable: boolean;
}

interface TagsStoreState {
  tabs: TabItem[];
  activeKey: string;
  addTab: (tab: TabItem) => void;
  removeTab: (key: string) => string;
  setActiveKey: (key: string) => void;
}

const HOME_TAB: TabItem = { key: "/", title: "首页", closable: false };

export const useTagsStore = create<TagsStoreState>()((set, get) => ({
  tabs: [HOME_TAB],
  activeKey: HOME_TAB.key,

  addTab: (tab) => {
    const { tabs } = get();
    if (tabs.some((t) => t.key === tab.key)) {
      set({ activeKey: tab.key });
      return;
    }
    set({ tabs: [...tabs, tab], activeKey: tab.key });
  },

  removeTab: (key) => {
    const { tabs, activeKey } = get();
    if (!tabs.find((t) => t.key === key)?.closable) return activeKey;

    const index = tabs.findIndex((t) => t.key === key);
    const nextTabs = tabs.filter((t) => t.key !== key);

    let nextActiveKey = activeKey;
    if (activeKey === key) {
      const nextIndex = Math.min(index, nextTabs.length - 1);
      nextActiveKey = nextTabs[Math.max(0, nextIndex)]?.key ?? HOME_TAB.key;
    }

    set({ tabs: nextTabs, activeKey: nextActiveKey });
    return nextActiveKey;
  },

  setActiveKey: (key) => {
    set({ activeKey: key });
  },
}));

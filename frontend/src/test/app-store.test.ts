import { useAppStore } from "@/shared/stores/app";

describe("useAppStore", () => {
  beforeEach(() => {
    useAppStore.setState({
      siderCollapsed: false,
      isPreferencesDrawerOpen: false,
      themePreference: "system",
      resolvedThemeMode: "light",
      navigationMode: "side",
    });
  });

  it("toggles the sider collapsed state", () => {
    const initialState = useAppStore.getState();

    expect(initialState.siderCollapsed).toBe(false);

    initialState.toggleSiderCollapsed();
    expect(useAppStore.getState().siderCollapsed).toBe(true);

    useAppStore.getState().setSiderCollapsed(false);
    expect(useAppStore.getState().siderCollapsed).toBe(false);
  });

  it("opens and closes the preferences drawer", () => {
    useAppStore.getState().openPreferencesDrawer();
    expect(useAppStore.getState().isPreferencesDrawerOpen).toBe(true);

    useAppStore.getState().closePreferencesDrawer();
    expect(useAppStore.getState().isPreferencesDrawerOpen).toBe(false);
  });

  it("updates theme preference and navigation mode", () => {
    useAppStore.getState().setThemePreference("dark");
    useAppStore.getState().setNavigationMode("top");

    expect(useAppStore.getState().themePreference).toBe("dark");
    expect(useAppStore.getState().navigationMode).toBe("top");
  });
});

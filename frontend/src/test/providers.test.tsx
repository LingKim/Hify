import { render, waitFor } from "@testing-library/react";
import type { PropsWithChildren } from "react";
import { AppProviders } from "@/app/providers/AppProviders";
import { useAppStore } from "@/shared/stores/app";

function TestConsumer({ children }: PropsWithChildren): JSX.Element {
  return <AppProviders>{children}</AppProviders>;
}

describe("AppProviders", () => {
  beforeEach(() => {
    useAppStore.setState({
      themePreference: "light",
      resolvedThemeMode: "light",
      isPreferencesDrawerOpen: false,
      navigationMode: "side",
      siderCollapsed: false,
    });
  });

  it("applies the resolved theme to the document", async () => {
    render(
      <TestConsumer>
        <div>theme</div>
      </TestConsumer>,
    );

    await waitFor(() => {
      expect(document.documentElement.dataset.theme).toBe("light");
    });
  });
});

import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { AppProviders } from "@/app/providers/AppProviders";
import { AppRouter } from "@/app/router/AppRouter";
import { useAppStore } from "@/shared/stores/app";

describe("AppRouter", () => {
  beforeEach(() => {
    useAppStore.setState({
      siderCollapsed: false,
      isPreferencesDrawerOpen: false,
      themePreference: "system",
      resolvedThemeMode: "light",
      navigationMode: "side",
    });

    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          code: 200,
          message: "success",
          data: { status: "ok" },
        }),
        {
          status: 200,
          headers: { "Content-Type": "application/json" },
        },
      ),
    );
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders the home page on the root route", () => {
    render(
      <MemoryRouter
        initialEntries={["/"]}
        future={{
          v7_startTransition: true,
          v7_relativeSplatPath: true,
        }}
      >
        <AppProviders>
          <AppRouter />
        </AppProviders>
      </MemoryRouter>,
    );

    expect(screen.getByRole("heading", { name: "Hify 前端开发底座" })).toBeInTheDocument();
  });

  it("renders the api preview page on the playground route", () => {
    render(
      <MemoryRouter
        initialEntries={["/playground/api-preview"]}
        future={{
          v7_startTransition: true,
          v7_relativeSplatPath: true,
        }}
      >
        <AppProviders>
          <AppRouter />
        </AppProviders>
      </MemoryRouter>,
    );

    expect(screen.getByRole("heading", { name: "后端联调预览" })).toBeInTheDocument();
  });

  it("renders the common components page on the playground route", () => {
    render(
      <MemoryRouter
        initialEntries={["/playground/common-components"]}
        future={{
          v7_startTransition: true,
          v7_relativeSplatPath: true,
        }}
      >
        <AppProviders>
          <AppRouter />
        </AppProviders>
      </MemoryRouter>,
    );

    expect(screen.getByRole("heading", { name: "公共组件演示" })).toBeInTheDocument();
  });

  it("renders the not found page for an unknown route", () => {
    render(
      <MemoryRouter
        initialEntries={["/unknown-page"]}
        future={{
          v7_startTransition: true,
          v7_relativeSplatPath: true,
        }}
      >
        <AppProviders>
          <AppRouter />
        </AppProviders>
      </MemoryRouter>,
    );

    expect(screen.getByText("页面不存在")).toBeInTheDocument();
  });

  it("opens the preferences drawer from the header settings action", async () => {
    render(
      <MemoryRouter
        initialEntries={["/"]}
        future={{
          v7_startTransition: true,
          v7_relativeSplatPath: true,
        }}
      >
        <AppProviders>
          <AppRouter />
        </AppProviders>
      </MemoryRouter>,
    );

    fireEvent.click(screen.getByRole("button", { name: "打开界面设置" }));

    expect(screen.getByText("界面设置")).toBeInTheDocument();
    expect(screen.getByText("主题模式")).toBeInTheDocument();
    expect(screen.getByText("菜单模式")).toBeInTheDocument();
  });
});

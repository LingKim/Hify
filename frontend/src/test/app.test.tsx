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

    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const requestUrl = String(input);

      if (requestUrl.includes("/api/v1/llms/providers")) {
        return new Response(
          JSON.stringify({
            code: 200,
            message: "success",
            data: {
              list: [],
              total: 0,
              page: 1,
              pageSize: 10,
              totalPages: 0,
            },
          }),
          {
            status: 200,
            headers: { "Content-Type": "application/json" },
          },
        );
      }

      if (requestUrl.includes("/api/v1/agents")) {
        return new Response(
          JSON.stringify({
            code: 200,
            message: "success",
            data: {
              list: [],
              total: 0,
              page: 1,
              pageSize: 10,
              totalPages: 0,
            },
          }),
          {
            status: 200,
            headers: { "Content-Type": "application/json" },
          },
        );
      }

      return new Response(
        JSON.stringify({
          code: 200,
          message: "success",
          data: { status: "ok" },
        }),
        {
          status: 200,
          headers: { "Content-Type": "application/json" },
        },
      );
    });
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

  it("renders the provider management page on the providers route", async () => {
    render(
      <MemoryRouter
        initialEntries={["/providers"]}
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

    expect(
      await screen.findByRole("heading", { name: "模型提供商管理" }),
    ).toBeInTheDocument();
  });

  it("renders the agent configuration page on the agents route", async () => {
    render(
      <MemoryRouter
        initialEntries={["/agents"]}
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

    expect(
      await screen.findByRole("heading", { name: "Agent 配置" }),
    ).toBeInTheDocument();
    expect(screen.getByText("运营后台")).toBeInTheDocument();
    expect(screen.getAllByText("Agent 配置").length).toBeGreaterThan(0);
    expect(screen.queryByText("未知页面")).not.toBeInTheDocument();
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

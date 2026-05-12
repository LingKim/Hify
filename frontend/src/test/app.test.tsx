import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { AppProviders } from "@/app/providers/AppProviders";
import { AppRouter } from "@/app/router/AppRouter";
import { ACCESS_TOKEN_STORAGE_KEY } from "@/shared/auth/token";
import { useAppStore } from "@/shared/stores/app";

function renderApp(initialPath: string): void {
  render(
    <MemoryRouter
      initialEntries={[initialPath]}
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
}

function loginForTest(): void {
  window.localStorage.setItem(ACCESS_TOKEN_STORAGE_KEY, "test-token");
}

describe("AppRouter", () => {
  beforeEach(() => {
    window.localStorage.clear();
    useAppStore.setState({
      siderCollapsed: false,
      isPreferencesDrawerOpen: false,
      themePreference: "system",
      resolvedThemeMode: "light",
      navigationMode: "side",
    });

    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const requestUrl = String(input);

      if (requestUrl.includes("/api/v1/auth/me")) {
        return new Response(
          JSON.stringify({
            code: 200,
            message: "success",
            data: {
              id: 1,
              username: "member",
              email: "member@hify.ai",
              role: "member",
              roleLabel: "普通用户",
            },
          }),
          {
            status: 200,
            headers: { "Content-Type": "application/json" },
          },
        );
      }

      if (requestUrl.includes("/api/v1/auth/login")) {
        return new Response(
          JSON.stringify({
            code: 200,
            message: "success",
            data: {
              accessToken: "login-token",
              tokenType: "Bearer",
              expiresIn: 3600,
              user: {
                id: 1,
                username: "member",
                email: "member@hify.ai",
                role: "member",
                roleLabel: "普通用户",
              },
            },
          }),
          {
            status: 200,
            headers: { "Content-Type": "application/json" },
          },
        );
      }

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

      if (requestUrl.includes("/api/v1/users")) {
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
    window.localStorage.clear();
  });

  it("redirects unauthenticated users to the login page", async () => {
    renderApp("/users");

    expect(
      await screen.findByRole("heading", { name: "登录 Hify" }),
    ).toBeInTheDocument();
  });

  it("logs in and returns to the requested page", async () => {
    renderApp("/users");

    fireEvent.change(await screen.findByPlaceholderText("用户名或邮箱"), {
      target: { value: "member" },
    });
    fireEvent.change(screen.getByPlaceholderText("登录密码"), {
      target: { value: "Member123!" },
    });
    fireEvent.click(screen.getByRole("button", { name: /登\s*录/ }));

    expect(
      await screen.findByRole("heading", { name: "用户管理" }),
    ).toBeInTheDocument();
    expect(window.localStorage.getItem(ACCESS_TOKEN_STORAGE_KEY)).toBe(
      "login-token",
    );
  });

  it("renders the home page on the root route", async () => {
    loginForTest();
    renderApp("/");

    expect(
      await screen.findByRole("heading", { name: "Hify 前端开发底座" }),
    ).toBeInTheDocument();
  });

  it("renders the api preview page on the playground route", async () => {
    loginForTest();
    renderApp("/playground/api-preview");

    expect(
      await screen.findByRole("heading", { name: "后端联调预览" }),
    ).toBeInTheDocument();
  });

  it("renders the provider management page on the providers route", async () => {
    loginForTest();
    renderApp("/providers");

    expect(
      await screen.findByRole("heading", { name: "模型提供商管理" }),
    ).toBeInTheDocument();
  });

  it("renders the agent configuration page on the agents route", async () => {
    loginForTest();
    renderApp("/agents");

    expect(
      await screen.findByRole("heading", { name: "Agent 配置" }),
    ).toBeInTheDocument();
    expect(screen.getByText("运营后台")).toBeInTheDocument();
    expect(screen.getAllByText("Agent 配置").length).toBeGreaterThan(0);
    expect(screen.queryByText("未知页面")).not.toBeInTheDocument();
  });

  it("renders the user management page on the users route", async () => {
    loginForTest();
    renderApp("/users");

    expect(
      await screen.findByRole("heading", { name: "用户管理" }),
    ).toBeInTheDocument();
  });

  it("renders the common components page on the playground route", async () => {
    loginForTest();
    renderApp("/playground/common-components");

    expect(
      await screen.findByRole("heading", { name: "公共组件演示" }),
    ).toBeInTheDocument();
  });

  it("renders the not found page for an unknown route", async () => {
    loginForTest();
    renderApp("/unknown-page");

    expect(await screen.findByText("页面不存在")).toBeInTheDocument();
  });

  it("opens the preferences drawer from the header settings action", async () => {
    loginForTest();
    renderApp("/");

    fireEvent.click(
      await screen.findByRole("button", { name: "打开界面设置" }),
    );

    expect(screen.getByText("界面设置")).toBeInTheDocument();
    expect(screen.getByText("主题模式")).toBeInTheDocument();
    expect(screen.getByText("菜单模式")).toBeInTheDocument();
  });
});

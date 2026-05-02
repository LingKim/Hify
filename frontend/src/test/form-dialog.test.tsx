import { App as AntdApp, ConfigProvider } from "antd";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { PropsWithChildren } from "react";
import { FormDialog } from "@/shared/ui";

interface DemoValues {
  name?: string;
  status?: "enabled" | "disabled";
  remark?: string;
}

interface DemoDetail {
  name: string;
  status: "enabled" | "disabled";
}

function createWrapper() {
  const client = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
      mutations: {
        retry: false,
      },
    },
  });

  return function Wrapper({ children }: PropsWithChildren): JSX.Element {
    return (
      <QueryClientProvider client={client}>
        <ConfigProvider>
          <AntdApp>{children}</AntdApp>
        </ConfigProvider>
      </QueryClientProvider>
    );
  };
}

describe("FormDialog", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders schema fields with 24-grid layout defaults and supports fullscreen toggling", async () => {
    render(
      <FormDialog<DemoValues>
        open
        mode="create"
        title="新建任务"
        schema={[
          {
            type: "input",
            key: "name",
            label: "名称",
          },
          {
            type: "textarea",
            key: "remark",
            label: "备注",
            colProps: { xs: 24, md: 24 },
          },
          {
            type: "custom",
            key: "status",
            label: "状态",
            render: ({ value, onChange }) => (
              <select
                aria-label="状态"
                value={(value as string | undefined) ?? ""}
                onChange={(event) => onChange(event.target.value)}
              >
                <option value="">请选择</option>
                <option value="enabled">启用</option>
                <option value="disabled">停用</option>
              </select>
            ),
          },
          {
            type: "input",
            key: "hiddenField",
            label: "隐藏字段",
            hidden: true,
          },
        ]}
        primaryAction={{
          text: "保存",
          api: vi.fn(async () => ({ ok: true })),
        }}
      />,
      { wrapper: createWrapper() },
    );

    expect(screen.getByLabelText("名称")).toBeInTheDocument();
    expect(screen.getByLabelText("状态")).toBeInTheDocument();
    expect(screen.queryByText("隐藏字段")).not.toBeInTheDocument();

    expect(screen.getByTestId("form-dialog-col-name").className).toContain("ant-col-md-12");
    expect(screen.getByTestId("form-dialog-col-remark").className).toContain("ant-col-md-24");

    fireEvent.click(screen.getByRole("button", { name: "放大全屏" }));

    await waitFor(() => {
      expect(document.querySelector(".form-dialog-modal-fullscreen")).not.toBeNull();
    });

    fireEvent.click(screen.getByRole("button", { name: "退出全屏" }));

    await waitFor(() => {
      expect(document.querySelector(".form-dialog-modal-fullscreen")).toBeNull();
    });
  });

  it("clears create-mode draft values after closing and reopening", async () => {
    const { rerender } = render(
      <FormDialog<DemoValues>
        open
        mode="create"
        title="新建任务"
        schema={[
          {
            type: "input",
            key: "name",
            label: "名称",
          },
        ]}
        primaryAction={{
          text: "保存",
          api: vi.fn(async () => ({ ok: true })),
        }}
      />,
      { wrapper: createWrapper() },
    );

    fireEvent.change(screen.getByLabelText("名称"), {
      target: { value: "临时内容" },
    });

    expect(screen.getByDisplayValue("临时内容")).toBeInTheDocument();

    rerender(
      <FormDialog<DemoValues>
        open={false}
        mode="create"
        title="新建任务"
        schema={[
          {
            type: "input",
            key: "name",
            label: "名称",
          },
        ]}
        primaryAction={{
          text: "保存",
          api: vi.fn(async () => ({ ok: true })),
        }}
      />,
    );

    rerender(
      <FormDialog<DemoValues>
        open
        mode="create"
        title="新建任务"
        schema={[
          {
            type: "input",
            key: "name",
            label: "名称",
          },
        ]}
        primaryAction={{
          text: "保存",
          api: vi.fn(async () => ({ ok: true })),
        }}
      />,
    );

    await waitFor(() => {
      expect((screen.getByLabelText("名称") as HTMLInputElement).value).toBe("");
    });
  });

  it("prefills edit values and lets detailApi override initial values", async () => {
    const detailApi = vi.fn(
      async (_id: string | number) =>
        ({
          name: "远端任务",
          status: "enabled",
        }) satisfies DemoDetail,
    );

    render(
      <FormDialog<DemoValues, DemoDetail>
        open
        mode="edit"
        editId={7}
        title="编辑任务"
        initialValues={{ name: "本地预填" }}
        detailQueryKey={(id) => ["task-detail", id]}
        detailApi={detailApi}
        mapDetailToValues={(detail) => ({
          name: detail.name,
          status: detail.status,
        })}
        schema={[
          {
            type: "input",
            key: "name",
            label: "名称",
          },
          {
            type: "select",
            key: "status",
            label: "状态",
            options: [
              { label: "启用", value: "enabled" },
              { label: "停用", value: "disabled" },
            ],
          },
        ]}
        primaryAction={{
          text: "保存",
          api: vi.fn(async () => ({ ok: true })),
        }}
      />,
      { wrapper: createWrapper() },
    );

    expect(screen.getByDisplayValue("本地预填")).toBeInTheDocument();

    await waitFor(() => {
      expect(detailApi).toHaveBeenCalledWith(7, expect.any(AbortSignal));
    });

    expect(await screen.findByDisplayValue("远端任务")).toBeInTheDocument();
  });

  it("submits the primary action and notifies parent callbacks", async () => {
    const submitApi = vi.fn(async (values: DemoValues) => ({
      id: 100,
      ...values,
    }));
    const onOpenChange = vi.fn();
    const onSuccess = vi.fn();

    render(
      <FormDialog<DemoValues>
        open
        mode="create"
        title="新建任务"
        onOpenChange={onOpenChange}
        onSuccess={onSuccess}
        schema={[
          {
            type: "input",
            key: "name",
            label: "名称",
            required: true,
          },
        ]}
        primaryAction={{
          text: "保存",
          api: submitApi,
          successMessage: "保存成功",
        }}
      />,
      { wrapper: createWrapper() },
    );

    fireEvent.change(screen.getByLabelText("名称"), {
      target: { value: "创建任务" },
    });
    fireEvent.click(screen.getByRole("button", { name: /保\s*存/ }));

    await waitFor(() => {
      expect(submitApi).toHaveBeenCalledWith(
        { name: "创建任务" },
        expect.objectContaining({ mode: "create", editId: undefined }),
        expect.any(AbortSignal),
      );
    });

    await waitFor(() => {
      expect(onSuccess).toHaveBeenCalledWith(
        expect.objectContaining({ id: 100, name: "创建任务" }),
        expect.objectContaining({ mode: "create", editId: undefined }),
      );
      expect(onOpenChange).toHaveBeenCalledWith(false);
    });
  });

  it("supports an independent secondary action without auto-closing", async () => {
    const secondaryApi = vi.fn(async (values: DemoValues) => ({
      draft: true,
      ...values,
    }));
    const onOpenChange = vi.fn();

    render(
      <FormDialog<DemoValues>
        open
        mode="edit"
        editId={1}
        title="编辑任务"
        initialValues={{ name: "原始任务" }}
        schema={[
          {
            type: "input",
            key: "name",
            label: "名称",
          },
        ]}
        primaryAction={{
          text: "保存",
          api: vi.fn(async () => ({ ok: true })),
        }}
        secondaryAction={{
          text: "保存草稿",
          api: secondaryApi,
          closeOnSuccess: false,
        }}
      />,
      { wrapper: createWrapper() },
    );

    fireEvent.change(screen.getByLabelText("名称"), {
      target: { value: "草稿内容" },
    });
    fireEvent.click(screen.getByRole("button", { name: /保\s*存\s*草\s*稿/ }));

    await waitFor(() => {
      expect(secondaryApi).toHaveBeenCalledWith(
        { name: "草稿内容" },
        expect.objectContaining({ mode: "edit", editId: 1 }),
        expect.any(AbortSignal),
      );
    });

    expect(onOpenChange).not.toHaveBeenCalled();
  });
});

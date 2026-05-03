import { App as AntdApp, ConfigProvider } from "antd";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { createRef, type PropsWithChildren } from "react";
import { ListTable, type ListTableRef } from "@/shared/ui";
import type { ListRequestParams, PageResult } from "@/shared/types/list";

interface DemoRecord {
  id: number;
  name: string;
  status: "enabled" | "disabled";
}

interface DemoQuery {
  keyword?: string;
  status?: "enabled" | "disabled";
  createdAtStart?: string;
  createdAtEnd?: string;
}

function createWrapper() {
  const client = new QueryClient({
    defaultOptions: {
      queries: {
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

function createPageResult(
  items: DemoRecord[],
  page = 1,
  total = items.length,
  pageSize = 10,
): PageResult<DemoRecord> {
  return {
    list: items,
    total,
    page,
    pageSize,
    totalPages: Math.ceil(total / pageSize),
  };
}

describe("ListTable", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("requests the first page on mount and renders returned rows", async () => {
    const api = vi.fn(async (_params: ListRequestParams<DemoQuery>) =>
      createPageResult([{ id: 1, name: "Alpha", status: "enabled" }]),
    );

    render(
      <ListTable<DemoRecord, DemoQuery>
        rowKey="id"
        columns={[
          { title: "名称", dataIndex: "name" },
          { title: "状态", dataIndex: "status" },
        ]}
        queryKey={(params) => ["demo-list", params]}
        api={api}
      />,
      { wrapper: createWrapper() },
    );

    await waitFor(() => {
      expect(api).toHaveBeenCalledWith({ page: 1, pageSize: 10 }, expect.any(AbortSignal));
    });

    expect(await screen.findByText("Alpha")).toBeInTheDocument();
  });

  it("enables horizontal scrolling by default for wide tables", async () => {
    const api = vi.fn(async (_params: ListRequestParams<DemoQuery>) =>
      createPageResult([{ id: 1, name: "Alpha", status: "enabled" }]),
    );

    const { container } = render(
      <ListTable<DemoRecord, DemoQuery>
        rowKey="id"
        columns={[
          { title: "名称", dataIndex: "name" },
          { title: "状态", dataIndex: "status" },
        ]}
        queryKey={(params) => ["demo-list", params]}
        api={api}
      />,
      { wrapper: createWrapper() },
    );

    expect(await screen.findByText("Alpha")).toBeInTheDocument();

    const scrollContent = container.querySelector(".ant-table-content");
    expect(scrollContent).not.toBeNull();
    expect(scrollContent).toHaveStyle({ overflowX: "auto" });
  });

  it("submits filters, resets to defaults, and clears row selection after a new query", async () => {
    const api = vi.fn(async (params: ListRequestParams<DemoQuery>) =>
      createPageResult([
        {
          id: 1,
          name: params.keyword === "Beta" ? "Beta" : "Alpha",
          status: "enabled",
        },
      ]),
    );

    render(
      <ListTable<DemoRecord, DemoQuery>
        rowKey="id"
        selectable
        columns={[{ title: "名称", dataIndex: "name" }]}
        filterSchema={[
          {
            type: "input",
            key: "keyword",
            label: "关键词",
            placeholder: "请输入关键词",
          },
        ]}
        batchActions={({ selectedRows }) => <span>批量处理 {selectedRows.length}</span>}
        queryKey={(params) => ["demo-list", params]}
        api={api}
      />,
      { wrapper: createWrapper() },
    );

    expect(await screen.findByText("Alpha")).toBeInTheDocument();

    fireEvent.click(screen.getAllByRole("checkbox")[1]);
    expect(await screen.findByText("批量处理 1")).toBeInTheDocument();

    fireEvent.change(screen.getByPlaceholderText("请输入关键词"), {
      target: { value: "Beta" },
    });
    fireEvent.click(screen.getByRole("button", { name: /查\s*询/ }));

    await waitFor(() => {
      expect(api).toHaveBeenLastCalledWith(
        { keyword: "Beta", page: 1, pageSize: 10 },
        expect.any(AbortSignal),
      );
    });

    expect(await screen.findByText("Beta")).toBeInTheDocument();
    expect(screen.queryByText("批量处理 1")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /重\s*置/ }));

    await waitFor(() => {
      expect(api).toHaveBeenLastCalledWith({ page: 1, pageSize: 10 }, expect.any(AbortSignal));
    });
  });

  it("supports date range mapping and exposes reload through refetch", async () => {
    const api = vi.fn(async (_params: ListRequestParams<DemoQuery>) =>
      createPageResult([{ id: 1, name: "Alpha", status: "enabled" }]),
    );
    const ref = createRef<ListTableRef<DemoRecord>>();

    render(
      <>
        <button type="button" onClick={() => ref.current?.reload()}>
          手动刷新
        </button>
        <ListTable<DemoRecord, DemoQuery>
          ref={ref}
          rowKey="id"
          columns={[{ title: "名称", dataIndex: "name" }]}
          filterSchema={[
            {
              type: "dateRange",
              key: "createdAt",
              label: "创建时间",
              queryKeys: ["createdAtStart", "createdAtEnd"],
            },
          ]}
          queryKey={(params) => ["demo-list", params]}
          api={api}
          initialQuery={{
            createdAtStart: "2026-05-01",
            createdAtEnd: "2026-05-02",
          }}
        />
      </>,
      { wrapper: createWrapper() },
    );

    await waitFor(() => {
      expect(api).toHaveBeenCalledWith(
        {
          createdAtStart: "2026-05-01",
          createdAtEnd: "2026-05-02",
          page: 1,
          pageSize: 10,
        },
        expect.any(AbortSignal),
      );
    });

    fireEvent.click(screen.getByRole("button", { name: "手动刷新" }));

    await waitFor(() => {
      expect(api).toHaveBeenCalledTimes(2);
    });
  });

  it("keeps previous rows visible while a pagination request is fetching", async () => {
    let resolveNextPage: ((value: PageResult<DemoRecord>) => void) | undefined;
    const api = vi.fn((params: ListRequestParams<DemoQuery>) => {
      if (params.page === 2) {
        return new Promise<PageResult<DemoRecord>>((resolve) => {
          resolveNextPage = resolve;
        });
      }

      return Promise.resolve(
        createPageResult([{ id: 1, name: "Alpha", status: "enabled" }], 1, 2, 1),
      );
    });

    const { container } = render(
      <ListTable<DemoRecord, DemoQuery>
        rowKey="id"
        initialPageSize={1}
        columns={[{ title: "名称", dataIndex: "name" }]}
        queryKey={(params) => ["demo-list", params]}
        api={api}
      />,
      { wrapper: createWrapper() },
    );

    expect(await screen.findByText("Alpha")).toBeInTheDocument();

    fireEvent.click(screen.getByText("2"));

    expect(screen.getByText("Alpha")).toBeInTheDocument();

    resolveNextPage?.(
      {
        list: [{ id: 2, name: "Beta", status: "disabled" }],
        total: 2,
        page: 2,
        pageSize: 1,
        totalPages: 2,
      },
    );

    expect(await screen.findByText("Beta")).toBeInTheDocument();
    expect(within(container).getByText("Beta")).toBeInTheDocument();
  });

  it("can hide pagination while still loading rows", async () => {
    const api = vi.fn(async (_params: ListRequestParams<DemoQuery>) =>
      createPageResult([{ id: 1, name: "Alpha", status: "enabled" }]),
    );

    const { container } = render(
      <ListTable<DemoRecord, DemoQuery>
        rowKey="id"
        showPagination={false}
        columns={[{ title: "名称", dataIndex: "name" }]}
        queryKey={(params) => ["demo-list", params]}
        api={api}
      />,
      { wrapper: createWrapper() },
    );

    expect(await screen.findByText("Alpha")).toBeInTheDocument();
    expect(container.querySelector(".ant-pagination")).toBeNull();
  });
});

import {
  forwardRef,
  startTransition,
  useImperativeHandle,
  useRef,
  useState,
  type Key,
  type ReactNode,
} from "react";
import { keepPreviousData, useQuery, type QueryKey } from "@tanstack/react-query";
import {
  Alert,
  Button,
  Form,
  Input,
  Pagination,
  Select,
  Space,
  Table,
  Typography,
} from "antd";
import type { ColumnType, ColumnsType } from "antd/es/table";
import type { TableProps } from "antd";
import { getErrorMessage } from "@/shared/api";
import type {
  BatchActionContext,
  ListFilterField,
  ListRequestParams,
  ListTableColumn,
  ListTableRef,
  PageResult,
} from "@/shared/types/list";

export interface ListTableProps<TData, TQuery extends object> {
  columns: ListTableColumn<TData>[];
  filterSchema?: ListFilterField[];
  queryKey: (params: ListRequestParams<TQuery>) => QueryKey;
  api: (params: ListRequestParams<TQuery>, signal?: AbortSignal) => Promise<PageResult<TData>>;
  showPagination?: boolean;
  initialQuery?: Partial<TQuery>;
  initialPageSize?: number;
  rowKey: keyof TData | ((record: TData) => React.Key);
  selectable?: boolean;
  batchActions?: (context: BatchActionContext<TData>) => ReactNode;
  tableActions?: (record: TData, index: number) => ReactNode;
  toolbar?: ReactNode;
  emptyText?: ReactNode;
  enabled?: boolean;
  scroll?: TableProps<TData>['scroll'];
}

type DraftQueryValues = Record<string, unknown>;

type TableSelection<TData> = NonNullable<TableProps<TData>["rowSelection"]>;

function normalizeInputQuery<TQuery extends object>(
  initialQuery: Partial<TQuery> | undefined,
): Record<string, unknown> {
  if (initialQuery === undefined) {
    return {};
  }

  return Object.fromEntries(
    Object.entries(initialQuery as Record<string, unknown>).filter(([, value]) => value !== undefined),
  );
}

function createDraftQueryValues<TQuery extends object>(
  filterSchema: ListFilterField[] | undefined,
  initialQuery: Partial<TQuery> | undefined,
): DraftQueryValues {
  const queryValues = normalizeInputQuery(initialQuery);

  if (filterSchema === undefined) {
    return queryValues;
  }

  return filterSchema.reduce<DraftQueryValues>((draft, field) => {
    if (field.type === "dateRange") {
      draft[field.key] = [
        (queryValues[field.queryKeys[0]] as string | undefined) ?? "",
        (queryValues[field.queryKeys[1]] as string | undefined) ?? "",
      ];
      return draft;
    }

    draft[field.key] = queryValues[field.key];
    return draft;
  }, {});
}

function buildSubmittedQueryValues(
  filterSchema: ListFilterField[] | undefined,
  draftQueryValues: DraftQueryValues,
): Record<string, unknown> {
  if (filterSchema === undefined) {
    return { ...draftQueryValues };
  }

  const nextQueryValues: Record<string, unknown> = {};

  filterSchema.forEach((field) => {
    const currentValue = draftQueryValues[field.key];

    if (field.type === "dateRange") {
      const [startValue = "", endValue = ""] = Array.isArray(currentValue)
        ? (currentValue as string[])
        : [];

      if (startValue !== "") {
        nextQueryValues[field.queryKeys[0]] = startValue;
      }

      if (endValue !== "") {
        nextQueryValues[field.queryKeys[1]] = endValue;
      }

      return;
    }

    if (
      currentValue === undefined ||
      currentValue === null ||
      currentValue === "" ||
      (Array.isArray(currentValue) && currentValue.length === 0)
    ) {
      return;
    }

    nextQueryValues[field.key] = currentValue;
  });

  return nextQueryValues;
}

function isSameQueryValue(left: unknown, right: unknown): boolean {
  if (Array.isArray(left) && Array.isArray(right)) {
    return (
      left.length === right.length &&
      left.every((value, index) => isSameQueryValue(value, right[index]))
    );
  }

  return left === right;
}

function isSameQueryValues(
  left: Record<string, unknown>,
  right: Record<string, unknown>,
): boolean {
  const leftKeys = Object.keys(left);
  const rightKeys = Object.keys(right);

  if (leftKeys.length !== rightKeys.length) {
    return false;
  }

  return leftKeys.every((key) => isSameQueryValue(left[key], right[key]));
}

function clearableSelectionState<TData>() {
  return {
    selectedRowKeys: [] as Key[],
    selectedRows: [] as TData[],
  };
}

function InnerListTable<TData, TQuery extends object>(
  {
    columns,
    filterSchema,
    queryKey,
    api,
    showPagination = true,
    initialQuery,
    initialPageSize = 10,
    rowKey,
    selectable = false,
    batchActions,
    tableActions,
    toolbar,
    emptyText,
    enabled = true,
    scroll,
  }: ListTableProps<TData, TQuery>,
  ref: React.ForwardedRef<ListTableRef<TData>>,
): JSX.Element {
  const initialSubmittedQueryValuesRef = useRef(normalizeInputQuery(initialQuery));
  const initialDraftQueryValuesRef = useRef(createDraftQueryValues(filterSchema, initialQuery));
  const [draftQueryValues, setDraftQueryValues] = useState<DraftQueryValues>(
    initialDraftQueryValuesRef.current,
  );
  const [submittedQueryValues, setSubmittedQueryValues] = useState<Record<string, unknown>>(
    initialSubmittedQueryValuesRef.current,
  );
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(initialPageSize);
  const [selectionState, setSelectionState] = useState(clearableSelectionState<TData>());
  const effectiveScroll =
    scroll === undefined
      ? { x: "max-content" }
      : scroll.x === undefined
        ? { ...scroll, x: "max-content" }
        : scroll;

  const effectivePage = showPagination ? page : 1;
  const requestParams = {
    ...(submittedQueryValues as TQuery),
    page: effectivePage,
    pageSize,
  } as ListRequestParams<TQuery>;

  const query = useQuery({
    queryKey: queryKey(requestParams),
    queryFn: ({ signal }) => api(requestParams, signal),
    enabled,
    placeholderData: keepPreviousData,
  });

  const clearSelection = () => {
    setSelectionState(clearableSelectionState<TData>());
  };

  useImperativeHandle(ref, () => ({
    reload: () => {
      void query.refetch();
    },
    reset: () => {
      const nextDraftQueryValues = initialDraftQueryValuesRef.current;
      const nextSubmittedQueryValues = initialSubmittedQueryValuesRef.current;
      const isSameState =
        isSameQueryValues(draftQueryValues, nextDraftQueryValues) &&
        isSameQueryValues(submittedQueryValues, nextSubmittedQueryValues) &&
        page === 1 &&
        pageSize === initialPageSize;

      clearSelection();

      if (isSameState) {
        void query.refetch();
        return;
      }

      startTransition(() => {
        setDraftQueryValues(nextDraftQueryValues);
        setSubmittedQueryValues(nextSubmittedQueryValues);
        setPage(1);
        setPageSize(initialPageSize);
      });
    },
    clearSelection,
    getSelectedRows: () => selectionState.selectedRows,
  }));

  const handleDraftValueChange = (key: string, value: unknown) => {
    setDraftQueryValues((currentValues) => ({
      ...currentValues,
      [key]: value,
    }));
  };

  const handleSearch = () => {
    const nextSubmittedQueryValues = buildSubmittedQueryValues(filterSchema, draftQueryValues);
    const shouldRefetch = isSameQueryValues(submittedQueryValues, nextSubmittedQueryValues) && page === 1;

    clearSelection();

    if (shouldRefetch) {
      void query.refetch();
      return;
    }

    startTransition(() => {
      setSubmittedQueryValues(nextSubmittedQueryValues);
      setPage(1);
    });
  };

  const handleReset = () => {
    const nextDraftQueryValues = initialDraftQueryValuesRef.current;
    const nextSubmittedQueryValues = initialSubmittedQueryValuesRef.current;
    const isSameState =
      isSameQueryValues(draftQueryValues, nextDraftQueryValues) &&
      isSameQueryValues(submittedQueryValues, nextSubmittedQueryValues) &&
      page === 1 &&
      pageSize === initialPageSize;

    clearSelection();

    if (isSameState) {
      void query.refetch();
      return;
    }

    startTransition(() => {
      setDraftQueryValues(nextDraftQueryValues);
      setSubmittedQueryValues(nextSubmittedQueryValues);
      setPage(1);
      setPageSize(initialPageSize);
    });
  };

  const normalizedColumns: ColumnsType<TData> = columns.map((column) => {
    const normalizedColumn = {
      ...column,
      title: column.title ?? column.label,
      dataIndex: (column.dataIndex ?? column.prop) as ColumnType<TData>["dataIndex"],
      render:
        column.render ??
        (column.slot === undefined
          ? undefined
          : (_value: unknown, record: TData, index: number) => column.slot?.(record, index)),
    };

    return normalizedColumn;
  });

  if (tableActions !== undefined) {
    normalizedColumns.push({
      title: "操作",
      key: "__actions__",
      align: "right",
      fixed: "right",
      width: 140,
      render: (_value: unknown, record: TData, index: number) => {
        const content = tableActions(record, index);

        if (content === null || content === undefined || content === false) {
          return <Typography.Text type="secondary">-</Typography.Text>;
        }

        return <Space size={8} wrap>{content}</Space>;
      },
    });
  }

  const rowSelection: TableSelection<TData> | undefined = selectable
    ? {
        selectedRowKeys: selectionState.selectedRowKeys,
        onChange: (nextSelectedRowKeys: Key[], nextSelectedRows: TData[]) => {
          setSelectionState({
            selectedRowKeys: nextSelectedRowKeys,
            selectedRows: nextSelectedRows,
          });
        },
      }
    : undefined;

  return (
    <div className="list-table">
      {toolbar !== undefined ? <div className="list-table-toolbar">{toolbar}</div> : null}

      {filterSchema !== undefined && filterSchema.length > 0 ? (
        <div className="list-table-panel">
          <Form layout="vertical">
            <div className="list-table-form-grid">
              {filterSchema.map((field) => {
                if (field.type === "input") {
                  return (
                    <Form.Item key={field.key} label={field.label} className="list-table-form-item">
                      <Input
                        allowClear={field.allowClear ?? true}
                        placeholder={field.placeholder}
                        value={(draftQueryValues[field.key] as string | undefined) ?? ""}
                        onChange={(event) =>
                          handleDraftValueChange(field.key, event.target.value)
                        }
                      />
                    </Form.Item>
                  );
                }

                if (field.type === "select") {
                  return (
                    <Form.Item key={field.key} label={field.label} className="list-table-form-item">
                      <Select
                        allowClear={field.allowClear ?? true}
                        placeholder={field.placeholder}
                        options={field.options}
                        value={(draftQueryValues[field.key] as string | number | undefined) ?? undefined}
                        onChange={(value) => handleDraftValueChange(field.key, value)}
                      />
                    </Form.Item>
                  );
                }

                if (field.type === "dateRange") {
                  const [startValue = "", endValue = ""] = Array.isArray(draftQueryValues[field.key])
                    ? (draftQueryValues[field.key] as string[])
                    : [];

                  return (
                    <Form.Item key={field.key} label={field.label} className="list-table-form-item">
                      <div className="list-table-date-range">
                        <Input
                          type="date"
                          value={startValue}
                          onChange={(event) =>
                            handleDraftValueChange(field.key, [
                              event.target.value,
                              endValue,
                            ])
                          }
                        />
                        <span className="list-table-date-range-separator">至</span>
                        <Input
                          type="date"
                          value={endValue}
                          onChange={(event) =>
                            handleDraftValueChange(field.key, [
                              startValue,
                              event.target.value,
                            ])
                          }
                        />
                      </div>
                    </Form.Item>
                  );
                }

                return (
                  <Form.Item key={field.key} label={field.label} className="list-table-form-item">
                    {field.render({
                      value: draftQueryValues[field.key],
                      onChange: (value) => handleDraftValueChange(field.key, value),
                      formValues: draftQueryValues,
                    })}
                  </Form.Item>
                );
              })}
            </div>

            <div className="list-table-actions">
              <Button type="primary" onClick={() => handleSearch()}>
                查询
              </Button>
              <Button onClick={() => handleReset()}>重置</Button>
            </div>
          </Form>
        </div>
      ) : null}

      {selectionState.selectedRows.length > 0 && batchActions !== undefined ? (
        <div className="list-table-batch-bar">
          <Typography.Text>已选 {selectionState.selectedRows.length} 项</Typography.Text>
          <Space size={8} wrap>
            {batchActions({
              selectedRowKeys: selectionState.selectedRowKeys,
              selectedRows: selectionState.selectedRows,
              clearSelection,
            })}
          </Space>
        </div>
      ) : null}

      {query.isError ? (
        <Alert
          type="error"
          showIcon
          message="列表数据加载失败"
          description={getErrorMessage(query.error)}
          className="list-table-error"
        />
      ) : null}

      <div className="list-table-panel">
        <div className="list-table-table-wrap">
          <Table<TData>
            rowKey={rowKey}
            columns={normalizedColumns}
          dataSource={query.data?.list ?? []}
          rowSelection={rowSelection}
          loading={query.isLoading || query.isFetching}
          pagination={false}
          scroll={effectiveScroll}
          locale={{
            emptyText: emptyText ?? "暂无数据",
          }}
          />
        </div>

        {showPagination ? (
          <div className="list-table-pagination">
            <TablePagination
              current={query.data?.page ?? effectivePage}
              pageSize={query.data?.pageSize ?? pageSize}
              total={query.data?.total ?? 0}
              onChange={(nextPage, nextPageSize) => {
                clearSelection();
                startTransition(() => {
                  setPage(nextPage);
                  setPageSize(nextPageSize);
                });
              }}
            />
          </div>
        ) : null}
      </div>
    </div>
  );
}

interface TablePaginationProps {
  current: number;
  pageSize: number;
  total: number;
  onChange: (page: number, pageSize: number) => void;
}

function TablePagination({
  current,
  pageSize,
  total,
  onChange,
}: TablePaginationProps): JSX.Element {
  return (
    <Pagination
      current={current}
      pageSize={pageSize}
      total={total}
      showSizeChanger
      showQuickJumper={false}
      showTotal={(value) => `共 ${value} 条`}
      onChange={onChange}
    />
  );
}

export const ListTable = forwardRef(InnerListTable) as <
  TData,
  TQuery extends object,
>(
  props: ListTableProps<TData, TQuery> & {
    ref?: React.ForwardedRef<ListTableRef<TData>>;
  },
) => JSX.Element;

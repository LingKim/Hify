import { useRef, useState } from "react";
import { Button, Select, Space, Tag, Typography } from "antd";
import type { ListRequestParams, ListTableRef, PageResult } from "@/shared/types/list";
import { FormDialog, FrameView, ListTable } from "@/shared/ui";

type TaskStatus = "enabled" | "disabled";
type TaskPriority = "P0" | "P1" | "P2";

interface DemoRecord {
  id: number;
  name: string;
  status: TaskStatus;
  owner: string;
  createdAt: string;
  remark: string;
  priority: TaskPriority;
  notifyOwner: boolean;
}

interface DemoQuery {
  keyword?: string;
  status?: TaskStatus;
  owner?: string;
  createdAtStart?: string;
  createdAtEnd?: string;
}

interface DemoFormValues {
  name?: string;
  status?: TaskStatus;
  owner?: string;
  remark?: string;
  priority?: TaskPriority;
  notifyOwner?: boolean;
}

const statusOptions = [
  { label: "启用", value: "enabled" },
  { label: "停用", value: "disabled" },
] as const;

const ownerOptions = [
  { label: "王敏", value: "王敏" },
  { label: "陈森", value: "陈森" },
  { label: "刘畅", value: "刘畅" },
  { label: "周雨", value: "周雨" },
] as const;

const priorityOptions = [
  { label: "P0", value: "P0" },
  { label: "P1", value: "P1" },
  { label: "P2", value: "P2" },
] as const;

const initialDemoRecords: DemoRecord[] = [
  {
    id: 101,
    name: "会员中心改版",
    status: "enabled",
    owner: "王敏",
    createdAt: "2026-04-26",
    remark: "需要同步梳理权益文案和埋点。",
    priority: "P0",
    notifyOwner: true,
  },
  {
    id: 102,
    name: "订单风控校验",
    status: "enabled",
    owner: "陈森",
    createdAt: "2026-04-24",
    remark: "重点关注异常退款链路。",
    priority: "P1",
    notifyOwner: false,
  },
  {
    id: 103,
    name: "素材库标签治理",
    status: "disabled",
    owner: "刘畅",
    createdAt: "2026-04-21",
    remark: "后续可能拆成异步任务。",
    priority: "P2",
    notifyOwner: false,
  },
  {
    id: 104,
    name: "广告投放看板",
    status: "enabled",
    owner: "周雨",
    createdAt: "2026-04-19",
    remark: "先跑通核心指标，二期再补导出。",
    priority: "P1",
    notifyOwner: true,
  },
  {
    id: 105,
    name: "售后工单分配",
    status: "disabled",
    owner: "王敏",
    createdAt: "2026-04-16",
    remark: "当前主要验证指派策略。",
    priority: "P1",
    notifyOwner: true,
  },
  {
    id: 106,
    name: "直播预约提醒",
    status: "enabled",
    owner: "刘畅",
    createdAt: "2026-04-12",
    remark: "需要确认是否接短信服务。",
    priority: "P2",
    notifyOwner: false,
  },
];

async function waitForDemo(delayMs = 180, signal?: AbortSignal): Promise<void> {
  await new Promise<void>((resolve, reject) => {
    const timeoutId = window.setTimeout(() => {
      cleanup();
      resolve();
    }, delayMs);

    const handleAbort = () => {
      window.clearTimeout(timeoutId);
      cleanup();
      reject(new DOMException("The operation was aborted.", "AbortError"));
    };

    const cleanup = () => {
      signal?.removeEventListener("abort", handleAbort);
    };

    if (signal?.aborted === true) {
      handleAbort();
      return;
    }

    signal?.addEventListener("abort", handleAbort, { once: true });
  });
}

async function fetchDemoList(
  records: DemoRecord[],
  params: ListRequestParams<DemoQuery>,
  signal?: AbortSignal,
): Promise<PageResult<DemoRecord>> {
  await waitForDemo(220, signal);

  const { page, pageSize, keyword, status, owner, createdAtStart, createdAtEnd } = params;

  const filteredRecords = records.filter((record) => {
    const matchesKeyword =
      keyword === undefined ||
      keyword.trim() === "" ||
      record.name.toLowerCase().includes(keyword.trim().toLowerCase());
    const matchesStatus = status === undefined || record.status === status;
    const matchesOwner = owner === undefined || record.owner === owner;
    const matchesStart = createdAtStart === undefined || record.createdAt >= createdAtStart;
    const matchesEnd = createdAtEnd === undefined || record.createdAt <= createdAtEnd;

    return matchesKeyword && matchesStatus && matchesOwner && matchesStart && matchesEnd;
  });

  const startIndex = (page - 1) * pageSize;
  const list = filteredRecords.slice(startIndex, startIndex + pageSize);

  return {
    list,
    total: filteredRecords.length,
    page,
    pageSize,
    totalPages: Math.max(1, Math.ceil(filteredRecords.length / pageSize)),
  };
}

async function fetchDemoDetail(
  records: DemoRecord[],
  id: string | number,
  signal?: AbortSignal,
): Promise<DemoRecord> {
  await waitForDemo(160, signal);

  const record = records.find((item) => item.id === Number(id));

  if (record === undefined) {
    throw new Error("当前任务不存在或已被删除");
  }

  return record;
}

function createRecordFromValues(
  values: DemoFormValues,
  currentRecords: DemoRecord[],
  editId?: number,
): DemoRecord {
  const baseRecord =
    editId === undefined
      ? undefined
      : currentRecords.find((record) => record.id === editId);

  const nextId =
    editId ??
    currentRecords.reduce((maxId, record) => Math.max(maxId, record.id), 100) + 1;

  return {
    id: nextId,
    name: values.name?.trim() || "未命名任务",
    status: values.status ?? baseRecord?.status ?? "enabled",
    owner: values.owner ?? baseRecord?.owner ?? ownerOptions[0].value,
    createdAt: baseRecord?.createdAt ?? new Date().toISOString().slice(0, 10),
    remark: values.remark?.trim() || "",
    priority: values.priority ?? baseRecord?.priority ?? "P1",
    notifyOwner: values.notifyOwner ?? baseRecord?.notifyOwner ?? false,
  };
}

export function CommonComponentsPage(): JSX.Element {
  const listRef = useRef<ListTableRef<DemoRecord>>(null);
  const [records, setRecords] = useState(initialDemoRecords);
  const [listRevision, setListRevision] = useState(0);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [dialogMode, setDialogMode] = useState<"create" | "edit">("create");
  const [currentEditId, setCurrentEditId] = useState<number | undefined>(undefined);
  const [currentRecord, setCurrentRecord] = useState<DemoRecord | undefined>(undefined);

  const openCreateDialog = () => {
    setDialogMode("create");
    setCurrentEditId(undefined);
    setCurrentRecord(undefined);
    setDialogOpen(true);
  };

  const openEditDialog = (record: DemoRecord) => {
    setDialogMode("edit");
    setCurrentEditId(record.id);
    setCurrentRecord(record);
    setDialogOpen(true);
  };

  const closeDialog = () => {
    setDialogOpen(false);
    setCurrentEditId(undefined);
    setCurrentRecord(undefined);
  };

  return (
    <>
      <FrameView
        title="公共组件演示"
        description="这一页把 FrameView、ListTable 和 FormDialog 串起来，验证后台页面里最常见的筛选、列表、编辑弹窗三段式流程。"
        headerExtra={(
          <Space wrap>
            <Button type="primary" onClick={() => openCreateDialog()}>
              新建任务
            </Button>
            <Button onClick={() => listRef.current?.reload()}>刷新当前页</Button>
          </Space>
        )}
        alert={(
          <Typography.Text type="secondary">
            当前演示重点放在组件边界：列表请求走 React Query，弹窗提交成功后由页面自行刷新列表，而不是组件之间互相耦合。
          </Typography.Text>
        )}
        footer={(
          <Typography.Text type="secondary">
            FormDialog 默认支持全屏切换、编辑详情回填、创建后清空，以及 Ant Design 24 栅格布局。
          </Typography.Text>
        )}
      >
        <ListTable<DemoRecord, DemoQuery>
          ref={listRef}
          rowKey="id"
          columns={[
            {
              label: "任务名称",
              prop: "name",
              width: 240,
            },
            {
              label: "状态",
              prop: "status",
              width: 120,
              render: (_value, record) => (
                <Tag color={record.status === "enabled" ? "green" : "default"}>
                  {record.status === "enabled" ? "启用中" : "已停用"}
                </Tag>
              ),
            },
            {
              label: "负责人",
              prop: "owner",
              width: 120,
            },
            {
              label: "优先级",
              prop: "priority",
              width: 100,
              render: (_value, record) => (
                <Tag color={record.priority === "P0" ? "red" : record.priority === "P1" ? "gold" : "blue"}>
                  {record.priority}
                </Tag>
              ),
            },
            {
              label: "创建时间",
              prop: "createdAt",
              width: 140,
            },
          ]}
          filterSchema={[
            {
              type: "input",
              key: "keyword",
              label: "关键词",
              placeholder: "输入任务名称",
            },
            {
              type: "select",
              key: "status",
              label: "状态",
              placeholder: "全部状态",
              options: [...statusOptions],
            },
            {
              type: "custom",
              key: "owner",
              label: "负责人",
              render: ({ value, onChange }) => (
                <Select
                  allowClear
                  placeholder="选择负责人"
                  value={(value as string | undefined) ?? undefined}
                  options={[...ownerOptions]}
                  onChange={(nextValue) => onChange(nextValue)}
                />
              ),
            },
            {
              type: "dateRange",
              key: "createdAt",
              label: "创建时间",
              queryKeys: ["createdAtStart", "createdAtEnd"],
            },
          ]}
          selectable
          initialPageSize={3}
          queryKey={(params) => [
            "playground",
            "common-components",
            "list",
            listRevision,
            params,
          ]}
          api={(params, signal) => fetchDemoList(records, params, signal)}
          batchActions={({ selectedRows, clearSelection }) => (
            <>
              <Button
                size="small"
                onClick={() => {
                  const selectedIds = new Set(selectedRows.map((record) => record.id));
                  setRecords((currentRecords) =>
                    currentRecords.map((record) =>
                      selectedIds.has(record.id)
                        ? { ...record, status: "enabled" }
                        : record,
                    ),
                  );
                  setListRevision((currentValue) => currentValue + 1);
                  clearSelection();
                }}
              >
                批量启用
              </Button>
              <Button
                size="small"
                onClick={() => {
                  const selectedIds = new Set(selectedRows.map((record) => record.id));
                  setRecords((currentRecords) =>
                    currentRecords.map((record) =>
                      selectedIds.has(record.id)
                        ? { ...record, status: "disabled" }
                        : record,
                    ),
                  );
                  setListRevision((currentValue) => currentValue + 1);
                  clearSelection();
                }}
              >
                批量停用
              </Button>
              <Button size="small" onClick={() => clearSelection()}>
                清空选中
              </Button>
            </>
          )}
          tableActions={(record) => (
            <>
              <Button type="link" size="small" onClick={() => openEditDialog(record)}>
                编辑
              </Button>
              <Button
                type="link"
                size="small"
                onClick={() => {
                  setRecords((currentRecords) =>
                    currentRecords.map((item) =>
                      item.id === record.id
                        ? {
                            ...item,
                            status: item.status === "enabled" ? "disabled" : "enabled",
                          }
                        : item,
                    ),
                  );
                  setListRevision((currentValue) => currentValue + 1);
                }}
              >
                {record.status === "enabled" ? "停用" : "启用"}
              </Button>
            </>
          )}
          toolbar={(
            <Typography.Text type="secondary">
              这个表格演示了 schema 筛选、分页、勾选、批量操作，以及外部通过 FormDialog 驱动新增/编辑的典型接法。
            </Typography.Text>
          )}
        />
      </FrameView>

      <FormDialog<DemoFormValues, DemoRecord>
        open={dialogOpen}
        mode={dialogMode}
        editId={currentEditId}
        title={(mode) => (mode === "create" ? "新建任务" : "编辑任务")}
        width={820}
        onOpenChange={(nextOpen) => {
          if (nextOpen === false) {
            closeDialog();
          } else {
            setDialogOpen(true);
          }
        }}
        initialValues={
          dialogMode === "edit" && currentRecord !== undefined
            ? {
                name: currentRecord.name,
                status: currentRecord.status,
                owner: currentRecord.owner,
              }
            : undefined
        }
        detailQueryKey={(id) => ["playground", "common-components", "detail", id]}
        detailApi={(id, signal) => fetchDemoDetail(records, id, signal)}
        mapDetailToValues={(detail) => ({
          name: detail.name,
          status: detail.status,
          owner: detail.owner,
          remark: detail.remark,
          priority: detail.priority,
          notifyOwner: detail.notifyOwner,
        })}
        rowProps={{ gutter: [16, 0] }}
        defaultColProps={{ xs: 24, md: 12 }}
        schema={[
          {
            type: "input",
            key: "name",
            label: "任务名称",
            required: true,
            placeholder: "请输入任务名称",
          },
          {
            type: "select",
            key: "status",
            label: "任务状态",
            required: true,
            placeholder: "请选择状态",
            options: [...statusOptions],
          },
          {
            type: "select",
            key: "owner",
            label: "负责人",
            required: true,
            placeholder: "请选择负责人",
            options: [...ownerOptions],
          },
          {
            type: "select",
            key: "priority",
            label: "优先级",
            placeholder: "请选择优先级",
            options: [...priorityOptions],
            colProps: { xs: 24, md: 12, xl: 8 },
          },
          {
            type: "switch",
            key: "notifyOwner",
            label: "变更提醒",
            checkedChildren: "提醒",
            unCheckedChildren: "静默",
            colProps: { xs: 24, md: 12, xl: 8 },
          },
          {
            type: "textarea",
            key: "remark",
            label: "备注说明",
            rows: 4,
            placeholder: "输入业务补充说明",
            colProps: { xs: 24, md: 24 },
          },
        ]}
        primaryAction={{
          text: dialogMode === "create" ? "创建任务" : "保存修改",
          successMessage: dialogMode === "create" ? "任务创建成功" : "任务保存成功",
          api: async (values, context, signal) => {
            await waitForDemo(260, signal);

            return {
              submitType: "primary",
              mode: context.mode,
              editId: context.editId,
              values: values as DemoFormValues,
            };
          },
        }}
        secondaryAction={
          dialogMode === "create"
            ? {
                text: "保存并继续新增",
                closeOnSuccess: false,
                resetOnSuccess: true,
                successMessage: "已创建任务，表单已清空",
                api: async (values, context, signal) => {
                  await waitForDemo(260, signal);

                  return {
                    submitType: "secondary",
                    mode: context.mode,
                    editId: context.editId,
                    values: values as DemoFormValues,
                  };
                },
              }
            : undefined
        }
        onSuccess={async (result, context) => {
          const submitResult = result as {
            submitType: "primary" | "secondary";
            values: DemoFormValues;
          };

          setRecords((currentRecords) => {
            if (context.mode === "create") {
              const nextRecord = createRecordFromValues(submitResult.values, currentRecords);
              return [nextRecord, ...currentRecords];
            }

            if (context.editId === undefined) {
              return currentRecords;
            }

            const nextRecord = createRecordFromValues(
              submitResult.values,
              currentRecords,
              Number(context.editId),
            );

            return currentRecords.map((record) =>
              record.id === nextRecord.id ? nextRecord : record,
            );
          });

          setListRevision((currentValue) => currentValue + 1);
        }}
      />
    </>
  );
}

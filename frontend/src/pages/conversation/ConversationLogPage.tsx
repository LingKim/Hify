import {
  DeleteOutlined,
  EyeOutlined,
  MessageOutlined,
  RollbackOutlined,
} from "@ant-design/icons";
import {
  App,
  Button,
  Descriptions,
  Drawer,
  Space,
  Timeline,
  Tooltip,
  Typography,
} from "antd";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  ConversationStatusTag,
  conversationStatusOptions,
} from "@/domain/conversation/components";
import {
  conversationMessagesQueryOptions,
  conversationQueryKeys,
  deleteConversationMutationOptions,
  fetchConversationList,
  updateConversationMutationOptions,
} from "@/domain/conversation/queries";
import type {
  ConversationListQuery,
  ConversationRecord,
} from "@/domain/conversation/types";
import { getErrorMessage } from "@/shared/api";
import {
  FrameView,
  ListTable,
  MarkdownRenderer,
  type ListTableColumn,
  type ListTableRef,
} from "@/shared/ui";

export function ConversationLogPage(): JSX.Element {
  const { message, modal } = App.useApp();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const tableRef = useRef<ListTableRef<ConversationRecord>>(null);
  const [selectedConversation, setSelectedConversation] =
    useState<ConversationRecord | null>(null);

  const detailMessagesQuery = useQuery(
    selectedConversation == null
      ? {
          ...conversationMessagesQueryOptions("", { page: 1, pageSize: 100 }),
          enabled: false,
        }
      : conversationMessagesQueryOptions(selectedConversation.id, {
          page: 1,
          pageSize: 100,
        }),
  );

  const deleteMutation = useMutation(
    deleteConversationMutationOptions(queryClient),
  );
  const statusMutation = useMutation(
    updateConversationMutationOptions(
      queryClient,
      selectedConversation?.id ?? "",
    ),
  );

  const columns = useMemo<ListTableColumn<ConversationRecord>[]>(
    () => [
      {
        title: "会话",
        key: "conversation",
        render: (_, record) => (
          <div className="provider-cell">
            <Typography.Text strong>{record.title}</Typography.Text>
            <Typography.Text type="secondary">
              {record.agentName} / {record.channel}
            </Typography.Text>
          </div>
        ),
      },
      {
        title: "状态",
        dataIndex: "status",
        render: (status) => (
          <ConversationStatusTag status={status as ConversationRecord["status"]} />
        ),
      },
      {
        title: "最后消息",
        dataIndex: "lastMessagePreview",
        render: (value: string | null) => value ?? "暂无消息",
      },
      {
        title: "消息数",
        dataIndex: "messageCount",
      },
      {
        title: "最后更新",
        dataIndex: "updatedAt",
        render: (value: string) =>
          new Date(value).toLocaleString("zh-CN", { hour12: false }),
      },
    ],
    [],
  );

  const handleDelete = (record: ConversationRecord) => {
    modal.confirm({
      title: "删除会话日志",
      content: `确认软删除「${record.title}」吗？消息和运行记录也会一并隐藏。`,
      okText: "删除",
      okButtonProps: { danger: true },
      cancelText: "取消",
      onOk: async () => {
        await deleteMutation.mutateAsync(record.id);
        message.success("会话已删除");
        tableRef.current?.reload();
      },
    });
  };

  const toggleStatus = async (record: ConversationRecord) => {
    try {
      await statusMutation.mutateAsync({
        status: record.status === "active" ? "archived" : "active",
      });
      message.success(record.status === "active" ? "会话已归档" : "会话已恢复");
      tableRef.current?.reload();
    } catch (error) {
      message.error(getErrorMessage(error));
    }
  };

  return (
    <FrameView
      title="会话日志"
      description="检索、查看、归档和软删除当前用户的对话记录。"
    >
      <ListTable<ConversationRecord, ConversationListQuery>
        ref={tableRef}
        rowKey="id"
        columns={columns}
        queryKey={conversationQueryKeys.list}
        api={fetchConversationList}
        initialPageSize={10}
        initialQuery={{ includeArchived: true }}
        filterSchema={[
          {
            type: "input",
            key: "keyword",
            label: "关键词",
            placeholder: "搜索标题或最后消息",
          },
          {
            type: "select",
            key: "status",
            label: "状态",
            options: conversationStatusOptions,
          },
        ]}
        tableActions={(record) => (
          <Space size={4}>
            <Tooltip title="查看详情">
              <Button
                icon={<EyeOutlined />}
                onClick={() => setSelectedConversation(record)}
              />
            </Tooltip>
            <Tooltip title="继续对话">
              <Button
                icon={<MessageOutlined />}
                disabled={record.status !== "active"}
                onClick={() => navigate(`/chat?conversationId=${record.id}`)}
              />
            </Tooltip>
            <Tooltip title={record.status === "active" ? "归档" : "恢复"}>
              <Button
                icon={<RollbackOutlined />}
                onClick={() => void toggleStatus(record)}
              />
            </Tooltip>
            <Tooltip title="删除">
              <Button
                icon={<DeleteOutlined />}
                onClick={() => handleDelete(record)}
              />
            </Tooltip>
          </Space>
        )}
      />

      <Drawer
        width={720}
        title="会话详情"
        open={selectedConversation != null}
        onClose={() => setSelectedConversation(null)}
      >
        {selectedConversation != null ? (
          <Space direction="vertical" size={20} style={{ width: "100%" }}>
            <Descriptions column={1} bordered size="small">
              <Descriptions.Item label="标题">
                {selectedConversation.title}
              </Descriptions.Item>
              <Descriptions.Item label="Agent">
                {selectedConversation.agentName}
              </Descriptions.Item>
              <Descriptions.Item label="状态">
                <ConversationStatusTag status={selectedConversation.status} />
              </Descriptions.Item>
              <Descriptions.Item label="消息数">
                {selectedConversation.messageCount}
              </Descriptions.Item>
            </Descriptions>

            <Timeline
              items={(detailMessagesQuery.data?.list ?? []).map((item) => ({
                color:
                  item.status === "failed"
                    ? "red"
                    : item.role === "user"
                      ? "blue"
                      : "green",
                children: (
                  <div className="conversation-log-message">
                    <Typography.Text strong>{item.role}</Typography.Text>
                    {item.role === "assistant" ? (
                      <MarkdownRenderer content={item.content} />
                    ) : (
                      <Typography.Paragraph>{item.content}</Typography.Paragraph>
                    )}
                  </div>
                ),
              }))}
            />
          </Space>
        ) : null}
      </Drawer>
    </FrameView>
  );
}

import {
  DeleteOutlined,
  PlusOutlined,
  SendOutlined,
} from "@ant-design/icons";
import {
  App,
  Button,
  Input,
  Pagination,
  Space,
  Spin,
  Tooltip,
  Typography,
} from "antd";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useRef, useState } from "react";
import {
  ConversationAgentSelect,
  ConversationListItem,
  EmptyConversation,
  MessageBubble,
} from "@/domain/conversation/components";
import {
  agentRuntimePreviewQueryOptions,
  conversationMessagesQueryOptions,
  conversationQueryKeys,
  createConversationMutationOptions,
  updateConversationMutationOptions,
} from "@/domain/conversation/queries";
import {
  fetchConversationList,
  streamConversationMessage,
} from "@/domain/conversation/service";
import type {
  ConversationDetailRecord,
  ConversationMessageRecord,
  ConversationRecord,
  ConversationStreamState,
} from "@/domain/conversation/types";
import { getErrorMessage } from "@/shared/api";

function createLocalMessage(
  conversationId: number,
  role: "user" | "assistant",
  content: string,
  status: ConversationMessageRecord["status"],
): ConversationMessageRecord {
  const now = new Date().toISOString();
  return {
    id: `local-${role}-${now}`,
    conversationId,
    runId: null,
    role,
    status,
    content,
    contentFormat: "text",
    sequence: Date.now(),
    tokenCount: null,
    latencyMs: null,
    modelSnapshot: null,
    error: null,
    createdAt: now,
    updatedAt: now,
    isLocal: true,
  };
}

export function ChatPage(): JSX.Element {
  const { message } = App.useApp();
  const queryClient = useQueryClient();
  const messageEndRef = useRef<HTMLDivElement>(null);
  const [selectedAgentId, setSelectedAgentId] = useState<number | undefined>();
  const [activeConversationId, setActiveConversationId] = useState<
    number | undefined
  >();
  const [keyword, setKeyword] = useState("");
  const [page, setPage] = useState(1);
  const [inputValue, setInputValue] = useState("");
  const [submittedContent, setSubmittedContent] = useState("");
  const [streamState, setStreamState] =
    useState<ConversationStreamState>("idle");
  const [localMessages, setLocalMessages] = useState<ConversationMessageRecord[]>(
    [],
  );

  const conversationListQuery = useQuery({
    queryKey: conversationQueryKeys.list({
      page,
      pageSize: 20,
      keyword: keyword || undefined,
    }),
    queryFn: ({ signal }) =>
      fetchConversationList(
        {
          page,
          pageSize: 20,
          keyword: keyword || undefined,
        },
        signal,
      ),
  });

  const runtimePreviewQuery = useQuery(
    selectedAgentId === undefined
      ? {
          ...agentRuntimePreviewQueryOptions(""),
          enabled: false,
        }
      : agentRuntimePreviewQueryOptions(selectedAgentId),
  );

  const messagesQuery = useQuery(
    activeConversationId === undefined
      ? {
          ...conversationMessagesQueryOptions("", {
            page: 1,
            pageSize: 100,
          }),
          enabled: false,
        }
      : conversationMessagesQueryOptions(activeConversationId, {
          page: 1,
          pageSize: 100,
        }),
  );

  const createConversationMutation = useMutation(
    createConversationMutationOptions(queryClient, {
      onSuccess: (data) => {
        setActiveConversationId(data.id);
      },
    }),
  );

  const archiveConversationMutation = useMutation(
    updateConversationMutationOptions(
      queryClient,
      activeConversationId ?? "",
    ),
  );

  const serverMessages = messagesQuery.data?.list ?? [];
  const effectiveMessages = useMemo(
    () => [...serverMessages, ...localMessages],
    [serverMessages, localMessages],
  );

  useEffect(() => {
    messageEndRef.current?.scrollIntoView({ block: "end" });
  }, [effectiveMessages]);

  const canSend =
    selectedAgentId !== undefined &&
    runtimePreviewQuery.data?.isRunnable === true &&
    streamState !== "creatingConversation" &&
    streamState !== "connecting" &&
    streamState !== "streaming" &&
    inputValue.trim() !== "";

  const canCreateConversation =
    streamState !== "creatingConversation" &&
    streamState !== "connecting" &&
    streamState !== "streaming";

  const ensureConversation = async (): Promise<ConversationDetailRecord> => {
    if (activeConversationId !== undefined) {
      return {
        ...(conversationListQuery.data?.list.find(
          (item) => item.id === activeConversationId,
        ) as ConversationRecord),
        openingMessage: runtimePreviewQuery.data?.openingMessage ?? null,
        agentSnapshot: {},
        metadata: null,
      };
    }
    if (selectedAgentId === undefined) {
      throw new Error("请先选择 Agent");
    }
    setStreamState("creatingConversation");
    return createConversationMutation.mutateAsync({
      agentId: selectedAgentId,
    });
  };

  const sendMessage = async (contentOverride?: string) => {
    const content = (contentOverride ?? inputValue).trim();
    if (content === "") {
      return;
    }

    try {
      const conversation = await ensureConversation();
      const conversationId = conversation.id;
      setSubmittedContent(content);
      setInputValue("");
      setLocalMessages([
        createLocalMessage(conversationId, "user", content, "completed"),
        createLocalMessage(conversationId, "assistant", "", "streaming"),
      ]);
      setStreamState("connecting");
      await streamConversationMessage(conversationId, content, {
        onRunStarted: () => setStreamState("streaming"),
        onMessageCreated: (event) => {
          setLocalMessages([
            {
              ...createLocalMessage(
                conversationId,
                "user",
                event.userMessage.content,
                "completed",
              ),
              id: event.userMessage.id,
              sequence: event.userMessage.sequence,
              createdAt: event.userMessage.createdAt,
              updatedAt: event.userMessage.createdAt,
            },
            {
              ...createLocalMessage(
                conversationId,
                "assistant",
                event.assistantMessage.content,
                event.assistantMessage.status,
              ),
              id: event.assistantMessage.id,
              sequence: event.assistantMessage.sequence,
              createdAt: event.assistantMessage.createdAt,
              updatedAt: event.assistantMessage.createdAt,
            },
          ]);
        },
        onDelta: (event) => {
          setLocalMessages((current) =>
            current.map((item) =>
              item.role === "assistant"
                ? { ...item, content: item.content + event.delta }
                : item,
            ),
          );
        },
        onMessageCompleted: (event) => {
          setLocalMessages((current) =>
            current.map((item) =>
              item.role === "assistant"
                ? {
                    ...item,
                    id: event.message.id,
                    content: event.message.content,
                    status: event.message.status,
                    sequence: event.message.sequence,
                  }
                : item,
            ),
          );
        },
        onError: (event) => {
          setStreamState("failed");
          setLocalMessages((current) =>
            current.map((item) =>
              item.role === "assistant"
                ? {
                    ...item,
                    status: "failed",
                    content: event.message,
                    error: event as unknown as Record<string, unknown>,
                  }
                : item,
            ),
          );
        },
        onDone: async () => {
          setStreamState("completed");
          setLocalMessages([]);
          await queryClient.invalidateQueries({
            queryKey: conversationQueryKeys.all,
          });
        },
      });
      setStreamState("idle");
    } catch (error) {
      setStreamState("failed");
      message.error(getErrorMessage(error));
    }
  };

  const archiveActiveConversation = async () => {
    if (activeConversationId === undefined) {
      return;
    }
    await archiveConversationMutation.mutateAsync({ status: "archived" });
    setActiveConversationId(undefined);
    setLocalMessages([]);
    message.success("会话已归档");
  };

  const createEmptyConversation = async () => {
    if (selectedAgentId === undefined) {
      message.warning("请先选择 Agent");
      return;
    }
    if (runtimePreviewQuery.data?.isRunnable === false) {
      message.warning(
        runtimePreviewQuery.data.blockedReason ?? "当前 Agent 暂不可运行",
      );
      return;
    }

    try {
      setStreamState("creatingConversation");
      setLocalMessages([]);
      const created = await createConversationMutation.mutateAsync({
        agentId: selectedAgentId,
      });
      setActiveConversationId(created.id);
      setPage(1);
      message.success("会话已创建");
    } catch (error) {
      message.error(getErrorMessage(error));
    } finally {
      setStreamState("idle");
    }
  };

  return (
    <div className="chat-workbench">
      <header className="chat-toolbar">
        <ConversationAgentSelect
          value={selectedAgentId}
          onChange={(agentId) => {
            setSelectedAgentId(agentId);
            setActiveConversationId(undefined);
            setLocalMessages([]);
          }}
        />
        <Button
          icon={<PlusOutlined />}
          disabled={!canCreateConversation}
          loading={streamState === "creatingConversation"}
          onClick={() => void createEmptyConversation()}
        >
          新建会话
        </Button>
      </header>

      <div className="chat-layout">
        <aside className="chat-sidebar">
          <Input.Search
            allowClear
            placeholder="搜索会话"
            value={keyword}
            onChange={(event) => setKeyword(event.target.value)}
            onSearch={() => setPage(1)}
          />
          <div className="conversation-list">
            {conversationListQuery.isFetching ? <Spin /> : null}
            {conversationListQuery.data?.list.map((record) => (
              <ConversationListItem
                key={record.id}
                record={record}
                active={record.id === activeConversationId}
                onClick={() => {
                  setActiveConversationId(record.id);
                  setSelectedAgentId(record.agentId);
                  setLocalMessages([]);
                }}
              />
            ))}
          </div>
          <Pagination
            simple
            current={page}
            pageSize={20}
            total={conversationListQuery.data?.total ?? 0}
            onChange={setPage}
          />
        </aside>

        <main className="chat-main">
          <div className="chat-main-header">
            <Typography.Text strong>
              {conversationListQuery.data?.list.find(
                (item) => item.id === activeConversationId,
              )?.title ?? "未选择会话"}
            </Typography.Text>
            <Tooltip title="归档会话">
              <Button
                type="link"
                size="small"
                icon={<DeleteOutlined />}
                disabled={activeConversationId === undefined}
                onClick={archiveActiveConversation}
              />
            </Tooltip>
          </div>

          <div className="chat-message-list">
            {messagesQuery.isFetching ? <Spin /> : null}
            {effectiveMessages.length === 0 ? (
              <EmptyConversation
                openingMessage={runtimePreviewQuery.data?.openingMessage}
              />
            ) : (
              effectiveMessages.map((item) => (
                <MessageBubble
                  key={item.id}
                  message={item}
                  retry={
                    item.status === "failed" && submittedContent !== ""
                      ? () => void sendMessage(submittedContent)
                      : undefined
                  }
                />
              ))
            )}
            <div ref={messageEndRef} />
          </div>

          <div className="chat-input-bar">
            <Input.TextArea
              value={inputValue}
              rows={3}
              maxLength={20000}
              disabled={streamState === "streaming"}
              placeholder="输入消息，Enter 发送，Shift + Enter 换行"
              onChange={(event) => setInputValue(event.target.value)}
              onPressEnter={(event) => {
                if (!event.shiftKey) {
                  event.preventDefault();
                  void sendMessage();
                }
              }}
            />
            <Space align="end">
              <Button
                type="primary"
                icon={<SendOutlined />}
                disabled={!canSend}
                loading={
                  streamState === "creatingConversation" ||
                  streamState === "connecting" ||
                  streamState === "streaming"
                }
                onClick={() => void sendMessage()}
              >
                发送
              </Button>
            </Space>
          </div>
        </main>
      </div>
    </div>
  );
}

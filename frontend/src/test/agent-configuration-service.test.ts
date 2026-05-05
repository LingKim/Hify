import { createAgent, fetchAgentConfigPreview } from "@/domain/agent-configuration/service";
import type { AgentFormValues } from "@/domain/agent-configuration/types";

const formValues: AgentFormValues = {
  name: "客服助手",
  description: "回答售前与售后常见问题",
  avatarUrl: "",
  status: "draft",
  orchestrationMode: "workflow",
  providerInstanceId: 1,
  providerModelId: 3,
  systemPrompt: "",
  openingMessage: "你好，我可以帮你查询产品和订单问题。",
  modelConfig: {
    temperature: 0.7,
    topP: 1,
    maxTokens: 2048,
  },
  runtimeConfig: {
    stream: true,
    maxIterations: 5,
    memoryWindow: 10,
  },
  workflowRef: {
    workflowDraftKey: "draft-only",
  },
  tools: [
    {
      toolId: 10,
      bindingName: "查询订单",
      isEnabled: true,
      sortOrder: 0,
      config: {
        timeoutSeconds: 20,
      },
    },
  ],
  knowledgeBases: [
    {
      knowledgeBaseId: 20,
      isEnabled: true,
      sortOrder: 0,
      retrievalConfig: {
        topK: 5,
        scoreThreshold: 0.5,
        rerankEnabled: false,
      },
    },
  ],
  tags: ["客服", "FAQ"],
};

describe("agent configuration service", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("sends aggregated create payload with workflow draft fields", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          code: 201,
          message: "success",
          data: {
            id: 1,
            ...formValues,
            systemPrompt: null,
            avatarUrl: null,
            tools: formValues.tools,
            knowledgeBases: formValues.knowledgeBases,
            model: null,
            toolCount: 1,
            knowledgeBaseCount: 1,
            metadata: null,
            createdAt: "2026-05-05T10:00:00Z",
            updatedAt: "2026-05-05T10:00:00Z",
          },
        }),
        {
          status: 201,
          headers: { "Content-Type": "application/json" },
        },
      ),
    );

    await createAgent(formValues);

    expect(fetchSpy).toHaveBeenCalledWith(
      "/api/v1/agents",
      expect.objectContaining({
        method: "POST",
        body: expect.stringContaining('"orchestrationMode":"workflow"'),
      }),
    );
    expect(JSON.parse(String(fetchSpy.mock.calls[0]?.[1]?.body))).toMatchObject({
      systemPrompt: null,
      workflowRef: {
        workflowDraftKey: "draft-only",
      },
      tools: [
        {
          toolId: 10,
          bindingName: "查询订单",
        },
      ],
      knowledgeBases: [
        {
          knowledgeBaseId: 20,
        },
      ],
    });
  });

  it("fetches agent config preview by id", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          code: 200,
          message: "success",
          data: {
            agentId: 1,
            name: "客服助手",
            status: "draft",
            orchestrationMode: "agent",
            isRunnable: false,
            model: null,
            enabledToolIds: [],
            enabledKnowledgeBaseIds: [],
            runtimeConfig: null,
            workflowRef: null,
            warnings: ["Agent 当前不是启用状态"],
          },
        }),
        {
          status: 200,
          headers: { "Content-Type": "application/json" },
        },
      ),
    );

    await fetchAgentConfigPreview(1);

    expect(fetchSpy).toHaveBeenCalledWith(
      "/api/v1/agents/1/config-preview",
      expect.objectContaining({
        method: "GET",
      }),
    );
  });
});

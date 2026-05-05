import {
  CheckCircleTwoTone,
  CheckCircleOutlined,
  CloseCircleOutlined,
  DeleteOutlined,
  GlobalOutlined,
  InfoCircleOutlined,
  PlusOutlined,
  StarFilled,
  WarningTwoTone,
} from "@ant-design/icons";
import {
  Button,
  Card,
  Empty,
  Flex,
  Input,
  InputNumber,
  Popover,
  Segmented,
  Select,
  Space,
  Switch,
  Tag,
  Typography,
} from "antd";
import type {
  ProviderHealthSummary,
  ProviderModelFormValue,
  ProviderSummaryRecord,
} from "@/domain/provider-management/types";

const healthColorMap: Record<string, string> = {
  healthy: "success",
  degraded: "warning",
  unhealthy: "error",
  unknown: "default",
};

const statusColorMap: Record<string, string> = {
  active: "success",
  draft: "processing",
  disabled: "default",
  archived: "error",
};

export const providerTypeOptions = [
  { label: "OpenAI", value: "openai" },
  { label: "Anthropic", value: "anthropic" },
  { label: "Gemini", value: "gemini" },
  { label: "Ollama", value: "ollama" },
  { label: "兼容接口", value: "openai_compatible" },
] as const;

export const apiFamilyOptions = [
  { label: "OpenAI Responses", value: "openai_responses" },
  { label: "OpenAI Chat", value: "openai_chat" },
  { label: "Anthropic", value: "anthropic_messages" },
  { label: "Gemini", value: "gemini_native" },
  { label: "Ollama", value: "ollama_native" },
] as const;

export const providerStatusOptions = [
  { label: "草稿", value: "draft" },
  { label: "启用", value: "active" },
  { label: "停用", value: "disabled" },
  { label: "归档", value: "archived" },
] as const;

export const authTypeOptions = [
  { label: "API Key", value: "api_key" },
  { label: "Bearer Token", value: "bearer_token" },
  { label: "无鉴权", value: "none" },
] as const;

const providerDefaultsMap: Record<
  string,
  {
    apiFamily: string;
    baseUrl: string;
    authType: string;
  }
> = {
  openai: {
    apiFamily: "openai_responses",
    baseUrl: "https://api.openai.com/v1",
    authType: "api_key",
  },
  anthropic: {
    apiFamily: "anthropic_messages",
    baseUrl: "https://api.anthropic.com",
    authType: "api_key",
  },
  gemini: {
    apiFamily: "gemini_native",
    baseUrl: "https://generativelanguage.googleapis.com",
    authType: "api_key",
  },
  ollama: {
    apiFamily: "ollama_native",
    baseUrl: "http://127.0.0.1:11434",
    authType: "none",
  },
  openai_compatible: {
    apiFamily: "openai_chat",
    baseUrl: "",
    authType: "api_key",
  },
};

export const modelStatusOptions = [
  { label: "启用", value: "active" },
  { label: "停用", value: "disabled" },
  { label: "归档", value: "archived" },
] as const;

export function createEmptyModel(index: number): ProviderModelFormValue {
  return {
    modelName: "",
    displayName: "",
    description: "",
    status: "active",
    isDefault: index === 0,
    sortOrder: index,
    supportsChat: true,
    supportsStream: true,
    supportsTools: false,
    supportsStructuredOutput: false,
    supportsVisionInput: false,
    supportsAudioInput: false,
    supportsReasoning: false,
    supportsEmbeddings: false,
    contextWindow: undefined,
    maxOutputTokens: undefined,
    maxInputTokens: undefined,
    temperatureSupported: true,
    topPSupported: true,
  };
}

export function getProviderHealthTone(health?: ProviderHealthSummary | null): string {
  if (health == null) {
    return "default";
  }

  return healthColorMap[health.healthState] ?? "default";
}

export function getProviderStatusTone(status: string): string {
  return statusColorMap[status] ?? "default";
}

export function ProviderTagSet({
  record,
}: {
  record: ProviderSummaryRecord;
}): JSX.Element {
  return (
    <Space size={[6, 6]} wrap>
      <Tag color="blue">{record.providerType}</Tag>
      <Tag color="geekblue">{record.apiFamily}</Tag>
      <Tag color={getProviderStatusTone(record.status)}>{record.status}</Tag>
      <Tag color={getProviderHealthTone(record.health)}>
        {record.health?.healthState ?? "unknown"}
      </Tag>
      {record.isDefault ? <Tag color="gold">默认实例</Tag> : null}
    </Space>
  );
}

export function ProviderHealthCell({
  record,
}: {
  record: ProviderSummaryRecord;
}): JSX.Element {
  const health = record.health;
  if (health == null) {
    return <Tag>未检测</Tag>;
  }

  const isHealthy = health.healthState === "healthy";
  return (
    <Popover
      title="健康状态详情"
      content={
        <div className="provider-health-popover">
          <HealthMetaItem label="总体状态" value={health.healthState} />
          <HealthMetaItem label="鉴权状态" value={health.authState} />
          <HealthMetaItem
            label="连通状态"
            value={health.connectivityState}
          />
          <HealthMetaItem label="推理状态" value={health.inferenceState} />
          <HealthMetaItem
            label="最近检测"
            value={formatDateTime(health.lastCheckAt)}
          />
          <HealthMetaItem
            label="P50 延迟"
            value={formatLatency(health.latencyMsP50)}
          />
          <HealthMetaItem
            label="P95 延迟"
            value={formatLatency(health.latencyMsP95)}
          />
          <HealthMetaItem
            label="错误信息"
            value={health.lastErrorMessage ?? "无"}
          />
        </div>
      }
    >
      <Space size={6}>
        {isHealthy ? (
          <CheckCircleTwoTone twoToneColor="#52c41a" />
        ) : (
          <WarningTwoTone twoToneColor="#faad14" />
        )}
        <Tag color={getProviderHealthTone(health)}>{health.healthState}</Tag>
      </Space>
    </Popover>
  );
}

export function ProviderTypeField({
  value,
  onChange,
  setFieldValue,
}: {
  value: unknown;
  onChange: (value: unknown) => void;
  setFieldValue: (key: string, value: unknown) => void;
}): JSX.Element {
  return (
    <Select
      value={typeof value === "string" ? value : undefined}
      options={providerTypeOptions.map((item) => ({
        label: item.label,
        value: item.value,
      }))}
      onChange={(nextValue) => {
        onChange(nextValue);
        const defaults = providerDefaultsMap[nextValue];
        if (defaults == null) {
          return;
        }
        setFieldValue("apiFamily", defaults.apiFamily);
        setFieldValue("authType", defaults.authType);
        if (defaults.baseUrl) {
          setFieldValue("baseUrl", defaults.baseUrl);
        }
      }}
    />
  );
}

export function ProviderBaseUrlHint({
  providerType,
}: {
  providerType: unknown;
}): JSX.Element {
  const defaults =
    typeof providerType === "string"
      ? providerDefaultsMap[providerType]
      : undefined;

  return (
    <div className="provider-inline-hint">
      <Space size={6}>
        <GlobalOutlined />
        <Typography.Text type="secondary">
          {defaults?.baseUrl
            ? `推荐默认地址：${defaults.baseUrl}`
            : "兼容接口请填写实际网关地址"}
        </Typography.Text>
      </Space>
    </div>
  );
}

export function ProviderAuthHint({
  providerType,
  authType,
}: {
  providerType: unknown;
  authType: unknown;
}): JSX.Element {
  return (
    <div className="provider-inline-hint">
      <Space size={6}>
        <InfoCircleOutlined />
        <Typography.Text type="secondary">
          {buildAuthHintText(providerType, authType)}
        </Typography.Text>
      </Space>
    </div>
  );
}

export function ProviderModelsEditor({
  value,
  onChange,
}: {
  value: ProviderModelFormValue[] | undefined;
  onChange: (nextValue: ProviderModelFormValue[]) => void;
}): JSX.Element {
  const models = value ?? [createEmptyModel(0)];

  const syncModels = (
    updater: (current: ProviderModelFormValue[]) => ProviderModelFormValue[],
  ) => {
    const nextModels = updater(models).map((model, index) => ({
      ...model,
      sortOrder: index,
    }));
    onChange(nextModels);
  };

  const updateModel = (
    index: number,
    patch: Partial<ProviderModelFormValue>,
  ) => {
    syncModels((current) =>
      current.map((model, currentIndex) => {
        if (currentIndex !== index) {
          return model;
        }
        return {
          ...model,
          ...patch,
        };
      }),
    );
  };

  const makeDefaultModel = (index: number) => {
    syncModels((current) =>
      current.map((model, currentIndex) => ({
        ...model,
        isDefault: currentIndex === index,
      })),
    );
  };

  const removeModel = (index: number) => {
    syncModels((current) => {
      const nextModels = current.filter((_, currentIndex) => currentIndex !== index);
      if (nextModels.length === 0) {
        return [createEmptyModel(0)];
      }
      if (!nextModels.some((model) => model.isDefault)) {
        const firstModel = nextModels[0];
        if (firstModel === undefined) {
          return [createEmptyModel(0)];
        }
        nextModels[0] = {
          ...firstModel,
          isDefault: true,
        };
      }
      return nextModels;
    });
  };

  return (
    <div className="provider-models-editor">
      <Flex justify="space-between" align="center" className="provider-models-toolbar">
        <div>
          <Typography.Text strong>模型清单</Typography.Text>
          <Typography.Paragraph type="secondary">
            同一提供商实例下可以维护多个模型，前端仍然在一个页面里完成配置。
          </Typography.Paragraph>
        </div>
        <Button
          type="dashed"
          icon={<PlusOutlined />}
          onClick={() => syncModels((current) => [...current, createEmptyModel(current.length)])}
        >
          添加模型
        </Button>
      </Flex>

      {models.length === 0 ? (
        <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="还没有配置模型" />
      ) : null}

      <div className="provider-model-grid">
        {models.map((model, index) => (
          <Card
            key={`${model.modelName}-${index}`}
            className="provider-model-card"
            title={
              <Space>
                <span>模型 {index + 1}</span>
                {model.isDefault ? (
                  <Tag color="gold" icon={<StarFilled />}>
                    默认
                  </Tag>
                ) : null}
              </Space>
            }
            extra={
              <Space>
                {!model.isDefault ? (
                  <Button type="link" onClick={() => makeDefaultModel(index)}>
                    设为默认
                  </Button>
                ) : null}
                <Button
                  type="text"
                  danger
                  icon={<DeleteOutlined />}
                  onClick={() => removeModel(index)}
                />
              </Space>
            }
          >
            <div className="provider-model-fields">
              <label className="provider-model-field">
                <span>模型名称</span>
                <Input
                  value={model.modelName}
                  placeholder="如 gpt-4.1"
                  onChange={(event) => {
                    updateModel(index, { modelName: event.target.value });
                  }}
                />
              </label>
              <label className="provider-model-field">
                <span>展示名称</span>
                <Input
                  value={model.displayName}
                  placeholder="如 GPT-4.1"
                  onChange={(event) => {
                    updateModel(index, { displayName: event.target.value });
                  }}
                />
              </label>
              <label className="provider-model-field provider-model-field-wide">
                <span>备注</span>
                <Input.TextArea
                  rows={2}
                  value={model.description}
                  placeholder="给运营或管理员的说明"
                  onChange={(event) => {
                    updateModel(index, { description: event.target.value });
                  }}
                />
              </label>
              <label className="provider-model-field">
                <span>状态</span>
                <Segmented
                  block
                  value={model.status}
                  options={[...modelStatusOptions]}
                  onChange={(value) => {
                    updateModel(index, { status: String(value) });
                  }}
                />
              </label>
              <label className="provider-model-field">
                <span>上下文窗口</span>
                <InputNumber
                  min={0}
                  style={{ width: "100%" }}
                  value={model.contextWindow}
                  placeholder="可选"
                  onChange={(value) => {
                    updateModel(index, { contextWindow: value ?? undefined });
                  }}
                />
              </label>
              <label className="provider-model-field">
                <span>最大输出 Token</span>
                <InputNumber
                  min={0}
                  style={{ width: "100%" }}
                  value={model.maxOutputTokens}
                  placeholder="可选"
                  onChange={(value) => {
                    updateModel(index, { maxOutputTokens: value ?? undefined });
                  }}
                />
              </label>
              <label className="provider-model-field">
                <span>最大输入 Token</span>
                <InputNumber
                  min={0}
                  style={{ width: "100%" }}
                  value={model.maxInputTokens}
                  placeholder="可选"
                  onChange={(value) => {
                    updateModel(index, { maxInputTokens: value ?? undefined });
                  }}
                />
              </label>
            </div>

            <div className="provider-capability-grid">
              <CapabilitySwitch
                label="聊天"
                checked={model.supportsChat}
                onChange={(checked) => {
                  updateModel(index, { supportsChat: checked });
                }}
              />
              <CapabilitySwitch
                label="流式"
                checked={model.supportsStream}
                onChange={(checked) => {
                  updateModel(index, { supportsStream: checked });
                }}
              />
              <CapabilitySwitch
                label="工具调用"
                checked={model.supportsTools}
                onChange={(checked) => {
                  updateModel(index, { supportsTools: checked });
                }}
              />
              <CapabilitySwitch
                label="结构化输出"
                checked={model.supportsStructuredOutput}
                onChange={(checked) => {
                  updateModel(index, { supportsStructuredOutput: checked });
                }}
              />
              <CapabilitySwitch
                label="视觉输入"
                checked={model.supportsVisionInput}
                onChange={(checked) => {
                  updateModel(index, { supportsVisionInput: checked });
                }}
              />
              <CapabilitySwitch
                label="音频输入"
                checked={model.supportsAudioInput}
                onChange={(checked) => {
                  updateModel(index, { supportsAudioInput: checked });
                }}
              />
              <CapabilitySwitch
                label="推理模型"
                checked={model.supportsReasoning}
                onChange={(checked) => {
                  updateModel(index, { supportsReasoning: checked });
                }}
              />
              <CapabilitySwitch
                label="Embedding"
                checked={model.supportsEmbeddings}
                onChange={(checked) => {
                  updateModel(index, { supportsEmbeddings: checked });
                }}
              />
              <CapabilitySwitch
                label="Temperature"
                checked={model.temperatureSupported}
                onChange={(checked) => {
                  updateModel(index, { temperatureSupported: checked });
                }}
              />
              <CapabilitySwitch
                label="Top P"
                checked={model.topPSupported}
                onChange={(checked) => {
                  updateModel(index, { topPSupported: checked });
                }}
              />
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}

function CapabilitySwitch({
  label,
  checked,
  onChange,
}: {
  label: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
}): JSX.Element {
  return (
    <div className="provider-capability-item">
      <Typography.Text>{label}</Typography.Text>
      <Switch
        checked={checked}
        checkedChildren={<CheckCircleOutlined />}
        unCheckedChildren={<CloseCircleOutlined />}
        onChange={onChange}
      />
    </div>
  );
}

function formatDateTime(value: string | null): string {
  if (!value) {
    return "无";
  }
  return new Date(value).toLocaleString("zh-CN", { hour12: false });
}

function formatLatency(value: number | null): string {
  return value == null ? "无" : `${value} ms`;
}

function buildAuthHintText(
  providerType: unknown,
  authType: unknown,
): string {
  if (providerType === "ollama" || authType === "none") {
    return "Ollama 或本地网关通常无需平台密钥。";
  }
  if (providerType === "anthropic") {
    return "Anthropic 一般使用 API Key，请确认网关是否需要额外 Header。";
  }
  if (providerType === "gemini") {
    return "Gemini 通常使用 API Key，建议核对实际网关的鉴权方式。";
  }
  return "大多数托管模型服务可直接使用 API Key 或 Bearer Token。";
}

function HealthMetaItem({
  label,
  value,
}: {
  label: string;
  value: string;
}): JSX.Element {
  return (
    <div className="provider-health-item">
      <Typography.Text type="secondary">{label}</Typography.Text>
      <Typography.Text>{value}</Typography.Text>
    </div>
  );
}

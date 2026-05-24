import {
  ApiOutlined,
  CheckCircleOutlined,
  DeleteOutlined,
  PlusOutlined,
} from "@ant-design/icons";
import { Button, Card, Empty, Input, Select, Space, Switch, Tag, Tooltip, Typography } from "antd";
import type {
  ToolFormParameterValue,
  ToolParameterRecord,
  ToolStatus,
  ToolSummaryRecord,
} from "@/domain/tool-integration/types";

export const toolStatusOptions = [
  { label: "草稿", value: "draft" },
  { label: "启用", value: "enabled" },
  { label: "停用", value: "disabled" },
  { label: "归档", value: "archived" },
] as const;

export const toolMethodOptions = ["GET", "POST", "PUT", "PATCH", "DELETE"].map(
  (method) => ({
    label: method,
    value: method,
  }),
);

export const toolAuthTypeOptions = [
  { label: "无鉴权", value: "none" },
  { label: "Bearer Token", value: "bearer" },
  { label: "Header API Key", value: "api_key_header" },
  { label: "Query API Key", value: "api_key_query" },
] as const;

export const toolParamLocationOptions = [
  { label: "Path", value: "path" },
  { label: "Query", value: "query" },
  { label: "Header", value: "header" },
  { label: "Body", value: "body" },
] as const;

export const toolSchemaTypeOptions = [
  { label: "字符串", value: "string" },
  { label: "数字", value: "number" },
  { label: "整数", value: "integer" },
  { label: "布尔", value: "boolean" },
  { label: "对象", value: "object" },
  { label: "数组", value: "array" },
] as const;

const statusColorMap: Record<ToolStatus, string> = {
  draft: "gold",
  enabled: "success",
  disabled: "default",
  archived: "error",
};

const statusLabelMap: Record<ToolStatus, string> = {
  draft: "草稿",
  enabled: "启用",
  disabled: "停用",
  archived: "归档",
};

export function ToolStatusTag({ status }: { status: ToolStatus }): JSX.Element {
  return <Tag color={statusColorMap[status]}>{statusLabelMap[status]}</Tag>;
}

export function ToolMethodTag({ method }: { method: string }): JSX.Element {
  return <Tag color="blue">{method}</Tag>;
}

export function ToolHealthCell({
  record,
}: {
  record: ToolSummaryRecord;
}): JSX.Element {
  if (record.lastTestStatus == null) {
    return <Tag>未测试</Tag>;
  }

  if (record.lastTestStatus === "success") {
    return (
      <Space size={6}>
        <CheckCircleOutlined />
        <Tag color="success">{record.lastTestLatencyMs ?? 0}ms</Tag>
      </Space>
    );
  }

  return <Tag color="error">{record.lastTestStatus}</Tag>;
}

export function createEmptyToolParameter(): ToolFormParameterValue {
  return {
    name: "",
    label: "",
    description: "",
    paramLocation: "query",
    schemaType: "string",
    isRequired: true,
    defaultValueJson: "",
    enumValuesJson: "",
    schemaJson: "",
  };
}

export function mapParameterToFormValue(
  parameter: ToolParameterRecord,
): ToolFormParameterValue {
  return {
    name: parameter.name,
    label: parameter.label,
    description: parameter.description ?? "",
    paramLocation: parameter.paramLocation,
    schemaType: parameter.schemaType,
    isRequired: parameter.isRequired,
    defaultValueJson:
      parameter.defaultValue == null
        ? ""
        : JSON.stringify(parameter.defaultValue, null, 2),
    enumValuesJson:
      parameter.enumValues == null
        ? ""
        : JSON.stringify(parameter.enumValues, null, 2),
    schemaJson:
      parameter.schema == null ? "" : JSON.stringify(parameter.schema, null, 2),
  };
}

export function ToolParametersEditor({
  value,
  onChange,
}: {
  value: ToolFormParameterValue[] | undefined;
  onChange: (nextValue: ToolFormParameterValue[]) => void;
}): JSX.Element {
  const parameters = value ?? [];

  const updateParameter = (
    index: number,
    patch: Partial<ToolFormParameterValue>,
  ) => {
    onChange(
      parameters.map((parameter, currentIndex) =>
        currentIndex === index ? { ...parameter, ...patch } : parameter,
      ),
    );
  };

  if (parameters.length === 0) {
    return (
      <Empty
        className="tool-parameters-empty"
        description="当前工具没有显式入参"
      >
        <Button
          icon={<PlusOutlined />}
          onClick={() => onChange([createEmptyToolParameter()])}
        >
          添加参数
        </Button>
      </Empty>
    );
  }

  return (
    <div className="tool-parameters-editor">
      <div className="tool-parameters-toolbar">
        <Typography.Text type="secondary">
          参数会用于测试执行表单和请求模板变量。
        </Typography.Text>
        <Button
          icon={<PlusOutlined />}
          onClick={() => onChange([...parameters, createEmptyToolParameter()])}
        >
          添加参数
        </Button>
      </div>
      {parameters.map((parameter, index) => (
        <Card
          className="tool-parameter-card"
          key={`${parameter.name}-${index}`}
          size="small"
          title={`参数 ${index + 1}`}
          extra={
            <Tooltip title="删除参数">
              <Button
                icon={<DeleteOutlined />}
                size="small"
                type="link"
                onClick={() =>
                  onChange(parameters.filter((_, currentIndex) => currentIndex !== index))
                }
              />
            </Tooltip>
          }
        >
          <div className="tool-parameter-grid">
            <Input
              placeholder="参数名"
              value={parameter.name}
              onChange={(event) =>
                updateParameter(index, { name: event.target.value })
              }
            />
            <Input
              placeholder="展示名"
              value={parameter.label}
              onChange={(event) =>
                updateParameter(index, { label: event.target.value })
              }
            />
            <Select
              options={[...toolParamLocationOptions]}
              value={parameter.paramLocation}
              onChange={(paramLocation) => updateParameter(index, { paramLocation })}
            />
            <Select
              options={[...toolSchemaTypeOptions]}
              value={parameter.schemaType}
              onChange={(schemaType) => updateParameter(index, { schemaType })}
            />
            <Input
              placeholder="默认值 JSON，可空"
              value={parameter.defaultValueJson}
              onChange={(event) =>
                updateParameter(index, { defaultValueJson: event.target.value })
              }
            />
            <Input
              placeholder="枚举 JSON 数组，可空"
              value={parameter.enumValuesJson}
              onChange={(event) =>
                updateParameter(index, { enumValuesJson: event.target.value })
              }
            />
            <Input
              className="tool-parameter-grid-wide"
              placeholder="描述"
              value={parameter.description}
              onChange={(event) =>
                updateParameter(index, { description: event.target.value })
              }
            />
            <Input.TextArea
              className="tool-parameter-grid-wide"
              placeholder='Schema JSON，可空，默认按类型生成，如 {"type":"string"}'
              rows={2}
              value={parameter.schemaJson}
              onChange={(event) =>
                updateParameter(index, { schemaJson: event.target.value })
              }
            />
            <Space>
              <Switch
                checked={parameter.isRequired}
                checkedChildren="必填"
                unCheckedChildren="可选"
                onChange={(isRequired) => updateParameter(index, { isRequired })}
              />
            </Space>
          </div>
        </Card>
      ))}
    </div>
  );
}

export function ToolRequestTemplateHint(): JSX.Element {
  return (
    <div className="tool-inline-hint">
      <Space size={6}>
        <ApiOutlined />
        <Typography.Text type="secondary">
          请求模板支持 {"{{参数名}}"} 占位符，JSON 留空时按空对象处理。
        </Typography.Text>
      </Space>
    </div>
  );
}

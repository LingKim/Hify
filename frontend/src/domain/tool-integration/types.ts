import type { PageResult } from "@/shared/types/list";

export type ToolStatus = "draft" | "enabled" | "disabled" | "archived";
export type ToolSourceType = "manual" | "openapi";
export type ToolHttpMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
export type ToolAuthType = "none" | "bearer" | "api_key_header" | "api_key_query";
export type ToolParamLocation = "path" | "query" | "header" | "body";
export type ToolSchemaType =
  | "string"
  | "number"
  | "integer"
  | "boolean"
  | "object"
  | "array";
export type ToolExecutionStatus = "success" | "failed" | "timeout";

export interface ToolListQuery {
  keyword?: string;
  status?: ToolStatus;
  sourceType?: ToolSourceType;
  httpMethod?: ToolHttpMethod;
}

export interface ToolAuthRecord {
  authType: ToolAuthType;
  secretMasked: string | null;
  headerName: string | null;
  queryName: string | null;
  lastRotatedAt: string | null;
}

export interface ToolParameterRecord {
  name: string;
  label: string;
  description: string | null;
  paramLocation: ToolParamLocation;
  schemaType: ToolSchemaType;
  isRequired: boolean;
  defaultValue: unknown;
  enumValues: unknown[] | null;
  schema: Record<string, unknown> | null;
  sortOrder: number;
  metadata: Record<string, unknown> | null;
}

export interface ToolSummaryRecord {
  id: number;
  name: string;
  description: string | null;
  status: ToolStatus;
  toolType: "http";
  sourceType: ToolSourceType;
  httpMethod: ToolHttpMethod;
  url: string;
  authType: ToolAuthType;
  parameterCount: number;
  boundAgentCount: number;
  lastTestStatus: ToolExecutionStatus | null;
  lastTestAt: string | null;
  lastTestLatencyMs: number | null;
  createdAt: string;
  updatedAt: string;
}

export interface ToolDetailRecord extends Omit<ToolSummaryRecord, "authType" | "parameterCount" | "boundAgentCount"> {
  timeoutSeconds: number;
  headersTemplate: Record<string, unknown> | null;
  queryTemplate: Record<string, unknown> | null;
  bodyTemplate: Record<string, unknown> | null;
  contentType: string;
  auth: ToolAuthRecord;
  parameters: ToolParameterRecord[];
  openapiSource: Record<string, unknown> | null;
  lastErrorMessage: string | null;
  metadata: Record<string, unknown> | null;
}

export type ToolListResult = PageResult<ToolSummaryRecord>;

export interface ToolOptionRecord {
  id: number;
  name: string;
  description: string | null;
  status: ToolStatus;
  httpMethod: ToolHttpMethod;
  url: string;
  parameterCount: number;
}

export interface ToolFormParameterValue {
  name: string;
  label: string;
  description?: string;
  paramLocation: ToolParamLocation;
  schemaType: ToolSchemaType;
  isRequired: boolean;
  defaultValueJson?: string;
  enumValuesJson?: string;
  schemaJson?: string;
}

export interface ToolFormValues {
  name: string;
  description?: string;
  status: ToolStatus;
  sourceType: ToolSourceType;
  httpMethod: ToolHttpMethod;
  url: string;
  timeoutSeconds: number;
  headersTemplateJson?: string;
  queryTemplateJson?: string;
  bodyTemplateJson?: string;
  contentType: string;
  authType: ToolAuthType;
  secretValue?: string;
  headerName?: string;
  queryName?: string;
  parameters: ToolFormParameterValue[];
  openapiSource?: Record<string, unknown> | null;
  metadata?: Record<string, unknown> | null;
}

export interface ToolExecuteTestPayload {
  parameters: Record<string, unknown>;
  timeoutSeconds?: number;
}

export interface ToolExecutionResult {
  logId: number;
  toolId: number;
  status: ToolExecutionStatus;
  request: {
    method: string;
    url: string;
    headers: Record<string, string>;
    bodyPreview: string | null;
  };
  response: {
    statusCode: number | null;
    headers: Record<string, string>;
    bodyPreview: string | null;
  };
  latencyMs: number;
  errorCode: string | null;
  errorMessage: string | null;
  createdAt: string;
}

export interface ToolExecutionLogRecord {
  id: number;
  toolId: number;
  source: "test" | "conversation";
  status: ToolExecutionStatus;
  requestMethod: string;
  requestUrl: string;
  responseStatusCode: number | null;
  latencyMs: number;
  errorCode: string | null;
  errorMessage: string | null;
  createdAt: string;
}

export type ToolExecutionLogListResult = PageResult<ToolExecutionLogRecord>;

export interface OpenApiPreviewPayload {
  document: Record<string, unknown>;
  operation: {
    path: string;
    method: ToolHttpMethod;
  };
  serverUrl?: string;
}

export interface OpenApiToolDraft {
  name: string;
  description: string | null;
  status: ToolStatus;
  sourceType: ToolSourceType;
  httpMethod: ToolHttpMethod;
  url: string;
  timeoutSeconds: number;
  headersTemplate: Record<string, unknown> | null;
  queryTemplate: Record<string, unknown> | null;
  bodyTemplate: Record<string, unknown> | null;
  contentType: string;
  auth: {
    authType: ToolAuthType;
    secretValue: string | null;
    headerName: string | null;
    queryName: string | null;
  };
  parameters: ToolParameterRecord[];
  openapiSource: Record<string, unknown> | null;
  metadata: Record<string, unknown> | null;
}

export interface OpenApiPreviewResult {
  draft: OpenApiToolDraft;
  warnings: string[];
}

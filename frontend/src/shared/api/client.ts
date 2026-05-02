import { getApiBasePath } from "@/shared/config/env";
import { AppBusinessError, AppRequestError, AppResponseFormatError } from "@/shared/api/errors";
import type {
  ApiResponseEnvelope,
  ParsedRequestDescriptor,
  QueryParams,
  RequestDescriptor,
} from "@/shared/api/types";

function parseRequestDescriptor(request: string): ParsedRequestDescriptor {
  const [method = "", ...pathParts] = request.trim().split(/\s+/);
  const path = pathParts.join(" ");

  if (method === "" || path === "") {
    throw new AppRequestError(`非法请求描述: ${request}`);
  }

  return {
    method: method.toUpperCase() as ParsedRequestDescriptor["method"],
    path,
  };
}

function normalizePath(path: string): string {
  if (path.startsWith("/api/")) {
    return path;
  }

  if (path.startsWith("/")) {
    return `${getApiBasePath()}${path}`;
  }

  return `${getApiBasePath()}/${path}`;
}

function replacePathParams(path: string, pathParams: RequestDescriptor["pathParams"]): string {
  if (pathParams === undefined) {
    return path;
  }

  return path.replace(/{(\w+)}/g, (_placeholder, key: string) => {
    const value = pathParams[key];

    if (value === undefined) {
      throw new AppRequestError(`缺少路径参数: ${key}`);
    }

    return encodeURIComponent(String(value));
  });
}

function appendQueryParams(path: string, query: QueryParams | undefined): string {
  if (query === undefined) {
    return path;
  }

  const searchParams = new URLSearchParams();

  for (const [key, value] of Object.entries(query)) {
    if (value === null || value === undefined) {
      continue;
    }

    if (Array.isArray(value)) {
      value.forEach((entry) => {
        searchParams.append(key, String(entry));
      });
      continue;
    }

    searchParams.append(key, String(value));
  }

  const queryString = searchParams.toString();

  if (queryString === "") {
    return path;
  }

  return `${path}?${queryString}`;
}

function buildBody(body: RequestDescriptor["body"]): BodyInit | null | undefined {
  if (body === undefined || body === null) {
    return body;
  }

  if (body instanceof FormData || body instanceof URLSearchParams) {
    return body;
  }

  if (typeof body === "string" || body instanceof Blob) {
    return body;
  }

  return JSON.stringify(body);
}

function buildHeaders(headers: HeadersInit | undefined, body: RequestDescriptor["body"]): Headers {
  const finalHeaders = new Headers(headers);

  if (
    body !== undefined &&
    body !== null &&
    !(body instanceof FormData) &&
    !(body instanceof URLSearchParams) &&
    typeof body !== "string" &&
    !finalHeaders.has("Content-Type")
  ) {
    finalHeaders.set("Content-Type", "application/json");
  }

  return finalHeaders;
}

export async function request<T>(descriptor: RequestDescriptor): Promise<T> {
  const { method, path } = parseRequestDescriptor(descriptor.request);
  const resolvedPath = replacePathParams(normalizePath(path), descriptor.pathParams);
  const requestUrl = appendQueryParams(resolvedPath, descriptor.query);

  let response: Response;

  try {
    response = await fetch(requestUrl, {
      ...descriptor.init,
      method,
      body: buildBody(descriptor.body),
      headers: buildHeaders(descriptor.headers, descriptor.body),
      signal: descriptor.signal,
    });
  } catch (error) {
    if (error instanceof Error) {
      throw new AppRequestError(error.message);
    }

    throw new AppRequestError("网络请求失败");
  }

  let payload: ApiResponseEnvelope<T> | null;

  try {
    payload = (await response.json()) as ApiResponseEnvelope<T> | null;
  } catch {
    throw new AppResponseFormatError("后端返回了无法识别的响应结构", response.status);
  }

  if (payload === null || typeof payload !== "object" || typeof payload.code !== "number") {
    throw new AppResponseFormatError("后端返回了无法识别的响应结构", response.status);
  }

  if (!response.ok || payload.code !== 200) {
    throw new AppBusinessError(payload.message || "请求失败", payload.code, response.status);
  }

  return payload.data;
}

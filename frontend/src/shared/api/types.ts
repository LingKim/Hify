import type { ResultEnvelope } from "@/shared/types/http";

export type HttpMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";

export type PrimitiveQueryValue = string | number | boolean;

export type QueryValue = PrimitiveQueryValue | PrimitiveQueryValue[] | null | undefined;

export type QueryParams = Record<string, QueryValue>;

export type PathParams = Record<string, string | number>;

export interface RequestDescriptor {
  request: `${HttpMethod} ${string}`;
  pathParams?: PathParams;
  query?: QueryParams;
  body?: BodyInit | object | null;
  headers?: HeadersInit;
  signal?: AbortSignal;
  init?: Omit<RequestInit, "method" | "body" | "headers" | "signal">;
}

export interface ParsedRequestDescriptor {
  method: HttpMethod;
  path: string;
}

export type ApiResponseEnvelope<T> = ResultEnvelope<T>;

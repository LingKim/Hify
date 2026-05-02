import { request } from "@/shared/api";
import { healthApi } from "@/domain/health/api";
import type { HealthSnapshot, HealthStatus } from "@/domain/health/types";

function buildSnapshot(status: string): HealthSnapshot {
  return {
    module: "backend-health",
    status,
    requestedAt: new Date().toLocaleString("zh-CN", {
      hour12: false,
    }),
  };
}

export async function fetchHealthStatus(signal?: AbortSignal): Promise<HealthStatus> {
  return request<HealthStatus>({
    request: healthApi.getHealthStatus,
    signal,
  });
}

export async function fetchHealthSnapshot(signal?: AbortSignal): Promise<HealthSnapshot> {
  const response = await fetchHealthStatus(signal);
  return buildSnapshot(response.status);
}

export interface HealthStatus {
  status: string;
}

export interface HealthSnapshot {
  module: string;
  requestedAt: string;
  status: string;
}

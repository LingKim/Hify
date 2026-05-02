export interface ResultEnvelope<T> {
  code: number;
  message: string;
  data: T;
}

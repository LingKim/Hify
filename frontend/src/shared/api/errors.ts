export class AppRequestError extends Error {
  public readonly status: number;

  public constructor(message: string, status = 500) {
    super(message);
    this.name = "AppRequestError";
    this.status = status;
  }
}

export class AppBusinessError extends AppRequestError {
  public readonly code: number;

  public constructor(message: string, code: number, status: number) {
    super(message, status);
    this.name = "AppBusinessError";
    this.code = code;
  }
}

export class AppResponseFormatError extends AppRequestError {
  public constructor(message: string, status = 500) {
    super(message, status);
    this.name = "AppResponseFormatError";
  }
}

export function getErrorMessage(error: unknown): string {
  if (error instanceof AppBusinessError) {
    return `${error.message}（code: ${error.code}）`;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "请求失败，请稍后重试。";
}

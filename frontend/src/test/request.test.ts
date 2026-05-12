import { AppBusinessError } from "@/shared/api/errors";
import { request } from "@/shared/api";
import { ACCESS_TOKEN_STORAGE_KEY } from "@/shared/auth/token";

describe("request", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    window.localStorage.clear();
  });

  it("returns the data field when the backend responds successfully", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          code: 200,
          message: "success",
          data: { status: "ok" },
        }),
        {
          status: 200,
          headers: { "Content-Type": "application/json" },
        },
      ),
    );

    await expect(
      request<{ status: string }>({
        request: "GET /health",
      }),
    ).resolves.toEqual({ status: "ok" });
  });

  it("throws a domain error when the backend returns a business error", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          code: 4001,
          message: "Agent 不存在",
          data: null,
        }),
        {
          status: 404,
          headers: { "Content-Type": "application/json" },
        },
      ),
    );

    await expect(
      request({
        request: "GET /health",
      }),
    ).rejects.toBeInstanceOf(AppBusinessError);
  });

  it("accepts 201 responses as success", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          code: 201,
          message: "success",
          data: { id: 1 },
        }),
        {
          status: 201,
          headers: { "Content-Type": "application/json" },
        },
      ),
    );

    await expect(
      request<{ id: number }>({
        request: "POST /providers",
        body: { name: "OpenAI" },
      }),
    ).resolves.toEqual({ id: 1 });
  });

  it("accepts 204 responses without a JSON body", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(null, {
        status: 204,
      }),
    );

    await expect(
      request<void>({
        request: "DELETE /providers/1",
      }),
    ).resolves.toBeUndefined();
  });

  it("replaces path params and appends query params", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          code: 200,
          message: "success",
          data: { ok: true },
        }),
        {
          status: 200,
          headers: { "Content-Type": "application/json" },
        },
      ),
    );

    await request<{ ok: boolean }>({
      request: "GET /users/{id}",
      pathParams: {
        id: "42",
      },
      query: {
        page: 2,
        keyword: "hify",
      },
    });

    expect(fetchSpy).toHaveBeenCalledWith(
      "/api/v1/users/42?page=2&keyword=hify",
      expect.objectContaining({
        method: "GET",
      }),
    );
  });

  it("sends the stored access token as a bearer token", async () => {
    window.localStorage.setItem(ACCESS_TOKEN_STORAGE_KEY, "stored-token");
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          code: 200,
          message: "success",
          data: { ok: true },
        }),
        {
          status: 200,
          headers: { "Content-Type": "application/json" },
        },
      ),
    );

    await request<{ ok: boolean }>({
      request: "GET /users",
    });

    const headers = fetchSpy.mock.calls[0]?.[1]?.headers;
    expect(headers).toBeInstanceOf(Headers);
    expect((headers as Headers).get("Authorization")).toBe(
      "Bearer stored-token",
    );
  });
});

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import type { PropsWithChildren } from "react";
import { useHealthQuery } from "@/domain/health/queries";

function createWrapper(client: QueryClient) {
  return function Wrapper({ children }: PropsWithChildren): JSX.Element {
    return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
  };
}

describe("useHealthQuery", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("returns the formatted health snapshot", async () => {
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

    const client = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    });

    const { result } = renderHook(() => useHealthQuery(), {
      wrapper: createWrapper(client),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toMatchObject({
      module: "backend-health",
      status: "ok",
    });
  });
});

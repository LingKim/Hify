import { render, screen, within } from "@testing-library/react";
import { MarkdownRenderer } from "@/shared/ui";

describe("MarkdownRenderer", () => {
  it("renders common LLM markdown without injecting raw HTML", () => {
    const { container } = render(
      <MarkdownRenderer
        content={[
          "## 结论",
          "",
          "- 支持 **重点**",
          "- 支持 `inline code`",
          "",
          "```ts",
          "const ok = true;",
          "```",
          "",
          "| 字段 | 说明 |",
          "| --- | --- |",
          "| role | assistant |",
          "",
          "[来源](https://example.com)",
          "",
          "<script>alert('xss')</script>",
        ].join("\n")}
      />,
    );

    expect(
      screen.getByRole("heading", { name: "结论", level: 2 }),
    ).toBeInTheDocument();
    expect(screen.getByText("重点").tagName).toBe("STRONG");
    expect(screen.getByText("inline code").tagName).toBe("CODE");

    const codeBlock = screen.getByText("const ok = true;");
    expect(codeBlock.closest("pre")).toBeInTheDocument();

    const table = screen.getByRole("table");
    expect(within(table).getByText("role")).toBeInTheDocument();
    expect(within(table).getByText("assistant")).toBeInTheDocument();

    const link = screen.getByRole("link", { name: "来源" });
    expect(link).toHaveAttribute("href", "https://example.com");
    expect(link).toHaveAttribute("target", "_blank");
    expect(link).toHaveAttribute("rel", "noreferrer");

    expect(container.querySelector("script")).not.toBeInTheDocument();
    expect(screen.getByText(/alert\('xss'\)/)).toBeInTheDocument();
  });
});

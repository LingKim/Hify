import { render, screen, within } from "@testing-library/react";
import { Button } from "antd";
import { FrameView } from "@/shared/ui";

describe("FrameView", () => {
  it("renders content without a header block when only filter and content are provided", () => {
    render(
      <FrameView filter={<div>筛选区域</div>}>
        <div>列表内容</div>
      </FrameView>,
    );

    expect(screen.getByText("筛选区域")).toBeInTheDocument();
    expect(screen.getByText("列表内容")).toBeInTheDocument();
    expect(screen.queryByTestId("frame-view-header")).not.toBeInTheDocument();
  });

  it("renders every optional section in the expected order", () => {
    render(
      <FrameView
        title="页面标题"
        description="页面说明"
        headerExtra={<Button>新增</Button>}
        toolbar={<div>工具栏</div>}
        filter={<div>筛选区域</div>}
        alert={<div>提示区域</div>}
        footer={<div>页脚说明</div>}
      >
        <div>主体内容</div>
      </FrameView>,
    );

    const header = screen.getByTestId("frame-view-header");
    const toolbar = screen.getByTestId("frame-view-toolbar");
    const filter = screen.getByTestId("frame-view-filter");
    const alert = screen.getByTestId("frame-view-alert");
    const content = screen.getByTestId("frame-view-content");
    const footer = screen.getByTestId("frame-view-footer");

    expect(header).toHaveTextContent("页面标题");
    expect(header).toHaveTextContent("页面说明");
    expect(within(header).getByRole("button", { name: /新\s*增/ })).toBeInTheDocument();

    expect(toolbar.compareDocumentPosition(filter)).toBe(Node.DOCUMENT_POSITION_FOLLOWING);
    expect(filter.compareDocumentPosition(alert)).toBe(Node.DOCUMENT_POSITION_FOLLOWING);
    expect(alert.compareDocumentPosition(content)).toBe(Node.DOCUMENT_POSITION_FOLLOWING);
    expect(content.compareDocumentPosition(footer)).toBe(Node.DOCUMENT_POSITION_FOLLOWING);
  });
});

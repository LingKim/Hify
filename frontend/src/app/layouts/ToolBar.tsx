import { SettingOutlined } from "@ant-design/icons";
import { Breadcrumb, Button, Tooltip } from "antd";
import { useLocation } from "react-router-dom";
import { useAppStore } from "@/shared/stores/app";

function buildBreadcrumb(pathname: string): { title: string }[] {
  if (pathname === "/providers") {
    return [{ title: "运营后台" }, { title: "模型提供商管理" }];
  }
  if (pathname === "/agents") {
    return [{ title: "运营后台" }, { title: "Agent 配置" }];
  }
  if (pathname === "/tools") {
    return [{ title: "运营后台" }, { title: "工具集成" }];
  }
  if (pathname === "/users") {
    return [{ title: "运营后台" }, { title: "用户管理" }];
  }
  if (pathname === "/conversations") {
    return [{ title: "运营后台" }, { title: "会话日志" }];
  }
  if (pathname === "/chat") {
    return [{ title: "应用" }, { title: "对话使用" }];
  }
  if (pathname === "/playground/api-preview") {
    return [{ title: "Playground" }, { title: "联调预览" }];
  }
  if (pathname === "/playground/common-components") {
    return [{ title: "Playground" }, { title: "公共组件" }];
  }
  if (pathname === "/") {
    return [{ title: "首页" }];
  }
  return [{ title: "未知页面" }];
}

export function ToolBar(): JSX.Element {
  const location = useLocation();
  const openPreferencesDrawer = useAppStore((s) => s.openPreferencesDrawer);

  return (
    <div className="tool-bar">
      <Breadcrumb items={buildBreadcrumb(location.pathname)} />
      <div className="tool-bar-actions">
        <Tooltip title="界面设置">
          <Button
            type="text"
            size="small"
            icon={<SettingOutlined />}
            aria-label="打开界面设置"
            onClick={() => openPreferencesDrawer()}
          />
        </Tooltip>
      </div>
    </div>
  );
}

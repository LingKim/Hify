import { SettingOutlined } from "@ant-design/icons";
import { Breadcrumb, Button, Tooltip } from "antd";
import { useLocation } from "react-router-dom";
import { useAppStore } from "@/shared/stores/app";

function buildBreadcrumb(pathname: string): { title: string }[] {
  if (pathname === "/playground/api-preview") {
    return [{ title: "Playground" }, { title: "联调预览" }];
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
            onClick={() => openPreferencesDrawer()}
          />
        </Tooltip>
      </div>
    </div>
  );
}

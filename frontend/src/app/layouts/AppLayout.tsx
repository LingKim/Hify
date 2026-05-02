import {
  ApiOutlined,
  HomeOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  RocketOutlined,
} from "@ant-design/icons";
import { Layout, Menu, Space, Typography } from "antd";
import type { ItemType } from "antd/es/menu/interface";
import { useEffect } from "react";
import { Outlet, useLocation, useNavigate } from "react-router-dom";
import { PreferencesDrawer } from "@/app/preferences/PreferencesDrawer";
import { useAppStore } from "@/shared/stores/app";
import { useTagsStore } from "@/shared/stores/tags";
import { TagViews } from "./TagViews";
import { ToolBar } from "./ToolBar";

const navigationItems: ItemType[] = [
  {
    key: "/",
    icon: <HomeOutlined />,
    label: "首页",
  },
  {
    key: "/playground/api-preview",
    icon: <ApiOutlined />,
    label: "联调预览",
  },
];

const routeTitleMap: Record<string, string> = {
  "/": "首页",
  "/playground/api-preview": "联调预览",
};

export function AppLayout(): JSX.Element {
  const navigate = useNavigate();
  const location = useLocation();
  const siderCollapsed = useAppStore((s) => s.siderCollapsed);
  const toggleSiderCollapsed = useAppStore((s) => s.toggleSiderCollapsed);
  const addTab = useTagsStore((s) => s.addTab);

  useEffect(() => {
    const title = routeTitleMap[location.pathname] ?? "未知页面";
    addTab({
      key: location.pathname,
      title,
      closable: location.pathname !== "/",
    });
  }, [location.pathname, addTab]);

  return (
    <Layout className="app-shell">
      <Layout.Sider
        className="app-sider"
        collapsed={siderCollapsed}
        collapsedWidth={88}
        width={248}
      >
        <div className="sider-body">
          <BrandBlock collapsed={siderCollapsed} />
          <Menu
            className="app-nav"
            mode="inline"
            selectedKeys={[location.pathname]}
            items={navigationItems}
            onClick={({ key }) => {
              navigate(key);
            }}
          />
        </div>
        <div className="sider-footer">
          <button
            className="sider-toggle"
            onClick={() => toggleSiderCollapsed()}
            aria-label={siderCollapsed ? "展开侧栏" : "收起侧栏"}
          >
            {siderCollapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
          </button>
        </div>
      </Layout.Sider>
      <Layout className="app-main">
        <TagViews />
        <ToolBar />
        <Layout.Content className="app-content">
          <Outlet />
        </Layout.Content>
      </Layout>
      <PreferencesDrawer />
    </Layout>
  );
}

function BrandBlock({ collapsed }: { collapsed: boolean }): JSX.Element {
  return (
    <div className={`brand-panel${collapsed ? " brand-panel-collapsed" : ""}`}>
      <Space
        align="center"
        size={12}
        className={`brand-stack${collapsed ? " brand-stack-collapsed" : ""}`}
      >
        <div className="brand-mark">
          <RocketOutlined />
        </div>
        {!collapsed ? (
          <div className="brand-copy">
            <Typography.Title className="brand-title" level={4}>
              Hify
            </Typography.Title>
            <Typography.Text className="brand-subtitle">
              AI Agent 开发平台
            </Typography.Text>
          </div>
        ) : null}
      </Space>
    </div>
  );
}

import {
  ApiOutlined,
  HomeOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  RocketOutlined,
  SettingOutlined,
} from "@ant-design/icons";
import { Breadcrumb, Button, Layout, Menu, Space, Tooltip, Typography } from "antd";
import type { ItemType } from "antd/es/menu/interface";
import { Outlet, useLocation, useNavigate } from "react-router-dom";
import { PreferencesDrawer } from "@/app/preferences/PreferencesDrawer";
import { useAppStore } from "@/shared/stores/app";

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

function buildBreadcrumb(pathname: string): { title: string }[] {
  if (pathname === "/playground/api-preview") {
    return [{ title: "Playground" }, { title: "联调预览" }];
  }

  if (pathname === "/") {
    return [{ title: "首页" }];
  }

  return [{ title: "未知页面" }];
}

export function AppLayout(): JSX.Element {
  const navigate = useNavigate();
  const location = useLocation();
  const siderCollapsed = useAppStore((state) => state.siderCollapsed);
  const toggleSiderCollapsed = useAppStore((state) => state.toggleSiderCollapsed);
  const navigationMode = useAppStore((state) => state.navigationMode);
  const openPreferencesDrawer = useAppStore((state) => state.openPreferencesDrawer);

  const navigationMenu = (
    <Menu
      className={`app-nav${navigationMode === "top" ? " app-nav-top" : ""}`}
      mode={navigationMode === "top" ? "horizontal" : "inline"}
      selectedKeys={[location.pathname]}
      items={navigationItems}
      onClick={({ key }) => {
        navigate(key);
      }}
    />
  );

  const topBarActions = (
    <div className="header-actions">
      {navigationMode === "side" ? (
        <Button
          type="primary"
          icon={siderCollapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
          onClick={() => {
            toggleSiderCollapsed();
          }}
        >
          {siderCollapsed ? "展开侧栏" : "收起侧栏"}
        </Button>
      ) : null}
      <Tooltip title="界面设置">
        <Button
          aria-label="打开界面设置"
          className="settings-trigger"
          icon={<SettingOutlined />}
          onClick={() => {
            openPreferencesDrawer();
          }}
        />
      </Tooltip>
    </div>
  );

  return (
    <Layout className="app-shell">
      {navigationMode === "side" ? (
        <Layout.Sider
          className="app-sider"
          collapsed={siderCollapsed}
          collapsedWidth={88}
          width={248}
        >
          <BrandBlock collapsed={siderCollapsed} />
          {navigationMenu}
        </Layout.Sider>
      ) : null}
      <Layout>
        <Layout.Header className={`app-header${navigationMode === "top" ? " app-header-top" : ""}`}>
          {navigationMode === "top" ? (
            <div className="top-nav-shell">
              <BrandBlock collapsed={false} compact />
              <div className="top-nav-menu">{navigationMenu}</div>
              {topBarActions}
            </div>
          ) : (
            <>
              <div>
                <Typography.Text className="header-kicker">Hify Frontend Scaffold</Typography.Text>
                <Typography.Title className="header-title" level={3}>
                  面向长期演进的前端底座
                </Typography.Title>
              </div>
              {topBarActions}
            </>
          )}
        </Layout.Header>
        {navigationMode === "top" ? (
          <div className="page-heading">
            <Typography.Text className="header-kicker">Hify Frontend Scaffold</Typography.Text>
            <Typography.Title className="header-title" level={3}>
              面向长期演进的前端底座
            </Typography.Title>
          </div>
        ) : null}
        <Layout.Content className="app-content">
          <Breadcrumb items={buildBreadcrumb(location.pathname)} />
          <div className="app-content-panel">
            <Outlet />
          </div>
        </Layout.Content>
      </Layout>
      <PreferencesDrawer />
    </Layout>
  );
}

interface BrandBlockProps {
  collapsed: boolean;
  compact?: boolean;
}

function BrandBlock({ collapsed, compact = false }: BrandBlockProps): JSX.Element {
  return (
    <div
      className={`brand-panel${collapsed ? " brand-panel-collapsed" : ""}${
        compact ? " brand-panel-compact" : ""
      }`}
    >
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
            <Typography.Text className="brand-subtitle">AI Agent 开发平台</Typography.Text>
          </div>
        ) : null}
      </Space>
    </div>
  );
}

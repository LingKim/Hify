import {
  ApiOutlined,
  AppstoreOutlined,
  BookOutlined,
  CommentOutlined,
  ToolOutlined,
  HomeOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  ProfileOutlined,
  RobotOutlined,
  SafetyCertificateOutlined,
  UserOutlined,
} from "@ant-design/icons";
import { Layout, Menu } from "antd";
import type { ItemType } from "antd/es/menu/interface";
import { useEffect } from "react";
import { Outlet, useLocation, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { currentUserQueryOptions } from "@/domain/auth/queries";
import {
  hasAnyPermission,
  routePermissionMap,
} from "@/domain/auth/permissions";
import { PreferencesDrawer } from "@/app/preferences/PreferencesDrawer";
import { getAccessToken } from "@/shared/auth/token";
import { useAppStore } from "@/shared/stores/app";
import { useTagsStore } from "@/shared/stores/tags";
import { HeaderBar } from "./HeaderBar";
import { ToolBar } from "./ToolBar";

const VERSION = "v0.1.0";

const navigationItems: ItemType[] = [
  {
    key: "/",
    icon: <HomeOutlined />,
    label: "首页",
  },
  {
    key: "/providers",
    icon: <RobotOutlined />,
    label: "模型提供商",
  },
  {
    key: "/agents",
    icon: <RobotOutlined />,
    label: "Agent 配置",
  },
  {
    key: "/tools",
    icon: <ToolOutlined />,
    label: "工具集成",
  },
  {
    key: "/knowledge",
    icon: <BookOutlined />,
    label: "知识库",
  },
  {
    key: "/chat",
    icon: <CommentOutlined />,
    label: "对话使用",
  },
  {
    key: "/conversations",
    icon: <ProfileOutlined />,
    label: "会话日志",
  },
  {
    key: "/users",
    icon: <UserOutlined />,
    label: "用户管理",
  },
  {
    key: "/rbac",
    icon: <SafetyCertificateOutlined />,
    label: "权限管理",
  },
  {
    key: "/playground/api-preview",
    icon: <ApiOutlined />,
    label: "联调预览",
  },
  {
    key: "/playground/common-components",
    icon: <AppstoreOutlined />,
    label: "公共组件",
  },
];

function filterNavigationItems(
  items: ItemType[],
  permissions: string[] | undefined,
): ItemType[] {
  return items.filter((item) => {
    if (item == null || !("key" in item)) {
      return item != null;
    }
    const routeKey = String(item.key);
    const requiredPermissions = routePermissionMap[routeKey] ?? [];
    return hasAnyPermission(
      permissions == null
        ? undefined
        : {
            id: 0,
            username: "",
            email: "",
            roles: [],
            permissions,
          },
      requiredPermissions,
    );
  });
}

const routeTitleMap: Record<string, string> = {
  "/": "首页",
  "/agents": "Agent 配置",
  "/tools": "工具集成",
  "/knowledge": "知识库",
  "/chat": "对话使用",
  "/conversations": "会话日志",
  "/providers": "模型提供商管理",
  "/users": "用户管理",
  "/rbac": "权限管理",
  "/playground/api-preview": "联调预览",
  "/playground/common-components": "公共组件演示",
};

export function AppLayout(): JSX.Element {
  const navigate = useNavigate();
  const location = useLocation();
  const siderCollapsed = useAppStore((s) => s.siderCollapsed);
  const toggleSiderCollapsed = useAppStore((s) => s.toggleSiderCollapsed);
  const addTab = useTagsStore((s) => s.addTab);
  const currentUserQuery = useQuery(
    currentUserQueryOptions(getAccessToken() !== null),
  );
  const visibleNavigationItems = filterNavigationItems(
    navigationItems,
    currentUserQuery.data?.permissions,
  );

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
        collapsedWidth={72}
        width={240}
      >
        <div className="sider-body">
          <BrandBlock collapsed={siderCollapsed} />
          <Menu
            className="app-nav"
            mode="inline"
            selectedKeys={[location.pathname]}
            items={visibleNavigationItems}
            onClick={({ key }) => {
              navigate(key);
            }}
          />
        </div>
        <div className="sider-footer">
          {!siderCollapsed && <span className="sider-version">{VERSION}</span>}
          <button
            className={`sider-toggle${siderCollapsed ? " sider-toggle-collapsed" : ""}`}
            onClick={() => toggleSiderCollapsed()}
            aria-label={siderCollapsed ? "展开侧栏" : "收起侧栏"}
          >
            {siderCollapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
          </button>
        </div>
      </Layout.Sider>
      <Layout className="app-main">
        <HeaderBar />
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
  if (collapsed) {
    return (
      <div className="brand-panel brand-panel-collapsed">
        <div className="brand-initial">H</div>
      </div>
    );
  }
  return (
    <div className="brand-panel">
      <div className="brand-name">Hify</div>
      <div className="brand-subtitle">AI Agent Platform</div>
    </div>
  );
}

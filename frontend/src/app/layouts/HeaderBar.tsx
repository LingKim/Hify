import { LogoutOutlined, UserOutlined } from "@ant-design/icons";
import { Avatar, Dropdown } from "antd";
import type { MenuProps } from "antd";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { authQueryKeys, currentUserQueryOptions } from "@/domain/auth/queries";
import { clearAccessToken, getAccessToken } from "@/shared/auth/token";
import { TagViews } from "./TagViews";

const userMenuItems: MenuProps["items"] = [
  {
    key: "logout",
    icon: <LogoutOutlined />,
    label: "退出登录",
  },
];

export function HeaderBar(): JSX.Element {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const currentUserQuery = useQuery(
    currentUserQueryOptions(getAccessToken() !== null),
  );
  const currentUser = currentUserQuery.data;
  const username = currentUser?.username ?? "未登录";
  const email = currentUser?.email ?? "请重新登录";
  const handleMenuClick: MenuProps["onClick"] = ({ key }) => {
    if (key !== "logout") {
      return;
    }
    clearAccessToken();
    queryClient.removeQueries({ queryKey: authQueryKeys.all });
    navigate("/login", { replace: true });
  };

  return (
    <div className="header-bar">
      <TagViews />
      <Dropdown
        menu={{ items: userMenuItems, onClick: handleMenuClick }}
        trigger={["hover"]}
        placement="bottomRight"
        popupRender={(menu) => (
          <div className="user-dropdown">
            <div className="user-dropdown-header">
              <Avatar
                size={36}
                icon={<UserOutlined />}
                className="user-dropdown-avatar"
              />
              <div className="user-dropdown-info">
                <div className="user-dropdown-name">{username}</div>
                <div className="user-dropdown-email">{email}</div>
              </div>
            </div>
            <div className="user-dropdown-divider" />
            {menu}
          </div>
        )}
      >
        <div className="header-bar-user">
          <Avatar size={28} icon={<UserOutlined />} />
          <span className="header-bar-username">{username}</span>
        </div>
      </Dropdown>
    </div>
  );
}

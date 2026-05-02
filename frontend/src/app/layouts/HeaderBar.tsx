import { LogoutOutlined, UserOutlined } from "@ant-design/icons";
import { Avatar, Dropdown } from "antd";
import type { MenuProps } from "antd";
import { TagViews } from "./TagViews";

const userMenuItems: MenuProps["items"] = [
  {
    key: "logout",
    icon: <LogoutOutlined />,
    label: "退出登录",
  },
];

export function HeaderBar(): JSX.Element {
  return (
    <div className="header-bar">
      <TagViews />
      <Dropdown
        menu={{ items: userMenuItems }}
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
                <div className="user-dropdown-name">Admin</div>
                <div className="user-dropdown-email">admin@hify.ai</div>
              </div>
            </div>
            <div className="user-dropdown-divider" />
            {menu}
          </div>
        )}
      >
        <div className="header-bar-user">
          <Avatar size={28} icon={<UserOutlined />} />
          <span className="header-bar-username">Admin</span>
        </div>
      </Dropdown>
    </div>
  );
}

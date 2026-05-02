import { SettingOutlined } from "@ant-design/icons";
import { Drawer, Segmented, Space, Typography } from "antd";
import {
  navigationModeItem,
  preferencesSections,
  themePreferenceItem,
  type NavigationMode,
  type ThemePreference,
} from "@/app/preferences/config";
import { useAppStore } from "@/shared/stores/app";

export function PreferencesDrawer(): JSX.Element {
  const isOpen = useAppStore((state) => state.isPreferencesDrawerOpen);
  const closeDrawer = useAppStore((state) => state.closePreferencesDrawer);
  const themePreference = useAppStore((state) => state.themePreference);
  const setThemePreference = useAppStore((state) => state.setThemePreference);
  const navigationMode = useAppStore((state) => state.navigationMode);
  const setNavigationMode = useAppStore((state) => state.setNavigationMode);

  return (
    <Drawer
      title="界面设置"
      placement="right"
      size="large"
      open={isOpen}
      onClose={closeDrawer}
      className="preferences-drawer"
    >
      <div className="preferences-panel">
        <div className="preferences-intro">
          <div className="preferences-mark">
            <SettingOutlined />
          </div>
          <div>
            <Typography.Title level={4}>统一配置中心</Typography.Title>
            <Typography.Paragraph>
              当前可以调整主题模式和菜单模式，后续更多界面配置会继续收敛到这里。
            </Typography.Paragraph>
          </div>
        </div>

        {preferencesSections.map((section) => (
          <section key={section.id} className="preferences-section">
            <Typography.Title level={5}>{section.title}</Typography.Title>

            {section.items.map((item) => {
              if (item.id === themePreferenceItem.id) {
                return (
                  <PreferenceField
                    key={item.id}
                    title={item.title}
                    description={item.description}
                    defaultBehavior={item.defaultBehavior}
                  >
                    <Segmented
                      block
                      value={themePreference}
                      options={themePreferenceItem.options.map((option) => ({
                        label: option.label,
                        value: option.value,
                      }))}
                      onChange={(value) => {
                        setThemePreference(value as ThemePreference);
                      }}
                    />
                  </PreferenceField>
                );
              }

              if (item.id === navigationModeItem.id) {
                return (
                  <PreferenceField
                    key={item.id}
                    title={item.title}
                    description={item.description}
                    defaultBehavior={item.defaultBehavior}
                  >
                    <Segmented
                      block
                      value={navigationMode}
                      options={navigationModeItem.options.map((option) => ({
                        label: option.label,
                        value: option.value,
                      }))}
                      onChange={(value) => {
                        setNavigationMode(value as NavigationMode);
                      }}
                    />
                  </PreferenceField>
                );
              }

              return null;
            })}
          </section>
        ))}

        <div className="preferences-extension">
          <Typography.Title level={5}>后续扩展</Typography.Title>
          <Typography.Paragraph>
            这里后续会继续加入自定义主题、信息密度、首页布局偏好等界面配置。
          </Typography.Paragraph>
        </div>
      </div>
    </Drawer>
  );
}

interface PreferenceFieldProps {
  title: string;
  description: string;
  defaultBehavior: string;
  children: React.ReactNode;
}

function PreferenceField({
  title,
  description,
  defaultBehavior,
  children,
}: PreferenceFieldProps): JSX.Element {
  return (
    <div className="preferences-field">
      <Space orientation="vertical" size={10}>
        <div>
          <Typography.Text strong>{title}</Typography.Text>
          <Typography.Paragraph>{description}</Typography.Paragraph>
          <Typography.Text type="secondary">{defaultBehavior}</Typography.Text>
        </div>
        {children}
      </Space>
    </div>
  );
}

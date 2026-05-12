import { LockOutlined, UserOutlined } from "@ant-design/icons";
import { Button, Form, Input, Typography } from "antd";
import type { LoginValues } from "@/domain/auth/types";

interface LoginPanelProps {
  loading: boolean;
  onSubmit: (values: LoginValues) => void;
}

export function LoginPanel({
  loading,
  onSubmit,
}: LoginPanelProps): JSX.Element {
  return (
    <main className="login-page">
      <section className="login-panel" aria-label="登录">
        <div className="login-brand">
          <div className="login-brand-mark">H</div>
          <div>
            <Typography.Title level={1}>登录 Hify</Typography.Title>
            <Typography.Text>进入团队内部 AI Agent 工作台</Typography.Text>
          </div>
        </div>

        <Form<LoginValues>
          className="login-form"
          layout="vertical"
          requiredMark={false}
          onFinish={onSubmit}
        >
          <Form.Item
            name="account"
            label="账号"
            rules={[{ required: true, message: "请输入用户名或邮箱" }]}
          >
            <Input
              autoComplete="username"
              prefix={<UserOutlined />}
              placeholder="用户名或邮箱"
              size="large"
            />
          </Form.Item>
          <Form.Item
            name="password"
            label="密码"
            rules={[{ required: true, message: "请输入登录密码" }]}
          >
            <Input.Password
              autoComplete="current-password"
              prefix={<LockOutlined />}
              placeholder="登录密码"
              size="large"
            />
          </Form.Item>
          <Button
            block
            className="login-submit"
            htmlType="submit"
            loading={loading}
            size="large"
            type="primary"
          >
            登录
          </Button>
        </Form>
      </section>
    </main>
  );
}

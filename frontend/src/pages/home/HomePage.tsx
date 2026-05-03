import { ArrowRightOutlined, LinkOutlined } from "@ant-design/icons";
import { Button, Card, Col, Row, Space, Tag, Typography } from "antd";
import { useNavigate } from "react-router-dom";

const designPrinciples = [
  "app / shared / domain 分层清晰",
  "React Query 管理服务端状态",
  "Zustand 只管理客户端 UI 状态",
];

export function HomePage(): JSX.Element {
  const navigate = useNavigate();

  return (
    <div className="page-stack">
      <Space orientation="vertical" size={12}>
        <Tag color="green">React 18 + Vite 8 + TypeScript</Tag>
        <Typography.Title level={1}>Hify 前端开发底座</Typography.Title>
        <Typography.Paragraph>
          这不是一个空白脚手架，而是一套可直接继续长出业务页面的前端底座。
          当前已经具备应用壳、路由、DDD 目录分层、描述式 fetch 请求层、 React Query
          查询链路，以及最小 Zustand 客户端状态边界。
        </Typography.Paragraph>
        <Space wrap>
          <Button
            type="primary"
            onClick={() => {
              navigate("/providers");
            }}
          >
            进入模型提供商管理
          </Button>
          <Button
            icon={<ArrowRightOutlined />}
            onClick={() => {
              navigate("/playground/api-preview");
            }}
          >
            查看联调页
          </Button>
          <Button
            icon={<LinkOutlined />}
            onClick={() => {
              window.open("/api/v1/health", "_blank", "noopener,noreferrer");
            }}
          >
            直接访问健康检查
          </Button>
        </Space>
      </Space>

      <Row gutter={[20, 20]} className="hero-grid">
        {designPrinciples.map((principle) => (
          <Col key={principle} xs={24} md={8}>
            <Card className="hero-card">
              <Typography.Title level={4}>{principle}</Typography.Title>
              <Typography.Paragraph type="secondary">
                这条约束已经体现在当前项目结构里，后续新增页面和领域模块时可沿用。
              </Typography.Paragraph>
            </Card>
          </Col>
        ))}
      </Row>
    </div>
  );
}

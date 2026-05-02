import { Card, Col, Row, Typography } from "antd";
import { HealthPreviewCard } from "@/domain/health/components";
import { useAppStore } from "@/shared/stores/app";

export function ApiPreviewPage(): JSX.Element {
  const siderCollapsed = useAppStore((state) => state.siderCollapsed);

  return (
    <div className="page-stack">
      <SpaceBlock />
      <Row gutter={[20, 20]}>
        <Col xs={24} xl={16}>
          <HealthPreviewCard />
        </Col>
        <Col xs={24} xl={8}>
          <Card title="当前联调约定">
            <Typography.Paragraph>
              前端请求统一走 `/api` 前缀，由 Vite 代理转发到本地 FastAPI。
            </Typography.Paragraph>
            <Typography.Paragraph>
              `health` 领域现在拆成 `api → service → queries` 三层，组件只消费 React Query
              hook，不再手写请求状态机。
            </Typography.Paragraph>
            <Typography.Paragraph>
              当前侧栏状态来自 Zustand：
              {siderCollapsed ? " 已折叠" : " 已展开"}。
            </Typography.Paragraph>
          </Card>
        </Col>
      </Row>
    </div>
  );
}

function SpaceBlock(): JSX.Element {
  return (
    <div>
      <Typography.Title level={1}>后端联调预览</Typography.Title>
      <Typography.Paragraph>
        这里是前后端联调的第一块落地页面，用来验证开发代理、请求层和错误态展示。
      </Typography.Paragraph>
    </div>
  );
}

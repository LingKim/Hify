import { Alert, Button, Card, Skeleton, Space, Tag, Typography } from "antd";
import { useHealthQuery } from "@/domain/health/queries";
import { getErrorMessage } from "@/shared/api";

export function HealthPreviewCard(): JSX.Element {
  const { data, error, isFetching, isLoading, refetch } = useHealthQuery();

  return (
    <Card
      title="后端联调状态"
      extra={
        <Button onClick={() => void refetch()} loading={isFetching}>
          重新检测
        </Button>
      }
    >
      <div className="status-block">
        <Typography.Paragraph type="secondary">
          该卡片直接请求后端 `/api/v1/health`，用于验证 Vite 代理、
          请求层封装与错误呈现链路是否正常。
        </Typography.Paragraph>

        {isLoading && data == null ? <Skeleton active paragraph={{ rows: 3 }} /> : null}

        {error !== null ? (
          <Alert type="error" showIcon title="联调失败" description={getErrorMessage(error)} />
        ) : null}

        {data != null ? (
          <div className="status-meta">
            <div className="status-item">
              <span className="status-item-label">模块</span>
              <Typography.Text strong>{data.module}</Typography.Text>
            </div>
            <div className="status-item">
              <span className="status-item-label">状态</span>
              <Space>
                <Tag color="success">{data.status}</Tag>
              </Space>
            </div>
            <div className="status-item">
              <span className="status-item-label">最近检测时间</span>
              <Typography.Text>{data.requestedAt}</Typography.Text>
            </div>
          </div>
        ) : null}
      </div>
    </Card>
  );
}

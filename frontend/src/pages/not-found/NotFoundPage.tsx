import { Button, Result } from "antd";
import { useNavigate } from "react-router-dom";

export function NotFoundPage(): JSX.Element {
  const navigate = useNavigate();

  return (
    <div className="not-found">
      <Result
        status="404"
        title="页面不存在"
        subTitle="当前路由没有匹配到页面，请返回首页或前往联调示例页。"
        extra={[
          <Button
            key="home"
            type="primary"
            onClick={() => {
              navigate("/");
            }}
          >
            返回首页
          </Button>,
          <Button
            key="playground"
            onClick={() => {
              navigate("/playground/api-preview");
            }}
          >
            打开联调页
          </Button>,
        ]}
      />
    </div>
  );
}

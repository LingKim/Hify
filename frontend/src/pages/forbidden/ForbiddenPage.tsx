import { Button, Result } from "antd";
import { useNavigate } from "react-router-dom";

export function ForbiddenPage(): JSX.Element {
  const navigate = useNavigate();

  return (
    <div className="not-found">
      <Result
        status="403"
        title="暂无访问权限"
        subTitle="当前账号没有访问该页面所需的权限，请联系管理员调整角色。"
        extra={
          <Button
            type="primary"
            onClick={() => {
              navigate("/");
            }}
          >
            返回首页
          </Button>
        }
      />
    </div>
  );
}

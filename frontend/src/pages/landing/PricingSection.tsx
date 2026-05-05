import { Button } from "antd";
import { CheckOutlined } from "@ant-design/icons";
import {
  ApiOutlined,
  GlobalOutlined,
  AppstoreOutlined,
  CodeOutlined,
  MobileOutlined,
  MessageOutlined,
} from "@ant-design/icons";

interface PricingTier {
  name: string;
  price: string;
  unit: string;
  features: string[];
  featured?: boolean;
  cta: string;
}

const TIERS: PricingTier[] = [
  {
    name: "免费版",
    price: "¥0",
    unit: "/月",
    cta: "免费开始",
    features: [
      "10,000 tokens / 月",
      "3 个 Agent",
      "基础模型访问",
      "社区支持",
    ],
  },
  {
    name: "专业版",
    price: "¥99",
    unit: "/月",
    cta: "立即升级",
    featured: true,
    features: [
      "100,000 tokens / 月",
      "无限 Agent",
      "全模型访问（GPT-4 / Claude）",
      "API 接口访问",
      "知识库 / RAG",
      "优先技术支持",
    ],
  },
  {
    name: "企业版",
    price: "联系销售",
    unit: "",
    cta: "联系我们",
    features: [
      "无限 tokens",
      "自定义模型接入",
      "私有化部署",
      "SLA 服务保障",
      "专属客户经理",
      "定制化培训",
    ],
  },
];

interface Integration {
  icon: JSX.Element;
  label: string;
  soon?: boolean;
}

const INTEGRATIONS: Integration[] = [
  { icon: <ApiOutlined />, label: "REST API" },
  { icon: <GlobalOutlined />, label: "Webhook" },
  { icon: <AppstoreOutlined />, label: "浏览器插件" },
  { icon: <CodeOutlined />, label: "VS Code 扩展" },
  { icon: <MobileOutlined />, label: "移动端 SDK", soon: true },
  { icon: <MessageOutlined />, label: "Slack 集成", soon: true },
];

export function PricingSection(): JSX.Element {
  return (
    <section className="landing-section reveal">
      <div className="landing-container">
        <div className="landing-section-header">
          <h2 className="landing-section-title">简单透明的定价</h2>
          <p className="landing-section-desc">
            从免费版开始，按需升级。无隐藏费用，随时取消
          </p>
        </div>

        <div className="pricing-grid">
          {TIERS.map((tier) => (
            <div
              key={tier.name}
              className={`pricing-card ${tier.featured ? "pricing-card-featured" : ""}`}
            >
              {tier.featured && (
                <span className="pricing-badge">推荐</span>
              )}
              <span className="pricing-name">{tier.name}</span>
              <div>
                <span className="pricing-price">{tier.price}</span>
                {tier.unit && (
                  <span className="pricing-price-unit">{tier.unit}</span>
                )}
              </div>
              <ul className="pricing-features">
                {tier.features.map((f) => (
                  <li key={f} className="pricing-feature">
                    <CheckOutlined className="pricing-feature-icon" />
                    <span>{f}</span>
                  </li>
                ))}
              </ul>
              <div className="pricing-cta">
                <Button
                  type={tier.featured ? "primary" : "default"}
                  block
                  size="large"
                >
                  {tier.cta}
                </Button>
              </div>
            </div>
          ))}
        </div>

        <div style={{ marginTop: 80 }}>
          <div className="landing-section-header">
            <h2 className="landing-section-title">丰富的集成生态</h2>
            <p className="landing-section-desc">
              通过 API 和集成，将 AI 写作能力嵌入你的工作流
            </p>
          </div>
          <div className="integration-grid">
            {INTEGRATIONS.map((intg) => (
              <div key={intg.label} className="integration-item">
                <span className="integration-icon">{intg.icon}</span>
                <span>{intg.label}</span>
                {intg.soon && <span className="integration-soon">即将上线</span>}
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

import { Button } from "antd";
import { ArrowRightOutlined, PlayCircleOutlined } from "@ant-design/icons";

export function HeroSection(): JSX.Element {
  const scrollToDemo = () => {
    document.getElementById("demo")?.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <section className="hero-section">
      <span className="hero-badge">
        <span className="hero-badge-dot" />
        AI-powered Writing Platform
      </span>

      <h1 className="hero-title">
        <span className="hero-title-gradient">AI 驱动的</span>
        <br />
        智能写作平台
      </h1>

      <p className="hero-subtitle">
        让 AI 成为你的写作伙伴。从构思到成稿，从博客到报告，
        Hify 帮助你大幅提升创作效率，释放内容生产力。
      </p>

      <div className="hero-actions">
        <Button type="primary" size="large" icon={<ArrowRightOutlined />}>
          免费开始
        </Button>
        <Button size="large" icon={<PlayCircleOutlined />} onClick={scrollToDemo}>
          观看演示
        </Button>
      </div>
    </section>
  );
}

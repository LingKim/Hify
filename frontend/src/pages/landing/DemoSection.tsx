import { useEffect, useState } from "react";
import { UserOutlined, ThunderboltOutlined } from "@ant-design/icons";

interface DemoScenario {
  prompt: string;
  response: string;
}

const SCENARIOS: DemoScenario[] = [
  {
    prompt: "帮我写一篇关于 AI 技术趋势的文章大纲",
    response: `好的，以下是为您准备的文章大纲：

## 2026 AI 技术趋势分析

### 1. 大语言模型的演进
从参数规模到推理能力，模型正变得更智能、更高效

### 2. AI Agent 的商业化落地
自主决策、工具调用、工作流编排，Agent 正在改变工作方式

### 3. 多模态融合
文本、图像、语音、视频的统一理解与生成`,
  },
  {
    prompt: "帮我起草一封项目进展邮件",
    response: `好的，已为您生成邮件草稿：

主题：Q2 项目进展更新

Hi 团队，

本周项目进展顺利，以下是关键更新：

1. 前端重构已完成 85%，预计下周完成
2. API 性能优化后响应时间降低了 40%
3. 用户测试反馈积极，NPS 评分提升 12 分

如有问题请随时沟通。`,
  },
  {
    prompt: "为新产品写一段营销文案",
    response: `好的，以下是为您撰写的营销文案：

释放 AI 的无限可能

用智能对话重新定义工作方式。从灵感到成品，只需一次对话。

  10x 效率提升 — 自动化重复性写作任务
  精准内容生成 — 理解上下文，输出专业内容
  多场景覆盖 — 邮件、报告、文案一站搞定

立即体验，让 AI 成为您的写作伙伴。`,
  },
];

export function DemoSection(): JSX.Element {
  const [scenarioIndex, setScenarioIndex] = useState(0);
  const [displayedText, setDisplayedText] = useState("");
  const [isTyping, setIsTyping] = useState(false);

  useEffect(() => {
    const current = SCENARIOS[scenarioIndex];
    if (!current) return;

    let alive = true;

    const run = async () => {
      setDisplayedText("");
      setIsTyping(false);

      await pause(1200);
      if (!alive) return;

      setIsTyping(true);

      for (let i = 0; i <= current.response.length; i++) {
        if (!alive) return;
        setDisplayedText(current.response.slice(0, i));
        await pause(18);
      }

      setIsTyping(false);

      await pause(3500);
      if (!alive) return;

      setScenarioIndex((prev) => (prev + 1) % SCENARIOS.length);
    };

    run();

    return () => {
      alive = false;
    };
  }, [scenarioIndex]);

  const scenario = SCENARIOS[scenarioIndex];

  return (
    <section className="landing-section reveal" id="demo">
      <div className="landing-container">
        <div className="landing-section-header">
          <h2 className="landing-section-title">实时写作演示</h2>
          <p className="landing-section-desc">
            看看 AI 如何在几秒内生成高质量内容，支持多种写作场景
          </p>
        </div>

        <div className="demo-editor">
          <div className="demo-editor-bar">
            <span className="demo-editor-dot" />
            <span className="demo-editor-dot" />
            <span className="demo-editor-dot" />
            <span className="demo-editor-title">Hify AI Writer</span>
          </div>

          <div className="demo-editor-body">
            {scenario && (
              <>
                <div className="demo-message">
                  <span className="demo-avatar demo-avatar-user">
                    <UserOutlined />
                  </span>
                  <div className="demo-bubble demo-bubble-user">
                    {scenario.prompt}
                  </div>
                </div>

                <div className="demo-message">
                  <span className="demo-avatar demo-avatar-ai">
                    <ThunderboltOutlined />
                  </span>
                  <div className="demo-bubble demo-bubble-ai">
                    <span className="demo-response">
                      {displayedText}
                      {isTyping && <span className="typing-cursor" />}
                    </span>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}

function pause(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

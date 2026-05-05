import {
  EditOutlined,
  MailOutlined,
  SoundOutlined,
  CodeOutlined,
  BarChartOutlined,
  BulbOutlined,
} from "@ant-design/icons";

interface UseCase {
  icon: JSX.Element;
  title: string;
  description: string;
}

const USE_CASES: UseCase[] = [
  {
    icon: <EditOutlined />,
    title: "博客与文章",
    description: "AI 辅助生成文章大纲、润色段落、优化 SEO 关键词，让创作更高效",
  },
  {
    icon: <MailOutlined />,
    title: "商务邮件",
    description: "快速起草专业邮件和商务回复，调整语气风格，提升沟通效率",
  },
  {
    icon: <SoundOutlined />,
    title: "营销文案",
    description: "广告语、产品描述、社交媒体内容，多风格多语言一键生成",
  },
  {
    icon: <CodeOutlined />,
    title: "技术文档",
    description: "API 文档、代码注释、技术博客，让技术写作不再枯燥",
  },
  {
    icon: <BarChartOutlined />,
    title: "报告生成",
    description: "商业报告、会议纪要、数据分析摘要，结构化输出专业内容",
  },
  {
    icon: <BulbOutlined />,
    title: "创意写作",
    description: "故事创作、头脑风暴、内容策划，激发无限创意灵感",
  },
];

export function UseCasesSection(): JSX.Element {
  return (
    <section className="landing-section reveal">
      <div className="landing-container">
        <div className="landing-section-header">
          <h2 className="landing-section-title">覆盖多种写作场景</h2>
          <p className="landing-section-desc">
            无论你是内容创作者、产品经理还是工程师，Hify 都能满足你的写作需求
          </p>
        </div>

        <div className="usecase-grid">
          {USE_CASES.map((uc) => (
            <div key={uc.title} className="usecase-card">
              <span className="usecase-icon">{uc.icon}</span>
              <span className="usecase-title">{uc.title}</span>
              <span className="usecase-desc">{uc.description}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

export function FooterSection(): JSX.Element {
  return (
    <footer className="landing-footer">
      <div className="landing-container">
        <div className="landing-footer-inner">
          <span className="landing-footer-brand">
            Hify &copy; 2026 &mdash; AI Agent 开发平台
          </span>
          <div className="landing-footer-links">
            <a className="landing-footer-link" href="/docs">
              帮助文档
            </a>
            <a className="landing-footer-link" href="/api">
              API 文档
            </a>
            <a className="landing-footer-link" href="/terms">
              使用条款
            </a>
            <a className="landing-footer-link" href="/privacy">
              隐私政策
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}

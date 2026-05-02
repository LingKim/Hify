import { Typography } from "antd";
import type { ReactNode } from "react";

export interface FrameViewProps {
  title?: ReactNode;
  description?: ReactNode;
  headerExtra?: ReactNode;
  toolbar?: ReactNode;
  filter?: ReactNode;
  alert?: ReactNode;
  footer?: ReactNode;
  children: ReactNode;
}

export function FrameView({
  title,
  description,
  headerExtra,
  toolbar,
  filter,
  alert,
  footer,
  children,
}: FrameViewProps): JSX.Element {
  const hasHeader = title !== undefined || description !== undefined || headerExtra !== undefined;

  return (
    <div className="frame-view">
      {hasHeader ? (
        <section className="frame-view-header" data-testid="frame-view-header">
          <div className="frame-view-header-main">
            {title !== undefined ? (
              <Typography.Title level={2} className="frame-view-title">
                {title}
              </Typography.Title>
            ) : null}
            {description !== undefined ? (
              <Typography.Paragraph className="frame-view-description">
                {description}
              </Typography.Paragraph>
            ) : null}
          </div>
          {headerExtra !== undefined ? (
            <div className="frame-view-header-extra">{headerExtra}</div>
          ) : null}
        </section>
      ) : null}

      {toolbar !== undefined ? (
        <section className="frame-view-section" data-testid="frame-view-toolbar">
          {toolbar}
        </section>
      ) : null}

      {filter !== undefined ? (
        <section className="frame-view-section" data-testid="frame-view-filter">
          {filter}
        </section>
      ) : null}

      {alert !== undefined ? (
        <section className="frame-view-section" data-testid="frame-view-alert">
          {alert}
        </section>
      ) : null}

      <section className="frame-view-section" data-testid="frame-view-content">
        {children}
      </section>

      {footer !== undefined ? (
        <section className="frame-view-section" data-testid="frame-view-footer">
          {footer}
        </section>
      ) : null}
    </div>
  );
}

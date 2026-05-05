import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "antd";
import { SunOutlined, MoonOutlined } from "@ant-design/icons";
import { useAppStore } from "@/shared/stores/app";
import { HeroSection } from "./HeroSection";
import { DemoSection } from "./DemoSection";
import { UseCasesSection } from "./UseCasesSection";
import { PricingSection } from "./PricingSection";
import { FooterSection } from "./FooterSection";
import "./landing.css";

export function LandingPage(): JSX.Element {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            entry.target.classList.add("reveal-visible");
          }
        }
      },
      { threshold: 0.1 },
    );

    document.querySelectorAll(".reveal").forEach((el) => observer.observe(el));
    return () => observer.disconnect();
  }, []);

  return (
    <div className="landing-page">
      <LandingNavbar scrolled={scrolled} />
      <HeroSection />
      <DemoSection />
      <UseCasesSection />
      <PricingSection />
      <FooterSection />
    </div>
  );
}

function LandingNavbar({ scrolled }: { scrolled: boolean }): JSX.Element {
  const navigate = useNavigate();

  return (
    <nav className={`landing-nav ${scrolled ? "landing-nav-scrolled" : ""}`}>
      <div className="landing-container">
        <div className="landing-nav-inner">
          <div className="landing-nav-brand">
            <span className="landing-nav-brand-icon">H</span>
            <span>Hify</span>
          </div>
          <div className="landing-nav-actions">
            <ThemeToggle />
            <Button type="primary" onClick={() => navigate("/agents")}>
              开始使用
            </Button>
          </div>
        </div>
      </div>
    </nav>
  );
}

function ThemeToggle(): JSX.Element {
  const resolvedThemeMode = useAppStore((s) => s.resolvedThemeMode);
  const setThemePreference = useAppStore((s) => s.setThemePreference);

  return (
    <button
      className="landing-theme-toggle"
      onClick={() =>
        setThemePreference(resolvedThemeMode === "dark" ? "light" : "dark")
      }
    >
      {resolvedThemeMode === "dark" ? <SunOutlined /> : <MoonOutlined />}
    </button>
  );
}

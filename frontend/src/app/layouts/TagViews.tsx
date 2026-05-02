import { CloseOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import { useTagsStore } from "@/shared/stores/tags";

export function TagViews(): JSX.Element {
  const tabs = useTagsStore((s) => s.tabs);
  const activeKey = useTagsStore((s) => s.activeKey);
  const removeTab = useTagsStore((s) => s.removeTab);
  const setActiveKey = useTagsStore((s) => s.setActiveKey);
  const navigate = useNavigate();

  const handleTabClick = (key: string) => {
    setActiveKey(key);
    navigate(key);
  };

  const handleTabClose = (e: React.MouseEvent, key: string) => {
    e.stopPropagation();
    const nextKey = removeTab(key);
    navigate(nextKey);
  };

  return (
    <div className="tag-views">
      <div className="tag-views-scroll">
        {tabs.map((tab) => (
          <div
            key={tab.key}
            className={`tag-item${tab.key === activeKey ? " tag-item-active" : ""}`}
            onClick={() => handleTabClick(tab.key)}
          >
            <span className="tag-item-title">{tab.title}</span>
            {tab.closable ? (
              <span
                className="tag-item-close"
                onClick={(e) => handleTabClose(e, tab.key)}
              >
                <CloseOutlined />
              </span>
            ) : null}
          </div>
        ))}
      </div>
    </div>
  );
}

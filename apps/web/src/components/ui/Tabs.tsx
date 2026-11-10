import React, { useId } from "react";
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export interface TabItem {
  id: string;
  label: string;
  count?: number;
  icon?: React.ReactNode;
}

export interface TabsProps {
  tabs?: TabItem[];
  items?: TabItem[];
  activeTab: string;
  onChange: (tabId: string) => void;
  className?: string;
  ariaLabel?: string;
}

export const Tabs: React.FC<TabsProps> = ({
  tabs,
  items,
  activeTab,
  onChange,
  className,
  ariaLabel = "Navigation tabs",
}) => {
  const baseId = useId();
  const tabList = tabs || items || [];

  const handleKeyDown = (e: React.KeyboardEvent, index: number) => {
    let targetIndex = -1;
    if (e.key === "ArrowRight") {
      targetIndex = (index + 1) % tabList.length;
    } else if (e.key === "ArrowLeft") {
      targetIndex = (index - 1 + tabList.length) % tabList.length;
    } else if (e.key === "Home") {
      targetIndex = 0;
    } else if (e.key === "End") {
      targetIndex = tabList.length - 1;
    }

    if (targetIndex !== -1) {
      e.preventDefault();
      onChange(tabList[targetIndex].id);
      const nextBtn = document.getElementById(`${baseId}-tab-${tabList[targetIndex].id}`);
      nextBtn?.focus();
    }
  };

  return (
    <div
      role="tablist"
      aria-label={ariaLabel}
      className={twMerge(
        clsx(
          "flex items-center gap-1 border-b border-slate-800 overflow-x-auto no-scrollbar",
          className
        )
      )}
    >
      {tabList.map((tab, idx) => {
        const isSelected = tab.id === activeTab;
        return (
          <button
            key={tab.id}
            id={`${baseId}-tab-${tab.id}`}
            role="tab"
            aria-selected={isSelected}
            aria-controls={`${baseId}-panel-${tab.id}`}
            tabIndex={isSelected ? 0 : -1}
            onClick={() => onChange(tab.id)}
            onKeyDown={(e) => handleKeyDown(e, idx)}
            className={clsx(
              "flex items-center gap-2 px-4 py-2.5 text-xs sm:text-sm font-medium border-b-2 transition-colors whitespace-nowrap focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-400 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950",
              isSelected
                ? "border-sky-500 text-sky-400 font-semibold"
                : "border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-700"
            )}
          >
            {tab.icon &&
              (React.isValidElement(tab.icon)
                ? tab.icon
                : typeof tab.icon === "function" ||
                  (typeof tab.icon === "object" && tab.icon !== null)
                ? React.createElement(
                    tab.icon as unknown as React.ComponentType<{ className?: string }>,
                    { className: "w-4 h-4" }
                  )
                : null)}
            <span>{tab.label}</span>
            {tab.count !== undefined && (
              <span
                className={clsx(
                  "px-1.5 py-0.5 text-[11px] rounded-full",
                  isSelected
                    ? "bg-sky-950 text-sky-300 border border-sky-800"
                    : "bg-slate-800 text-slate-400"
                )}
              >
                {tab.count.toLocaleString()}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
};


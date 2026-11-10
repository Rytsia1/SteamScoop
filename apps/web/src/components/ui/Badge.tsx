import React from "react";
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?:
    | "default"
    | "positive"
    | "negative"
    | "neutral"
    | "info"
    | "warning"
    | "outline";
  size?: "sm" | "md";
}

export const Badge: React.FC<BadgeProps> = ({
  variant = "default",
  size = "md",
  className,
  children,
  ...props
}) => {
  const baseStyles =
    "inline-flex items-center font-medium rounded-full tracking-wide";

  const variantStyles = {
    default: "bg-slate-800 text-slate-300 border border-slate-700/60",
    positive: "bg-emerald-950/70 text-emerald-300 border border-emerald-800/60",
    negative: "bg-rose-950/70 text-rose-300 border border-rose-800/60",
    neutral: "bg-slate-800/80 text-slate-300 border border-slate-700/60",
    info: "bg-sky-950/70 text-sky-300 border border-sky-800/60",
    warning: "bg-amber-950/70 text-amber-300 border border-amber-800/60",
    outline: "bg-transparent text-slate-300 border border-slate-700",
  };

  const sizeStyles = {
    sm: "text-[11px] px-2 py-0.5",
    md: "text-xs px-2.5 py-1",
  };

  return (
    <span
      className={twMerge(clsx(baseStyles, variantStyles[variant], sizeStyles[size], className))}
      {...props}
    >
      {children}
    </span>
  );
};


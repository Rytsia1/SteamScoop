import React from "react";
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "text" | "rectangular" | "circular" | "card";
}

export const Skeleton: React.FC<SkeletonProps> = ({
  variant = "rectangular",
  className,
  ...props
}) => {
  const variantStyles = {
    text: "h-4 w-full rounded",
    rectangular: "rounded-lg",
    circular: "rounded-full",
    card: "h-32 rounded-xl",
  };

  return (
    <div
      aria-hidden="true"
      className={twMerge(
        clsx(
          "animate-pulse bg-slate-800/80 border border-slate-700/30",
          variantStyles[variant],
          className
        )
      )}
      {...props}
    />
  );
};

export const CardSkeleton: React.FC<{ count?: number; className?: string }> = ({
  count = 1,
  className,
}) => {
  return (
    <div className={twMerge(clsx("grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5", className))}>
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 flex flex-col gap-4 animate-pulse"
        >
          <div className="flex items-center gap-3">
            <Skeleton variant="circular" className="w-10 h-10 shrink-0" />
            <div className="flex-1 space-y-2">
              <Skeleton variant="text" className="w-3/4 h-4" />
              <Skeleton variant="text" className="w-1/2 h-3" />
            </div>
          </div>
          <div className="space-y-2 pt-2">
            <Skeleton variant="text" className="w-full h-3" />
            <Skeleton variant="text" className="w-5/6 h-3" />
          </div>
          <div className="pt-3 border-t border-slate-800/80 flex justify-between">
            <Skeleton variant="text" className="w-20 h-4" />
            <Skeleton variant="text" className="w-16 h-4" />
          </div>
        </div>
      ))}
    </div>
  );
};

export const ChartSkeleton: React.FC<{ height?: number | string; className?: string }> = ({
  height = 300,
  className,
}) => {
  return (
    <div
      style={{ height }}
      className={twMerge(
        clsx(
          "w-full rounded-xl border border-slate-800 bg-slate-900/40 p-6 flex flex-col justify-between animate-pulse",
          className
        )
      )}
    >
      <div className="flex justify-between items-center">
        <Skeleton variant="text" className="w-48 h-5" />
        <Skeleton variant="text" className="w-24 h-4" />
      </div>
      <div className="flex items-end justify-between gap-4 h-3/5 px-4">
        <Skeleton variant="rectangular" className="w-full h-2/3" />
        <Skeleton variant="rectangular" className="w-full h-4/5" />
        <Skeleton variant="rectangular" className="w-full h-1/2" />
        <Skeleton variant="rectangular" className="w-full h-full" />
        <Skeleton variant="rectangular" className="w-full h-3/4" />
      </div>
      <div className="flex justify-between">
        <Skeleton variant="text" className="w-16 h-3" />
        <Skeleton variant="text" className="w-16 h-3" />
        <Skeleton variant="text" className="w-16 h-3" />
      </div>
    </div>
  );
};


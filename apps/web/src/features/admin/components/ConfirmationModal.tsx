import React from "react";
import { AlertTriangle, AlertCircle, ShieldAlert, Loader2 } from "lucide-react";

export interface ConfirmationModalProps {
  isOpen: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: "danger" | "warning" | "primary";
  isLoading?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

export const ConfirmationModal: React.FC<ConfirmationModalProps> = ({
  isOpen,
  title,
  message,
  confirmLabel = "Confirm Action",
  cancelLabel = "Cancel",
  variant = "primary",
  isLoading = false,
  onConfirm,
  onCancel,
}) => {
  if (!isOpen) return null;

  const getVariantStyles = () => {
    switch (variant) {
      case "danger":
        return {
          icon: ShieldAlert,
          iconColor: "text-rose-400 bg-rose-950/60 border-rose-800",
          btnColor: "bg-rose-600 hover:bg-rose-500 text-white shadow-rose-900/30",
        };
      case "warning":
        return {
          icon: AlertTriangle,
          iconColor: "text-amber-400 bg-amber-950/60 border-amber-800",
          btnColor: "bg-amber-600 hover:bg-amber-500 text-white shadow-amber-900/30",
        };
      default:
        return {
          icon: AlertCircle,
          iconColor: "text-sky-400 bg-sky-950/60 border-sky-800",
          btnColor: "bg-sky-600 hover:bg-sky-500 text-white shadow-sky-900/30",
        };
    }
  };

  const styles = getVariantStyles();
  const Icon = styles.icon;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirm-modal-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-150"
    >
      <div className="w-full max-w-md rounded-xl bg-slate-900 border border-slate-800 shadow-2xl overflow-hidden p-6 space-y-4">
        <div className="flex items-start gap-3">
          <div className={`p-2.5 rounded-lg border ${styles.iconColor} shrink-0`}>
            <Icon className="w-5 h-5" aria-hidden="true" />
          </div>
          <div className="space-y-1">
            <h3 id="confirm-modal-title" className="text-base font-bold text-slate-100">
              {title}
            </h3>
            <p className="text-xs text-slate-400 leading-relaxed">{message}</p>
          </div>
        </div>

        <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
          <button
            type="button"
            disabled={isLoading}
            onClick={onCancel}
            className="px-3.5 py-2 rounded-lg text-xs font-medium text-slate-300 hover:text-white hover:bg-slate-800 border border-slate-700/80 transition-colors disabled:opacity-50"
          >
            {cancelLabel}
          </button>
          <button
            type="button"
            disabled={isLoading}
            onClick={onConfirm}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold shadow-md transition-all disabled:opacity-50 ${styles.btnColor}`}
          >
            {isLoading && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
            <span>{confirmLabel}</span>
          </button>
        </div>
      </div>
    </div>
  );
};


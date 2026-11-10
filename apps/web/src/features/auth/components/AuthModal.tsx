import React, { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { Modal } from "../../../components/ui/Modal";
import { Input } from "../../../components/ui/Input";
import { Button } from "../../../components/ui/Button";
import { ErrorAlert } from "../../../components/feedback/ErrorAlert";
import { LogIn, UserPlus } from "lucide-react";

export const AuthModal: React.FC = () => {
  const { isAuthModalOpen, closeAuthModal, login, register } = useAuth();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      if (mode === "login") {
        await login({ email, password });
      } else {
        await register({ email, password, display_name: displayName });
      }
      setEmail("");
      setPassword("");
      setDisplayName("");
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Authentication failed. Please check your credentials.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleModeSwitch = (newMode: "login" | "register") => {
    setMode(newMode);
    setError(null);
  };

  return (
    <Modal
      isOpen={isAuthModalOpen}
      onClose={closeAuthModal}
      title={mode === "login" ? "Researcher Sign In" : "Register Researcher Account"}
      description="Access private research workspaces, saved query configurations, and reproducibility snapshots."
      maxWidth="md"
    >
      <div className="space-y-4">
        {/* Mode Toggle Tabs */}
        <div className="flex border-b border-slate-800" role="tablist">
          <button
            type="button"
            role="tab"
            aria-selected={mode === "login"}
            onClick={() => handleModeSwitch("login")}
            className={`flex-1 py-2 text-xs font-semibold border-b-2 text-center transition-colors ${
              mode === "login"
                ? "border-sky-500 text-sky-400"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            Sign In
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={mode === "register"}
            onClick={() => handleModeSwitch("register")}
            className={`flex-1 py-2 text-xs font-semibold border-b-2 text-center transition-colors ${
              mode === "register"
                ? "border-sky-500 text-sky-400"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            Create Account
          </button>
        </div>

        {error && <ErrorAlert title="Authentication Error" message={error} />}

        <form onSubmit={handleSubmit} className="space-y-3.5 pt-1">
          {mode === "register" && (
            <Input
              label="Display Name"
              type="text"
              required
              placeholder="Dr. Researcher"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              disabled={isSubmitting}
            />
          )}

          <Input
            label="Email Address"
            type="email"
            required
            placeholder="researcher@institution.edu"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            disabled={isSubmitting}
          />

          <Input
            label="Password"
            type="password"
            required
            placeholder="••••••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            disabled={isSubmitting}
          />

          <div className="pt-2">
            <Button
              type="submit"
              variant="primary"
              className="w-full"
              isLoading={isSubmitting}
              leftIcon={
                mode === "login" ? (
                  <LogIn className="w-4 h-4" aria-hidden="true" />
                ) : (
                  <UserPlus className="w-4 h-4" aria-hidden="true" />
                )
              }
            >
              {mode === "login" ? "Sign In to Workspace" : "Register Account"}
            </Button>
          </div>
        </form>
      </div>
    </Modal>
  );
};

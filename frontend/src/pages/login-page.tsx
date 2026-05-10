import { FormEvent, useState } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import { loginUser } from "../api/auth";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Card, CardBody } from "../components/ui/card";
import { ErrorMessage } from "../components/ui/error-message";
import { Input } from "../components/ui/input";
import { useAuth } from "../contexts/auth-context";

const copy = {
  eyebrow: "Account Access",
  title: "\u767b\u5f55 GaokaoPilot",
  subtitle:
    "\u4f7f\u7528\u4f60\u7684\u8d26\u53f7\u7ee7\u7eed\u8bbf\u95ee\u4e2a\u6027\u5316\u529f\u80fd\u3002\u5f53\u524d\u9662\u6821\u67e5\u8be2\u3001\u95ee\u7b54\u548c\u63a8\u8350\u4ecd\u53ef\u533f\u540d\u4f7f\u7528\u3002",
  username: "\u7528\u6237\u540d\u6216\u90ae\u7bb1",
  password: "\u5bc6\u7801",
  submit: "\u767b\u5f55",
  pending: "\u767b\u5f55\u4e2d...",
  noAccount: "\u8fd8\u6ca1\u6709\u8d26\u53f7\uff1f",
  register: "\u53bb\u6ce8\u518c",
  home: "\u8fd4\u56de\u9996\u9875",
  blankUsername: "\u8bf7\u8f93\u5165\u7528\u6237\u540d\u6216\u90ae\u7bb1\u3002",
  blankPassword: "\u8bf7\u8f93\u5165\u5bc6\u7801\u3002",
};

interface LoginLocationState {
  from?: string;
  registered?: boolean;
  username?: string;
}

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated, loadingUser, setAccessToken, refreshCurrentUser } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const locationState = (location.state ?? null) as LoginLocationState | null;
  const successMessage =
    locationState?.registered && typeof locationState.username === "string"
      ? `\u8d26\u53f7 ${locationState.username} \u6ce8\u518c\u6210\u529f\uff0c\u8bf7\u767b\u5f55\u3002`
      : null;

  if (!loadingUser && isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!username.trim()) {
      setError(copy.blankUsername);
      return;
    }
    if (!password) {
      setError(copy.blankPassword);
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      const token = await loginUser({
        username: username.trim(),
        password,
      });
      setAccessToken(token.access_token);
      await refreshCurrentUser();
      const redirectTo = typeof locationState?.from === "string" ? locationState.from : "/";
      navigate(redirectTo, { replace: true });
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "\u767b\u5f55\u5931\u8d25\uff0c\u8bf7\u7a0d\u540e\u91cd\u8bd5\u3002",
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section className="mx-auto grid min-h-[calc(100vh-10rem)] max-w-5xl gap-6 lg:grid-cols-[1.05fr_0.95fr] lg:items-center">
      <div className="panel border-slate-200/80 bg-[linear-gradient(135deg,rgba(255,255,255,0.98)_0%,rgba(240,249,255,0.95)_52%,rgba(236,253,245,0.95)_100%)]">
        <Badge tone="brand">{copy.eyebrow}</Badge>
        <h1 className="mt-5 text-4xl font-semibold tracking-tight text-slate-950 sm:text-5xl">
          {copy.title}
        </h1>
        <p className="mt-4 max-w-2xl text-sm leading-7 text-slate-600">{copy.subtitle}</p>

        <div className="mt-8 flex flex-wrap gap-3 text-sm">
          <Link
            to="/"
            className="inline-flex rounded-full border border-slate-300 bg-white px-4 py-2 font-medium text-slate-700 transition hover:border-slate-400 hover:bg-slate-50"
          >
            {copy.home}
          </Link>
          <Link
            to="/register"
            className="inline-flex rounded-full bg-slate-950 px-4 py-2 font-medium text-white transition hover:bg-slate-800"
          >
            {copy.register}
          </Link>
        </div>
      </div>

      <Card className="overflow-hidden">
        <CardBody className="space-y-6 p-6 sm:p-8">
          <div>
            <p className="eyebrow">{copy.eyebrow}</p>
            <h2 className="mt-3 text-2xl font-semibold text-slate-950">{copy.submit}</h2>
          </div>

          <form className="space-y-4" onSubmit={handleSubmit}>
            <Input
              label={copy.username}
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              placeholder="alice / alice@example.com"
              autoComplete="username"
            />
            <Input
              label={copy.password}
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="\u8bf7\u8f93\u5165\u5bc6\u7801"
              autoComplete="current-password"
            />

            {error ? <ErrorMessage>{error}</ErrorMessage> : null}
            {successMessage ? <p className="text-sm text-emerald-700">{successMessage}</p> : null}

            <Button type="submit" fullWidth disabled={submitting}>
              {submitting ? copy.pending : copy.submit}
            </Button>
          </form>

          <p className="text-sm text-slate-600">
            {copy.noAccount}{" "}
            <Link to="/register" className="font-semibold text-sky-700 hover:text-sky-800">
              {copy.register}
            </Link>
          </p>
        </CardBody>
      </Card>
    </section>
  );
}

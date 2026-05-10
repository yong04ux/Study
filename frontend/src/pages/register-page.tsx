import { FormEvent, useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { registerUser } from "../api/auth";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Card, CardBody } from "../components/ui/card";
import { ErrorMessage } from "../components/ui/error-message";
import { Input } from "../components/ui/input";
import { useAuth } from "../contexts/auth-context";

const copy = {
  eyebrow: "Create Account",
  title: "\u6ce8\u518c\u65b0\u8d26\u53f7",
  subtitle:
    "\u5148\u5b8c\u6210\u6700\u5c0f\u6ce8\u518c\u6d41\u7a0b\uff0c\u540e\u7eed\u518d\u9010\u6b65\u63a5\u5165\u66f4\u591a\u4e2a\u6027\u5316\u80fd\u529b\u3002",
  username: "\u7528\u6237\u540d",
  email: "\u90ae\u7bb1",
  password: "\u5bc6\u7801",
  confirmPassword: "\u786e\u8ba4\u5bc6\u7801",
  submit: "\u6ce8\u518c",
  pending: "\u6ce8\u518c\u4e2d...",
  haveAccount: "\u5df2\u7ecf\u6709\u8d26\u53f7\uff1f",
  login: "\u53bb\u767b\u5f55",
  home: "\u8fd4\u56de\u9996\u9875",
  blankUsername: "\u8bf7\u8f93\u5165\u7528\u6237\u540d\u3002",
  blankEmail: "\u8bf7\u8f93\u5165\u90ae\u7bb1\u3002",
  blankPassword: "\u8bf7\u8f93\u5165\u5bc6\u7801\u3002",
  shortPassword: "\u5bc6\u7801\u81f3\u5c11\u9700\u8981 6 \u4f4d\u3002",
  passwordMismatch: "\u4e24\u6b21\u8f93\u5165\u7684\u5bc6\u7801\u4e0d\u4e00\u81f4\u3002",
};

export function RegisterPage() {
  const navigate = useNavigate();
  const { isAuthenticated, loadingUser } = useAuth();
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!loadingUser && isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!username.trim()) {
      setError(copy.blankUsername);
      return;
    }
    if (!email.trim()) {
      setError(copy.blankEmail);
      return;
    }
    if (!password) {
      setError(copy.blankPassword);
      return;
    }
    if (password.length < 6) {
      setError(copy.shortPassword);
      return;
    }
    if (password !== confirmPassword) {
      setError(copy.passwordMismatch);
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      await registerUser({
        username: username.trim(),
        email: email.trim(),
        password,
      });
      navigate("/login", {
        replace: true,
        state: { registered: true, username: username.trim() },
      });
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "\u6ce8\u518c\u5931\u8d25\uff0c\u8bf7\u7a0d\u540e\u91cd\u8bd5\u3002",
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section className="mx-auto grid min-h-[calc(100vh-10rem)] max-w-5xl gap-6 lg:grid-cols-[0.98fr_1.02fr] lg:items-center">
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
            to="/login"
            className="inline-flex rounded-full bg-slate-950 px-4 py-2 font-medium text-white transition hover:bg-slate-800"
          >
            {copy.login}
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
              placeholder="alice"
              autoComplete="username"
            />
            <Input
              label={copy.email}
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="alice@example.com"
              autoComplete="email"
            />
            <Input
              label={copy.password}
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="\u81f3\u5c11 6 \u4f4d"
              autoComplete="new-password"
            />
            <Input
              label={copy.confirmPassword}
              type="password"
              value={confirmPassword}
              onChange={(event) => setConfirmPassword(event.target.value)}
              placeholder="\u518d\u6b21\u8f93\u5165\u5bc6\u7801"
              autoComplete="new-password"
            />

            {error ? <ErrorMessage>{error}</ErrorMessage> : null}

            <Button type="submit" fullWidth disabled={submitting}>
              {submitting ? copy.pending : copy.submit}
            </Button>
          </form>

          <p className="text-sm text-slate-600">
            {copy.haveAccount}{" "}
            <Link to="/login" className="font-semibold text-sky-700 hover:text-sky-800">
              {copy.login}
            </Link>
          </p>
        </CardBody>
      </Card>
    </section>
  );
}

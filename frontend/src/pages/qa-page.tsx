import { FormEvent, useEffect, useRef, useState } from "react";
import { askQuestion } from "../api/qa";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Card, CardBody, CardHeader } from "../components/ui/card";
import { ErrorMessage } from "../components/ui/error-message";
import { Input } from "../components/ui/input";
import { Loading } from "../components/ui/loading";
import { Select } from "../components/ui/select";
import { Textarea } from "../components/ui/textarea";
import { cx } from "../components/ui/cx";
import type { QaSource } from "../types/qa";

/* 智能问答页：左侧选择省份/科类和示例问题，右侧用聊天流展示答案和 RAG 引用来源。
   支持多轮对话上下文 —— 同一会话内的追问会携带 conversation_id。 */

type ChatMessage =
  | {
      id: string;
      role: "user";
      content: string;
      createdAt: string;
    }
  | {
      id: string;
      role: "assistant";
      content: string;
      sources: QaSource[];
      createdAt: string;
    };

const subjectOptions = ["物理类", "历史类", "理科", "文科"];

const exampleQuestions = [
  { label: "平行志愿是什么意思？", category: "policy" },
  { label: "计算机科学与技术专业主要学什么？", category: "major" },
  { label: "位次和分数哪个更重要？", category: "advice" },
  { label: "广东物理类考生如何填报志愿？", category: "policy" },
  { label: "强基计划需要什么条件？", category: "policy" },
  { label: "什么是征集志愿？", category: "policy" },
  { label: "中外合作办学值得去吗？", category: "advice" },
  { label: "大学转专业一般有什么要求？", category: "advice" },
  { label: "985和211高校有什么区别？", category: "school" },
  { label: "软件工程和计算机科学有什么不同？", category: "major" },
  { label: "退档后还能被其他学校录取吗？", category: "policy" },
  { label: "人工智能专业就业前景怎么样？", category: "major" },
  { label: "新高考3+1+2选科对报专业有什么影响？", category: "policy" },
  { label: "服从调剂会不会被调到完全不相关的专业？", category: "advice" },
  { label: "保研率高的大学有哪些？", category: "school" },
];

const copy = {
  eyebrow: "RAG QA",
  title: "智能问答",
  subtitle:
    "输入高考政策、专业或志愿填报相关问题，系统会先检索资料库，再结合资料生成回答。支持多轮追问。",
  province: "省份",
  subjectType: "科类",
  questionPlaceholder: "输入你的问题，例如：平行志愿是什么意思？",
  send: "发送",
  thinking: "正在思考...",
  examples: "示例问题",
  examplesHint: "点击即可提问",
  sources: "引用来源",
  noSources: "本次回答暂无引用来源。",
  document: "文档",
  similarity: "距离",
  sourcePath: "来源路径",
  chunk: "片段",
  errorFallback: "问答请求失败，请检查后端服务或稍后重试。",
  emptyQuestion: "请输入至少 2 个字的问题。",
  initialAssistant:
    "你好！我是高考志愿填报助手。你可以问我：\n• 政策规则（如平行志愿、退档、征集志愿）\n• 专业介绍（如计算机、软件工程、人工智能等学什么）\n• 院校信息（985/211/双一流层次、保研率等）\n• 填报策略（冲稳保怎么设置、如何参考位次等）\n\n如果你有具体分数，也可以直接问「广东物理类600分能报哪些学校」，我会为你做志愿推荐。",
  assistantTitle: "问答工作区",
  helper: "左侧调整省份和科类，右侧以聊天形式展示 AI 回答和引用来源。同一会话内可以追问。",
  conversationContext: "多轮对话中",
  newConversation: "新对话",
  filterAll: "全部",
  filterPolicy: "政策",
  filterMajor: "专业",
  filterAdvice: "策略",
  filterSchool: "院校",
};

const categoryFilters = [
  { key: "all", label: copy.filterAll },
  { key: "policy", label: copy.filterPolicy },
  { key: "major", label: copy.filterMajor },
  { key: "advice", label: copy.filterAdvice },
  { key: "school", label: copy.filterSchool },
] as const;

function createId() {
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function createConversationId() {
  return `conv-${Date.now()}-${Math.random().toString(16).slice(2, 10)}`;
}

function formatDistance(distance: number | null) {
  if (distance === null || Number.isNaN(distance)) {
    return null;
  }
  return distance.toFixed(4);
}

function SourceCard({ source, index }: { source: QaSource; index: number }) {
  const distance = formatDistance(source.distance);

  return (
    <div className="rounded-2xl border border-slate-200/80 bg-slate-50/80 px-4 py-4">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-sm font-semibold text-slate-900">
          {source.filename || `${copy.document} ${index + 1}`}
        </p>
        {distance ? (
          <Badge tone="neutral">
            {copy.similarity}: {distance}
          </Badge>
        ) : null}
      </div>

      <p className="mt-3 whitespace-pre-wrap text-sm leading-7 text-slate-700">
        {source.content}
      </p>

      <div className="mt-3 flex flex-wrap gap-2 text-xs text-slate-500">
        {source.source ? (
          <span>
            {copy.sourcePath}: {source.source}
          </span>
        ) : null}
        {source.chunk_index !== null ? (
          <span>
            {copy.chunk}: {source.chunk_index}
          </span>
        ) : null}
      </div>
    </div>
  );
}

function AssistantMessage({
  message,
}: {
  message: Extract<ChatMessage, { role: "assistant" }>;
}) {
  return (
    <div className="mr-auto max-w-[92%]">
      <div className="rounded-[1.4rem] rounded-tl-sm border border-slate-200/80 bg-white px-5 py-4 shadow-[0_18px_40px_rgba(15,23,42,0.06)]">
        <p className="whitespace-pre-wrap text-sm leading-7 text-slate-800">{message.content}</p>
      </div>

      <div className="mt-3 space-y-3">
        {message.sources.length > 0 ? (
          <>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
              {copy.sources}
            </p>
            {message.sources.map((source, index) => (
              <SourceCard key={`${message.id}-source-${index}`} source={source} index={index} />
            ))}
          </>
        ) : (
          <p className="text-xs text-slate-500">{copy.noSources}</p>
        )}
      </div>
    </div>
  );
}

function UserMessage({
  message,
}: {
  message: Extract<ChatMessage, { role: "user" }>;
}) {
  return (
    <div className="ml-auto max-w-[86%] rounded-[1.4rem] rounded-tr-sm bg-slate-950 px-5 py-4 text-white shadow-[0_18px_40px_rgba(15,23,42,0.16)]">
      <p className="whitespace-pre-wrap text-sm leading-7">{message.content}</p>
    </div>
  );
}

export function QaPage() {
  const [province, setProvince] = useState("广东");
  const [subjectType, setSubjectType] = useState(subjectOptions[0]);
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "initial-assistant",
      role: "assistant",
      content: copy.initialAssistant,
      sources: [],
      createdAt: new Date().toISOString(),
    },
  ]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const [conversationId] = useState(() => createConversationId());
  const [exampleFilter, setExampleFilter] = useState<string>("all");

  const hasConversation = messages.filter((m) => m.role === "user").length > 0;

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, loading]);

  const submitQuestion = async (nextQuestion: string) => {
    const trimmedQuestion = nextQuestion.trim();
    if (trimmedQuestion.length < 2) {
      setError(copy.emptyQuestion);
      return;
    }

    const userMessage: ChatMessage = {
      id: createId(),
      role: "user",
      content: trimmedQuestion,
      createdAt: new Date().toISOString(),
    };

    setMessages((current) => [...current, userMessage]);
    setQuestion("");
    setError(null);
    setLoading(true);

    try {
      const response = await askQuestion({
        question: trimmedQuestion,
        province: province.trim() || "广东",
        subject_type: subjectType,
        conversation_id: conversationId,
      });

      const assistantMessage: ChatMessage = {
        id: createId(),
        role: "assistant",
        content: response.answer,
        sources: response.sources,
        createdAt: new Date().toISOString(),
      };
      setMessages((current) => [...current, assistantMessage]);
    } catch (requestError) {
      const message =
        requestError instanceof Error ? requestError.message : copy.errorFallback;
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    await submitQuestion(question);
  };

  const filteredExamples =
    exampleFilter === "all"
      ? exampleQuestions
      : exampleQuestions.filter((q) => q.category === exampleFilter);

  return (
    <section className="grid min-h-[calc(100vh-9rem)] gap-6 lg:grid-cols-[minmax(0,0.76fr)_minmax(0,1.24fr)]">
      <aside className="space-y-6">
        <Card>
          <CardBody className="space-y-6 p-6">
            <div>
              <p className="eyebrow">{copy.eyebrow}</p>
              <h1 className="mt-3 text-3xl font-semibold tracking-tight text-slate-950">
                {copy.title}
              </h1>
              <p className="mt-4 text-sm leading-7 text-slate-600">{copy.subtitle}</p>
            </div>

            <div className="grid gap-4">
              <Input
                label={copy.province}
                value={province}
                onChange={(event) => setProvince(event.target.value)}
              />
              <Select
                label={copy.subjectType}
                value={subjectType}
                onChange={(event) => setSubjectType(event.target.value)}
              >
                {subjectOptions.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </Select>
            </div>

            <div className="rounded-2xl border border-slate-200/80 bg-slate-50/80 px-4 py-4 text-sm leading-7 text-slate-600">
              {copy.helper}
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardHeader className="flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <p className="text-sm font-semibold uppercase tracking-[0.24em] text-slate-500">
                {copy.examples}
              </p>
              <span className="text-xs text-slate-400">{copy.examplesHint}</span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {categoryFilters.map((filter) => (
                <button
                  key={filter.key}
                  type="button"
                  onClick={() => setExampleFilter(filter.key)}
                  className={cx(
                    "rounded-full px-3 py-1 text-xs font-medium transition",
                    exampleFilter === filter.key
                      ? "bg-slate-950 text-white"
                      : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                  )}
                >
                  {filter.label}
                </button>
              ))}
            </div>
          </CardHeader>
          <CardBody className="space-y-2 max-h-[26rem] overflow-y-auto">
            {filteredExamples.map((item) => (
              <button
                key={item.label}
                type="button"
                onClick={() => void submitQuestion(item.label)}
                disabled={loading}
                className="w-full rounded-2xl border border-slate-200/80 bg-white px-4 py-3 text-left text-sm leading-6 text-slate-700 transition hover:border-sky-200 hover:bg-sky-50/70 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {item.label}
              </button>
            ))}
          </CardBody>
        </Card>
      </aside>

      <Card className="flex min-h-[38rem] flex-col overflow-hidden">
        <CardHeader className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="eyebrow">{copy.assistantTitle}</p>
            <h2 className="mt-2 text-xl font-semibold tracking-tight text-slate-950">
              {copy.title}
            </h2>
          </div>
          <div className="flex items-center gap-2">
            {hasConversation && (
              <Badge tone="brand">{copy.conversationContext}</Badge>
            )}
            <Badge tone="neutral">RAG + Agent</Badge>
          </div>
        </CardHeader>

        <div className="flex-1 space-y-5 overflow-y-auto bg-[radial-gradient(circle_at_top,_rgba(186,230,253,0.3),_transparent_38%),linear-gradient(180deg,_rgba(248,250,252,0.98),_rgba(241,245,249,0.96))] px-5 py-5 sm:px-6">
          {messages.map((message) =>
            message.role === "user" ? (
              <UserMessage key={message.id} message={message} />
            ) : (
              <AssistantMessage key={message.id} message={message} />
            ),
          )}

          {loading ? (
            <div className="mr-auto max-w-[80%] rounded-[1.4rem] rounded-tl-sm border border-slate-200/80 bg-white px-5 py-4 shadow-[0_18px_40px_rgba(15,23,42,0.06)]">
              <Loading label={copy.thinking} />
            </div>
          ) : null}

          <div ref={messagesEndRef} />
        </div>

        {error ? (
          <div className="border-t border-slate-200/80 bg-white px-4 py-4 sm:px-6">
            <ErrorMessage>{error}</ErrorMessage>
          </div>
        ) : null}

        <form
          className={cx("border-t border-slate-200/80 bg-white px-4 py-4 sm:px-6", error ? "pt-0" : "")}
          onSubmit={handleSubmit}
        >
          <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
            <Textarea
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              rows={2}
              placeholder={copy.questionPlaceholder}
              className="min-h-14 flex-1 resize-none"
            />
            <Button type="submit" disabled={loading} className="sm:min-w-28">
              {loading ? copy.thinking : copy.send}
            </Button>
          </div>
        </form>
      </Card>
    </section>
  );
}

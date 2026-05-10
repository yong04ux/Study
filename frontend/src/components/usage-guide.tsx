import { Badge } from "./ui/badge";
import { Card, CardBody } from "./ui/card";

interface UsageGuideProps {
  badge?: string;
  title: string;
  description?: string;
  steps: string[];
}

export function UsageGuide({ badge = "Guide", title, description, steps }: UsageGuideProps) {
  return (
    <Card className="overflow-hidden border-sky-200/80 bg-[linear-gradient(135deg,rgba(240,249,255,0.96)_0%,rgba(236,253,245,0.96)_100%)]">
      <CardBody className="space-y-4">
        <div>
          <Badge tone="brand">{badge}</Badge>
          <h2 className="mt-3 text-xl font-semibold tracking-tight text-slate-950">{title}</h2>
          {description ? (
            <p className="mt-3 text-sm leading-7 text-slate-600">{description}</p>
          ) : null}
        </div>

        <ol className="space-y-3">
          {steps.map((step, index) => (
            <li
              key={`${index + 1}-${step}`}
              className="flex gap-3 rounded-2xl border border-white/80 bg-white/80 px-4 py-4"
            >
              <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-slate-950 text-xs font-semibold text-white">
                {index + 1}
              </span>
              <p className="text-sm leading-7 text-slate-700">{step}</p>
            </li>
          ))}
        </ol>
      </CardBody>
    </Card>
  );
}

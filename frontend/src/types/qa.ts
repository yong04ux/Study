export interface QaAskRequest {
  // 用户问题；后端会根据内容判断走 RAG 还是志愿推荐 Agent。
  question: string;
  // 页面传入的省份和科类，推荐意图缺省时会作为兜底信息。
  province: string;
  subject_type: string;
  // 调试开关：false 时后端只返回检索摘要，不调用大模型。
  use_llm?: boolean;
  // 多轮对话 ID，同一会话传入相同 ID 可保持上下文。
  conversation_id?: string;
}

export interface QaSource {
  // 被 RAG 检索命中的文档片段正文。
  content: string;
  // 来源文件名和路径，用于前端展示引用来源。
  filename: string | null;
  source: string | null;
  // 文档切分后的片段序号和向量距离。
  chunk_index: number | null;
  distance: number | null;
}

export interface QaAskResponse {
  // 最终回答文本。
  answer: string;
  // 回答引用的资料片段；推荐类问题会返回“志愿推荐 Agent”作为虚拟来源。
  sources: QaSource[];
}

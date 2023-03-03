export type ChatMessage = {
  id: string;
  author_role: "user" | "assistant" | string;
  model_slug?: string;
  message?: string;
  parent?: string;
  children: Array<string>;
  typing?: boolean;
};

export type ChatConversationDetail = {
  id: string;
  current_node: string;
  title: string;
  create_time: number;
  mapping: Record<string, ChatMessage>;
};

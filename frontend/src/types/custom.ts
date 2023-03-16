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
  current_node: string | null;
  title: string;
  create_time: number;
  mapping: Record<string, ChatMessage>;
  model_name: string | null;
};

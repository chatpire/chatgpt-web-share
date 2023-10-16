import { ChatSourceTypes } from './schema';

export interface NewConversationInfo {
  title: string | null;
  source: ChatSourceTypes | null;
  model: string | null;
  openaiWebPlugins: string[] | null;
}

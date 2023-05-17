import { RemovableRef } from '@vueuse/core';

import { BaseConversationSchema, ConversationHistoryDocument, OpenAIChatPlugin, UserRead } from '@/types/schema';

interface UserState {
  user: UserRead | null;
  savedUsername: string | null;
  savedPassword: string | null;
}

export type Preference = {
  sendKey: 'Shift+Enter' | 'Enter' | 'Ctrl+Enter';
  renderUserMessageInMd: boolean;
  codeAutoWrap: boolean;
  widerConversationPage: boolean;
};

interface AppState {
  theme: any;
  language: any;
  preference: RemovableRef<Preference>;
}

interface ConversationState {
  conversations: Array<BaseConversationSchema>;
  newConversation: BaseConversationSchema | null;
  conversationHistoryMap: Record<string, ConversationHistoryDocument>;
}

export type { AppState, ConversationState, UserState };

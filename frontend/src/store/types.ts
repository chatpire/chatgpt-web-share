import { RemovableRef } from '@vueuse/core';

import { BaseConversationHistory, BaseConversationSchema, UserRead } from '@/types/schema';

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
  language: RemovableRef<'zh-CN' | 'en-US' | string>;
  preference: RemovableRef<Preference>;
}

interface ConversationState {
  conversations: Array<BaseConversationSchema>;
  newConversation: BaseConversationSchema | null;
  conversationHistoryMap: Record<string, BaseConversationHistory>;
}

export type { AppState, ConversationState, UserState };

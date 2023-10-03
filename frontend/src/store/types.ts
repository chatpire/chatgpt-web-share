import { RemovableRef } from '@vueuse/core';
import { UploadFileInfo } from 'naive-ui';

import { BaseConversationHistory, BaseConversationSchema, UploadedFileInfoSchema, UserRead } from '@/types/schema';

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

type FileUploadGroup = {
  uploadedFileInfos: UploadedFileInfoSchema[];
  naiveUiUploadFileInfos: UploadFileInfo[];
  naiveUiFileIdToServerFileIdMap: Record<string, string>;
}

interface FileState {
  attachments: FileUploadGroup;
  images: FileUploadGroup;
}

export type { AppState, ConversationState, FileState, UserState };

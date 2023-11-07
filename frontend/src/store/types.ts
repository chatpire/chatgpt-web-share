import { RemovableRef } from '@vueuse/core';
import { UploadFileInfo } from 'naive-ui';
import { Ref } from 'vue';

import {
  BaseConversationHistory,
  BaseConversationSchema,
  ChatSourceTypes,
  UploadedFileInfoSchema,
  UserRead,
} from '@/types/schema';

export type SavedLoginForm = {
  rememberPassword: boolean;
  savedUsername: string | undefined;
  savedPassword: string | undefined;
}

interface UserState {
  user: UserRead | null;
  savedLoginForm: Ref<SavedLoginForm>;
}

export type Preference = {
  sendKey: 'Shift+Enter' | 'Enter' | 'Ctrl+Enter';
  renderUserMessageInMd: boolean;
  codeAutoWrap: boolean;
  widerConversationPage: boolean;
};

interface AppState {
  theme: any;
  language: Ref<'zh-CN' | 'en-US' | string>;
  preference: Ref<Preference>;
  lastSelectedSource: Ref<ChatSourceTypes | null>;
  lastSelectedModel: Ref<string | null>;
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
};

type ImageUploadGroup = FileUploadGroup & {
  imageMetadataMap: Record<string, { width: number; height: number }>; // 使用 server 端的文件 id 作为 key
};

interface FileState {
  attachments: FileUploadGroup;
  images: ImageUploadGroup;
}

export type { AppState, ConversationState, FileState, UserState };

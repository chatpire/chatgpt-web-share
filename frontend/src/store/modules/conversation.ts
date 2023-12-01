import { defineStore } from 'pinia';

import {
  deleteConversationApi,
  getAllConversationsApi,
  getConversationHistoryApi,
  getConversationHistoryFromCacheApi,
  setConversationTitleApi,
} from '@/api/conv';
import { NewConversationInfo } from '@/types/custom';
import { BaseChatMessage, BaseConversationSchema } from '@/types/schema';

import { ConversationState } from '../types';

export const newConversationId = 'new_conversation';

const useConversationStore = defineStore('conversation', {
  state: (): ConversationState => ({
    conversations: [],
    conversationHistoryMap: {},
    newConversation: null,
  }),
  getters: {},
  actions: {
    async fetchAllConversations() {
      const result = (await getAllConversationsApi()).data;
      this.$patch({ conversations: result });
    },

    async fetchConversationHistory(conversation_id: string) {
      if (this.conversationHistoryMap[conversation_id]) {
        return this.conversationHistoryMap[conversation_id];
      }
      const result = (await getConversationHistoryApi(conversation_id)).data;
      this.conversationHistoryMap[conversation_id] = result;
    },

    async fetchConversationHistoryFromCache(conversation_id: string, fallback_refresh = true) {
      try {
        const result = (await getConversationHistoryFromCacheApi(conversation_id)).data;
        this.conversationHistoryMap[conversation_id] = result;
      } catch (e) {
        if (fallback_refresh) {
          return this.fetchConversationHistory(conversation_id);
        }
        throw e;
      }
    },

    createNewConversation(info: NewConversationInfo) {
      if (
        !info.source ||
        !info.model ||
        !(info.source === 'openai_api' || info.source === 'openai_web') ||
        (info.model !== 'gpt_4_plugins' && info.openaiWebPlugins && info.openaiWebPlugins.length > 0)
      ) {
        console.error('Invalid conversation info', info);
        throw new Error('Invalid conversation info');
      }
      console.log(info);
      const currentTime = new Date().toISOString();
      this.newConversation = {
        id: -1,
        source: info.source,
        is_valid: true,
        conversation_id: newConversationId,
        title: info.title || '',
        current_model: info.model,
        create_time: currentTime,
        update_time: currentTime,
      };
      this.conversationHistoryMap[newConversationId] = {
        _id: newConversationId,
        source: info.source,
        title: info.title || '',
        current_model: info.model,
        current_node: '',
        create_time: currentTime,
        update_time: currentTime,
        mapping: {},
        metadata: info.openaiWebPlugins
          ? {
            source: 'openai_web',
            plugin_ids: info.openaiWebPlugins,
          }
          : undefined,
      };
    },

    removeNewConversation() {
      if (!this.newConversation) {
        return;
      }
      delete this.conversationHistoryMap[this.newConversation!.conversation_id!];
      this.newConversation = null;
    },

    addConversation(conversation: BaseConversationSchema) {
      this.conversations.push(conversation);
    },

    async deleteConversation(conversation_id: string) {
      await deleteConversationApi(conversation_id);
      delete this.conversationHistoryMap[conversation_id];
      this.conversations = this.conversations.filter((conv: any) => conv.conversation_id !== conversation_id);
    },

    async changeConversationTitle(conversation_id: string, title: string) {
      await setConversationTitleApi(conversation_id, title);
      await this.fetchAllConversations();
      if (this.conversationHistoryMap[conversation_id]) {
        this.conversationHistoryMap[conversation_id].title = title;
      }
    },

    // 仅当收到新信息时调用，为了避免重复获取整个对话历史
    addMessagesToConversation(conversation_id: string, messages: BaseChatMessage[]) {
      if (!this.conversationHistoryMap[conversation_id]) {
        return;
      }

      const convHistory = this.conversationHistoryMap[conversation_id];
      // convHistory.mapping[sendMessage.id] = sendMessage;
      // convHistory.mapping[recvMessage.id] = recvMessage;
      for (let i = 0; i < messages.length; i++) {
        if (i > 0) messages[i].parent = messages[i - 1].id;
        if (i < messages.length - 1) messages[i].children = [messages[i + 1].id];
        convHistory.mapping[messages[i].id] = messages[i];
      }

      // 这里只有在新建对话时调用
      if (convHistory.current_node === null) {
        convHistory.current_node = messages[messages.length - 1].id;
      } else {
        const lastTopMessage = convHistory.mapping[convHistory.current_node!];
        messages[0].parent = lastTopMessage?.id;
        lastTopMessage?.children.push(messages[0].id);
        convHistory.current_node = messages[messages.length - 1].id;
      }
    },
  },
});

export default useConversationStore;

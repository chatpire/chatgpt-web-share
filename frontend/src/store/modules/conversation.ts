import { defineStore } from 'pinia';

import {
  deleteConversationApi,
  getAllConversationsApi,
  getConversationHistoryApi,
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

    async fetchConversationHistory(conversation_id: string, fallback_cache = false) {
      // 解析历史记录
      if (this.conversationHistoryMap[conversation_id]) {
        return this.conversationHistoryMap[conversation_id];
      }
      const result = (await getConversationHistoryApi(conversation_id, fallback_cache)).data;
      this.$patch({
        conversationHistoryMap: {
          [conversation_id]: result,
        },
      });
    },

    createNewConversation(info: NewConversationInfo) {
      if (!info.title || !info.source || !info.model || !(info.source === 'openai_api' || info.source === 'openai_web')) {
        throw new Error('Invalid conversation info');
      }
      const currentTime = new Date().toISOString();
      this.newConversation = {
        source: info.source,
        conversation_id: newConversationId,
        title: info.title,
        current_model: info.model,
        create_time: currentTime,
        update_time: currentTime,
      };
      this.conversationHistoryMap[newConversationId] = {
        _id: newConversationId,
        source: info.source,
        title: info.title,
        current_model: info.model,
        create_time: currentTime,
        update_time: currentTime,
        mapping: {},
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
    addMessageToConversation(conversation_id: string, sendMessage: BaseChatMessage, recvMessage: BaseChatMessage) {
      if (!this.conversationHistoryMap[conversation_id]) {
        return;
      }
      if (!sendMessage.id || !recvMessage.id) {
        throw new Error('Message id is null');
      }

      const convHistory = this.conversationHistoryMap[conversation_id];
      convHistory.mapping[sendMessage.id] = sendMessage;
      convHistory.mapping[recvMessage.id] = recvMessage;

      // 这里只有在新建对话时调用
      if (convHistory.current_node === null) {
        convHistory.current_node = recvMessage.id;
      } else {
        const lastTopMessage = convHistory.mapping[convHistory.current_node!];
        sendMessage.parent = lastTopMessage?.id;
        lastTopMessage?.children.push(sendMessage.id);
        convHistory.current_node = recvMessage.id;
      }
      sendMessage.children = [recvMessage.id];
      recvMessage.parent = sendMessage.id;
    },
  },
});

export default useConversationStore;

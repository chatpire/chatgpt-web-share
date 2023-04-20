import { defineStore } from 'pinia';

import { deleteConversationApi, getAllConversationsApi, getConversationHistoryApi, setConversationTitleApi } from '@/api/chat';
import { ChatConversationDetail, ChatMessage } from '@/types/custom';
import { ConversationSchema } from '@/types/schema';

const useConversationStore = defineStore('conversation', {
  state: (): any => ({
    conversations: [] as Array<ConversationSchema>,
    conversationDetailMap: {} as Record<string, ChatConversationDetail>, // conv_id => ChatConversationDetail
  }),
  getters: {},
  actions: {
    async fetchAllConversations() {
      const result = (await getAllConversationsApi()).data;
      this.$patch({ conversations: result });
    },

    async fetchConversationHistory(conversation_id: string) {
      // 解析历史记录
      if (this.conversationDetailMap[conversation_id]) {
        return this.conversationDetailMap[conversation_id];
      }

      const result = (await getConversationHistoryApi(conversation_id)).data;

      const conv_detail: ChatConversationDetail = {
        id: conversation_id,
        current_node: result.current_node,
        title: result.title,
        create_time: result.create_time,
        mapping: {},
        model_name: result.model_name,
      };

      for (const message_id in result.mapping) {
        const current_msg = result.mapping[message_id];
        conv_detail.mapping[message_id] = {
          id: message_id,
          parent: current_msg.parent,
          children: current_msg.children,
          author_role: current_msg.message?.author?.role,
          model_slug: current_msg.message?.metadata?.model_slug,
          message: current_msg.message?.content?.parts.join('\n\n'),
        } as ChatMessage;
      }

      this.$patch({
        conversationDetailMap: {
          [conversation_id]: conv_detail,
        },
      });
    },

    addConversation(conversation: ConversationSchema) {
      this.conversations.push(conversation);
    },

    async deleteConversation(conversation_id: string) {
      await deleteConversationApi(conversation_id);
      delete this.conversationDetailMap[conversation_id];
      this.conversations = this.conversations.filter((conv: any) => conv.conversation_id !== conversation_id);
    },

    async changeConversationTitle(conversation_id: string, title: string) {
      await setConversationTitleApi(conversation_id, title);
      await this.fetchAllConversations();
      if (this.conversationDetailMap[conversation_id]) {
        this.conversationDetailMap[conversation_id].title = title;
      }
    },

    // 仅当收到新信息时调用，为了避免重复获取整个对话历史
    addMessageToConversation(conversation_id: string, sendMessage: ChatMessage, recvMessage: ChatMessage) {
      if (!this.conversationDetailMap[conversation_id]) {
        return;
      }

      const conv_detail = this.conversationDetailMap[conversation_id];
      conv_detail.mapping[sendMessage.id] = sendMessage;
      conv_detail.mapping[recvMessage.id] = recvMessage;

      // 这里只有在新建对话时调用
      if (conv_detail.current_node === null) {
        conv_detail.current_node = recvMessage.id;
      } else {
        const lastTopMessage = conv_detail.mapping[conv_detail.current_node];
        sendMessage.parent = lastTopMessage.id;
        lastTopMessage.children.push(sendMessage.id);
        conv_detail.current_node = recvMessage.id;
      }
      sendMessage.children = [recvMessage.id];
      recvMessage.parent = sendMessage.id;
    },
  },
});

export default useConversationStore;

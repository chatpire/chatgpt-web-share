<template>
  <div>
    <StatusCard />
    <div class="flex-grow flex flex-col">
      <!-- <div class="flex box-content" v-if="!newConversation"> -->
      <n-button
        secondary
        strong
        type="primary"
        :disabled="props.loading"
        @click="emits('new-conversation')"
      >
        <template #icon>
          <n-icon class="">
            <Add />
          </n-icon>
        </template>
        {{ $t('commons.newConversation') }}
      </n-button>
      <!-- </div> -->
      <n-scrollbar class="h-0 flex-grow mt-4">
        <n-menu
          ref="menuRef"
          v-model:value="convId"
          class="-mx-2"
          :content-style="{ backgroundColor: 'red' }"
          :disabled="props.loading"
          :options="menuOptions"
          :root-indent="18"
        />
      </n-scrollbar>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { Add } from '@vicons/ionicons5';
import { NEllipsis } from 'naive-ui';
import { computed, h } from 'vue';
import { useI18n } from 'vue-i18n';

import { useConversationStore } from '@/store';
import { ConversationSchema } from '@/types/schema';
import { dropdownRenderer, popupChangeConversationTitleDialog } from '@/utils/renders';
import { Dialog, Message } from '@/utils/tips';

import StatusCard from './StatusCard.vue';

const { t } = useI18n();

const conversationStore = useConversationStore();

const props = defineProps<{
  loading: boolean;
  value: string | null;
  newConv: ConversationSchema | null;
}>();

const emits = defineEmits<{
  (e: 'update:value', value: string | null): void;
  (e: 'new-conversation'): void;
}>();

// get and set to bind convId and value
const convId = computed<string | null>({
  get() {
    return props.value;
  },
  set(value: string | null) {
    emits('update:value', value);
  },
});

const menuOptions = computed(() => {
  // 根据 created_time 降序排序
  const sorted_conversations = conversationStore.conversations?.toSorted((a: ConversationSchema, b: ConversationSchema) => {
    // return a.create_time - b.create_time;
    if (!a.create_time) return -1;
    if (!b.create_time) return 1;
    const date_a = new Date(a.create_time),
      date_b = new Date(b.create_time);
    return date_b.getTime() - date_a.getTime();
  });
  const results = sorted_conversations?.map((conversation: ConversationSchema) => {
    return {
      label: () => h(NEllipsis, null, { default: () => conversation.title }),
      key: conversation.conversation_id,
      disabled: props.loading == true,
      extra: () => dropdownRenderer(conversation, handleDeleteConversation, handleChangeConversationTitle),
    };
  });
  if (props.newConv) {
    results?.unshift({
      label: props.newConv.title,
      key: props.newConv.conversation_id,
      disabled: props.loading == true,
    });
  }
  return results;
});

const handleDeleteConversation = (conversation_id: string | undefined) => {
  if (!conversation_id) return;
  const d = Dialog.info({
    title: t('commons.confirmDialogTitle'),
    content: t('tips.deleteConversation'),
    positiveText: t('commons.confirm'),
    negativeText: t('commons.cancel'),
    onPositiveClick: () => {
      d.loading = true;
      return new Promise((resolve) => {
        conversationStore
          .deleteConversation(conversation_id)
          .then(() => {
            Message.success(t('tips.deleteConversationSuccess'));
            if (convId.value == conversation_id) convId.value = null;
          })
          .catch(() => {
            Message.error(t('tips.deleteConversationFailed'));
          })
          .finally(() => {
            d.loading = false;
            resolve(true);
          });
      });
    },
  });
};

const handleChangeConversationTitle = (conversation_id: string | undefined) => {
  if (!conversation_id) return;
  popupChangeConversationTitleDialog(
    conversation_id,
    async (title: string) => {
      await conversationStore.changeConversationTitle(conversation_id, title);
    },
    () => {
      Message.success(t('tips.changeConversationTitleSuccess'));
    },
    () => {
      Message.error(t('tips.changeConversationTitleFailed'));
    }
  );
};
</script>

<style>
@media print {
  body * {
    visibility: hidden;
  }

  #print-content * {
    visibility: visible;
  }

  /* no margin in page */
  @page {
    margin-left: 0;
    margin-right: 0;
  }
}
</style>

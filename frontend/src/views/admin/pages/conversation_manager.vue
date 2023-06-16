<template>
  <div>
    <div class="mb-4 mt-1 ml-1 flex flex-row justify-between space-x-2">
      <div class="flex flex-row space-x-4">
        <n-button circle @click="refreshData">
          <template #icon>
            <n-icon>
              <RefreshFilled />
            </n-icon>
          </template>
        </n-button>
        <div v-show="checkedRowKeys.length !== 0" class="space-x-2">
          <n-button type="warning" secondary @click="handleInvalidateConversations">
            <template #icon>
              <n-icon>
                <EmojiFlagsFilled />
              </n-icon>
            </template>
            {{ $t('commons.invalidateConversation') }}
          </n-button>
          <n-button type="error" secondary @click="handleVanishConversations">
            <template #icon>
              <n-icon>
                <TrashOutline />
              </n-icon>
            </template>
            {{ $t('commons.vanishConversation') }}
          </n-button>
          <n-button type="info" secondary @click="handleAssignConversations">
            <template #icon>
              <n-icon>
                <PersonAddAlt1Filled />
              </n-icon>
            </template>
            {{ $t('commons.chooseUserToAssign') }}
          </n-button>
        </div>
      </div>
      <div class="space-x-2">
        <n-button @click="handleVanishAllInvalidConversations">
          {{ $t('commons.deleteInvalidConversations') }}
        </n-button>
        <n-button type="error" @click="handleClearAllConversations">
          {{ $t('commons.clearAllConversations') }}
        </n-button>
      </div>
    </div>
    <n-data-table
      v-model:checked-row-keys="checkedRowKeys"
      size="small"
      :columns="columns"
      :data="data"
      :bordered="true"
      :pagination="{
        pageSize: 20,
      }"
      :row-key="rowKey"
    />
  </div>
</template>

<script setup lang="ts">
import { TrashOutline } from '@vicons/ionicons5';
import { EmojiFlagsFilled, PersonAddAlt1Filled, RefreshFilled } from '@vicons/material';
import type { DataTableColumns } from 'naive-ui';
import { NButton, NIcon, NTooltip } from 'naive-ui';
import { computed, h, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';

import {
  assignConversationToUserApi,
  clearAllConversationApi,
  deleteConversationApi,
  getAdminAllConversationsApi,
  vanishConversationApi,
} from '@/api/conv';
import { BaseConversationSchema } from '@/types/schema';
import { getChatModelNameTrans } from '@/utils/chat';
import { getDateStringSorter } from '@/utils/table';
import { Dialog, Message } from '@/utils/tips';

import UserSelector from '../components/UserSelector.vue';
const { t } = useI18n();
const router = useRouter();
const data = ref<Array<BaseConversationSchema>>([]);
const rowKey = (row: BaseConversationSchema) => row.conversation_id;
const checkedRowKeys = ref<Array<string>>([]);

const refreshData = () => {
  getAdminAllConversationsApi(false).then((res) => {
    data.value = res.data;
  });
};

refreshData();

const columns: DataTableColumns<BaseConversationSchema> = [
  {
    type: 'selection',
  },
  {
    title: '#',
    key: 'id',
    sorter: 'default',
  },
  {
    title: 'UUID',
    key: 'conversation_id',
    render: (row) => {
      return h(
        NTooltip,
        { trigger: 'hover' },
        {
          trigger: () => row.conversation_id?.substring(0, 4),
          default: () => row.conversation_id,
        }
      );
    },
  },
  {
    title: t('labels.source'),
    key: 'type',
    render: (row) => {
      return t(`sources_short.${row.source}`);
    },
  },
  {
    title: t('commons.title'),
    key: 'title',
    sorter: 'default',
    render: (row) => {
      return h(
        NButton,
        {
          text: true,
          tag: 'a',
          href: router.resolve({
            name: 'conversationHistory',
            params: { conversation_id: row.conversation_id },
          }).href,
          target: '_blank',
        },
        {
          default: () => (row.title ? row.title : t('commons.empty')),
          // }
        }
      );
    },
  },
  {
    title: t('commons.belongToUser'),
    key: 'user_id',
    render: (row) => {
      return row.user_id ? row.user_id : t('commons.empty');
    },
    sorter: 'default',
  },
  {
    title: t('commons.createTime'),
    key: 'create_time',
    defaultSortOrder: 'descend',
    sorter: getDateStringSorter<BaseConversationSchema>('create_time'),
    render: (row) => {
      if (!row.create_time) return '';
      return h(
        NTooltip,
        { trigger: 'hover' },
        {
          trigger: () => new Date(row.create_time!).toLocaleString(),
          default: () => row.create_time,
        }
      );
    },
  },
  {
    title: t('commons.modelName'),
    key: 'current_model',
    render(row) {
      return row.current_model ? getChatModelNameTrans(row.current_model) : t('commons.unknown');
    },
    sorter: 'default',
  },
  {
    title: t('commons.isValid'),
    key: 'is_valid',
    render(row) {
      return row.is_valid ? t('commons.yes') : t('commons.no');
    },
    sorter: (a, b) => {
      const val_a = a.is_valid ? 1 : 0;
      const val_b = b.is_valid ? 1 : 0;
      return val_a - val_b;
    },
  },
];

const handleInvalidateConversations = () => {
  const d = Dialog.info({
    title: t('commons.invalidateConversation'),
    content: t('tips.invalidateConversation'),
    positiveText: t('commons.confirm'),
    negativeText: t('commons.cancel'),
    onPositiveClick: () => {
      d.loading = true;
      return new Promise((resolve, reject) => {
        const action = async () => {
          for (const conversation_id of checkedRowKeys.value) {
            await deleteConversationApi(conversation_id);
          }
        };
        action()
          .then(() => {
            Message.success(t('tips.deleteConversationSuccess'));
            refreshData();
            resolve(true);
          })
          .catch((err) => {
            Message.error(t('tips.deleteConversationFailed') + ': ' + err);
            reject(err);
          })
          .finally(() => {
            d.loading = false;
          });
      });
    },
  });
};

const handleVanishConversations = () => {
  const d = Dialog.warning({
    title: t('commons.vanishConversation'),
    content: t('tips.vanishConversation'),
    positiveText: t('commons.confirm'),
    negativeText: t('commons.cancel'),
    onPositiveClick: () => {
      d.loading = true;
      return new Promise((resolve, reject) => {
        const action = async () => {
          for (const conversation_id of checkedRowKeys.value) {
            await vanishConversationApi(conversation_id);
            await new Promise((resolve) => setTimeout(resolve, 200));
          }
        };
        action()
          .then(() => {
            Message.success(t('tips.success'));
            refreshData();
            checkedRowKeys.value = [];
            resolve(true);
          })
          .catch((err) => {
            Message.error(t('tips.failed') + ': ' + err);
            reject(err);
          })
          .finally(() => {
            d.loading = false;
          });
      });
    },
  });
};

const handleAssignConversations = () => {
  let username: string | null = null;
  const d = Dialog.warning({
    title: t('commons.chooseUserToAssign'),
    content: () =>
      h(UserSelector, {
        'onUpdate:value': (val: string | null) => {
          username = val;
        },
      }),
    positiveText: t('commons.confirm'),
    negativeText: t('commons.cancel'),
    onPositiveClick: () => {
      d.loading = true;
      return new Promise((resolve, reject) => {
        if (username === null) {
          Message.error(t('errors.noUserSelected'));
          d.loading = false;
          reject(false);
          return;
        }
        const action = async () => {
          for (const conversation_id of checkedRowKeys.value) {
            await assignConversationToUserApi(conversation_id, username!);
          }
        };
        action()
          .then(() => {
            Message.success(t('tips.success'));
            refreshData();
            checkedRowKeys.value = [];
            resolve(true);
          })
          .catch((err) => {
            Message.error(t('tips.failed') + ': ' + err);
            reject(err);
          })
          .finally(() => {
            d.loading = false;
          });
      });
    },
  });
};

const handleVanishAllInvalidConversations = () => {
  const d = Dialog.info({
    title: t('commons.deleteInvalidConversations'),
    content: t('commons.deleteInvalidConversationsConfirm'),
    positiveText: t('commons.confirm'),
    negativeText: t('commons.cancel'),
    onPositiveClick: () => {
      d.loading = true;
      const action = async () => {
        for (const conversation of data.value) {
          if (!conversation.is_valid) {
            await vanishConversationApi(conversation.conversation_id!);
            await new Promise((resolve) => setTimeout(resolve, 200));
          }
        }
        data.value = data.value.filter((conversation) => conversation.is_valid);
      };
      return new Promise((resolve, reject) => {
        action()
          .then(() => {
            Message.success(t('tips.deleteConversationSuccess'));
            refreshData();
            checkedRowKeys.value = [];
            resolve(true);
          })
          .catch((err) => {
            console.error(err);
            Message.error(t('tips.deleteConversationFailed'));
            reject();
          })
          .finally(() => {
            d.loading = false;
          });
      });
    },
  });
};

const handleClearAllConversations = () => {
  const d = Dialog.error({
    title: t('commons.clearAllConversations'),
    content: t('commons.readyToClearAllConversations'),
    positiveText: t('commons.confirm'),
    negativeText: t('commons.cancel'),
    onPositiveClick: () => {
      d.loading = true;
      return new Promise((resolve, reject) => {
        clearAllConversationApi()
          .then(() => {
            Message.success(t('tips.deleteConversationSuccess'));
            refreshData();
            checkedRowKeys.value = [];
            resolve(true);
          })
          .catch((err) => {
            console.error(err);
            Message.error(t('tips.deleteConversationFailed'));
            reject();
          })
          .finally(() => {
            d.loading = false;
          });
      });
    },
  });
};
</script>

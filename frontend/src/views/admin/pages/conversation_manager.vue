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
        <n-button circle @click="syncConversations">
          <template #icon>
            <n-icon>
              <CloudDownloadFilled />
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
      :scroll-x="1600"
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
import { CloudDownloadFilled, EmojiFlagsFilled, PersonAddAlt1Filled, RefreshFilled } from '@vicons/material';
import type { DataTableColumns } from 'naive-ui';
import { NButton, NEllipsis, NIcon, NTooltip } from 'naive-ui';
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
import { runActionSyncOpenaiWebConversations } from '@/api/system';
import { getAllUserApi } from '@/api/user';
import { BaseConversationSchema, OpenaiWebConversationSchema, UserReadAdmin } from '@/types/schema';
import { getChatModelNameTrans } from '@/utils/chat';
import { getDateStringSorter } from '@/utils/table';
import { Dialog, Message } from '@/utils/tips';

import UserSelector from '../components/UserSelector.vue';
const { t } = useI18n();
const router = useRouter();
const data = ref<BaseConversationSchema[]>([]);
const userInfo = ref<UserReadAdmin[] | null>(null);
const rowKey = (row: BaseConversationSchema) => row.conversation_id;
const checkedRowKeys = ref<Array<string>>([]);

const refreshData = () => {
  getAdminAllConversationsApi(false).then((res) => {
    data.value = res.data;
  });
};

const syncConversations = () => {
  const d = Dialog.info({
    title: t('dialog.title.syncConversations'),
    content: t('dialog.content.syncConversations'),
    positiveText: t('commons.confirm'),
    negativeText: t('commons.cancel'),
    onPositiveClick: () => {
      d.loading = true;
      return new Promise((resolve, reject) => {
        runActionSyncOpenaiWebConversations()
          .then(() => {
            Message.success(t('tips.success'));
            refreshData();
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

const userIdFilterOptions = computed(() => {
  return userInfo.value?.map((user) => {
    return {
      label: user.username,
      value: user.id,
    };
  });
});

const columns = computed<DataTableColumns<BaseConversationSchema>>(() => [
  {
    type: 'selection',
  },
  // {
  //   title: '#',
  //   key: 'id',
  //   sorter: 'default',
  // },
  {
    title: 'UUID',
    key: 'conversation_id',
    width: 80,
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
    width: 80,
    render: (row) => {
      return t(`sources_short.${row.source}`);
    },
  },
  {
    title: t('commons.title'),
    key: 'title',
    sorter: 'default',
    width: 450,
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
          default: () =>
            h(
              NEllipsis,
              { style: 'max-width: 400px' },
              { default: () => (row.title ? row.title : t('commons.empty')) }
            ),
        }
      );
    },
  },
  {
    title: t('commons.belongToUser'),
    key: 'user_id',
    width: 160,
    render: (row) => {
      // return userInfo.value?.find((user) => user.id === row.user_id)?.username || t('commons.empty');
      const user = userInfo.value?.find((user) => user.id === row.user_id);
      return h(
        NTooltip,
        { trigger: 'hover' },
        {
          trigger: () => user?.username || t('commons.empty'),
          default: () => {
            let result = user?.nickname || user?.username || t('commons.empty');
            if (user?.remark) {
              result += ` (${user.remark})`;
            }
            return result;
          },
        }
      );
    },
    ellipsis: {
      tooltip: true,
    },
    filterOptions: userIdFilterOptions.value,
    defaultFilterOptionValues: userInfo.value?.map((user) => user.id),
    filter: (value, row) => {
      return row.user_id === value;
    },
  },
  {
    title: 'Source ID',
    key: 'source_id',
    width: 80,
    render: (row) => {
      let result = 'N/A';
      if (row.source === 'openai_web') {
        const conv = row as OpenaiWebConversationSchema;
        result = conv.source_id || t('commons.empty');
      }
      return h(
        NTooltip,
        { trigger: 'hover' },
        {
          trigger: () => result?.substring(0, 4),
          default: () => result,
        }
      );
    },
  },
  {
    title: t('commons.createTime'),
    key: 'create_time',
    width: 200,
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
    width: 200,
    render(row) {
      return row.current_model ? getChatModelNameTrans(row.current_model) : t('commons.unknown');
    },
    sorter: 'default',
  },
  {
    title: t('commons.isValid'),
    key: 'is_valid',
    width: 120,
    render(row) {
      return row.is_valid ? t('commons.yes') : t('commons.no');
    },
    sorter: (a, b) => {
      const val_a = a.is_valid ? 1 : 0;
      const val_b = b.is_valid ? 1 : 0;
      return val_a - val_b;
    },
  },
]);

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

getAllUserApi().then((res) => {
  userInfo.value = res.data;
});

getAdminAllConversationsApi(false).then((res) => {
  data.value = res.data;
});
</script>

<template>
  <div class="mb-4 mt-1 flex flex-row justify-between">
    <n-button @click="handleVanishAllInvalidConversations"> {{ $t("commons.deleteInvalidConversations") }} </n-button>
    <div class="space-x-2" v-show="checkedRowKeys.length !== 0">
      <n-button type="warning" secondary @click="handleInvalidateConversations">
        <template #icon>
          <n-icon>
            <EmojiFlagsFilled />
          </n-icon>
        </template>
        {{ $t("commons.invalidateConversation") }}
      </n-button>
      <n-button type="error" secondary @click="handleVanishConversations">
        <template #icon>
          <n-icon>
            <TrashOutline />
          </n-icon>
        </template>
        {{ $t("commons.vanishConversation") }}
      </n-button>
      <n-button type="info" secondary @click="handleAssignConversations">
        <template #icon>
          <n-icon>
            <PersonAddAlt1Filled />
          </n-icon>
        </template>
        {{ $t("commons.chooseUserToAssign") }}
      </n-button>
    </div>
  </div>
  <n-data-table size="small" :columns="columns" :data="data" :bordered="true" :pagination="{
    pageSize: 20
  }" :row-key="rowKey" v-model:checked-row-keys="checkedRowKeys" />
</template>

<script setup lang="ts">
import { ref, h } from 'vue';
import type { DataTableColumns } from 'naive-ui'
import { NButton, NIcon, NTooltip } from 'naive-ui';
import { ConversationSchema } from '@/types/schema';
import { useI18n } from 'vue-i18n';
import { Dialog, Message } from '@/utils/tips';
import { TrashOutline } from '@vicons/ionicons5';
import { EmojiFlagsFilled, PersonAddAlt1Filled } from '@vicons/material';
import UserSelector from './UserSelector.vue';
import { assignConversationToUserApi, deleteConversationApi, getAllConversationsApi, vanishConversationApi } from '@/api/chat';
import { getModelNameTrans, modelNameMap } from '@/utils/renders';

const { t } = useI18n();

const data = ref<Array<ConversationSchema>>([]);
const rowKey = (row: ConversationSchema) => row.conversation_id;
const checkedRowKeys = ref<Array<string>>([]);

getAllConversationsApi(false).then(res => {
  data.value = res.data;
})

const columns: DataTableColumns<ConversationSchema> = [
  {
    type: 'selection',
  },
  {
    title: "#",
    key: 'id',
    sorter: 'default'
  },
  {
    title: "UUID",
    key: 'conversation_id',
    render: (row) => {
      return h(NTooltip, { trigger: "hover" }, {
        trigger: () => row.conversation_id?.substring(0, 4),
        default: () => row.conversation_id
      })
    }
  },
  {
    title: t("commons.title"),
    key: 'title',
    sorter: 'default'
  },
  {
    title: t("commons.belongToUser"),
    key: 'user_id',
    render: (row) => {
      return row.user_id ? row.user_id : t("commons.empty")
    },
    sorter: 'default'
  },
  {
    title: t("commons.createTime"),
    key: 'create_time',
    defaultSortOrder: 'descend',
    sorter: (a, b) => {
      if (!a.create_time || !b.create_time) return 0;
      return new Date(a.create_time!).getTime() - new Date(b.create_time!).getTime()
    },
    render: (row) => {
      if (!row.create_time) return '';
      return h(NTooltip, { trigger: "hover" }, {
        trigger: () => new Date(row.create_time! + 'Z').toLocaleString(),
        default: () => row.create_time
      })

    }
  },
  {
    title: t("commons.modelName"),
    key: 'model_name',
    render(row) {
      return row.model_name ? getModelNameTrans(row.model_name) : t("commons.unknown")
    },
    sorter: 'default'
  },
  {
    title: t("commons.isValid"),
    key: 'is_valid',
    render(row) {
      return row.is_valid ? t("commons.yes") : t("commons.no")
    },
    sorter: (a, b) => {
      const val_a = a.is_valid ? 1 : 0;
      const val_b = b.is_valid ? 1 : 0;
      return val_a - val_b;
    }
  },
]

const handleInvalidateConversations = () => {
  const d = Dialog.info({
    title: t("commons.invalidateConversation"),
    content: t("tips.invalidateConversation"),
    positiveText: t("commons.confirm"),
    negativeText: t("commons.cancel"),
    onPositiveClick: () => {
      d.loading = true;
      return new Promise((resolve, reject) => {
        const action = async () => {
          for (const conversation_id of checkedRowKeys.value) {
            await deleteConversationApi(conversation_id)
          }
        }
        action().then(() => {
          Message.success(t("tips.deleteConversationSuccess"))
          getAllConversationsApi(false).then(res => {
            data.value = res.data;
          })
          resolve(true)
        }).catch((err) => {
          Message.error(t("tips.deleteConversationFailed") + ": " + err)
          reject(err)
        }).finally(() => {
          d.loading = false;
        })
      })
    }
  })
}

const handleVanishConversations = () => {
  const d = Dialog.warning({
    title: t("commons.vanishConversation"),
    content: t("tips.vanishConversation"),
    positiveText: t("commons.confirm"),
    negativeText: t("commons.cancel"),
    onPositiveClick: () => {
      d.loading = true;
      return new Promise((resolve, reject) => {
        const action = async () => {
          for (const conversation_id of checkedRowKeys.value) {
            await vanishConversationApi(conversation_id)
          }
        }
        action().then(() => {
          Message.success(t("tips.success"))
          getAllConversationsApi(false).then(res => {
            data.value = res.data;
          })
          checkedRowKeys.value = [];
          resolve(true)
        }).catch((err) => {
          Message.error(t("tips.failed") + ": " + err)
          reject(err)
        }).finally(() => {
          d.loading = false;
        })
      })
    }
  })
}

const handleAssignConversations = () => {
  let username: string | null = null;
  const d = Dialog.warning({
    title: t("commons.chooseUserToAssign"),
    content: () => h(UserSelector, {
      'onUpdate:value': (val: string | null) => {
        username = val;
      }
    }),
    positiveText: t("commons.confirm"),
    negativeText: t("commons.cancel"),
    onPositiveClick: () => {
      d.loading = true;
      return new Promise((resolve, reject) => {
        if (username === null) {
          Message.error(t("errors.noUserSelected"));
          d.loading = false;
          reject(false);
          return;
        }
        const action = async () => {
          for (const conversation_id of checkedRowKeys.value) {
            await assignConversationToUserApi(conversation_id, username!)
          }
        }
        action().then(() => {
          Message.success(t("tips.success"))
          getAllConversationsApi(false).then(res => {
            data.value = res.data;
          })
          checkedRowKeys.value = [];
          resolve(true)
        }).catch((err) => {
          Message.error(t("tips.failed") + ": " + err)
          reject(err)
        }).finally(() => {
          d.loading = false;
        })
      })
    }
  })
}

const handleVanishAllInvalidConversations = () => {
  const d = Dialog.info({
    title: t("commons.deleteInvalidConversations"),
    content: t("commons.deleteInvalidConversationsConfirm"),
    positiveText: t("commons.confirm"),
    negativeText: t("commons.cancel"),
    onPositiveClick: () => {
      d.loading = true;
      const action = async () => {
        for (const conversation of data.value) {
          if (!conversation.is_valid) {
            await vanishConversationApi(conversation.conversation_id!)
          }
        }
        data.value = data.value.filter(conversation => conversation.is_valid)
      }
      return new Promise((resolve, reject) => {
        action().then(() => {
          Message.success(t("tips.deleteConversationSuccess"))
          checkedRowKeys.value = [];
          resolve(true)
        }).catch((err) => {
          Message.error(t("tips.deleteConversationFailed"))
          reject()
        }).finally(() => {
          d.loading = false;
        })
      })
    }
  })
}
</script>

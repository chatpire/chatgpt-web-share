<template>
  <div class="mb-4">
    <n-button @click="handleVanishInvalidConversations"> {{ $t("commons.deleteInvalidConversations") }} </n-button>
  </div>
  <n-data-table size="small" :columns="columns" :data="data" :bordered="true" :pagination="{
    pageSize: 20
  }" />
</template>

<script setup lang="ts">
import { ref, reactive, computed, h } from 'vue';
import { useUserStore } from '@/store';
import type { DataTableColumns } from 'naive-ui'
import { NButton, NIcon, NTooltip } from 'naive-ui';
import { ConversationSchema, UserCreate, UserRead } from '@/types/schema';
import { useI18n } from 'vue-i18n';
import { getAllUserApi, registerApi } from '@/api/user';
import { Dialog, Message } from '@/utils/tips';
import { TrashOutline } from '@vicons/ionicons5';
import { EmojiFlagsFilled, PersonAddAlt1Filled } from '@vicons/material';
import UserSelector from './UserSelector.vue';
import { assignConversationToUserApi, deleteConversationApi, getAllConversationsApi, vanishConversationApi } from '@/api/chat';
import { modelNameMap } from '@/utils/renders';

const { t } = useI18n();

const data = ref<Array<ConversationSchema>>([]);

getAllConversationsApi(false).then(res => {
  data.value = res.data;
})

const columns: DataTableColumns<ConversationSchema> = [
  {
    title: "#",
    key: 'id'
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
    key: 'title'
  },
  {
    title: t("commons.belongToUser"),
    key: 'user_id',
    render: (row) => {
      return row.user_id ? row.user_id : t("commons.empty")
    }
  },
  {
    title: t("commons.createTime"),
    key: 'create_time',
    render: (row) => {
      if (!row.create_time) return '';
      // parse datetime, get local string
      return h(NTooltip, { trigger: "hover" }, {
        trigger: () => new Date(row.create_time!).toLocaleDateString(),
        default: () => row.create_time
      })

    }
  },
  {
    title: t("commons.modelName"),
    key: 'model_name',
    render(row) {
      return row.model_name ? modelNameMap[row.model_name!] : t("commons.unknown")
    }
  },
  {
    title: t("commons.isValid"),
    key: 'is_valid',
    render(row) {
      return row.is_valid ? t("commons.yes") : t("commons.no")
    }
  },
  {
    title: t("commons.actions"),
    key: 'actions',
    render(row) {
      // TODO: 删除、修改密码，两个按钮
      return h("div", {
        class: "flex justify-start space-x-2"
      }, [
        h(NButton, {
          size: "small",
          type: "warning",
          circle: true,
          secondary: true,
          disabled: !row.is_valid,
          onClick: () => {
            const d = Dialog.info({
              title: t("commons.invalidateConversation"),
              content: t("tips.invalidateConversation"),
              positiveText: t("commons.confirm"),
              negativeText: t("commons.cancel"),
              onPositiveClick: () => {
                d.loading = true;
                return new Promise((resolve, reject) => {
                  deleteConversationApi(row.conversation_id!).then(() => {
                    Message.success(t("tips.success"));
                    getAllConversationsApi(false).then(res => {
                      data.value = res.data;
                    })
                    resolve(true);
                  }).catch((err: any) => {
                    Message.error(t("tips.failed") + ": " + err);
                    reject(err);
                  }).finally(() => {
                    d.loading = false;
                  })
                })
              }
            })
          }
        }, {
          icon: () => h(NIcon, null, {
            default: () => h(EmojiFlagsFilled)
          })
        }),
        h(NButton, {
          size: "small",
          type: "error",
          circle: true,
          secondary: true,
          // disabled: row.is_valid,
          onClick: () => {
            const d = Dialog.warning({
              title: t("commons.vanishConversation"),
              content: t("tips.vanishConversation"),
              positiveText: t("commons.confirm"),
              negativeText: t("commons.cancel"),
              onPositiveClick: () => {
                d.loading = true;
                return new Promise((resolve, reject) => {
                  vanishConversationApi(row.conversation_id!).then(() => {
                    Message.success(t("tips.success"));
                    getAllConversationsApi(false).then(res => {
                      data.value = res.data;
                    })
                    resolve(true);
                  }).catch((err: any) => {
                    Message.error(t("tips.failed") + ": " + err);
                    reject(err);
                  }).finally(() => {
                    d.loading = false;
                  })
                })
              }
            })
          }
        }, {
          icon: () => h(NIcon, null, {
            default: () => h(TrashOutline)
          })
        }),
        h(NButton, {
          size: "small",
          type: "info",
          circle: true,
          secondary: true,
          // disabled: row.is_valid,
          onClick: () => {
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
                  if (username == null) {
                    reject("No user selected");
                  }
                  assignConversationToUserApi(row.conversation_id!, username!).then(() => {
                    Message.success(t("tips.success"));
                    getAllConversationsApi(false).then(res => {
                      data.value = res.data;
                    })
                    resolve(true);
                  }).catch((err: any) => {
                    Message.error(t("tips.failed") + ": " + err);
                    reject(err);
                  }).finally(() => {
                    d.loading = false;
                  })
                })
              }
            })
          }
        }, {
          icon: () => h(NIcon, null, {
            default: () => h(PersonAddAlt1Filled)
          })
        })

      ])
    }
  }
]

const handleVanishInvalidConversations = () => {
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

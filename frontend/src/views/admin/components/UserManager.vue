<template>
  <div class="mb-4">
    <n-button type="primary" @click="handleAddUser"> {{ $t("commons.addUser") }} </n-button>
  </div>
  <n-data-table :scroll-x="1200" size="small" :columns="columns" :data="data" :bordered="true" :pagination="{
    pageSize: 10
  }" />
</template>

<script setup lang="ts">
import { ref, reactive, computed, h } from 'vue';
import { useUserStore } from '@/store';
import { DataTableColumns, NButton, NIcon } from 'naive-ui'
import { LimitSchema, UserCreate, UserRead, chatStatusMap } from '@/types/schema';
import { useI18n } from 'vue-i18n';
import { getAllUserApi, registerApi, deleteUserApi, resetUserPasswordApi, updateUserLimitApi } from '@/api/user';
import { Dialog, Message } from '@/utils/tips';
import { TrashOutline, Pencil } from '@vicons/ionicons5';
import { PasswordRound } from '@vicons/material';
import EditUserForm from './EditUserForm.vue';
import EditLimitForm from './EditLimitForm.vue';
import { getCountTrans, popupResetUserPasswordDialog } from '@/utils/renders';

const { t } = useI18n();

const userStore = useUserStore();

const data = ref<Array<UserRead>>([]);

getAllUserApi().then(res => {
  data.value = res.data;
})

const columns: DataTableColumns<UserRead> = [
  {
    title: "#",
    key: 'id'
  },
  {
    title: t("commons.username"),
    key: 'username'
  },
  {
    title: t("commons.nickname"),
    key: 'nickname'
  },
  {
    title: t("commons.email"),
    key: 'email'
  },
  {
    title: t("commons.isSuperuser"),
    key: 'is_superuser',
    render(row) {
      return row.is_superuser ? t("commons.yes") : t("commons.no")
    }
  },
  {
    title: t("commons.activeTime"),
    key: 'active_time',
    render(row) {
      return row.active_time ? new Date(row.active_time).toLocaleString() : t("commons.neverActive")
    }
  },
  {
    title: t("commons.maxConversationCount"),
    key: 'max_conv_count',
    render(row) {
      return getCountTrans(row.max_conv_count!);
    }
  },
  {
    title: t("commons.availableAskCount"),
    key: 'available_ask_count',
    render(row) {
      return getCountTrans(row.available_ask_count!);
    }
  },
  {
    title: t("commons.availableGPT4AskCount"),
    key: 'available_gpt4_ask_count',
    render(row) {
      return getCountTrans(row.available_gpt4_ask_count!);
    }
  },
  {
    title: t("commons.canUsePaidModel"),
    key: 'can_use_paid',
    render(row) {
      return row.can_use_paid ? t("commons.yes") : t("commons.no")
    }
  },
  {
    title: t("commons.canUseGPT4Model"),
    key: 'can_use_gpt4',
    render(row) {
      return row.can_use_gpt4 ? t("commons.yes") : t("commons.no")
    }
  },
  {
    title: t('commons.status'),
    key: 'chat_status',
    render(row) {
      console.log(row.chat_status, chatStatusMap)
      return row.chat_status ? t(chatStatusMap[row.chat_status as keyof typeof chatStatusMap]) : ''
    }
  },
  {
    title: t("commons.actions"),
    key: 'actions',
    fixed: 'right',
    render(row) {
      // TODO: 删除、修改密码，两个按钮
      return h("div", {
        class: "flex justify-start space-x-2"
      }, [
        h(NButton, {
          size: "small",
          type: "error",
          circle: true,
          secondary: true,
          onClick: () => {
            const d = Dialog.warning({
              title: t("commons.deleteUser"),
              content: t("tips.deleteUserConfirm"),
              positiveText: t("commons.confirm"),
              negativeText: t("commons.cancel"),
              onPositiveClick: () => {
                d.loading = true;
                return new Promise((resolve, reject) => {
                  deleteUserApi(row.id).then(res => {
                    Message.success(t("tips.deleteUserSuccess"));
                    getAllUserApi().then(res => {
                      data.value = res.data;
                    })
                    resolve(true);
                  }).catch(err => {
                    Message.error(t("tips.deleteUserFailed") + ": " + err);
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
          onClick: () => {
            popupResetUserPasswordDialog(
              async (password: string) => {
                await resetUserPasswordApi(row.id, password);
              },
              () => { Message.info(t("tips.resetUserPasswordSuccess")) },
              () => { Message.error(t("tips.resetUserPasswordFailed")) }
            )
          }
        }, {
          icon: () => h(NIcon, null, {
            default: () => h(PasswordRound)
          })
        }),
        h(NButton, {
          size: "small",
          type: "primary",
          circle: true,
          secondary: true,
          onClick: handleSetUserLimit(row)
        }, {
          icon: () => h(NIcon, null, {
            default: () => h(Pencil)
          })
        })

      ])
    }
  }
]

const handleAddUser = () => {
  const user = ref<UserCreate>({
    username: '',
    nickname: '',
    email: '',
    password: '',
    is_superuser: false
  })
  const d = Dialog.info({
    title: t("commons.addUser"),
    content: () => h(EditUserForm, {
      user: user.value,
      'onUpdate:user': (newUser: UserCreate) => {
        user.value = newUser;
      }
    }, { default: () => "" }),
    positiveText: t("commons.confirm"),
    negativeText: t("commons.cancel"),
    onPositiveClick: () => {
      d.loading = true;
      return new Promise((resolve, reject) => {
        registerApi(user.value).then(res => {
          Message.success(t("commons.addUserSuccess"));
          getAllUserApi().then(res => {
            data.value = res.data;
          })
          resolve(true);
        }).catch(err => {
          Message.error(t("commons.addUserFailed") + ": " + err);
          reject(err);
        }).finally(() => {
          d.loading = false;
        })
      })
    }
  })
}

const handleSetUserLimit = (user: UserRead) => () => {
  const limit = ref<LimitSchema>({
    max_conv_count: user.max_conv_count,
    available_ask_count: user.available_ask_count,
    can_use_paid: user.can_use_paid,
    can_use_gpt4: user.can_use_gpt4,
    available_gpt4_ask_count: user.available_gpt4_ask_count
  })
  const d = Dialog.info({
    title: t("commons.setUserLimit"),
    content: () => h(EditLimitForm, {
      limit: limit.value,
      'onUpdate:limit': (newLimit: LimitSchema) => {
        limit.value = newLimit;
      }
    }, { default: () => "" }),
    positiveText: t("commons.confirm"),
    negativeText: t("commons.cancel"),
    onPositiveClick: () => {
      d.loading = true;
      return new Promise((resolve, reject) => {
        updateUserLimitApi(user.id, limit.value).then(res => {
          Message.success(t("commons.setUserLimitSuccess"));
          getAllUserApi().then(res => {
            data.value = res.data;
          })
          resolve(true);
        }).catch(err => {
          reject(err);
        }).finally(() => {
          d.loading = false;
        })
      })
    }
  })
}

</script>

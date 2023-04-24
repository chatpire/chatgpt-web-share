<template>
  <div>
    <div class="mb-4 mt-1 ml-1 flex flex-row space-x-2 justify-between">
      <n-button
        circle
        @click="refreshData"
      >
        <template #icon>
          <n-icon>
            <RefreshFilled />
          </n-icon>
        </template>
      </n-button>
      <n-button
        type="primary"
        @click="handleAddUser"
      >
        {{ $t('commons.addUser') }}
      </n-button>
    </div>
    <n-data-table
      :scroll-x="1400"
      size="small"
      :columns="columns"
      :data="data"
      :bordered="true"
      :pagination="{
        pageSize: 20,
      }"
    />
  </div>
</template>

<script setup lang="ts">
import { Pencil, TrashOutline } from '@vicons/ionicons5';
import { PasswordRound, RefreshFilled } from '@vicons/material';
import { DataTableColumns, NButton, NIcon } from 'naive-ui';
import { h, ref } from 'vue';
import { useI18n } from 'vue-i18n';

import { deleteUserApi, getAllUserApi, registerApi, updateUserByIdApi, updateUserSettingApi } from '@/api/user';
import { useUserStore } from '@/store';
import { chatStatusMap, UserCreate, UserReadAdmin, UserSettingSchema, UserUpdateAdmin } from '@/types/schema';
import {getCountTrans, getRevChatModelNameTrans} from '@/utils/chat';
import { popupResetUserPasswordDialog } from '@/utils/renders';
import { Dialog, Message } from '@/utils/tips';

import EditUserForm from '../components/EditUserForm.vue';
import EditUserSettingForm from '../components/EditUserSettingForm.vue';

const { t } = useI18n();

const userStore = useUserStore();

const data = ref<Array<UserReadAdmin>>([]);

const refreshData = () => {
  getAllUserApi().then((res) => {
    data.value = res.data;
    // Message.success(t("tips.refreshed"));
  });
};

getAllUserApi().then((res) => {
  data.value = res.data;
});

const columns: DataTableColumns<UserReadAdmin> = [
  {
    title: '#',
    key: 'id',
  },
  {
    title: t('commons.username'),
    key: 'username',
  },
  {
    title: t('commons.nickname'),
    key: 'nickname',
  },
  {
    title: t('commons.status'),
    key: 'rev_chat_status',
    render(row) {
      return row.rev_chat_status ? t(chatStatusMap[row.rev_chat_status as keyof typeof chatStatusMap]) : '';
    },
    sorter: 'default',
  },
  {
    title: t('commons.activeTime'),
    key: 'active_time',
    render(row) {
      return row.active_time ? new Date(row.active_time + 'Z').toLocaleString() : t('commons.neverActive');
    },
    sorter: (a, b) => {
      if (!a.active_time || !b.active_time) return 0;
      return new Date(a.active_time!).getTime() - new Date(b.active_time!).getTime();
    },
  },
  {
    title: t('commons.maxConversationCount'),
    key: 'max_conv_count',
    render(row) {
      return row.setting.revchatgpt_ask_limits ? getCountTrans(row.setting.revchatgpt_ask_limits.max_conv_count) : t('commons.unlimited');
    },
  },
  {
    title: t('commons.availableTotalAskCount'),
    key: 'available_ask_count',
    render(row) {
      // return getCountTrans(row.available_ask_count!);
      return row.setting.revchatgpt_ask_limits ? getCountTrans(row.setting.revchatgpt_ask_limits.total_count) : t('commons.unlimited');
    },
  },
  {
    title: t('commons.availableAskCountPerModel'),
    key: 'availableAskCountPerModel',
    render(row) {
      if (row.setting.revchatgpt_available_models && row.setting.revchatgpt_ask_limits) {
        const per_model_count = row.setting.revchatgpt_ask_limits!.per_model_count;
        return row.setting.revchatgpt_available_models
          .map((model) => {
            if (per_model_count && per_model_count[model]) {
              return `${getRevChatModelNameTrans(model)}: ${getCountTrans(per_model_count[model])}`;
            }
          })
          .join(', ');
      } else {
        return t('commons.unlimited');
      }
    },
  },
  {
    title: t('commons.availableModels'),
    key: 'availableModels',
    render(row) {
      return row.setting.revchatgpt_available_models ? row.setting.revchatgpt_available_models.map((model) => getRevChatModelNameTrans(model)).join(', ') : t('commons.unlimited');
    },
  },
  {
    title: t('commons.email'),
    key: 'email',
  },
  {
    title: t('commons.isSuperuser'),
    key: 'is_superuser',
    render(row) {
      return row.is_superuser ? t('commons.yes') : t('commons.no');
    },
  },
  {
    title: t('commons.actions'),
    key: 'actions',
    fixed: 'right',
    render(row) {
      // TODO: 删除、修改密码，两个按钮
      return h(
        'div',
        {
          class: 'flex justify-start space-x-2',
        },
        [
          h(
            NButton,
            {
              size: 'small',
              type: 'error',
              circle: true,
              secondary: true,
              onClick: () => {
                const d = Dialog.warning({
                  title: t('commons.deleteUser'),
                  content: t('tips.deleteUserConfirm'),
                  positiveText: t('commons.confirm'),
                  negativeText: t('commons.cancel'),
                  onPositiveClick: () => {
                    d.loading = true;
                    return new Promise((resolve, reject) => {
                      deleteUserApi(row.id)
                        .then((res) => {
                          Message.success(t('tips.deleteUserSuccess'));
                          getAllUserApi().then((res) => {
                            data.value = res.data;
                          });
                          resolve(true);
                        })
                        .catch((err) => {
                          Message.error(t('tips.deleteUserFailed') + ': ' + err);
                          reject(err);
                        })
                        .finally(() => {
                          d.loading = false;
                        });
                    });
                  },
                });
              },
            },
            {
              icon: () =>
                h(NIcon, null, {
                  default: () => h(TrashOutline),
                }),
            }
          ),
          h(
            NButton,
            {
              size: 'small',
              type: 'info',
              circle: true,
              secondary: true,
              onClick: () => {
                popupResetUserPasswordDialog(
                  async (password: string) => {
                    await updateUserByIdApi(row.id, {
                      password
                    });
                  },
                  () => {
                    Message.info(t('tips.resetUserPasswordSuccess'));
                  },
                  () => {
                    Message.error(t('tips.resetUserPasswordFailed'));
                  }
                );
              },
            },
            {
              icon: () =>
                h(NIcon, null, {
                  default: () => h(PasswordRound),
                }),
            }
          ),
          h(
            NButton,
            {
              size: 'small',
              type: 'primary',
              circle: true,
              secondary: true,
              onClick: handleUpdateUserSetting(row),
            },
            {
              icon: () =>
                h(NIcon, null, {
                  default: () => h(Pencil),
                }),
            }
          ),
        ]
      );
    },
  },
];

const handleAddUser = () => {
  const user = ref<UserCreate>({
    username: '',
    nickname: '',
    email: '',
    password: '',
    is_superuser: false,
  });
  const d = Dialog.info({
    title: t('commons.addUser'),
    content: () =>
      h(
        EditUserForm,
        {
          user: user.value,
          'onUpdate:user': (newUser: UserCreate) => {
            user.value = newUser;
          },
        },
        { default: () => '' }
      ),
    positiveText: t('commons.confirm'),
    negativeText: t('commons.cancel'),
    onPositiveClick: () => {
      d.loading = true;
      return new Promise((resolve, reject) => {
        registerApi(user.value)
          .then((res) => {
            Message.success(t('commons.addUserSuccess'));
            getAllUserApi().then((res) => {
              data.value = res.data;
            });
            resolve(true);
          })
          .catch((err) => {
            Message.error(t('commons.addUserFailed') + ': ' + err);
            reject(err);
          })
          .finally(() => {
            d.loading = false;
          });
      });
    },
  });
};

const handleUpdateUserSetting = (user: UserReadAdmin) => () => {
  const setting = ref<UserSettingSchema>(user.setting);
  const d = Dialog.info({
    title: t('commons.setUserLimit'),
    content: () =>
      h(
        EditUserSettingForm,
        {
          value: setting.value,
          'onUpdate:value': (newVal: UserSettingSchema) => {
            setting.value = newVal;
          },
        },
        { default: () => '' }
      ),
    positiveText: t('commons.confirm'),
    negativeText: t('commons.cancel'),
    onPositiveClick: () => {
      d.loading = true;
      return new Promise((resolve, reject) => {
        updateUserSettingApi(user.id, setting.value)
          .then((res) => {
            Message.success(t('commons.setUserLimitSuccess'));
            getAllUserApi().then((res) => {
              data.value = res.data;
            });
            resolve(true);
          })
          .catch((err) => {
            reject(err);
          })
          .finally(() => {
            d.loading = false;
          });
      });
    },
  });
};
</script>

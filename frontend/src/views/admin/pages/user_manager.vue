<template>
  <div class="mb-4 mt-1 ml-1 flex flex-row space-x-2 justify-between">
    <n-button circle @click="refreshData">
      <template #icon>
        <n-icon>
          <RefreshFilled />
        </n-icon>
      </template>
    </n-button>
    <n-button type="primary" @click="triggerShowCreateUserDrawer">
      {{ $t('commons.addUser') }}
    </n-button>
  </div>
  <n-data-table
    :scroll-x="1600"
    size="small"
    :columns="columns"
    :data="data"
    :bordered="true"
    :pagination="{
      pageSize: 20,
    }"
  />
  <n-drawer
    v-if="showUpdateUserDrawer"
    v-model:show="showUpdateUserDrawer"
    :width="sm ? '50%' : '80%'"
    :placement="'right'"
    closable
  >
    <n-drawer-content :title="t('commons.updateUser')">
      <UpdateUserForm :user-id="currentUserId" :init-tab="updateUserFormTab" @save="triggerCloseUserSettingDrawer" />
    </n-drawer-content>
  </n-drawer>
  <n-drawer
    v-if="showCreateUserDrawer"
    v-model:show="showCreateUserDrawer"
    :width="'50%'"
    :placement="'right'"
    closable
  >
    <n-drawer-content :title="t('commons.createUser')">
      <CreateUserForm @save="triggerCloseCreateUserDrawer" />
    </n-drawer-content>
  </n-drawer>
</template>

<script setup lang="ts">
import { Pencil, TrashOutline } from '@vicons/ionicons5';
import { RefreshFilled, SettingsRound } from '@vicons/material';
import { DataTableColumns, NButton, NIcon } from 'naive-ui';
import { h, ref } from 'vue';
import { useI18n } from 'vue-i18n';

import { deleteUserApi, getAllUserApi } from '@/api/user';
import { chatStatusMap, UserReadAdmin } from '@/types/schema';
import { getCountTrans, getRevChatModelNameTrans, revChatModelNames } from '@/utils/chat';
import { screenWidthGreaterThan as wgt } from '@/utils/screen';
import { Dialog, Message } from '@/utils/tips';

import CreateUserForm from '../components/CreateUserForm.vue';
import UpdateUserForm from '../components/UpdateUserForm.vue';

const { t } = useI18n();

const sm = wgt('sm');

const data = ref<Array<UserReadAdmin>>([]);

const currentUserId = ref<number>(0);
const showUpdateUserDrawer = ref(false);
const showCreateUserDrawer = ref(false);
const updateUserFormTab = ref<string>('basic');

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
  { title: '#', key: 'id' },
  { title: t('commons.username'), key: 'username' },
  { title: t('commons.nickname'), key: 'nickname' },
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
      return new Date(a.active_time).getTime() - new Date(b.active_time).getTime();
    },
  },
  {
    title: t('commons.maxConversationCount'),
    key: 'max_conv_count',
    render(row) {
      return row.setting.revchatgpt_ask_limits
        ? getCountTrans(row.setting.revchatgpt_ask_limits.max_conv_count)
        : t('commons.unlimited');
    },
  },
  {
    title: t('commons.availableTotalAskCount'),
    key: 'available_ask_count',
    render(row) {
      // return getCountTrans(row.available_ask_count!);
      return row.setting.revchatgpt_ask_limits
        ? getCountTrans(row.setting.revchatgpt_ask_limits.total_count)
        : t('commons.unlimited');
    },
  },
  {
    title: t('commons.availableAskCountPerModel'),
    key: 'availableAskCountPerModel',
    render(row) {
      if (row.setting.revchatgpt_available_models && row.setting.revchatgpt_ask_limits) {
        const per_model_count = row.setting.revchatgpt_ask_limits.per_model_count;
        return revChatModelNames
          .map((modelName) => {
            if (row.setting.revchatgpt_available_models.includes(modelName)) {
              return `${getRevChatModelNameTrans(modelName)}: ${getCountTrans(per_model_count[modelName])}`;
            } else {
              return `${getRevChatModelNameTrans(modelName)}: ${t('commons.disabled')}`;
            }
          })
          .join(', ');
      } else {
        return t('commons.unlimited');
      }
    },
  },
  { title: t('commons.email'), key: 'email' },
  {
    title: t('commons.isSuperuser'),
    key: 'is_superuser',
    render(row) {
      return row.is_superuser ? t('commons.yes') : t('commons.no');
    },
  },
  {
    title: t('labels.remark'),
    key: 'remark',
    render(row) {
      return row.remark ? row.remark : t('commons.empty');
    },
  },
  {
    title: t('commons.actions'),
    key: 'actions',
    fixed: 'right',
    render(row) {
      return h('div', { class: 'flex justify-start space-x-2 w-20 mx-1' }, [
        // 删除
        h(
          NButton,
          { size: 'small', type: 'error', circle: true, secondary: true, onClick: () => handleDeleteUser(row) },
          { icon: () => h(NIcon, null, { default: () => h(TrashOutline) }) }
        ),
        h(
          NButton,
          {
            size: 'small',
            type: 'primary',
            circle: true,
            secondary: true,
            onClick: triggerShowUserSettingDrawer(row, 'basic'),
          },
          { icon: () => h(NIcon, null, { default: () => h(Pencil) }) }
        ),
        h(
          NButton,
          {
            size: 'small',
            type: 'info',
            circle: true,
            secondary: true,
            onClick: triggerShowUserSettingDrawer(row, 'setting'),
          },
          { icon: () => h(NIcon, null, { default: () => h(SettingsRound) }) }
        ),
      ]);
    },
  },
];

const handleDeleteUser = (row: UserReadAdmin) => {
  const d = Dialog.warning({
    title: t('commons.deleteUser'),
    content: t('tips.deleteUserConfirm'),
    positiveText: t('commons.confirm'),
    negativeText: t('commons.cancel'),
    onPositiveClick: () => {
      d.loading = true;
      return new Promise((resolve, reject) => {
        deleteUserApi(row.id)
          .then(() => {
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
};

const triggerShowUserSettingDrawer = (user: UserReadAdmin, tab: 'basic' | 'setting') => () => {
  currentUserId.value = user.id;
  updateUserFormTab.value = tab;
  showUpdateUserDrawer.value = true;
};

const triggerCloseUserSettingDrawer = () => {
  showUpdateUserDrawer.value = false;
  getAllUserApi().then((res) => {
    data.value = res.data;
  });
};

const triggerShowCreateUserDrawer = () => {
  showCreateUserDrawer.value = true;
};

const triggerCloseCreateUserDrawer = () => {
  showCreateUserDrawer.value = false;
  getAllUserApi().then((res) => {
    data.value = res.data;
  });
};
</script>

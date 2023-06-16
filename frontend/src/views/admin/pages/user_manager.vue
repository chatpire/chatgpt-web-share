<template>
  <div class="mb-4 mt-1 ml-1 flex flex-row gap-x-2 gap-y-1 space justify-between">
    <n-button circle @click="refreshData">
      <template #icon>
        <n-icon>
          <RefreshFilled />
        </n-icon>
      </template>
    </n-button>
    <n-button type="primary" @click="drawer.open('create', null)">
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
    v-if="drawer.show.value"
    v-model:show="drawer.show.value"
    :width="gtsm() ? '60%' : '100%'"
    :placement="'right'"
  >
    <n-drawer-content closable :title="drawer.title.value" :native-scrollbar="false">
      <CreateUserForm v-if="drawer.name.value == 'create'" @save="handleCreateUser" />
      <UpdateUserBasicForm
        v-else-if="drawer.name.value == 'updateBasic'"
        :user="currentUser"
        @save="handleUpdateUserBasic"
      />
      <UpdateUserSettingForm
        v-else-if="drawer.name.value == 'updateSetting'"
        :user="currentUser"
        @save="handleUpdateUserSetting"
      />
    </n-drawer-content>
  </n-drawer>
</template>

<script setup lang="ts">
import { Pencil, TrashOutline } from '@vicons/ionicons5';
import { RefreshFilled, SettingsRound } from '@vicons/material';
import { DataTableColumns, NButton, NIcon } from 'naive-ui';
import { h, ref } from 'vue';
import { useI18n } from 'vue-i18n';

import { deleteUserApi, getAllUserApi, registerApi, updateUserByIdApi, updateUserSettingApi } from '@/api/user';
import ChatTypeTagInfoCell from '@/components/ChatTypeTagInfoCell.vue';
import { useDrawer } from '@/hooks/drawer';
import { chatStatusMap, UserCreate, UserReadAdmin, UserSettingSchema, UserUpdateAdmin } from '@/types/schema';
import { getCountTrans } from '@/utils/chat';
import { screenWidthGreaterThan } from '@/utils/media';
import { getDateStringSorter } from '@/utils/table';
import { Dialog, Message } from '@/utils/tips';
import { renderUserPerModelCounts } from '@/utils/user';

import CreateUserForm from '../components/CreateUserForm.vue';
import UpdateUserBasicForm from '../components/UpdateUserBasicForm.vue';
import UpdateUserSettingForm from '../components/UpdateUserSettingForm.vue';

const { t } = useI18n();

const gtsm = screenWidthGreaterThan('sm');

const data = ref<Array<UserReadAdmin>>([]);

const currentUser = ref<UserReadAdmin | null>(null);

const refreshData = () => {
  getAllUserApi().then((res) => {
    data.value = res.data;
    Message.success(t('tips.refreshed'));
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
      return row.setting.openai_web_chat_status ? t(chatStatusMap[row.setting.openai_web_chat_status as keyof typeof chatStatusMap]) : '';
    },
    sorter: 'default',
  },
  {
    title: t('commons.activeTime'),
    key: 'last_active_time',
    render(row) {
      return row.last_active_time ? new Date(row.last_active_time).toLocaleString() : t('commons.neverActive');
    },
    sorter: getDateStringSorter<UserReadAdmin>('last_active_time'),
  },
  {
    title: `${t('labels.max_conv_count')}`,
    key: 'ask_count_limits',
    render(row) {
      return h(ChatTypeTagInfoCell, {
        value: {
          openai_web: getCountTrans(row.setting.openai_web.max_conv_count),
          openai_api: getCountTrans(row.setting.openai_api.max_conv_count),
        },
      });
    },
  },
  {
    title: t('labels.available_ask_count'),
    key: 'available_ask_count',
    render(row) {
      // return getCountTrans(row.available_ask_count!);
      return renderUserPerModelCounts(row.setting, true);
    },
  },
  // TODO
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
    width: '120px',
    render(row) {
      return h('div', { class: 'w-full flex flex-row justify-center space-x-2' }, [
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
            onClick: () => drawer.open('updateBasic', row),
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
            onClick: () => drawer.open('updateSetting', row),
          },
          { icon: () => h(NIcon, null, { default: () => h(SettingsRound) }) }
        ),
      ]);
    },
  },
];

const drawer = useDrawer([
  { name: 'create', title: t('commons.createUser') },
  {
    name: 'updateBasic',
    title: t('commons.updateUserBasic'),
    beforeOpen: (row: UserReadAdmin) => {
      currentUser.value = JSON.parse(JSON.stringify(row));
    },
    afterClose: () => {
      currentUser.value = null;
    },
  },
  {
    name: 'updateSetting',
    title: t('commons.updateUserSetting'),
    beforeOpen: (row: UserReadAdmin) => {
      currentUser.value = JSON.parse(JSON.stringify(row));
    },
    afterClose: () => {
      currentUser.value = null;
    },
  },
]);

const handleCreateUser = (userCreate: UserCreate) => {
  registerApi(userCreate)
    .then(() => {
      Message.success(t('tips.createSuccess'));
      getAllUserApi().then((res) => {
        data.value = res.data;
      });
    })
    .finally(() => {
      drawer.close();
    });
};

const handleUpdateUserBasic = (userUpdate: Partial<UserUpdateAdmin>) => {
  if (!currentUser.value) return;
  if (userUpdate.password === '') {
    delete userUpdate.password;
  }
  updateUserByIdApi(currentUser.value.id, userUpdate)
    .then((res) => {
      Message.success(t('tips.updateSuccess'));
      data.value = data.value.map((item) => {
        if (item.id === res.data.id) {
          return res.data;
        } else {
          return item;
        }
      });
    })
    .finally(() => {
      drawer.close();
    });
};

const handleUpdateUserSetting = (userSetting: Partial<UserSettingSchema>) => {
  if (!currentUser.value) return;
  updateUserSettingApi(currentUser.value.id, userSetting)
    .then((res) => {
      Message.success(t('tips.updateSuccess'));
      data.value = data.value.map((item) => {
        if (item.id === res.data.id) {
          return res.data;
        } else {
          return item;
        }
      });
    })
    .finally(() => {
      drawer.close();
    });
};

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
</script>

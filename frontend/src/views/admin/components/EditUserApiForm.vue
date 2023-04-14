<template>
  <!-- user register form -->
  <n-data-table :columns="columns" :data="data" />
  <n-button type="primary" @click="handleAddUserApi"> {{ t("commons.addApi") }} </n-button>
</template>

<script setup lang="ts">
import { ref, h } from 'vue';
import { ApiRead, UserApiCreate, UserApiRead } from '@/types/schema';
import { i18n } from '@/i18n';
import { Dialog, Message } from '@/utils/tips';
import { DataTableColumns, NButton, NIcon, NSelect } from 'naive-ui';
import { deleteUserApi, updateUserApi, createUserApi } from '@/api/api';
import { TrashOutline } from '@vicons/ionicons5';

const t = i18n.global.t as any;

const props = defineProps<{
  userId: number;
  data: UserApiRead[];
  apiList: ApiRead[];
}>()

const data = ref(props.data)
const getApi = (api_id:number) => {
  return props.apiList.find(item => item.id === api_id)
}
const columns: DataTableColumns<UserApiRead> = [
  {
    title: '#',
    key: 'id',
    render(row) {
      return row.id === -1 ? '': row.id
    }
  },
  {
    title: "api",
    key: 'api',
    render(row, index) {
      const options = props.apiList.map((key, index) => {
        return {
          label: key.type + '-' + key.id,
          value: key.id
        };
      })
      return h(NSelect, {
        value: row.api_id === -1 ? null: row.api_id,
        options,
        onUpdateValue(v) {
          const obj = data.value[index]
          const newUserApi = ref<UserApiCreate>({
            user_id: props.userId,
            api_id: v,
            models: obj.models,
          })
          if (row.id !== -1){
            updateUserApi(row.id, newUserApi.value).then(res => {
              data.value[index] = {...res.data, api:getApi(v)}
              Message.success(t("commons.updateSuccess"));
            }).catch(err => {
              Message.error(t("commons.updateFailed"));
            })
          } else {
            createUserApi(newUserApi.value).then(res => {
              data.value[index] = {...res.data, api:getApi(v)}
              Message.success(t("commons.createSuccess"));
            }).catch(err => {
              Message.error(t("commons.createFailed"));
            })
          }
        }
      })
    }
  },
  {
    title: t("commons.modelName"),
    key: 'models',
    render(row, index) {
      const options = Object.keys(row.api.models).map((key, index) => {
        return {
          label: key,
          value: key
        };
      })
      return h(NSelect, {
        value: row.models,
        options,
        multiple: true,
        onUpdateValue(v) {
          const obj = data.value[index]
          const newUserApi = ref<UserApiCreate>({
            user_id: obj.user_id,
            api_id: obj.api_id,
            models: v,
          })
          updateUserApi(row.id, newUserApi.value).then(res => {
            data.value[index].models = v
            Message.success(t("commons.updateSuccess"));
          }).catch(err => {
            Message.error(t("commons.updateFailed"));
          })
        }
      })
    }
  },
  {
    title: t("commons.actions"),
    key: 'actions',
    fixed: 'right',
    render(row) {
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
              title: t("commons.deleteApi"),
              content: t("tips.deleteApiConfirm"),
              positiveText: t("commons.confirm"),
              negativeText: t("commons.cancel"),
              onPositiveClick: () => {
                d.loading = true;
                return new Promise((resolve, reject) => {
                  deleteUserApi(row.id).then(res => {
                    Message.success(t("tips.deleteSuccess"));
                    data.value = data.value.filter(item => item.id !== row.id)
                    resolve(true);
                  }).catch(err => {
                    Message.error(t("tips.deleteFailed") + ": " + err);
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
        })

      ])
    }
  }
]
const handleAddUserApi = () => {
  data.value.push({
    id: -1,
    user_id: props.userId,
    api_id: -1,
    models: [],
    api: {
      id: -1,
      type: '',
      key: '',
      endpoint: '',
      models: {}
    }
  })
}
</script>
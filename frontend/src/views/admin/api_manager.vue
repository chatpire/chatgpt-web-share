<template>
  <div class="mb-4 mt-1 ml-1 flex flex-row space-x-2 justify-between">
    <n-button circle @click="refreshData"> 
      <template #icon>
        <n-icon>
          <RefreshFilled />
        </n-icon>
      </template>
    </n-button>
    <n-button type="primary" @click="handleAddAPI"> {{ $t("commons.addApi") }} </n-button>
  </div>

  <n-data-table size="small" :columns="columns" :data="data" :bordered="true" :pagination="{
    pageSize: 20
  }" />
</template>

<script setup lang="ts">
import { ref, reactive, computed, h } from 'vue';
import { DataTableColumns, NButton, NIcon, NTag } from 'naive-ui'
import { ApiCreate, ApiRead } from '@/types/schema';
import { useI18n } from 'vue-i18n';
import { getAllApi, createApi, deleteApi } from '@/api/api';
import { Dialog, Message } from '@/utils/tips';
import { TrashOutline, Pencil } from '@vicons/ionicons5';
import { PasswordRound, RefreshFilled } from '@vicons/material';
import EditApiForm from './components/EditApiForm.vue';

const { t } = useI18n();


const data = ref<Array<ApiRead>>([]);

const refreshData = () => {
  getAllApi().then(res => {
    data.value = res.data;
    Message.success(t("tips.refreshed"));
  })
}

getAllApi().then(res => {
  data.value = res.data;
})

const columns: DataTableColumns<ApiRead> = [
  {
    title: "#",
    key: 'id'
  },
  {
    title: t("commons.apiType"),
    key: 'type'
  },
  {
    title: t("commons.apiKey"),
    key: 'key',
    render(row) {
      return row.key.substring(0, 2) + "******"
    }
  },
  {
    title: t('commons.apiEndpoint'),
    key: 'endpoint'
  },
  {
    title: t("commons.modelName"),
    key: 'models',
    render (row) {
        const tags = Object.keys(row.models).map((model: string) => {
          return h(
            NTag,
            {
              style: {
                marginRight: '6px'
              },
              type: 'info',
              bordered: false
            },
            {
              default: () => model
            }
          )
        })
        return tags
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
                  deleteApi(row.id).then(res => {
                    Message.success(t("tips.deleteSuccess"));
                    getAllApi().then(res => {
                      data.value = res.data;
                    })
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

const handleAddAPI = () => {
  const api = ref<ApiCreate>({
    type: 'openai',
    key: '',
    endpoint: ''
  })
  const d = Dialog.info({
    title: t("commons.addUser"),
    content: () => h(EditApiForm, {
      api: api.value,
      'onUpdate:api': (newApi: ApiCreate) => {
        api.value = newApi;
      }
    }, { default: () => "" }),
    positiveText: t("commons.confirm"),
    negativeText: t("commons.cancel"),
    onPositiveClick: () => {
      d.loading = true;
      return new Promise((resolve, reject) => {
        createApi(api.value).then(res => {
          Message.success(t("commons.addSuccess"));
          getAllApi().then(res => {
            data.value = res.data;
          })
          resolve(true);
        }).catch(err => {
          Message.error(t("commons.addFailed") + ": " + err);
          reject(err);
        }).finally(() => {
          d.loading = false;
        })
      })
    }
  })
}


</script>

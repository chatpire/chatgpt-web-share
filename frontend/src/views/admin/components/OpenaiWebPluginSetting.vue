<template>
  <div class="flex flex-row lt-sm:flex-col lt-sm:space-y-2 justify-between items-center mb-3">
    <n-radio-group v-model:value="categoryOption" name="radiogroup">
      <n-space>
        <n-radio :value="'installed'">
          {{ $t('commons.enabled') }}
        </n-radio>
        <n-radio :value="''">
          {{ $t('commons.all') }}
        </n-radio>
        <n-radio :value="'most_popular'">
          {{ $t('commons.most_popular') }}
        </n-radio>
        <n-radio :value="'newly_added'">
          {{ $t('commons.newly_added') }}
        </n-radio>
      </n-space>
    </n-radio-group>
    <n-text>
      {{ $t('desc.openai_web_installed_plugins') }}
    </n-text>
    <!-- TODO: add search -->
    <!-- <n-input v-model:value="searchOption" placeholder="Search" clearable class="w-full" style="width: 200px">
      <template #suffix>
        <n-icon> <SearchRound /> </n-icon>
      </template>
    </n-input> -->
  </div>
  <n-layout class="p-3">
    <n-empty
      v-if="loading"
      class="h-full min-h-141 flex justify-center"
      :style="{ backgroundColor: themeVars.cardColor }"
      :description="$t('tips.loading')"
    >
      <template #icon>
        <n-spin size="medium" />
      </template>
    </n-empty>
    <n-empty v-else-if="currentPlugins?.items.length == 0" class="min-h-144" :description="$t('commons.noPluginsAvailable')" />
    <div v-else>
      <div class="flex flex-wrap gap-3">
        <n-card v-for="(plugin, i) of currentPlugins?.items" :key="i" class="w-68 h-45">
          <div class="flex flex-col gap-4 rounded border">
            <div class="flex gap-4">
              <n-avatar :key="`${plugin.id}-logo`" :size="64" :src="plugin.manifest?.logo_url" />
              <div class="flex min-w-0 flex-col items-start justify-between">
                <div class="max-w-full truncate text-lg leading-6">
                  {{ plugin.manifest?.name_for_human }}
                </div>
                <div class="flex flex-row space-x-4">
                  <n-button
                    v-if="plugin.user_settings?.is_installed"
                    :disabled="requestingPatchId"
                    :loading="requestingPatchId == plugin.id"
                    type="primary"
                    size="small"
                    @click="changePluginSetting(plugin.id, false)"
                  >
                    {{ $t('commons.disable') }}
                  </n-button>
                  <n-button
                    v-else
                    :disabled="requestingPatchId"
                    :loading="requestingPatchId == plugin.id"
                    size="small"
                    @click="changePluginSetting(plugin.id, true)"
                  >
                    {{ $t('commons.enable') }}
                  </n-button>
                  <n-button text @click="showPluginDetail(plugin)">
                    {{ $t('commons.detail') }}
                  </n-button>
                </div>
              </div>
            </div>
            <!-- <n-text class="h-[60px] text-sm line-clamp-3">
                    
                  </n-text> -->
            <n-ellipsis :line-clamp="3">
              {{ plugin.manifest?.description_for_human }}
            </n-ellipsis>
          </div>
        </n-card>
      </div>
    </div>
    <div class="flex flex-col w-full items-center mt-4">
      <n-pagination v-model:page="pageNumber" simple :page-count="pageCount" />
    </div>
  </n-layout>
</template>

<script setup lang="ts">
import { useWindowSize } from '@vueuse/core';
import { useThemeVars } from 'naive-ui';
import { computed, h, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';

import {
  getInstalledOpenaiChatPluginsApi,
  getOpenaiChatPluginsApi,
  patchOpenaiChatPluginsUsersSettingsApi,
} from '@/api/chat';
import OpenaiWebPluginDetailCard from '@/components/OpenaiWebPluginDetailCard.vue';
import { OpenaiChatPlugin, OpenaiChatPluginListResponse } from '@/types/schema';
import { Dialog, Message } from '@/utils/tips';

const { width } = useWindowSize();

const { t } = useI18n();
const themeVars = useThemeVars();

const loading = ref(true);
const requestingPatchId = ref<string | null>(null);

const categoryOption = ref<string>('installed');

const currentPlugins = ref<OpenaiChatPluginListResponse | null>(null);

const pageNumber = ref(1);

// pageSize 计算：根据屏幕宽度，计算出每行显示的个数，显示三行。每个 card 宽度为 280
const pageSize = computed(() => {
  const cardWidth = 280;
  const gap = 24;
  const cardCount = Math.floor((width.value - gap) / (cardWidth + gap));
  return cardCount * 3;
});

const pageCount = computed(() =>
  currentPlugins.value?.count ? Math.ceil(currentPlugins.value.count / pageSize.value) : 0
);

watch(categoryOption, () => {
  pageNumber.value = 1;
  getPlugins(categoryOption.value);
});

watch(pageNumber, onPageUpdate);

function changePluginSetting(pluginId: string | undefined | null, isInstalled: boolean) {
  if (!pluginId) {
    return;
  }
  requestingPatchId.value = pluginId;
  patchOpenaiChatPluginsUsersSettingsApi(pluginId, {
    is_installed: isInstalled,
  })
    .then(() => {
      Message.success(isInstalled ? t('tips.enablePluginSuccess') : t('tips.disablePluginSuccess'));
      getPlugins();
    })
    .finally(() => {
      requestingPatchId.value = null;
    });
}

function onPageUpdate(page: number) {
  console.log('onPageUpdate', page);
  getPlugins(categoryOption.value, (page - 1) * pageSize.value);
}

function getPlugins(category = 'installed', offset = 0, limit = pageSize.value, search = '') {
  loading.value = true;
  if (category === 'installed') {
    getInstalledOpenaiChatPluginsApi()
      .then((res) => {
        currentPlugins.value = res.data;
      })
      .catch(() => {
        currentPlugins.value = null;
      })
      .finally(() => {
        loading.value = false;
      });
  } else {
    getOpenaiChatPluginsApi(offset, limit, category, search)
      .then((res) => {
        currentPlugins.value = res.data;
      })
      .catch(() => {
        currentPlugins.value = null;
      })
      .finally(() => {
        loading.value = false;
      });
  }
}

function showPluginDetail(plugin: OpenaiChatPlugin) {
  Dialog.info({
    title: plugin.manifest?.name_for_human || 'unknown',
    style: {
      width: '630px',
    },
    content: () =>
      h(OpenaiWebPluginDetailCard, {
        plugin,
      }),
  });
}

getPlugins('installed');
</script>

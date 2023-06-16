<template>
  <n-card class="mb-4 h-full">
    <n-tabs
      class="-mt-2"
      default-value="pluginSettings"
      size="large"
      animated
      pane-wrapper-style="margin: 0 -4px"
      pane-style="padding-left: 4px; padding-right: 4px; box-sizing: border-box;"
    >
      <n-tab-pane name="pluginSettings" :tab="$t('commons.pluginSettings')">
        <div class="flex flex-row lt-sm:flex-col lt-sm:space-y-2 justify-between items-center mb-3">
          <n-radio-group v-model:value="filterOption" name="radiogroup">
            <n-space>
              <n-radio :value="'all'">
                {{ $t('commons.all') }}
              </n-radio>
              <n-radio :value="'most_popular'">
                {{ $t('commons.most_popular') }}
              </n-radio>
              <n-radio :value="'newly_added'">
                {{ $t('commons.newly_added') }}
              </n-radio>
              <n-radio :value="'installed'">
                {{ $t('commons.enabled') }}
              </n-radio>
            </n-space>
          </n-radio-group>
          <n-text>
            {{ $t('desc.openai_web_installed_plugins') }}
          </n-text>
          <n-input v-model:value="searchOption" placeholder="Search" clearable class="w-full" style="width: 200px">
            <template #suffix>
              <n-icon> <SearchRound /> </n-icon>
            </template>
          </n-input>
        </div>
        <n-layout class="p-3">
          <n-empty
            v-if="loading"
            class="h-full flex justify-center"
            :style="{ backgroundColor: themeVars.cardColor }"
            :description="$t('tips.loading')"
          >
            <template #icon>
              <n-spin size="medium" />
            </template>
          </n-empty>
          <n-empty v-else-if="!fetchPluginsSuccess" :description="$t('commons.noPluginsAvailable')" />
          <div v-else>
            <div class="flex flex-wrap gap-3">
              <n-card v-for="(plugin, i) of currentPagePlugins" :key="i" class="w-68 h-45">
                <div class="flex flex-col gap-4 rounded border">
                  <div class="flex gap-4">
                    <n-avatar :key="`${plugin.id}-logo`" :size="64" :src="plugin.manifest?.logo_url" />
                    <div class="flex min-w-0 flex-col items-start justify-between">
                      <div class="max-w-full truncate text-lg leading-6">
                        {{ plugin.manifest?.name_for_human }}
                      </div>
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
            <n-pagination v-model:page="page" simple :page-count="pageCount" />
          </div>
        </n-layout>
      </n-tab-pane>
    </n-tabs>
  </n-card>
</template>

<script setup lang="ts">
import { SearchRound } from '@vicons/material';
import { useWindowSize } from '@vueuse/core';
import { useThemeVars } from 'naive-ui';
import { computed, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';

import { getAllOpenaiChatPluginsApi, patchOpenaiChatPluginsUsersSettingsApi } from '@/api/chat';
import { OpenAIChatPlugin } from '@/types/schema';
import { Message } from '@/utils/tips';

const { width } = useWindowSize();

const { t } = useI18n();
const themeVars = useThemeVars();

const allPlugins = ref<OpenAIChatPlugin[]>([]);
const loading = ref(true);
const requestingPatchId = ref<string | null>(null);
const fetchPluginsSuccess = ref(false);

const page = ref(1);

// pageSize 计算：根据屏幕宽度，计算出每行显示的个数，显示三行。每个 card 宽度为 280
const pageSize = computed(() => {
  const cardWidth = 280;
  const gap = 24;
  const cardCount = Math.floor((width.value - gap) / (cardWidth + gap));
  return cardCount * 3;
});

const filterOption = ref('all');

const searchOption = ref('');

const currentPlugins = computed(() => {
  let result = allPlugins.value;
  if (filterOption.value === 'newly_added') {
    result = result.filter((plugin) => plugin.categories?.findIndex((category) => category.id === 'newly_added') != -1);
  } else if (filterOption.value === 'most_popular') {
    result = result.filter(
      (plugin) => plugin.categories?.findIndex((category) => category.id === 'most_popular') != -1
    );
  } else if (filterOption.value === 'installed') {
    result = result.filter((plugin) => plugin.user_settings?.is_installed);
  }
  if (searchOption.value.trim() !== '') {
    result = result.filter(
      (plugin) =>
        plugin.manifest?.name_for_human?.toLowerCase().includes(searchOption.value.toLowerCase()) ||
        plugin.manifest?.name_for_model?.toLowerCase().includes(searchOption.value.toLowerCase()) ||
        plugin.manifest?.description_for_human?.toLowerCase().includes(searchOption.value.toLowerCase()) ||
        plugin.manifest?.name_for_model?.toLowerCase().includes(searchOption.value.toLowerCase())
    );
  }
  return result;
});

const pageCount = computed(() => Math.ceil(currentPlugins.value.length / pageSize.value));

const currentPagePlugins = computed(() => {
  const start = (page.value - 1) * pageSize.value;
  const end = start + pageSize.value;
  return currentPlugins.value.slice(start, end);
});

watch(filterOption, () => {
  page.value = 1;
});

function changePluginSetting(pluginId: string | undefined, isInstalled: boolean) {
  if (!pluginId) {
    return;
  }
  requestingPatchId.value = pluginId;
  patchOpenaiChatPluginsUsersSettingsApi(pluginId, {
    is_installed: isInstalled,
  })
    .then(() => {
      Message.success(isInstalled ? t('tips.enablePluginSuccess') : t('tips.disablePluginSuccess'));
      fetchData();
    })
    .finally(() => {
      requestingPatchId.value = null;
    });
}

function fetchData() {
  getAllOpenaiChatPluginsApi()
    .then((res) => {
      allPlugins.value = res.data;
      fetchPluginsSuccess.value = true;
    })
    .catch(() => {
      fetchPluginsSuccess.value = false;
    })
    .finally(() => {
      loading.value = false;
    });
}

fetchData();
</script>

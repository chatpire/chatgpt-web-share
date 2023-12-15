<template>
  <n-card content-style="padding: 0;">
    <n-collapse @update:expanded-names="handleExpand">
      <n-collapse-item :title="$t('commons.serverStatus')" name="serverStatus">
        <n-list hoverable show-divider>
          <n-list-item>
            <div class="flex flex-row justify-between content-center">
              <div>
                <n-icon class="mr-1">
                  <md-people />
                </n-icon>{{ $t('commons.activeUserIn5m') }}
              </div>
              <div>{{ serverStatus.active_user_in_5m }}</div>
            </div>
          </n-list-item>
          <n-list-item>
            <div class="flex flex-row justify-between content-center">
              <div>
                <n-icon class="mr-1">
                  <md-people />
                </n-icon>{{ $t('commons.activeUserIn1h') }}
              </div>
              <div>{{ serverStatus.active_user_in_1h }}</div>
            </div>
          </n-list-item>
          <n-list-item>
            <div class="flex flex-row justify-between content-center">
              <div>
                <n-icon class="mr-1">
                  <md-people />
                </n-icon>{{ $t('commons.activeUserIn1d') }}
              </div>
              <div>{{ serverStatus.active_user_in_1d }}</div>
            </div>
          </n-list-item>
          <n-list-item>
            <div class="flex flex-row justify-between content-center">
              <div>
                <n-icon class="mr-1">
                  <EventBusyFilled />
                </n-icon>{{ $t('commons.isChatbotBusy') }}
              </div>
              <div>{{ serverStatus.is_chatbot_busy ? $t('commons.yes') : $t('commons.no') }}</div>
            </div>
          </n-list-item>
          <n-list-item>
            <div class="flex flex-row justify-between content-center">
              <div>
                <n-icon class="mr-1">
                  <QueueFilled />
                </n-icon>{{ $t('commons.chatbotWaitingCount') }}
              </div>
              <div>{{ serverStatus.chatbot_waiting_count }}</div>
            </div>
          </n-list-item>
          <n-list-item>
            <div class="flex flex-row justify-between content-center">
              <div>
                <n-icon class="mr-1">
                  <DataUsageRound />
                </n-icon>{{ $t('labels.gpt4_count_in_3_hours') }}
              </div>
              <div>{{ serverStatus.gpt4_count_in_3_hours }}</div>
            </div>
          </n-list-item>
        </n-list>
      </n-collapse-item>
    </n-collapse>
  </n-card>
</template>

<script setup lang="ts">
import { MdPeople } from '@vicons/ionicons4';
import { EventBusyFilled, QueueFilled, DataUsageRound } from '@vicons/material';
import { ref } from 'vue';

import { getServerStatusApi } from '@/api/status';
import { CommonStatusSchema } from '@/types/schema';

const serverStatus = ref<CommonStatusSchema>({});

const isExpaned = ref(false);

const handleExpand = (names: string[]) => {
  if (names.length > 0) {
    isExpaned.value = true;
    updateData();
  } else {
    isExpaned.value = false;
  }
};

const updateData = () => {
  if (isExpaned.value)
    getServerStatusApi().then((res) => {
      // console.log(res.data);
      serverStatus.value = res.data;
    });
};
updateData();
setInterval(updateData, 5000);
</script>

<style>
div.n-collapse-item {
  padding: 1em;
}
</style>

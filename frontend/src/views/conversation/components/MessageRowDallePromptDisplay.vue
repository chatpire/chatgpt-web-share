<template>
  <div class="flex flex-col items-start gap-2 my-3">
    <n-card
      class="max-w-full rounded-xl border-black/10 border-[0.5px] shadow-xxs w-[280px]"
      :content-style="{ padding: 0 }"
      @click="expandPrompt = !expandPrompt"
    >
      <div class="flex flex-row items-center justify-between">
        <div class="min-w-0">
          <div class="flex h-14 items-center gap-2.5 px-3 py-2">
            <div class="flex h-[34px] w-[34px] shrink-0 items-center justify-center">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 34 34"
                fill="none"
                class="h-[34px] w-[34px]"
                width="34"
                height="34"
              >
                <rect width="34" height="34" rx="6" fill="#ECECF1" />
                <rect
                  x="29"
                  y="19.4004"
                  width="4.8"
                  height="4.8"
                  transform="rotate(180 29 19.4004)"
                  fill="#3C46FF"
                />
                <rect
                  x="24.1992"
                  y="19.4004"
                  width="4.8"
                  height="4.8"
                  transform="rotate(180 24.1992 19.4004)"
                  fill="#FF6E3C"
                />
                <rect
                  x="19.3984"
                  y="19.4004"
                  width="4.8"
                  height="4.8"
                  transform="rotate(180 19.3984 19.4004)"
                  fill="#51DA4C"
                />
                <rect
                  x="14.6016"
                  y="19.4004"
                  width="4.8"
                  height="4.8"
                  transform="rotate(180 14.6016 19.4004)"
                  fill="#42FFFF"
                />
                <rect
                  x="9.80078"
                  y="19.4004"
                  width="4.8"
                  height="4.8"
                  transform="rotate(180 9.80078 19.4004)"
                  fill="#FFFF66"
                />
              </svg>
            </div>
            <div class="flex min-w-0 flex-1 flex-col items-start text-sm leading-[18px]">
              <div class="truncate font-medium">
                DALL·E 3
              </div>
              <div class="max-w-full truncate opacity-70">
                {{ statusText }}
              </div>
            </div>
          </div>
        </div>
        <div v-show="prompts.length > 0" class="mx-4 h-full flex items-center">
          <n-icon :component="expandPrompt ? ExpandLessRound : ExpandMoreRound" size="24px" />
        </div>
      </div>
    </n-card>

    <n-card v-show="expandPrompt && prompts.length > 0" class="rounded-xl border-black/10 shadow-xxs" :content-style="{ padding: 0 }">
      <n-list hoverable clickable class="rounded-xl">
        <n-list-item v-for="(prompt, i) of prompts" :key="prompt" @click="copyPrompt(prompt)">
          <template #prefix>
            <n-tag v-if="prompts.length > 1" :bordered="false" type="info">
              {{ i }}
            </n-tag>
          </template>
          {{ prompt }}
        </n-list-item>
      </n-list>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ExpandLessRound, ExpandMoreRound } from '@vicons/material';
import { computed, ref } from 'vue';

import { BaseChatMessage, OpenaiWebChatMessage } from '@/types/schema';
import { getContentRawText } from '@/utils/chat';
import { Message } from '@/utils/tips';

const props = defineProps<{
  messages: BaseChatMessage[];
}>();

const expandPrompt = ref(false);

type DallePrompt = {
  prompts?: string[];
  prompt?: string;
};

const jsonContent = computed(() => {
  try {
    const message = props.messages[0] as OpenaiWebChatMessage;
    if (message.content?.content_type !== 'code') {
      console.error('Invalid message type');
      return {
      };
    }
    const dallePrompt = JSON.parse(getContentRawText(message)) as DallePrompt;
    return dallePrompt;
  } catch (e) {
    return {
    };
  }
});

const prompts = computed(() => {
  const prompts = [];
  if (jsonContent.value.prompt) {
    prompts.push(jsonContent.value.prompt);
  }
  else if (jsonContent.value.prompts) {
    prompts.push(...jsonContent.value.prompts);
  }
  return prompts;
});

const statusText = computed(() => {
  if (!jsonContent.value || jsonContent.value.prompts?.length === 0) {
    return 'Creating prompts...';
  }
  
  return `Created ${prompts.value.length} prompt${prompts.value.length > 1 ? 's' : ''}`;
});

function copyPrompt(prompt: string) {
  navigator.clipboard.writeText(prompt);
  Message.success('Copied!');
}
</script>

import { DataTableColumns } from 'naive-ui';
import { h } from 'vue';

import ChatModelTagsRow from '@/components/ChatModelTagsRow.vue';
import ChatTypeTagInfoCell from '@/components/ChatTypeTagInfoCell.vue';
import { i18n } from '@/i18n';
import { openaiApiChatModelNames, openaiWebChatModelNames } from '@/types/json_schema';
import { chatStatusMap, UserRead, UserSettingSchema } from '@/types/schema';
import { getCountTrans } from '@/utils/chat';

const t = i18n.global.t as any;

export const renderUserPerModelCounts = (setting: UserSettingSchema, availableOnly = false) => {
  // console.log('renderUserPerModelCounts', setting);
  const openaiWebCounts = {} as Record<string, string>;
  const openaiApiCounts = {} as Record<string, string>;
  openaiWebChatModelNames.forEach((model) => {
    if (availableOnly && !setting.openai_web.available_models.includes(model)) return;
    if (setting.openai_web.per_model_ask_count[model] == undefined) setting.openai_web.per_model_ask_count[model] = 0;
    openaiWebCounts[model] = getCountTrans(setting.openai_web.per_model_ask_count[model]);
  });
  openaiApiChatModelNames.forEach((model) => {
    if (availableOnly && !setting.openai_api.available_models.includes(model)) return;
    if (setting.openai_api.per_model_ask_count[model] == undefined) setting.openai_api.per_model_ask_count[model] = 0;
    openaiApiCounts[model] = getCountTrans(setting.openai_api.per_model_ask_count[model]);
  });
  // console.log(revCounts, apiCounts);
  return h(ChatTypeTagInfoCell, {
    value: {
      openai_web: h(ChatModelTagsRow, {
        value: openaiWebCounts,
      }),
      openai_api: h(ChatModelTagsRow, {
        value: openaiApiCounts,
      }),
    },
  });
};

type ListAttr<T> = {
  title: string;
  key: string;
  render?: (row: T) => any;
};

// 用于 UserProfile，复用了一部分 user_manager 代码
export function getUserAttrColumns(): ListAttr<UserRead>[] {
  return [
    { title: '#', key: 'id' },
    { title: t('commons.username'), key: 'username' },
    { title: t('commons.email'), key: 'email' },
    { title: t('commons.nickname'), key: 'nickname' },
    {
      title: t('labels.openai_web_chat_status'),
      key: 'rev_chat_status',
      render(row) {
        return row.setting.openai_web_chat_status
          ? t(chatStatusMap[row.setting.openai_web_chat_status as keyof typeof chatStatusMap])
          : '';
      },
    },
    {
      title: t('labels.last_active_time'),
      key: 'last_active_time',
      render(row) {
        return row.last_active_time ? new Date(row.last_active_time).toLocaleString() : t('commons.neverActive');
      },
    },
    {
      title: `${t('labels.ask_count_limits')}`,
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
    }
  ];
}

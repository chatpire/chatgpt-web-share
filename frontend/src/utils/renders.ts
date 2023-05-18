import { MdMore } from '@vicons/ionicons4';
import { NButton, NDropdown, NIcon, NInput, NSelect, SelectOption } from 'naive-ui';
import { h } from 'vue';

import ChatModelTagsRow from '@/components/ChatModelTagsRow.vue';
import ChatTypeTagInfoCell from '@/components/ChatTypeTagInfoCell.vue';
import { i18n } from '@/i18n';
import useUserStore from '@/store/modules/user';
import {NewConversationInfo} from '@/types/custom';
import { BaseConversationSchema, UserSettingSchema } from '@/types/schema';
import { getChatModelNameTrans, getCountTrans } from '@/utils/chat';
import { Dialog, Message } from '@/utils/tips';
import NewConversationForm from '@/views/conversation/components/NewConversationForm.vue';

const t = i18n.global.t as any;

export const dropdownRenderer = (
  conversation: BaseConversationSchema,
  handleDeleteConversation: (conversation_id?: string) => void,
  handleChangeConversationTitle: (conversation_id?: string) => void
) =>
  h(
    NDropdown,
    {
      trigger: 'hover',
      options: [
        {
          label: t('commons.delete'),
          key: 'delete',
          props: {
            onClick: () => handleDeleteConversation(conversation.conversation_id),
          },
        },
        {
          label: t('commons.rename'),
          key: 'rename',
          props: {
            onClick: () => handleChangeConversationTitle(conversation.conversation_id),
          },
        },
      ],
    },
    {
      default: () =>
        h(
          NButton,
          {
            size: 'small',
            quaternary: true,
            circle: true,
          },
          { default: () => h(NIcon, null, { default: () => h(MdMore) }) }
        ),
    }
  );

export const popupInputDialog = (
  title: string,
  placeholder: string,
  callback: (inp: string) => Promise<any>,
  success: () => void,
  fail: () => void
) => {
  let input = '';
  const d = Dialog.info({
    title: title,
    positiveText: t('commons.confirm'),
    negativeText: t('commons.cancel'),
    content: () =>
      h(NInput, {
        onInput: (e) => (input = e),
        autofocus: true,
        placeholder: placeholder,
      }),
    onPositiveClick() {
      d.loading = true;
      return new Promise((resolve) => {
        callback(input)
          .then(() => {
            success();
            resolve(true);
          })
          .catch(() => {
            fail();
            resolve(true);
          })
          .finally(() => {
            d.loading = false;
          });
      });
    },
  });
};

export const popupChangeConversationTitleDialog = (
  conversation_id: string,
  callback: (title: string) => Promise<any>,
  success: () => void,
  fail: () => void
) => {
  popupInputDialog(t('commons.rename'), t('tips.rename'), callback, success, fail);
};

export const popupResetUserPasswordDialog = (
  callback: (password: string) => Promise<any>,
  success: () => void,
  fail: () => void
) => {
  popupInputDialog(t('commons.resetPassword'), t('tips.resetPassword'), callback, success, fail);
};

// export interface NewConversationInfo {
//   title: string;
//   type: 'rev' | 'api';
//   model: string;
// }
export const popupNewConversationDialog = (callback: (newConversationInfo: NewConversationInfo) => Promise<void>) => {
  let input = null as NewConversationInfo | null;
  const d = Dialog.info({
    title: t('commons.newConversation'),
    positiveText: t('commons.confirm'),
    negativeText: t('commons.cancel'),
    content: () =>
      h(NewConversationForm, {
        onInput: (newConversationInfo) => {
          input = newConversationInfo;
        },
      }),
    onPositiveClick() {
      d.loading = true;
      return new Promise((resolve, reject) => {
        if (input === null) {
          resolve(false);
        }
        if (input?.model === null) {
          Message.error(t('tips.modelRequired'));
          resolve(false);
        }
        callback(input!)
          .then(() => {
            resolve(true);
          })
          .catch(() => {
            resolve(true);
          })
          .finally(() => {
            d.loading = false;
          });
      });
    },
  });
};

export const renderUserPerModelCounts = (setting: UserSettingSchema) => {
  const value = {
    rev: h(ChatModelTagsRow, {
      value: {
        gpt_3_5: getCountTrans(setting.rev.per_model_ask_count.gpt_3_5),
        gpt_4: getCountTrans(setting.rev.per_model_ask_count.gpt_4),
        gpt_4_browsing: getCountTrans(setting.rev.per_model_ask_count.gpt_4_browsing),
        gpt_4_plugins: getCountTrans(setting.rev.per_model_ask_count.gpt_4_plugins),
      }
    }),
    api: h(ChatModelTagsRow, {
      value: {
        gpt_3_5: getCountTrans(setting.api.per_model_ask_count.gpt_3_5),
        gpt_4: getCountTrans(setting.api.per_model_ask_count.gpt_4),
      }
    })
  };
  return h(ChatTypeTagInfoCell, {
    value
  });
};
import { MdMore } from '@vicons/ionicons4';
import { NButton, NDropdown, NIcon, NInput, NSelect, SelectOption } from 'naive-ui';
import { h } from 'vue';

import { i18n } from '@/i18n';
import useUserStore from '@/store/modules/user';
import { BaseConversationSchema } from '@/types/schema';
import { getChatModelNameTrans } from '@/utils/chat';
import { Dialog } from '@/utils/tips';

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

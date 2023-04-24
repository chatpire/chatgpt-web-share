import {MdMore} from '@vicons/ionicons4';
import {NButton, NDropdown, NIcon, NInput, NSelect, SelectOption} from 'naive-ui';
import {h} from 'vue';

import {i18n} from '@/i18n';
import useUserStore from '@/store/modules/user';
import {RevConversationSchema} from '@/types/schema';
import {getRevChatModelNameTrans} from '@/utils/chat';
import {Dialog} from '@/utils/tips';

const t = i18n.global.t as any;

const dropdownRenderer = (
  conversation: RevConversationSchema,
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

const popupInputDialog = (title: string, placeholder: string, callback: (inp: string) => Promise<any>, success: () => void, fail: () => void) => {
  let input = '';
  const secondInput: string | undefined = undefined;
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

const getAvailableModelOptions = (): SelectOption[] => {
  const userStore = useUserStore();
  const options = [{ label: t('commons.shaModel'), value: 'text-davinci-002-render-sha' }];
  // if (userStore.user?.setting.openai_api_available_models)
  //   options.push({
  //     label: t('commons.paidModel'),
  //     value: 'text-davinci-002-render-paid',
  //   });
  // if (userStore.user?.can_use_gpt4) options.push({ label: t('commons.gpt4Model'), value: 'gpt-4' });
  userStore.user?.setting.openai_api_available_models?.forEach((model) => {
    options.push({ label: getRevChatModelNameTrans(model), value: model });
  });
  return options;
};

const popupNewConversationDialog = (callback: (_conv_title: string, _conv_model: string) => Promise<any>) => {
  let convTitle = '';
  let convModel = '';
  const d = Dialog.info({
    title: t('commons.newConversation'),
    positiveText: t('commons.confirm'),
    negativeText: t('commons.cancel'),
    // content: () =>
    //   h(NInput, { onInput: (e) => (input = e), autofocus: true, placeholder: placeholder, }),

    // 用一个 NInput 和一个 NSelect
    content: () =>
      h(
        'div',
        {
          style: 'display: flex; flex-direction: column; gap: 16px;',
        },
        [
          h(NInput, {
            onInput: (e) => (convTitle = e),
            autofocus: true,
            placeholder: t('tips.conversationTitle'),
          }),
          h(NSelect, {
            placeholder: t('tips.whetherUsePaidModel'),
            'onUpdate:value': (value: string) => (convModel = value),
            options: getAvailableModelOptions(),
          }),
        ]
      ),
    onPositiveClick() {
      d.loading = true;
      return new Promise((resolve) => {
        callback(convTitle, convModel)
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

const popupChangeConversationTitleDialog = (
  conversation_id: string,
  callback: (title: string) => Promise<any>,
  success: () => void,
  fail: () => void
) => {
  popupInputDialog(t('commons.rename'), t('tips.rename'), callback, success, fail);
};

const popupResetUserPasswordDialog = (callback: (password: string) => Promise<any>, success: () => void, fail: () => void) => {
  popupInputDialog(t('commons.resetPassword'), t('tips.resetPassword'), callback, success, fail);
};

export {
  dropdownRenderer,
  popupChangeConversationTitleDialog,
  popupNewConversationDialog,
  popupResetUserPasswordDialog,
};

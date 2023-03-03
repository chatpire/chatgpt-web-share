import {
  NDropdown,
  NButton,
  NIcon,
  NInput,
  NSelect,
  SelectOption,
  NInputNumber,
  NSwitch,
} from "naive-ui";
import { h } from "vue";
import { MdMore } from "@vicons/ionicons4";
import { i18n } from "@/i18n";
import { ConversationSchema, LimitSchema } from "@/types/schema";
import { Dialog } from "@/utils/tips";

const t = i18n.global.t as any;

const dropdownRenderer = (
  conversation: ConversationSchema,
  handleDeleteConversation: (conversation_id?: string) => void,
  handleChangeConversationTitle: (conversation_id?: string) => void
) =>
  h(
    NDropdown,
    {
      trigger: "hover",
      options: [
        {
          label: t("commons.delete"),
          key: "delete",
          props: {
            onClick: () =>
              handleDeleteConversation(conversation.conversation_id),
          },
        },
        {
          label: t("commons.rename"),
          key: "rename",
          props: {
            onClick: () =>
              handleChangeConversationTitle(conversation.conversation_id),
          },
        },
      ],
    },
    {
      default: () =>
        h(
          NButton,
          {
            size: "small",
            quaternary: true,
            circle: true,
          },
          { default: () => h(NIcon, null, { default: () => h(MdMore) }) }
        ),
    }
  );

const popupInputDialog = (
  title: string,
  placeholder: string,
  callback: (inp: string) => Promise<any>,
  success: () => void,
  fail: () => void
) => {
  let input = "";
  let secondInput: string | undefined = undefined;
  const d = Dialog.info({
    title: title,
    positiveText: t("commons.confirm"),
    negativeText: t("commons.cancel"),
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

const popupNewConversationDialog = (
  callback: (_conv_title: string, _conv_model: string) => Promise<any>
) => {
  let convTitle = "";
  let convModel = "";
  const d = Dialog.info({
    title: t("commons.newConversation"),
    positiveText: t("commons.confirm"),
    negativeText: t("commons.cancel"),
    // content: () =>
    //   h(NInput, { onInput: (e) => (input = e), autofocus: true, placeholder: placeholder, }),

    // 用一个 NInput 和一个 NSelect
    content: () =>
      h(
        "div",
        {
          style: "display: flex; flex-direction: column; gap: 16px;",
        },
        [
          h(NInput, {
            onInput: (e) => (convTitle = e),
            autofocus: true,
            placeholder: t("tips.conversationTitle"),
          }),
          h(NSelect, {
            placeholder: t("tips.whetherUsePaidModel"),
            "onUpdate:value": (value: string) => (convModel = value),
            options: [
              { label: t("commons.shaModel"), value: "sha" },
              { label: t("commons.paidModel"), value: "paid" },
            ] as SelectOption[],
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
  popupInputDialog(
    t("commons.rename"),
    t("tips.rename"),
    callback,
    success,
    fail
  );
};

const popupResetUserPasswordDialog = (
  callback: (password: string) => Promise<any>,
  success: () => void,
  fail: () => void
) => {
  popupInputDialog(
    t("commons.resetPassword"),
    t("tips.resetPassword"),
    callback,
    success,
    fail
  );
};

export {
  dropdownRenderer,
  popupNewConversationDialog,
  popupChangeConversationTitleDialog,
  popupResetUserPasswordDialog,
};

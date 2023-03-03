import { createPinia } from "pinia";
import useAppStore from "./modules/app";
import useUserStore from "./modules/user";
import useConversationStore from "./modules/conversation";

const pinia = createPinia();

export { useAppStore, useUserStore, useConversationStore };
export default pinia;

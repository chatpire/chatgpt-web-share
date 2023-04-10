import { Preference } from "@/types/custom";
import { UserRead, ConversationSchema } from "@/types/schema";
import { RemovableRef, UseStorageOptions } from "@vueuse/core";

interface UserState {
  user: UserRead | null;
  savedUsername: string | null;
  savedPassword: string | null;
}

interface AppState {
  theme: any;
  language: any;
  preference: RemovableRef<Preference>
}

export type { UserState, AppState };

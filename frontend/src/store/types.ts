import { UserRead, ConversationSchema } from "@/types/schema";

interface UserState {
  user: UserRead | null;
  savedUsername: string | null;
  savedPassword: string | null;
}

interface AppState {
  theme: any;
  language: any;
}

export type { UserState, AppState };

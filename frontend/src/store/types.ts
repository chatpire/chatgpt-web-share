import { UserRead, ConversationSchema } from "@/types/schema";

interface UserState {
  user: UserRead | null;
  savedUsername: string | null;
  savedPassword: string | null;
}

interface AppState {
  theme: string | null | undefined;
}

export type { UserState, AppState };

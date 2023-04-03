import { components } from "./openapi";

export type UserRead = components["schemas"]["UserRead"];
export type UserCreate = components["schemas"]["UserCreate"];
export type UserUpdate = components["schemas"]["UserUpdate"];
export type ConversationSchema = components["schemas"]["ConversationSchema"];
export type ServerStatusSchema = components["schemas"]["ServerStatusSchema"];
export type LimitSchema = components["schemas"]["LimitSchema"];
export type ChatStatus = components["schemas"]["ChatStatus"];
export type ChatModels = components["schemas"]["ChatModels"];

export type SystemInfo = components["schemas"]["SystemInfo"];
export type RequestStatistics = components["schemas"]["RequestStatistics"];

export type LogFilterOptions = components["schemas"]["LogFilterOptions"]

export type AskParams = components["schemas"]["AskParams"];
export type AskResponse = components["schemas"]["AskResponse"];

export const chatStatusMap = {
  asking: "commons.askingChatStatus",
  queueing: "commons.queueingChatStatus",
  idling: "commons.idlingChatStatus",
};

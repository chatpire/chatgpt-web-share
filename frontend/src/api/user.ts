import axios from 'axios';

import { LimitSchema, UserCreate, UserRead } from '@/types/schema';

import ApiUrl from './url';

export interface LoginData {
  username: string;
  password: string;
}

export function loginApi(data: LoginData) {
  const formData = new FormData();
  formData.set('username', data.username);
  formData.set('password', data.password);
  return axios.post<any>(ApiUrl.Login, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
}

export function registerApi(userInfo: UserCreate) {
  return axios.post<UserRead>(ApiUrl.Register, userInfo);
}

export function logoutApi() {
  return axios.post<any>(ApiUrl.Logout);
}

export function getUserInfoApi() {
  return axios.get<UserRead>(ApiUrl.UserInfo);
}

export function getAllUserApi() {
  return axios.get<UserRead[]>(ApiUrl.UserList);
}

export function deleteUserApi(user_id: number) {
  return axios.delete(ApiUrl.UserList + `/${user_id}`);
}

export function resetUserPasswordApi(user_id: number, new_password: string) {
  return axios.patch(ApiUrl.UserList + `/${user_id}/reset-password`, null, {
    params: { new_password },
  });
}

export function updateUserLimitApi(user_id: number, limit: LimitSchema) {
  return axios.post(ApiUrl.UserList + `/${user_id}/limit`, limit);
}

// export function updateUserInfoApi(userInfo: Partial<UserUpdate>) {
//   return axios.patch<UserRead>(ApiUrl.UserInfo, userInfo);
// }

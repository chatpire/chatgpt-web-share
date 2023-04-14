import { ApiCreate, ApiRead, UserApiCreate, UserApiRead } from "@/types/schema";
import axios from "axios";
import ApiUrl from "./url";

export function getAllApi() {
    return axios.get<ApiRead[]>(ApiUrl.ApiList);
}

export function createApi(new_api: ApiCreate){
    return axios.post<ApiRead>(ApiUrl.ApiList, new_api);
}

export function deleteApi(api_id: number) {
    return axios.delete(ApiUrl.ApiList + `/${api_id}`);
}

export function updateApi(api_id: number, new_api: ApiCreate) {
    return axios.patch(ApiUrl.ApiList + `/${api_id}`, new_api);
}


export function getUserApi(user_id: number) {
    return axios.get<UserApiRead[]>(ApiUrl.UserApi + `?user_id=${user_id}`);
}

export function createUserApi(new_user_api: UserApiCreate) {
    return axios.post<UserApiCreate>(ApiUrl.UserApi, new_user_api);
}

export function deleteUserApi(user_api_id: number) {
    return axios.delete(ApiUrl.UserApi + `${user_api_id}`);
}

export function updateUserApi(user_api_id: number, new_user_api: UserApiCreate) {
    return axios.patch(ApiUrl.UserApi + `${user_api_id}`, new_user_api);
}

export function getMyModels() {
    return axios.get<string []>(ApiUrl.MyModels);
}
import { defineStore } from 'pinia';
import { ref } from 'vue';
import api from '@/api';
import router from '@/router';

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token'));
  const isAuthenticated = ref(!!token.value);

  const login = async (username: string, password: string) => {
    try {
      // Hack: backend POST /login expects url-formencoded body, not JSON
      // So use PUT instead, which accepts JSON
      // const res = await api.post('/login', { username, password });
      const res = await api.put('/login', { username, password });
      // response body should contain {"access_token": jwt_token, "token_type": "bearer"}
      token.value = res.data.access_token;
      isAuthenticated.value = true;
      // existence of token.value is already checked in isAuthenticated
      // alternative solution is set to empty string if value is null:
      // .setitem('token', token.value ?? '')
      localStorage.setItem('token', token.value as string);
      router.push('/');
    } catch (err) {
      logout();
      throw err;
    }
  }

  const logout = () => {
    token.value = null;
    isAuthenticated.value = false;
    localStorage.removeItem('token');
    router.push('/login');
  }

  return { token, isAuthenticated, login, logout };
})
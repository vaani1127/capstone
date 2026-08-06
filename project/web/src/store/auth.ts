import { create } from 'zustand';
import { apiClient } from '@/services/api';

export type UserRole = 'Admin' | 'Doctor' | 'Nurse' | 'Patient';

export interface User {
  id: number;
  name: string;
  email: string;
  role: UserRole;
  is_active: boolean;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<void>;
  setUser: (user: User | null) => void;
  fetchCurrentUser: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  token: localStorage.getItem('token'),
  isAuthenticated: !!localStorage.getItem('token'),
  isLoading: false,
  error: null,

  login: async (email: string, password: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await apiClient.post<{
        access_token: string;
        refresh_token?: string;
        user: User;
      }>('/auth/login', { email, password });

      localStorage.setItem('token', response.access_token);
      if (response.refresh_token) {
        localStorage.setItem('refresh_token', response.refresh_token);
      }

      set({
        user: response.user,
        token: response.access_token,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Login failed';
      set({
        isLoading: false,
        error: message,
      });
      throw error;
    }
  },

  logout: () => {
    localStorage.removeItem('token');
    localStorage.removeItem('refresh_token');
    set({
      user: null,
      token: null,
      isAuthenticated: false,
      error: null,
    });
  },

  refreshToken: async () => {
    try {
      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken) throw new Error('No refresh token');

      const response = await apiClient.post<{
        access_token: string;
      }>('/auth/refresh', { refresh_token: refreshToken });

      localStorage.setItem('token', response.access_token);
      set({ token: response.access_token });
    } catch (error) {
      get().logout();
      throw error;
    }
  },

  setUser: (user) => set({ user }),

  fetchCurrentUser: async () => {
    try {
      const user = await apiClient.get<User>('/users/me');
      set({ user });
    } catch (error) {
      get().logout();
      throw error;
    }
  },
}));

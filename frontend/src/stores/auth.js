import { defineStore } from "pinia";
import api from "../api/client";

export const useAuthStore = defineStore("auth", {
	state: () => ({
		user: null,
		access: localStorage.getItem("access") || null,
		refresh: localStorage.getItem("refresh") || null,
		loading: false,
		error: null,
	}),
	actions: {
		async login(username, password) {
			this.loading = true; 
			this.error = null;
			try {
				console.log('Attempting login with:', { username, baseURL: import.meta.env.VITE_API_BASE });
				const { data } = await api.post("/api/token/", { username, password });
				this.access = data.access; 
				this.refresh = data.refresh;
				localStorage.setItem("access", data.access);
				localStorage.setItem("refresh", data.refresh);
				await this.fetchMe();
				return true;
			} catch (e) {
				console.error('Login error:', e.response?.data || e.message);
				// Show more specific error message
				if (e.response?.status === 400) {
					this.error = e.response?.data?.detail || e.response?.data?.non_field_errors?.[0] || "Invalid username or password";
				} else if (e.response?.status === 401) {
					this.error = "Invalid credentials";
				} else if (e.response?.status === 0 || !e.response) {
					this.error = "Cannot connect to server. Please check your connection.";
				} else {
					this.error = e.response?.data?.detail || "Login failed. Please try again.";
				}
				return false;
			} finally {
				this.loading = false;
			}
		},
		async refreshToken() {
			if (!this.refresh) return false;
			try {
				const { data } = await api.post("/api/token/refresh/", { refresh: this.refresh });
				this.access = data.access;
				localStorage.setItem("access", data.access);
				return true;
			} catch {
				this.logout();
				return false;
			}
		},
		async fetchMe() {
			try {
			  const { data } = await api.get("/api/auth/me/");
			  this.user = data;
			} catch (e) {
			  if (e.response?.status === 401) {
				const refreshed = await this.refreshToken();
				if (refreshed) {
				  const { data } = await api.get("/api/auth/me/");
				  this.user = data;
				  return;
				}
			  }
			  this.user = null;
			  throw e;
			}
		  },
		logout() {
			this.user = null; this.access = null; this.refresh = null;
			localStorage.removeItem("access"); localStorage.removeItem("refresh");
		},
		hasWriteRole() {
			const r = this.user?.role;
			return ["ADMIN","DOCTOR","LAB_TECH","PHARMACIST"].includes(r);
		},
	},
});

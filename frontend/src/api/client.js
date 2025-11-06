import axios from "axios";

const api = axios.create({
	baseURL: import.meta.env.VITE_API_BASE,
});

api.interceptors.request.use((config) => {
	const token = localStorage.getItem("access");
	if (token) config.headers.Authorization = `Bearer ${token}`;
	return config;
});

let refreshPromise = null;

async function refreshAccessToken() {
	if (!refreshPromise) {
		const refresh = localStorage.getItem("refresh");
		refreshPromise = refresh
			? axios
					.post(`${import.meta.env.VITE_API_BASE}/api/token/refresh/`, { refresh })
					.then(({ data }) => {
						localStorage.setItem("access", data.access);
						return data.access;
					})
			: Promise.reject(new Error("no-refresh"));
	}
	try {
		const token = await refreshPromise;
		return token;
	} finally {
		// allow future refreshes
		refreshPromise = null;
	}
}

api.interceptors.response.use(
	(res) => res,
	async (error) => {
		const original = error.config;
		if (!error.response) return Promise.reject(error);

		const status = error.response.status;
		const url = (original?.url || "").toString();
		const isAuthEndpoint = url.includes("/api/token/");

		// Only try refresh once per request, and never for auth endpoints
		if (status === 401 && !original?._retry && !isAuthEndpoint) {
			original._retry = true;
			try {
				const newAccess = await refreshAccessToken();
				original.headers = original.headers || {};
				original.headers.Authorization = `Bearer ${newAccess}`;
				return api(original);
			} catch {
				// fall through to redirect
			}
		}

		// If unauthorized after refresh (or no refresh), redirect to login
		if (status === 401) {
			try {
				sessionStorage.setItem(
					"post_login_redirect",
					window.location.pathname + window.location.search
				);
			} catch {}
			localStorage.removeItem("access");
			localStorage.removeItem("refresh");
			const current = encodeURIComponent(window.location.pathname + window.location.search);
			window.location.href = `/login?next=${current}`;
			return new Promise(() => {});
		}

		return Promise.reject(error);
	}
);

export default api;
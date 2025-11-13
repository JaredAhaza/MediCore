import axios from "axios";

// Validate and normalize API base URL
const getApiBaseURL = () => {
	const envURL = import.meta.env.VITE_API_BASE;
	
	// Ensure URL has protocol
	if (!envURL) {
		console.error('VITE_API_BASE is not set!');
		return 'https://medicore-e9xf.onrender.com';
	}
	
	// If URL doesn't start with http:// or https://, add https://
	if (!envURL.startsWith('http://') && !envURL.startsWith('https://')) {
		console.warn('VITE_API_BASE missing protocol, adding https://');
		return `https://${envURL}`;
	}
	
	return envURL;
};

const API_BASE_URL = getApiBaseURL();
console.log('API Base URL:', API_BASE_URL);

const api = axios.create({
	baseURL: API_BASE_URL,
	headers: {
		'Content-Type': 'application/json',
	},
});

api.interceptors.request.use((config) => {
	const token = localStorage.getItem("access");
	if (token) {
		config.headers.Authorization = `Bearer ${token}`;
	}
	// Ensure Content-Type is set for POST/PUT/PATCH requests
	if (config.data && (config.method === 'post' || config.method === 'put' || config.method === 'patch')) {
		config.headers['Content-Type'] = 'application/json';
	}
	return config;
}, (error) => {
	console.error('Request error:', error);
	return Promise.reject(error);
});

let refreshPromise = null;

async function refreshAccessToken() {
	if (!refreshPromise) {
		const refresh = localStorage.getItem("refresh");
		refreshPromise = refresh
			? axios
					.post(`${API_BASE_URL}/api/token/refresh/`, 
						{ refresh },
						{ headers: { 'Content-Type': 'application/json' } }
					)
					.then(({ data }) => {
						localStorage.setItem("access", data.access);
						return data.access;
					})
					.catch((error) => {
						console.error('Token refresh error:', error.response?.data || error.message);
						throw error;
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
		
		// Log error details for debugging
		if (error.response) {
			console.error('API Error:', {
				status: error.response.status,
				statusText: error.response.statusText,
				data: error.response.data,
				url: original?.url,
				method: original?.method,
			});
		} else if (error.request) {
			console.error('Network Error:', error.request);
		} else {
			console.error('Error:', error.message);
		}
		
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
import { watch, onMounted } from "vue";

export default function useDraftForm(key, stateRef, { throttleMs = 300 } = {}) {
	let t = null;

	const load = () => {
		try {
			const raw = sessionStorage.getItem(key);
			if (!raw) return;
			const saved = JSON.parse(raw);
			if (saved && typeof saved === "object") {
				Object.assign(stateRef.value, saved);
			}
		} catch {}
	};

	const save = () => {
		try {
			sessionStorage.setItem(key, JSON.stringify(stateRef.value));
		} catch {}
	};

	const clear = () => {
		try {
			sessionStorage.removeItem(key);
		} catch {}
	};

	onMounted(load);

	watch(
		stateRef,
		() => {
			if (throttleMs <= 0) return save();
			clearTimeout(t);
			t = setTimeout(save, throttleMs);
		},
		{ deep: true }
	);

	return { load, save, clear };
}
<script setup></script>

<template>
	<div>
		<NavBar />
		<main class="container">
			<router-view />
		</main>
	</div>
</template>

<script setup>
import NavBar from "./components/NavBar.vue";
</script>

<style>
body { margin:0; font-family: system-ui, Arial, sans-serif; }
.container { max-width: 1000px; margin: 1rem auto; padding: 0 1rem; }
a { text-decoration: none; color: #0366d6; }
nav {
  background: #0f172a; /* slate-900 */
  color: #ffffff;
  padding: 0.75rem 0;
  position: sticky;
  top: 0;
  z-index: 50;
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}
nav .container { display:flex; align-items:center; gap:1rem; }
nav a {
  color: #ffffff;
  margin-right: 0.25rem;
  font-weight: 600;
  opacity: 0.9;
  padding: 6px 10px;
  border-radius: 6px;
}
nav a:hover { opacity: 1; background: rgba(255,255,255,0.12); }
nav .container a:first-child { font-weight: 700; letter-spacing: 0.2px; }
nav button {
  margin-left: 0.25rem;
  padding: 6px 10px;
  background: #ef4444; /* red-500 */
  color: #ffffff;
  border: none;
  border-radius: 6px;
}
nav button:hover { background: #dc2626; /* red-600 */ }
button { cursor: pointer; }
input, select, textarea { padding: .5rem; width: 100%; margin: .25rem 0 .75rem; }
.card { border: 1px solid #ddd; padding: 1rem; border-radius: .5rem; margin-bottom: 1rem; }
</style>

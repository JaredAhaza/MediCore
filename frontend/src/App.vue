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
a { text-decoration: none; color: #0a63; }
nav { background: #0a63; color: white; padding: 0.75rem; }
nav a { color: white; margin-right: 1rem; }
button { cursor: pointer; }
input, select, textarea { padding: .5rem; width: 100%; margin: .25rem 0 .75rem; }
.card { border: 1px solid #ddd; padding: 1rem; border-radius: .5rem; margin-bottom: 1rem; }
</style>

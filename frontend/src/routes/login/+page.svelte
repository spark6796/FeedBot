<script>
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';

	const backendUrl = import.meta.env.VITE_BACKEND_URL;

	async function login(code) {
		try {
			const response = await fetch(`${backendUrl}/auth/discord/login`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ code }),
				credentials: 'include'
			});

			if (response.ok) {
				goto('/dashboard');
			} else {
				console.error('Failed to get authorization URL');
			}
		} catch (error) {
			console.error('Error during login:', error);
		}
	}
	onMount(() => {
		const params = new URLSearchParams(window.location.search);
		const code = params.get('code');
		if (code) {
			login(code);
		} else {
			alert('Some Error Occurred. Please try logging in again.');
			goto('/');
		}
	});
</script>

<div class="bg flex h-screen w-full items-center justify-center text-8xl">
	<div
		class="bungee-regular flex h-fit w-fit animate-pulse items-center justify-center rounded-xl border-8 border-[#154467] bg-slate-800 p-8 text-center text-4xl font-bold text-white hover:border-sky-700"
	>
		Logging you in...
	</div>
</div>

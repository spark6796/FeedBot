<script>
	import { goto } from '$app/navigation';
	const oauthUrl = import.meta.env.VITE_DISCORD_OAUTH2_URL;
</script>

<div class="bg h-screen w-full">
	<div class="h-1/4 w-full pt-8">
		<img src="/title.png" alt="Feed bot" class="mx-auto" />
	</div>
	<div class="flex h-3/4 w-full items-center justify-center">
		<button
			on:click={() => (window.location.href = oauthUrl)}
			class="bungee-regular flex h-fit w-fit items-center justify-center rounded-xl border-8 border-[#154467] bg-slate-800 p-8 text-center text-4xl font-bold text-white transition-transform hover:scale-105 hover:border-sky-700"
		>
			Continue with discord
			<img src="/discord.svg" alt="discord logo" class="pl-4" />
		</button>
	</div>
</div>

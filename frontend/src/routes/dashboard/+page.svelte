<script>
    import { onMount } from 'svelte';
    import { goto } from '$app/navigation';
	
    const backendUrl = import.meta.env.VITE_BACKEND_URL;

    let user = null;
    let showUserMenu = false;
    let widgets = [];
    let isLoading = true;
    let notificationMessage = '';
    let showNotification = false;
    let notificationType = 'success'; // or 'error'
    
    function showNotifications(message, type = 'success', duration = 5000) {
        notificationMessage = message;
        notificationType = type;
        showNotification = true;
        if (duration) {
            setTimeout(() => {
                showNotification = false;
                notificationMessage = '';
            }, duration);
        }
    }
    
    function showErrorMessage(message, duration = 5000) {
        showNotifications(message, 'error', duration);
    }

    onMount(async () => {
        try {
            
            const userResponse = await fetch(`${backendUrl}/panel/getdata`, {
                credentials: 'include'
            });

            if (!userResponse.ok) {
                goto('/')
            }

            const responseData = await userResponse.json();
            user = responseData.data;
            if (!user) {
                throw new Error('No user data received');
            }
            
            const feeds = user.feeds || [];
            if (feeds.length === 0) {
                widgets = [];
                isLoading = false;
                return;

            }
            widgets = feeds.map((feed, index) => ({
                id: index + 1,
                title: feed.title || 'Untitled Feed',
                description: feed.description || 'Configure your RSS feed',
                rssUrl: feed.rssUrl || '',
                webhookUrl: feed.webhookUrl || '',
                enabled: feed.enabled || false
            }));

        } catch (error) {
            console.error('Dashboard load error:', error);
            if (error.message.includes('auth')) {
                goto('/');
            }
        } finally {
            isLoading = false;
        }
    });

    let editingWidget = null;
    let editMenu = {
        show: false,
        title: '',
        description: '',
        rssUrl: '',
        webhookUrl: '',
        isNewWidget: false
    };
    let deleteConfirm = {
        show: false,
        widget: null
    };

    async function deleteWidget(widget) {
        widgets = widgets.filter(w => w.id !== widget.id);
        deleteConfirm.show = false;
        await updateBackend();
    }

    async function toggleWidget(widget) {
        const wasEnabled = widget.enabled;
        widget.enabled = !widget.enabled;
        widgets = widgets;
        
        const success = await updateBackend();
        if (success && !wasEnabled && widget.enabled) {
            showNotifications(
                `Feed "${widget.title}" enabled! Please wait about 1 minute - you'll receive a welcome message in your Discord channel when initialization is complete.`,
                'success',
                10000
            );
        }
    }

    function openEditMenu(widget, isNew = false) {
        editingWidget = widget;
        editMenu = {
            show: true,
            title: widget.title,
            description: widget.description,
            rssUrl: widget.rssUrl || '',
            webhookUrl: widget.webhookUrl || '',
            isNewWidget: isNew
        };
    }

    async function updateBackend() {
        try {
            const feedsData = widgets.map(widget => ({
                title: widget.title,
                description: widget.description,
                rssUrl: widget.rssUrl,
                webhookUrl: widget.webhookUrl,
                enabled: widget.enabled
            }));

            const response = await fetch(`${backendUrl}/panel/updatefeeds`, {
                method: 'POST',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ feeds: feedsData })
            });

            const data = await response.json();

            if (!response.ok) {
                if (response.status === 400 && data.detail?.errors) {
                    const errorList = data.detail.errors.join('\n• ');
                    showErrorMessage(`Feed Validation Errors:\n• ${errorList}`, 0);
                    return false;
                }
                showErrorMessage('Failed to update feeds. Please try again.', 5000);
                return false;
            }

            user = data.data;
            return true;
        } catch (error) {
            console.error('Failed to update feeds:', error);
            showErrorMessage('An unexpected error occurred. Please try again.', 5000);
            return false;
        }
    }

    async function saveEditMenu() {
        if (editingWidget) {
            editingWidget.title = editMenu.title;
            editingWidget.description = editMenu.description;
            editingWidget.rssUrl = editMenu.rssUrl;
            editingWidget.webhookUrl = editMenu.webhookUrl;
            widgets = widgets; 
            
            if (editMenu.isNewWidget) {
                const success = await updateBackend();
                if (!success) {
                    widgets = widgets.filter(w => w.id !== editingWidget.id);
                }
            } else {
                await updateBackend();
            }
        }
        editMenu.show = false;
    }

    function addWidget() {
        if (widgets.length >= 4) return;
        
        const newId = Math.max(0, ...widgets.map(w => w.id)) + 1;
        const newWidget = {
            id: newId,
            title: `Feed ${newId}`,
            description: 'Configure your RSS feed',
            rssUrl: '',
            webhookUrl: '',
            enabled: false 
        };
        
        widgets = [...widgets, newWidget];
        openEditMenu(newWidget, true);
    }
</script>


<div class="min-h-screen w-full bg-slate-900 p-6">
    <div class="max-w-6xl mx-auto px-4 sm:px-6">
        {#if isLoading}
            <div class="flex items-center justify-center min-h-[50vh]">
                <div class="text-white text-center">
                    <svg class="animate-spin h-8 w-8 mx-auto mb-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <p>Loading your dashboard...</p>
                </div>
            </div>
        {:else}
            <div class="flex flex-col sm:flex-row items-center justify-between gap-4 mb-6">
                <h1 class="text-3xl sm:text-4xl text-white font-bold">DASHBOARD</h1>
            <div class="flex flex-wrap items-center gap-4">
                <button
                    on:click={addWidget}
                    disabled={widgets.length >= 4}
                    class="flex items-center gap-2 px-3 sm:px-4 py-2 rounded-lg transition-colors text-sm sm:text-base whitespace-nowrap"
                    class:bg-blue-600={widgets.length < 4}
                    class:hover:bg-blue-700={widgets.length < 4}
                    class:bg-gray-600={widgets.length >= 4}
                    class:cursor-not-allowed={widgets.length >= 4}
                >
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 sm:h-5 sm:w-5" viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clip-rule="evenodd" />
                    </svg>
                    {widgets.length >= 4 ? 'Max Feeds' : 'Add Feed'}
                </button>
                
                <div class="relative">
                    <!-- svelte-ignore a11y_consider_explicit_label -->
                    <button
                        on:click={() => showUserMenu = !showUserMenu}
                        class="flex items-center gap-2 p-2 text-white hover:bg-gray-700 rounded-lg transition-colors text-sm sm:text-base"
                    >
                    </button>
                </div>
            </div>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6">
            {#each widgets as widget (widget.id)}
                <div class="bg-gray-800 text-white rounded-lg p-4 shadow">
                    <div class="flex items-start justify-between mb-4">
                        <h3 class="text-lg font-semibold">{widget.title}</h3>
                        <div class="flex gap-2">
                            <button
                                aria-label="Delete widget"
                                on:click={() => {
                                    deleteConfirm.widget = widget;
                                    deleteConfirm.show = true;
                                }}
                                class="p-1.5 text-gray-400 hover:text-red-400 hover:bg-gray-700 rounded-lg transition-colors"
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                                    <path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd" />
                                </svg>
                            </button>
                            <button
                                aria-label="Edit widget"
                                on:click={() => openEditMenu(widget)}
                                class="p-1.5 text-gray-400 hover:text-white hover:bg-gray-700 rounded-lg transition-colors"
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                                    <path fill-rule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clip-rule="evenodd" />
                                </svg>
                            </button>
                        </div>
                    </div>

                    <p class="text-sm text-gray-300 mb-4">{widget.description}</p>

                    <div class="flex items-center justify-between pt-2 border-t border-gray-700">
                        <div class="text-sm text-gray-400">
                            Status: {widget.enabled ? 'Enabled' : 'Disabled'}
                        </div>

                        <button
                            aria-label={`${widget.enabled ? 'Disable' : 'Enable'} ${widget.title}`}
                            class="relative inline-flex h-6 w-11 items-center rounded-full transition-colors"
                            class:bg-green-600={widget.enabled}
                            class:bg-gray-600={!widget.enabled}
                            on:click={() => toggleWidget(widget)}
                        >
                            <span
                                class="inline-block h-4 w-4 transform rounded-full bg-white transition-transform"
                                class:translate-x-6={widget.enabled}
                                class:translate-x-1={!widget.enabled}
                            ></span>
                        </button>
                    </div>
                </div>
            {/each}
            </div>
        {/if}

        <!-- Notification System -->
        {#if showNotification}
            <div class="fixed top-4 right-4 p-4 rounded-lg shadow-lg max-w-md z-50 transition-all"
                 class:bg-red-500={notificationType === 'error'}
                 class:bg-green-500={notificationType === 'success'}>
                <div class="flex justify-between items-start">
                    <div class="flex-1 mr-4 text-white">
                        <h3 class="font-semibold mb-2">
                            {#if notificationType === 'error'}
                                Error
                            {:else if notificationType === 'success'}
                                Success
                            {/if}
                        </h3>
                        <div class="text-sm whitespace-pre-wrap">
                            {#if notificationType === 'error'}
                                <pre class="font-mono bg-red-600/50 p-2 rounded">{notificationMessage}</pre>
                            {:else}
                                <p class="bg-green-600/50 p-2 rounded">{notificationMessage}</p>
                            {/if}
                        </div>
                    </div>
                    <button 
                        class="text-white transition-colors"
                        class:hover:text-red-200={notificationType === 'error'}
                        class:hover:text-green-200={notificationType === 'success'}
                        aria-label="Close notification"
                        on:click={() => { showNotification = false; notificationMessage = ''; }}
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                            <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
                        </svg>
                    </button>
                </div>
            </div>
        {/if}
    </div>
</div>

{#if editMenu.show}
    <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4">
        <div class="bg-gray-800 rounded-lg p-6 w-full max-w-md">
            <h2 class="text-xl text-white font-semibold mb-4">Edit Feed Hook</h2>
            
            <div class="space-y-4">
                <div>
                    <label class="block text-sm font-medium text-gray-300 mb-1" for="widget-title">
                        Title
                    </label>
                    <input
                        type="text"
                        id="widget-title"
                        bind:value={editMenu.title}
                        class="w-full px-3 py-2 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                    />
                </div>
                
                <div>
                    <label class="block text-sm font-medium text-gray-300 mb-1" for="widget-description">
                        Description
                    </label>
                    <textarea
                        id="widget-description"
                        bind:value={editMenu.description}
                        rows="2"
                        class="w-full px-3 py-2 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                    ></textarea>
                </div>

                <div>
                    <label class="block text-sm font-medium text-gray-300 mb-1" for="rss-url">
                        RSS Feed URL
                    </label>
                    <input
                        type="url"
                        id="rss-url"
                        placeholder="https://example.com/feed.xml"
                        bind:value={editMenu.rssUrl}
                        class="w-full px-3 py-2 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                    />
                </div>

                <div>
                    <label class="block text-sm font-medium text-gray-300 mb-1" for="webhook-url">
                        Discord Webhook URL
                    </label>
                    <input
                        type="url"
                        id="webhook-url"
                        placeholder="https://discord.com/api/webhooks/..."
                        bind:value={editMenu.webhookUrl}
                        class="w-full px-3 py-2 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                    />
                </div>
            </div>
            
            <div class="flex justify-end gap-3 mt-6">
                <button
                    on:click={() => {
                        if (editMenu.isNewWidget) {
                            widgets = widgets.filter(w => w.id !== editingWidget.id);
                        }
                        editMenu.show = false;
                    }}
                    class="px-4 py-2 text-gray-300 hover:text-white transition-colors"
                >
                    Cancel
                </button>
                <button
                    on:click={saveEditMenu}
                    class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                    Save Changes
                </button>
            </div>
        </div>
    </div>
{/if}

{#if deleteConfirm.show}
    <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4">
        <div class="bg-gray-800 rounded-lg p-4 w-full max-w-sm">
            <h3 class="text-lg text-white font-semibold mb-3">Delete Widget?</h3>
            <p class="text-sm text-gray-300 mb-4">
                Are you sure you want to delete "{deleteConfirm.widget?.title}"? This cannot be undone.
            </p>
            
            <div class="flex justify-end gap-3">
                <button
                    on:click={() => deleteConfirm.show = false}
                    class="px-3 py-1.5 text-gray-300 hover:text-white transition-colors"
                >
                    Cancel
                </button>
                <button
                    on:click={() => deleteWidget(deleteConfirm.widget)}
                    class="px-3 py-1.5 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                >
                    Delete
                </button>
            </div>
        </div>
    </div>
{/if}
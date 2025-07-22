- ✅ FIXED: Clicking "buy pack" from the homepage goes straight into the app - should direct to a purchase
    - Fixed by modifying LandingPage.svelte to store purchase intent in localStorage
    - Modified App.svelte to detect purchase intent after authentication and redirect to subscription manager
    - Modified SubscriptionManager.svelte to handle pack purchases and show pricing modal automatically
    - Users now see proper checkout flow when clicking "Buy Pack" from homepage
    - I'm guessing the pro plan is similar
- When I click "save scenario", I don't see the option to load that scenario.
    - I don't see it even if I reload the page - did it actually save?


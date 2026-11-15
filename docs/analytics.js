// PostHog analytics, shared by the Product Page and the app.
// Paste your PostHog Project API key below (PostHog > Settings > Project > Project API key).
// It starts with "phc_" and is safe to commit (it is a public key).
// If your PostHog account is in the EU, change us.i.posthog.com to eu.i.posthog.com.
var POSTHOG_KEY = "phc_PASTE_YOUR_KEY_HERE";
var POSTHOG_HOST = "https://us.i.posthog.com";

!function(t,e){var o,n,p,r;e.__SV||(window.posthog=e,e._i=[],e.init=function(i,s,a){function g(t,e){var o=e.split(".");2==o.length&&(t=t[o[0]],e=o[1]),t[e]=function(){t.push([e].concat(Array.prototype.slice.call(arguments,0)))}}(p=t.createElement("script")).type="text/javascript",p.crossOrigin="anonymous",p.async=!0,p.src=s.api_host.replace(".i.posthog.com","-assets.i.posthog.com")+"/static/array.js",(r=t.getElementsByTagName("script")[0]).parentNode.insertBefore(p,r);var u=e;for(void 0!==a?u=e[a]=[]:a="posthog",u.people=u.people||[],u.toString=function(t){var e="posthog";return"posthog"!==a&&(e+="."+a),t||(e+=" (stub)"),e},u.people.toString=function(){return u.toString(1)+".people (stub)"},o="init capture register register_once unregister identify alias reset opt_in_capturing opt_out_capturing has_opted_out_capturing startSessionRecording stopSessionRecording getFeatureFlag isFeatureEnabled onFeatureFlags reloadFeatureFlags".split(" "),n=0;n<o.length;n++)g(u,o[n]);e._i.push([i,s,a])},e.__SV=1)}(document,window.posthog||[]);

if (POSTHOG_KEY.indexOf("PASTE") === -1) {
  posthog.init(POSTHOG_KEY, {
    api_host: POSTHOG_HOST,
    person_profiles: "identified_only",
    autocapture: true,          // clicks
    capture_pageview: true,     // pageviews
    session_recording: { maskAllInputs: false }  // session replay (turn it on in PostHog settings too)
  });
}

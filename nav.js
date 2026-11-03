// Site banner. Add this as the first thing in <body>: <script src="/nav.js"></script>
// To add a page to the banner, add a line to LINKS.
(function () {
  const LINKS = [
    { href: "/about/", label: "About" },
    { href: "/cv/", label: "CV" },
    { href: "/projects/", label: "Projects" },
    { href: "/blog/", label: "Blog" },
  ];

  const css = `
    .site-banner {
      /* Pull out of the body's 24px/16px padding so the banner spans the page. */
      margin: -24px -16px 24px;
      padding: 12px 16px;
      background: var(--surface);
      border-bottom: 1px solid var(--border);
    }
    .site-banner-inner {
      max-width: 1100px;
      margin: 0 auto;
      display: flex;
      flex-wrap: wrap;
      align-items: baseline;
      gap: 6px 20px;
    }
    .site-banner a {
      color: var(--muted);
      text-decoration: none;
      font-size: 0.95rem;
    }
    .site-banner a:hover { text-decoration: underline; }
    .site-banner a[aria-current="page"] { color: var(--ink); font-weight: 600; }
    .site-banner a.site-banner-home {
      color: var(--ink);
      font-weight: 700;
      margin-right: auto;
    }
  `;

  const path = location.pathname;
  const links = LINKS.map(({ href, label }) => {
    const current = path.startsWith(href) ? ' aria-current="page"' : "";
    return `<a href="${href}"${current}>${label}</a>`;
  }).join("");

  document.currentScript.insertAdjacentHTML(
    "afterend",
    `<style>${css}</style>
     <nav class="site-banner" aria-label="Site">
       <div class="site-banner-inner">
         <a class="site-banner-home" href="/">njrovito</a>
         ${links}
       </div>
     </nav>`
  );
})();

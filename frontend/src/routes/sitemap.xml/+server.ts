// Static sitemap. Profile pages are auth-gated so we don't list them.
const SITE = 'https://marathakalyanam.com';

const urls: Array<{ loc: string; priority: string; changefreq: string }> = [
	{ loc: '/', priority: '1.0', changefreq: 'weekly' },
	{ loc: '/search', priority: '0.9', changefreq: 'daily' },
	{ loc: '/about', priority: '0.6', changefreq: 'monthly' },
	{ loc: '/register', priority: '0.8', changefreq: 'monthly' },
	{ loc: '/login', priority: '0.5', changefreq: 'monthly' }
];

export async function GET() {
	const today = new Date().toISOString().split('T')[0];
	const body =
		`<?xml version="1.0" encoding="UTF-8"?>\n` +
		`<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n` +
		urls
			.map(
				(u) =>
					`  <url>\n    <loc>${SITE}${u.loc}</loc>\n    <lastmod>${today}</lastmod>\n    <changefreq>${u.changefreq}</changefreq>\n    <priority>${u.priority}</priority>\n  </url>`
			)
			.join('\n') +
		`\n</urlset>\n`;

	return new Response(body, {
		headers: {
			'Content-Type': 'application/xml; charset=utf-8',
			'Cache-Control': 'public, max-age=3600'
		}
	});
}

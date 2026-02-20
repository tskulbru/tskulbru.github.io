import { defineConfig } from 'astro/config';
import { remarkReadingTime } from './src/utils/readingTime';
import rehypePrettyCode from 'rehype-pretty-code';
import tailwindcss from '@tailwindcss/vite';
import react from '@astrojs/react';
import sitemap from '@astrojs/sitemap';
import partytown from '@astrojs/partytown';
import fs from 'node:fs';
import path from 'node:path';

const options = {
    // Specify the theme to use or a custom theme json, in our case
    // it will be a moonlight-II theme from
    // https://github.com/atomiks/moonlight-vscode-theme/blob/master/src/moonlight-ii.json
    // Callbacks to customize the output of the nodes
    //theme: json,
    onVisitLine(node) {
        // Prevent lines from collapsing in `display: grid` mode, and
        // allow empty lines to be copy/pasted
        if (node.children.length === 0) {
            node.children = [
                {
                    type: 'text',
                    value: ' '
                }
            ];
        }
    },
    onVisitHighlightedLine(node) {
        // Adding a class to the highlighted line
        node.properties.className = ['highlighted'];
    }
};

// Build a map of blog post slugs to their dates from frontmatter
function getPostDates() {
    const postsDir = path.resolve('./src/pages/posts');
    const dateMap = {};
    const files = fs.readdirSync(postsDir).filter(f => f.endsWith('.md'));
    for (const file of files) {
        const content = fs.readFileSync(path.join(postsDir, file), 'utf-8');
        const pubMatch = content.match(/pubDate:\s*['"]?(\d{4}-\d{2}-\d{2})['"]?/);
        const modMatch = content.match(/modifiedDate:\s*['"]?(\d{4}-\d{2}-\d{2})['"]?/);
        const slug = file.replace('.md', '');
        dateMap[slug] = {
            lastmod: modMatch ? modMatch[1] : pubMatch ? pubMatch[1] : null
        };
    }
    return dateMap;
}
const postDates = getPostDates();

// https://astro.build/config
export default defineConfig({
    site: 'https://tskulbru.dev',

    markdown: {
        syntaxHighlight: false,
        // Disable syntax built-in syntax hightlighting from astro
        rehypePlugins: [[rehypePrettyCode, options]],
        remarkPlugins: [remarkReadingTime]
    },

    integrations: [
		react(),
		sitemap({
			filter: (page) => !page.includes('/draft/'),
			serialize(item) {
				const url = item.url;
				// Homepage
				if (url === 'https://tskulbru.dev/' || url === 'https://tskulbru.dev') {
					item.priority = 1.0;
					item.changefreq = 'weekly';
				// Blog post listing and portfolio
				} else if (url.endsWith('/posts/') || url.endsWith('/portfolio/')) {
					item.priority = 0.9;
					item.changefreq = 'weekly';
				// Individual blog posts - use actual dates
				} else if (url.includes('/posts/') && !url.endsWith('/posts/')) {
					item.priority = 0.8;
					item.changefreq = 'monthly';
					const slug = url.replace('https://tskulbru.dev/posts/', '').replace(/\/$/, '');
					if (postDates[slug]?.lastmod) {
						item.lastmod = new Date(postDates[slug].lastmod).toISOString();
					}
				// Tag pages
				} else if (url.includes('/tags/')) {
					item.priority = 0.5;
					item.changefreq = 'weekly';
				// App privacy/support pages
				} else if (url.includes('/apps/')) {
					item.priority = 0.3;
					item.changefreq = 'yearly';
				} else {
					item.priority = 0.7;
					item.changefreq = 'weekly';
				}
				return item;
			},
		}),
		partytown({
			config: {
				// Add the "dataLayer.push" as a forwarding-event.
				forward: ['dataLayer.push'],
			}
		})
	],
    output: 'static',

    vite: {
        plugins: [tailwindcss()]
    }
});
import { defineConfig } from 'astro/config';
import { remarkReadingTime } from './src/utils/readingTime';
import rehypePrettyCode from 'rehype-pretty-code';
import tailwindcss from '@tailwindcss/vite';
import react from '@astrojs/react';
import sitemap from '@astrojs/sitemap';
import partytown from '@astrojs/partytown';

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
			filter: (page) => {
				// Exclude draft pages or any pages you don't want indexed
				return !page.includes('/draft/');
			},
			changefreq: 'weekly',
			priority: 0.7,
			lastmod: new Date(),
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
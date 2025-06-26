export interface SEOProps {
	title: string;
	description: string;
	image?: string;
	imageAlt?: string;
	type?: 'website' | 'article';
	publishedTime?: string;
	modifiedTime?: string;
	tags?: string[];
	author?: string;
	canonicalURL?: string;
}

export function generateSocialShareUrls(url: string, title: string, blueskyUri?: string) {
	const encodedUrl = encodeURIComponent(url);
	const encodedTitle = encodeURIComponent(title);
	
	// Generate Bluesky share URL
	let blueskyUrl = '';
	if (blueskyUri) {
		// Convert AT URI to web URL for the original post
		// AT URI format: at://did:plc:rmnykyqh3zleost7ii4qe5nc/app.bsky.feed.post/3lqwaglsecc2j
		const parts = blueskyUri.split('/');
		const did = parts[2];
		const postId = parts[4];
		// Link directly to the original post so users can quote it manually
		blueskyUrl = `https://bsky.app/profile/${did}/post/${postId}`;
	} else {
		// Fallback to regular compose intent
		const shareText = `${title} ${url}`;
		blueskyUrl = `https://bsky.app/intent/compose?text=${encodeURIComponent(shareText)}`;
	}
	
	return {
		twitter: `https://twitter.com/intent/tweet?url=${encodedUrl}&text=${encodedTitle}`,
		linkedin: `https://www.linkedin.com/sharing/share-offsite/?url=${encodedUrl}`,
		facebook: `https://www.facebook.com/sharer/sharer.php?u=${encodedUrl}`,
		reddit: `https://www.reddit.com/submit?url=${encodedUrl}&title=${encodedTitle}`,
		hackernews: `https://news.ycombinator.com/submitlink?u=${encodedUrl}&t=${encodedTitle}`,
		bluesky: blueskyUrl
	};
}

export function generateBreadcrumbStructuredData(breadcrumbs: Array<{name: string, url: string}>) {
	return {
		"@context": "https://schema.org",
		"@type": "BreadcrumbList",
		"itemListElement": breadcrumbs.map((crumb, index) => ({
			"@type": "ListItem",
			"position": index + 1,
			"name": crumb.name,
			"item": crumb.url
		}))
	};
}

export function generateFAQStructuredData(faqs: Array<{question: string, answer: string}>) {
	return {
		"@context": "https://schema.org",
		"@type": "FAQPage",
		"mainEntity": faqs.map(faq => ({
			"@type": "Question",
			"name": faq.question,
			"acceptedAnswer": {
				"@type": "Answer",
				"text": faq.answer
			}
		}))
	};
}

export function getEstimatedReadingTime(content: string): number {
	const wordsPerMinute = 200;
	const wordCount = content.trim().split(/\s+/).length;
	return Math.ceil(wordCount / wordsPerMinute);
} 
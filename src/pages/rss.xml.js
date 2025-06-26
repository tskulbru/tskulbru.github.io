import rss, {pagesGlobToRssItems} from '@astrojs/rss';

export async function GET(context) {
  return rss({
    title: 'tskulbru.dev | Development, Cloud Architecture & DevOps Blog',
    description: 'Technical blog covering Kubernetes, microservices, cloud architecture, mobile development, and modern development practices. Deep dives into K8s, Go, Android, database migrations, and production-ready solutions.',
    site: context.site,
    items: await pagesGlobToRssItems(
      import.meta.glob('./posts/*.{md,mdx}'),
    ),
    stylesheet: './rss/styles.xsl',
    customData: `<language>en-us</language>`,
  });
}
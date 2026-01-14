---
layout: ../../layouts/post.astro
title: "Letting Bluesky Handle My Blog Comments"
pubDate: 2025-06-09
description: "Why I decided to use Bluesky as the comment section for my blog, and what it feels like to let the conversation happen out in the open."
author: "Torstein Skulbru"
isPinned: false
excerpt: "I've always wanted a comment section that felt more like a conversation and less like a chore. Here's why I let Bluesky take over my blog comments."
blueskyUri: "at://did:plc:rmnykyqh3zleost7ii4qe5nc/app.bsky.feed.post/3lr7boayidk2k"
image:
  src: "/images/bsky-comment.png"
  alt: "An example comment on a blog post"
tags: ["bluesky", "blog", "meta"]
modifiedDate: 2026-01-14
---

I've always had mixed feelings about blog comments. On one hand, I love the idea of readers chiming in, sharing their thoughts, and maybe even sparking a little debate. On the other hand, traditional comment sections can be a magnet for spam, require constant moderation, and often feel a bit... disconnected from the rest of the web.

So, for a long time, I just didn't have comments at all. If you wanted to say something, you could always find me on Twitter (well, X), or send an email. But it never felt quite right.

### Enter Bluesky

Recently, I stumbled across a few blog posts ([Jade Garafola](https://blog.jade0x.com/post/adding-bluesky-comments-to-your-astro-blog/) and [Jaap Stronks](https://www.jaapstronks.nl/blog/add-bluesky-comments-to-your-astro-blog/)) about using Bluesky as a comment system. The idea is simple: when I publish a new post, I share it on Bluesky. Any replies to that post become the "comments" for the blog post itself.

Now, instead of a lonely comment box at the bottom of the page, there's a real conversation happening out in the open, where anyone can join in, follow threads, and see who's talking. It feels more like a town square and less like a locked suggestion box.

### Why I Like It

- **No more spam filters.** If you want to comment, you do it with your real Bluesky account.
- **The conversation is public.** Anyone can join, and you can follow interesting people you meet in the comments.
- **It's easy for me.** I don't have to moderate, update plugins, or worry about GDPR.
- **It feels more connected.** Comments aren't just for my blog—they're part of the wider Bluesky network.

### How It Works (in a nutshell)

Whenever I write a new post, I share it on Bluesky. I grab the post's unique URI and add it to the blog post's metadata. My site then fetches replies to that Bluesky post and shows them as comments right here, at the bottom of the page. If you want to join the conversation, just reply to the Bluesky thread!

### Give It a Try

Scroll down to the comments section and see what people are saying. Want to add your own thoughts? Just click the link to reply on Bluesky. I'd love to hear what you think—about this post, about Bluesky, or about anything else.

Maybe this is the future of blog comments. Or maybe it's just a fun experiment. Either way, I'm enjoying the conversation.

### How I Set It Up

If you're curious how this works under the hood, here's how I set up Bluesky comments on my Astro blog. It's not too tricky!

#### 1. The Comments Component

I created a file at `src/components/CommentSection.astro`:

```astro
---
interface Props {
  uri: string;
}

const { uri } = Astro.props;

// Get the post ID for the Bluesky link
const postId = uri.split('/').pop();
const blueskyLink = `https://bsky.app/profile/${uri.split('/')[2]}/post/${postId}`;
---

<div class="comments-section mt-8 pt-6" data-bluesky-uri={uri}>
  <h2 class="text-2xl font-bold pb-4">Comments</h2>
  <div class="rounded-2xl bg-stone-200/50 p-[1px] shadow-[inset_0_0_0_1px_rgba(255,255,255,0.4)] dark:bg-gray-900 mb-6">
    <div class="rounded-[1rem] bg-stone-300 p-4 dark:bg-stone-800">
      <p class="text-sm text-gray-700 dark:text-gray-300">
        Reply on Bluesky <a href={blueskyLink} target="_blank" rel="noopener noreferrer" class="font-bold text-orange-600 hover:text-orange-700 underline">here</a> to join the conversation.
      </p>
    </div>
  </div>

  <div class="comments-loader text-center py-8 text-gray-600 dark:text-gray-400">Loading comments...</div>
  <div class="comments-error text-center py-4 text-red-600 dark:text-red-400" style="display: none;"></div>
  <div class="comments-list space-y-4" style="display: none;"></div>

  <button class="refresh-comments mt-6 px-4 py-2 rounded-xl bg-stone-600 text-white text-sm font-bold uppercase hover:bg-stone-500 transition-colors duration-200">
    Refresh Comments
  </button>
</div>

<script>
  import { initializeCommentSections } from '@/utils/commentSection';
  initializeCommentSections();
</script>
```

#### 2. The JavaScript/TypeScript Logic

I put the logic for fetching and rendering comments in `src/utils/commentSection.ts`:

```ts
interface BlueskyPost {
  post: {
    author: {
      avatar: string;
      displayName: string;
      handle: string;
    };
    record: {
      text: string;
    };
    indexedAt: string;
    likeCount: number;
    repostCount: number;
    replyCount: number;
  };
  replies?: BlueskyPost[];
}

class CommentSection {
  private readonly uri: string;
  private readonly loader: HTMLElement;
  private readonly errorDiv: HTMLElement;
  private readonly commentsList: HTMLElement;
  private readonly refreshButton: HTMLElement;

  constructor(container: HTMLElement) {
    const uri = container.dataset.blueskyUri;
    if (!uri) throw new Error('Bluesky URI is required');
    this.uri = uri;

    const loader = container.querySelector('.comments-loader');
    const errorDiv = container.querySelector('.comments-error');
    const commentsList = container.querySelector('.comments-list');
    const refreshButton = container.querySelector('.refresh-comments');

    if (!loader || !errorDiv || !commentsList || !refreshButton) {
      throw new Error('Required DOM elements not found');
    }

    this.loader = loader as HTMLElement;
    this.errorDiv = errorDiv as HTMLElement;
    this.commentsList = commentsList as HTMLElement;
    this.refreshButton = refreshButton as HTMLElement;

    this.initialize();
  }

  private async initialize() {
    this.refreshButton.addEventListener('click', () => this.fetchComments());
    await this.fetchComments();
    setInterval(() => this.fetchComments(), 5 * 60 * 1000);
  }

  private async fetchComments() {
    this.loader.style.display = 'block';
    this.errorDiv.style.display = 'none';
    this.commentsList.style.display = 'none';

    try {
      const endpoint = `https://api.bsky.app/xrpc/app.bsky.feed.getPostThread?uri=${encodeURIComponent(this.uri)}`;
      const response = await fetch(endpoint, {
        method: 'GET',
        headers: { 'Accept': 'application/json' }
      });

      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const data = await response.json();
      const comments = data.thread?.replies || [];
      this.renderComments(comments);
      this.loader.style.display = 'none';
      this.commentsList.style.display = 'block';
    } catch (error: unknown) {
      this.loader.style.display = 'none';
      this.errorDiv.style.display = 'block';
      const errorMessage = error instanceof Error ? error.message : 'An unknown error occurred';
      this.errorDiv.textContent = `Error loading comments: ${errorMessage}`;
    }
  }

  private renderComments(comments: BlueskyPost[]) {
    if (comments.length === 0) {
      this.commentsList.innerHTML = '<p class="no-comments">No comments yet. Be the first to comment!</p>';
      return;
    }
    this.commentsList.innerHTML = comments.map(comment => this.renderComment(comment)).join('');
  }

  private renderComment(comment: BlueskyPost): string {
    const date = new Date(comment.post.indexedAt).toLocaleDateString();
    const renderReplies = (replies: BlueskyPost[] = []): string => {
      if (replies.length === 0) return '';
      return `
        <div class="replies">
          ${replies.map(reply => {
            const replyDate = new Date(reply.post.indexedAt).toLocaleDateString();
            return `
              <div class="comment reply">
                <div class="comment-header">
                  <img src="${reply.post.author.avatar}" alt="${reply.post.author.displayName}'s avatar" class="avatar" style="width: 32px; height: 32px; border-radius: 50%; object-fit: cover;" />
                  <div class="author-info">
                    <span class="author-name">${reply.post.author.displayName}</span>
                    <span class="author-handle">@${reply.post.author.handle}</span>
                  </div>
                </div>
                <div class="comment-content">${reply.post.record.text}</div>
                <div class="comment-footer">
                  <div class="interaction-counts">
                    <span>${reply.post.replyCount || 0} 💬</span>
                    <span>${reply.post.repostCount || 0} 🔁</span>
                    <span>${reply.post.likeCount || 0} ❤️</span>
                  </div>
                  <time datetime="${reply.post.indexedAt}">${replyDate}</time>
                </div>
                ${renderReplies(reply.replies)}
              </div>
            `;
          }).join('')}
        </div>
      `;
    };

    return `
      <div class="comment">
        <div class="comment-header">
          <img src="${comment.post.author.avatar}" alt="${comment.post.author.displayName}'s avatar" class="avatar" style="width: 32px; height: 32px; border-radius: 50%; object-fit: cover;" />
          <div class="author-info">
            <span class="author-name">${comment.post.author.displayName}</span>
            <span class="author-handle">@${comment.post.author.handle}</span>
          </div>
        </div>
        <div class="comment-content">${comment.post.record.text}</div>
        <div class="comment-footer">
          <div class="interaction-counts">
            <span>${comment.post.replyCount || 0} 💬</span>
            <span>${comment.post.repostCount || 0} 🔁</span>
            <span>${comment.post.likeCount || 0} ❤️</span>
          </div>
          <time datetime="${comment.post.indexedAt}">${date}</time>
        </div>
        ${renderReplies(comment.replies)}
      </div>
    `;
  }
}

// Initialize all comment sections on the page
export function initializeCommentSections() {
  document.querySelectorAll('.comments-section').forEach(container => {
    new CommentSection(container as HTMLElement);
  });
}

// Auto-initialize when DOM is loaded
if (typeof window !== 'undefined') {
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeCommentSections);
  } else {
    initializeCommentSections();
  }
}
```

#### 3. Add the Component to Your Blog Post Layout

In your blog post layout (for me, it's `src/layouts/post.astro`), I include the comments section like this:

```astro
{frontmatter.blueskyUri && <CommentSection uri={frontmatter.blueskyUri} />}
```

#### 4. How to Get Your Bluesky Post URI

To connect your blog post to a Bluesky thread, you need the unique URI for your Bluesky post. Here's how to get it:

**Step 1: Find your Bluesky DID (decentralized identifier)**

- Go to your Bluesky profile settings.
- Look for your DID. It usually starts with `did:plc:` and is a long string of letters and numbers.
<video width="500" height="200" controls loop video controls autoplay>
    <source src="/assets/bsky-capture.mp4" type="video/mp4">
    Your browser does not support the video tag.
</video>

**Step 2: Get the Post ID**

- After you share your blog post on Bluesky, click the timestamp on your Bluesky post to open the single post view.
- Look at the URL in your browser. The last part after the final slash is your post ID.
![](/images/bsky-link.png)

**Step 3: Format the URI**

- The final URI should look like this:

  ```yaml
  at://did:plc:your-did/app.bsky.feed.post/your-post-id
  ```

  Replace `your-did` with your Bluesky DID, and `your-post-id` with the post ID you just found.

#### 5. Add the Bluesky URI to Your Post

Now, add the URI to your blog post's frontmatter:

```yaml
blueskyUri: "at://did:plc:your-did/app.bsky.feed.post/your-post-id"
```

That's it! After you publish your blog and update the frontmatter, your comments section will show replies from your Bluesky post.

---

*For more details and helpful visuals, check out [Jaap Stronks' guide](https://www.jaapstronks.nl/blog/add-bluesky-comments-to-your-astro-blog/).* 
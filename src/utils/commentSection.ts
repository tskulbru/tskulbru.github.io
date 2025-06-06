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
    if (!uri) {
      throw new Error('Bluesky URI is required');
    }
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

    // Auto-refresh comments every 5 minutes
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
        headers: {
          'Accept': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      const comments = data.thread?.replies || [];

      this.renderComments(comments);
      this.loader.style.display = 'none';
      this.commentsList.style.display = 'block';
    } catch (error: unknown) {
      this.loader.style.display = 'none';
      this.errorDiv.style.display = 'block';

      const errorMessage = error instanceof Error
        ? error.message
        : 'An unknown error occurred';

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
                  <img src="${reply.post.author.avatar}"
                       alt="${reply.post.author.displayName}'s avatar"
                       class="avatar"
                       style="width: 32px; height: 32px; border-radius: 50%; object-fit: cover;" />
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
          <img src="${comment.post.author.avatar}"
               alt="${comment.post.author.displayName}'s avatar"
               class="avatar"
               style="width: 32px; height: 32px; border-radius: 50%; object-fit: cover;" />
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
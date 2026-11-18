# StoryShield Updates

## Recent Feature Updates

### 1. Spoiler-safe reading with optional future spoilers

- Answers are limited to the reader's saved chapter and page by default.
- A new "Allow future spoilers" switch lets readers explicitly include future book context.
- The companion also uses a spoiler-aware system prompt when this option is enabled.
- Users receive clear feedback when a question is blocked or when spoiler mode is active.

### 2. "Summary so far" panel

- Readers can generate a summary of everything available up to their current reading position.
- Summary requests retrieve a broader set of relevant chunks and remain spoiler-safe.
- The interface displays a loading state and clearly reports errors or empty responses.

### 3. Saved reading bookmarks

- The reader can save the current chapter and page.
- Saved progress is restored when a book is reopened.
- The embedded PDF opens at the bookmarked page, and the reader interface shows the current position.
- Bookmark controls provide success and failure feedback.

### 4. Read and pending book tracking

- Each book can be marked as "Read" or moved back to "Pending."
- The library header shows separate counts for read, pending, and total books.
- Book cards display their current reading status for quick scanning.

### 5. Improved upload and assistant error handling

- PDFs without extractable text now return a clear 422 error instead of being indexed as an empty book.
- Failed uploads are recorded with a failed status and an explanation.
- Empty responses from the Groq assistant are rejected and converted into a clear retryable API error.
- Retrieval, spoiler opt-in, reading-status, and empty-response behavior are covered by focused backend tests.

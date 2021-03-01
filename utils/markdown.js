import remark from 'remark';
import remarkHtml from 'remark-html';

export async function markdownToHtml(content) {
    const options = {
        sanitize: true,
    };
    const result = await remark().use(remarkHtml, options).process(content);
    return result.toString();
}

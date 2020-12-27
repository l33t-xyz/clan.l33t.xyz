import remark from 'remark';
import html from 'remark-html';

export default async function markdownToHtml(markdown) {
    const options = {
        sanitize: true,
    };
    const result = await remark().use(html, options).process(markdown);
    return result.toString();
}

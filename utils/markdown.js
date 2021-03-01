import html from 'remark-html';
//import mdx from 'remark-mdx';
import remark from 'remark';

export async function markdownToHtml(content) {
    const options = {
        sanitize: true,
    };
    const result = await remark().use(html, options).process(content);
    return result.toString();
}

// export async function mdxToJSX(content) {
//     const jsx = await remark().use(mdx).process(content);
//     return jsx;
// }

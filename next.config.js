// next.config.js
// https://nextjs.org/docs/api-reference/next.config.js/introduction
// https://github.com/vercel/next.js/blob/canary/packages/next/next-server/server/config.ts

// https://mdxjs.com/getting-started/next

const withMDX = require('@next/mdx')({
    extension: /\.mdx?$/,
    options: {
        remarkPlugins: [],
        rehypePlugins: [],
    },
});

module.exports = withMDX({
    basePath: '',
    pageExtensions: ['js', 'jsx', 'md', 'mdx'],
    webpack: (config, options) => {
        config.node = {
            fs: 'empty',
        };
        return config;
    },
});

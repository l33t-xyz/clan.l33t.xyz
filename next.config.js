// next.config.js
// https://nextjs.org/docs/api-reference/next.config.js/introduction

// https://mdxjs.com/getting-started/next

const withMDX = require('@next/mdx')({
    extension: /\.mdx?$/,
    options: {
        remarkPlugins: [],
        rehypePlugins: [],
    },
});

const nextConfig = {
    pageExtensions: ['js', 'jsx', 'md', 'mdx'],
    webpack: (config, { isServer }) => {
        if (!isServer) {
            // Fallbacks for Node.js modules required by MDX
            config.resolve.fallback = {
                fs: false,
            };
        }
        return config;
    },
};

module.exports = withMDX(nextConfig);

// next.config.js
// https://nextjs.org/docs/api-reference/next.config.js/introduction

const path = require('path');

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
        // Define path aliases
        config.resolve.alias['@components'] = path.join(
            __dirname,
            'components'
        );
        config.resolve.alias['@styles'] = path.join(__dirname, 'styles');
        config.resolve.alias['@utils'] = path.join(__dirname, 'utils');

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

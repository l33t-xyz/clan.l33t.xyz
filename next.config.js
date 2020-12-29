// next.config.js
// https://nextjs.org/docs/api-reference/next.config.js/introduction
// https://github.com/vercel/next.js/blob/canary/packages/next/next-server/server/config.ts


const { PHASE_DEVELOPMENT_SERVER } = require('next/constants')

module.exports = (phase, { defaultConfig }) => {
    if (phase === PHASE_DEVELOPMENT_SERVER) {
        return {
            /* development only config options here */
            basePath: ''
        }
    }

    return {
        /* config options for all phases except development here */
        basePath: ''
    }
}

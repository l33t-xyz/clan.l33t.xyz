import { markdownToHtml } from './markdown';

const CLAN_API_PROTOCOL = 'https';
const CLAN_API_BASE_URL = 'l33t.xyz';

export async function getClanPageServerSideProps(context) {
    let result = null;

    const defaultResult = {
        notFound: true,
    };

    const hostname = context.req.headers.host;
    const path = context.resolvedUrl;
    const clanName = getClanFromHostnameOrPath(hostname, path);

    if (clanName) {
        const site = await fetchClanSite(clanName);
        result = {
            props: { site },
        };
    } else {
        result = defaultResult;
    }

    return result;
}

export function getClanFromHostnameOrPath(hostname, path) {
    let clanName = null;

    const clanHostnameMatch = hostname.match(
        /^(?<clanName>[a-z]+)\.clan\.l33t\.xyz$/
    );
    const localHostnameMatch = hostname.match(/^localhost:\d+$/);

    if (clanHostnameMatch) {
        clanName = clanHostnameMatch.groups.clanName;
    } else if (localHostnameMatch) {
        const pathParts = path.split('/');
        clanName = pathParts[1];
    }

    return clanName;
}

export async function fetchClanSite(clanName) {
    let site;

    const res = await fetch(
        `${CLAN_API_PROTOCOL}://${CLAN_API_BASE_URL}/api/clans/${clanName}/public`
    );
    const data = await res.json();

    if (!data || !data.success) {
        site = null;
    } else {
        site = data.site;

        // convert Markdown to HTML
        // for (let i = 0; i < site.public_pages.length; ++i) {
        //     const page = site.public_pages[i];
        //     const content = page.content || '';
        //     const html = await markdownToHtml(content);
        //     page.html = html;
        // }
    }
    return site;
}

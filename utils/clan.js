import { markdownToHtml } from './markdown';

const CLAN_API_PROTOCOL = 'https';
const CLAN_API_BASE_URL = 'l33t.xyz';

export async function getClanPageServerSideProps(context) {
    let result = null;

    const defaultResult = {
        notFound: true,
    };

    const { cookie, host } = context.req.headers;
    const path = context.resolvedUrl;
    const clanName = getClanFromHostnameOrPath(host, path);

    if (clanName) {
        const site = await fetchClanSite(clanName, cookie);
        result = {
            props: { site },
        };
    } else {
        result = defaultResult;
    }

    return result;
}

export function getClanFromHostnameOrPath(host, path) {
    let clanName = null;

    const clanHostnameMatch = host.match(
        /^(?<clanName>[a-z]+)\.(dev\.)?clan\.l33t\.xyz(:\d+)?$/
    );
    const localHostnameMatch = host.match(/^localhost:\d+$/);

    if (clanHostnameMatch) {
        clanName = clanHostnameMatch.groups.clanName;
    } else if (localHostnameMatch) {
        const pathParts = path.split('/');
        clanName = pathParts[1];
    }

    return clanName;
}

export async function fetchClanSite(clanName, cookie) {
    let site;

    const res = await fetch(
        `${CLAN_API_PROTOCOL}://jontsai.dev.${CLAN_API_BASE_URL}/api/clans/${clanName}/public`,
        {
            credentials: 'include',
            headers: {
                cookie,
            },
        }
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

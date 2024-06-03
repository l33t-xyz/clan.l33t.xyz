import { useEffect } from 'react';

export function Layout(props) {
    useEffect(() => {
        const site = props.children.props.site || {};
        const siteMeta = site.meta || {};
        const siteSettings = siteMeta.settings || {};
        const theme = siteSettings.theme || 'default';
        document.querySelector('body').classList.add(`theme-${theme}`);
    });

    return (
        <div className="page-layout">
            {props.children}
            <style jsx global>{`
                body {
                    margin: 0;
                    padding: 0;
                    font-family: sans-serif;
                }
            `}</style>
        </div>
    );
}

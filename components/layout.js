import { useEffect } from 'react';

function Layout(props) {
    useEffect(() => {
        const site = props.children.props.site;
        const siteSettings = site.meta.settings;
        const theme = siteSettings.theme; // default, dark-forest, dark-steel-blue
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

export default Layout;

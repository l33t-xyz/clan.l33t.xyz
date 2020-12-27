import Head from 'next/head';

import Header from '../components/header';
import Footer from '../components/footer';
import CommonCSS from '../components/css/common';
import CommonJS from '../components/js/common';
import NonBlockingJS from '../components/js/nonblocking';

import css from '../styles/common.module.scss';
import utilsCss from '../styles/utils.module.scss';

export default function Page({ children, ...props }) {
    return (
        <div className={css.container}>
            <Head>
                <title>{props.site.name}</title>

                <meta charSet="utf-8" />
                <meta
                    name="viewport"
                    content="width=device-width, initial-scale=1, shrink-to-fit=no"
                />

                <link rel="icon" href="/favicon.ico" />
            </Head>
            <CommonCSS />
            <CommonJS />
            <main className={css.main}>{children}</main>
            <Footer {...props} />
            <NonBlockingJS />
        </div>
    );
}

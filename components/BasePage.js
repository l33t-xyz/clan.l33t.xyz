import Head from 'next/head';
import React from 'react';

import { Header } from '@components/Header';
import { Footer } from '@components/Footer';
import CommonCSS from '@components/css/common';
import CommonJS from '@components/js/common';
import NonBlockingJS from '@components/js/nonblocking';

import css from '@styles/common.module.scss';
import utilsCss from '@styles/utils.module.scss';

function BasePage(WrappedComponent) {
    return class extends React.Component {
        constructor(props) {
            super(props);
            this.state = {
                site: props.site,
            };
        }

        render() {
            const site = this.props.site;
            return (
                <div className={css.container}>
                    <Head>
                        <title>{site.name}</title>

                        <meta charSet="utf-8" />
                        <meta
                            name="viewport"
                            content="width=device-width, initial-scale=1, shrink-to-fit=no"
                        />

                        <link rel="icon" href="/favicon.ico" />
                    </Head>
                    <CommonCSS />
                    <CommonJS />
                    <main className={css.main}>
                        <WrappedComponent page={this} />
                    </main>
                    <Footer site={site} />
                    <NonBlockingJS />
                </div>
            );
        }
    };
}

export default BasePage;

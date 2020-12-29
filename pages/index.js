import {Col, Nav, Navbar, Row, Tab} from 'react-bootstrap';

import Safe from 'react-safe';

import Page from '../components/base_page';

import css from '../styles/common.module.scss';

import markdownToHtml from '../lib/markdownToHtml';

export default function IndexPage({ site }) {
    const defaultActiveKey = site.public_pages[0].slug;

    const navItemsJSX = site.public_pages.map((page, index) => {
        return (
            <Nav.Item key={`nav-item-${index}`}>
                <Nav.Link eventKey={page.slug}>{page.title}</Nav.Link>
            </Nav.Item>
        );
    });

    const tabPanesJSX = site.public_pages.map((page, index) => {
        return (
            <Tab.Pane eventKey={page.slug} key={page.slug}>
                <Safe.div>{page.html}</Safe.div>
            </Tab.Pane>
        );
    });

    return (
        <Page site={site}>
            <Tab.Container id="nav-tabs" defaultActiveKey={defaultActiveKey}>
                <Navbar
                    collapseOnSelect
                    fixed="top"
                    bg="dark"
                    variant="dark"
                    expand="lg"
                >
                    <Navbar.Brand>{site.name}</Navbar.Brand>
                    <Navbar.Toggle aria-controls="responsive-navbar-nav" />
                    <Navbar.Collapse id="responsive-navbar-nav">
                        <Nav className="mr-auto nav">{navItemsJSX}</Nav>
                    </Navbar.Collapse>
                </Navbar>
                <Tab.Content>{tabPanesJSX}</Tab.Content>
            </Tab.Container>
        </Page>
    );
}

export async function getServerSideProps(context) {
    const res = await fetch(`https://l33t.xyz/api/clans/amazon/public`);
    const data = await res.json();

    if (!data) {
        return {
            notFound: true,
        };
    }

    for (let i = 0; i < data.public_pages.length; ++i) {
        const page = data.public_pages[i];
        const html = await markdownToHtml(page.content || '');
        page.html = html;
    }

    return {
        props: { site: data },
    };
}

import { Col, Nav, Navbar, Row, Tab, Jumbotron } from 'react-bootstrap';
import React, { useState, useEffect } from 'react';
import Safe from 'react-safe';
import MDX from '@mdx-js/runtime';

/**
 * This provides the ClanPage component,
 * which is a React component that renders a page
 * with a Tabbed navigation bar.
 */
const ClanPage = ({ page }) => {
    const [activeKey, setActiveKey] = useState(null);

    const site = page.props.site;
    const defaultActiveKey = site.public_pages[0].slug;

    useEffect(() => {
        // https://github.com/l33t-xyz/xterm.js
        formatXtermWidgets();
    });

    const makeNavClickHandler = (activeKey) => () => {
        setActiveKey(activeKey);
    };

    const navItemsJSX = site.public_pages.map((page, index) => (
        <Nav.Item key={`nav-item-${index}`}>
            <Nav.Link
                eventKey={page.slug}
                onClick={makeNavClickHandler(page.slug)}
            >
                {page.title}
            </Nav.Link>
        </Nav.Item>
    ));

    const tabPanesJSX = site.public_pages.map((page, index) => {
        const attachments = page.attachments;
        let heroImage = null;
        if (attachments.length > 0) {
            heroImage = attachments[0].thumbnails.large.url;
        }

        const heroStyle = {};
        if (heroImage) {
            heroStyle.backgroundImage = `url(${heroImage})`;
            heroStyle.backgroundRepeat = 'no-repeat';
            heroStyle.attachment = 'fixed';
            heroStyle.backgroundPosition = 'center';
            heroStyle.backgroundSize = 'cover';
        }

        let pageContentJSX = null;

        if (page.slug === 'members') {
            const loginStatus = site.member
                ? `Welcome back, ${site.member.name}!`
                : 'You are not logged in.';

            pageContentJSX = <div className="page-content">{loginStatus}</div>;
        } else {
            pageContentJSX = (
                <div className="page-content">
                    <MDX>{page.content || ''}</MDX>
                </div>
            );
        }

        // const pageContentJSX = (
        //     <Safe.div className="page-content">
        //         {page.html}
        //     </Safe.div>
        // );

        return (
            <Tab.Pane eventKey={page.slug} key={page.slug}>
                <Jumbotron fluid className="jumbotron" style={heroStyle}>
                    <h1 className="page-title">{page.title}</h1>
                </Jumbotron>
                {pageContentJSX}
            </Tab.Pane>
        );
    });

    const currentActiveKey = activeKey || defaultActiveKey;

    return (
        <div>
            <Tab.Container
                id="nav-tabs"
                activeKey={currentActiveKey}
                defaultActiveKey={defaultActiveKey}
            >
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
        </div>
    );
};

export default ClanPage;

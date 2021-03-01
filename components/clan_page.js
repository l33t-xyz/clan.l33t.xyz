import { Col, Nav, Navbar, Row, Tab, Jumbotron } from 'react-bootstrap';
import Safe from 'react-safe';
import MDX from '@mdx-js/runtime';

import BasePage from './base_page';

import { getClanPageServerSideProps } from '../utils/clan';

class ClanPage extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            activeKey: null,
        };
    }

    componentDidUpdate() {
        // https://github.com/l33t-xyz/xterm.js
        formatXtermWidgets();
    }

    render() {
        const site = this.props.page.props.site;

        const defaultActiveKey = site.public_pages[0].slug;

        const navItemsJSX = site.public_pages.map((page, index) => {
            return (
                <Nav.Item key={`nav-item-${index}`}>
                    <Nav.Link
                        eventKey={page.slug}
                        onClick={this.makeNavClickHandler(page.slug).bind(this)}
                    >
                        {page.title}
                    </Nav.Link>
                </Nav.Item>
            );
        });

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

            const pageContentJSX = (
                <div className="page-content">
                    <MDX>{page.content || ''}</MDX>
                </div>
            );

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

        const activeKey = this.state.activeKey || defaultActiveKey;

        return (
            <div>
                <Tab.Container
                    id="nav-tabs"
                    activeKey={activeKey}
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
    }

    makeNavClickHandler(activeKey) {
        return function (e) {
            this.setState({
                activeKey,
            });
        };
    }
}

export default ClanPage;

import { Col, Nav, Navbar, Row, Tab } from 'react-bootstrap';
import Safe from 'react-safe';

import BasePage from '../components/base_page';

import css from '../styles/common.module.scss';

import markdownToHtml from '../lib/markdownToHtml';

class IndexPage extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            activeKey: null,
        };
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
            return (
                <Tab.Pane eventKey={page.slug} key={page.slug}>
                    <Safe.div>{page.html}</Safe.div>
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

export async function getServerSideProps(context) {
    let result = null;

    const defaultResult = {
        notFound: true,
    };

    const hostname = context.req.headers.host;
    const match = hostname.match(/^(?<clanName>[a-z]+)\.clan.l33t.xyz$/);

    if (match) {
        const clanName = match.groups.clanName;
        const res = await fetch(
            `https://l33t.xyz/api/clans/${clanName}/public`
        );
        const data = await res.json();

        if (!data || !data.success) {
            result = defaultResult;
        } else {
            const site = data.site;

            for (let i = 0; i < site.public_pages.length; ++i) {
                const page = site.public_pages[i];
                const html = await markdownToHtml(page.content || '');
                page.html = html;
            }
            result = {
                props: { site },
            };
        }
    } else {
        result = defaultResult;
    }

    return result;
}

export default BasePage(IndexPage);

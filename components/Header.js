import { Nav, Navbar } from 'react-bootstrap';

import Link from 'next/link';
import { useRouter } from 'next/router';

import css from '../styles/header.module.scss';

export function Header({ children, ...props }) {
    const router = useRouter();
    return null;
    return (
        <div className={css.header}>
            <Navbar
                collapseOnSelect
                fixed="top"
                bg="dark"
                variant="dark"
                expand="lg"
            >
                <Navbar.Brand>{props.site.name}</Navbar.Brand>
                <Navbar.Toggle aria-controls="responsive-navbar-nav" />
                <Navbar.Collapse id="responsive-navbar-nav">
                    <Nav className="mr-auto">{navItemsJSX}</Nav>
                </Navbar.Collapse>
            </Navbar>
        </div>
    );
}

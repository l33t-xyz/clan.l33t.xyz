import css from '../styles/footer.module.scss';

export function Footer({ children, ...props }) {
    return (
        <footer className={css.footer}>
            <span>
                &copy; {props.site.name} {new Date().getFullYear()}
            </span>
            <br />
            <span>
                Clan Website Powered by <a href="https://l33t.xyz">l33t.xyz</a>{' '}
                | <a href="https://github.com/l33t-xyz/clan.l33t.xyz">GitHub</a>
            </span>
        </footer>
    );
}

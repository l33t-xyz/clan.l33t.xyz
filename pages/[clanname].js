import BasePage from '../components/base_page';
import ClanPage from '../components/clan_page';

import { getClanPageServerSideProps } from '../utils/clan';

class LocalClanPage extends React.Component {
    render() {
        return <ClanPage page={this.props.page} />;
    }
}

export async function getServerSideProps(context) {
    const result = await getClanPageServerSideProps(context);
    return result;
}

export default BasePage(LocalClanPage);

import BasePage from '@components/BasePage';
import ClanPage from '@components/ClanPage';

import { getClanPageServerSideProps } from '@utils/clan';

const LocalClanPage = ({ page }) => {
    return <ClanPage page={page} />;
};

export async function getServerSideProps(context) {
    const result = await getClanPageServerSideProps(context);
    return result;
}

export default BasePage(LocalClanPage);

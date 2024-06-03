import BasePage from '@components/BasePage';
import ClanPage from '@components/ClanPage';

import { getClanPageServerSideProps } from '@utils/clan';

const IndexPage = ({ page }) => {
    return <ClanPage page={page} />;
};

export async function getServerSideProps(context) {
    const result = await getClanPageServerSideProps(context);
    return result;
}

export default BasePage(IndexPage);

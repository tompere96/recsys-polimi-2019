from challenge2019.SLIM.SlimElasticNet import SLIMElasticNetRecommender
from challenge2019.cf.user_cf import *
from challenge2019.cf.item_cf import *
from challenge2019.cbf.item_cbf import *
from challenge2019.SLIM.SLIM_BPR_Cython import *
from challenge2019.topPop.topPop import *
from challenge2019.cbf.user_cbf import *
from challenge2019.SLIM.SlimElasticNet import *
from challenge2019.hybrid.hybrid_item_cf_P3alpha import HybridItemCfP3alpha


class Hybrid(object):

    def __init__(self, divide_recommendations=False):
        self.URM = None
        self.SM_item = None
        self.recommenderUser = UserCollaborativeFiltering()
        # self.recommenderItem = ItemCollaborativeFiltering()
        self.recommenderHybridItem = HybridItemCfP3alpha()
        self.recommender_SLIM_BPR = SLIM_BPR_Cython()
        self.recommenderItemCBF = ItemContentBasedFiltering()
        self.recommenderUserCBF = UserContentBasedFiltering()
        self.recommenderTopPop = TopPop()
        self.recommender_SLIM_E = SLIMElasticNetRecommender()
        self.divide_recommendations = divide_recommendations
        self.fitted = False

    def fit(self, URM, fit_once=False, weights=None):
        if weights is None:
            weights = {
                "SLIM": 0.11,
                "item_cf": 0.15,
                "user_cf": 0.17
            }

        self.weights = weights

        if not (fit_once and self.fitted):
            self.URM = URM
            if self.divide_recommendations:
                True

            self.recommenderUser.fit(URM, knn=784, shrink=10)
            # self.recommenderItem.fit(URM, knn=12, shrink=23)
            self.recommenderHybridItem.fit(URM)
            self.recommender_SLIM_E.fit(URM)
            # self.recommender_SLIM_BPR.fit(URM)
            # self.recommenderItemCBF.fit(URM, knn_asset=100, knn_price=100, knn_sub_class=300, shrink=10)
            # self.recommenderUserCBF.fit(URM, knn_age=700, knn_region=700, shrink=20)
            self.recommenderTopPop.fit(URM)
            self.fitted = True

    def recommend(self, user_id, at=10):

        normalized_ratings = True
        # todo add weight and

        self.URM.eliminate_zeros()
        liked_items = self.URM[user_id]

        if len(liked_items.data) == 0:
            # add top pop? or even substitute
            expected_ratings = self.recommenderTopPop.get_expected_ratings(user_id)

        elif len(liked_items.data) < 30:
            expected_ratings = 0.11 * self.recommenderUser.get_expected_ratings(user_id,
                                                                                                   normalized_ratings=normalized_ratings) \
                               + 0.15 * self.recommenderHybridItem.get_expected_ratings(user_id,
                                                                                                           normalized_ratings=normalized_ratings) \
                               + 0.17 * self.recommender_SLIM_E.get_expected_ratings(user_id,
                                                                                                       normalized_ratings=normalized_ratings)
        else:
            expected_ratings = self.weights["user_cf"] * self.recommenderUser.get_expected_ratings(user_id,
                                                                                                        normalized_ratings=normalized_ratings) \
                               + self.weights["item_cf"] * self.recommenderHybridItem.get_expected_ratings(user_id,
                                                                                                          normalized_ratings=normalized_ratings) \
                               + self.weights["SLIM_E"] * self.recommender_SLIM_E.get_expected_ratings(user_id,
                                                                                                       normalized_ratings=normalized_ratings)
        recommended_items = np.flip(np.argsort(expected_ratings), 0)

        unseen_items_mask = np.in1d(recommended_items, self.URM[user_id].indices,
                                    assume_unique=True, invert=True)
        recommended_items = recommended_items[unseen_items_mask]
        return recommended_items[0:at]


if __name__ == '__main__':
    recommender = Hybrid(divide_recommendations=False)
    Runner.run(recommender, True, find_weights_hybrid=True, evaluate_different_type_of_users=True,
               batch_evaluation=False)

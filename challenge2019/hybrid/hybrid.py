from GraphBased.RP3beta import RP3betaRecommender
from challenge2019.MF.ALS import AlternatingLeastSquare
from challenge2019.MF.pureSVD import PureSVDRecommender
from challenge2019.SLIM.SlimElasticNet import SLIMElasticNetRecommender
from challenge2019.cf.user_cf import *
from challenge2019.cf.item_cf import *
from challenge2019.cbf.item_cbf import *
from challenge2019.SLIM.SLIM_BPR_Cython import *
from challenge2019.topPop.topPop import *
from challenge2019.cbf.user_cbf import *
from challenge2019.SLIM.SlimElasticNet import *
from challenge2019.featureWeighting.feature_weighting_on_item import *
from challenge2019.hybrid.hybrid_item_cf_P3alpha import HybridItemCfP3alpha
from challenge2019.hybrid.hybrid_item_cf_RP3beta import HybridItemCfRP3Beta
from challenge2019.topPop.topPop_userClasses import TopPopUserClasses


class Hybrid(object):

    def __init__(self, divide_recommendations=False):
        self.URM = None
        self.SM_item = None
        self.recommenderUser = UserCollaborativeFiltering()
        # self.recommenderItem = ItemCollaborativeFiltering()
        self.RP3Beta = RP3betaRecommender()
        self.recommenderHybridItem = HybridItemCfRP3Beta()
        # self.recommender_SLIM_BPR = SLIM_BPR_Cython()
        self.recommenderItemCBF = ItemContentBasedFiltering()
        self.recommenderUserCBF = UserContentBasedFiltering()
        self.recommenderTopPop = TopPop()
        # self.recommender_pureSVD = PureSVDRecommender()
        self.recommender_SLIM_E = SLIMElasticNetRecommender()
        self.recommender_ALS = AlternatingLeastSquare()
        self.divide_recommendations = divide_recommendations
        self.fitted = False
        self.weights = None

    def fit(self, URM, fit_once=False, weights=None):
        if weights is None:
            weights = {
                "MF": 0.02294,
                "SLIM_E": 0.9962,
                "item_cbf": 0.9306,
                "item_cf": 0.9985,
                "user_cf": 0.005833
            }  # 0.052? best online2
            weights_3484 = {
                "MF": 0.009341,
                "SLIM_E": 0.4219,
                "item_cbf": 1,
                "item_cf": 1,
                "user_cf": 0.006311
            }  # 0.05321 seed 1234, values found witandom seed
            weights_simple = {
                "item_cbf": 0.9759,
                "item_cf": 0.9924,
                "user_cf": 0.006102
            }  # 0.0527  seed 1234

        self.weights = weights

        if not (fit_once and self.fitted):
            self.URM = URM
            if self.divide_recommendations:
                True

            self.recommenderUser.fit(URM, knn=784, shrink=10)
            # self.RP3Beta.fit(URM, alpha=0.203, beta=.1879, topK=108)
            # self.recommenderItem.fit(URM, knn=12, shrink=23)
            self.recommenderHybridItem.fit(URM)
            self.recommender_SLIM_E.fit(URM)
            self.recommender_ALS.fit(URM)
            # self.recommender_pureSVD.fit(URM)

            # self.recommender_SLIM_BPR.fit(URM)
            self.recommenderItemCBF.fit(URM)
            self.recommenderUserCBF.fit(URM)
            self.recommenderTopPop.fit(URM)
            self.fitted = True

    def recommend(self, user_id, at=10):

        normalized_ratings = False

        self.URM.eliminate_zeros()
        liked_items = self.URM[user_id]

        if len(liked_items.data) == 0:
            recommended_items = []
            expected_items_top_pop = self.recommenderTopPop.recommend(user_id, at=20)
            expected_items_user_cbf = self.recommenderUserCBF.recommend(user_id, at=20)
            intersection = np.intersect1d(expected_items_user_cbf, expected_items_top_pop)
            if len(intersection) == 0:
                recommended_items = np.concatenate((expected_items_top_pop[:5], expected_items_top_pop[:5]))
            else:
                expected_items_top_pop = np.setdiff1d(expected_items_top_pop, intersection)
                expected_items_user_cbf = np.setdiff1d(expected_items_user_cbf, intersection)
                recommended_items = np.concatenate(
                    (intersection, expected_items_top_pop[:5], expected_items_user_cbf[:5]))


        # elif len(liked_items.data) > 50:
        #   expected_ratings = self.RP3Beta.get_expected_ratings(user_id, normalized_ratings=normalized_ratings)
        else:
            expected_ratings = self.weights["user_cf"] * self.recommenderUser.get_expected_ratings(user_id,
                                                                                                   normalized_ratings=normalized_ratings) \
                               + self.weights["item_cf"] * self.recommenderHybridItem.get_expected_ratings(user_id,
                                                                                                           normalized_ratings=normalized_ratings) \
                               + self.weights["SLIM_E"] * self.recommender_SLIM_E.get_expected_ratings(user_id,
                                                                                                       normalized_ratings=normalized_ratings) \
                               + self.weights["MF"] * self.recommender_ALS.get_expected_ratings(user_id) \
                               + self.weights["item_cbf"] * self.recommenderItemCBF.get_expected_ratings(user_id)

            recommended_items = np.flip(np.argsort(expected_ratings), 0)

            unseen_items_mask = np.in1d(recommended_items, self.URM[user_id].indices,
                                        assume_unique=True, invert=True)
            recommended_items = recommended_items[unseen_items_mask]
        return recommended_items[0:at]


if __name__ == '__main__':
    recommender = Hybrid(divide_recommendations=False)
    Runner.run(recommender, True, find_weights_hybrid=False, evaluate_different_type_of_users=True,
               batch_evaluation=True)

    # best score on seed 69: MAP@10 : 0.03042666580147029
    # 0.03298346361837503
    # 0.03291286461327143

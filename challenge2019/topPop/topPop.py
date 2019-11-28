import numpy as np
import scipy.sparse as sps

from challenge2019.Base.Similarity.Compute_Similarity_Python import Compute_Similarity_Python
from challenge2019.utils.run import Runner
from challenge2019.utils.utils import Utils

class TopPop():
    def __init__(self):
        self.URM = None

    def fit(self, URM, knn=100, shrink=5, similarity="cosine"):
        self.URM = URM
        self.occurrencies = np.array(np.zeros(self.URM.shape[1]))
        for i in range(0, self.URM.shape[1]):
            self.occurrencies[i] = len(self.URM[:, i].data)

    def get_expected_ratings(self, user_id):
        data = np.arange(0.0, 1.0, 0.1)
        data = np.flip(data, 0)

        recommended_items = self.recommend(user_id)
        #expected_ratings = np.array(data)[recommended_items.astype(int)]
        expected_ratings = sps.coo_matrix(data, (recommended_items, np.zeros(10)), shape=(self.URM.shape[1]))
        expected_ratings = np.squeeze(np.asarray(expected_ratings))
        print(expected_ratings)
        return expected_ratings

    def recommend(self, user_id, at=10):
        expected_ratings = self.occurrencies
        recommended_items = np.flip(np.argsort(expected_ratings), 0)

        unseen_items_mask = np.in1d(recommended_items, self.URM[user_id].indices,
                                    assume_unique=True, invert=True)
        recommended_items = recommended_items[unseen_items_mask]
        return recommended_items[0:at]

recommender = TopPop()
Runner.run(recommender, True)
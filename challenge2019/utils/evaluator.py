import multiprocessing
from functools import partial
from random import randint

import numpy as np
from tqdm import tqdm
import scipy.sparse as sps

from .utils import Utils
from challenge2019.Base.Evaluation.Evaluator import EvaluatorProf

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    colors = [HEADER, OKBLUE, OKGREEN, WARNING, FAIL, BOLD, UNDERLINE]

    @staticmethod
    def color(msg, color):
        assert 0 < color < len(bcolors.colors)
        return bcolors.colors[color] + msg + bcolors.ENDC

class Evaluator(object):

    def __init__(self):

        self.URM_train = None
        self.URM_test = None
        self.test_dictionary = {}
        self.train_test_split = 0.7
        self.recommender = None

    def train_test_holdout(self, URM_all, seed, train_perc=0.8):

        print(bcolors.color("Splitting using 2080 \n Splitting...", 1))
        numInteractions = URM_all.nnz
        URM_all = URM_all.tocoo()
        shape = URM_all.shape
        if seed is not None:
            np.random.seed(seed)
        train_mask = np.random.choice([True, False], numInteractions, p=[train_perc, 1 - train_perc])

        URM_train = sps.coo_matrix((URM_all.data[train_mask], (URM_all.row[train_mask], URM_all.col[train_mask])),
                                   shape=shape)
        URM_train = URM_train.tocsr()

        test_mask = np.logical_not(train_mask)

        URM_test = sps.coo_matrix((URM_all.data[test_mask], (URM_all.row[test_mask], URM_all.col[test_mask])),
                                  shape=shape)
        URM_test = URM_test.tocsr()

        user_indexes = np.arange(URM_all.shape[0])

        self.URM_train = URM_train
        self.URM_test = URM_test
        return URM_test, URM_train

    # Split random, 20% of each user
    def random_split(self, URM, seed):
        user_indexes = np.arange(URM.shape[0])
        tmp = 0
        print("Splitting using random 20% on long users\n---------------------")
        for user_index in tqdm(user_indexes, desc="Splitting dataset: "):
            # FOREACH USER
            item_left = len(URM[user_index].data)

            if item_left > 4:
                # If has more than 3 interactions

                # Array with the indexes of the non zero values
                non_zero = URM[user_index].indices
                # Shuffle array of indices
                if seed is not None:
                    np.random.seed(seed)
                np.random.shuffle(non_zero)
                # Select 20% of the array
                non_zero = non_zero[:min(int(len(non_zero) * .2), 9)]
                # Change values
                URM[user_index, non_zero] = 0
                URM.eliminate_zeros()
                self.test_dictionary[user_index] = non_zero
                tmp += len(self.test_dictionary[user_index])

            else:
                self.test_dictionary[user_index] = []

        self.URM_train = URM

        print('Number of element in test : {} \nNumber of elements in training : {}'.format(tmp,
                                                                                            len(URM.data)))
        return self.URM_test, self.URM_train

    # TODO matteo scrivi come funziona
    def random_split_to_all_users(self, URM, seed):
        user_indexes = np.arange(URM.shape[0])
        tmp = 0
        print("Splitting, 20% of all users\n---------------------")
        for user_index in tqdm(user_indexes, desc="Splitting dataset: "):
            # FOREACH USER
            item_left = len(URM[user_index].data)

            if item_left > 4:
                # If has more than 3 interactions

                # Array with the indexes of the non zero values
                non_zero = URM[user_index].indices
                # Shuffle array of indices
                if seed is not None:
                    np.random.seed(seed)
                np.random.shuffle(non_zero)
                # Select 20% of the array
                non_zero = non_zero[:min(int(len(non_zero) * .2), 9)]
                # Change values
                URM[user_index, non_zero] = 0
                URM.eliminate_zeros()
                self.test_dictionary[user_index] = non_zero
                tmp += len(self.test_dictionary[user_index])

            elif item_left > 1:
                non_zero = URM[user_index].indices
                if seed is not None:
                    np.random.seed(seed)
                np.random.shuffle(non_zero)
                non_zero = non_zero[0]
                URM[user_index, non_zero] = 0
                URM.eliminate_zeros()
                self.test_dictionary[user_index] = [non_zero]
                tmp += 1
            elif item_left == 1:
                x = np.random.randint(2, size=1)
                if x == 1:
                    non_zero = URM[user_index].indices
                    if seed is not None:
                        np.random.seed(seed)
                    np.random.shuffle(non_zero)
                    non_zero = non_zero[0]
                    URM[user_index, non_zero] = 0
                    URM.eliminate_zeros()
                    self.test_dictionary[user_index] = [non_zero]
                    tmp += 1
                else:
                    self.test_dictionary[user_index] = []
            else:
                self.test_dictionary[user_index] = []

        self.URM_train = URM
        print('Number of element in test : {} \nNumber of elements in training : {}'.format(tmp,
                                                                                            len(URM.data)))
        return self.URM_test, self.URM_train

    def leave_one_out(self, URM, seed):
        user_indexes = np.arange(URM.shape[0])
        tmp = 0
        print("Splitting using leave one out\n---------------------")
        for user_index in tqdm(user_indexes, desc="Splitting dataset: "):
            # FOREACH USER
            item_left = len(URM[user_index].data)
            if item_left > 1:
                # If has more than 1 interactions

                # Array with the indexes of the non zero values
                non_zero = URM[user_index].indices
                # Shuffle array of indices
                np.random.seed(seed)
                np.random.shuffle(non_zero)
                # Select 1 element of the array
                non_zero = non_zero[:1]
                # Change values
                URM[user_index, non_zero] = 0
                URM.eliminate_zeros()
                self.test_dictionary[user_index] = non_zero
                tmp += len(self.test_dictionary[user_index])

            else:
                self.test_dictionary[user_index] = []

        self.URM_train = URM
        print('Number of element in test : {} \nNumber of elements in training : {}'.format(tmp,
                                                                                            len(URM.data)))
        return self.URM_test, self.URM_train

    def MAP(self, relevant_items, is_relevant):
        # Cumulative sum: precision at 1, at 2, at 3 ...
        p_at_k = is_relevant * np.cumsum(is_relevant, dtype=np.float32) / (1 + np.arange(is_relevant.shape[0]))
        # print(recommended_items, relevant_items)
        map_score = np.sum(p_at_k) / np.min([relevant_items.shape[0], is_relevant.shape[0]])
        # if map_score == 0: print(recommended_items,relevant_items)
        return map_score

    def recall(self, relevant_items, is_relevant):

        recall_score = np.sum(is_relevant, dtype=np.float32) / relevant_items.shape[0]

        return recall_score

    def precision(self, relevant_items, is_relevant):

        precision_score = np.sum(is_relevant, dtype=np.float32) / len(is_relevant)

        return precision_score

    def evaluate_recommender(self, recommender, fit=False):
        MAP_final = 0
        precision_final = 0
        recall_final = 0
        n_eval = 0

        print("Start recommending...")

        utils = Utils()
        URM = utils.get_urm_from_csv()
        user_indexes = np.arange(URM.shape[0])

        if fit:
            recommender.fit(self.URM_train)

        for user_id in tqdm(user_indexes, desc='Computing Recommendations: '):
            recommended_items = recommender.recommend(user_id)
            start_pos = self.URM_test.indptr[user_id]
            end_pos = self.URM_test.indptr[user_id + 1]
            if end_pos - start_pos > 0:
                relevant_items = self.URM_test.indices[start_pos:end_pos]
                is_relevant = np.in1d(recommended_items, relevant_items, assume_unique=True)

                MAP_final += self.MAP(relevant_items, is_relevant)
                precision_final += self.precision(relevant_items, is_relevant)
                recall_final += self.recall(relevant_items, is_relevant)

                n_eval += 1

        MAP_final /= n_eval
        precision_final /= n_eval
        recall_final /= n_eval
        print(bcolors.color('Recall : {} \nPrecision : {}'.format(recall_final, precision_final), 2))
        return MAP_final

    def fit_and_evaluate_recommender(self, recommender):
        return self.evaluate_recommender(recommender, fit=True)

    def fit_and_evaluate_recommender_on_different_age_of_user(self, recommender):
        MAP_age = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        user_age = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        MAP_final = 0
        n_eval = 0
        utils = Utils()
        URM = utils.get_urm_from_csv()
        age_matrix = utils.get_ucm_age_from_csv()
        user_indexes = np.arange(URM.shape[0])
        recommender.fit(self.URM_train)

        for user_id in user_indexes:
            item_left = len(self.URM_train[user_id].data)
            if item_left == 0:
                app = 0
                recommended_items = recommender.recommend(user_id)
                start_pos = self.URM_test.indptr[user_id]
                end_pos = self.URM_test.indptr[user_id + 1]
                if end_pos - start_pos > 0:
                    relevant_items = self.URM_test.indices[start_pos:end_pos]
                    is_relevant = np.in1d(recommended_items, relevant_items, assume_unique=True)
                    app = self.MAP(relevant_items, is_relevant)

                    if len(age_matrix[user_id].data) > 0:
                        age = age_matrix[user_id]
                        age = int(age.data)
                        MAP_age[age] += app
                        user_age[age] += 1
                    MAP_final += app
                    n_eval += 1

        for i in range(1, 11, 1):
            print("age: {}".format(str(i)))
            print("Number of cold users with this age: {}".format(user_age[i]))
            if user_age[i] > 0:
                print("MAP@10 for these users: {}".format(str(MAP_age[i] / user_age[i])))
            else:
                print("0")

        MAP_final /= n_eval
        return MAP_final

    # TODO: non va mica - only works with one regio
    def fit_and_evaluate_recommender_on_different_region_of_user(self, recommender):
        MAP_region = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        user_region = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        MAP_final = 0
        n_eval = 0
        utils = Utils()
        URM = utils.get_urm_from_csv()
        user_indexes = np.arange(URM.shape[0])
        region_matrix = utils.get_ucm_region_from_csv()
        recommender.fit(self.URM_train)

        for user_id in user_indexes:
            item_left = len(self.URM_train[user_id].data)
            if item_left == 0:
                app = 0
                recommended_items = recommender.recommend(user_id)
                start_pos = self.URM_test.indptr[user_id]
                end_pos = self.URM_test.indptr[user_id + 1]
                if end_pos - start_pos > 0:
                    relevant_items = self.URM_test.indices[start_pos:end_pos]
                    is_relevant = np.in1d(recommended_items, relevant_items, assume_unique=True)
                    app = self.MAP(relevant_items, is_relevant)

                    if len(region_matrix[user_id].data) > 0:
                        region = region_matrix[user_id]
                        region = int(region.data)
                        MAP_region[region] += app
                        user_region[region] += 1
                    MAP_final += app
                    n_eval += 1

        for i in range(0, 8, 1):
            print("region: {}".format(str(i)))
            print("Number of cold users with this age: {}".format(user_region[i]))
            if user_region[i] > 0:
                print("MAP@10 for these users: {}".format(str(MAP_region[i] / user_region[i])))
            else:
                print("0")
        MAP_final /= n_eval
        return MAP_final

    def evaluate_recommender_on_different_length_of_user(self, recommender, fit=True):
        # used to evaluate an already trained model
        MAP_lenght = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        user_lenght = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        MAP_final = 0
        n_eval = 0

        utils = Utils()
        URM = utils.get_urm_from_csv()
        user_indexes = np.arange(URM.shape[0])

        if fit:
            recommender.fit(self.URM_train)
        for user_id in tqdm(user_indexes, desc='Computing Recommendations: '):
            start_pos = self.URM_test.indptr[user_id]
            end_pos = self.URM_test.indptr[user_id + 1]
            recommended_items = recommender.recommend(user_id)
            if end_pos - start_pos > 0:
                item_left = len(self.URM_train[user_id].data)
                relevant_items = self.URM_test.indices[start_pos:end_pos]
                is_relevant = np.in1d(recommended_items, relevant_items, assume_unique=True)
                app = self.MAP(relevant_items, is_relevant)

                if item_left == 0:
                    MAP_lenght[0] += app
                    user_lenght[0] += 1
                elif item_left < 4:
                    MAP_lenght[1] += app
                    user_lenght[1] += 1
                elif item_left < 8:
                    MAP_lenght[2] += app
                    user_lenght[2] += 1
                elif item_left < 12:
                    MAP_lenght[3] += app
                    user_lenght[3] += 1
                elif item_left < 16:
                    MAP_lenght[4] += app
                    user_lenght[4] += 1
                elif item_left < 20:
                    MAP_lenght[5] += app
                    user_lenght[5] += 1
                elif item_left < 24:
                    MAP_lenght[6] += app
                    user_lenght[6] += 1
                elif item_left < 28:
                    MAP_lenght[7] += app
                    user_lenght[7] += 1
                elif item_left < 32:
                    MAP_lenght[8] += app
                    user_lenght[8] += 1
                elif item_left < 36:
                    MAP_lenght[9] += app
                    user_lenght[9] += 1
                else:
                    MAP_lenght[10] += app
                    user_lenght[10] += 1

                MAP_final += app
                n_eval += 1

        for i in range(11):
            if user_lenght[i] > 0:
                print("MAP@10 for users with < {} interactions: {}".format(i*4, str(MAP_lenght[i] / user_lenght[i])))
                MAP_lenght[i] = MAP_lenght[i] / user_lenght[i]
            else:
                print("Empty category")

        MAP_final /= n_eval
        return MAP_final, MAP_lenght


    #
    #
    # Bayesian optimization methods
    #
    #

    def optimize_hyperparameters_bo_cf(self, knn, shrink):
        recommender = self.recommender
        recommender.fit(self.URM_train, shrink=int(shrink), knn=int(knn))
        MAP = self.evaluate_recommender(recommender)
        return MAP

    def optimize_hyperparameters_bo_item_cbf(self, knn_asset, knn_price, knn_sub_class, shrink):
        recommender = self.recommender
        recommender.fit(self.URM_train, shrink=int(shrink), knn_asset=int(knn_asset), knn_price=int(knn_price),
                        knn_sub_class=int(knn_sub_class))
        MAP = self.evaluate_recommender(recommender)
        return MAP

    def optimize_weights_item_cbf(self, price, asset, sub_class):
        recommender = self.recommender
        weights = {
            "price": price,
            "asset": asset,
            "sub_class": sub_class
        }
        recommender.fit(self.URM_train, weights=weights)
        MAP = self.evaluate_recommender(recommender)
        return MAP

    def optimize_hyperparameters_bo_user_cbf(self, knn, shrink):
        recommender = self.recommender
        recommender.fit(self.URM_train, shrink=int(shrink), knn=int(knn))
        MAP = self.evaluate_recommender(recommender)
        return MAP

    def optimize_hyperparameters_bo_P3alpha(self, topk, alpha):
        recommender = self.recommender
        recommender.fit(self.URM_train, topK=int(topk), alpha=alpha)
        MAP = self.evaluate_recommender(recommender)
        return MAP

    def optimize_hyperparameters_bo_RP3beta(self, topk, alpha, beta):
        recommender = self.recommender
        recommender.fit(self.URM_train, topK=int(topk), alpha=alpha, beta=beta)
        MAP = self.evaluate_recommender(recommender)
        return MAP

    def optimize_hyperparameters_bo_pure_svd(self, num_factors):
        recommender = self.recommender
        recommender.fit(self.URM_train, num_factors=int(num_factors))
        MAP = self.evaluate_recommender(recommender)
        return MAP

    def optimize_hyperparameters_bo_ALS(self, n_factors, regularization, iterations, alpha):
        recommender = self.recommender
        recommender.fit(self.URM_train, n_factors=int(n_factors), regularization=regularization,
                        iterations=int(iterations), alpha=alpha)
        MAP = self.evaluate_recommender(recommender)
        return MAP

    def optimize_hyperparameters_bo_fw(self, loss_tolerance, iteration_limit, damp_coeff, topK, add_zeros_quota):
        recommender = self.recommender
        recommender.fit(self.URM_train, loss_tolerance=loss_tolerance, iteration_limit=int(iteration_limit),
                        damp_coeff=damp_coeff, topK=int(topK), add_zeros_quota=add_zeros_quota)
        MAP = self.evaluate_recommender(recommender)
        return MAP

    def optimize_hyperparameters_bo_SLIM_el(self, max_iter, topK, alpha, l1_ratio, tol):
        recommender = self.recommender
        recommender.fit(self.URM_train, max_iter=int(max_iter), topK=int(topK), alpha=alpha, l1_ratio=l1_ratio, tol=tol)
        MAP = self.evaluate_recommender(recommender)
        return MAP

    def optimize_hyperparameters_bo_SLIM_bpr(self, lj_reg, topK, learning_rate, li_reg):

        recommender = self.recommender
        recommender.fit(self.URM_train, topK=int(topK), learning_rate=learning_rate, li_reg=li_reg
                        , lj_reg=lj_reg)
        MAP = self.evaluate_recommender(recommender)
        return MAP

    def optimize_weights_hybrid_cold_users(self, at, threshold):
        recommender = self.recommender
        recommender.fit(self.URM_train, fit_once=True, at=at, threshold=threshold)
        MAP = self.evaluate_recommender(recommender)
        return MAP

    def optimize_weights_hybrid(self, item_cf, user_cf, SLIM_E, MF, item_cbf):
        recommender = self.recommender
        weights = {
            "SLIM_E": SLIM_E,
            "item_cf": item_cf,
            "user_cf": user_cf,
            "MF": MF,
            "item_cbf": item_cbf
            # "user_cbf": user_cbf,
        }
        recommender.fit(self.URM_train, fit_once=True, weights=weights)
        MAP = self.evaluate_recommender(recommender)
        return MAP

    def optimize_weights_new_hybrid(self, item_cf, user_cf, SLIM_E, MF, item_cbf, RP3beta):
        recommender = self.recommender
        weights = {
            "SLIM_E": SLIM_E,
            "item_cf": item_cf,
            "user_cf": user_cf,
            "MF": MF,
            "item_cbf": item_cbf,
            "RP3beta": RP3beta
        }
        recommender.fit(self.URM_train, fit_once=True, weights=weights)
        MAP = self.evaluate_recommender(recommender)
        return MAP

    def optimize_weights_hybrid_20(self, item, user_cf, MF):
        recommender = self.recommender
        weights = {
            "user_cf": user_cf,
            "MF": MF,
            "item": item
        }
        recommender.fit(self.URM_train, fit_once=True, weights=weights)
        MAP = self.evaluate_recommender(recommender)
        return MAP

    def optimize_weights_hybrid_all_item(self, cf, SLIM_E, RP3, cbf):
        recommender = self.recommender
        weights = {
            "SLIM_E": SLIM_E,
            "RP3": RP3,
            "cf": cf,
            "cbf": cbf
        }
        recommender.fit(self.URM_train, fit_once=True, weights=weights)
        MAP = self.evaluate_recommender(recommender)
        return MAP

    def optimize_weights_hybrid_item(self, alpha):
        recommender = self.recommender
        recommender.fit(self.URM_train, alpha=alpha, fit_once=True)
        MAP = self.evaluate_recommender(recommender)
        return MAP

    def optimize_long_item_cf(self, knn, shrink):
        recommender = self.recommender
        recommender.fit(self.URM_train, shrink=int(shrink), knn=int(knn))
        MAP = self.evaluate_recommender(recommender)
        return MAP

    #
    #
    # Runner for the bayesian optimization algorithm
    #
    #
    #

    def optimize_bo(self, tuning_params, func):
        from bayes_opt import BayesianOptimization

        optimizer = BayesianOptimization(
            f=func,
            pbounds=tuning_params,
            verbose=5,
            random_state=randint(0, 100),
        )

        optimizer.maximize(
            init_points=5,
            n_iter=100,
            acq="ei", xi=1e-4
        )
        print(optimizer.max)

    def set_recommender_to_tune(self, recommender):
        self.recommender = recommender


#
#
# Early stopping class (NOT USED)
#
#

class EvaluatorEarlyStopping(EvaluatorProf):

    def __init__(self, URM_test_list=None, cutoff_list=None):
        super().__init__(URM_test_list, cutoff_list)
        self.evaluator = Evaluator()
        self.evaluator.random_split(URM_test_list, None)

    def evaluateRecommender(self, recommender_object, validation_metric):
        MAP = self.evaluator.evaluate_recommender(recommender_object)
        print('MAP:')
        print(MAP)
        return MAP

# todo modify evaluator so that it calculates the three different MAP for the three different part of the hybrid

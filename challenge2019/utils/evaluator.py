from random import randint

import numpy as np
import pandas as pd
import scipy
import random

from scipy.sparse import csr_matrix, lil_matrix
from tqdm import tqdm

from .utils import Utils
from challenge2019.Base.Evaluation.Evaluator import EvaluatorProf


class Evaluator():

    def __init__(self):
        self.URM_train = None
        self.URM_test = None
        self.test_dictionary = {}
        self.train_test_split = 0.7
        self.recommender = None

    # Split random, 20% of each user
    def random_split(self, URM, URM_csv):
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
    # Split random, 20% of each user
    def random_split_to_all_users(self, URM, URM_csv):
        user_indexes = np.arange(URM.shape[0])
        tmp = 0
        print("Splitting using random 20% on everything\n---------------------")
        for user_index in tqdm(user_indexes, desc="Splitting dataset: "):
            # FOREACH USER
            item_left = len(URM[user_index].data)

            if item_left > 4:
                # If has more than 3 interactions

                # Array with the indexes of the non zero values
                non_zero = URM[user_index].indices
                # Shuffle array of indices
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
    def random_split_to_short_users(self, URM, URM_csv):
        user_indexes = np.arange(URM.shape[0])
        tmp = 0
        print("Splitting using random 20% on everything\n---------------------")
        for user_index in tqdm(user_indexes, desc="Splitting dataset: "):
            # FOREACH USER
            item_left = len(URM[user_index].data)

            if 5 > item_left > 0:
                x = np.random.randint(4, size=1)
                if x == 0:
                    non_zero = URM[user_index].indices
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

    def leave_one_out(self, URM, URM_csv):
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

    def MAP(self, recommended_items, relevant_items):
        # print(recommended_items)
        is_relevant = np.isin(recommended_items , relevant_items, assume_unique=True)
        # Cumulative sum: precision at 1, at 2, at 3 ...
        p_at_k = is_relevant * np.cumsum(is_relevant, dtype=np.float32) / (1 + np.arange(len(is_relevant)))
        # print(recommended_items, relevant_items)
        map_score = np.sum(p_at_k) / np.min([len(relevant_items), len(is_relevant)])
        # if map_score == 0: print(recommended_items,relevant_items)
        return map_score

    def evaluate(self, user_id, recommended_items):
        relevant_items = self.test_dictionary[user_id]
        if (len(relevant_items) is not 0):
            map = self.MAP(recommended_items, relevant_items)
            return map
        else:
            return 0

    def fit_and_evaluate_recommender(self, recommender):
        MAP_final = 0
        utils = Utils()
        #URM_enh = utils.get_URM_tfidf(self.URM_train)
        recommender.fit(self.URM_train)
        for user_id in tqdm(Utils.get_target_user_list(), desc='Computing Recommendations: '):
            recommended_items = recommender.recommend(user_id)
            MAP_final += self.evaluate(user_id, recommended_items)

        MAP_final /= len(Utils.get_target_user_list())
        return MAP_final


    def fit_and_evaluate_recommender_on_different_type_of_user(self, recommender):
        # used to evaluate an already trained model
        MAP_final = 0
        MAP_cold = 0
        cold_users = 0
        MAP_short = 0
        short_users = 0
        MAP_long = 0
        long_users = 0
        recommender.fit(self.URM_train)
        for user_id in tqdm(Utils.get_target_user_list(), desc='Computing Recommendations: '):
            recommended_items = recommender.recommend(user_id)
            item_left = len(self.URM_train[user_id].data)
            app = self.evaluate(user_id, recommended_items)
            if item_left == 0:
                MAP_cold += app
                cold_users += 1
            elif item_left < 4:
                MAP_short += app
                short_users += 1
            elif item_left >= 4:
                MAP_long += app
                long_users += 1
            MAP_final += app


        print(cold_users)
        print(short_users)
        print(long_users)
        print(len(Utils.get_target_user_list()))
        print("MAP@10 for cold users: {}".format(MAP_cold / cold_users))
        print("MAP@10 for short users: {}".format(MAP_short / short_users))
        print("MAP@10 for long users with actual target users: {}".format(MAP_long / long_users))
        print("MAP@10 for long users with all users: {}".format(MAP_long / len(Utils.get_target_user_list())))
        MAP_final /= len(Utils.get_target_user_list())
        return MAP_final

    def find_epochs(self, recommender, k):
        for i in range(20, 100, 5):
            print(k)
            MAP_final = 0
            recommender.fit(self.URM_train, epochs=250, lambda_i=0.4, lambda_j=0.4, topk=k)
            count = 0
            for user_id in tqdm(Utils.get_target_user_list(), desc='Computing Recommendations: '):
                recommended_items = recommender.recommend(user_id)
                MAP_final += self.evaluate(user_id, recommended_items)

            MAP_final /= len(Utils.get_target_user_list())
            print('epoches' + str(i))
            print(MAP_final)
            print('\n\n')
        return MAP_final

    def find_weight_item_cbf(self, recommender):
        recommender.fit(self.URM_train)
        for i in range(1, 10, 2):
            for j in range(1, 10 - i, 2):
                k = 10 - i - j
                MAP_final = 0
                print('asset ' + str(i) + '\nprice ' + str(j) + '\nsub_class ' + str(k))
                count = 0
                for user_id in tqdm(Utils.get_target_user_list()):
                    recommended_items = recommender.recommend(user_id, i / 10, j / 10, k / 10)
                    MAP_final += self.evaluate(user_id, recommended_items)
                    count += 1
                MAP_final /= len(Utils.get_target_user_list())
                print(MAP_final)
                print('\n\n')
        return MAP_final

    def find_weights_hybrid(self, recommender):
        recommender.fit(self.URM_train)
        for i in range(1, 8, 2):
            for j in range(1, 10 - i, 2):
                for k in range(1, 10 - i - j, 2):
                    l = 10 - i - j - k
                    MAP_final = 0
                    print('asset ' + str(i) + '\nprice ' + str(j) + '\nsub_class ' + str(k))
                    count = 0
                    for user_id in tqdm(Utils.get_target_user_list()):
                        recommended_items = recommender.recommend(user_id, i / 10, j / 10, k / 10, l/10)
                        MAP_final += self.evaluate(user_id, recommended_items)
                        count += 1
                    MAP_final /= len(Utils.get_target_user_list())
                    print(MAP_final)
                    print('\n\n')
        return MAP_final


    def find_hyper_parameters_cf(self, recommender):
        for knn in range(50,301, 50):
            for shrink in range(15, 26, 5):
                print('knn ' + str(knn) + '\nshrink ' + str(shrink))
                MAP_final = 0
                recommender.fit(self.URM_train, knn=knn, shrink=shrink)
                for user_id in tqdm(Utils.get_target_user_list(), desc='Computing Recommendations: '):
                    recommended_items = recommender.recommend(user_id)
                    MAP_final += self.evaluate(user_id, recommended_items)

                MAP_final /= len(Utils.get_target_user_list())
                print(MAP_final)
                print('\n\n')
        return

    def find_hyper_parameters_user_cbf(self, recommender):
        for knn in range(1000,10001, 500):
            for shrink in [20]:
                print('knn ' + str(knn) + '\nshrink ' + str(shrink))
                MAP_final = 0
                recommender.fit(self.URM_train, knn_age=knn, knn_region=knn, shrink=shrink)
                for user_id in tqdm(Utils.get_target_user_list(), desc='Computing Recommendations: '):
                    recommended_items = recommender.recommend(user_id)
                    MAP_final += self.evaluate(user_id, recommended_items)

                MAP_final /= len(Utils.get_target_user_list())
                print(MAP_final)
                print('\n\n')
        return MAP_final

    def optimize_hyperparameters_bo_cf(self, knn, shrink):
        recommender = self.recommender
        recommender.fit(self.URM_train, shrink=int(shrink), knn=int(knn))
        MAP = self.evaluate_recommender(recommender)
        return MAP

    def optimize_hyperparameters_bo_SLIM_el(self, topK, alpha, l1_ratio, tol):
        recommender = self.recommender
        recommender.fit(self.URM_train, topK=int(topK), alpha=alpha, l1_ratio=l1_ratio
                        , tol=tol)
        MAP = self.evaluate_recommender(recommender)
        return MAP

    def optimize_bo(self, tuning_params,func):
        from bayes_opt import BayesianOptimization

        optimizer = BayesianOptimization(
            f=func,
            pbounds=tuning_params,
            verbose=5,
            random_state=5,
        )

        optimizer.maximize(
            init_points=5,
            n_iter=8,
        )

    def set_recommender_to_tune(self, recommender):
        self.recommender = recommender

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

#todo modify evaluator so that it calculates the three different MAP for the three different part of the hybrid
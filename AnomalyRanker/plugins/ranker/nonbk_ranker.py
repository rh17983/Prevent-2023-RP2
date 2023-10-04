# -*- coding: utf-8 -*-
"""The module that contains anomaly ranker that ranks the anomalies by
non-backtracking metric.
"""
from plugins.ranker.general_ranker import GeneralRanker
from scipy import linalg as LA
import numpy as np


class NonBkRanker(GeneralRanker):
    """This class ranks the anomalies by non-backtracking metric.
    """
    @classmethod
    def rank(cls, anomalies_seq):
        """Implementation of rank. See class doc for more information.

        Args:
            anomalies_seq(list): A list of sets, each set contains the
                anomalies' idices at a timestamp.

        Returns:
            A list whose elements are the anomaly list. Each anoamly list
            contains the tuples of KPI index and rankings. Example: [[${KPI
            index 1}, ${KPI ranking 1}, ${KPI index 2}, ${KPI ranking 2}, ...],
            ...]
        """
        if len(anomalies_seq) is 0:
            return [], []

        anomaly_list = sorted(list(anomalies_seq))
        sub_matrix = np.array(cls.sub_matrix(anomaly_list))
        size = len(sub_matrix)

        target_matrix = cls.__compute_target(sub_matrix)
        max_vector = cls.compute_max_eigenvector(target_matrix)[0:size]

        max_vector = [np.absolute(v) for v in max_vector]

        id_val_list = list(zip(anomaly_list, max_vector))

        sorted_list = sorted(id_val_list,
                             key=lambda x: np.absolute(x[1]),
                             reverse=True)

        rankings = []
        values = []
        for (idx, value) in sorted_list:
            if value == 0:
                break
            rankings.append(idx)
            values.append(value)

        return rankings, values

    @classmethod
    def compute_max_eigenvector(cls, matrix):
        """Compute the maximun eigenvector of a given matrix.

        Args:
            matrix(list): The matrix to be computed.

        Returns:
            A list which represents the maximun eigenvector of the matrix.
        """
        e_values, vl, e_vectors = LA.eig(matrix, left=True, right=True)

        max_value = max(e_values)
        max_vector = e_vectors[list(e_values).index(max_value)]

        return max_vector

    @classmethod
    def __compute_target(cls, matrix):
        """Transform the matrix to the non-backtracking target form.
        
        Args:
            matrix(list): The input target.

        Returns:
            The matrix in non-backtracking target form.
        """
        size = len(matrix)

        A = matrix
        I = np.identity(size)
        degrees = [max(row) for row in matrix]
        D = np.diag(degrees)
        I_sub_D = np.subtract(I, D)
        O = np.zeros((size, size))

        M1 = np.concatenate((A, I_sub_D), axis=1)
        M2 = np.concatenate((I, O), axis=1)

        M = np.concatenate((M1, M2), axis=0)

        return M

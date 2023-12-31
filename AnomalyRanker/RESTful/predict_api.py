# -*- coding: utf-8 -*-
"""The module that formats the input from the RESTful requests.
"""
import util.kpi_info as kpi_info
import util.localizer_log as localizer_log
from datetime import datetime


def format_input_single(anomalies):
    """Format the input of a single RESTful API data to the format of predictor.

    Args:
        anomalies(list): A list of integers, which are the KPI indices.

    Returns:
        A tuple which composes of:
        - A boolean indicates if the input format is correct.
        - If the format is correct, then a list of 0/1 in which 1 indicates
        that the KPI at that index is anomalous. If the format is not correct,
        then None.
    """
    size = len(kpi_info.kpi_list)

    if not isinstance(anomalies, list):
        localizer_log.warning("Anomalies are not organized as a list.")
        return False, []

    try:
        anomalies = [kpi_info.get_index((term['resource']['name'], 'default', term['metric']['name'])) for term in anomalies]
    except KeyError:
        localizer_log.warning("Some element in the list does not contain key 'resource' or 'metric'!")
        return False, []

    if not all([isinstance(i, int) and 0 <= i < size for i in anomalies]):
        localizer_log.warning("Some KPIs found in Anomalies are not presented in kpi_list.")
        return False, []
    return True, [1 if i in anomalies else 0 for i in range(size)]


def format_input_list(anomaly_list):
    """Format the input of a list of RESTful API data to the format of predictor.

    Args:
        anomaly_list(list): A list of list, each list contains the KPI indices.

    Returns:
        A tuple which composes of:
        - A boolean indicates if the input format is correct.
        - If the format is correct, then a list of list of 0/1 in which 1
        indicates that the KPI at that index is anomalous. If the format is not
        correct, then None.
    """
    if not isinstance(anomaly_list, list):
        localizer_log.warning("Anomaly set is not organized as a list.")
        return False, []

    results = []
    for anomalies in anomaly_list:
        valid, result = format_input_single(anomalies)
        if valid:
            results.append(result)
        else:
            return False, []

    return True, results


def format_input_single_for_convert(point_number, anomalies, fault_injection_point, failure_point, fault_class_name):
    """Format the input of a single RESTful API data to the format of predictor.

    Args:
        anomalies(list): A list of integers, which are the KPI indices.

    Returns:
        A tuple which composes of:
        - A boolean indicates if the input format is correct.
        - If the format is correct, then a list of 0/1 in which 1 indicates
        that the KPI at that index is anomalous. If the format is not correct,
        then None.
    """

    if not isinstance(anomalies, list):
        localizer_log.warning("Anomalies are not organized as a list.")
        return False, []

    if point_number < fault_injection_point:
        class_name = "n"
        localizer_log.warning("OK")
    elif point_number < failure_point:
        class_name = fault_class_name
        localizer_log.warning("OK")

    try:
        anomalies = [(int(term['metric']['name']) - 1) for term in anomalies]
    except KeyError:
        localizer_log.warning("Some element in the list does not contain key 'resource' or 'metric'!")
        return False, []

    size = len(kpi_info.kpi_list)
    if not all([isinstance(i, int) and 0 <= i < size for i in anomalies]):
        localizer_log.warning("Some KPIs found in Anomalies are not presented in kpi_list.")
        return False, []

    result_list = [int(anomalies[0]['timestamp'])]
    for i in range(size):
        if i in anomalies:
            value_to_add = 1
        else:
            value_to_add = 0

        result_list.append(value_to_add)

    result_list.append(class_name)

    return True, result_list


def format_input_list_for_convert(anomaly_list, fault_injection_point, failure_point, fault_class_name):
    """Format the input of a list of RESTful API data to the format of predictor.

    Args:
        anomaly_list(list): A list of list, each list contains the KPI indices.

    Returns:
        A tuple which composes of:
        - A boolean indicates if the input format is correct.
        - If the format is correct, then a list of list of 0/1 in which 1
        indicates that the KPI at that index is anomalous. If the format is not
        correct, then None.
    """

    if not isinstance(anomaly_list, list):
        localizer_log.warning("Anomaly set is not organized as a list.")
        return False, []

    results = []
    point_number = 0
    for anomalies in anomaly_list:
        point_number += 1
        if point_number >= failure_point:
            localizer_log.warning("A-A-A")
            localizer_log.warning(point_number)
            localizer_log.warning(fault_injection_point)
            localizer_log.warning(failure_point)
            break

        valid, result = format_input_single_for_convert(point_number, anomalies, fault_injection_point, failure_point, fault_class_name)
        if valid:
            results.append(result)
        else:
            return False, []

    return True, results

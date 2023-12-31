# -*- coding: utf-8 -*-
"""The module that runs as the server side of the RESTful API.

Example:
    $python3 ranker_app.py

Attributes:
    kpi_initialized(boolean): KPI list initalized or not.
    gml_initialized(boolean): GML model initalized or not.
    trained(boolean): predictor trained or not.
"""
import os
import sys
import pickle
import time
import csv

import numpy as np
from flask import Flask, request, jsonify, abort
from sklearn import svm

import RESTful.predict_api as predict_api
import util.kpi_info as kpi_info
import util.causality_graph as causality_graph
import util.localizer_log as localizer_log
import util.localizer_config as localizer_config
from util.localizer_config import config
import networkx as nx
from joblib import dump, load

import utils_clustering

THIS_DIRECTORY_PATH = os.path.dirname(os.path.abspath(__file__))

localizer_config.rest_mode = True

__predictor_name = config.get('restful', 'predictor')
__predictor = localizer_config.get_plugin('predictor', __predictor_name)

__rest_log = config.get('restful', 'log_file')
# TODO: Check if it is empty, may need further validation check
if __rest_log:
    if os.path.isfile(__rest_log):
        os.remove(__rest_log)
    localizer_log.reg_file(__rest_log)
    localizer_log.msg("Write log information to " + __rest_log)

kpi_initialized = False
gml_initialized = False
trained = False

__cache_folder = os.path.join(THIS_DIRECTORY_PATH, 'RESTful', 'caches')
localizer_config.build_if_not_exist(__cache_folder)

__kpi_cachefile = os.path.join(__cache_folder, 'kpi.cache')
__gml_cachefile = os.path.join(__cache_folder, 'gml.cache')
__pred_cachefile = os.path.join(__cache_folder, 'predictor.cache')

__nu = 0.1
__gamma = 0.1

__rest_cached = config.getboolean('restful', 'cached')
if __rest_cached:

    if os.path.exists(__kpi_cachefile):
        localizer_log.stdout("Read KPI list from cache..")
        with open(__kpi_cachefile, 'rb') as f:
            kpi_info.initialize(pickle.load(f))
            kpi_initialized = True

    print("\nKPIs List from the saved kpi_info.kpi_list:\n")
    for ii in range(len(kpi_info.kpi_list)):
        print(kpi_info.kpi_list[ii])
    print("kpi_info.kpi_list len:", len(kpi_info.kpi_list))

    if os.path.exists(__gml_cachefile):
        localizer_log.stdout("Read GML model from cache..")

        with open(__gml_cachefile, 'rb') as f:
            causality_graph.read(pickle.load(f))
            gml_initialized = True

    full_matrix_cache = causality_graph.get_weighted_matrix()
    # print("\n Full matrix cache:\n")
    # for ii in range(len(full_matrix_cache)):
    #     print(len(full_matrix_cache[ii]), full_matrix_cache[ii])
    # print("full_matrix_cache len:", len(full_matrix_cache))

    if os.path.exists(__pred_cachefile):
        localizer_log.stdout("Read Predictor model from cache: " + __pred_cachefile)
        with open(__pred_cachefile, 'rb') as f:
            __predictor = pickle.load(f)
            trained = True

app = Flask(__name__)


@app.route('/reset', methods=['POST'])
def reset():
    """
    Reset all elements, i.e. kpi_list, gml_model, predictor. See README for more information.
    Args:
        None
    Returns:
        None
    """

    localizer_log.stdout("Received reset request.")
    global trained
    global kpi_initialized
    global gml_initialized

    data = request.get_json()
    if data and \
            'reset' in data:
        if data['reset'] is True:

            trained = False
            kpi_initialized = False
            gml_initialized = False

            localizer_log.stdout("Reset app")
            return 'Succeed', 200
        else:
            localizer_log.warning("Value True not found.")
            return 'Failed', 500

    localizer_log.warning("Data format wrong.")
    return 'Failed', 500


@app.route('/update_kpi', methods=['POST'])
def update_kpi():
    """Update KPI list. See README for more information.

    Args:
        None

    Returns:
        None
    """

    localizer_log.stdout("Received update_kpi request.")
    global kpi_initialized

    data = request.get_json()

    if data and 'kpis' in data:

        kpi_content = data['kpis']

        if kpi_info.initialize(kpi_content):
            kpi_initialized = True
            localizer_log.stdout("Updated kpi list.")

            global __rest_cached
            if __rest_cached:
                global __kpi_cachefile
                with open(__kpi_cachefile, 'wb') as f:
                    pickle.dump(kpi_content, f)
                    localizer_log.msg("Cached kpi list.")
            return 'Succeed', 200
    else:
        localizer_log.warning("KPI data not received or key 'kpis' not found.")

    return 'Failed', 500


@app.route('/update_gml', methods=['POST'])
def update_gml():
    """Update GML modle. See README for more information.

    Args:
        None

    Returns:
        None
    """
    localizer_log.stdout("Received update_gml request.")
    global kpi_initialized
    global gml_initialized

    data = request.get_json()

    # check kpi model initialized
    if not kpi_initialized:
        localizer_log.warning("Cannot update gml without initializing KPI list")
        return 'KPI list not initialized', 500

    if data and 'gml' in data:
        gml_content = str(data['gml'])
        if gml_content == '' or causality_graph.read(gml_content):
            localizer_log.stdout("Updated GML model.")
            gml_initialized = True
            global __rest_cached
            if __rest_cached:
                global __gml_cachefile
                with open(__gml_cachefile, 'wb') as f:
                    pickle.dump(gml_content, f)
                    localizer_log.msg("Cached kpi list.")
            return 'Succeed', 200
    else:
        localizer_log.warning(("GML data not received "
                               "or key 'gml' not found."))
    return 'Failed', 500


@app.route('/set_fp_model_training_params')
def set_fp_model_training_params():
    global __pred_cachefile
    global __nu
    global __gamma

    __pred_cachefile = os.path.join(__cache_folder, 'predictor_' + request.args.get('model_code') + '.cache')
    __nu = request.args.get('nu')
    __gamma = request.args.get('gamma')

    return 'Succeed', 200


@app.route('/set_pred_model')
def set_pred_model():
    global __pred_cachefile
    __pred_cachefile = os.path.join(__cache_folder, 'predictor_' + request.args.get('model_code') + '.cache')

    return 'Succeed', 200


@app.route('/convert_anomalies', methods=['POST'])
def convert_anomalies():
    global kpi_initialized
    localizer_log.stdout("Received convert request.")

    try:
        anomalies_file_name = request.args.get('anomalies_file_name')
        fault_injection_point = int(request.args.get('fault_injection_point'))
        failure_point = int(request.args.get('failure_point'))
        fault_class_name = request.args.get('fault_class_name')
    except:
        e = sys.exc_info()[0]
        print(e)
        return 'Cannot get parameters', 500

    try:
        data = request.get_json()
    except:
        e = sys.exc_info()[0]
        return 'Wrong json 1', 500

    if not kpi_initialized:
        localizer_log.warning("Cannot convert without initialized KPI list")
        return 'KPI list not initialized', 500

    output_file = "../Toolset-Premise/tmp/anomalies_csv/" + anomalies_file_name + ".csv"
    valid, inputs = predict_api.format_input_list_for_convert(data, fault_injection_point, failure_point, fault_class_name)
    print("Len inputs", len(inputs))

    if len(inputs) <= 0:
        localizer_log.warning("Data should have at least one set of anomalies")
    elif valid:
        with open(output_file, 'w') as csv_output:
            writer = csv.writer(csv_output)
            headers = ["timestamp"] + [(gcd.resource + "_" + gcd.metric) for gcd in kpi_info.kpi_list] + ["class"]
            writer.writerow(headers)
            writer.writerows(inputs)

        return 'Succeed', 200
    else:
        return 'Wrong anomaly format', 500


@app.route('/train', methods=['POST'])
def train():
    """
    Train the predictor. See README for more information.

    Args:
        None

    Returns:
        None
    """

    localizer_log.stdout("Received train request.")

    global __predictor
    global kpi_initialized
    global trained

    global __pred_cachefile
    global __nu
    global __gamma

    try:
        data = request.get_json()
    except:
        e = sys.exc_info()[0]
        print(e)
        return 'Wrong json 1', 500

    if not kpi_initialized:
        localizer_log.warning("Cannot train without initialized KPI list")
        return 'KPI list not initialized', 500

    if data and 'training' in data and isinstance(data['training'], list):

        # inputs - list (anomalous KPIs list) of lists (anomalous kpi. size = number of all parameters. if for example 3rd element = 1, it means 3rd parameter in this timestamp is anomalous)
        valid, inputs = predict_api.format_input_list(data['training'])

        if len(inputs) <= 0:
            localizer_log.warning("Training data should have at least one set of anomalies")
        elif valid:

            localizer_log.stdout("Training started: nu: " + str(__nu) + ", kernel: rbf, gamma:" + str(__gamma))

            if not (__gamma == "auto") and not (__gamma == "scale"):
                gamma = float(__gamma)
            else:
                gamma = __gamma

            clf = svm.OneClassSVM(nu=float(__nu), kernel="rbf", gamma=gamma)

            clf.fit(inputs)
            localizer_log.stdout("Training completed: nu: " + str(__nu) + ", kernel: rbf, gamma:" + str(__gamma))

            trained = True

            with open(__pred_cachefile, 'wb') as fl:
                pickle.dump(clf, fl)

            return 'Succeed', 200
        else:
            return 'Wrong anomaly format', 500
    else:
        localizer_log.warning("training data not received, or key 'train' not found, or data is not a list")

    return 'Wrong json', 500


@app.route('/predict', methods=['POST'])
def predict():
    """Make a prediction. See README for more information.

    Args:
        None

    Returns:
        None
    """
    localizer_log.stdout("Received predict request.")
    global __predictor
    global trained

    global __pred_cachefile

    if os.path.exists(__pred_cachefile):
        with open(__pred_cachefile, 'rb') as fl:
            clf = pickle.load(fl)
            localizer_log.stdout("Read Predictor model from cache: " + __pred_cachefile)
            trained = True
    else:
        localizer_log.warning("Predictor model could not be found in " + __pred_cachefile)
        return 'Model not found', 501

    localizer_log.stdout(
        "Classifier loaded: nu: " + str(clf.nu) + ", kernel: " + str(clf.kernel) + ", gamma:" + str(clf.gamma))

    data = request.get_json()
    if data and 'anomalies' in data and check_data(data['anomalies']):
        parse_valid, parse_idx = convert_to_num(data['anomalies'])
        if parse_valid or parse_idx:
            valid, inputs = predict_api.format_input_single(parse_idx)
            if valid:

                # prediction = __predictor.predict([inputs])[0]
                result = clf.predict([inputs])
                prediction = [False if x == 1 else True for x in result][0]  # True or False
                print(prediction)

                ret = {'prediction': prediction}
                if not parse_valid:
                    ret['warning'] = 'Some unseen KPI appears. Ignored it.'
                return jsonify(ret)
    else:
        localizer_log.warning(("prediction data not received, "
                               "or key 'anomalies' not found"))
    return '', 500


@app.route('/localize', methods=['POST'])
def localize():
    """Make a localization. See README for more information.

    Args:
        None

    Returns:
        None
    """

    localizer_log.stdout("Received localize request.")
    global kpi_initialized
    global gml_initialized
    data = request.get_json()
    
    data_set_code =  request.args.get('data_set_code')
    minute =  request.args.get('minute')
    print("Requiest:", data_set_code, minute)
    
    # My code. Set rank selection
    rank_selection = request.args.get('rank_selection')
    config.set('oracle', 'rank_selection', rank_selection)

    ranker_name = config.get('restful', 'ranker')
    ranker = localizer_config.get_plugin('ranker', ranker_name)

    oracle_name = config.get('restful', 'oracle')
    oracle = localizer_config.get_plugin('oracle', oracle_name)

    if not kpi_initialized:
        localizer_log.warning("Cannot perform localization without initializing KPI list")
        return 'KPI list not initialized', 500

    if not gml_initialized:
        localizer_log.warning("Cannot perform localization without initializing GML model")
        return 'GML not initialized', 500

    if data and 'anomalies' in data and check_data(data['anomalies']):
        
        # NEW
        if len(data['anomalies']) == 0:
            ret = {'suspected_list': [], 'localization': []}
            return jsonify(ret)
        # NEW END

        parse_valid, kpis = convert_to_num(data['anomalies'])
        
        if not parse_valid:
            input('Some unseen KPI appears. Ignored it.')
            
        kpis_index = [term['idx'] for term in kpis]
        kpis_re_above_thrsh = [term['re_above_thrsh'] for term in kpis]
        kpis_node = [term['resource']['name'] for term in kpis]
        kpis_metric = [term['metric']['name'] for term in kpis]
        
        print("RECEIVED KPIs")
        for idx, kpi_index in enumerate(kpis_index):
            print(kpis_index[idx], kpis_node[idx], kpis_metric[idx], round(kpis_re_above_thrsh[idx], 4))

        personalization_dict = {}
        max_re_above_threshold = np.max(kpis_re_above_thrsh)

        for elem_idx, kpi_re_above_thrsh in enumerate(kpis_re_above_thrsh):
            # personalization_dict[kpis_index[elem_idx]] = round(kpi_re_above_thrsh/max_re_above_threshold, 2)
            personalization_dict[elem_idx] = kpi_re_above_thrsh/max_re_above_threshold

        rankings, values = ranker().rank(kpis_index, personalization_dict)

        print("Rankings: ", rankings, "Values: ", values)

        if config.get('restful', 'oracle') == "sum_oracle.SumOracle":
            _, rsc_sorted = oracle.check([list(zip(rankings, values))], None, 0)
            ret = {'suspected_list': rsc_sorted, 'localization': rsc_sorted[0]}

        if config.get('restful', 'oracle') == "basic_oracle.BasicOracle":
            single_check, suspected_list, strong_sus = oracle.check([list(zip(rankings, values))], None, 0)
            ret = {'suspected_list': suspected_list, 'localization': strong_sus}

        if not parse_valid:
            ret['warning'] = 'Some unseen KPI appears. Ignored it.'

        return jsonify(ret)

    else:
        localizer_log.warning("localization data not received, or key 'anomalies' not found")

    return '', 500


# NOT USED !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
@app.route('/rank', methods=['POST'])
# NOT USED !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
def rank():
    try:
        localizer_log.stdout("Received rank request.")
        data = request.get_json()

        if data and 'gml' in data:

            gml_content = str(data['gml'])
            graph = nx.parse_gml(gml_content.split('\n'))

            # Extract KPIs from the graph.
            kpi_content = []
            for label, data in graph.nodes(data=True):
                kpi_content.append({
                    'timestamp': None,
                    'resource': {
                        'name': data['resource'],
                    },
                    'metric': {
                        'name': data['metric'],
                    },
                    'value': None,
                })

            # Save KPIs list.
            kpi_info.initialize(kpi_content)

            # Save the graph.
            causality_graph.read(gml_content)

            # Ranking.
            ranker_name = config.get('restful', 'ranker')
            ranker = localizer_config.get_plugin('ranker', ranker_name)

            oracle_name = config.get('restful', 'oracle')
            oracle = localizer_config.get_plugin('oracle', oracle_name)

            parse_valid, parse_idx = convert_to_num(kpi_content)

            rankings, values = ranker().rank([term['idx'] for term in parse_idx], graph)
            print("rankings: ", rankings, "values: ", values)
            localizer_log.warning(rankings)
            localizer_log.warning(values)

            single_check, suspected_list, strong_sus = oracle.check([list(zip(rankings, values))], None, 0)
            ret = {'suspected_list': suspected_list, 'localization': strong_sus}

            if not parse_valid:
                ret['warning'] = 'Some unseen KPI appears. Ignored it.'

            return jsonify(ret)
        return 'Failed', 501
    except Exception:
        abort(502)


def check_data(anomalies):
    """Check if the provided data is correct.

    Args:
        anomalies(list): A list of anomalies (i.e. indices of KPIs).

    Returns:
        True if the data is in correct format, otherwise False.
    """

    list_bool = isinstance(anomalies, list)
    if not list_bool:
        localizer_log.warning("Anomalies are not organized as a list.")

    # Legacy code
    # try:
    #     anomalies = [int(x) for x in anomalies]
    # except ValueError:
    #     localizer_log.warning(("Elements in the list cannot"
    #                            " be converted into integer!"))
    #     return False
    # indices_bool = all([isinstance(x, int) and
    #                     (x >= 0 and x < len(kpi_info.kpi_list))
    #                     for x in anomalies])
    # if not indices_bool:
    #     localizer_log.warning("GCD number in Anomalies is wrong.")
    # return list_bool and indices_bool
    return list_bool


def convert_to_num(anomalies):
    result = []
    ret = True
    try:
        for term in anomalies:
            kpi = kpi_info.get_kpi_by_tag((term['resource']['name'], 'default', term['metric']['name']))
            if kpi:
                result.append({'resource': {'name': kpi.resource},
                                'metric': {'name': kpi.metric},
                                'idx': kpi.idx,
                                're_above_thrsh': float(term['value'])
                              })
            else:
                ret = False
    except KeyError:
        localizer_log.warning("Anomalies are not organized as a list.")
        return False, None

    return ret, result


if __name__ == '__main__':
    # port = config.getint('restful', 'service_port')
    port = sys.argv[1]
    app.run(host='0.0.0.0', port=port, debug=False)

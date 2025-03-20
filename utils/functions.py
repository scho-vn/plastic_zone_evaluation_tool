import pandas as pd
import csv
from collections import namedtuple
import os
import numpy as np
import pickle
import json


def data_input_from_csv_fe(csv_filepath: str = None):
    """
    Convert data input from csv to dictionary with filenames and crack tip positions.

    Parameters
    ----------
    csv_filepath : str
            self-explaining

    Returns
    ----------
    data_input_dict_corr : dict [filename]: tuple (float, float)
            dict containing the filename and the respective crack tip position corrected according to rethore

    data_input_dict_uncorr : dict [filename]: tuple (float, float)
    dict containing the filename and the respective crack tip position by line intercept method


    """

    csv_file = pd.read_csv(csv_filepath)

    csv_file = csv_file.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
    csv_file.rename(columns=lambda x: x.strip(), inplace=True)

    # convert to dict and return
    csv_input_dict_corr = {}
    for index, row in csv_file.iterrows():
        csv_input_dict_corr.update({row[0]: (row[1], row[2])})

    return csv_input_dict_corr


def data_input_from_csv_mt(csv_filepath: str = None):
    """
    Convert data input from csv to dictionary with filenames and crack tip positions.

    Parameters
    ----------
    csv_filepath : str
            self-explaining

    Returns
    ----------
    data_input_dict_corr : dict [filename]: tuple (float, float,)
            dict containing the filename and the respective crack tip position corrected according to rethore

    data_input_dict_uncorr : dict [filename]: tuple (float, float,)
    dict containing the filename and the respective crack tip position by line intercept method


    """

    csv_file = pd.read_csv(csv_filepath)

    csv_file = csv_file.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
    csv_file.rename(columns=lambda x: x.strip(), inplace=True)

    # convert to dict and return
    csv_input_dict_corr = {}
    csv_input_dict_uncorr = {}
    for index, row in csv_file.iterrows():
        csv_input_dict_corr.update({row[1]: (row[2] + row[4], row[3] + row[5], row[6])})
        csv_input_dict_uncorr.update({f"{row[6]}-{row[1]}": (row[2], row[3])})

    # return {'Uncorrected': csv_input_dict_corr, 'Corrected': csv_input_dict_uncorr}
    return csv_input_dict_uncorr


def data_input_from_csv(csv_filepath: str = None):
    """
    Convert data input from csv to dictionary with filenames and crack tip positions.

    Parameters
    ----------
    csv_filepath : str
            self-explaining

    Returns
    ----------
    data_input_dict_corr : dict [filename]: tuple (float, float)
            dict containing the filename and the respective crack tip position corrected according to rethore

    data_input_dict_uncorr : dict [filename]: tuple (float, float)
    dict containing the filename and the respective crack tip position by line intercept method


    """

    csv_file = pd.read_csv(csv_filepath)

    csv_file = csv_file.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
    csv_file.rename(columns=lambda x: x.strip(), inplace=True)

    # convert to dict and return
    csv_input_dict_corr = {}
    csv_input_dict_uncorr = {}
    for index, row in csv_file.iterrows():
        csv_input_dict_corr.update({row[1]: (row[2] + row[4], row[3] + row[5])})
        csv_input_dict_uncorr.update({row[1]: (row[2], row[3])})

    # return {'Uncorrected': csv_input_dict_corr, 'Corrected': csv_input_dict_uncorr}
    return csv_input_dict_corr


def load_from_pickle(dict_path):
    with open(dict_path, mode="rb") as read_file:
        return pickle.load(read_file)


def data_input_from_dict(dict_filepath: str = None):
    """
    Convert data input from csv to dictionary with filenames and crack tip positions.

    Parameters
    ----------
    dict_filepath : str
            self-explaining

    Returns
    ----------
    data_input_dict : dict [filename]: tuple (float, float)
            dict containing the filename and the respective crack tip position


    """

    picklefile = load_from_pickle(dict_filepath)

    # convert to dict and return
    csv_input_dict = {}

    for key in picklefile.keys():
        if len(picklefile[key]) == 0:
            continue
        else:
            sub_dict = picklefile[key]

            for key, value in sub_dict.items():
                csv_input_dict.update({key: (value[0], value[1])})

    return csv_input_dict


def sum_results(
    specimen_name: str = "not defined",
    side: str = None,
    result_path: str = None,
    delete_single_files: bool = True,
    key_index: str = None,
):
    """Loop through single files and sum it up .

    Parameters
    ----------
    specimen_name : str
            self-explaining
    side : str
            side, has to be "left" or "right"
    key_index: str
            Define the row that will be set for the index

    result_path: str
            Path containing the single .csv files
    delete_single_files: bool, default = True
            Deletes single .csv files after summary - cleanup function :).

    """

    csv_files = [
        x
        for x in list(filter(lambda f: f.endswith(".csv"), os.listdir(result_path)))
        if "Summary" not in x
    ]

    df_concat = pd.concat(
        [pd.read_csv(os.path.join(result_path, f)) for f in sorted(csv_files)],
        ignore_index=False,
    ).set_index(key_index, drop=False)

    if np.any(delete_single_files):
        for filename in sorted(csv_files):
            file = os.path.join(result_path, filename)
            os.remove(file)
    df_concat.to_csv(os.path.join(result_path, f"{specimen_name}_{side}_Summary.csv"))


def pickle_output(
    specimen_name: str = "not defined",
    side: str = None,
    result_path: str = None,
    which: str = None,
):
    """

    Pickle  .

    Parameters
    ----------
    specimen_name : str
            self-explaining
    side : str
            side, has to be "left" or "right"
    result_path: str
            Path containing the single .csv files
    which: str
            object to get pickled

    """

    with open(
        os.path.join(result_path, f"{specimen_name}_{side}_Plastic_Zone.pickle"), "wb"
    ) as handle:
        pickle.dump(which, handle, protocol=pickle.HIGHEST_PROTOCOL)


def json_output(
    specimen_name: str = "not defined",
    side: str = None,
    result_path: str = None,
    which: str = None,
):
    """

    JSON output

    Parameters
    ----------
    specimen_name : str
            self-explaining
    side : str
            side, has to be "left" or "right"
    result_path: str
            Path containing the single .csv files
    which: str
            object to get jsoned

    """

    with open(
        os.path.join(result_path, f"{specimen_name}_{side}_Plastic_Zone.json"), "w"
    ) as handle:
        print("done")
        json.dump(which, handle)


def filter_data_input(data_in: dict = None, limit: tuple = (None, None)):

    if isinstance(data_in, dict):
        dict_filtered = {}
        for k, v in data_in.items():
            if abs(v[0]) > limit[0] and abs(v[0]) < limit[1]:
                dict_filtered.update({k: v})

        return dict_filtered

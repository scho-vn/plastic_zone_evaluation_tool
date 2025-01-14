import csv
import pickle
import os
import shutil
import pickle
import numpy as np

from matplotlib import pyplot as plt, cm
from matplotlib import tri
from matplotlib.colors import ListedColormap
from scipy.interpolate import griddata
import scipy.interpolate
import cv2
import pandas as pd
import math
import crackpy
from crackpy.structure_elements.data_files import Nodemap
from crackpy.fracture_analysis.data_processing import InputData
from sympy.plotting import plot_contour

from utils.functions import data_input_from_csv, sum_results, pickle_output, filter_data_input, data_input_from_csv_mt, json_output
from utils.data_processing import Data_Processing
from utils.plot import Plotter
from utils.result_writer import Result_Writer



global_path = os.getcwd()
specimen_name='EBr0001'
side = 'right'
specimen_type = 'MT'

specimenlist=['EBr0001', 'EBr0002', 'EBr0003', 'EBr0007', 'EBr0008', 'EBr0009']
specimenlist=['FPa0037']
sidelist=['left', 'right']
sidelist=['right']
for specimen_name in specimenlist:
    for side in sidelist:
        data_input = data_input_from_csv_mt(csv_filepath=f'/home/scho_vn/Auswertung_MT_MDIC/{specimen_name}_{side}_MDIC.csv')


        #filtered_data = filter_data_input(data_in=data_input, limit=22)
        filtered_data = filter_data_input(data_in=data_input, limit=22)
        sum_nodemaps_to_results={}


        input_list=list(filtered_data)


        for item in input_list:

            nodemap_name = item.split('-')[1]

            analysis = Data_Processing(specimen_name=specimen_name,
                                       side = side,
                                       nodemap_name = item.split('-')[1],
                                       specimen_type = specimen_type)
            mask = analysis.mask_data(crack_tip_x=data_input[item][0],
                                      crack_tip_y=data_input[item][1],
                                      folder_id =int(item.split('-')[0]),
                                      strain_treshold = 0.68,
                                      crack_tip_tolerance = 0.1,
                                      reduce_x_window = (0.9,0.9),
                                      reduce_y_window = (0.1,0.1))

            evaluate = analysis.evaluate_contours(which_contours = ['Whole', 'Upper', 'Lower'],
                                                  secondary_crack_treshold=80)

            sum_nodemaps_to_results.update(analysis.nodemap_to_results)

            plotter = Plotter(Result=analysis,
                              which_contours = ['Whole'])
            plotter.plot_contour(plot_contour=True,
                                 plot_extreme_points=True,
                                 window_x=(4,4),
                                 window_y=(4,4),)

            plotter.plot_contour_on_nodemap(strain_treshold = 0.68,
                                            num_colors = 120,
                                            num_colorbars = 3,
                                            colormap = 'viridis')

            Result_Writer(Result=analysis).write_to_csv()

        summary = sum_results(specimen_name=specimen_name,
                              side=side,
                              result_path=os.path.join(global_path, '02_results',f'{specimen_name}', f'{side}',
                                                       '02_Data_Evaluation'),
                              delete_single_files=True,
                              key_index='Cycles')

        specimen_name_to_results ={f'{specimen_name}_{side}': sum_nodemaps_to_results}

        pickle_output(specimen_name=specimen_name,
                      side=side,
                      result_path=analysis.output_path_pickle,
                      which=specimen_name_to_results)

        #json_output(specimen_name=specimen_name,
                      #side=side,
                      #result_path=analysis.output_path_pickle,
                      #which=specimen_name_to_results)
        print('done')


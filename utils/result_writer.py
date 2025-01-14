import numpy as np
import matplotlib.pyplot as plt
import os
import csv

import pandas as pd
import seaborn as sns

from utils.data_processing import Data_Processing

class Result_Writer:

    def __init__(self, Result: Data_Processing):

        self.analysis = Result


    def write_to_csv(self):

        """
        Write analyzed data to .csv and analysis parameter to .txt .

        """

        analysis = self.analysis
        result_path = self.analysis.output_path_results

        if np.any(self.analysis.is_contour_detected):

            res_dict =  {k: v for k, v in self.analysis.key_to_results['Whole'].items() if isinstance(v,(int,str,float))}
            res_dict.pop('Secondary crack', None)

            # update with analysis from lower and upper area segmentation if avaiable. only add area, circumferential lenght,
            # and center of gravity coordinates

            for item in [item for item in self.analysis.key_to_results.keys() if item not in ['Whole']]:
                res_dict.update({f'{item}_Area PZ[mm²]': self.analysis.key_to_results[item]['Area PZ[mm²]']})
                res_dict.update({f'{item}_Contour lenght[mm]': self.analysis.key_to_results[item]['Contour lenght[mm]']})
                res_dict.update({f'{item}_COG_X[mm]': self.analysis.key_to_results[item]['COG_X[mm]']})
                res_dict.update({f'{item}_COG_Y[mm]': self.analysis.key_to_results[item]['COG_Y[mm]']})


            with open(os.path.join(result_path,f'{self.analysis.nodemap_name}.csv'), 'w') as csv_file:
                writer = csv.DictWriter(csv_file, res_dict.keys())
                writer.writeheader()
                writer.writerow(res_dict)

            print(f'Wrote results for {self.analysis.nodemap_name}')
            print(f'-------------------------------------------------')
        else:
            print(f'No results written for {self.analysis.nodemap_name}.')





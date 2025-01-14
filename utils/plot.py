import numpy as np
import matplotlib.pyplot as plt
import os
import seaborn as sns
import cv2
from mpl_toolkits.axes_grid1 import make_axes_locatable
from matplotlib import pyplot as plt, cm
from matplotlib import tri
from matplotlib.colors import ListedColormap

from utils.data_processing import Data_Processing
class Plotter:
    def __init__(self, Result: Data_Processing, which_contours : list =['Whole']):

        """Plotter - self explaining .

        Parameters
        ----------
        which_contours : list [str]
                list of contours to be evaluated. Can only be "Whole", "Upper" or "Lower"

        plot_nodemap : bool, default = True
                plot the nodemap underneath
        plot_extreme_points : bool, default = True
                plot the detected extreme points

        """

        self.list_of_contours = which_contours
        self.analysis = Result
        #self.plot_nodemap = plot_nodemap


    def plot_contour(self, plot_contour : True = bool,  plot_extreme_points: True = bool,
                     window_x: tuple = (3,3), window_y: tuple = (3,3)):

        """Plotter - self explaining .

        Parameters
        ----------

        plot_contour : bool, default = True
                plot the contour
        plot_extreme_points : bool, default = True
                plot the extreme points of the contour

        window_x : tuple (float, float)
            window around left and right extreme x coordinates to set plot x_lim around
        window_y : tuple (float, float)
            window around top and bottom extreme y coordinates to set plot y_lim around
        """

        colorpalette = sns.color_palette('colorblind')

        if self.analysis.specimen_type == 'MT':
            self.analysis.nodemap_name = f'{self.analysis.nodemap_folder_id}_{self.analysis.nodemap_name}'


        if np.any(self.analysis.is_contour_detected):


            self.plot_contour = plot_contour
            self.plot_extreme_points = plot_extreme_points



            for item in self.list_of_contours:
                fig, axs = plt.subplots(1, 1, gridspec_kw={'hspace': 0, 'wspace': 0, },
                                        figsize=(4, 6),)

                if np.any(plot_contour):
                    empty_image = np.zeros(self.analysis.griddata[0].shape, dtype=np.uint8)
                    empty_image.fill(255)

                    contour_to_plot=self.analysis.nodemap_to_results[self.analysis.nodemap_name][item]['Largest Contour [px]']
                    img_contour = cv2.drawContours(empty_image, contour_to_plot, -1, (0, 255, 255), 6)
                    axs.imshow(np.flipud(img_contour), extent=[self.analysis.nodemap_file.coor_x.min(), self.analysis.nodemap_file.coor_x.max(),
                                                               self.analysis.nodemap_file.coor_y.min(), self.analysis.nodemap_file.coor_y.max()], cmap='gray')
                    sns.scatterplot(x=[self.analysis.crack_tip_x], y=[self.analysis.crack_tip_y], marker='X', ax=axs, zorder=1)


                if np.any(plot_extreme_points):
                        for idx,ext in enumerate(['Ext_Bottom','Ext_Top','Ext_Left','Ext_Right']):
                            x_coords, y_coords = self.analysis.nodemap_to_results[self.analysis.nodemap_name][item][ext]
                            sns.scatterplot(x=[x_coords], y=[y_coords], color=colorpalette[idx], ax=axs, edgecolor='k', zorder=2)

                axs.set_xlim(self.analysis.nodemap_to_results[self.analysis.nodemap_name][item]['Ext_Left'][0]-window_x[0],
                             self.analysis.nodemap_to_results[self.analysis.nodemap_name][item]['Ext_Right'][0]+window_x[1])
                axs.set_ylim(self.analysis.nodemap_to_results[self.analysis.nodemap_name][item]['Ext_Top'][1]-window_y[0],
                             self.analysis.nodemap_to_results[self.analysis.nodemap_name][item]['Ext_Bottom'][1]+window_y[1])
                axs.set_xlabel(r'$\it x$ [mm]')
                axs.set_ylabel(r'$\it y$ [mm]')
                plt.tight_layout()

                output_name = f'{self.analysis.nodemap_name}.png'

                if not os.path.exists(os.path.join(self.analysis.output_path_contours, f'{item}')):
                    os.mkdir(os.path.join(self.analysis.output_path_contours, f'{item}'))

                save = os.path.join(self.analysis.output_path_contours, f'{item}', output_name)
                plt.savefig(save, dpi=300, bbox_inches='tight')
                plt.clf()
                plt.close()
                print(f'Plotted contour for {self.analysis.nodemap_name}.')

        else:
            print(f'No contour plotted for {self.analysis.nodemap_name}.')


    def plot_contour_on_nodemap(self,strain_treshold: float = 0.68, num_colors: int =120, num_colorbars : int =10,
                                colormap : str = 'viridis'):

        if np.any(self.analysis.is_contour_detected):

            for item in self.list_of_contours:
                fig, axs = plt.subplots(1, 1, gridspec_kw={'hspace': 0, 'wspace': 0, },
                                        figsize=(4, 6),)

                f_min = 0.0
                f_max = strain_treshold
                num_colors = num_colors
                num_colorbars = num_colorbars
                cmap_plot = colormap

                contour_vector = np.linspace(f_min, f_max, num_colors, endpoint=True)
                label_vector = np.linspace(f_min, f_max, num_colorbars, endpoint=True)

                cm_create = cm.get_cmap(cmap_plot, 512)
                cmap_list = ListedColormap(cm_create(np.linspace(0.1, 0.9, 256)))

                #plot nodemap

                triangulation = tri.Triangulation(x=self.analysis.nodemap_file.coor_x, y=self.analysis.nodemap_file.coor_y)
                plot = axs.tricontourf(triangulation, (self.analysis.nodemap_file.eps_vm * 100), contour_vector, extend='max', cmap=cmap_list)



                # add contour

                contour_to_plot = self.analysis.nodemap_to_results[self.analysis.nodemap_name][item]['Largest contour [mm]']


                sns.scatterplot(x=contour_to_plot[0], y=contour_to_plot[1], s=1, color='k', ax=axs, edgecolor=None)

                divider = make_axes_locatable(axs)
                cax = divider.append_axes("right", size="5%", pad=0.05)


                cbar=plt.colorbar(plot, cax=cax, ticks=label_vector, label=r'$\it\epsilon_{vm}$ [%]', format='%.2f',
                             orientation='vertical')
                #cbar.solids.set(alpha=1)

                axs.set_xlabel(r'$\it x$ [mm]')
                axs.set_ylabel(r'$\it y$ [mm]')

                axs.set_aspect('equal')
                plt.tight_layout()

                output_name = f'{self.analysis.nodemap_name}.png'

                if not os.path.exists(os.path.join(self.analysis.output_path_nodemaps, f'{item}')):
                    os.mkdir(os.path.join(self.analysis.output_path_nodemaps, f'{item}'))

                save = os.path.join(self.analysis.output_path_nodemaps, f'{item}', output_name)
                plt.savefig(save, dpi=300, bbox_inches='tight')
                plt.clf()
                plt.close()
                print(f'Plotted nodemap for {self.analysis.nodemap_name}.')

        else:
            print(f'No contour plotted for {self.analysis.nodemap_name}.')








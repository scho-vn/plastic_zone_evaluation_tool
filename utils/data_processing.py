import math
import matplotlib
from crackpy.structure_elements.data_files import Nodemap
from crackpy.fracture_analysis.data_processing import InputData
from scipy.interpolate import griddata
import cv2
import os
import numpy as np

matplotlib.use("tKAgg")


class Data_Processing:
    def __init__(
        self,
        specimen_name: str = "not defined",
        side: str = None,
        nodemap_name: str = None,
        specimen_type: str = None,
    ):
        """
        Parameter for analyzing the plastic zone based on either FE or DIC data.

        Parameters
        ----------
        specimen_name : str
                self-explaining
        side : str
                side, has to be "left" or "right"
        nodemap_name : str
                self-explaining
        specimen_type : str
                specimen type, can be either "Biax", "MT" or "FE". Defines how the input data are proceeded.

        """

        global_path = os.getcwd()
        self.specimen_name = specimen_name
        self.side = side
        self.nodemap_name = nodemap_name
        self.specimen_type = specimen_type

        self.output_path = os.path.join(
            global_path, "02_results", self.specimen_name, self.side
        )

        if not os.path.exists(self.output_path):
            os.makedirs(self.output_path)

        self.output_path_image = os.path.join(self.output_path, "01_Plots")
        self.output_path_contours = os.path.join(self.output_path_image, "01_Contours")
        self.output_path_nodemaps = os.path.join(self.output_path_image, "02_Nodemaps")
        self.output_path_results = os.path.join(self.output_path, "02_Data_Evaluation")
        self.output_path_pickle = os.path.join(self.output_path, "03_Data_Pickle")

        for folder in [
            self.output_path_image,
            self.output_path_contours,
            self.output_path_nodemaps,
            self.output_path_results,
            self.output_path_pickle,
        ]:
            if not os.path.exists(folder):
                os.makedirs(folder)

    def get_meta_attributes(self):
        """
        Define the meta attributes according to specimen type - default is MT Specimen
        """
        if self.specimen_type == "Biax":
            self.meta_attributes = [
                "force",
                "cycles",
                "displacement",
                "potential",
                "cracklength",
                "time",
                "dms_1",
                "dms_2",
                "x",
                "y",
                "z",
                "alignment_translation_x",
                "alignment_translation_y",
                "alignment_translation_z",
                "experimental_data_load_main_axis_fy",
                "experimental_data_load_side_axis_fx",
                "experimental_data_cycles_catman",
                "experimental_data_cycles",
                "experimental_data_crack_tip_x_right",
                "experimental_data_crack_tip_y_right",
                "experimental_data_crack_tip_x_left",
                "experimental_data_crack_tip_y_left",
                "experimental_data_stage",
                "experimental_data_step_number",
            ]

            self.meta_attributes_to_keywords = {v: v for v in self.meta_attributes}

            return self.meta_attributes_to_keywords

    def mask_data(
        self,
        crack_tip_x: float = None,
        crack_tip_y: float = None,
        folder_id: float = None,
        strain_treshold: float = 0.68,
        crack_tip_tolerance: float = 0.1,
        reduce_x_window: tuple = (0, 0),
        reduce_y_window: tuple = (0, 0),
    ):
        """
        Mask plastic zone within nodemap files for given crack tip x and y coordinates.

        Parameters
        ----------
        crack_tip_x : float
                crack tip position x from manual input or data range
        crack_tip_y : float
                crack tip position y from manual input or data range

        folder_id : float
                nodemap folder - only valid for mt specimen
        strain_treshold : float
                threshold value for masking the strain field
        crack_tip_tolerance : float
                tolerance for masking behind the crack tip in mm
        reduce_x_window, reduce_y_window : tuple (float, float)
                to narrow down the analysed window, one can mask areas with a given distance from the outermost window
                coordinates.

                example: total window is defined by x.min=20, x.max=28, y.min=4, y.max=10
                applying both masks reduce_x_window = (2,3) and reduce_y_window = (1,1.5) narrows down the analyzed
                coordinates to (20+2, 28-3,  4+1, 10-1.5) --> new window is x.min=22, x.max=25, y.min=5, y.max=8.5


        Returns
        ----------
        key_to_contour : dict
            dictionary containing the detected contours and corresponsing hierachical information for the whole contour,
            lower and upper half, assuming that we separate by a straight line throught the crack tip
        griddata : tuple (arr, arr, arr)
            tuple containing the grid where the initial data were mapped. x, y and z = strains.


        """

        if self.side == "left":
            self.flip = -1
        else:
            self.flip = 1

        if self.specimen_type == "Biax":

            self.cycles = int(self.nodemap_name.split("_")[1])
            self.nodemap_path = os.path.join(
                os.getcwd(),
                "data_examples",
                self.specimen_name,
                "nodemaps",
            )
            self.nodemap = Nodemap(name=self.nodemap_name, folder=self.nodemap_path)

            self.nodemap_file = InputData(
                self.nodemap, meta_keywords=self.meta_attributes_to_keywords
            )
            self.cycles = self.nodemap_file.experimental_data_cycles
            self.force = self.nodemap_file.experimental_data_load_main_axis_fy
            self.cracklength = self.nodemap_file.experimental_data_crack_tip_x_right
            self.crack_tip_x = crack_tip_x * self.flip
            self.crack_tip_y = crack_tip_y

            self.strain_treshold = strain_treshold
            self.crack_tip_tolerance = crack_tip_tolerance
            self.reduce_x_window = reduce_x_window
            self.reduce_y_window = reduce_y_window

            # get nodemap data and flip if side == left
            self.nodemap_file.coor_x = self.nodemap_file.coor_x * self.flip

            x_coordinates = self.nodemap_file.coor_x
            y_coordinates = self.nodemap_file.coor_y
            strains = self.nodemap_file.eps_vm * 100
            cracklength = self.nodemap_file.cracklength
            force_meta = self.nodemap_file.experimental_data_load_main_axis_fy

        if self.specimen_type == "MT":

            self.nodemap_folder_id = folder_id
            self.nodemap_path = os.path.join(
                os.getcwd(),
                "data_examples",
                self.specimen_name,
                "nodemaps",
            )
            self.nodemap = Nodemap(name=self.nodemap_name, folder=self.nodemap_path)

            self.nodemap_file = InputData(self.nodemap)
            self.crack_tip_x = crack_tip_x * self.flip
            self.crack_tip_y = crack_tip_y
            self.folder = folder_id

            self.cycles = self.nodemap_file.cycles

            self.strain_treshold = strain_treshold
            self.crack_tip_tolerance = crack_tip_tolerance
            self.reduce_x_window = reduce_x_window
            self.reduce_y_window = reduce_y_window

            # get nodemap data and flip if side == left
            self.nodemap_file.coor_x = self.nodemap_file.coor_x * self.flip

            x_coordinates = self.nodemap_file.coor_x
            y_coordinates = self.nodemap_file.coor_y
            strains = self.nodemap_file.eps_vm * 100

        if self.specimen_type == "FE":
            self.nodemap_path = os.path.join(
                os.getcwd(),
                "data_examples",
                self.specimen_name,
                "nodemaps",
            )
            self.nodemap = Nodemap(name=self.nodemap_name, folder=self.nodemap_path)

            self.nodemap_file = InputData(self.nodemap)

            self.crack_tip_x = crack_tip_x * self.flip
            self.crack_tip_y = crack_tip_y

            self.cycles = 0

            self.strain_treshold = strain_treshold
            self.crack_tip_tolerance = crack_tip_tolerance
            self.reduce_x_window = reduce_x_window
            self.reduce_y_window = reduce_y_window

            # get nodemap data and flip if side == left
            self.nodemap_file.coor_x = self.nodemap_file.coor_x * self.flip

            x_coordinates = self.nodemap_file.coor_x
            y_coordinates = self.nodemap_file.coor_y
            strains = self.nodemap_file.eps_vm * 100

        # prepare image data
        # Mesh Data to Grid

        if self.specimen_type == "FE":
            x_int = np.arange(
                start=x_coordinates.min(), stop=x_coordinates.max(), step=0.02
            )
            y_int = np.arange(
                start=y_coordinates.min(), stop=y_coordinates.max(), step=0.02
            )

        else:
            x_int = np.arange(
                start=x_coordinates.min(), stop=x_coordinates.max(), step=0.01
            )
            y_int = np.arange(
                start=y_coordinates.min(), stop=y_coordinates.max(), step=0.01
            )
        xi, yi = np.meshgrid(x_int, y_int)
        zi = griddata(
            (x_coordinates, y_coordinates), strains, (xi, yi), method="linear"
        )

        self.griddata = (xi, yi, zi)

        # mask data according to given parameters - we only analyze the area in front of the crack tip.
        # A reduction of the window is necessary for DIC data to filter possible artefacts or if the crack tip is
        # too close to any of the borders of the image.

        thresholded_strains = zi > self.strain_treshold

        in_front_of_ct_x = xi > abs(self.crack_tip_x) - self.crack_tip_tolerance

        x_window = (
            in_front_of_ct_x,
            (xi < x_coordinates.max() - self.reduce_x_window[1]),
        )

        y_window = (
            (yi < self.crack_tip_y + self.reduce_y_window[0]),
            (yi > self.crack_tip_y - self.reduce_y_window[1]),
        )

        upper_half = yi <= self.crack_tip_y
        lower_half = yi >= self.crack_tip_y

        # create mask for whole contour, lower and upper half and binarize
        if self.specimen_type == "Biax":
            mask_all = 1 * (
                np.all(
                    [
                        thresholded_strains,
                        x_window[0],
                        x_window[1],
                        y_window[0],
                        y_window[1],
                    ],
                    axis=0,
                )
            )
            mask_lower = 1 * (
                np.all(
                    [
                        thresholded_strains,
                        x_window[0],
                        x_window[1],
                        upper_half,
                        y_window[1],
                    ],
                    axis=0,
                )
            )
            mask_upper = 1 * (
                np.all(
                    [
                        thresholded_strains,
                        x_window[0],
                        x_window[1],
                        lower_half,
                        y_window[0],
                    ],
                    axis=0,
                )
            )
        if self.specimen_type == "MT":
            mask_all = 1 * (
                np.all([thresholded_strains, x_window[0], x_window[1]], axis=0)
            )
            mask_lower = 1 * (
                np.all(
                    [thresholded_strains, x_window[0], x_window[1], upper_half], axis=0
                )
            )
            mask_upper = 1 * (
                np.all(
                    [thresholded_strains, x_window[0], x_window[1], lower_half], axis=0
                )
            )

        if self.specimen_type == "FE":
            mask_all = 1 * (np.all([thresholded_strains, in_front_of_ct_x], axis=0))
            mask_lower = 1 * (
                np.all(
                    [thresholded_strains, x_window[0], x_window[1], upper_half], axis=0
                )
            )
            mask_upper = 1 * (
                np.all(
                    [thresholded_strains, x_window[0], x_window[1], lower_half], axis=0
                )
            )

        # put in dict
        masked_dict = {"Whole": mask_all, "Upper": mask_upper, "Lower": mask_lower}
        self.key_to_contour = {}
        nodemap_to_contour = {}

        for key, value in masked_dict.items():
            # plt.imshow(value)
            # plt.show()

            norm_image = cv2.normalize(
                value,
                None,
                alpha=0,
                beta=255,
                norm_type=cv2.NORM_MINMAX,
                dtype=cv2.CV_8UC1,
            )
            contours, hierarchy = cv2.findContours(
                norm_image, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE
            )
            self.key_to_contour.update(
                {f"{key}": {"Contour": contours, "Hierarchy": hierarchy}}
            )

        nodemap_to_contour.update({f"{self.nodemap_name}": self.key_to_contour})
        print(f"Masked data for {self.nodemap_name}")
        print("-------------------------------------")
        return self.key_to_contour, self.griddata

    def evaluate_contours(
        self, which_contours=None, secondary_crack_treshold: float = 80
    ):
        """
        evaluate the detected contours

        Parameters
        ----------
        which_contours : list [str]
                list of contours to be evaluated. Can only be "Whole", "Upper" or "Lower"
        secondary_crack_treshold: float, [%]
                the occurence of possible secondary cracks bases on a case differentiation taking into account the total
                area of the largest and comparing it to the area of all other detected contours. If the total percentage
                of area difference exceeds the secondary_crack_treshold in [%] (means that the contour is 80% smaller than
                the largest contour) we assume that the second contour is an artefact and therefore not a secondary crack.
                Usually secondary cracks show a contour that is nearly equally sized to the largest contour.

        Returns
        ----------
        nodemap_to_results : dict
            dictionary containing the analyzed contour using size descriptors for each element that is defined in the
            input list "which contour"

        is_contour_detected : bool
            set to True if all contours were detected. If any of the masked areas returns no contour, bit is set to
            False
        """

        if which_contours is None:
            which_contours = ["Whole"]
        key_to_contour = self.key_to_contour
        griddata = self.griddata
        (
            x_int,
            y_int,
        ) = (
            griddata[0][0],
            griddata[1][:, 0].flatten(),
        )
        self.list_of_contours = which_contours
        self.secondary_crack_treshold = secondary_crack_treshold
        self.key_to_results = {}
        self.nodemap_to_results = {}
        self.contour_detected_list = []
        self.is_contour_detected = None

        for item in self.list_of_contours:
            count_found_contours = len(key_to_contour[item]["Contour"])
            print(f"{item} Contour : Found number of contours:{count_found_contours}")

            # case distinguishion for all detected contours. is there no contour, a single contour or multiple?

            if count_found_contours == 0:
                print("no contours found")
                sec_crack = "No"
                self.contour_detected_list.append(False)
                continue

            else:
                self.contour_detected_list.append(True)
                if count_found_contours == 1:
                    contour_to_analyze = max(key_to_contour[item]["Contour"], key=len)
                    sec_crack = "No"

                if count_found_contours > 1:
                    sec_crack = "Yes"
                    found_contours = np.arange(0, count_found_contours)
                    contour_all = sorted(
                        key_to_contour[item]["Contour"],
                        key=cv2.contourArea,
                        reverse=True,
                    )  # cnt[0] largest cnt[1] second largest
                    contour_to_analyze = max(
                        key_to_contour[item]["Contour"], key=cv2.contourArea
                    )
                    for k in found_contours:
                        area_pz = cv2.contourArea(contour_to_analyze)
                        area = cv2.contourArea(contour_all[k])
                        area_diff = ((area_pz - area) / area_pz) * 100
                        if area_diff > self.secondary_crack_treshold:
                            contour_to_analyze = max(
                                key_to_contour[item]["Contour"], key=cv2.contourArea
                            )

                        else:
                            contour_to_analyze = max(
                                key_to_contour[item]["Contour"], key=cv2.contourArea
                            )
                            continue

                # Analyze the contours properties
                area_contour = cv2.contourArea(contour_to_analyze)

                # find the coordinates of the extreme points left, right, top and bottom
                # to convert the pixel coordinates to mm we need the grid and remap.

                extLeft = tuple(
                    contour_to_analyze[contour_to_analyze[:, :, 0].argmin()][0]
                )
                x_left, y_left = x_int[int(extLeft[0])], y_int[int(extLeft[1])]
                extRight = tuple(
                    contour_to_analyze[contour_to_analyze[:, :, 0].argmax()][0]
                )
                x_right, y_right = x_int[int(extRight[0])], y_int[int(extRight[1])]
                extTop = tuple(
                    contour_to_analyze[contour_to_analyze[:, :, 1].argmax()][0]
                )
                x_top, y_top = x_int[int(extTop[0])], y_int[int(extTop[1])]
                extBot = tuple(
                    contour_to_analyze[contour_to_analyze[:, :, 1].argmin()][0]
                )
                x_bottom, y_bottom = x_int[int(extBot[0])], y_int[int(extBot[1])]

                # height and lenght are the distances between the outermost top and bottom and left and right points.
                pz_height = abs(y_top - y_bottom)
                pz_lenght = abs(x_right - x_left)

                # center of gravity - cog
                moments = cv2.moments(contour_to_analyze)
                cog_x, cog_y = (
                    x_int[int(moments["m10"] / moments["m00"])],
                    y_int[int(moments["m01"] / moments["m00"])],
                )

                # convert area and contour lenght in mm - one mm equals xx pixel
                pixelsize = len(x_int) / (x_int.max() - x_int.min())
                area_pz = area_contour / (pixelsize**2)
                contour_lenght_pz = (
                    cv2.arcLength(contour_to_analyze, closed=True)
                ) / pixelsize

                # calculate angle between crack tip and center of gravity in degree
                angle_ct_to_cog = math.degrees(
                    math.atan2(cog_y - self.crack_tip_y, cog_x - self.crack_tip_x)
                )

                # convert largest contour pixel coordinates into x-y coordinates

                pixel_to_x_coords = [x_int[v[0][0]] for v in contour_to_analyze]
                pixel_to_y_coords = [y_int[v[0][1]] for v in contour_to_analyze]

                # sum results

                if self.specimen_type == "Biax":
                    self.key_to_results.update(
                        {
                            f"{item}": {
                                "Cycles": self.cycles,
                                "Filename": self.nodemap_name,
                                "Crack Tip X[mm]": self.crack_tip_x,
                                "Crack Tip Y[mm]": self.crack_tip_y,
                                "Crack lenght[mm]": self.nodemap_file.cracklength,
                                "Area PZ[mm²]": area_pz,
                                "COG_X[mm]": cog_x,
                                "COG_Y[mm]": cog_y,
                                "Contour lenght[mm]": contour_lenght_pz,
                                "Angle[°]": angle_ct_to_cog,
                                "Epsmax[%]": self.nodemap_file.eps_vm.max(),
                                "Threshold": self.strain_treshold,
                                "X_min[mm]": self.nodemap_file.coor_x.min(),
                                "X_max[mm]": self.nodemap_file.coor_x.max(),
                                "Y_min[mm]": self.nodemap_file.coor_y.min(),
                                "Y_max[mm]": self.nodemap_file.coor_y.max(),
                                "Pixelsize": pixelsize,
                                "Height": pz_height,
                                "Lenght": contour_lenght_pz,
                                "Secondary crack": sec_crack,
                                "Largest Contour [px]": contour_to_analyze,
                                "Ext_Bottom": (x_bottom, y_bottom),
                                "Ext_Top": (x_top, y_top),
                                "Ext_Left": (x_left, y_left),
                                "Ext_Right": (x_right, y_right),
                                "Largest contour [mm]": (
                                    pixel_to_x_coords,
                                    pixel_to_y_coords,
                                ),
                            }
                        }
                    )
                    self.nodemap_to_results.update(
                        {f"{self.nodemap_name}": self.key_to_results}
                    )

                self.is_contour_detected = np.any(self.contour_detected_list)

                print(f"Stored data for {self.nodemap_name}")
                print("-------------------------------------")

                if self.specimen_type == "MT":
                    self.key_to_results.update(
                        {
                            f"{item}": {
                                "Cycles": self.cycles,
                                "Filename": f"{self.nodemap_folder_id}_{self.nodemap_name}",
                                "Crack Tip X[mm]": self.crack_tip_x,
                                "Crack Tip Y[mm]": self.crack_tip_y,
                                "Crack lenght[mm]": self.nodemap_file.cracklength,
                                "Area PZ[mm²]": area_pz,
                                "COG_X[mm]": cog_x,
                                "COG_Y[mm]": cog_y,
                                "Contour lenght[mm]": contour_lenght_pz,
                                "Angle[°]": angle_ct_to_cog,
                                "Epsmax[%]": self.nodemap_file.eps_vm.max(),
                                "Threshold": self.strain_treshold,
                                "X_min[mm]": self.nodemap_file.coor_x.min(),
                                "X_max[mm]": self.nodemap_file.coor_x.max(),
                                "Y_min[mm]": self.nodemap_file.coor_y.min(),
                                "Y_max[mm]": self.nodemap_file.coor_y.max(),
                                "Pixelsize": pixelsize,
                                "Height": pz_height,
                                "Lenght": contour_lenght_pz,
                                "Secondary crack": sec_crack,
                                "Largest Contour [px]": contour_to_analyze,
                                "Ext_Bottom": (x_bottom, y_bottom),
                                "Ext_Top": (x_top, y_top),
                                "Ext_Left": (x_left, y_left),
                                "Ext_Right": (x_right, y_right),
                                "Largest contour [mm]": (
                                    pixel_to_x_coords,
                                    pixel_to_y_coords,
                                ),
                            }
                        }
                    )
                    self.nodemap_to_results.update(
                        {
                            f"{self.nodemap_folder_id}_{self.nodemap_name}": self.key_to_results
                        }
                    )

                if self.specimen_type == "FE":
                    self.key_to_results.update(
                        {
                            f"{item}": {
                                "Cycles": self.cycles,
                                "Filename": f"{self.nodemap_name}",
                                "Crack Tip X[mm]": self.crack_tip_x,
                                "Crack Tip Y[mm]": self.crack_tip_y,
                                "Crack lenght[mm]": self.nodemap_file.cracklength,
                                "Area PZ[mm²]": area_pz,
                                "COG_X[mm]": cog_x,
                                "COG_Y[mm]": cog_y,
                                "Contour lenght[mm]": contour_lenght_pz,
                                "Angle[°]": angle_ct_to_cog,
                                "Epsmax[%]": self.nodemap_file.eps_vm.max(),
                                "Threshold": self.strain_treshold,
                                "X_min[mm]": self.nodemap_file.coor_x.min(),
                                "X_max[mm]": self.nodemap_file.coor_x.max(),
                                "Y_min[mm]": self.nodemap_file.coor_y.min(),
                                "Y_max[mm]": self.nodemap_file.coor_y.max(),
                                "Pixelsize": pixelsize,
                                "Height": pz_height,
                                "Lenght": contour_lenght_pz,
                                "Secondary crack": sec_crack,
                                "Largest Contour [px]": contour_to_analyze,
                                "Ext_Bottom": (x_bottom, y_bottom),
                                "Ext_Top": (x_top, y_top),
                                "Ext_Left": (x_left, y_left),
                                "Ext_Right": (x_right, y_right),
                                "Largest contour [mm]": (
                                    pixel_to_x_coords,
                                    pixel_to_y_coords,
                                ),
                            }
                        }
                    )
                    self.nodemap_to_results.update(
                        {f"{self.nodemap_name}": self.key_to_results}
                    )

                self.is_contour_detected = np.any(self.contour_detected_list)

                print(f"Stored data for {self.nodemap_name}")
                print("-------------------------------------")

        return self.nodemap_to_results
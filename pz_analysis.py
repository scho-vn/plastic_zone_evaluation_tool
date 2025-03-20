import os
from utils.functions import (
    data_input_from_csv,
    sum_results,
    pickle_output,
    filter_data_input,
    data_input_from_dict,
    data_input_from_csv_mt,
)
from utils.data_processing import Data_Processing
from utils.plot import Plotter
from utils.result_writer import Result_Writer


global_path = os.getcwd()
specimen_name = "dic_cruciform_specimen"
side = "right"
specimen_type = "Biax"


data_input = data_input_from_csv(
    csv_filepath=os.path.join(
        global_path, "data_examples", f"{specimen_name}", "Cruciform_5.csv"
    )
)

filtered_data = filter_data_input(data_in=data_input, limit=(30, 70))
sum_nodemaps_to_results = {}
input_list = list(filtered_data)


for item in input_list:

    analysis = Data_Processing(
        specimen_name=specimen_name,
        side=side,
        nodemap_name=item,
        specimen_type=specimen_type,
    )
    meta_attributes = analysis.get_meta_attributes()
    mask = analysis.mask_data(
        crack_tip_x=data_input[item][0],
        crack_tip_y=data_input[item][1],
        strain_treshold=0.68,
        crack_tip_tolerance=0.1,
        reduce_x_window=(0, 2),
        reduce_y_window=(6, 6),
    )

    evaluate = analysis.evaluate_contours(
        which_contours=["Whole", "Upper", "Lower"], secondary_crack_treshold=80
    )

    sum_nodemaps_to_results.update(analysis.nodemap_to_results)

    plotter = Plotter(Result=analysis, which_contours=["Whole"])
    plotter.plot_contour(
        plot_contour=True,
        plot_extreme_points=True,
        window_x=(2, 2),
        window_y=(2, 2),
    )

    plotter.plot_contour_on_nodemap(
        strain_treshold=0.68, num_colors=120, num_colorbars=3, colormap="viridis"
    )

    Result_Writer(Result=analysis).write_to_csv()

summary = sum_results(
    specimen_name=specimen_name,
    side=side,
    result_path=os.path.join(
        global_path, "02_results", f"{specimen_name}", f"{side}", "02_Data_Evaluation"
    ),
    delete_single_files=True,
    key_index="Cycles",
)

specimen_name_to_results = {f"{specimen_name}_{side}": sum_nodemaps_to_results}

pickle_output(
    specimen_name=specimen_name,
    side=side,
    result_path=analysis.output_path_pickle,
    which=specimen_name_to_results,
)
print("done")



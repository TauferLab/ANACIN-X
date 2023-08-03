from IPython.display import Image, clear_output
import ipywidgets as widgets
from ipywidgets import interact, interact_manual
import os

layout=widgets.Layout(width='50%')
#Number of processes widget
num_processes_widget = widgets.IntText(
    value=0,
    description='Number of processess:',
    style= {'description_width': 'initial'},
    layout=layout
)

#Number of runs widget
num_runs_widget = widgets.IntText(
    value=0,
    description='Number of runs:',
    style= {'description_width': 'initial'},
    layout=layout
)
#Number of iterations widget
num_iterations_widget = widgets.IntText(
    value=0,
    description='Number of iterations:',
    style= {'description_width': 'initial'},
    layout=layout
)

#PnMPI Config Widget
pnmpi_conf_widget = widgets.Dropdown(
    options=[('',""),('csmpi', "csmpi.conf"), ('dumpi_csmpi', "dumpi_csmpi.conf"), ('dumpi_ninja', "dumpi_ninja.conf"), ('dumpi_pluto_csmpi', "dumpi_pluto_csmpi.conf"), ('dumpi', "dumpi.conf"), ('dumpi_csmpi_ninja', "dumpi_csmpi_ninja.conf"), ('dumpi_pluto', "dumpi_pluto.conf"), ('empty', "empty.conf")],
    value='',
    description='PnMPI Config:',
    style= {'description_width': 'initial'},
    continious_update=True,
    layout=layout
)

#Executable Path Widget
executable_widget = widgets.Text(
    value="",
    description='Executable path:',
    style= {'description_width': 'initial'},
    layout=layout
)

#Executable args Widget
executable_args_widget = widgets.Text(
    value="",
    description='Executable args:',
    style= {'description_width': 'initial'},
    layout=layout
)

trace_widget = widgets.Button(
    description='Trace',
    style= {'description_width': 'initial'},
    layout=layout
)

create_instance_widget =  widgets.Button(
    description='Create Instance',
    style= {'description_width': 'initial'},
    button_style='success',
    layout=layout
)

kill_instance_widget =  widgets.Button(
    description='Kill Instance',
    style= {'description_width': 'initial'},
    button_style='danger',
    layout=layout
)

gen_event_graph_widget = widgets.Button(
    description='Generate Event Graph',
    style= {'description_width': 'initial'},
    layout=layout
)

slice_extraction_widget = widgets.Button(
    description='Extract Slices',
    style= {'description_width': 'initial'},
    layout=layout
)

compute_kdts_widget = widgets.Button(
    description='Compute KDTS',
    style= {'description_width': 'initial'},
    layout=layout
)

create_visualization_widget = widgets.Button(
    description='Create Visualization',
    style= {'description_width': 'initial'},
    layout=layout
)

display_visualization_widget = widgets.Button(
    description='Display Visualization',
    style= {'description_width': 'initial'},
    layout=layout
)

benchmark_type_selector_widget = widgets.Button(
    description='Benchmark',
    style= {'description_width': 'initial'},
    layout=layout
)

extern_type_selector_widget = widgets.Button(
    description='External Application',
    style= {'description_width': 'initial'},
    layout=layout
)

#Output directory
output_dir_widget = widgets.Text(
    value="",
    description='Enter output directory path:',
    style= {'description_width': 'initial'},
    layout=layout
)

#Image path
image_path_widget = widgets.Text(
    value="",
    description='Enter container image path:',
    style= {'description_width': 'initial'},
    layout=layout
)

param_num_processes = num_processes_widget.value
param_num_runs = num_runs_widget.value
param_num_iterations = num_iterations_widget.value
param_pnmpi_config = pnmpi_conf_widget.value
param_executable = executable_widget.value
param_executable_args = executable_args_widget.value
param_output_dir = output_dir_widget.value
param_image_path = image_path_widget.value

def listen_processess(change):
    global param_num_processes
    param_num_processes = change.new
    
def listen_runs(change):
    global param_num_runs
    param_num_runs = change.new
    
def listen_iterations(change):
    global param_num_iterations
    param_num_iterations = change.new
    
def listen_pnmpi(change):
    global param_pnmpi_config
    param_pnmpi_config = change.new

def listen_executable(change):
    global param_executable
    param_executable = change.new   
    
def listen_args(change):
    global param_executable_args
    param_executable_args = change.new  

def listen_output_dir(change):
    global param_output_dir
    param_output_dir = change.new  

def listen_image_path(change):
    global param_image_path
    param_image_path = change.new  
# print(param_num_processes)
# print(param_num_runs)
# print(param_num_iterations)
# print(param_pnmpi_config)
# print(param_executable)
# print(param_executable_args)

    
def on_button_clicked_0(button):
#     with output:
#         print("Button clicked.")
    clear_output()
    display(button)
    if button == trace_widget:
        print("Tracing...")
        if clean_output_dir(param_output_dir) == 0:
            print("Invalid output directory")
            return
#         def trace_execution(executable_path, args, num_processes, num_runs, num_iterations, pnmpi_conf, output_dir):
#         trace_execution("/ANACIN-X/apps/comm_pattern_generator/build/comm_pattern_generator", "/home/bbogale/results/message_race_msg_size_512_niters_5_ndp_0.0_0.1_1.0.json /ANACIN-X/anacin-x/config", 30, 10, "dumpi_pluto_csmpi.conf", "/home/bbogale/results")
        #trace_execution("/ANACIN-X/apps/comm_pattern_generator/build/comm_pattern_generator", "/home/bbogale/results/message_race_msg_size_512_niters_5_ndp_0.0_0.1_1.0.json /ANACIN-X/anacin-x/config", param_num_processes, param_num_runs, param_num_iterations, param_pnmpi_config, "/home/bbogale/results")
        tmp_param = param_output_dir + "/message_race_msg_size_512_niters_" + str(param_num_iterations) + "_ndp_0.0_0.1_1.0.json" + " /ANACIN-X/anacin-x/config"
        trace_execution("/ANACIN-X/apps/comm_pattern_generator/build/comm_pattern_generator", tmp_param, param_num_processes, param_num_runs, param_num_iterations, param_pnmpi_config, param_output_dir)
    elif button == kill_instance_widget:
        print("Killing Instance..")
        kill_instance()
    elif button == create_instance_widget:
        print("Creating Instance..")
        create_instance(param_output_dir, param_image_path)
    elif button == gen_event_graph_widget:
        print("Generating Event Graph...")
#         generate_event_graph(30, 10, "dumpi_and_csmpi.json", "/home/bbogale/results/")
        #generate_event_graph(param_num_processes, param_num_runs, "dumpi_and_csmpi.json", "/home/bbogale/results/")
        generate_event_graph(param_num_processes, param_num_runs, "dumpi_and_csmpi.json", param_output_dir)
    elif button == slice_extraction_widget:
        print("Extracting Slices...")
#         extract_slices(30, 10,  "barrier_delimited_full.json", "/home/bbogale/results/")
        #extract_slices(param_num_processes, param_num_runs,  "barrier_delimited_full.json", "/home/bbogale/results/")
        extract_slices(param_num_processes, param_num_runs,  "barrier_delimited_full.json", param_output_dir)
    elif button == compute_kdts_widget:
        print("Computing the KDTS...")
#         compute_kdts(30, "barrier_delimited_full.json", "/home/bbogale/results/")
        #compute_kdts(param_num_processes, "barrier_delimited_full.json", "/home/bbogale/results/")        
        compute_kdts(param_num_processes, "barrier_delimited_full.json", param_output_dir)
        print("Done!")
    elif button == create_visualization_widget:
        print("Creating Visualization...")
       #!apptainer exec instance://anacin_jupyter_instance \
       #bash -c 'cd /ANACIN-X ; python3 anacin-x/event_graph_analysis/visualization/make_message_nd_plot.py \
       #/home/bbogale/results/kdts.pkl \
       #message_race \
       #anacin-x/event_graph_analysis/graph_kernel_policies/wlst_5iters_logical_timestamp_label.json \
       #/home/bbogale/results/kdts \
       #0.0 0.1 1.0'
        create_graph(param_output_dir)
    elif button == display_visualization_widget:
#         display(display_visualization_widget)
        param_tmp = param_output_dir + "/kdts.png"
        #display(Image(filename="/home/bbogale/results//kdts.png"))
        display(Image(filename=param_tmp))
    
def on_button_clicked_1(button):
    clear_output()
    display(widgets.HBox([benchmark_type_selector_widget, extern_type_selector_widget]))
    if button == benchmark_type_selector_widget:
        display(num_processes_widget, num_runs_widget, num_iterations_widget, pnmpi_conf_widget)
    elif button == extern_type_selector_widget:
        display(num_processes_widget, num_runs_widget, num_iterations_widget, pnmpi_conf_widget, executable_widget, executable_args_widget)
    
num_processes_widget.observe(listen_processess, names='value')
num_runs_widget.observe(listen_runs, names='value')
num_iterations_widget.observe(listen_iterations, names='value')
pnmpi_conf_widget.observe(listen_pnmpi, names='value')
executable_widget.observe(listen_executable, names='value')
executable_args_widget.observe(listen_args, names='value')
output_dir_widget.observe(listen_output_dir, names='value')
image_path_widget.observe(listen_image_path, names='value')


trace_widget.on_click(on_button_clicked_0)
create_instance_widget.on_click(on_button_clicked_0)
kill_instance_widget.on_click(on_button_clicked_0)
gen_event_graph_widget.on_click(on_button_clicked_0)
slice_extraction_widget.on_click(on_button_clicked_0)
compute_kdts_widget.on_click(on_button_clicked_0)
create_visualization_widget.on_click(on_button_clicked_0)
display_visualization_widget.on_click(on_button_clicked_0)

benchmark_type_selector_widget.on_click(on_button_clicked_1)
extern_type_selector_widget.on_click(on_button_clicked_1)

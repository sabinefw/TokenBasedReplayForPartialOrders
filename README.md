# TokenBasedReplayForPartialOrders
Algorithm for exact Token-based Replay on partially ordered event logs in (concurrent) partial order semantics and workflow nets, including a fast variant calculating upper and lower fitness bounds. Submitted to ICPM 2025 / research track.

To reproduce the experimental results in the submitted paper, or to conduct own experiments, please use the script "ExperimentPartialOrderConFormanceAnalysis.py" in the folder source/experiments.

1.) Create and fill the folders data/nets, data/partially_ordered_logs and data/totally_ordered_logs with the corresponding data from the zip-files provided in this Github to reproduce the experiments in the paper. Note that the totally ordered logs, which are quite large in size, are not provided on this Github as they are publicly available. Please edit the file names of the actually used totally ordered event log files in the dictionary in lines 17-31 of the test script accordingly.

2.) Set the experiment configuration: <br>
    a.) In line 49, choose whether to conduct the experiment using partially or totally ordered event logs by setting the corresponding flag.   
    b.) In line 50, set the number of iterations. The experiments in the article were conducted with 100 iterations.

3.) Run the experiments.

4.) After running the experiments, find the results in the folder results. Within this folder, there are separate folders for the results on partially and totally ordered event logs.
    The names of the result files encode the involved data and the timestamp when the experiments were performed.
    We provide three different kind of result files:    
    a.) Conformance and performance on the global level of the event logs (saved in the folder general).    
    b.) Conformance on the level of single elements of the event logs (saved in the folder run-details).    
    c.) Statistics for the places in the nets that include the missing tokens there and how often in which step of the algorithm the place was analyzed (saved in the folder place-details).    

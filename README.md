# TokenBasedReplayForPartialOrders
Algorithm for exact Token-based Replay on partially ordered event logs in certain-true concurrent semantics and workflow nets, and a fast algorithm variant for calculating upper and lower fitness bounds. Submitted to CAiSE'26 (technical / technology oriented track).

To reproduce the experimental results in the paper, or to conduct own experiments, please use the script "ExperimentPartialOrderConFormanceAnalysis.py" in the folder source/experiments.

1.) Make sure that the folders data/nets, data/partially_ordered_logs, data/totally_ordered_logs, results/po/general, results/po/run-details and results/po/place-details exist in the source/experiments folder, and fill them with the data you want to conduct experiments on, e.g. the data provided in the zip-files provided in this Github repository to reproduce the experiments of the paper. Note that the totally ordered reference event logs are not provided on this Github as they are quite large in size and publicly available. If you use own data, please edit the file names of the actually used totally ordered event log files in the "ExperimentPartialOrderConFormanceAnalysis.py" test script (lines 17-31) accordingly.

2.) Set the experiment configuration: <br>
    a.) In line 49, choose to conduct the experiment using partially (or totally ordered) event logs by setting the corresponding flag to True (else False).   
    b.) In line 50, set the number of iterations. If you are just interested in the fitness values, one iteration is sufficent. If you are interested in runtime experiments, more iterations may be useful. The experiments in the article were conducted with 100 iterations.

3.) Run the experiments.

4.) After running the experiments, you will find the results in the folder results. Within this folder, there are separate folders for the results on partially and totally ordered event logs.
    The names of the result files encode the involved data and the timestamp when the experiments were performed.
    We provide three different kind of result files:    
    a.) Conformance and performance on the global level of the event logs (saved in the folder general).    
    b.) Conformance on the level of single elements of the event logs (saved in the folder run-details).    
    c.) Statistics for the places in the nets that include the missing tokens there and how often in which step of the algorithm the place was analyzed (saved in the folder place-details).    

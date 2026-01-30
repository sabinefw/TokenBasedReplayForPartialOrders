# TokenBasedReplayForPartialOrders
Algorithm for caluclating an exact fitness value using token-based replay on partially ordered event logs in certain-true concurrent semantics and workflow nets, and a fast algorithm variant for calculating upper and lower fitness bounds. Submitted to Petri Nets'26.

To reproduce the experimental results in the paper, or to conduct own experiments, please use the script "ExperimentPartialOrderConFormanceAnalysis.py" in the folder source/experiments.

1.) Create the folders (or verify that they exist) data/nets, data/partially_ordered_logs, results/po/general, results/po/run-details and results/po/place-details in the source/experiments folder. Fill them with the data you want to conduct experiments on, e.g. the data provided in the zip-files in this Github repository to reproduce the experiments of the paper. Note that the totally ordered reference event logs are not provided on this Github as they are quite large in size and publicly available. Edit the file names of the actually used totally ordered event log files in the "ExperimentPartialOrderConFormanceAnalysis.py" test script (lines 24 ff.) accordingly.

2.) Set the experiment configuration (if required): <br>
    a.) In line 18, set the number of iterations (number_tests_per_pair). If you are just interested in the fitness values, one iteration is sufficent. If you are interested in runtime experiments, more iterations may be useful. The experiments in the article were conducted with 100 iterations.
    (If you would like to use the algorithms as classic token-based replay algorithms to conduct experiments on totally ordered event logs, set the "is_experiment_with_po" flag to False.)   

3.) Run the experiments.

4.) After running the experiments, you will find the results in the folder results. Within this folder, there are separate folders for the results on partially and totally ordered event logs.
    The names of the result files encode the involved data and the timestamp when the experiments were performed.
    We provide three different kind of result files:    
    a.) Conformance and performance on the global level of the event logs (saved in the folder general).    
    b.) Conformance on the level of single elements of the event logs (saved in the folder run-details).    
    c.) Statistics for the places in the nets that include the missing tokens there and how often in which step of the algorithm the place was analyzed (saved in the folder place-details).    

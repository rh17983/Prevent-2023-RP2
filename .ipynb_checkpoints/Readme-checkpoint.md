# Document structure

 - Introduction
 - Terminology
 - Data set naming conventions
 - Artefact structure
 - Prerequisites
 - Environment Setup
 - Running Experiments
 - References


# Introduction
---

This artefact includes:

1. **A large data set of KPIs** (values of metrics collected from different nodes) that we obtained by running a large set of experiments on [**REDIS**](https://redis.io/), a commercially compliant, distributed cloud system.
2. **The results of experimenting with Prevent, Premise [1], and Loud [2]**, three tools for predicting and localizing failures in multi-tier distributed systems, to comparatively evaluate their performance to predict and localize failures in dynamic systems.
3. **The toolset to execute Prevent, Premise [1], and Loud [2]** to replicate our results (point 2 above) based on the provided datasets of KPIs (point 1 above).

**Prevent** combines two approaches, **PREVENT-A** and **PREVENT-E**, that offer implementations of state classifiers to predict failures, both integrated with the same anomaly ranker to localize faults. 

The experiments compare:

* **Prevent** with **Premise** in terms of

    * **stability**: rate of predictions between the ﬁrst valid prediction and the system crash 
    * **reliability**: rate of predictions before the injection of the failure  
    * **earliness**: time interval between the ﬁrst valid prediction and the system crash 

* **Prevent** with **Loud** in terms of false-positive rate


# Terminology
---

* **KPI**: Key Performance Indicators, values of the metrics collected at the cluster nodes.
* **State Classifier**: the component of Prevent that predicts failures based on the analysis of the KPIs.
* **Anomaly Ranker**: the component of Prevent and Loud that locates the sources of the failure propagation by statistically testing the relations between the KPIs.
* **Deep Autoencoder**: the sub-component of Prevent State Classifier and a sub-component of Anomaly Ranker that detects anomalous KPIs (concerning the observations in the training phase) in the observed data.
* **Granger Causality Analyzer**: the sub-component of the Anomaly Ranker that conducts a Granger Causality analysis of the anomalous KPIs.
* **Master-slave pair**: a pair of master-slave nodes of the target application (Redis cluster). In our experiments, we used a cluster consisting of 10 master-slave pairs.


# Data set naming conventions
---

The datasets containing KPIs collected during executions with seeded failures, along with all their associated data (anomalies, predictions, localizations), follow a specific naming convention: {failure type}-{replica number}.

The "failure type" can be one of the following:

* cpu-stress (for CPU stress)
* mem-leak (for memory leak)
* pack-corr (for network packet corruption)
* pack-delay (for network packet delay)
* pack-loss (for network packet loss)

The "replica number" ranges from 0 to 2, as each experiment was replicated thrice.

The datasets collected during normal, fault-free executions, along with all their associated data, are named as follows:
* normal_1_14: This dataset comprises data collected over two weeks of normal execution and is utilized for training and validating the Prevent State Classifier's models.
* fpr-validation: This dataset is gathered during a third week of normal execution and serves the purpose of evaluating the false positive rate of the Prevent and Loud approaches.


# Artifact structure
---

* AnomalyRanker: this folder contains the Anomaly Ranker server scripts
* Prevent-E: this folder contains the Prevent-E State Classifier scripts, including training and evaluating the Prevent-E's RBM model and making predictions
* resources: this folder contains the input and output data
* prevent_a.ipynb: this notebook contains a comprehensive set of scripts that cover various tasks, including training and evaluating the Prevent-A's Deep Autoencoder model, detecting anomalies, making predictions, and handling the client-side interaction with the Anomaly Ranker. The client side of the Anomaly Ranker is responsible for sending detected anomalies to the Anomaly Ranker server and receiving localization information in return.
* premise.ipynb: this notebook contains a set of scripts that include training Premise's Logistic Model Tree model, making predictions and localizations
* results.ipynb: this notebook contains the script which visualizes the combination of the Prevent State Classifier predictions and the Prevent Anomaly Ranker localizations, visualizes the predictions and localizations of Premise, and calculates the false positive rate of Prevent and Loud on a normal data
* requirements.txt file: the set of the Python packages to install in the Python virtual environment 


## Data files in the "resources" folder:

 - datasets/

    This folder houses the **Raw Data** and **Preprocessed Data** collected during normal executions, which are conducted without any injected faults. Additionally, it contains data collected during executions with various types of failures, including CPU Stress, Memory Leak, Network Packet Corruption, Network Packet Delay, and Network Packet Loss. These failures were introduced with a fixed injection intensity rate and a frequency of one sample per minute, extending up to a system disruption.

    The folders follow a naming pattern of {data set code}-{suffix}. The "data set code" adheres to the {failure type}-{replica number} pattern for datasets with seeded failures, while it is either "normal_1_14" or "fpr-validation" for normal data (as explained in the Data set naming conventions section).

    The "suffix" value can take one of the following options:
    
     * "consolidated": These datasets contain the **Raw Data**.
     * "tuned": These datasets contain the **Preprocessed Data**, which is employed for training and evaluating the Prevent-A, Premise, and LOUD models.
     * "rbm": These datasets contain the **Preprocessed Data**, which is identical to the one found in the corresponding folders with the "tuned" suffix, but they include an additional column (timestamp). This data format is utilized for training and evaluating the Prevent-E State Classifier.


 - anomalies/
 
    This folder contains the sets of **Anomalous KPIs**, with their anomaly scores (the value of the reconstruction error done by the Deep Autoencoder model), detected by the Deep Autoencoder model for each timestamp on **Preprocessed Data**.

    The data in these .json files are formatted as JSON records, with each record consisting of the following fields:
> * timestamp - timestamp of the observation (date/time in Unix format)
> * resource - the node of the cluster
> * metric - metric name
> * value - reconstruction error of the KPI


 - predictions-a/
 
    This folder contains the **Prevent-A Classifier predictions** - the classifications made on Preprocessed Data.
    The .csv files report the predictions at each timestamp, where 0 means normal state and 1 indicates failure alert.
 

 - predictions-e/
 
    This folder contains the **Prevent-E Classifier predictions** - the classifications made on Preprocessed Data.
    The .csv files report the predictions at each timestamp, where 0 means normal state and 1 indicates failure alert.


 - predictions-p/
 
    This folder contains the **Premise Predictions and Localizations** - the classifications and localizations made on Preprocessed Data (utilizing the detected anomalies as an input).
    The .csv files report the predictions at each timestamp, where 0 means normal state, 1 indicates failure alert with incorrect localization, and 2 indicates failure alert with correct localization.


 - localisations/
 
    This folder contains the **Anomaly Ranker Localizations** made on Preprocessed Data (utilizing the detected anomalies as an input).
    The rows of the .csv files correspond to the localization provided by the Anomaly Ranker at a timestamp.

    The descriptions of the columns of the datasets:

> * the minute of the experiment (starts from 0)
> * the node localized as faulty (the first node in the ranking). This cell is empty if the number of anomalous metrics of the node that occurs first in the ranking is equal to the number of anomalous metrics of the node that occurs second (and/or third).
> * the first node in the ranking
> * the number of anomalous metrics of the node that occurs first in the ranking
> * the second node in the ranking
> * the number of anomalous metrics of the node that occurs second in the ranking
> * and so forth


 - GC-Graphs/
 
    This folder contains the Granger Causality graph files.


 - features/

    This folder contains the .csv files with the set of KPIs before and after the data engineering phase.


 - bams/
 
    This folder contains the **Binary Anomaly Matrixes**, the data structures representing the sets of anomalous KPIs, detected by the Deep Autoencoder model for each timestamp on the Preprocessed Data. The binary values of the data set indicate the anomality of the KPI at the timestamp (0 - not anomalous, 1 - anomalous).


 - bams_shuffled/

    This folder contains the **Shuffled Binary Anomaly Matrixes** - the same (see the previous point) binary anomaly matrixes with the anomalous values shuffled among all ten node master-slave pairs of the cluster. It represents a synthetic sequence of anomalous KPIs that we derived by replicating and grouping anomalies from the **anomalies** folder. We use these sequences for training and testing Premise.


# Prerequisites
---

## Machine configuration we used in our experiments with Prevent-A and Premise
 - Type: Google Cloud VM instance e2-standard-4
 - OS: Ubuntu 20.04 LTS. x86/64, amd64 focal image built on 2023-06-16, supports Shielded VM features
 - Processor: 2 vCPU
 - Memory: 4GB
 - Disc space: 30GB
 - Software packages:
     - Python 3.8.10
 
## Machine configuration we used in our experiments with Prevent-E
 - OS: MacOS Catalina
 - Processor: 2.2 GHz 6-Core Intel Core i7
 - Memory: 16 GB 2400 MHz DDR4
 - Software packages
     - Matlab 2020b


# Environment Setup
---

## Setup Prevent-A and Premise

1. Copy the "AnomalyRanker" and the "resources" folders and the requirements.txt, prevent_a.ipynb, premise.ipynb, and results.ipynb files to your computer

2. Go to the folder you copied the documents to (we will call it the root folder).

3. Update the package manager
```
sudo apt update
```

4. Make python3 default
```
nano ~/.bashrc
add the string and save/close: alias python=python3
source ~/.bashrc
```

5. Install pip for python3
```
sudo apt install python3-pip
```

6. Upgrade pip
```
python -m pip install --upgrade pip
```

7. Check the version of Python (we used version 3.8.10)
```
python --version
```

8. Check the version of pip (we used the version 20.0.2)
```
pip --version
```

9. Install screen tool
```
sudo apt install screen
```

10. Install python virtual environment
```
sudo apt install python3.8-venv
```

11. Install git
```
sudo apt install git
```

12. Install Jupyter Lab
```
pip3 install jupyterlab
```

13. Go to the Anomaly Ranker folder
```
cd AnomalyRanker
```

14. Create a virtual environment for the Anomaly Ranker
```
python -m venv venv
```

15. Activate the virtual environment of the Anomaly Ranker
```
source venv/bin/activate
```

16. Install python packages for the Anomaly Ranker
```
python -m pip install -r requirements.txt
```

17. Go to the root folder
```
cd ..
```

18. Create a new (option: -S) or enter to the existing (option: -r) screen for Prevent-A and Premise
```
screen {option} prevent
```

19. Create a virtual environment for Prevent-A and Premise
```
python -m venv venv
```

20. Activate the virtual environment for Prevent-A and Premise
```
source venv/bin/activate
```

21. Install Java
```
sudo apt install default-jre
sudo apt install default-jdk
```

22. Install the python-javabridge package
```
pip3 install git+https://github.com/LeeKamentsky/python-javabridge.git

Expected result: Successfully installed javabridge-1.0.19
```

23. Install python packages for Prevent-A and Premise
```
python -m pip install -r requirements.txt
```

24. Install jupyter kernel
```
python -m ipykernel install --user --name=Kernel-prevent-23
```

25. Add the path of the jupyterlab (alternative way: log out/in)
```
PATH="$PATH:$HOME/.local/bin/"
```

26. Start Jupiter Lab (copy the auth token from the Jupiter Lab start command output in the console)
```
jupyter lab --port 5601 --ip 0.0.0.0
```

27. Exit the screen
```
CTRL + A + D
```


## Setup Prevent-E

1. Download the Matlab 2020b from https://mathworks.com/downloads/
2. Install the Matlab 2020b on your computer
3. Copy the "Prevent-E" and the "resources" folders to your computer


# Running Experiments
---


## Preprocess the raw data

1. Open the Jupiter Lab instance in your browser
```
URL: {machine IP adress}:5601
```

> **_NOTE:_** Your firewall must allow inbound connections on this port

> **_NOTE:_** Use the Kernel-prevent-23 kernel for all notebooks

> **_NOTE:_** You might have to enter the token copied from the Jupiter Lab start command output in the console


2. Run all in the dataset_tune.ipynb notebook
```

Purpose: Preprocessing the raw data

input: **Raw Data**
output: **Preprocessed Data**
```

## Get the Prevent-E predictions

> **_NOTE:_**  If you run the Matlab on a separate machine, then, before the execution of the Matlab's Main.m script, move the files of the Preprocessed Data (the dataset folders with the suffix _rbm, see detail in the "Data files in the "resources" folder" section) to the resources/datasets folder from the same folder of the machine you have run the data preproccessing script (the dataset_tune.ipynb notebook).

> **_NOTE:_**  If you run the Matlab on a separate machine, then, after the execution of the Matlab's Main.m script, move the results files from the resources/predictions-e folder to the same folder of the machine you run the results.ipynb notebook.

1. Start Matlab
2. Go to the "Prevent-E" folder in the Matlab's UI
3. Run Main.m script

```
Sub-scripts: 


1. Training the Prevent-E RBM model

Input data:

- The **Preprocessed Data** collected during the two weeks of normal execution.
Location: resources/datasets/normal_1_14_rbm

output data: --


2. Making predictions on the data, collected during the one week of normal execution.

Input data:

- The **Preprocessed Data** collected during the one week of normal execution. 
Location: resources/datasets/fpr-validation_rbm

Output data:

- **Prevent-E Classifier predictions**
Location: resources/predictions-e/fpr-validation.csv


3. Making predictions on the experimental data, collected during the execution with seeded faults.

Input data:

- The **Preprocessed Data** collected during the execution with seeded faults.
Location:  resources/datasets/{failure type}-{replica number}_rbm folders, where the "failure type" value is amoung the cpu-stress, mem-leak, pack-corr, pack-delay, and pack-loss, and the "replica number" ranges from 0 to 2.

Output data:

- **Prevent-E Classifier predictions**
Location: resources/predictions-e folder

```


## Start the Anomaly Ranker server

> **_NOTE:_**  Run the Anomaly Ranker server on the same machine you run the jupyter lab

1. Go to the Anomaly Ranker folder
```
cd AnomalyRanker
```

2. Create a new (option: -S) or enter to the existing (option: -r) Anomaly Ranker screen
```
screen {option} prevent_anomaly_ranker
```

3. Activate the virtual environment for the Anomaly Ranker
```
source venv/bin/activate
```

4. Start the Anomaly Ranker server
```
python ranker_app.py 5006
```

5. Exit from the Anomaly Ranker screen
```
CTRL + A + D
```


## Get the Prevent-A predictions, Prevent-A & Prevent-E localizations, Premise predictions and localizations, final results and create vizualizations

1. Open the Jupiter Lab instance in your browser
```
URL: {machine IP adress}:5601
```

> **_NOTE:_** Your firewall must allow inbound connections on this port

> **_NOTE:_** Use the Kernel-prevent-23 kernel for all notebooks

> **_NOTE:_** You might have to enter the token copied from the Jupiter Lab start command output in the console


2. Run all in the prevent_a.ipynb notebook
```
Sub-scripts: 


1. Training the Prevent-A Deep Autoencoder model

Input data: The **Preprocessed Data** collected during the two weeks of normal execution.
Location: resources/datasets/normal_1_14_tuned

output data: --


2. Making Prevent-A predictions on the experimental data, collected during the one week of normal execution.

Input data:

- The **Preprocessed Data** collected during the one week of normal execution.
Location: resources/datasets/fpr-validation_tuned

Output data:

- **Prevent-A Classifier predictions**.
Location: resources/predictions-a/fpr-validation.csv


3. Making Prevent-A predictions on the experimental data, collected during the execution with seeded faults.

Input data:

- The **Preprocessed Data** collected during the execution with seeded faults.
Location:  resources/datasets/{failure type}-{replica number}_tuned folders, where the "failure type" value is among the cpu-stress, mem-leak, pack-corr, pack-delay, and pack-loss, and the "replica number" ranges from 0 to 2.

Output data:

- **Prevent-A Classifier predictions**.
Location: resources/predictions-a folder

 
4. Detection of the anomalous KPIs

Input data:

- The **Preprocessed Data** collected during the one week of normal execution.
Location: resources/datasets/fpr-validation_tuned

- The **Preprocessed Data** collected during the execution with seeded faults.
Location: the resources/datasets/{failure type}-{replica number}_tuned folders, where the "failure type" value is among the cpu-stress, mem-leak, pack-corr, pack-delay, and pack-loss, and the "replica number" ranges from 0 to 2

Output data:

- The **Anomalous KPIs**.
Location: resources/anomalies folder.


5. Localization of the failures by requesting the Anomaly Ranker server

Input data:

- **Anomalous KPIs**. 
Location: resources/anomalies folder.

Output data:

- **Anomaly Ranker Localizations**.
Location: resources/localisations folder.


6. Creation of The Shuffled Binary Anomaly Matrixes for the experimental data sets with seeded failures. Represent sets of the anomalous KPIs in the format required by the Premise. Used as an input for Premise.

Input data:

- The **Preprocessed Data** collected during the execution with seeded faults.
Location: the resources/datasets/{failure type}-{replica number}_tuned folders, where the "failure type" value is among the cpu-stress, mem-leak, pack-corr, pack-delay, and pack-loss, and the "replica number" ranges from 0 to 2

Output data: 

- The **Shuffled Binary Anomaly Matrixes**.
Location: resources/bams_shuffled

```

3. Run all in the premise.ipynb notebook
```
Sub-scripts: 

1. Training the Premise Logistic Model Tree model

Input: **Shuffled Binary Anomaly Matrixes**
Location: resources/bams_shuffled

Output: --


2. Making Premise Predictions and Localizations

Input: **Shuffled Binary Anomaly Matrixes**
Location: resources/bams_shuffled

Output: **Premise Predictions and Localizations**.
Location: resources/predictions-p
```

4. Run all in the results.ipynb notebook
```
Sub-scripts:

- Analysis and visualization of the prediction and localization results of Prevent-A, Prevent-E and Premise on the experimental data sets with seeded faults
- Calculation of the false positive rate of the Prevent-A, Prevent-E, and Loud on a one-week normal data

Input:

- **Prevent-A Classifier predictions** on a one-week normal data.
Location: resources/predictions-a/fpr-validation.csv

- **Prevent-A Classifier predictions** on experimental data sets with seeded failures.
Location: resources/predictions-a folder

- **Prevent-E Classifier predictions** on a one-week normal data.
Location: resources/predictions-e/fpr-validation.csv

- **Prevent-E Classifier predictions** on experimental data sets with seeded failures.
Location: resources/predictions-e folder

- **Premise Predictions and Localizations**
Location: resources/predictions-p folder

- **Anomaly Ranker localizations**
Location: resources/localisations folder.

Output:

- Visualization of the prediction and localisation of Prevent-A, Prevent-E, and Premise on the experimental data sets with seeded faults
- Calculation of the false positive rate of the Prevent-A, Prevent-E, and Loud on a one-week normal data

```


#  References
---

[1] Leonardo Mariani, Mauro Pezzè, Oliviero Riganelli, and Rui Xin. Predicting failures in multi-tier distributed systems. Journal of Systems and Software, 161, 2020. URL: https://star.inf.usi.ch/media/papers/2020-jss-mariani-premise.pdf

[2] Leonardo Mariani, Cristina Monni, Mauro Pezzè, Oliviero Riganelli, and Rui Xin. Localizing faults in cloud systems. In Proceedings of the International Conference on Software Testing, Veriﬁcation and Validation, ICST '18, pages 262–273. IEEE Computer Society, 2018. URL: https://star.inf.usi.ch/media/papers/2018-icst-mariani-load.pdfv
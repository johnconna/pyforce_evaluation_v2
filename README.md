# pyforce_evaluation
## 0x00 Introduction
This is a project build for ez evaluate PYPI detecting frameworks; Integrated OSSF/Bandit4mal&EA4MP.
Also the project add so many auto & batch optimize scripts
## 0x01 Overview
### 1.Fetch_benign_packages
This project is designed to fetch benign packages from famous.csv
Also can extract packages easily
### 2.Preprocess_packages
We found that the suffix of the file isn't 100% match with the real file,
So we statistic all the package MAGIC,and provide a rename script according to MAGIC
Also for Bandit4mal, It needs decompressed packages.
Thus we provide the script.
### 3.Bandit4mal
Bandit4mal is OK,but in our practice.
It best to using pip installed bandit4mal rather than project from github.
The json output results is hard to process.
Also we provide process scripts to extract the core infos
### 4.OSSF-Packages
OSSF is ez to deploy, but u may need proxy to have better network(Ignore if you don't need proxy:)
But the analysis container seems have some problem, so it's difficult to paraelle, thus we provide a serial_batch script
Also OSSF only provide malious metrics, so our idea is give prompt & OSSF_analysis_results.json to LLM
We also provide this script.
### 5.EA4MP
EA4MP is hard to reproduce by origional scripts, Eg:
Lack of initial env;
import use the absolute path,so there are conutless import errors;
Metadata may not fetch from remote.
So we rebuild the project follow it's idea:
Using ML-models to judge metadata;
Using fine-tuned BERT to judge sequence;
And finally using Adaboost or share-same-weight to judge

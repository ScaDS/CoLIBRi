# CoLIBRi

Supporting quotation through multi-modal retrieval and conversational search on technical drawings. 


## Technical Specifications and Installation

* Requirements:
  * Docker installation
  * GPU that supports CUDA (11.8), ~10+ GB of VRAM
  * Make sure you firewall does not block the ports if you want to access the CoLIBRi from a remote location:
    * 5201: Frontend
    * 6201: Preprocessor
    * 7201: Database
    * 9201: LLM backend (conv-search)
* Our Specs:
  * Ubuntu 22.04.4 LTS
  * Nvidia 1080ti, driver version 535.161.08
* To run the applicaton: run ```docker compose up -d``` in the CoLIBRi directory
  * Frontend will be hosted on ```localhost:5201```
  * If you want to update the Database, see the tools section below

## Components

### Database Service

* ToDo

### Frontend Service

* ToDo

### Preprocessor Service

* ToDo


### Conversational Search

* ToDo


## Additional Tools

### Initial Database Population

The database uses a .csv file to initially read the dataset for the search. You can either generate this file yourself, 
or generate it using the corresponding tool. For this run ````./tools/generate_database_examples.py````. If you run from
command line, you can either parse the directory with the dataset and the output directory like this:
```
python3 generate_database_examples.py dataset_dir output_dir
```
Otherwise, you can change the values at the bottom of the python file.

### Drawing Generator

This Generator was used to generate drawings for OCR training. You can find all the files in ```./tools/data_generator```.
To use it, first make sure you have all the additional files required for the generation. This includes:
 * A dictionary containing all of the words that the generator picks from
 * A list of norms that the generator picks from
 * A list of materials that the generator picks from
 * A dataset of 3D models that the generator can use. We used the [MCB](https://github.com/stnoah1/mcb) dataset for this
Change the corresponding paths at the bottom of the python file or run it using the command line.

### Benchmarks

The benchmark scripts we used for our paper are provided in ```./tools/benchmarks```.
 * ```benchmark_preprocessor.ipynb```: notebook for getting the corresponding responses from the preprocessor for a given set of drawings
 * ```evaluate_preprocessor_result.ipynb```: evaluate those reponses 
 * ```benchmark_vlm.ipynb```: run the feature extraction on a set of drawings using a VLM
 * ```evaluate_vlm_results.ipynb``` evaluate the VLM responses
 * ...
 * Other Results were generated using tools from other repos:
   * Table I uses PaddleOCR's inbuilt eval tool
   * Table III uses eDOCr2 eval tool
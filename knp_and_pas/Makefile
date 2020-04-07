TARGET :=
GPUS := 0,1

INPUT_DIR := /mnt/hinoki/murawaki/covid19

PYTHON := nice -19 $(shell which python)
BERTKNP_DIR := /mnt/berry/home/ueda/bertknp-0.2-20190901
PYTHON_FOR_BERTKNP := $(BERTKNP_DIR)/.venv/bin/python
PAS_ANALYSIS_DIR := /mnt/berry/home/ueda/work/bert_pas_analysis
PYTHON_FOR_PAS := /mnt/berry_f/home/ueda/.virtualenvs/bert_pas_analysis-i-v_TqeF/bin/python
KNP := /mnt/orange/brew/data/bin/knp
PAS_MODEL_FILE := /mnt/hinoki/ueda/bert/pas_analysis/result/best/model_best.pth
HERE := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))

# ゆくゆくは複数ファイルを扱えるようにする
#SRC_JSONL_FILES := $(shell find $(INPUT_DIR) -name *.output.jsonl)
SRC_JSONL_FILE := $(INPUT_DIR)/$(TARGET).output.jsonl
OUTPUT_BASE_DIR := /mnt/hinoki/ueda/covid19/causalitygraph
TSV_FILE := $(OUTPUT_BASE_DIR)/tsv/$(TARGET).tsv
KNP_FILE := $(OUTPUT_BASE_DIR)/knp/$(TARGET).knp
KNP_DIR := $(OUTPUT_BASE_DIR)/knp/$(TARGET)
SPLIT_KNP_DONE := $(OUTPUT_BASE_DIR)/knp/$(TARGET).done
PAS_DONE := $(OUTPUT_BASE_DIR)/pas/$(TARGET).done
PAS_DIR := $(OUTPUT_BASE_DIR)/pas/$(TARGET)
TGT_JSONL_FILE := $(OUTPUT_BASE_DIR)/json/$(TARGET).jsonl

all: $(TGT_JSONL_FILE)

# edit json file
$(TGT_JSONL_FILE): $(TSV_FILE) $(PAS_DONE)
	cat $< | $(PYTHON) $(HERE)knp2json.py --pas-dir $(PAS_DIR) --skipped-file $(dir $@)skipped.$(TARGET).txt > $@ || rm -f $@

# perform PAS analysis
$(PAS_DONE): $(SPLIT_KNP_DONE)
	$(PYTHON_FOR_PAS) $(PAS_ANALYSIS_DIR)/src/inference.py -r $(PAS_MODEL_FILE) --knp-dir $(KNP_DIR) --export-dir $(PAS_DIR) --use-bertknp -d $(GPUS) > $(dir $(PAS_DONE))$(TARGET)_tree.txt && touch $@

# split KNP file into documents for PAS analysis
$(SPLIT_KNP_DONE): $(KNP_FILE) $(TSV_FILE)
	$(PYTHON) $(HERE)split_knp.py --knp-file $(KNP_FILE) --tsv-file $(TSV_FILE) --output-dir $(KNP_DIR) && touch $@

# apply BERTKNP
$(KNP_FILE): $(TSV_FILE)
	mkdir -p $(dir $@)
	cut -f3 $< | env PERL5LIB=/home/ueda/usr/lib/perl5/site_perl/5.26.2 CUDA_VISIBLE_DEVICES=$(GPUS) $(BERTKNP_DIR)/bin/bertknp -j -p $(PYTHON_FOR_BERTKNP) -k $(KNP) > $@ || rm -f $@

# extract S-ID and sentences from json file and convert to tsv
$(TSV_FILE): $(SRC_JSONL_FILE)
	mkdir -p $(dir $@)
	cat $< | $(PYTHON) $(HERE)preprocess_json.py > $@ || rm -f $@
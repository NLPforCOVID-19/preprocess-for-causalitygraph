MAKEFILE_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))

PYTHON := python3
DATE := 20191228
BASE_DIR := /share/tool/causalgraph/fuman
INPUT_EVENT_FILES_TOP_DIR := $(BASE_DIR)/event_pairs/$(DATE)
OUT_CLUSTERING_FILES_TOP_DIR := $(BASE_DIR)/clustering/$(DATE)

INPUT_EVENT_FILES := $(shell find -L $(INPUT_EVENT_FILES_TOP_DIR) -maxdepth 1 -type f -name '*.event_pairs.json' -size +1c)
OUT_CLUSTERING_FILES := $(patsubst $(INPUT_EVENT_FILES_TOP_DIR)/%.event_pairs.json, $(OUT_CLUSTERING_FILES_TOP_DIR)/%.done, $(INPUT_EVENT_FILES))

NICE := nice -19

all: $(OUT_CLUSTERING_FILES)

$(OUT_CLUSTERING_FILES): $(OUT_CLUSTERING_FILES_TOP_DIR)/%.done: $(INPUT_EVENT_FILES_TOP_DIR)/%.event_pairs.json
	mkdir -p $(dir $@) && \
	$(NICE) $(PYTHON) $(MAKEFILE_DIR)/clustering.py --event_path $(INPUT_EVENT_FILES_TOP_DIR) --out_path $(OUT_CLUSTERING_FILES_TOP_DIR) --keywords $(notdir $(subst .done,,$@)) && \
	touch $@

clean:
	rm -f $(OUT_CLUSTERING_FILES)

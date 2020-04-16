MAKEFILE_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))

PYTHON := python3
DATE := 20191228
BASE_DIR := /share/tool/causalgraph/fuman
INPUT_JSON_FILES_TOP_DIR := $(BASE_DIR)/data/$(DATE)
OUT_EVENT_FILES_TOP_DIR := $(BASE_DIR)/event_pairs/$(DATE)
TMP_DIR := /data/$(USER)
TMP_BASE_DIR := $(TMP_DIR)/event_pairs.$(DATE)

GZIP_EXT := xz
INPUT_JSON_FILES := $(shell find -L $(INPUT_JSON_FILES_TOP_DIR) -type f -name '*.jsonl.$(GZIP_EXT)')
OUT_EVENT_FILES := $(patsubst $(INPUT_JSON_FILES_TOP_DIR)/%.jsonl.$(GZIP_EXT), $(OUT_EVENT_FILES_TOP_DIR)/%.event_pairs.json, $(INPUT_JSON_FILES))

NICE := nice -19

all: $(OUT_EVENT_FILES)

$(OUT_EVENT_FILES): $(OUT_EVENT_FILES_TOP_DIR)/%.event_pairs.json: $(INPUT_JSON_FILES_TOP_DIR)/%.jsonl.$(GZIP_EXT)
	mkdir -p $(dir $@) $(TMP_BASE_DIR) && \
	if [ -d "$(subst .event_pairs.json,,$@).svg" ]; then mv $(subst .event_pairs.json,,$@).svg $(TMP_BASE_DIR)/$(notdir $(subst .event_pairs.json,,$@).svg); fi && \
	if [ -d "$(subst .event_pairs.json,,$@).detail.svg" ]; then mv $(subst .event_pairs.json,,$@).detail.svg $(TMP_BASE_DIR)/$(notdir $(subst .event_pairs.json,,$@).detail.svg); fi && \
	$(NICE) $(PYTHON) $(MAKEFILE_DIR)/json2event.py --json_file $< --svg_dir $(TMP_BASE_DIR)/$(notdir $(subst .event_pairs.json,,$@).svg) --svg_detail_dir $(TMP_BASE_DIR)/$(notdir $(subst .event_pairs.json,,$@).detail.svg) > $@ && \
	mv $(TMP_BASE_DIR)/$(notdir $(subst .event_pairs.json,,$@).svg) $(subst .event_pairs.json,,$@).svg && \
	mv $(TMP_BASE_DIR)/$(notdir $(subst .event_pairs.json,,$@).detail.svg) $(subst .event_pairs.json,,$@).detail.svg

clean:
	rm -f $(OUT_EVENT_FILES)

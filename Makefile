TARGET :=
GPUS := 0,1

INPUT_DIR := /mnt/hinoki/murawaki/covid19

export PYTHON := nice -19 $(shell which python)

OUTPUT_BASE_DIR := /mnt/hinoki/ueda/covid19/causalitygraph
SRC_JSONL_FILE := $(INPUT_DIR)/$(TARGET).output.jsonl
TGT_JSONL_FILE := $(OUTPUT_BASE_DIR)/json/$(TARGET).jsonl

.PHONY: all
all: $(TGT_JSONL_FILE)

#water.event_pairs.json: $(JSONL)

$(TGT_JSONL_FILE): $(SRC_JSONL_FILE)
	$(MAKE) -f knp_and_pas/Makefile GPUS=$(GPUS) TARGET=$(TARGET)

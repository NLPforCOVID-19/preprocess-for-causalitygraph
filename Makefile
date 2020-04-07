TARGET :=
INPUT_DIR := /mnt/hinoki/murawaki/covid19

SRC_JSONL_FILE := $(INPUT_DIR)/$(TARGET).output.jsonl
JSONL := $(TARGET).jsonl

.PHONY: all
all:

water.event_pairs.json: $(JSONL)

$(JSONL): $(SRC_JSONL_FILE)
	$(MAKE) -f knp_and_pas/Makefile $@

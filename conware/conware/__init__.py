RECORDING_EXTENSION = "tsv"
MODEL_FILE = "model.pickle"
INTERRUPT_MAP = "interrupt_map.pickle"
MODEL_FILE_OPTIMIZED = "model_optimized.pickle"
COVERAGE_LOG = None
MEM_LOG = None
MODEL = None
OUTPUT_TSV = None


class Operation:
    READ = 0
    WRITE = 1
    INTERRUPT = 2

"""Small domain-error vocabulary for the future ingestion orchestrator."""


class ScientificIngestionError(RuntimeError):
    """Base error with a stable machine-readable category."""

    code = "scientific_ingestion_error"


class ScientificAcquisitionError(ScientificIngestionError):
    """The source release or one of its raw artifacts could not be acquired."""

    code = "scientific_acquisition_error"


class ScientificParserError(ScientificIngestionError):
    """An artifact could not be parsed as a source dataset."""

    code = "scientific_parser_error"


class ScientificRecordValidationError(ScientificIngestionError):
    """One source record failed source-agnostic contract validation."""

    code = "scientific_record_validation_error"


class ScientificPersistenceConflict(ScientificIngestionError):
    """Future persistence detected an idempotency or identity conflict."""

    code = "scientific_persistence_conflict"

"""Mapping configuration API routes.

Provides CRUD endpoints for field-level redaction mappings, a validation
endpoint for checking mappings against sample records, a preview endpoint
for visualising redaction results, and a sample endpoint for reading the
first record from a local file.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Response
from fastapi.responses import JSONResponse

from cecil.api.schemas import (
    ErrorResponse,
    FieldMappingEntrySchema,
    FieldPreviewEntry,
    FieldPreviewRequest,
    FieldPreviewResponse,
    LoadMappingYamlRequest,
    MappingConfigRequest,
    MappingConfigResponse,
    MappingValidationRequest,
    MappingValidationResponse,
    RedactionActionSchema,
    SampleRecordRequest,
    SampleRecordResponse,
)
from cecil.core.providers.local_file import LocalFileProvider
from cecil.core.sanitizer.actions import apply_action
from cecil.core.sanitizer.mapping import MappingParser, validate_mapping_against_record
from cecil.core.sanitizer.models import (
    MappingConfig,
    RedactionAction,
)
from cecil.utils.errors import CecilError


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/mappings", tags=["mappings"])

# Maximum length for string values returned in sample/preview responses.
_MAX_SAFE_PIPE_VALUE_LENGTH = 200


@dataclass
class MappingState:
    """Mutable mapping state stored in the in-memory mapping store.

    Attributes:
        mapping_id: Unique identifier for the mapping.
        config: The validated domain MappingConfig.
        created_at: Timestamp when the mapping was created.
    """

    mapping_id: str
    config: MappingConfig
    created_at: datetime


# In-memory mapping store keyed by mapping_id.
_mapping_store: dict[str, MappingState] = {}


def _truncate(value: str, max_length: int = _MAX_SAFE_PIPE_VALUE_LENGTH) -> str:
    """Truncate a string to the given maximum length.

    Args:
        value: The string to truncate.
        max_length: Maximum allowed length.

    Returns:
        The original string if within limits, otherwise truncated.
    """
    if len(value) <= max_length:
        return value
    return value[:max_length]


def _request_to_domain_config(request: MappingConfigRequest) -> MappingConfig:
    """Convert an API request to a domain MappingConfig via MappingParser.

    Args:
        request: The API mapping configuration request.

    Returns:
        A validated MappingConfig domain object.

    Raises:
        MappingValidationError: If the mapping data is invalid.
    """
    raw: dict[str, Any] = {
        "version": request.version,
        "default_action": request.default_action.value,
        "fields": {
            name: {"action": entry.action.value, **entry.options}
            for name, entry in request.fields.items()
        },
    }
    return MappingParser().parse_dict(raw)


def _config_to_response(
    mapping_id: str,
    config: MappingConfig,
    created_at: datetime,
) -> MappingConfigResponse:
    """Convert a domain MappingConfig to an API response.

    Args:
        mapping_id: The unique mapping identifier.
        config: The domain MappingConfig.
        created_at: When the mapping was created.

    Returns:
        A MappingConfigResponse suitable for API serialization.
    """
    fields: dict[str, FieldMappingEntrySchema] = {}
    for name, entry in config.fields.items():
        fields[name] = FieldMappingEntrySchema(
            action=RedactionActionSchema(entry.action.value),
            options={k: str(v) for k, v in entry.options.items()},
        )

    return MappingConfigResponse(
        mapping_id=mapping_id,
        version=config.version,
        default_action=RedactionActionSchema(config.default_action.value),
        fields=fields,
        policy_hash=config.policy_hash(),
        created_at=created_at,
    )


def _schema_action_to_domain(action: RedactionActionSchema) -> RedactionAction:
    """Convert an API RedactionActionSchema to a domain RedactionAction.

    Args:
        action: The API action schema value.

    Returns:
        The corresponding domain RedactionAction.
    """
    return RedactionAction(action.value)


@router.post(
    "/",
    response_model=MappingConfigResponse,
    status_code=201,
    responses={422: {"model": ErrorResponse}},
)
async def create_mapping(
    request: MappingConfigRequest,
) -> MappingConfigResponse | JSONResponse:
    """Create a new mapping configuration.

    Validates the mapping via MappingParser, stores it in memory,
    and returns the stored mapping with its ID and policy hash.

    Args:
        request: The mapping configuration to create.

    Returns:
        A MappingConfigResponse with the new mapping's metadata.
    """
    try:
        config = _request_to_domain_config(request)
    except CecilError as err:
        logger.warning(
            "Mapping validation failed",
            extra={"error_type": type(err).__name__},
        )
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(
                error="mapping_validation_error",
                message=str(err),
            ).model_dump(),
        )

    mapping_id = str(uuid4())
    now = datetime.now(tz=UTC)
    _mapping_store[mapping_id] = MappingState(
        mapping_id=mapping_id,
        config=config,
        created_at=now,
    )

    logger.info(
        "Mapping created",
        extra={"mapping_id": mapping_id, "field_count": len(config.fields)},
    )

    return _config_to_response(mapping_id, config, now)


@router.get(
    "/",
    response_model=list[MappingConfigResponse],
)
async def list_mappings() -> list[MappingConfigResponse]:
    """List all saved mapping configurations.

    Returns:
        A list of MappingConfigResponse objects for all stored mappings.
    """
    return [
        _config_to_response(state.mapping_id, state.config, state.created_at)
        for state in _mapping_store.values()
    ]


@router.post(
    "/load-yaml",
    response_model=MappingConfigResponse,
    status_code=201,
    responses={
        404: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
    },
)
async def load_mapping_yaml(
    request: LoadMappingYamlRequest,
) -> MappingConfigResponse | JSONResponse:
    """Load a mapping configuration from a YAML file on disk.

    Reads and parses the YAML file, validates its structure, stores
    the resulting MappingConfig in memory, and returns the mapping
    response with its ID and policy hash.

    Args:
        request: The request containing the file path.

    Returns:
        A MappingConfigResponse with the loaded mapping, or an
        error response if the file is missing or invalid.
    """
    resolved = Path(request.path).resolve()
    if not resolved.is_file():
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(
                error="file_not_found",
                message="Mapping file does not exist",
            ).model_dump(),
        )

    try:
        config = MappingParser().parse_file(resolved)
    except CecilError as err:
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(
                error="mapping_parse_error",
                message=str(err),
            ).model_dump(),
        )

    mapping_id = str(uuid4())
    now = datetime.now(tz=UTC)
    _mapping_store[mapping_id] = MappingState(
        mapping_id=mapping_id,
        config=config,
        created_at=now,
    )

    logger.info(
        "Mapping loaded from YAML",
        extra={"mapping_id": mapping_id, "field_count": len(config.fields)},
    )

    return _config_to_response(mapping_id, config, now)


@router.get(
    "/{mapping_id}",
    response_model=MappingConfigResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_mapping(mapping_id: str) -> MappingConfigResponse | JSONResponse:
    """Retrieve a mapping configuration by ID.

    Args:
        mapping_id: The unique mapping identifier.

    Returns:
        A MappingConfigResponse, or 404 if not found.
    """
    state = _mapping_store.get(mapping_id)
    if state is None:
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(
                error="mapping_not_found",
                message="No mapping found with the given ID",
            ).model_dump(),
        )
    return _config_to_response(state.mapping_id, state.config, state.created_at)


@router.put(
    "/{mapping_id}",
    response_model=MappingConfigResponse,
    responses={
        404: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
    },
)
async def update_mapping(
    mapping_id: str,
    request: MappingConfigRequest,
) -> MappingConfigResponse | JSONResponse:
    """Update an existing mapping configuration.

    Re-validates the mapping via MappingParser before storing.

    Args:
        mapping_id: The unique mapping identifier.
        request: The updated mapping configuration.

    Returns:
        A MappingConfigResponse with the updated mapping, or an error.
    """
    state = _mapping_store.get(mapping_id)
    if state is None:
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(
                error="mapping_not_found",
                message="No mapping found with the given ID",
            ).model_dump(),
        )

    try:
        config = _request_to_domain_config(request)
    except CecilError as err:
        logger.warning(
            "Mapping update validation failed",
            extra={"mapping_id": mapping_id, "error_type": type(err).__name__},
        )
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(
                error="mapping_validation_error",
                message=str(err),
            ).model_dump(),
        )

    state.config = config

    logger.info(
        "Mapping updated",
        extra={"mapping_id": mapping_id, "field_count": len(config.fields)},
    )

    return _config_to_response(state.mapping_id, state.config, state.created_at)


@router.delete(
    "/{mapping_id}",
    status_code=204,
    response_model=None,
    responses={404: {"model": ErrorResponse}},
)
async def delete_mapping(mapping_id: str) -> Response | JSONResponse:
    """Delete a mapping configuration.

    Args:
        mapping_id: The unique mapping identifier.

    Returns:
        204 No Content on success, or 404 if not found.
    """
    if mapping_id not in _mapping_store:
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(
                error="mapping_not_found",
                message="No mapping found with the given ID",
            ).model_dump(),
        )

    del _mapping_store[mapping_id]

    logger.info("Mapping deleted", extra={"mapping_id": mapping_id})

    return Response(status_code=204)


@router.post(
    "/validate",
    response_model=MappingValidationResponse,
    responses={422: {"model": ErrorResponse}},
)
async def validate_mapping(
    request: MappingValidationRequest,
) -> MappingValidationResponse | JSONResponse:
    """Validate a mapping configuration against a sample record.

    Builds a MappingConfig from the request and checks field overlap
    with the provided sample record.

    Args:
        request: The mapping and sample record to validate.

    Returns:
        A MappingValidationResponse with match details.
    """
    try:
        config = _request_to_domain_config(request.mapping)
    except CecilError as err:
        logger.warning(
            "Mapping validation failed during validate",
            extra={"error_type": type(err).__name__},
        )
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(
                error="mapping_validation_error",
                message=str(err),
            ).model_dump(),
        )

    result = validate_mapping_against_record(config, request.sample_record)

    return MappingValidationResponse(
        is_valid=result.is_valid,
        matched_fields=result.matched_fields,
        unmapped_fields=result.unmapped_fields,
        missing_fields=result.missing_fields,
    )


@router.post(
    "/preview",
    response_model=FieldPreviewResponse,
)
async def preview_mapping(request: FieldPreviewRequest) -> FieldPreviewResponse:
    """Preview redaction actions on sample data.

    For each field in the sample record that has a mapping entry,
    applies the redaction action and returns original/transformed pairs.
    String values are truncated to 200 characters for Safe-Pipe compliance.

    Args:
        request: The field mappings and sample record to preview.

    Returns:
        A FieldPreviewResponse with preview entries.
    """
    entries: list[FieldPreviewEntry] = []

    for field_name, value in request.sample_record.items():
        field_entry = request.fields.get(field_name)
        if field_entry is None:
            continue

        domain_action = _schema_action_to_domain(field_entry.action)
        truncated_value = _truncate(str(value))
        transformed = apply_action(
            truncated_value,
            domain_action,
            field_name,
            options={k: v for k, v in field_entry.options.items()},
        )

        entries.append(
            FieldPreviewEntry(
                field_name=field_name,
                original=truncated_value,
                transformed=transformed,
                action=field_entry.action,
            ),
        )

    return FieldPreviewResponse(entries=entries)


@router.post(
    "/sample",
    response_model=SampleRecordResponse,
    responses={404: {"model": ErrorResponse}},
)
async def read_sample_record(
    request: SampleRecordRequest,
) -> SampleRecordResponse | JSONResponse:
    """Read the first record from a local file.

    Uses LocalFileProvider to stream the first record. All values are
    converted to strings and truncated to 200 characters for Safe-Pipe
    compliance.

    Args:
        request: The source file path and optional format.

    Returns:
        A SampleRecordResponse with the first record, or 404 if the
        file does not exist.
    """
    resolved = Path(request.source).resolve()
    if not resolved.is_file():
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(
                error="file_not_found",
                message="Source file does not exist",
            ).model_dump(),
        )

    format_hint = request.file_format.value if request.file_format is not None else None
    provider = LocalFileProvider(
        file_path=str(resolved),
        format_hint=format_hint,
    )

    try:
        provider.connect()
        first_record: dict[str, Any] | None = None
        for record in provider.stream_records():
            first_record = record
            break
    except CecilError as err:
        logger.warning(
            "Failed to read sample record",
            extra={"error_type": type(err).__name__},
        )
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(
                error="provider_error",
                message=f"Cannot read file: {type(err).__name__}",
            ).model_dump(),
        )
    finally:
        provider.close()

    if first_record is None:
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(
                error="no_records",
                message="File contains no records",
            ).model_dump(),
        )

    # Convert all values to strings and truncate for Safe-Pipe compliance.
    safe_record: dict[str, str] = {k: _truncate(str(v)) for k, v in first_record.items()}

    return SampleRecordResponse(
        record=safe_record,
        field_count=len(safe_record),
        source=str(resolved),
    )

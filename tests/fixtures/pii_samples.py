"""PII sample data generator for Cecil tests.

Provides deterministic, well-known PII values and factory functions
that produce realistic log-like records containing embedded PII.
Every piece of PII is catalogued so tests can assert it has been
fully redacted from sanitizer output.

The generator uses ``faker`` with a fixed seed to guarantee
reproducible test data across runs.
"""

from __future__ import annotations

import json
from collections.abc import Generator
from dataclasses import dataclass, field
from typing import Any

from faker import Faker


# Fixed seed for deterministic output across all test runs.
_SEED = 20260208
_fake = Faker()
Faker.seed(_SEED)


# ── Known PII constants ──────────────────────────────────────────────
# These are the "ground truth" PII strings.  After sanitization, none
# of these values may appear in any output, log, or telemetry payload.


@dataclass(frozen=True)
class KnownPII:
    """A single identity bundle of related PII fields.

    All fields are plain strings so they can be searched for in
    serialized output via simple substring matching.
    """

    email: str
    ssn: str
    phone: str
    name: str
    address: str
    credit_card: str
    ip_address: str
    date_of_birth: str

    def all_values(self) -> list[str]:
        """Return every PII value as a flat list.

        Returns:
            A list of all PII string values in this bundle.
        """
        return [
            self.email,
            self.ssn,
            self.phone,
            self.name,
            self.address,
            self.credit_card,
            self.ip_address,
            self.date_of_birth,
        ]


# Hard-coded PII bundles with values that are easy to grep for.
KNOWN_PII_BUNDLES: list[KnownPII] = [
    KnownPII(
        email="john.doe@example.com",
        ssn="123-45-6789",
        phone="(555) 867-5309",
        name="John Doe",
        address="123 Main Street, Springfield, IL 62701",
        credit_card="4111-1111-1111-1111",
        ip_address="192.168.1.42",
        date_of_birth="1985-03-15",
    ),
    KnownPII(
        email="jane.smith@testmail.org",
        ssn="987-65-4321",
        phone="+1-202-555-0173",
        name="Jane Smith",
        address="456 Oak Avenue, Portland, OR 97201",
        credit_card="5500-0000-0000-0004",
        ip_address="10.0.0.99",
        date_of_birth="1990-07-22",
    ),
    KnownPII(
        email="bob.wilson@corporate.net",
        ssn="456-78-9012",
        phone="(312) 555-0198",
        name="Bob Wilson",
        address="789 Pine Road, Chicago, IL 60601",
        credit_card="3782-822463-10005",
        ip_address="172.16.254.1",
        date_of_birth="1978-11-03",
    ),
]


def all_known_pii_values() -> list[str]:
    """Return every known PII value across all bundles.

    Useful for asserting that none of these strings appear in
    sanitized output.

    Returns:
        A flat list of all PII strings from all bundles.
    """
    values: list[str] = []
    for bundle in KNOWN_PII_BUNDLES:
        values.extend(bundle.all_values())
    return values


# ── Faker-based PII generation ───────────────────────────────────────


@dataclass
class GeneratedPIIBatch:
    """A batch of faker-generated PII with tracking metadata.

    Attributes:
        identities: List of PII bundles produced by faker.
        all_pii_values: Flat list of every PII value for leak checking.
    """

    identities: list[KnownPII] = field(default_factory=list)
    all_pii_values: list[str] = field(default_factory=list)


def generate_pii_batch(count: int = 10) -> GeneratedPIIBatch:
    """Generate a batch of fake PII identities using faker.

    Uses a fixed seed so output is deterministic.

    Args:
        count: Number of identities to generate.

    Returns:
        A batch containing the generated identities and a flat list
        of all PII values for leak detection assertions.
    """
    # Re-seed to ensure determinism regardless of call order.
    Faker.seed(_SEED)
    local_fake = Faker()
    Faker.seed(_SEED)

    batch = GeneratedPIIBatch()
    for _ in range(count):
        identity = KnownPII(
            email=local_fake.email(),
            ssn=local_fake.ssn(),
            phone=local_fake.phone_number(),
            name=local_fake.name(),
            address=local_fake.address().replace("\n", ", "),
            credit_card=local_fake.credit_card_number(),
            ip_address=local_fake.ipv4(),
            date_of_birth=local_fake.date_of_birth().isoformat(),
        )
        batch.identities.append(identity)
        batch.all_pii_values.extend(identity.all_values())

    return batch


# ── Log record factories ─────────────────────────────────────────────


def make_llm_log_record(pii: KnownPII, model: str = "gpt-4") -> dict[str, Any]:
    """Create a realistic LLM API log record with embedded PII.

    Simulates the kind of log entry a company might have from their
    AI/LLM usage that Cecil needs to sanitize.

    Args:
        pii: The PII bundle to embed in the record.
        model: The model identifier for the log entry.

    Returns:
        A dictionary resembling an LLM API log entry.
    """
    return {
        "timestamp": "2026-01-15T10:30:00Z",
        "model": model,
        "user_email": pii.email,
        "user_name": pii.name,
        "prompt": (
            f"Hello, my name is {pii.name} and my email is {pii.email}. "
            f"My SSN is {pii.ssn} and I live at {pii.address}. "
            f"You can reach me at {pii.phone}."
        ),
        "completion": (
            f"Thank you {pii.name}, I've noted your details. "
            f"Your account linked to {pii.email} has been updated."
        ),
        "tokens_in": 45,
        "tokens_out": 22,
        "cost_usd": 0.0067,
        "ip_address": pii.ip_address,
        "session_id": "sess-abc123",
        "metadata": {
            "department": "engineering",
            "credit_card_on_file": pii.credit_card,
            "dob": pii.date_of_birth,
        },
    }


def make_log_records_from_bundles(
    bundles: list[KnownPII] | None = None,
    model: str = "gpt-4",
) -> list[dict[str, Any]]:
    """Create a list of log records from PII bundles.

    Args:
        bundles: PII bundles to convert into log records.
            Defaults to ``KNOWN_PII_BUNDLES``.
        model: The model identifier for log entries.

    Returns:
        A list of dictionaries, each resembling an LLM API log entry.
    """
    if bundles is None:
        bundles = KNOWN_PII_BUNDLES
    return [make_llm_log_record(pii, model=model) for pii in bundles]


def stream_log_records(
    count: int = 100,
    model: str = "gpt-4",
) -> Generator[dict[str, Any], None, None]:
    """Yield log records one at a time for streaming pipeline tests.

    Cycles through the hard-coded PII bundles so the same known PII
    values appear repeatedly (useful for leak detection).

    Args:
        count: Total number of records to yield.
        model: The model identifier for log entries.

    Yields:
        A single log record dictionary.
    """
    for i in range(count):
        pii = KNOWN_PII_BUNDLES[i % len(KNOWN_PII_BUNDLES)]
        yield make_llm_log_record(pii, model=model)


# ── Fixture file generators ──────────────────────────────────────────


def generate_sample_jsonl(path: str, count: int = 10) -> list[str]:
    """Write sample JSONL log entries to a file and return all PII values.

    Each line is a JSON object resembling an LLM API log with
    embedded PII from the known bundles.

    Args:
        path: Filesystem path where the JSONL file will be written.
        count: Number of log entries to write.

    Returns:
        A list of all PII values embedded in the generated file.
    """
    pii_values: list[str] = []
    with open(path, "w", encoding="utf-8") as fh:
        for record in stream_log_records(count=count):
            fh.write(json.dumps(record) + "\n")
    # Collect all PII values that were written
    for i in range(count):
        pii = KNOWN_PII_BUNDLES[i % len(KNOWN_PII_BUNDLES)]
        pii_values.extend(pii.all_values())
    return pii_values


def generate_sample_csv(path: str, count: int = 10) -> list[str]:
    """Write sample CSV records to a file and return all PII values.

    Creates a CSV with columns: email, name, ssn, phone, model,
    tokens_in, tokens_out, cost_usd.

    Args:
        path: Filesystem path where the CSV file will be written.
        count: Number of data rows to write (excluding header).

    Returns:
        A list of all PII values embedded in the generated file.
    """
    import csv

    pii_values: list[str] = []
    fieldnames = [
        "email",
        "name",
        "ssn",
        "phone",
        "model",
        "tokens_in",
        "tokens_out",
        "cost_usd",
    ]

    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for i in range(count):
            pii = KNOWN_PII_BUNDLES[i % len(KNOWN_PII_BUNDLES)]
            writer.writerow(
                {
                    "email": pii.email,
                    "name": pii.name,
                    "ssn": pii.ssn,
                    "phone": pii.phone,
                    "model": "gpt-4",
                    "tokens_in": 45,
                    "tokens_out": 22,
                    "cost_usd": 0.0067,
                }
            )
            pii_values.extend([pii.email, pii.name, pii.ssn, pii.phone])

    return pii_values

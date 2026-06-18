#!/usr/bin/env python

from sqlalchemy.testing import fixtures, assert_raises_message
from sqlalchemy.testing.assertions import AssertsCompiledSQL

from databend_sqlalchemy import (
    CSVFormat,
    TSVFormat,
    NDJSONFormat,
    ParquetFormat,
    Compression,
)


class CompileCopyFormatCompressionTest(fixtures.TestBase, AssertsCompiledSQL):

    __only_on__ = "databend"

    _FORMATS = [
        (CSVFormat, "CSV"),
        (TSVFormat, "TSV"),
        (NDJSONFormat, "NDJSON"),
        (ParquetFormat, "PARQUET"),
    ]

    def test_no_compression_emits_no_option(self):
        # ``None`` and the ``Compression.NONE`` sentinel both mean uncompressed.
        # Regression: ``Compression.NONE`` is a truthy Enum member, so the old
        # ``if compression:`` guard treated it as "a codec was set" — emitting a
        # spurious ``COMPRESSION = NONE`` option and, for ParquetFormat, raising.
        for fmt_cls, type_ in self._FORMATS:
            expected = f"FILE_FORMAT = (TYPE = {type_})"
            self.assert_compile(fmt_cls(), expected)
            self.assert_compile(fmt_cls(compression=Compression.NONE), expected)

    def test_explicit_codec_is_emitted(self):
        for fmt_cls, type_, codec in [
            (CSVFormat, "CSV", Compression.GZIP),
            (TSVFormat, "TSV", Compression.GZIP),
            (NDJSONFormat, "NDJSON", Compression.GZIP),
            (ParquetFormat, "PARQUET", Compression.ZSTD),
            (ParquetFormat, "PARQUET", Compression.SNAPPY),
        ]:
            self.assert_compile(
                fmt_cls(compression=codec),
                f"FILE_FORMAT = (TYPE = {type_}, COMPRESSION = {codec.value})",
            )

    def test_parquet_rejects_unsupported_codec(self):
        # ParquetFormat still rejects codecs its writer can't use.
        for codec in [Compression.GZIP, Compression.BZ2, Compression.ZIP]:
            assert_raises_message(
                TypeError,
                "Compression should be None, ZStd, or Snappy.",
                ParquetFormat,
                compression=codec,
            )

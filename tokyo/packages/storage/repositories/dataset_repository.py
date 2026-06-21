from tokyo.packages.contracts.market_data import DatasetRecord
from tokyo.packages.storage.models import DatasetRecordModel
from tokyo.packages.storage.repositories.base import BaseRepository


class DatasetRepository(BaseRepository):
    async def add(self, record: DatasetRecord) -> DatasetRecord:
        self.session.add(
            DatasetRecordModel(
                record_id=record.record_id,
                dataset_id=record.dataset_id,
                dataset_type=record.dataset_type,
                provider=record.provider,
                source_uri=record.source_uri,
                partition=record.partition,
                symbol_id=record.symbol_id,
                provider_symbol=record.provider_symbol,
                time_range=record.time_range.model_dump(mode="json") if record.time_range else None,
                format=record.format,
                compression=record.compression,
                encoding=record.encoding,
                content_hash=record.content_hash,
                content_length=record.content_length,
                payload_ref=record.payload_ref,
                payload_inline=record.payload_inline,
                retrieved_at=record.retrieved_at,
                quality=record.quality.model_dump(mode="json"),
                metadata_=record.metadata,
            )
        )
        return record


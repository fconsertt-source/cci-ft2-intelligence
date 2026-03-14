# tests/unit/test_import_ft2_data_uc.py — النسخة المصححة
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock


from src.application.ports.ft2_reader_port import Ft2ReaderPort
from src.application.ports.ft2_writer_port import Ft2WriterPort
from src.application.ports.logger_port import LoggerPort
from src.application.use_cases.import_ft2_data_uc import ImportFt2DataUseCase
from src.domain.dtos.ft2_entry_dto import FT2EntryDTO


def test_import_uc_delegates_to_ports():
    # Arrange
    mock_reader = Mock(spec=Ft2ReaderPort)
    mock_writer = Mock(spec=Ft2WriterPort)
    mock_logger = Mock(spec=LoggerPort)

    # إرجاع قائمة من FT2EntryDTO (التصميم الجديد)
    mock_reader.read.return_value = [
        FT2EntryDTO(
            id="1",
            device_id="DEV_001",
            timestamp=datetime.now(),
            temperature=5.0,
            vaccine_type="Pfizer",
            batch="BATCH_001",
            duration_minutes=120.0,
        )
    ]

    uc = ImportFt2DataUseCase(
        reader=mock_reader, writer=mock_writer, logger=mock_logger
    )

    input_path = "/input"  # ← str (مطابق Ft2ReaderPort)
    output_path = Path("/output.json")  # ← Path (مطابق Ft2WriterPort)

    # Act
    uc.execute(input_dir=input_path, output_path=output_path)

    # Assert — التحقق من compliance مع الـ Ports
    mock_reader.read.assert_called_once_with(input_path)  # ← str
    mock_writer.write.assert_called_once_with(
        mock_reader.read.return_value, output_path
    )  # ← data first, destination second
    mock_logger.info.assert_any_call(
        f"Importing FT2 data from '{input_path}' to '{output_path}'"
    )

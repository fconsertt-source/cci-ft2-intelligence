from unittest.mock import MagicMock, patch
from scripts import verify_visual_reports
import os


def test_verify_visual_reports_runs_and_calls_generate(tmp_path, monkeypatch):
    # Arrange: set working dir to tmp_path
    monkeypatch.chdir(tmp_path)
    out_dir = tmp_path / 'data' / 'output' / 'visual_tests'
    out_dir.mkdir(parents=True)
    data_path = out_dir / 'mock_visual_data.tsv'
    # create file
    data_path.write_text('center_id\tcenter_name')

    fake_gen = MagicMock()
    fake_gen.generate.return_value = str(out_dir / 'visual_test_official.pdf')

    with patch('src.reporting.unified_pdf_generator.UnifiedPDFGenerator', return_value=fake_gen):
        verify_visual_reports.main()
        assert fake_gen.generate.called

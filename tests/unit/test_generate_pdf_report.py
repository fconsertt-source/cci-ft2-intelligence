import os
from unittest.mock import MagicMock, patch

from scripts import generate_pdf_report


def test_generate_pdf_report_handles_missing_file(tmp_path, caplog):
    # Ensure missing TSV returns early without exception
    caplog.clear()
    # Point to a non-existing path by ensuring data/output/centers_report.tsv is absent
    tsv = os.path.join('data', 'output', 'centers_report.tsv')
    if os.path.exists(tsv):
        os.remove(tsv)

    generate_pdf_report.main()
    # Should have logged an error about missing file
    assert any('ملف التقرير غير موجود' in r.message for r in caplog.records)


def test_generate_pdf_report_calls_generator(monkeypatch, tmp_path):
    # Create a fake TSV file
    out_dir = tmp_path / 'data' / 'output'
    out_dir.mkdir(parents=True)
    tsv = out_dir / 'centers_report.tsv'
    tsv.write_text('center_id\tcenter_name')

    # Monkeypatch the expected path
    monkeypatch.chdir(tmp_path)

    fake_path = '/fake/report.pdf'
    FakeGen = MagicMock()
    FakeGen.generate.return_value = fake_path

    # Patch the symbol where the script looks it up
    with patch('scripts.generate_pdf_report.UnifiedPDFGenerator', return_value=FakeGen):
        generate_pdf_report.main()

    FakeGen.generate.assert_called_once()

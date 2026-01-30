import pytest
from src.core.enums.vvm_stage import VVMStage

def test_vvm_stage_from_duration():
    # NONE: < 2 days (2880 mins)
    assert VVMStage.from_duration(2800) == VVMStage.NONE
    
    # A: 2-6 days (2880 - 8640 mins)
    assert VVMStage.from_duration(3000) == VVMStage.A
    
    # B: 6-11 days (8640 - 15840 mins)
    assert VVMStage.from_duration(9000) == VVMStage.B
    
    # C: 11-14 days (15840 - 20160 mins)
    assert VVMStage.from_duration(16000) == VVMStage.C
    
    # D: >= 14 days (20160 mins)
    assert VVMStage.from_duration(21000) == VVMStage.D

def test_vvm_stage_colors():
    assert VVMStage.NONE.get_color() == "#4CAF50"
    assert VVMStage.D.get_color() == "#B71C1C"

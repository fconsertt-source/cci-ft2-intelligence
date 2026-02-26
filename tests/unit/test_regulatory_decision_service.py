from src.domain.services.regulatory_decision_service import RegulatoryDecisionService
from src.domain.value_objects.vaccine_specification import VaccineSpecification


def test_freeze_sensitive_absolute_discard():
    """Test that freeze-sensitive vaccines get absolute DISCARD for freeze."""
    
    # Arrange
    service = RegulatoryDecisionService()
    spec = VaccineSpecification(
        vaccine_type="Hepatitis_B",
        min_temp=2.0,
        max_temp=8.0,
        freeze_sensitive=True,
        max_heat_duration_hours=72.0,
        regulatory_source="WHO/IVB/06.10"
    )
    
    # Act
    decision = service.evaluate(temperature=-19.0, duration_minutes=1440.0, spec=spec)
    
    # Assert
    assert decision == "DISCARD"


def test_freeze_stable_frozen_storage_safe():
    """Test that freeze-stable vaccines in frozen range are SAFE."""
    
    # Arrange
    service = RegulatoryDecisionService()
    spec = VaccineSpecification(
        vaccine_type="OPV",
        min_temp=2.0,
        max_temp=8.0,
        freeze_sensitive=False,
        freeze_range=[-25.0, -15.0],
        max_heat_duration_hours=48.0,
        regulatory_source="WHO/IVB/06.10"
    )
    
    # Act
    decision = service.evaluate(temperature=-20.0, duration_minutes=1440.0, spec=spec)
    
    # Assert
    assert decision == "SAFE"


def test_freeze_stable_unintended_freeze_discard():
    """Test that freeze-stable vaccines get DISCARD if frozen outside range."""
    
    # Arrange
    service = RegulatoryDecisionService()
    spec = VaccineSpecification(
        vaccine_type="OPV",
        min_temp=2.0,
        max_temp=8.0,
        freeze_sensitive=False,
        freeze_range=[-25.0, -15.0],
        max_heat_duration_hours=48.0,
        regulatory_source="WHO/IVB/06.10"
    )
    
    # Act
    decision = service.evaluate(temperature=-5.0, duration_minutes=1440.0, spec=spec)
    
    # Assert
    assert decision == "DISCARD"


def test_heat_exposure_duration_threshold():
    """Test that heat exposure exceeding duration threshold leads to DISCARD."""
    
    # Arrange
    service = RegulatoryDecisionService()
    spec = VaccineSpecification(
        vaccine_type="Hepatitis_B",
        min_temp=2.0,
        max_temp=8.0,
        freeze_sensitive=True,
        max_heat_duration_hours=72.0,  # 3 days
        regulatory_source="WHO/IVB/06.10"
    )
    
    # Act
    decision = service.evaluate(temperature=10.0, duration_minutes=10080.0, spec=spec)  # 7 days
    
    # Assert
    assert decision == "DISCARD"


def test_max_heat_temp_exceeded():
    """Test that max heat temperature exceeded leads to DISCARD."""
    
    # Arrange
    service = RegulatoryDecisionService()
    spec = VaccineSpecification(
        vaccine_type="HPV",
        min_temp=2.0,
        max_temp=8.0,
        freeze_sensitive=True,
        max_heat_temp=37.0,
        max_heat_duration_hours=72.0,
        regulatory_source="WHO/IVB/06.10"
    )
    
    # Act
    decision = service.evaluate(temperature=38.0, duration_minutes=60.0, spec=spec)
    
    # Assert
    assert decision == "DISCARD"


def test_within_regulatory_range_safe():
    """Test that temperatures within range lead to SAFE."""
    
    # Arrange
    service = RegulatoryDecisionService()
    spec = VaccineSpecification(
        vaccine_type="Hepatitis_B",
        min_temp=2.0,
        max_temp=8.0,
        freeze_sensitive=True,
        max_heat_duration_hours=72.0,
        regulatory_source="WHO/IVB/06.10"
    )
    
    # Act
    decision = service.evaluate(temperature=4.0, duration_minutes=1440.0, spec=spec)
    
    # Assert
    assert decision == "SAFE"

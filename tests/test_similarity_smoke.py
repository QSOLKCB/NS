import crucible_core as cc


def test_similarity_screening_import_and_authority():
    assert cc.DUPLICATE_DETECTOR_VERSION == "0.1.0"
    Detector = getattr(cc, "Duplicate" + "Dead" + "Family" + "Detector")
    gate = Detector(structural_threshold=0.82, dead_family_threshold=0.76, minimum_shared_tokens=4)
    assert not any(gate.authority_snapshot().values())

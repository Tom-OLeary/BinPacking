from consolidation import ConsolidationGenerator


def test_consolidation_generator():
    generator = ConsolidationGenerator()
    results = generator.run()

    assert len(results) == 3

    # PickupC and/or DeliverC should be ignored due to missing values
    assert "PickupC" not in [r.pick_up_location for r in results]
    assert "DeliverC" not in [r.deliver_to_location for r in results]

    expected = {
        ("PickupA", "DeliverA"): {
            "total_volume": 65,
            "total_weight": 600,
        },
        ("PickupA", "DeliverB"): {
            "total_volume": 60,
            "total_weight": 700,
        },
        ("PickupB", "DeliverB"): {
            "total_volume": 65,
            "total_weight": 650,
        },
    }
    for row in results:
        pickup = row.pick_up_location
        deliver = row.deliver_to_location
        _expected = expected[(pickup, deliver)]
        assert row.total_volume == _expected["total_volume"]
        assert row.total_weight == _expected["total_weight"]

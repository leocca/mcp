from app import calculate_order_total
import pytest


def test_total_simple():
    assert calculate_order_total([10.0, 20.0, 30.0]) == 60.0

def test_total_avec_remise():
    assert calculate_order_total([100.0, 50.0], 0.5) == 75.0

def test_remise_invalide():
    with pytest.raises(ValueError):
        calculate_order_total([10.0], 1.5)

def test_panier_vide():
    assert calculate_order_total([]) == 0.0

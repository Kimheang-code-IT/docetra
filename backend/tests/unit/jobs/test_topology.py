"""Job topology constants must stay stable for broker contract compatibility."""

from app.jobs import topology


def test_exchange_names():
    assert topology.EVENT_EXCHANGE == "docetra.events"
    assert topology.DEAD_LETTER_EXCHANGE == "docetra.dlx"

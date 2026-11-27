import json
import state_store


def test_state_round_trip(tmp_path, monkeypatch):
    path = tmp_path / "processed.json"
    monkeypatch.setattr(state_store, "STATE_FILE", str(path))
    state_store.save_processed({"abc", "xyz"})
    assert state_store.load_processed() == {"abc", "xyz"}
    assert json.loads(path.read_text()) == ["abc", "xyz"]

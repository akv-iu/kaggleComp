"""One runnable check: the agent survives a full episode and beats the baseline.

Run: .venv/Scripts/python.exe test_agent.py
"""

from kaggle_environments import make

from main import ANIMALS, _harvest_day, _next_animal, _scan, agent


def test_harvest_day():
    # Yield caps before max_yield_day for melon; wheat/carrot are window-limited.
    assert _harvest_day("WHEAT") == 4, _harvest_day("WHEAT")
    assert _harvest_day("CARROT") == 3, _harvest_day("CARROT")
    assert _harvest_day("MELON") == 10, _harvest_day("MELON")


def test_next_animal():
    empty = {a: 0 for a in ANIMALS}
    # The opening buys the bird that pays on day 4, not the cow that pays on day 8.
    assert _next_animal(dict(empty), 0) == "GOOSE"
    assert _next_animal(dict(empty), 5) != "GOOSE"
    # Deadlines: a cow bought on day 21 never reaches its first production.
    assert _next_animal(dict(empty), 21, "PASTURE") is None
    assert _next_animal(dict(empty), 24) == "GOOSE"
    # A pasture never gets a goose, whatever the herd is short of.
    assert _next_animal({"GOOSE": 0, "COW": 9, "SHEEP": 0}, 5, "PASTURE") == "SHEEP"
    # A beast already bought outranks every rule above -- it earns nothing in the
    # shed, and "too late to buy one" is no reason to leave the one we own crated.
    assert _next_animal(dict(empty), 28, "PASTURE", {"COW": 1}) == "COW"


def test_scan_last_hour_and_build():
    tiles = [["LOCKED"] * 10 for _ in range(10)]
    tiles[0][0] = None
    # Hour 23 has no following turn in which to water, so nothing is planted.
    jobs, _, _ = _scan(tiles, 0, 23, {"MELON": 1}, 99, 3000, {})
    assert not any(job[3][0] == "PLANT" for job in jobs), jobs
    # With no slots left the crew builds nothing either.
    assert not _scan(tiles, 0, 0, {}, 0, 3000, {})[0]
    # An empty pasture asks the market for the animal that fits it.
    tiles[0][0] = {"kind": "PASTURE"}
    want = _scan(tiles, 0, 0, {}, 99, 9999, {})[1]
    assert set(want) <= {"COW", "SHEEP"}, want


def test_episode():
    env = make("kaggriculture", configuration={"seed": 1}, debug=True)
    env.run([agent, "starter"])
    final = env.steps[-1]
    mine, theirs = final[0], final[1]
    # debug=True surfaces exceptions; a crashed agent scores like "pass", so the
    # status assert matters more than the score.
    assert mine.status == "DONE", mine.status
    assert mine.reward > theirs.reward, (mine.reward, theirs.reward)
    return mine.reward, theirs.reward


if __name__ == "__main__":
    test_harvest_day()
    test_next_animal()
    test_scan_last_hour_and_build()
    print("unit checks ok")
    print("episode: me=%.0f starter=%.0f" % test_episode())

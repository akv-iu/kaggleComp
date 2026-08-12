"""One runnable check: the agent survives a full episode and beats the baseline.

Run: .venv/Scripts/python.exe test_agent.py
"""

from kaggle_environments import make

from main import ANIMALS, _harvest_day, _next_animal, _scan, _wheat_target, agent


def test_harvest_day():
    # Yield caps before max_yield_day for melon; wheat/carrot are window-limited.
    assert _harvest_day("WHEAT") == 4, _harvest_day("WHEAT")
    assert _harvest_day("CARROT") == 3, _harvest_day("CARROT")
    assert _harvest_day("MELON") == 10, _harvest_day("MELON")
    assert _wheat_target(8, 0) == 6
    assert _wheat_target(8, 20) == 10


def test_next_animal():
    empty = {a: 0 for a in ANIMALS}
    # The opening takes the faster-paying bird before shifting to premium animals.
    assert _next_animal(dict(empty), 0) == "GOOSE"
    assert _next_animal(dict(empty), 5) != "GOOSE"
    # Deadlines: a cow bought on day 21 never reaches its first production, and a
    # goose bought after day 20 eats more wheat than it lays egg.
    assert _next_animal(dict(empty), 21, "PASTURE") is None
    assert _next_animal(dict(empty), 20, "COOP") == "GOOSE"
    assert _next_animal(dict(empty), 21, "COOP") is None
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
    # Only one new structure enters the pipeline, and it is the tile nearest the
    # shed rather than the row-major corner.
    tiles[4][4] = None
    jobs, want, _ = _scan(tiles, 0, 0, {}, 99, 9999, {})
    builds = [job for job in jobs if job[3][0].startswith("BUILD_")]
    assert len(builds) == 1 and builds[0][1:3] == (4, 4), builds
    assert sum(want.values()) == 1, want
    # An empty pasture asks the market for the animal that fits it.
    tiles[4][4] = "LOCKED"
    tiles[0][0] = {"kind": "PASTURE"}
    want = _scan(tiles, 0, 0, {}, 99, 9999, {})[1]
    assert set(want) <= {"COW", "SHEEP"}, want
    # Feeding and care cannot pay back on the final day; harvest and fertilizer can.
    tiles[0][0] = {"kind": "COOP", "animal": "GOOSE", "fed_today": False,
                   "cared_today": False, "yield_units": 2,
                   "fertilizer_available": True}
    jobs = _scan(tiles, 29, 0, {}, 99, 9999, {})[0]
    ops = {job[3][0] for job in jobs}
    assert {"HARVEST", "COLLECT_FERTILIZER"} <= ops, ops
    assert not {"FEED", "CARE"} & ops, ops
    # Before its yield window, a crop only needs water every other day.
    tiles[0][0] = {"kind": "PLANT", "crop": "WHEAT", "planted_day": 0,
                   "watered_today": False, "consecutive_unwatered": 0,
                   "yield_units": 0}
    assert not _scan(tiles, 1, 0, {}, 99, 9999, {})[0]
    tiles[0][0]["consecutive_unwatered"] = 1
    assert _scan(tiles, 1, 0, {}, 99, 9999, {})[0][0][3] == ["WATER"]


def test_episode():
    env = make("kaggriculture", configuration={"seed": 1}, debug=True)
    env.run([agent, "starter"])
    final = env.steps[-1]
    mine, theirs = final[0], final[1]
    # debug=True surfaces exceptions; a crashed agent scores like "pass", so the
    # status assert matters more than the score.
    assert mine.status == "DONE", mine.status
    assert mine.reward > theirs.reward, (mine.reward, theirs.reward)
    assert len(mine.observation["farms"][0]["hands"]) > 0  # final-day cleanup crew
    return mine.reward, theirs.reward


if __name__ == "__main__":
    test_harvest_day()
    test_next_animal()
    test_scan_last_hour_and_build()
    print("unit checks ok")
    print("episode: me=%.0f starter=%.0f" % test_episode())

"""One runnable check: the agent survives a full episode and beats the baseline.

Run: .venv/Scripts/python.exe test_agent.py
"""

from kaggle_environments import make

from main import (ANIMALS, HERD_RUSH_DAY, _assign, _harvest_day, _next_animal,
                  _scan, _wheat_target, agent)


def test_harvest_day():
    # Yield caps before max_yield_day for melon; wheat/carrot are window-limited.
    assert _harvest_day("WHEAT") == 4, _harvest_day("WHEAT")
    assert _harvest_day("CARROT") == 3, _harvest_day("CARROT")
    assert _harvest_day("MELON") == 10, _harvest_day("MELON")
    assert _wheat_target(8, 0) == 6
    assert _wheat_target(8, 20) == 10


def test_next_animal():
    empty = {a: 0 for a in ANIMALS}
    # The opening buys premium animals from day 0: the rush fills the whole herd
    # there, and gating that day to geese spends it on the dump product.
    assert _next_animal(dict(empty), 0) == "COW"
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
    # Inside the rush window `slots` does not hold the herd back -- the empty
    # structure is what creates the hiring load that pays for the crew.
    assert _scan(tiles, 0, 0, {}, 0, 3000, {})[0]
    # Past it, no slots means no new structure.
    assert not _scan(tiles, HERD_RUSH_DAY + 1, 0, {}, 0, 3000, {})[0]
    # The rush grows the herd in parallel; afterwards it is one head at a time,
    # on the tile nearest the shed rather than the row-major corner.
    tiles[4][4] = None
    builds = [j for j in _scan(tiles, 0, 0, {}, 99, 9999, {})[0]
              if j[3][0].startswith("BUILD_")]
    assert len(builds) == 2, builds
    jobs, want, _ = _scan(tiles, HERD_RUSH_DAY + 1, 0, {}, 99, 9999, {})
    builds = [job for job in jobs if job[3][0].startswith("BUILD_")]
    assert len(builds) == 1 and builds[0][1:3] == (4, 4), builds
    assert sum(want.values()) == 1, want
    # A structure is free, so a beast already paid for and standing in the shed
    # is never held up by an empty bank. Without this the farm can deadlock with
    # its whole herd crated and no cash to authorise the $0 pasture.
    assert [j[3] for j in _scan(tiles, 20, 0, {}, 99, 0, {"COW": 1})[0]
            if j[3][0].startswith("BUILD_")] == [["BUILD_PASTURE"]]
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


def test_assign_takes_the_closest_pair_in_a_band():
    # Two jobs of equal priority and two units. Scan order offers the far job
    # first; it must not claim the unit standing next to the near one.
    tiles = [[None] * 10 for _ in range(10)]
    # Offering (9,2) first makes it claim the unit at (3,4) -- 8 steps -- and
    # leaves the unit at (5,7) a 9-step walk to (3,0). Pairing by distance costs
    # 13 steps instead of 17.
    units = [[3, 4], [5, 7]]
    jobs = [(0, 9, 2, ["WATER"], None), (0, 3, 0, ["WATER"], None)]
    acts = _assign(units, jobs, tiles, [{}, {}])
    assert acts == [["NORTH"], ["EAST"]], acts
    # Priority still wins over distance: the far high-priority job goes first.
    jobs = [(-1, 9, 8, ["WATER"], None), (0, 1, 0, ["WATER"], None)]
    assert _assign([[0, 0]], jobs, tiles, [{}])[0] == ["EAST"]


def test_strawberry():
    tiles = [["LOCKED"] * 10 for _ in range(10)]
    tiles[0][0] = {"kind": "PLANT", "crop": "STRAWBERRY", "planted_day": 0,
                   "watered_today": True, "consecutive_unwatered": 0,
                   "yield_units": 0, "fertilized_until_day": -1}

    def ops(day):
        return {job[3][0] for job in _scan(tiles, day, 0, {}, 99, 9999, {})[0]}

    # The nightly refresh counts from tomorrow, so a berry planted on day 0
    # produces on the nights of days 9, 11, 13, 15 -- fertilize on those, and
    # never after the fourth production, when the tile is already marked to die.
    assert "FERTILIZE" in ops(9), ops(9)
    assert "FERTILIZE" not in ops(10), ops(10)
    assert "FERTILIZE" not in ops(17), ops(17)
    # Berries wait for the melon opening to pay for them.
    tiles[0][0] = None
    assert not _scan(tiles, 5, 0, {"STRAWBERRY": 1}, 99, 0, {})[0]
    jobs = _scan(tiles, 6, 0, {"STRAWBERRY": 1}, 99, 0, {})[0]
    assert [job[3] for job in jobs] == [["PLANT", "STRAWBERRY"]], jobs


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
    test_strawberry()
    test_assign_takes_the_closest_pair_in_a_band()
    print("unit checks ok")
    print("episode: me=%.0f starter=%.0f" % test_episode())

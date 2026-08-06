"""One runnable check: the agent survives a full episode and beats the baseline.

Run: .venv/Scripts/python.exe test_agent.py
"""

from kaggle_environments import make

from main import _harvest_day, agent


def test_harvest_day():
    # Yield caps before max_yield_day for melon; wheat/carrot are window-limited.
    assert _harvest_day("WHEAT") == 4, _harvest_day("WHEAT")
    assert _harvest_day("CARROT") == 3, _harvest_day("CARROT")
    assert _harvest_day("MELON") == 10, _harvest_day("MELON")


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
    print("harvest days ok")
    print("episode: me=%.0f starter=%.0f" % test_episode())

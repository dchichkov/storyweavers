"""Greenhouse transfer case, authored after the shared-rule freeze.

Source: luna_high_direct_20/03_greenhouse/story.txt. Resource-limited watering,
temporary shade, cooperation, and return of the borrowed can. This is a compact
executable adaptation, not a claim of full source-story reconstruction.
"""
from dataclasses import asdict

from ...world import Entity, Fact, Frame, World, kernel
from ..language import Language


class Greenhouse(World):
    def facts_for_attention(self):
        facts = list(self.facts.values())
        facts += [Fact("hero." + k, k, ("care", "goal", "hero"), value)
                  for k, value in self.entities["hero"].memes.items()]
        return facts


def make_world(seed=0):
    entities = {
        "hero": Entity("hero", "Nia", "person", "greenhouse", pronoun="she",
                       properties={"animate", "can_hold"}, memes={"Care": .9, "Desire": .7}),
        "caretaker": Entity("caretaker", "Mr Bell", "person", "greenhouse", pronoun="he", properties={"animate", "can_hold"}),
        "owner": Entity("owner", "Mrs Okafor", "person", "outside", pronoun="she", properties={"animate", "can_hold"}),
        "tomatoes": Entity("tomatoes", "tomato seedling", "plant", "bench", number="plural", state={"dry", "drooping"}),
        "sunflower": Entity("sunflower", "sunflower", "plant", "greenhouse", state={"dry"}),
        "can": Entity("can", "watering can", "tool", "caretaker", state={"empty"}, properties={"portable", "borrowed"}),
        "barrel": Entity("barrel", "rain barrel", "object", "greenhouse", state={"one_can_of_water"}),
        "tap": Entity("tap", "tap", "object", "greenhouse", state={"broken"}),
        "cloth": Entity("cloth", "shade cloth", "object", "bench", state={"intact"}),
        "umbrella": Entity("umbrella", "umbrella", "tool", "hero", state={"closed"}, properties={"portable"}),
        "pot": Entity("pot", "pot", "object", "bench", state={"weighted_with_pebbles"}),
        "tie": Entity("tie", "garden tie", "object", "drawer", properties={"portable"}),
        "clip": Entity("clip", "clip", "object", "owner", properties={"portable"}),
    }
    facts = {"water": Fact("water", "The barrel holds one can of water; the tap is broken.", ("resource", "goal")),
             "plants": Fact("plants", "The tomato seedlings and sunflower have dry soil.", ("care", "goal")),
             "shade": Fact("shade", "The umbrella can provide temporary shade.", ("planning", "tool"))}
    return Greenhouse("greenhouse", entities, "hero", "caretaker", "tomatoes", "can", "greenhouse", facts)


KERNELS = {
    "notice": kernel("notice", excludes=("noticed",), adds=("noticed",)),
    "borrow": kernel("borrow", ("noticed",), ("borrowed",), ("borrowed",)),
    "fill": kernel("fill", ("borrowed",), query=("resource",)),
    "water": kernel("water", ("borrowed",), query=("care",), preferences=(("Care", 1),)),
    "shade_break": kernel("shade_break", ("tomatoes_watered",), ("shade_broken",), ("shade_broken",)),
    "open_umbrella": kernel("open_umbrella", ("shade_broken",), ("umbrella_open",), ("umbrella_open",)),
    "secure": kernel("secure", ("umbrella_open",), ("protected",), ("protected",)),
    "arrive": kernel("arrive", ("protected",), ("arrived",), ("arrived",)),
    "repair_shade": kernel("repair_shade", ("arrived",), ("shade_repaired",), ("shade_repaired",)),
    "repair_tap": kernel("repair_tap", ("protected",), ("tap_repaired",), ("tap_repaired",)),
    "close_umbrella": kernel("close_umbrella", ("shade_repaired",), ("umbrella_closed",), ("umbrella_closed",)),
    "return": kernel("return", ("sunflower_watered", "umbrella_closed"), ("returned",), ("returned",)),
    "ending": kernel("ending", ("returned",), (), ("ended",)),
}


def candidates(w):
    e, rows = w.entities, []
    if w.finished or e["hero"].location != "greenhouse" or "can_hold" not in e["hero"].properties:
        return rows
    def add(kind, actor="hero", patient="", instrument="", destination=""):
        k = KERNELS[kind]
        if k.requires <= w.flags and not k.excludes & w.flags:
            rows.append((k, Frame(kind, actor, patient, instrument, destination, ("plants", "water", "shade"))))
    add("notice", patient="tomatoes")
    if e["can"].location == "caretaker" and e["caretaker"].location == "greenhouse":
        add("borrow", patient="can", destination="hero")
    if e["can"].location == "hero" and "empty" in e["can"].state:
        if "tomatoes_watered" not in w.flags and "one_can_of_water" in e["barrel"].state:
            add("fill", patient="barrel", instrument="can")
        elif "sunflower_watered" not in w.flags and "repaired" in e["tap"].state:
            add("fill", patient="tap", instrument="can")
    if e["can"].location == "hero" and "full" in e["can"].state:
        patient = "tomatoes" if "tomatoes_watered" not in w.flags else "sunflower"
        if "dry" in e[patient].state and (patient == "tomatoes" or "repaired" in e["tap"].state):
            add("water", patient=patient, instrument="can")
    if "intact" in e["cloth"].state:
        add("shade_break", actor="cloth", patient="cloth")
    if e["umbrella"].location == "hero" and "closed" in e["umbrella"].state:
        add("open_umbrella", patient="umbrella")
    if ("open" in e["umbrella"].state and e["umbrella"].location == "hero"
            and "weighted_with_pebbles" in e["pot"].state and e["tie"].location == "drawer"):
        add("secure", patient="umbrella", instrument="tie", destination="pot")
    if e["owner"].location == "outside" and e["clip"].location == "owner":
        add("arrive", actor="owner", instrument="clip", destination="greenhouse")
    if e["owner"].location == "greenhouse" and e["clip"].location == "owner" and "broken" in e["cloth"].state:
        add("repair_shade", actor="owner", patient="cloth", instrument="clip")
    if e["caretaker"].location == "greenhouse" and "broken" in e["tap"].state:
        add("repair_tap", actor="caretaker", patient="tap")
    if "repaired" in e["cloth"].state and "open" in e["umbrella"].state:
        add("close_umbrella", patient="umbrella")
    if e["can"].location == "hero" and e["caretaker"].location == "greenhouse" and "empty" in e["can"].state:
        add("return", patient="can", destination="caretaker")
    if (e["can"].location == "caretaker" and "repaired" in e["cloth"].state
            and all("watered" in e[x].state for x in ("tomatoes", "sunflower"))):
        add("ending", actor="tomatoes", patient="tomatoes")
    return rows


def commit(w, f, sentence):
    if f not in [frame for _, frame in candidates(w)]:
        raise ValueError("frame is not executable in this greenhouse")
    before = w.snapshot()
    e, kind = w.entities, f.kind
    w.flags.update(KERNELS[kind].adds)
    if kind == "borrow":
        e["can"].location = "hero"
    elif kind == "fill":
        e["can"].state = {"full"}
        if f.patient == "barrel":
            e["barrel"].state = {"empty"}
    elif kind == "water":
        e["can"].state = {"empty"}
        e[f.patient].state.discard("dry")
        e[f.patient].state.add("watered")
        w.flags.add(f.patient + "_watered")
    elif kind == "shade_break":
        e["cloth"].state = {"broken"}
        e["tomatoes"].state.add("exposed")
    elif kind == "open_umbrella":
        e["umbrella"].state = {"open"}
    elif kind == "secure":
        e["umbrella"].location = "pot"
        e["tie"].location = "umbrella"
        e["tomatoes"].state.discard("exposed")
        e["tomatoes"].state.add("shaded")
    elif kind == "arrive":
        e["owner"].location = "greenhouse"
    elif kind == "repair_shade":
        e["cloth"].state = {"repaired"}
        e["clip"].location = "cloth"
    elif kind == "repair_tap":
        e["tap"].state = {"repaired"}
    elif kind == "close_umbrella":
        e["umbrella"].state = {"closed"}
        e["umbrella"].location = "hero"
        e["tie"].location = "drawer"
    elif kind == "return":
        e["can"].location = "caretaker"
    elif kind == "ending":
        e["tomatoes"].state.discard("drooping")
        e["tomatoes"].state.add("upright")
    w.focus = f.actor
    record = dict(id=len(w.history) + 1, frame=asdict(f), sentence=sentence, before=before, after=w.snapshot())
    w.history.append(record)
    return record


def plan(w, f, tense="past"):
    g = Language(w, tense)
    n, r, v, s, pp = g.n, g.ref, g.v, g.s, g.pp
    if f.kind == "notice":
        premise = s("hero", v("notice", s("tomatoes", g.be("thirsty"))))
        shortage = s("caretaker", v("explain", s("tap", g.be("broken"))))
        return g.join(s("hero", v("want", v("water", r("sunflower")))), g.join(premise, shortage), "but")
    if f.kind == "borrow":
        return s("hero", g.adv(v("borrow", r("can", adjectives=("blue",))), pp("from", r("caretaker"))))
    if f.kind == "fill":
        return s("hero", g.adv(v("fill", r("can")), pp("from", r(f.patient))))
    if f.kind == "water":
        return s("hero", g.adv(v("water", r(f.patient)), pp("with", r("can"))))
    if f.kind == "shade_break":
        return g.join(s("cloth", v("fall")), s("tomatoes", g.be("exposed")))
    if f.kind == "open_umbrella":
        return s("hero", g.adv(v("open", r("umbrella", adjectives=("yellow",))), pp("above", r("tomatoes"))))
    if f.kind == "secure":
        fetch = g.adv(v("fetch", r("tie")), pp("from", n("drawer")))
        secure = g.adv(v("secure", r("umbrella")), pp("in", r("pot", adjectives=("heavy",))), pp("with", n("garden tie")))
        return g.sequence("hero", fetch, secure)
    if f.kind == "arrive":
        return s("owner", g.adv(v("arrive"), pp("with", r("clip"))))
    if f.kind == "repair_shade":
        return s(g.both(r("hero"), r("owner")), g.adv(v("repair", r("cloth")), pp("with", r("clip"))))
    if f.kind == "repair_tap":
        return s("caretaker", v("repair", r("tap")))
    if f.kind == "close_umbrella":
        return s("hero", v("close", r("umbrella")))
    if f.kind == "return":
        return s("hero", g.adv(v("return", r("can")), pp("to", r("caretaker"))))
    if f.kind == "ending":
        return s("tomatoes", g.adv(v("stand"), pp("under", r("cloth", adjectives=("repaired",)))))
    raise ValueError(f"missing greenhouse event mapping: {f.kind}")

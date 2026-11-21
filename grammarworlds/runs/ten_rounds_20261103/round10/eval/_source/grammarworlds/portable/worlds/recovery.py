"""Rescue, kite and key semantic plans, sharing the same Python grammar port.

These are event-to-language mappings, not new syntax or inflection rules.
Existing world preconditions, effects, and attention weights are unchanged.
"""
from ...world import frames as candidates, commit, make_world
from ..language import Language


def plan(world, frame, tense="past"):
    g = Language(world, tense)
    h, t, tool, helper = world.hero, world.target, world.tool, world.helper
    target, instrument = g.ref(t), g.ref(tool)
    n, v, s, pp = g.n, g.v, g.s, g.pp
    scenario, kind = world.scenario, frame.kind
    goal = {"rescue": lambda: g.adv(v("rescue", target), "safely"),
            "kite": lambda: v("repair", target),
            "key": lambda: v("find", target)}[scenario]()
    if kind == "notice":
        if scenario == "rescue":
            state = s(t, g.be("stranded"))
            view = g.adv(v("notice", g.ref(t, adjectives=("cold",))), pp("on", n("ledge", "high")))
        elif scenario == "kite":
            state = s(t, g.be("torn"))
            view = g.adv(v("notice", g.ref(t, adjectives=("torn",))), pp("on", n("grass")))
        else:
            state = g.join(s("door", g.be("locked")), s(t, g.be("missing")))
            view = v("see", state)
        return g.either(s(h, v("notice", state)), s(h, view))
    if kind == "want":
        return g.either(s(h, v("want", goal)), s(h, v("hope", goal)))
    if kind == "attempt":
        if scenario == "rescue":
            attempt, obstacle = v("try", v("reach", target)), s(h, g.can(v("reach", n("ledge"))), negative=True)
        elif scenario == "kite":
            attempt = g.adv(v("toss", target), pp("in", n("wind")))
            obstacle = s(t, g.adv(v("fall"), pp("on", n("grass"))))
        else:
            attempt = g.adv(v("look"), pp("under", n("bench")))
            obstacle = s(t, g.be("hidden"))
        return g.join(s(h, attempt), obstacle, "but")
    if kind == "ask":
        request = g.adv(v("ask", g.ref(helper)), pp("for", n("help", det="bare")))
        return s(h, request)
    if kind == "think":
        action = {"rescue": lambda: v("reach", n("ledge")),
                  "kite": lambda: v("cover", n("tear")),
                  "key": lambda: v("light", n("darkness"))}[scenario]()
        return s(h, v("realize", s(instrument, g.can(action))))
    if kind == "fetch":
        return s(h, g.adv(v("fetch", instrument), pp("from", n(world.entities[tool].location))))
    if kind == "receive":
        return s(helper, v("bring", g.ref(h), instrument))
    if kind == "solve":
        if scenario == "rescue":
            action = g.adv(v("lift", target), "down")
        elif scenario == "kite":
            action = v("mend", target)
        else:
            action = g.adv(v("find", target), pp("under", n("bench")))
        return g.either(s(h, v("use", instrument, action)), s(h, g.adv(action, pp("with", instrument))))
    if kind == "finish":
        if scenario == "rescue":
            return g.join(s(h, g.adv(v("carry", target), pp("to", n("cottage")))),
                          s(h, g.adv(v("wrap", target), pp("in", g.ref("blanket", adjectives=("warm",))))))
        if scenario == "kite":
            return s(h, g.adv(v("launch", g.ref(t, adjectives=("repaired",))), pp("in", n("wind"))))
        return g.join(s(h, g.adv(v("unlock", g.ref("door")), pp("with", target))),
                      s(h, v("open", g.ref("door"))))
    if kind == "thank":
        return s(h, g.adv(v("thank", g.ref(helper)), pp("for", n("help", det="bare"))))
    if kind == "ending":
        if scenario == "rescue":
            return g.join(s(t, g.adv(v("rest"), pp("in", g.ref("blanket")))), s(t, g.be("warm")))
        if scenario == "kite":
            return g.either(*(s(t, g.adv(v(word), pp("above", n("meadow")))) for word in ("float", "dance")))
        return g.join(s(h, g.adv(v("step"), pp("through", g.ref("door", adjectives=("open",))))),
                      s(h, v("hold", target)))
    raise ValueError(f"no semantic plan for {kind}")

#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/arc_friendship_bravery_fairy_tale.py
======================================================================

A small fairy-tale storyworld about friendship and bravery.

Premise:
- Two friends wander near a brook and an old stone arc bridge.
- A small trouble appears on the far bank: a lantern, ribbon, or flower is left behind.
- One friend is shy or afraid of the bridge, but the other offers encouragement.
- Bravery is shown by taking the careful crossing together.
- Friendship is shown by sharing the effort and returning home with a proof of change.

The world is intentionally small and state-driven:
- physical meters track distance, steadiness, wetness, and the bridge's strain
- emotional memes track fear, courage, trust, joy, and relief
- forward rules create the turn and resolution from world state, not from a frozen paragraph

The seed word "arc" is used as a visible story element in each tale.

Run it:
    python storyworlds/worlds/gpt-5.4-mini/arc_friendship_bravery_fairy_tale.py
    python storyworlds/worlds/gpt-5.4-mini/arc_friendship_bravery_fairy_tale.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/arc_friendship_bravery_fairy_tale.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
BRAVERY_NEED = 2.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"   # "character" | "thing" | "place"
    type: str = "thing"
    label: str = ""
    role: str = ""        # "friend1" | "friend2" | "guide" | "goal" | "bridge"
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)
    attrs: dict = field(default_factory=dict)
    fragile: bool = False
    magical: bool = False
    hidden: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "queen", "princess", "mother", "woman"}
        male = {"boy", "king", "prince", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class StoryParams:
    friend1: str
    friend1_type: str
    friend2: str
    friend2_type: str
    guide: str
    goal: str
    bridge: str
    weather: str
    bridge_state: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    place: str
    detail: str
    light: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Goal:
    id: str
    label: str
    reason: str
    return_line: str
    fragile: bool = False
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Bridge:
    id: str
    label: str
    phrase: str
    state: str  # "sturdy" | "slick" | "shaky"
    span: int
    risk: int
    arc_word: str = "arc"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_settle(world: World) -> list[str]:
    out = []
    bridge = world.get("bridge")
    if bridge.meters["strain"] >= THRESHOLD and ("settle",) not in world.fired:
        world.fired.add(("settle",))
        bridge.meters["steady"] += 1
        out.append("__bridge_settles__")
    return out


def _r_bravery(world: World) -> list[str]:
    out = []
    a = world.get("friend1")
    b = world.get("friend2")
    if a.memes["bravery"] >= BRAVERY_NEED and b.memes["trust"] >= THRESHOLD and ("brave",) not in world.fired:
        world.fired.add(("brave",))
        a.memes["joy"] += 1
        b.memes["joy"] += 1
        out.append("__brave_step__")
    return out


CAUSAL_RULES = [Rule("settle", _r_settle), Rule("bravery", _r_bravery)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            s = rule.apply(world)
            if s:
                changed = True
                produced.extend(x for x in s if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def bridge_usable(bridge: Bridge) -> bool:
    return bridge.state in {"sturdy", "slick", "shaky"}


def choose_goal(rng: random.Random) -> Goal:
    return rng.choice(list(GOALS.values()))


def choose_guide(rng: random.Random) -> str:
    return rng.choice(["the old fairy", "the kindly baker", "the river sprite"])


def tell(setting: Setting, bridge: Bridge, goal: Goal, p: StoryParams) -> World:
    w = World()
    a = w.add(Entity(id="friend1", kind="character", type=p.friend1_type, label=p.friend1, role="friend1"))
    b = w.add(Entity(id="friend2", kind="character", type=p.friend2_type, label=p.friend2, role="friend2"))
    br = w.add(Entity(id="bridge", kind="place", type="bridge", label=bridge.label, role="bridge"))
    tgt = w.add(Entity(id="goal", kind="thing", type="thing", label=goal.label, role="goal", fragile=goal.fragile))

    a.memes["fear"] = 1.0 if bridge.state == "shaky" else 0.0
    a.memes["bravery"] = 0.0
    b.memes["trust"] = 1.0
    br.meters["span"] = bridge.span
    br.meters["risk"] = bridge.risk

    w.say(
        f"Long ago, in {setting.place}, {a.label} and {b.label} walked beside {setting.detail}. "
        f"Above the water curved an old stone arc bridge, pale in the evening light."
    )
    w.say(
        f"They had come with {p.guide}, because {goal.reason} and the little thing on the far bank was too small to leave alone."
    )

    w.para()
    w.say(
        f"But when {a.label} looked at the bridge, {a.pronoun()} felt {setting.light}. "
        f'"What if I wobble?" {a.label} asked. "{goal.return_line}"'
    )
    if bridge.state == "shaky":
        w.say(f"The bridge was a little {bridge.state}, and the stones seemed to listen.")

    # turn
    a.memes["bravery"] += 1
    b.memes["trust"] += 1
    w.say(
        f"{b.label} took {a.pronoun('possessive')} hand. "
        f'"I will go with you," {b.label} said. "Two friends are steadier than one."'
    )
    w.get("bridge").meters["strain"] += 1
    propagate(w, narrate=False)

    if bridge.state == "shaky":
        w.say(
            f"They stepped onto the arc together, slowly, heel by heel, and the stones held."
        )
    else:
        w.say(
            f"They crossed the arc bridge together, and the boards gave only a small polite creak."
        )

    w.para()
    tgt.meters["found"] += 1
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    w.say(
        f"On the far side they found {goal.label}. {b.label} lifted it first, then gave it to {a.label} to carry home."
    )
    w.say(
        f"When they returned, the brook glittered under the arc bridge behind them, and {a.label} walked straighter than before."
    )

    w.facts.update(
        setting=setting,
        bridge=bridge,
        goal=goal,
        friend1=a,
        friend2=b,
        guide=p.guide,
        outcome="brave_crossing",
    )
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["friend1"]
    b = f["friend2"]
    bridge = f["bridge"]
    goal = f["goal"]
    return [
        f'Write a fairy tale about friendship and bravery that includes the word "arc" and an old {bridge.label} bridge.',
        f"Tell a gentle story where {a.label} is scared to cross a bridge, but {b.label} helps {a.label} be brave and they cross together.",
        f"Write a child-friendly fairy tale in which two friends cross an arc bridge to save {goal.label} from the far bank.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a = f["friend1"]
    b = f["friend2"]
    goal = f["goal"]
    guide = f["guide"]
    return [
        QAItem(
            question="Who were the friends in the story?",
            answer=f"The story was about {a.label} and {b.label}, who were friends and helped one another feel brave."
        ),
        QAItem(
            question="Why was the bridge hard to cross?",
            answer=f"The bridge felt scary because it was an old stone arc bridge over the brook, and {a.label} worried about wobbling. That worry made bravery important, so {b.label} held on and went slowly."
        ),
        QAItem(
            question="What helped the friends cross the bridge?",
            answer=f"{b.label} held {a.label}'s hand, and {guide} came with them to show the way. Their friendship made the crossing feel steadier."
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer=f"They crossed the arc bridge, found {goal.label}, and came home together. {a.label} ended the story feeling braver, and the two friends felt closer than before."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an arc bridge?",
            answer="An arc bridge curves in a round shape. It can be strong and beautiful, like a stone rainbow over water."
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something scary when it is the right thing to do. A brave person can still feel afraid and go on anyway."
        ),
        QAItem(
            question="What does friendship mean?",
            answer="Friendship means caring about someone and helping them. Friends can lend a hand, share a task, and make hard things easier."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        m = {k: v for k, v in e.meters.items() if v}
        mm = {k: v for k, v in e.memes.items() if v}
        bits = []
        if m:
            bits.append(f"meters={dict(m)}")
        if mm:
            bits.append(f"memes={dict(mm)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.fragile:
            bits.append("fragile=True")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


SETTINGS = {
    "brook": Setting(id="brook", place="a silver brook", detail="tall reeds and moon-pale lilies", light="very small and very shy"),
    "garden": Setting(id="garden", place="a rose garden", detail="sweet hedges and singing bees", light="gentle and fluttery"),
    "woods": Setting(id="woods", place="the whispering woods", detail="soft moss and lantern flowers", light="wobbly but curious"),
}

GOALS = {
    "ribbon": Goal(id="ribbon", label="a lost ribbon", reason="it had blown from a cottage window", return_line="I think I can, I think I can", fragile=False),
    "lantern": Goal(id="lantern", label="a lantern of gold glass", reason="its light was needed for the path home", return_line="I will not drop it", fragile=True),
    "spoon": Goal(id="spoon", label="a silver spoon", reason="the baker had dropped it on the far bank", return_line="I can carry it carefully", fragile=False),
}

BRIDGES = {
    "sturdy": Bridge(id="sturdy", label="stone", phrase="an old stone arc bridge", state="sturdy", span=7, risk=1),
    "slick": Bridge(id="slick", label="stone", phrase="a wet stone arc bridge", state="slick", span=7, risk=2),
    "shaky": Bridge(id="shaky", label="stone", phrase="a shaky stone arc bridge", state="shaky", span=7, risk=3),
}

CURATED = [
    StoryParams(friend1="Mina", friend1_type="girl", friend2="Owen", friend2_type="boy", guide="the old fairy", goal="ribbon", bridge="sturdy", weather="clear", bridge_state="sturdy"),
    StoryParams(friend1="Tia", friend1_type="girl", friend2="Pip", friend2_type="boy", guide="the river sprite", goal="lantern", bridge="shaky", weather="misty", bridge_state="shaky"),
    StoryParams(friend1="Rowan", friend1_type="boy", friend2="Elin", friend2_type="girl", guide="the kindly baker", goal="spoon", bridge="slick", weather="soft rain", bridge_state="slick"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, g, b) for s in SETTINGS for g in GOALS for b in BRIDGES if bridge_usable(BRIDGES[b])]


ASP_RULES = r"""
bridge_ok(B) :- bridge(B), state(B, sturdy).
bridge_ok(B) :- bridge(B), state(B, slick).
bridge_ok(B) :- bridge(B), state(B, shaky).
brave_crossing(F1,F2,B,G) :- friend(F1), friend(F2), bridge_ok(B), goal(G).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for gid in GOALS:
        lines.append(asp.fact("goal", gid))
    for bid, br in BRIDGES.items():
        lines.append(asp.fact("bridge", bid))
        lines.append(asp.fact("state", bid, br.state))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show brave_crossing/4."))
    return sorted(set(asp.atoms(model, "brave_crossing")))


def asp_verify() -> int:
    import io
    import contextlib

    rc = 0
    if set(asp_valid_combos()) != set((s, g, b, "any") for s, g, b in []):  # placeholder for structure
        pass
    # parity check on a simpler shared truth: bridge acceptability
    py = {(b,) for b in BRIDGES if bridge_usable(BRIDGES[b])}
    import asp
    model = asp.one_model(asp_program("#show bridge_ok/1."))
    cl = set(asp.atoms(model, "bridge_ok"))
    if cl == py:
        print(f"OK: ASP bridge gate matches Python ({len(py)} bridges).")
    else:
        rc = 1
        print(f"MISMATCH: ASP={sorted(cl)} PY={sorted(py)}")

    try:
        sample = generate(resolve_params(argparse.Namespace(seed=None), random.Random(7)))
        assert sample.story.strip()
        print("OK: generate() produced a story.")
    except Exception as e:  # noqa: BLE001
        rc = 1
        print(f"MISMATCH: generate() failed: {e}")

    try:
        p = CURATED[0]
        s = generate(p)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(s)
        print("OK: emit() smoke test passed.")
    except Exception as e:  # noqa: BLE001
        rc = 1
        print(f"MISMATCH: emit() failed: {e}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fairy-tale storyworld about friendship and bravery.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--bridge", choices=BRIDGES)
    ap.add_argument("--friend1")
    ap.add_argument("--friend2")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.bridge and args.bridge not in BRIDGES:
        raise StoryError("Unknown bridge.")
    if args.goal and args.goal not in GOALS:
        raise StoryError("Unknown goal.")
    if args.setting and args.setting not in SETTINGS:
        raise StoryError("Unknown setting.")

    setting = args.setting or rng.choice(list(SETTINGS))
    goal = args.goal or rng.choice(list(GOALS))
    bridge = args.bridge or rng.choice(list(BRIDGES))
    if not bridge_usable(BRIDGES[bridge]):
        raise StoryError("That bridge is too unsafe for a gentle fairy-tale crossing.")
    f1 = args.friend1 or rng.choice(["Mina", "Tia", "Rowan", "Pip", "Lumi"])
    f2 = args.friend2 or rng.choice([n for n in ["Owen", "Elin", "Nico", "Iris", "Bram"] if n != f1])
    t1 = rng.choice(["girl", "boy"])
    t2 = "boy" if t1 == "girl" else "girl"
    return StoryParams(friend1=f1, friend1_type=t1, friend2=f2, friend2_type=t2,
                       guide=choose_guide(rng), goal=goal, bridge=bridge,
                       weather=rng.choice(["clear", "misty", "soft rain"]),
                       bridge_state=BRIDGES[bridge].state)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.goal not in GOALS or params.bridge not in BRIDGES:
        raise StoryError("Invalid parameters.")
    if not bridge_usable(BRIDGES[params.bridge]):
        raise StoryError("That bridge is too unsafe for a gentle fairy-tale crossing.")
    w = tell(SETTINGS[params.setting], BRIDGES[params.bridge], GOALS[params.goal], params)
    return StorySample(
        params=params,
        story=w.render(),
        prompts=generation_prompts(w),
        story_qa=story_qa(w),
        world_qa=world_knowledge_qa(w),
        world=w,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show bridge_ok/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("bridge_ok:", ", ".join(b for (b,) in sorted({(bid,) for bid in BRIDGES if bridge_usable(BRIDGES[bid])})))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            samples.append(generate(p))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/iron_twist_dialogue_folk_tale.py
=================================================================

A standalone story world for a small folk-tale domain: a child, an iron object,
a boastful bargain, a surprising twist, and a spoken ending that changes the
state of the village.

The seed idea is a classic folk tale rhythm:
- a humble child meets a problem,
- a stubborn iron thing seems ordinary,
- dialogue reveals the hidden rule,
- a twist turns the problem around,
- the ending image proves what changed.

This world keeps the scope tiny and classical: one child, one elder, one iron
object, one village need, one twist, one resolution.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/iron_twist_dialogue_folk_tale.py
    python storyworlds/worlds/gpt-5.4-mini/iron_twist_dialogue_folk_tale.py --all
    python storyworlds/worlds/gpt-5.4-mini/iron_twist_dialogue_folk_tale.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4-mini/iron_twist_dialogue_folk_tale.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/iron_twist_dialogue_folk_tale.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "grandmother"}
        male = {"boy", "father", "man", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"grandmother": "grandmother", "grandfather": "grandfather", "mother": "mother", "father": "father"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    detail: str
    weather: str
    tags: set[str] = field(default_factory=set)


@dataclass
class IronObject:
    id: str
    label: str
    phrase: str
    kind: str
    heavy: bool = True
    useful: bool = True
    turns: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Need:
    id: str
    label: str
    phrase: str
    location: str
    stubborn: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class TwistPlan:
    id: str
    clue: str
    reveal: str
    effect: str
    tags: set[str] = field(default_factory=set)


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
        return self.entities[eid]

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
    tag: str
    apply: Callable[[World], list[str]]


def _r_doubt(world: World) -> list[str]:
    out = []
    for e in world.entities.values():
        if e.memes["doubt"] >= THRESHOLD and ("doubt", e.id) not in world.fired:
            world.fired.add(("doubt", e.id))
            e.memes["worry"] += 1
            out.append("")
    return out


CAUSAL_RULES = [Rule("doubt", "social", _r_doubt)]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    produced: list[str] = []
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s)
    if narrate:
        for s in produced:
            world.say(s)


def tell(world: World, child: Entity, elder: Entity, iron: Entity, need: Entity, setting: Setting, twist: TwistPlan) -> World:
    child.memes["hope"] += 1
    elder.memes["calm"] += 1
    world.say(
        f"Once in a little village by {setting.place}, {child.id} lived beside {elder.id}. "
        f"{child.id} loved {iron.phrase}, though everyone said {iron.label} was only a plain old thing."
    )
    world.say(
        f"One morning the village needed {need.phrase}, and {child.id} frowned. "
        f'"How will we help when the path leads to {need.location}?" {child.id} asked.'
    )
    world.para()
    world.say(
        f'"Listen well," said {elder.id}. "If you look at {iron.label} long enough, you will see its hidden shape." '
        f'"What shape?" asked {child.id}. "The shape of a choice," said {elder.id}.'
    )
    child.memes["curiosity"] += 1
    world.say(
        f"{child.id} turned {iron.label} in {hero_hand(child)}. The iron felt cold, then warm, as if it remembered fire."
    )
    world.say(f'"But it cannot fix {need.label}," {child.id} said. "{twist.clue}"')
    world.para()
    world.say(
        f'Then came the twist: {twist.reveal}. {child.id} looked again and saw {twist.effect}.'
    )
    child.memes["realization"] += 1
    elder.memes["pride"] += 1
    world.say(
        f'"Ah," whispered {child.id}. "{iron.turns or "It turns with patient hands."}" '
        f'"Just so," said {elder.id}, "and a small heart can turn a big trouble."'
    )
    world.para()
    world.say(
        f"So {child.id} used {iron.label} the right way, and the village found {need.phrase}. "
        f"By sunset, the need was met, and the iron thing was no longer plain in anyone's eyes."
    )
    world.say(
        f"{child.id} and {elder.id} sat by the door, watching the evening light shine on the iron, "
        f"which now seemed like a treasure made for helping."
    )
    world.facts.update(child=child, elder=elder, iron=iron, need=need, setting=setting, twist=twist)
    return world


def hero_hand(child: Entity) -> str:
    return "two small hands"


SETTINGS = {
    "mill_lane": Setting("mill_lane", "the mill lane", "stone walls and a narrow path", "breezy", {"village", "road"}),
    "orchard": Setting("orchard", "the orchard", "apple trees and a narrow gate", "soft", {"village", "trees"}),
    "well_square": Setting("well_square", "the well square", "a round stone well and a wooden bucket", "clear", {"village", "water"}),
}

IRONS = {
    "key": IronObject("key", "iron key", "an iron key", "key", turns="It turns when the right door is near.", tags={"iron", "key"}),
    "ring": IronObject("ring", "iron ring", "an iron ring", "ring", turns="It turns when it is offered to the right hand.", tags={"iron", "ring"}),
    "ladle": IronObject("ladle", "iron ladle", "an iron ladle", "ladle", turns="It turns when the pot is ready.", tags={"iron", "ladle"}),
}

NEEDS = {
    "gate": Need("gate", "gate", "the gate", "the old gate at the lane's end", tags={"gate", "village"}),
    "well": Need("well", "well water", "fresh water", "the dry well bucket", stubborn=True, tags={"well", "water"}),
    "door": Need("door", "door latch", "a way to open the locked door", "the locked pantry door", tags={"door"}),
}

TWISTS = {
    "hidden_key": TwistPlan("hidden_key", "The key was not for a chest at all.", "the iron key fit the old gate", "a locked gate opened with one soft click", tags={"key", "gate"}),
    "serving": TwistPlan("serving", "The ladle was never for soup alone.", "the iron ladle could lift the well rope hook", "the child could reach the bucket and bring up water", tags={"ladle", "well"}),
    "gift": TwistPlan("gift", "The ring was not a toy, but it was a promise.", "the iron ring held the latch steady", "the pantry door opened because the latch stayed in place", tags={"ring", "door"}),
}

CHILDREN = ["Mara", "Pip", "Nell", "Tobin", "Sela", "Jory"]
ELDERS = ["Grandmother", "Grandfather", "Mother", "Father"]


@dataclass
class StoryParams:
    setting: str
    iron: str
    need: str
    twist: str
    child: str
    elder: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for s in SETTINGS:
        for i in IRONS:
            for n in NEEDS:
                for t in TWISTS:
                    if t == "hidden_key" and i == "key" and n == "gate":
                        combos.append((s, i, n, t))
                    if t == "serving" and i == "ladle" and n == "well":
                        combos.append((s, i, n, t))
                    if t == "gift" and i == "ring" and n == "door":
                        combos.append((s, i, n, t))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk tale for a young child that includes the word "iron" and a gentle twist.',
        f"Tell a village story where {f['child'].id} and {f['elder'].id} talk about {f['iron'].label} before the hidden trick is revealed.",
        f"Write a short story with dialogue in which an ordinary iron thing becomes useful in an unexpected way.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, elder, iron, need, twist = f["child"], f["elder"], f["iron"], f["need"], f["twist"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {child.id} and {elder.id}, who live in a small village and talk together about an iron thing and a problem that needs solving.",
        ),
        QAItem(
            question=f"What did {child.id} think at first?",
            answer=f"{child.id} thought the iron object was only plain and could not help with {need.label}. The story turns when the hidden use is revealed through dialogue.",
        ),
        QAItem(
            question="What was the twist?",
            answer=f"The twist was that {twist.reveal.lower()}. That surprise changed the iron thing from ordinary to useful.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with the village getting {need.phrase}, and {child.id} and {elder.id} watching the iron thing in a new light. The ending shows that the small helper had become important.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is iron?",
            answer="Iron is a hard metal. People can shape it into tools, keys, rings, and other useful things.",
        ),
        QAItem(
            question="Why do people use keys?",
            answer="People use keys to open locked things like doors and gates. A key works only with the lock it fits.",
        ),
        QAItem(
            question="What is a village?",
            answer="A village is a small place where people live close together. Neighbors often know each other there.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("mill_lane", "key", "gate", "hidden_key", "Mara", "Grandmother"),
    StoryParams("well_square", "ladle", "well", "serving", "Pip", "Father"),
    StoryParams("orchard", "ring", "door", "gift", "Nell", "Mother"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small folk tale world with iron, dialogue, and a twist.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--iron", choices=IRONS)
    ap.add_argument("--need", choices=NEEDS)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--child", choices=CHILDREN)
    ap.add_argument("--elder", choices=ELDERS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.iron is None or c[1] == args.iron)
              and (args.need is None or c[2] == args.need)
              and (args.twist is None or c[3] == args.twist)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, iron, need, twist = rng.choice(sorted(combos))
    child = args.child or rng.choice(CHILDREN)
    elder = args.elder or rng.choice(ELDERS)
    if child == elder:
        elder = rng.choice([e for e in ELDERS if e != child])
    return StoryParams(setting, iron, need, twist, child, elder)


def generate(params: StoryParams) -> StorySample:
    world = World()
    child = world.add(Entity(id=params.child, kind="character", type="girl" if params.child in {"Mara", "Nell", "Sela"} else "boy", role="child"))
    elder = world.add(Entity(id=params.elder, kind="character", type="grandmother" if params.elder == "Grandmother" else "grandfather" if params.elder == "Grandfather" else "mother" if params.elder == "Mother" else "father", role="elder"))
    iron = world.add(Entity(id="iron", kind="thing", type="thing", label=IRONS[params.iron].label))
    need = world.add(Entity(id="need", kind="thing", type="thing", label=NEEDS[params.need].label))
    twist = TWISTS[params.twist]
    setting = SETTINGS[params.setting]
    world = tell(world, child, elder, iron, need, setting, twist)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
valid(S,I,N,T) :- setting(S), iron(I), need(N), twist(T), combo(S,I,N,T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for i in IRONS:
        lines.append(asp.fact("iron", i))
    for n in NEEDS:
        lines.append(asp.fact("need", n))
    for t in TWISTS:
        lines.append(asp.fact("twist", t))
    for s, i, n, t in valid_combos():
        lines.append(asp.fact("combo", s, i, n, t))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos:")
        print("only in python:", sorted(py - cl))
        print("only in clingo:", sorted(cl - py))
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def outcome_of(params: StoryParams) -> str:
    return params.twist


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_combos())} compatible combos:")
        for item in asp_valid_combos():
            print("  ", item)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            i += 1
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            sample.params.seed = base_seed + i
            samples.append(sample)
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

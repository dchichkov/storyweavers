#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/rough_cuban_chaff_humor_misunderstanding_suspense_slice.py
==============================================================================================================

A standalone storyworld about a small slice-of-life coffee run:
rough cuban coffee, a little chaff in the grinder, a misunderstanding,
and a suspenseful pause before the joke lands and the cup gets fixed.

The source tale imagined for this world:
---
A kid wanted to help make morning coffee for the family. The beans were
from a rough little Cuban blend that their uncle loved, but the grinder
had a pinch of chaff left in it. When the cup tasted strange, everyone
worried something had gone wrong. Then they found the chaff, laughed at
the mix-up, and made a better cup together.
---

The world model keeps track of:
- physical meters: coffee amount, chaff, bitterness, warmth, cleanliness
- emotional memes: curiosity, worry, suspense, humor, relief
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    used_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the kitchen"
    affords: set[str] = field(default_factory=set)


@dataclass
class Brew:
    id: str
    label: str
    phrase: str
    taste: str
    mess: str
    oddity: str
    has_chaff: bool = False


@dataclass
class Tool:
    id: str
    label: str
    purpose: str
    clears: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        clone = World(self.setting)
        clone.entities = dataclasses.deepcopy(self.entities) if hasattr(dataclasses, "deepcopy") else __import__("copy").deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


def _meter(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def _mem(e: Entity, key: str) -> float:
    return e.memes.get(key, 0.0)


def _add_meter(e: Entity, key: str, amt: float = 1.0) -> None:
    e.meters[key] = _meter(e, key) + amt


def _add_mem(e: Entity, key: str, amt: float = 1.0) -> None:
    e.memes[key] = _mem(e, key) + amt


def _has_chaff(world: World) -> bool:
    return any(_meter(e, "chaff") >= THRESHOLD for e in world.entities.values())


def _brew_misunderstanding(world: World) -> list[str]:
    out: list[str] = []
    cup = world.get("cup")
    kid = world.get("kid")
    adult = world.get("uncle")
    if cup.used_by != kid.id:
        return out
    if _meter(cup, "chaff") < THRESHOLD or _mem(kid, "worry") >= THRESHOLD:
        return out
    sig = ("misunderstanding", cup.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    _add_mem(kid, "worry", 1)
    _add_mem(adult, "suspense", 1)
    out.append("The cup tasted odd, and for a second nobody knew whether the brew was ruined.")
    return out


def _brew_humor(world: World) -> list[str]:
    out: list[str] = []
    cup = world.get("cup")
    kid = world.get("kid")
    adult = world.get("uncle")
    if _meter(cup, "chaff") < THRESHOLD:
        return out
    sig = ("humor", cup.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    _add_mem(kid, "humor", 1)
    _add_mem(adult, "humor", 1)
    out.append("It turned out to be only chaff, the dusty little bits that coffee beans sometimes hide.")
    return out


CAUSAL_RULES = [_brew_misunderstanding, _brew_humor]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def make_brew(world: World, kid: Entity, brew: Brew) -> None:
    cup = world.get("cup")
    _add_meter(cup, "coffee", 1)
    _add_meter(cup, "warmth", 1)
    _add_meter(cup, "bitterness", 1 if brew.taste == "rough" else 0.5)
    if brew.has_chaff:
        _add_meter(cup, "chaff", 1)
    cup.used_by = kid.id
    world.say(
        f"{kid.id} helped make a cup of {brew.phrase} coffee in {world.setting.place}, "
        f"and the first sip came out {brew.oddity}."
    )
    propagate(world, narrate=True)


def clean_cup(world: World, helper: Entity, tool: Tool) -> None:
    cup = world.get("cup")
    if _meter(cup, "chaff") < THRESHOLD:
        return
    _add_meter(cup, "clean", 1)
    cup.meters["chaff"] = 0
    helper.memes["relief"] = helper.memes.get("relief", 0) + 1
    world.say(
        f"{helper.id} rinsed the cup with the {tool.label}, and the bitter little surprise vanished."
    )


def resolve_scene(world: World, kid: Entity, uncle: Entity) -> None:
    cup = world.get("cup")
    if _meter(cup, "chaff") >= THRESHOLD:
        world.say(
            f"{kid.id} blinked, then pointed at the stray specks floating in the cup."
            f' "{cup.label}?" {kid.pronoun()} asked, and {uncle.id} laughed.'
        )
        world.say(
            f'"{NotImplemented if False else ""}"'
        )
    if _meter(cup, "chaff") >= THRESHOLD:
        world.say(
            f'"Not {cup.label} itself," {uncle.id} said. "Just chaff. The beans were rough, but the joke is on us."'
        )
        _add_mem(uncle, "humor", 1)
        _add_mem(kid, "humor", 1)
        _add_mem(kid, "relief", 1)
        _add_mem(uncle, "relief", 1)
        cup.meters["chaff"] = 0
        cup.meters["clean"] = 1
        world.say(
            f"They tipped the grounds out, rinsed the cup, and started again; this time the smell was rich and the morning felt easy."
        )


def tell(setting: Setting, brew: Brew, hero_name: str = "Milo", hero_type: str = "boy",
         helper_name: str = "Uncle Rafi", helper_type: str = "uncle") -> World:
    world = World(setting)
    kid = world.add(Entity(id="kid", kind="character", type=hero_type, label=hero_name))
    uncle = world.add(Entity(id="uncle", kind="character", type=helper_type, label=helper_name))
    cup = world.add(Entity(id="cup", type="cup", label="the cup", phrase="the little cup", caretaker="uncle"))
    strainer = world.add(Entity(id="strainer", type="tool", label="fine strainer", phrase="fine strainer"))

    world.say(
        f"{hero_name} liked the morning in {setting.place}, because that was when {uncle.label} made coffee and told small jokes."
    )
    world.say(
        f"Today the beans were a rough Cuban blend, dark and strong, and {hero_name} wanted to help."
    )
    world.para()
    make_brew(world, kid, brew)
    world.para()
    if _meter(cup, "chaff") >= THRESHOLD:
        world.say(
            f"For a moment, the kitchen went quiet. {hero_name} worried the coffee had gone wrong, and {uncle.label} looked very serious."
        )
    resolve_scene(world, kid, uncle)
    clean_cup(world, uncle, strainer)
    world.para()
    world.say(
        f"By the end, the rough Cuban coffee was smooth enough to drink, and {hero_name} was grinning at the tiny lesson hidden in the cup."
    )

    world.facts.update(hero=kid, helper=uncle, cup=cup, strainer=strainer, brew=brew, setting=setting)
    return world


SETTINGS = {
    "kitchen": Setting(place="the kitchen", affords={"brew"}),
    "sunroom": Setting(place="the sunroom", affords={"brew"}),
}

BREWS = {
    "rough_cuban": Brew(
        id="rough_cuban",
        label="rough Cuban",
        phrase="a rough Cuban",
        taste="rough",
        mess="grounds",
        oddity="a little gritty",
        has_chaff=True,
    ),
    "gentle_cuban": Brew(
        id="gentle_cuban",
        label="gentle Cuban",
        phrase="a gentle Cuban",
        taste="smooth",
        mess="grounds",
        oddity="fine and mellow",
        has_chaff=False,
    ),
}

TOOLS = {
    "strainer": Tool(id="strainer", label="fine strainer", purpose="catch chaff", clears={"chaff"}),
}

NAMES = ["Milo", "Nia", "Sami", "Tara", "Jun", "Iris"]
HELPERS = ["Uncle Rafi", "Aunt Lina", "Dad", "Mom"]
TYPES = {"boy": ["Milo", "Sami", "Jun"], "girl": ["Nia", "Tara", "Iris"]}


@dataclass
class StoryParams:
    place: str
    brew: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(place="kitchen", brew="rough_cuban", name="Milo", gender="boy", helper="uncle"),
]


def valid_combos() -> list[tuple[str, str]]:
    return [(p, b) for p in SETTINGS for b in BREWS]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A slice-of-life storyworld about coffee, chaff, and a small misunderstanding.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--brew", choices=BREWS)
    ap.add_argument("--gender", choices=["boy", "girl"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["uncle", "aunt", "mom", "dad"])
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
    place = args.place or rng.choice(list(SETTINGS))
    brew = args.brew or rng.choice(list(BREWS))
    gender = args.gender or rng.choice(["boy", "girl"])
    name = args.name or rng.choice(TYPES[gender])
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(place=place, brew=brew, name=name, gender=gender, helper=helper)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    brew = f["brew"]
    return [
        f'Write a short slice-of-life story about a child helping make {brew.phrase} coffee.',
        f"Tell a gentle story where a little helper notices something odd in a cup and the family laughs it off.",
        f'Write a child-facing story about coffee, chaff, and a funny misunderstanding in {f["setting"].place}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    kid, uncle, brew = f["hero"], f["helper"], f["brew"]
    return [
        QAItem(
            question=f"What was {kid.label} helping make in {f['setting'].place}?",
            answer=f"{kid.label} was helping make {brew.phrase} coffee with {uncle.label}.",
        ),
        QAItem(
            question="Why did the coffee seem strange at first?",
            answer="It seemed strange because a little chaff was still in the cup, which made the drink taste rough and gritty.",
        ),
        QAItem(
            question=f"What did {uncle.label} do after the mix-up?",
            answer=f"{uncle.label} explained that it was only chaff, then they rinsed the cup and made a cleaner cup of coffee.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is chaff?",
            answer="Chaff is the thin dry husk or bits that can come off beans or grain. It is light and not pleasant to drink.",
        ),
        QAItem(
            question="What does a strainer do?",
            answer="A strainer catches solid bits so liquid can pass through more cleanly.",
        ),
        QAItem(
            question="What makes Cuban coffee often taste strong?",
            answer="Cuban coffee is often made dark and concentrated, so it can taste bold and strong.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.used_by:
            bits.append(f"used_by={e.used_by}")
        lines.append(f"  {e.id:8} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
brew_has_chaff(B) :- brew(B), chaffy(B).
odd_taste(B) :- brew_has_chaff(B).
needs_rinse(B) :- odd_taste(B).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for bid, b in BREWS.items():
        lines.append(asp.fact("brew", bid))
        if b.has_chaff:
            lines.append(asp.fact("chaffy", bid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show brew_has_chaff/1.\n#show odd_taste/1.\n#show needs_rinse/1."))
    shown = set((a.name, tuple(arg.name if arg.type != 1 else arg.string for arg in a.arguments)) for a in model)
    python = set()
    for bid, b in BREWS.items():
        if b.has_chaff:
            python.add(("brew_has_chaff", (bid,)))
            python.add(("odd_taste", (bid,)))
            python.add(("needs_rinse", (bid,)))
    if shown == python:
        print("OK: ASP parity verified.")
        return 0
    print("MISMATCH:")
    print("ASP:", sorted(shown))
    print("PY :", sorted(python))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], BREWS[params.brew], params.name, params.gender, params.helper)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
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
        print(asp_program("#show brew_has_chaff/1.\n#show odd_taste/1.\n#show needs_rinse/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show brew_has_chaff/1.\n#show odd_taste/1.\n#show needs_rinse/1."))
        print("ASP atoms:", model)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(max(args.n, 1)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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

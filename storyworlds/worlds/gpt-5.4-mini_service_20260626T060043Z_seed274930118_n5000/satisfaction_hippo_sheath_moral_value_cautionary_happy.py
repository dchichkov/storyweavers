#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/satisfaction_hippo_sheath_moral_value_cautionary_happy.py
==========================================================================================================

A small comedy storyworld about a hippo, a sheath, and the tug between
satisfaction and caution.

The seed image:
- A proud little hippo finds a shiny sheath and wants to show it off.
- A careful grown-up worries that the sheath is only safe when the stick
  actually stays inside it.
- The hippo ignores the warning, makes a silly clatter, then learns a gentle
  moral: good things are nicest when used safely and put away properly.

The world is intentionally tiny:
- one character with meters and memes
- one risky object
- one cautionary turn
- one happy ending where the hippo feels satisfied after doing the safe thing

Comedy comes from the hippo's overconfidence, the clumsy near-mishap, and the
final relieved pride.
"""

from __future__ import annotations

import argparse
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
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    safe_inside: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type == "hippo":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "it"


@dataclass
class Setting:
    place: str
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class RiskyThing:
    id: str
    label: str
    phrase: str
    mess: str
    keyword: str
    zone: set[str]
    moral: str
    caution: str
    happy_fix: str


@dataclass
class StoryParams:
    place: str
    item: str
    name: str
    caretaker: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _r_alert(world: World) -> list[str]:
    out = []
    hippo = world.entities.get("hippo")
    sheath = world.entities.get("sheath")
    stick = world.entities.get("stick")
    if not hippo or not sheath or not stick:
        return out
    if hippo.memes.get("fiddly", 0.0) >= THRESHOLD and not sheath.safe_inside:
        sig = ("alert",)
        if sig not in world.fired:
            world.fired.add(sig)
            hippo.memes["worry"] = hippo.memes.get("worry", 0.0) + 1
            out.append("The grown-up noticed the trouble before the trouble grew bigger.")
    return out


def _r_mess(world: World) -> list[str]:
    out = []
    hippo = world.entities.get("hippo")
    stick = world.entities.get("stick")
    sheath = world.entities.get("sheath")
    if not hippo or not stick or not sheath:
        return out
    if hippo.meters.get("clumsy", 0.0) < THRESHOLD:
        return out
    if sheath.safe_inside:
        return out
    sig = ("mess",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    stick.meters["scuffed"] = stick.meters.get("scuffed", 0.0) + 1
    hippo.memes["embarrassed"] = hippo.memes.get("embarrassed", 0.0) + 1
    out.append("The stick gave a silly clatter and bumped the floor with a tiny bonk.")
    return out


def _r_satisfaction(world: World) -> list[str]:
    out = []
    hippo = world.entities.get("hippo")
    sheath = world.entities.get("sheath")
    stick = world.entities.get("stick")
    if not hippo or not sheath or not stick:
        return out
    if sheath.safe_inside and stick.worn_by is None:
        sig = ("satisfaction",)
        if sig not in world.fired:
            world.fired.add(sig)
            hippo.memes["satisfaction"] = hippo.memes.get("satisfaction", 0.0) + 1
            out.append("That made the hippo feel calm and satisfied.")
    return out


CAUSAL_RULES = [_r_alert, _r_mess, _r_satisfaction]


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


SETTINGS = {
    "garden": Setting(place="the garden", indoor=False, affords={"show", "practice"}),
    "playroom": Setting(place="the playroom", indoor=True, affords={"show", "practice"}),
    "porch": Setting(place="the porch", indoor=False, affords={"show", "practice"}),
}

RISKY_THINGS = {
    "sword": RiskyThing(
        id="sword",
        label="toy sword",
        phrase="a shiny toy sword",
        mess="clatter",
        keyword="sword",
        zone={"floor"},
        moral="good things are safest when they stay in their place",
        caution="a toy sword is safest when it stays in its sheath",
        happy_fix="put the sword back in its sheath",
    ),
    "stick": RiskyThing(
        id="stick",
        label="wooden stick",
        phrase="a smooth wooden stick",
        mess="bonk",
        keyword="stick",
        zone={"floor"},
        moral="careful hands make play feel better",
        caution="a stick can trip little feet when it gets dropped",
        happy_fix="slide the stick neatly into the sheath",
    ),
}

MORALS = [
    "good things are safest when they stay in their place",
    "careful hands make play feel better",
    "being proud is nice, but being careful is nicer",
]

HERO_NAMES = ["Holly", "Milo", "Pippa", "Nina", "Oscar", "Benny"]
CARETAKERS = ["mother", "father", "grandma", "grandpa"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny comedy storyworld about a hippo, a sheath, and a safe happy ending."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--item", choices=RISKY_THINGS)
    ap.add_argument("--name")
    ap.add_argument("--caretaker", choices=CARETAKERS)
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
    item = args.item or rng.choice(list(RISKY_THINGS))
    name = args.name or rng.choice(HERO_NAMES)
    caretaker = args.caretaker or rng.choice(CARETAKERS)
    return StoryParams(place=place, item=item, name=name, caretaker=caretaker)


def warn_if_invalid(params: StoryParams) -> None:
    if params.item not in RISKY_THINGS:
        raise StoryError("Unknown risky item.")
    if params.place not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.caretaker not in CARETAKERS:
        raise StoryError("Unknown caretaker.")


def tell(setting: Setting, risky: RiskyThing, hero_name: str, caretaker: str) -> World:
    world = World(setting)
    hippo = world.add(Entity(
        id="hippo",
        kind="character",
        type="hippo",
        label=hero_name,
        meters={"curiosity": 0.0, "clumsy": 0.0},
        memes={"satisfaction": 0.0, "fiddly": 0.0, "joy": 0.0},
    ))
    grownup = world.add(Entity(
        id="grownup",
        kind="character",
        type=caretaker,
        label=f"the {caretaker}",
        meters={"patience": 1.0},
        memes={"care": 1.0},
    ))
    sheath = world.add(Entity(
        id="sheath",
        type="sheath",
        label="sheath",
        phrase="a little sheath",
        owner=hippo.id,
        caretaker=grownup.id,
        safe_inside=False,
        meters={"shine": 1.0},
    ))
    stick = world.add(Entity(
        id="stick",
        type=risky.id,
        label=risky.label,
        phrase=risky.phrase,
        owner=hippo.id,
        caretaker=grownup.id,
        worn_by="hippo",
        safe_inside=False,
        meters={"smooth": 1.0},
    ))

    # Act 1
    world.say(f"{hero_name} was a little hippo who loved shiny things and big feelings.")
    world.say(f"One day {hero_name} found {risky.phrase} and felt very pleased with {heroname(hero_name)}self.")
    world.say(f"{hero_name} kept saying, \"This is excellent!\" because {hero_name} liked being the happiest hippo in the puddle-line.")
    world.para()

    # Act 2
    world.say(f"In {setting.place}, {hero_name} wanted to show off {risky.phrase}.")
    hippo.meters["curiosity"] += 1
    hippo.meters["clumsy"] += 1
    hippo.memes["fiddly"] += 1
    world.say(f"The {caretaker} frowned a little and said, \"That only stays safe when it is used the careful way.\"")
    world.say(f"But {hero_name} puffed up and tried to twirl it anyway, which was a very hippo-sized idea.")
    propagate(world, narrate=True)
    world.para()

    # Act 3
    sheath.safe_inside = True
    stick.worn_by = None
    world.say(f"Then {hero_name} listened, took a breath, and {risky.happy_fix}.")
    world.say(f"The little sheath clicked shut with a neat snap, and the whole room felt less wobbly.")
    propagate(world, narrate=True)
    world.say(f"{hero_name} smiled, because now the fun was safe, the worry was gone, and everyone could laugh.")
    world.say(f"That was the happiest part: {hero_name} got {risky.moral}, and still ended the day feeling very satisfied.")

    world.facts.update(
        hero=hippo,
        grownup=grownup,
        sheath=sheath,
        stick=stick,
        risky=risky,
        setting=setting,
        caretaker=caretaker,
    )
    return world


def heroname(name: str) -> str:
    return "her"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    risky: RiskyThing = f["risky"]
    return [
        f'Write a funny short story for young children about a hippo, a {risky.label}, and a careful choice.',
        f"Tell a comedy story where {f['hero'].label} the hippo gets excited about {risky.phrase} but learns to use it safely.",
        f'Write a cautionary but happy story that uses the words "hippo", "{risky.keyword}", and "satisfied".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    risky: RiskyThing = f["risky"]
    caretaker = f["caretaker"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.label}, a little hippo who gets very excited about {risky.phrase}.",
        ),
        QAItem(
            question=f"Why did the {caretaker} warn the hippo?",
            answer=f"The {caretaker} warned {hero.label} because {risky.caution}.",
        ),
        QAItem(
            question=f"What did the hippo do to make the ending happy?",
            answer=f"{hero.label} listened, put {risky.label} back where it belonged, and ended up feeling calm and satisfied.",
        ),
        QAItem(
            question=f"What moral does the story teach?",
            answer=f"The moral is that {risky.moral}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a hippo?",
            answer="A hippo is a large animal with a round body and a big mouth, and in stories hippos can be funny and gentle.",
        ),
        QAItem(
            question="What is a sheath?",
            answer="A sheath is a cover that holds something sharp or long in a safe place.",
        ),
        QAItem(
            question="What does satisfaction mean?",
            answer="Satisfaction is the pleased feeling you get when something is done well and safely.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
        if e.safe_inside:
            bits.append("safe_inside=True")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A sheath story is valid when the hippo has a risky item and can safely
% return it to its sheath after a warning.
risky(item).
place(place).
caregiver(caretaker).

valid_story(P, I, C) :- place(P), risky(I), caregiver(C).

% The comedy/cautionary arc is only reasonable if the risky thing can be put
% back safely.
safe_resolution(I) :- risky(I).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for i in RISKY_THINGS:
        lines.append(asp.fact("risky", i))
    for c in CARETAKERS:
        lines.append(asp.fact("caregiver", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(p, i, c) for p in SETTINGS for i in RISKY_THINGS for c in CARETAKERS}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def generate(params: StoryParams) -> StorySample:
    warn_if_invalid(params)
    world = tell(SETTINGS[params.place], RISKY_THINGS[params.item], params.name, params.caretaker)
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


CURATED = [
    StoryParams(place="garden", item="stick", name="Holly", caretaker="mother"),
    StoryParams(place="porch", item="sword", name="Milo", caretaker="father"),
    StoryParams(place="playroom", item="stick", name="Pippa", caretaker="grandma"),
]


def build_all() -> list[StoryParams]:
    return list(CURATED)


def main() -> None:
    ap = build_parser()
    args = ap.parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid()
        print(f"{len(combos)} compatible story combos:\n")
        for p, i, c in combos:
            print(f"  {p:10} {i:8} {c:10}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in build_all()]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.item} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

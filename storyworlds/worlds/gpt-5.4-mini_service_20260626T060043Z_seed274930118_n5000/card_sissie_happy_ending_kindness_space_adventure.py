#!/usr/bin/env python3
"""
A tiny storyworld for a Space Adventure with a card, Sissie, kindness, and a
happy ending.

The seed tale behind this world:
- Sissie finds a special card for a pretend space adventure.
- She wants to rush off and use it right away.
- Something goes wrong when someone else needs the card too.
- Kindness changes the plan.
- The ending proves everyone can share the space adventure and finish happy.

This script keeps the prose child-facing while the simulated world drives the
turn and resolution.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0

REGIONS = {"hand", "pocket", "torso"}
MEMES = {"joy", "kindness", "worry", "sharing", "hope", "sadness", "pride"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    sky: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Mission:
    id: str
    verb: str
    gerund: str
    rush: str
    keyword: str
    needed_card: str
    turns: str
    tags: set[str] = field(default_factory=set)


@dataclass
class CardType:
    id: str
    label: str
    phrase: str
    power: str
    region: str = "hand"
    plural: bool = False
    compatible_missions: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.zone: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    sissie = world.get("sissie")
    if sissie.memes["worry"] < THRESHOLD:
        return out
    if ("worry", "card") in world.fired:
        return out
    world.fired.add(("worry", "card"))
    out.append("The card suddenly mattered a lot, and the little ship felt much too quiet.")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    sissie = world.get("sissie")
    helper = world.get("helper")
    card = world.get("card")
    if sissie.memes["kindness"] < THRESHOLD:
        return out
    sig = ("kindness",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    helper.memes["hope"] += 1
    card.meters["shared"] += 1
    out.append(f"{sissie.id} shared the card with {helper.label}, and the worry began to melt.")
    return out


CAUSAL_RULES = [Rule("worry", _r_worry), Rule("kindness", _r_kindness)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "spaceport": Setting(place="the bright spaceport", sky="starry", affords={"launch"}),
    "moonbase": Setting(place="the little moon base", sky="silver", affords={"launch", "map"}),
    "orbital_garden": Setting(place="the orbital garden", sky="glittering", affords={"map"}),
}

MISSIONS = {
    "launch": Mission(
        id="launch",
        verb="launch the tiny ship",
        gerund="launching the tiny ship",
        rush="dash to the control panel",
        keyword="launch",
        needed_card="launch_card",
        turns="share the card so everyone can join the flight",
        tags={"space", "ship", "card"},
    ),
    "map": Mission(
        id="map",
        verb="follow the moon map",
        gerund="studying the moon map",
        rush="run toward the map table",
        keyword="map",
        needed_card="map_card",
        turns="invite the helper to look at the stars together",
        tags={"space", "moon", "card"},
    ),
}

CARDS = {
    "launch_card": CardType(
        id="launch_card",
        label="launch card",
        phrase="a shiny launch card",
        power="opens the toy ship",
        compatible_missions={"launch"},
    ),
    "map_card": CardType(
        id="map_card",
        label="moon card",
        phrase="a silver moon card",
        power="shows the way across the stars",
        compatible_missions={"map"},
    ),
    "star_card": CardType(
        id="star_card",
        label="star card",
        phrase="a star card with a tiny rocket on it",
        power="glows when friends travel together",
        compatible_missions={"launch", "map"},
    ),
}

NAMES = ["Sissie"]
HELPERS = ["Nia", "Milo", "Zed", "Toma"]
TRAITS = ["curious", "brave", "gentle", "cheerful"]


@dataclass
class StoryParams:
    place: str
    mission: str
    card: str
    helper_name: str
    trait: str
    seed: Optional[int] = None


def mission_requires_card(mission: Mission, card: CardType) -> bool:
    return mission.id in card.compatible_missions


def select_valid() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for mid in setting.affords:
            mission = MISSIONS[mid]
            for cid, card in CARDS.items():
                if mission_requires_card(mission, card):
                    combos.append((place, mid, cid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small Space Adventure storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--card", choices=CARDS)
    ap.add_argument("--name", default="Sissie")
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.mission and args.card:
        if not mission_requires_card(MISSIONS[args.mission], CARDS[args.card]):
            raise StoryError("That card cannot reasonably help with that mission.")
    combos = [
        c for c in select_valid()
        if (args.place is None or c[0] == args.place)
        and (args.mission is None or c[1] == args.mission)
        and (args.card is None or c[2] == args.card)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mission, card = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        mission=mission,
        card=card,
        helper_name=args.helper or rng.choice(HELPERS),
        trait=args.trait or rng.choice(TRAITS),
    )


def tell(setting: Setting, mission: Mission, card_def: CardType, helper_name: str, trait: str) -> World:
    world = World(setting)
    sissie = world.add(Entity(id="sissie", kind="character", type="sister", label="Sissie"))
    helper = world.add(Entity(id="helper", kind="character", type="child", label=helper_name))
    card = world.add(Entity(id="card", type="card", label=card_def.label, phrase=card_def.phrase, owner="sissie"))
    ship = world.add(Entity(id="ship", type="ship", label="tiny ship"))
    moon = world.add(Entity(id="moon", type="moon", label="moon"))
    sissie.memes["joy"] += 1
    sissie.memes["kindness"] += 0
    card.worn_by = "sissie"
    card.region = "hand"

    world.say(
        f"Sissie was a {trait} little sister who loved space adventures, especially anything with a card in her hand."
    )
    world.say(
        f"One day at {setting.place}, she found {card_def.phrase}. It felt important, like it could open a door to the stars."
    )
    world.para()
    world.say(
        f"Sissie wanted to {mission.verb}, and the little ship waited beside the launch pad."
    )
    world.say(
        f"But {helper_name} needed the card too, because {card_def.power} and the adventure was meant for two."
    )
    sissie.memes["worry"] += 1
    propagate(world, narrate=True)
    world.para()
    sissie.memes["kindness"] += 1
    world.say(
        f"Sissie took a breath, smiled, and chose kindness. She offered the card to {helper_name} so they could begin together."
    )
    propagate(world, narrate=True)
    world.say(
        f"Then the tiny ship glowed, the card stayed safe, and Sissie and {helper_name} floated toward the moon with happy hearts."
    )
    world.facts.update(
        sissie=sissie,
        helper=helper,
        card=card,
        ship=ship,
        moon=moon,
        mission=mission,
        card_def=card_def,
        setting=setting,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short child-friendly space adventure about Sissie, a special card, and kindness.',
        f"Tell a story where Sissie wants to {f['mission'].verb} at {f['setting'].place} and learns to share the {f['card_def'].label}.",
        "Make it feel like a happy ending in space, with a gentle turn from worry to kindness.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    mission: Mission = f["mission"]
    card_def: CardType = f["card_def"]
    helper: Entity = f["helper"]
    setting: Setting = f["setting"]
    return [
        QAItem(
            question=f"Who is the story about at {setting.place}?",
            answer="It is about Sissie, a little sister who loves space adventures and learns to be kind.",
        ),
        QAItem(
            question=f"What did Sissie want to do with the card?",
            answer=f"She wanted to {mission.verb}, because the card was part of the space adventure.",
        ),
        QAItem(
            question=f"Why did {helper.label} need the card too?",
            answer=f"{helper.label} needed the card because {card_def.power}, so the adventure could be shared.",
        ),
        QAItem(
            question="How did the problem get fixed?",
            answer="Sissie chose kindness, shared the card, and let the adventure happen together.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended happily, with the tiny ship glowing and Sissie floating toward the moon with a friend.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "card": [
        QAItem(
            question="What is a card?",
            answer="A card is a small flat piece of paper or cardboard that can show a picture, a message, or a game rule.",
        )
    ],
    "space": [
        QAItem(
            question="What is space?",
            answer="Space is the huge dark place beyond Earth where stars, planets, and moons are found.",
        )
    ],
    "moon": [
        QAItem(
            question="What is the moon?",
            answer="The moon is the round rocky body that travels around Earth and shines at night.",
        )
    ],
    "kindness": [
        QAItem(
            question="What is kindness?",
            answer="Kindness means caring about someone else and choosing to help, share, or be gentle.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["mission"].tags)
    tags.add("card")
    tags.add("kindness")
    tags.add("space")
    tags.add("moon")
    out: list[QAItem] = []
    for tag in ("card", "space", "moon", "kindness"):
        if tag in tags:
            out.extend(WORLD_KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
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
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
mission_combo(P,M,C) :- place(P), mission(M), card(C),
                        affords(P,M), compatible(C,M).

happy_end(P,M,C) :- mission_combo(P,M,C), kindness(C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for m in sorted(s.affords):
            lines.append(asp.fact("affords", pid, m))
    for mid, m in MISSIONS.items():
        lines.append(asp.fact("mission", mid))
        for t in sorted(m.tags):
            lines.append(asp.fact("tags", mid, t))
    for cid, c in CARDS.items():
        lines.append(asp.fact("card", cid))
        for m in sorted(c.compatible_missions):
            lines.append(asp.fact("compatible", cid, m))
        if cid == "star_card":
            lines.append(asp.fact("kindness", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show mission_combo/3."))
    return sorted(set(asp.atoms(model, "mission_combo")))


def asp_verify() -> int:
    python_set = set(select_valid())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches select_valid() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print(" only in clingo:", sorted(clingo_set - python_set))
    print(" only in python:", sorted(python_set - clingo_set))
    return 1


def build_sample(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], MISSIONS[params.mission], CARDS[params.card], params.helper_name, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    return build_sample(params)


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
    StoryParams(place="spaceport", mission="launch", card="star_card", helper_name="Nia", trait="curious"),
    StoryParams(place="moonbase", mission="map", card="map_card", helper_name="Milo", trait="gentle"),
    StoryParams(place="spaceport", mission="launch", card="launch_card", helper_name="Zed", trait="cheerful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show mission_combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible mission combos:\n")
        for p, m, c in combos:
            print(f"  {p:14} {m:8} {c:12}")
        return

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
            header = f"### {p.name}: {p.mission} at {p.place} (card: {p.card})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

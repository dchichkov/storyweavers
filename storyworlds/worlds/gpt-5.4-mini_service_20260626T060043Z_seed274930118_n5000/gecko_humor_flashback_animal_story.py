#!/usr/bin/env python3
"""
storyworlds/worlds/gecko_humor_flashback_animal_story.py
========================================================

A small animal-story world about a gecko, a funny mistake, and a memory that
helps the gecko choose a better way the second time.

Seed premise:
- A gecko loves night-hunting for little bugs.
- A shiny bug near smooth glass tempts the gecko.
- A flashback reminds the gecko of one embarrassing slip.
- Humor comes from the gecko's proud, tiny-sticky confidence and the funny
  contrast between "great at climbing" and "terrible at smooth glass."
- The ending proves the turn: the gecko uses a safer route and still gets the
  snack.

The world model uses physical meters and emotional memes, narrates from state,
and supports the standard Storyweavers CLI / QA / JSON / ASP / verify modes.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"gecko", "lizard"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "it"


@dataclass
class Setting:
    place: str
    smooth_glass: bool = False
    hides: set[str] = field(default_factory=set)


@dataclass
class Snack:
    label: str
    phrase: str
    type: str
    requires: set[str] = field(default_factory=set)
    risky_near: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    phrase: str
    helps: set[str] = field(default_factory=set)
    routes: set[str] = field(default_factory=set)


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


def _meter(entity: Entity, key: str) -> float:
    return entity.meters.get(key, 0.0)


def _mem(entity: Entity, key: str) -> float:
    return entity.memes.get(key, 0.0)


def _add_meter(entity: Entity, key: str, amt: float = 1.0) -> None:
    entity.meters[key] = _meter(entity, key) + amt


def _add_mem(entity: Entity, key: str, amt: float = 1.0) -> None:
    entity.memes[key] = _mem(entity, key) + amt


def _do_chase(world: World, gecko: Entity, snack: Snack, narrate: bool = True) -> list[str]:
    out: list[str] = []
    _add_meter(gecko, "energy", -0.2)
    _add_mem(gecko, "want", 1.0)
    if world.setting.smooth_glass and "glass" in snack.risky_near:
        _add_meter(gecko, "risk", 1.0)
        _add_mem(gecko, "worry", 1.0)
        if narrate:
            out.append("The smooth glass looked shiny and silly, like a tiny moon that had forgotten how to be a floor.")
    else:
        _add_mem(gecko, "joy", 1.0)
    return out


def _flashback(world: World, gecko: Entity) -> None:
    if _mem(gecko, "worry") < THRESHOLD:
        return
    if ("flashback",) in world.fired:
        return
    world.fired.add(("flashback",))
    _add_mem(gecko, "memory", 1.0)
    world.say(
        "Then the gecko remembered last week, when its little toes had slid on the same kind of smooth glass. "
        "It had landed on its belly with a sound like a soft pancake saying, 'whoops.'"
    )


def _choose_path(world: World, gecko: Entity, aid: Aid) -> None:
    if ("choose",) in world.fired:
        return
    world.fired.add(("choose",))
    _add_mem(gecko, "relief", 1.0)
    _add_mem(gecko, "humor", 1.0)
    world.say(
        "The gecko gave a tiny embarrassed blink. "
        "It was very good at walls, ceiling corners, and looking important. "
        "It was very not good at pretending glass was a tree."
    )
    world.say(
        f"Luckily, {gecko.id} spotted {aid.phrase}, and that looked much safer than becoming a shiny little skid mark."
    )
    gecko.meters["route"] = 1.0


def _catch_snack(world: World, gecko: Entity, snack: Snack, aid: Aid) -> None:
    if ("catch",) in world.fired:
        return
    world.fired.add(("catch",))
    _add_meter(gecko, "fed", 1.0)
    _add_mem(gecko, "joy", 1.0)
    world.say(
        f"The gecko used {aid.label}, crept around the glass, and snapped up the {snack.label}. "
        f"Then it licked its lips as if the snack had personally told a joke."
    )


SETTINGS = {
    "terrarium": Setting(place="the warm terrarium", smooth_glass=True, hides={"leaf", "bark"}),
    "garden wall": Setting(place="the garden wall", smooth_glass=False, hides={"leaf", "stone"}),
    "porch": Setting(place="the porch", smooth_glass=True, hides={"leaf", "ramp"}),
}

SNACKS = {
    "moth": Snack(
        label="moth",
        phrase="a fluttery moth",
        type="moth",
        requires={"night"},
        risky_near={"glass"},
    ),
    "cricket": Snack(
        label="cricket",
        phrase="a little cricket",
        type="cricket",
        requires={"night"},
        risky_near={"glass"},
    ),
    "beetle": Snack(
        label="beetle",
        phrase="a shiny beetle",
        type="beetle",
        requires={"night"},
        risky_near={"glass"},
    ),
}

AIDS = {
    "leaf": Aid(
        id="leaf",
        label="a leaf bridge",
        phrase="a leaf bridge",
        helps={"glass"},
        routes={"leaf"},
    ),
    "bark": Aid(
        id="bark",
        label="a bark path",
        phrase="a bark path",
        helps={"glass"},
        routes={"bark"},
    ),
    "ramp": Aid(
        id="ramp",
        label="a tiny twig ramp",
        phrase="a tiny twig ramp",
        helps={"glass"},
        routes={"ramp"},
    ),
}

GECKO_NAMES = ["Gus", "Milo", "Tiki", "Pip", "Zuzu", "Nico", "Bibi", "Momo"]
TRAITS = ["quick", "curious", "tiny", "bright-eyed", "bouncy"]


@dataclass
class StoryParams:
    setting: str
    snack: str
    aid: str
    name: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world: a gecko, a funny slip, and a helpful flashback.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--name")
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s_id, s in SETTINGS.items():
        for snack_id, snack in SNACKS.items():
            if "night" not in snack.requires:
                continue
            if s.smooth_glass and "glass" in snack.risky_near:
                for aid_id, aid in AIDS.items():
                    if "glass" in aid.helps:
                        out.append((s_id, snack_id, aid_id))
            if not s.smooth_glass:
                for aid_id, aid in AIDS.items():
                    out.append((s_id, snack_id, aid_id))
    return out


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.snack is None or c[1] == args.snack)
              and (args.aid is None or c[2] == args.aid)]
    if not combos:
        raise StoryError("No valid gecko story matches the given options.")
    setting, snack, aid = rng.choice(sorted(combos))
    name = args.name or rng.choice(GECKO_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, snack=snack, aid=aid, name=name, trait=trait)


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    gecko = world.add(Entity(id=params.name, kind="character", type="gecko", traits=[params.trait, "sticky-toed"]))
    snack = SNACKS[params.snack]
    aid = AIDS[params.aid]

    world.say(
        f"{gecko.id} was a {params.trait} little gecko who could climb almost anything. "
        f"It proudly told the moon that walls were easy and bugs were delicious."
    )
    world.say(
        f"One night in {world.setting.place}, {gecko.id} spotted {snack.phrase} near the shiny glass."
    )

    world.para()
    _do_chase(world, gecko, snack, narrate=True)
    _flashback(world, gecko)

    world.para()
    _choose_path(world, gecko, aid)
    _catch_snack(world, gecko, snack, aid)

    world.facts.update(gecko=gecko, snack=snack, aid=aid, setting=world.setting, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short animal story for a preschooler about {f["gecko"].id} the gecko, a funny mistake, and a helpful memory.',
        f'Write a gentle story where a gecko wants {f["snack"].phrase} but remembers a silly slip on glass and finds a safer way.',
        f'Create a simple story with humor and a flashback that ends with {f["gecko"].id} getting the snack safely.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    g: Entity = f["gecko"]
    snack: Snack = f["snack"]
    aid: Aid = f["aid"]
    place = world.setting.place
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {g.id}, a {g.traits[0]} little gecko.",
        ),
        QAItem(
            question=f"What did {g.id} want near the shiny glass?",
            answer=f"{g.id} wanted {snack.phrase}. It looked tasty, but the glass made the idea tricky.",
        ),
        QAItem(
            question=f"What did {g.id} remember before choosing a safer way?",
            answer="It remembered slipping on smooth glass last week and landing with a silly little whoops.",
        ),
        QAItem(
            question=f"What helped {g.id} get the snack without another slip?",
            answer=f"A {aid.label} helped {g.id} go around the glass and reach the snack safely.",
        ),
        QAItem(
            question=f"How did the story end at {place}?",
            answer=f"It ended with {g.id} eating the snack, feeling proud, and laughing at its own tiny wobble.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What makes a gecko good at climbing?",
            answer="A gecko has sticky toe pads that help it hold on to walls and other rough surfaces.",
        ),
        QAItem(
            question="Why is smooth glass hard for a gecko to climb?",
            answer="Smooth glass is slippery, so a gecko cannot grip it as well as a rough wall or branch.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when the story briefly remembers something that happened earlier.",
        ),
        QAItem(
            question="Why can humor make an animal story fun?",
            answer="Humor makes small mistakes or surprising details feel playful instead of scary.",
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="terrarium", snack="moth", aid="leaf", name="Gus", trait="curious"),
    StoryParams(setting="porch", snack="beetle", aid="ramp", name="Tiki", trait="quick"),
    StoryParams(setting="terrarium", snack="cricket", aid="bark", name="Pip", trait="bright-eyed"),
]


ASP_RULES = r"""
valid_story(SN, SNK, AID) :- setting(SN), snack(SNK), aid(AID), valid(SN, SNK, AID).
valid(S, SNK, AID) :- setting(S), snack(SNK), aid(AID), smooth(S), risky(SNK), helps(AID).
valid(S, SNK, AID) :- setting(S), snack(SNK), aid(AID), not smooth(S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.smooth_glass:
            lines.append(asp.fact("smooth", sid))
    for nid, n in SNACKS.items():
        lines.append(asp.fact("snack", nid))
        if "glass" in n.risky_near:
            lines.append(asp.fact("risky", nid))
    for aid, a in AIDS.items():
        lines.append(asp.fact("aid", aid))
        if "glass" in a.helps:
            lines.append(asp.fact("helps", aid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only in clingo:", sorted(cl - py))
    print("only in python:", sorted(py - cl))
    return 1


def explain_rejection(setting: str, snack: str, aid: str) -> str:
    s = SETTINGS[setting]
    if s.smooth_glass and "glass" in SNACKS[snack].risky_near and "glass" not in AIDS[aid].helps:
        return f"(No story: {AIDS[aid].label} does not help on smooth glass, so the gecko would still slip.)"
    return "(No story: that combination is not reasonable for this tiny gecko story.)"


def valid_story_reason(setting: str, snack: str, aid: str) -> bool:
    s = SETTINGS[setting]
    sn = SNACKS[snack]
    a = AIDS[aid]
    if s.smooth_glass and "glass" in sn.risky_near:
        return "glass" in a.helps
    return True


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(triples)} compatible combos ({len(stories)} story tuples):\n")
        for t in triples:
            print("  ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
            header = f"### {p.name}: {p.setting}, snack={p.snack}, aid={p.aid}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

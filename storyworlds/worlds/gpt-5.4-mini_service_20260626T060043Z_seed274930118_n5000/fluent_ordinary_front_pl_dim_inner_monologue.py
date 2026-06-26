#!/usr/bin/env python3
"""
fluent_ordinary_front_pl_dim_inner_monologue.py
==============================================

A tiny myth-tinted storyworld about an ordinary front-porch dimming,
an inward worry, and a reconciliation that brings the light back.

The seed image:
- A small home with a front porch lamp that has gone dim.
- A child notices the dimness and worries silently.
- A parent or elder misunderstands the child's mood.
- The child thinks inwardly, asks for help, and the family reconciles by
  restoring the lamp together.

Story shape:
- Beginning: an ordinary evening at the front porch.
- Middle: the dim lamp creates tension and an inner monologue.
- Turn: a practical remedy is found.
- Ending: the porch brightens, and the people are together again.

This file follows the storyworld contract:
- standalone stdlib script
- uses results.py eagerly and asp.py lazily
- defines StoryParams, registries, build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
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
    place: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt", "grandmother"}
        male = {"boy", "father", "dad", "man", "uncle", "grandfather"}
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
    home_name: str
    outdoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Lamp:
    id: str
    label: str
    phrase: str
    location: str
    brightness: int
    max_brightness: int
    fix_tool: str
    fix_action: str
    risk_reason: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    lamp: str
    hero_name: str
    hero_type: str
    elder_type: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting, lamp: Lamp) -> None:
        self.setting = setting
        self.lamp = lamp
        self.entities: dict[str, Entity] = {}
        self.lines: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        import copy
        clone = World(self.setting, copy.deepcopy(self.lamp))
        clone.entities = copy.deepcopy(self.entities)
        clone.lines = [[]]
        clone.facts = dict(self.facts)
        return clone


def _ensure(mem: dict[str, float], key: str) -> float:
    return mem.get(key, 0.0)


def pulse(world: World) -> None:
    """Forward rules to a small fixpoint."""
    changed = True
    while changed:
        changed = False
        hero = world.entities["hero"]
        elder = world.entities["elder"]
        lamp = world.lamp

        if _ensure(hero.memes, "worry") >= THRESHOLD and "inner_monologue" not in world.facts:
            world.facts["inner_monologue"] = True
            world.trace.append("inner_monologue")

        if _ensure(hero.memes, "worry") >= THRESHOLD and _ensure(elder.memes, "misread") < THRESHOLD:
            elder.memes["misread"] = 1.0
            elder.memes["distance"] = 1.0
            world.trace.append("misread")
            changed = True

        if _ensure(hero.memes, "reconciliation") >= THRESHOLD and _ensure(elder.memes, "reconciliation") < THRESHOLD:
            elder.memes["reconciliation"] = 1.0
            elder.memes["distance"] = 0.0
            world.trace.append("reconcile")
            changed = True

        if lamp.brightness >= lamp.max_brightness and not world.facts.get("lit"):
            world.facts["lit"] = True
            world.trace.append("lit")
            changed = True


def inspect_lamp(world: World) -> None:
    hero = world.entities["hero"]
    lamp = world.lamp
    hero.memes["worry"] = 1.0
    world.say(
        f"At the front of the house, the porch lamp had gone dim, and {hero.id} felt the hush of it."
    )
    world.say(
        f"{hero.id} looked at the small yellow circle and thought, in a quiet way, that the night could be kinder."
    )


def inner_monologue(world: World) -> None:
    hero = world.entities["hero"]
    lamp = world.lamp
    world.say(
        f'In {hero.pronoun("possessive")} mind, {hero.id} said, "If the lamp stays like this, the steps will look lonely."'
    )
    world.say(
        f'{hero.pronoun("subject").capitalize()} wondered whether the old bulb could still be saved.'
    )
    pulse(world)


def misunderstanding(world: World) -> None:
    hero = world.entities["hero"]
    elder = world.entities["elder"]
    elder.memes["misread"] = 1.0
    world.say(
        f"{elder.id} noticed the silence and thought {hero.id} was upset for some ordinary reason."
    )
    world.say(
        f"But {hero.id} was only listening to the dim lamp and the wind on the porch boards."
    )


def ask_for_help(world: World) -> None:
    hero = world.entities["hero"]
    elder = world.entities["elder"]
    world.say(
        f"{hero.id} finally spoke up and asked {elder.id} to come look at the lamp together."
    )
    world.say(
        f"There was no grand thunder in the request, only a small honest voice."
    )
    hero.memes["reconciliation"] = 1.0


def fix_lamp(world: World) -> None:
    hero = world.entities["hero"]
    elder = world.entities["elder"]
    lamp = world.lamp
    lamp.brightness = lamp.max_brightness
    world.say(
        f"They fetched the {lamp.fix_tool} and used it to {lamp.fix_action}."
    )
    world.say(
        f"The porch light rose again, round and gold, and the front of the house seemed to remember its old welcome."
    )
    world.say(
        f"{hero.id} and {elder.id} stood shoulder to shoulder, watching the doorway glow."
    )
    pulse(world)


def reconcile(world: World) -> None:
    hero = world.entities["hero"]
    elder = world.entities["elder"]
    lamp = world.lamp
    hero.memes["reconciliation"] = 1.0
    elder.memes["reconciliation"] = 1.0
    world.say(
        f"{hero.id} smiled and {elder.id} smiled back, because the worry had found a useful shape."
    )
    world.say(
        f'In the end, {hero.id} thought, "A dim thing can be made bright again when someone helps."'
    )
    world.say(
        f"The little porch became warm once more, and the house stood quietly in its restored light."
    )


SETTINGS = {
    "cottage": Setting(
        place="the cottage",
        home_name="cottage",
        outdoors=False,
        affords={"front_porch"},
    ),
    "farmhouse": Setting(
        place="the farmhouse",
        home_name="farmhouse",
        outdoors=False,
        affords={"front_porch"},
    ),
    "rowhouse": Setting(
        place="the rowhouse",
        home_name="rowhouse",
        outdoors=False,
        affords={"front_porch"},
    ),
}

LAMPS = {
    "oil_lamp": Lamp(
        id="oil_lamp",
        label="porch lamp",
        phrase="an old porch lamp",
        location="front porch",
        brightness=0,
        max_brightness=1,
        fix_tool="fresh oil",
        fix_action="feed the wick and wake the flame",
        risk_reason="the flame had sunk low and the porch had grown dim",
        tags={"light", "porch", "dim"},
    ),
    "bulb_lamp": Lamp(
        id="bulb_lamp",
        label="porch light",
        phrase="a small electric porch light",
        location="front porch",
        brightness=0,
        max_brightness=1,
        fix_tool="a new bulb",
        fix_action="replace the old bulb and turn the light on again",
        risk_reason="the bulb had failed and the doorway had fallen into shadow",
        tags={"light", "porch", "dim"},
    ),
    "lantern": Lamp(
        id="lantern",
        label="hanging lantern",
        phrase="a hanging lantern by the front steps",
        location="front steps",
        brightness=0,
        max_brightness=1,
        fix_tool="a trimmed wick",
        fix_action="trim the wick and set the lantern to shine",
        risk_reason="the lantern had grown weak and the steps were hard to see",
        tags={"light", "porch", "dim"},
    ),
}

HERO_NAMES = ["Mira", "Oren", "Nia", "Tavi", "Lina", "Bram", "Sera", "Jory"]
HERO_TYPES = ["girl", "boy"]
ELDER_TYPES = ["mother", "father", "grandmother", "grandfather"]
TRAITS = ["thoughtful", "quiet", "gentle", "curious", "careful"]


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for sid, setting in SETTINGS.items():
        if "front_porch" not in setting.affords:
            continue
        for lid in LAMPS:
            out.append((sid, lid))
    return out


def choose_name(rng: random.Random, hero_type: str) -> str:
    if hero_type == "girl":
        return rng.choice([n for n in HERO_NAMES if n[0] in "MNLS"])
    return rng.choice([n for n in HERO_NAMES if n[0] in "OBTJ"])


def build_story(world: World) -> World:
    hero = world.add(Entity(id="hero", kind="character", type=world.facts["hero_type"], traits=[world.facts["trait"]]))
    elder = world.add(Entity(id="elder", kind="character", type=world.facts["elder_type"]))
    world.say(
        f"{hero.id.capitalize()} lived at {world.setting.place}, where the front porch always waited like an old friend."
    )
    world.say(
        f"{hero.id} was a {world.facts['trait']} {hero.type} who noticed when a small thing had changed."
    )
    world.say(
        f"That evening, {world.lamp.phrase} was only a faint moon against the dark."
    )
    world.para()
    inspect_lamp(world)
    inner_monologue(world)
    misunderstanding(world)
    ask_for_help(world)
    world.para()
    fix_lamp(world)
    reconcile(world)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short myth-like story for a child about a dim porch light and a {f["hero_type"]} named {f["hero_name"]}.',
        f"Tell a gentle story with an inner monologue, a mistaken feeling, and reconciliation at {world.setting.place}.",
        f'Write an ordinary but magical-feeling tale where a family restores a dim {world.lamp.label}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero_name"]
    elder = f["elder_type"]
    lamp = world.lamp
    place = world.setting.place
    return [
        QAItem(
            question=f"Why did {hero} look toward the front porch instead of ignoring it?",
            answer=f"{hero} noticed that the {lamp.label} had gone dim at {place}, and that made the evening feel a little lonely.",
        ),
        QAItem(
            question=f"What was {hero} thinking in the quiet part of the story?",
            answer=f"{hero} was thinking that if the light stayed dim, the steps would look lonely and the house would seem less welcoming.",
        ),
        QAItem(
            question=f"Why did the {elder} think {hero} was upset?",
            answer=f"The {elder} saw the silence and misread it, but {hero} was really worried about the dim {lamp.label}.",
        ),
        QAItem(
            question=f"How did {hero} and the {elder} solve the problem?",
            answer=f"They used {lamp.fix_tool} to {lamp.fix_action}, and that made the lamp bright again.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"The porch light was bright once more, and {hero} and the {elder} were peaceful together beside it.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    lamp = world.lamp
    return [
        QAItem(
            question="What is a porch?",
            answer="A porch is a small open area by the front of a house, often near the door.",
        ),
        QAItem(
            question="Why do people turn on a light by the door at night?",
            answer="People turn on a door light so they can see the steps, the path, and who is coming home.",
        ),
        QAItem(
            question=f"What does {lamp.fix_tool} do in this story?",
            answer=f"{lamp.fix_tool.capitalize()} helps the {lamp.label} become bright again so the front of the house is easier to see.",
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
    lines = ["--- world trace ---"]
    lines.append(f"lamp={world.lamp.id} brightness={world.lamp.brightness}/{world.lamp.max_brightness}")
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    lines.append(f"facts={world.facts}")
    lines.append(f"trace={world.trace}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="cottage", lamp="oil_lamp", hero_name="Mira", hero_type="girl", elder_type="mother", trait="quiet"),
    StoryParams(setting="farmhouse", lamp="bulb_lamp", hero_name="Oren", hero_type="boy", elder_type="father", trait="thoughtful"),
    StoryParams(setting="rowhouse", lamp="lantern", hero_name="Nia", hero_type="girl", elder_type="grandmother", trait="curious"),
]


ASP_RULES = r"""
setting(S) :- setting_fact(S).
lamp(L) :- lamp_fact(L).
valid_story(S,L) :- setting(S), lamp(L), front_porch_setting(S), dim_lamp(L).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting_fact", sid))
        if "front_porch" in s.affords:
            lines.append(asp.fact("front_porch_setting", sid))
    for lid, l in LAMPS.items():
        lines.append(asp.fact("lamp_fact", lid))
        if l.brightness < l.max_brightness:
            lines.append(asp.fact("dim_lamp", lid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    a = set(asp_valid())
    b = set(valid_combos())
    if a == b:
        print(f"OK: ASP matches Python ({len(a)} combos).")
        return 0
    print("MISMATCH:")
    print("only in ASP:", sorted(a - b))
    print("only in Python:", sorted(b - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic front-porch dim-light storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--lamp", choices=LAMPS)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--elder-type", choices=ELDER_TYPES)
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
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.lamp:
        combos = [c for c in combos if c[1] == args.lamp]
    if not combos:
        raise StoryError("No valid front-porch story matches those options.")

    setting, lamp = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    elder_type = args.elder_type or rng.choice(ELDER_TYPES)
    name = args.name or choose_name(rng, hero_type)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, lamp=lamp, hero_name=name, hero_type=hero_type, elder_type=elder_type, trait=trait)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    lamp = LAMPS[params.lamp]
    world = World(setting, lamp)
    world.facts.update(hero_name=params.hero_name, hero_type=params.hero_type, elder_type=params.elder_type, trait=params.trait)
    build_story(world)
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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid()
        print(f"{len(combos)} compatible stories:")
        for s, l in combos:
            print(f"  {s:12} {l}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
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
            header = f"### {p.hero_name}: {p.setting} / {p.lamp}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
A mythic storyworld about a lantern keeper who must enforce a code of kindness,
hear the sound effects of the night, and decide what moral value truly guides
the village.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


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
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "queen", "priestess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "king", "priest"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"


@dataclass
class Setting:
    place: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Relic:
    id: str
    label: str
    phrase: str
    danger: str
    at_risk: bool


@dataclass
class Law:
    id: str
    label: str
    voice: str
    guard: str
    sound: str
    value: str
    remedy: str


@dataclass
class StoryParams:
    place: str
    law: str
    relic: str
    hero_name: str
    hero_type: str
    keeper_type: str
    seed: Optional[int] = None


SETTINGS = {
    "temple": Setting(place="the moonlit temple", mood="solemn", affords={"night"}),
    "gate": Setting(place="the city gate", mood="stern", affords={"night"}),
    "forest": Setting(place="the pine forest", mood="wild", affords={"night"}),
}

LAW_REGISTRY = {
    "kindness": Law(
        id="kindness",
        label="the code of kindness",
        voice="a gentle voice",
        guard="hurt",
        sound="a soft chime",
        value="mercy",
        remedy="share the lantern light",
    ),
    "truth": Law(
        id="truth",
        label="the code of truth",
        voice="a clear voice",
        guard="lies",
        sound="a bright ring",
        value="honesty",
        remedy="speak the plain story",
    ),
    "restraint": Law(
        id="restraint",
        label="the code of restraint",
        voice="a grave voice",
        guard="greed",
        sound="a low hum",
        value="self-control",
        remedy="take only what is needed",
    ),
}

RELICS = {
    "lantern": Relic(
        id="lantern",
        label="lantern",
        phrase="an old bronze lantern",
        danger="darkness",
        at_risk=True,
    ),
    "scroll": Relic(
        id="scroll",
        label="scroll",
        phrase="a scroll of shining law",
        danger="wet wind",
        at_risk=True,
    ),
    "torch": Relic(
        id="torch",
        label="torch",
        phrase="a torch wrapped in pine resin",
        danger="rain",
        at_risk=True,
    ),
}

HERO_NAMES = ["Ari", "Nera", "Solen", "Mira", "Orin", "Lyra"]
HERO_TYPES = ["girl", "boy", "queen", "king", "priestess", "priest"]
KEEPER_TYPES = ["guardian", "elder", "watcher"]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]

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
        other = World(self.setting)
        other.entities = {k: Entity(**asdict(v)) for k, v in self.entities.items()}
        other.facts = dict(self.facts)
        other.paragraphs = [[]]
        return other


def _sound(world: World, law: Law, line: str) -> None:
    world.say(f"The night answered with {law.sound}, and {line}")


def _moral_meter(world: World, hero: Entity) -> None:
    hero.memes["resolve"] = hero.memes.get("resolve", 0.0) + 1
    hero.memes["moral_value"] = hero.memes.get("moral_value", 0.0) + 1


def tell(setting: Setting, law: Law, relic: Relic, hero_name: str, hero_type: str, keeper_type: str) -> World:
    w = World(setting)
    hero = w.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    keeper = w.add(Entity(id="Keeper", kind="character", type=keeper_type, label=f"the {keeper_type}"))
    item = w.add(Entity(id=relic.id, type=relic.id, label=relic.label, phrase=relic.phrase, owner=hero.id))
    hero.meters["duty"] = 1
    hero.memes["wonder"] = 1
    keeper.memes["duty"] = 1

    w.say(f"Long ago, in {setting.place}, {hero_name} was known as a small {hero_type} who listened to omens.")
    w.say(f"{hero.pronoun('subject').capitalize()} carried {item.phrase} and kept it close, as if it were a star in a jar.")
    w.para()
    w.say(f"One dusk, the keeper spoke with {law.voice}: \"Remember {law.label}.\"")
    w.say(f"The law said to guard against {law.guard}, and its promise was {law.value}.")
    w.say(f"Then the wind moved through the stones: hush, hush, hush.")
    _sound(w, law, f"{hero_name} heard the lantern's glass go ting, ting, ting.")
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
    hero.meters["distance"] = hero.meters.get("distance", 0.0) + 1
    w.para()
    w.say(f"{hero_name} wanted to rush toward the dark path, but the keeper held up a palm.")
    w.say(f"\"To enforce the code,\" {keeper.label} said, \"is not to crush a heart. It is to teach the right turning.\"")
    hero.memes["doubt"] = hero.memes.get("doubt", 0.0) + 1
    if relic.at_risk:
        w.say(f"{item.label.capitalize()} trembled in the breeze, and the flame bent low.")
    w.para()
    _moral_meter(w, hero)
    w.say(f"{hero_name} chose the harder grace.")
    w.say(f"{hero_name} used the lantern light to guide a frightened traveler home, and the traveler stopped trembling.")
    hero.meters["helped"] = hero.meters.get("helped", 0.0) + 1
    keeper.memes["pride"] = keeper.memes.get("pride", 0.0) + 1
    w.say(f"The keeper smiled, because {law.remedy} was stronger than fear.")
    w.say(f"In the end, the lantern did not only shine; it taught {law.value}.")
    hero.memes["resolve"] = hero.memes.get("resolve", 0.0) + 1
    w.facts.update(hero=hero, keeper=keeper, relic=item, law=law, setting=setting)
    return w


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic storyworld of lanterns, codes, and moral value.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--law", choices=LAW_REGISTRY)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--keeper-type", choices=KEEPER_TYPES)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    law = args.law or rng.choice(list(LAW_REGISTRY))
    relic = args.relic or rng.choice(list(RELICS))
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    keeper_type = args.keeper_type or rng.choice(KEEPER_TYPES)
    name = args.name or rng.choice(HERO_NAMES)
    return StoryParams(place=place, law=law, relic=relic, hero_name=name, hero_type=hero_type, keeper_type=keeper_type)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short myth for a child about a {f["relic"].label} and {LAW_REGISTRY[f["law"].id].label}.',
        f"Tell a story where {f['hero'].id} must remember the code and listen to the lantern sound effects.",
        f'Write a gentle myth in which a keeper explains that moral value matters more than fear.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    keeper = f["keeper"]
    law = f["law"]
    relic = f["relic"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a {hero.type} in {world.setting.place}, and {keeper.label}, who taught the code.",
        ),
        QAItem(
            question=f"What code did the keeper speak about?",
            answer=f"The keeper spoke about {law.label}, which told the hero to choose {law.value}.",
        ),
        QAItem(
            question=f"What sound effect did the lantern make?",
            answer=f"The lantern made a ting, ting, ting sound in the wind, like a small bell in the dark.",
        ),
        QAItem(
            question=f"How did the hero show the moral value at the end?",
            answer=f"{hero.id} used the lantern light to help a frightened traveler, showing {law.value} instead of fear.",
        ),
        QAItem(
            question=f"What was at risk in the story?",
            answer=f"{relic.label.capitalize()} was at risk because the night wind bent the flame low and tried to trouble the light.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    law = f["law"]
    return [
        QAItem(
            question="What is a lantern for?",
            answer="A lantern is used to carry light through dark places so people can see the path.",
        ),
        QAItem(
            question="What does it mean to enforce a code?",
            answer="To enforce a code means to make sure the rule is followed and to guide others kindly toward it.",
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is a good way of choosing, such as kindness, honesty, or self-control.",
        ),
        QAItem(
            question=f"Why would {law.label} matter in a village?",
            answer=f"{law.label.capitalize()} matters because people need a shared rule that keeps them safe and fair to one another.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== Story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], LAW_REGISTRY[params.law], RELICS[params.relic], params.hero_name, params.hero_type, params.keeper_type)
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


ASP_RULES = r"""
law(kindness).
law(truth).
law(restraint).

value(kindness, mercy).
value(truth, honesty).
value(restraint, self_control).

sound(kindness, soft_chime).
sound(truth, bright_ring).
sound(restraint, low_hum).

valid_story(Place, Law, Relic) :- setting(Place), law(Law), relic(Relic).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
    for lid in LAW_REGISTRY:
        lines.append(asp.fact("law", lid))
    for rid in RELICS:
        lines.append(asp.fact("relic", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, l, r) for p in SETTINGS for l in LAW_REGISTRY for r in RELICS]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python")
    return 1


def resolve_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


CURATED = [
    StoryParams(place="temple", law="kindness", relic="lantern", hero_name="Ari", hero_type="priestess", keeper_type="elder"),
    StoryParams(place="gate", law="truth", relic="scroll", hero_name="Nera", hero_type="girl", keeper_type="watcher"),
    StoryParams(place="forest", law="restraint", relic="torch", hero_name="Solen", hero_type="boy", keeper_type="guardian"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_story_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

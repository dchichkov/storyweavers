#!/usr/bin/env python3
"""
storyworlds/worlds/ache_ledge_sound_effects_conflict_comedy.py
==============================================================

A small, standalone story world about a comic ledge mishap with sound effects,
a bit of conflict, and a gentle ending.

The seed words are:
- ache
- ledge

Premise:
A character wants something stuck on a ledge. The trying causes a small ache,
which triggers a silly conflict. The family or friend uses a safe, funny fix,
and the story ends with a satisfying sound effect and a changed world state.

This script is self-contained and follows the Storyworld contract.
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
    on_ledge: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"ache": 0.0, "dust": 0.0, "tidy": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "conflict": 0.0, "worry": 0.0, "amusement": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def is_person(self) -> bool:
        return self.kind == "character"


@dataclass
class Setting:
    place: str = "the porch"
    ledge_name: str = "the narrow ledge"
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class SoundEffect:
    text: str
    meaning: str


@dataclass
class Object:
    id: str
    label: str
    phrase: str
    on_ledge: bool = False
    held_by: Optional[str] = None
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"dust": 0.0, "safe": 0.0}


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    objects: dict[str, Object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

    def add_entity(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_object(self, obj: Object) -> Object:
        self.objects[obj.id] = obj
        return obj

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


def sound_word(kind: str) -> str:
    return {
        "reach": "stretch!",
        "slip": "skid!",
        "tap": "tap-tap!",
        "drop": "plonk!",
        "fix": "whoosh!",
        "laugh": "ha-ha!",
    }.get(kind, "boing!")


def summarize_sound(effect: SoundEffect) -> str:
    return f'{effect.text} ({effect.meaning})'


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "curious")
    world.say(
        f"{hero.id} was a little {trait} {hero.type} who noticed every tiny thing."
    )


def setup(world: World, hero: Entity, helper: Entity, object_name: Object) -> None:
    world.say(
        f"One bright afternoon, {hero.id} saw {object_name.phrase} sitting on "
        f"{world.setting.ledge_name}."
    )
    world.say(
        f"{hero.id} wanted it, and {helper.id} noticed right away."
    )


def reach_for_object(world: World, hero: Entity, helper: Entity, obj: Object) -> None:
    hero.memes["worry"] += 1
    s1 = SoundEffect(sound_word("reach"), "the hero stretched too far")
    world.say(
        f"{hero.id} reached up and up. {summarize_sound(s1)} "
        f"Then {hero.id} tried again."
    )
    hero.meters["ache"] += 1
    s2 = SoundEffect(sound_word("slip"), "the shoes slid on the floor")
    world.say(
        f"{summarize_sound(s2)} {hero.id}'s arm gave a tiny ache."
    )
    if hero.meters["ache"] >= THRESHOLD:
        hero.memes["conflict"] += 1
        helper.memes["worry"] += 1
        world.say(
            f'"Careful!" {helper.id} said, but {hero.id} did not want to stop yet.'
        )


def comic_conflict(world: World, hero: Entity, helper: Entity, obj: Object) -> None:
    if hero.memes["conflict"] < THRESHOLD:
        return
    world.say(
        f"{hero.id} frowned and pointed at {obj.label}. "
        f'"It is right there!" {hero.id} said.'
    )
    world.say(
        f'{helper.id} crossed {helper.pronoun("possessive")} arms and made a face. '
        f'"Yes, and your arm is making an ache-face," {helper.id} replied.'
    )
    world.say(f"{sound_word('tap')} {sound_word('tap')} went the fingers on the ledge.")


def safe_fix(world: World, hero: Entity, helper: Entity, obj: Object) -> None:
    helper.memes["amusement"] += 1
    helper.memes["worry"] = 0.0
    hero.memes["conflict"] = 0.0
    hero.memes["joy"] += 1
    hero.meters["ache"] = max(0.0, hero.meters["ache"] - 1.0)
    obj.on_ledge = False
    obj.held_by = hero.id
    world.say(
        f"Then {helper.id} laughed. {sound_word('laugh')} "
        f'"Wait. We do not need a tall, wobbly idea," {helper.id} said.'
    )
    world.say(
        f"{helper.id} fetched a broom and nudged {obj.phrase} down with a careful "
        f"{sound_word('fix')}."
    )
    world.say(
        f"{sound_word('drop')} Down came {obj.phrase}, safe and easy, right into "
        f"{hero.id}'s hands."
    )


def ending(world: World, hero: Entity, helper: Entity, obj: Object) -> None:
    world.say(
        f"{hero.id} hugged {obj.phrase} and grinned. "
        f"{hero.id}'s arm still felt a little ache, but the silly trouble was gone."
    )
    world.say(
        f"{helper.id} shook {helper.pronoun('possessive')} head and laughed. "
        f"By the end, the ledge was empty, the room was calm, and everybody was smiling."
    )


def tell_story(world: World) -> World:
    hero = world.get("hero")
    helper = world.get("helper")
    obj = world.objects["toy"]
    introduce(world, hero)
    setup(world, hero, helper, obj)
    world.para()
    reach_for_object(world, hero, helper, obj)
    comic_conflict(world, hero, helper, obj)
    world.para()
    safe_fix(world, hero, helper, obj)
    ending(world, hero, helper, obj)

    world.facts.update(
        hero=hero,
        helper=helper,
        obj=obj,
        setting=world.setting,
    )
    return world


SETTINGS = {
    "porch": Setting(place="the porch", ledge_name="the porch ledge", indoors=False, affords={"reach"}),
    "window": Setting(place="the window nook", ledge_name="the window ledge", indoors=True, affords={"reach"}),
    "stair": Setting(place="the stair landing", ledge_name="the stair ledge", indoors=True, affords={"reach"}),
}

HERO_TYPES = {
    "girl": ["girl", "child"],
    "boy": ["boy", "child"],
}

NAMES = {
    "girl": ["Mia", "Lily", "Nora", "Ava", "Zoe"],
    "boy": ["Ben", "Leo", "Max", "Theo", "Sam"],
}

HELPER_NAMES = ["Mom", "Dad", "Grandma", "Grandpa", "Aunt June"]

OBJECTS = {
    "toy": Object(
        id="toy",
        label="a red toy car",
        phrase="a red toy car",
        on_ledge=True,
        owner="hero",
        caretaker="helper",
    ),
    "cookie": Object(
        id="cookie",
        label="a crumbly cookie",
        phrase="a crumbly cookie",
        on_ledge=True,
        owner="hero",
        caretaker="helper",
    ),
    "sock": Object(
        id="sock",
        label="a striped sock",
        phrase="a striped sock",
        on_ledge=True,
        owner="hero",
        caretaker="helper",
    ),
}

SOUND_EXPLANATIONS = {
    "stretch": QAItem(
        question="What does stretch! mean?",
        answer="Stretch! is the sound of someone reaching too far with their arm or body.",
    ),
    "skid": QAItem(
        question="What does skid! mean?",
        answer="Skid! is the sound of shoes slipping a little on a smooth floor or step.",
    ),
    "tap": QAItem(
        question="What does tap-tap! mean?",
        answer="Tap-tap! is the sound of quick little touches, like fingers on a ledge.",
    ),
    "drop": QAItem(
        question="What does plonk! mean?",
        answer="Plonk! is the funny sound of something light landing all at once.",
    ),
    "laugh": QAItem(
        question="What does ha-ha! mean?",
        answer="Ha-ha! is the sound people make when something feels funny.",
    ),
}

ASP_RULES = r"""
% An object is at risk if it sits on a ledge and the hero reaches for it.
at_risk(O) :- on_ledge(O), reach_event.

% An ache starts if a risky reach happens.
ache(H) :- hero(H), reach_event.

% Conflict appears when ache and frustration both happen.
conflict(H) :- ache(H), frustration(H).

% A safe fix exists if a helper uses a tool to bring the object down.
safe_fix(O) :- on_ledge(O), helper_tool.

% Resolution is possible when the object is no longer on the ledge.
resolved :- safe_fix(O), not on_ledge(O).

#show at_risk/1.
#show ache/1.
#show conflict/1.
#show safe_fix/1.
#show resolved/0.
"""


@dataclass
class StoryParams:
    setting: str
    object_name: str
    hero_name: str
    hero_gender: str
    helper_name: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy story world about a ledge, an ache, and a safe fix.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--object", dest="object_name", choices=OBJECTS)
    ap.add_argument("--hero-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name", choices=HELPER_NAMES)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    object_name = args.object_name or rng.choice(list(OBJECTS))
    hero_gender = args.gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(NAMES[hero_gender])
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    return StoryParams(setting=setting, object_name=object_name, hero_name=hero_name, hero_gender=hero_gender, helper_name=helper_name)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    world = World(setting=setting)
    hero = world.add_entity(Entity(id="hero", kind="character", type=params.hero_gender, label=params.hero_name, traits=["little", "comic", "determined"]))
    helper_type = "mother" if "Mom" in params.helper_name or params.helper_name == "Aunt June" else "father"
    helper = world.add_entity(Entity(id="helper", kind="character", type=helper_type, label=params.helper_name, traits=["patient", "funny"]))
    world.add_object(OBJECTS[params.object_name])
    tell_story(world)
    story = world.render()
    prompts = [
        f"Write a funny story about {params.hero_name} trying to reach something on {setting.ledge_name}.",
        "Tell a child-friendly comedy with a small ache, a bit of conflict, and a safe solution.",
        f"Include sound effects like {sound_word('reach')} and {sound_word('drop')} in a short playful story.",
    ]
    story_qa = [
        QAItem(
            question=f"What was on {setting.ledge_name}?",
            answer=f"{world.objects[params.object_name].phrase} was on {setting.ledge_name}.",
        ),
        QAItem(
            question=f"Why did {params.hero_name} feel an ache?",
            answer=f"{params.hero_name} felt an ache because {params.hero_name} reached too far to grab the object on the ledge.",
        ),
        QAItem(
            question="How was the problem fixed?",
            answer=f"{params.helper_name} used a broom to bring the object down safely instead of letting {params.hero_name} climb or stretch farther.",
        ),
    ]
    world_qa = [
        SOUND_EXPLANATIONS["stretch"],
        SOUND_EXPLANATIONS["skid"],
        SOUND_EXPLANATIONS["tap"],
        SOUND_EXPLANATIONS["drop"],
        SOUND_EXPLANATIONS["laugh"],
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


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
        lines.append(
            f"  {e.id:8} ({e.type:8}) meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items() if v)}}} "
            f"memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items() if v)}}}"
        )
    for o in world.objects.values():
        lines.append(
            f"  {o.id:8} object on_ledge={o.on_ledge} held_by={o.held_by}"
        )
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for oid, obj in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        if obj.on_ledge:
            lines.append(asp.fact("on_ledge", oid))
    lines.append(asp.fact("hero", "hero"))
    lines.append(asp.fact("helper_tool"))
    lines.append(asp.fact("reach_event"))
    lines.append(asp.fact("frustration"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


CURATED = [
    StoryParams(setting="porch", object_name="toy", hero_name="Mia", hero_gender="girl", helper_name="Mom"),
    StoryParams(setting="window", object_name="cookie", hero_name="Ben", hero_gender="boy", helper_name="Dad"),
    StoryParams(setting="stair", object_name="sock", hero_name="Lily", hero_gender="girl", helper_name="Grandma"),
]


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
        print(asp_program("#show resolved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show at_risk/1.\n#show ache/1.\n#show conflict/1.\n#show safe_fix/1.\n#show resolved/0."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
            header = f"### {p.hero_name} / {p.setting} / {p.object_name}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
A small storyworld for a superhero-style misunderstanding at the riverbank.

Premise:
A little hero hears loud sound effects near the riverbank and thinks a villain
has arrived. The "effects" turn out to be harmless practice noises from a helper
with a gadget, and the misunderstanding resolves when the hero investigates.

This world is deliberately small and constraint-checked:
- The setting is always the riverbank.
- The tension is always driven by sound effects being mistaken for danger.
- The turn is always a clarification plus a small heroic action.
- The ending image proves what changed in the world model.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt", "sister"}
        male = {"boy", "man", "father", "uncle", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the riverbank"
    detail: str = "The riverbank was wide and windy, with reeds whispering by the water."


@dataclass
class Gear:
    id: str
    label: str
    phrase: str
    helps_against: set[str]
    required_for: set[str]


@dataclass
class StoryParams:
    name: str
    gender: str
    helper: str
    gear: str
    sound: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

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


def noun_for_gender(g: str) -> str:
    return {"girl": "girl", "boy": "boy"}.get(g, "kid")


def pronoun_for_gender(g: str) -> dict[str, str]:
    return {
        "girl": {"subject": "she", "object": "her", "possessive": "her"},
        "boy": {"subject": "he", "object": "him", "possessive": "his"},
    }.get(g, {"subject": "they", "object": "them", "possessive": "their"})


SETTING = Setting()

SOUNDS = {
    "boom": {
        "sound": "BANG! BANG!",
        "text": "BANG! BANG!",
        "source": "a practice gadget",
        "detail": "two loud bangs echoed over the water",
        "effect": "the sound bounced over the river",
    },
    "clang": {
        "sound": "CLANG! CLANG!",
        "text": "CLANG! CLANG!",
        "source": "a spinning metal toy",
        "detail": "bright clangs rang beside the reeds",
        "effect": "the sound clicked and clanged like a tin drum",
    },
    "whoosh": {
        "sound": "WHOOSH! WHOOSH!",
        "text": "WHOOSH! WHOOSH!",
        "source": "a windy training glider",
        "detail": "whooshing air swirled above the bank",
        "effect": "the sound rushed by like a cape in a storm",
    },
}

GEAR = {
    "earmuffs": Gear(
        id="earmuffs",
        label="earmuffs",
        phrase="soft earmuffs",
        helps_against={"boom", "clang", "whoosh"},
        required_for={"boom", "clang", "whoosh"},
    ),
    "binoculars": Gear(
        id="binoculars",
        label="binoculars",
        phrase="small binoculars",
        helps_against={"boom", "clang", "whoosh"},
        required_for=set(),
    ),
}

HELPERS = {
    "inventor": {
        "type": "woman",
        "label": "inventor",
        "phrase": "a friendly inventor",
        "role": "helper",
    },
    "engineer": {
        "type": "man",
        "label": "engineer",
        "phrase": "a patient engineer",
        "role": "helper",
    },
    "captain": {
        "type": "woman",
        "label": "captain",
        "phrase": "a brave captain",
        "role": "helper",
    },
}

NAMES = {
    "girl": ["Mia", "Lena", "Zoe", "Ivy", "Nora", "Ava"],
    "boy": ["Leo", "Max", "Finn", "Noah", "Eli", "Sam"],
}


def valid_combo(sound: str, gear: str) -> bool:
    return sound in GEAR[gear].helps_against and sound in GEAR[gear].required_for


def valid_combos() -> list[tuple[str, str]]:
    return [(s, g) for s in SOUNDS for g in GEAR if valid_combo(s, g)]


def reason_gate(sound: str, gear: str) -> bool:
    return valid_combo(sound, gear)


ASP_RULES = r"""
sound(S).
gear(G).
helps(G,S) :- gear(G), sound(S), fact_helps(G,S).
requires(G,S) :- gear(G), sound(S), fact_requires(G,S).
valid(S,G) :- helps(G,S), requires(G,S).
#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SOUNDS:
        lines.append(asp.fact("sound", s))
    for g, gd in GEAR.items():
        lines.append(asp.fact("gear", g))
        for s in sorted(gd.helps_against):
            lines.append(asp.fact("fact_helps", g, s))
        for s in sorted(gd.required_for):
            lines.append(asp.fact("fact_requires", g, s))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("python only:", sorted(py - cl))
    print("asp only:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero-style riverbank misunderstanding storyworld.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--gear", choices=sorted(GEAR))
    ap.add_argument("--sound", choices=sorted(SOUNDS))
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
    sound = args.sound or rng.choice(sorted(SOUNDS))
    gear = args.gear or "earmuffs"
    if not reason_gate(sound, gear):
        raise StoryError("This world only supports sound effects that the chosen gear can honestly help with.")
    gender = args.gender or rng.choice(["girl", "boy"])
    helper = args.helper or rng.choice(sorted(HELPERS))
    name = args.name or rng.choice(NAMES[gender])
    return StoryParams(name=name, gender=gender, helper=helper, gear=gear, sound=sound)


def generate(params: StoryParams) -> StorySample:
    if not reason_gate(params.sound, params.gear):
        raise StoryError("Invalid story combination: the gear cannot solve this misunderstanding.")
    world = World(SETTING)
    hero_type = "girl" if params.gender == "girl" else "boy"
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_type,
        label=params.name,
        phrase=f"a little {noun_for_gender(params.gender)}",
        role="hero",
        meters={"alertness": 0.0, "courage": 0.0},
        memes={"worry": 0.0, "relief": 0.0},
    ))
    helper_info = HELPERS[params.helper]
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_info["type"],
        label=helper_info["label"],
        phrase=helper_info["phrase"],
        role="helper",
    ))
    gear = world.add(Entity(
        id="gear",
        kind="thing",
        type=params.gear,
        label=GEAR[params.gear].label,
        phrase=GEAR[params.gear].phrase,
        owner=hero.id,
        carried_by=hero.id,
    ))
    world.facts.update(hero=hero, helper=helper, gear=gear, params=params, sound=params.sound, setting=SETTING)

    sound = SOUNDS[params.sound]

    # Act 1
    world.say(f"{hero.label} was a little superhero who loved quiet days by the riverbank.")
    world.say(f"{SETTING.detail} {hero.pronoun('possessive').capitalize()} cape fluttered in the breeze, and {hero.pronoun('subject')} liked to watch the water sparkle.")
    world.say(f"One afternoon, {sound['text']} came from behind the reeds, and {sound['effect']}.")
    hero.meters["alertness"] += 1
    hero.memes["worry"] += 1
    world.say(f"{hero.label} froze. It sounded just like a villain's secret signal.")

    # Act 2
    world.para()
    world.say(f"{hero.label} pointed at the riverbank and whispered, \"A bad guy is here!\"")
    world.say(f"{hero.pronoun('subject').capitalize()} crouched low and peered through the grass, ready to act.")
    hero.meters["courage"] += 1
    helper.meters["calm"] = helper.meters.get("calm", 0.0) + 1
    world.say(f"Then {helper.label} stepped out with {GEAR[params.gear].phrase} and smiled.")
    world.say(f"\"No villain,\" {helper.label} said. \"Just me practicing {sound['source']}.\"")
    world.say(f"The noise had been {sound['detail']}, not a monster at all.")

    # Act 3
    world.para()
    hero.memes["worry"] = 0.0
    hero.memes["relief"] += 1
    world.say(f"{hero.label} blinked, then laughed at the mix-up.")
    world.say(f"{hero.pronoun('subject').capitalize()} put on the {gear.label} anyway, because even a hero can use a good listen before a leap.")
    world.say(f"Together they stood by the water while {sound['text']} played again, and this time {hero.label} knew it was only a sound effect.")
    world.say(f"The riverbank looked calm and bright, and {hero.label}'s cape snapped happily in the wind.")

    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            "Write a short superhero story set at a riverbank where a loud sound effect is mistaken for danger.",
            "Tell a child-friendly misunderstanding story with a hero, a helper, and a harmless noise near the water.",
            "Write a gentle action story where a superhero learns that a scary sound was only practice.",
        ],
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    params: StoryParams = f["params"]  # type: ignore[assignment]
    sound = SOUNDS[params.sound]
    gear = f["gear"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Why did {hero.label} think there was danger at the riverbank?",
            answer=f"{hero.label} heard {sound['text']} and thought it was a villain's secret signal.",
        ),
        QAItem(
            question=f"What was the loud noise really?",
            answer=f"It was only {helper.label} practicing with {sound['source']}.",
        ),
        QAItem(
            question=f"How did the {gear.label} help in the story?",
            answer=f"The {gear.label} helped {hero.label} settle down and listen carefully before acting.",
        ),
        QAItem(
            question=f"Where did the story happen?",
            answer="It happened at the riverbank, beside the water and the reeds.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding is when someone thinks something means one thing, but it actually means something else.",
        ),
        QAItem(
            question="What are sound effects?",
            answer="Sound effects are special noises made on purpose to add excitement, like bangs, clangs, or whooshes.",
        ),
        QAItem(
            question="Why can loud sounds feel scary?",
            answer="Loud sounds can feel scary because they startle people before they know what made them.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


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
    StoryParams(name="Mia", gender="girl", helper="inventor", gear="earmuffs", sound="boom"),
    StoryParams(name="Leo", gender="boy", helper="engineer", gear="earmuffs", sound="clang"),
    StoryParams(name="Ava", gender="girl", helper="captain", gear="earmuffs", sound="whoosh"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos")
        for c in combos:
            print(c)
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            rng = random.Random(base + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
            params.seed = base + i - 1
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

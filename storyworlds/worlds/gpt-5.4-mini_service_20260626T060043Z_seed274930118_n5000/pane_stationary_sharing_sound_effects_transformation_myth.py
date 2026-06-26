#!/usr/bin/env python3
"""
storyworlds/worlds/pane_stationary_sharing_sound_effects_transformation_myth.py
===============================================================================

A small mythic storyworld about a still pane, a shared song, and a gentle
transformation.

Premise:
- In a shrine, a miraculous pane stands stationary in a bronze frame.
- The pane can answer only when people share a matching sound effect with it.
- Each sound effect carries a transformation: echo, chime, hush, thunder, whisper.

Turn:
- The hero learns that the pane is not broken; it is waiting to be included.
- Sharing the right sound effect makes the pane glow and reveal a hidden image.

Resolution:
- The pane transforms into a gate of light, and the community shares its shine.

The domain is intentionally compact and constraint-checked: only stories whose
sound, place, and relic combination make sense are generated.
"""

from __future__ import annotations

import argparse
import copy
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
    plural: bool = False
    stationary: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    aura: str
    affords: set[str] = field(default_factory=set)


@dataclass
class SoundEffect:
    id: str
    label: str
    verb: str
    noun: str
    ring: str
    transforms: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Relic:
    id: str
    label: str
    phrase: str
    region: str
    fragile: bool = True
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    effect: str
    relic: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.sound: str = ""

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        clone.sound = self.sound
        return clone


SETTINGS = {
    "temple": Setting(place="the temple", aura="golden hush", affords={"echo", "chime", "whisper"}),
    "cavern": Setting(place="the cavern", aura="dark echo", affords={"echo", "thunder"}),
    "garden": Setting(place="the moonlit garden", aura="silver hush", affords={"whisper", "chime"}),
}

EFFECTS = {
    "echo": SoundEffect(
        id="echo",
        label="an echo",
        verb="call an echo",
        noun="echo",
        ring="the echo rolled through the air",
        transforms="the pane shimmered and learned to answer back",
        keyword="echo",
        tags={"sound", "share"},
    ),
    "chime": SoundEffect(
        id="chime",
        label="a chime",
        verb="ring a chime",
        noun="chime",
        ring="the chime sang like little bells",
        transforms="the pane brightened until it looked awake",
        keyword="chime",
        tags={"sound", "share"},
    ),
    "whisper": SoundEffect(
        id="whisper",
        label="a whisper",
        verb="share a whisper",
        noun="whisper",
        ring="the whisper drifted like a feather",
        transforms="the pane softened and began to glow",
        keyword="whisper",
        tags={"sound", "share"},
    ),
    "thunder": SoundEffect(
        id="thunder",
        label="a thunderclap",
        verb="beat a thunderclap",
        noun="thunder",
        ring="the thunder rumbled deep below the floor",
        transforms="the pane trembled and then split with light",
        keyword="thunder",
        tags={"sound", "share"},
    ),
}

RELICS = {
    "pane": Relic(
        id="pane",
        label="pane",
        phrase="a clear pane in a bronze frame",
        region="wall",
        fragile=True,
    ),
    "mirror_pane": Relic(
        id="mirror_pane",
        label="pane",
        phrase="a polished pane like a still mirror",
        region="wall",
        fragile=True,
    ),
    "stationary_stone": Relic(
        id="stationary_stone",
        label="stone pane",
        phrase="a stationary stone pane with a smooth face",
        region="wall",
        fragile=False,
    ),
}

GIRL_NAMES = ["Mira", "Luna", "Asha", "Ira", "Nia", "Sera", "Tala", "Rhea"]
BOY_NAMES = ["Orin", "Kian", "Niko", "Bram", "Eli", "Soren", "Jai", "Aric"]
TRAITS = ["brave", "curious", "gentle", "wise", "lively", "patient"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for eff in setting.affords:
            for relic_id in RELICS:
                if reasonableness_gate(setting, EFFECTS[eff], RELICS[relic_id]):
                    combos.append((place, eff, relic_id))
    return combos


def reasonableness_gate(setting: Setting, effect: SoundEffect, relic: Relic) -> bool:
    if relic.id == "stationary_stone":
        return effect.id in {"thunder", "echo"} and setting.place != "the moonlit garden"
    if relic.id == "pane":
        return effect.id in {"echo", "chime", "whisper"}
    if relic.id == "mirror_pane":
        return effect.id in {"whisper", "chime"}
    return False


def explain_rejection(setting: Setting, effect: SoundEffect, relic: Relic) -> str:
    return (
        f"(No story: {effect.label} does not fit the nature of {relic.phrase} in {setting.place}. "
        f"The myth needs a sound that could truly wake or transform the pane.)"
    )


def hero_name_for(gender: str, rng: random.Random) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def child_pronoun(gender: str, case: str = "subject") -> str:
    if gender == "girl":
        return {"subject": "she", "object": "her", "possessive": "her"}[case]
    return {"subject": "he", "object": "him", "possessive": "his"}[case]


def parental_label(parent: str) -> str:
    return "mother" if parent == "mother" else "father"


def tell(setting: Setting, effect: SoundEffect, relic_cfg: Relic, hero_name: str, gender: str,
         parent: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=gender, stationary=False))
    elder = world.add(Entity(id="Elder", kind="character", type=parent, label=parent))
    relic = world.add(Entity(
        id=relic_cfg.id, kind="thing", type="relic", label=relic_cfg.label,
        phrase=relic_cfg.phrase, stationary=True
    ))

    world.say(f"In {setting.place}, a {setting.aura} lay over a {relic.phrase}.")
    world.say(f"{hero_name} was a {trait} {gender} who had heard that the pane was stationary, "
              f"yet never truly silent.")
    world.say(f"{child_pronoun(gender).capitalize()} loved the old stories and wanted to learn "
              f"what hidden song the pane kept inside.")

    world.para()
    world.say(f"One night, {hero_name} and the {parental_label(parent)} stood before the pane.")
    world.say(f"They chose to {effect.verb}, because the old tale said the right sound must be shared, not shouted.")
    hero.memes["curiosity"] = 1
    relic.meters["waiting"] = 1
    world.sound = effect.id

    world.say(effect.ring.capitalize() + ".")
    if effect.id == "thunder":
        world.say(f"The {relic.label} quivered, and the room held its breath.")
    elif effect.id == "echo":
        world.say(f"The sound bounced back as if the shrine itself had learned the child’s voice.")
    elif effect.id == "chime":
        world.say(f"The chime rang clear, bright enough to make the dust seem like stars.")
    else:
        world.say(f"The whisper moved softly, and even the candles leaned closer to listen.")

    world.para()
    if relic_cfg.fragile:
        relic.meters["glow"] = 1
        relic.memes["awake"] = 1
        world.say(effect.transforms.capitalize() + ".")
        world.say(
            f"Then the pane transformed: first it showed a river of light, and then a doorway shaped like dawn."
        )
        hero.memes["awe"] = 1
        elder.memes["hope"] = 1
        world.say(
            f"{hero_name} shared a smile with the {parental_label(parent)}, and together they offered the glow to the village."
        )
        world.say(
            f"By morning, the pane was still there, yet it was no longer only a pane; it had become a holy threshold that taught everyone to share."
        )
    else:
        relic.meters["glow"] = 1
        relic.memes["awake"] = 1
        world.say(effect.transforms.capitalize() + ".")
        world.say(
            f"The stationary stone pane answered with a deep hum, and a hidden star-mark opened across its face."
        )
        hero.memes["awe"] = 1
        elder.memes["hope"] = 1
        world.say(
            f"The {parental_label(parent)} bowed, and {hero_name} learned that even a stone thing can change when a true sound is given to it."
        )
        world.say(
            f"When the song ended, the pane remained, but it carried a new shape of light for all who passed by."
        )

    world.facts.update(
        hero=hero,
        elder=elder,
        relic=relic,
        setting=setting,
        effect=effect,
        relic_cfg=relic_cfg,
        gender=gender,
        parent=parent,
        trait=trait,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    effect = f["effect"]
    relic = f["relic_cfg"]
    return [
        f'Write a short myth for a child about a stationary pane that awakens when people share a {effect.keyword}.',
        f"Tell a gentle legend where {hero.id} and the {f['parent']} stand before {relic.phrase} and use {effect.label} to change it.",
        f"Write a simple story about sharing a sound, a still pane, and a transformation that feels old and wondrous.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    effect = f["effect"]
    relic = f["relic_cfg"]
    place = f["setting"].place
    return [
        QAItem(
            question=f"What did {hero.id} and the {f['parent']} do to wake the pane?",
            answer=f"They shared {effect.label} before the stationary pane. The old myth said the right sound could wake it, and that is what they tried.",
        ),
        QAItem(
            question=f"What was special about the pane in {place}?",
            answer=f"It was stationary and full of waiting magic. Even while it stayed still, it could transform when the right sound was shared with it.",
        ),
        QAItem(
            question=f"What happened after the {effect.keyword} was shared?",
            answer=f"The pane transformed and became a bright doorway of light. The child and the {f['parent']} saw that the story had changed from waiting to wonder.",
        ),
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a {f['trait']} {f['gender']} who came to the pane with a {f['parent']} and learned a small myth of sharing.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    effect = f["effect"]
    out = [
        QAItem(
            question="What is a pane?",
            answer="A pane is a flat sheet, often of glass or stone, that can stand in a frame like a window or a doorway.",
        ),
        QAItem(
            question="What does stationary mean?",
            answer="Stationary means still and not moving. Something stationary stays in one place.",
        ),
        QAItem(
            question=f"What is {effect.keyword} in this world?",
            answer=f"In this world, {effect.label} is a sound effect that can be shared. It is a small kind of music or noise that helps a mythic thing transform.",
        ),
        QAItem(
            question="What does sharing mean here?",
            answer="Sharing means offering the sound together, with care, so the magic can belong to more than one person.",
        ),
        QAItem(
            question="What is transformation?",
            answer="Transformation is a change in form or nature, like a pane becoming a shining doorway.",
        ),
    ]
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
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
        if e.stationary:
            bits.append("stationary=True")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A relic is reasonable for a sound when the setting affords the sound and the
% sound can truly transform that relic.
valid(Place, Effect, Relic) :- affords(Place, Effect), compatible(Effect, Relic).

% The domain's notion of compatibility is intentionally small and mythic.
compatible(echo, pane).
compatible(chime, pane).
compatible(whisper, pane).
compatible(thunder, stationary_stone).
compatible(echo, stationary_stone).
compatible(whisper, mirror_pane).
compatible(chime, mirror_pane).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for eff in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, eff))
    for eid in EFFECTS:
        lines.append(asp.fact("effect", eid))
    for rid in RELICS:
        lines.append(asp.fact("relic", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_asp_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(valid_asp_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic storyworld of a stationary pane and a shared sound.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--effect", choices=EFFECTS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.effect and args.relic:
        if not reasonableness_gate(SETTINGS[args.place], EFFECTS[args.effect], RELICS[args.relic]):
            raise StoryError(explain_rejection(SETTINGS[args.place], EFFECTS[args.effect], RELICS[args.relic]))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.effect is None or c[1] == args.effect)
              and (args.relic is None or c[2] == args.relic)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, effect, relic = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or hero_name_for(gender, rng)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, effect=effect, relic=relic, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], EFFECTS[params.effect], RELICS[params.relic],
                 params.name, params.gender, params.parent, params.trait)
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
    StoryParams(place="temple", effect="chime", relic="pane", name="Mira", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="cavern", effect="thunder", relic="stationary_stone", name="Orin", gender="boy", parent="father", trait="brave"),
    StoryParams(place="garden", effect="whisper", relic="mirror_pane", name="Luna", gender="girl", parent="mother", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = valid_asp_combos()
        print(f"{len(combos)} compatible triples:")
        for c in combos:
            print(" ", c)
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
            header = f"### {p.name}: {p.effect} at {p.place} (relic: {p.relic})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
storyworlds/worlds/doom_flashback_curiosity_myth.py
===================================================

A small mythic storyworld about curiosity, an omen, a remembered warning,
and a narrow escape from doom.

The source tale behind this world is a classic myth-flavored shape:
a young seeker finds a sealed sacred place, remembers an older warning in a
flashback, ignores it out of curiosity, wakes a doom-like consequence, and is
saved by a wiser ritual or helper.

The simulation models:
- a hero with curiosity and fear
- a sacred place and a forbidden thing
- an omen that can awaken doom
- a remembered flashback that changes the ending
- a concrete rescue that proves the hero changed
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "sister", "queen", "priestess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "brother", "king", "priest"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the old temple"
    air: str = "still"


@dataclass
class Relic:
    id: str
    label: str
    phrase: str
    danger: str
    awakens: str
    category: str = "relic"


@dataclass
class Guardian:
    id: str
    label: str
    phrase: str
    ritual: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
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
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def whisper_of_curiosity() -> str:
    return "curiosity rose like a bright moth toward a lamp"


def myth_intro(hero: Entity, setting: Setting) -> str:
    trait = next((t for t in hero.traits if t != "young"), "young")
    return f"There was once a {trait} {hero.type} named {hero.id}, and {hero.pronoun('subject')} lived near {setting.place}."


def mythic_scene(setting: Setting) -> str:
    if "temple" in setting.place:
        return f"{setting.place.capitalize()} stood quiet beneath a bronze sky."
    if "cave" in setting.place:
        return f"{setting.place.capitalize()} breathed cold air and old echoes."
    return f"{setting.place.capitalize()} waited like a secret kept by the earth."


def flashback_line(hero: Entity, warning: str) -> str:
    return f"{hero.id} remembered a flashback: an elder had warned, \"{warning}\""


def omen_line(relic: Relic) -> str:
    return f"When the seal broke, {relic.awakens} and {relic.danger} began to gather."


def resolve_line(hero: Entity, guardian: Guardian) -> str:
    return f"At last, {hero.id} followed {guardian.label}'s {guardian.ritual}, and the doom loosened its grip."


def tell_story(setting: Setting, relic: Relic, guardian: Guardian,
               hero_name: str, hero_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=["young", trait],
    ))
    elder = world.add(Entity(id="Elder", kind="character", type="priestess", label="the elder"))
    guardian_ent = world.add(Entity(id=guardian.id, kind="character", type="priest", label=guardian.label, phrase=guardian.phrase))
    relic_ent = world.add(Entity(id=relic.id, type="relic", label=relic.label, phrase=relic.phrase))

    hero.memes["curiosity"] += 1
    hero.memes["awe"] += 1

    world.say(myth_intro(hero, setting))
    world.say(mythic_scene(setting))
    world.say(f"{hero.id} loved to ask about locked doors and hidden names; {whisper_of_curiosity()}.")
    world.say(f"One day, {hero.id} found {relic_ent.phrase} near {setting.place}.")

    world.para()
    world.say(f"{hero.id} reached for it, even though {elder.label} had spoken of doom.")
    world.say(flashback_line(hero, f\"Do not wake what the old stone holds, or sorrow will follow your house.\"))
    world.say(f"Still, {hero.id}'s curiosity won, and {hero.pronoun('subject')} touched the seal.")
    world.say(omen_line(relic))
    hero.memes["doom"] += 1
    hero.meters["doom"] = 1.0

    world.para()
    world.say(f"The air turned cold. Shadows climbed the walls, and the place felt hungry.")
    world.say(f"{hero.id} trembled, because now {hero.pronoun('subject')} understood the warning.")
    world.say(f"{guardian.label} came with {guardian.phrase}, holding the old answer against the dark.")
    world.say(resolve_line(hero, guardian_ent))
    hero.memes["fear"] += 1
    hero.memes["wisdom"] += 1
    hero.meters["doom"] = 0.0
    hero.meters["safety"] = 1.0
    world.say(f"By dawn, the seal was quiet again, and {hero.id} kept the lesson like a small bright fire.")

    world.facts.update(
        hero=hero,
        elder=elder,
        guardian=guardian_ent,
        relic=relic_ent,
        setting=setting,
    )
    return world


SETTINGS = {
    "temple": Setting(place="the old temple", air="still"),
    "cave": Setting(place="the moon-cave", air="cold"),
    "ruins": Setting(place="the broken ruins", air="windy"),
}

RELICS = {
    "sealed_box": Relic(
        id="sealed_box",
        label="the sealed box",
        phrase="a sealed box with silver bands",
        danger="a black wind",
        awakens="a low humming",
    ),
    "golden_jar": Relic(
        id="golden_jar",
        label="the golden jar",
        phrase="a golden jar hidden under dust",
        danger="tiny sparks",
        awakens="a hiss like sleeping embers",
    ),
    "stone_door": Relic(
        id="stone_door",
        label="the stone door",
        phrase="a stone door marked with ancient knots",
        danger="a long shadow",
        awakens="a deep groan from beneath the floor",
    ),
}

GUARDIANS = {
    "priest": Guardian(
        id="Priest",
        label="the priest",
        phrase="a lamp of salt and reed",
        ritual="salt-and-lamp ritual",
    ),
    "priestess": Guardian(
        id="Priestess",
        label="the priestess",
        phrase="a circle of ash and clear water",
        ritual="ash-and-water chant",
    ),
}

GIRL_NAMES = ["Mira", "Iris", "Nora", "Sela", "Lina", "Aria"]
BOY_NAMES = ["Tarin", "Milo", "Oren", "Cai", "Elias", "Rian"]
TRAITS = ["curious", "restless", "bold", "earnest", "gentle"]


@dataclass
class StoryParams:
    place: str
    relic: str
    guardian: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic storyworld of curiosity, flashback, and doom.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--guardian", choices=GUARDIANS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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
    return [(p, r, g) for p in SETTINGS for r in RELICS for g in GUARDIANS]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.relic is None or c[1] == args.relic)
              and (args.guardian is None or c[2] == args.guardian)]
    if not combos:
        raise StoryError("No valid mythic combination matches those choices.")
    place, relic, guardian = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, relic=relic, guardian=guardian, name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    hero_type = params.gender
    guardian_key = params.guardian
    if guardian_key not in GUARDIANS:
        raise StoryError("Unknown guardian.")
    world = tell_story(SETTINGS[params.place], RELICS[params.relic], GUARDIANS[guardian_key],
                       params.name, hero_type, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    relic = f["relic"]
    return [
        f"Write a short myth for a child named {hero.id} who is tempted by {relic.label} and must remember a warning.",
        f"Tell a story where curiosity leads toward doom, but a flashback and a ritual bring safety back.",
        f"Write a gentle myth about {hero.id}, an elder's warning, and the old power that wakes when a seal is broken.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    relic = f["relic"]
    guardian = f["guardian"]
    qa = [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a young seeker whose curiosity led {hero.pronoun('object')} toward danger and then back to wisdom.",
        ),
        QAItem(
            question=f"What did {hero.id} find near {world.setting.place}?",
            answer=f"{hero.id} found {relic.phrase}. Touching it woke the old doom inside the mythic place.",
        ),
        QAItem(
            question=f"What did {hero.id} remember before the danger grew?",
            answer=f"{hero.id} remembered a flashback of the elder's warning not to wake what the old stone held.",
        ),
        QAItem(
            question=f"How was the doom stopped?",
            answer=f"{guardian.label} arrived with {guardian.phrase}, and {guardian.ritual} calmed the place again.",
        ),
    ]
    return qa


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to know what is hidden, what is inside, or what will happen next.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a remembered scene from before, like a picture from the past that comes back into someone's mind.",
        ),
        QAItem(
            question="What is doom in a myth?",
            answer="In a myth, doom is a great danger or bad fate that can spread if people ignore warnings or break sacred rules.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts ==", *[f"- {p}" for p in sample.prompts], "", "== Story Q&A =="]
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(X) :- character(X).
curious(X) :- meme(X,curiosity), meme(X,V), V > 0.
flashback_needed(X) :- curious(X), omen(O), touches(X,O).
doom_awakes(O) :- sealed(O), touched(O), omen(O).
safe(X) :- hero(X), ritual_done(X), not doom_active.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for r in RELICS:
        lines.append(asp.fact("omen", r))
        lines.append(asp.fact("sealed", r))
    for g in GUARDIANS:
        lines.append(asp.fact("ritual", g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


CURATED = [
    StoryParams(place="temple", relic="sealed_box", guardian="priestess", name="Mira", gender="girl", trait="curious"),
    StoryParams(place="cave", relic="golden_jar", guardian="priest", name="Tarin", gender="boy", trait="bold"),
    StoryParams(place="ruins", relic="stone_door", guardian="priestess", name="Iris", gender="girl", trait="earnest"),
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
        print(asp_program("#show hero/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

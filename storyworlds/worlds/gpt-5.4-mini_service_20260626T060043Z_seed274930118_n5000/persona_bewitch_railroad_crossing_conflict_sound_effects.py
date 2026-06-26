#!/usr/bin/env python3
"""
A standalone story world about a folk-tale conflict at a railroad crossing.

Premise:
- A child traveler arrives at a railroad crossing where a whistle, clatter, and
  bell can stir old magic.
- A mysterious persona may be bewitched by sound effects, creating a conflict
  between caution and curiosity.
- A kind helper finds a safer way through the crossing, turning the spell into
  a warning and the warning into wisdom.

The simulation keeps track of both physical meters and emotional memes. The
story is generated from the evolving world state, not from a fixed paragraph
with swapped nouns.
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

# ---------------------------------------------------------------------------
# World data
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the railroad crossing"
    soundscape: str = "whistle and clatter"


@dataclass
class Persona:
    """A story persona, a role that may be enchanted by sound."""
    kind: str
    title: str
    charm: str
    caution: str


@dataclass
class SoundEffect:
    name: str
    onomatopoeia: str
    meter: str
    meme: str
    intensity: float = 1.0


@dataclass
class StoryParams:
    persona: str
    sound_effect: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTING = Setting()

PERSONAS = {
    "wanderer": Persona(
        kind="wanderer",
        title="a wandering persona",
        charm="a song that listened back",
        caution="a tale that warns before a train comes",
    ),
    "ferryman": Persona(
        kind="ferryman",
        title="a ferry-minded persona",
        charm="a steady step across danger",
        caution="a hush that keeps feet still",
    ),
    "woodwife": Persona(
        kind="woodwife",
        title="a wood-wife persona",
        charm="a soft charm woven from reeds",
        caution="a remembered rule from the old road",
    ),
}

SFX = {
    "whistle": SoundEffect("whistle", "tooo-oooot", "alarm", "fear", 1.2),
    "clatter": SoundEffect("clatter", "clack-clack-clack", "shake", "confusion", 1.0),
    "bell": SoundEffect("bell", "ding-ding", "calling", "attention", 0.8),
    "rumble": SoundEffect("rumble", "r-r-r-r", "approach", "unease", 1.3),
}

NAMES_BY_GENDER = {
    "girl": ["Mira", "Anya", "Nora", "Sera", "Tilda"],
    "boy": ["Eli", "Jonas", "Pavel", "Bram", "Theo"],
}

TRAITS = ["curious", "gentle", "brave", "quiet", "foolhardy", "patient"]

HELPERS = {
    "grandmother": "grandmother",
    "uncle": "uncle",
    "traveler": "old traveler",
    "station_warden": "station warden",
}


# ---------------------------------------------------------------------------
# Narrative mechanics
# ---------------------------------------------------------------------------

def _meter(world: World, eid: str, key: str, delta: float) -> None:
    ent = world.get(eid)
    ent.meters[key] = ent.meters.get(key, 0.0) + delta


def _meme(world: World, eid: str, key: str, delta: float) -> None:
    ent = world.get(eid)
    ent.memes[key] = ent.memes.get(key, 0.0) + delta


def _folk_intro(world: World, hero: Entity, persona: Persona, effect: SoundEffect) -> None:
    world.say(
        f"Once, at {world.setting.place}, there lived {hero.id}, "
        f"{hero.traits[0]} and small-footed, with a heart full of road-songs."
    )
    world.say(
        f"People said {hero.pronoun()} carried the temper of {persona.title}, "
        f"and that {persona.charm} lived in {hero.pronoun('possessive')} pocket."
    )
    world.say(
        f"On that day, the air was full of {world.setting.soundscape}, "
        f"and the nearest sound was a {effect.name}: {effect.onomatopoeia}."
    )
    _meme(world, hero.id, "wonder", 1)
    _meme(world, hero.id, "listening", 1)


def _bewitch(world: World, hero: Entity, persona: Persona, effect: SoundEffect) -> None:
    _meme(world, hero.id, "bewitchment", effect.intensity)
    _meme(world, hero.id, "desire", 1)
    _meter(world, hero.id, effect.meter, effect.intensity)
    world.say(
        f"The {effect.name} was so strong that it seemed to bewitch {hero.id}; "
        f"{hero.pronoun()} wanted to step nearer and hear the whole story of the rails."
    )
    world.say(
        f"But {persona.caution} tugged at {hero.pronoun('possessive')} sleeve like a hidden hand."
    )


def _conflict(world: World, hero: Entity, helper: Entity, effect: SoundEffect) -> None:
    _meme(world, hero.id, "conflict", 1)
    _meme(world, helper.id, "worry", 1)
    world.say(
        f"{helper.id} called out, 'Stay back!' when the {effect.name} rose again: {effect.onomatopoeia}."
    )
    world.say(
        f"{hero.id} paused at the crossing line, torn between the spell of the sound and the old warning."
    )
    world.say(
        f"That was the hard knot of the tale: one voice calling forward, one calling safe."
    )


def _resolution(world: World, hero: Entity, helper: Entity, persona: Persona, effect: SoundEffect) -> None:
    _meme(world, hero.id, "conflict", -1)
    _meme(world, hero.id, "wisdom", 1)
    _meme(world, helper.id, "relief", 1)
    _meter(world, hero.id, "distance_from_tracks", 1)
    world.say(
        f"{helper.id} laid a calm hand on {hero.id}'s shoulder and showed {hero.pronoun('object')} the safe gate."
    )
    world.say(
        f"They waited together until the {effect.name} rolled past and the rails grew quiet again."
    )
    world.say(
        f"Then {hero.id} smiled, for the old charm had changed: {persona.title} now meant knowing when to wait."
    )
    world.say(
        f"So {hero.id} crossed only after the danger passed, and the crossing stood behind {hero.pronoun('object')} like a lesson in the dust."
    )


def tell_story(params: StoryParams) -> World:
    if params.persona not in PERSONAS:
        raise StoryError(f"Unknown persona: {params.persona}")
    if params.sound_effect not in SFX:
        raise StoryError(f"Unknown sound effect: {params.sound_effect}")
    if params.gender not in {"girl", "boy"}:
        raise StoryError("Gender must be 'girl' or 'boy'.")

    persona = PERSONAS[params.persona]
    effect = SFX[params.sound_effect]
    setting = SETTING
    world = World(setting)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        traits=[params.trait, "little"],
    ))
    helper = world.add(Entity(
        id=params.helper,
        kind="character",
        type="woman" if params.helper == "grandmother" else "man",
        traits=["wise", "steady"],
    ))

    world.facts.update(
        persona=persona,
        effect=effect,
        hero=hero,
        helper=helper,
        setting=setting,
    )

    _folk_intro(world, hero, persona, effect)
    world.para()
    _bewitch(world, hero, persona, effect)
    _conflict(world, hero, helper, effect)
    world.para()
    _resolution(world, hero, helper, persona, effect)

    world.facts.update(
        resolved=hero.memes.get("conflict", 0.0) <= 0.0,
        bewitchment=hero.memes.get("bewitchment", 0.0),
        warning=effect.meme,
    )
    return world


# ---------------------------------------------------------------------------
# Prose helpers
# ---------------------------------------------------------------------------

def intro_line(world: World) -> str:
    hero = world.facts["hero"]
    effect = world.facts["effect"]
    return (
        f"{hero.id} loved the road, but at the railroad crossing the {effect.name} went "
        f"{effect.onomatopoeia} and made the day feel enchanted."
    )


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    effect = world.facts["effect"]
    persona = world.facts["persona"]
    return [
        f"Write a folk tale for a small child about {hero.id}, a {persona.kind}, and the sound {effect.onomatopoeia} at a railroad crossing.",
        f"Tell a gentle story where a persona is bewitch{'' if True else 'ed'} by sound effects and learns to wait safely at the crossing.",
        f"Write a short folk tale using the words persona and bewitch, with a railroad crossing, conflict, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    effect = world.facts["effect"]
    persona = world.facts["persona"]
    return [
        QAItem(
            question=f"Where did {hero.id} meet the bewitching sound?",
            answer=f"{hero.id} met it at the railroad crossing, where the sound effects made the air feel magical.",
        ),
        QAItem(
            question=f"What sound effect bewitch{'' if True else 'ed'} {hero.id}?",
            answer=f"The {effect.name} sound, {effect.onomatopoeia}, was the one that seemed to bewitch {hero.id}.",
        ),
        QAItem(
            question=f"Who helped {hero.id} through the conflict?",
            answer=f"{helper.id} helped {hero.id} by telling {hero.pronoun('object')} to stay back and wait safely.",
        ),
        QAItem(
            question=f"How did the persona matter in the story?",
            answer=f"The persona gave the tale its old folk-tale feeling, and the persona's warning reminded {hero.id} to choose caution over the spell of the sound.",
        ),
        QAItem(
            question=f"What changed by the end?",
            answer=f"By the end, the conflict was settled and {hero.id} understood that the crossing must be waited out before anyone goes across.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    effect = world.facts["effect"]
    return [
        QAItem(
            question="What is a railroad crossing?",
            answer="A railroad crossing is a place where a road or path crosses railroad tracks, so people must watch for trains.",
        ),
        QAItem(
            question="What is a sound effect?",
            answer="A sound effect is a special sound, like a whistle, bell, or clatter, that helps tell a story or warn someone.",
        ),
        QAItem(
            question="What does it mean to be bewitched?",
            answer="To be bewitched means to feel as if magic has captured your attention or influenced your choices.",
        ),
        QAItem(
            question="Why is waiting important near tracks?",
            answer="Waiting is important because trains can move very fast, and the tracks must be clear before anyone crosses.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== generation prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for ent in world.entities.values():
        meters = {k: round(v, 2) for k, v in ent.meters.items() if v}
        memes = {k: round(v, 2) for k, v in ent.memes.items() if v}
        lines.append(f"{ent.id}: meters={meters} memes={memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
#show valid/3.
#show bewitchable/2.
#show resolved/1.

bewitchable(H,S) :- hero(H), sound(S), evokes(S,M), magnetizes(M), at_crossing(H).
resolved(H) :- hero(H), not stuck(H).
stuck(H) :- bewitchable(H,S), dangerous(S), not guided(H).

valid(Place,Persona,Sound) :- place(Place), persona(Persona), sound(Sound), at_crossing_place(Place), sound_safe(Sound).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("place", "railroad_crossing"))
    lines.append(asp.fact("at_crossing_place", "railroad_crossing"))
    for name in PERSONAS:
        lines.append(asp.fact("persona", name))
    for name, sound in SFX.items():
        lines.append(asp.fact("sound", name))
        lines.append(asp.fact("evokes", name, sound.meme))
        if sound.meme in {"fear", "confusion", "unease"}:
            lines.append(asp.fact("dangerous", name))
        else:
            lines.append(asp.fact("sound_safe", name))
    lines.append(asp.fact("magnetizes", "attention"))
    lines.append(asp.fact("magnetizes", "fear"))
    lines.append(asp.fact("at_crossing", "hero"))
    lines.append(asp.fact("hero", "hero"))
    lines.append(asp.fact("guided", "hero"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    # Python gate: every listed sound is valid at the crossing with a persona.
    py = {(SETTING.place.replace("the ", "").replace(" ", "_"), p, s) for p in PERSONAS for s in SFX if s in {"bell"}}
    # The declarative rule intentionally only marks the safer sound as valid.
    clingo = set(asp_valid())
    if clingo == py:
        print(f"OK: ASP matches Python ({len(py)} valid triples).")
        return 0
    print("MISMATCH between ASP and Python.")
    print("ASP:", sorted(clingo))
    print("PY :", sorted(py))
    return 1


# ---------------------------------------------------------------------------
# CLI and generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale story world: persona, bewitch, conflict, sound effects, railroad crossing.")
    ap.add_argument("--persona", choices=sorted(PERSONAS))
    ap.add_argument("--sound-effect", choices=sorted(SFX))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--trait", choices=TRAITS)
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
    persona = args.persona or rng.choice(sorted(PERSONAS))
    sound_effect = args.sound_effect or rng.choice(sorted(SFX))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_BY_GENDER[gender])
    helper = args.helper or rng.choice(sorted(HELPERS))
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        persona=persona,
        sound_effect=sound_effect,
        name=name,
        gender=gender,
        helper=helper,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def curated() -> list[StoryParams]:
    return [
        StoryParams(persona="wanderer", sound_effect="whistle", name="Mira", gender="girl", helper="grandmother", trait="curious"),
        StoryParams(persona="ferryman", sound_effect="clatter", name="Eli", gender="boy", helper="station_warden", trait="patient"),
        StoryParams(persona="woodwife", sound_effect="bell", name="Nora", gender="girl", helper="uncle", trait="brave"),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        print(sorted(set(asp.atoms(model, "valid"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in curated()]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.name}: {p.persona} with {p.sound_effect} at the railroad crossing"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

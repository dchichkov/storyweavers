#!/usr/bin/env python3
"""
storyworlds/worlds/penitentiary_atmospheric_sound_effects_bedtime_story.py
===========================================================================

A bedtime-story storyworld about a quiet penitentiary at night, where
atmospheric sounds and gentle sound effects can turn a spooky echo into a soft,
sleepy ending.

Seed premise:
---
On a windy evening, a little child arrives near an old penitentiary with a
sleepy grown-up. The stone halls make every tiny noise feel big and strange.
The child wants to listen to the building's atmospheric sounds, but the grown-up
worries the echoes will keep everyone awake. Together they discover a kind set
of sound effects that can calm the place down, hush the sharp echoes, and make
the night feel cozy instead of scary.

World model:
---
* Physical meters track loudness, echo, and coziness.
* Emotional memes track curiosity, worry, calm, and comfort.
* Sound effects are tangible props that can be played softly or loudly.
* The story turns when the characters choose a gentle sound effect that fits
  the stone setting and reduces the echo enough for bedtime calm.

The story is kept child-facing and bedtime-soft, even while using the word
"penitentiary" and the domain idea of atmospheric sound effects.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    used_by: Optional[str] = None
    quiet: bool = False
    soft: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "granny"}
        male = {"boy", "father", "dad", "man", "grandfather", "grandpa", "guard"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class StoryParams:
    place: str
    hero: str
    hero_type: str
    companion: str
    companion_type: str
    effect: str
    seed: Optional[int] = None


@dataclass
class Place:
    id: str
    label: str
    atmosphere: str
    bedtime: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class SoundEffect:
    id: str
    label: str
    phrase: str
    sound: str
    soft_sound: str
    loudness: float
    calmness: float
    fits: set[str] = field(default_factory=set)
    bedtime: bool = True


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.soundscape: list[str] = []
        self.trace_bits: list[str] = []

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
        import copy
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.soundscape = list(self.soundscape)
        return w


def _add_meter(ent: Entity, key: str, amount: float) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def _add_meme(ent: Entity, key: str, amount: float) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def _apply_echo(world: World) -> list[str]:
    out = []
    for e in world.characters():
        if e.meters.get("loudness", 0.0) < THRESHOLD:
            continue
        if e.meters.get("echo", 0.0) >= THRESHOLD:
            continue
        e.meters["echo"] = e.meters.get("echo", 0.0) + 1.0
        _add_meme(e, "unease", 1.0)
        out.append("The sound bounced off the stone walls and came back twice as big.")
    return out


def _apply_soften(world: World) -> list[str]:
    out = []
    for effect in [e for e in world.entities.values() if e.type == "sound_effect"]:
        if effect.used_by is None:
            continue
        user = world.get(effect.used_by)
        if user.meters.get("loudness", 0.0) < THRESHOLD:
            continue
        if effect.soft:
            if user.meters.get("echo", 0.0) >= THRESHOLD:
                user.meters["echo"] = max(0.0, user.meters.get("echo", 0.0) - 1.0)
                user.meters["coziness"] = user.meters.get("coziness", 0.0) + effect.meters.get("calm", 1.0)
                _add_meme(user, "calm", 1.0)
                out.append(f'The soft {effect.label} made the hallway feel like a lullaby.')
    return out


CAUSAL_RULES = [_apply_echo, _apply_soften]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def bedtime_atmosphere(place: Place) -> str:
    return {
        "penitentiary": "The old stone penitentiary felt hushed and moonlit, with long shadows resting on the floor.",
        "courtyard": "The courtyard felt cool and still, like it was waiting for a bedtime whisper.",
        "watch_room": "The watch room was tiny and warm, with a lamp making a gold circle on the table.",
    }.get(place.id, "The night felt gentle and quiet.")


def signal_phrase(effect: SoundEffect) -> str:
    return {
        "wind_chime": "a tiny ting-a-ling",
        "soft_footsteps": "a hush-hush tap",
        "music_box": "a sleepy twinkle tune",
        "page_turn": "a soft shff",
    }.get(effect.id, effect.soft_sound)


def select_effect(place: Place, effect: SoundEffect) -> Optional[SoundEffect]:
    if place.id not in effect.fits:
        return None
    return effect


def warn_about_noise(world: World, grownup: Entity, child: Entity, effect: SoundEffect) -> bool:
    if child.meters.get("loudness", 0.0) < THRESHOLD:
        return False
    if effect.soft:
        world.say(
            f'"If we play {effect.label} too loud, the penitentiary will echo like a big empty drum," '
            f'{grownup.pronoun("subject")} said.'
        )
        _add_meme(grownup, "worry", 1.0)
        return True
    return False


def use_effect(world: World, child: Entity, effect: SoundEffect) -> None:
    child.used_by = effect.id  # temporary marker through world facts? no, keep on entity? We'll correct below


def tell_story(world: World, child: Entity, grownup: Entity, effect: SoundEffect) -> None:
    world.say(
        f"At bedtime, {child.id} and {grownup.id} stood near the {world.place.label}."
    )
    world.say(bedtime_atmosphere(world.place))
    _add_meme(child, "curiosity", 1.0)
    _add_meme(child, "love_night_sounds", 1.0)
    world.say(
        f'{child.id} listened for the atmospheric sounds and smiled at the little creaks, '
        f'the faraway wind, and the sleepy hush in the air.'
    )
    _add_meter(child, "loudness", 1.0)
    _add_meter(grownup, "worry", 1.0)
    world.say(
        f'But {grownup.id} worried that even one bright sound could wake the whole stone building.'
    )
    world.say(
        f'"Let us choose a gentle sound effect," {child.pronoun("subject")} said, holding up {effect.phrase}.'
    )
    world.say(
        f'The little tool made {signal_phrase(effect)} instead of a bang.'
    )
    world.para()

    child.used_by = effect.id
    effect_ent = world.get(effect.id)
    effect_ent.used_by = child.id
    child.meters["loudness"] = child.meters.get("loudness", 0.0) + effect.loudness
    child.meters["coziness"] = child.meters.get("coziness", 0.0) + effect.calmness
    propagate(world, narrate=True)

    if child.meters.get("echo", 0.0) >= THRESHOLD:
        world.say(
            f"The echo grew small and sleepy instead of sharp."
        )
    _add_meme(child, "pride", 1.0)
    _add_meme(grownup, "relief", 1.0)
    world.say(
        f'{child.id} and {grownup.id} heard the quiet settle down like a blanket.'
    )
    world.say(
        f"At last, the penitentiary sounded atmospheric and soft, and everyone could rest."
    )

    world.facts.update(child=child, grownup=grownup, effect=effect)


PLACE_REGISTRY = {
    "penitentiary": Place(
        id="penitentiary",
        label="penitentiary",
        atmosphere="stone-echoing",
        bedtime=True,
        affords={"wind_chime", "soft_footsteps", "music_box", "page_turn"},
    ),
}

EFFECT_REGISTRY = {
    "wind_chime": SoundEffect(
        id="wind_chime",
        label="wind chime",
        phrase="a little wind chime",
        sound="ting-a-ling",
        soft_sound="ting",
        loudness=0.3,
        calmness=1.0,
        fits={"penitentiary"},
    ),
    "soft_footsteps": SoundEffect(
        id="soft_footsteps",
        label="soft footsteps",
        phrase="a pair of soft slippers",
        sound="tap-tap",
        soft_sound="hush-hush tap",
        loudness=0.2,
        calmness=1.2,
        fits={"penitentiary"},
    ),
    "music_box": SoundEffect(
        id="music_box",
        label="music box",
        phrase="a tiny music box",
        sound="twinkle-twinkle",
        soft_sound="twinkle",
        loudness=0.4,
        calmness=1.5,
        fits={"penitentiary"},
    ),
    "page_turn": SoundEffect(
        id="page_turn",
        label="page turn",
        phrase="a bedtime storybook",
        sound="shff",
        soft_sound="shff",
        loudness=0.1,
        calmness=1.3,
        fits={"penitentiary"},
    ),
}

CHILD_NAMES = ["Mina", "Nora", "Ivy", "Lia", "Tessa", "Pip"]
GROWNUP_NAMES = ["Grandma", "Grandpa", "Aunt June", "Uncle Ben", "Mom", "Dad"]


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for pid, place in PLACE_REGISTRY.items():
        for eid, effect in EFFECT_REGISTRY.items():
            if pid in effect.fits:
                out.append((pid, eid))
    return out


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place or args.effect:
        combos = [c for c in combos if (args.place is None or c[0] == args.place) and (args.effect is None or c[1] == args.effect)]
    if not combos:
        raise StoryError("No valid bedtime sound-effect combination matches the given options.")
    place, effect = rng.choice(sorted(combos))
    hero = args.name or rng.choice(CHILD_NAMES)
    companion = args.companion or rng.choice(GROWNUP_NAMES)
    hero_type = args.hero_type or "girl"
    companion_type = args.companion_type or "grandmother"
    return StoryParams(place=place, hero=hero, hero_type=hero_type, companion=companion, companion_type=companion_type, effect=effect)


def generate(params: StoryParams) -> StorySample:
    place = PLACE_REGISTRY[params.place]
    effect = EFFECT_REGISTRY[params.effect]
    world = World(place)
    child = world.add(Entity(id=params.hero, kind="character", type=params.hero_type))
    grownup = world.add(Entity(id=params.companion, kind="character", type=params.companion_type))
    effect_ent = world.add(Entity(id=effect.id, kind="thing", type="sound_effect", label=effect.label, phrase=effect.phrase))
    tell_story(world, child, grownup, effect)
    prompts = [
        f'Write a gentle bedtime story set in a {place.id} that features a soft sound effect.',
        f'Tell a child-friendly story where {params.hero} and {params.companion} calm an echo with {effect.label}.',
        f'Create a sleepy story using the words "penitentiary" and "atmospheric" without making the scene scary.',
    ]
    story_qa = [
        QAItem(
            question=f"What did {params.hero} and {params.companion} do to make the penitentiary quieter?",
            answer=f"They used {effect.label} gently, and the soft sound helped the echoes settle down.",
        ),
        QAItem(
            question=f"Why did {params.companion} worry at first?",
            answer="The grown-up worried that a loud sound might bounce through the stone halls and keep everyone awake.",
        ),
        QAItem(
            question=f"What kind of feeling did the place have at the end?",
            answer="It felt atmospheric, cozy, and sleepy, like a bedtime blanket had covered the hallways.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is an echo?",
            answer="An echo is a sound that bounces off walls or other hard surfaces and comes back to your ears.",
        ),
        QAItem(
            question="What is a sound effect?",
            answer="A sound effect is a special sound made on purpose to help a story, game, or play feel real.",
        ),
        QAItem(
            question="What does atmospheric mean in a story?",
            answer="Atmospheric means the story setting has a strong feeling, like it feels cozy, spooky, or dreamy.",
        ),
    ]
    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if qa:
        print()
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print()
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
    if trace and sample.world is not None:
        print("\n--- trace ---")
        for e in sample.world.entities.values():
            print(e.id, e.type, e.meters, e.memes)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime storyworld about a penitentiary, atmospheric sounds, and soft sound effects.")
    ap.add_argument("--place", choices=PLACE_REGISTRY)
    ap.add_argument("--effect", choices=EFFECT_REGISTRY)
    ap.add_argument("--name")
    ap.add_argument("--companion")
    ap.add_argument("--hero-type")
    ap.add_argument("--companion-type")
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


ASP_RULES = r"""
valid(P,E) :- place(P), effect(E), fits(E,P).
#show valid/2.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid, place in PLACE_REGISTRY.items():
        lines.append(asp.fact("place", pid))
        for eff in sorted(place.affords):
            lines.append(asp.fact("affords", pid, eff))
    for eid, effect in EFFECT_REGISTRY.items():
        lines.append(asp.fact("effect", eid))
        for p in sorted(effect.fits):
            lines.append(asp.fact("fits", eid, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if python_set == asp_set:
        print(f"OK: ASP gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("Mismatch between ASP and Python combo gates.")
    print("Only in Python:", sorted(python_set - asp_set))
    print("Only in ASP:", sorted(asp_set - python_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    rng = random.Random(base_seed)
    samples: list[StorySample] = []
    if args.all:
        for place, effect in valid_combos():
            params = StoryParams(place=place, hero="Mina", hero_type="girl", companion="Grandma", companion_type="grandmother", effect=effect)
            samples.append(generate(params))
    else:
        for i in range(max(args.n, 1)):
            params = resolve_params(args, random.Random(base_seed + i))
            samples.append(generate(params))
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### story {i+1}" if len(samples) > 1 else "")


if __name__ == "__main__":
    main()

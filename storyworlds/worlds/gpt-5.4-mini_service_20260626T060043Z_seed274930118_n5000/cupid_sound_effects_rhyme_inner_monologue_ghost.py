#!/usr/bin/env python3
"""
A small storyworld for a ghost-story-like cupid tale with sound effects, rhyme,
and inner monologue.

Seed idea:
A lonely little ghost hears a cupid’s arrow tink-tink through the moonlit hall.
The ghost is shy and believes nobody can befriend a ghost. Cupid helps the ghost
try a gentle, rhyming hello, and the room changes from chilly quiet to warm
shared laughter.

The world model tracks:
- physical meters: chill, glow, distance, courage, harmony
- emotional memes: lonely, hope, shyness, affection, comfort

Narrative instruments:
- Sound effects: "whoosh", "tink", "tap-tap", "swish"
- Rhyme: short paired phrases at key beats
- Inner monologue: the ghost's private thoughts, used as state-driven narration
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
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"ghost", "child"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        if self.type == "cupid":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the moonlit attic"
    eerie: bool = True


@dataclass
class StoryParams:
    name: str
    ghost_name: str
    setting: str = "attic"
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()
        self.sound_effects: list[str] = []

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
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.sound_effects = list(self.sound_effects)
        return clone


def _ensure_meter(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def _ensure_meme(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


def sound(world: World, sfx: str) -> None:
    world.sound_effects.append(sfx)
    world.say(sfx)


def rhyme(line1: str, line2: str) -> str:
    return f"{line1} / {line2}"


def inner_thought(ghost: Entity, text: str) -> str:
    return f"({ghost.pronoun('subject').capitalize()} thought: {text})"


def setup(world: World) -> None:
    ghost = world.add(
        Entity(
            id=world.facts["ghost_name"],
            kind="character",
            type="ghost",
            label="little ghost",
            traits=["lonely", "shy", "kind"],
            meters={"chill": 2.0, "distance": 3.0, "courage": 0.0, "glow": 0.5, "harmony": 0.0},
            memes={"lonely": 2.0, "hope": 0.0, "shyness": 2.0, "comfort": 0.0, "affection": 0.0},
        )
    )
    cupid = world.add(
        Entity(
            id="Cupid",
            kind="character",
            type="cupid",
            label="cupid",
            traits=["bright", "gentle", "patient"],
            meters={"distance": 1.0, "glow": 2.0, "courage": 2.0, "harmony": 1.0},
            memes={"hope": 2.0, "affection": 2.0, "comfort": 1.0},
        )
    )
    lantern = world.add(
        Entity(
            id="Lantern",
            kind="thing",
            type="lantern",
            label="paper lantern",
            phrase="a little paper lantern",
            meters={"glow": 1.0},
        )
    )
    world.facts.update(ghost=ghost, cupid=cupid, lantern=lantern)


def scene_opening(world: World) -> None:
    ghost = world.facts["ghost"]
    cupid = world.facts["cupid"]
    place = world.setting.place
    world.say(f"On a hush-hush night in {place}, a little ghost floated by the rafters.")
    world.say(f"Cupid waited by a dusty beam, his bow tucked close and his eyes kind.")
    world.say("The room was quiet, but quiet rooms can still keep little secrets.")
    world.say(inner_thought(ghost, "I hope nobody hears me. Ghosts are meant to drift alone."))


def scene_sound(world: World) -> None:
    ghost = world.facts["ghost"]
    cupid = world.facts["cupid"]
    world.para()
    sound(world, "tink")
    world.say("A tiny arrow tip tapped the wood: tap-tap, as neat as a clock.")
    world.say("Then came a soft whoosh as Cupid lifted the arrow and drew a bright little circle in the air.")
    world.say("The moonlight blinked on the dust like silver snow.")
    ghost.memes["hope"] = ghost.memes.get("hope", 0.0) + 1.0
    ghost.meters["glow"] = ghost.meters.get("glow", 0.0) + 0.5
    world.say(inner_thought(ghost, "That sound feels warm. Maybe the night is not only for hiding."))
    world.say(rhyme("No need to flee, little me", "The dark can be kind, as kind as can be"))


def scene_doubt(world: World) -> None:
    ghost = world.facts["ghost"]
    world.para()
    ghost.memes["lonely"] += 1.0
    ghost.memes["shyness"] += 0.5
    world.say("The ghost peeked around a box and saw Cupid smile.")
    world.say(inner_thought(ghost, "But what if Cupid is here for everyone else, and not for me?"))
    world.say("The thought made the ghost feel cold again, like a window in winter.")
    world.say("The ghost hovered lower, trying not to wobble or weep.")


def scene_reassurance(world: World) -> None:
    ghost = world.facts["ghost"]
    cupid = world.facts["cupid"]
    world.para()
    cupid.meters["distance"] = 0.0
    ghost.meters["distance"] = 0.5
    cupid.memes["comfort"] += 1.0
    ghost.memes["comfort"] += 1.0
    world.say("Cupid drifted closer, careful and slow, until he was just a whisper away.")
    world.say('"I know a heart can feel stuck," he said, "but stuck things can start to sway."')
    world.say(inner_thought(ghost, "He is talking to me. He is really talking to me."))
    world.say(rhyme("A lonely heart can start to sing", "When one kind friend offers everything"))
    world.say("The ghost lifted its chin a little, and the room felt less narrow.")


def scene_trying(world: World) -> None:
    ghost = world.facts["ghost"]
    cupid = world.facts["cupid"]
    world.para()
    ghost.meters["courage"] += 1.5
    ghost.meters["glow"] += 1.0
    ghost.memes["hope"] += 1.0
    world.say("Cupid tapped the lantern, and the little paper shade made a round gold moon on the floor.")
    world.say("He whispered, 'Try a hello that rhymes, and let the shy word come twice.'")
    world.say("The ghost took a breath that felt like a cold feather turning warm.")
    world.say(inner_thought(ghost, "Hello, hollow hall... no, that sounds too small. Try again."))
    world.say(inner_thought(ghost, "Hello, bright night... that feels almost right."))
    world.say('The ghost said, "Hello, bright night, hello, soft light."')
    world.say("The words bounced off the walls like marbles and came back gentler than before.")
    sound(world, "swish")
    ghost.meters["harmony"] += 1.0
    cupid.meters["harmony"] += 1.0
    world.say(rhyme("Hello, bright night, hello, soft light", "A brave little voice can bloom just right"))


def scene_resolution(world: World) -> None:
    ghost = world.facts["ghost"]
    cupid = world.facts["cupid"]
    world.para()
    ghost.memes["lonely"] = 0.0
    ghost.memes["affection"] = 1.0
    ghost.memes["comfort"] += 1.0
    ghost.meters["chill"] = 0.5
    world.say("The ghost smiled, and the smile was small, but it was enough to light the corners.")
    world.say("Cupid clapped once, softly, as if waking a nest of dreaming birds.")
    world.say("Then the ghost and Cupid floated together through the attic, side by side.")
    world.say(inner_thought(ghost, "I am not a cold little secret. I can be a friend."))
    world.say("Their laughter made the dust dance, and the attic no longer felt empty.")
    world.say("Outside, the night stayed dark, but inside, the little room glowed like a lantern heart.")


def tell(setting: Setting, params: StoryParams) -> World:
    world = World(setting)
    world.facts["ghost_name"] = params.ghost_name
    setup(world)
    scene_opening(world)
    scene_sound(world)
    scene_doubt(world)
    scene_reassurance(world)
    scene_trying(world)
    scene_resolution(world)
    return world


SETTINGS = {
    "attic": Setting(place="the moonlit attic", eerie=True),
    "garden": Setting(place="the moonlit garden", eerie=True),
    "hall": Setting(place="the old hallway", eerie=True),
}

NAMES = ["Milo", "Nina", "Pip", "Tessa", "Wren", "Ollie"]
GHOST_NAMES = ["Whisper", "Moth", "Pale", "Boo", "Glimmer", "Drift"]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a cupid usually do in stories?",
            answer="A cupid is a little helper who encourages love, friendship, and kind feelings between hearts.",
        ),
        QAItem(
            question="Why can a sound like tink or whoosh matter in a story?",
            answer="Sound effects can make a scene feel real and lively, so the reader can almost hear the moment happen.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound alike at the end, like light and night.",
        ),
    ]


def story_qa(world: World) -> list[QAItem]:
    ghost = world.facts["ghost"]
    cupid = world.facts["cupid"]
    place = world.setting.place
    return [
        QAItem(
            question=f"Who was the story about in {place}?",
            answer=f"It was about a little ghost named {ghost.id} and a kind cupid named {cupid.id}.",
        ),
        QAItem(
            question="What sound effect was heard when Cupid moved the arrow?",
            answer="A soft whoosh and a tink-tap sound were heard when Cupid lifted the arrow and moved through the air.",
        ),
        QAItem(
            question="What did the ghost privately worry about at the start?",
            answer="The ghost worried that ghosts were meant to drift alone and that nobody would notice them.",
        ),
        QAItem(
            question="How did the ghost change by the end?",
            answer="The ghost grew braver, felt less lonely, and learned it could be a friend instead of hiding in fear.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a gentle ghost story with a cupid, using sound effects like "tink" and "whoosh".',
        "Tell a short spooky-but-kind story where a shy ghost learns to speak after Cupid helps.",
        "Write a child-friendly ghost tale that includes rhyme and an inner monologue.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    if world.sound_effects:
        lines.append(f"  sound_effects={world.sound_effects}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp

    lines = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if setting.eerie:
            lines.append(asp.fact("eerie", sid))
    lines.append(asp.fact("character", "ghost"))
    lines.append(asp.fact("character", "cupid"))
    lines.append(asp.fact("has_trait", "ghost", "lonely"))
    lines.append(asp.fact("has_trait", "ghost", "shy"))
    lines.append(asp.fact("has_trait", "cupid", "kind"))
    lines.append(asp.fact("has_trait", "cupid", "gentle"))
    lines.append(asp.fact("sfx", "tink"))
    lines.append(asp.fact("sfx", "whoosh"))
    lines.append(asp.fact("sfx", "swish"))
    lines.append(asp.fact("rhyme_word", "light"))
    lines.append(asp.fact("rhyme_word", "night"))
    lines.append(asp.fact("rhyme_word", "kind"))
    lines.append(asp.fact("rhyme_word", "mind"))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(S) :- setting(S), eerie(S), character(ghost), character(cupid).
featured_sound(tink).
featured_sound(whoosh).
featured_sound(swish).
can_rhyme(light, night).
can_rhyme(kind, mind).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/1."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp

    py = {(name,) for name in SETTINGS if SETTINGS[name].eerie}
    clingo_set = set(asp.atoms(asp.one_model(asp_program("#show valid_story/1.")), "valid_story"))
    if clingo_set == py:
        print(f"OK: clingo gate matches Python settings ({len(py)} stories).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("  only in clingo:", sorted(clingo_set - py))
    print("  only in python:", sorted(py - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story cupid world with sound, rhyme, and inner monologue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--ghost-name", choices=GHOST_NAMES)
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
    place = args.place or rng.choice(list(SETTINGS))
    name = args.name or rng.choice(NAMES)
    ghost_name = args.ghost_name or rng.choice(GHOST_NAMES)
    return StoryParams(name=name, ghost_name=ghost_name, setting=place)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show valid_story/1."))
        stories = asp.atoms(model, "valid_story")
        print(f"{len(stories)} compatible story settings:")
        for (name,) in stories:
            print(f"  {name}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in SETTINGS:
            p = StoryParams(name=NAMES[0], ghost_name=GHOST_NAMES[0], setting=place, seed=base_seed)
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

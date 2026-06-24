#!/usr/bin/env python3
"""
A small ghost-story world about curiosity, repetition, and surprise.

Seed tale:
---
Mina lived in a quiet old house with a squeaky stair and a little chest in the hall.
One night, she kept hearing a soft tap-tap-tap near the attic door.
Every time she looked, the sound stopped.

Mina grew more curious. She followed the sound to a dusty trunk and found a loose strap
dangling from the lid. When the strap swung, it tapped the wood again and again.

Then a gentle surprise arrived: a tiny white ghost was inside the trunk, not to frighten
anyone, but to keep the attic lantern from falling. Mina tied the strap tightly, and the
ghost gave her a happy wave before floating away.

Narrative instruments:
- Curiosity: the hero investigates a repeating sound or sign.
- Repetition: the same small sound or mistake happens more than once.
- Surprise: the hidden cause is revealed, and it is gentle.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"dust": 0.0, "tied": 0.0, "tap": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "surprise": 0.0, "calm": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Strap:
    id: str
    label: str
    phrase: str
    use: str
    fix: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    strap: str
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
        self.fired: set[tuple] = set()
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


def _r_repetition(world: World) -> list[str]:
    out: list[str] = []
    child = world.get(world.facts["hero"])
    if child.meters["tap"] < THRESHOLD:
        return out
    sig = ("repetition", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["curiosity"] += 1
    out.append("The little tap sounded again, as if the house wanted to be noticed.")
    return out


def _r_surprise(world: World) -> list[str]:
    out: list[str] = []
    child = world.get(world.facts["hero"])
    ghost = world.get(world.facts["ghost"])
    strap = world.get(world.facts["strap"])
    if child.memes["curiosity"] < THRESHOLD or strap.meters["tied"] < THRESHOLD:
        return out
    sig = ("surprise", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["surprise"] += 1
    ghost.memes["calm"] += 1
    out.append("A tiny ghost peeked out, gave a shy wave, and smiled at the tidy strap.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_repetition, _r_surprise):
            sents = rule(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


SETTINGS = {
    "hall": Setting(place="the old hall", indoor=True, affords={"listen"}),
    "attic": Setting(place="the attic", indoor=True, affords={"listen"}),
    "bedroom": Setting(place="the bedroom", indoor=True, affords={"listen"}),
}

STRAPS = {
    "trunk_strap": Strap(
        id="trunk_strap",
        label="strap",
        phrase="a dusty leather strap",
        use="hold the attic trunk shut",
        fix="tie the trunk strap tight",
        tags={"strap", "dust", "ghost"},
    ),
    "lantern_strap": Strap(
        id="lantern_strap",
        label="strap",
        phrase="a narrow cloth strap",
        use="hang the lantern safely",
        fix="fasten the lantern strap again",
        tags={"strap", "light", "ghost"},
    ),
    "music_strap": Strap(
        id="music_strap",
        label="strap",
        phrase="a blue velvet strap",
        use="hold a little music box closed",
        fix="button the music box strap neatly",
        tags={"strap", "music", "ghost"},
    ),
}

GIRL_NAMES = ["Mina", "Lily", "Nora", "Ivy", "Mia", "Ella", "Rose"]
BOY_NAMES = ["Theo", "Ben", "Leo", "Finn", "Max", "Eli", "Sam"]
TRAITS = ["curious", "quiet", "brave", "gentle", "thoughtful", "sly"]


@dataclass
class StoryWorldData:
    world: World
    hero: Entity
    parent: Entity
    ghost: Entity
    strap: Entity
    setting: Setting
    strap_def: Strap


def build_storyworld(params: StoryParams) -> StoryWorldData:
    setting = SETTINGS[params.place]
    strap_def = STRAPS[params.strap]
    world = World(setting)

    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    ghost = world.add(Entity(id="ghost", kind="character", type="ghost", label="the little ghost"))
    strap = world.add(Entity(
        id="strap",
        type="strap",
        label="strap",
        phrase=strap_def.phrase,
        owner=ghost.id,
    ))

    world.facts.update(hero=hero.id, parent=parent.id, ghost=ghost.id, strap=strap.id, strap_def=strap_def, setting=setting)

    # Act 1
    world.say(f"{hero.id} was a little {params.trait} {params.gender} who loved quiet places and secret sounds.")
    world.say(f"At {setting.place}, {hero.pronoun('subject')} kept hearing a soft tap-tap-tap near the old attic door.")
    world.say(f"{hero.id} listened once, then listened again, because {hero.pronoun('subject')} was very curious.")

    # Act 2
    world.para()
    child = hero
    child.meters["tap"] += 1
    child.memes["curiosity"] += 1
    propagate(world, narrate=True)
    world.say(f"{child.id} followed the sound past a dusty chair and found {strap_def.phrase} hanging loose.")
    world.say(f"The strap swung and tapped the wood again, and then again, like a tiny house knock.")
    child.meters["tap"] += 1
    child.memes["curiosity"] += 1
    propagate(world, narrate=True)

    # Act 3
    world.para()
    world.say(f"{child.id} reached up, held the strap still, and tied it tight.")
    strap.meters["tied"] += 1
    propagate(world, narrate=True)
    world.say(f"That was when the little ghost peeked out from the trunk and waved.")
    world.say(f'"I was only trying to keep the lantern safe," the ghost said with a warm little sigh.')
    world.say(f"{child.id} smiled, and the room felt calm instead of spooky.")
    world.say(f"At the end, the strap stayed neat, the tapping stopped, and the ghost floated away like a soft white puff.")

    return StoryWorldData(world=world, hero=hero, parent=parent, ghost=ghost, strap=strap, setting=setting, strap_def=strap_def)


def generation_prompts(data: StoryWorldData) -> list[str]:
    hero = data.hero
    strap_def = data.strap_def
    return [
        f'Write a gentle ghost story for a young child that includes the word "strap" and a repeating sound.',
        f"Tell a story where {hero.id} keeps hearing the same tap again and again, then discovers why the {strap_def.label} was moving.",
        f"Write a cozy surprise story in an old house where curiosity leads to a kind ghost and a helpful strap.",
    ]


def story_qa(data: StoryWorldData) -> list[QAItem]:
    hero = data.hero
    strap_def = data.strap_def
    return [
        QAItem(
            question=f"Why did {hero.id} keep listening near the attic door?",
            answer=f"{hero.id} kept listening because {hero.pronoun('subject')} was curious and wanted to find out what was making the soft tap-tap-tap sound.",
        ),
        QAItem(
            question=f"What was making the tapping noise in the old house?",
            answer=f"The tapping came from {strap_def.phrase} swinging and tapping the wood again and again.",
        ),
        QAItem(
            question=f"What surprise did {hero.id} find after holding the strap still?",
            answer="A tiny, gentle ghost peeked out and waved. It was not there to frighten anyone; it was only trying to keep the lantern safe.",
        ),
        QAItem(
            question=f"How did the story end after the strap was tied tight?",
            answer=f"The tapping stopped, the room felt calm, and {hero.id} smiled while the ghost floated away.",
        ),
    ]


def world_qa(data: StoryWorldData) -> list[QAItem]:
    return [
        QAItem(
            question="What is a strap?",
            answer="A strap is a long, narrow piece of material used to hold, carry, or fasten something in place.",
        ),
        QAItem(
            question="Why do people tie things tightly sometimes?",
            answer="People tie things tightly so they stay safe, closed, or steady and do not slip or fall open.",
        ),
        QAItem(
            question="What is a ghost in a story like this?",
            answer="In a gentle story, a ghost can be a pretend spooky character that is actually friendly and quiet.",
        ),
    ]


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


def dump_trace(data: StoryWorldData) -> str:
    lines = ["--- world model state ---"]
    for e in data.world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  place: {data.setting.place}")
    lines.append(f"  strap: {data.strap_def.phrase}")
    return "\n".join(lines)


def explain_invalid(place: str, strap: str) -> str:
    return f"(No story: the combination {place!r} with {strap!r} does not make a gentle repetition-and-surprise ghost story.)"


CURATED = [
    StoryParams(place="attic", strap="trunk_strap", name="Mina", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="hall", strap="lantern_strap", name="Theo", gender="boy", parent="father", trait="thoughtful"),
    StoryParams(place="bedroom", strap="music_strap", name="Ivy", gender="girl", parent="mother", trait="quiet"),
]


def valid_combos() -> list[tuple[str, str]]:
    return [(p, s) for p in SETTINGS for s in STRAPS]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in SETTINGS:
        raise StoryError("(No story: unknown place.)")
    if args.strap and args.strap not in STRAPS:
        raise StoryError("(No story: unknown strap.)")
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.strap:
        combos = [c for c in combos if c[1] == args.strap]
    if not combos:
        raise StoryError(explain_invalid(args.place or "?", args.strap or "?"))
    place, strap = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, strap=strap, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    data = build_storyworld(params)
    return StorySample(
        params=params,
        story=data.world.render(),
        prompts=generation_prompts(data),
        story_qa=story_qa(data),
        world_qa=world_qa(data),
        world=data.world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(StoryWorldData(
            world=sample.world,
            hero=sample.world.get(sample.world.facts["hero"]),
            parent=sample.world.get(sample.world.facts["parent"]),
            ghost=sample.world.get(sample.world.facts["ghost"]),
            strap=sample.world.get(sample.world.facts["strap"]),
            setting=sample.world.facts["setting"],
            strap_def=sample.world.facts["strap_def"],
        )))
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost story world: curiosity, repetition, and a gentle surprise.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--strap", choices=STRAPS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--trait")
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
story(P,S) :- place(P), strap(S).
#show story/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for s in STRAPS:
        lines.append(asp.fact("strap", s))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show story/2."))
    return sorted(set(asp.atoms(model, "story")))


def asp_verify() -> int:
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: clingo gate matches valid_combos() ({len(valid_combos())} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos().")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
            header = f"### {p.name}: {p.place} / {p.strap}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

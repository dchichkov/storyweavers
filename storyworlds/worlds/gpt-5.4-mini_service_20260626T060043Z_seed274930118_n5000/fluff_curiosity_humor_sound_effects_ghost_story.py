#!/usr/bin/env python3
"""
storyworlds/worlds/fluff_curiosity_humor_sound_effects_ghost_story.py
=====================================================================

A tiny ghost-story world with fluff, curiosity, humor, and sound effects.

Seed premise:
A child hears mysterious soft sounds, follows fluffy clues, discovers a harmless
"ghost" in a dusty old room, and learns the spooky noises were only fluff,
wind, and a funny little trick of the house.

The world is built as a stateful simulation:
- curiosity increases when a character notices a strange sound or a fluffy clue
- fear increases when the house makes spooky noises
- humor increases when the mystery turns out harmless or silly
- the final story depends on the simulated resolution, not on a fixed template

This file follows the Storyweavers world contract:
- StoryParams and registries are defined here
- generate() returns a StorySample
- ASP rules are inline in ASP_RULES
- --verify checks the Python gate against the ASP twin and runs sample stories
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

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
    soundscape: str = ""
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    sound: str
    clue: str
    source: str
    resolution: str
    harmless: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    mystery: str
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
        self.sound_events: list[str] = []

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


def meter(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def add_meter(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.meters[key] = meter(ent, key) + amount


def add_meme(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def sound_line(sound: str) -> str:
    return {
        "rustle": "Rustle, rustle.",
        "tap": "Tap-tap-tap.",
        "creak": "Creeeak.",
        "whoosh": "Whoooosh.",
        "thump": "Thump.",
        "flump": "Flump-flump.",
    }.get(sound, f"{sound.capitalize()}.")


def spooky_beat(mystery: Mystery) -> str:
    return {
        "attic": "from up above the ceiling",
        "closet": "from behind the closet door",
        "hallway": "from the dark hallway",
        "basement": "from below the floorboards",
    }.get(mystery.source, "from somewhere in the house")


def light_effect(setting: Setting) -> str:
    return "a small lamp glowed softly" if setting.indoor else "moonlight pooled on the floor"


def _curiosity(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if meter(ent, "noticed") >= THRESHOLD and meter(ent, "curiosity") < THRESHOLD:
            add_meter(ent, "curiosity", 1.0)
            out.append(f"{ent.id} leaned in to listen more carefully.")
    return out


def _fear(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if meter(ent, "heard_spooky") >= THRESHOLD and meter(ent, "fear") < THRESHOLD:
            add_meter(ent, "fear", 1.0)
            out.append(f"The strange sound made {ent.id} squeeze {ent.pronoun('possessive')} hands together.")
    return out


def _humor(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if meter(ent, "mystery_solved") >= THRESHOLD and meter(ent, "humor") < THRESHOLD:
            add_meter(ent, "humor", 1.0)
            out.append(f"{ent.id} gave a small laugh at the silly answer.")
    return out


CAUSAL_RULES = [_curiosity, _fear, _humor]


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


def ask_sound(world: World, child: Entity, mystery: Mystery) -> None:
    add_meter(child, "noticed", 1.0)
    world.sound_events.append(mystery.sound)
    world.say(f"{sound_line(mystery.sound)} It came {spooky_beat(mystery)}.")
    propagate(world)


def inspect_clue(world: World, child: Entity, mystery: Mystery) -> None:
    add_meter(child, "curiosity", 1.0)
    world.say(f"{child.id} followed the clue: {mystery.clue}.")
    world.say(f"Near it, {light_effect(world.setting)}.")
    propagate(world)


def reveal(world: World, child: Entity, parent: Entity, mystery: Mystery) -> None:
    add_meter(child, "mystery_solved", 1.0)
    add_meter(child, "joy", 1.0)
    add_meter(child, "humor", 1.0)
    world.say(
        f"Then {child.id} found the source: {mystery.resolution}. "
        f"It was only a harmless little trick, not a real ghost."
    )
    world.say(
        f"{parent.id} smiled and said the house liked to make spooky noises when the air moved."
    )
    propagate(world)


def tell(setting: Setting, mystery: Mystery, hero_name: str = "Mia", hero_type: str = "girl",
         parent_type: str = "mother", hero_trait: str = "curious") -> World:
    world = World(setting)
    child = world.add(Entity(id=hero_name, kind="character", type=hero_type, tags={"child"}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    ghost = world.add(Entity(id="ghost", kind="thing", type="ghost", label="the ghost", tags={"ghost", "fluff"}))

    add_meter(child, "curiosity", 0.0)
    add_meter(child, "fear", 0.0)
    add_meter(child, "humor", 0.0)

    world.say(
        f"One {('stormy' if mystery.source in {'attic', 'basement', 'hallway'} else 'quiet')} night, "
        f"{hero_name} was a {hero_trait} little {hero_type} in {setting.place}."
    )
    world.say(f"{hero_name} liked to listen for tiny sounds, because every room had a secret.")
    world.say(f"The air felt soft with {mystery.tags and 'fluff' or 'dust'} and old shadows.")

    world.para()
    ask_sound(world, child, mystery)
    inspect_clue(world, child, mystery)
    world.say(
        f"{hero_name} whispered, 'Maybe a ghost is hiding here.' "
        f"But {hero_name} kept looking anyway."
    )

    world.para()
    add_meter(child, "noticed", 1.0)
    add_meter(child, "heard_spooky", 1.0)
    world.say(f"Something went {sound_line(mystery.sound).lower()}")
    world.say(f"That made {hero_name} a little jumpy, but also more curious.")
    propagate(world)

    world.para()
    reveal(world, child, parent, mystery)

    world.facts.update(
        child=child,
        parent=parent,
        ghost=ghost,
        mystery=mystery,
        setting=setting,
        resolved=True,
    )
    return world


SETTINGS = {
    "attic": Setting(place="the attic", indoor=True, soundscape="wind in the rafters", affords={"fluff", "ghost"}),
    "closet": Setting(place="the closet", indoor=True, soundscape="hanger clicks", affords={"fluff", "ghost"}),
    "hallway": Setting(place="the hallway", indoor=True, soundscape="floorboard creaks", affords={"ghost"}),
    "basement": Setting(place="the basement", indoor=True, soundscape="pipe taps", affords={"ghost", "fluff"}),
}

MYSTERIES = {
    "attic_fluff": Mystery(
        id="attic_fluff",
        sound="rustle",
        clue="a small trail of white fluff near a trunk",
        source="attic",
        resolution="a pillow was torn open, and its fluff was drifting around like tiny snow",
        harmless=True,
        tags={"fluff", "ghost"},
    ),
    "closet_fluff": Mystery(
        id="closet_fluff",
        sound="creak",
        clue="a puff of fluff caught on a coat hook",
        source="closet",
        resolution="the closet door was wobbling, and a sweater sleeve had spilled fluffy stuffing",
        harmless=True,
        tags={"fluff", "ghost"},
    ),
    "hallway_sheet": Mystery(
        id="hallway_sheet",
        sound="whoosh",
        clue="a white shape swaying by the lamp",
        source="hallway",
        resolution="a bedsheet had slipped from a chair and was waving in the breeze",
        harmless=True,
        tags={"ghost"},
    ),
    "basement_pipe": Mystery(
        id="basement_pipe",
        sound="tap",
        clue="tiny bumps of dust near the steps",
        source="basement",
        resolution="a loose pipe was tapping the wall like a drum",
        harmless=True,
        tags={"ghost"},
    ),
}

GIRL_NAMES = ["Mia", "Lina", "Nora", "Zoe", "Ivy", "Ella", "Pia", "Rae"]
BOY_NAMES = ["Leo", "Finn", "Theo", "Max", "Ben", "Noah", "Owen", "Eli"]
TRAITS = ["curious", "brave", "silly", "careful", "bright", "bouncy"]


@dataclass
class StoryParams:
    setting: str
    mystery: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for s in SETTINGS:
        for m in MYSTERIES:
            combos.append((s, m))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    mystery = f["mystery"]
    return [
        f'Write a short ghost story for a child named {child.id} that includes the word "fluff".',
        f"Tell a gentle spooky story where {child.id} hears {mystery.sound} sounds and investigates with curiosity.",
        f"Write a funny little mystery story set in {world.setting.place} that ends with a harmless reveal.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    mystery = f["mystery"]
    qa = [
        QAItem(
            question=f"What made {child.id} start looking around in the story?",
            answer=f"{child.id} heard a spooky little {mystery.sound} and noticed a fluffy clue, so {child.pronoun('subject')} wanted to find out what it was.",
        ),
        QAItem(
            question=f"Why did {child.id} feel nervous and curious at the same time?",
            answer=f"The sound seemed ghostly at first, so {child.id} felt a shiver of fear, but the fluffy clue made {child.pronoun('object')} curious enough to keep going.",
        ),
        QAItem(
            question=f"What did {child.id}'s {parent.pronoun('subject') if hasattr(parent, 'pronoun') else 'parent'} say about the spooky noise?",
            answer=f"{parent.id} explained that the house can make odd sounds when air moves or things shift, so it was not a real ghost problem.",
        ),
    ]
    if f.get("resolved"):
        qa.append(QAItem(
            question=f"What was the ghost really?",
            answer=f"It was not a real ghost at all. The mystery turned out to be {mystery.resolution}, which was funny once everyone knew the truth.",
        ))
    return qa


WORLD_KNOWLEDGE = {
    "fluff": [
        QAItem(
            question="What is fluff?",
            answer="Fluff is soft, light stuff like pillow filling, sweater fibers, or fuzzy bits that can float in the air.",
        )
    ],
    "ghost": [
        QAItem(
            question="What do people mean when they say ghost story?",
            answer="A ghost story is a spooky tale about a mystery that may seem scary at first, but sometimes the answer is harmless.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["mystery"].tags)
    out: list[QAItem] = []
    for tag, items in WORLD_KNOWLEDGE.items():
        if tag in tags:
            out.extend(items)
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  sound events: {world.sound_events}")
    return "\n".join(lines)


ASP_RULES = r"""
noticed(C) :- heard(C,_).
curious(C) :- noticed(C).
fear(C) :- heard_spooky(C).
humor(C) :- mystery_solved(C).
resolved(C) :- curious(C), humor(C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if setting.indoor:
            lines.append(asp.fact("indoor", sid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, a))
    for mid, mystery in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("source", mid, mystery.source))
        lines.append(asp.fact("sound", mid, mystery.sound))
        if mystery.harmless:
            lines.append(asp.fact("harmless", mid))
        for t in sorted(mystery.tags):
            lines.append(asp.fact("tag", mid, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show setting/1.\n#show mystery/1.\n"))
    sets = sorted(set(asp.atoms(model, "setting")))
    mys = sorted(set(asp.atoms(model, "mystery")))
    return [(s[0], m[0]) for s in sets for m in mys]


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print(" only in clingo:", sorted(cl - py))
    print(" only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small ghost-story world with fluff, curiosity, humor, and spooky sound effects.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
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
    combos = valid_combos()
    if args.setting and args.mystery and (args.setting, args.mystery) not in combos:
        raise StoryError("No valid combination matches the given options.")
    setting = args.setting or rng.choice(sorted(SETTINGS))
    mystery = args.mystery or rng.choice(sorted(MYSTERIES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, mystery=mystery, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], MYSTERIES[params.mystery], params.name, params.gender, params.parent, params.trait)
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
    StoryParams(setting="attic", mystery="attic_fluff", name="Mia", gender="girl", parent="mother", trait="curious"),
    StoryParams(setting="closet", mystery="closet_fluff", name="Leo", gender="boy", parent="father", trait="silly"),
    StoryParams(setting="hallway", mystery="hallway_sheet", name="Nora", gender="girl", parent="mother", trait="brave"),
    StoryParams(setting="basement", mystery="basement_pipe", name="Finn", gender="boy", parent="father", trait="careful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show setting/1.\n#show mystery/1.\n"))
        print(f"{len(asp.atoms(model, 'setting')) * len(asp.atoms(model, 'mystery'))} compatible combos")
        return

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
            header = f"### {p.name}: {p.mystery} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

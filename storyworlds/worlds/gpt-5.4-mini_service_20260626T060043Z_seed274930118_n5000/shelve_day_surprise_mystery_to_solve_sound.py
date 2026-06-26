#!/usr/bin/env python3
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

GHOSTLY_METER = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    located_in: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "grandmother", "aunt", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "grandfather", "uncle", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def subject_name(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    place: str
    time_of_day: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    label: str
    phrase: str
    clue_noise: str
    surprise: str
    reveal: str
    resolved_by: str
    keyword: str


@dataclass
class SoundEffect:
    id: str
    text: str
    source: str
    meter: str = "spook"


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.zone: str = ""
        self.fired: set[tuple] = set()

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.zone = self.zone
        w.fired = set(self.fired)
        return w


def _r_spook(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters.get("spook", 0.0) < GHOSTLY_METER:
            continue
        if ("spook", e.id) in world.fired:
            continue
        world.fired.add(("spook", e.id))
        e.memes["fear"] = e.memes.get("fear", 0.0) + 1.0
        out.append("A cold little shiver ran through the room.")
    return out


def _r_resolution(world: World) -> list[str]:
    out: list[str] = []
    mystery = world.facts.get("mystery_entity")
    clue = world.facts.get("clue_entity")
    if isinstance(mystery, Entity) and isinstance(clue, Entity):
        if clue.meters.get("found", 0.0) >= GHOSTLY_METER and ("resolve", mystery.id) not in world.fired:
            world.fired.add(("resolve", mystery.id))
            mystery.meters["solved"] = 1.0
            out.append("The mystery finally made sense.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_spook, _r_resolution):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def shelving_story_narration() -> str:
    return "shelve"  # keep the seed word present in the source world


def setup_line(setting: Setting) -> str:
    if setting.time_of_day == "day":
        return f"It was a quiet day in {setting.place}, and even the shadows seemed to listen."
    return f"It was a hush-filled evening in {setting.place}, and the shadows seemed to listen."


def sound_line(sound: SoundEffect) -> str:
    return sound.text


def child_fear_line(child: Entity, sound: SoundEffect) -> str:
    return f"{child.subject_name()} froze at the {sound.text.lower()}."


def tell(world: World, child: Entity, grownup: Entity, shelf: Entity,
         mystery: Mystery, sound: SoundEffect) -> World:
    world.say(setup_line(world.setting))
    world.say(
        f"{child.subject_name()} and {grownup.subject_name()} stood near the old shelf, "
        f"where dusty books leaned like sleepy ghosts."
    )
    world.say(
        f"Then came {sound_line(sound)}, loud enough to make {child.subject_name()} blink."
    )
    world.para()
    world.say(
        f"{child.subject_name()} wanted to know why the shelf kept making that spooky sound."
    )
    world.say(
        f"That was the mystery to solve: {mystery.phrase}."
    )
    world.say(
        f"{grownup.subject_name()} pointed at the shelf and whispered that the room could be tricky on a strange day."
    )
    world.say(
        f"Another sound drifted out: {mystery.clue_noise}."
    )
    child.memes["curiosity"] = child.memes.get("curiosity", 0.0) + 1.0
    shelf.meters["spook"] = shelf.meters.get("spook", 0.0) + 1.0
    propagate(world, narrate=False)
    world.para()
    world.say(
        f"{child.subject_name()} followed the clue, looked behind the shelf, and found {mystery.reveal}."
    )
    world.say(
        f"It was a surprise, but not a bad one."
    )
    world.say(
        f"The mystery was solved when {mystery.resolved_by}."
    )
    world.say(
        f"At the end of the day, the old shelf was only a shelf again, and the room felt warm and still."
    )
    child.memes["relief"] = child.memes.get("relief", 0.0) + 1.0
    world.facts.update(
        child=child,
        grownup=grownup,
        shelf=shelf,
        mystery=mystery,
        sound=sound,
        clue_entity=shelf,
        mystery_entity=shelf,
    )
    return world


SETTINGS = {
    "old_house": Setting(place="the old house", time_of_day="day", mood="ghostly", affords={"listen", "search"}),
    "library": Setting(place="the library", time_of_day="day", mood="quiet", affords={"listen", "search"}),
    "shop": Setting(place="the little shop", time_of_day="day", mood="hushed", affords={"listen", "search"}),
}

MYSTERIES = {
    "mouse": Mystery(
        id="mouse",
        label="mouse",
        phrase="what was making the shelf tap and whisper",
        clue_noise="tik-tik, skritch",
        surprise="a tiny wind-up mouse",
        reveal="a wind-up mouse hiding under a stack of paper",
        resolved_by="the mouse's little key was wound too tight",
        keyword="mystery",
    ),
    "lantern": Mystery(
        id="lantern",
        label="lantern",
        phrase="why the shelf glowed and hummed",
        clue_noise="hum-hum, flicker",
        surprise="a paper lantern with a battery light",
        reveal="a paper lantern tucked behind a jar",
        resolved_by="the battery light had been bumped on",
        keyword="surprise",
    ),
    "cat": Mystery(
        id="cat",
        label="cat",
        phrase="what was rustling behind the shelf",
        clue_noise="scritch, scritch",
        surprise="a kitten with shiny eyes",
        reveal="a kitten curled in a basket behind the shelf",
        resolved_by="the kitten had chased a ribbon and got stuck there",
        keyword="sound",
    ),
}

SOUNDS = {
    "knock": SoundEffect(id="knock", text="Knock-knock, thump", source="the shelf"),
    "creak": SoundEffect(id="creak", text="Creeeak, groooan", source="the old wood"),
    "tap": SoundEffect(id="tap", text="Tap-tap-tap", source="inside the shelf"),
}

NAMES = {
    "girl": ["Mina", "Luna", "Ivy", "Nora", "June"],
    "boy": ["Eli", "Noah", "Theo", "Finn", "Owen"],
}

TRAITS = ["brave", "curious", "quiet", "gentle", "bright"]


@dataclass
class StoryParams:
    place: str
    child_name: str
    child_type: str
    grownup_type: str
    mystery: str
    sound: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, m, s) for p in SETTINGS for m in MYSTERIES for s in SOUNDS]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle ghost-story mystery about a shelf on a day.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--sound", choices=SOUNDS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--grownup", choices=["mother", "father", "grandmother", "grandfather", "aunt", "uncle"])
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
    place = args.place or rng.choice(list(SETTINGS))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    sound = args.sound or rng.choice(list(SOUNDS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    grownup = args.grownup or rng.choice(["mother", "father", "grandmother", "grandfather", "aunt", "uncle"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, child_name=name, child_type=gender, grownup_type=grownup, mystery=mystery, sound=sound, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_type, label=params.child_name))
    grownup = world.add(Entity(id="grownup", kind="character", type=params.grownup_type, label=f"the {params.grownup_type}"))
    shelf = world.add(Entity(id="shelf", kind="thing", type="shelf", label="the old shelf", located_in=params.place))
    mystery = MYSTERIES[params.mystery]
    sound = SOUNDS[params.sound]
    shelf.meters["spook"] = 1.0
    tell(world, child, grownup, shelf, mystery, sound)
    story = world.render()
    prompts = [
        f"Write a gentle ghost-story mystery set in {world.setting.place} on a day with a spooky shelf sound.",
        f"Tell a child-friendly story where {child.subject_name()} hears {sound.text} and solves the mystery.",
        f"Write a story with surprise, mystery to solve, and sound effects about an old shelf.",
    ]
    story_qa = [
        QAItem(
            question=f"What did {child.subject_name()} want to find out about the old shelf?",
            answer=f"{child.subject_name()} wanted to find out {mystery.phrase}.",
        ),
        QAItem(
            question=f"What spooky sound did the shelf make?",
            answer=f"The shelf made {sound.text}.",
        ),
        QAItem(
            question=f"What was the surprise behind the shelf?",
            answer=f"The surprise was {mystery.reveal}.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a shelf for?",
            answer="A shelf is a flat board or ledge used to hold books, jars, or other things.",
        ),
        QAItem(
            question="Why do sounds echo in a quiet room?",
            answer="Sounds can seem louder in a quiet room because there is less noise to cover them up.",
        ),
        QAItem(
            question="What does it mean to solve a mystery?",
            answer="To solve a mystery means to figure out what was causing the puzzling thing to happen.",
        ),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- trace ---")
        for e in sample.world.entities.values():
            print(e.id, e.type, dict(e.meters), dict(e.memes))
    if qa:
        print()
        for section, items in [("prompts", sample.prompts), ("story_qa", sample.story_qa), ("world_qa", sample.world_qa)]:
            print(section)
            for item in items:
                if isinstance(item, str):
                    print(item)
                else:
                    print(f"Q: {item.question}")
                    print(f"A: {item.answer}")


ASP_RULES = r"""
kind(setting).
kind(mystery).
kind(sound).

valid(P, M, S) :- setting(P), mystery(M), sound(S).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery", m))
    for s in SOUNDS:
        lines.append(asp.fact("sound", s))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(place="old_house", child_name="Mina", child_type="girl", grownup_type="mother", mystery="mouse", sound="tap", trait="curious"),
    StoryParams(place="library", child_name="Theo", child_type="boy", grownup_type="grandfather", mystery="cat", sound="creak", trait="brave"),
    StoryParams(place="shop", child_name="Ivy", child_type="girl", grownup_type="aunt", mystery="lantern", sound="knock", trait="gentle"),
]


def format_qa(sample: StorySample) -> str:
    out = []
    out.append("== prompts ==")
    out.extend(sample.prompts)
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

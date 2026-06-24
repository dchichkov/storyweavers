#!/usr/bin/env python3
"""
A small fable-style storyworld about a deaf character, a surprising twist,
a transformation in the middle, and a lesson learned at the end.

The world is built from a simple tale seed:
a deaf little creature is left out of a noisy celebration, finds another way
to join, and changes the whole group by what it learns.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
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
    worn_by: Optional[str] = None
    plural: bool = False
    deaf: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "hen", "owl", "rabbit", "deer", "fox", "mouse"}
        male = {"boy", "father", "dad", "man", "rooster", "frog", "turtle", "crow"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool = False
    sounds: str = ""
    mood: str = ""
    affords: set[str] = field(default_factory=set)


@dataclass
class Event:
    id: str
    verb: str
    noun: str
    twist: str
    transform: str
    lesson: str
    cue: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Guide:
    id: str
    label: str
    phrase: str
    help_line: str
    tail: str
    covers: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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


THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "orchard": Setting(place="the orchard", sounds="birds sang in the branches", mood="sunlit", affords={"song", "drum"}),
    "meadow": Setting(place="the meadow", sounds="grass whispered in the wind", mood="soft", affords={"song", "drum"}),
    "riverside": Setting(place="the riverside", sounds="water chuckled over the stones", mood="bright", affords={"song", "drum"}),
}

EVENTS = {
    "song_day": Event(
        id="song_day",
        verb="sing with the others",
        noun="song day",
        twist="the child could not hear the song at all",
        transform="learned to follow the beat by feeling the drum",
        lesson="everyone can belong in a different way",
        cue="sing",
        tags={"song", "deaf"},
    ),
    "drum_circle": Event(
        id="drum_circle",
        verb="join the drum circle",
        noun="drum circle",
        twist="the loud drum made the deaf child smile instead of shrink away",
        transform="became the one who showed the others the rhythm",
        lesson="kind help can turn a problem into a gift",
        cue="drum",
        tags={"drum", "deaf"},
    ),
    "parade": Event(
        id="parade",
        verb="walk in the parade",
        noun="parade",
        twist="the bell leader forgot to watch the path and stumbled",
        transform="learned that eyes and hands can guide a team too",
        lesson="a leader must notice every friend",
        cue="march",
        tags={"parade", "deaf"},
    ),
}

GUIDES = [
    Guide(
        id="drum",
        label="a little drum",
        phrase="a round little drum with a red strap",
        help_line="The drum can make a clear beat you can feel in your paws.",
        tail="the beat hopped through the ground like a tiny rabbit",
        covers={"sound"},
    ),
    Guide(
        id="shell",
        label="a shiny shell",
        phrase="a shiny shell worn on a ribbon",
        help_line="The shell could catch the light whenever it was time to turn.",
        tail="the light flashed like a wink from the sun",
        covers={"light"},
    ),
    Guide(
        id="scarf",
        label="a bright scarf",
        phrase="a bright scarf for waving signals",
        help_line="The scarf could show a pattern for stop, go, and spin.",
        tail="the scarf swayed like a small flag in the breeze",
        covers={"signal"},
    ),
]

ANIMALS = {
    "rabbit": {"type": "rabbit", "label": "rabbit"},
    "fox": {"type": "fox", "label": "fox"},
    "deer": {"type": "deer", "label": "deer"},
    "mouse": {"type": "mouse", "label": "mouse"},
}


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story is reasonable when the setting supports the event.
valid_story(S, E, G) :- setting(S), event(E), guide(G), affords(S, C), cue_of(E, C).

% A guide is a useful fix when it matches the event cue.
good_fix(E, G) :- event(E), guide(G), cue_of(E, C), covers(G, C).

valid_combo(S, E, G) :- valid_story(S, E, G), good_fix(E, G).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if setting.indoors:
            lines.append(asp.fact("indoors", sid))
        for cue in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, cue))
    for eid, ev in EVENTS.items():
        lines.append(asp.fact("event", eid))
        lines.append(asp.fact("cue_of", eid, ev.cue))
    for gid, g in enumerate(GUIDES):
        lines.append(asp.fact("guide", f"g{gid}"))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", f"g{gid}", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s, setting in SETTINGS.items():
        for e, ev in EVENTS.items():
            if ev.cue not in setting.affords:
                continue
            for g in GUIDES:
                if ev.cue in g.covers:
                    combos.append((s, e, g.id))
    return combos


def explain_rejection(setting: Setting, event: Event, guide: Guide) -> str:
    return (
        f"(No story: {setting.place} supports {event.cue}, but {guide.label} does not fit "
        f"the twist of {event.noun}. The guide must actually help the deaf child join.)"
    )


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    event: str
    guide: str
    name: str
    animal: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Story mechanics
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    event = EVENTS[params.event]
    guide_def = next(g for g in GUIDES if g.id == params.guide)

    world = World(setting)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=ANIMALS[params.animal]["type"],
        label=params.name,
        traits=["small", "deaf"],
        deaf=True,
    ))
    elder = world.add(Entity(
        id="elder",
        kind="character",
        type="owl",
        label="the old owl",
    ))
    tool = world.add(Entity(
        id="guide",
        type="thing",
        label=guide_def.label,
        phrase=guide_def.phrase,
        owner=hero.id,
    ))
    tool.worn_by = hero.id

    hero.memes["hope"] = 0
    hero.memes["left_out"] = 0
    hero.memes["joy"] = 0
    hero.meters["still"] = 0

    world.say(f"{hero.id} was a small deaf {hero.type} who loved gentle days at {setting.place}.")
    world.say(f"{setting.sounds.capitalize()}, and {hero.id} watched the others from the edge of the path.")
    world.say(f"Every year there was a {event.noun}, and {hero.id} wanted to {event.verb}.")
    world.say(f"{event.twist.capitalize()}. That made {hero.id} feel left out.")
    world.para()

    hero.memes["left_out"] += 1
    world.say(f"The old owl noticed and came closer with {guide_def.phrase}.")
    world.say(guide_def.help_line)
    world.say(f'"If the sound is hard to hear," said the owl, "then let the beat, the light, or the signals lead you."')
    world.say(f"That was the twist: {hero.id} did not need to hear the whole thing to join it.")
    world.para()

    hero.memes["hope"] += 1
    hero.meters["still"] += 1
    world.say(f"{hero.id} held {hero.pronoun('possessive')} breath, watched the cue, and tried again.")
    world.say(f"With the {guide_def.label}, {hero.id} {event.transform}.")
    hero.memes["joy"] += 1
    hero.memes["left_out"] = 0
    world.say(f"Soon {hero.id} was no longer at the edge. {hero.id.capitalize()} was in the middle, moving with the group.")
    world.say(f"The others followed {hero.id}'s clear signs, and the whole path felt kind and new.")
    world.para()

    world.say(f"At the end of the day, the lesson was simple: {event.lesson}.")
    world.say(f"{hero.id} went home with {guide_def.tail}, and even the old owl smiled at the quiet kind of victory.")

    world.facts.update(
        hero=hero,
        elder=elder,
        guide=tool,
        guide_def=guide_def,
        event=event,
        setting=setting,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    event = f["event"]
    return [
        f'Write a short fable about a deaf {hero.type} who wants to {event.verb} at {world.setting.place}.',
        f"Tell a gentle story with a twist, a transformation, and a lesson learned about {event.noun}.",
        f"Write a child-friendly fable where a deaf character finds another way to join the group.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    event = f["event"]
    guide = f["guide_def"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, a small deaf {hero.type} who wants to {event.verb}.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The twist was that {hero.id} could not hear the celebration at first, so the group needed a different way to include {hero.pronoun('object')}.",
        ),
        QAItem(
            question=f"How did {hero.id} change by the end?",
            answer=f"{hero.id} transformed from feeling left out to helping lead the group with {guide.label}.",
        ),
        QAItem(
            question=f"What lesson was learned?",
            answer=f"The lesson learned was that {event.lesson}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does deaf mean?",
            answer="Deaf means a person or animal cannot hear sounds in the usual way.",
        ),
        QAItem(
            question="What is a fable?",
            answer="A fable is a short story that often uses animals and ends with a lesson.",
        ),
        QAItem(
            question="What can a drum be used for in a story like this?",
            answer="A drum can help show a beat that someone can feel and follow, even if they cannot hear well.",
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.deaf:
            bits.append("deaf=True")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
NAMES = ["Mina", "Toby", "Lena", "Pip", "Nico", "June", "Sage", "Ivy"]
ANIMAL_ORDER = ["rabbit", "fox", "deer", "mouse"]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.event is None or c[1] == args.event)
              and (args.guide is None or c[2] == args.guide)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, event, guide = rng.choice(sorted(combos))
    animal = args.animal or rng.choice(ANIMAL_ORDER)
    name = args.name or rng.choice(NAMES)
    return StoryParams(place=place, event=event, guide=guide, name=name, animal=animal)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="orchard", event="song_day", guide="drum", name="Mina", animal="rabbit"),
    StoryParams(place="meadow", event="drum_circle", guide="scarf", name="Pip", animal="mouse"),
    StoryParams(place="riverside", event="parade", guide="shell", name="Toby", animal="deer"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny fable world about deafness, transformation, twist, and lesson learned."
    )
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--event", choices=sorted(EVENTS))
    ap.add_argument("--guide", choices=[g.id for g in GUIDES])
    ap.add_argument("--animal", choices=sorted(ANIMALS))
    ap.add_argument("--name")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for s, e, g in combos:
            print(f"  {s:10} {e:12} {g}")
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
            header = f"### {p.name}: {p.event} at {p.place} (guide: {p.guide})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

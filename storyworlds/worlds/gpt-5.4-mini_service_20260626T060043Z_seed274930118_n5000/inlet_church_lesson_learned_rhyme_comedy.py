#!/usr/bin/env python3
"""
A standalone story world: a comedy about a child at a church near an inlet,
where a noisy rhyme causes trouble and a gentle lesson is learned.

The seed premise is simple:
- A child arrives at a church by an inlet.
- They love making a rhyme, but the church asks for quiet.
- Their funny mistake echoes through the hall.
- A kind adult helps them learn the lesson and turn the rhyme into a soft, respectful one.
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
# Core world model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    place: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def obj(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    inland_note: str = ""
    sound: str = ""
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    noise: str
    mess: str
    effect: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Lesson:
    id: str
    lesson: str
    soft_version: str
    helper_line: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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
        import copy
        return World(
            setting=self.setting,
            entities=copy.deepcopy(self.entities),
            paragraphs=[[]],
            facts=dict(self.facts),
            fired=set(self.fired),
        )


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "inlet_church": Setting(
        place="the church by the inlet",
        inland_note="The inlet water glimmered outside the windows.",
        sound="The gulls and water lapped softly beyond the walls.",
        affords={"rhyme", "lesson"},
    )
}

ACTIVITIES = {
    "rhyme": Activity(
        id="rhyme",
        verb="make a rhyme",
        gerund="making rhymes",
        noise="a bouncy rhyme",
        mess="noise",
        effect="echoed through the church",
        tags={"rhyme", "comedy"},
    ),
    "lesson": Activity(
        id="lesson",
        verb="learn the lesson",
        gerund="learning the lesson",
        noise="a quiet whisper",
        mess="calm",
        effect="made the room peaceful",
        tags={"lesson"},
    ),
}

LESSONS = {
    "quiet_in_church": Lesson(
        id="quiet_in_church",
        lesson="church is a place for quiet voices and careful steps",
        soft_version="a tiny rhyme sung in a whisper",
        helper_line="They can still be funny without being loud.",
    )
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Zoe", "Ava"]
BOY_NAMES = ["Leo", "Finn", "Theo", "Max", "Ben"]
TRAITS = ["curious", "cheerful", "silly", "playful", "bouncy"]


@dataclass
class StoryParams:
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------

def _do_rhyme(world: World, child: Entity, church: Entity) -> None:
    child.memes["glee"] = child.memes.get("glee", 0) + 1
    child.memes["volume"] = child.memes.get("volume", 0) + 1
    church.meters["echo"] = church.meters.get("echo", 0) + 1
    world.say(
        f"{child.id} blurted out a rhyme and {child.pronoun('possessive')} voice "
        f"{ACTIVITIES['rhyme'].effect}."
    )
    world.say(
        f"The rhyme was so bouncy that even the candles seemed to wobble."
    )


def _warn(world: World, adult: Entity, child: Entity, lesson: Lesson) -> None:
    world.say(
        f"{adult.pronoun().capitalize()} smiled and said, "
        f"'{lesson.lesson}.'"
    )
    world.say(
        f"Then {adult.pronoun()} added, '{lesson.helper_line}'"
    )


def _soften(world: World, child: Entity, lesson: Lesson) -> None:
    child.memes["guilt"] = child.memes.get("guilt", 0) + 1
    child.memes["understanding"] = child.memes.get("understanding", 0) + 1
    child.memes["volume"] = 0
    world.say(
        f"{child.id} tried again, this time with {lesson.soft_version}."
    )
    world.say(
        f"The new version was tiny and neat, and it sat in the air like a feather."
    )


def tell_story(params: StoryParams) -> World:
    setting = SETTINGS["inlet_church"]
    world = World(setting=setting)

    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={},
        memes={},
    ))
    adult = world.add(Entity(
        id="Caretaker",
        kind="character",
        type="mother" if params.gender == "girl" else "father",
        label="the grown-up",
        meters={},
        memes={},
    ))
    church = world.add(Entity(
        id="Church",
        kind="thing",
        type="church",
        label="the church",
        place=setting.place,
        meters={},
        memes={},
    ))

    lesson = LESSONS["quiet_in_church"]

    # Beginning
    world.say(
        f"{child.id} came to {setting.place} with a grin."
    )
    world.say(
        f"Outside, {setting.inland_note}"
    )
    world.say(
        f"{child.id} felt {params.trait} and wanted to {ACTIVITIES['rhyme'].verb}."
    )

    # Middle turn
    world.para()
    world.say(
        f"But inside the church, the walls seemed to listen."
    )
    _do_rhyme(world, child, church)
    world.say(
        f"A few heads turned at once, as if the whole room had jumped."
    )
    _warn(world, adult, child, lesson)

    # Resolution
    world.para()
    _soften(world, child, lesson)
    world.say(
        f"{child.id} nodded and learned that a joke can be funny without a shout."
    )
    world.say(
        f"In the end, the rhyme was smaller, the church was calm, and the inlet still sparkled outside."
    )

    world.facts.update(
        child=child,
        adult=adult,
        church=church,
        lesson=lesson,
        setting=setting,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    lesson = f["lesson"]
    return [
        "Write a short comedy story for a young child about a church by an inlet, a loud rhyme, and a lesson learned.",
        f"Tell a gentle funny story where {child.id} visits {world.setting.place} and learns that {lesson.lesson}.",
        "Write a child-friendly story that ends with a quieter rhyme after a silly mistake in church.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    adult: Entity = f["adult"]
    lesson: Lesson = f["lesson"]
    return [
        QAItem(
            question=f"Where did {child.id} go at the start of the story?",
            answer=f"{child.id} went to {world.setting.place}, where the inlet could be heard and seen outside.",
        ),
        QAItem(
            question=f"What funny thing did {child.id} do that caused trouble?",
            answer=f"{child.id} made a rhyme too loudly, and it echoed through the church.",
        ),
        QAItem(
            question=f"What lesson did {adult.pronoun()} teach {child.id}?",
            answer=f"{adult.pronoun().capitalize()} taught that {lesson.lesson}.",
        ),
        QAItem(
            question=f"How did the story end for {child.id}?",
            answer=f"{child.id} learned to make a quieter rhyme, and the church became calm again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a church?",
            answer="A church is a quiet place where people gather, sit carefully, and often speak in soft voices.",
        ),
        QAItem(
            question="What is an inlet?",
            answer="An inlet is a narrow stretch of water that reaches into the land from the sea.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a funny pattern in words where the endings sound alike, like cat and hat.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
setting(inlet_church).
affords(inlet_church,rhyme).
affords(inlet_church,lesson).

activity(rhyme).
activity(lesson).

valid_story(Setting, ChildMood, Ending) :-
    setting(Setting),
    ChildMood = "silly",
    Ending = "quiet_lesson".

has_comedy(Setting) :- setting(Setting), affords(Setting,rhyme).
has_lesson(Setting) :- setting(Setting), affords(Setting,lesson).
"""

def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", "inlet_church")]
    lines.append(asp.fact("affords", "inlet_church", "rhyme"))
    lines.append(asp.fact("affords", "inlet_church", "lesson"))
    lines.append(asp.fact("activity", "rhyme"))
    lines.append(asp.fact("activity", "lesson"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    atoms = set(asp.atoms(model, "valid_story"))
    expected = {("inlet_church", "silly", "quiet_lesson")}
    if atoms == expected:
        print("OK: ASP parity verified.")
        return 0
    print("MISMATCH: ASP parity failed.")
    print("  got:", sorted(atoms))
    print("  expected:", sorted(expected))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.place:
            bits.append(f"place={e.place}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy story world: inlet, church, rhyme, lesson learned.")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        vals = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(vals)} compatible story shape(s):")
        for t in vals:
            print("  ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        presets = [
            StoryParams(name="Mia", gender="girl", trait="silly"),
            StoryParams(name="Leo", gender="boy", trait="bouncy"),
            StoryParams(name="Nora", gender="girl", trait="cheerful"),
        ]
        samples = [generate(p) for p in presets]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + i
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
            header = f"### {p.name}: {p.gender}, {p.trait}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

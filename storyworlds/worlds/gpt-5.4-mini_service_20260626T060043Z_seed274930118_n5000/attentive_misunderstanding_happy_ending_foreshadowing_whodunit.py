#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/attentive_misunderstanding_happy_ending_foreshadowing_whodunit.py
================================================================================================

A small whodunit-style story world about an attentive child, a puzzling mix-up,
and a happy ending. The mystery is tiny and child-facing: someone notices clues,
misunderstands what they mean, then learns the real answer and fixes the problem.

Core premise from the seed:
- attentive
- misunderstanding
- happy ending
- foreshadowing
- whodunit style

The domain is a quiet library room where a small object goes missing, clues are
noticed with care, and the final reveal turns out kinder than the characters
first feared.
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
# Model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    hidden: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    detail: str
    afford: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    kind: str
    text: str
    points_to: str
    foreshadows: str = ""


@dataclass
class Suspect:
    id: str
    label: str
    role: str
    good_reason: str
    real_action: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
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


@dataclass
class StoryParams:
    setting: str
    suspect: str
    clue: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "library": Setting(
        place="the little library",
        detail="Tall shelves made long shadows, and the reading rug was very quiet.",
        afford={"search", "read", "sort"},
    ),
    "museum": Setting(
        place="the small museum",
        detail="Glass cases gleamed, and the hallway felt still as a whisper.",
        afford={"search", "look", "sort"},
    ),
    "classroom": Setting(
        place="the classroom",
        detail="Crayons, books, and cubbies waited in neat rows, but one cubby was not neat at all.",
        afford={"search", "look", "sort"},
    ),
}

SUSPECTS = {
    "cat": Suspect(
        id="cat",
        label="the library cat",
        role="helper",
        good_reason="likes warm paper boxes",
        real_action="had curled up beside the lost object and nudged it under a bench",
    ),
    "ranger": Suspect(
        id="ranger",
        label="the night ranger",
        role="helper",
        good_reason="checks doors and windows after closing",
        real_action="had moved the key ring to a safer hook",
    ),
    "parent": Suspect(
        id="parent",
        label="the grown-up helper",
        role="helper",
        good_reason="was tidying up the room before snack time",
        real_action="had put the missing item in the basket by mistake",
    ),
}

CLUES = {
    "pawprint": Clue(
        id="pawprint",
        kind="track",
        text="tiny dusty paw prints near the chair",
        points_to="cat",
        foreshadows="The prints looked suspicious at first, but they were only a trail to where the object had slid.",
    ),
    "keys": Clue(
        id="keys",
        kind="object",
        text="a jangling key ring hanging on a low hook",
        points_to="ranger",
        foreshadows="The keys made a little clink-clink sound, like they had been placed there carefully.",
    ),
    "basket": Clue(
        id="basket",
        kind="object",
        text="a basket with a ribbon on the handle",
        points_to="parent",
        foreshadows="The basket was close to the missing item all along, which was easy to miss in a hurry.",
    ),
    "bookmark": Clue(
        id="bookmark",
        kind="trace",
        text="a torn paper bookmark with a star on it",
        points_to="cat",
        foreshadows="The bookmark matched the reading rug, hinting that the missing thing had been moved while books were being sorted.",
    ),
}

OBJECTS = {
    "glasses": Entity(id="glasses", type="glasses", label="glasses", phrase="a pair of bright blue glasses", plural=True),
    "shell": Entity(id="shell", type="shell", label="shell", phrase="a shiny shell charm"),
    "badge": Entity(id="badge", type="badge", label="badge", phrase="a small helper badge"),
}

HERO_NAMES = ["Mina", "Leo", "Ari", "Nora", "Toby", "Ivy", "Maya", "Noah"]
HELPER_NAMES = ["Pip", "June", "Sam", "Rin", "Tess", "Ollie"]
HERO_TYPES = ["girl", "boy"]
HELPER_TYPES = ["girl", "boy"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for setting_id, setting in SETTINGS.items():
        for clue_id, clue in CLUES.items():
            for suspect_id, suspect in SUSPECTS.items():
                if setting_id == "classroom" and clue_id == "keys" and suspect_id != "parent":
                    continue
                out.append((setting_id, clue_id, suspect_id))
    return out


def explain_rejection(setting_id: str, clue_id: str, suspect_id: str) -> str:
    return (
        f"(No story: the clue '{clue_id}' does not fit a tidy mystery in {setting_id} "
        f"with suspect '{suspect_id}'. Try a clue that can plausibly be misunderstood "
        f"before the happy ending.)"
    )


# ---------------------------------------------------------------------------
# Narrative world
# ---------------------------------------------------------------------------
def is_attentive(hero: Entity) -> bool:
    return hero.memes.get("attentive", 0.0) >= 1.0


def story_setup(world: World, hero: Entity, helper: Entity, suspect: Suspect, clue: Clue, missing: Entity) -> None:
    world.say(
        f"{hero.id} was an attentive {hero.type} who noticed small things other people skipped over."
    )
    world.say(
        f"One quiet day at {world.setting.place}, {hero.id} and {helper.id} found that {missing.phrase} was gone."
    )
    world.say(world.setting.detail)
    world.say(
        f"Near the empty spot, they saw {clue.text}."
    )
    world.facts["clue_hint"] = clue.foreshadows


def misunderstanding(world: World, hero: Entity, helper: Entity, suspect: Suspect, clue: Clue) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1.0
    helper.memes["worry"] = helper.memes.get("worry", 0.0) + 1.0
    world.say(
        f"{helper.id} whispered that the clue meant {suspect.label} must have taken the missing thing."
    )
    world.say(
        f"{hero.id} agreed at first, because {clue.text} sounded like a strong secret."
    )
    world.say(
        f"But the clue had a softer meaning than it first seemed."
    )
    world.facts["misunderstanding"] = True


def foreshadow(world: World, clue: Clue) -> None:
    world.say(clue.foreshadows)


def reveal(world: World, hero: Entity, helper: Entity, suspect: Suspect, clue: Clue, missing: Entity) -> None:
    world.say(
        f"{hero.id} looked again and noticed one more tiny detail: the missing item had left a faint trail."
    )
    world.say(
        f"That trail led to {suspect.label}, but not because {suspect.label} was stealing."
    )
    world.say(
        f"Instead, {suspect.real_action}."
    )
    world.say(
        f"The missing {missing.label} was found safely, and everyone laughed with relief."
    )
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
    helper.memes["joy"] = helper.memes.get("joy", 0.0) + 1.0
    world.facts["resolved"] = True


def ending(world: World, hero: Entity, helper: Entity, suspect: Suspect, missing: Entity) -> None:
    world.say(
        f"In the end, {hero.id} put the {missing.label} back where it belonged, and {suspect.label} got a gentle pat for helping."
    )
    world.say(
        f"It was a happy ending: the room was tidy again, the mystery was solved, and {hero.id}'s careful eyes had made the difference."
    )


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def tell(setting: Setting, suspect: Suspect, clue: Clue, hero_name: str, hero_type: str,
         helper_name: str, helper_type: str, missing_id: str = "glasses") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type))
    suspect_ent = world.add(Entity(id=suspect.id, kind="character", type="adult", label=suspect.label))
    missing = world.add(Entity(**{**OBJECTS[missing_id].__dict__}))
    missing.owner = hero.id

    hero.memes["attentive"] = 1.0
    world.facts.update(hero=hero, helper=helper, suspect=suspect_ent, clue=clue, missing=missing, setting=setting)

    story_setup(world, hero, helper, suspect, clue, missing)
    world.para()
    misunderstanding(world, hero, helper, suspect, clue)
    world.para()
    foreshadow(world, clue)
    reveal(world, hero, helper, suspect, clue, missing)
    ending(world, hero, helper, suspect, missing)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    clue: Clue = f["clue"]
    missing: Entity = f["missing"]
    suspect: Entity = f["suspect"]
    return [
        f'Write a short whodunit for a child about an attentive {hero.type} named {hero.id} who notices {clue.text}.',
        f"Tell a gentle mystery where {hero.id} thinks {suspect.label} caused a problem, but the clue turns out to mean something kinder.",
        f'Write a story with a misunderstanding, a foreshadowing clue, and a happy ending about a missing {missing.label}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    suspect: Entity = f["suspect"]
    clue: Clue = f["clue"]
    missing: Entity = f["missing"]
    return [
        QAItem(
            question=f"Who noticed the clue first in the mystery?",
            answer=f"{hero.id} noticed it first because {hero.id} was attentive and kept looking carefully.",
        ),
        QAItem(
            question=f"What did {helper.id} think the clue meant at first?",
            answer=f"{helper.id} thought {suspect.label} had taken the missing {missing.label}, which was the misunderstanding.",
        ),
        QAItem(
            question=f"What clue was left behind near the missing thing?",
            answer=f"The clue was {clue.text}. It seemed suspicious at first, but it later made sense.",
        ),
        QAItem(
            question=f"What happened at the end of the story?",
            answer=f"The missing {missing.label} was found, {suspect.label} was not the thief, and the story ended happily.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    clue: Clue = f["clue"]
    out = [
        QAItem(
            question="What is a clue in a mystery?",
            answer="A clue is a small piece of information that helps someone figure out what happened.",
        ),
        QAItem(
            question="Why should an attentive person look carefully at details?",
            answer="Because tiny details can show what really happened and help solve a puzzle without guessing too fast.",
        ),
    ]
    if clue.kind == "track":
        out.append(QAItem(
            question="What are tracks or footprints?",
            answer="Tracks are marks left behind by feet, paws, or wheels, and they can show where something went.",
        ))
    return out


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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.hidden:
            bits.append("hidden=True")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.kind == "character":
            bits.append(f"type={e.type}")
        else:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A clue can point to a suspect and still be misread as a sign of guilt.
misunderstood(C) :- clue(C), foreshadows(C).

% A story is valid when the setting, clue, and suspect line up.
valid_story(S, C, P) :- setting(S), clue(C), suspect(P), fits(S, C, P).

% A clue fits when it can plausibly be misunderstood and still lead to a happy reveal.
fits(S, C, P) :- setting(S), clue(C), suspect(P), usable(S, C), red_herring(C, P).

% Children should be able to understand the ending.
happy_end(S, C, P) :- valid_story(S, C, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.afford):
            lines.append(asp.fact("affords", sid, a))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("points_to", cid, c.points_to))
        lines.append(asp.fact("foreshadows", cid))
    for pid, p in SUSPECTS.items():
        lines.append(asp.fact("suspect", pid))
        lines.append(asp.fact("red_herring", pid, p.id))
    # mark all clues as usable in this tiny world
    for cid in CLUES:
        lines.append(asp.fact("usable", "library", cid))
        lines.append(asp.fact("usable", "museum", cid))
        lines.append(asp.fact("usable", "classroom", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Params / CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny whodunit story world with attentive clues and a happy ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
    combos = [c for c in combos if (args.setting is None or c[0] == args.setting)
              and (args.clue is None or c[1] == args.clue)
              and (args.suspect is None or c[2] == args.suspect)]
    if not combos:
        raise StoryError("(No valid mystery combination matches the given options.)")
    setting, clue, suspect = rng.choice(sorted(combos))
    hero_gender = args.gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(HERO_NAMES)
    helper_name = args.helper or rng.choice(HELPER_NAMES)
    return StoryParams(
        setting=setting,
        suspect=suspect,
        clue=clue,
        hero_name=hero_name,
        hero_type=hero_gender,
        helper_name=helper_name,
        helper_type=helper_gender,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        SUSPECTS[params.suspect],
        CLUES[params.clue],
        params.hero_name,
        params.hero_type,
        params.helper_name,
        params.helper_type,
    )
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
        print(f"{len(vals)} compatible stories:")
        for row in vals:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("library", "cat", "pawprint", "Mina", "girl", "Pip", "boy"),
            StoryParams("museum", "keys", "ranger", "Leo", "boy", "June", "girl"),
            StoryParams("classroom", "basket", "parent", "Nora", "girl", "Sam", "boy"),
            StoryParams("library", "bookmark", "cat", "Ari", "boy", "Tess", "girl"),
        ]
        samples = [generate(p) for p in curated]
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

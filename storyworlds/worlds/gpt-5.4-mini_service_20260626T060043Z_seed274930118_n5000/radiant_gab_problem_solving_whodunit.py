#!/usr/bin/env python3
"""
storyworlds/worlds/radiant_gab_problem_solving_whodunit.py
===========================================================

A tiny whodunit storyworld about a child detective named Gab, a radiant clue,
and a careful chain of reasoning that solves a small mystery.

The world is deliberately small: one missing object, a few plausible suspects,
and a single evidence trail that the detective can follow to a satisfying
reveal. The prose is aimed at young readers, but the structure is classical:
setup, suspicion, clue-chasing, solution, and a closing image that proves the
world changed.

Seeded premise:
---
Gab loved problems that needed careful thinking. In a quiet room with a radiant
lamp, something valuable went missing. Everyone had a story, but only one story
fit the clues. Gab had to look, compare, and think before the truth could come
out.

World updates:
---
    missing object -> worry + confusion
    clue found -> clue_count + confidence
    incorrect guess -> suspicion rises, confidence falls a little
    correct deduction -> relief + order restored
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
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool
    lighting: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    missing_label: str
    missing_phrase: str
    location: str
    clue_kind: str
    clue_phrase: str
    culprit_id: str
    culprit_reason: str
    evidence: tuple[str, ...]


@dataclass
class StoryParams:
    setting: str
    mystery: str
    name: str
    sidekick: str
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


SETTINGS = {
    "library": Setting(
        place="the old library",
        indoors=True,
        lighting="radiant desk lamp",
        affords={"search", "question"},
    ),
    "gallery": Setting(
        place="the small art gallery",
        indoors=True,
        lighting="radiant skylight",
        affords={"search", "question"},
    ),
    "workshop": Setting(
        place="the maker workshop",
        indoors=True,
        lighting="radiant ceiling lamp",
        affords={"search", "question"},
    ),
}

MYSTERIES = {
    "coin": Mystery(
        id="coin",
        missing_label="silver coin",
        missing_phrase="a shiny silver coin",
        location="the donation box",
        clue_kind="dust",
        clue_phrase="a little trail of dust on the windowsill",
        culprit_id="mouse",
        culprit_reason="it liked shiny things and had carried the coin into the wall nook",
        evidence=("dust", "small", "hidden"),
    ),
    "pin": Mystery(
        id="pin",
        missing_label="glass pin",
        missing_phrase="a bright glass pin",
        location="the display shelf",
        clue_kind="thread",
        clue_phrase="a blue thread caught on a nail",
        culprit_id="cat",
        culprit_reason="it had brushed past the shelf and knocked the pin behind a crate",
        evidence=("thread", "blue", "crate"),
    ),
    "key": Mystery(
        id="key",
        missing_label="brass key",
        missing_phrase="an old brass key",
        location="the locked drawer",
        clue_kind="smudge",
        clue_phrase="a muddy smudge on the drawer handle",
        culprit_id="dog",
        culprit_reason="it had nosed the drawer open while chasing a toy",
        evidence=("mud", "handle", "drawer"),
    ),
}

SIDEKICKS = {
    "gab": {"label": "Gab", "type": "boy"},
    "mira": {"label": "Mira", "type": "girl"},
    "pip": {"label": "Pip", "type": "boy"},
}

GIRL_NAMES = ["Mira", "Ava", "Nora", "Lina", "Zoe"]
BOY_NAMES = ["Gab", "Finn", "Leo", "Theo", "Max"]


def valid_combos() -> list[tuple[str, str]]:
    return [(s, m) for s in SETTINGS for m in MYSTERIES]


def explain_rejection(setting: str, mystery: str) -> str:
    return f"(No story: the {setting} mystery '{mystery}' does not make a reasonable whodunit.)"


def reasonableness_gate(setting: str, mystery: str) -> None:
    if setting not in SETTINGS:
        raise StoryError(f"(No story: unknown setting '{setting}'.)")
    if mystery not in MYSTERIES:
        raise StoryError(f"(No story: unknown mystery '{mystery}'.)")


def _question(world: World, ent: Entity, about: str) -> None:
    ent.memes["curiosity"] = ent.memes.get("curiosity", 0.0) + 1
    world.say(f"{ent.id} asked a careful question about {about}.")


def _search(world: World, ent: Entity, mystery: Mystery) -> None:
    ent.meters["searches"] = ent.meters.get("searches", 0.0) + 1
    ent.memes["confidence"] = ent.memes.get("confidence", 0.0) + 1
    world.say(
        f"{ent.id} looked by {mystery.location} under the {world.setting.lighting}, "
        f"searching for a clue."
    )


def _find_clue(world: World, ent: Entity, mystery: Mystery) -> None:
    key = ("clue", mystery.id)
    if key in world.fired:
        return
    world.fired.add(key)
    ent.meters["clues"] = ent.meters.get("clues", 0.0) + 1
    ent.memes["confidence"] = ent.memes.get("confidence", 0.0) + 1
    world.facts["clue_found"] = mystery.clue_phrase
    world.say(
        f"Then {ent.id} noticed {mystery.clue_phrase}. "
        f"That looked important, because it did not belong there."
    )


def _infer(world: World, ent: Entity, mystery: Mystery) -> None:
    ent.memes["confidence"] = ent.memes.get("confidence", 0.0) + 1
    world.say(
        f"{ent.id} thought about the clue, the missing {mystery.missing_label}, "
        f"and who could reach it without anyone noticing."
    )


def _reveal(world: World, ent: Entity, mystery: Mystery, culprit: Entity) -> None:
    ent.memes["relief"] = ent.memes.get("relief", 0.0) + 1
    ent.memes["confidence"] = ent.memes.get("confidence", 0.0) + 1
    culprit.memes["caught"] = culprit.memes.get("caught", 0.0) + 1
    world.say(
        f"At last, {ent.id} pointed to {culprit.id}. "
        f"{mystery.missing_phrase.capitalize()} had gone missing, but the clue fit: "
        f"{mystery.culprit_reason}."
    )
    world.say(
        f"Everyone saw that the clue matched the missing thing, and the mystery was solved."
    )


def tell(setting_key: str, mystery_key: str, hero_name: str, sidekick_key: str) -> World:
    setting = SETTINGS[setting_key]
    mystery = MYSTERIES[mystery_key]
    world = World(setting)

    hero_type = "boy" if hero_name in BOY_NAMES else "girl"
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    sidekick_info = SIDEKICKS[sidekick_key]
    sidekick = world.add(Entity(id=sidekick_info["label"], kind="character", type=sidekick_info["type"]))
    culprit_type = {"mouse": "thing", "cat": "thing", "dog": "thing"}[mystery.culprit_id]
    culprit = world.add(Entity(id=mystery.culprit_id, kind="character" if culprit_type == "thing" else "thing", type=culprit_type))

    world.facts.update(
        setting=setting,
        mystery=mystery,
        hero=hero,
        sidekick=sidekick,
        culprit=culprit,
    )

    world.say(
        f"In {setting.place}, under a {setting.lighting}, {hero.id} and {sidekick.id} found a problem."
    )
    world.say(
        f"The {mystery.missing_label} from {mystery.location} had vanished, and nobody wanted to guess wrong."
    )

    world.para()
    _question(world, hero, mystery.missing_label)
    _search(world, hero, mystery)
    _find_clue(world, sidekick, mystery)

    world.para()
    _infer(world, hero, mystery)
    world.say(
        f"{sidekick.id} listened, then repeated the facts out loud so nothing would get muddled."
    )
    world.say(
        f"{hero.id} compared the clue with the missing item and the places everyone had stood."
    )
    _reveal(world, hero, mystery, culprit)

    world.para()
    world.say(
        f"In the end, the {mystery.missing_label} was returned, the room felt calm again, "
        f"and the {setting.lighting} glowed softly over a solved mystery."
    )

    world.facts["solved"] = True
    world.facts["clue_phrase"] = mystery.clue_phrase
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting = f["setting"]
    mystery = f["mystery"]
    hero = f["hero"]
    sidekick = f["sidekick"]
    return [
        f'Write a child-friendly whodunit set in {setting.place} with a radiant clue and the word "radiant".',
        f"Tell a short mystery where {hero.id} and {sidekick.id} solve the case of the missing {mystery.missing_label}.",
        f'Write a problem-solving story in which a careful detective notices "{mystery.clue_kind}" and figures out who moved the {mystery.missing_label}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    setting = f["setting"]
    mystery = f["mystery"]
    hero = f["hero"]
    sidekick = f["sidekick"]
    culprit = f["culprit"]
    return [
        QAItem(
            question=f"What problem did {hero.id} and {sidekick.id} have to solve in {setting.place}?",
            answer=(
                f"They had to find the missing {mystery.missing_label}. "
                f"It had disappeared from {mystery.location}, so they had to think carefully."
            ),
        ),
        QAItem(
            question=f"What clue helped {hero.id} solve the case?",
            answer=(
                f"The important clue was {mystery.clue_phrase}. "
                f"It stood out because it did not belong where it was found."
            ),
        ),
        QAItem(
            question=f"Who turned out to be the one who caused the mystery?",
            answer=(
                f"The clue led to {culprit.id}. "
                f"{mystery.culprit_reason.capitalize()}."
            ),
        ),
        QAItem(
            question=f"How did the story end after the case was solved?",
            answer=(
                f"The missing {mystery.missing_label} was returned, and the room felt calm again. "
                f"The radiant light still shone, but now everything made sense."
            ),
        ),
    ]


WORLD_KNOWLEDGE = {
    "radiant": [
        QAItem(
            question="What does radiant mean?",
            answer="Radiant means shining with bright light or warm glow.",
        )
    ],
    "clue": [
        QAItem(
            question="What is a clue?",
            answer="A clue is a small piece of information that helps someone solve a mystery.",
        )
    ],
    "problem": [
        QAItem(
            question="What does it mean to solve a problem?",
            answer="To solve a problem means to figure out what is wrong and make it better.",
        )
    ],
    "question": [
        QAItem(
            question="Why do detectives ask questions?",
            answer="Detectives ask questions so they can compare answers and find the truth.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        qa
        for tag in ("radiant", "clue", "problem", "question")
        if tag in WORLD_KNOWLEDGE
        for qa in WORLD_KNOWLEDGE[tag]
    ]


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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(parts)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="library", mystery="coin", name="Gab", sidekick="mira"),
    StoryParams(setting="gallery", mystery="pin", name="Mira", sidekick="gab"),
    StoryParams(setting="workshop", mystery="key", name="Gab", sidekick="pip"),
]


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("has_culprit", mid, m.culprit_id))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Setting,Mystery) :- setting(Setting), mystery(Mystery).
has_solution(Mystery) :- has_culprit(Mystery,_).
valid_story(Setting,Mystery) :- valid(Setting,Mystery), has_solution(Mystery).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small radiant whodunit for Gab.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--sidekick", choices=SIDEKICKS)
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
    if args.setting and args.mystery:
        reasonableness_gate(args.setting, args.mystery)

    combos = [
        (s, m)
        for s, m in valid_combos()
        if (args.setting is None or s == args.setting)
        and (args.mystery is None or m == args.mystery)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, mystery = rng.choice(sorted(combos))
    hero_name = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    sidekick = args.sidekick or rng.choice(sorted(SIDEKICKS))
    return StoryParams(setting=setting, mystery=mystery, name=hero_name, sidekick=sidekick)


def generate(params: StoryParams) -> StorySample:
    world = tell(params.setting, params.mystery, params.name, params.sidekick)
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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (setting, mystery) combos:\n")
        for setting, mystery in triples:
            print(f"  {setting:10} {mystery:8}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.mystery} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

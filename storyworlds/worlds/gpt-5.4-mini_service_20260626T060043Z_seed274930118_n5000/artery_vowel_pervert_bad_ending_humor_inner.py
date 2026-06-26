#!/usr/bin/env python3
"""
artery_vowel_pervert_bad_ending_humor_inner.py
==============================================

A small mystery-flavored story world about a child, a clue, and a bad ending.
The seed words are woven into the domain: artery, vowel, and pervert.

Premise:
- A curious child notices a strange note, a painted map, and an odd person who
  keeps muttering about letters and routes.
- The child follows a clue trail through a small setting.
- Humor comes from the child's inner monologue, but the outcome is a bad ending:
  the clue is misunderstood, the trail goes cold, and the real answer slips away.

The world models physical state with meters and emotional state with memes.
"""

from __future__ import annotations

import argparse
import copy
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"dust": 0.0, "tension": 0.0, "clue": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "worry": 0.0, "amused": 0.0, "unease": 0.0, "resolve": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    indoor: bool
    mystery_nooks: list[str] = field(default_factory=list)


@dataclass
class Clue:
    label: str
    phrase: str
    truth: str
    decoy: str
    odd_mark: str
    hide_place: str
    risk_word: str


@dataclass
class StoryParams:
    setting: str
    clue: str
    hero_name: str
    hero_type: str
    suspect_type: str
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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = copy.deepcopy(self.facts)
        return w


def _narrate_inner(hero: Entity, text: str) -> str:
    return f'({hero.id} thought: "{text}")'


def setup_line(world: World, hero: Entity, suspect: Entity, clue: Clue) -> None:
    world.say(
        f"{hero.id} was a {hero.type} who loved quiet mysteries, especially when a clue "
        f"looked too strange to be honest."
    )
    world.say(
        f"On the table sat {clue.phrase}, and nearby stood {suspect.label}, who kept "
        f"glancing at the word {clue.risk_word} as if it might bite."
    )
    world.say(
        _narrate_inner(hero, "If a clue whispers in a funny way, it is either clever or lying. I hope it is clever.")
    )


def clue_tension(world: World, hero: Entity, suspect: Entity, clue: Clue) -> None:
    hero.memes["curiosity"] += 1
    suspect.meters["tension"] += 1
    world.say(
        f"{hero.id} followed the little marks on the floor to {clue.hide_place}. "
        f"The marks curved like a secret path through the {world.setting.place}."
    )
    world.say(
        f"{suspect.label} smiled too quickly and said, \"It is only a vowel game.\""
    )
    world.say(
        _narrate_inner(hero, "That is exactly what someone says when it is not only a vowel game.")
    )
    world.say(
        f"{hero.id} noticed that {clue.odd_mark} was painted beside the trail, and that made the room feel colder."
    )


def false_guess(world: World, hero: Entity, clue: Clue) -> None:
    hero.memes["amused"] += 1
    hero.memes["worry"] += 1
    world.say(
        f"{hero.id} guessed that the clue must point to an artery under the sink, because the line on the map bent like one."
    )
    world.say(
        _narrate_inner(hero, "That would be an amazing secret to find in a hallway, which is why it is probably wrong.")
    )
    world.say(
        f"Then {hero.id} leaned closer and saw that the red line was just paint, not blood, not a path, and not a promise."
    )


def reveal_and_bad_end(world: World, hero: Entity, suspect: Entity, clue: Clue) -> None:
    hero.memes["resolve"] += 1
    hero.memes["unease"] += 1
    world.say(
        f"At last, {hero.id} opened the small box at {clue.hide_place}, but inside was only a torn paper with a broken vowel on it."
    )
    world.say(
        f"{suspect.label} laughed and said the real message had been moved earlier, before anyone started listening."
    )
    world.say(
        _narrate_inner(hero, "Of course. The last place you check is always where the answer used to be.")
    )
    world.say(
        f"So the mystery ended badly: the true clue was gone, the room stayed quiet, and {hero.id} was left with the wrong answer and a very puzzled face."
    )


def tell_story(world: World) -> World:
    hero = world.add(Entity(id=world.facts["hero_name"], kind="character", type=world.facts["hero_type"]))
    suspect = world.add(Entity(id="suspect", kind="character", type=world.facts["suspect_type"], label="the odd visitor"))
    clue: Clue = world.facts["clue_obj"]

    setup_line(world, hero, suspect, clue)
    world.para()
    clue_tension(world, hero, suspect, clue)
    world.para()
    false_guess(world, hero, clue)
    world.para()
    reveal_and_bad_end(world, hero, suspect, clue)
    return world


SETTINGS = {
    "hallway": Setting(place="the hallway", indoor=True, mystery_nooks=["the coat rack", "the shoe bench", "the mail shelf"]),
    "library": Setting(place="the library", indoor=True, mystery_nooks=["the quiet aisle", "the return cart", "the window seat"]),
    "basement": Setting(place="the basement", indoor=True, mystery_nooks=["the old trunk", "the furnace corner", "the cracked tile"]),
}

CLUES = {
    "artery": Clue(
        label="artery map",
        phrase="a folded map with a red artery line",
        truth="the red line marked an old hallway shortcut",
        decoy="the line pointed to a secret treasure",
        odd_mark="a tiny smudge shaped like a comma",
        hide_place="the return cart",
        risk_word="artery",
    ),
    "vowel": Clue(
        label="vowel note",
        phrase="a note full of vowels and tiny arrows",
        truth="the letters spelled a locker number",
        decoy="the letters named a magic spell",
        odd_mark="a circle around the letter O",
        hide_place="the shoe bench",
        risk_word="vowel",
    ),
    "pervert": Clue(
        label="weird warning",
        phrase="a strange warning from the pervert",
        truth="the warning was really about a person who liked to twist the story",
        decoy="the warning proved the room was haunted",
        odd_mark="a crooked underline under the word pervert",
        hide_place="the coat rack",
        risk_word="pervert",
    ),
}

HERO_NAMES = ["Mina", "Ivo", "Nia", "Tess", "Luca", "Pia", "Eli", "Noor"]
HERO_TYPES = ["girl", "boy"]
SUSPECT_TYPES = ["man", "woman"]
TRAITS = ["curious", "shy", "bright", "careful", "funny"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    clue = f["clue_obj"]
    return [
        f'Write a short mystery for a child that uses the word "{clue.risk_word}" and ends badly.',
        f"Tell a funny, eerie story about {f['hero_name']} in {world.setting.place} who thinks a clue is about {clue.risk_word}.",
        f"Write a simple inner-monologue mystery where the hero follows a clue, makes a wrong guess, and misses the real answer.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero_name"]
    clue: Clue = f["clue_obj"]
    suspect = "the odd visitor"
    return [
        QAItem(
            question=f"What kind of story is this?",
            answer="It is a small mystery story with a funny inner voice and a bad ending, because the answer gets away before the hero can catch it.",
        ),
        QAItem(
            question=f"What did {hero} think the red line might mean?",
            answer=f"{hero} thought it might be an artery under the sink, because the line bent like a secret path.",
        ),
        QAItem(
            question=f"What was strange about {suspect}?",
            answer=f"{suspect} smiled too quickly and kept talking about {clue.risk_word} as if it were only a joke.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended badly: the real clue was already moved, so the hero was left with the wrong answer and a puzzled face.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an artery?",
            answer="An artery is a blood vessel that carries blood away from the heart to the rest of the body.",
        ),
        QAItem(
            question="What is a vowel?",
            answer="A vowel is a letter like A, E, I, O, or U, and vowels help make words easier to say.",
        ),
        QAItem(
            question="What does pervert mean in this story world?",
            answer="In this story world, it means an odd person who twists meaning around and makes the mystery harder to trust.",
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
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(X) :- hero_name(X).
suspect(X) :- suspect_type(X).

odd(X) :- clue(X), clue_word(X, artery).
odd(X) :- clue(X), clue_word(X, vowel).
odd(X) :- clue(X), clue_word(X, pervert).

bad_ending(Story) :- story(Story), moved_away(clue), wrong_guess(hero).
humor(Story) :- story(Story), inner_monologue(hero), funny_thought(hero).

show_story(S) :- bad_ending(S), humor(S).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("story", "mystery"),
        asp.fact("hero_name", "hero"),
        asp.fact("suspect_type", "suspect"),
    ]
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("clue_word", cid, cid))
    lines.append(asp.fact("moved_away", "clue"))
    lines.append(asp.fact("wrong_guess", "hero"))
    lines.append(asp.fact("inner_monologue", "hero"))
    lines.append(asp.fact("funny_thought", "hero"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show show_story/1."))
    has = set(asp.atoms(model, "show_story"))
    expected = {("mystery",)}
    if has == expected:
        print("OK: ASP parity matches Python reasonableness gate.")
        return 0
    print("MISMATCH between ASP and Python reasonableness gate.")
    print("  ASP:", sorted(has))
    print("  PY :", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery story world with a bad ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--suspect-type", choices=SUSPECT_TYPES)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    clue = args.clue or rng.choice(list(CLUES))
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    suspect_type = args.suspect_type or rng.choice(SUSPECT_TYPES)
    name = args.name or rng.choice(HERO_NAMES)
    if clue == "pervert" and suspect_type == "boy":
        raise StoryError("The pervert clue works best with an odd adult suspect, not a boy.")
    return StoryParams(
        setting=setting,
        clue=clue,
        hero_name=name,
        hero_type=hero_type,
        suspect_type=suspect_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.setting])
    clue = CLUES[params.clue]
    world.facts = {
        "hero_name": params.hero_name,
        "hero_type": params.hero_type,
        "suspect_type": params.suspect_type,
        "clue_obj": clue,
    }
    tell_story(world)
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
    StoryParams(setting="hallway", clue="artery", hero_name="Mina", hero_type="girl", suspect_type="woman"),
    StoryParams(setting="library", clue="vowel", hero_name="Ivo", hero_type="boy", suspect_type="man"),
    StoryParams(setting="basement", clue="pervert", hero_name="Tess", hero_type="girl", suspect_type="woman"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show show_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show show_story/1."))
        print(sorted(set(asp.atoms(model, "show_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

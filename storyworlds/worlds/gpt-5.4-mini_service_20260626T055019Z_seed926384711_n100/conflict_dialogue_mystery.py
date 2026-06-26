#!/usr/bin/env python3
"""
Story world: a small mystery with dialogue and a gentle conflict.

A child and a helper look for a missing item, ask questions, notice clues, and
end with the truth. The story is state-driven: suspicion rises, clues reduce it,
and the conflict resolves when the hidden item is found.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    hidden: bool = False
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
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
    indoor: bool = False


@dataclass
class Clue:
    id: str
    label: str
    hint: str
    location: str
    reveal: str


@dataclass
class Mystery:
    id: str
    missing: str
    lost_where: str
    recovered_from: str
    suspicion_word: str
    clue_word: str
    dialogue_open: str
    dialogue_close: str


@dataclass
class StoryParams:
    setting: str
    mystery: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_gender: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


SETTINGS = {
    "library": Setting(place="the library", indoor=True),
    "attic": Setting(place="the attic", indoor=True),
    "garden": Setting(place="the garden", indoor=False),
}

MYSTERIES = {
    "bell": Mystery(
        id="bell",
        missing="silver bell",
        lost_where="on the reading table",
        recovered_from="inside a big storybook",
        suspicion_word="suspicion",
        clue_word="clue",
        dialogue_open='"The bell is gone," said {hero}. "Who moved it?"',
        dialogue_close='"I did not take it," said {helper}. "Let us follow the clues."',
    ),
    "key": Mystery(
        id="key",
        missing="little brass key",
        lost_where="near the paint box",
        recovered_from="under a folded cloth",
        suspicion_word="doubt",
        clue_word="hint",
        dialogue_open='"The key has vanished," said {hero}. "This feels strange."',
        dialogue_close='"I did not hide it," said {helper}. "We should look carefully."',
    ),
    "lantern": Mystery(
        id="lantern",
        missing="tiny lantern",
        lost_where="by the window seat",
        recovered_from="behind a cushion",
        suspicion_word="worry",
        clue_word="trace",
        dialogue_open='"The lantern is missing," said {hero}. "Something is off."',
        dialogue_close='"I did not move it," said {helper}. "Let us talk and search."',
    ),
}

CLUES = {
    "bell": [
        Clue("glint", "a little glint", "It flashed silver under the page edge.", "storybook", "The bell had been tucked inside a big storybook."),
        Clue("dust", "dusty page", "A soft round mark on the page showed where something had rested.", "storybook", "The bell had left a round dent in the book."),
    ],
    "key": [
        Clue("cloth", "folded cloth", "One corner of cloth looked oddly puffed up.", "cloth", "The key was hiding under the folded cloth."),
        Clue("scratch", "small scratch", "A tiny scratch on the table matched the key's teeth.", "table", "The key had been set down and covered by cloth."),
    ],
    "lantern": [
        Clue("cushion", "soft cushion", "One cushion had a round bump under its seam.", "cushion", "The lantern was behind the cushion."),
        Clue("string", "loose string", "A dangling string pointed toward the window seat.", "window", "The lantern had slipped out of sight near the cushion."),
    ],
}

HERO_NAMES = ["Mia", "Nora", "Leo", "Finn", "Ava", "Eli", "Tara", "Ben"]
HELPER_NAMES = ["Mina", "Owen", "Lola", "Hugo", "Zoe", "Iris", "Noah", "Jade"]

ASSERTIVE_LINES = [
    "That does not sound right.",
    "Something is not adding up.",
    "The room felt full of questions.",
    "They needed to think before pointing fingers.",
]

RESOLUTION_LINES = [
    "Soon the little mystery made sense.",
    "At last the clues fit together.",
    "The answer was hiding in plain sight.",
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small dialogue mystery storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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


def _pronoun(gender: str, case: str = "subject") -> str:
    return {"girl": {"subject": "she", "object": "her", "possessive": "her"},
            "boy": {"subject": "he", "object": "him", "possessive": "his"}}[gender][case]


def _name_for_gender(rng: random.Random, gender: str) -> str:
    pool = HERO_NAMES if gender == "girl" else [n for n in HERO_NAMES + HELPER_NAMES if n not in {"Mina", "Lola", "Iris", "Jade", "Tara", "Ava", "Nora", "Zoe"}]
    return rng.choice(pool)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if hero_gender == "girl" else "girl")
    hero_name = args.hero_name or _name_for_gender(rng, hero_gender)
    helper_name = args.helper_name or _name_for_gender(rng, helper_gender)
    if hero_name == helper_name:
        helper_name = _name_for_gender(rng, helper_gender)
    return StoryParams(
        setting=setting,
        mystery=mystery,
        hero_name=hero_name,
        hero_gender=hero_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
    )


def _make_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_gender, label=params.hero_name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_gender, label=params.helper_name))
    missing = world.add(Entity(id="missing", type="object", label=mystery.missing, phrase=mystery.missing, owner=hero.id, caretaker=hero.id))
    world.facts.update(hero=hero, helper=helper, missing=missing, mystery=mystery)
    return world


def _introduce(world: World) -> None:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    mystery = world.facts["mystery"]
    world.say(f"{hero.label} was in {world.setting.place}, where quiet corners could hide odd things.")
    world.say(f"{hero.label} loved solving small puzzles, and {helper.label} liked helping with careful questions.")
    world.say(mystery.dialogue_open.format(hero=hero.label, helper=helper.label))
    world.say(mystery.dialogue_close.format(hero=hero.label, helper=helper.label))


def _conflict(world: World) -> None:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    mystery = world.facts["mystery"]
    missing = world.facts["missing"]
    hero.memes["worry"] = 1.0
    hero.memes["suspicion"] = 1.0
    helper.memes["calm"] = 1.0
    world.para()
    world.say(f"{hero.label} frowned. \"If nobody took {missing.label}, then where did it go?\"")
    world.say(f"{helper.label} shook their head. \"Not every missing thing is lost forever,\" {helper.pronoun().capitalize()} said.")
    world.say(random.choice(ASSERTIVE_LINES))
    world.say(f"{hero.label} looked under the table, then at the shelves, then back at {helper.label}.")
    world.say(f"\"It feels like a mystery,\" {hero.label} said. \"And I do not want to blame the wrong person.\"")
    hero.memes["conflict"] = 1.0


def _search_and_reveal(world: World) -> None:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    mystery = world.facts["mystery"]
    clues = CLUES[mystery.id]
    clue1, clue2 = clues
    world.para()
    world.say(f"{helper.label} pointed to {clue1.location}. \"Look at this {clue1.label},\" {helper.label} said.")
    world.say(f"{hero.label} leaned closer. \"That means someone moved it carefully,\" {hero.label} said.")
    world.say(clue1.hint)
    world.say(f"Then {helper.label} checked {clue2.location}. \"Here is another {mystery.clue_word},\" {helper.label} said.")
    world.say(clue2.hint)
    hero.memes["worry"] = 0.0
    hero.memes["suspicion"] = 0.0
    world.facts["reveal"] = clue1.reveal + " " + clue2.reveal


def _resolution(world: World) -> None:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    mystery = world.facts["mystery"]
    missing = world.facts["missing"]
    hero.memes["joy"] = 1.0
    hero.memes["conflict"] = 0.0
    world.para()
    world.say(random.choice(RESOLUTION_LINES))
    world.say(f"{hero.label} opened the big storybook, and there it was: {missing.label} {mystery.recovered_from}.")
    world.say(f"\"Oh!\" said {hero.label}. \"It was hiding all along.\"")
    world.say(f"{helper.label} smiled. \"Now the clues make sense.\"")
    world.say(f"{hero.label} laughed and put the {missing.label} back where it belonged.")
    world.say(f"By the end, the room felt calm again, and both friends were glad they had talked first.")


def tell(params: StoryParams) -> World:
    world = _make_world(params)
    _introduce(world)
    _conflict(world)
    _search_and_reveal(world)
    _resolution(world)
    return world


def _story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    mystery = world.facts["mystery"]
    missing = world.facts["missing"]
    return [
        QAItem(
            question=f"What was the mystery in the story?",
            answer=f"The mystery was that {missing.label} had gone missing in {world.setting.place}.",
        ),
        QAItem(
            question=f"Why did {hero.label} feel upset at first?",
            answer=f"{hero.label} felt upset because {missing.label} was missing and the room did not make sense yet.",
        ),
        QAItem(
            question=f"How did {helper.label} help solve the problem?",
            answer=f"{helper.label} helped by looking for clues, asking careful questions, and staying calm instead of guessing.",
        ),
        QAItem(
            question=f"Where was the missing item found?",
            answer=f"It was found {mystery.recovered_from}.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The conflict ended, the missing thing was found, and the two friends felt happy and relieved.",
        ),
    ]


def _world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue in a mystery?",
            answer="A clue is a small piece of information that helps someone figure out what happened.",
        ),
        QAItem(
            question="Why do people ask questions in a mystery?",
            answer="People ask questions so they can understand the situation and solve the problem carefully.",
        ),
        QAItem(
            question="What does it mean to make a careful guess?",
            answer="A careful guess means thinking about the clues first instead of deciding too quickly.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    mystery = world.facts["mystery"]
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    missing = world.facts["missing"]
    prompts = [
        f'Write a short child-friendly mystery story that includes dialogue and the word "conflict".',
        f"Tell a gentle mystery where {hero.label} and {helper.label} look for {missing.label} and solve the problem by talking.",
        f"Write a small story in a cozy setting where a missing object is found through clues and careful dialogue.",
    ]
    world_qa = _world_qa(world)
    story_qa = _story_qa(world)
    world.facts["prompts"] = prompts
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


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


CURATED = [
    StoryParams(setting="library", mystery="bell", hero_name="Mia", hero_gender="girl", helper_name="Owen", helper_gender="boy"),
    StoryParams(setting="attic", mystery="key", hero_name="Leo", hero_gender="boy", helper_name="Lola", helper_gender="girl"),
    StoryParams(setting="garden", mystery="lantern", hero_name="Ava", hero_gender="girl", helper_name="Finn", helper_gender="boy"),
]


ASP_RULES = r"""
% A mystery is valid when a missing thing exists and there is at least one clue.
valid_mystery(S, M) :- setting(S), mystery(M), has_clue(M).

has_clue(M) :- clue(M, _).

valid_story(S, M, H, K) :- valid_mystery(S, M), hero_gender(H), helper_gender(K).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if setting.indoor:
            lines.append(asp.fact("indoor", sid))
    for mid, mystery in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("missing", mid, mystery.missing))
        lines.append(asp.fact("lost_where", mid, mystery.lost_where))
        for clue in CLUES[mid]:
            lines.append(asp.fact("clue", mid, clue.id))
    lines.append(asp.fact("hero_gender", "girl"))
    lines.append(asp.fact("hero_gender", "boy"))
    lines.append(asp.fact("helper_gender", "girl"))
    lines.append(asp.fact("helper_gender", "boy"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = {(s, m, h, k) for s in SETTINGS for m in MYSTERIES for h in ("girl", "boy") for k in ("girl", "boy")}
    python_set = {(s, m, h, k) for (s, m, h, k) in python_set if CLUES.get(m)}
    if clingo_set == python_set:
        print(f"OK: clingo gate matches Python gate ({len(clingo_set)} stories).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("clingo only:", sorted(clingo_set - python_set))
    print("python only:", sorted(python_set - clingo_set))
    return 1


def build_story(params: StoryParams) -> StorySample:
    return generate(params)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        setting=args.setting or rng.choice(list(SETTINGS)),
        mystery=args.mystery or rng.choice(list(MYSTERIES)),
        hero_name=args.hero_name or _name_for_gender(rng, args.hero_gender or rng.choice(["girl", "boy"])),
        hero_gender=args.hero_gender or rng.choice(["girl", "boy"]),
        helper_name=args.helper_name or _name_for_gender(rng, args.helper_gender or rng.choice(["girl", "boy"])),
        helper_gender=args.helper_gender or rng.choice(["girl", "boy"]),
    )


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/4."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
A tiny nursery-rhyme storyworld about an old, cross autobot and a little mystery
to solve. The world is built from a short simulated premise, then driven through
setup, suspicion, clues, a reveal, and a tidy ending.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import asdict, dataclass, field
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
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"child", "girl", "boy"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        if self.type in {"autobot", "robot"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"mother", "father", "woman", "man"}:
            female = self.type in {"mother", "woman"}
            if female:
                return {"subject": "she", "object": "her", "possessive": "her"}[case]
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool = True
    mood: str = "cozy"
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    title: str
    clue_word: str
    cause: str
    found_by: str
    reveal: str
    locations: set[str]


@dataclass
class Tool:
    id: str
    label: str
    helps: set[str]
    prep: str
    tail: str


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


def is_reasonable(setting: Setting, mystery: Mystery, tool: Tool) -> bool:
    return mystery.id in setting.affords and mystery.id in tool.helps


ASP_RULES = r"""
mystery_possible(S, M) :- setting(S), mystery(M), affords(S, M).
tool_helps(T, M) :- tool(T), helps(T, M).
solvable(S, M) :- mystery_possible(S, M), tool_helps(T, M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for m in sorted(s.affords):
            lines.append(asp.fact("affords", sid, m))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("clue_word", mid, m.clue_word))
        for loc in sorted(m.locations):
            lines.append(asp.fact("located", mid, loc))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for h in sorted(t.helps):
            lines.append(asp.fact("helps", tid, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show solvable/2."))
    return sorted(set(asp.atoms(model, "solvable")))


@dataclass
class StoryParams:
    setting: str
    mystery: str
    tool: str
    name: str
    helper: str
    seed: Optional[int] = None


SETTINGS = {
    "nursery": Setting(place="the nursery", indoor=True, mood="cozy", affords={"toy", "button", "lullaby"}),
    "playroom": Setting(place="the playroom", indoor=True, mood="bright", affords={"toy", "button", "marble"}),
    "attic": Setting(place="the attic", indoor=True, mood="dusty", affords={"button", "key", "toy"}),
}

MYSTERIES = {
    "toy": Mystery(
        id="toy",
        title="the missing toy",
        clue_word="toy",
        cause="the toy rolled under a cradle",
        found_by="under the cradle",
        reveal="The little toy had only rolled away, not vanished.",
        locations={"nursery", "playroom", "attic"},
    ),
    "button": Mystery(
        id="button",
        title="the missing button",
        clue_word="button",
        cause="a button popped loose from a coat",
        found_by="inside a mitten basket",
        reveal="The lost button was shining inside the basket all along.",
        locations={"nursery", "attic"},
    ),
    "key": Mystery(
        id="key",
        title="the missing key",
        clue_word="key",
        cause="the key slipped behind a rocking chair",
        found_by="behind the chair",
        reveal="The little key had only slid behind the chair.",
        locations={"attic"},
    ),
}

TOOLS = {
    "lamp": Tool(id="lamp", label="a little lamp", helps={"toy", "button", "key"}, prep="lit a little lamp", tail="shone the lamp on the floor"),
    "magnifier": Tool(id="magnifier", label="a round magnifier", helps={"button", "key"}, prep="picked up a round magnifier", tail="looked very closely"),
    "stick": Tool(id="stick", label="a smooth stick", helps={"toy"}, prep="tapped with a smooth stick", tail="nudged the rug and crate"),
}

GIRL_NAMES = ["Mina", "Lily", "Pip", "Nora", "June"]
BOY_NAMES = ["Tom", "Ben", "Finn", "Perry", "Jules"]
HELPERS = ["grandma", "grandpa", "aunt", "uncle"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid, s in SETTINGS.items():
        for mid, m in MYSTERIES.items():
            if mid not in s.affords:
                continue
            for tid, t in TOOLS.items():
                if is_reasonable(s, m, t):
                    out.append((sid, mid, tid))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme mystery storyworld about an old cross autobot.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("No valid mystery story matches the chosen options.")
    setting, mystery, tool = rng.choice(sorted(combos))
    name = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(setting=setting, mystery=mystery, tool=tool, name=name, helper=helper)


def _say_little_rhyme(world: World, text: str) -> None:
    world.say(text)


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    hero = world.add(Entity(id=params.name, kind="character", type="child", label=params.name, traits=["little", "curious"]))
    helper = world.add(Entity(id=params.helper, kind="character", type="elder", label=params.helper, traits=["senile", "cross"]))
    autobot = world.add(Entity(id="autobot", kind="character", type="autobot", label="the autobot", traits=["senile", "cross"]))
    mystery = MYSTERIES[params.mystery]
    tool = TOOLS[params.tool]

    world.facts.update(hero=hero, helper=helper, autobot=autobot, mystery=mystery, tool=tool)

    _say_little_rhyme(world, f"{hero.id} was a little one, bright as a spark, in {world.setting.place}.")
    _say_little_rhyme(world, f"With {helper.label} and the {autobot.label}, there lived an old, cross autobot who muttered, \"Humph!\"")
    _say_little_rhyme(world, f"The {autobot.label} was senile and cross, yet loved a puzzle more than a spoon.")
    _say_little_rhyme(world, f"One soft day, a mystery came: {mystery.title}.")
    world.para()

    _say_little_rhyme(world, f"The clue was a {mystery.clue_word}, small and neat, but nobody knew where it could meet.")
    _say_little_rhyme(world, f"{helper.id} frowned and said, \"Oh dear me, oh my, we must look and look, or we shall not know why.\"")
    _say_little_rhyme(world, f"The {autobot.label} was cross, yet tapped a wheel and said, \"First the floor, then the sill, then the shadow still.\"")
    _say_little_rhyme(world, f"{hero.id} held the {tool.label} and followed close by.")
    world.para()

    _say_little_rhyme(world, f"{tool.prep.capitalize()}, and the room grew bright.")
    _say_little_rhyme(world, f"They peeped and they peeked in the nursery light; the {autobot.label} was senile but keen when the clue came in sight.")
    _say_little_rhyme(world, f"At last they found it {mystery.found_by}, just as the rhyme had sung.")
    _say_little_rhyme(world, f"{mystery.reveal}")
    _say_little_rhyme(world, f"The {autobot.label} blinked once, then twice, and the cross old hum became a happy vice.")
    _say_little_rhyme(world, f"{helper.id} laughed, {hero.id} clapped, and the little mystery was done.")

    world.facts["resolved"] = True
    world.facts["ending"] = f"{mystery.reveal} The autobot was cross no more."
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, autobot, mystery, tool = f["hero"], f["helper"], f["autobot"], f["mystery"], f["tool"]
    return [
        QAItem(
            question=f"Who helped {hero.id} solve the mystery in {world.setting.place}?",
            answer=f"{helper.id} helped, and the old cross autobot helped too."
        ),
        QAItem(
            question=f"What kind of autobot was in the story?",
            answer=f"It was a senile and cross autobot, but it still liked solving puzzles."
        ),
        QAItem(
            question=f"What was the mystery?",
            answer=f"It was {mystery.title}, and the clue word was {mystery.clue_word}."
        ),
        QAItem(
            question=f"What did they use to look for the clue?",
            answer=f"They used {tool.label} to search carefully."
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended when they found the missing thing and the autobot was cross no more."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something puzzling that people try to figure out by looking for clues."
        ),
        QAItem(
            question="What does a magnifier do?",
            answer="A magnifier helps you look at tiny things more closely."
        ),
        QAItem(
            question="What does it mean to be cross?",
            answer="If someone is cross, they feel grumpy or annoyed."
        ),
        QAItem(
            question="What does senile mean?",
            answer="Senile means very old and forgetful, though a story can use it for a silly old character."
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short nursery-rhyme story about a child, an old cross autobot, and a mystery to solve in {world.setting.place}.',
        f'Tell a cozy rhyme where {f["hero"].id} and {f["helper"].id} help a senile autobot solve {f["mystery"].title}.',
        f'Compose a gentle story with clues, a lamp, and a happy reveal, using the words autobot, senile, and cross.',
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


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


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(cl - py))
    print("  only in python:", sorted(py - cl))
    return 1


def asp_valid() -> list[tuple]:
    return asp_valid_impl()


def asp_valid_impl() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show solvable/2."))
    return sorted(set(asp.atoms(model, "solvable")))


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    StoryParams(setting="nursery", mystery="toy", tool="lamp", name="Mina", helper="grandma"),
    StoryParams(setting="playroom", mystery="button", tool="magnifier", name="Tom", helper="grandpa"),
    StoryParams(setting="attic", mystery="key", tool="lamp", name="Perry", helper="aunt"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show solvable/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid()
        print(f"{len(combos)} compatible combos:\n")
        for row in combos:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    suspicious: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "teacher", "librarian"}
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
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    title: str
    clue: str
    answer: str
    trail: str
    reveal: str
    location: str
    suspense: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    helps: set[str]
    explain: str


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

    def copy(self) -> "World":
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


SETTINGS = {
    "library": Setting(place="the library", indoors=True, affords={"search"}),
    "kitchen": Setting(place="the kitchen", indoors=True, affords={"search"}),
    "garden": Setting(place="the garden", indoors=False, affords={"search"}),
}

MYSTERIES = {
    "missing-book": Mystery(
        id="missing-book",
        title="the missing book",
        clue="a torn bookmark",
        answer="the book was under the reading table",
        trail="followed the tiny paper trail",
        reveal="there it was, tucked under the table",
        location="under the reading table",
        suspense="something had been hiding in plain sight",
        tags={"book", "paper", "library"},
    ),
    "quiet-noise": Mystery(
        id="quiet-noise",
        title="the quiet noise",
        clue="a soft tapping sound",
        answer="the sound came from rain on the window",
        trail="watched the window for a clue",
        reveal="the window clicked again with another drip",
        location="the window",
        suspense="the room kept making the smallest sound",
        tags={"rain", "window", "sound"},
    ),
    "lost-key": Mystery(
        id="lost-key",
        title="the lost key",
        clue="a shiny mark on the floor",
        answer="the key had slid behind the rug",
        trail="searched the edges of the rug",
        reveal="a tiny glint blinked from the rug's edge",
        location="behind the rug",
        suspense="the clue looked important and a little spooky",
        tags={"key", "rug", "floor"},
    ),
}

TOOLS = {
    "dictionary": Tool(
        id="dictionary",
        label="dictionary",
        helps={"definition"},
        explain="A dictionary gives the meaning of a word.",
    ),
    "flashlight": Tool(
        id="flashlight",
        label="flashlight",
        helps={"search"},
        explain="A flashlight shines light into dark places.",
    ),
    "notebook": Tool(
        id="notebook",
        label="notebook",
        helps={"note"},
        explain="A notebook helps you keep clues in order.",
    ),
}

GIRL_NAMES = ["Mia", "Zoe", "Lily", "Ava", "Nora", "Ella", "Ruby", "Maya"]
BOY_NAMES = ["Leo", "Ben", "Finn", "Noah", "Theo", "Sam", "Eli", "Max"]
TRAITS = ["curious", "careful", "quiet", "brave", "thoughtful", "patient"]


@dataclass
class StoryParams:
    place: str
    mystery: str
    tool: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


ASP_RULES = r"""
setting(library). setting(kitchen). setting(garden).
indoors(library). indoors(kitchen).
affords(library,search). affords(kitchen,search). affords(garden,search).

mystery(missing_book). mystery(quiet_noise). mystery(lost_key).

tool(dictionary). tool(flashlight). tool(notebook).
helps(dictionary,definition).
helps(flashlight,search).
helps(notebook,note).

compatible(S,M,T) :- affords(S,search), mystery(M), tool(T), helps(T,definition), M = missing_book.
compatible(S,M,T) :- affords(S,search), mystery(M), tool(T), helps(T,search), M != missing_book.
compatible(S,M,T) :- affords(S,search), mystery(M), tool(T), helps(T,note), M != quiet_noise.
#show compatible/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for h in sorted(t.helps):
            lines.append(asp.fact("helps", tid, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for mid, mystery in MYSTERIES.items():
            for tid, tool in TOOLS.items():
                if "definition" in tool.helps and mid == "missing-book" and place in SETTINGS:
                    out.append((place, mid, tid))
                elif "search" in tool.helps and mid != "missing-book":
                    out.append((place, mid, tid))
                elif "note" in tool.helps and mid != "quiet-noise":
                    out.append((place, mid, tid))
    return sorted(set(out))


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    a, b = set(asp_valid_combos()), set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery story world with a definition twist.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
              if (args.place is None or c[0] == args.place)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.tool is None or c[2] == args.tool)]
    if args.mystery == "missing-book" and args.tool == "dictionary" and args.place is None:
        pass
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mystery, tool = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, mystery=mystery, tool=tool, name=name, gender=gender, parent=parent, trait=trait)


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    mystery = MYSTERIES[params.mystery]
    tool = TOOLS[params.tool]
    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    item = world.add(Entity(id="tool", type=tool.id, label=tool.label, phrase=tool.label, owner=hero.id))
    item.suspicious = True

    world.say(f"{hero.id} was a {params.trait} little {params.gender} who loved clues.")
    if tool.id == "dictionary":
        world.say(f"{hero.pronoun().capitalize()} opened a dictionary and found the definition of a word that felt important.")
    elif tool.id == "flashlight":
        world.say(f"{hero.pronoun().capitalize()} held a flashlight like a tiny brave star.")
    else:
        world.say(f"{hero.pronoun().capitalize()} kept a notebook ready for every clue.")

    world.say(f"One day, {hero.id} and {hero.pronoun('possessive')} {params.parent} went to {setting.place}.")
    world.say(f"There, they noticed {mystery.clue}. {mystery.suspense.capitalize()}")

    world.para()
    hero.memes["curiosity"] = 1
    if mystery.id == "missing-book":
        world.say(f"{hero.id} asked for the word's definition, and the dictionary gave a calm answer.")
        world.say(f"The clue led them to {mystery.trail}.")
        world.say(f"Then came the twist: {mystery.reveal}.")
    elif mystery.id == "quiet-noise":
        world.say(f"{hero.id} listened carefully and asked what the sound might mean.")
        world.say(f"The flashlight swept the room, but the answer was simpler than it seemed.")
        world.say(f"Twist: {mystery.reveal}.")
    else:
        world.say(f"{hero.id} took notes and followed the clue step by step.")
        world.say(f"The search moved around the room until the tiny shine turned up.")
        world.say(f"Twist: {mystery.reveal}.")

    world.para()
    hero.memes["relief"] = 1
    world.say(f"In the end, {mystery.answer}.")
    world.say(f"{hero.id} smiled because the mystery had a plain, true definition after all.")

    world.facts.update(hero=hero, parent=parent, mystery=mystery, tool=tool, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, mystery, tool = f["hero"], f["parent"], f["mystery"], f["tool"]
    return [
        f"Write a short mystery story for a child where {hero.id} uses a {tool.label} and learns the definition of a clue.",
        f"Tell a gentle story about {hero.id} and {hero.pronoun('possessive')} {parent.label} solving {mystery.title} with a surprising twist.",
        f"Write a story that includes a definition, a clue, and a twist ending at {f['setting'].place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, mystery, tool = f["hero"], f["parent"], f["mystery"], f["tool"]
    return [
        QAItem(
            question=f"Who is the mystery story about?",
            answer=f"It is about {hero.id}, a {hero.type} child who went to {f['setting'].place} with {hero.pronoun('possessive')} {parent.type}.",
        ),
        QAItem(
            question=f"What clue did {hero.id} notice at {f['setting'].place}?",
            answer=f"{hero.id} noticed {mystery.clue}, which made the mystery feel important.",
        ),
        QAItem(
            question=f"What tool helped {hero.id} think about the clue?",
            answer=f"A {tool.label} helped {hero.id}, because it fit the kind of mystery they were solving.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The twist was that {mystery.reveal}, so the mystery was simpler than it first looked.",
        ),
        QAItem(
            question=f"What was the answer to the mystery?",
            answer=f"The answer was that {mystery.answer}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    out = [
        QAItem(question="What is a definition?", answer="A definition tells what a word means."),
        QAItem(question="What does a mystery need?", answer="A mystery needs a clue, some wondering, and then an answer."),
    ]
    if f["tool"].id == "dictionary":
        out.append(QAItem(question="What does a dictionary do?", answer="A dictionary gives the meaning of a word."))
    if f["tool"].id == "flashlight":
        out.append(QAItem(question="What does a flashlight do?", answer="A flashlight shines light so you can look more carefully."))
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
        bits = []
        if e.suspicious:
            bits.append("suspicious=True")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


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


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        vals = asp_valid_stories()
        print(f"{len(vals)} compatible (place, mystery, tool) combos:\n")
        for p, m, t in vals:
            print(f"  {p:9} {m:13} {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(place="library", mystery="missing-book", tool="dictionary", name="Mia", gender="girl", parent="mother", trait="curious"),
            StoryParams(place="kitchen", mystery="lost-key", tool="flashlight", name="Leo", gender="boy", parent="father", trait="careful"),
            StoryParams(place="garden", mystery="quiet-noise", tool="notebook", name="Nora", gender="girl", parent="mother", trait="thoughtful"),
        ]
        samples = [generate(p) for p in curated]
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
            header = f"### {p.name}: {p.mystery} at {p.place} (tool: {p.tool})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

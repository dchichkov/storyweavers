#!/usr/bin/env python3
"""
A small story world: a detective-style playroom quest about a synonym clue.
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


@dataclass
class Clue:
    word: str
    synonym: str
    hint: str


@dataclass
class Item:
    id: str
    label: str
    owner: str = ""
    hidden_in: str = ""
    found: bool = False


@dataclass
class Character:
    id: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "girl":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type == "boy":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class World:
    place: str
    hero: Character
    partner: Character
    suspect: Character
    clue: Clue
    quest: str
    key_item: Item
    evidence: list[str] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
    name: str
    partner_name: str
    suspect_name: str
    clue_word: str
    synonym: str
    quest: str
    seed: Optional[int] = None


NAMES = ["Mina", "Jasper", "Toby", "Nina", "Pip", "Clara", "Theo", "Luna"]
QUESTS = [
    "find the missing key",
    "solve the case of the lost crayon",
    "track down the quiet toy train",
    "discover who hid the red badge",
]
CLUES = [
    Clue(word="quick", synonym="fast", hint="something that means the same thing"),
    Clue(word="small", synonym="tiny", hint="a word that says not very big"),
    Clue(word="happy", synonym="glad", hint="a word that feels cheerful"),
    Clue(word="smart", synonym="clever", hint="a word that means good at thinking"),
]
SUSPECTS = ["Maddie", "Owen", "Ivy", "Ben"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective-style synonym quest in a playroom.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--partner-name", choices=NAMES)
    ap.add_argument("--suspect-name", choices=SUSPECTS)
    ap.add_argument("--clue-word")
    ap.add_argument("--synonym")
    ap.add_argument("--quest", choices=QUESTS)
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
    clue = None
    if args.clue_word or args.synonym:
        for c in CLUES:
            if args.clue_word and c.word != args.clue_word:
                continue
            if args.synonym and c.synonym != args.synonym:
                continue
            clue = c
            break
        if clue is None:
            raise StoryError("No clue matches the requested word/synonym pair.")
    else:
        clue = rng.choice(CLUES)

    quest = args.quest or rng.choice(QUESTS)
    name = args.name or rng.choice(NAMES)
    partner = args.partner_name or rng.choice([n for n in NAMES if n != name])
    suspect = args.suspect_name or rng.choice(SUSPECTS)
    return StoryParams(
        name=name,
        partner_name=partner,
        suspect_name=suspect,
        clue_word=clue.word,
        synonym=clue.synonym,
        quest=quest,
    )


def _make_world(params: StoryParams) -> World:
    hero = Character(id=params.name, type="girl" if params.name in {"Mina", "Nina", "Clara", "Luna"} else "boy", label=params.name)
    partner = Character(id=params.partner_name, type="girl" if params.partner_name in {"Mina", "Nina", "Clara", "Luna"} else "boy", label=params.partner_name)
    suspect = Character(id=params.suspect_name, type="child", label=params.suspect_name)
    clue = next(c for c in CLUES if c.word == params.clue_word and c.synonym == params.synonym)
    key_item = Item(id="key_item", label="tiny brass key", hidden_in="the block shelf")
    world = World(place="the playroom", hero=hero, partner=partner, suspect=suspect, clue=clue, quest=params.quest, key_item=key_item)
    hero.meters["curiosity"] = 1
    partner.meters["curiosity"] = 1
    hero.memes["focus"] = 1
    partner.memes["focus"] = 1
    return world


def tell(world: World) -> None:
    h, p, s, clue = world.hero, world.partner, world.suspect, world.clue
    world.say(f"In the playroom, {h.id} and {p.id} were on a small detective quest: they wanted to {world.quest}.")
    world.say(f"On the puzzle board, they found a clue word: “{clue.word}.” {p.id} whispered that a synonym was “{clue.synonym}.”")
    world.say(f"{h.id} studied the toys, the bins, and the shelves. The hidden thing had to match the hint, not the loudest idea in the room.")
    world.para()
    world.say(f"Then {h.id} noticed a sticker on the block shelf. It was the right kind of tiny mark, and it pointed to {world.key_item.hidden_in}.")
    world.say(f"They asked {s.id}, who had been sorting toys nearby. {s.id} looked nervous, then said they had moved the {world.key_item.label} while cleaning up.")
    world.para()
    world.say(f"{h.id} smiled like a real detective. “{clue.synonym} means {clue.word},” {h.pronoun()} said, and the clue finally made sense.")
    world.key_item.found = True
    world.evidence.append("sticker on the block shelf")
    world.evidence.append("the synonym pair matched the clue")
    world.say(f"Together they found the {world.key_item.label}, and the playroom felt bright again. The case was solved, and the quest ended with a tidy shelf and happy faces.")

    world.facts["found"] = world.key_item.found
    world.facts["quest"] = world.quest
    world.facts["clue_word"] = clue.word
    world.facts["synonym"] = clue.synonym
    world.facts["evidence"] = list(world.evidence)


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a short detective story for children set in a playroom.",
        f"Tell a quest story where a child learns that “{world.clue.synonym}” is a synonym for “{world.clue.word}.”",
        f"Make a gentle mystery about how two kids solve a {world.quest} in the playroom.",
    ]


def story_qa(world: World) -> list[QAItem]:
    h, p, s, clue = world.hero, world.partner, world.suspect, world.clue
    return [
        QAItem(
            question=f"Where did {h.id} and {p.id} solve the mystery?",
            answer="They solved it in the playroom, among the toys, shelves, and bins.",
        ),
        QAItem(
            question=f"What synonym did {p.id} give for “{clue.word}”?",
            answer=f"{p.id} said that “{clue.synonym}” was a synonym for “{clue.word}.”",
        ),
        QAItem(
            question=f"What was the quest they were trying to finish?",
            answer=f"They were trying to {world.quest}.",
        ),
        QAItem(
            question=f"Why did {s.id} look nervous?",
            answer=f"{s.id} looked nervous because they had moved the {world.key_item.label} while cleaning up.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer="They found the missing item, solved the case, and left the playroom tidy and cheerful.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    clue = world.clue
    return [
        QAItem(
            question="What is a synonym?",
            answer="A synonym is a word that means the same or almost the same as another word.",
        ),
        QAItem(
            question="What is a detective?",
            answer="A detective is someone who looks for clues and solves mysteries.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a mission or search for something important.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = _make_world(params)
    tell(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.append(f"place={world.place}")
    lines.append(f"hero={world.hero.id} meters={dict(world.hero.meters)} memes={dict(world.hero.memes)}")
    lines.append(f"partner={world.partner.id} meters={dict(world.partner.meters)} memes={dict(world.partner.memes)}")
    lines.append(f"suspect={world.suspect.id}")
    lines.append(f"clue={world.clue.word}->{world.clue.synonym}")
    lines.append(f"evidence={world.evidence}")
    return "\n".join(lines)


ASP_RULES = r"""
place(playroom).
quest(find_missing_key).
quest(solve_lost_crayon).
quest(track_toy_train).
quest(discover_hidden_badge).
synonym(quick,fast).
synonym(small,tiny).
synonym(happy,glad).
synonym(smart,clever).

valid_quest(Q) :- quest(Q).
valid_synonym(W,S) :- synonym(W,S).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", "playroom")]
    for c in CLUES:
        lines.append(asp.fact("pair", c.word, c.synonym))
    for q in QUESTS:
        lines.append(asp.fact("quest_choice", q.replace(" ", "_")))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_quest/1.\n#show valid_synonym/2."))
    atoms = set(asp.atoms(model, "valid_quest")) | set(asp.atoms(model, "valid_synonym"))
    expected = set((q.replace(" ", "_"),) for q in QUESTS) | set((c.word, c.synonym) for c in CLUES)
    if atoms == expected:
        print(f"OK: ASP parity matches {len(expected)} facts.")
        return 0
    print("MISMATCH between ASP and Python registries.")
    print("ASP:", sorted(atoms))
    print("PY :", sorted(expected))
    return 1


CURATED = [
    StoryParams(name="Mina", partner_name="Theo", suspect_name="Maddie", clue_word="quick", synonym="fast", quest="find the missing key"),
    StoryParams(name="Jasper", partner_name="Luna", suspect_name="Owen", clue_word="small", synonym="tiny", quest="solve the case of the lost crayon"),
]


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
        print(asp_program("#show valid_quest/1.\n#show valid_synonym/2."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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

#!/usr/bin/env python3
"""
Territorial Moral Value Quest Whodunit
=====================================

A small classical storyworld about a child-sized mystery:
someone crosses a boundary, something goes missing, clues are gathered,
and the truth restores a fair border.

This world stays close to whodunit style while keeping the prose gentle
and child-facing. The moral value comes from the ending: respect territory,
ask first, and return what was borrowed.
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
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: str = ""
    place: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Territory:
    id: str
    label: str
    owner: str
    clue: str
    boundaries: list[str]


@dataclass
class Quest:
    id: str
    goal: str
    verb: str
    object_label: str
    object_phrase: str
    hidden_by: str
    reveal_clue: str


@dataclass
class Suspect:
    id: str
    label: str
    temperament: str
    boundary_style: str
    alibi: str
    clue_match: str = ""


@dataclass
class StoryParams:
    territory: str
    quest: str
    suspect: str
    name: str
    seed: Optional[int] = None


class World:
    def __init__(self, territory: Territory, quest: Quest) -> None:
        self.territory = territory
        self.quest = quest
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


TERRITORIES = {
    "garden": Territory("garden", "the garden fence", "Mrs. Green", "muddy paw prints", ["gate", "hedge"]),
    "library": Territory("library", "the quiet library corner", "Mr. Vale", "a bent bookmark", ["archway", "reading rug"]),
    "treehouse": Territory("treehouse", "the treehouse ladder", "Milo", "a splinter on the rung", ["ladder", "platform"]),
    "bakery": Territory("bakery", "the bakery counter", "Aunt Jun", "a dusting of flour", ["counter", "window"]),
}

QUESTS = {
    "key": Quest("key", "find the missing key", "find", "key", "a small brass key", "locked box", "a tiny brass shine"),
    "map": Quest("map", "find the missing map", "find", "map", "a folded paper map", "coat pocket", "a corner fold"),
    "ribbon": Quest("ribbon", "find the missing ribbon", "find", "ribbon", "a red ribbon", "basket handle", "a red thread"),
    "bell": Quest("bell", "find the missing bell", "find", "bell", "a silver bell", "shelf basket", "a little chime"),
}

SUSPECTS = {
    "cat": Suspect("cat", "a sleepy cat", "quiet", "curled up near edges", "was napping on the warm mat", "fur fluff"),
    "dog": Suspect("dog", "a bouncy dog", "playful", "crosses boundaries fast", "was chasing a ball in the yard", "mud"),
    "bird": Suspect("bird", "a clever bird", "curious", "peeks from high places", "was perched on the roof beam", "feather"),
    "rabbit": Suspect("rabbit", "a shy rabbit", "careful", "stays by soft paths", "was hiding in the clover patch", "leaf"),
}

NAMES = ["Nia", "Milo", "Tara", "Jude", "Pip", "Lena", "Owen", "Iris", "Kai", "June"]
MORAL_VALUES = ["respect", "fairness", "honesty"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for t in TERRITORIES:
        for q in QUESTS:
            for s in SUSPECTS:
                combos.append((t, q, s))
    return combos


def reasonableness_gate(params: StoryParams) -> None:
    if params.territory not in TERRITORIES:
        raise StoryError("Unknown territory.")
    if params.quest not in QUESTS:
        raise StoryError("Unknown quest.")
    if params.suspect not in SUSPECTS:
        raise StoryError("Unknown suspect.")


def build_world(params: StoryParams) -> World:
    territory = TERRITORIES[params.territory]
    quest = QUESTS[params.quest]
    world = World(territory, quest)

    hero = world.add(Entity(id=params.name, kind="character", label=params.name, tags={"detective"}))
    owner = world.add(Entity(id=territory.owner, kind="character", label=territory.owner, tags={"owner"}))
    culprit = world.add(Entity(
        id=params.suspect,
        kind="character",
        label=SUSPECTS[params.suspect].label,
        tags={"suspect"},
    ))
    item = world.add(Entity(
        id=quest.id,
        kind="thing",
        label=quest.object_label,
        phrase=quest.object_phrase,
        owner=territory.owner,
        place=territory.id,
        meters={"missing": 1.0},
        tags={"missing", params.quest},
    ))

    world.facts.update(hero=hero, owner=owner, culprit=culprit, item=item, territory=territory, quest=quest)
    return world


def tell_story(world: World) -> None:
    hero = world.facts["hero"]
    owner = world.facts["owner"]
    culprit = world.facts["culprit"]
    item = world.facts["item"]
    territory = world.facts["territory"]
    quest = world.facts["quest"]
    suspect = SUSPECTS[culprit.id]

    world.say(
        f"{hero.label} liked solving little mysteries, especially ones about what belonged where."
    )
    world.say(
        f"One morning, {hero.label} heard that {owner.label}'s {quest.object_label} was gone from {territory.label}."
    )
    world.say(
        f"{hero.label} started a careful quest to {quest.verb} the missing {quest.object_label} before the day got long."
    )

    world.para()
    world.say(
        f"At the edge of {territory.label}, {hero.label} found {territory.clue}."
    )
    world.say(
        f"That clue mattered, because {territory.owner} kept a neat boundary there, and only someone crossing in from outside could leave it."
    )
    world.say(
        f"{hero.label} looked at three suspects, but only {suspect.label} matched the clue they saw."
    )

    world.para()
    world.say(
        f"{suspect.label} had an alibi: {suspect.alibi}."
    )
    world.say(
        f"Even so, {hero.label} noticed {suspect.clue_match or quest.reveal_clue} on the path near {territory.label}."
    )
    world.say(
        f"The trail led to a {quest.hidden_by}, where the missing {quest.object_label} had been tucked away."
    )
    item.meters["found"] = 1.0
    item.place = territory.id
    item.meters["missing"] = 0.0

    world.para()
    world.say(
        f"{hero.label} asked one gentle question, and the truth came out at once."
    )
    world.say(
        f"{suspect.label} had moved the {quest.object_label} without asking, which was a territorial mistake, not a cruel one."
    )
    world.say(
        f"{hero.label} helped return it to {owner.label}, and everyone agreed that borders work best when people respect them."
    )
    world.say(
        f"By sunset, {territory.label} was calm again, and the little mystery ended with the {quest.object_label} exactly where it belonged."
    )


def generation_prompts(world: World) -> list[str]:
    territory = world.facts["territory"]
    quest = world.facts["quest"]
    return [
        f'Write a short whodunit story for a young child about a territorial mistake in {territory.label}.',
        f"Tell a gentle mystery where someone must {quest.verb} a missing {quest.object_label} and learn a moral lesson about boundaries.",
        f'Write a child-friendly whodunit that includes the word "territorial" and ends with a fair return.',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    owner = world.facts["owner"]
    culprit = world.facts["culprit"]
    territory = world.facts["territory"]
    quest = world.facts["quest"]
    return [
        QAItem(
            question=f"What did {hero.label} try to do in the mystery?",
            answer=f"{hero.label} tried to {quest.verb} the missing {quest.object_label} and solve the mystery.",
        ),
        QAItem(
            question=f"Why was the clue at {territory.label} important?",
            answer=(
                f"It was important because {territory.owner} had a clear boundary there, so the clue showed that someone crossed into the territory."
            ),
        ),
        QAItem(
            question=f"Who had moved the {quest.object_label}?",
            answer=f"{culprit.label} had moved it without asking, and then {hero.label} helped return it to {owner.label}.",
        ),
        QAItem(
            question="What moral did the story teach?",
            answer="It taught that people should respect territorial boundaries and ask before taking something.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does territorial mean?",
            answer="Territorial means protecting or caring about a space, boundary, or area that belongs to someone or something.",
        ),
        QAItem(
            question="What is a whodunit?",
            answer="A whodunit is a mystery story where the reader tries to figure out who caused the problem.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a mission or search to reach a goal, usually by following clues or solving problems.",
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is a good rule for how to treat other people, like being fair, honest, or respectful.",
        ),
    ]


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
    lines.append("== World knowledge Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for ent in world.entities.values():
        bits = []
        if ent.kind:
            bits.append(f"kind={ent.kind}")
        if ent.label:
            bits.append(f"label={ent.label}")
        if ent.place:
            bits.append(f"place={ent.place}")
        if ent.meters:
            bits.append(f"meters={ent.meters}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"{ent.id}: " + ", ".join(bits))
    return "\n".join(lines)


ASP_RULES = r"""
territory(T) :- territory_fact(T).
quest(Q) :- quest_fact(Q).
suspect(S) :- suspect_fact(S).

valid(T,Q,S) :- territory(T), quest(Q), suspect(S).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for t in TERRITORIES:
        lines.append(asp.fact("territory_fact", t))
    for q in QUESTS:
        lines.append(asp.fact("quest_fact", q))
    for s in SUSPECTS:
        lines.append(asp.fact("suspect_fact", s))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in ASP:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Territorial whodunit storyworld.")
    ap.add_argument("--territory", choices=TERRITORIES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--suspect", choices=SUSPECTS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.territory:
        combos = [c for c in combos if c[0] == args.territory]
    if args.quest:
        combos = [c for c in combos if c[1] == args.quest]
    if args.suspect:
        combos = [c for c in combos if c[2] == args.suspect]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    territory, quest, suspect = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    return StoryParams(territory=territory, quest=quest, suspect=suspect, name=name)


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = build_world(params)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} valid territory-quest-suspect combos:\n")
        for t, q, s in triples:
            print(f"  {t:10} {q:8} {s}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("garden", "key", "dog", "Nia"),
            StoryParams("library", "map", "bird", "Milo"),
            StoryParams("treehouse", "bell", "cat", "Tara"),
            StoryParams("bakery", "ribbon", "rabbit", "Jude"),
        ]
        samples = [generate(p) for p in curated]
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.territory}/{p.quest}/{p.suspect}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Standalone storyworld: cinema, Wang, quest, and moral value in a rhyming style.
A small simulated domain where a child-like hero, a cinema outing, and a quest
create a gentle moral choice and a resolved ending.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    goal: str
    trouble: str
    turn: str
    rhyme_a: str
    rhyme_b: str
    tags: set[str] = field(default_factory=set)


@dataclass
class MoralChoice:
    id: str
    value: str
    risk: str
    wise_move: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "cinema": Setting(place="the cinema", indoors=True, affords={"quest"}),
    "lobby": Setting(place="the cinema lobby", indoors=True, affords={"quest"}),
    "street": Setting(place="the street by the cinema", indoors=False, affords={"quest"}),
}

QUESTS = {
    "lost_ticket": Quest(
        id="lost_ticket",
        goal="find the lost ticket",
        trouble="the ticket slipped under a seat",
        turn="Wang asked kindly for help",
        rhyme_a="seat",
        rhyme_b="neat",
        tags={"cinema", "help"},
    ),
    "clean_screen": Quest(
        id="clean_screen",
        goal="wipe a sticky screen",
        trouble="popcorn dots made the screen look rough",
        turn="Wang chose to clean before the show",
        rhyme_a="gleam",
        rhyme_b="dream",
        tags={"cinema", "care"},
    ),
    "share_snack": Quest(
        id="share_snack",
        goal="share a snack with a friend",
        trouble="there was only one sweet bun",
        turn="Wang decided to split it fairly",
        rhyme_a="share",
        rhyme_b="care",
        tags={"kindness", "share"},
    ),
}

MORAL_VALUES = {
    "honesty": MoralChoice(
        id="honesty",
        value="honesty",
        risk="a small lie could make trouble grow",
        wise_move="tell the truth right away",
        ending="the truth made the room feel bright and calm",
        tags={"truth", "help"},
    ),
    "kindness": MoralChoice(
        id="kindness",
        value="kindness",
        risk="keeping the treat would leave a friend in pain",
        wise_move="share what there is",
        ending="sharing made both faces glow",
        tags={"share", "care"},
    ),
    "responsibility": MoralChoice(
        id="responsibility",
        value="responsibility",
        risk="mess left behind would bother the next guest",
        wise_move="clean up before play",
        ending="the neat room was ready for the next show",
        tags={"clean", "care"},
    ),
}

NAMES = ["Wang", "Mia", "Leo", "Nora", "Ava", "Ben"]
TRAITS = ["brave", "gentle", "bright", "cheerful", "careful"]


# ---------------------------------------------------------------------------
# Per-world params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    quest: str
    moral: str
    name: str = "Wang"
    gender: str = "boy"
    trait: str = "brave"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Helper logic
# ---------------------------------------------------------------------------

def quest_needs_moral(quest: Quest, moral: MoralChoice) -> bool:
    return bool(quest.tags & moral.tags)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, setting in SETTINGS.items():
        for qid, quest in QUESTS.items():
            if "cinema" not in quest.tags:
                continue
            for mid, moral in MORAL_VALUES.items():
                if quest_needs_moral(quest, moral) and place_id in {"cinema", "lobby"}:
                    combos.append((place_id, qid, mid))
    return combos


def explain_rejection(quest: Quest, moral: MoralChoice) -> str:
    return (
        f"(No story: the quest '{quest.id}' and the moral value '{moral.id}' do not fit "
        f"together in a cinematic way. Pick a cinema-linked quest with a matching moral choice.)"
    )


def setting_detail(setting: Setting) -> str:
    if setting.indoors:
        return "The lights were low, and the screen stood tall and white."
    return "The air was cool outside, with the cinema just ahead."


def rhyme_line(a: str, b: str) -> str:
    return f"{a} and {b}"


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

def tell(setting: Setting, quest: Quest, moral: MoralChoice, name: str, gender: str, trait: str) -> World:
    world = World(setting=setting)
    hero = world.add(Entity(id=name, kind="character", type=gender, traits=["little", trait]))
    friend = world.add(Entity(id="Friend", kind="character", type="friend", label="friend"))
    ticket = world.add(Entity(id="Ticket", type="thing", label="ticket", phrase="a small paper ticket"))
    snack = world.add(Entity(id="Snack", type="thing", label="bun", phrase="a sweet bun"))

    hero.memes["hope"] = 1
    hero.memes["care"] = 0
    world.facts.update(hero=hero, friend=friend, ticket=ticket, snack=snack, quest=quest, moral=moral)

    # Act 1
    world.say(
        f"{hero.id} went to {setting.place}, so neat and bright, "
        f"with a hopeful heart and a quest in sight."
    )
    world.say(
        f"{hero.id} was a little {trait} {gender} who loved a good show, "
        f"and every soft glow made that bright heart grow."
    )
    world.say(
        f"The goal was to {quest.goal}, but {quest.trouble}, oh dear; "
        f"still {hero.id} stayed steady and drew close with cheer."
    )

    # Act 2
    world.para()
    world.say(setting_detail(setting))
    world.say(
        f"Then came the choice: {moral.risk}. "
        f"{quest.turn}, and the moment felt ripe."
    )
    hero.memes["worry"] = 1
    world.say(
        f"{hero.id} thought, 'I can choose what is right and true, "
        f"for a kind little act can help me through.'"
    )

    # Act 3
    world.para()
    hero.memes["worry"] = 0
    hero.memes["care"] += 1
    hero.memes["joy"] = 1
    world.say(
        f"So {hero.id} chose to {moral.wise_move}, and that was the clue; "
        f"the hard little knot was untied right through."
    )
    if quest.id == "lost_ticket":
        world.say(
            f"{hero.id} looked by the {quest.rhyme_a}, then near the seat, "
            f"and found the lost ticket, tidy and neat."
        )
    elif quest.id == "clean_screen":
        world.say(
            f"{hero.id} wiped the screen till it shone like a {quest.rhyme_b}, "
            f"and the cinema sparkled in silvery gleam."
        )
    elif quest.id == "share_snack":
        world.say(
            f"{hero.id} split the bun so both could share, "
            f"and the sweet little snack felt more than fair."
        )

    world.say(
        f"{moral.ending}. {hero.id} smiled at {friend.label or 'the friend'}, "
        f"and the night felt warm, with a gentle end."
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    quest = f["quest"]
    moral = f["moral"]
    return [
        f'Write a rhyming story for young children about {hero.id} at the cinema.',
        f"Tell a gentle quest story where {hero.id} must {quest.goal} and choose {moral.value}.",
        f'Write a short moral tale with cinema lights, a quest, and a happy ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    quest = f["quest"]
    moral = f["moral"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a small {hero.type} with a brave heart at the cinema.",
        ),
        QAItem(
            question=f"What was {hero.id}'s quest?",
            answer=f"{hero.id}'s quest was to {quest.goal}, even though {quest.trouble}.",
        ),
        QAItem(
            question=f"What moral value did {hero.id} choose?",
            answer=f"{hero.id} chose {moral.value}, which helped the story end well.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with a good choice, a solved quest, and a calm, happy cinema.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cinema?",
            answer="A cinema is a place where people go to watch movies on a big screen.",
        ),
        QAItem(
            question="What does it mean to be honest?",
            answer="Being honest means telling the truth and not pretending something untrue.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means caring about other people and helping or sharing with them.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for p in sample.prompts:
        lines.append(p)
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
quest_moral_fit(Q,M) :- quest(Q), moral(M), shared_tag(Q,M).
valid(Place,Q,M) :- setting(Place), quest(Q), moral(M), allowed_place(Place,Q), quest_moral_fit(Q,M).
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
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        for t in sorted(q.tags):
            lines.append(asp.fact("shared_tag", qid, t))
        lines.append(asp.fact("allowed_place", "cinema", qid))
        lines.append(asp.fact("allowed_place", "lobby", qid))
    for mid, m in MORAL_VALUES.items():
        lines.append(asp.fact("moral", mid))
        for t in sorted(m.tags):
            lines.append(asp.fact("shared_tag", mid, t))
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
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="cinema", quest="lost_ticket", moral="honesty", name="Wang", gender="boy", trait="brave"),
    StoryParams(place="lobby", quest="clean_screen", moral="responsibility", name="Wang", gender="boy", trait="careful"),
    StoryParams(place="cinema", quest="share_snack", moral="kindness", name="Wang", gender="boy", trait="gentle"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming storyworld: cinema, Wang, quest, and moral value.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--moral", choices=MORAL_VALUES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["boy", "girl"])
    ap.add_argument("--trait", choices=TRAITS)
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
    filtered = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.quest is None or c[1] == args.quest)
        and (args.moral is None or c[2] == args.moral)
    ]
    if not filtered:
        if args.quest and args.moral:
            raise StoryError(explain_rejection(QUESTS[args.quest], MORAL_VALUES[args.moral]))
        raise StoryError("(No valid combination matches the given options.)")
    place, quest, moral = rng.choice(filtered)
    name = args.name or "Wang"
    gender = args.gender or "boy"
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, quest=quest, moral=moral, name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], QUESTS[params.quest], MORAL_VALUES[params.moral],
                 params.name, params.gender, params.trait)
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
        print("--- trace ---")
        for e in sample.world.entities.values():
            print(e.id, e.kind, e.type, e.meters, e.memes)
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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, quest, moral) combos:")
        for c in combos:
            print(" ", c)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

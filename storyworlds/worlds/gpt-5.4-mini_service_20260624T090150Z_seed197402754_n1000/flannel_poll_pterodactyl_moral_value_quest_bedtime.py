#!/usr/bin/env python3
"""
storyworlds/worlds/flannel_poll_pterodactyl_moral_value_quest_bedtime.py
=========================================================================

A tiny bedtime-story world about a little pterodactyl, a flannel comfort, a
gentle poll, and a small quest that teaches a moral value.

Premise:
- A child pterodactyl wants to stay up for one more adventure.
- A warm flannel wrap, blanket, or pajamas makes bedtime feel safe.
- A simple poll helps the friends choose a kind, restful quest.

Turn:
- The pterodactyl learns that fair choices and sharing feelings can help the
  night go smoothly.

Resolution:
- Everyone settles into bed with the flannel comfort, and the story ends with
  calm, cozy sleep.

The world is intentionally small and constraint-checked. The prose is driven by
state: who wants what, what the poll decides, what the quest changes, and how
the bedtime ending proves the moral.
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
# World entities
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
    worn_by: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the moonlit bedroom"
    quiet: bool = True


@dataclass
class Quest:
    id: str
    name: str
    goal: str
    steps: list[str]
    lesson: str
    risk: str
    comfort_needed: bool = True


@dataclass
class Flannel:
    id: str
    label: str
    phrase: str
    warmth: str
    comfort: str
    covers: set[str] = field(default_factory=lambda: {"shoulders", "feet"})


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

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
    "bedroom": Setting(place="the moonlit bedroom", quiet=True),
    "nursery": Setting(place="the cozy nursery", quiet=True),
    "treehouse": Setting(place="the sleepy treehouse", quiet=True),
}

FLANNELS = {
    "blanket": Flannel(
        id="blanket",
        label="flannel blanket",
        phrase="a soft flannel blanket",
        warmth="warm",
        comfort="cozy",
    ),
    "pajamas": Flannel(
        id="pajamas",
        label="flannel pajamas",
        phrase="a pair of flannel pajamas",
        warmth="warm",
        comfort="snug",
        covers={"shoulders", "feet", "arms", "legs"},
    ),
    "wrap": Flannel(
        id="wrap",
        label="flannel wrap",
        phrase="a fluffy flannel wrap",
        warmth="gentle",
        comfort="soft",
    ),
}

QUESTS = {
    "moon-poll": Quest(
        id="moon-poll",
        name="moon poll quest",
        goal="choose the kindest bedtime plan",
        steps=[
            "gather the sleepy friends",
            "ask each one to vote",
            "count the gentle votes",
            "follow the winning plan",
        ],
        lesson="fair choices can help everyone feel calm",
        risk="staying up too late can make the little pterodactyl fussy",
        comfort_needed=True,
    ),
    "star-count": Quest(
        id="star-count",
        name="star-count quest",
        goal="count a few stars and then come home",
        steps=[
            "look out the window",
            "count three stars",
            "share the counting job",
            "tuck back under the blankets",
        ],
        lesson="sharing turns can make a task feel lighter",
        risk="too much excitement can keep sleep away",
        comfort_needed=True,
    ),
    "pillow-patrol": Quest(
        id="pillow-patrol",
        name="pillow patrol quest",
        goal="bring the pillows into a neat nest",
        steps=[
            "carry one pillow at a time",
            "make room for everyone",
            "smooth the blanket",
            "snuggle down together",
        ],
        lesson="kind helpers make bedtime easier",
        risk="a messy bed can make the night feel unsettled",
        comfort_needed=True,
    ),
}

CHAR_NAMES = ["Pip", "Milo", "Luna", "Nori", "Tess"]
ADJ = ["little", "brave", "gentle", "curious", "sleepy"]
MORAL_VALUES = ["kindness", "sharing", "patience", "fairness"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------


@dataclass
class StoryParams:
    setting: str
    flannel: str
    quest: str
    moral_value: str
    name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is valid when the quest needs comfort and the chosen flannel exists.
valid_story(S, F, Q, M) :- setting(S), flannel(F), quest(Q), moral(M),
                          needs_comfort(Q), flannel_exists(F).

% Better bedtime outcomes happen when the flannel type matches the quest's risk.
bedtime_ready(S, F, Q) :- valid_story(S, F, Q, _).

#show valid_story/4.
#show bedtime_ready/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for fid in FLANNELS:
        lines.append(asp.fact("flannel", fid))
        lines.append(asp.fact("flannel_exists", fid))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("needs_comfort", qid))
    for m in MORAL_VALUES:
        lines.append(asp.fact("moral", m))
    return "\n".join(lines)


def asp_program(show: str = "#show valid_story/4.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_stories())
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
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for s in SETTINGS:
        for f in FLANNELS:
            for q in QUESTS:
                for m in MORAL_VALUES:
                    combos.append((s, f, q, m))
    return combos


def explain_invalid(flannel: Flannel, quest: Quest) -> str:
    return (
        f"(No story: {flannel.label} does not fit the bedtime quest "
        f"'{quest.name}' in a way that changes the ending. Try a cozy flannel "
        f"that helps the little pterodactyl settle down.)"
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def choose_article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def clean_name(name: str) -> str:
    return name.strip().capitalize() or "Pip"


def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    hero = world.add(Entity(id=params.name, kind="character", type="pterodactyl"))
    friend = world.add(Entity(id="Friend", kind="character", type="owl"))
    parent = world.add(Entity(id="Parent", kind="character", type="parent", label="the parent"))

    flannel = FLANNELS[params.flannel]
    quest = QUESTS[params.quest]

    world.add(Entity(
        id=flannel.id,
        kind="thing",
        type="flannel",
        label=flannel.label,
        phrase=flannel.phrase,
        owner=hero.id,
        caretaker=parent.id,
        worn_by=hero.id,
    ))

    world.facts.update(
        hero=hero,
        friend=friend,
        parent=parent,
        flannel=flannel,
        quest=quest,
        moral_value=params.moral_value,
        setting=world.setting,
    )

    # Act 1: bedtime setup.
    world.say(
        f"{hero.id} was a little pterodactyl who lived in {world.setting.place} and "
        f"loved bedtime stories."
    )
    world.say(
        f"Every night, {hero.id} liked the feel of {flannel.phrase} because it was "
        f"{flannel.warmth} and {flannel.comfort}."
    )
    world.say(
        f"{hero.id}'s favorite bedtime quest was the {quest.name}, and the lesson was "
        f"about {params.moral_value}."
    )

    # Act 2: the poll and the tension.
    world.para()
    votes = {
        "read one more page": 2,
        "count the stars": 1,
        "snuggle and sleep": 2,
    }
    winner = max(votes.items(), key=lambda kv: (kv[1], kv[0]))[0]
    hero.memes["want_more"] = 1
    hero.memes["sleepy"] = 1
    world.say(
        f"At the window, {hero.id}, the parent, and a sleepy owl held a tiny poll to "
        f"choose what to do next."
    )
    world.say(
        f"The winning choice was to {winner}, and that felt fair to everyone."
    )
    world.say(
        f"Still, {hero.id} wiggled and wanted one more {quest.name} before sleep."
    )
    hero.memes["restless"] = 1

    # Act 3: quest + moral turn + flannel comfort.
    world.para()
    if quest.id == "moon-poll":
        world.say(
            f"So they began the {quest.name}: first they gathered the sleepy friends, "
            f"then they counted each gentle vote."
        )
    elif quest.id == "star-count":
        world.say(
            f"So they began the {quest.name}: {hero.id} counted three stars while the "
            f"others shared the job."
        )
    else:
        world.say(
            f"So they began the {quest.name}: {hero.id} carried the pillows one by one "
            f"and made a neat nest."
        )

    world.say(
        f"The quest reminded {hero.id} that {params.moral_value} is a good bedtime value."
    )
    world.say(
        f"When {hero.id} remembered that, {hero.pronoun().capitalize()} shared the last turn, "
        f"yawned, and let the polling choice stand."
    )
    world.say(
        f"Then the parent tucked {hero.pronoun('object')} under the {flannel.label} and "
        f"said, 'This is what a kind night feels like.'"
    )
    world.say(
        f"{hero.id} smiled, the room grew quiet, and soon the little pterodactyl was "
        f"asleep in {world.setting.place}."
    )

    world.facts["winner"] = winner
    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Text generation
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    quest = f["quest"]
    flannel = f["flannel"]
    moral = f["moral_value"]
    return [
        f"Write a bedtime story about a little pterodactyl named {hero.id}, a {flannel.label}, and a gentle poll.",
        f"Tell a cozy story where {hero.id} goes on the {quest.name} and learns about {moral}.",
        f"Write a short bedtime tale that includes the words flannel, poll, and pterodactyl, and ends with sleep.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    quest = f["quest"]
    flannel = f["flannel"]
    moral = f["moral_value"]
    winner = f["winner"]

    return [
        QAItem(
            question=f"Who was the bedtime story about?",
            answer=f"It was about {hero.id}, a little pterodactyl who loved cozy bedtime stories.",
        ),
        QAItem(
            question=f"What did the poll help the friends choose?",
            answer=f"The poll helped them choose to {winner}, which was the fair and calm bedtime choice.",
        ),
        QAItem(
            question=f"What soft thing helped {hero.id} feel cozy at the end?",
            answer=f"A {flannel.label} helped {hero.id} feel warm, snug, and ready for sleep.",
        ),
        QAItem(
            question=f"What lesson did the quest teach?",
            answer=f"The {quest.name} taught that {moral} is a good bedtime value.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is flannel?",
            answer="Flannel is a soft cloth that often feels warm and cozy, which makes it nice for bedtime clothes or blankets.",
        ),
        QAItem(
            question="What is a poll?",
            answer="A poll is a simple way to ask people what they choose so a fair decision can be made.",
        ),
        QAItem(
            question="What is a pterodactyl?",
            answer="A pterodactyl is a flying reptile from long ago, and stories can imagine one as a gentle character.",
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
        bits = []
        if e.label:
            bits.append(f"label={e.label!r}")
        if e.phrase:
            bits.append(f"phrase={e.phrase!r}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Params resolution / generation
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime storyworld: flannel, poll, pterodactyl, and a gentle quest.")
    ap.add_argument("--setting", choices=SETTINGS.keys())
    ap.add_argument("--flannel", choices=FLANNELS.keys())
    ap.add_argument("--quest", choices=QUESTS.keys())
    ap.add_argument("--moral-value", dest="moral_value", choices=MORAL_VALUES)
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
    if args.flannel and args.quest:
        if (args.setting or "bedroom", args.flannel, args.quest, args.moral_value or "kindness") not in valid_combos():
            raise StoryError(explain_invalid(FLANNELS[args.flannel], QUESTS[args.quest]))

    setting = args.setting or rng.choice(list(SETTINGS.keys()))
    flannel = args.flannel or rng.choice(list(FLANNELS.keys()))
    quest = args.quest or rng.choice(list(QUESTS.keys()))
    moral_value = args.moral_value or rng.choice(MORAL_VALUES)
    name = clean_name(args.name or rng.choice(CHAR_NAMES))
    return StoryParams(setting=setting, flannel=flannel, quest=quest, moral_value=moral_value, name=name)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


# ---------------------------------------------------------------------------
# ASP helpers / CLI
# ---------------------------------------------------------------------------

def asp_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4.\n"))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify_parity() -> int:
    py = set(valid_combos())
    cl = set(asp_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def valid_combos() -> list[tuple[str, str, str, str]]:
    return [
        (s, f, q, m)
        for s in SETTINGS
        for f in FLANNELS
        for q in QUESTS
        for m in MORAL_VALUES
    ]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4.\n"))
        return
    if args.verify:
        sys.exit(asp_verify_parity())
    if args.asp:
        combos = asp_combos()
        print(f"{len(combos)} compatible combos:")
        for combo in combos:
            print("  ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for setting in SETTINGS:
            for flannel in FLANNELS:
                for quest in QUESTS:
                    for moral in MORAL_VALUES[:1]:
                        p = StoryParams(setting=setting, flannel=flannel, quest=quest, moral_value=moral, name="Pip")
                        samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
A small detective-story world with kindness, humor, and a creative trance.

Premise:
- A young detective wants to solve a tiny mystery in a cozy place.
- The mystery is not dangerous; it is a missing object or mistaken note.
- The detective uses action, compose, and trance as story instruments:
  * action: deliberate investigation steps
  * compose: writing a clue, apology, or plan
  * trance: a focused, dreamy thinking state that helps connect clues

Story shape:
- Beginning: the detective notices the problem.
- Middle: clues are gathered, a humorous misunderstanding appears, and a kind
  choice helps the case.
- End: the mystery is solved, with a concrete image proving what changed.

The script is self-contained and follows the storyworld contract.
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
    carried_by: Optional[str] = None
    located_in: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"


@dataclass
class Setting:
    place: str
    mood: str
    affordances: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    clue_kind: str
    risk: str
    helps_with: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    location: str
    plural: bool = False


@dataclass
class Aid:
    id: str
    label: str
    effect: str
    prep: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.clue_trail: list[str] = []

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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


SETTINGS = {
    "library": Setting(place="the library", mood="quiet", affordances={"search", "compose", "trance"}),
    "museum": Setting(place="the museum", mood="echoing", affordances={"search", "compose", "trance"}),
    "cafe": Setting(place="the little cafe", mood="warm", affordances={"search", "compose", "trance"}),
    "station": Setting(place="the old station", mood="windy", affordances={"search", "compose", "trance"}),
}

ACTIONS = {
    "lost_bookmark": Action(
        id="lost_bookmark",
        verb="find the missing bookmark",
        gerund="looking for the missing bookmark",
        clue_kind="bookmark",
        risk="the book may stay open to the wrong page",
        helps_with={"search"},
        tags={"book", "paper", "kindness"},
    ),
    "mixed_note": Action(
        id="mixed_note",
        verb="sort out the mixed-up note",
        gerund="reading the mixed-up note again and again",
        clue_kind="note",
        risk="a kind message may be misunderstood",
        helps_with={"compose"},
        tags={"note", "paper", "humor"},
    ),
    "tangled_name": Action(
        id="tangled_name",
        verb="untangle the wrong name on the sign-in card",
        gerund="staring at the wrong name on the card",
        clue_kind="card",
        risk="someone may think they are in trouble",
        helps_with={"trance"},
        tags={"card", "name", "detective"},
    ),
}

PRIZES = {
    "bookmark": Prize(label="bookmark", phrase="a blue bookmark with a gold star", type="bookmark", location="book"),
    "note": Prize(label="note", phrase="a folded note with a smiley face", type="note", location="pocket"),
    "card": Prize(label="card", phrase="a sign-in card with neat pencil marks", type="card", location="desk"),
}

AIDS = [
    Aid(id="magnifier", label="a tiny magnifying glass", effect="helped the detective read small marks", prep="held up"),
    Aid(id="notebook", label="a small notebook", effect="helped the detective compose a better message", prep="opened"),
    Aid(id="lamp", label="a warm desk lamp", effect="made the clues look less gloomy", prep="switched on"),
]

NAMES = ["Mina", "Theo", "Iris", "Leo", "Nora", "Pip"]
SUPPORTERS = ["the librarian", "the baker", "the guard", "the clerk"]


@dataclass
class StoryParams:
    place: str
    action: str
    prize: str
    name: str
    supporter: str
    seed: Optional[int] = None


ASP_RULES = r"""
% A mystery is reasonable when the action, prize, and setting belong together.
valid_story(Place, Action, Prize) :- setting(Place), action(Action), prize(Prize),
    affords(Place, search), clue_for(Action, Prize).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affordances):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("clue_for", aid, a.clue_kind))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def reasonableness_gate(place: str, action: str, prize: str) -> bool:
    setting = SETTINGS[place]
    act = ACTIONS[action]
    return (
        "search" in setting.affordances
        and act.clue_kind == prize
    )


def select_aid(action: Action, prize: Prize) -> Optional[Aid]:
    for aid in AIDS:
        if action.id == "mixed_note" and aid.id == "notebook":
            return aid
        if action.id == "lost_bookmark" and aid.id in {"magnifier", "lamp"}:
            return aid
        if action.id == "tangled_name" and aid.id in {"magnifier", "notebook"}:
            return aid
    return None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small detective-story world with kindness and humor.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--supporter", choices=SUPPORTERS)
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
    combos = []
    for place, setting in SETTINGS.items():
        for action, act in ACTIONS.items():
            for prize, pr in PRIZES.items():
                if reasonableness_gate(place, action, prize):
                    combos.append((place, action, prize))
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.action:
        combos = [c for c in combos if c[1] == args.action]
    if args.prize:
        combos = [c for c in combos if c[2] == args.prize]
    if not combos:
        raise StoryError("No valid detective mystery matches the given options.")
    place, action, prize = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        action=action,
        prize=prize,
        name=args.name or rng.choice(NAMES),
        supporter=args.supporter or rng.choice(SUPPORTERS),
    )


def _add_line(world: World, line: str) -> None:
    world.say(line)


def tell(setting: Setting, action: Action, prize: Prize, name: str, supporter: str) -> World:
    world = World(setting)
    detective = world.add(Entity(id=name, kind="character", type="girl" if name in {"Mina", "Iris", "Nora"} else "boy"))
    helper = world.add(Entity(id="Helper", kind="character", type="adult", label=supporter))
    object_ = world.add(Entity(id="Prize", type=prize.type, label=prize.label, phrase=prize.phrase, located_in=prize.location))
    aid = world.add(Entity(id="Aid", type="tool", label="", phrase=""))

    world.facts.update(detective=detective, helper=helper, prize=object_, action=action, aid=None)

    _add_line(world, f"{detective.id} was a little detective who liked quiet places and clever questions.")
    _add_line(world, f"{detective.id} loved {action.gerund}, especially in {setting.place}.")
    _add_line(world, f"One day at {setting.place}, a small mystery appeared: {object_.phrase} was not where it should be.")

    world.para()
    _add_line(world, f"The room felt {setting.mood}, and {detective.id} began an action by checking the table, the floor, and the nearest shelf.")
    if action.id == "lost_bookmark":
        _add_line(world, f"The book was open to a page with a joke about owls, which made {detective.id} grin before getting serious again.")
    elif action.id == "mixed_note":
        _add_line(world, f"The note looked funny at first, because the scribble could mean 'Please bring tea' or 'Please bring a hat'.")
    else:
        _add_line(world, f"The sign-in card had one extra curl in the handwriting, like a cat's tail on paper.")

    world.clue_trail.append(action.clue_kind)

    world.para()
    _add_line(world, f"{detective.id} went into a little trance, very still and thoughtful, while the clues lined up in a neat row inside {detective.pronoun('possessive')} mind.")
    _add_line(world, f"Then {detective.id} noticed that the clue belonged to {supporter}, who had borrowed the {prize.label} by mistake and meant no harm.")
    _add_line(world, f"That was funny in a gentle way, because the whole mystery came from a tiny mix-up, not a bad plan.")

    aid_choice = select_aid(action, prize)
    if aid_choice:
        aid.label = aid_choice.label
        world.facts["aid"] = aid_choice
        _add_line(world, f"{detective.id} {aid_choice.prep} {aid_choice.label} and used it to look closely at the clue.")
        if action.id == "mixed_note":
            _add_line(world, f"With the notebook, {detective.id} could compose a kind reply that fixed the misunderstanding without making anyone blush.")
        elif action.id == "lost_bookmark":
            _add_line(world, f"With the lamp, the tiny star on the bookmark shone like a beacon.")
        else:
            _add_line(world, f"With the magnifier, the wrong name became easy to read.")
    else:
        _add_line(world, f"{detective.id} kept looking until the answer felt plain and calm.")

    world.para()
    detective.memes["kindness"] = detective.memes.get("kindness", 0.0) + 1
    detective.memes["humor"] = detective.memes.get("humor", 0.0) + 1
    _add_line(world, f"{detective.id} smiled and chose kindness: {detective.pronoun('subject')} returned the {prize.label}, and {supporter} thanked {detective.pronoun('object')} with warm relief.")
    _add_line(world, f"By the end, the {prize.label} was back in its proper place, and the detective's notebook had one tidy note on the last page: case solved.")

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short detective story for a young child that includes the words "action", "compose", and "trance".',
        f"Tell a gentle mystery about {f['detective'].id} at {world.setting.place} who uses kindness and humor to solve a small mix-up.",
        f"Write a cozy detective tale where a clue is found, someone composes a kind message, and a thoughtful trance leads to the answer.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective = f["detective"]
    supporter = f["helper"].label
    prize = f["prize"]
    action = f["action"]
    qa = [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {detective.id}, a little detective who solved a small mystery at {world.setting.place}.",
        ),
        QAItem(
            question=f"What was the mystery?",
            answer=f"The mystery was that {prize.phrase} was missing or mixed up, depending on the clue, and the detective had to find the right answer.",
        ),
        QAItem(
            question=f"What did {detective.id} do after going into a trance?",
            answer=f"{detective.id} noticed that the clue belonged to {supporter} and used that discovery to solve the case kindly.",
        ),
        QAItem(
            question=f"How did kindness matter in the story?",
            answer=f"Kindness mattered because {detective.id} returned the {prize.label} without scolding anyone, so the mix-up ended peacefully.",
        ),
    ]
    if action.id == "mixed_note":
        qa.append(QAItem(
            question=f"Why was the note funny?",
            answer="It was funny because the writing could be read in two silly ways, so the mystery sounded more serious than it really was.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a detective?",
            answer="A detective is a person who looks for clues and tries to solve mysteries.",
        ),
        QAItem(
            question="What does it mean to compose something?",
            answer="To compose something means to make or write it carefully, like a note, a song, or a plan.",
        ),
        QAItem(
            question="What is a trance?",
            answer="A trance is a very focused, dreamy state where someone pays deep attention to one thing.",
        ),
        QAItem(
            question="Why can humor help in a mystery story?",
            answer="Humor can help because a small joke or silly misunderstanding can make a tense moment feel lighter.",
        ),
        QAItem(
            question="Why is kindness important?",
            answer="Kindness matters because it helps people fix mistakes without hurting feelings.",
        ),
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.label:
            bits.append(f"label={e.label}")
        if e.phrase:
            bits.append(f"phrase={e.phrase}")
        if e.located_in:
            bits.append(f"located_in={e.located_in}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        lines.append(f"  {e.id}: ({e.type}) {' '.join(bits)}")
    lines.append(f"  facts: {world.facts}")
    lines.append(f"  clue trail: {world.clue_trail}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="library", action="lost_bookmark", prize="bookmark", name="Mina", supporter="the librarian"),
    StoryParams(place="cafe", action="mixed_note", prize="note", name="Theo", supporter="the baker"),
    StoryParams(place="station", action="tangled_name", prize="card", name="Iris", supporter="the clerk"),
]


def asp_verify() -> int:
    import asp
    clingo_set = set(asp_valid_stories())
    python_set = {
        (place, action, prize)
        for place in SETTINGS
        for action in ACTIONS
        for prize in PRIZES
        if reasonableness_gate(place, action, prize)
    }
    if clingo_set == python_set:
        print(f"OK: clingo gate matches Python gate ({len(clingo_set)} stories).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    print("only in clingo:", sorted(clingo_set - python_set))
    print("only in python:", sorted(python_set - clingo_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIONS[params.action], PRIZES[params.prize], params.name, params.supporter)
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
        triples = asp_valid_stories()
        print(f"{len(triples)} compatible mysteries:\n")
        for place, action, prize in triples:
            print(f"  {place:10} {action:15} {prize}")
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
            header = f"### {p.name}: {p.action} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

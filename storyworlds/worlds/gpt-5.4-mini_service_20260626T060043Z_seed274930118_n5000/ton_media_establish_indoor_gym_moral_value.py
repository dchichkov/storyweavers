#!/usr/bin/env python3
"""
A small detective-story world set in an indoor gym.

Premise:
- A child detective in an indoor gym notices a suspicious situation.
- Clues point through a quest for a lost item.
- The turn is a moral choice: report honestly, even if blame feels scary.
- The ending proves the moral value by showing the truth established.

Seed words woven into the world:
- ton
- media
- establish
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
    owner: Optional[str] = None
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self) -> str:
        if self.kind == "character":
            return "they"
        return "it"


@dataclass
class Location:
    name: str = "the indoor gym"
    indoors: bool = True
    affords: set[str] = field(default_factory=lambda: {"quest", "mystery", "practice"})


@dataclass
class Case:
    clue: str
    quest: str
    suspect: str
    moral_value: str
    media_item: str
    establish_phrase: str


@dataclass
class StoryParams:
    name: str
    helper: str
    clue: str
    suspect: str
    seed: Optional[int] = None


class World:
    def __init__(self, location: Location) -> None:
        self.location = location
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy

        clone = World(self.location)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        return clone


CASES = [
    Case(
        clue="a chalky footprint",
        quest="follow the clue to the lost whistle",
        suspect="the mop cart",
        moral_value="honesty matters more than looking clever",
        media_item="the media team camera",
        establish_phrase="establish the truth",
    ),
    Case(
        clue="a bent jump rope",
        quest="trace who moved the practice cone",
        suspect="the storage shelf",
        moral_value="fairness matters even in a hurry",
        media_item="the media recorder",
        establish_phrase="establish what really happened",
    ),
    Case(
        clue="a shiny badge",
        quest="find where the coach's note went",
        suspect="the bench by the wall",
        moral_value="telling the truth is brave",
        media_item="the media notebook",
        establish_phrase="establish the honest answer",
    ),
]

NAMES = ["Mia", "Leo", "Nora", "Eli", "Ava", "Finn", "Zoe", "Ben"]
HELPERS = ["coach", "friend", "camera kid", "scorekeeper"]
SUSPECTS = ["the mop cart", "the storage shelf", "the bench by the wall", "the water station"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for case in CASES:
        combos.append((Location().name, case.clue, case.suspect))
    return combos


ASP_RULES = r"""
% The gym is valid only when the case clue can support a quest and a moral turn.
valid_story(L, C, S) :- indoor_gym(L), clue(C), suspect(S), quest(C), moral(C).
"""


def asp_facts() -> str:
    import asp

    lines = [asp.fact("indoor_gym", "the indoor gym")]
    for case in CASES:
        lines.append(asp.fact("clue", case.clue))
        lines.append(asp.fact("quest", case.clue))
        lines.append(asp.fact("suspect", case.suspect))
        lines.append(asp.fact("moral", case.moral_value))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set((a[0], a[1], a[2]) for a in asp_valid_stories())
    if python_set == asp_set:
        print(f"OK: ASP matches Python gate ({len(python_set)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    print(" only in Python:", sorted(python_set - asp_set))
    print(" only in ASP:", sorted(asp_set - python_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Indoor-gym detective story world.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--clue", choices=[c.clue for c in CASES])
    ap.add_argument("--suspect", choices=SUSPECTS)
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
    clue = args.clue or rng.choice([c.clue for c in CASES])
    case = next(c for c in CASES if c.clue == clue)
    suspect = args.suspect or case.suspect
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(name=name, helper=helper, clue=clue, suspect=suspect)


def build_world(params: StoryParams) -> World:
    location = Location()
    world = World(location)
    case = next(c for c in CASES if c.clue == params.clue)

    detective = world.add(Entity(id=params.name, kind="character", label=params.name, role="detective"))
    helper = world.add(Entity(id=params.helper, kind="character", label=params.helper, role="helper"))
    media = world.add(Entity(id="media", kind="thing", label=case.media_item, phrase=case.media_item))
    ton = world.add(Entity(id="ton", kind="thing", label="a ton plate", phrase="a one-ton gym plate"))
    clue = world.add(Entity(id="clue", kind="thing", label=case.clue, phrase=case.clue))
    suspect = world.add(Entity(id="suspect", kind="thing", label=case.suspect, phrase=case.suspect))

    detective.memes["curiosity"] = 1
    detective.memes["doubt"] = 1
    world.facts.update(
        detective=detective,
        helper=helper,
        clue_entity=clue,
        suspect_entity=suspect,
        media=media,
        ton=ton,
        case=case,
    )

    world.say(f"{detective.label} was a small detective in the indoor gym, where every squeak sounded like a clue.")
    world.say(f"One afternoon, {detective.label} noticed {case.clue} near {case.suspect} and decided to follow the trail.")
    world.say(f"{helper.label} from the media club held up {case.media_item}, hoping to record the case carefully.")
    world.para()
    world.say(f"The quest was to {case.quest}, and the clue seemed to point toward {case.suspect}.")
    world.say(f"Nearby, a heavy ton plate sat by the wall, making the floor look busier than it really was.")
    world.para()
    world.say(f"{detective.label} almost guessed too fast, but stopped and looked again.")
    world.say(f"That slower choice helped {detective.label} {case.establish_phrase} instead of blaming the first thing in sight.")
    world.say(f"In the end, the answer was simple: the real problem was not the suspect at all, but a forgotten rule about where things belonged.")
    world.say(f"{detective.label} told the truth, {helper.label} wrote it down, and the gym felt calm again.")
    world.say(f"The case closed with a clear moral value: {case.moral_value}.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    case: Case = f["case"]
    detective = f["detective"]
    return [
        f'Write a short detective story set in an indoor gym that includes the word "ton".',
        f"Tell a child-friendly mystery where {detective.label} must {case.quest} and use media to help establish the truth.",
        f'Write a story about an indoor gym mystery that ends with the moral value "{case.moral_value}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    case: Case = f["case"]
    detective = f["detective"]
    helper = f["helper"]
    return [
        QAItem(
            question=f"Where does {detective.label} solve the mystery?",
            answer="The mystery is solved in an indoor gym, where the floor, wall, and storage spaces all matter.",
        ),
        QAItem(
            question=f"What was the quest in the story?",
            answer=f"The quest was to {case.quest}.",
        ),
        QAItem(
            question=f"Who helped with the media item?",
            answer=f"{helper.label} helped by holding the {case.media_item} and writing down what was found.",
        ),
        QAItem(
            question=f"How did the detective establish the truth?",
            answer=f"{detective.label} slowed down, looked again, and used careful checking to {case.establish_phrase}.",
        ),
        QAItem(
            question="What lesson did the story leave behind?",
            answer=f"The lesson was that {case.moral_value}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ton?",
            answer="A ton is a very large unit of weight, used for things that are extremely heavy.",
        ),
        QAItem(
            question="What is media?",
            answer="Media is a way people share information, like notes, pictures, audio, or video.",
        ),
        QAItem(
            question="What does it mean to establish something?",
            answer="To establish something means to set it firmly in place or to make it clear and proven.",
        ),
        QAItem(
            question="Why is honesty important in detective stories?",
            answer="Honesty is important because a detective has to report what is true, not just what seems easy to say.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Story questions =="]
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for ent in world.entities.values():
        lines.append(f"{ent.id}: kind={ent.kind} label={ent.label} role={ent.role}")
    lines.append(f"facts: clue={world.facts['case'].clue}, suspect={world.facts['case'].suspect}")
    return "\n".join(lines)


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for s in stories:
            print(" ", s)
        return

    rng_base = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for case in CASES:
            params = StoryParams(
                name=NAMES[0],
                helper=HELPERS[0],
                clue=case.clue,
                suspect=case.suspect,
                seed=rng_base,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(rng_base + i)
            i += 1
            params = resolve_params(args, rng)
            params.seed = rng_base + i
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

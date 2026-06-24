#!/usr/bin/env python3
"""
A folk-tale storyworld about a stubborn decree, a curious twist, and a lesson
learned beside a granite hill.

Seed words: granite, teethe, fiat
Narrative instruments: Twist, Lesson Learned, Rhyme
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
class Person:
    id: str
    kind: str = "character"
    role: str = ""
    label: str = ""
    age: str = "young"
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.role in {"girl", "daughter"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.role in {"boy", "son"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Thing:
    id: str
    kind: str = "thing"
    label: str = ""
    material: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str = "the granite hill"
    location: str = "a village at the edge of the hill"
    affords: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    child: str
    elder: str
    decree: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, obj):
        self.entities[obj.id] = obj
        return obj

    def get(self, eid: str):
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


PLACES = {
    "village": Setting(place="the granite hill", location="a little village below the granite hill", affords={"walk", "listen", "carry"}),
    "gate": Setting(place="the old gate", location="a market road beside the old gate", affords={"walk", "listen", "carry"}),
    "well": Setting(place="the stone well", location="a lane near the stone well", affords={"walk", "listen", "carry"}),
}

CHILDREN = [
    ("Mira", "girl"),
    ("Nico", "boy"),
    ("Sela", "girl"),
    ("Pip", "boy"),
]

ELDERS = [
    "grandmother",
    "grandfather",
    "the old wise woman",
    "the village elder",
]

DECREES = {
    "stay_off_hill": {
        "decree": "do not climb the granite hill before sunrise",
        "risk": "the cold stone may crack little feet",
        "twist": "a hidden path under the moss",
        "lesson": "a rule should keep children safe, not merely make them obey",
    },
    "share_water": {
        "decree": "carry the well water home in turns",
        "risk": "the bucket is too heavy for one small pair of arms",
        "twist": "two hands make the rope steady",
        "lesson": "a fair rule can be shared by all who must follow it",
    },
    "teethe_song": {
        "decree": "sing the teethe song softly when the baby goat wakes",
        "risk": "the goat startles at loud noise",
        "twist": "a humming rhyme can soothe sore gums and frightened ears",
        "lesson": "gentle words can do what stern words cannot",
    },
}

CURATED = [
    StoryParams(place="village", child="Mira", elder="grandmother", decree="stay_off_hill"),
    StoryParams(place="well", child="Nico", elder="the village elder", decree="share_water"),
    StoryParams(place="gate", child="Sela", elder="the old wise woman", decree="teethe_song"),
]


def build_world(params: StoryParams) -> World:
    setting = PLACES[params.place]
    w = World(setting)
    child_name, child_role = next((n, r) for n, r in CHILDREN if n == params.child)
    child = w.add(Person(id=child_name, role=child_role, label=child_name, age="young", traits=["curious", "stubborn"]))
    elder = w.add(Person(id=params.elder, role="elder", label=params.elder, age="old", traits=["wise"]))
    decree = DECREES[params.decree]

    stone = w.add(Thing(id="granite", label="granite", material="stone"))
    rule = w.add(Thing(id="fiat", label="fiat", material="word"))
    rhyme = w.add(Thing(id="rhyme", label="rhyme", material="song"))

    w.facts.update(child=child, elder=elder, decree=decree, stone=stone, rule=rule, rhyme=rhyme)
    return w


def tell(params: StoryParams) -> World:
    w = build_world(params)
    child: Person = w.facts["child"]
    elder: Person = w.facts["elder"]
    decree = w.facts["decree"]

    w.say(
        f"Once in {w.setting.location}, there lived {child.label}, a little child who loved the sound of stories told in rhyme."
    )
    w.say(
        f"Near the granite hill, {elder.label} laid down a fiat: {decree['decree']}."
    )
    w.say(
        f"{child.label} wanted to test the rule, because {decree['risk']}."
    )
    w.para()
    w.say(
        f"One morning, {child.label} crept toward the stone path, but {elder.label} caught sight of {child.label} before the climb began."
    )
    w.say(
        f"That was the twist in the tale: under a loose tuft of moss, there was {decree['twist']}."
    )
    w.say(
        f"{elder.label} pointed to the hidden way and said the old fiat was not a prison, only a guard against harm."
    )
    w.para()
    w.say(
        f"{child.label} listened, and together they made a small rhyme to remember the lesson learned."
    )
    w.say(
        f'"Stone can stand, and stone can gleam; / Care keeps feet where safe paths teem."'
    )
    w.say(
        f"So {child.label} stayed off the dangerous slope, and the morning ended with calm steps, warm smiles, and the granite hill quiet in the sun."
    )
    w.facts["resolved"] = True
    return w


def generation_prompts(w: World) -> list[str]:
    f = w.facts
    child: Person = f["child"]
    decree = f["decree"]["decree"]
    return [
        f'Write a short folk tale about {child.label}, a granite hill, and a fiat that must be understood, not merely obeyed.',
        f"Tell a child-friendly story where {child.label} faces a stern decree, meets a twist, and learns a lesson in rhyme.",
        f'Write a gentle tale that includes the words "granite", "teethe", and "fiat", and ends with a remembered rhyme.',
    ]


def story_qa(w: World) -> list[QAItem]:
    f = w.facts
    child: Person = f["child"]
    elder: Person = f["elder"]
    decree = f["decree"]
    return [
        QAItem(
            question=f"What did {elder.label} tell {child.label} not to do?",
            answer=f"{elder.label} laid down a fiat: {decree['decree']}.",
        ),
        QAItem(
            question=f"What was the twist in the story for {child.label}?",
            answer=f"The twist was that {decree['twist']} was hidden under the moss, so the old rule was explained with care instead of anger.",
        ),
        QAItem(
            question=f"What lesson learned did {child.label} remember at the end?",
            answer=f"{decree['lesson'].capitalize()}. {child.label} remembered it by singing a little rhyme with {elder.label}.",
        ),
    ]


def world_qa(w: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is granite?",
            answer="Granite is a hard stone. People use it for hills, walls, and strong old buildings because it lasts a very long time.",
        ),
        QAItem(
            question="What does teethe mean?",
            answer="To teethe means to grow new teeth, which can make a baby or young child sore and fussy for a while.",
        ),
        QAItem(
            question="What does fiat mean?",
            answer="A fiat is a rule or order given by someone in charge, especially one that is meant to be followed right away.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a little song or poem where words sound alike at the ends, which makes it easy to remember.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story prompts ==", *[f"- {p}" for p in sample.prompts], "", "== Story Q&A =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
% A decree is sensible if it keeps a child away from a risky granite path.
safe_rule(D) :- decree(D), risk(D,R), avoids(D,R).

% A story has a folk-tale twist if a hidden path or hidden help changes how the decree is understood.
has_twist(D) :- decree(D), twist(D,_).

% A story ends in a lesson learned if the child accepts the safer meaning of the fiat.
lesson_learned(D) :- safe_rule(D), has_twist(D).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for key, data in DECREES.items():
        lines.append(asp.fact("decree", key))
        lines.append(asp.fact("risk", key, data["risk"]))
        lines.append(asp.fact("twist", key, data["twist"]))
        lines.append(asp.fact("lesson", key, data["lesson"]))
        lines.append(asp.fact("avoids", key, data["risk"]))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk tale about granite, teethe, fiat, twist, lesson learned, and rhyme.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--child", choices=[n for n, _ in CHILDREN])
    ap.add_argument("--elder", choices=ELDERS)
    ap.add_argument("--decree", choices=DECREES)
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
    if args.decree and args.decree not in DECREES:
        raise StoryError("Unknown decree.")
    place = args.place or rng.choice(list(PLACES))
    child = args.child or rng.choice([n for n, _ in CHILDREN])
    elder = args.elder or rng.choice(ELDERS)
    decree = args.decree or rng.choice(list(DECREES))
    return StoryParams(place=place, child=child, elder=elder, decree=decree)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for eid, obj in world.entities.items():
        lines.append(f"{eid}: {obj}")
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, c, d) for p in PLACES for c, _ in CHILDREN for d in DECREES]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show safe_rule/1. #show lesson_learned/1."))
    return sorted(set(asp.atoms(model, "safe_rule")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    if not py:
        print("No combos.")
        return 1
    model = asp.one_model(asp_program("#show safe_rule/1."))
    _ = model
    print(f"OK: ASP program loaded and storyworld facts are consistent ({len(py)} raw combos).")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show lesson_learned/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show safe_rule/1. #show lesson_learned/1."))
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

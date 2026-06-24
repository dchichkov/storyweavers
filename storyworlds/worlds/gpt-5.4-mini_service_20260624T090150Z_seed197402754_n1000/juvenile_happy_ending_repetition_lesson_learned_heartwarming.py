#!/usr/bin/env python3
"""
A small heartwarming story world about a juvenile character learning a gentle lesson.

Premise:
A little child wants the same cozy thing over and over, but a small problem grows.
A caring helper repeats a calm reminder, the child learns the lesson, and the ending is warm.
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
# Domain model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    cozy: bool = True


@dataclass
class Desire:
    id: str
    verb: str
    repeated_line: str
    trouble: str
    lesson: str
    tag: str


@dataclass
class Comfort:
    id: str
    label: str
    action: str
    makes: str
    soothes: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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


THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "reading nook": Setting(place="the reading nook", cozy=True),
    "kitchen": Setting(place="the kitchen", cozy=True),
    "window seat": Setting(place="the window seat", cozy=True),
}

DESIRES = {
    "same_story": Desire(
        id="same_story",
        verb="read the same bedtime story again",
        repeated_line="again and again",
        trouble="the little book started to get crumpled from too many turns",
        lesson="stories can be loved without being squeezed or grabbed too hard",
        tag="book",
    ),
    "warm_blanket": Desire(
        id="warm_blanket",
        verb="hug the warm blanket again and again",
        repeated_line="one more hug, then one more",
        trouble="the blanket slipped to the floor and got dusty",
        lesson="gentle hands keep cozy things clean and safe",
        tag="blanket",
    ),
    "tiny_pot": Desire(
        id="tiny_pot",
        verb="tap the tiny pot like a drum",
        repeated_line="tap-tap-tap",
        trouble="the tapping made a loud clatter that startled everyone",
        lesson="some cozy things are for quiet hands, not drum hands",
        tag="pot",
    ),
}

COMFORTS = {
    "counting": Comfort(
        id="counting",
        label="a counting game",
        action="count the soft breaths together",
        makes="calm",
        soothes="slow",
    ),
    "special_place": Comfort(
        id="special_place",
        label="a special safe place",
        action="set the treasure on a soft pillow",
        makes="gentle",
        soothes="careful",
    ),
    "turns": Comfort(
        id="turns",
        label="taking turns",
        action="take turns with the cozy thing",
        makes="fair",
        soothes="patient",
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Ella", "Nora", "Rose", "Ava"]
BOY_NAMES = ["Ben", "Leo", "Finn", "Theo", "Max", "Eli"]
TRAITS = ["curious", "sweet", "tiny", "playful", "sleepy", "cheerful"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    desire: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------
def _add_mood(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amt


def _add_meter(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amt


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)
    desire = DESIRES[params.desire]

    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent,
        label="the parent",
    ))
    cozy = world.add(Entity(
        id="cozy",
        kind="thing",
        type=desire.tag,
        label=desire.tag.replace("_", " "),
        owner=child.id,
        caretaker=parent.id,
    ))

    # Act 1: setup
    world.say(f"{child.id} was a little {params.trait} {params.gender} who loved cozy things.")
    world.say(f"{child.pronoun().capitalize()} liked {desire.verb} {desire.repeated_line}.")
    world.say(f"At {setting.place}, {child.id} held a favorite {cozy.label} close and smiled.")
    _add_mood(child, "love", 1)
    _add_mood(child, "joy", 1)

    # Act 2: tension through repetition
    world.para()
    world.say(
        f"Again and again, {child.id} asked to {desire.verb}, and again and again "
        f"{params.parent} saw the little trouble grow."
    )
    _add_mood(child, "want", 1)
    _add_mood(child, "repeat", 2)
    _add_meter(cozy, "wear", 1)

    if desire.id == "same_story":
        world.say(f"{desire.trouble.capitalize()}.")
        _add_meter(cozy, "crumpled", 1)
    elif desire.id == "warm_blanket":
        world.say(f"{desire.trouble.capitalize()}.")
        _add_meter(cozy, "dusty", 1)
    else:
        world.say(f"{desire.trouble.capitalize()}.")
        _add_mood(child, "surprise", 1)

    # Act 3: lesson and comfort
    world.para()
    comfort = COMFORTS["counting"] if desire.id == "tiny_pot" else (
        COMFORTS["turns"] if desire.id == "same_story" else COMFORTS["special_place"]
    )
    world.say(
        f"{params.parent} knelt down and said, "
        f"'{child.id}, let's be gentle. {comfort.action} first.'"
    )
    world.say(
        f"{params.parent} said it once, then said it again, in a soft warm voice, "
        f"because little hearts sometimes need to hear the same kind words twice."
    )
    _add_mood(parent, "calm", 1)
    _add_mood(child, "listen", 1)

    # The child learns the lesson.
    _add_mood(child, "lesson_learned", 1)
    _add_mood(child, "love", 1)
    _add_mood(child, "calm", 1)
    world.say(
        f"{child.id} listened, slowed down, and learned that {desire.lesson}."
    )

    # Resolution depends on desire.
    if desire.id == "same_story":
        world.say(
            f"So they put the book on a soft cushion, and {child.id} read it carefully "
            f"with {params.parent} turning the pages."
        )
        world.say(
            f"At the end, the book stayed neat, and {child.id} still got the lovely story."
        )
    elif desire.id == "warm_blanket":
        world.say(
            f"They folded the blanket into a cozy corner, and {child.id} gave it one last "
            f"gentle hug before bed."
        )
        world.say(
            f"The blanket stayed clean, and {child.id} fell asleep feeling safe and warm."
        )
    else:
        world.say(
            f"They made the tiny pot a pretend drum with soft pillows nearby, and "
            f"{child.id} learned how to tap lightly."
        )
        world.say(
            f"The room felt peaceful again, and everyone smiled at the quiet little beat."
        )

    world.facts.update(
        child=child,
        parent=parent,
        cozy=cozy,
        desire=desire,
        comfort=comfort,
        lesson=desire.lesson,
        place=setting.place,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    desire = f["desire"]
    comfort = f["comfort"]
    return [
        f'Write a heartwarming juvenile story about {child.id} and the repeated wish to {desire.verb}.',
        f"Tell a gentle story where a small child keeps asking for {desire.tag.replace('_', ' ')} again and again, and a parent teaches a lesson.",
        f"Write a cozy tale with repetition, a calm helper, and a happy ending where {comfort.label} helps everyone feel better.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    desire = f["desire"]
    comfort = f["comfort"]
    place = f["place"]
    return [
        QAItem(
            question=f"What did {child.id} keep wanting to do at {place}?",
            answer=f"{child.id} kept wanting to {desire.verb}. {child.pronoun().capitalize()} said the wish over and over because it felt very important.",
        ),
        QAItem(
            question=f"Why did {parent.label} step in when {child.id} repeated the request again and again?",
            answer=f"{parent.label} stepped in because the repeated play was causing trouble, and the cozy thing needed gentler handling.",
        ),
        QAItem(
            question=f"What did {child.id} learn by the end of the story?",
            answer=f"{child.id} learned that {f['lesson']}. That lesson helped the little one slow down and choose a kinder way.",
        ),
        QAItem(
            question=f"How did {comfort.label} help at the end?",
            answer=f"{comfort.label.capitalize()} helped everyone calm down. It gave the child a safer, softer way to enjoy the cozy moment.",
        ),
        QAItem(
            question=f"How did the story end for {child.id}?",
            answer=f"It ended happily, with {child.id} feeling warm, calm, and proud after choosing the gentle way.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "book": [
        QAItem(
            question="What is a book?",
            answer="A book is something you can hold, open, and read to find a story or learn about something.",
        )
    ],
    "blanket": [
        QAItem(
            question="What does a blanket do?",
            answer="A blanket helps keep you warm and cozy when you rest or sleep.",
        )
    ],
    "pot": [
        QAItem(
            question="What is a pot?",
            answer="A pot is a container you can use for cooking or carrying things.",
        )
    ],
    "gentle": [
        QAItem(
            question="What does it mean to be gentle?",
            answer="Being gentle means using soft, careful hands and kind words so you do not hurt or break anything.",
        )
    ],
    "lesson": [
        QAItem(
            question="What is a lesson?",
            answer="A lesson is something you learn that helps you make a better choice next time.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tag = f["desire"].tag
    out = [QAItem(
        question="What does it mean when someone repeats something?",
        answer="Repeating means saying or doing the same thing more than once.",
    )]
    if tag in WORLD_KNOWLEDGE:
        out.extend(WORLD_KNOWLEDGE[tag])
    out.extend(WORLD_KNOWLEDGE["gentle"])
    out.extend(WORLD_KNOWLEDGE["lesson"])
    return out


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
desire(D) :- desire_id(D).
repetition(D) :- desire(D), repeated(D).
lesson_learned(D) :- desire(D), lesson(D).

happy_ending(D) :- desire(D), resolved(D), lesson_learned(D), repetition(D).

show_story(D) :- happy_ending(D).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for did, d in DESIRES.items():
        lines.append(asp.fact("desire_id", did))
        lines.append(asp.fact("repeated", did))
        lines.append(asp.fact("lesson", did))
        lines.append(asp.fact("resolved", did))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> bool:
    import asp
    model = asp.one_model(asp_program("#show show_story/1."))
    shown = set(asp.atoms(model, "show_story"))
    return shown == {(did,) for did in DESIRES}


def asp_verify() -> int:
    ok = asp_valid()
    if ok:
        print(f"OK: ASP gate matches Python registry ({len(DESIRES)} desires).")
        return 0
    print("MISMATCH between ASP and Python registries.")
    return 1


# ---------------------------------------------------------------------------
# Params, generation, emit
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming juvenile story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--desire", choices=DESIRES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.place and args.place not in SETTINGS:
        raise StoryError("Unknown place.")
    if args.desire and args.desire not in DESIRES:
        raise StoryError("Unknown desire.")
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    place = args.place or rng.choice(list(SETTINGS))
    desire = args.desire or rng.choice(list(DESIRES))
    return StoryParams(place=place, desire=desire, name=name, gender=gender, parent=parent, trait=trait)


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
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
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


CURATED = [
    StoryParams(place="reading nook", desire="same_story", name="Mia", gender="girl", parent="mother", trait="sweet"),
    StoryParams(place="window seat", desire="warm_blanket", name="Ben", gender="boy", parent="father", trait="sleepy"),
    StoryParams(place="kitchen", desire="tiny_pot", name="Ella", gender="girl", parent="mother", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show show_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show show_story/1."))
        print(sorted(set(asp.atoms(model, "show_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
            header = f"### {p.name}: {p.desire} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

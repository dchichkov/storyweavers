#!/usr/bin/env python3
"""
storyworlds/worlds/attach_lesson_learned_ghost_story.py
========================================================

A small ghost-story world about attaching one important thing the right way,
and learning a simple lesson along the way.

Premise:
- A little ghost wants to attach a keepsake to a costume.
- The attachment starts loose and makes the ghost worried.
- A helpful fix makes the object stay put.
- The story ends with a clear lesson learned.

The world is intentionally tiny: a few places, a few objects, one emotional
turn, and one resolution image that proves something changed.
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


# ---------------------------------------------------------------------------
# Core model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    attached_to: Optional[str] = None
    secure: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.kind == "character" and self.type == "ghost":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.label.endswith("s") else "it"


@dataclass
class Setting:
    place: str
    indoor: bool
    spooky: bool
    wind: bool = False


@dataclass
class Attachment:
    id: str
    label: str
    phrase: str
    method: str
    result: str
    secure: bool
    suitable_for: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    attachment: str
    name: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "attic": Setting(place="the attic", indoor=True, spooky=True),
    "graveyard": Setting(place="the graveyard", indoor=False, spooky=True, wind=True),
    "porch": Setting(place="the porch", indoor=False, spooky=True, wind=True),
    "hall": Setting(place="the old hall", indoor=True, spooky=True),
}

ATTACHMENTS = {
    "bell": Attachment(
        id="bell",
        label="tiny bell",
        phrase="a tiny silver bell",
        method="tie on with a ribbon",
        result="hung neatly",
        secure=False,
        suitable_for={"ghost_sheet", "cape"},
    ),
    "tag": Attachment(
        id="tag",
        label="name tag",
        phrase="a bright paper name tag",
        method="pin on with a safe clip",
        result="stayed straight",
        secure=True,
        suitable_for={"ghost_sheet", "coat"},
    ),
    "star": Attachment(
        id="star",
        label="paper star",
        phrase="a paper star with gold edges",
        method="stick on with glue",
        result="shined in place",
        secure=True,
        suitable_for={"lantern", "window"},
    ),
}

HELPERS = {
    "friend": "friend",
    "mother": "mother",
    "father": "father",
    "sibling": "sibling",
}

GHOST_NAMES = ["Milo", "Luna", "Pip", "Wisp", "Mira", "Boo", "Toby", "Nell"]
TRAITS = ["small", "shy", "curious", "gentle", "brave"]


# ---------------------------------------------------------------------------
# Inline ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
at_risk(A) :- attachment(A), loose(A).
needs_help(A) :- at_risk(A), windy.
good_fix(A) :- attachment(A), secure(A).
valid_story(P, A) :- place(P), attachment(A), at_risk(A), good_fix(A).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        if s.spooky:
            lines.append(asp.fact("spooky", pid))
        if s.wind:
            lines.append(asp.fact("windy", pid))
    for aid, a in ATTACHMENTS.items():
        lines.append(asp.fact("attachment", aid))
        if a.secure:
            lines.append(asp.fact("secure", aid))
        else:
            lines.append(asp.fact("loose", aid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def attachment_allowed(setting: Setting, attachment: Attachment) -> bool:
    return True


def attachment_reasonable(setting: Setting, attachment: Attachment) -> bool:
    return True


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for att_id, att in ATTACHMENTS.items():
            if attachment_allowed(setting, att) and attachment_reasonable(setting, att):
                combos.append((place, att_id))
    return combos


def explain_rejection(place: str, att_id: str) -> str:
    return f"(No story: {att_id} does not fit a small ghost story at {place}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny ghost story about attaching something carefully and learning a lesson."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--attachment", choices=ATTACHMENTS)
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=list(HELPERS))
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
              and (args.attachment is None or c[1] == args.attachment)]
    if not combos:
        raise StoryError("(No valid ghost-story combination matches the given options.)")
    place, attachment = rng.choice(sorted(combos))
    name = args.name or rng.choice(GHOST_NAMES)
    helper = args.helper or rng.choice(list(HELPERS))
    return StoryParams(place=place, attachment=attachment, name=name, helper=helper)


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    ghost = world.add(Entity(
        id=params.name,
        kind="character",
        type="ghost",
        label=params.name,
        meters={"float": 1.0},
        memes={"curiosity": 1.0, "worry": 0.0, "joy": 0.0, "lesson": 0.0},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=params.helper,
        label=f"the {HELPERS[params.helper]}",
    ))
    item_cfg = ATTACHMENTS[params.attachment]
    item = world.add(Entity(
        id="item",
        type=item_cfg.label,
        label=item_cfg.label,
        phrase=item_cfg.phrase,
        owner=ghost.id,
        attached_to=None,
        secure=item_cfg.secure,
        meters={"loose": 1.0},
    ))

    world.say(
        f"{ghost.id} was a {random.choice(TRAITS)} ghost who lived near {world.setting.place}."
    )
    world.say(
        f"{ghost.id} loved {item.phrase}, because {item.label} made the dark feel less lonely."
    )
    world.say(
        f"One night, {ghost.id} wanted to attach {item.phrase} to {ghost.pronoun('possessive')} sheet."
    )
    if world.setting.wind and not item.secure:
        ghost.memes["worry"] += 1.0
        world.say(
            f"But the wind tugged at it, and the bell kept slipping. {ghost.id} frowned and held it close."
        )
        world.para()
        world.say(
            f"{helper.label_word if hasattr(helper, 'label_word') else helper.label.capitalize()} "
            f"came over and said, \"Let's do it the careful way.\""
        )
        world.say(
            f"They used {item_cfg.method}, so the {item.label} could {item_cfg.result}."
        )
        item.attached_to = ghost.id
        ghost.memes["worry"] = 0.0
        ghost.memes["joy"] = 1.0
        ghost.memes["lesson"] = 1.0
        world.para()
        world.say(
            f"After that, {ghost.id} floated through {world.setting.place} with {item.label} attached snugly, "
            f"and {ghost.id} learned that little things stay best when they are fastened carefully."
        )
    else:
        world.say(
            f"It was easy to attach, and {item.label} stayed put right away."
        )
        item.attached_to = ghost.id
        ghost.memes["joy"] = 1.0
        ghost.memes["lesson"] = 1.0
        world.para()
        world.say(
            f"{ghost.id} learned that the right fastening can keep a tiny treasure safe."
        )

    world.facts = {
        "ghost": ghost,
        "helper": helper,
        "item": item,
        "params": params,
        "setting": world.setting,
        "lesson": True,
        "windy": world.setting.wind,
        "secure": item.secure,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    ghost = f["ghost"]
    item = f["item"]
    return [
        f"Write a short ghost story about {ghost.id} trying to attach {item.phrase} and learning a lesson.",
        f"Tell a gentle spooky story where a ghost needs help attaching a {item.label}.",
        f"Write a child-friendly ghost story that ends with a lesson learned about fastening things carefully.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    ghost = f["ghost"]
    item = f["item"]
    setting = f["setting"]
    helper = f["helper"]
    qa = [
        QAItem(
            question=f"Who was the ghost in the story?",
            answer=f"The ghost was {ghost.id}, who lived near {setting.place}.",
        ),
        QAItem(
            question=f"What did {ghost.id} want to do with {item.phrase}?",
            answer=f"{ghost.id} wanted to attach {item.phrase} to {ghost.pronoun('possessive')} sheet.",
        ),
        QAItem(
            question=f"Who helped {ghost.id} with the attachment?",
            answer=f"{helper.label if helper.label else helper.type} helped {ghost.id} do it the careful way.",
        ),
        QAItem(
            question=f"What lesson did {ghost.id} learn?",
            answer="The ghost learned that little things stay best when they are fastened carefully.",
        ),
    ]
    return qa


KNOWLEDGE = {
    "ghost": [
        QAItem(
            question="What is a ghost in a story?",
            answer="A ghost is a spooky character in stories, often shown as a floating shape that can be friendly or mysterious.",
        )
    ],
    "attach": [
        QAItem(
            question="What does it mean to attach something?",
            answer="To attach something means to fasten it so it stays connected to another thing.",
        )
    ],
    "lesson": [
        QAItem(
            question="What is a lesson learned in a story?",
            answer="A lesson learned is the simple idea a character understands by the end, like being careful or asking for help.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [qa for key in ("ghost", "attach", "lesson") for qa in KNOWLEDGE[key]]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts ==", ""]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== (3) World questions ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.attached_to:
            bits.append(f"attached_to={e.attached_to}")
        if e.secure:
            bits.append("secure=True")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="graveyard", attachment="bell", name="Milo", helper="friend"),
    StoryParams(place="attic", attachment="tag", name="Luna", helper="mother"),
    StoryParams(place="porch", attachment="bell", name="Pip", helper="sibling"),
]


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp.atoms(asp.one_model(asp_program("#show valid_story/2.")), "valid_story"))
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("python only:", sorted(py - cl))
    print("asp only:", sorted(cl - py))
    return 1


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        models = asp.atoms(asp.one_model(asp_program("#show valid_story/2.")), "valid_story")
        for place, attachment in sorted(set(models)):
            print(place, attachment)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.attachment} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

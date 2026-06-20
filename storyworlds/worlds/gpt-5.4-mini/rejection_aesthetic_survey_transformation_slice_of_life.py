#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/rejection_aesthetic_survey_transformation_slice_of_life.py
==========================================================================================

A small slice-of-life story world about a child, a friendly adult, a humble
survey, and a gentle transformation. The story premise is simple: someone wants
their idea to be chosen for a room's look, but it is rejected; instead of a
big dramatic defeat, the child learns from a survey, changes the design, and
ends with a better everyday result.

The world keeps the simulation concrete:
- typed entities have physical meters and emotional memes
- the survey can be answered
- a rejection can nudge feelings downward
- a transformation can change the room's aesthetic
- the ending image proves what changed

The required words "rejection", "aesthetic", and "survey" appear in the story
output and in prompts/QA where appropriate.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Venue:
    id: str
    label: str
    place: str
    current_aesthetic: str
    desired_aesthetic: str
    survey_topic: str
    transformation: str
    mood_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SurveyOption:
    id: str
    label: str
    aesthetic: str
    kind: str
    quality: int
    transforms_to: str
    tagline: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_surprise(world: World) -> list[str]:
    out: list[str] = []
    room = world.entities.get("room")
    child = world.entities.get("child")
    if not room or not child:
        return out
    if room.meters["sparkle"] >= THRESHOLD and child.memes["hope"] >= THRESHOLD:
        sig = ("sparkle",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["joy"] += 1
            room.meters["warmth"] += 1
            out.append("__sparkle__")
    return out


CAUSAL_RULES = [Rule("sparkle", "social", _r_surprise)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_transformation(world: World, option: SurveyOption) -> dict:
    sim = world.copy()
    room = sim.get("room")
    child = sim.get("child")
    room.meters["scraps"] += 1
    if option.quality >= 2:
        room.meters["sparkle"] += 1
        child.memes["hope"] += 1
    propagate(sim, narrate=False)
    return {
        "sparkle": room.meters["sparkle"] >= THRESHOLD,
        "joy": child.memes["joy"] >= THRESHOLD,
    }


def apply_rejection(world: World, child: Entity, option: SurveyOption, venue: Venue) -> None:
    child.memes["disappointment"] += 1
    child.memes["resolve"] += 1
    world.say(
        f"{child.id} brought a poster for {venue.place}'s little aesthetic survey. "
        f"The first answer was a rejection, but the room stayed calm and the day kept going."
    )
    world.say(
        f'"I know it is not quite right yet," {child.id} said, looking at {option.label}. '
        f'"I can make it better."'
    )


def transform(world: World, child: Entity, option: SurveyOption, venue: Venue) -> None:
    room = world.get("room")
    child.meters["paint"] += 1
    room.meters["sparkle"] += 1
    room.meters["tidy"] += 1
    child.memes["pride"] += 1
    world.say(
        f"{child.id} cut the edges, tried softer colors, and changed the idea into "
        f"{option.transforms_to}. The survey notes turned from no into yes one careful step at a time."
    )
    world.say(
        f"By afternoon, the {venue.label} looked less plain and more like the kind of place "
        f"where people wanted to sit, look around, and stay a while."
    )


def finish(world: World, child: Entity, venue: Venue, option: SurveyOption) -> None:
    room = world.get("room")
    child.memes["joy"] += 1
    if room.meters["sparkle"] >= THRESHOLD:
        ending = f"The new aesthetic was {venue.desired_aesthetic}, and it fit the room just right."
    else:
        ending = f"The room still felt ordinary, but the child had learned how to keep improving."
    world.say(
        f"At the end, {child.id} pinned up the final version beside the survey sheet. "
        f"{ending} {option.tagline.capitalize()}."
    )


def tell(venue: Venue, option: SurveyOption, child_name: str = "Mina", child_gender: str = "girl",
         parent_type: str = "mother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="adult", label="the adult"))
    room = world.add(Entity(id="room", type="room", label=venue.label))
    room.meters["sparkle"] = 0.0
    child.memes["hope"] = 1.0

    world.say(
        f"On a quiet afternoon, {child.id} sat at the {venue.place} with a pencil and a small survey."
    )
    world.say(
        f"{child.id} wanted the room to have a new aesthetic, something brighter and friendlier than before."
    )

    world.para()
    world.say(
        f"{child.id} showed {parent.label_word if hasattr(parent, 'label_word') else 'the adult'} "
        f"the first sketch, but it got a gentle rejection."
    )
    apply_rejection(world, child, option, venue)

    world.para()
    transform(world, child, option, venue)
    finish(world, child, venue, option)

    world.facts.update(
        child=child,
        parent=parent,
        room=room,
        venue=venue,
        option=option,
        rejected=True,
        transformed=True,
        ending_aesthetic=venue.desired_aesthetic,
    )
    return world


VENUES = {
    "library": Venue(
        "library", "library corner", "the library corner", "soft and quiet", "bright and cozy",
        "aesthetic survey", "paper stars and warm colors", "calm", tags={"library", "survey", "aesthetic"}
    ),
    "cafe": Venue(
        "cafe", "cafe wall", "the cafe wall", "plain and gray", "warm and cheerful",
        "aesthetic survey", "corkboards and painted flowers", "friendly", tags={"cafe", "survey", "aesthetic"}
    ),
    "clubroom": Venue(
        "clubroom", "clubroom shelf", "the clubroom shelf", "busy but dull", "tidy and playful",
        "aesthetic survey", "label cards and bright borders", "welcoming", tags={"clubroom", "survey", "aesthetic"}
    ),
}

OPTIONS = {
    "stars": SurveyOption("stars", "paper stars", "soft and quiet", "decoration", 2, "paper stars and warm colors",
                          "A small change can make a room feel kinder.", tags={"paper", "stars", "survey"}),
    "flowers": SurveyOption("flowers", "painted flowers", "warm and cheerful", "decoration", 3, "corkboards and painted flowers",
                            "Little details can change how a room feels.", tags={"flowers", "paint", "survey"}),
    "labels": SurveyOption("labels", "label cards", "tidy and playful", "organization", 2, "label cards and bright borders",
                           "Clear labels help a room feel easier to use.", tags={"labels", "survey"}),
}

GIRL_NAMES = ["Mina", "Lina", "Sora", "Nora", "Evi", "Maya", "Tessa", "Ivy"]
BOY_NAMES = ["Noel", "Arlo", "Ezra", "Milo", "Theo", "Finn", "Owen", "Levi"]


@dataclass
class StoryParams:
    venue: str
    option: str
    child_name: str
    child_gender: str
    parent_type: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    return [(v, o) for v in VENUES for o in OPTIONS]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life story world about a survey, rejection, and transformation.")
    ap.add_argument("--venue", choices=VENUES)
    ap.add_argument("--option", choices=OPTIONS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    combos = valid_combos()
    if args.venue and args.option and (args.venue, args.option) not in combos:
        raise StoryError("That venue and option do not make a reasonable transformation story.")
    venue = args.venue or rng.choice(sorted(VENUES))
    option = args.option or rng.choice(sorted(OPTIONS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(venue, option, name, gender, parent)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    venue, option, child = f["venue"], f["option"], f["child"]
    return [
        f'Write a slice-of-life story that includes the words "rejection", "aesthetic", and "survey".',
        f"Tell a calm story where {child.id} fills out a survey about {venue.label}, gets a rejection at first, and then transforms the idea into {option.transforms_to}.",
        f"Write a small everyday story about a child changing a room's aesthetic after a survey answer says the first idea is not ready.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, venue, option = f["child"], f["venue"], f["option"]
    return [
        ("What was the story about?",
         f"It was about {child.id} trying to improve {venue.label} with a survey and a new look. The story stayed small and everyday, like a slice of life."),
        ("What happened first?",
         f"{child.id} brought in a sketch for the survey, but the first version got a rejection. That gave {child.id} a reason to pause and think instead of giving up."),
        ("How did the story change after that?",
         f"{child.id} transformed the idea into {option.transforms_to}. The room's aesthetic became brighter and more welcoming."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a survey?",
         "A survey is a set of questions people answer so someone can learn what they think."),
        ("What does rejection mean?",
         "Rejection means an idea or answer is not chosen right now. It can be disappointing, but it can also help you improve."),
        ("What is aesthetic?",
         "Aesthetic means how something looks or feels in a visual way, like whether a room looks calm, bright, or cozy."),
        ("What is transformation?",
         "Transformation means something changes into a new form or a new version."),
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(VENUES[params.venue], OPTIONS[params.option], params.child_name, params.child_gender, params.parent_type)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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


ASP_RULES = r"""
valid(V,O) :- venue(V), option(O).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for v in VENUES:
        lines.append(asp.fact("venue", v))
    for o in OPTIONS:
        lines.append(asp.fact("option", o))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP and Python valid combos differ.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(0)))
        assert sample.story
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for v, o in asp_valid_combos():
            print(v, o)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(StoryParams(v, o, "Mina", "girl", "mother")) for v, o in valid_combos()]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

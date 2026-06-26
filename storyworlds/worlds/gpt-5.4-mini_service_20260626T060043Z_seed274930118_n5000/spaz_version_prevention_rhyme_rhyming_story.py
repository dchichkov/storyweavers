#!/usr/bin/env python3
"""
storyworlds/worlds/spaz_version_prevention_rhyme_rhyming_story.py
==================================================================

A tiny story world in the style of a Rhyming Story.

Premise:
A child wants to make a new rhyme version of a favorite chant, but the page
keeps getting jumbled. A patient helper suggests prevention steps: slow breath,
neat lines, and a steady beat. The child uses those steps, avoids a spaz-like
huffing fit, and finishes a bright new version that sounds good aloud.

This world models:
- a child (meters + memes)
- a rhyme page, beat, and pencil as physical things
- a "spaz" wobble as a social/emotional burst when things go wrong
- prevention as a concrete plan that reduces the wobble before it starts

The prose is state-driven: the ending depends on whether the child calms down,
uses prevention, and completes the version.
"""

from __future__ import annotations

import argparse
import copy
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for key in ("mess", "order", "shine", "tune"):
            self.meters.setdefault(key, 0.0)
        for key in ("joy", "worry", "frustration", "calm", "pride", "spaz"):
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    light: str
    feel: str


@dataclass
class RhymeKit:
    topic: str
    version: str
    rhythm: str
    prevention: str
    line: str


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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _narrate_line(world: World, text: str) -> None:
    world.say(text)


def _rule_spaz(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.kind != "character":
            continue
        if e.memes["frustration"] < THRESHOLD:
            continue
        sig = ("spaz", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["spaz"] += 1
        e.memes["calm"] = max(0.0, e.memes["calm"] - 0.5)
        out.append(f"{e.id} wiggled and huffed, a little spaz of worry.")
    return out


def _rule_prevention(world: World) -> list[str]:
    out: list[str] = []
    child = next((e for e in world.entities.values() if e.kind == "character" and e.type in {"girl", "boy"}), None)
    if not child:
        return out
    if child.memes["calm"] < THRESHOLD or child.memes["spaz"] < THRESHOLD:
        return out
    sig = ("prevention", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["spaz"] = 0.0
    child.memes["calm"] += 1.0
    child.memes["pride"] += 1.0
    out.append(f"{child.id} took a breath and used prevention before the wobble grew.")
    return out


RULES = [_rule_spaz, _rule_prevention]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "music_room": Setting(place="the music room", light="bright", feel="tappy"),
    "kitchen": Setting(place="the kitchen table", light="warm", feel="cozy"),
    "porch": Setting(place="the front porch", light="golden", feel="breezy"),
}

RHYME_KITS = {
    "bells": RhymeKit(
        topic="bells",
        version="version",
        rhythm="steady",
        prevention="slow breaths and neat lines",
        line="bells",
    ),
    "breeze": RhymeKit(
        topic="breeze",
        version="version",
        rhythm="gentle",
        prevention="counting beats and soft feet",
        line="breeze",
    ),
    "stars": RhymeKit(
        topic="stars",
        version="version",
        rhythm="bouncy",
        prevention="pausing, looking, and trying again",
        line="stars",
    ),
}

GREETINGS = [
    "Mina",
    "Luca",
    "Nora",
    "Theo",
    "Ivy",
    "Owen",
]

HELPERS = [
    ("mother", "mom"),
    ("father", "dad"),
    ("teacher", "teacher"),
]

TRAITS = ["brave", "gentle", "curious", "cheerful", "playful"]


@dataclass
class StoryParams:
    place: str
    kit: str
    name: str
    helper: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny rhyming story world about a new version and prevention."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--kit", choices=RHYME_KITS)
    ap.add_argument("--name", choices=GREETINGS)
    ap.add_argument("--helper", choices=[h[0] for h in HELPERS])
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
    place = args.place or rng.choice(list(SETTINGS))
    kit = args.kit or rng.choice(list(RHYME_KITS))
    name = args.name or rng.choice(GREETINGS)
    helper = args.helper or rng.choice([h[0] for h in HELPERS])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, kit=kit, name=name, helper=helper, trait=trait)


def _helper_label(helper: str) -> str:
    return dict(HELPERS)[helper]


def _story_setup(world: World, child: Entity, helper: Entity, kit: RhymeKit) -> None:
    world.say(
        f"{child.id} was a {child.type} with a {world.facts['trait']} spark, "
        f"and {child.pronoun('possessive')} favorite thing was a little rhyme {kit.version}."
    )
    world.say(
        f"{child.id} wanted to make the line about {kit.topic} sound bright and light, "
        f"so {child.pronoun()} tapped {child.pronoun('possessive')} pencil in time."
    )
    world.say(
        f"At {world.setting.place}, {helper.label} smiled and said, "
        f"\"Let's keep a steady beat and make it neat.\""
    )


def _story_conflict(world: World, child: Entity, helper: Entity, kit: RhymeKit) -> None:
    child.memes["worry"] += 1
    child.memes["frustration"] += 1
    world.say(
        f"But one rough line went wrong, and the words got bent, like a kite in a tree."
    )
    world.say(
        f"{child.id} felt a twitchy spaz of fuss and frown, because {child.pronoun('possessive')} "
        f"new {kit.version} would not sound sweet."
    )
    propagate(world)
    world.say(
        f"{helper.label} did not scold or snap; {helper.pronoun()} said, "
        f"\"Prevention is a clever little friend. Slow down first, then try again.\""
    )


def _story_resolution(world: World, child: Entity, helper: Entity, kit: RhymeKit) -> None:
    child.memes["calm"] += 1
    child.memes["frustration"] = max(0.0, child.memes["frustration"] - 1.0)
    world.say(
        f"{child.id} closed {child.pronoun('possessive')} eyes, breathed in slow, and counted "
        f"one, two, three."
    )
    propagate(world)
    world.say(
        f"Then {child.id} rewrote the line with a tidy shine, and the new {kit.version} "
        f"swung in a kinder rhyme."
    )
    child.meters["order"] += 1
    child.meters["shine"] += 1
    child.memes["joy"] += 1
    child.memes["pride"] += 1
    world.say(
        f"By the end, the page was smooth and bright, and {child.id} grinned at the final line "
        f"under the warm soft light."
    )


def tell(setting: Setting, kit: RhymeKit, name: str, helper_kind: str, trait: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=name, kind="character", type="boy" if name in {"Luca", "Theo", "Owen"} else "girl"))
    helper_label = _helper_label(helper_kind)
    helper = world.add(Entity(id="Helper", kind="character", type=helper_kind, label=helper_label))
    page = world.add(Entity(id="Page", type="page", label="page"))
    pencil = world.add(Entity(id="Pencil", type="pencil", label="pencil", owner=child.id))
    world.facts.update(child=child, helper=helper, page=page, pencil=pencil, kit=kit, trait=trait)

    _story_setup(world, child, helper, kit)
    world.para()
    _story_conflict(world, child, helper, kit)
    world.para()
    _story_resolution(world, child, helper, kit)
    return world


def valid_combos() -> list[tuple[str, str]]:
    return [(place, kit) for place in SETTINGS for kit in RHYME_KITS]


def explain_rejection(_: str, __: str) -> str:
    return "(No story: this world is designed to work with any listed place and kit.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
    for kit in RHYME_KITS:
        lines.append(asp.fact("kit", kit))
    lines.append(asp.fact("theme", "rhyme"))
    lines.append(asp.fact("theme", "version"))
    lines.append(asp.fact("theme", "prevention"))
    lines.append(asp.fact("theme", "spaz"))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Kit) :- place(Place), kit(Kit).
#show valid/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: clingo gate matches valid_combos() ({len(valid_combos())} combos).")
        return 0
    print("MISMATCH between clingo and Python combo gates.")
    return 1


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short rhyming story for children about a new {f["kit"].version} and prevention.',
        f'Tell a gentle story where {f["child"].id} makes a {f["kit"].topic} rhyme at {world.setting.place} without getting too spazzy.',
        f'Write a small story that includes the words “version” and “prevention” and ends with a happy rhyme.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    kit = f["kit"]
    return [
        QAItem(
            question=f"What did {child.id} want to make?",
            answer=f"{child.id} wanted to make a new {kit.version} of a rhyme about {kit.topic}."
        ),
        QAItem(
            question=f"Who helped {child.id} stay calm?",
            answer=f"{helper.label.capitalize()} helped by reminding {child.id} about prevention and a steady beat."
        ),
        QAItem(
            question=f"What did {child.id} do to stop the spaz-like fuss?",
            answer=f"{child.id} took a slow breath, used prevention, and tried the rhyme again."
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with a neat new version, a bright page, and {child.id} feeling proud."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a version?",
            answer="A version is one way of making something, like a new take on a song, rhyme, or story."
        ),
        QAItem(
            question="What is prevention?",
            answer="Prevention means doing something early to stop a problem before it starts."
        ),
        QAItem(
            question="What does a steady beat help with?",
            answer="A steady beat can help you keep time, remember words, and say a rhyme more smoothly."
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.kind:7}/{e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], RHYME_KITS[params.kit], params.name, params.helper, params.trait)
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/2."))
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} compatible combos:\n")
        for place, kit in combos:
            print(f"  {place:12} {kit}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in SETTINGS:
            for kit in RHYME_KITS:
                params = StoryParams(
                    place=place,
                    kit=kit,
                    name=random.Random(base_seed + len(samples)).choice(GREETINGS),
                    helper=random.Random(base_seed + len(samples) + 1).choice([h[0] for h in HELPERS]),
                    trait=random.Random(base_seed + len(samples) + 2).choice(TRAITS),
                    seed=base_seed + len(samples),
                )
                samples.append(generate(params))
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

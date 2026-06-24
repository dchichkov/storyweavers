#!/usr/bin/env python3
"""
storyworlds/worlds/snicker_railing_systematic_lesson_learned_teamwork_repetition.py
===================================================================================

A small, self-contained storyworld about a strange railing, a few nervous
snickers, and a lesson learned through teamwork and repetition.

The tale style leans ghost-story: dim hallways, a creaky stair rail, a careful
little mystery, and a gentle ending where the characters prove they can face the
problem together.
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

TOPIC_WORDS = ("snicker", "railing", "systematic")


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the old house"
    affords: set[str] = field(default_factory=lambda: {"inspect", "listen", "shine_light"})


@dataclass
class StoryParams:
    name: str
    helper_name: str
    parent_name: str
    seed: Optional[int] = None


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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        return clone


def _r_snicker(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("Child")
    rail = world.entities.get("Railing")
    if not child or not rail:
        return out
    if child.memes.get("uneasy", 0.0) < 1.0:
        return out
    sig = ("snicker",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    rail.memes["mysterious"] = rail.memes.get("mysterious", 0.0) + 1
    out.append("A small snicker seemed to float up from the railing.")
    return out


def _r_systematic(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("Child")
    helper = world.entities.get("Helper")
    rail = world.entities.get("Railing")
    if not child or not helper or not rail:
        return out
    if child.memes.get("determination", 0.0) < 1.0 or helper.memes.get("teamwork", 0.0) < 1.0:
        return out
    if rail.meters.get("checked", 0.0) < 3.0:
        return out
    sig = ("systematic",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    rail.memes["safe"] = rail.memes.get("safe", 0.0) + 1
    out.append("They checked every board in a systematic way.")
    return out


def _r_repetition(world: World) -> list[str]:
    out: list[str] = []
    rail = world.entities.get("Railing")
    helper = world.entities.get("Helper")
    if not rail or not helper:
        return out
    if rail.meters.get("checked", 0.0) < 2.0:
        return out
    sig = ("repetition",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    helper.memes["calm"] = helper.memes.get("calm", 0.0) + 1
    out.append("Again and again, they listened for the same creak until the sound made sense.")
    return out


CAUSAL_RULES = [_r_snicker, _r_repetition, _r_systematic]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def build_story(params: StoryParams) -> World:
    setting = Setting()
    world = World(setting)
    child = world.add(Entity(id="Child", kind="character", type="boy", label=params.name))
    helper = world.add(Entity(id="Helper", kind="character", type="girl", label=params.helper_name))
    parent = world.add(Entity(id="Parent", kind="character", type="mother", label=params.parent_name))
    rail = world.add(Entity(id="Railing", kind="thing", type="railing", label="the railing"))

    child.memes["uneasy"] = 1.0
    helper.memes["teamwork"] = 1.0
    child.memes["determination"] = 1.0

    world.say(
        f"Late at night in {setting.place}, {child.label} heard a tiny snicker near {rail.label}."
    )
    world.say(
        f"The old hallway was dim, and {rail.label} gave one soft creak every time the floorboards shifted."
    )
    world.para()

    world.say(
        f"{child.label} wanted to look, but the sound made {child.pronoun('object')} hesitate."
    )
    world.say(
        f"{helper.label} held up a lantern and said they should be systematic, one step at a time."
    )
    rail.meters["checked"] = 1.0

    world.para()
    world.say(
        f"So the two of them began to inspect {rail.label} together."
    )
    world.say(
        f"{child.label} tapped the first post while {helper.label} listened, then they switched and did it again."
    )
    rail.meters["checked"] = 2.0
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"They kept going, careful and quiet, until the last loose nail was found."
    )
    rail.meters["checked"] = 3.0
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"In the end, {parent.label} smiled and tightened the nail, and the railing stopped sounding spooky."
    )
    world.say(
        f"{child.label} laughed at the little snicker, because it had only been the wind under the rail."
    )
    world.say(
        f"{child.label} learned that teamwork and repetition can turn a ghostly worry into an answer."
    )

    world.facts.update(
        child=child,
        helper=helper,
        parent=parent,
        rail=rail,
        setting=setting,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    return [
        f"Write a gentle ghost story for a small child about {child.label}, a snicker, and a railing.",
        "Tell a short story where teamwork and repetition help solve a spooky hallway mystery.",
        "Write a simple story in which a strange sound at a railing turns out not to be a real ghost.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    parent = f["parent"]
    rail = f["rail"]
    return [
        QAItem(
            question=f"Why did {child.label} feel nervous near {rail.label}?",
            answer=f"{child.label} felt nervous because a tiny snicker seemed to come from {rail.label}, and the hallway was dark and spooky.",
        ),
        QAItem(
            question=f"How did {child.label} and {helper.label} solve the problem?",
            answer=f"They solved it by working together in a systematic way, checking {rail.label} again and again until they found the loose nail.",
        ),
        QAItem(
            question=f"What did {child.label} learn at the end of the story?",
            answer=f"{child.label} learned that teamwork and repetition can help turn a scary mystery into something simple and safe.",
        ),
        QAItem(
            question=f"Who fixed the last problem with {rail.label}?",
            answer=f"{parent.label} fixed the last problem by tightening the loose nail after the children found it.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a railing?",
            answer="A railing is a bar or fence that people can hold onto, especially on stairs or porches.",
        ),
        QAItem(
            question="What does systematic mean?",
            answer="Systematic means doing something in an orderly, careful way, one step after another.",
        ),
        QAItem(
            question="What is repetition?",
            answer="Repetition means doing the same action again and again, which can help you notice small details.",
        ),
        QAItem(
            question="What is a snicker?",
            answer="A snicker is a small quiet laugh, often the kind that sounds sneaky or silly.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("topic", "snicker"),
            asp.fact("topic", "railing"),
            asp.fact("topic", "systematic"),
            asp.fact("feature", "lesson_learned"),
            asp.fact("feature", "teamwork"),
            asp.fact("feature", "repetition"),
            asp.fact("place", "old_house"),
            asp.fact("affords", "old_house", "inspect"),
            asp.fact("affords", "old_house", "listen"),
            asp.fact("affords", "old_house", "shine_light"),
        ]
    )


ASP_RULES = r"""
topic(snicker).
topic(railing).
topic(systematic).
feature(lesson_learned).
feature(teamwork).
feature(repetition).

needs_repetition(repetition).
needs_teamwork(teamwork).
has_lesson(lesson_learned) :- needs_repetition(repetition), needs_teamwork(teamwork).

story_ok :- topic(snicker), topic(railing), topic(systematic), has_lesson(lesson_learned).
#show story_ok/0.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show story_ok/0."))
    ok = any(sym.name == "story_ok" for sym in model)
    if ok:
        print("OK: ASP twin recognizes the story world.")
        return 0
    print("MISMATCH: ASP twin failed.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world about a snickering railing and a lesson learned.")
    ap.add_argument("--name")
    ap.add_argument("--helper-name")
    ap.add_argument("--parent-name")
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


GIRL_NAMES = ["Mina", "Ivy", "Nora", "Luna", "Ada", "Ruby"]
BOY_NAMES = ["Eli", "Finn", "Owen", "Theo", "Milo", "Jude"]
PARENT_NAMES = ["Mom", "Dad", "Aunt June", "Uncle Ben"]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    name = args.name or rng.choice(BOY_NAMES)
    helper_name = args.helper_name or rng.choice(GIRL_NAMES)
    parent_name = args.parent_name or rng.choice(PARENT_NAMES)
    return StoryParams(name=name, helper_name=helper_name, parent_name=parent_name)


def generate(params: StoryParams) -> StorySample:
    world = build_story(params)
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
        print(asp_program("#show story_ok/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show story_ok/0."))
        print("story_ok" if any(sym.name == "story_ok" for sym in model) else "no model")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        params = StoryParams(name="Mina", helper_name="Luna", parent_name="Mom")
        samples = [generate(params)]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

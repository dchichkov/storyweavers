#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/colonial_bow_soot_transformation_repetition_bedtime_story.py
===========================================================================================

A small bedtime-style storyworld built from the seed words **colonial**, **bow**,
and **soot**, with two core instruments:

* **Transformation**: a soot-darkened bow becomes clean and bright again.
* **Repetition**: a calming bedtime rhythm repeats while the child helps.

The setting is a quiet colonial house at night. A child notices a little black
soot on a bow, worries about it, then helps a grown-up clean and reshape the
bow before bedtime. The ending image proves the change by showing the bow
resting neatly, clean and ready for tomorrow.

The domain is intentionally tiny and classical: one room, one child, one adult,
one treasured bow, and one soft cleaning ritual.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
CLEAN_GOAL = 2.0
SOOT_MESS = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother"}
        male = {"boy", "father", "dad", "man", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "grandmother": "grandma", "grandfather": "grandpa"}.get(self.type, self.type)


@dataclass
class StoryParams:
    name: str
    gender: str
    adult: str
    room: str
    bow_kind: str
    scent: str
    seed: Optional[int] = None


@dataclass
class Setting:
    id: str
    room_phrase: str
    colonial_detail: str
    bedtime_detail: str


@dataclass
class Bow:
    id: str
    label: str
    phrase: str
    ribbon: str
    shape: str
    color: str
    can_transform: bool = True


@dataclass
class SootSource:
    id: str
    label: str
    phrase: str
    leaves_soot: bool = True


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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_soot_settles(world: World) -> list[str]:
    out: list[str] = []
    bow = world.entities.get("bow")
    if not bow or bow.meters["soot"] < THRESHOLD:
        return out
    sig = ("soot", bow.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    bow.memes["worry"] += 1
    out.append("__soft_worry__")
    return out


def _r_cleaning_progress(world: World) -> list[str]:
    out: list[str] = []
    bow = world.entities.get("bow")
    if not bow or bow.meters["soot"] <= 0:
        return out
    sig = ("clean_progress", bow.id, round(bow.meters["soot"], 1))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    out.append("__clean_progress__")
    return out


CAUSAL_RULES = [Rule("soot_settles", _r_soot_settles), Rule("cleaning_progress", _r_cleaning_progress)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            if not s.startswith("__"):
                world.say(s)
    return produced


def make_soot(world: World, bow: Entity, source: SootSource) -> None:
    bow.meters["soot"] += 1
    bow.memes["surprise"] += 1
    source_ent = world.entities[source.id]
    source_ent.meters["used"] += 1
    propagate(world, narrate=False)


def wash(world: World, bow: Entity) -> None:
    bow.meters["soot"] = max(0.0, bow.meters["soot"] - 1.0)
    bow.meters["clean"] += 1
    bow.memes["hope"] += 1
    propagate(world, narrate=False)


def reshape(world: World, bow: Entity) -> None:
    if bow.meters["soot"] > 0:
        bow.meters["clean"] += 1
    bow.meters["straight"] += 1
    bow.memes["calm"] += 1


def repeat_rhythm(world: World, child: Entity, adult: Entity) -> None:
    child.memes["calm"] += 1
    adult.memes["calm"] += 1
    world.say('The grown-up said, "Slowly, softly, we can clean it."')
    world.say('So the child hummed, "Wash and wait, wash and wait."')
    world.say('Again the grown-up said, "Slowly, softly, we can clean it."')
    world.say('Again the child hummed, "Wash and wait, wash and wait."')


SETTINGS = {
    "attic_room": Setting("attic_room", "the attic room", "with narrow beams and a tiny window", "where the lamp made a soft gold circle"),
    "front_parlor": Setting("front_parlor", "the front parlor", "with polished wood and a quiet fireplace", "where the mantel clock ticked like a lullaby"),
}

BOWS = {
    "hair_bow": Bow("bow", "bow", "a ribbon bow", "ribbon", "soft", "blue"),
    "gift_bow": Bow("bow", "bow", "a gift bow", "paper", "neat", "red"),
}

SOOT = {
    "lamp_soot": SootSource("lamp", "lamp", "the old lamp wick"),
    "chimney_soot": SootSource("chimney", "chimney", "the fireplace chimney"),
}

TRAITS = ["careful", "gentle", "curious", "sleepy", "patient"]
NAMES = {
    "girl": ["Mina", "Clara", "Lily", "Nora"],
    "boy": ["Eli", "Theo", "Noah", "Sam"],
}


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, b, t) for s in SETTINGS for b in BOWS for t in SOOT]


def explain_rejection() -> str:
    return "(No story: this tiny world needs a bow, a little soot source, and a room to clean in.)"


def outcome_of(params: StoryParams) -> str:
    return "transformed"


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for bid in BOWS:
        lines.append(asp.fact("bow", bid))
    for tid in SOOT:
        lines.append(asp.fact("soot_source", tid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, B, T) :- setting(S), bow(B), soot_source(T).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        print("MISMATCH in valid_combos")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))
        return 1
    print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        assert sample.story
        print("OK: default generate smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime storyworld: colonial, bow, soot, and a soft transformation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--bow", choices=BOWS)
    ap.add_argument("--soot", choices=SOOT)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=["mother", "father", "grandmother", "grandfather"])
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
    if args.setting and args.bow and args.soot is None:
        pass
    if args.setting and args.bow and args.soot:
        if (args.setting, args.bow, args.soot) not in valid_combos():
            raise StoryError(explain_rejection())
    setting = args.setting or rng.choice(list(SETTINGS))
    bow = args.bow or rng.choice(list(BOWS))
    soot = args.soot or rng.choice(list(SOOT))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    adult = args.adult or rng.choice(["mother", "grandmother", "father"])
    return StoryParams(name=name, gender=gender, adult=adult, room=setting, bow_kind=bow, scent=soot)


def tell(setting: Setting, bow: Bow, soot: SootSource, child: Entity, adult: Entity) -> World:
    world = World()
    world.add(child)
    world.add(adult)
    bow_ent = world.add(Entity(id="bow", kind="thing", type="thing", label="bow"))
    lamp = world.add(Entity(id=soot.id, kind="thing", type="thing", label=soot.label))
    bow_ent.meters["clean"] = 0.0
    child.memes["sleepy"] += 1

    world.say(
        f"In the colonial house, {child.id} and {adult.label_word} moved softly through {setting.room_phrase}. "
        f"{setting.colonial_detail} {setting.bedtime_detail}."
    )
    world.say(
        f"On the table sat {bow.phrase}, and a little soot clung to it like a dark dust."
    )
    world.say(
        f'{child.id} touched the bow and whispered, "Why is the {bow.label} so dark?"'
    )

    world.para()
    make_soot(world, bow_ent, soot)
    world.say(
        f"{adult.label_word.capitalize()} smiled and nodded. 'Because soot makes things look old and gray,' "
        f"{adult.pronoun()} said."
    )
    world.say(
        f'"But we can clean it," {adult.pronoun()} said, "slowly and softly."'
    )
    repeat_rhythm(world, child, adult)

    world.para()
    wash(world, bow_ent)
    reshape(world, bow_ent)
    wash(world, bow_ent)
    world.say(
        f"{child.id} dipped the cloth again, and again, until the soot faded away."
    )
    world.say(
        f"The bow changed a little each time: dark, lighter, bright; flat, neat, ready."
    )
    world.say(
        f'At last {adult.label_word} tied the {bow.label} neatly, and the little bow looked fresh again.'
    )
    world.say(
        f'{child.id} yawned and smiled. "Wash and wait," {child.id} murmured once more, "wash and wait."'
    )
    world.say(
        f"Then the clean {bow.label} rested beside the bed, and the colonial room grew quiet and warm."
    )
    world.facts.update(
        child=child,
        adult=adult,
        bow=bow_ent,
        setting=setting,
        soot=soot,
        transformed=bow_ent.meters["clean"] >= CLEAN_GOAL and bow_ent.meters["soot"] <= 0,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a bedtime story that uses the words "colonial", "bow", and "soot".',
        f'Tell a gentle story where {f["child"].id} notices soot on a bow in a colonial house and helps a grown-up clean it before bed.',
        'Write a soft repetition story where a child and adult repeat a calming phrase while something dark becomes clean again.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    bow = f["bow"]
    answers = [
        QAItem(
            question="What was the child worried about?",
            answer=f'{child.id} was worried about the soot on the bow. It looked dark at first, but the grown-up showed that it could be cleaned.'
        ),
        QAItem(
            question="How did the bow change?",
            answer="It changed from dark and dusty to clean and neat. The washing happened twice, and that repeated care helped the bow become bright again."
        ),
        QAItem(
            question="What repeated in the story?",
            answer='The words "Wash and wait, wash and wait" repeated. That gentle repetition made the cleaning feel calm and helped the child settle for bedtime.'
        ),
    ]
    return answers


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is soot?", "Soot is a black powder left behind by smoke. It can make things look gray or dirty until they are cleaned."),
        QAItem("What does it mean to transform something?", "To transform something means to change it into a different state. In this story, the bow changed from sooty to clean."),
        QAItem("Why can repeating a calm phrase help at bedtime?", "Repeating a calm phrase can help a child feel settled and safe. The rhythm makes the evening feel peaceful and steady."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if e.role:
            parts.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(parts)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.room]
    bow = BOWS[params.bow_kind]
    soot = SOOT[params.scent]
    child = Entity(id=params.name, kind="character", type=params.gender, role="child")
    adult = Entity(id=params.adult, kind="character", type=params.adult, label=params.adult)
    world = tell(setting, bow, soot, child, adult)
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


CURATED = [
    StoryParams("Mina", "girl", "grandmother", "attic_room", "hair_bow", "lamp_soot"),
    StoryParams("Eli", "boy", "mother", "front_parlor", "gift_bow", "chimney_soot"),
]


def asp_verify_run() -> int:
    return asp_verify()


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify_run())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid combos:")
        for row in asp_valid_combos():
            print(" ", row)
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
            header = f"### {p.name}: colonial bow soot bedtime story"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

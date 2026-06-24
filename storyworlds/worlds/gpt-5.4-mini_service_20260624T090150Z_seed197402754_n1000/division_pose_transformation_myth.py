#!/usr/bin/env python3
"""
storyworlds/worlds/division_pose_transformation_myth.py
========================================================

A small myth-style storyworld about a sacred division, a chosen pose, and a
transformation that changes what is seen and what is felt.

The seed tale imagined for this world:
---
In an old valley, a young helper named Iri served the Weaver of Dawn. The Weaver
kept a holy mirror that could split one clear thing into two true shapes. One
festival night, the valley people brought a cracked statue to the shrine. They
asked for a sign, but the statue stood crooked and sad.

Iri wanted to help. The Weaver said the statue must first be given the right
pose: one side bowed toward the earth, the other raised toward the sky. Then the
mirror could divide the crack into two paths and turn ruin into a new blessing.
Iri learned the pose, held still, and watched the old statue change. At last the
valley saw two shining images where one broken idol had been before.

Causal state updates:
---
    sacred division enacted      -> a relic or image can split into two true forms
    chosen pose held             -> body becomes still, awe increases, fear drops
    transformation succeeds      -> brokenness decreases, wonder increases
    failed pose                  -> strain and doubt rise, transformation stalls
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    pose: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "goddess", "queen", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "god", "father", "priest"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the shrine valley"


@dataclass
class Transformation:
    id: str
    title: str
    source: str
    result_a: str
    result_b: str
    trigger_pose: str
    requires_division: bool = True
    wonder: str = "shining"


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

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


def _inc(ent: Entity, key: str, n: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + n


def _m(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def _e(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


SETTINGS = {
    "shrine_valley": Setting(place="the shrine valley"),
    "moon_temple": Setting(place="the moon temple"),
    "river_grove": Setting(place="the river grove"),
}

TRANSFORMATIONS = {
    "idol_twins": Transformation(
        id="idol_twins",
        title="the divided idol",
        source="a cracked statue",
        result_a="a dawn-faced idol",
        result_b="a moon-faced idol",
        trigger_pose="the right pose",
        wonder="bright",
    ),
    "crown_split": Transformation(
        id="crown_split",
        title="the split crown",
        source="a heavy crown",
        result_a="a sun crown",
        result_b="a star crown",
        trigger_pose="the balanced pose",
        wonder="glittering",
    ),
    "mask_double": Transformation(
        id="mask_double",
        title="the two masks",
        source="a plain mask",
        result_a="a laughing mask",
        result_b="a quiet mask",
        trigger_pose="the still pose",
        wonder="glowing",
    ),
}

NAMES = ["Iri", "Mara", "Soren", "Lysa", "Tavi", "Nilo", "Asha", "Kian"]
LEAD_TYPES = {"child", "boy", "girl", "apprentice"}
HELPER_TYPES = {"priest", "priestess", "elder", "weaver", "guardian"}
TRAITS = ["brave", "careful", "curious", "devoted", "gentle"]


def valid_combos() -> list[tuple[str, str]]:
    return [(s, t) for s in SETTINGS for t in TRANSFORMATIONS]


@dataclass
class StoryParams:
    setting: str
    transformation: str
    name: str
    lead_type: str
    helper_type: str
    trait: str
    seed: Optional[int] = None


class StoryWorld(World):
    pass


def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, tr in TRANSFORMATIONS.items():
        lines.append(asp.fact("transformation", tid))
        lines.append(asp.fact("source", tid, tr.source))
        lines.append(asp.fact("result", tid, tr.result_a))
        lines.append(asp.fact("result", tid, tr.result_b))
        lines.append(asp.fact("trigger_pose", tid, tr.trigger_pose))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,T) :- setting(S), transformation(T).
needs_pose(T,P) :- trigger_pose(T,P).
has_division(T) :- transformation(T), source(T,_), result(T,_), result(T,_).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a, p = set(asp_valid_combos()), set(valid_combos())
    if a == p:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - p:
        print("  only in clingo:", sorted(a - p))
    if p - a:
        print("  only in python:", sorted(p - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic story world of division, pose, and transformation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--transformation", choices=TRANSFORMATIONS)
    ap.add_argument("--name")
    ap.add_argument("--lead-type", choices=sorted(LEAD_TYPES))
    ap.add_argument("--helper-type", choices=sorted(HELPER_TYPES))
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.transformation:
        combos = [c for c in combos if c[1] == args.transformation]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, transformation = rng.choice(sorted(combos))
    lead_type = args.lead_type or rng.choice(sorted(LEAD_TYPES))
    helper_type = args.helper_type or rng.choice(sorted(HELPER_TYPES))
    trait = args.trait or rng.choice(TRAITS)
    name = args.name or rng.choice(NAMES)
    return StoryParams(setting=setting, transformation=transformation, name=name,
                       lead_type=lead_type, helper_type=helper_type, trait=trait)


def _introduce(world: World, hero: Entity, helper: Entity, tr: Transformation) -> None:
    world.say(
        f"In {world.setting.place}, {hero.id} was a {hero.memes.get('trait', 'young')} {hero.type} "
        f"who served beside {helper.label} at the old shrine."
    )
    world.say(
        f"Before the night of signs, the people brought {tr.source}, hoping the gods would answer."
    )


def _pose(world: World, hero: Entity, tr: Transformation) -> None:
    hero.pose = tr.trigger_pose
    _inc(hero, "stillness")
    _inc(hero, "awe")
    world.say(
        f"{hero.id} learned {tr.trigger_pose} and held very still, one hand down and one hand lifted."
    )


def _division(world: World, tr: Transformation, relic: Entity) -> None:
    if _m(relic, "fracture") < THRESHOLD:
        return
    sig = ("divide", relic.id, tr.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    _inc(relic, "split")
    _inc(relic, "wonder")
    world.say(
        f"The holy mirror answered, and the crack divided into two paths."
    )


def _transform(world: World, tr: Transformation, relic: Entity) -> None:
    if _m(relic, "split") < THRESHOLD or world.facts.get("pose") != tr.trigger_pose:
        return
    sig = ("transform", relic.id, tr.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    relic.label = tr.result_a + " and " + tr.result_b
    _inc(relic, "renewed")
    _inc(relic, "wonder", 2)
    world.say(
        f"Then the broken image changed: one side rose as {tr.result_a}, and the other as {tr.result_b}."
    )


def tell(setting: Setting, tr: Transformation, name: str, lead_type: str, helper_type: str, trait: str) -> World:
    world = StoryWorld(setting)
    hero = world.add(Entity(id=name, kind="character", type=lead_type, label=name))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, label=f"the {helper_type}"))
    relic = world.add(Entity(id="Relic", kind="thing", type="idol", label=tr.source, phrase=tr.source))
    relic.meters["fracture"] = 1.0
    hero.memes["trait"] = trait
    world.facts.update(hero=hero, helper=helper, relic=relic, transformation=tr, pose=tr.trigger_pose)

    world.say(
        f"{hero.id} was a {trait} {lead_type} who watched the shrine fires and listened for omens."
    )
    world.say(
        f"The {helper_type} told {hero.id} that every true change began with a right pose."
    )
    world.para()
    _pose(world, hero, tr)
    world.say(
        f"At the altar, {hero.id} faced {tr.source} and waited for the sacred division."
    )
    _division(world, tr, relic)
    _transform(world, tr, relic)
    world.para()
    if _m(relic, "renewed") >= THRESHOLD:
        world.say(
            f"By dawn, the shrine no longer held one broken thing, but two bright forms."
        )
        world.say(
            f"{hero.id} smiled because the old crack had become a blessing."
        )
        world.facts["resolved"] = True
    else:
        world.say(
            f"The mirror stayed quiet, and the old shape remained unchanged."
        )
        world.facts["resolved"] = False
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    tr = f["transformation"]
    return [
        f"Write a mythic story about {hero.id} learning {tr.trigger_pose} so a sacred division can transform {tr.source}.",
        f"Tell a child-friendly myth where a {hero.type} named {hero.id} helps the shrine turn {tr.source} into {tr.result_a} and {tr.result_b}.",
        "Write a short myth about pose, division, and a wonder-filled transformation at a shrine.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    tr = f["transformation"]
    relic = f["relic"]
    helper = f["helper"]
    return [
        QAItem(
            question=f"Who learned {tr.trigger_pose} in the story?",
            answer=f"{hero.id} learned {tr.trigger_pose} from {helper.label} at the shrine.",
        ),
        QAItem(
            question=f"What was divided before the transformation happened?",
            answer=f"{relic.phrase} was divided, and its crack split into two true paths.",
        ),
        QAItem(
            question=f"What did the sacred change become at the end?",
            answer=f"It became {tr.result_a} and {tr.result_b}, so one broken image turned into two shining forms.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pose?",
            answer="A pose is a way of holding the body still or arranging the body for a special purpose, like a dance, a picture, or a ritual.",
        ),
        QAItem(
            question="What does division mean?",
            answer="Division means splitting one thing into two or more parts.",
        ),
        QAItem(
            question="What is transformation?",
            answer="Transformation means changing from one form into another form.",
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
        if e.pose:
            bits.append(f"pose={e.pose!r}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        TRANSFORMATIONS[params.transformation],
        params.name,
        params.lead_type,
        params.helper_type,
        params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


CURATED = [
    StoryParams(setting="shrine_valley", transformation="idol_twins", name="Iri", lead_type="child", helper_type="weaver", trait="curious"),
    StoryParams(setting="moon_temple", transformation="crown_split", name="Mara", lead_type="apprentice", helper_type="priestess", trait="devoted"),
    StoryParams(setting="river_grove", transformation="mask_double", name="Soren", lead_type="boy", helper_type="elder", trait="careful"),
]


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
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid/2."))
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} compatible combos:\n")
        for s, t in combos:
            print(f"  {s:14} {t}")
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
            header = f"### {p.name}: {p.transformation} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

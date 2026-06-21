#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/dandelion_general_ize_repetition_animal_story.py
=================================================================================

A tiny animal-story world about a few animals learning to general-ize from one
spotty lesson about dandelions.

Seed prompt
-----------
Write a story that includes the following words and narrative instruments.
Words: dandelion, general-ize
Features: Repetition
Style: Animal Story

World premise
-------------
A little animal notices one dandelion puff drifting everywhere on the wind and
tries to general-ize that all fluff must be the same. A parent or helper animal
shows that some fluff is harmless, some is sticky, and the right way to learn is
to look closely instead of over-generalizing. The story ends with a concrete
change in behavior: the animals sort, compare, and choose a better habit.

This script follows the storyworld contract:
- typed entities with meters and memes
- state-driven prose with a real turn and resolution
- three Q&A sets grounded in simulated state
- a Python reasonableness gate plus an inline ASP twin
- support for --verify, --asp, --show-asp, --json, --qa, --trace, --all, -n

The world is intentionally small and child-facing, with repetition in the prose
so the key lesson can echo without becoming a frozen template.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2

ANIMAL_PRONOUNS = {
    "female": {"subject": "she", "object": "her", "possessive": "her"},
    "male": {"subject": "he", "object": "him", "possessive": "his"},
    "neutral": {"subject": "they", "object": "them", "possessive": "their"},
}


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
    helpful: bool = False
    sticky: bool = False
    fluffy: bool = False

    def pronoun(self, case: str = "subject") -> str:
        gender = self.attrs.get("gender", "neutral")
        return ANIMAL_PRONOUNS.get(gender, ANIMAL_PRONOUNS["neutral"])[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class Animal:
    id: str
    species: str
    gender: str
    label: str
    curious: bool = True
    cautious: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    helper: bool = False

    def pronoun(self, case: str = "subject") -> str:
        return ANIMAL_PRONOUNS.get(self.gender, ANIMAL_PRONOUNS["neutral"])[case]

    @property
    def label_word(self) -> str:
        return self.label


@dataclass
class DandelionPatch:
    id: str
    label: str
    place: str
    wind: str
    puffs: int
    sticky: bool = False
    fluffy: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Lesson:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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

    def animals(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "animal"]

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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_swirl(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters["startled"] < THRESHOLD:
            continue
        sig = ("swirl", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for a in world.animals():
            a.memes["confused"] += 1
        out.append("__repetition__")
    return out


CAUSAL_RULES = [Rule("swirl", "social", _r_swirl)]


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


def has_hazard(patch: DandelionPatch, touch: str) -> bool:
    return patch.fluffy and touch in {"grab", "blow", "shout"}


def sensible_lessons() -> list[Lesson]:
    return [l for l in LESSONS.values() if l.sense >= SENSE_MIN]


def is_reasonable(patch: DandelionPatch, lesson: Lesson) -> bool:
    return patch.fluffy and lesson.power >= 2


def lesson_outcome(patch: DandelionPatch, lesson: Lesson, delay: int) -> str:
    return "revised" if lesson.power >= patch.puffs + delay else "stuck"


def explain_rejection(patch: DandelionPatch) -> str:
    return f"(No story: {patch.label} is not a good lesson scene here.)"


def explain_lesson(rid: str) -> str:
    l = LESSONS[rid]
    return f"(Refusing lesson '{rid}': it is too weak for this world.)"


def _do_startle(world: World, patch: Entity) -> None:
    patch.meters["startled"] += 1
    propagate(world, narrate=False)


def _do_touch(world: World, patch: DandelionPatch) -> None:
    _do_startle(world, world.get("patch"))
    world.say(
        f"{patch.label} was there, and there, and there again. The dandelion puff "
        f"bounced on the wind, soft and light and soft and light."
    )


def setup(world: World, a: Entity, b: Entity, patch: DandelionPatch) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"On a breezy morning, {a.id} and {b.id} padded across the meadow. "
        f"Near the path stood {patch.place}, where a dandelion puff had gone "
        f"round and round in the grass."
    )
    world.say(
        f'"{a.id} saw a dandelion," {a.id} said. "{a.id} saw a dandelion again." '
        f'{b.id} laughed, because the little song kept repeating.'
    )


def wonder(world: World, a: Entity, b: Entity, patch: DandelionPatch) -> None:
    a.memes["wonder"] += 1
    world.say(
        f"{a.id} tilted {a.pronoun('possessive')} head. "
        f'"If one dandelion puff is little and soft, then all fluff must be the same," '
        f"{a.id} said. " f'"Can we general-ize that?"'
    )
    world.say(
        f"{b.id} blinked slowly. "{b.id} knew that one look is not always enough."
    )


def warn(world: World, helper: Entity, a: Entity, patch: DandelionPatch) -> None:
    helper.memes["care"] += 1
    world.say(
        f'{helper.id} sat beside the grass and said, "Easy now. One dandelion '
        f'does not teach the whole meadow."'
    )
    world.say(
        f'"Look closely, look closely," {helper.id} said. "Some fluffy bits drift, '
        f'some fluffy bits stick, and some fluffy bits are tucked away."'
    )


def repeat_test(world: World, patch: DandelionPatch) -> None:
    patch_entity = world.get("patch")
    patch_entity.meters["startled"] += 1
    patch_entity.meters["shown"] += 1
    world.say(
        f"The puff lifted, then settled, then lifted again. It was the same puff, "
        f"but not the same lesson."
    )


def compare(world: World, a: Entity, b: Entity, helper: Entity) -> None:
    a.memes["care"] += 1
    b.memes["care"] += 1
    world.say(
        f"{helper.id} showed {a.id} a dry seed head, a sticky burr, and a downy "
        f"thistle tuft. Again and again, they compared one thing with another."
    )
    world.say(
        f'"This one blows away. This one sticks. This one pokes." '
        f"{helper.id} tapped each one with a paw."
    )


def revise(world: World, a: Entity, b: Entity, lesson: Lesson) -> None:
    a.memes["understanding"] += 1
    b.memes["understanding"] += 1
    world.say(
        f"{a.id} nodded. " f'"I should not over-general-ize from one tiny puff," '
        f"{a.id} said."
    )
    world.say(
        f'"I should look, and look again." {b.id} repeated it, softly and happily."
    )


def ending(world: World, a: Entity, b: Entity, patch: DandelionPatch) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"Then they went on, stepping carefully through the meadow. A dandelion "
        f"seed drifted past their noses, and this time they smiled, compared, and "
        f"kept walking."
    )
    world.say(
        f"One dandelion, two dandelions, three dandelions -- the wind still sang, "
        f"but the little animals listened better now."
    )


def tell(kind_a: str, kind_b: str, helper_kind: str, patch: DandelionPatch,
         lesson: Lesson, delay: int = 0) -> World:
    world = World()
    a = world.add(Entity(
        id="Milo", kind="animal", type=kind_a, label="Milo",
        attrs={"gender": "male"},
    ))
    b = world.add(Entity(
        id="Pip", kind="animal", type=kind_b, label="Pip",
        attrs={"gender": "female"},
    ))
    helper = world.add(Entity(
        id="Mama", kind="animal", type=helper_kind, label="Mama",
        attrs={"gender": "female"}, role="helper", helpful=True,
    ))
    patch_ent = world.add(Entity(
        id="patch", kind="thing", type="patch", label=patch.label,
        fluffy=patch.fluffy, sticky=patch.sticky,
    ))

    setup(world, a, b, patch)
    world.para()
    wonder(world, a, b, patch)
    warn(world, helper, a, patch)
    repeat_test(world, patch)

    if lesson_outcome(patch, lesson, delay) == "revised":
        world.para()
        compare(world, a, b, helper)
        revise(world, a, b, lesson)
        world.para()
        ending(world, a, b, patch)
        outcome = "revised"
    else:
        world.para()
        world.say(
            f"{a.id} tried to general-ize too fast, and the idea stuck in the "
            f"wrong place like a burr on fur."
        )
        world.say(
            f"But {helper.id} kept the animals safe, and they went back to look "
            f"again before deciding anything."
        )
        outcome = "stuck"

    world.facts.update(
        a=a, b=b, helper=helper, patch_cfg=patch, patch=patch_ent, lesson=lesson,
        outcome=outcome, delay=delay
    )
    return world


PATCHES = {
    "meadow": DandelionPatch(id="meadow", label="the meadow", place="the meadow", wind="breezy", puffs=3, tags={"dandelion"}),
    "path": DandelionPatch(id="path", label="the path", place="the path", wind="windy", puffs=2, tags={"dandelion"}),
    "hill": DandelionPatch(id="hill", label="the little hill", place="the little hill", wind="soft", puffs=4, tags={"dandelion"}),
}

LESSONS = {
    "compare": Lesson(id="compare", sense=3, power=3,
                      text="showed them how to compare one thing with another",
                      fail="tried to compare too quickly, but the lesson did not stick",
                      qa_text="showed them how to compare one thing with another",
                      tags={"generalize"}),
    "look_again": Lesson(id="look_again", sense=3, power=4,
                         text="told them to look again before deciding",
                         fail="told them to look again, but they were too hasty to listen",
                         qa_text="told them to look again before deciding",
                         tags={"generalize"}),
    "slow_down": Lesson(id="slow_down", sense=2, power=2,
                        text="asked them to slow down and notice differences",
                        fail="asked them to slow down, but the habit was too strong",
                        qa_text="asked them to slow down and notice differences",
                        tags={"generalize"}),
    "sticky_vs_soft": Lesson(id="sticky_vs_soft", sense=3, power=4,
                             text="showed them that sticky things and soft things are not the same",
                             fail="showed them the difference, but they still mixed it up",
                             qa_text="showed them that sticky things and soft things are not the same",
                             tags={"dandelion", "generalize"}),
}

ANIMALS = [
    ("mouse", "mouse", "female"),
    ("rabbit", "rabbit", "female"),
    ("fox", "fox", "male"),
    ("bear", "bear", "male"),
    ("squirrel", "squirrel", "female"),
]

CURATED = [
    StoryParams(kind_a="rabbit", kind_b="mouse", helper_kind="bear", patch="meadow", lesson="compare", delay=0),
    StoryParams(kind_a="fox", kind_b="squirrel", helper_kind="rabbit", patch="path", lesson="look_again", delay=0),
    StoryParams(kind_a="mouse", kind_b="rabbit", helper_kind="fox", patch="hill", lesson="sticky_vs_soft", delay=0),
]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for p in PATCHES.values():
        for l in LESSONS.values():
            if is_reasonable(p, l):
                combos.append((p.id, l.id))
    return combos


@dataclass
class StoryParams:
    patch: str
    lesson: str
    kind_a: str = "rabbit"
    kind_b: str = "mouse"
    helper_kind: str = "bear"
    delay: int = 0
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write an animal story that repeats the word dandelion a few times and teaches a child not to general-ize too fast.",
        f"Tell a gentle story where {f['a'].id} sees one dandelion puff and learns to look again before deciding what all fluffy things are like.",
        "Write a short meadow story with repetition, comparison, and a kind helper animal who points out differences.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, b, helper = f["a"], f["b"], f["helper"]
    patch = f["patch_cfg"]
    lesson = f["lesson"]
    return [
        ("Who is the story about?",
         f"It is about {a.id}, {b.id}, and {helper.id} in a windy meadow. The animals are small, curious, and ready to learn."),
        ("Why did the animals need help?",
         f"{a.id} tried to general-ize from one dandelion puff too quickly. {helper.id} wanted them to look again, because one thing does not always teach the whole truth."),
        ("What changed by the end?",
         f"They learned to compare things before deciding. By the end, they noticed that one puff, one burr, and one tuft were not the same, so they handled the meadow more carefully."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a dandelion?",
         "A dandelion is a common plant with a yellow flower that turns into a fluffy white puff. The puff can blow away in the wind and make new seeds travel."),
        ("What does it mean to general-ize?",
         "To general-ize means to decide something about a whole group from a small number of examples. It can help sometimes, but it can also be wrong if you do it too fast."),
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_choice_rejection(patch: DandelionPatch, lesson: Lesson) -> str:
    if not is_reasonable(patch, lesson):
        return f"(No story: this lesson is too weak for the dandelion scene.)"
    return "(No story: invalid combination.)"


def outcome_of(params: StoryParams) -> str:
    return "revised" if params.lesson in LESSONS else "stuck"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PATCHES.items():
        lines.append(asp.fact("patch", pid))
        if p.fluffy:
            lines.append(asp.fact("fluffy", pid))
        lines.append(asp.fact("puffs", pid, p.puffs))
    for lid, l in LESSONS.items():
        lines.append(asp.fact("lesson", lid))
        lines.append(asp.fact("sense", lid, l.sense))
        lines.append(asp.fact("power", lid, l.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
reasonable(P,L) :- patch(P), lesson(L), fluffy(P), sense(L,S), sense_min(M), S >= M, power(L,Pw), Pw >= 2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reasonable/2."))
    return sorted(set(asp.atoms(model, "reasonable")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == {(a, b) for a, b in python_set}:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        print("MISMATCH between clingo and python valid_combos().")
        return 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(1)))
        _ = sample.story
        print("OK: smoke test generate() completed.")
    except Exception as exc:
        print(f"FAILED smoke test: {exc}")
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world about dandelions and learning not to general-ize too fast.")
    ap.add_argument("--patch", choices=PATCHES)
    ap.add_argument("--lesson", choices=LESSONS)
    ap.add_argument("--kind-a", dest="kind_a", choices=[a[0] for a in ANIMALS])
    ap.add_argument("--kind-b", dest="kind_b", choices=[a[0] for a in ANIMALS])
    ap.add_argument("--helper-kind", dest="helper_kind", choices=[a[0] for a in ANIMALS])
    ap.add_argument("--delay", type=int, default=None)
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
    if args.patch and args.lesson:
        if (args.patch, args.lesson) not in valid_combos():
            raise StoryError(explain_choice_rejection(PATCHES[args.patch], LESSONS[args.lesson]))
    combos = [c for c in valid_combos()
              if (args.patch is None or c[0] == args.patch)
              and (args.lesson is None or c[1] == args.lesson)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    patch, lesson = rng.choice(sorted(combos))
    return StoryParams(
        patch=patch,
        lesson=lesson,
        kind_a=args.kind_a or rng.choice([a[0] for a in ANIMALS]),
        kind_b=args.kind_b or rng.choice([a[0] for a in ANIMALS]),
        helper_kind=args.helper_kind or rng.choice([a[0] for a in ANIMALS]),
        delay=args.delay if args.delay is not None else 0,
    )


def generate(params: StoryParams) -> StorySample:
    if params.patch not in PATCHES or params.lesson not in LESSONS:
        raise StoryError("Invalid parameters.")
    world = tell(params.kind_a, params.kind_b, params.helper_kind, PATCHES[params.patch], LESSONS[params.lesson], params.delay)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("#show reasonable/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} reasonable patch/lesson combos:")
        for p, l in combos:
            print(f"  {p:8} {l}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Storyworld: slip-dim curiosity misunderstanding repetition adventure
====================================================================

A tiny standalone storyworld for an adventure-style tale about a curious child,
a dim passage, a repeated misunderstanding, and a safe resolution.

The domain is small on purpose:
- a child explores a dim place
- curiosity makes them repeat a risky action
- a companion misunderstands the plan
- a helper clears up the confusion
- the ending proves the change with a concrete image

This file is self-contained except for the shared storyworld result containers
and the optional ASP helper, both imported from the Storyweavers repo.
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
from pathlib import Path
from typing import Callable, Optional


def _bootstrap_repo_path() -> None:
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        if (parent / "results.py").exists() and (parent / "asp.py").exists():
            sys.path.insert(0, str(parent))
            return
        if (parent / "storyworlds" / "results.py").exists():
            sys.path.insert(0, str(parent / "storyworlds"))
            return


_bootstrap_repo_path()
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    id: str
    place: str
    detail: str
    dimness: int
    wind: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Curiosity:
    id: str
    question: str
    repeat_line: str
    action: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Misunderstanding:
    id: str
    confusion: str
    misunderstanding_line: str
    fixed_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Repetition:
    id: str
    count: int
    pattern: str
    consequence: str
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_echo(world: World) -> list[str]:
    out = []
    if world.facts.get("repeated", 0) < 2:
        return out
    sig = ("echo",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child = world.get("child")
    child.memes["certainty"] -= 1
    child.memes["curiosity"] += 1
    out.append("The repeated steps made the child more certain that something hidden was waiting ahead.")
    return out


def _r_confusion(world: World) -> list[str]:
    out = []
    if not world.facts.get("misunderstood"):
        return out
    sig = ("confusion",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    companion = world.get("companion")
    companion.memes["worry"] += 1
    out.append("The companion grew worried because the plan sounded like trouble.")
    return out


CAUSAL_RULES = [Rule("echo", _r_echo), Rule("confusion", _r_confusion)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
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
            world.say(s)
    return produced


def _speak_and_repeat(world: World, child: Entity, cur: Curiosity) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f'{child.id} peered into the {world.facts["setting"].place} and whispered, '
        f'"{cur.question}"'
    )
    world.say(f'Then {child.id} said it again: "{cur.repeat_line}"')


def _misread(world: World, companion: Entity, mis: Misunderstanding, child: Entity) -> None:
    companion.memes["misunderstood"] += 1
    world.say(
        f'{companion.id} frowned. "{mis.misunderstanding_line}" '
        f'But {child.id} had meant something else entirely.'
    )


def _repair(world: World, helper: Entity, mis: Misunderstanding, child: Entity) -> None:
    helper.memes["calm"] += 1
    world.say(
        f'{helper.id} held up a lantern and said, "{mis.fixed_line}" '
        f'The words made the path feel less strange at once.'
    )


def _travel(world: World, child: Entity, setting: Setting, rep: Repetition) -> None:
    child.meters["steps"] += rep.count
    world.facts["repeated"] = rep.count
    world.say(
        f'{child.id} took {rep.count} careful steps through the {setting.detail}. '
        f'{rep.pattern}'
    )
    propagate(world)


def _finish(world: World, child: Entity, helper: Entity, setting: Setting, rep: Repetition) -> None:
    child.memes["brave"] += 1
    helper.memes["pride"] += 1
    world.say(
        f'At the end, {child.id} found the way forward, and the dim place no longer '
        f'felt frightening. {rep.consequence}'
    )
    world.say(
        f'When they turned back, the lantern lit the floorboards, and the same path '
        f'looked like an adventure trail instead of a mystery.'
    )


def tell(setting: Setting, cur: Curiosity, mis: Misunderstanding, rep: Repetition,
         child_name: str = "Mia", child_gender: str = "girl",
         companion_name: str = "Ben", companion_gender: str = "boy",
         helper_name: str = "Grandpa", helper_gender: str = "man") -> World:
    world = World()
    world.facts["setting"] = setting
    world.facts["curiosity"] = cur
    world.facts["misunderstanding"] = mis
    world.facts["repetition"] = rep

    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="explorer"))
    companion = world.add(Entity(id=companion_name, kind="character", type=companion_gender, role="companion"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="guide"))
    world.add(Entity(id="lantern", kind="thing", type="tool", label="lantern"))

    world.say(
        f'On an adventure afternoon, {child.id} and {companion.id} went into '
        f'the {setting.place}. {setting.detail}'
    )
    world.say(
        f'The place was so dim that even the edges of the room seemed to slip-dim '
        f'into shadow.'
    )
    world.para()
    _speak_and_repeat(world, child, cur)
    _travel(world, child, setting, rep)
    world.para()
    _misread(world, companion, mis, child)
    world.say(f'{child.id} shook {child.pronoun("possessive")} head. "{cur.action}"')
    world.say(
        f'Before the confusion could grow, {helper.id} came closer with a lantern '
        f'and a steady voice.'
    )
    _repair(world, helper, mis, child)
    _finish(world, child, helper, setting, rep)

    world.facts.update(
        child=child, companion=companion, helper=helper,
        outcome="resolved",
        repeated=rep.count,
        dimness=setting.dimness,
        warned=companion.memes["misunderstood"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "cavern": Setting(
        id="cavern",
        place="cavern",
        detail="The cavern mouth opened wide, with stone walls and a slippery floor.",
        dimness=8,
        wind="cold",
        tags={"adventure", "slip-dim"},
    ),
    "attic": Setting(
        id="attic",
        place="attic",
        detail="The attic was full of boxes, old beams, and dusty corners.",
        dimness=7,
        wind="still",
        tags={"adventure", "slip-dim"},
    ),
    "tunnel": Setting(
        id="tunnel",
        place="tunnel",
        detail="The tunnel bent under the hill, with echoes that bounced like little drums.",
        dimness=9,
        wind="thin",
        tags={"adventure", "slip-dim"},
    ),
}

CURIOSITIES = {
    "pebble": Curiosity(
        id="pebble",
        question="What was making that tiny clicking sound?",
        repeat_line="Maybe the cave is answering us.",
        action="follow the sound",
        tags={"curiosity"},
    ),
    "door": Curiosity(
        id="door",
        question="Where did that narrow door lead?",
        repeat_line="Maybe it opens for explorers.",
        action="push the old door",
        tags={"curiosity"},
    ),
    "glimmer": Curiosity(
        id="glimmer",
        question="Was the faint glimmer a secret path?",
        repeat_line="Maybe the light is hiding a trail.",
        action="look for the glimmer again",
        tags={"curiosity"},
    ),
}

MISUNDERSTANDINGS = {
    "echo": Misunderstanding(
        id="echo",
        confusion="The words bounced off the walls and sounded bigger than they were.",
        misunderstanding_line="You should stop. That sounds like a warning, not a clue.",
        fixed_line="It was only an echo. The child was talking about a sound, not a danger.",
        tags={"misunderstanding"},
    ),
    "slip": Misunderstanding(
        id="slip",
        confusion="The dim floor looked slippery, and the companion thought the child wanted to rush.",
        misunderstanding_line="You are about to slip and fall!",
        fixed_line="A careful step is enough. We can keep going slowly.",
        tags={"misunderstanding", "slip-dim"},
    ),
    "map": Misunderstanding(
        id="map",
        confusion="A torn map made the path look wrong, and the companion thought they were lost.",
        misunderstanding_line="We must be lost already!",
        fixed_line="The map is torn, but the trail still makes sense if we follow it twice.",
        tags={"misunderstanding"},
    ),
}

REPETITIONS = {
    "twice": Repetition(
        id="twice",
        count=2,
        pattern="The same footstep landed twice, and each time the echo came back softer.",
        consequence="The repeated steps showed them which stones were solid.",
        tags={"repetition"},
    ),
    "three": Repetition(
        id="three",
        count=3,
        pattern="The child checked the same corner three times, each time finding a better clue.",
        consequence="The third look revealed a hidden handhold in the wall.",
        tags={"repetition"},
    ),
    "again": Repetition(
        id="again",
        count=2,
        pattern="Again and again, the lantern swept over the ground until the shine made a line.",
        consequence="The repeated light uncovered a safe path around the dark patch.",
        tags={"repetition"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe"]
BOY_NAMES = ["Ben", "Leo", "Theo", "Finn", "Max"]

CURATED = [
    StoryParams(setting="cavern", curiosity="pebble", misunderstanding="echo", repetition="twice",
                child_name="Mia", child_gender="girl", companion_name="Ben", companion_gender="boy",
                helper_name="Grandpa", helper_gender="man"),
    StoryParams(setting="attic", curiosity="door", misunderstanding="map", repetition="three",
                child_name="Leo", child_gender="boy", companion_name="Nora", companion_gender="girl",
                helper_name="Aunt May", helper_gender="woman"),
    StoryParams(setting="tunnel", curiosity="glimmer", misunderstanding="slip", repetition="again",
                child_name="Ava", child_gender="girl", companion_name="Finn", companion_gender="boy",
                helper_name="Dad", helper_gender="man"),
]


@dataclass
class StoryParams:
    setting: str
    curiosity: str
    misunderstanding: str
    repetition: str
    child_name: str = "Mia"
    child_gender: str = "girl"
    companion_name: str = "Ben"
    companion_gender: str = "boy"
    helper_name: str = "Grandpa"
    helper_gender: str = "man"
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for c in CURIOSITIES:
            for m in MISUNDERSTANDINGS:
                if c == "glimmer" and m == "slip":
                    combos.append((s, c, m))
                elif c == "pebble" and m == "echo":
                    combos.append((s, c, m))
                elif c == "door" and m == "map":
                    combos.append((s, c, m))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld with slip-dim curiosity and repetition.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--curiosity", choices=CURIOSITIES)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--repetition", choices=REPETITIONS)
    ap.add_argument("--name")
    ap.add_argument("--companion")
    ap.add_argument("--helper")
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
              if (args.setting is None or c[0] == args.setting)
              and (args.curiosity is None or c[1] == args.curiosity)
              and (args.misunderstanding is None or c[2] == args.misunderstanding)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, curiosity, misunderstanding = rng.choice(sorted(combos))
    if args.repetition:
        repetition = args.repetition
    else:
        repetition = "again" if curiosity == "glimmer" else ("twice" if curiosity == "pebble" else "three")
    child_gender = rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    companion_gender = "boy" if child_gender == "girl" else "girl"
    companion_name = args.companion or rng.choice([n for n in (BOY_NAMES if companion_gender == "boy" else GIRL_NAMES) if n != child_name])
    helper_gender = rng.choice(["man", "woman"])
    helper_name = args.helper or rng.choice(["Grandpa", "Aunt May", "Dad", "Mom"])
    return StoryParams(setting=setting, curiosity=curiosity, misunderstanding=misunderstanding,
                       repetition=repetition, child_name=child_name, child_gender=child_gender,
                       companion_name=companion_name, companion_gender=companion_gender,
                       helper_name=helper_name, helper_gender=helper_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    s = f["setting"].place
    c = f["curiosity"].question
    m = f["misunderstanding"].misunderstanding_line
    return [
        f'Write an adventure story for a young child set in a dim {s} that includes the words "slip-dim" and "{c}"',
        f"Tell a story where curiosity makes {f['child'].id} repeat a question in a dim {s}, and a companion misreads the plan before a helper clears it up.",
        f'Write a gentle adventure with repetition, misunderstanding, and a safe ending in the {s}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    companion: Entity = f["companion"]
    helper: Entity = f["helper"]
    s: Setting = f["setting"]
    cur: Curiosity = f["curiosity"]
    mis: Misunderstanding = f["misunderstanding"]
    rep: Repetition = f["repetition"]
    return [
        QAItem(
            question=f"What did {child.id} keep asking about in the {s.place}?",
            answer=f"{child.id} was curious about {cur.question.lower()} in the {s.place}. The child repeated the thought because the dim place felt full of adventure.",
        ),
        QAItem(
            question=f"Why did {companion.id} misunderstand {child.id}?",
            answer=f"{companion.id} misunderstood because {mis.confusion.lower()} That made the plan sound risky even though {child.id} meant something careful.",
        ),
        QAItem(
            question=f"What happened after {child.id} repeated the same step {rep.count} times?",
            answer=f"The repetition helped {child.id} notice a safe way forward. The repeated steps showed that the path was steady instead of scary.",
        ),
        QAItem(
            question=f"How did {helper.id} help the adventure end well?",
            answer=f"{helper.id} cleared up the confusion and gave a calm explanation. Then the group could keep exploring with a lantern and a better plan.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What does an echo do?", "An echo is a sound that bounces back from walls or rocks. It can make a small voice sound bigger in a cave or tunnel."),
        QAItem("Why can a dim place feel strange?", "A dim place has less light, so it is harder to see. That can make ordinary shadows seem mysterious."),
        QAItem("Why is repeating a careful step helpful?", "Repeating a careful step can help you notice patterns and safe spots. It gives you another chance to see what you missed before."),
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


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.curiosity not in CURIOSITIES or params.misunderstanding not in MISUNDERSTANDINGS or params.repetition not in REPETITIONS:
        raise StoryError("Unknown story ingredients.")
    if (params.setting, params.curiosity, params.misunderstanding) not in valid_combos():
        raise StoryError("This combination does not fit the adventure logic.")
    world = tell(
        SETTINGS[params.setting],
        CURIOSITIES[params.curiosity],
        MISUNDERSTANDINGS[params.misunderstanding],
        REPETITIONS[params.repetition],
        child_name=params.child_name,
        child_gender=params.child_gender,
        companion_name=params.companion_name,
        companion_gender=params.companion_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
    )
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
        print("--- world model state ---")
        for e in sample.world.entities.values():
            print(e.id, e.kind, e.type, dict(e.meters), dict(e.memes))
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
valid(S,C,M) :- setting(S), curiosity(C), misunderstanding(M), allowed(C,M).
allowed(pebble,echo).
allowed(door,map).
allowed(glimmer,slip).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for c in CURIOSITIES:
        lines.append(asp.fact("curiosity", c))
    for m in MISUNDERSTANDINGS:
        lines.append(asp.fact("misunderstanding", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    rc = 0
    try:
        sample = generate(CURATED[0])
        assert sample.story
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    c, p = set(asp_valid_combos()), set(valid_combos())
    if c == p:
        print(f"OK: clingo gate matches valid_combos() ({len(c)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
        print("only in clingo:", sorted(c - p))
        print("only in python:", sorted(p - c))
    return rc


CURATED = [
    StoryParams(setting="cavern", curiosity="pebble", misunderstanding="echo", repetition="twice", child_name="Mia", child_gender="girl", companion_name="Ben", companion_gender="boy", helper_name="Grandpa", helper_gender="man"),
    StoryParams(setting="attic", curiosity="door", misunderstanding="map", repetition="three", child_name="Leo", child_gender="boy", companion_name="Nora", companion_gender="girl", helper_name="Aunt May", helper_gender="woman"),
    StoryParams(setting="tunnel", curiosity="glimmer", misunderstanding="slip", repetition="again", child_name="Ava", child_gender="girl", companion_name="Finn", companion_gender="boy", helper_name="Dad", helper_gender="man"),
]


def valid_story_seed(rng: random.Random) -> StoryParams:
    return resolve_params(argparse.Namespace(setting=None, curiosity=None, misunderstanding=None, repetition=None, name=None, companion=None, helper=None), rng)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for combo in asp_valid_combos():
            print(combo)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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

#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/tuesday_happy_ending_friendship_reconciliation_whodunit.py
==========================================================================================

A small whodunit-style storyworld about a Tuesday mystery in a classroom, where
friends misunderstand one another, investigate clues, and end with a happy
reconciliation.

The world is intentionally tiny:
- a missing or moved object
- a few typed characters and objects
- physical meters and emotional memes
- a simple causal chain that supports a complete story

This script follows the Storyweavers storyworld contract:
- stdlib only
- imports storyworlds/results.py eagerly
- defines StoryParams, registries, build_parser, resolve_params, generate,
  emit, and main
- supports --all, --seed, -n, --trace, --qa, --json, --asp, --verify,
  and --show-asp
- includes Python and ASP parity checks
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing | place
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "teacher"}
        male = {"boy", "father", "dad", "man", "boy_teacher"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "teacher": "teacher"}.get(self.type, self.type)


@dataclass
class Clue:
    id: str
    label: str
    location: str
    tells: str
    owner: str = ""
    moved: bool = False
    suspicious: bool = False


@dataclass
class Action:
    id: str
    verb: str
    object_word: str
    clue_word: str
    tension: str
    resolution: str
    risky: bool = False
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.clues: dict[str, Clue] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_clue(self, clue: Clue) -> Clue:
        self.clues[clue.id] = clue
        return clue

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
        clone.clues = copy.deepcopy(self.clues)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_sad(world: World) -> list[str]:
    out = []
    for e in world.entities.values():
        if e.kind != "character":
            continue
        if e.memes["hurt"] >= THRESHOLD and ("sadness", e.id) not in world.fired:
            world.fired.add(("sadness", e.id))
            e.memes["sadness"] += 1
            out.append("")
    return out


def _r_reveal(world: World) -> list[str]:
    out = []
    if world.facts.get("revealed") and ("reveal", "one") not in world.fired:
        world.fired.add(("reveal", "one"))
        out.append("__reveal__")
    return out


CAUSAL_RULES = [Rule("sad", _r_sad), Rule("reveal", _r_reveal)]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    produced: list[str] = []
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s and not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for culprit in CULPRITS.values():
            for object_id in OBJECTS:
                if culprit.is_plausible and OBJECTS[object_id].moved:
                    combos.append((setting, culprit.id, object_id))
    return combos


@dataclass
class StoryParams:
    setting: str
    culprit: str
    object_id: str
    investigator: str
    friend: str
    teacher: str
    seed: Optional[int] = None


@dataclass
class Setting:
    id: str
    scene: str
    opening: str
    hiding: str
    ending: str


@dataclass
class Culprit:
    id: str
    label: str
    accusation: str
    clue: str
    reason: str
    is_plausible: bool = True


@dataclass
class ObjectCfg:
    id: str
    label: str
    hidden_place: str
    clue: str
    moved: bool = True


SETTINGS = {
    "classroom": Setting(
        "classroom",
        "a bright classroom with little desks and a reading rug",
        "It was Tuesday, and the classroom felt quiet after recess.",
        "behind the story basket",
        "The room looked neat again, but the mystery had changed everything."
    ),
    "library": Setting(
        "library",
        "a small school library with low shelves and soft chairs",
        "It was Tuesday, and the library smelled like paper and crayons.",
        "under a stack of picture books",
        "The shelves were tidy again, and the friends were smiling."
    ),
}

CULPRITS = {
    "cat": Culprit("cat", "the class cat puppet", "The cat took it!", "tiny paw prints", "the puppet had been knocked down by accident", True),
    "wind": Culprit("wind", "a draft from the window", "The wind did it!", "a fluttering paper strip", "the window had been open", True),
    "friend": Culprit("friend", "a worried friend", "My friend hid it!", "a careful ribbon trail", "the friend had moved it to keep it safe", True),
}

OBJECTS = {
    "glue": ObjectCfg("glue", "the glue stick", "inside the art box", "a sticky cap"),
    "book": ObjectCfg("book", "the blue storybook", "on the rug", "a bent page corner"),
    "ribbon": ObjectCfg("ribbon", "the red ribbon", "on the reading table", "a bright red thread"),
}

NAMES = ["Maya", "Noah", "Lily", "Ben", "Ava", "Leo", "Nina", "Eli"]
TRAITS = ["curious", "careful", "kind", "patient", "smart"]


def story_has_reconciliation(world: World) -> bool:
    return world.facts.get("ended_happy", False)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny Tuesday whodunit storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--object", dest="object_id", choices=OBJECTS)
    ap.add_argument("--investigator")
    ap.add_argument("--friend")
    ap.add_argument("--teacher")
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


def explain_rejection(culprit: Culprit, obj: ObjectCfg) -> str:
    return f"(No story: {culprit.label} and {obj.label} do not make a useful mystery.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.culprit is None or c[1] == args.culprit)
              and (args.object_id is None or c[2] == args.object_id)]
    if not combos:
        if args.culprit and args.object_id:
            raise StoryError(explain_rejection(CULPRITS[args.culprit], OBJECTS[args.object_id]))
        raise StoryError("(No valid combination matches the given options.)")
    setting, culprit, object_id = rng.choice(sorted(combos))
    inv = args.investigator or rng.choice(NAMES)
    friend = args.friend or rng.choice([n for n in NAMES if n != inv])
    teacher = args.teacher or rng.choice(["Ms. Reed", "Mr. Fox"])
    return StoryParams(setting, culprit, object_id, inv, friend, teacher)


def _accuse(world: World, inv: Entity, friend: Entity, culprit: Culprit, obj: ObjectCfg) -> None:
    inv.memes["worry"] += 1
    friend.memes["hurt"] += 1
    world.say(
        f"\"Someone took {obj.label}!\" {inv.id} said. "
        f"{friend.id} looked surprised, and the room felt smaller."
    )
    world.say(
        f"{friend.id} pointed at the clue: {culprit.clue}. "
        f"That made the mystery feel real."
    )


def _investigate(world: World, inv: Entity, friend: Entity, culprit: Culprit, obj: ObjectCfg) -> None:
    inv.memes["curious"] += 1
    friend.memes["hope"] += 1
    world.facts["revealed"] = True
    world.say(
        f"{inv.id} looked under the desks and near the shelves. "
        f"{friend.id} followed the clue trail and found that {obj.label} had been moved."
    )
    world.say(
        f"The clue was not a mean trick after all; it was a hint that someone had tried to keep the item safe."
    )


def _reconcile(world: World, inv: Entity, friend: Entity, teacher: Entity, obj: ObjectCfg) -> None:
    inv.memes["apology"] += 1
    friend.memes["forgive"] += 1
    inv.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.facts["ended_happy"] = True
    world.say(
        f"Then {inv.id} said sorry to {friend.id}, and {friend.id} said sorry too."
    )
    world.say(
        f"{teacher.label_word.capitalize()} smiled and explained that the item had been moved to keep it from getting lost."
    )
    world.say(
        f"By the end of Tuesday, {obj.label} was back where it belonged, and the friends were talking again."
    )


def tell(setting: Setting, culprit: Culprit, obj: ObjectCfg,
         investigator: str, friend: str, teacher_name: str) -> World:
    world = World()
    inv = world.add(Entity(id=investigator, kind="character", type="girl" if investigator in {"Maya", "Lily", "Ava", "Nina"} else "boy", role="investigator"))
    fri = world.add(Entity(id=friend, kind="character", type="girl" if friend in {"Maya", "Lily", "Ava", "Nina"} else "boy", role="friend"))
    teacher = world.add(Entity(id=teacher_name, kind="character", type="teacher", role="teacher"))
    world.add_clue(Clue(id="clue", label=culprit.clue, location=obj.hidden_place, tells=culprit.reason, suspicious=True))
    world.facts.update(setting=setting, culprit=culprit, object=obj, inv=inv, friend=fri, teacher=teacher)
    world.say(f"On {setting.id}, the children were in {setting.scene}. {setting.opening}")
    world.say(
        f"{inv.id} noticed that {obj.label} was missing. {fri.id} was standing nearby, so the mystery began at once."
    )
    world.para()
    _accuse(world, inv, fri, culprit, obj)
    _investigate(world, inv, fri, culprit, obj)
    world.para()
    _reconcile(world, inv, fri, teacher, obj)
    world.say(setting.ending)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting: Setting = f["setting"]
    culprit: Culprit = f["culprit"]
    obj: ObjectCfg = f["object"]
    return [
        f'Write a Tuesday whodunit for a young child set in {setting.scene}, and include the word "tuesday".',
        f"Tell a friendship mystery where {obj.label} goes missing, the children investigate clues, and everyone makes up at the end.",
        f"Write a happy-ending classroom mystery about {culprit.label} and {obj.label}, with apology and reconciliation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    obj: ObjectCfg = f["object"]
    culprit: Culprit = f["culprit"]
    inv: Entity = f["inv"]
    fri: Entity = f["friend"]
    teacher: Entity = f["teacher"]
    return [
        QAItem(
            question="What kind of story is this?",
            answer="It is a whodunit about a missing thing, a few clues, and friends trying to understand what happened. It ends happily because the children talk, apologize, and solve the mistake together."
        ),
        QAItem(
            question=f"What was missing?",
            answer=f"{obj.label} was missing at the start, so the children began looking for clues. The object was moved, not stolen, which is why the mystery could end in reconciliation."
        ),
        QAItem(
            question=f"Why did {fri.id} stop seeming suspicious?",
            answer=f"The clue trail showed that {culprit.reason}. That meant {fri.id} had not done anything mean, and the misunderstanding could be fixed."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with apologies, a teacher's calm explanation, and the friends smiling again. On Tuesday, {obj.label} went back where it belonged and nobody stayed angry."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue?",
            answer="A clue is a small piece of information that helps someone figure out what happened. In a mystery, clues can point toward the answer."
        ),
        QAItem(
            question="What does reconcile mean?",
            answer="Reconcile means to make peace after a disagreement. Friends reconcile when they stop being upset and start trusting each other again."
        ),
        QAItem(
            question="What is a whodunit?",
            answer="A whodunit is a mystery story where someone asks who did something and then follows clues to find out. The fun is in solving the puzzle."
        ),
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
    out = ["--- world ---"]
    for e in world.entities.values():
        out.append(f"{e.id}: kind={e.kind} type={e.type} role={e.role} memes={dict(e.memes)}")
    for cid, c in world.clues.items():
        out.append(f"clue:{cid} label={c.label} location={c.location} tells={c.tells}")
    out.append(f"facts={sorted(world.facts.keys())}")
    return "\n".join(out)


CURATED = [
    StoryParams("classroom", "friend", "glue", "Maya", "Lily", "Ms. Reed"),
    StoryParams("library", "cat", "book", "Noah", "Ben", "Mr. Fox"),
    StoryParams("classroom", "wind", "ribbon", "Ava", "Nina", "Ms. Reed"),
]


ASP_RULES = r"""
valid(S,C,O) :- setting(S), culprit(C), object(O), plausible(C), moved(O).
happy_end :- apology, explanation, returned, friends_again.
apology :- investigator(_), friend(_).
explanation :- teacher(_).
returned :- object_moved_back.
friends_again :- apology, explanation.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, c in CULPRITS.items():
        lines.append(asp.fact("culprit", cid))
        if c.is_plausible:
            lines.append(asp.fact("plausible", cid))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        if o.moved:
            lines.append(asp.fact("moved", oid))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combos differ.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, culprit=None, object_id=None, investigator=None, friend=None, teacher=None), random.Random(7)))
        _ = sample.story
        _ = format_qa(sample)
        print("OK: generate smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: ASP and Python agree.")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], CULPRITS[params.culprit], OBJECTS[params.object_id],
                 params.investigator, params.friend, params.teacher)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.culprit is None or c[1] == args.culprit)
              and (args.object_id is None or c[2] == args.object_id)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, culprit, obj = rng.choice(sorted(combos))
    investigator = args.investigator or rng.choice(NAMES)
    friend = args.friend or rng.choice([n for n in NAMES if n != investigator])
    teacher = args.teacher or rng.choice(["Ms. Reed", "Mr. Fox"])
    return StoryParams(setting, culprit, obj, investigator, friend, teacher)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/3.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
            header = f"### {p.setting} / {p.culprit} / {p.object_id}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

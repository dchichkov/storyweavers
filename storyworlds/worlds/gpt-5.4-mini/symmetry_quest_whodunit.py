#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/symmetry_quest_whodunit.py
==========================================================

A standalone story world for a small whodunit quest: a child detective follows
a symmetry clue through a tidy little mystery, finds the missing object, and
learns that the matching pair was hidden in plain sight.

The world uses typed entities with physical meters and emotional memes, a small
forward-chained causal model, and a declarative ASP twin for parity checks.
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
REASONABLE_HUNCH = 2


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
class Quest:
    id: str
    place: str
    object_name: str
    missing_name: str
    clue: str
    symmetry_pattern: str
    false_lead: str
    solved_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.clues_found: int = 0

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
        c.clues_found = self.clues_found
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_clue(world: World) -> list[str]:
    out: list[str] = []
    sleuth = world.get("sleuth")
    if sleuth.meters["observant"] < THRESHOLD:
        return out
    sig = ("clue",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.clues_found += 1
    sleuth.memes["hope"] += 1
    out.append("__clue__")
    return out


def _r_reveal(world: World) -> list[str]:
    out: list[str] = []
    if world.clues_found < THRESHOLD:
        return out
    sig = ("reveal",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("missing").meters["found"] += 1
    out.append("__reveal__")
    return out


CAUSAL_RULES = [Rule("clue", "social", _r_clue), Rule("reveal", "social", _r_reveal)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            s = rule.apply(world)
            if s:
                changed = True
                produced.extend(x for x in s if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def quest_reasonable(quest: Quest) -> bool:
    return bool(quest.symmetry_pattern) and "mirror" in quest.tags


def question_symmetry(quest: Quest) -> bool:
    return "symmetry" in quest.tags and quest.clue.count("left") + quest.clue.count("right") >= 1


def predict(world: World, quest: Quest) -> dict:
    sim = world.copy()
    _conduct_search(sim, quest, narrate=False)
    return {"found": bool(sim.get("missing").meters["found"] >= THRESHOLD), "hope": sim.get("sleuth").memes["hope"]}


def _conduct_search(world: World, quest: Quest, narrate: bool = True) -> None:
    sleuth = world.get("sleuth")
    sleuth.meters["observant"] += 1
    sleuth.memes["focus"] += 1
    world.say(
        f"{sleuth.id} studied the room like a careful detective. "
        f"The first clue was {quest.clue}, and it seemed to point to {quest.place}."
    )
    propagate(world, narrate=narrate)


def introduce(world: World, sleuth: Entity, helper: Entity, quest: Quest) -> None:
    world.say(
        f"On a quiet afternoon, {sleuth.id} and {helper.id} were asked to help solve a little mystery."
    )
    world.say(
        f"At {quest.place}, someone had lost {quest.missing_name}, and the only note left behind was a sign of symmetry."
    )


def observe(world: World, sleuth: Entity, quest: Quest) -> None:
    sleuth.memes["curiosity"] += 1
    world.say(
        f"{sleuth.id} noticed {quest.symmetry_pattern}. {sleuth.pronoun().capitalize()} said the pattern looked matched on both sides."
    )


def warn(world: World, helper: Entity, quest: Quest) -> None:
    helper.memes["calm"] += 1
    world.say(
        f'{helper.id} pointed to a false lead: "{quest.false_lead}." '
        f"But the clue felt too neat for that."
    )


def reveal(world: World, sleuth: Entity, quest: Quest) -> None:
    world.say(
        f"{sleuth.id} checked the room again and found {quest.object_name} hiding where the pattern made sense."
    )
    world.say(
        f"It was tucked in a mirrored spot, just like the clue promised, and the mystery clicked into place."
    )


def finish(world: World, sleuth: Entity, helper: Entity, quest: Quest) -> None:
    sleuth.memes["pride"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"Then {sleuth.id} and {helper.id} stood side by side and looked at the solved scene: {quest.solved_image}."
    )
    world.say(
        f"The missing thing had been found, the symmetry was real, and the little quest ended with a bright, satisfied grin."
    )


def tell(quest: Quest, sleuth_name: str = "Mina", helper_name: str = "Grandpa",
         sleuth_gender: str = "girl", helper_gender: str = "boy",
         parent_type: str = "father") -> World:
    world = World()
    sleuth = world.add(Entity("sleuth", "character", sleuth_gender, label=sleuth_name, role="detective"))
    helper = world.add(Entity("helper", "character", helper_gender, label=helper_name, role="guide"))
    parent = world.add(Entity("parent", "character", parent_type, label="the grown-up", role="parent"))
    missing = world.add(Entity("missing", "thing", "thing", label=quest.missing_name, role="missing"))
    clue = world.add(Entity("clue", "thing", "thing", label=quest.clue, role="clue"))

    sleuth.meters["observant"] = 1.0
    helper.memes["patience"] = 1.0
    world.facts["quest"] = quest
    world.facts["parent"] = parent
    world.facts["sleuth"] = sleuth
    world.facts["helper"] = helper
    world.facts["missing"] = missing
    world.facts["clue"] = clue

    introduce(world, sleuth, helper, quest)
    world.para()
    observe(world, sleuth, quest)
    warn(world, helper, quest)
    world.para()
    _conduct_search(world, quest)
    reveal(world, sleuth, quest)
    finish(world, sleuth, helper, quest)

    world.facts.update(
        solved=bool(missing.meters["found"] >= THRESHOLD),
        clue_seen=True,
        symmetry=quest.symmetry_pattern,
    )
    return world


QUESTS = {
    "mirror_garden": Quest(
        "mirror_garden",
        "the garden path",
        "a silver spoon",
        "the missing spoon",
        "A row of stones made a mirror pattern, left and right, left and right.",
        "left-right symmetry",
        "the spoon must be under the porch",
        "the spoon was found beside a mirrored flower bed",
        tags={"symmetry", "mirror"},
    ),
    "window_hall": Quest(
        "window_hall",
        "the hall by the windows",
        "a red ribbon",
        "the missing ribbon",
        "The windows came in matching pairs, one on each side of the hall.",
        "pair symmetry",
        "the ribbon must be in the basket",
        "the ribbon was found in a twin basket on the other side",
        tags={"symmetry", "mirror"},
    ),
    "shell_stairs": Quest(
        "shell_stairs",
        "the front steps",
        "a little shell",
        "the missing shell",
        "The shell marks on the steps repeated in a steady left-right rhythm.",
        "step symmetry",
        "the shell must be behind the lamp",
        "the shell was found beside a paired stair planter",
        tags={"symmetry", "mirror"},
    ),
}

SLEUTH_NAMES = ["Mina", "June", "Nora", "Tess", "Lena", "Pia"]
HELPER_NAMES = ["Grandpa", "Aunt Rae", "Uncle Ben", "Mom", "Dad", "Mrs. Lane"]


@dataclass
class StoryParams:
    quest: str
    sleuth_name: str
    sleuth_gender: str
    helper_name: str
    helper_gender: str
    parent: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str]]:
    return [(qid,) for qid, q in QUESTS.items() if quest_reasonable(q)]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A symmetry-quest whodunit storyworld.")
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
    combos = [c for c in valid_combos() if args.quest is None or c[0] == args.quest]
    if not combos:
        raise StoryError("(No valid quest matches the given options.)")
    qid = rng.choice(sorted(q[0] for q in combos))
    quest = QUESTS[qid]
    gender = args.gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(SLEUTH_NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(qid, name, gender, helper, helper_gender, parent)


def generation_prompts(world: World) -> list[str]:
    q = world.facts["quest"]
    return [
        f'Write a child-friendly whodunit quest that includes the word "symmetry" and ends with the missing item found.',
        f"Tell a mystery story where {world.facts['sleuth'].label} follows a symmetry clue at {q.place} and solves the quest.",
        f"Write a short detective tale for a young child with a neat clue, a false lead, and a satisfying reveal.",
    ]


def story_qa(world: World) -> list[QAItem]:
    q = world.facts["quest"]
    sleuth = world.facts["sleuth"]
    helper = world.facts["helper"]
    return [
        QAItem(
            question="What kind of clue helped solve the mystery?",
            answer=f"A symmetry clue helped solve it. The pattern was {q.symmetry_pattern}, so {sleuth.label} knew to look for a matching spot."
        ),
        QAItem(
            question="What did the helper say first?",
            answer=f"{helper.label} pointed to a false lead and mentioned that {q.false_lead}. But the neat symmetry made that guess feel wrong."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with the missing item found and everyone relieved. The solved scene showed {q.solved_image}, which proved the quest was complete."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is symmetry?",
            answer="Symmetry means one side matches the other side. A shape or pattern can look balanced because the parts line up in a pair."
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues and checks them carefully. A good detective notices small details and follows them to the answer."
        ),
        QAItem(
            question="What is a clue?",
            answer="A clue is a small piece of information that helps solve a mystery. It points the search in the right direction."
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
    lines.append("== (3) World knowledge ==")
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
        lines.append(f"  {e.id:8} ({e.kind:8}) {e.label!r} {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: this quest setup would not give a convincing symmetry clue.)"


CURATED = [
    StoryParams("mirror_garden", "Mina", "girl", "Grandpa", "boy", "father"),
    StoryParams("window_hall", "June", "girl", "Mom", "girl", "mother"),
    StoryParams("shell_stairs", "Tess", "girl", "Dad", "boy", "father"),
]


ASP_RULES = r"""
quest(Q) :- quest_fact(Q).
reasonable(Q) :- quest(Q), mirror(Q).
clue_seen(Q) :- reasonable(Q), symmetry(Q).
found(Q) :- clue_seen(Q).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest_fact", qid))
        lines.append(asp.fact("symmetry", qid))
        lines.append(asp.fact("mirror", qid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show reasonable/1."))
    return sorted(set(asp.atoms(model, "reasonable")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set((x[0],) for x in valid_combos()):
        print("OK: ASP parity with valid_combos().")
    else:
        rc = 1
        print("MISMATCH in ASP parity.")
    try:
        sample = generate(resolve_params(argparse.Namespace(quest=None, name=None, helper=None, gender=None, helper_gender=None, parent=None), random.Random(1)))
        _ = sample.story
        print("OK: smoke test generation succeeded.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(
        QUESTS[params.quest],
        params.sleuth_name,
        params.helper_name,
        params.sleuth_gender,
        params.helper_gender,
        params.parent,
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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show reasonable/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("reasonable quests:", ", ".join(x[0] for x in asp_valid_combos()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.sleuth_name}: {p.quest}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

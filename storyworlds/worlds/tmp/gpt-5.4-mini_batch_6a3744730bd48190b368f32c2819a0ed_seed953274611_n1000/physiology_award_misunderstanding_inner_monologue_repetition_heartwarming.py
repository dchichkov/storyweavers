#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/physiology_award_misunderstanding_inner_monologue_repetition_heartwarming.py
=============================================================================================================

A small, heartwarming story world about a child who hears about a physiology
award, misunderstands what it means, repeats a little phrase to themselves, and
finally learns that kindness and care matter more than a trophy.

The world is built as a tiny simulation:
- typed entities with meters and memes,
- state-driven causal beats,
- a reasonableness gate,
- an inline ASP twin for parity checking,
- three QA sets grounded in the simulated world.

The seed words are present in the story domain: physiology, award.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
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
        return self.label or self.type


@dataclass
class Award:
    id: str
    label: str
    reason: str
    stage: str
    glow: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Misunderstanding:
    id: str
    line: str
    repeat: str
    clue: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    award: str
    misunderstanding: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    parent_type: str
    seed: Optional[int] = None


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


def _r_worry(world: World) -> list[str]:
    out = []
    child = world.get("child")
    if child.memes["worry"] >= THRESHOLD and ("worry" not in world.fired):
        world.fired.add(("worry",))
        child.meters["stillness"] += 1
        out.append("__worry__")
    return out


def _r_relief(world: World) -> list[str]:
    out = []
    child = world.get("child")
    helper = world.get("helper")
    parent = world.get("parent")
    if child.memes["understanding"] >= THRESHOLD and ("relief" not in world.fired):
        world.fired.add(("relief",))
        child.memes["joy"] += 1
        helper.memes["joy"] += 1
        parent.memes["joy"] += 1
        out.append("__relief__")
    return out


CAUSAL_RULES = [Rule("worry", _r_worry), Rule("relief", _r_relief)]


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


def valid_awards() -> list[str]:
    return [a.id for a in AWARDS.values()]


def valid_combos() -> list[tuple[str, str]]:
    return [(aid, mid) for aid in AWARDS for mid in MISMATCHES]


def mismatch_reasonable(award: Award, miss: Misunderstanding) -> bool:
    return bool(award.reason and miss.line and miss.repeat)


def predict(world: World, miss: Misunderstanding) -> dict:
    sim = world.copy()
    sim.get("child").memes["worry"] += 1
    sim.get("child").memes["repeat"] += 1
    return {"worry": sim.get("child").memes["worry"]}


def setup(world: World, child: Entity, helper: Entity, parent: Entity, award: Award, miss: Misunderstanding) -> None:
    child.memes["curiosity"] += 1
    child.memes["repeat"] += 1
    world.say(
        f"{child.id} heard about the {award.label} and kept thinking about it."
    )
    world.say(
        f"At school, the announcement said the award was for {award.reason}, and {child.id} nodded along."
    )


def misunderstanding_beat(world: World, child: Entity, helper: Entity, miss: Misunderstanding, award: Award) -> None:
    child.memes["worry"] += 1
    child.memes["repeat"] += 1
    world.say(
        f'{child.id} whispered to {helper.id}, "{miss.line}"'
    )
    world.say(
        f'Inside {child.id}\'s head, one small thought kept circling: "{miss.repeat}" "{miss.repeat}" "{miss.repeat}".'
    )


def correction(world: World, parent: Entity, child: Entity, helper: Entity, award: Award, miss: Misunderstanding) -> None:
    child.memes["understanding"] += 1
    helper.memes["care"] += 1
    parent.memes["care"] += 1
    world.say(
        f"{parent.label_word.capitalize()} smiled and explained that physiology was about how bodies work, not about being the biggest or the fastest."
    )
    world.say(
        f'{helper.id} added, "The award is for caring work too. Quiet help counts."'
    )


def closing(world: World, child: Entity, helper: Entity, parent: Entity, award: Award) -> None:
    child.memes["joy"] += 1
    world.say(
        f"{child.id} looked at the little ribbon again and felt their chest warm up."
    )
    world.say(
        f'This time, {child.id} repeated the right thing: "{award.reason} matters."'
    )
    world.say(
        f"At the end, the family tucked the award on a shelf, and the room felt brighter just because everyone understood."
    )


def tell(award: Award, miss: Misunderstanding, child_name: str = "Mina", child_gender: str = "girl",
         helper_name: str = "Nico", helper_gender: str = "boy", parent_type: str = "mother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="mom"))
    world.add(Entity(id="award", type="award", label=award.label, tags=set(award.tags)))
    world.add(Entity(id="misunderstanding", type="idea", label=miss.line, tags=set(miss.tags)))

    setup(world, child, helper, parent, award, miss)
    world.para()
    misunderstanding_beat(world, child, helper, miss, award)
    correction(world, parent, child, helper, award, miss)
    world.para()
    closing(world, child, helper, parent, award)

    world.facts.update(
        child=child, helper=helper, parent=parent, award=award, miss=miss,
        understood=child.memes["understanding"] >= THRESHOLD,
    )
    return world


AWARDS = {
    "kindness": Award(
        id="kindness",
        label="kindness award",
        reason="being gentle with others",
        stage="the front of the classroom",
        glow="soft and gold",
        tags={"award", "kindness"},
    ),
    "care": Award(
        id="care",
        label="care award",
        reason="helping people feel better",
        stage="the hallway table",
        glow="warm and bright",
        tags={"award", "care"},
    ),
}

MISMATCHES = {
    "speed": Misunderstanding(
        id="speed",
        line="So the award is for the fastest body, right?",
        repeat="fastest body",
        clue="speed",
        tags={"misunderstanding", "physiology"},
    ),
    "strong": Misunderstanding(
        id="strong",
        line="So the award is for the strongest arms, right?",
        repeat="strongest arms",
        clue="strong",
        tags={"misunderstanding", "physiology"},
    ),
    "look": Misunderstanding(
        id="look",
        line="So the award is for looking perfect, right?",
        repeat="looking perfect",
        clue="look",
        tags={"misunderstanding", "award"},
    ),
}

GIRL_NAMES = ["Mina", "Lena", "Ruby", "Ivy", "Nora"]
BOY_NAMES = ["Nico", "Theo", "Owen", "Milo", "Eli"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a, m = f["award"], f["miss"]
    child, helper = f["child"], f["helper"]
    return [
        f'Write a heartwarming story for a young child that includes the words "physiology" and "award".',
        f"Tell a gentle story where {child.id} misunderstands a physiology award, repeats a worried phrase to themselves, and then learns what the award really means.",
        f"Write a short heartwarming story in which {helper.id} helps {child.id} replace a misunderstanding with a kinder thought about an award.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, helper, parent, award, miss = f["child"], f["helper"], f["parent"], f["award"], f["miss"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id}, who hears about the {award.label} and gets a little confused. {helper.id} and {parent.label_word} help {child.id} understand it kindly."),
        ("What did {0} keep repeating?".format(child.id),
         f"{child.id} kept repeating '{miss.repeat}' in their head when they misunderstood the award. The repetition shows how the worry kept circling until someone explained the truth."),
        ("What did the parent explain?",
         f"{parent.label_word.capitalize()} explained that physiology means learning how bodies work. {parent.label_word.capitalize()} also said the award was really about kindness and care, not just being the fastest or strongest."),
    ]
    if f.get("understood"):
        qa.append((
            "How did the story end?",
            f"It ended warmly, with {child.id} feeling proud and calm after the misunderstanding was cleared up. The award stayed on the shelf, but the real prize was that everyone understood each other."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does physiology mean?",
         "Physiology is the study of how bodies work and what they do to stay alive and healthy."),
        ("What is an award?",
         "An award is a special prize or honor given to someone for doing something well or kindly."),
        ("What is a misunderstanding?",
         "A misunderstanding happens when someone gets the meaning wrong at first, but can learn the truth after someone explains."),
        ("Why can repeating a worried thought feel bigger?",
         "When the same worried thought repeats again and again, it can start to feel louder inside a person's mind even if nothing has changed."),
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
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
misunderstanding(M) :- miss(M).
repetition(M) :- miss(M), repeat_phrase(M, _).
understood :- child_understanding(U), U >= 1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for aid, a in AWARDS.items():
        lines.append(asp.fact("award", aid))
        lines.append(asp.fact("reason", aid, a.reason))
    for mid, m in MISMATCHES.items():
        lines.append(asp.fact("miss", mid))
        lines.append(asp.fact("repeat_phrase", mid, m.repeat))
    lines.append(asp.fact("physiology_word", "physiology"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show award/1.\n#show miss/1."))
    awards = [a for (a,) in asp.atoms(model, "award")]
    misses = [m for (m,) in asp.atoms(model, "miss")]
    return sorted((a, m) for a in awards for m in misses if a in AWARDS and m in MISMATCHES)


def asp_verify() -> int:
    import asp
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
    try:
        sample = generate(resolve_params(argparse.Namespace(award=None, misunderstanding=None, child_name=None, child_gender=None, helper_name=None, helper_gender=None, parent_type=None), random.Random(1)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming physiology-award misunderstanding story world.")
    ap.add_argument("--award", choices=AWARDS)
    ap.add_argument("--misunderstanding", choices=MISMATCHES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
    award = args.award or rng.choice(list(AWARDS))
    miss = args.misunderstanding or rng.choice(list(MISMATCHES))
    if award not in AWARDS or miss not in MISMATCHES:
        raise StoryError("Unknown award or misunderstanding.")
    child_gender = rng.choice(["girl", "boy"])
    helper_gender = "boy" if child_gender == "girl" else "girl"
    child_name = args.name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper_name = args.helper or rng.choice(BOY_NAMES if helper_gender == "boy" else GIRL_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        award=award,
        misunderstanding=miss,
        child_name=child_name,
        child_gender=child_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        parent_type=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if params.award not in AWARDS:
        raise StoryError("Invalid award.")
    if params.misunderstanding not in MISMATCHES:
        raise StoryError("Invalid misunderstanding.")
    world = tell(
        AWARDS[params.award],
        MISMATCHES[params.misunderstanding],
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        parent_type=params.parent_type,
    )
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


CURATED = [
    StoryParams(award="kindness", misunderstanding="speed", child_name="Mina", child_gender="girl", helper_name="Nico", helper_gender="boy", parent_type="mother"),
    StoryParams(award="care", misunderstanding="strong", child_name="Eli", child_gender="boy", helper_name="Lena", helper_gender="girl", parent_type="father"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show award/1.\n#show miss/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for a, m in combos:
            print(f"  {a:10} {m}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

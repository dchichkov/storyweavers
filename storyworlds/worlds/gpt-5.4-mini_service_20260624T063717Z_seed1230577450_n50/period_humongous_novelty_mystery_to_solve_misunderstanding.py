#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T063717Z_seed1230577450_n50/period_humongous_novelty_mystery_to_solve_misunderstanding.py
=========================================================================================================================================

A small adventure-style storyworld about a period, a humongous novelty, and a
mystery caused by a misunderstanding.

Premise:
- A child notices a strange new thing in a calm setting.
- The thing is humongous and novel, which makes it feel mysterious.
- A misunderstanding makes a helper think something went wrong.
- The child solves the mystery by looking closely, asking, and comparing clues.
- The ending proves what changed in the world: the misunderstanding clears and
  the novelty becomes understood.

This file follows the Storyweavers contract:
- standalone stdlib script
- imports shared result containers eagerly
- lazy-imports storyworlds/asp.py only inside ASP helpers
- defines StoryParams, registries, build_parser, resolve_params, generate,
  emit, and main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool
    covers: set[str]


@dataclass
class ObjectCfg:
    label: str
    phrase: str
    region: str
    novelty: str
    size: str = "humongous"
    plural: bool = False


@dataclass
class MysteryCfg:
    label: str
    clue: str
    misunderstanding: str
    solve_action: str
    reveal: str
    risk: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.clues: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.clues = list(self.clues)
        return clone


SETTINGS = {
    "attic": Setting("the attic", True, {"floor", "shelves"}),
    "harbor": Setting("the harbor", False, {"dock", "water"}),
    "museum": Setting("the museum hall", True, {"floor", "tables"}),
    "garden": Setting("the garden path", False, {"path", "bench"}),
}

OBJECTS = {
    "wheel": ObjectCfg("wheel", "a humongous new wheel", "floor", "novelty"),
    "kite": ObjectCfg("kite", "a humongous novelty kite", "sky", "novelty"),
    "shell": ObjectCfg("shell", "a humongous polished shell", "path", "novelty"),
    "lantern": ObjectCfg("lantern", "a humongous bright lantern", "floor", "novelty"),
}

MYSTERIES = {
    "echo": MysteryCfg(
        label="echo",
        clue="soft footsteps echoed back",
        misunderstanding="the helper thought somebody else was hiding nearby",
        solve_action="follow the echo",
        reveal="it was only the humongous wheel rolling around a corner",
        risk="the helper worried the noise meant trouble",
    ),
    "shadow": MysteryCfg(
        label="shadow",
        clue="a long shadow moved across the floor",
        misunderstanding="the helper thought a stranger had arrived",
        solve_action="peek behind the cloth",
        reveal="it was just the novelty kite hanging from a hook",
        risk="the helper worried the shape meant a problem",
    ),
    "tapping": MysteryCfg(
        label="tapping",
        clue="a tapping sound came from the box",
        misunderstanding="the helper thought something was broken inside",
        solve_action="open the lid slowly",
        reveal="it was the lantern’s loose charm tapping the side",
        risk="the helper worried the box held a bad surprise",
    ),
}

CHILDREN = ["Ava", "Ben", "Mila", "Leo", "Nia", "Owen"]
HELPERS = ["grandpa", "aunt", "mom", "dad", "big sister", "teacher"]


@dataclass
class StoryParams:
    setting: str
    object: str
    mystery: str
    child: str
    helper: str
    seed: Optional[int] = None


def reasonableness_gate(setting: Setting, obj: ObjectCfg, mystery: MysteryCfg) -> bool:
    return obj.region in setting.covers and obj.novelty == "novelty" and mystery.label in MYSTERIES


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s_id, s in SETTINGS.items():
        for o_id, o in OBJECTS.items():
            for m_id, m in MYSTERIES.items():
                if reasonableness_gate(s, o, m):
                    out.append((s_id, o_id, m_id))
    return out


ASP_RULES = r"""
setting(S) :- setting_fact(S).
object(O) :- object_fact(O).
mystery(M) :- mystery_fact(M).

valid(S,O,M) :- setting(S), object(O), mystery(M),
                covers(S,R), worn_on(O,R), novelty(O).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting_fact", sid))
        for r in sorted(s.covers):
            lines.append(asp.fact("covers", sid, r))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object_fact", oid))
        lines.append(asp.fact("worn_on", oid, o.region))
        lines.append(asp.fact("novelty", oid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery_fact", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python gate:")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld with a mystery to solve.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--object", dest="object_", choices=OBJECTS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--child", choices=CHILDREN)
    ap.add_argument("--helper", choices=HELPERS)
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.object_ is None or c[1] == args.object_)
              and (args.mystery is None or c[2] == args.mystery)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, obj, mystery = rng.choice(sorted(combos))
    child = args.child or rng.choice(CHILDREN)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(setting=setting, object=obj, mystery=mystery, child=child, helper=helper)


def _say(world: World, text: str) -> None:
    world.say(text)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.setting])
    child = world.add(Entity(params.child, kind="character", type="boy" if params.child in {"Ben", "Leo", "Owen"} else "girl"))
    helper = world.add(Entity(params.helper, kind="character", type=params.helper if params.helper in {"grandpa", "mom", "dad", "aunt", "teacher"} else "helper"))
    obj_cfg = OBJECTS[params.object]
    myst = MYSTERIES[params.mystery]
    obj = world.add(Entity("object", type="thing", label=obj_cfg.label, phrase=obj_cfg.phrase, owner=child.id, caretaker=helper.id))

    child.memes["curiosity"] = 1
    obj.meters["novelty"] = 1
    _say(world, f"{child.id} was a curious child who liked tiny adventures and new surprises.")
    _say(world, f"One day, {child.id} found {obj_cfg.phrase} in {world.setting.place}.")
    _say(world, f"It looked {obj_cfg.size} and full of {obj_cfg.novelty}, so {child.id} wanted to explore it at once.")
    world.para()
    _say(world, f"Then the mystery began: {myst.clue}.")
    _say(world, f"{helper.id} gasped because {myst.risk}; {myst.misunderstanding}.")
    child.memes["problem_solving"] = 1
    world.para()
    _say(world, f"{child.id} did not rush away. Instead, {child.pronoun().capitalize()} chose to {myst.solve_action}.")
    _say(world, f"That slow look turned the clue into a real answer: {myst.reveal}.")
    helper.memes["relief"] = 1
    helper.memes["conflict"] = 0
    world.para()
    _say(world, f"{helper.id} smiled and laughed with relief, and the misunderstanding faded like a cloud.")
    _say(world, f"By the end, {child.id} had solved the mystery, and the humongous novelty was no longer strange at all.")

    world.facts.update(child=child, helper=helper, obj=obj, obj_cfg=obj_cfg, mystery=myst, setting=world.setting)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short adventure story for a young child about a {f["obj_cfg"].size} {f["obj_cfg"].novelty} that starts with a mystery and ends with a clear answer.',
        f"Tell a gentle mystery story where {f['child'].id} notices a strange new object in {world.setting.place} and helps {f['helper'].id} understand what it is.",
        f'Write a child-facing story that uses the words "period", "humongous", and "novelty" while showing a misunderstanding getting solved.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, helper, obj_cfg, myst = f["child"], f["helper"], f["obj_cfg"], f["mystery"]
    return [
        QAItem(
            question=f"What did {child.id} find in {world.setting.place}?",
            answer=f"{child.id} found {obj_cfg.phrase} in {world.setting.place}, and it seemed humongous and full of novelty.",
        ),
        QAItem(
            question=f"Why did {helper.id} feel worried?",
            answer=f"{helper.id} felt worried because {myst.risk}, and then there was a misunderstanding about what the strange clue meant.",
        ),
        QAItem(
            question=f"How was the mystery solved?",
            answer=f"{child.id} solved it by {myst.solve_action}, which showed that {myst.reveal}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does the word novelty mean?",
            answer="Novelty means something is new, unusual, or exciting because people have not seen it before.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a puzzle or unknown thing that makes people wonder and look for clues.",
        ),
        QAItem(
            question="What does humongous mean?",
            answer="Humongous means very, very big.",
        ),
        QAItem(
            question="What is a period in a story or time line?",
            answer="A period is a stretch of time or a part of a story when something is happening.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        out.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(out)


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
    StoryParams(setting="attic", object="wheel", mystery="echo", child="Ava", helper="grandpa"),
    StoryParams(setting="museum", object="lantern", mystery="tapping", child="Leo", helper="teacher"),
    StoryParams(setting="garden", object="kite", mystery="shadow", child="Mila", helper="mom"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            header = f"### {p.child}: {p.object} in {p.setting} (mystery: {p.mystery})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

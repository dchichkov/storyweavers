#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/slipper_involve_sciatica_curiosity_reconciliation_cautionary_mystery.py
=========================================================================================================

A standalone storyworld for a small mystery about a curious child, an odd
slipper clue, a cautious warning, and a reconciliation at the end.

The seed ingredients are treated as a tiny classical domain:
- slipper: a missing/borrowed household object that can hide a clue
- involve: the investigation may involve another person or object
- sciatica: an adult's sore leg/back condition that explains a limp and
  motivates caution, rest, and a kinder resolution

The story shape is intentionally mystery-like:
1. Curiosity notices a clue.
2. Caution prevents a reckless choice.
3. The mystery is solved by involving the right helper.
4. Reconciliation turns worry into understanding.

This script follows the Storyweavers storyworld contract:
- self-contained stdlib script
- imports storyworlds/results.py eagerly
- defines StoryParams, build_parser, resolve_params, generate, emit, main
- includes Python reasonableness gate plus inline ASP twin
- supports default run, -n, --all, --seed, --trace, --qa, --json,
  --asp, --verify, and --show-asp
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if "comfort" not in self.attrs:
            self.attrs["comfort"] = ""

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



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Scene:
    id: str
    place: str
    clue_spot: str
    mystery_line: str
    dark_hint: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    hidden: str
    belongs_to: str
    kind: str = "slipper"

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Concern:
    id: str
    speaker: str
    text: str
    caution: str
    risk: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Helper:
    id: str
    label: str
    action: str
    makes_reconcile: bool = True

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


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
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


SCENES = {
    "hallway": Scene("hallway", "the hallway", "by the front door", "The hallway felt like a clue all by itself.", "Something small was out of place."),
    "stairs": Scene("stairs", "the stairs", "on the second step", "The stairs held a tiny secret.", "A quiet problem seemed to wait there."),
    "porch": Scene("porch", "the porch", "beside the welcome mat", "The porch looked ordinary, but it was not.", "A little mystery had been left behind."),
}

CLUES = {
    "slipper": Clue("slipper", "slipper", "a single slipper", "under a bench", "its pair"),
    "slip_fall": Clue("slip_fall", "slipper", "a slipper with a scuff on the side", "near a chair", "its pair"),
    "soft_slipper": Clue("soft_slipper", "slipper", "a soft slipper with a frayed ribbon", "behind a plant", "its pair"),
}

CONCERNS = {
    "sciatica": Concern("sciatica", "parent", "their leg ached and moved slowly", "be careful", "a sore leg"),
    "tired_back": Concern("tired_back", "parent", "their back was stiff from a long day", "slow down", "a stiff back"),
}

HELPERS = {
    "sibling": Helper("sibling", "older sibling", "points out the clue"),
    "neighbor": Helper("neighbor", "kind neighbor", "shows where the slipper belongs"),
    "parent": Helper("parent", "parent", "explains the sore leg and the missing slipper"),
}


@dataclass
@dataclass
class StoryParams:
    scene: str
    clue: str
    concern: str
    helper: str
    child_name: str
    child_gender: str
    parent_gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for s in SCENES:
        for c in CLUES:
            for co in CONCERNS:
                for h in HELPERS:
                    combos.append((s, c, co, h))
    return combos


def reasonableness_gate(params: StoryParams) -> None:
    if params.clue not in CLUES:
        raise StoryError("Unknown clue.")
    if params.concern != "sciatica":
        raise StoryError("This storyworld keeps the mystery centered on sciatica.")
    if params.helper not in HELPERS:
        raise StoryError("Unknown helper.")
    if params.scene not in SCENES:
        raise StoryError("Unknown scene.")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A child curiosity mystery with a slipper clue and a cautious adult.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--concern", choices=CONCERNS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent-gender", choices=["mother", "father"], dest="parent_gender")
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


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SCENES:
        lines.append(asp.fact("scene", sid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("involves", cid, "slipper"))
    for coid in CONCERNS:
        lines.append(asp.fact("concern", coid))
        if coid == "sciatica":
            lines.append(asp.fact("cautionary", coid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, C, Co, H) :- scene(S), clue(C), concern(Co), helper(H), cautionary(Co).
solve(H) :- helper(H).
mystery(C) :- clue(C), involves(C, slipper).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_smoke() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show mystery/1.\n#show solve/1."))
    return sorted(set(asp.atoms(model, "mystery"))) + sorted(set(asp.atoms(model, "solve")))


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.concern and args.concern != "sciatica":
        raise StoryError("This storyworld only supports sciatica as the cautionary concern.")
    combos = [c for c in valid_combos()
              if (args.scene is None or c[0] == args.scene)
              and (args.clue is None or c[1] == args.clue)
              and (args.concern is None or c[2] == args.concern)
              and (args.helper is None or c[3] == args.helper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    scene, clue, concern, helper = rng.choice(sorted(combos))
    child_gender = args.gender or rng.choice(["girl", "boy"])
    parent_gender = args.parent_gender or rng.choice(["mother", "father"])
    name = args.name or rng.choice(["Mia", "Lily", "Zoe", "Ben", "Max", "Noah"])
    return StoryParams(scene, clue, concern, helper, name, child_gender, parent_gender)


def _child_pronouns(gender: str) -> tuple[str, str, str]:
    if gender == "girl":
        return "she", "her", "her"
    return "he", "him", "his"


def tell(params: StoryParams) -> World:
    world = World()
    child = world.add(Entity(params.child_name, "character", params.child_gender, role="curious"))
    parent = world.add(Entity("Parent", "character", params.parent_gender, label="the parent", role="cautionary"))
    clue = world.add(Entity("slipper", "thing", "thing", label=CLUES[params.clue].label))
    helper = world.add(Entity("Helper", "character", "boy", label=HELPERS[params.helper].label, role="helper"))
    scene = SCENES[params.scene]
    concern = CONCERNS[params.concern]

    child.memes["curiosity"] = 2
    parent.memes["caution"] = 2
    world.say(f"{child.id} wandered into {scene.place} because {scene.mystery_line}")
    world.say(f"Then {child.id} noticed {CLUES[params.clue].phrase} {CLUES[params.clue].hidden}.")
    world.para()
    world.say(f'"{CLUES[params.clue].label}?" {child.id} whispered. "{scene.dark_hint}"')
    world.say(f"{child.id} wanted to involve someone, because the clue felt important.")
    world.say(f"Their {parent.label_word} watched and said, \"{concern.text}. {concern.caution}.\"")
    child.memes["curiosity"] += 1
    parent.memes["caution"] += 1
    world.para()
    world.say(f"{child.id} listened, and the mystery grew gentler instead of bigger.")
    if params.helper == "sibling":
        world.say(f"An older sibling came over and pointed out that the slipper was its pair.")
    elif params.helper == "neighbor":
        world.say(f"A kind neighbor smiled and showed where the slipper belonged.")
    else:
        world.say(f"The parent sat down, explained the sore leg, and said the missing slipper had caused the worry.")
    world.say(f"That helped everyone {HELPERS[params.helper].action}, and the answer made sense at last.")
    world.para()
    child.memes["reconciliation"] += 1
    parent.memes["reconciliation"] += 1
    world.say(f"{child.id} and the parent made up with a hug.")
    world.say(f"By the end, the little slipper was back with its pair, and the room felt calm again.")
    world.facts.update(child=child, parent=parent, clue=clue, helper=helper, scene=scene, concern=concern)
    world.facts.update(outcome="reconciled", clue_word="slipper", involved=True, cautionary=True)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a mystery story for a 4-year-old that includes the word "slipper" and ends in reconciliation.',
        f"Tell a cautionary curiosity story where {f['child'].id} notices a slipper clue, involves a helper, and learns why a parent with sciatica must move carefully.",
        "Write a gentle mystery about a missing slipper, a careful warning, and a happy make-up at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    clue = f["clue"]
    helper = f["helper"]
    concern = f["concern"]
    return [
        QAItem(
            question="What did the child notice?",
            answer=f"{child.id} noticed a slipper clue. It looked out of place, so the child became curious and wanted to know more."
        ),
        QAItem(
            question="Why did the parent tell the child to be careful?",
            answer=f"The parent had sciatica, so {parent.pronoun('subject')} moved slowly and needed the child to slow down too. That caution kept the mystery calm instead of turnting into a tumble."
        ),
        QAItem(
            question="How was the mystery solved?",
            answer=f"They involved {helper.label}, who helped explain the clue and where it belonged. Once everyone understood the missing slipper, the worry faded."
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended with reconciliation. The child and the parent hugged, and the room felt peaceful again."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a slipper?", "A slipper is a soft shoe for indoors. People wear it at home to keep their feet warm."),
        QAItem("What is sciatica?", "Sciatica is a painful leg or back problem that can make walking slow and careful. A person with sciatica may need to rest and move gently."),
        QAItem("What does it mean to involve someone?", "To involve someone means to include them or ask them to help. In a mystery, involving the right helper can make the answer easier to find."),
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
    for e in list(world.entities.values()):
        bits = []
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("hallway", "slipper", "sciatica", "sibling", "Mia", "girl", "mother"),
    StoryParams("stairs", "soft_slipper", "sciatica", "neighbor", "Ben", "boy", "father"),
    StoryParams("porch", "slip_fall", "sciatica", "parent", "Lily", "girl", "mother"),
]


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in [(i.question, i.answer) for i in story_qa(world)]],
        world_qa=[QAItem(q, a) for q, a in [(i.question, i.answer) for i in world_knowledge_qa(world)]],
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


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    rc = 0
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in ASP parity.")
    try:
        _ = tell(CURATED[0])
        print("OK: normal generation smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def build_show_asp() -> str:
    return asp_program("#show valid/4.\n#show mystery/1.\n#show solve/1.")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(build_show_asp())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(facts := asp_valid_combos())
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for idx, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {idx + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()

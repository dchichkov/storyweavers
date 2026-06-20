#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/posey_bang_bathroom_mystery_to_solve_problem.py
================================================================================

A small standalone storyworld for a bathroom mystery adventure.

Premise:
- A curious child named Posey hears a loud "bang" in the bathroom.
- The mystery turns out to be a problem that can be solved with careful
  problem solving: something is stuck, fallen, or hidden.
- The story should feel like a tiny adventure with curiosity, clues, a turn,
  and a calm resolution.

The domain is intentionally small and classical:
- one bathroom
- a child
- one puzzling sound
- one small problem to solve
- one helpful fix

The words "posey" and "bang" are intentionally available as seed vocabulary and
can appear in the story or prompts.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
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
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, str] = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
class Clue:
    id: str
    label: str
    detail: str
    kind: str
    risky: bool = False
    helpful: bool = False

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Fix:
    id: str
    label: str
    method: str
    success: str
    fail: str
    power: int

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
@dataclass
class StoryParams:
    clue: str
    fix: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    posey = world.get("Posey")
    if posey.memes.get("curiosity", 0) >= THRESHOLD and posey.meters.get("confused", 0) >= THRESHOLD:
        if ("worry", "Posey") not in world.fired:
            world.fired.add(("worry", "Posey"))
            posey.memes["worry"] = posey.memes.get("worry", 0) + 1
            out.append("Posey felt brave enough to look closer.")
    return out


def _r_fix(world: World) -> list[str]:
    out: list[str] = []
    clue = world.get("clue")
    if clue.meters.get("stuck", 0) >= THRESHOLD and ("fix", clue.id) not in world.fired:
        world.fired.add(("fix", clue.id))
        clue.meters["fixed"] = clue.meters.get("fixed", 0) + 1
        out.append("The problem got solved.")
    return out


CAUSAL_RULES = [Rule("worry", _r_worry), Rule("fix", _r_fix)]


def solveable(clue: Clue, fix: Fix) -> bool:
    return clue.risky and fix.power >= 1


def choose_fix(clue: Clue, fix: Fix) -> bool:
    return clue.risky and fix.power >= 1


def tell(clue: Clue, fix: Fix, name: str, gender: str, parent: str) -> World:
    w = World()
    posey = w.add(Entity("Posey", kind="character", type=gender, role="hero", traits=["curious", "brave"]))
    grownup = w.add(Entity("Parent", kind="character", type=parent, role="helper", label="the parent"))
    mystery = w.add(Entity("clue", kind="thing", type="thing", label=clue.label))
    faucet = w.add(Entity("bathroom", kind="thing", type="room", label="the bathroom"))

    posey.memes["curiosity"] = 1.0
    mystery.meters["stuck"] = 1.0 if clue.risky else 0.0
    w.facts.update(name=name, gender=gender, parent=parent, clue=clue, fix=fix)

    w.say(f"Posey was in the bathroom when a loud bang came from near the {clue.label}.")
    w.say(f'{posey.id} tilted {posey.pronoun("possessive")} head. "What made that bang?" {posey.pronoun()} whispered.')
    w.say(f"{posey.id} looked under the sink, behind the towel rack, and beside the tub.")
    w.para()
    posey.meters["confused"] = 1.0
    propagate(w, narrate=True)
    w.say(f'Then {posey.id} found a clue: {clue.detail}.')
    w.say(f'"I think I can solve this," {posey.id} said, and called for {grownup.label_word}.')
    w.para()
    if clue.risky:
        w.say(f"{grownup.label_word.capitalize()} came over and used {fix.method}.")
        if fix.power >= 1:
            mystery.meters["stuck"] = 0.0
            mystery.meters["fixed"] = 1.0
            w.say(f"It worked at once: {fix.success}.")
            w.say(f"The bathroom was quiet again, and Posey smiled at the solved mystery.")
        else:
            w.say(f"But {fix.fail}.")
            w.say("The bang stayed a mystery, and Posey had to wait for a better idea.")
    else:
        w.say(f"{grownup.label_word.capitalize()} explained there was no real problem after all.")
        w.say("The bang had only been the shower curtain tapping the wall in the breeze.")
        w.say("Posey laughed, glad the mystery was tiny and harmless.")
    w.facts["solved"] = clue.risky and fix.power >= 1
    return w


CLUES = {
    "drawer": Clue("drawer", "drawer", "A toothbrush had slipped behind the drawer and knocked it shut.", "thing", risky=True),
    "soap": Clue("soap", "soap dish", "The soap dish had slid and tapped the sink with a little bang.", "thing", risky=True),
    "curtain": Clue("curtain", "shower curtain", "The shower curtain had blown into the wall and made the bang.", "thing", risky=False),
}

FIXES = {
    "open": Fix("open", "open the drawer", "carefully pull the drawer open", "the drawer opened and the toothbrush was easy to reach", "the drawer was still jammed", 1),
    "lift": Fix("lift", "lift the soap dish", "lift the soap dish and set it straight", "the soap dish settled neatly back in place", "it stayed wobbly and noisy", 1),
    "ignore": Fix("ignore", "ignore it", "do nothing", "nothing changed", "the sound kept happening", 0),
}

GIRL_NAMES = ["Posey", "Lily", "Mia", "Nora", "Ava"]
BOY_NAMES = ["Theo", "Ben", "Sam", "Leo", "Max"]
TRAITS = ["curious", "careful", "brave", "thoughtful"]


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for cid, clue in CLUES.items():
        for fid, fix in FIXES.items():
            if choose_fix(clue, fix):
                out.append((cid, fid))
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    clue: Clue = f["clue"]
    fix: Fix = f["fix"]
    return [
        f'Write an adventure story for a young child set in a bathroom, using the words "posey" and "bang".',
        f"Tell a small mystery about Posey hearing a bang in the bathroom and solving it by noticing {clue.label}.",
        f"Write a curious, child-friendly story where Posey investigates a bathroom bang and uses {fix.method} to fix the problem.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    clue: Clue = f["clue"]
    fix: Fix = f["fix"]
    items = [
        QAItem("Who is the story about?", "It is about Posey, a curious child who hears a strange bang in the bathroom."),
        QAItem("What mystery did Posey try to solve?", f"Posey tried to solve why the {clue.label} made a bang. The clue led Posey to the small problem hiding in the bathroom."),
    ]
    if f.get("solved"):
        items.append(QAItem("How did Posey solve the problem?", f"Posey called for the parent, and the parent used {fix.method}. That careful problem solving fixed the trouble and quieted the bathroom again."))
        items.append(QAItem("How did the story end?", "It ended with Posey smiling because the mystery was solved and the bathroom was calm again."))
    else:
        items.append(QAItem("Why was the problem not solved right away?", "The first idea was too weak, so the mystery stayed unsolved for a little while. Posey still stayed curious and kept looking for a better answer."))
    return items


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is curiosity?", "Curiosity is the feeling that makes you wonder, ask questions, and look closely to learn something new."),
        QAItem("What should you do when you hear a strange sound?", "You should stay calm, look carefully, and call a grown-up if you need help. That is a safe way to solve a mystery."),
        QAItem("What is problem solving?", "Problem solving is thinking step by step to find out what is wrong and how to fix it."),
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
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
risky_mystery(C) :- clue(C), risky(C).
solvable(C, F) :- clue(C), fix(F), risky(C), power(F, P), P >= 1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        if clue.risky:
            lines.append(asp.fact("risky", cid))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("power", fid, fix.power))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show solvable/2."))
    return sorted(set(asp.atoms(model, "solvable")))


@dataclass
class ArgsLike:
    pass

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in ASP gate:")
        print("  only in ASP:", sorted(cl - py))
        print("  only in Python:", sorted(py - cl))
    try:
        sample = generate(CURATED[0])
        assert sample.story
        print("OK: smoke test story generation succeeded.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bathroom mystery adventure storyworld.")
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    combos = [c for c in valid_combos()
              if (args.clue is None or c[0] == args.clue)
              and (args.fix is None or c[1] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    clue, fix = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or "Posey"
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(clue, fix, name, gender, parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(CLUES[params.clue], FIXES[params.fix], params.name, params.gender, params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


CURATED = [
    StoryParams("drawer", "open", "Posey", "girl", "mother"),
    StoryParams("soap", "lift", "Posey", "girl", "father"),
    StoryParams("curtain", "open", "Posey", "girl", "mother"),
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
        print(asp_program("#show solvable/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} solvable combos:")
        for c in combos:
            print(" ", c)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

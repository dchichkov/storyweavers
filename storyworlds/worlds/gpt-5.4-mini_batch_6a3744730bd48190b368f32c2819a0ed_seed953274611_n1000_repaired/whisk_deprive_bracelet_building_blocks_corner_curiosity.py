#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/whisk_deprive_bracelet_building_blocks_corner_curiosity.py
==========================================================================================

A tiny storyworld in a whodunit-like style: something goes missing from the
building blocks corner, a curious child notices the clue trail, and the missing
bracelet is recovered from the whisked-away hiding spot.

Seed words: whisk, deprive, bracelet
Setting: building blocks corner
Feature: Curiosity
Style note: whodunit
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
    tags: set[str] = field(default_factory=set)
    worn: bool = False
    held: bool = False

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
        return self.label or self.id
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class StoryParams:
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    adult_name: str
    adult_gender: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


@dataclass
class Rule:
    name: str
    apply: callable
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_suspicion(world: World) -> list[str]:
    out = []
    if world.get("bracelet").meters["missing"] >= THRESHOLD and ("suspicion",) not in world.fired:
        world.fired.add(("suspicion",))
        world.get("helper").memes["curiosity"] += 1
        world.get("child").memes["curiosity"] += 1
        out.append("__suspicion__")
    return out


def _r_reveal(world: World) -> list[str]:
    out = []
    if world.get("whisk").meters["moved"] >= THRESHOLD and world.get("bracelet").meters["missing"] >= THRESHOLD:
        if ("reveal",) not in world.fired:
            world.fired.add(("reveal",))
            out.append("__reveal__")
    return out


CAUSAL_RULES = [Rule("suspicion", _r_suspicion), Rule("reveal", _r_reveal)]


def propagate(world: World) -> None:
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True


def tell(params: StoryParams) -> World:
    w = World()
    child = w.add(Entity(id=params.child_name, kind="character", type=params.child_gender,
                         role="curious child", traits=["curious"]))
    helper = w.add(Entity(id=params.helper_name, kind="character", type=params.helper_gender,
                          role="helper", traits=["watchful"]))
    adult = w.add(Entity(id=params.adult_name, kind="character", type=params.adult_gender,
                         role="adult"))
    whisk = w.add(Entity(id="whisk", label="whisk", attrs={"setting": "building blocks corner"}))
    bracelet = w.add(Entity(id="bracelet", label="bracelet", attrs={"owner": child.id}))
    blocks = w.add(Entity(id="blocks", label="tower of blocks"))
    child.memes["curiosity"] = 2
    helper.memes["curiosity"] = 1

    w.say(
        f"In the building blocks corner, {child.id} and {helper.id} were stacking a little tower beside a shiny bracelet."
    )
    w.say(
        f"{child.id} was full of curiosity. {child.pronoun().capitalize()} kept looking at the blocks, the bracelet, and the strange whisk on the shelf."
    )

    w.para()
    w.say(
        f"Then the bracelet was gone. {helper.id} frowned and asked where it had gone, while {child.id} noticed a thin trail of blocks and dust."
    )
    bracelet.meters["missing"] += 1
    whisk.meters["moved"] += 1
    blocks.meters["scattered"] += 1
    propagate(w)

    w.para()
    w.say(
        f"{child.id} followed the clue, peered behind the whisk, and found the bracelet tucked in a small block cave."
    )
    bracelet.meters["missing"] = 0
    bracelet.meters["found"] += 1
    child.memes["joy"] += 1
    helper.memes["relief"] += 1
    adult.memes["approval"] += 1
    w.say(
        f"{adult.id} smiled, because nobody had been deprived of the bracelet for long, and the mystery was solved without a fuss."
    )

    w.facts.update(
        child=child, helper=helper, adult=adult, whisk=whisk, bracelet=bracelet, blocks=blocks,
        outcome="found"
    )
    return w


def valid_combos() -> list[tuple[str, str, str]]:
    return [("building blocks corner", "whisk", "bracelet")]


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("place", "building blocks_corner"),
        asp.fact("item", "whisk"),
        asp.fact("item", "bracelet"),
        asp.fact("curious", "child"),
        asp.fact("valid", "building_blocks_corner", "whisk", "bracelet"),
    ])


ASP_RULES = r"""
valid_story(P,I,B) :- valid(P,I,B), curious(child).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit storyworld in the building blocks corner.")
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--adult")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    if args.gender is not None and args.gender not in {"girl", "boy"}:
        raise StoryError("invalid gender")
    gender = args.gender or rng.choice(["girl", "boy"])
    helper_gender = "girl" if gender == "boy" else "boy"
    adult_gender = rng.choice(["mother", "father"])
    return StoryParams(
        child_name=args.name or rng.choice(["Mia", "Leo", "Nora", "Finn"]),
        child_gender=gender,
        helper_name=args.helper or rng.choice(["Ava", "Max", "June", "Owen"]),
        helper_gender=helper_gender,
        adult_name=args.adult or rng.choice(["Mom", "Dad"]),
        adult_gender=adult_gender,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a whodunit-style story for a child in the building blocks corner where a whisk, a bracelet, and curiosity all matter.",
        f"Tell a gentle mystery where {f['child'].id} notices what happened to the bracelet and solves it.",
        "Write a short story that includes whisk, deprive, bracelet, and a curious clue trail.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, helper, adult = f["child"], f["helper"], f["adult"]
    return [
        ("Who solved the mystery?", f"{child.id} solved it by following the clues and finding the bracelet in the blocks."),
        ("Why did the child keep looking around?", f"{child.id} was curious, so {child.pronoun()} noticed the whisk, the bracelet, and the little clue trail."),
        ("What happened to the bracelet at first?", "It was missing for a little while, which made everyone wonder where it had gone."),
        ("What did the adult do at the end?", f"{adult.id} smiled and helped turn the mystery into a calm ending once the bracelet was found."),
        ("How did the helper feel?", f"{helper.id} felt relieved when the bracelet turned up in the block cave."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a whisk?", "A whisk is a kitchen tool with thin wires that is used to mix things quickly."),
        ("What is curiosity?", "Curiosity is the feeling that makes you want to look, ask, and learn more."),
        ("What is a bracelet?", "A bracelet is a small piece of jewelry that you wear around your wrist."),
        ("What are building blocks?", "Building blocks are toys children stack and connect to make towers, roads, and pretend rooms."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("\n== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("\n== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        out.append(f"  {e.id}: meters={meters} memes={memes} role={e.role}")
    return "\n".join(out)


def explain_rejection() -> str:
    return "(No story: this world only supports the building blocks corner mystery with a whisk and a bracelet.)"


def resolve_valid(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def generate_one(args: argparse.Namespace, seed: int) -> StorySample:
    params = resolve_params(args, random.Random(seed))
    params.seed = seed
    return generate(params)


def verify() -> int:
    rc = 0
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        _ = sample.to_json()
        print("OK: smoke story generation works.")
    except Exception as e:
        print(f"FAIL: smoke story generation crashed: {e}")
        return 1
    try:
        py = set(valid_combos())
        aspc = set(asp_valid_combos())
        if py == aspc:
            print("OK: ASP and Python parity match.")
        else:
            print("FAIL: ASP/Python mismatch.")
            print("python:", sorted(py))
            print("asp:", sorted(aspc))
            rc = 1
    except Exception as e:
        print(f"FAIL: ASP verification crashed: {e}")
        rc = 1
    return rc


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
        print(asp_program("", "#show valid_story/3."))
        return
    if args.verify:
        sys.exit(verify())
    if args.asp:
        print("compatible story:", valid_combos()[0])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(
            child_name="Mia", child_gender="girl", helper_name="Owen", helper_gender="boy",
            adult_name="Mom", adult_gender="mother", seed=0
        ))]
    else:
        for i in range(args.n):
            samples.append(generate_one(args, base_seed + i))

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

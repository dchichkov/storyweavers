#!/usr/bin/env python3
"""
A storyworld about a curious child, a grocery store, and a mouldy discovery.

The seed tale premise:
A child goes to a grocery store, notices something mouldy, follows curiosity,
and learns how to handle it safely with a grown-up's help.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the grocery store"


@dataclass
class Curiosity:
    id: str
    verb: str
    gerund: str
    nudge: str
    search: str
    clue: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ObjectThing:
    id: str
    label: str
    phrase: str
    type: str
    location: str
    spoilable: bool = True
    plural: bool = False


@dataclass
class HelperPlan:
    id: str
    label: str
    step: str
    finish: str
    tag: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        import copy

        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        return w

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def _r_mould_spreads(world: World) -> list[str]:
    out: list[str] = []
    child = world.get(world.facts["child"].id)
    if child.meters.get("curiosity", 0.0) < THRESHOLD:
        return out
    if not world.facts.get("near_mould"):
        return out
    sig = ("mould_spread", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["alarm"] = child.meters.get("alarm", 0.0) + 1
    out.append("The closer the child leaned, the more certain it became that the spot was mouldy.")
    return out


def _r_helper_cleans(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("reported"):
        return out
    mould = world.get("mould")
    helper = world.get("helper")
    sig = ("helper", mould.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    mould.meters["removed"] = 1
    helper.meters["care"] = helper.meters.get("care", 0.0) + 1
    out.append(f"{helper.label.capitalize()} took the mouldy item away to the proper place.")
    return out


CAUSAL_RULES = [_r_mould_spreads, _r_helper_cleans]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell() -> World:
    world = World(Setting())
    child = world.add(Entity(id="child", kind="character", type="boy", label="Finn"))
    helper = world.add(Entity(id="helper", kind="character", type="mother", label="mom"))
    item = world.add(Entity(id="mould", type="item", label="mould", phrase="a mouldy orange", location="produce shelf"))
    snack = world.add(Entity(id="snack", type="item", label="cracker box", phrase="a box of crackers", location="next shelf"))

    world.facts["child"] = child
    world.facts["helper"] = helper
    world.facts["mould"] = item
    world.facts["snack"] = snack

    child.meters["curiosity"] = 1.0
    world.facts["near_mould"] = True

    world.say("Finn and his mom went to the grocery store for a small adventure.")
    world.say("Finn loved the bright aisles because every shelf seemed like it might hide a surprise.")
    world.say("Near the fruit, he noticed one orange with a fuzzy green patch.")
    world.para()
    world.say("Finn wanted to look closer. His curiosity tugged him forward, but his mom raised a hand and said, \"Don't touch that.\"")
    world.say("Finn tilted his head and asked why it looked strange.")
    propagate(world, narrate=True)
    world.say("Mom explained that mould can grow on old food, so it is safer to leave it alone and tell a grown-up.")
    world.say("Finn pointed instead of grabbing, and mom thanked him for using his curious eyes and safe hands.")
    world.para()
    world.facts["reported"] = True
    propagate(world, narrate=True)
    world.say("Together they told an employee, and the mouldy orange was taken away.")
    world.say("Finn left the grocery store feeling like a real explorer, because he had learned that curiosity is best when it stays careful.")
    world.say("At the end of the trip, the fruit shelf was tidy again, and Finn was proud of his brave, safe adventure.")

    world.facts.update(
        resolved=True,
        place=world.setting.place,
        curiosity="curiosity",
        setting=world.setting,
    )
    return world


SETTINGS = {"grocery_store": Setting(place="the grocery store")}

CURIOSITIES = {
    "mould": Curiosity(
        id="mould",
        verb="look closer",
        gerund="looking closer",
        nudge="a fuzzy spot on the orange",
        search="check the fruit",
        clue="a soft green fuzz",
        tags={"mould", "food"},
    ),
}

HELPERS = {
    "mom_help": HelperPlan(
        id="mom_help",
        label="a mom's help",
        step="tell a grown-up",
        finish="take the mouldy orange away",
        tag="care",
    )
}

ITEMS = {
    "orange": ObjectThing(
        id="orange",
        label="orange",
        phrase="a bright orange fruit",
        type="fruit",
        location="produce shelf",
    ),
    "cracker_box": ObjectThing(
        id="cracker_box",
        label="cracker box",
        phrase="a box of crackers",
        type="box",
        location="snack aisle",
        spoilable=False,
    ),
}


@dataclass
class StoryParams:
    setting: str = "grocery_store"
    curiosity: str = "mould"
    helper: str = "mom_help"
    seed: Optional[int] = None
    name: str = "Finn"
    gender: str = "boy"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A curious grocery store adventure about mould.")
    ap.add_argument("--setting", choices=SETTINGS.keys(), default="grocery_store")
    ap.add_argument("--curiosity", choices=CURIOSITIES.keys(), default="mould")
    ap.add_argument("--helper", choices=HELPERS.keys(), default="mom_help")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["boy", "girl"], default="boy")
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
    name = args.name or rng.choice(["Finn", "Mia", "Noah", "Ava", "Leo", "Zoe"])
    return StoryParams(
        setting=args.setting,
        curiosity=args.curiosity,
        helper=args.helper,
        seed=args.seed,
        name=name,
        gender=args.gender,
    )


def reasonableness_gate(params: StoryParams) -> None:
    if params.setting != "grocery_store":
        raise StoryError("This world only supports a grocery store setting.")
    if params.curiosity != "mould":
        raise StoryError("This storyworld is built around a mould discovery.")
    if params.helper != "mom_help":
        raise StoryError("Only the mom-help resolution is modeled here.")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    return [
        "Write a short adventurous story about a curious child in a grocery store who notices mould on food.",
        f"Tell a child-friendly adventure where {child.label} wants to look closer at something mouldy but learns to stay safe.",
        "Write a simple story set in a grocery store that shows curiosity, caution, and help from a grown-up.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    helper = world.facts["helper"]
    return [
        QAItem(
            question=f"Why did {child.label} want to look at the orange more closely?",
            answer=f"{child.label} was curious, and the fuzzy spot on the orange made him want to look closer.",
        ),
        QAItem(
            question="What did mom tell Finn to do instead of touching the mouldy food?",
            answer="She told him not to touch it and to tell a grown-up instead.",
        ),
        QAItem(
            question="What happened after they told an employee?",
            answer="The mouldy orange was taken away, and the fruit shelf was safe and tidy again.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is mould?",
            answer="Mould is a fuzzy growth that can appear on old or damp food and make it unsafe to eat.",
        ),
        QAItem(
            question="Why should children not touch mouldy food?",
            answer="Children should not touch mouldy food because it can be unsafe, and a grown-up should handle it.",
        ),
    ]


def asp_facts() -> str:
    import asp

    lines = [
        asp.fact("setting", "grocery_store"),
        asp.fact("curiosity", "mould"),
        asp.fact("helper", "mom_help"),
        asp.fact("has_place", "grocery_store", "produce"),
        asp.fact("has_mess", "mould"),
        asp.fact("has_resolution", "tell_grown_up"),
    ]
    return "\n".join(lines)


ASP_RULES = r"""
allowed_story(S) :- setting(S), curiosity(mould), helper(mom_help).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show allowed_story/1."))
    atoms = asp.atoms(model, "allowed_story")
    if atoms == [("grocery_store",)]:
        print("OK: ASP and Python gate agree.")
        return 0
    print("MISMATCH: ASP and Python gate disagree.")
    return 1


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = tell()
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


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
        print(asp_program("#show allowed_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show allowed_story/1."))
        print(asp.atoms(model, "allowed_story"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params_list = [StoryParams(setting="grocery_store", curiosity="mould", helper="mom_help", name=n) for n in ["Finn", "Mia", "Leo"]]
        samples = [generate(p) for p in params_list]
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

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

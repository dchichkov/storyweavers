#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/infect_wawa_empress_storage_closet_twist_adventure.py
==============================================================================================================

A small Adventure-style story world set in a storage closet.

Premise:
- A curious child, a brave helper named Wawa, and an empress costume figure
  share a storage closet full of boxes, labels, and old stage props.
- A tiny sticky "infect" on the labels makes one important box hard to open.
- The hero uses a tool called Twist to open the box and help the empress.

The story is generated from a compact world model with typed entities, physical
meters, and emotional memes. The state drives the prose: who is trapped, what is
stuck, what is missing, and how the fix changes the ending image.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carries: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "child", "kid"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def init_meter(self, key: str, value: float = 0.0) -> None:
        self.meters.setdefault(key, value)

    def init_meme(self, key: str, value: float = 0.0) -> None:
        self.memes.setdefault(key, value)


@dataclass
class Setting:
    place: str = "the storage closet"
    tight: bool = True
    affords: set[str] = field(default_factory=lambda: {"search", "open_box", "rescue"})


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps_with: set[str]
    twist: bool = False


@dataclass
class StoryParams:
    activity: str
    tool: str
    hero_name: str
    hero_type: str
    companion_name: str
    companion_type: str
    empress_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}
        self.fired: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

    def render_paragraphs(self) -> str:
        return self.render()

    def trace(self) -> str:
        out = ["--- world model state ---"]
        for e in self.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            bits = []
            if meters:
                bits.append(f"meters={meters}")
            if memes:
                bits.append(f"memes={memes}")
            out.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
        return "\n".join(out)


SETTINGS = {
    "storage_closet": Setting(),
}

TOOLS = {
    "Twist": Tool(
        id="Twist",
        label="Twist",
        phrase="a small Twist tool with a bright orange handle",
        helps_with={"open_box", "unstick", "rescue"},
        twist=True,
    ),
}

ACTIVITIES = {
    "adventure": "search the storage closet for the lost empress box",
}

NAMES = ["Mina", "Tara", "Niko", "Ivy", "June", "Arlo", "Lina", "Theo"]
COMPANIONS = ["Wawa"]
EMPRESS_NAMES = ["Empress Wawa", "Empress Luma", "Empress Aurelia"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [("storage_closet", "adventure", "Twist")]


def asp_facts() -> str:
    import asp

    lines = []
    lines.append(asp.fact("setting", "storage_closet"))
    lines.append(asp.fact("activity", "adventure"))
    lines.append(asp.fact("tool", "Twist"))
    lines.append(asp.fact("twist_tool", "Twist"))
    lines.append(asp.fact("affords", "storage_closet", "adventure"))
    lines.append(asp.fact("helps_with", "Twist", "open_box"))
    lines.append(asp.fact("helps_with", "Twist", "unstick"))
    lines.append(asp.fact("helps_with", "Twist", "rescue"))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,A,T) :- affords(S,A), twist_tool(T), helps_with(T,open_box), helps_with(T,rescue).
#show valid/3.
"""


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in ASP:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld set in a storage closet.")
    ap.add_argument("--activity", choices=ACTIVITIES.keys())
    ap.add_argument("--tool", choices=TOOLS.keys())
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("--empress", choices=EMPRESS_NAMES)
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
    if args.activity and args.activity != "adventure":
        raise StoryError("Only the adventure activity is valid in this storage-closet world.")
    if args.tool and args.tool != "Twist":
        raise StoryError("Only Twist is the reasonable tool for this story.")

    hero_type = args.gender or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(NAMES)
    companion_name = args.companion or "Wawa"
    empress_name = args.empress or rng.choice(EMPRESS_NAMES)
    return StoryParams(
        activity="adventure",
        tool="Twist",
        hero_name=hero_name,
        hero_type=hero_type,
        companion_name=companion_name,
        companion_type="companion",
        empress_name=empress_name,
    )


def valid_story_gate(params: StoryParams) -> None:
    if params.tool != "Twist":
        raise StoryError("This world needs Twist to solve the closet problem.")
    if params.activity != "adventure":
        raise StoryError("The story must be an Adventure.")
    if not params.empress_name:
        raise StoryError("An empress must be present in the storage closet story.")


def generate(params: StoryParams) -> StorySample:
    valid_story_gate(params)
    world = World(SETTINGS["storage_closet"])

    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    companion = world.add(Entity(id="Wawa", kind="character", type="companion", label=params.companion_name))
    empress = world.add(Entity(id="Empress", kind="character", type="empress", label=params.empress_name))
    box = world.add(Entity(id="Box", kind="thing", type="box", label="the old box", phrase="an old box"))
    label = world.add(Entity(id="Label", kind="thing", type="label", label="a sticky label", phrase="a sticky label"))
    twist = world.add(Entity(id="Twist", kind="thing", type="tool", label="Twist", phrase=TOOLS["Twist"].phrase))
    crown = world.add(Entity(id="Crown", kind="thing", type="crown", label="a silver crown", phrase="a silver crown"))

    twist.init_meter("used", 0)
    box.init_meter("stuck", 1)
    label.init_meter("sticky", 1)
    label.init_meter("infect", 1)  # seed word, child-friendly meaning: sticky spill spread onto the labels
    empress.init_meme("hope", 0)
    hero.init_meme("curiosity", 1)
    companion.init_meme("bravery", 1)

    world.say(
        f"{hero.id} stepped into the storage closet with {companion.id}, where old boxes leaned like sleepy towers."
    )
    world.say(
        f"On the top shelf sat {empress.label}, and {empress.label} looked worried because a sticky infect had spread over the box label."
    )
    world.say(
        f"{hero.id} wanted an adventure, and {companion.id} gave a brave little wawa cheer from the floor."
    )
    world.say(
        f"Then {hero.id} found {twist.phrase}. {hero.id} picked up Twist and turned it carefully against the stuck lid."
    )
    twist.meters["used"] += 1
    box.meters["stuck"] = 0
    label.meters["sticky"] = 0
    label.meters["infect"] = 0
    crown.meters["found"] = 1
    empress.memes["hope"] += 1
    hero.memes["curiosity"] += 1
    companion.memes["bravery"] += 1

    world.say(
        f"The lid popped open at last, and inside was {crown.label}. {empress.label} smiled so widely that the whole closet felt brighter."
    )
    world.say(
        f"{hero.id} carried {crown.label} down from the shelf, {companion.id} trotted beside {hero.id}, and the little crew turned the storage closet into a safe, happy treasure room."
    )

    world.facts.update(
        hero=hero,
        companion=companion,
        empress=empress,
        box=box,
        label=label,
        twist=twist,
        crown=crown,
        setting=world.setting,
        params=params,
    )

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short Adventure story about a storage closet, a brave helper named Wawa, and an empress with a stuck box.',
        f"Tell a child-friendly adventure where {f['hero'].id} uses Twist to open a box in the storage closet and help {f['empress'].label}.",
        'Write a gentle story that includes the words infect, wawa, empress, and Twist, and ends with a happy discovery.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    empress = f["empress"]
    twist = f["twist"]
    box = f["box"]
    crown = f["crown"]
    companion = f["companion"]
    return [
        QAItem(
            question=f"Who went into the storage closet for the adventure?",
            answer=f"{hero.id} went into the storage closet with {companion.id}.",
        ),
        QAItem(
            question=f"What did {hero.id} use to open the stuck box?",
            answer=f"{hero.id} used {twist.label} to turn the stuck lid until it opened.",
        ),
        QAItem(
            question=f"What did they find inside the box?",
            answer=f"They found {crown.label} inside the box for {empress.label}.",
        ),
        QAItem(
            question=f"Why was the box hard to open?",
            answer="A sticky infect spread over the label and made the lid stick shut.",
        ),
        QAItem(
            question=f"How did the story end for {empress.label}?",
            answer=f"{empress.label} smiled, because the crown was safe again and the storage closet felt bright and happy.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a storage closet?",
            answer="A storage closet is a small room for keeping boxes, tools, and other things that are not being used right now.",
        ),
        QAItem(
            question="What is a twist tool for?",
            answer="A Twist tool can help turn, loosen, or open something that is stuck.",
        ),
        QAItem(
            question="What does a helper like Wawa do in an adventure?",
            answer="A helper like Wawa can cheer, search, and stay brave while the hero solves a problem.",
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
    lines.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(sample.world.trace())
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(
        activity="adventure",
        tool="Twist",
        hero_name="Mina",
        hero_type="girl",
        companion_name="Wawa",
        companion_type="companion",
        empress_name="Empress Wawa",
    )
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
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
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

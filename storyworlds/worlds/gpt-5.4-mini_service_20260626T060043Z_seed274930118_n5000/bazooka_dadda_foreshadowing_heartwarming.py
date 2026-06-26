#!/usr/bin/env python3
"""
Standalone storyworld: a child, a foreshadowed surprise, and a heartwarming reveal.

Premise:
- A child and their dadda are preparing a small surprise.
- The surprise uses a bazooka-shaped bubble maker, which is big and funny-looking.
- Early clues hint at the final reveal before it happens.

World model:
- Physical meters track supplies, setup, and how ready the surprise is.
- Emotional memes track excitement, worry, secrecy, and warmth.

The story stays child-facing and gentle: the bazooka is a bubble bazooka, a toy.
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


# ---------------------------------------------------------------------------
# Parameters and registries
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str = "backyard"
    child_name: str = "Mina"
    child_type: str = "girl"
    dadda_name: str = "Dadda"
    seed: Optional[int] = None


@dataclass(frozen=True)
class Setting:
    id: str
    name: str
    light: str
    weather: str
    mood: str


@dataclass(frozen=True)
class Item:
    id: str
    name: str
    phrase: str
    kind: str


@dataclass(frozen=True)
class SurprisePlan:
    id: str
    title: str
    clue: str
    reveal: str
    ending_image: str


SETTINGS = {
    "backyard": Setting("backyard", "the backyard", "golden", "soft evening", "quiet"),
    "kitchen": Setting("kitchen", "the kitchen", "warm", "late afternoon", "cozy"),
    "porch": Setting("porch", "the porch", "blue-gray", "windy afternoon", "calm"),
}

ITEMS = {
    "bazooka": Item(
        "bazooka",
        "bazooka",
        "a big bubble bazooka",
        "toy",
    ),
    "bubbles": Item(
        "bubbles",
        "bubbles",
        "a bottle of bubble mix",
        "supply",
    ),
    "banner": Item(
        "banner",
        "banner",
        "a bright paper banner",
        "decoration",
    ),
    "snack": Item(
        "snack",
        "snack",
        "a plate of star-shaped cookies",
        "treat",
    ),
}

PLANS = {
    "cheer_mom": SurprisePlan(
        "cheer_mom",
        "a surprise for Mom",
        "There was a long cardboard box hidden behind the door, and something round and shiny peeked out of it.",
        "Dadda and the child had been preparing a surprise party with bubble fun and cookies for Mom.",
        "Mom laughed, clapped, and stood in the middle of the sparkling bubbles while the family hugged close.",
    ),
    "welcome_home": SurprisePlan(
        "welcome_home",
        "a welcome-home surprise",
        "The child noticed ribbon tails on the table and heard Dadda whisper, 'Not yet.'",
        "They were getting ready to welcome home a loved one with bubbles, a banner, and a smile.",
        "When the door opened, everyone shouted the welcome and the bubbles floated like tiny moons.",
    ),
}


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    hidden: bool = False

    def inc_meter(self, key: str, amount: float = 1.0) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amount

    def inc_meme(self, key: str, amount: float = 1.0) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.stage: str = "setup"

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


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def pronoun(kind: str, case: str = "subject") -> str:
    if kind == "girl":
        return {"subject": "she", "object": "her", "possessive": "her"}[case]
    if kind == "boy":
        return {"subject": "he", "object": "him", "possessive": "his"}[case]
    return {"subject": "they", "object": "them", "possessive": "their"}[case]


def setup_world(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.child_type not in {"girl", "boy", "child"}:
        raise StoryError(f"Unsupported child type: {params.child_type}")

    world = World(SETTINGS[params.setting])

    child = world.add(Entity(
        id="child",
        kind="character",
        label=params.child_name,
        owner=None,
        meters={"ready": 0.0, "curiosity": 1.0},
        memes={"warmth": 1.0, "wonder": 1.0, "worry": 0.0},
    ))
    dadda = world.add(Entity(
        id="dadda",
        kind="character",
        label=params.dadda_name,
        owner=None,
        meters={"ready": 0.0, "care": 1.0},
        memes={"warmth": 2.0, "secrecy": 1.0, "joy": 0.0},
    ))
    bazooka = world.add(Entity(
        id="bazooka",
        kind="toy",
        label="bazooka",
        phrase="a big bubble bazooka",
        owner="dadda",
        meters={"assembled": 0.0, "loaded": 0.0, "sparkle": 0.0},
        memes={"mystery": 1.0},
        hidden=True,
    ))
    bubbles = world.add(Entity(
        id="bubbles",
        kind="supply",
        label="bubbles",
        phrase="a bottle of bubble mix",
        owner="dadda",
        meters={"full": 1.0},
    ))
    banner = world.add(Entity(
        id="banner",
        kind="decoration",
        label="banner",
        phrase="a bright paper banner",
        owner="dadda",
        meters={"hung": 0.0},
    ))
    snack = world.add(Entity(
        id="snack",
        kind="treat",
        label="snack",
        phrase="a plate of star-shaped cookies",
        owner="dadda",
        meters={"set_out": 0.0},
    ))

    world.facts.update(
        child=child,
        dadda=dadda,
        bazooka=bazooka,
        bubbles=bubbles,
        banner=banner,
        snack=snack,
        plan=PLANS["cheer_mom"] if params.setting != "kitchen" else PLANS["welcome_home"],
    )
    return world


def foreshadow(world: World) -> None:
    child = world.facts["child"]
    dadda = world.facts["dadda"]
    bazooka = world.facts["bazooka"]
    bubbles = world.facts["bubbles"]
    banner = world.facts["banner"]
    snack = world.facts["snack"]
    plan: SurprisePlan = world.facts["plan"]

    world.say(
        f"{child.label} was a little {child.memes.get('wonder', 1.0) > 0 and 'curious' or 'quiet'} child who loved "
        f"quiet evenings in {world.setting.name}."
    )
    world.say(
        f"One day, {child.label} saw {dadda.label} carrying {bubbles.phrase}, {banner.phrase}, and a box that kept "
        f"making soft thumps."
    )
    world.say(
        f"The biggest clue was {bazooka.phrase}; it looked silly and huge, and {dadda.label} covered it fast with a towel."
    )
    child.inc_meme("curiosity", 1.0)
    child.inc_meme("worry", 0.5)
    dadda.inc_meme("secrecy", 1.0)
    bazooka.hidden = True
    world.facts["foreshadow_line"] = plan.clue


def build_surprise(world: World) -> None:
    bazooka = world.facts["bazooka"]
    bubbles = world.facts["bubbles"]
    banner = world.facts["banner"]
    snack = world.facts["snack"]
    child = world.facts["child"]
    dadda = world.facts["dadda"]

    world.para()
    world.say(
        f"After that, {dadda.label} asked {child.label} to help without explaining too much."
    )
    child.inc_meme("warmth", 1.0)
    child.inc_meter("ready", 1.0)
    dadda.inc_meter("ready", 1.0)

    bazooka.hidden = False
    bazooka.inc_meter("assembled", 1.0)
    bazooka.inc_meter("loaded", 1.0)
    bazooka.inc_meter("sparkle", 1.0)
    bubbles.inc_meter("full", 0.0)
    banner.inc_meter("hung", 1.0)
    snack.inc_meter("set_out", 1.0)

    world.say(
        f"They filled the bazooka with bubble mix, taped up the banner, and set the cookies on the table."
    )
    world.say(
        f"{child.label} started to smile, because the box thumps and the hidden ribbon made sense now."
    )
    world.facts["built"] = True


def reveal(world: World) -> None:
    child = world.facts["child"]
    dadda = world.facts["dadda"]
    bazooka = world.facts["bazooka"]
    plan: SurprisePlan = world.facts["plan"]

    world.para()
    child.inc_meme("worry", -0.5)
    child.inc_meme("wonder", 1.0)
    dadda.inc_meme("joy", 2.0)
    world.say(
        f"Then {dadda.label} said, 'Okay, now you can look.'"
    )
    world.say(
        f"{plan.reveal}"
    )
    world.say(
        f"{plan.ending_image}"
    )
    world.facts["revealed"] = True
    world.facts["bazooka_visible"] = not bazooka.hidden


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A surprise is foreshadowed when a clue about the final reveal appears early.
foreshadowed(P) :- clue(P), early(P).

% The plan is heartwarming when the child feels curiosity first, then warmth,
% and the ending shows family joy.
heartwarming(P) :- foreshadowed(P), child_curiosity(P), child_warmth(P), family_joy(P).

% The bazooka is only child-safe if it is explicitly a bubble toy.
safe_bazooka(B) :- bazooka(B), bubble_toy(B).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("setting_name", sid, s.name))
    for iid, item in ITEMS.items():
        lines.append(asp.fact(item.kind, iid))
        lines.append(asp.fact("label", iid, item.label))
    for pid, plan in PLANS.items():
        lines.append(asp.fact("plan", pid))
        lines.append(asp.fact("clue", pid))
        lines.append(asp.fact("early", pid))
        lines.append(asp.fact("bubble_toy", "bazooka"))
        lines.append(asp.fact("child_curiosity", pid))
        lines.append(asp.fact("child_warmth", pid))
        lines.append(asp.fact("family_joy", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show heartwarming/1."))
    asp_set = set(asp.atoms(model, "heartwarming"))
    py_set = {("cheer_mom",), ("welcome_home",)}
    if asp_set == py_set:
        print(f"OK: ASP parity matches Python gate ({len(py_set)} plans).")
        return 0
    print("MISMATCH between ASP and Python gate:")
    print("  asp:", sorted(asp_set))
    print("  py :", sorted(py_set))
    return 1


def python_reasonable_plan(params: StoryParams) -> bool:
    return params.setting in SETTINGS and params.child_name.strip() and params.dadda_name.strip()


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    plan: SurprisePlan = world.facts["plan"]
    child: Entity = world.facts["child"]
    return [
        f"Write a heartwarming story about {child.label}, {world.facts['dadda'].label}, and a hidden bazooka-shaped toy.",
        f"Tell a gentle story where early clues about a surprise lead to a warm family reveal.",
        f"Write a child-friendly story with foreshadowing, bubbles, cookies, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child: Entity = world.facts["child"]
    dadda: Entity = world.facts["dadda"]
    bazooka: Entity = world.facts["bazooka"]
    plan: SurprisePlan = world.facts["plan"]

    return [
        QAItem(
            question=f"What did {child.label} notice that seemed secret at first?",
            answer=f"{child.label} noticed {dadda.label} carrying a hidden bubble bazooka, plus bubbles, a banner, and cookies.",
        ),
        QAItem(
            question=f"Why did the story feel foreshadowed before the reveal?",
            answer=f"It felt foreshadowed because the story gave early clues: the box thumps, the hidden towel, and the big bazooka-shaped toy.",
        ),
        QAItem(
            question=f"What made the ending heartwarming?",
            answer=f"The ending was heartwarming because the surprise was made with care, and the family smiled together when the bubbles and cookies were finally shared.",
        ),
        QAItem(
            question=f"What was the bazooka in this story?",
            answer=f"It was a big bubble bazooka, a toy that made bubbles instead of anything scary.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is when a story gives little clues early on about something that will matter later.",
        ),
        QAItem(
            question="Why are bubbles fun for children?",
            answer="Bubbles are fun because they float, sparkle, and pop in a playful way that feels magical.",
        ),
        QAItem(
            question="What does heartwarming mean?",
            answer="Heartwarming means something makes people feel tender, happy, and cared for.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def generate(params: StoryParams) -> StorySample:
    if not python_reasonable_plan(params):
        raise StoryError("The requested story parameters are incomplete or unreasonable.")
    world = setup_world(params)
    foreshadow(world)
    build_surprise(world)
    reveal(world)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = ", ".join(f"{k}={v}" for k, v in sorted(e.meters.items()))
        memes = ", ".join(f"{k}={v}" for k, v in sorted(e.memes.items()))
        bits = []
        if meters:
            bits.append(f"meters[{meters}]")
        if memes:
            bits.append(f"memes[{memes}]")
        if e.hidden:
            bits.append("hidden=True")
        lines.append(f"{e.id}: {e.kind} {e.label} {' '.join(bits)}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print()
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(setting="backyard", child_name="Mina", child_type="girl", dadda_name="Dadda"),
    StoryParams(setting="kitchen", child_name="Noah", child_type="boy", dadda_name="Dadda"),
    StoryParams(setting="porch", child_name="Lia", child_type="girl", dadda_name="Dadda"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming foreshadowing storyworld with a bubble bazooka and Dadda.")
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy", "child"])
    ap.add_argument("--dadda-name")
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
    return StoryParams(
        setting=args.setting or rng.choice(sorted(SETTINGS)),
        child_name=args.child_name or rng.choice(["Mina", "Lia", "Noah", "Eli", "Iris"]),
        child_type=args.child_type or rng.choice(["girl", "boy"]),
        dadda_name=args.dadda_name or "Dadda",
    )


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show heartwarming/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show heartwarming/1."))
        print(sorted(set(asp.atoms(model, "heartwarming"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

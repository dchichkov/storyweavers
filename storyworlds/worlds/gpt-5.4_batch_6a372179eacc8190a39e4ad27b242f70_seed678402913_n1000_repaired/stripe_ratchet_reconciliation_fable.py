#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/stripe_ratchet_reconciliation_fable.py
=================================================================

A standalone storyworld for a small fable domain about two animal neighbors who
quarrel after a cart spills on the road, then reconcile by using a cloth marked
with a stripe and a ratchet tool together.

The world model prefers plausible, cooperative repairs:
- the cloth must be large enough to gather the spilled cargo
- the ratchet tool must be strong enough to steady the cart on that road

Every valid story ends in reconciliation, but the apology beat and the details
of repair vary with the simulated state.

Run it
------
python storyworlds/worlds/gpt-5.4/stripe_ratchet_reconciliation_fable.py
python storyworlds/worlds/gpt-5.4/stripe_ratchet_reconciliation_fable.py --all
python storyworlds/worlds/gpt-5.4/stripe_ratchet_reconciliation_fable.py --setting brook_path --cargo apples
python storyworlds/worlds/gpt-5.4/stripe_ratchet_reconciliation_fable.py --stripe_item kerchief   # may be rejected
python storyworlds/worlds/gpt-5.4/stripe_ratchet_reconciliation_fable.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/stripe_ratchet_reconciliation_fable.py --verify
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
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.attrs.get("plural") else "it"


@dataclass
class Setting:
    id: str
    place: str
    path_phrase: str
    destination: str
    bump: int
    weather: str
    image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Cargo:
    id: str
    label: str
    phrase: str
    plural: bool
    bulk: int
    scatter: str
    gathered_as: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StripeItem:
    id: str
    label: str
    phrase: str
    size: int
    stripe_text: str
    wrap_text: str
    ending_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class RatchetTool:
    id: str
    label: str
    phrase: str
    power: int
    click_text: str
    tighten_text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    advice: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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


def cargo_fits(stripe_item: StripeItem, cargo: Cargo) -> bool:
    return stripe_item.size >= cargo.bulk


def tool_holds(tool: RatchetTool, setting: Setting, cargo: Cargo) -> bool:
    need = setting.bump + cargo.bulk - 1
    return tool.power >= need


def valid_combo(setting: Setting, cargo: Cargo, stripe_item: StripeItem, tool: RatchetTool) -> bool:
    return cargo_fits(stripe_item, cargo) and tool_holds(tool, setting, cargo)


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for cargo_id, cargo in CARGOS.items():
            for stripe_id, stripe_item in STRIPE_ITEMS.items():
                for tool_id, tool in TOOLS.items():
                    if valid_combo(setting, cargo, stripe_item, tool):
                        out.append((setting_id, cargo_id, stripe_id, tool_id))
    return out


def explain_rejection(setting: Setting, cargo: Cargo, stripe_item: StripeItem, tool: RatchetTool) -> str:
    reasons: list[str] = []
    if not cargo_fits(stripe_item, cargo):
        reasons.append(
            f"{stripe_item.phrase} is too small to gather {cargo.phrase} after a spill"
        )
    if not tool_holds(tool, setting, cargo):
        need = setting.bump + cargo.bulk - 1
        reasons.append(
            f"{tool.phrase} is too weak for {setting.path_phrase} with {cargo.phrase} "
            f"(needs power {need}, has {tool.power})"
        )
    if not reasons:
        reasons.append("this combination does not make a sensible repair")
    return "(No story: " + "; ".join(reasons) + ".)"


def opening_scene(world: World, a: Entity, b: Entity, cargo: Cargo, stripe_item: StripeItem, tool: RatchetTool) -> None:
    cart = world.get("cart")
    a.memes["hope"] += 1
    b.memes["hope"] += 1
    world.say(
        f"In {world.setting.place}, {a.id} and {b.id} shared a little cart and a plan. "
        f"They were taking {cargo.phrase} to {world.setting.destination}, and the day "
        f"looked gentle enough for singing."
    )
    world.say(
        f"Folded in the cart lay {stripe_item.phrase}; {stripe_item.stripe_text}. "
        f"Beside it hung {tool.phrase}, ready to click if patient paws used it well."
    )
    cart.meters["loaded"] += 1
    world.say(world.setting.image)


def hurry_and_loosen(world: World, a: Entity, b: Entity, tool: RatchetTool) -> None:
    cart = world.get("cart")
    cart.meters["loose"] += 1
    a.memes["pride"] += a.attrs["pride"]
    b.memes["pride"] += b.attrs["pride"]
    world.say(
        f"But each wanted to be the cleverer driver. {a.id} said the cart should be tied one way, "
        f"and {b.id} said another. {tool.click_text.capitalize()} sounded only twice before they stopped "
        f"listening to each other, and the last good pull was never made."
    )


def spill(world: World, a: Entity, b: Entity, cargo: Cargo) -> None:
    cart = world.get("cart")
    load = world.get("load")
    if cart.meters["loose"] < THRESHOLD:
        return
    load.meters["spilled"] += 1
    cart.meters["stable"] = 0.0
    a.memes["anger"] += 1
    b.memes["anger"] += 1
    a.memes["hurt"] += 1
    b.memes["hurt"] += 1
    world.say(
        f"When they reached {world.setting.path_phrase}, a hard bump shook the wheels. "
        f"The cart tipped sideways, and {cargo.scatter}."
    )


def quarrel(world: World, a: Entity, b: Entity) -> None:
    friendship = world.get("friendship")
    friendship.meters["distance"] += 1
    a.memes["cooperation"] = 0.0
    b.memes["cooperation"] = 0.0
    world.say(
        f'"You pulled too fast," said {a.id}. "{b.id}, you did not hold the line." '
        f'"And you would not wait," said {b.id}. Their voices grew sharp, and the road felt wider between them.'
    )


def fail_alone(world: World, a: Entity, b: Entity, cargo: Cargo, stripe_item: StripeItem, tool: RatchetTool) -> None:
    world.say(
        f"{a.id} tried to gather {cargo.gathered_as} with one pair of paws, while {b.id} tugged at "
        f"{tool.label} alone. Yet {stripe_item.label} slid crooked, the wheel still wobbled, and neither "
        f"animal could set the cart right without the other."
    )
    world.get("cart").meters["stuck"] += 1


def helper_arrives(world: World, helper: Helper, cargo: Cargo) -> None:
    world.say(
        f"Just then {helper.phrase} paused by the road. {helper.advice} "
        f"{helper.label.capitalize()} looked at {cargo.gathered_as} on the ground and then at the two stiff backs."
    )


def choose_first_apology(a: Entity, b: Entity) -> tuple[Entity, Entity]:
    score_a = a.attrs["kindness"] - a.attrs["pride"]
    score_b = b.attrs["kindness"] - b.attrs["pride"]
    if score_a > score_b:
        return a, b
    if score_b > score_a:
        return b, a
    if a.id <= b.id:
        return a, b
    return b, a


def reconcile(world: World, first: Entity, second: Entity) -> None:
    friendship = world.get("friendship")
    first.memes["shame"] += 1
    second.memes["shame"] += 1
    first.memes["anger"] = 0.0
    second.memes["anger"] = 0.0
    first.memes["cooperation"] += 1
    second.memes["cooperation"] += 1
    friendship.meters["distance"] = 0.0
    friendship.meters["mended"] += 1
    world.say(
        f"{first.id} lowered {first.pronoun('possessive')} head first. "
        f'"I am sorry," said {first.id}. "I cared more about being right than about helping."'
    )
    world.say(
        f"{second.id} looked at the spilled road, then at {first.id}. "
        f'"I am sorry too," said {second.id}. "I pulled against you when I should have pulled with you."'
    )


def repair(world: World, a: Entity, b: Entity, cargo: Cargo, stripe_item: StripeItem, tool: RatchetTool) -> None:
    cart = world.get("cart")
    load = world.get("load")
    load.meters["spilled"] = 0.0
    load.meters["gathered"] += 1
    cart.meters["stable"] += 1
    cart.meters["loose"] = 0.0
    world.say(
        f"Then they worked the way friends should. {a.id} and {b.id} spread {stripe_item.phrase} on the dust, "
        f"{stripe_item.wrap_text}, and lifted the bundle back into the cart together."
    )
    world.say(
        f"After that, one held the wheel steady while the other pulled {tool.label}. "
        f"{tool.click_text.capitalize()} went again and again until the cart stood firm."
    )


def ending(world: World, a: Entity, b: Entity, cargo: Cargo, stripe_item: StripeItem) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    a.memes["trust"] += 1
    b.memes["trust"] += 1
    world.say(
        f"By the time they reached {world.setting.destination}, the road no longer felt split in two. "
        f"{cargo.ending_image}, and {stripe_item.ending_text} above them like a small flag of peace."
    )
    world.say(
        f"So the two neighbors learned that pride can spill a cart, but apology and shared work can set it upright again."
    )


def tell(
    setting: Setting,
    cargo: Cargo,
    stripe_item: StripeItem,
    tool: RatchetTool,
    helper: Helper,
    animal1_name: str,
    animal1_type: str,
    animal2_name: str,
    animal2_type: str,
    pride1: int,
    pride2: int,
    kindness1: int,
    kindness2: int,
) -> World:
    world = World(setting=setting)
    a = world.add(
        Entity(
            id=animal1_name,
            kind="character",
            type=animal1_type,
            role="friend_a",
            label=animal1_name,
            attrs={"pride": pride1, "kindness": kindness1},
        )
    )
    b = world.add(
        Entity(
            id=animal2_name,
            kind="character",
            type=animal2_type,
            role="friend_b",
            label=animal2_name,
            attrs={"pride": pride2, "kindness": kindness2},
        )
    )
    world.add(Entity(id="cart", type="cart", label="cart"))
    world.add(
        Entity(
            id="load",
            type="cargo",
            label=cargo.label,
            attrs={"plural": cargo.plural},
        )
    )
    world.add(Entity(id="friendship", type="bond", label="friendship"))
    world.facts.update(
        setting=setting,
        cargo=cargo,
        stripe_item=stripe_item,
        tool=tool,
        helper=helper,
        animal1=a,
        animal2=b,
    )

    opening_scene(world, a, b, cargo, stripe_item, tool)
    hurry_and_loosen(world, a, b, tool)
    world.para()
    spill(world, a, b, cargo)
    quarrel(world, a, b)
    fail_alone(world, a, b, cargo, stripe_item, tool)
    world.para()
    helper_arrives(world, helper, cargo)
    first, second = choose_first_apology(a, b)
    reconcile(world, first, second)
    world.facts["first_apology"] = first.id
    world.para()
    repair(world, a, b, cargo, stripe_item, tool)
    ending(world, a, b, cargo, stripe_item)
    world.facts["reconciled"] = world.get("friendship").meters["mended"] >= THRESHOLD
    world.facts["stable"] = world.get("cart").meters["stable"] >= THRESHOLD
    world.facts["gathered"] = world.get("load").meters["gathered"] >= THRESHOLD
    return world


SETTINGS = {
    "meadow_lane": Setting(
        id="meadow_lane",
        place="a green meadow",
        path_phrase="the rutted lane by the meadow hedge",
        destination="the hollow market",
        bump=1,
        weather="clear",
        image="Larks sang overhead, and even the stones seemed sleepy in the sun.",
        tags={"road", "market"},
    ),
    "brook_path": Setting(
        id="brook_path",
        place="a brookside path",
        path_phrase="the rooty path beside the brook",
        destination="the willow fair",
        bump=2,
        weather="breezy",
        image="The brook chattered beside them, and the path curled around wet roots.",
        tags={"brook", "road"},
    ),
    "hill_road": Setting(
        id="hill_road",
        place="a windy hill",
        path_phrase="the steep road over the windy hill",
        destination="the stone square",
        bump=3,
        weather="windy",
        image="Wind brushed the grass flat, and the road climbed in patient, stony steps.",
        tags={"hill", "road"},
    ),
}

CARGOS = {
    "berries": Cargo(
        id="berries",
        label="berries",
        phrase="a basket of berries",
        plural=True,
        bulk=1,
        scatter="red berries pattered over the ground like marbles",
        gathered_as="the berries",
        ending_image="The berries rode safely at last",
        tags={"berries", "cart"},
    ),
    "apples": Cargo(
        id="apples",
        label="apples",
        phrase="two shiny apples and a sack of windfalls",
        plural=True,
        bulk=2,
        scatter="the apples rolled into the grass and the sack split at the mouth",
        gathered_as="the apples and the split sack",
        ending_image="The apples no longer knocked against one another in worry",
        tags={"apples", "cart"},
    ),
    "nuts": Cargo(
        id="nuts",
        label="nuts",
        phrase="a heavy sack of nuts",
        plural=True,
        bulk=2,
        scatter="the sack burst, and nuts bounced into every little ditch and hoofprint",
        gathered_as="the loose nuts",
        ending_image="The nuts sat quiet in their tied bundle",
        tags={"nuts", "cart"},
    ),
    "pumpkins": Cargo(
        id="pumpkins",
        label="pumpkins",
        phrase="two round pumpkins",
        plural=True,
        bulk=3,
        scatter="the pumpkins lurched out and thumped into the dust",
        gathered_as="the pumpkins",
        ending_image="The pumpkins rode side by side without wobbling",
        tags={"pumpkins", "cart"},
    ),
}

STRIPE_ITEMS = {
    "kerchief": StripeItem(
        id="kerchief",
        label="kerchief",
        phrase="a small kerchief",
        size=1,
        stripe_text="A single blue stripe crossed it from corner to corner",
        wrap_text="tucked the fruit into its corners",
        ending_text="the blue stripe fluttered",
        tags={"stripe", "cloth"},
    ),
    "blanket": StripeItem(
        id="blanket",
        label="blanket",
        phrase="a soft travel blanket",
        size=2,
        stripe_text="A warm gold stripe ran down its middle like a path of sunlight",
        wrap_text="folded its broad sides over the spilled load",
        ending_text="the gold stripe shone",
        tags={"stripe", "blanket"},
    ),
    "wagon_cloth": StripeItem(
        id="wagon_cloth",
        label="wagon cloth",
        phrase="a stout wagon cloth",
        size=3,
        stripe_text="Three brave bands made one long red stripe across its face",
        wrap_text="wrapped the whole load snugly and knotted the ends",
        ending_text="the red stripe streamed",
        tags={"stripe", "cloth"},
    ),
}

TOOLS = {
    "ratchet_clasp": RatchetTool(
        id="ratchet_clasp",
        label="the ratchet clasp",
        phrase="a little ratchet clasp",
        power=1,
        click_text="click, click",
        tighten_text="tightened the side rope",
        qa_text="They used the ratchet clasp to tighten the side rope",
        tags={"ratchet", "tool"},
    ),
    "ratchet_strap": RatchetTool(
        id="ratchet_strap",
        label="the ratchet strap",
        phrase="a stout ratchet strap",
        power=2,
        click_text="click-click, click-click",
        tighten_text="cinched the load tight",
        qa_text="They used the ratchet strap to cinch the load tight",
        tags={"ratchet", "tool"},
    ),
    "ratchet_winch": RatchetTool(
        id="ratchet_winch",
        label="the ratchet winch",
        phrase="a strong ratchet winch",
        power=3,
        click_text="clack, clack, clack",
        tighten_text="drew the cart straight and tight",
        qa_text="They used the ratchet winch to draw the cart straight and tight",
        tags={"ratchet", "tool"},
    ),
}

HELPERS = {
    "owl": Helper(
        id="owl",
        label="owl",
        phrase="an old owl from the willow tree",
        advice='"A load shared in silence grows crooked," said the owl. "A load shared in honesty grows light."',
        tags={"owl", "advice"},
    ),
    "tortoise": Helper(
        id="tortoise",
        label="tortoise",
        phrase="a slow tortoise with bright eyes",
        advice='"If you wish to move a cart, do not pull your hearts apart," said the tortoise.',
        tags={"tortoise", "advice"},
    ),
    "goat": Helper(
        id="goat",
        label="goat",
        phrase="a hill goat with wise horns",
        advice='"Roads are rough enough without rough words," said the goat.',
        tags={"goat", "advice"},
    ),
}

ANIMAL_PAIRS = [
    ("Mole", "mole", "Skunk", "skunk"),
    ("Fox", "fox", "Badger", "badger"),
    ("Hare", "hare", "Otter", "otter"),
    ("Mouse", "mouse", "Hedgehog", "hedgehog"),
]

TRAITS = [
    {"pride": 2, "kindness": 3},
    {"pride": 3, "kindness": 4},
    {"pride": 4, "kindness": 4},
    {"pride": 4, "kindness": 5},
]


@dataclass
class StoryParams:
    setting: str
    cargo: str
    stripe_item: str
    tool: str
    helper: str
    animal1_name: str
    animal1_type: str
    animal2_name: str
    animal2_type: str
    pride1: int
    pride2: int
    kindness1: int
    kindness2: int
    seed: Optional[int] = None


KNOWLEDGE = {
    "stripe": [
        (
            "What is a stripe?",
            "A stripe is a long band of color that runs across cloth, fur, or another surface. It helps something stand out so you notice it right away.",
        )
    ],
    "ratchet": [
        (
            "What is a ratchet?",
            "A ratchet is a tool that clicks as it tightens something one step at a time. It helps hold ropes or straps firm so a load does not slip.",
        )
    ],
    "cart": [
        (
            "Why do people tie things down in a cart?",
            "They tie a load down so bumps in the road do not throw it out. A steady cart is safer and easier to pull.",
        )
    ],
    "apology": [
        (
            "What does an apology do?",
            "An apology tells someone you know you caused hurt and want to mend it. It makes room for trust to grow again when the other person is ready.",
        )
    ],
    "cooperation": [
        (
            "Why is it easier to carry a heavy job together?",
            "Two helpers can share the work and notice different problems. Working together also keeps one person from becoming tired or stubborn all alone.",
        )
    ],
    "owl": [
        (
            "Why are owls often wise in fables?",
            "In fables, owls often watch quietly before they speak. That makes them good symbols for calm advice.",
        )
    ],
    "tortoise": [
        (
            "Why is a tortoise a good fable helper?",
            "A tortoise moves slowly and thinks carefully. That makes the tortoise a good character for patient advice.",
        )
    ],
    "goat": [
        (
            "Why might a goat understand a rough road?",
            "Goats are good at climbing and balancing on hard ground. In a story, that makes a goat a believable guide on a bumpy path.",
        )
    ],
}
KNOWLEDGE_ORDER = ["stripe", "ratchet", "cart", "apology", "cooperation", "owl", "tortoise", "goat"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["animal1"]
    b = f["animal2"]
    cargo = f["cargo"]
    stripe_item = f["stripe_item"]
    tool = f["tool"]
    setting = f["setting"]
    return [
        f'Write a short fable about two animal neighbors carrying {cargo.phrase} along {setting.path_phrase}. Include the word "stripe" and the word "ratchet".',
        f"Tell a reconciliation fable where {a.id} and {b.id} quarrel after their cart spills, then make peace by using {stripe_item.phrase} and {tool.phrase} together.",
        f"Write a gentle animal story with a clear moral: pride causes trouble on the road, but apology and shared work mend it.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["animal1"]
    b = f["animal2"]
    cargo = f["cargo"]
    stripe_item = f["stripe_item"]
    tool = f["tool"]
    helper = f["helper"]
    first = f["first_apology"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {a.id} and {b.id}, two animal neighbors sharing a cart on the road. They begin as partners, then become cross with each other after the spill.",
        ),
        (
            "Why did the cart spill?",
            f"The cart spilled because they hurried and stopped listening before the load was tied properly. When the wheels hit the rough bump in the road, the loose cart tipped and the cargo fell out.",
        ),
        (
            "Why could they not fix the problem while they were angry?",
            f"They each tried to work alone, but one pair of paws could not gather the load and steady the cart at the same time. Their anger pulled them apart, so the repair needed cooperation before it could succeed.",
        ),
        (
            f"Who apologized first, and why did that matter?",
            f"{first} apologized first, which softened the quarrel and opened the door for the other apology. That mattered because reconciliation changed them from two stubborn workers into a team again.",
        ),
        (
            "How did they repair the cart and save the load?",
            f"They spread {stripe_item.phrase} to gather the spilled cargo, then lifted it back together. After that they used {tool.label} to tighten the cart until it stood firm.",
        ),
        (
            f"What did {helper.label} do in the story?",
            f"The {helper.label} did not lift the cart for them, but gave wise advice at the right moment. That advice helped them see that the real trouble was not only the road, but the quarrel between them.",
        ),
        (
            "What changed by the end of the story?",
            f"At the end, the cart was steady and their friendship was steady too. The ending proves the change because they reach the market together instead of pulling in opposite directions.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"stripe", "ratchet", "cart", "apology", "cooperation", f["helper"].id}
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits: list[str] = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:11} ({ent.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="meadow_lane",
        cargo="berries",
        stripe_item="kerchief",
        tool="ratchet_clasp",
        helper="owl",
        animal1_name="Mole",
        animal1_type="mole",
        animal2_name="Skunk",
        animal2_type="skunk",
        pride1=3,
        pride2=4,
        kindness1=4,
        kindness2=4,
    ),
    StoryParams(
        setting="brook_path",
        cargo="apples",
        stripe_item="blanket",
        tool="ratchet_strap",
        helper="tortoise",
        animal1_name="Fox",
        animal1_type="fox",
        animal2_name="Badger",
        animal2_type="badger",
        pride1=4,
        pride2=3,
        kindness1=4,
        kindness2=5,
    ),
    StoryParams(
        setting="hill_road",
        cargo="pumpkins",
        stripe_item="wagon_cloth",
        tool="ratchet_winch",
        helper="goat",
        animal1_name="Hare",
        animal1_type="hare",
        animal2_name="Otter",
        animal2_type="otter",
        pride1=4,
        pride2=4,
        kindness1=5,
        kindness2=4,
    ),
]


ASP_RULES = r"""
fits(SI, C) :- stripe_item(SI), cargo(C), cloth_size(SI, SS), cargo_bulk(C, CB), SS >= CB.
holds(T, S, C) :- tool(T), setting(S), cargo(C),
                  tool_power(T, TP), road_need(S, SNeed), cargo_bulk(C, CB),
                  TP >= SNeed + CB - 1.
valid(S, C, SI, T) :- setting(S), cargo(C), stripe_item(SI), tool(T), fits(SI, C), holds(T, S, C).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        lines.append(asp.fact("road_need", setting_id, setting.bump))
    for cargo_id, cargo in CARGOS.items():
        lines.append(asp.fact("cargo", cargo_id))
        lines.append(asp.fact("cargo_bulk", cargo_id, cargo.bulk))
    for stripe_id, stripe_item in STRIPE_ITEMS.items():
        lines.append(asp.fact("stripe_item", stripe_id))
        lines.append(asp.fact("cloth_size", stripe_id, stripe_item.size))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("tool_power", tool_id, tool.power))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    smoke_params = CURATED[0]
    try:
        sample = generate(smoke_params)
        if not sample.story.strip():
            raise StoryError("empty story from generate()")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke generation/emit succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A fable storyworld about a spilled cart, a stripe-marked cloth, a ratchet tool, and reconciliation."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--cargo", choices=CARGOS)
    ap.add_argument("--stripe_item", choices=STRIPE_ITEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible story combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.cargo and args.stripe_item and args.tool:
        setting = SETTINGS[args.setting]
        cargo = CARGOS[args.cargo]
        stripe_item = STRIPE_ITEMS[args.stripe_item]
        tool = TOOLS[args.tool]
        if not valid_combo(setting, cargo, stripe_item, tool):
            raise StoryError(explain_rejection(setting, cargo, stripe_item, tool))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.cargo is None or combo[1] == args.cargo)
        and (args.stripe_item is None or combo[2] == args.stripe_item)
        and (args.tool is None or combo[3] == args.tool)
    ]
    if not combos:
        if args.setting and args.cargo and args.stripe_item and args.tool:
            raise StoryError(
                explain_rejection(
                    SETTINGS[args.setting],
                    CARGOS[args.cargo],
                    STRIPE_ITEMS[args.stripe_item],
                    TOOLS[args.tool],
                )
            )
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, cargo_id, stripe_id, tool_id = rng.choice(sorted(combos))
    helper_id = args.helper or rng.choice(sorted(HELPERS))
    animal1_name, animal1_type, animal2_name, animal2_type = rng.choice(ANIMAL_PAIRS)
    trait1 = rng.choice(TRAITS)
    trait2 = rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id,
        cargo=cargo_id,
        stripe_item=stripe_id,
        tool=tool_id,
        helper=helper_id,
        animal1_name=animal1_name,
        animal1_type=animal1_type,
        animal2_name=animal2_name,
        animal2_type=animal2_type,
        pride1=trait1["pride"],
        pride2=trait2["pride"],
        kindness1=trait1["kindness"],
        kindness2=trait2["kindness"],
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        cargo = CARGOS[params.cargo]
        stripe_item = STRIPE_ITEMS[params.stripe_item]
        tool = TOOLS[params.tool]
        helper = HELPERS[params.helper]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err.args[0]})") from None

    if not valid_combo(setting, cargo, stripe_item, tool):
        raise StoryError(explain_rejection(setting, cargo, stripe_item, tool))

    world = tell(
        setting=setting,
        cargo=cargo,
        stripe_item=stripe_item,
        tool=tool,
        helper=helper,
        animal1_name=params.animal1_name,
        animal1_type=params.animal1_type,
        animal2_name=params.animal2_name,
        animal2_type=params.animal2_type,
        pride1=params.pride1,
        pride2=params.pride2,
        kindness1=params.kindness1,
        kindness2=params.kindness2,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, cargo, stripe_item, tool) combos:\n")
        for setting_id, cargo_id, stripe_id, tool_id in combos:
            print(f"  {setting_id:12} {cargo_id:9} {stripe_id:11} {tool_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.animal1_name} and {p.animal2_name}: {p.cargo} on {p.setting} ({p.stripe_item}, {p.tool})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/ease_correct_magic_foreshadowing_flashback_slice_of.py
=================================================================================

A small slice-of-life storyworld about a child in an ordinary home, a small
everyday problem, and a gentle bit of household magic used the correct way.

The core tale rebuilt here is simple:
- a child has something important later that day,
- a worn household item needs mending,
- the child first tries to hurry,
- a remembered lesson and a calm helper guide the child to the correct method,
- the ending image shows that the work now feels easy with practice.

This world includes:
- Magic: ordinary domestic mending magic,
- Foreshadowing: an early sign that the item "wants" the right fix,
- Flashback: the child remembers a past lesson that changes the present choice.

Run it
------
    python storyworlds/worlds/gpt-5.4/ease_correct_magic_foreshadowing_flashback_slice_of.py
    python storyworlds/worlds/gpt-5.4/ease_correct_magic_foreshadowing_flashback_slice_of.py --item backpack --tool moon_thread
    python storyworlds/worlds/gpt-5.4/ease_correct_magic_foreshadowing_flashback_slice_of.py --item mug --tool warm_chalk
    python storyworlds/worlds/gpt-5.4/ease_correct_magic_foreshadowing_flashback_slice_of.py --all
    python storyworlds/worlds/gpt-5.4/ease_correct_magic_foreshadowing_flashback_slice_of.py --qa
    python storyworlds/worlds/gpt-5.4/ease_correct_magic_foreshadowing_flashback_slice_of.py --verify
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

# Make the shared result containers importable when this script is run directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Shared entity model.
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "aunt", "woman"}
        male = {"boy", "father", "grandfather", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Domain knobs.
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    id: str
    place: str
    time_phrase: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ItemConfig:
    id: str
    label: str
    phrase: str
    material: str
    problem: str
    risk: str
    needs: str
    fixed_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ToolConfig:
    id: str
    label: str
    phrase: str
    repairs: set[str] = field(default_factory=set)
    motion: str = ""
    lesson: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Occasion:
    id: str
    label: str
    place: str
    carry: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# Story parameters.
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    item: str
    tool: str
    occasion: str
    hero_name: str
    hero_gender: str
    helper_type: str
    helper_name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Content registries.
# ---------------------------------------------------------------------------
SETTINGS = {
    "kitchen_morning": Setting(
        id="kitchen_morning",
        place="the kitchen table",
        time_phrase="On a soft morning",
        tags={"home", "morning"},
    ),
    "hallway_morning": Setting(
        id="hallway_morning",
        place="the hallway bench",
        time_phrase="Early that morning",
        tags={"home", "morning"},
    ),
    "window_nook": Setting(
        id="window_nook",
        place="the sunny window nook",
        time_phrase="After breakfast",
        tags={"home", "morning"},
    ),
}

ITEMS = {
    "backpack": ItemConfig(
        id="backpack",
        label="backpack",
        phrase="a blue backpack with a side pocket",
        material="cloth",
        problem="the side pocket had a small tear",
        risk="her crayons might tumble out on the way",
        needs="a neat little seam",
        fixed_word="sat smooth and strong again",
        tags={"cloth", "school", "backpack"},
    ),
    "apron": ItemConfig(
        id="apron",
        label="apron",
        phrase="a striped baking apron",
        material="cloth",
        problem="one pocket was coming loose",
        risk="the wooden spoon might slip right through",
        needs="a tidy row of stitches",
        fixed_word="hung straight and ready again",
        tags={"cloth", "baking", "apron"},
    ),
    "mug": ItemConfig(
        id="mug",
        label="mug",
        phrase="a white mug painted with tiny pears",
        material="ceramic",
        problem="a small crack ran near the handle",
        risk="warm cocoa might leak onto small hands",
        needs="a careful warming line",
        fixed_word="gleamed whole and steady again",
        tags={"ceramic", "kitchen", "mug"},
    ),
}

TOOLS = {
    "moon_thread": ToolConfig(
        id="moon_thread",
        label="moon thread",
        phrase="a spool of moon thread",
        repairs={"cloth"},
        motion="the pale thread lifted its end as if it already knew where to go",
        lesson="Tiny stitches first, then a breath, then the knot.",
        tags={"thread", "mending", "magic"},
    ),
    "humming_thimble": ToolConfig(
        id="humming_thimble",
        label="humming thimble",
        phrase="a humming thimble",
        repairs={"cloth"},
        motion="the little silver thimble gave a warm hum against the table",
        lesson="Let the cloth rest flat before you guide the magic through.",
        tags={"thimble", "mending", "magic"},
    ),
    "warm_chalk": ToolConfig(
        id="warm_chalk",
        label="warm chalk",
        phrase="a stick of warm chalk",
        repairs={"ceramic"},
        motion="the chalk left a soft gold dust in the air before it even touched the crack",
        lesson="Trace the broken line slowly and keep your hand steady.",
        tags={"chalk", "repair", "magic"},
    ),
}

OCCASIONS = {
    "school_art": Occasion(
        id="school_art",
        label="art time at school",
        place="school",
        carry="carry crayons and paper",
        tags={"school"},
    ),
    "neighbor_baking": Occasion(
        id="neighbor_baking",
        label="baking buns with the neighbor",
        place="next door",
        carry="carry a spoon and recipe card",
        tags={"baking"},
    ),
    "porch_cocoa": Occasion(
        id="porch_cocoa",
        label="hot cocoa on the porch",
        place="the porch",
        carry="hold warm cocoa safely",
        tags={"cocoa"},
    ),
}

GIRL_NAMES = ["Lina", "Maya", "Tessa", "Nora", "Eva", "Ruby", "Mina", "Lucy"]
BOY_NAMES = ["Owen", "Milo", "Theo", "Eli", "Ben", "Noah", "Finn", "Leo"]
HELPER_TYPES = ["mother", "father", "grandmother", "grandfather"]

# Compatible item/occasion pairs: the ordinary errand or plan must suit the item.
ITEM_OCCASIONS = {
    "backpack": {"school_art"},
    "apron": {"neighbor_baking"},
    "mug": {"porch_cocoa"},
}


# ---------------------------------------------------------------------------
# World model.
# ---------------------------------------------------------------------------
class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
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


# ---------------------------------------------------------------------------
# Reasonableness gates.
# ---------------------------------------------------------------------------
def tool_fits_item(tool: ToolConfig, item: ItemConfig) -> bool:
    return item.material in tool.repairs


def occasion_fits_item(occasion: Occasion, item: ItemConfig) -> bool:
    return occasion.id in ITEM_OCCASIONS[item.id]


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for item_id, item in ITEMS.items():
            for tool_id, tool in TOOLS.items():
                if not tool_fits_item(tool, item):
                    continue
                for occasion_id, occasion in OCCASIONS.items():
                    if occasion_fits_item(occasion, item):
                        out.append((setting_id, item_id, tool_id, occasion_id))
    return out


def explain_bad_tool(item: ItemConfig, tool: ToolConfig) -> str:
    return (
        f"(No story: {tool.label} is not the correct kind of household magic for a "
        f"{item.label}. It repairs {sorted(tool.repairs)}, but {item.label} is {item.material}.)"
    )


def explain_bad_occasion(item: ItemConfig, occasion: Occasion) -> str:
    return (
        f"(No story: {item.label} does not fit the plan '{occasion.label}'. "
        f"The ordinary problem and the day's outing need to match.)"
    )


# ---------------------------------------------------------------------------
# Screenplay beats.
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity, setting: Setting, item: ItemConfig, occasion: Occasion) -> None:
    world.say(
        f"{setting.time_phrase}, {hero.id} sat by {setting.place} getting ready for "
        f"{occasion.label}."
    )
    world.say(
        f"Beside {hero.pronoun('object')} lay {item.phrase}. {item.problem}, and {item.risk}."
    )


def foreshadow(world: World, tool: ToolConfig, item: ItemConfig) -> None:
    world.get("tool").meters["glow"] += 1
    world.get("item").memes["listening"] += 1
    world.say(
        f"On the shelf nearby rested {tool.phrase}, and {tool.motion}. "
        f"It was a small sign that the morning would go better with patience than hurry."
    )


def worry(world: World, hero: Entity, occasion: Occasion) -> None:
    hero.memes["worry"] += 1
    world.say(
        f"{hero.id} wanted to leave soon so {hero.pronoun()} could {occasion.carry}. "
        f"But the broken spot made {hero.pronoun('object')} pause."
    )


def rush_wrong(world: World, hero: Entity, item: ItemConfig) -> None:
    hero.memes["hurry"] += 1
    world.get("item").meters["crooked"] += 1
    world.say(
        f"{hero.id} tried to fix it in one quick swoop. The magic tugged too fast, "
        f"and the mend came out crooked instead of correct."
    )
    world.say(
        f"{hero.pronoun().capitalize()} looked at the {item.label} and felt a hot little pinch of worry."
    )


def helper_arrives(world: World, helper: Entity) -> None:
    helper.memes["care"] += 1
    world.say(
        f"{helper.id} came in carrying the smell of tea and toast and knelt beside the table."
    )


def flashback(world: World, hero: Entity, helper: Entity, tool: ToolConfig) -> None:
    hero.memes["memory"] += 1
    world.say(
        f"Then {hero.id} remembered another morning. In that flashback, {helper.id} had "
        f"covered {hero.pronoun('possessive')} small hand with {helper.pronoun('possessive')} own and said, "
        f'"{tool.lesson}"'
    )


def correct_method(world: World, hero: Entity, helper: Entity, item: ItemConfig, tool: ToolConfig) -> None:
    item_ent = world.get("item")
    item_ent.meters["crooked"] = 0.0
    item_ent.meters["fixed"] += 1
    hero.memes["focus"] += 1
    hero.memes["confidence"] += 1
    hero.memes["worry"] = 0.0
    world.say(
        f'"Let the magic follow your hands, not race ahead of them," {helper.id} said softly.'
    )
    world.say(
        f"{hero.id} tried again, this time the correct way. Slowly, carefully, "
        f"{tool.label} followed the edge that needed mending, and {item.needs} appeared."
    )


def resolution(world: World, hero: Entity, item: ItemConfig, occasion: Occasion) -> None:
    hero.memes["relief"] += 1
    hero.memes["ease"] += 1
    world.say(
        f"Soon the {item.label} {item.fixed_word}. When {hero.id} lifted it, the work felt almost easy."
    )
    world.say(
        f"{hero.pronoun().capitalize()} smiled, thanked {world.get('helper').id}, and set off for {occasion.label}."
    )
    world.say(
        f"At the door, {hero.id} gave the mended {item.label} one small pat, pleased that a careful start had made the whole morning gentler."
    )


def tell(
    setting: Setting,
    item_cfg: ItemConfig,
    tool_cfg: ToolConfig,
    occasion: Occasion,
    hero_name: str,
    hero_gender: str,
    helper_type: str,
    helper_name: str,
) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper"))
    item = world.add(Entity(id="item", type=item_cfg.material, label=item_cfg.label, phrase=item_cfg.phrase))
    tool = world.add(Entity(id="tool", type="tool", label=tool_cfg.label, phrase=tool_cfg.phrase))

    introduce(world, hero, setting, item_cfg, occasion)
    foreshadow(world, tool_cfg, item_cfg)

    world.para()
    worry(world, hero, occasion)
    rush_wrong(world, hero, item_cfg)
    helper_arrives(world, helper)
    flashback(world, hero, helper, tool_cfg)

    world.para()
    correct_method(world, hero, helper, item_cfg, tool_cfg)
    resolution(world, hero, item_cfg, occasion)

    world.facts.update(
        hero=hero,
        helper=helper,
        setting=setting,
        item_cfg=item_cfg,
        tool_cfg=tool_cfg,
        occasion=occasion,
        foreshadowed=tool.meters["glow"] >= THRESHOLD,
        flashback_used=hero.memes["memory"] >= THRESHOLD,
        wrong_first=item.meters["fixed"] >= THRESHOLD,
        fixed=item.meters["fixed"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# QA.
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "magic": [
        (
            "What is household magic in this story world?",
            "It is a gentle kind of magic used for ordinary jobs like mending and fixing. It works best when someone is calm, careful, and paying attention.",
        )
    ],
    "foreshadowing": [
        (
            "What is foreshadowing?",
            "Foreshadowing is a small early clue about something that will matter later. It helps a reader feel that the story was quietly pointing ahead.",
        )
    ],
    "flashback": [
        (
            "What is a flashback?",
            "A flashback is a short memory scene from an earlier time. It can help a character remember something important in the present.",
        )
    ],
    "cloth": [
        (
            "Why do cloth things need neat stitches?",
            "Cloth can pull apart if a tear is left open. Small neat stitches hold the edges together so the item stays strong.",
        )
    ],
    "ceramic": [
        (
            "Why can a cracked mug be a problem?",
            "A crack can let warm drink leak out or make the mug weaker. That is why it should be repaired carefully before someone uses it.",
        )
    ],
    "school": [
        (
            "Why does a backpack pocket matter at school?",
            "A backpack pocket helps hold small things like crayons, pencils, or notes. If it tears, those little things can fall out on the way.",
        )
    ],
    "baking": [
        (
            "Why might an apron need a strong pocket?",
            "An apron pocket often holds a spoon, towel, or recipe card. If the pocket comes loose, those things may slip out while someone cooks.",
        )
    ],
    "cocoa": [
        (
            "Why should a mug handle be safe and steady?",
            "A mug handle helps hands hold a warm drink without spilling it. If the mug is cracked near the handle, it may not feel safe to use.",
        )
    ],
}
KNOWLEDGE_ORDER = ["magic", "foreshadowing", "flashback", "cloth", "ceramic", "school", "baking", "cocoa"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    item_cfg = f["item_cfg"]
    tool_cfg = f["tool_cfg"]
    occasion = f["occasion"]
    return [
        'Write a slice-of-life story for a 3-to-5-year-old that includes the words "ease" and "correct," plus magic, foreshadowing, and a flashback.',
        f"Tell a gentle home story where {hero.id} must mend a {item_cfg.label} before {occasion.label}, first rushing, then remembering the correct way.",
        f"Write a magical everyday story where {tool_cfg.label} helps with a small problem, and the ending shows that careful practice can make hard work feel easy.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    item_cfg = f["item_cfg"]
    tool_cfg = f["tool_cfg"]
    occasion = f["occasion"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, who had a small thing to mend before {occasion.label}, and {helper.id}, who helped with calm advice.",
        ),
        (
            f"What problem did {hero.id} notice?",
            f"{hero.id} saw that the {item_cfg.label} needed fixing because {item_cfg.problem}. That mattered because {item_cfg.risk}.",
        ),
        (
            "What was the early clue that magic would matter later?",
            f"The story showed {tool_cfg.phrase} giving a small magical sign before anyone used it. That foreshadowing hinted that the right kind of magic would help solve the problem.",
        ),
        (
            f"Why did the first try not work well?",
            f"The first try was too quick, so the mend came out crooked instead of correct. The problem was not the magic itself, but the hurried way {hero.id} used it.",
        ),
        (
            "What happened in the flashback?",
            f"In the flashback, {hero.id} remembered an earlier lesson from {helper.id}. That memory gave {hero.pronoun('object')} the exact calm steps needed to try again.",
        ),
        (
            f"How was the problem solved?",
            f"{hero.id} slowed down and used {tool_cfg.label} the correct way. Because the careful method matched the {item_cfg.label}, the mend held and the morning felt easier.",
        ),
        (
            "How did the story end?",
            f"It ended with the {item_cfg.label} ready again and {hero.id} leaving for {occasion.label}. The last image shows that the work felt easy once {hero.pronoun()} stopped hurrying and followed the lesson.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"magic", "foreshadowing", "flashback"}
    tags |= set(f["item_cfg"].tags)
    tags |= set(f["occasion"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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


# ---------------------------------------------------------------------------
# Trace.
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:11}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated set.
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        setting="kitchen_morning",
        item="backpack",
        tool="moon_thread",
        occasion="school_art",
        hero_name="Lina",
        hero_gender="girl",
        helper_type="grandmother",
        helper_name="Grandma June",
    ),
    StoryParams(
        setting="window_nook",
        item="apron",
        tool="humming_thimble",
        occasion="neighbor_baking",
        hero_name="Milo",
        hero_gender="boy",
        helper_type="father",
        helper_name="Dad",
    ),
    StoryParams(
        setting="hallway_morning",
        item="mug",
        tool="warm_chalk",
        occasion="porch_cocoa",
        hero_name="Eva",
        hero_gender="girl",
        helper_type="mother",
        helper_name="Mom",
    ),
]


# ---------------------------------------------------------------------------
# ASP twin.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
compatible_tool(I, T) :- item(I), tool(T), material(I, M), repairs(T, M).
compatible_occasion(I, O) :- item(I), occasion(O), fits(I, O).
valid(S, I, T, O) :- setting(S), compatible_tool(I, T), compatible_occasion(I, O).

#show valid/4.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        lines.append(asp.fact("material", item_id, item.material))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        for material in sorted(tool.repairs):
            lines.append(asp.fact("repairs", tool_id, material))
    for occasion_id in OCCASIONS:
        lines.append(asp.fact("occasion", occasion_id))
    for item_id, occasion_ids in ITEM_OCCASIONS.items():
        for occasion_id in sorted(occasion_ids):
            lines.append(asp.fact("fits", item_id, occasion_id))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "#show valid/4.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program(show="#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid_combos():")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    # Smoke-test ordinary generation.
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Standard storyworld interface.
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A slice-of-life magical mending storyworld. Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--occasion", choices=OCCASIONS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=HELPER_TYPES)
    ap.add_argument("--helper-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.item and args.tool:
        item = ITEMS[args.item]
        tool = TOOLS[args.tool]
        if not tool_fits_item(tool, item):
            raise StoryError(explain_bad_tool(item, tool))
    if args.item and args.occasion:
        item = ITEMS[args.item]
        occasion = OCCASIONS[args.occasion]
        if not occasion_fits_item(occasion, item):
            raise StoryError(explain_bad_occasion(item, occasion))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.item is None or combo[1] == args.item)
        and (args.tool is None or combo[2] == args.tool)
        and (args.occasion is None or combo[3] == args.occasion)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, item_id, tool_id, occasion_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    helper_type = args.helper_type or rng.choice(HELPER_TYPES)
    default_helper_name = {
        "mother": "Mom",
        "father": "Dad",
        "grandmother": "Grandma June",
        "grandfather": "Grandpa Ray",
    }[helper_type]
    helper_name = args.helper_name or default_helper_name

    return StoryParams(
        setting=setting_id,
        item=item_id,
        tool=tool_id,
        occasion=occasion_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        helper_type=helper_type,
        helper_name=helper_name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.occasion not in OCCASIONS:
        raise StoryError(f"(Unknown occasion: {params.occasion})")

    item_cfg = ITEMS[params.item]
    tool_cfg = TOOLS[params.tool]
    occasion = OCCASIONS[params.occasion]

    if not tool_fits_item(tool_cfg, item_cfg):
        raise StoryError(explain_bad_tool(item_cfg, tool_cfg))
    if not occasion_fits_item(occasion, item_cfg):
        raise StoryError(explain_bad_occasion(item_cfg, occasion))

    world = tell(
        setting=SETTINGS[params.setting],
        item_cfg=item_cfg,
        tool_cfg=tool_cfg,
        occasion=occasion,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        helper_type=params.helper_type,
        helper_name=params.helper_name,
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
        print(asp_program(show="#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, item, tool, occasion) combos:\n")
        for setting_id, item_id, tool_id, occasion_id in combos:
            print(f"  {setting_id:16} {item_id:10} {tool_id:16} {occasion_id}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.item} with {p.tool} before {p.occasion}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

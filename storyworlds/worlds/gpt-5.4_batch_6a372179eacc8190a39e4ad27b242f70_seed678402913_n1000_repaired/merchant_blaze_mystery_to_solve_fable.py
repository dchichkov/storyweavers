#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/merchant_blaze_mystery_to_solve_fable.py
===================================================================

A small story world about a merchant who finds signs of a blaze at a market
stall, resists blaming the nearest innocent suspect, and solves the mystery by
following better clues.

The domain is shaped like a fable: the setting is simple, the conflict is clear,
the turn comes from careful observation, and the ending proves the lesson.
Different settings allow different causes of the fire, and the world refuses
unreasonable combinations.

Run it
------
    python storyworlds/worlds/gpt-5.4/merchant_blaze_mystery_to_solve_fable.py
    python storyworlds/worlds/gpt-5.4/merchant_blaze_mystery_to_solve_fable.py --setting dawn_square --cause sunbeam_glass
    python storyworlds/worlds/gpt-5.4/merchant_blaze_mystery_to_solve_fable.py --setting lantern_lane --cause sunbeam_glass
    python storyworlds/worlds/gpt-5.4/merchant_blaze_mystery_to_solve_fable.py --all --qa
    python storyworlds/worlds/gpt-5.4/merchant_blaze_mystery_to_solve_fable.py --verify
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        mapping = {
            "female": {"subject": "she", "object": "her", "possessive": "her"},
            "male": {"subject": "he", "object": "him", "possessive": "his"},
        }
        if self.type in mapping:
            return mapping[self.type][case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    id: str
    place: str
    opening: str
    affords: set[str] = field(default_factory=set)
    mood: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Goods:
    id: str
    label: str
    phrase: str
    stash: str
    flammability: int
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Cause:
    id: str
    label: str
    risk: int
    spark_text: str
    true_clue: str
    proof_text: str
    prevention: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SuspectCfg:
    id: str
    label: str
    phrase: str
    type: str
    trace: str
    defense: str
    tags: set[str] = field(default_factory=set)


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


def propagate(world: World) -> None:
    merchant = world.get("merchant")
    suspect = world.get("suspect")
    stall = world.get("stall")
    if stall.meters["scorched"] >= THRESHOLD and ("fear",) not in world.fired:
        world.fired.add(("fear",))
        merchant.memes["fear"] += 1
        merchant.memes["care"] += 1
    if suspect.memes["suspected"] >= THRESHOLD and ("hurt", suspect.id) not in world.fired:
        world.fired.add(("hurt", suspect.id))
        suspect.memes["hurt"] += 1
    if merchant.memes["solved"] >= THRESHOLD and ("relief",) not in world.fired:
        world.fired.add(("relief",))
        merchant.memes["relief"] += 1
        suspect.memes["relief"] += 1


SETTINGS = {
    "dawn_square": Setting(
        id="dawn_square",
        place="Dawn Square",
        opening="Each morning Dawn Square woke in a gold wash of sunlight, and shutters clicked open like birds stretching their wings.",
        affords={"sunbeam_glass", "brazier_spark"},
        mood="bright",
        tags={"market", "sun"},
    ),
    "lantern_lane": Setting(
        id="lantern_lane",
        place="Lantern Lane",
        opening="In Lantern Lane, traders opened their stalls before sunrise while old lamps still swung over the narrow street.",
        affords={"lantern_ember", "brazier_spark"},
        mood="dim",
        tags={"market", "lantern"},
    ),
    "windy_gate": Setting(
        id="windy_gate",
        place="Windy Gate Market",
        opening="At Windy Gate Market, canvas awnings flapped and every basket seemed to rustle a little secret of its own.",
        affords={"lantern_ember", "brazier_spark"},
        mood="windy",
        tags={"market", "wind"},
    ),
}

GOODS = {
    "silk": Goods(
        id="silk",
        label="silk scarves",
        phrase="a stack of silk scarves bright as parrots",
        stash="hung the silk scarves where every color could catch the eye",
        flammability=3,
        ending_image="the silk scarves fluttered safely in the shade",
        tags={"cloth", "market_goods"},
    ),
    "straw": Goods(
        id="straw",
        label="straw mats",
        phrase="a pile of straw mats tied with neat twine",
        stash="stacked the straw mats beside the post",
        flammability=3,
        ending_image="the straw mats rested far from any spark",
        tags={"straw", "market_goods"},
    ),
    "spice": Goods(
        id="spice",
        label="spice sacks",
        phrase="small spice sacks that smelled of cinnamon and clove",
        stash="arranged the spice sacks in a careful row",
        flammability=2,
        ending_image="the spice sacks sat under a safe awning, filling the air with warm smell instead of smoke",
        tags={"spice", "market_goods"},
    ),
}

CAUSES = {
    "sunbeam_glass": Cause(
        id="sunbeam_glass",
        label="a sunbeam bent through a glass bottle",
        risk=2,
        spark_text="A sharp morning sunbeam had slipped through a round bottle and burned one bright point for too long.",
        true_clue="On the cloth lay a neat round singe mark, and the bottle above it still held a bead of light.",
        proof_text="The mark was too small and round to come from clumsy hands. It matched the bright point made by the glass.",
        prevention="moved the bottle away from the sun and stretched a little shade cloth over the shelf",
        tags={"sun", "glass", "fire_safety"},
    ),
    "lantern_ember": Cause(
        id="lantern_ember",
        label="an ember dropped from a hanging lantern",
        risk=3,
        spark_text="A hanging lantern had shed a tiny ember in the night, and the ember had kissed the goods below.",
        true_clue="The cord above the stall was blackened from the top down, and a little ash rested under the lantern hook.",
        proof_text="The scorch had started above, not below. The black thread on the hanging cord pointed straight to the lantern.",
        prevention="took down the old lantern and hung a fresh one with a tight hook far from the goods",
        tags={"lantern", "ember", "fire_safety"},
    ),
    "brazier_spark": Cause(
        id="brazier_spark",
        label="a wind-blown spark from the baker's brazier",
        risk=2,
        spark_text="A restless wind had carried a spark from the baker's brazier across the lane and into the merchant's stall.",
        true_clue="A faint trail of gray ash ran under the awning from the baker's side, and the burn on the goods leaned with the wind.",
        proof_text="The ash made a little path, and the lean of the burn showed which way the spark had traveled.",
        prevention="worked with the baker to set a screen beside the brazier and moved the goods farther from the lane",
        tags={"brazier", "wind", "fire_safety"},
    ),
}

SUSPECTS = {
    "crow": SuspectCfg(
        id="crow",
        label="Crow",
        phrase="a glossy crow who liked shiny things",
        type="animal",
        trace="A blue feather was snagged on the awning, and several neighbors muttered that Crow must have pecked at something dangerous.",
        defense="Crow had only stolen a cherry pit from the fruit stand and never gone near the lamp.",
        tags={"crow", "blame"},
    ),
    "goat": SuspectCfg(
        id="goat",
        label="Goat",
        phrase="a hungry goat from the cart yard",
        type="animal",
        trace="Fresh hoofprints circled the stall, and people said Goat must have knocked something over in the dark.",
        defense="Goat had nibbled cabbage leaves at dawn, but the shelves were too high for Goat to touch the lamp or bottle.",
        tags={"goat", "blame"},
    ),
    "child": SuspectCfg(
        id="child",
        label="Pip",
        phrase="Pip, a curious child with dusty sandals",
        type="male",
        trace="Small shoeprints near the jars made a few traders whisper that Pip had played where he should not.",
        defense="Pip had delivered bread before sunrise and left long before the stall warmed with light.",
        tags={"child", "blame"},
    ),
}

MERCHANTS = [
    ("Nima", "female"),
    ("Basil", "male"),
    ("Suri", "female"),
    ("Tarin", "male"),
]

TRAITS = ["patient", "careful", "steady", "sharp-eyed", "honest", "calm"]


def cause_possible(setting: Setting, goods: Goods, cause: Cause) -> bool:
    return cause.id in setting.affords and goods.flammability >= cause.risk


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for goods_id, goods in GOODS.items():
            for cause_id, cause in CAUSES.items():
                if not cause_possible(setting, goods, cause):
                    continue
                for suspect_id in SUSPECTS:
                    combos.append((setting_id, goods_id, cause_id, suspect_id))
    return combos


@dataclass
class StoryParams:
    setting: str
    goods: str
    cause: str
    suspect: str
    merchant_name: str
    merchant_gender: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        setting="dawn_square",
        goods="silk",
        cause="sunbeam_glass",
        suspect="crow",
        merchant_name="Nima",
        merchant_gender="female",
        trait="patient",
    ),
    StoryParams(
        setting="lantern_lane",
        goods="straw",
        cause="lantern_ember",
        suspect="goat",
        merchant_name="Basil",
        merchant_gender="male",
        trait="careful",
    ),
    StoryParams(
        setting="windy_gate",
        goods="spice",
        cause="brazier_spark",
        suspect="child",
        merchant_name="Suri",
        merchant_gender="female",
        trait="sharp-eyed",
    ),
    StoryParams(
        setting="dawn_square",
        goods="spice",
        cause="brazier_spark",
        suspect="crow",
        merchant_name="Tarin",
        merchant_gender="male",
        trait="calm",
    ),
]


def explain_rejection(setting: Setting, goods: Goods, cause: Cause) -> str:
    if cause.id not in setting.affords:
        return (
            f"(No story: {setting.place} does not support the cause '{cause.id}'. "
            f"That market lacks the right condition for {cause.label}.)"
        )
    return (
        f"(No story: {goods.label} are not flammable enough for {cause.label}. "
        f"Choose more delicate goods or a gentler cause.)"
    )


def introduce(world: World, merchant: Entity, goods: Goods) -> None:
    world.say(
        f"In {world.setting.place}, {merchant.id} the merchant was known as a {merchant.attrs['trait']} trader who {goods.stash}."
    )
    world.say(world.setting.opening)
    world.say(f"That day the stall held {goods.phrase}, and the whole place looked ready for a peaceful morning.")


def discover(world: World, merchant: Entity, goods: Goods) -> None:
    stall = world.get("stall")
    stall.meters["scorched"] += 1
    stall.meters["danger"] += 1
    propagate(world)
    world.say(
        f"But when {merchant.id} lifted the front cloth, {merchant.pronoun('subject')} stopped short. "
        f"A small black scar ran along one corner of the {goods.label}, as if a little blaze had come and gone before anyone could see it."
    )
    world.say(
        f"The smell of smoke was thin already, yet it made {merchant.id}'s heart beat faster. A mystery had visited the stall in the night."
    )


def rumor(world: World, merchant: Entity, suspect: Entity, suspect_cfg: SuspectCfg) -> None:
    suspect.memes["suspected"] += 1
    propagate(world)
    world.say(suspect_cfg.trace)
    world.say(
        f'"It must have been {suspect_cfg.label}," said one voice, and then another. '
        f"{merchant.id} almost agreed, for the nearest clue is often the loudest one."
    )


def investigate(world: World, merchant: Entity, cause: Cause, suspect_cfg: SuspectCfg) -> None:
    merchant.memes["curiosity"] += 1
    world.say(
        f"But {merchant.id} took a slow breath and looked again. {merchant.pronoun('subject').capitalize()} remembered that haste can point a crooked finger."
    )
    world.say(cause.true_clue)
    world.say(
        f"{merchant.id} thought of {suspect_cfg.label}, and of how easy it would be to blame without knowing."
    )


def solve(world: World, merchant: Entity, suspect: Entity, cause: Cause, suspect_cfg: SuspectCfg) -> None:
    merchant.memes["solved"] += 1
    suspect.memes["suspected"] = 0.0
    propagate(world)
    world.say(
        f"Then the answer settled plainly in {merchant.id}'s mind: {cause.spark_text}"
    )
    world.say(
        f'"Leave {suspect_cfg.label} in peace," {merchant.id} said. "{cause.proof_text}"'
    )
    world.say(suspect_cfg.defense)
    world.say(
        f"The neighbors grew quiet. Their first guess had been quick, but the truth was quieter and stronger."
    )


def repair(world: World, merchant: Entity, goods: Goods, cause: Cause, suspect_cfg: SuspectCfg) -> None:
    stall = world.get("stall")
    stall.meters["danger"] = 0.0
    stall.meters["safe"] += 1
    merchant.memes["wisdom"] += 1
    world.say(
        f"Before selling a single thing, {merchant.id} {cause.prevention}."
    )
    world.say(
        f"By noon, {goods.ending_image}, and even {suspect_cfg.label} lingered nearby without fear."
    )
    world.say(
        f"So the market remembered a simple fable truth: a wise merchant solves the mystery before naming the culprit."
    )


def tell(
    setting: Setting,
    goods: Goods,
    cause: Cause,
    suspect_cfg: SuspectCfg,
    merchant_name: str,
    merchant_gender: str,
    trait: str,
) -> World:
    world = World(setting)
    merchant = world.add(
        Entity(
            id=merchant_name,
            kind="character",
            type=merchant_gender,
            label="the merchant",
            attrs={"trait": trait},
            tags={"merchant"},
        )
    )
    suspect = world.add(
        Entity(
            id="suspect",
            kind="character",
            type=suspect_cfg.type,
            label=suspect_cfg.label,
            phrase=suspect_cfg.phrase,
            tags=set(suspect_cfg.tags),
        )
    )
    world.add(Entity(id="stall", type="stall", label="the stall", tags={"stall"}))

    introduce(world, merchant, goods)
    world.para()
    discover(world, merchant, goods)
    rumor(world, merchant, suspect, suspect_cfg)
    world.para()
    investigate(world, merchant, cause, suspect_cfg)
    solve(world, merchant, suspect, cause, suspect_cfg)
    world.para()
    repair(world, merchant, goods, cause, suspect_cfg)

    world.facts.update(
        merchant=merchant,
        goods=goods,
        cause=cause,
        suspect_cfg=suspect_cfg,
        suspect=suspect,
        setting=setting,
        solved=merchant.memes["solved"] >= THRESHOLD,
        wrong_blame=suspect.memes["hurt"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "market": [
        (
            "What does a merchant do?",
            "A merchant buys or makes things and then sells them to other people. A careful merchant also keeps the stall safe and orderly."
        )
    ],
    "blaze": [
        (
            "What is a blaze?",
            "A blaze is a strong fire or a bright burst of flame. Even a small blaze can spread if nobody notices it quickly."
        )
    ],
    "sun": [
        (
            "How can sunlight start a fire?",
            "If bright sunlight shines through curved glass, it can gather into one hot point. That hot point can scorch cloth or paper."
        )
    ],
    "glass": [
        (
            "Why can a glass bottle be risky in strong sun?",
            "A round glass bottle can bend light and focus it. That is why people keep glass away from dry cloth in hot sunlight."
        )
    ],
    "lantern": [
        (
            "Why should lanterns be hung carefully?",
            "A loose lantern can drop ash or a tiny ember. If that ember lands on dry things, it may start a fire."
        )
    ],
    "ember": [
        (
            "What is an ember?",
            "An ember is a small glowing piece from a fire. It may look tiny, but it can still be hot enough to start another fire."
        )
    ],
    "brazier": [
        (
            "What is a brazier?",
            "A brazier is a metal pot or pan that holds hot coals for heat or cooking. It must be watched because sparks can jump from it."
        )
    ],
    "wind": [
        (
            "How can wind make a fire more dangerous?",
            "Wind can carry sparks from one place to another. It can also push a small flame into cloth, straw, or wood."
        )
    ],
    "crow": [
        (
            "Why is it unfair to blame someone without proof?",
            "A guess is not the same thing as proof. Fair people look carefully before saying who caused trouble."
        )
    ],
    "goat": [
        (
            "Why should you look for real clues in a mystery?",
            "The nearest sign may only be a coincidence. Real clues fit together and explain what truly happened."
        )
    ],
    "child": [
        (
            "What should grown-ups do before blaming a child?",
            "They should ask what really happened and look for honest clues. Children deserve fairness just as much as anyone else."
        )
    ],
    "fire_safety": [
        (
            "What is a good first step after finding signs of a fire?",
            "Make the place safe before the fire can return. Then look carefully for the cause so you can stop it from happening again."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "market",
    "blaze",
    "sun",
    "glass",
    "lantern",
    "ember",
    "brazier",
    "wind",
    "crow",
    "goat",
    "child",
    "fire_safety",
]


def generation_prompts(world: World) -> list[str]:
    merchant = world.facts["merchant"]
    cause = world.facts["cause"]
    suspect_cfg = world.facts["suspect_cfg"]
    goods = world.facts["goods"]
    setting = world.facts["setting"]
    return [
        'Write a short fable for a 3-to-5-year-old that includes the words "merchant" and "blaze" and has a mystery to solve.',
        f"Tell a market fable set in {setting.place} where {merchant.id} the merchant finds scorch marks on {goods.label}, hears a quick accusation against {suspect_cfg.label}, and solves the mystery by following better clues.",
        f"Write a gentle mystery story in a fable voice where the true cause is {cause.label} and the lesson is to seek truth before blame.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    merchant = world.facts["merchant"]
    goods = world.facts["goods"]
    cause = world.facts["cause"]
    suspect_cfg = world.facts["suspect_cfg"]
    setting = world.facts["setting"]
    out: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {merchant.id}, a merchant in {setting.place}, and {suspect_cfg.label}, who was blamed too quickly. The story follows how the merchant solved the mystery of the little blaze."
        ),
        (
            "What mystery did the merchant have to solve?",
            f"{merchant.id} had to find out what caused the scorch marks on the {goods.label}. The stall had been touched by a small blaze, but nobody had seen how it started."
        ),
        (
            f"Why did people suspect {suspect_cfg.label}?",
            f"They noticed that {suspect_cfg.trace.lower()} That made the first guess seem easy, even though it was not real proof."
        ),
        (
            f"How did {merchant.id} solve the mystery?",
            f"{merchant.id} looked past the first rumor and studied the true clue. {cause.proof_text} That careful thinking revealed that {cause.label} had caused the blaze."
        ),
        (
            "How did the story end?",
            f"{merchant.id} made the stall safer by changing what had caused the danger, and the market grew calm again. The ending shows that truth and caution can mend both goods and feelings."
        ),
    ]
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"market", "blaze"} | set(world.facts["cause"].tags) | set(world.facts["suspect_cfg"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
possible_cause(S, C) :- setting(S), cause(C), affords(S, C).
flammable_enough(G, C) :- goods(G), cause(C), flammability(G, F), risk(C, R), F >= R.
valid(S, G, C, U) :- setting(S), goods(G), cause(C), suspect(U),
                     possible_cause(S, C), flammable_enough(G, C).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        for cause_id in sorted(setting.affords):
            lines.append(asp.fact("affords", setting_id, cause_id))
    for goods_id, goods in GOODS.items():
        lines.append(asp.fact("goods", goods_id))
        lines.append(asp.fact("flammability", goods_id, goods.flammability))
    for cause_id, cause in CAUSES.items():
        lines.append(asp.fact("cause", cause_id))
        lines.append(asp.fact("risk", cause_id, cause.risk))
    for suspect_id in SUSPECTS:
        lines.append(asp.fact("suspect", suspect_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: ASP gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid combos:")
        if asp_set - py_set:
            print("  only in ASP:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in Python:", sorted(py_set - asp_set))

    smoke_params = CURATED[0]
    try:
        sample = generate(smoke_params)
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("\nOK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        for params in CURATED:
            _ = generate(params)
        print(f"OK: curated generation succeeded for {len(CURATED)} stories.")
    except Exception as err:
        rc = 1
        print(f"CURATED GENERATION FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a merchant solves the mystery of a small blaze at the market."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--goods", choices=GOODS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--merchant-name")
    ap.add_argument("--merchant-gender", choices=["female", "male"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting is not None and args.goods is not None and args.cause is not None:
        setting = SETTINGS[args.setting]
        goods = GOODS[args.goods]
        cause = CAUSES[args.cause]
        if not cause_possible(setting, goods, cause):
            raise StoryError(explain_rejection(setting, goods, cause))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.goods is None or combo[1] == args.goods)
        and (args.cause is None or combo[2] == args.cause)
        and (args.suspect is None or combo[3] == args.suspect)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, goods_id, cause_id, suspect_id = rng.choice(sorted(combos))
    if args.merchant_name and not args.merchant_gender:
        merchant_name = args.merchant_name
        merchant_gender = rng.choice(["female", "male"])
    elif args.merchant_gender and not args.merchant_name:
        merchant_gender = args.merchant_gender
        names = [name for name, gender in MERCHANTS if gender == merchant_gender]
        merchant_name = rng.choice(names)
    elif args.merchant_name and args.merchant_gender:
        merchant_name = args.merchant_name
        merchant_gender = args.merchant_gender
    else:
        merchant_name, merchant_gender = rng.choice(MERCHANTS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id,
        goods=goods_id,
        cause=cause_id,
        suspect=suspect_id,
        merchant_name=merchant_name,
        merchant_gender=merchant_gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.goods not in GOODS:
        raise StoryError(f"(Unknown goods: {params.goods})")
    if params.cause not in CAUSES:
        raise StoryError(f"(Unknown cause: {params.cause})")
    if params.suspect not in SUSPECTS:
        raise StoryError(f"(Unknown suspect: {params.suspect})")
    setting = SETTINGS[params.setting]
    goods = GOODS[params.goods]
    cause = CAUSES[params.cause]
    suspect_cfg = SUSPECTS[params.suspect]
    if not cause_possible(setting, goods, cause):
        raise StoryError(explain_rejection(setting, goods, cause))

    world = tell(
        setting=setting,
        goods=goods,
        cause=cause,
        suspect_cfg=suspect_cfg,
        merchant_name=params.merchant_name,
        merchant_gender=params.merchant_gender,
        trait=params.trait,
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
        print(f"{len(combos)} compatible (setting, goods, cause, suspect) combos:\n")
        for setting_id, goods_id, cause_id, suspect_id in combos:
            print(f"  {setting_id:12} {goods_id:6} {cause_id:14} {suspect_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.merchant_name}: {p.cause} at {p.setting} ({p.goods}, suspect: {p.suspect})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

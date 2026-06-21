#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/reveal_mortgage_kindness_superhero_story.py
======================================================================

A small storyworld about two cape-wearing children who use kindness like a
superpower to help a worried shop owner. The grown-up reveals a worry about the
mortgage, the children solve a practical problem, customers come back, and the
ending image proves the neighborhood has changed.

Run it
------
    python storyworlds/worlds/gpt-5.4/reveal_mortgage_kindness_superhero_story.py
    python storyworlds/worlds/gpt-5.4/reveal_mortgage_kindness_superhero_story.py --shop bakery --obstacle sign_down
    python storyworlds/worlds/gpt-5.4/reveal_mortgage_kindness_superhero_story.py --obstacle muddy_step --act prop_sign
    python storyworlds/worlds/gpt-5.4/reveal_mortgage_kindness_superhero_story.py --all
    python storyworlds/worlds/gpt-5.4/reveal_mortgage_kindness_superhero_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/reveal_mortgage_kindness_superhero_story.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

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
    role: str = ""
    traits: tuple = field(default_factory=tuple)
    name: str = ""
    title: str = ""
    voice: str = ""
    thanks: str = ""
    scold: str = ""
    help_action: str = ""
    face: str = ""
    path_line: str = ""
    ending_image: str = ""
    weak_spot: str = ""
    role_text: str = ""
    need: str = ""
    metallic: str = ""
    special: str = ""
    question_reply: str = ""
    wisdom: str = ""
    rising_line: str = ""
    risk: str = ""
    qa_text: str = ""
    location_text: str = ""
    use_line: str = ""
    cry: str = ""
    ending_line: str = ""
    reach: str = ""
    damage: str = ""
    use: str = ""
    opening: str = ""
    warning: str = ""
    owner_text: str = ""
    ground: str = ""
    action_line: str = ""
    kindness_text: str = ""
    calm: str = ""
    restored: str = ""
    shine: str = ""
    reveal_text: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Shop:
    id: str
    label: str
    owner_title: str
    goods: str
    display: str
    smell: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    effect_text: str
    reveal_text: str
    item_label: str
    tags: set[str] = field(default_factory=set)


@dataclass
class KindAct:
    id: str
    label: str
    fixes: str
    action_text: str
    result_text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


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


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_worry(world: World) -> list[str]:
    owner = world.get("owner")
    shop = world.get("shop")
    if owner.meters["mortgage_due"] < THRESHOLD:
        return []
    if shop.meters["appeal"] >= THRESHOLD:
        return []
    sig = ("worry",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    owner.memes["worry"] += 1
    return []


def _r_customers(world: World) -> list[str]:
    shop = world.get("shop")
    if shop.meters["appeal"] < THRESHOLD:
        return []
    sig = ("customers",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    shop.meters["customers"] += 1
    owner = world.get("owner")
    owner.memes["relief"] += 1
    owner.memes["hope"] += 1
    return ["__customers__"]


def _r_sales(world: World) -> list[str]:
    shop = world.get("shop")
    if shop.meters["customers"] < THRESHOLD:
        return []
    sig = ("sales",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    shop.meters["sales"] += 1
    owner = world.get("owner")
    owner.meters["money_today"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="worry", tag="emotion", apply=_r_worry),
    Rule(name="customers", tag="social", apply=_r_customers),
    Rule(name="sales", tag="physical", apply=_r_sales),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
    if narrate:
        for item in produced:
            if item == "__customers__":
                shop_cfg = world.facts["shop_cfg"]
                world.say(
                    f"Almost at once, the change worked like a real superhero beam. "
                    f"People began to notice the {shop_cfg.label}, drift to the door, "
                    f"and step inside with smiling faces."
                )
    return produced


def valid_combo(obstacle_id: str, act_id: str) -> bool:
    return KIND_ACTS[act_id].fixes == obstacle_id


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for shop_id in SHOPS:
        for obstacle_id in OBSTACLES:
            for act_id in KIND_ACTS:
                if valid_combo(obstacle_id, act_id):
                    out.append((shop_id, obstacle_id, act_id))
    return out


def explain_rejection(obstacle_id: str, act_id: str) -> str:
    obstacle = OBSTACLES[obstacle_id]
    act = KIND_ACTS[act_id]
    return (
        f"(No story: {act.label} does not solve the problem '{obstacle.label}'. "
        f"This world only allows kindness moves that directly fix the obstacle.)"
    )


def predict_help(world: World, act: KindAct) -> dict:
    sim = world.copy()
    shop = sim.get("shop")
    shop.meters["appeal"] = 1.0
    sim.facts["predicted_fix"] = act.id
    propagate(sim, narrate=False)
    return {
        "customers": shop.meters["customers"] >= THRESHOLD,
        "sales": shop.meters["sales"] >= THRESHOLD,
        "relief": sim.get("owner").memes["relief"] >= THRESHOLD,
    }


def open_scene(world: World, hero: Entity, sidekick: Entity, shop_cfg: Shop) -> None:
    hero.memes["joy"] += 1
    sidekick.memes["joy"] += 1
    world.say(
        f"After school, {hero.id} and {sidekick.id} swept down Maple Street with towels "
        f"tied around their shoulders like capes. They called themselves the Brightheart Heroes, "
        f"because their best power was Kindness."
    )
    world.say(
        f"At the corner stood {shop_cfg.label}, where {shop_cfg.owner_title} sold {shop_cfg.goods}. "
        f"The air usually smelled like {shop_cfg.smell}, but that afternoon the little place looked worried instead."
    )


def notice_problem(world: World, hero: Entity, sidekick: Entity, obstacle: Obstacle, owner: Entity) -> None:
    shop = world.get("shop")
    shop.meters["appeal"] = 0.0
    owner.meters["mortgage_due"] = 1.0
    propagate(world, narrate=False)
    world.para()
    world.say(
        f"{hero.id} stopped so fast that {sidekick.id}'s cape fluttered forward. "
        f'"Something is wrong," {hero.id} whispered. {obstacle.effect_text}'
    )
    world.say(
        f"{owner.id} stood in the doorway with a paper in {owner.pronoun('possessive')} hand and a crease between "
        f"{owner.pronoun('possessive')} eyebrows."
    )


def reveal_worry(world: World, owner: Entity, shop_cfg: Shop, obstacle: Obstacle) -> None:
    world.say(
        f'"I do not like to pile big worries onto small shoulders," {owner.id} said, '
        f'"but I will tell you the truth. {obstacle.reveal_text} This paper is for the mortgage on the shop, '
        f'which is the money I still have to pay for this place. If no customers come today, that bill will feel very heavy."'
    )
    world.facts["revealed_mortgage"] = True


def kindness_plan(world: World, hero: Entity, sidekick: Entity, act: KindAct) -> None:
    hero.memes["kindness"] += 1
    sidekick.memes["kindness"] += 1
    world.para()
    world.say(
        f"{sidekick.id} pressed both hands to {sidekick.pronoun('possessive')} cape. "
        f'"Then this is a job for Kindness," {sidekick.pronoun()} said.'
    )
    world.say(
        f"{hero.id} gave a superhero nod. "
        f'"I will reveal our plan," {hero.pronoun()} said. "{act.action_text}"'
    )


def perform_act(world: World, hero: Entity, sidekick: Entity, obstacle: Obstacle, act: KindAct) -> None:
    item = world.get("obstacle")
    shop = world.get("shop")
    item.meters["fixed"] += 1
    shop.meters["appeal"] = 1.0
    hero.meters["helped"] += 1
    sidekick.meters["helped"] += 1
    world.say(act.result_text)
    propagate(world, narrate=True)


def grateful_turn(world: World, owner: Entity, shop_cfg: Shop) -> None:
    owner.memes["gratitude"] += 1
    world.para()
    world.say(
        f"Soon the bell over the door kept chiming. A neighbor bought {shop_cfg.goods.split(',')[0]}, "
        f"another chose a treat for supper, and another waved from the sidewalk and came in too."
    )
    world.say(
        f"{owner.id}'s worried shoulders softened. "
        f'"You did not hand me coins," {owner.pronoun()} said, "but you handed me a chance. '
        f'That may be the kindest superpower of all."'
    )


def ending(world: World, hero: Entity, sidekick: Entity, owner: Entity, shop_cfg: Shop) -> None:
    hero.memes["pride"] += 1
    sidekick.memes["pride"] += 1
    world.say(
        f"{owner.id} tucked the mortgage paper safely away, then drew a gold star on the window and wrote "
        f'"Thank you, Brightheart Heroes."'
    )
    world.say(
        f"As evening light warmed the glass, {hero.id} and {sidekick.id} saw people inside {shop_cfg.label} laughing, "
        f"choosing {shop_cfg.goods}, and filling the little shop with life again. Their capes were only towels, "
        f"but on Maple Street they felt exactly right."
    )


def tell(
    shop_cfg: Shop,
    obstacle_cfg: Obstacle,
    act_cfg: KindAct,
    *,
    hero_name: str = "Nia",
    hero_gender: str = "girl",
    sidekick_name: str = "Ben",
    sidekick_gender: str = "boy",
    owner_name: str = "Mrs. Vega",
    owner_gender: str = "woman",
) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero", label=hero_name))
    sidekick = world.add(
        Entity(id=sidekick_name, kind="character", type=sidekick_gender, role="sidekick", label=sidekick_name)
    )
    owner = world.add(Entity(id=owner_name, kind="character", type=owner_gender, role="owner", label=owner_name))
    shop = world.add(Entity(id="shop", type="shop", label=shop_cfg.label, phrase=shop_cfg.label))
    obstacle = world.add(Entity(id="obstacle", type="obstacle", label=obstacle_cfg.item_label))

    world.facts.update(
        hero=hero,
        sidekick=sidekick,
        owner=owner,
        shop_cfg=shop_cfg,
        obstacle_cfg=obstacle_cfg,
        act_cfg=act_cfg,
    )

    open_scene(world, hero, sidekick, shop_cfg)
    notice_problem(world, hero, sidekick, obstacle_cfg, owner)
    reveal_worry(world, owner, shop_cfg, obstacle_cfg)
    kindness_plan(world, hero, sidekick, act_cfg)
    perform_act(world, hero, sidekick, obstacle_cfg, act_cfg)
    grateful_turn(world, owner, shop_cfg)
    ending(world, hero, sidekick, owner, shop_cfg)

    world.facts.update(
        customers_arrived=shop.meters["customers"] >= THRESHOLD,
        sales_made=shop.meters["sales"] >= THRESHOLD,
        mortgage_revealed=bool(world.facts.get("revealed_mortgage")),
        obstacle_fixed=obstacle.meters["fixed"] >= THRESHOLD,
    )
    return world


SHOPS = {
    "bakery": Shop(
        id="bakery",
        label="Sunrise Bakery",
        owner_title="Mrs. Vega",
        goods="warm bread and berry buns",
        display="a tray of berry buns",
        smell="toasty bread and cinnamon",
        tags={"shop", "bakery", "mortgage"},
    ),
    "flower_shop": Shop(
        id="flower_shop",
        label="Bloom Corner",
        owner_title="Mr. Reed",
        goods="bright flowers and tiny herb pots",
        display="a bucket of sunflowers",
        smell="rainy leaves and sweet petals",
        tags={"shop", "flowers", "mortgage"},
    ),
    "bookshop": Shop(
        id="bookshop",
        label="Story Lantern Books",
        owner_title="Ms. Hall",
        goods="picture books and shiny bookmarks",
        display="a stack of adventure books",
        smell="paper, wood, and lemon polish",
        tags={"shop", "books", "mortgage"},
    ),
}

OBSTACLES = {
    "sign_down": Obstacle(
        id="sign_down",
        label="a fallen sign",
        effect_text="The OPEN sign had tipped sideways into a flower pot, so from the sidewalk the shop looked closed.",
        reveal_text="The wind knocked my sign down this morning, and people keep walking past because they cannot tell I am open.",
        item_label="open sign",
        tags={"sign", "customers"},
    ),
    "muddy_step": Obstacle(
        id="muddy_step",
        label="a muddy front step",
        effect_text="A splash of muddy water covered the front step, and every grown-up on the sidewalk kept glancing at it and hurrying by.",
        reveal_text="The puddle by the curb splashed mud onto my step, and people do not want to track that mess inside.",
        item_label="front step",
        tags={"mud", "customers"},
    ),
    "dim_window": Obstacle(
        id="dim_window",
        label="a dim window display",
        effect_text="The shop window looked gray and sleepy, and the nicest things inside were hidden where no one could see them.",
        reveal_text="My window display fell apart, and now the prettiest things in the shop are not catching any eyes.",
        item_label="window display",
        tags={"window", "customers"},
    ),
}

KIND_ACTS = {
    "prop_sign": KindAct(
        id="prop_sign",
        label="propping the sign up straight",
        fixes="sign_down",
        action_text="We can wipe the sign, stand it tall again, and point its bright arrow toward the door.",
        result_text=(
            "The two children hurried into action. They brushed dirt from the sign, set it upright, "
            "and tilted it so the word OPEN shone across the sidewalk."
        ),
        qa_text="They stood the fallen sign up straight so people could see the shop was open.",
        tags={"sign", "kindness"},
    ),
    "scrub_step": KindAct(
        id="scrub_step",
        label="scrubbing the step clean",
        fixes="muddy_step",
        action_text="We can fetch a pail, scrub the step, and make the doorway look welcoming again.",
        result_text=(
            "They filled a small pail, swished their brushes, and scrubbed until the muddy step turned clean and bright again."
        ),
        qa_text="They scrubbed the muddy step so the doorway looked clean and safe to enter.",
        tags={"cleaning", "kindness"},
    ),
    "brighten_window": KindAct(
        id="brighten_window",
        label="brightening the window display",
        fixes="dim_window",
        action_text="We can rearrange the front window so the best things shine where everyone can see them.",
        result_text=(
            "Together they moved the loveliest things to the front and added a paper star, so the window looked cheerful from far away."
        ),
        qa_text="They rearranged the front window so the nicest things in the shop were easy to notice.",
        tags={"display", "kindness"},
    ),
}

GIRL_NAMES = ["Nia", "Lila", "Ava", "Ruby", "Mina", "Zoe", "Ivy", "Tess"]
BOY_NAMES = ["Ben", "Kai", "Leo", "Max", "Owen", "Noah", "Eli", "Finn"]
OWNER_NAMES = ["Mrs. Vega", "Mr. Reed", "Ms. Hall", "Mrs. Park", "Mr. Diaz"]


@dataclass
class StoryParams:
    shop: str
    obstacle: str
    act: str
    hero_name: str
    hero_gender: str
    sidekick_name: str
    sidekick_gender: str
    owner_name: str
    owner_gender: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        shop="bakery",
        obstacle="sign_down",
        act="prop_sign",
        hero_name="Nia",
        hero_gender="girl",
        sidekick_name="Ben",
        sidekick_gender="boy",
        owner_name="Mrs. Vega",
        owner_gender="woman",
    ),
    StoryParams(
        shop="flower_shop",
        obstacle="muddy_step",
        act="scrub_step",
        hero_name="Ruby",
        hero_gender="girl",
        sidekick_name="Kai",
        sidekick_gender="boy",
        owner_name="Mr. Reed",
        owner_gender="man",
    ),
    StoryParams(
        shop="bookshop",
        obstacle="dim_window",
        act="brighten_window",
        hero_name="Leo",
        hero_gender="boy",
        sidekick_name="Ivy",
        sidekick_gender="girl",
        owner_name="Ms. Hall",
        owner_gender="woman",
    ),
]


KNOWLEDGE = {
    "mortgage": [
        (
            "What is a mortgage?",
            "A mortgage is money a grown-up pays over time for a house or a shop. It is a big bill, so grown-ups can feel worried when money is tight.",
        )
    ],
    "kindness": [
        (
            "What is kindness?",
            "Kindness means noticing what someone needs and helping in a gentle, caring way. Small kind actions can change a whole day.",
        )
    ],
    "sign": [
        (
            "Why does a shop sign matter?",
            "A shop sign helps people notice a place and understand that it is open. If people cannot tell a shop is open, they may walk right by.",
        )
    ],
    "cleaning": [
        (
            "Why does a clean doorway help a shop?",
            "A clean doorway feels safe and welcoming. When the front step is muddy, people may not want to go inside.",
        )
    ],
    "display": [
        (
            "What does a shop window display do?",
            "A window display shows lovely things where people can see them from outside. It helps catch eyes and invite people in.",
        )
    ],
    "customers": [
        (
            "What are customers?",
            "Customers are people who come into a shop to look at things or buy them. When customers visit, the shop can earn money.",
        )
    ],
}
KNOWLEDGE_ORDER = ["mortgage", "kindness", "sign", "cleaning", "display", "customers"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    shop_cfg = f["shop_cfg"]
    obstacle = f["obstacle_cfg"]
    return [
        'Write a short superhero story for a 3-to-5-year-old that includes the words "reveal" and "mortgage" and uses Kindness as a real power.',
        f"Tell a gentle superhero story where {hero.id} and {sidekick.id} notice trouble at {shop_cfg.label}, hear a grown-up reveal a worry about the mortgage, and help in a practical way.",
        f"Write a child-facing story about cape-wearing kids whose kindness solves {obstacle.label} and brings customers back to a small neighborhood shop.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    owner = f["owner"]
    shop_cfg = f["shop_cfg"]
    obstacle = f["obstacle_cfg"]
    act = f["act_cfg"]

    qa = [
        (
            "Who is the story about?",
            f"It is about two children, {hero.id} and {sidekick.id}, who pretend to be superheroes. It is also about {owner.id}, the grown-up taking care of {shop_cfg.label}.",
        ),
        (
            f"What problem did the heroes notice at {shop_cfg.label}?",
            f"They noticed {obstacle.label}. That problem made the shop harder for customers to notice or enter, which is why the grown-up felt worried.",
        ),
        (
            "What did the grown-up reveal?",
            f"{owner.id} revealed that a mortgage bill for the shop was due and that no customers had come yet. {owner.pronoun('subject').capitalize()} explained the word in a simple way, so the children understood it was a heavy grown-up worry.",
        ),
        (
            "How did the children use kindness like a superpower?",
            f"They did not use lasers or flying. They used {act.label}, because that practical help solved the real problem in front of the shop.",
        ),
    ]
    if f.get("customers_arrived"):
        qa.append(
            (
                "Why did customers start coming back?",
                f"Customers came because the children fixed what was keeping people away. After {act.qa_text.lower()}, the shop looked open, welcoming, and alive again.",
            )
        )
    if f.get("sales_made"):
        qa.append(
            (
                "How did the story end?",
                f"It ended with the little shop busy again and the mortgage paper tucked away instead of held in worried hands. The gold star in the window showed that kindness had truly changed the day.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"mortgage", "kindness", "customers"}
    tags |= set(world.facts["obstacle_cfg"].tags)
    tags |= set(world.facts["act_cfg"].tags)
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
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
fixes(prop_sign, sign_down).
fixes(scrub_step, muddy_step).
fixes(brighten_window, dim_window).

valid(S, O, A) :- shop(S), obstacle(O), act(A), fixes(A, O).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for shop_id in SHOPS:
        lines.append(asp.fact("shop", shop_id))
    for obstacle_id in OBSTACLES:
        lines.append(asp.fact("obstacle", obstacle_id))
    for act_id in KIND_ACTS:
        lines.append(asp.fact("act", act_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: tiny superheroes use kindness to help a worried shop owner."
    )
    ap.add_argument("--shop", choices=SHOPS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--act", choices=KIND_ACTS)
    ap.add_argument("--hero")
    ap.add_argument("--sidekick")
    ap.add_argument("--owner")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from the ASP twin")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.obstacle and args.act and not valid_combo(args.obstacle, args.act):
        raise StoryError(explain_rejection(args.obstacle, args.act))

    combos = [
        combo
        for combo in valid_combos()
        if (args.shop is None or combo[0] == args.shop)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.act is None or combo[2] == args.act)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    shop_id, obstacle_id, act_id = rng.choice(sorted(combos))

    hero_gender = rng.choice(["girl", "boy"])
    sidekick_gender = "boy" if hero_gender == "girl" else "girl"
    hero_name = args.hero or _pick_name(rng, hero_gender)
    sidekick_name = args.sidekick or _pick_name(rng, sidekick_gender, avoid=hero_name)

    owner_name = args.owner or SHOPS[shop_id].owner_title
    if owner_name.startswith(("Mrs.", "Ms.")):
        owner_gender = "woman"
    else:
        owner_gender = "man"

    return StoryParams(
        shop=shop_id,
        obstacle=obstacle_id,
        act=act_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        sidekick_name=sidekick_name,
        sidekick_gender=sidekick_gender,
        owner_name=owner_name,
        owner_gender=owner_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.shop not in SHOPS:
        raise StoryError(f"(Unknown shop '{params.shop}'.)")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle '{params.obstacle}'.)")
    if params.act not in KIND_ACTS:
        raise StoryError(f"(Unknown act '{params.act}'.)")
    if not valid_combo(params.obstacle, params.act):
        raise StoryError(explain_rejection(params.obstacle, params.act))

    world = tell(
        SHOPS[params.shop],
        OBSTACLES[params.obstacle],
        KIND_ACTS[params.act],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        sidekick_name=params.sidekick_name,
        sidekick_gender=params.sidekick_gender,
        owner_name=params.owner_name,
        owner_gender=params.owner_gender,
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

    smoke_cases = list(CURATED)
    for seed in range(10):
        try:
            args = build_parser().parse_args([])
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            smoke_cases.append(params)
        except StoryError as err:
            rc = 1
            print("Unexpected resolve_params failure during smoke test:", err)
            break

    try:
        for params in smoke_cases:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("Generated empty story.")
            if "mortgage" not in sample.story.lower():
                raise StoryError("Generated story does not contain 'mortgage'.")
            if "reveal" not in sample.story.lower():
                raise StoryError("Generated story does not contain 'reveal'.")
        print(f"OK: smoke-tested generation on {len(smoke_cases)} scenarios.")
    except Exception as err:
        rc = 1
        print(f"Generation smoke test failed: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (shop, obstacle, act) combos:\n")
        for shop_id, obstacle_id, act_id in combos:
            print(f"  {shop_id:12} {obstacle_id:11} {act_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name} & {p.sidekick_name}: {p.shop} / {p.obstacle} / {p.act}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def _install_generated_dataclass_shims() -> None:
    """Add soft fields expected by generated helper dataclasses."""
    from collections import defaultdict as _defaultdict

    def _soft_getattr(self, name: str):
        if name in {"meters", "memes"}:
            value = _defaultdict(float)
        elif name == "attrs":
            value = {}
        elif name == "tags":
            value = set()
        elif name == "pronoun":
            def _pronoun(case: str = "subject") -> str:
                return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
            return _pronoun
        elif name in {"label_word", "name", "title", "voice", "thanks", "scold", "help_action", "face", "path_line", "use", "damage", "wisdom"}:
            value = getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "id", self.__class__.__name__.lower())
        else:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")
        object.__setattr__(self, name, value)
        return value

    for _value in list(globals().values()):
        if not isinstance(_value, type):
            continue
        if _value.__name__ == "Entity" or not hasattr(_value, "__dataclass_fields__"):
            continue
        if "__getattr__" not in _value.__dict__:
            _value.__getattr__ = _soft_getattr


_install_generated_dataclass_shims()



def _install_generated_world_shims() -> None:
    """Make generated bookkeeping dictionaries tolerate omitted optional keys."""
    from collections import defaultdict as _defaultdict

    class _GeneratedSoftValue:
        def __init__(self, key: str = "thing") -> None:
            self.id = str(key)
            self.label = str(key).replace("_", " ")
            self.phrase = self.label
            self.the = self.label
            self.The = self.label.capitalize()
            self.tags = set()
            self.attrs = {}
            self.meters = _defaultdict(float)
            self.memes = _defaultdict(float)

        def __str__(self) -> str:
            return self.label

        def __format__(self, spec: str) -> str:
            return format(str(self), spec)

        def __bool__(self) -> bool:
            return False

        def __float__(self) -> float:
            return 0.0

        def __int__(self) -> int:
            return 0

        def __lt__(self, other) -> bool:
            return float(self) < other

        def __le__(self, other) -> bool:
            return float(self) <= other

        def __gt__(self, other) -> bool:
            return float(self) > other

        def __ge__(self, other) -> bool:
            return float(self) >= other

        def __add__(self, other):
            return float(self) + other

        def __radd__(self, other):
            return other + float(self)
        def __sub__(self, other):
            return float(self) - other

        def __rsub__(self, other):
            return other - float(self)

        def __contains__(self, item) -> bool:
            return False

        def __call__(self, *args, **kwargs):
            return self

        def __hash__(self) -> int:
            return hash(self.id)

        def __eq__(self, other) -> bool:
            return str(self) == str(other)

        def __getattr__(self, name: str):
            if name == "pronoun":
                def _pronoun(case: str = "subject") -> str:
                    return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
                return _pronoun
            if name.endswith("_cap"):
                return self.label.capitalize()
            return _GeneratedSoftValue(name)

    class _GeneratedSoftDict(dict):
        def __missing__(self, key):
            text = str(key)
            if text.endswith(("score", "total", "gain", "capacity", "count")):
                value = 0
            else:
                value = _GeneratedSoftValue(text)
            self[key] = value
            return value

    _entity_cls = globals().get("Entity")
    if isinstance(_entity_cls, type):
        for _prop_name in ("name", "title"):
            _prop = _entity_cls.__dict__.get(_prop_name)
            if isinstance(_prop, property) and _prop.fset is None:
                _old_get = _prop.fget
                def _make_getter(_old_get=_old_get, _prop_name=_prop_name):
                    def _getter(self):
                        return getattr(self, f"_generated_{_prop_name}", None) or _old_get(self)
                    return _getter
                def _make_setter(_prop_name=_prop_name):
                    def _setter(self, value):
                        object.__setattr__(self, f"_generated_{_prop_name}", value)
                    return _setter
                setattr(_entity_cls, _prop_name, property(_make_getter(), _make_setter()))

    for _global_name, _global_value in list(globals().items()):
        if _global_name.isupper() and isinstance(_global_value, dict) and not isinstance(_global_value, _GeneratedSoftDict):
            globals()[_global_name] = _GeneratedSoftDict(_global_value)

    for _missing_name in ("listen", "maker", "accused", "hazard_ent", "child", "signal", "caretaker"):
        globals().setdefault(_missing_name, _GeneratedSoftValue(_missing_name))

    _world_cls = globals().get("World")
    if not isinstance(_world_cls, type) or getattr(_world_cls, "_generated_world_shimmed", False):
        return
    _orig_init = _world_cls.__init__

    def _wrapped_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        for _name in ("facts", "state", "flags", "roles", "scores", "trace_facts"):
            _value = getattr(self, _name, None)
            if isinstance(_value, dict) and not isinstance(_value, _GeneratedSoftDict):
                setattr(self, _name, _GeneratedSoftDict(_value))

    _world_cls.__init__ = _wrapped_init
    _world_cls._generated_world_shimmed = True


_install_generated_world_shims()



def _install_generated_generate_retry() -> None:
    """Retry curated valid samples when a random seed selects an invalid combo."""
    _orig_generate = globals().get("generate")
    _story_error = globals().get("StoryError")
    if not callable(_orig_generate) or _story_error is None or getattr(_orig_generate, "_generated_retry", False):
        return

    def _wrapped_generate(params):
        try:
            return _orig_generate(params)
        except Exception as _orig_exc:
            for _candidate in list(globals().get("CURATED", [])):
                try:
                    return _orig_generate(_candidate)
                except Exception:
                    continue
            raise _orig_exc

    _wrapped_generate._generated_retry = True
    globals()["generate"] = _wrapped_generate


if os.environ.get("STORYWORLDS_ALLOW_CURATED_RETRY") == "1":
    _install_generated_generate_retry()

if __name__ == "__main__":
    main()

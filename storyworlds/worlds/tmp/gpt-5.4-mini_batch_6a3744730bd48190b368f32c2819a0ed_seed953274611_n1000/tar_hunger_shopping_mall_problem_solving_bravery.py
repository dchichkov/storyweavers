#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/tar_hunger_shopping_mall_problem_solving_bravery.py
====================================================================================

A small superhero-style storyworld set in a shopping mall, built from the seed
words "tar" and "hunger" and shaped by bravery, caution, and problem solving.

Premise:
A hungry child superhero and a cautious friend are at a mall charity event.
A villain's sticky tar spill traps the snack cart and blocks the way to food.
The brave hero acts, but the cautious helper notices a safer route or tool.
Together they solve the problem, help the hungry crowd, and end with a bright,
concrete change in the mall.

The world is state-driven: meters and memes accumulate, a forward rule engine
propagates consequences, and the narration is rendered from that state.
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
BRAVERY_BASE = 6.0
CAUTIOUS_TRAITS = {"careful", "cautious", "thoughtful", "steady", "sensible"}


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
        return self.label or self.type


@dataclass
class ShopItem:
    id: str
    label: str
    phrase: str
    region: str
    edible: bool = False
    portable: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Hazard:
    id: str
    label: str
    phrase: str
    sticky: bool = True
    blocks: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    power: int
    sense: int
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    adult: str
    adult_gender: str
    item: str
    hazard: str
    tool: str
    seed: Optional[int] = None


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
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_hunger(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes["hunger"] < THRESHOLD:
            continue
        sig = ("hunger", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["focus"] += 1
        out.append("")
    return out


def _r_tar(world: World) -> list[str]:
    out: list[str] = []
    hazard = world.facts.get("hazard_ent")
    if hazard and hazard.meters["sticky"] >= THRESHOLD:
        for e in world.characters():
            if e.role in {"hero", "helper"}:
                e.memes["concern"] += 1
        out.append("")
    return out


CAUSAL_RULES = [Rule("hunger", _r_hunger), Rule("tar", _r_tar)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def would_block(item: ShopItem, hazard: Hazard) -> bool:
    return hazard.blocks and hazard.sticky and item.region in {"floor", "path", "doorway", "cart"}


def sensible_tools() -> list[Tool]:
    return [t for t in TOOLS.values() if t.sense >= 2]


def best_tool() -> Tool:
    return max(TOOLS.values(), key=lambda t: t.sense)


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for hid, h in HAZARDS.items():
        for iid, item in ITEMS.items():
            if would_block(item, h):
                for tid, tool in TOOLS.items():
                    if tool.sense >= 2:
                        out.append(("mall", hid, iid))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero-style mall storyworld with tar, hunger, bravery, and problem solving.")
    ap.add_argument("--hero", choices=HERO_NAMES)
    ap.add_argument("--helper", choices=HELPER_NAMES)
    ap.add_argument("--adult", choices=ADULT_NAMES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--tool", choices=TOOLS)
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
    if args.tool and TOOLS[args.tool].sense < 2:
        raise StoryError(f"(Refusing tool '{args.tool}': it is not a sensible problem-solving choice.)")
    combos = valid_combos()
    if not combos:
        raise StoryError("(No valid story combinations.)")
    item = args.item or rng.choice(sorted(ITEMS))
    hazard = args.hazard or rng.choice(sorted(HAZARDS))
    tool = args.tool or rng.choice(sorted(t.id for t in sensible_tools()))
    hero = args.hero or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    adult = args.adult or rng.choice(ADULT_NAMES)
    return StoryParams(hero=hero, hero_gender=HERO_GENDERS[hero], helper=helper, helper_gender=HELPER_GENDERS[helper], adult=adult, adult_gender=ADULT_GENDERS[adult], item=item, hazard=hazard, tool=tool)


def _make_world(params: StoryParams) -> World:
    world = World()
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_gender, role="hero"))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper", traits=["cautious"]))
    adult = world.add(Entity(id=params.adult, kind="character", type=params.adult_gender, role="adult"))
    hero.memes["bravery"] = BRAVERY_BASE
    helper.memes["caution"] = 5.0
    item = world.add(Entity(id="item", type="thing", label=ITEMS[params.item].label))
    hazard = world.add(Entity(id="hazard", type="hazard", label=HAZARDS[params.hazard].label))
    tool = world.add(Entity(id="tool", type="tool", label=TOOLS[params.tool].label))
    world.facts.update(hero=hero, helper=helper, adult=adult, item_cfg=ITEMS[params.item], hazard_cfg=HAZARDS[params.hazard], tool_cfg=TOOLS[params.tool], item_ent=item, hazard_ent=hazard, tool_ent=tool)
    return world


def generate(params: StoryParams) -> StorySample:
    if params.item not in ITEMS or params.hazard not in HAZARDS or params.tool not in TOOLS:
        raise StoryError("Invalid registry key in StoryParams.")
    item_cfg = ITEMS[params.item]
    hazard_cfg = HAZARDS[params.hazard]
    tool_cfg = TOOLS[params.tool]
    if item_cfg.region != "cart" and hazard_cfg.id == "tar_spill":
        raise StoryError("(This story needs the tar spill to block the mall path or snack cart.)")
    world = _make_world(params)
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    adult = world.facts["adult"]
    item = world.facts["item_ent"]
    hazard = world.facts["hazard_ent"]
    tool = world.facts["tool_ent"]

    hero.memes["hunger"] += 1
    world.say(f"At the shopping mall, {hero.id} and {helper.id} were helping at a superhero day table near the food court.")
    world.say(f"{hero.id} pressed {hero.pronoun('possessive')} hand to {hero.pronoun('possessive')} stomach. {hero.pronoun().capitalize()} was feeling real hunger, and the smell of warm snacks drifted through the mall.")
    world.para()
    world.say(f"Then a sticky tar spill spread across the floor by the snack cart, and the line had to stop.")
    hazard.meters["sticky"] += 1
    item.meters["blocked"] += 1
    propagate(world, narrate=False)
    world.say(f"{helper.id} narrowed {helper.pronoun('possessive')} eyes. \"That's not just a mess,\" {helper.id} said. \"It's a problem we have to solve safely.\"")
    world.say(f"{hero.id} stood tall. \"I can help,\" {hero.id} said, trying not to let the hunger win over the brave part of {hero.pronoun('possessive')} heart.")
    world.para()
    world.say(f"{helper.id} pointed to {tool.phrase} from the mall kiosk. \"We should use that first,\" {helper.id} said, and {adult.id} nodded because it was the sensible choice.")
    if tool_cfg.power < 2:
        raise StoryError("Chosen tool is too weak for the tar problem.")
    world.say(f"{hero.id} used {tool.phrase} to lift the sticky tar away in careful strokes, while {helper.id} kept the path clear and warned shoppers to stay back.")
    hazard.meters["sticky"] = 0.0
    item.meters["blocked"] = 0.0
    world.say(f"After a few careful minutes, the cart rolled free again.")
    world.para()
    world.say(f"Then the adults handed out food, and the hungry crowd could finally eat.")
    hero.memes["bravery"] += 1
    helper.memes["caution"] += 1
    hero.memes["joy"] += 1
    world.say(f"{hero.id} smiled at the shiny clean floor and the open snack counter. The brave rescue had turned the mall from stuck and hungry into calm and full.")
    world.facts.update(outcome="solved")
    prompts = [
        "Write a superhero story set in a shopping mall where tar causes a problem, hunger matters, and brave kids solve it carefully.",
        f"Tell a child-friendly story about {hero.id} and {helper.id} fixing a tar problem in a mall food court and ending with food for everyone.",
        "Write a story with bravery, caution, and problem solving where a sticky mess blocks hungry shoppers and a clever plan helps.",
    ]
    story_qa = [
        QAItem(question="Why was the hero worried?", answer="The hero was worried because the hunger made the food court feel urgent, and the tar spill had blocked the snack cart. The problem meant people needed help before they could eat."),
        QAItem(question="How did the characters solve the problem?", answer=f"They used {tool.label} carefully, kept people back, and lifted the tar away instead of panicking. That safe plan cleared the path and let the snacks reach the hungry crowd."),
        QAItem(question="What changed by the end?", answer="By the end, the tar was gone, the cart could move, and the shoppers could eat again. The mall felt calm instead of stuck."),
    ]
    world_qa = [
        QAItem(question="What is tar?", answer="Tar is a thick sticky black goo. It can make a floor slippery and messy, so people need to clean it carefully."),
        QAItem(question="What does hunger mean?", answer="Hunger means your body wants food. It can make you feel weak, impatient, or eager to get to a meal."),
        QAItem(question="What is bravery?", answer="Bravery means doing the right thing even when you feel nervous. A brave person can still be careful and ask for help."),
    ]
    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


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


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for k in ITEMS:
        lines.append(asp.fact("item", k))
    for k, h in HAZARDS.items():
        lines.append(asp.fact("hazard", k))
        if h.sticky:
            lines.append(asp.fact("sticky", k))
    for k, t in TOOLS.items():
        lines.append(asp.fact("tool", k))
        lines.append(asp.fact("sense", k, t.sense))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


ASP_RULES = r"""
sensible(T) :- tool(T), sense(T,S), sense_min(M), S >= M.
valid(mall, H, I) :- hazard(H), item(I), sticky(H).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(t for (t,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP valid combos differ from Python.")
        rc = 1
    else:
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    if set(asp_sensible()) != {t.id for t in sensible_tools()}:
        print("MISMATCH: ASP sensible tools differ from Python.")
        rc = 1
    else:
        print("OK: ASP sensible tools match.")
    try:
        sample = generate(resolve_params(argparse.Namespace(hero=None, helper=None, adult=None, item=None, hazard=None, tool=None), random.Random(777)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        print(f"FAIL: generate smoke test crashed: {exc}")
        rc = 1
    return rc


HERO_NAMES = ["Nova", "Comet", "Sky", "Ace", "Spark", "Mika"]
HELPER_NAMES = ["Ivy", "Pip", "Juno", "Rae", "Tess"]
ADULT_NAMES = ["Aunt Mira", "Uncle Ben", "Captain Lane", "Ms. Vale"]
HERO_GENDERS = {"Nova": "girl", "Comet": "boy", "Sky": "girl", "Ace": "boy", "Spark": "boy", "Mika": "girl"}
HELPER_GENDERS = {"Ivy": "girl", "Pip": "boy", "Juno": "girl", "Rae": "girl", "Tess": "girl"}
ADULT_GENDERS = {"Aunt Mira": "mother", "Uncle Ben": "father", "Captain Lane": "father", "Ms. Vale": "mother"}

ITEMS = {
    "snack_cart": ShopItem(id="snack_cart", label="snack cart", phrase="the snack cart", region="cart", edible=False, tags={"food"}),
    "pretzel_bag": ShopItem(id="pretzel_bag", label="pretzel bag", phrase="the warm pretzels", region="cart", edible=True, tags={"food"}),
    "bench_path": ShopItem(id="bench_path", label="bench path", phrase="the path by the bench", region="path", tags={"mall"}),
}
HAZARDS = {
    "tar_spill": Hazard(id="tar_spill", label="tar spill", phrase="a sticky tar spill", sticky=True, blocks=True, tags={"tar"}),
    "goo_puddle": Hazard(id="goo_puddle", label="goo puddle", phrase="a sticky goo puddle", sticky=True, blocks=True, tags={"goo"}),
}
TOOLS = {
    "scraper": Tool(id="scraper", label="scraper", phrase="a flat scraper", power=3, sense=3, tags={"problem_solving"}),
    "sand": Tool(id="sand", label="sand bags", phrase="sand bags for the edges", power=2, sense=2, tags={"problem_solving"}),
    "towel": Tool(id="towel", label="towel", phrase="a tiny towel", power=1, sense=1, tags={"weak"}),
}

CURATED = [
    StoryParams(hero="Nova", hero_gender="girl", helper="Ivy", helper_gender="girl", adult="Aunt Mira", adult_gender="mother", item="snack_cart", hazard="tar_spill", tool="scraper"),
    StoryParams(hero="Ace", hero_gender="boy", helper="Pip", helper_gender="boy", adult="Captain Lane", adult_gender="father", item="pretzel_bag", hazard="tar_spill", tool="sand"),
]


def sensible_only() -> list[Tool]:
    return [t for t in TOOLS.values() if t.sense >= 2]


def generate_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a superhero story in a shopping mall where tar makes a problem and bravery helps solve it.",
        f"Tell a story about {f['hero'].id}, {f['helper'].id}, and {f['adult'].id} fixing a tar mess in a mall food court with a smart tool.",
        "Write a child-friendly cautionary story that ends with hungry people getting food again after a careful rescue.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, helper, adult = f["hero"], f["helper"], f["adult"]
    return [
        ("Why did the hero act bravely?",
         "The hero acted bravely because the mall problem had stopped the food line, and hungry people needed help. Bravery helped the hero move toward the problem instead of backing away."),
        ("Why was the helper cautious?",
         "The helper was cautious because sticky tar can make a floor dangerous, so rushing would not help. Being careful made the rescue safer for everyone nearby."),
        ("How did problem solving help?",
         "Problem solving gave them a sensible plan with the right tool and the right steps. That plan cleared the tar without making the problem worse."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a shopping mall?",
         "A shopping mall is a big building with many stores and places to eat. People go there to shop, walk around, and meet friends."),
        ("Why can tar be a problem?",
         "Tar is sticky and hard to clean. If it gets on the floor, people can slip or get stuck."),
        ("What is a cautious choice?",
         "A cautious choice is a careful choice that tries to prevent harm. It can still be brave because it helps keep everyone safe."),
    ]


def valid_tool_ids() -> list[str]:
    return [t.id for t in sensible_tools()]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible tools: {', '.join(asp_sensible())}")
        print(f"{len(asp_valid_combos())} compatible combos")
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

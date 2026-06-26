#!/usr/bin/env python3
"""
storyworlds/worlds/deepseek_v4_flash_service_waylay_problem_solving_nursery_rhyme.py
=====================================================================================

A standalone story-world sketch for a tiny nursery-rhyme domain about
a little traveler who gets waylaid and must solve a problem to continue.

Initial story (used to build a world model):
---
Little Nellie Nye went walking down the lane,
A basket full of berries for her granny in the rain.
But crossing by the old stone bridge, a rickety old thing,
A plank gave way and down she fell with such a terrible sting!

Her berries spilled, her apron ripped, the basket hit the ground.
Poor Nellie sat and wiped her tears without a single sound.
A robin in the hawthorn sang, "Tut tut, don't you cry!
The path ahead is winding but the sun is in the sky."

She picked the berries one by one and mended with a thread
From Granny's sewing needle that she carried in her head.
"A problem is a puzzle, and a puzzle wants a key.
I'll fix the bridge with fallen twigs and cross the stream, you'll see!"

The robin brought a ribbon, and a snail lent sticky goo,
The bridge was patched and sturdy, and the rain began to woo.
Nellie crossed with careful steps, the berries safe and sound,
And Granny at the cottage door said, "Clever girl I've found!"

Causal state updates:
---
    waylaid (fell)         -> actor.health -= 1, actor.sadness += 1
    solve problem step     -> actor.cleverness += 1, actor.hope += 1
    use found item         -> item.consumed = True, actor.inventory -= 1
    help from friend       -> friend.kindness += 1, actor.gratitude += 1
    reach destination      -> actor.relief += 1, all sadness -> 0
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    consumable: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "granny", "maiden"}
        male = {"boy", "grandad", "lad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"granny": "granny", "grandad": "grandad"}.get(self.type, self.type)


@dataclass
class Setting:
    place: str = "the lane"
    obstacle: str = "a rickety bridge"
    affords: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    name: str
    verb: str
    injury: str
    fix_method: str
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Load:
    label: str
    phrase: str
    type: str
    plural: bool = False


@dataclass
class Helper:
    id: str
    label: str
    gift: str
    gift_phrase: str
    plural: bool = False


@dataclass
class Tool:
    id: str
    label: str
    purpose: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_waylay(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["waylaid"] >= THRESHOLD and actor.memes["sadness"] < THRESHOLD:
            sig = ("waylay_sad", actor.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.memes["sadness"] += 1
            out.append(f"{actor.pronoun('possessive').capitalize()} heart felt heavy as a stone.")
    return out


def _r_solve(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["solving"] >= THRESHOLD and actor.memes["hope"] < THRESHOLD:
            sig = ("solve_hope", actor.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.memes["hope"] += 1
            out.append("A spark of clever thinking lit up the gloom.")
    return out


def _r_arrive(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["arrived"] >= THRESHOLD and actor.memes["relief"] < THRESHOLD:
            sig = ("arrive_relief", actor.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.memes["relief"] += 1
            actor.memes["sadness"] = 0.0
            out.append("All the trouble melted like morning dew.")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="waylay", tag="emotional", apply=_r_waylay),
    Rule(name="solve", tag="emotional", apply=_r_solve),
    Rule(name="arrive", tag="emotional", apply=_r_arrive),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "")
    desc = f"little {trait} {hero.type}".strip()
    world.say(f"{hero.id} was a {desc} who walked the winding lane.")


def sets_out(world: World, hero: Entity, load: Load, setting: Setting) -> None:
    world.say(
        f"{hero.pronoun().capitalize()} carried {load.phrase} "
        f"in a basket on {hero.pronoun('possessive')} arm, "
        f"along {setting.place} where the hedgerows grew so warm."
    )


def encounters_obstacle(world: World, hero: Entity, obstacle: Obstacle) -> None:
    hero.meters["waylaid"] += 1
    world.say(
        f"But {obstacle.name} stood in {hero.pronoun('possessive')} way, "
        f"{obstacle.verb} and worn and old."
    )
    world.say(
        f"Before {hero.pronoun()} knew, the {obstacle.name} gave way, "
        f"and {hero.pronoun()} felt {obstacle.injury} and cold."
    )
    propagate(world)


def cries_and_rests(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.pronoun().capitalize()} sat upon a mossy bank and let a tear-drop fall."
    )
    world.say("The berries lay all scattered, and the basket cracked its wall.")


def helper_arrives(world: World, hero: Entity, helper: Helper) -> None:
    helper_ent = world.add(Entity(
        id=helper.id, kind="character", type=helper.label,
        label=helper.label,
    ))
    helper_ent.memes["kindness"] += 1
    world.facts["helper"] = helper_ent
    world.say(
        f"A {helper.label} came hopping near, a friendly little sight, "
        f"and chirped, 'Don't worry, little one, I'll help you set things right!'"
    )
    world.say(
        f"The {helper.label} brought a {helper.gift} {helper.gift_phrase} "
        f"and laid it at {hero.pronoun('possessive')} feet."
    )


def thinks_and_solves(world: World, hero: Entity, tool: Tool) -> None:
    tool_ent = world.add(Entity(
        id=tool.id, type="tool", label=tool.label,
        carried_by=hero.id, consumable=True,
    ))
    world.facts["tool"] = tool_ent
    hero.memes["solving"] += 1
    world.say(
        f"{hero.pronoun().capitalize()} dried {hero.pronoun('possessive')} eyes and thought, "
        f"'A problem wants a key!'"
    )
    world.say(
        f"{hero.pronoun().capitalize()} found a {tool.label} lying near and "
        f"used it cleverly."
    )
    tool_ent.meters["consumed"] += 1
    propagate(world)


def mends_and_fixes(world: World, hero: Entity, obstacle: Obstacle) -> None:
    hero.memes["solving"] += 1
    world.say(
        f"{hero.pronoun().capitalize()} patched the {obstacle.name} with the gifts "
        f"and sturdy {world.facts.get('tool', Entity(id='x', label='twig')).label} too."
    )
    world.say("The bridge was strong and steady now, the path no longer blue.")
    propagate(world)


def crosses_and_arrives(world: World, hero: Entity, load: Load, destination: str) -> None:
    hero.meters["arrived"] += 1
    world.say(
        f"{hero.pronoun().capitalize()} crossed with {hero.pronoun('possessive')} basket safe, "
        f"the berries snug and neat."
    )
    world.say(
        f"At {destination}, a warm embrace and a kiss upon the cheek."
    )
    propagate(world)


def grandma_says(world: World, hero: Entity) -> None:
    world.say(
        f"'{hero.id}, my clever child, you solved the problem well! "
        f"The waylay in the lane became a story you can tell.'"
    )


def tell(setting: Setting, obstacle: Obstacle, load_cfg: Load,
         tool_cfg: Tool, helper_cfg: Helper,
         hero_name: str = "Nellie", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None,
         destination: str = "Granny's cottage door") -> World:
    world = World(setting)

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little"] + (hero_traits or ["clever", "brave"]),
    ))
    dest_entity = world.add(Entity(
        id="Destination", kind="thing", type="place",
        label=destination,
    ))
    world.facts["destination"] = destination

    introduce(world, hero)
    sets_out(world, hero, load_cfg, setting)
    world.para()
    encounters_obstacle(world, hero, obstacle)
    world.para()
    cries_and_rests(world, hero)
    helper_arrives(world, hero, helper_cfg)
    world.para()
    thinks_and_solves(world, hero, tool_cfg)
    mends_and_fixes(world, hero, obstacle)
    world.para()
    crosses_and_arrives(world, hero, load_cfg, destination)
    grandma_says(world, hero)

    world.facts.update(
        hero=hero, obstacle=obstacle, load_cfg=load_cfg,
        tool_cfg=tool_cfg, helper_cfg=helper_cfg,
        setting=setting,
    )
    return world


SETTINGS = {
    "lane": Setting(place="the winding lane", obstacle="a rickety bridge", affords={"bridge"}),
    "wood": Setting(place="the shady wood", obstacle="a fallen log", affords={"log"}),
    "field": Setting(place="the open field", obstacle="a muddy ditch", affords={"ditch"}),
    "hill": Setting(place="the steep hill", obstacle="a gushing stream", affords={"stream"}),
}

OBSTACLES = {
    "bridge": Obstacle(
        id="bridge",
        name="rickety bridge",
        verb="creaking",
        injury="a bump and a graze",
        fix_method="patch with twigs and gifts",
        keyword="bridge",
        tags={"bridge", "crossing"},
    ),
    "log": Obstacle(
        id="log",
        name="fallen log",
        verb="rotting",
        injury="a scrape and a tumble",
        fix_method="roll with rope and sticks",
        keyword="log",
        tags={"log", "wood"},
    ),
    "ditch": Obstacle(
        id="ditch",
        name="muddy ditch",
        verb="slippery",
        injury="a splash and a shiver",
        fix_method="fill with stones and leaves",
        keyword="ditch",
        tags={"mud", "ditch"},
    ),
    "stream": Obstacle(
        id="stream",
        name="gushing stream",
        verb="rushing",
        injury="a soak and a fright",
        fix_method="build a raft with reeds",
        keyword="stream",
        tags={"water", "stream"},
    ),
}

LOADS = {
    "berries": Load(
        label="berries",
        phrase="ripe red berries",
        type="berries",
        plural=True,
    ),
    "eggs": Load(
        label="eggs",
        phrase="fresh brown eggs",
        type="eggs",
        plural=True,
    ),
    "flowers": Load(
        label="flowers",
        phrase="pretty wild flowers",
        type="flowers",
        plural=True,
    ),
    "apples": Load(
        label="apples",
        phrase="juicy golden apples",
        type="apples",
        plural=True,
    ),
}

HELPERS = {
    "robin": Helper(
        id="robin",
        label="robin redbreast",
        gift="ribbon",
        gift_phrase="of silken red and blue",
    ),
    "squirrel": Helper(
        id="squirrel",
        label="squirrel",
        gift="acorn",
        gift_phrase="shiny and brown",
    ),
    "rabbit": Helper(
        id="rabbit",
        label="rabbit",
        gift="carrot",
        gift_phrase="long and orange and sweet",
    ),
    "frog": Helper(
        id="frog",
        label="frog",
        gift="lily pad",
        gift_phrase="green and wide and wet",
    ),
}

TOOLS = {
    "twig": Tool(
        id="twig",
        label="sturdy twig",
        purpose="patching",
    ),
    "stone": Tool(
        id="stone",
        label="flat stone",
        purpose="bridging",
    ),
    "reed": Tool(
        id="reed",
        label="tall reed",
        purpose="weaving",
    ),
    "vine": Tool(
        id="vine",
        label="long vine",
        purpose="tying",
    ),
}

GIRL_NAMES = ["Nellie", "Polly", "Molly", "Daisy", "Rosie", "Lily", "Poppy", "Ivy", "Maisie", "Elsie"]
BOY_NAMES = ["Tommy", "Billy", "Charlie", "Freddy", "Sammy", "Teddy", "Archie", "Ollie", "Georgie", "Harry"]
TRAITS = ["clever", "brave", "kind", "merry", "bright", "keen"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for obs_id in setting.affords:
            obs = OBSTACLES[obs_id]
            for load_id in LOADS:
                for tool_id in TOOLS:
                    for helper_id in HELPERS:
                        combos.append((place, obs_id, load_id, tool_id, helper_id))
    return combos


@dataclass
class StoryParams:
    place: str
    obstacle: str
    load: str
    tool: str
    helper: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "bridge": [("What is a bridge for?",
                "A bridge helps you cross over water or a gap so you can keep going on your journey.")],
    "crossing": [("How do you cross a stream safely?",
                  "You look for a bridge or a shallow part, and you step carefully so you do not slip.")],
    "wood": [("What can you find in the woods?",
              "In the woods you can find trees, leaves, sticks, and helpful animals like squirrels.")],
    "mud": [("Why is mud slippery?",
             "Mud is wet dirt that makes the ground soft and slippery, so you must walk slowly.")],
    "water": [("What happens if you fall in a stream?",
               "You get wet and cold, and you might need dry clothes and help to get warm again.")],
    "helping": [("Why is it good to help someone who is stuck?",
                 "Helping makes the other person feel better and solves the problem faster. Friends help each other.")],
    "ribbon": [("What can you do with a ribbon?",
                "A ribbon can tie things together, like patching a broken basket or fixing a bridge.")],
    "twig": [("How can a twig be useful?",
              "A sturdy twig can be used to poke, prop, or patch things that are broken.")],
}
KNOWLEDGE_ORDER = ["bridge", "crossing", "wood", "mud", "water", "helping", "ribbon", "twig"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    kw = f["obstacle"].keyword
    return [
        f'Write a short nursery rhyme about a child who gets waylaid on a journey and solves a problem.',
        f'Tell a gentle story where {hero.id} meets a helpful animal and must fix a broken bridge.',
        f'Write a simple rhyming story that uses the word "{kw}" and ends with a happy arrival.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    sub = hero.pronoun("subject")
    pos = hero.pronoun("possessive")
    ob = f["obstacle"]
    load = f["load_cfg"]
    helper = f["helper_cfg"]
    tool = f["tool_cfg"]
    dest = world.facts.get("destination", "Granny's cottage")
    trait = next((t for t in hero.traits if t != "little"), hero.type)

    qa: list[QAItem] = [
        QAItem(
            question=f"Who went walking with {load.label} for {dest}?",
            answer=f"A little {trait} {hero.type} named {hero.id} carried {load.label} along {world.setting.place}.",
        ),
        QAItem(
            question=f"What happened when {hero.id} reached the {ob.name}?",
            answer=f"The {ob.name} was {ob.verb} and broke, and {hero.id} fell and felt {ob.injury}. The {load.label} scattered.",
        ),
        QAItem(
            question=f"Who helped {hero.id} after the fall?",
            answer=f"A {helper.label} came and gave {hero.id} a {helper.gift} to help fix things.",
        ),
        QAItem(
            question=f"What did {hero.id} use to solve the problem?",
            answer=f"{hero.id.capitalize()} found a {tool.label} and used it with the {helper.gift} to mend the {ob.name}.",
        ),
        QAItem(
            question=f"Did {hero.id} get to {dest} in the end?",
            answer=f"Yes, {sub} crossed the fixed {ob.name} safely and arrived at {dest}, where someone said {pos} name with a smile.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["obstacle"].tags)
    tags.add("helping")
    tags.add("twig")
    tags.add("ribbon")
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="lane", obstacle="bridge", load="berries",
        tool="twig", helper="robin", name="Nellie",
        gender="girl", trait="clever",
    ),
    StoryParams(
        place="wood", obstacle="log", load="eggs",
        tool="vine", helper="squirrel", name="Tommy",
        gender="boy", trait="brave",
    ),
    StoryParams(
        place="field", obstacle="ditch", load="flowers",
        tool="stone", helper="rabbit", name="Polly",
        gender="girl", trait="kind",
    ),
    StoryParams(
        place="hill", obstacle="stream", load="apples",
        tool="reed", helper="frog", name="Billy",
        gender="boy", trait="bright",
    ),
]


def explain_rejection(obstacle: Obstacle, load: Load) -> str:
    return "(No story: this combination does not form a reasonable problem-solving nursery rhyme.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery rhyme world: a child, a waylay, a problem solved. "
                    "Unspecified choices are picked at random (seeded).")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--load", choices=LOADS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None,
                    help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true",
                    help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true",
                    help="check the inline ASP gate matches valid_combos()")
    ap.add_argument("--show-asp", action="store_true",
                    help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    filtered = [c for c in combos
                if (args.place is None or c[0] == args.place)
                and (args.obstacle is None or c[1] == args.obstacle)
                and (args.load is None or c[2] == args.load)
                and (args.tool is None or c[3] == args.tool)
                and (args.helper is None or c[4] == args.helper)]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")

    place, obs_id, load_id, tool_id, helper_id = rng.choice(sorted(filtered))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place, obstacle=obs_id, load=load_id,
        tool=tool_id, helper=helper_id,
        name=name, gender=gender, trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], OBSTACLES[params.obstacle],
                 LOADS[params.load], TOOLS[params.tool],
                 HELPERS[params.helper], params.name, params.gender,
                 [params.trait, "brave"])
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
affords(P, O) :- setting(P), obstacle(O), place_of_obstacle(P, O).
valid(Place, O, L, T, H) :- affords(Place, O), load(L), tool(T), helper(H).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for oid in OBSTACLES:
        lines.append(asp.fact("obstacle", oid))
    for lid in LOADS:
        lines.append(asp.fact("load", lid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, obstacle, load, tool, helper) combos:\n")
        for t in triples:
            print(f"  {t[0]:9} {t[1]:8} {t[2]:8} {t[3]:8} {t[4]:8}")
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
            header = f"### {p.name}: {p.obstacle} at {p.place} (load: {p.load})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

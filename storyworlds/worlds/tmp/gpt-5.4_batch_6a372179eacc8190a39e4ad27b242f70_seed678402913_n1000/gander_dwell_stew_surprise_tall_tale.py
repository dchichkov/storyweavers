#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/gander_dwell_stew_surprise_tall_tale.py
==================================================================

A standalone story world for a tiny tall-tale domain: a child cooks an enormous
pot of stew for hungry neighbors, but the road to the feast is blocked by rough
ground. A giant gander, famous for where he does dwell, appears as a surprise
helper and gets the stew where it needs to go.

The reasonableness gate is simple and strict:
- each place affords only certain obstacles
- each hauling tool can handle only certain obstacles

So the world refuses mismatched stories like taking a sled through mud or a
wagon straight across a creek.

Run it
------
python storyworlds/worlds/gpt-5.4/gander_dwell_stew_surprise_tall_tale.py
python storyworlds/worlds/gpt-5.4/gander_dwell_stew_surprise_tall_tale.py --place marsh --obstacle creek --tool raft
python storyworlds/worlds/gpt-5.4/gander_dwell_stew_surprise_tall_tale.py --obstacle snow --tool wagon
python storyworlds/worlds/gpt-5.4/gander_dwell_stew_surprise_tall_tale.py --all
python storyworlds/worlds/gpt-5.4/gander_dwell_stew_surprise_tall_tale.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/gander_dwell_stew_surprise_tall_tale.py --verify
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
    role: str = ""
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
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    scene: str
    dwelling: str
    crowd: str
    affords: set[str] = field(default_factory=set)
    boast: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Stew:
    id: str
    label: str
    aroma: str
    color: str
    ingredient: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    trouble: str
    struggle: str
    gander_help: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    handles: set[str] = field(default_factory=set)
    roll_text: str = ""
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
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


def place_supports(place: Place, obstacle: Obstacle) -> bool:
    return obstacle.id in place.affords


def tool_fits(tool: Tool, obstacle: Obstacle) -> bool:
    return obstacle.id in tool.handles


def valid_combo(place: Place, obstacle: Obstacle, tool: Tool) -> bool:
    return place_supports(place, obstacle) and tool_fits(tool, obstacle)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for obstacle_id, obstacle in OBSTACLES.items():
            for tool_id, tool in TOOLS.items():
                if valid_combo(place, obstacle, tool):
                    combos.append((place_id, obstacle_id, tool_id))
    return sorted(combos)


def explain_rejection(place: Place, obstacle: Obstacle, tool: Tool) -> str:
    if not place_supports(place, obstacle):
        return (
            f"(No story: {place.label.capitalize()} does not fit a {obstacle.label} trip in this world. "
            f"Pick an obstacle the place can really have.)"
        )
    return (
        f"(No story: {tool.label.capitalize()} cannot sensibly carry a giant stew through {obstacle.label}. "
        f"Choose a tool that matches the ground.)"
    )


def introduce(world: World, hero: Entity, place: Place, stew: Stew) -> None:
    hero.memes["pride"] += 1
    world.say(
        f"In {place.label}, where {place.scene}, {hero.id} set out to cook a kettle of {stew.label} "
        f"so big that the spoon looked like an oar and the steam could have fogged three barns."
    )
    world.say(
        f"The {stew.label} bubbled {stew.color} and rich, smelling of {stew.aroma}, "
        f"and {hero.id} promised there would be enough for every one of the {place.crowd} and then some."
    )
    if place.boast:
        world.say(place.boast)


def rumor(world: World, place: Place) -> None:
    world.say(
        f"Folks in {place.label} liked to whisper that a giant gander did dwell {place.dwelling}, "
        f"but most days they treated that tale like moonshine talk."
    )


def load_stew(world: World, hero: Entity, tool: Tool) -> None:
    world.say(
        f"At supper time {hero.id} heaved the kettle onto {tool.phrase}. "
        f"The load made the boards groan, yet {hero.pronoun()} grinned and started for the feast."
    )
    world.get("kettle").meters["loaded"] += 1
    world.get("tool").meters["burden"] += 1


def hit_trouble(world: World, hero: Entity, obstacle: Obstacle, tool: Tool) -> None:
    hero.memes["worry"] += 1
    world.get("road").meters["blocked"] += 1
    world.say(
        f"Then the road gave {hero.pronoun('object')} trouble. {obstacle.trouble} "
        f"{obstacle.struggle} and even {tool.label} began to complain."
    )
    world.say(
        f"If the kettle tipped, the whole supper would turn from stew into a sad, smoky puddle."
    )


def struggle(world: World, hero: Entity, tool: Tool) -> None:
    hero.meters["strain"] += 1
    world.say(
        f"{hero.id} leaned hard on {tool.label}. {tool.roll_text} Still, the great kettle barely budged, "
        f"and for one long minute {hero.pronoun()} did not know how supper would ever arrive."
    )


def surprise_gander(world: World, hero: Entity, place: Place, obstacle: Obstacle) -> None:
    gander = world.get("gander")
    gander.memes["surprise"] += 1
    hero.memes["amazement"] += 1
    world.say(
        f"Then came the surprise. Out of the place where the giant gander did dwell {place.dwelling}, "
        f"there strode a white bird taller than a gate and broader than a quilt on a wash line."
    )
    world.say(
        f'The gander gave one grand honk, dipped {gander.pronoun("possessive")} head at the wobbling kettle, '
        f"and {obstacle.gander_help}."
    )


def rescue(world: World, hero: Entity, obstacle: Obstacle, tool: Tool) -> None:
    world.get("road").meters["blocked"] = 0.0
    world.get("tool").meters["moving"] += 1
    world.get("kettle").meters["safe"] += 1
    hero.memes["relief"] += 1
    hero.memes["gratitude"] += 1
    world.say(
        f"After that, {tool.label} moved as easy as a leaf on a current. "
        f"The kettle stayed level, the stew stayed hot, and the hard part of the road lost its bragging rights."
    )
    world.say(
        f"By the time {hero.id} reached the feast, not a spoonful had been lost."
    )


def feast(world: World, hero: Entity, place: Place, stew: Stew, obstacle: Obstacle) -> None:
    hero.memes["joy"] += 1
    world.get("crowd").memes["satisfaction"] += 1
    world.say(
        f"The {place.crowd} lined up with bowls in both hands. They took one gander at the kettle, "
        f"laughed at the size of it, and ate until even the stars seemed sleepy."
    )
    world.say(
        f"{hero.id} saved the last shining ladle for the giant bird, and the gander swallowed it with a pleased blink. "
        f"{obstacle.ending}"
    )
    world.say(
        f"Ever since then, when a job in {place.label} looks too big, people say, "
        f'"Do not stew over it. Leave room for surprise."'
    )


def tell(
    place: Place,
    stew: Stew,
    obstacle: Obstacle,
    tool: Tool,
    hero_name: str,
    hero_gender: str,
) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    gander = world.add(Entity(id="Gander", kind="character", type="bird", label="the giant gander", role="helper"))
    kettle = world.add(Entity(id="kettle", type="pot", label="the kettle"))
    haul = world.add(Entity(id="tool", type="tool", label=tool.label))
    road = world.add(Entity(id="road", type="path", label="the road"))
    crowd = world.add(Entity(id="crowd", type="crowd", label=place.crowd))

    introduce(world, hero, place, stew)
    rumor(world, place)

    world.para()
    load_stew(world, hero, tool)
    hit_trouble(world, hero, obstacle, tool)
    struggle(world, hero, tool)

    world.para()
    surprise_gander(world, hero, place, obstacle)
    rescue(world, hero, obstacle, tool)

    world.para()
    feast(world, hero, place, stew, obstacle)

    world.facts.update(
        hero=hero,
        gander=gander,
        kettle=kettle,
        crowd=crowd,
        place=place,
        stew=stew,
        obstacle=obstacle,
        tool=tool,
        arrived=kettle.meters["safe"] >= THRESHOLD,
        surprised=hero.memes["amazement"] >= THRESHOLD,
    )
    return world


PLACES = {
    "prairie": Place(
        id="prairie",
        label="the prairie",
        scene="the wind combed the grass in green waves clear to the horizon",
        dwelling="in a willow pocket by the creek bend",
        crowd="hay hands",
        affords={"mud", "creek"},
        boast="Some said the kettle was so wide that two calves once took shade beside it.",
        tags={"prairie"},
    ),
    "marsh": Place(
        id="marsh",
        label="the marsh",
        scene="the reeds rattled like dry fiddles and the water flashed between them",
        dwelling="among the cattails behind the broad blue water",
        crowd="reed cutters",
        affords={"mud", "creek"},
        boast="People swore the bubbles from that pot could scare fog clean off the water.",
        tags={"marsh"},
    ),
    "mountain": Place(
        id="mountain",
        label="the mountain hollow",
        scene="the pines stood straight as spears and the echo answered every clank twice",
        dwelling="under a shelf of stone above the old switchback",
        crowd="timber families",
        affords={"snow", "creek"},
        boast="Old folks claimed the stew pot had once been mistaken for a silver mine from far away.",
        tags={"mountain"},
    ),
}

STEWS = {
    "bean": Stew(
        id="bean",
        label="bean stew",
        aroma="beans, onions, and pepper",
        color="brown",
        ingredient="beans",
        tags={"beans", "stew"},
    ),
    "pumpkin": Stew(
        id="pumpkin",
        label="pumpkin stew",
        aroma="pumpkin, sage, and sweet cream",
        color="golden",
        ingredient="pumpkin",
        tags={"pumpkin", "stew"},
    ),
    "beef": Stew(
        id="beef",
        label="beef stew",
        aroma="beef, carrots, and rosemary",
        color="deep brown",
        ingredient="beef",
        tags={"beef", "stew"},
    ),
}

OBSTACLES = {
    "mud": Obstacle(
        id="mud",
        label="mud",
        trouble="A belt of spring mud lay ahead, thick enough to steal boots",
        struggle="clung to every inch of the trail",
        gander_help="set its huge feet in the muck and pulled from the front with such steady force that the trail let go",
        ending="Then it strutted back toward the reeds, leaving tracks that filled with clean water and reflected the moon.",
        tags={"mud"},
    ),
    "snow": Obstacle(
        id="snow",
        label="snow",
        trouble="A drift of late snow blocked the pass, bright and deep as spilled flour",
        struggle="rose in a white hump across the path",
        gander_help="spread its mighty wings and shoved a tailwind behind the load until the runners sang over the crust",
        ending="Then it climbed the ridge in three flapping bounds and vanished into the shining dusk.",
        tags={"snow"},
    ),
    "creek": Obstacle(
        id="creek",
        label="a creek crossing",
        trouble="The creek had climbed its banks and cut the path in two",
        struggle="splashed and swirled where the crossing ought to have been",
        gander_help="slid into the water, took the tow rope in its bill, and ferried the supper across as neat as a boatman",
        ending="Then it drifted downstream like a proud little ship, honking once at the moon.",
        tags={"creek"},
    ),
}

TOOLS = {
    "wagon": Tool(
        id="wagon",
        label="wagon",
        phrase="a broad farm wagon",
        handles={"mud"},
        roll_text="The wheels threw clods the size of loaves.",
        tags={"wagon"},
    ),
    "sled": Tool(
        id="sled",
        label="sled",
        phrase="a long hickory sled",
        handles={"snow"},
        roll_text="The runners hissed and skittered under the weight.",
        tags={"sled"},
    ),
    "raft": Tool(
        id="raft",
        label="raft",
        phrase="a plank raft with a rope line",
        handles={"creek"},
        roll_text="The planks bobbed and knocked together like teeth in winter.",
        tags={"raft"},
    ),
}


@dataclass
class StoryParams:
    place: str
    stew: str
    obstacle: str
    tool: str
    name: str
    gender: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="prairie",
        stew="bean",
        obstacle="mud",
        tool="wagon",
        name="June",
        gender="girl",
    ),
    StoryParams(
        place="mountain",
        stew="pumpkin",
        obstacle="snow",
        tool="sled",
        name="Eli",
        gender="boy",
    ),
    StoryParams(
        place="marsh",
        stew="beef",
        obstacle="creek",
        tool="raft",
        name="Mara",
        gender="girl",
    ),
]

GIRL_NAMES = ["June", "Mara", "Tess", "Lula", "Ada", "Nell"]
BOY_NAMES = ["Eli", "Beau", "Finn", "Cal", "Otis", "Jude"]

KNOWLEDGE = {
    "stew": [
        (
            "What is stew?",
            "Stew is a hot meal cooked slowly in one pot with broth, vegetables, and other food mixed together. It stays warm and feeds many people."
        )
    ],
    "gander": [
        (
            "What is a gander?",
            "A gander is a male goose. Geese are big birds with strong necks, webbed feet, and loud honks."
        )
    ],
    "mud": [
        (
            "Why is mud hard for wheels?",
            "Mud is wet, sticky ground, so wheels can sink and get grabbed by it. That makes heavy loads hard to pull."
        )
    ],
    "snow": [
        (
            "Why can a sled slide on snow?",
            "A sled has smooth runners instead of wheels. On packed snow, those runners can glide much more easily."
        )
    ],
    "creek": [
        (
            "What is a creek?",
            "A creek is a small stream of flowing water. If it rises high enough, it can cover a path and make crossing hard."
        )
    ],
    "wagon": [
        (
            "What is a wagon for?",
            "A wagon carries heavy things on wheels. It works best on ground that a wheel can still roll through."
        )
    ],
    "sled": [
        (
            "What is a sled for?",
            "A sled is used to pull things over snow or ice. Its runners slide where wheels would get stuck."
        )
    ],
    "raft": [
        (
            "What does a raft do?",
            "A raft floats on water and carries things across. It is useful when the problem is a water crossing instead of rough land."
        )
    ],
}
KNOWLEDGE_ORDER = ["stew", "gander", "mud", "snow", "creek", "wagon", "sled", "raft"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    place = f["place"]
    stew = f["stew"]
    obstacle = f["obstacle"]
    tool = f["tool"]
    return [
        f'Write a short tall tale for a 3-to-5-year-old that includes the words "gander", "dwell", and "stew".',
        f"Tell a tall tale where {hero.id} cooks a huge pot of {stew.label} in {place.label}, gets stopped by {obstacle.label}, and then a giant gander appears as a surprise helper.",
        f"Write a child-facing story about hauling supper with a {tool.label}, where the ending image proves the stew reached a hungry crowd."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    place = f["place"]
    stew = f["stew"]
    obstacle = f["obstacle"]
    tool = f["tool"]
    crowd = f["crowd"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, who cooked a giant kettle of {stew.label}, and a huge gander who came to help. The story also includes the hungry {crowd.label} waiting for supper."
        ),
        (
            f"What was {hero.id} trying to do?",
            f"{hero.id} was trying to haul a great kettle of {stew.label} to the feast. The stew was meant for the {place.crowd}, so getting it there mattered."
        ),
        (
            f"What problem stopped {hero.id} on the way?",
            f"{obstacle.trouble}. That was a problem because the kettle was so heavy that one bad jolt could spill the supper."
        ),
        (
            "Why was the gander a surprise?",
            f"The giant gander was a surprise because people only whispered that one did dwell {place.dwelling}. Then it suddenly stepped out and proved the old tale true."
        ),
        (
            "How did the giant gander help?",
            f"The gander helped with the {tool.label} when the road turned hard. {obstacle.gander_help.capitalize()}, so the kettle stayed level and the stew stayed safe."
        ),
        (
            "How did the story end?",
            f"The {place.crowd} got their hot {stew.label}, and even the giant gander got a last ladle. The ending proves the hard trip changed from worry to a full, happy feast."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"stew", "gander", f["obstacle"].id, f["tool"].id}
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits: list[str] = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
ok_place(P, O) :- place(P), obstacle(O), affords(P, O).
ok_tool(T, O)  :- tool(T), obstacle(O), handles(T, O).
valid(P, O, T) :- ok_place(P, O), ok_tool(T, O).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for obstacle_id in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, obstacle_id))
    for obstacle_id in OBSTACLES:
        lines.append(asp.fact("obstacle", obstacle_id))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        for obstacle_id in sorted(tool.handles):
            lines.append(asp.fact("handles", tool_id, obstacle_id))
    for stew_id in STEWS:
        lines.append(asp.fact("stew", stew_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
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

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("Smoke test generated an empty story.")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:  # pragma: no cover - explicit verify guard
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale story world: giant stew, hard road, surprise gander helper."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--stew", choices=STEWS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story triples derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.obstacle and args.tool:
        place = PLACES[args.place]
        obstacle = OBSTACLES[args.obstacle]
        tool = TOOLS[args.tool]
        if not valid_combo(place, obstacle, tool):
            raise StoryError(explain_rejection(place, obstacle, tool))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, obstacle_id, tool_id = rng.choice(combos)
    stew_id = args.stew or rng.choice(sorted(STEWS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(name_pool)
    return StoryParams(
        place=place_id,
        stew=stew_id,
        obstacle=obstacle_id,
        tool=tool_id,
        name=name,
        gender=gender,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        stew = STEWS[params.stew]
        obstacle = OBSTACLES[params.obstacle]
        tool = TOOLS[params.tool]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter value: {err})") from err

    if not valid_combo(place, obstacle, tool):
        raise StoryError(explain_rejection(place, obstacle, tool))

    world = tell(
        place=place,
        stew=stew,
        obstacle=obstacle,
        tool=tool,
        hero_name=params.name,
        hero_gender=params.gender,
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, obstacle, tool) combos:\n")
        for place, obstacle, tool in combos:
            print(f"  {place:9} {obstacle:8} {tool}")
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.stew} in {p.place} with {p.tool} past {p.obstacle}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

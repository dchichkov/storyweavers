#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/jumble_ancestor_boulder_friendship_superhero_story.py
=================================================================================

A standalone story world for a tiny superhero-style friendship tale.

Premise
-------
Two friends wearing homemade superhero capes arrive at a local heritage place
for a community celebration. After a windy night, a jumble of branches, boxes,
or banners lies around the path, and a boulder blocks the way to an ancestor
landmark. One child first dreams of solving the problem alone for glory, but the
world pushes back: some boulders are too heavy. The story turns when the friends
work together with a sensible method, clear the path, and discover that the most
heroic power is friendship.

Run it
------
python storyworlds/worlds/gpt-5.4/jumble_ancestor_boulder_friendship_superhero_story.py
python storyworlds/worlds/gpt-5.4/jumble_ancestor_boulder_friendship_superhero_story.py --place ancestor_oak --boulder medium --tool branch_lever
python storyworlds/worlds/gpt-5.4/jumble_ancestor_boulder_friendship_superhero_story.py --tool kick
python storyworlds/worlds/gpt-5.4/jumble_ancestor_boulder_friendship_superhero_story.py --all
python storyworlds/worlds/gpt-5.4/jumble_ancestor_boulder_friendship_superhero_story.py --qa --json
"""

from __future__ import annotations

import argparse
import contextlib
import io
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
SENSE_MIN = 2


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"          # character | thing
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    movable: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
@dataclass
class Place:
    id: str
    label: str
    festival: str
    ancestor_site: str
    scene: str
    jumble: str
    extra_tools: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class BoulderCfg:
    id: str
    label: str
    need: int
    color: str
    size_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ToolCfg:
    id: str
    label: str
    phrase: str
    power: int
    sense: int
    teamwork: bool
    use_line: str
    qa_line: str
    tags: set[str] = field(default_factory=set)


PLACES = {
    "ancestor_oak": Place(
        "ancestor_oak",
        "the hill path",
        "Ancestor Day",
        "the old ancestor oak at the top of the hill",
        "The path curled uphill like the road to a secret headquarters.",
        "a jumble of twigs, paper stars, and tipped picnic boxes",
        extra_tools={"branch_lever"},
        tags={"ancestor", "tree"},
    ),
    "ancestor_mural": Place(
        "ancestor_mural",
        "the museum yard",
        "Hero History Morning",
        "the bright wall painting of the town's first ancestor family",
        "The museum yard gleamed with painted shields and strings of ribbon.",
        "a jumble of fallen banner poles, ribbons, and empty crates",
        extra_tools={"wagon_rope"},
        tags={"ancestor", "museum"},
    ),
    "ancestor_bridge": Place(
        "ancestor_bridge",
        "the creek path",
        "Bridge Brightening Day",
        "the little stone bridge built by an ancestor long ago",
        "The creek flashed in the sun under the small stone arch.",
        "a jumble of leaves, lantern sticks, and rolled-up bunting",
        extra_tools={"branch_lever", "wagon_rope"},
        tags={"ancestor", "bridge"},
    ),
}

BOULDERS = {
    "small": BoulderCfg(
        "small", "small boulder", 2, "speckled gray",
        "It was round as a giant loaf of bread and just heavy enough to matter.",
        tags={"boulder"},
    ),
    "medium": BoulderCfg(
        "medium", "medium boulder", 3, "mossy brown",
        "It sat in the middle of the path like a grumpy stone monster.",
        tags={"boulder"},
    ),
    "large": BoulderCfg(
        "large", "large boulder", 4, "dark granite",
        "It was as wide as a wheelbarrow and looked much too proud to budge.",
        tags={"boulder"},
    ),
}

TOOLS = {
    "hands": ToolCfg(
        "hands", "hands", "their own hands", 2, 2, True,
        "planted their sneakers, counted to three, and pushed shoulder to shoulder",
        "used their own hands and pushed together",
        tags={"friendship", "teamwork"},
    ),
    "branch_lever": ToolCfg(
        "branch_lever", "branch lever", "a long fallen branch as a lever", 3, 3, True,
        "slid a long branch under the stone and leaned on it together",
        "used a long branch like a lever and leaned together",
        tags={"lever", "teamwork"},
    ),
    "wagon_rope": ToolCfg(
        "wagon_rope", "wagon rope", "a parade rope tied to a little wagon", 4, 3, True,
        "looped a rope around the boulder, braced the wagon, and hauled in one steady pull",
        "looped a rope around the boulder and hauled together with the wagon",
        tags={"rope", "teamwork"},
    ),
    "kick": ToolCfg(
        "kick", "kick", "a flying kick", 1, 1, False,
        "tried a dramatic kick",
        "tried to kick the boulder",
        tags={"bad_idea"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Max", "Ben", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo", "Owen"]
TRAITS = ["showy", "steady", "quick", "careful", "bright", "brave"]
CAPE_STYLES = {
    "lightning": ("Captain Comet", "Bolt Buddy"),
    "sky": ("Star Shield", "Cloud Flash"),
    "forest": ("Leaf Guardian", "Moss Meteor"),
}


# ---------------------------------------------------------------------------
# World and rules
# ---------------------------------------------------------------------------
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


def propagate(world: World) -> None:
    path = world.get("path")
    crowd = world.get("crowd")
    boulder = world.get("boulder")
    hero = world.get("hero")
    friend = world.get("friend")

    if path.meters["blocked"] >= THRESHOLD and ("blocked",) not in world.fired:
        world.fired.add(("blocked",))
        crowd.memes["worry"] += 1
        hero.memes["urgency"] += 1
        friend.memes["urgency"] += 1

    if hero.memes["solo_fail"] >= THRESHOLD and ("solo_fail",) not in world.fired:
        world.fired.add(("solo_fail",))
        hero.memes["humility"] += 1
        friend.memes["care"] += 1

    if boulder.meters["moved"] >= THRESHOLD and ("cleared",) not in world.fired:
        world.fired.add(("cleared",))
        path.meters["blocked"] = 0.0
        crowd.memes["relief"] += 1
        hero.memes["joy"] += 1
        friend.memes["joy"] += 1
        hero.memes["friendship"] += 1
        friend.memes["friendship"] += 1


# ---------------------------------------------------------------------------
# Constraint helpers
# ---------------------------------------------------------------------------
def place_allows(place: Place, tool: ToolCfg) -> bool:
    if tool.id == "hands":
        return True
    return tool.id in place.extra_tools


def valid_combo(place: Place, boulder: BoulderCfg, tool: ToolCfg) -> bool:
    return tool.sense >= SENSE_MIN and place_allows(place, tool) and tool.power >= boulder.need


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for pid, place in PLACES.items():
        for bid, boulder in BOULDERS.items():
            for tid, tool in TOOLS.items():
                if valid_combo(place, boulder, tool):
                    out.append((pid, bid, tid))
    return out


def explain_rejection(place: Place, boulder: BoulderCfg, tool: ToolCfg) -> str:
    if tool.sense < SENSE_MIN:
        return (f"(No story: '{tool.id}' is too silly for this world. "
                f"A superhero story here still needs a sensible plan.)")
    if not place_allows(place, tool):
        return (f"(No story: {place.label} does not offer {tool.phrase}. "
                f"Pick a tool that could really be found there.)")
    if tool.power < boulder.need:
        return (f"(No story: {tool.phrase} is not strong enough for the {boulder.label}. "
                f"The plan must be able to move the stone.)")
    return "(No story: this combination is unreasonable.)"


def direct_success(trait: str, boulder: BoulderCfg) -> bool:
    return not (trait == "showy" and boulder.need >= 3)


def outcome_of(params: "StoryParams") -> str:
    return "direct" if direct_success(params.trait, BOULDERS[params.boulder]) else "stumble"


# ---------------------------------------------------------------------------
# Screenplay verbs
# ---------------------------------------------------------------------------
def intro(world: World, hero: Entity, friend: Entity, place: Place, capes: tuple[str, str]) -> None:
    hero_name, friend_name = capes
    world.say(
        f"{hero.id} and {friend.id} loved pretending they were superheroes. "
        f"Today {hero.id} called {hero.pronoun('object')}self {hero_name}, and "
        f"{friend.id} grinned and chose the name {friend_name}."
    )
    world.say(
        f"They ran to {place.label} for {place.festival}. {place.scene}"
    )
    world.say(
        f"They wanted to carry shiny paper stars up to {place.ancestor_site} before everyone else arrived."
    )


def discover_problem(world: World, place: Place, boulder: BoulderCfg) -> None:
    path = world.get("path")
    path.meters["blocked"] += 1
    propagate(world)
    world.say(
        f"But the windy night had made a jumble on the path: {place.jumble} lay everywhere."
    )
    world.say(
        f"Right in the middle sat a {boulder.color} boulder. {boulder.size_line}"
    )
    world.say(
        "No one could reach the celebration spot until the path was clear."
    )


def solo_boast(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["pride"] += 1
    world.say(
        f'"Stand back," said {hero.id}. "A real hero can do this alone."'
    )
    world.say(
        f"{friend.id} frowned, not because {friend.pronoun()} was scared, "
        f"but because {friend.pronoun()} knew big problems rarely liked lonely plans."
    )


def solo_fail(world: World, hero: Entity, boulder: BoulderCfg) -> None:
    hero.memes["solo_fail"] += 1
    propagate(world)
    world.say(
        f"{hero.id} shoved with both hands until {hero.pronoun('possessive')} cape slipped sideways, "
        f"but the {boulder.label} only gave a tiny scrape and stayed put."
    )
    world.say(
        f"{hero.id} stepped back, cheeks warm. The stone was stronger than bragging."
    )


def friendship_turn(world: World, hero: Entity, friend: Entity, tool: ToolCfg, place: Place) -> None:
    world.say(
        f'{friend.id} touched {hero.id}\'s sleeve and said, '
        f'"Super teams do not have to win alone. Let\'s use {tool.phrase}."'
    )
    if tool.id != "hands":
        world.say(
            f"That idea fit the place perfectly, because near them was exactly what they needed."
        )
    hero.memes["trust"] += 1
    friend.memes["trust"] += 1


def direct_team_choice(world: World, hero: Entity, friend: Entity, tool: ToolCfg) -> None:
    world.say(
        f'{hero.id} took one look at the boulder, then at {friend.id}, and nodded. '
        f'"You\'re right," {hero.pronoun()} said. "Best friends make the best rescue team."'
    )
    hero.memes["trust"] += 1
    friend.memes["trust"] += 1


def move_boulder(world: World, hero: Entity, friend: Entity, boulder: Entity, tool: ToolCfg, place: Place) -> None:
    boulder.meters["moved"] += 1
    boulder.meters["distance"] += 1
    propagate(world)
    world.say(
        f"Together they {tool.use_line}. The boulder rolled with a deep stoney grrrr "
        f"until it bumped safely off the path."
    )
    world.say(
        f"Then they whisked aside the rest of the jumble so the way to {place.ancestor_site} opened wide."
    )


def ending(world: World, hero: Entity, friend: Entity, place: Place, capes: tuple[str, str]) -> None:
    crowd = world.get("crowd")
    hero_name, friend_name = capes
    if crowd.memes["relief"] >= THRESHOLD:
        world.say(
            f"Families clapped, and one grandparent laughed that {hero_name} and {friend_name} "
            f"had saved the morning without any lasers at all."
        )
    world.say(
        f"{hero.id} bumped shoulders with {friend.id}. The path to {place.ancestor_site} was clear, "
        f"and the two capes fluttered side by side like one brave flag."
    )
    world.say(
        "That was when they understood their truest superpower: friendship made each of them stronger."
    )


# ---------------------------------------------------------------------------
# Story builder
# ---------------------------------------------------------------------------
def tell(place: Place, boulder_cfg: BoulderCfg, tool_cfg: ToolCfg,
         hero_name: str = "Lily", hero_gender: str = "girl",
         friend_name: str = "Max", friend_gender: str = "boy",
         parent_type: str = "mother", trait: str = "showy",
         cape_style: str = "lightning") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero", traits=[trait]))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend", traits=["loyal"]))
    world.add(Entity(id="crowd", kind="character", type="group", role="crowd", label="the families"))
    world.add(Entity(id="path", type="path", label="the path"))
    boulder = world.add(Entity(id="boulder", type="boulder", label=boulder_cfg.label, movable=True))
    world.add(Entity(id="parent", kind="character", type=parent_type, role="adult", label="the parent"))

    capes = CAPE_STYLES[cape_style]

    intro(world, hero, friend, place, capes)
    world.para()
    discover_problem(world, place, boulder_cfg)
    world.para()

    if direct_success(trait, boulder_cfg):
        direct_team_choice(world, hero, friend, tool_cfg)
    else:
        solo_boast(world, hero, friend)
        solo_fail(world, hero, boulder_cfg)
        friendship_turn(world, hero, friend, tool_cfg, place)

    world.para()
    move_boulder(world, hero, friend, boulder, tool_cfg, place)
    world.para()
    ending(world, hero, friend, place, capes)

    world.facts.update(
        hero=hero,
        friend=friend,
        place=place,
        boulder_cfg=boulder_cfg,
        tool=tool_cfg,
        parent=world.get("parent"),
        capes=capes,
        outcome="direct" if direct_success(trait, boulder_cfg) else "stumble",
        blocked=True,
        cleared=world.get("path").meters["blocked"] < THRESHOLD,
        solo_attempt=hero.memes["solo_fail"] >= THRESHOLD,
        festival=place.festival,
    )
    return world


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    boulder: str
    tool: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    parent: str
    trait: str
    cape_style: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "ancestor": [(
        "What is an ancestor?",
        "An ancestor is a family member from long ago, like a great-grandparent or someone even earlier. "
        "People sometimes remember ancestors with stories, trees, pictures, or old buildings."
    )],
    "boulder": [(
        "What is a boulder?",
        "A boulder is a very big rock. It is much heavier than a stone you can toss in your hand."
    )],
    "lever": [(
        "How does a lever help move something heavy?",
        "A lever is a strong bar, like a branch or pole, that helps lift or shift something heavy. "
        "It lets people use their strength in a smarter way."
    )],
    "rope": [(
        "Why is a rope useful for pulling?",
        "A rope lets you pull from a safer distance and share the work. "
        "When two people pull together, the load feels easier to move."
    )],
    "friendship": [(
        "Why can friendship help in a hard job?",
        "Friendship helps because friends listen, encourage one another, and work together. "
        "A good friend can turn a lonely problem into a team solution."
    )],
    "teamwork": [(
        "What is teamwork?",
        "Teamwork means people helping each other to do one job. "
        "Each person adds strength, ideas, or care so the job goes better."
    )],
}

KNOWLEDGE_ORDER = ["ancestor", "boulder", "lever", "rope", "friendship", "teamwork"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, friend = f["hero"], f["friend"]
    place, boulder, tool = f["place"], f["boulder_cfg"], f["tool"]
    prompts = [
        'Write a short superhero story for a 3-to-5-year-old that includes the words "jumble", "ancestor", and "boulder".',
        f"Tell a friendship story where {hero.id} and {friend.id} pretend to be superheroes, find a path blocked by a {boulder.label}, and solve the problem together.",
        f"Write a gentle heroic story set at {place.label} during {place.festival}, where teamwork matters more than showing off."
    ]
    if f["outcome"] == "stumble":
        prompts.append(
            f"Include a moment where {hero.id} first wants to act alone, then learns that using {tool.phrase} with a friend is the wiser kind of heroism."
        )
    return prompts


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, friend = f["hero"], f["friend"]
    place, boulder, tool = f["place"], f["boulder_cfg"], f["tool"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two friends, {hero.id} and {friend.id}, who pretend to be superheroes together. "
            f"They go to {place.label} to help on {place.festival}."
        ),
        (
            "What problem did they find?",
            f"They found a jumble on the path and a {boulder.label} blocking the way to {place.ancestor_site}. "
            f"Because the path was blocked, families could not reach the celebration spot."
        ),
        (
            f"How did they move the boulder?",
            f"They {tool.qa_line}. That worked because their plan was strong enough for the stone and they shared the effort."
        ),
    ]
    if f["solo_attempt"]:
        qa.append((
            f"Why did {hero.id} stop trying to do everything alone?",
            f"{hero.id} pushed alone first, but the boulder barely scraped and did not move. "
            f"That failure showed {hero.pronoun('object')} that pride was weaker than a good plan and a good friend."
        ))
    qa.append((
        "What changed by the end of the story?",
        f"At the end, the path was clear and everyone could walk up to the ancestor place again. "
        f"{hero.id} and {friend.id} also understood that friendship was their real superpower."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"ancestor", "boulder", "friendship", "teamwork"}
    tool = world.facts["tool"]
    tags |= set(tool.tags)
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
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(x[0] for x in world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid(P, B, T) :- place(P), boulder(B), tool(T), sense(T, S), sense_min(M), S >= M,
                  need(B, N), power(T, W), W >= N, available(P, T).

direct :- chosen_trait(T), not showy(T).
direct :- chosen_trait(T), showy(T), chosen_boulder(B), need(B, N), N < 3.
stumble :- chosen_trait(T), showy(T), chosen_boulder(B), need(B, N), N >= 3.

outcome(direct) :- direct.
outcome(stumble) :- stumble.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for tid in sorted(["hands"] + list(place.extra_tools)):
            lines.append(asp.fact("available", pid, tid))
    for bid, b in BOULDERS.items():
        lines.append(asp.fact("boulder", bid))
        lines.append(asp.fact("need", bid, b.need))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("power", tid, t.power))
        lines.append(asp.fact("sense", tid, t.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    for tr in TRAITS:
        lines.append(asp.fact("trait", tr))
    lines.append(asp.fact("showy", "showy"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_trait", params.trait),
        asp.fact("chosen_boulder", params.boulder),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    pset, cset = set(valid_combos()), set(asp_valid_combos())
    if pset == cset:
        print(f"OK: gate matches valid_combos() ({len(pset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if pset - cset:
            print("  only in python:", sorted(pset - cset))
        if cset - pset:
            print("  only in clingo:", sorted(cset - pset))

    cases = list(CURATED)
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = []
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            bad.append((p, asp_outcome(p), outcome_of(p)))
    if not bad:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(bad)} outcomes differ.")
        for p, a, py in bad[:5]:
            print(" ", p, a, py)

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=False, qa=True, header="### smoke")
        print("OK: generate/emit smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams("ancestor_oak", "small", "hands", "Lily", "girl", "Max", "boy", "mother", "steady", "lightning"),
    StoryParams("ancestor_oak", "medium", "branch_lever", "Mia", "girl", "Ben", "boy", "father", "showy", "forest"),
    StoryParams("ancestor_mural", "large", "wagon_rope", "Theo", "boy", "Ava", "girl", "mother", "showy", "sky"),
    StoryParams("ancestor_bridge", "medium", "branch_lever", "Nora", "girl", "Finn", "boy", "father", "careful", "sky"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: superhero friendship clears a blocked heritage path."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--boulder", choices=BOULDERS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.boulder and args.tool:
        place, boulder, tool = PLACES[args.place], BOULDERS[args.boulder], TOOLS[args.tool]
        if not valid_combo(place, boulder, tool):
            raise StoryError(explain_rejection(place, boulder, tool))
    elif args.tool and TOOLS[args.tool].sense < SENSE_MIN:
        place = PLACES[args.place] if args.place else next(iter(PLACES.values()))
        boulder = BOULDERS[args.boulder] if args.boulder else next(iter(BOULDERS.values()))
        raise StoryError(explain_rejection(place, boulder, TOOLS[args.tool]))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.boulder is None or c[1] == args.boulder)
        and (args.tool is None or c[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, boulder_id, tool_id = rng.choice(sorted(combos))
    hero, hero_gender = _pick_name(rng)
    friend, friend_gender = _pick_name(rng, avoid=hero)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    cape_style = rng.choice(sorted(CAPE_STYLES))
    return StoryParams(
        place_id, boulder_id, tool_id,
        hero, hero_gender, friend, friend_gender,
        parent, trait, cape_style
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        BOULDERS[params.boulder],
        TOOLS[params.tool],
        params.hero,
        params.hero_gender,
        params.friend,
        params.friend_gender,
        params.parent,
        params.trait,
        params.cape_style,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, boulder, tool) combos:\n")
        for place, boulder, tool in combos:
            print(f"  {place:15} {boulder:7} {tool}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
            header = f"### {p.hero} & {p.friend}: {p.boulder} boulder at {p.place} with {p.tool} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

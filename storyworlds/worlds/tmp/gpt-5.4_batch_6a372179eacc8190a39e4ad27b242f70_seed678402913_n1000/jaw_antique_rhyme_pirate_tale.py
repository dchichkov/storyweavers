#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/jaw_antique_rhyme_pirate_tale.py
===========================================================

A standalone story world for a small pirate-tale domain built from the seed
words "jaw" and "antique" with a rhyme-driven turn.

Premise
-------
Two children playing pirates find an antique clue tool. A pirate obstacle blocks
their way to a small treasure. One child wants to rush. The other remembers a
short rhyme etched on the antique object. When they use the right antique for
the right obstacle, the world changes: the path opens, fear eases, and the
treasure can be found.

The reasonableness gate is deliberately small:
- each place only affords certain obstacles
- each obstacle has exactly one antique tool that sensibly solves it

So the world refuses mismatched stories like using an antique key to solve fog.

Run it
------
python storyworlds/worlds/gpt-5.4/jaw_antique_rhyme_pirate_tale.py
python storyworlds/worlds/gpt-5.4/jaw_antique_rhyme_pirate_tale.py --place moonlit_cove --obstacle fog_bank --antique compass
python storyworlds/worlds/gpt-5.4/jaw_antique_rhyme_pirate_tale.py --obstacle chest_lock --antique spyglass
python storyworlds/worlds/gpt-5.4/jaw_antique_rhyme_pirate_tale.py --all
python storyworlds/worlds/gpt-5.4/jaw_antique_rhyme_pirate_tale.py --qa --json
python storyworlds/worlds/gpt-5.4/jaw_antique_rhyme_pirate_tale.py --verify
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "grandmother"}
        male = {"boy", "father", "man", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    open_line: str
    image: str
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Antique:
    id: str
    label: str
    phrase: str
    solves: str
    shine: str
    rhyme: str
    clue_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    block_line: str
    rash_idea: str
    solved_line: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    gleam: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    obstacle: str
    antique: str
    treasure: str
    captain: str
    captain_gender: str
    mate: str
    mate_gender: str
    elder: str
    elder_type: str
    boldness: str
    seed: Optional[int] = None


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.history: list[str] = []
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"captain", "mate"}]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def log(self, event: str) -> None:
        self.history.append(event)

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.history = list(self.history)
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_path_open(world: World) -> list[str]:
    antique = world.entities.get("antique")
    obstacle = world.entities.get("obstacle")
    if antique is None or obstacle is None:
        return []
    if antique.meters["used_well"] < THRESHOLD or obstacle.meters["blocked"] < THRESHOLD:
        return []
    sig = ("path_open",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    obstacle.meters["blocked"] = 0.0
    obstacle.meters["cleared"] += 1
    world.get("path").meters["open"] += 1
    for kid in world.kids():
        kid.memes["relief"] += 1
        kid.memes["hope"] += 1
        kid.memes["fear"] = 0.0
    world.log("path_opened")
    return []


def _r_treasure_found(world: World) -> list[str]:
    if world.get("path").meters["open"] < THRESHOLD:
        return []
    if world.get("treasure").meters["hidden"] < THRESHOLD:
        return []
    sig = ("treasure_found",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("treasure").meters["hidden"] = 0.0
    world.get("treasure").meters["found"] += 1
    for kid in world.kids():
        kid.memes["joy"] += 1
        kid.memes["wonder"] += 1
    world.log("treasure_found")
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="path_open", tag="physical", apply=_r_path_open),
    Rule(name="treasure_found", tag="physical", apply=_r_treasure_found),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            made = rule.apply(world)
            if made:
                changed = True
                out.extend(made)
            elif world.history:
                pass
            if made:
                changed = True
    if narrate:
        for sent in out:
            world.say(sent)
    return out


PLACES = {
    "moonlit_cove": Place(
        id="moonlit_cove",
        label="Moonlit Cove",
        open_line="At Moonlit Cove, the waves clicked over pebbles like quiet pirate coins.",
        image="A hook-shaped rock leaned over the water, and the children liked to call it Jaw Rock.",
        affords={"fog_bank", "far_marker"},
        tags={"sea", "cove"},
    ),
    "captains_cabin": Place(
        id="captains_cabin",
        label="the old captain's cabin",
        open_line="In the old captain's cabin, the boards creaked as if the ship still remembered storms.",
        image="A carved shark jaw grinned over a small brass chest in the corner.",
        affords={"chest_lock"},
        tags={"cabin", "ship"},
    ),
    "echo_cave": Place(
        id="echo_cave",
        label="Echo Cave",
        open_line="By Echo Cave, the tide breathed in and out under a stone arch.",
        image="The cave mouth looked like a giant gray jaw waiting to sing back every shout.",
        affords={"fog_bank", "chest_lock"},
        tags={"cave", "sea"},
    ),
}

ANTIQUES = {
    "compass": Antique(
        id="compass",
        label="antique compass",
        phrase="an antique brass compass",
        solves="fog_bank",
        shine="Its glass face caught the light, and the tiny needle trembled as if it knew secrets.",
        rhyme="Needle bright, point us right; through the mist, bring morning light.",
        clue_line="Around the rim, tiny letters still shone: 'Needle bright, point us right.'",
        tags={"compass", "rhyme"},
    ),
    "key": Antique(
        id="key",
        label="antique key",
        phrase="an antique iron key",
        solves="chest_lock",
        shine="Its old teeth were worn smooth by long-ago fingers.",
        rhyme="Old key, turn slow and true; wake the gold for me and you.",
        clue_line="On the bow of the key, the old words were still clear: 'Turn slow and true.'",
        tags={"key", "rhyme"},
    ),
    "spyglass": Antique(
        id="spyglass",
        label="antique spyglass",
        phrase="an antique spyglass bound in faded leather",
        solves="far_marker",
        shine="Its brass rings flashed when it was lifted toward the sea.",
        rhyme="Glass to eye, sea to sky; show the mark that's small and shy.",
        clue_line="A thin silver band around it said: 'Glass to eye, sea to sky.'",
        tags={"spyglass", "rhyme"},
    ),
}

OBSTACLES = {
    "fog_bank": Obstacle(
        id="fog_bank",
        label="fog bank",
        block_line="A white fog bank rolled over the water and swallowed the little red buoy that marked the safe way.",
        rash_idea="Captain {captain} wanted to charge straight ahead before the mist changed shape again.",
        solved_line="The needle steadied, and soon a safe path curved out of the fog like a ribbon.",
        ending_image="Beyond the last curl of mist, the treasure place waited in clear silver light.",
        tags={"fog", "sea"},
    ),
    "chest_lock": Obstacle(
        id="chest_lock",
        label="chest lock",
        block_line="The brass chest would not open. Its lid sat tight as a closed jaw.",
        rash_idea="Captain {captain} wanted to tug and thump the lid as hard as possible.",
        solved_line="The lock gave one neat click, and the old jaw-like lid lifted with a sleepy sigh.",
        ending_image="Inside the open chest, treasure glow warmed the dusty boards.",
        tags={"lock", "chest"},
    ),
    "far_marker": Obstacle(
        id="far_marker",
        label="far marker",
        block_line="The map said the prize was hidden past Jaw Rock, but the tiny shell mark was far too small to spot with bare eyes.",
        rash_idea="Captain {captain} wanted to dig at the first patch of sand that looked lucky.",
        solved_line="The far mark leaped close in the lens, and the right patch of sand winked from beside Jaw Rock.",
        ending_image="At the foot of Jaw Rock, the true hiding place shone plain at last.",
        tags={"marker", "sea"},
    ),
}

TREASURES = {
    "pearls": Treasure(
        id="pearls",
        label="pearls",
        phrase="a tiny cloth bag of moon-pale pearls",
        gleam="They glowed softly like drops of frozen moonlight.",
        tags={"treasure"},
    ),
    "coins": Treasure(
        id="coins",
        label="coins",
        phrase="a round tin of bright gold-colored coins",
        gleam="They flashed and chimed when the tin was tipped.",
        tags={"treasure"},
    ),
    "shell_crown": Treasure(
        id="shell_crown",
        label="shell crown",
        phrase="a little shell crown with blue ribbon ties",
        gleam="It sparkled with salt and tiny bits of glassy green sea stone.",
        tags={"treasure"},
    ),
}

GIRL_NAMES = ["Lila", "Mina", "Nora", "Ava", "Ruby", "Tess", "Wren", "Lucy"]
BOY_NAMES = ["Finn", "Toby", "Max", "Eli", "Jack", "Sam", "Leo", "Ben"]
BOLDNESS = ["bold", "bouncy", "eager", "stormy"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for obstacle_id in sorted(place.affords):
            for antique_id, antique in ANTIQUES.items():
                if antique.solves == obstacle_id:
                    combos.append((place_id, obstacle_id, antique_id))
    return combos


def explain_rejection(place: Place, obstacle: Obstacle, antique: Antique) -> str:
    if obstacle.id not in place.affords:
        return (
            f"(No story: {place.label} does not naturally set up the problem '{obstacle.label}'. "
            f"Pick a place that actually affords that obstacle.)"
        )
    return (
        f"(No story: {antique.label} does not sensibly solve '{obstacle.label}'. "
        f"This world only allows antique tools that honestly fit the obstacle.)"
    )


def outcome_of(params: StoryParams) -> str:
    if (params.place, params.obstacle, params.antique) in set(valid_combos()):
        return "solved"
    return "invalid"


def _do_use_antique(world: World, antique_cfg: Antique, obstacle_cfg: Obstacle, narrate: bool = True) -> None:
    antique_ent = world.get("antique")
    if antique_cfg.solves != obstacle_cfg.id:
        antique_ent.memes["doubt"] += 1
        world.log("wrong_tool")
        return
    antique_ent.meters["used_well"] += 1
    world.log("used_antique_well")
    propagate(world, narrate=narrate)


def predict_solution(world: World, antique_cfg: Antique, obstacle_cfg: Obstacle) -> dict:
    sim = world.copy()
    _do_use_antique(sim, antique_cfg, obstacle_cfg, narrate=False)
    return {
        "path_open": sim.get("path").meters["open"] >= THRESHOLD,
        "treasure_found": sim.get("treasure").meters["found"] >= THRESHOLD,
    }


def opening(world: World, captain: Entity, mate: Entity, elder: Entity, antique_cfg: Antique) -> None:
    for kid in (captain, mate):
        kid.memes["joy"] += 1
        kid.memes["curiosity"] += 1
    world.say(
        f"{world.place.open_line} {world.place.image}"
    )
    world.say(
        f'"Captain {captain.id} and Mate {mate.id}!" {captain.id} cried, thumping a heel on the floorboards of make-believe. '
        f'"Treasure first, supper later!"'
    )
    world.say(
        f"{elder.label_word.capitalize()} smiled and handed them {antique_cfg.phrase}. "
        f'"This belonged to an old sea captain," {elder.pronoun()} said. '
        f'"It is antique, so small hands must use it gently."'
    )
    world.say(antique_cfg.shine)


def obstacle_rises(world: World, captain: Entity, obstacle_cfg: Obstacle) -> None:
    obstacle = world.get("obstacle")
    obstacle.meters["blocked"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
        kid.memes["frustration"] += 1
    world.log("obstacle_blocked")
    world.say(obstacle_cfg.block_line)
    world.say(obstacle_cfg.rash_idea.format(captain=captain.id))


def warning(world: World, captain: Entity, mate: Entity, antique_cfg: Antique, obstacle_cfg: Obstacle) -> None:
    pred = predict_solution(world, antique_cfg, obstacle_cfg)
    mate.memes["care"] += 1
    world.facts["predicted_path_open"] = pred["path_open"]
    world.say(
        f'{mate.id} touched {antique_cfg.label} with one careful finger. '
        f'"Wait, Captain {captain.id}," {mate.pronoun()} said. "{antique_cfg.clue_line}"'
    )
    if pred["path_open"]:
        world.say(
            f"{mate.id} thought the old rhyme might show them the true way instead of a hasty one."
        )


def speak_rhyme(world: World, captain: Entity, mate: Entity, antique_cfg: Antique) -> None:
    for kid in (captain, mate):
        kid.memes["hope"] += 1
    world.log("rhyme_spoken")
    world.say(
        f'Together they whispered the rhyme: "{antique_cfg.rhyme}"'
    )


def solve(world: World, obstacle_cfg: Obstacle, treasure_cfg: Treasure) -> None:
    _do_use_antique(world, ANTIQUES[world.facts["antique_cfg"].id], obstacle_cfg)
    if world.get("path").meters["open"] >= THRESHOLD:
        world.say(obstacle_cfg.solved_line)
        world.say(obstacle_cfg.ending_image)
    if world.get("treasure").meters["found"] >= THRESHOLD:
        world.say(
            f"There it was: {treasure_cfg.phrase}. {treasure_cfg.gleam}"
        )


def ending(world: World, captain: Entity, mate: Entity, elder: Entity, treasure_cfg: Treasure) -> None:
    for kid in (captain, mate):
        kid.memes["pride"] += 1
    world.say(
        f"{captain.id}'s jaw dropped first, and then {mate.id} laughed so hard the cave gave a tiny echo back."
    )
    world.say(
        f'"We did not bash or guess," {mate.id} said. "We listened."'
    )
    world.say(
        f'{elder.label_word.capitalize()} nodded. "That is how old pirate clues like to be treated."'
    )
    world.say(
        f"Hand in hand, the little pirates carried {treasure_cfg.label} home through the salt air, "
        f"with the antique clue tucked safely between them."
    )


def tell(
    place_cfg: Place,
    antique_cfg: Antique,
    obstacle_cfg: Obstacle,
    treasure_cfg: Treasure,
    captain_name: str = "Finn",
    captain_gender: str = "boy",
    mate_name: str = "Lila",
    mate_gender: str = "girl",
    elder_type: str = "grandmother",
    boldness: str = "bold",
) -> World:
    world = World(place_cfg)
    captain = world.add(Entity(
        id=captain_name,
        kind="character",
        type=captain_gender,
        role="captain",
        traits=[boldness],
    ))
    mate = world.add(Entity(
        id=mate_name,
        kind="character",
        type=mate_gender,
        role="mate",
        traits=["careful"],
    ))
    elder = world.add(Entity(
        id="Elder",
        kind="character",
        type=elder_type,
        role="elder",
        label="the elder",
    ))
    antique = world.add(Entity(
        id="antique",
        type="tool",
        label=antique_cfg.label,
        phrase=antique_cfg.phrase,
        tags=set(antique_cfg.tags),
    ))
    obstacle = world.add(Entity(
        id="obstacle",
        type="obstacle",
        label=obstacle_cfg.label,
        tags=set(obstacle_cfg.tags),
    ))
    treasure = world.add(Entity(
        id="treasure",
        type="treasure",
        label=treasure_cfg.label,
        phrase=treasure_cfg.phrase,
        tags=set(treasure_cfg.tags),
    ))
    path = world.add(Entity(
        id="path",
        type="path",
        label="the way",
    ))
    treasure.meters["hidden"] += 1

    opening(world, captain, mate, elder, antique_cfg)
    world.para()
    obstacle_rises(world, captain, obstacle_cfg)
    warning(world, captain, mate, antique_cfg, obstacle_cfg)
    world.para()
    speak_rhyme(world, captain, mate, antique_cfg)
    world.facts["antique_cfg"] = antique_cfg
    solve(world, obstacle_cfg, treasure_cfg)
    world.para()
    ending(world, captain, mate, elder, treasure_cfg)

    world.facts.update(
        place=place_cfg,
        antique=antique,
        antique_cfg=antique_cfg,
        obstacle=obstacle,
        obstacle_cfg=obstacle_cfg,
        treasure=treasure,
        treasure_cfg=treasure_cfg,
        captain=captain,
        mate=mate,
        elder=elder,
        solved=path.meters["open"] >= THRESHOLD,
        rhyme_used="rhyme_spoken" in world.history,
        found=treasure.meters["found"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "compass": [
        (
            "What does a compass do?",
            "A compass is a tool with a needle that points in a steady direction. Sailors can use it to help them find the right way when everything else looks confusing.",
        )
    ],
    "key": [
        (
            "What is a key for?",
            "A key is made to fit a lock and turn it open. The right key works gently, while forcing a lid can break things.",
        )
    ],
    "spyglass": [
        (
            "What is a spyglass?",
            "A spyglass is a little telescope pirates and sailors use to see faraway things. It makes tiny marks look bigger and easier to find.",
        )
    ],
    "rhyme": [
        (
            "What is a rhyme?",
            "A rhyme is a short saying or poem with words that sound alike. Rhymes are easy to remember, so they can help people keep a clue in mind.",
        )
    ],
    "fog": [
        (
            "Why is fog hard to travel through?",
            "Fog is made of tiny water drops hanging in the air, and it hides what is ahead. That makes it easy to miss the safe path.",
        )
    ],
    "lock": [
        (
            "Why should you open an old lock gently?",
            "Old locks can be stiff or delicate, especially on antique things. Turning the right key slowly is safer than yanking or banging.",
        )
    ],
    "marker": [
        (
            "Why do explorers use markers and clues?",
            "Markers help explorers find the exact place they are looking for. Without them, many spots can look almost the same.",
        )
    ],
    "antique": [
        (
            "What does antique mean?",
            "Antique means very old and from long ago. Antique things should be handled carefully because they can be special and fragile.",
        )
    ],
}
KNOWLEDGE_ORDER = ["antique", "rhyme", "compass", "key", "spyglass", "fog", "lock", "marker"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    captain = f["captain"]
    mate = f["mate"]
    place = f["place"]
    antique_cfg = f["antique_cfg"]
    obstacle_cfg = f["obstacle_cfg"]
    treasure_cfg = f["treasure_cfg"]
    return [
        f'Write a short pirate tale for a 3-to-5-year-old that includes the words "jaw" and "antique" and uses a rhyme to solve a problem.',
        f"Tell a gentle pirate story where Captain {captain.id} wants to rush, but {mate.id} remembers a rhyme on {antique_cfg.phrase} and helps the crew past {obstacle_cfg.label}.",
        f"Write a child-facing adventure set at {place.label} where an antique clue leads to {treasure_cfg.label} and the ending shows what changed.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    captain = f["captain"]
    mate = f["mate"]
    elder = f["elder"]
    place = f["place"]
    antique_cfg = f["antique_cfg"]
    obstacle_cfg = f["obstacle_cfg"]
    treasure_cfg = f["treasure_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two little pirates, Captain {captain.id} and Mate {mate.id}, and their {elder.label_word} who trusts them with an old clue. The story follows how they solve one pirate problem together.",
        ),
        (
            "What antique thing did they get?",
            f"They were given {antique_cfg.phrase}. It was antique, which means it was very old and needed gentle hands.",
        ),
        (
            "What problem blocked the treasure hunt?",
            f"{obstacle_cfg.block_line} That problem stopped them from reaching the treasure until they changed their plan.",
        ),
        (
            f"Why did {mate.id} tell Captain {captain.id} to wait?",
            f"{mate.id} remembered that the antique object carried a rhyme clue. The clue mattered because it matched the obstacle and could open the way better than guessing.",
        ),
    ]
    if f["rhyme_used"]:
        qa.append(
            (
                "What rhyme did they say, and why did it help?",
                f'They said, "{antique_cfg.rhyme}" The rhyme helped them remember the right way to use the antique clue, so they solved the problem calmly instead of rushing.',
            )
        )
    if f["solved"]:
        qa.append(
            (
                "How did the obstacle get solved?",
                f"They used the antique object that truly fit the obstacle, and the world changed right away. The path opened, their fear dropped away, and hope turned into treasure-finding joy.",
            )
        )
    if f["found"]:
        qa.append(
            (
                "What happened at the end?",
                f"They found {treasure_cfg.phrase}, and {captain.id}'s jaw dropped when the treasure shone out. The ending proves they had really moved from being stuck to being successful.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"antique", "rhyme"}
    tags |= set(world.facts["antique_cfg"].tags)
    tags |= set(world.facts["obstacle_cfg"].tags)
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
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  history: {world.history}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="moonlit_cove",
        obstacle="fog_bank",
        antique="compass",
        treasure="pearls",
        captain="Finn",
        captain_gender="boy",
        mate="Lila",
        mate_gender="girl",
        elder="Nana",
        elder_type="grandmother",
        boldness="bold",
    ),
    StoryParams(
        place="captains_cabin",
        obstacle="chest_lock",
        antique="key",
        treasure="coins",
        captain="Nora",
        captain_gender="girl",
        mate="Ben",
        mate_gender="boy",
        elder="Grandpa",
        elder_type="grandfather",
        boldness="eager",
    ),
    StoryParams(
        place="moonlit_cove",
        obstacle="far_marker",
        antique="spyglass",
        treasure="shell_crown",
        captain="Toby",
        captain_gender="boy",
        mate="Ruby",
        mate_gender="girl",
        elder="Nana",
        elder_type="grandmother",
        boldness="bouncy",
    ),
    StoryParams(
        place="echo_cave",
        obstacle="chest_lock",
        antique="key",
        treasure="pearls",
        captain="Mina",
        captain_gender="girl",
        mate="Leo",
        mate_gender="boy",
        elder="Grandpa",
        elder_type="grandfather",
        boldness="stormy",
    ),
]


ASP_RULES = r"""
compatible_antique(A, O) :- antique(A), solves(A, O).
valid(P, O, A) :- place(P), obstacle(O), antique(A), affords(P, O), compatible_antique(A, O).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for obstacle_id in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, obstacle_id))
    for antique_id, antique in ANTIQUES.items():
        lines.append(asp.fact("antique", antique_id))
        lines.append(asp.fact("solves", antique_id, antique.solves))
    for obstacle_id in OBSTACLES:
        lines.append(asp.fact("obstacle", obstacle_id))
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
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    smoke_cases = list(CURATED)
    try:
        args = build_parser().parse_args([])
        params = resolve_params(args, random.Random(7))
        smoke_cases.append(params)
    except StoryError as err:
        rc = 1
        print(f"SMOKE setup failed: {err}")

    try:
        for params in smoke_cases:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("Generated empty story.")
            emit(sample, trace=False, qa=False, header="")
        print(f"OK: smoke-generated {len(smoke_cases)} stories.")
    except Exception as err:
        rc = 1
        print(f"SMOKE generation failed: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: antique pirate clues, a remembered rhyme, and a treasure hunt."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--antique", choices=ANTIQUES)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--captain")
    ap.add_argument("--mate")
    ap.add_argument("--captain-gender", choices=["girl", "boy"])
    ap.add_argument("--mate-gender", choices=["girl", "boy"])
    ap.add_argument("--elder-type", choices=["grandmother", "grandfather"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place_id = args.place
    obstacle_id = args.obstacle
    antique_id = args.antique

    if place_id and obstacle_id and antique_id:
        place = PLACES[place_id]
        obstacle = OBSTACLES[obstacle_id]
        antique = ANTIQUES[antique_id]
        if (place_id, obstacle_id, antique_id) not in set(valid_combos()):
            raise StoryError(explain_rejection(place, obstacle, antique))

    combos = [
        combo
        for combo in valid_combos()
        if (place_id is None or combo[0] == place_id)
        and (obstacle_id is None or combo[1] == obstacle_id)
        and (antique_id is None or combo[2] == antique_id)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, obstacle_id, antique_id = rng.choice(sorted(combos))
    treasure_id = args.treasure or rng.choice(sorted(TREASURES))
    captain_gender = args.captain_gender or rng.choice(["girl", "boy"])
    mate_gender = args.mate_gender or rng.choice(["girl", "boy"])
    captain = args.captain or pick_name(rng, captain_gender)
    mate = args.mate or pick_name(rng, mate_gender, avoid=captain)
    elder_type = args.elder_type or rng.choice(["grandmother", "grandfather"])
    elder = "Nana" if elder_type == "grandmother" else "Grandpa"
    boldness = rng.choice(BOLDNESS)

    return StoryParams(
        place=place_id,
        obstacle=obstacle_id,
        antique=antique_id,
        treasure=treasure_id,
        captain=captain,
        captain_gender=captain_gender,
        mate=mate,
        mate_gender=mate_gender,
        elder=elder,
        elder_type=elder_type,
        boldness=boldness,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.antique not in ANTIQUES:
        raise StoryError(f"(Unknown antique: {params.antique})")
    if params.treasure not in TREASURES:
        raise StoryError(f"(Unknown treasure: {params.treasure})")
    if (params.place, params.obstacle, params.antique) not in set(valid_combos()):
        raise StoryError(
            explain_rejection(PLACES[params.place], OBSTACLES[params.obstacle], ANTIQUES[params.antique])
        )

    world = tell(
        place_cfg=PLACES[params.place],
        antique_cfg=ANTIQUES[params.antique],
        obstacle_cfg=OBSTACLES[params.obstacle],
        treasure_cfg=TREASURES[params.treasure],
        captain_name=params.captain,
        captain_gender=params.captain_gender,
        mate_name=params.mate,
        mate_gender=params.mate_gender,
        elder_type=params.elder_type,
        boldness=params.boldness,
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
        print(f"{len(combos)} compatible (place, obstacle, antique) combos:\n")
        for place, obstacle, antique in combos:
            print(f"  {place:14} {obstacle:11} {antique}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.captain} & {p.mate}: {p.antique} at {p.place} against {p.obstacle}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

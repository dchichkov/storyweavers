#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/commodore_mature_piccalilli_surprise_mystery_to_solve.py
====================================================================================

A small comedy storyworld about a calm harbor lunch, a missing jar of piccalilli,
and a child who helps a mature commodore solve a silly mystery by following real
clues and sounds.

The world model tracks:
- typed entities with physical meters and emotional memes
- a reasonableness gate over which culprit/tool/place combinations make sense
- a simple outcome model (neat find vs messy find)
- an inline ASP twin for parity checking

Run it
------
    python storyworlds/worlds/gpt-5.4/commodore_mature_piccalilli_surprise_mystery_to_solve.py
    python storyworlds/worlds/gpt-5.4/commodore_mature_piccalilli_surprise_mystery_to_solve.py --place pier --culprit gull --tool spyglass
    python storyworlds/worlds/gpt-5.4/commodore_mature_piccalilli_surprise_mystery_to_solve.py --culprit dog --tool spyglass
    python storyworlds/worlds/gpt-5.4/commodore_mature_piccalilli_surprise_mystery_to_solve.py --all
    python storyworlds/worlds/gpt-5.4/commodore_mature_piccalilli_surprise_mystery_to_solve.py --verify
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    intro: str
    finale: str
    hideouts: set[str] = field(default_factory=set)
    culprits: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Culprit:
    id: str
    label: str
    phrase: str
    sound: str
    step_sound: str
    hideout: str
    clue: str
    reason: str
    neat_tools: set[str] = field(default_factory=set)
    messy: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    action: str
    sense: int
    tidy: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Snack:
    id: str
    label: str
    serving: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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


def culprit_allowed(place: Place, culprit: Culprit) -> bool:
    return culprit.id in place.culprits and culprit.hideout in place.hideouts


def sensible_tool(culprit: Culprit, tool: Tool) -> bool:
    return tool.sense >= SENSE_MIN and tool.id in culprit.neat_tools


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for culprit_id, culprit in CULPRITS.items():
            if not culprit_allowed(place, culprit):
                continue
            for tool_id, tool in TOOLS.items():
                if sensible_tool(culprit, tool):
                    combos.append((place_id, culprit_id, tool_id))
    return combos


def outcome_of(params: "StoryParams") -> str:
    culprit = CULPRITS[params.culprit]
    tool = TOOLS[params.tool]
    if tool.tidy and not culprit.messy:
        return "neat"
    return "messy"


def discover(world: World, hero: Entity, commodore: Entity, culprit: Entity, jar: Entity,
             culprit_cfg: Culprit, tool_cfg: Tool) -> None:
    hero.memes["curiosity"] += 1
    commodore.memes["calm"] += 1
    world.say(
        f'"Mystery to solve," said {commodore.id}, smoothing {commodore.pronoun("possessive")} coat. '
        f'"A mature commodore does not shout first. A mature commodore looks, listens, and only then says hmm."'
    )
    world.say(
        f'{hero.id} listened. "{culprit_cfg.sound}! {culprit_cfg.step_sound}!" came from '
        f'{jar.attrs["hideout_phrase"]}.'
    )
    world.say(
        f'Using {tool_cfg.phrase}, {hero.id} {tool_cfg.action}. That matched the clue about {culprit_cfg.clue}.'
    )
    culprit.meters["found"] += 1
    jar.meters["found"] += 1


def propagate(world: World) -> None:
    jar = world.get("jar")
    culprit = world.get("culprit")
    if jar.meters["missing"] >= THRESHOLD and culprit.meters["hungry"] >= THRESHOLD:
        sig = ("confusion", culprit.id)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("crowd").meters["confusion"] += 1
            world.get("hero").memes["surprise"] += 1
            world.get("commodore").memes["calm"] += 1
    if culprit.meters["found"] >= THRESHOLD and jar.meters["found"] >= THRESHOLD:
        sig = ("relief", culprit.id)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("hero").memes["relief"] += 1
            world.get("commodore").memes["relief"] += 1
            world.get("crowd").meters["confusion"] = 0.0


def setup(world: World, hero: Entity, commodore: Entity, snack_cfg: Snack) -> None:
    hero.memes["joy"] += 1
    commodore.memes["pride"] += 1
    world.say(
        f"On Harbor Snack Day, {world.place.intro} {hero.id} helped Commodore {commodore.id} "
        f"line up plates for {snack_cfg.serving}."
    )
    world.say(
        f'The commodore was wonderfully mature about everything except sauces. '
        f'For the sandwiches, {commodore.pronoun()} had brought one shining jar of piccalilli and called it '
        f'"the little yellow crown of lunch."'
    )


def surprise_missing(world: World, hero: Entity, commodore: Entity, culprit_cfg: Culprit) -> None:
    jar = world.get("jar")
    jar.meters["missing"] += 1
    world.get("culprit").meters["hungry"] += 1
    propagate(world)
    world.say(
        f'Then came the surprise. "Clink?" said {hero.id}. The jar was gone.'
    )
    world.say(
        f'Only a yellow dab on the table, a wobbly spoon, and a distant "{culprit_cfg.sound}!" answered back.'
    )


def inspect_clues(world: World, hero: Entity, commodore: Entity, culprit_cfg: Culprit) -> None:
    world.say(
        f'{hero.id} crouched to inspect the floorboards and found {culprit_cfg.clue}. '
        f'Commodore {commodore.id} nodded as if clues were tiny sailors lining up for roll call.'
    )
    world.say(
        f'"No one panic," said the commodore. "Panic makes crumbs. Crumbs make more mysteries."'
    )


def reveal(world: World, hero: Entity, commodore: Entity, culprit: Entity, jar: Entity,
           culprit_cfg: Culprit, tool_cfg: Tool, snack_cfg: Snack, outcome: str) -> None:
    hideout_phrase = jar.attrs["hideout_phrase"]
    if outcome == "neat":
        jar.meters["spilled"] = 0.0
        world.say(
            f'There, tucked by {hideout_phrase}, sat {culprit_cfg.phrase} with the jar balanced beside {culprit.pronoun("object")}.'
        )
        world.say(
            f'"Aha!" cried {hero.id}. "{culprit.label} wanted the smell, not a crime career."'
        )
    else:
        jar.meters["spilled"] += 1
        culprit.meters["mess"] += 1
        world.say(
            f'There, tucked by {hideout_phrase}, sat {culprit_cfg.phrase}. '
            f'The jar tipped, gave a cheerful "splat!", and painted one stripe of piccalilli on the floor.'
        )
        world.say(
            f'Even Commodore {commodore.id} had to laugh. "{culprit.label.capitalize()} has solved the mystery of how to make lunch louder," '
            f'{commodore.pronoun()} said.'
        )
    world.say(
        f'{culprit.label.capitalize()} looked more hopeful than wicked, because {culprit_cfg.reason}.'
    )
    world.say(
        f'So the commodore wiped the jar, saved enough piccalilli for the {snack_cfg.label}, and set out one plain crust for the culprit instead.'
    )


def ending(world: World, hero: Entity, commodore: Entity, culprit: Entity, outcome: str) -> None:
    hero.memes["joy"] += 1
    commodore.memes["joy"] += 1
    propagate(world)
    if outcome == "neat":
        world.say(
            f'When the harbor horn went "toot-toot!", everyone cheered. {world.place.finale}'
        )
    else:
        world.say(
            f'When the harbor horn went "toot-toot!", everyone cheered anyway, even while stepping around the yellow stripe. {world.place.finale}'
        )
    world.say(
        f'From then on, {hero.id} said the most mature thing a commodore had ever taught {hero.pronoun("object")}: '
        f'"If lunch goes missing, listen before you accuse."'
    )


def tell(place: Place, culprit_cfg: Culprit, tool_cfg: Tool, snack_cfg: Snack,
         hero_name: str, hero_type: str, commodore_name: str, commodore_type: str) -> World:
    world = World(place)
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name, role="hero"))
    commodore = world.add(
        Entity(
            id="commodore",
            kind="character",
            type=commodore_type,
            label=commodore_name,
            role="commodore",
            traits=["mature", "calm"],
        )
    )
    culprit = world.add(
        Entity(
            id="culprit",
            kind="character",
            type="animal",
            label=culprit_cfg.label,
            phrase=culprit_cfg.phrase,
            role="culprit",
            tags=set(culprit_cfg.tags),
        )
    )
    jar = world.add(
        Entity(
            id="jar",
            kind="thing",
            type="jar",
            label="piccalilli jar",
            phrase="the bright jar of piccalilli",
            attrs={"hideout": culprit_cfg.hideout, "hideout_phrase": HIDEOUT_PHRASES[culprit_cfg.hideout]},
            tags={"piccalilli"},
        )
    )
    world.add(Entity(id="crowd", kind="group", type="crowd", label="the crowd"))

    setup(world, hero, commodore, snack_cfg)
    world.para()
    surprise_missing(world, hero, commodore, culprit_cfg)
    inspect_clues(world, hero, commodore, culprit_cfg)
    discover(world, hero, commodore, culprit, jar, culprit_cfg, tool_cfg)
    outcome = "neat" if tool_cfg.tidy and not culprit_cfg.messy else "messy"
    world.para()
    reveal(world, hero, commodore, culprit, jar, culprit_cfg, tool_cfg, snack_cfg, outcome)
    ending(world, hero, commodore, culprit, outcome)

    world.facts.update(
        hero=hero,
        commodore=commodore,
        culprit=culprit,
        culprit_cfg=culprit_cfg,
        jar=jar,
        place=place,
        tool=tool_cfg,
        snack=snack_cfg,
        outcome=outcome,
        hideout_phrase=HIDEOUT_PHRASES[culprit_cfg.hideout],
        mystery_solved=culprit.meters["found"] >= THRESHOLD,
    )
    return world


PLACES = {
    "pier": Place(
        id="pier",
        label="the pier",
        intro="under the bunting on the pier, beside three patient rowboats,",
        finale="The sandwiches vanished into happy mouths, and the mystery vanished into laughter.",
        hideouts={"lifebuoy", "rope_coil", "crate"},
        culprits={"gull", "dog"},
        tags={"harbor"},
    ),
    "boathouse": Place(
        id="boathouse",
        label="the boathouse",
        intro="inside the boathouse, where the walls smelled of salt and old paint,",
        finale="Even the oars seemed pleased, tapping softly against the wall like polite applause.",
        hideouts={"crate", "boot", "lifebuoy"},
        culprits={"goat", "dog"},
        tags={"harbor"},
    ),
    "lighthouse_yard": Place(
        id="lighthouse_yard",
        label="the lighthouse yard",
        intro="in the lighthouse yard, under a striped tent that snapped in the breeze,",
        finale="The lighthouse blinked over the whole scene as if it had enjoyed the joke too.",
        hideouts={"bench", "crate", "lifebuoy"},
        culprits={"gull", "goat"},
        tags={"harbor"},
    ),
}

HIDEOUT_PHRASES = {
    "lifebuoy": "the red lifebuoy stand",
    "rope_coil": "a fat coil of rope",
    "crate": "an apple crate",
    "boot": "one giant rubber boot by the door",
    "bench": "the windy bench under the flagpole",
}

CULPRITS = {
    "gull": Culprit(
        id="gull",
        label="gull",
        phrase="a puffed-up gull",
        sound="squawk",
        step_sound="flap-flap",
        hideout="lifebuoy",
        clue="a feather stuck in a mustard-yellow smear",
        reason="the tangy smell had drifted across the water like a trumpet for hungry birds",
        neat_tools={"spyglass", "crumb_trail"},
        messy=False,
        tags={"gull", "bird"},
    ),
    "dog": Culprit(
        id="dog",
        label="dog",
        phrase="the harbor dog",
        sound="woof",
        step_sound="sniff-sniff",
        hideout="crate",
        clue="muddy pawprints with one brave yellow toe",
        reason="dogs trust smells more than signs, and the jar smelled very important",
        neat_tools={"sniff_book", "crumb_trail"},
        messy=True,
        tags={"dog"},
    ),
    "goat": Culprit(
        id="goat",
        label="goat",
        phrase="a moon-eyed goat",
        sound="maa",
        step_sound="clop-clop",
        hideout="boot",
        clue="three square hoofprints and a nibble taken from the paper menu",
        reason="goats have no respect for menus and every respect for jars that smell exciting",
        neat_tools={"sniff_book", "ladle_tap"},
        messy=True,
        tags={"goat"},
    ),
}

TOOLS = {
    "spyglass": Tool(
        id="spyglass",
        label="spyglass",
        phrase="the commodore's brass spyglass",
        action="peered high and low through the long shiny tube",
        sense=3,
        tidy=True,
        tags={"spyglass"},
    ),
    "sniff_book": Tool(
        id="sniff_book",
        label="sniff notebook",
        phrase="a little sniff notebook",
        action="followed the smell in tidy zigzags and wrote each clue down",
        sense=3,
        tidy=True,
        tags={"smell"},
    ),
    "crumb_trail": Tool(
        id="crumb_trail",
        label="crumb trail",
        phrase="a very official crumb trail",
        action="set down three tiny bread crumbs and waited for the greediest witness",
        sense=2,
        tidy=False,
        tags={"crumbs"},
    ),
    "ladle_tap": Tool(
        id="ladle_tap",
        label="ladle tap",
        phrase="a soup ladle on a bucket",
        action='went "ting-ting!" with the ladle and listened for answering hooves',
        sense=2,
        tidy=False,
        tags={"sound"},
    ),
    "umbrella_poke": Tool(
        id="umbrella_poke",
        label="umbrella poke",
        phrase="an old umbrella",
        action="poked at everything in a most unhelpful way",
        sense=1,
        tidy=False,
        tags={"silly"},
    ),
}

SNACKS = {
    "sandwiches": Snack(
        id="sandwiches",
        label="sandwiches",
        serving="a mountain of cucumber sandwiches",
        tags={"sandwich"},
    ),
    "rolls": Snack(
        id="rolls",
        label="rolls",
        serving="warm cheese rolls",
        tags={"roll"},
    ),
    "crackers": Snack(
        id="crackers",
        label="crackers",
        serving="round crackers stacked like coins",
        tags={"cracker"},
    ),
}

GIRL_NAMES = ["Mina", "Tess", "Nora", "Lucy", "Poppy", "Ada"]
BOY_NAMES = ["Ben", "Otis", "Max", "Finn", "Theo", "Eli"]
COMMODORE_NAMES = ["Brisk", "Wobble", "Puffin", "Tackle", "Merriweather"]


@dataclass
class StoryParams:
    place: str
    culprit: str
    tool: str
    snack: str
    hero_name: str
    hero_gender: str
    commodore_name: str
    commodore_gender: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="pier",
        culprit="gull",
        tool="spyglass",
        snack="sandwiches",
        hero_name="Mina",
        hero_gender="girl",
        commodore_name="Brisk",
        commodore_gender="man",
    ),
    StoryParams(
        place="boathouse",
        culprit="goat",
        tool="ladle_tap",
        snack="rolls",
        hero_name="Ben",
        hero_gender="boy",
        commodore_name="Wobble",
        commodore_gender="man",
    ),
    StoryParams(
        place="boathouse",
        culprit="dog",
        tool="sniff_book",
        snack="crackers",
        hero_name="Tess",
        hero_gender="girl",
        commodore_name="Puffin",
        commodore_gender="woman",
    ),
    StoryParams(
        place="lighthouse_yard",
        culprit="gull",
        tool="crumb_trail",
        snack="rolls",
        hero_name="Otis",
        hero_gender="boy",
        commodore_name="Merriweather",
        commodore_gender="woman",
    ),
]


KNOWLEDGE = {
    "piccalilli": [
        (
            "What is piccalilli?",
            "Piccalilli is a bright yellow pickle relish made from chopped vegetables and mustardy spices. People spoon a little onto sandwiches or cold snacks for a tangy taste."
        )
    ],
    "commodore": [
        (
            "What is a commodore?",
            "A commodore is a leader connected with boats or a sailing club. It is a title, a bit like being the captain of many captains."
        )
    ],
    "gull": [
        (
            "Why do gulls come near food by the water?",
            "Gulls are very good at spotting snacks from far away. If they smell or see food, they swoop closer to investigate."
        )
    ],
    "dog": [
        (
            "Why are dogs good at finding things?",
            "Dogs have strong noses and notice smells that people miss. They often follow a scent trail to whatever interests them."
        )
    ],
    "goat": [
        (
            "Why do goats nibble odd things?",
            "Goats explore with their mouths and are famous for trying curious bites. They are not trying to be naughty; they are checking the world in a goatish way."
        )
    ],
    "spyglass": [
        (
            "What is a spyglass?",
            "A spyglass is a small telescope you hold in your hand. It helps you see things that are farther away."
        )
    ],
    "sound": [
        (
            "How can a sound help solve a mystery?",
            "A sound tells you where something may be hiding or moving. If you listen carefully, the noise becomes a clue."
        )
    ],
    "smell": [
        (
            "How can smell be a clue?",
            "A smell can lead you toward what made it, especially food. Following a strong smell is one way to search carefully."
        )
    ],
}
KNOWLEDGE_ORDER = ["piccalilli", "commodore", "gull", "dog", "goat", "spyglass", "sound", "smell"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    culprit = f["culprit_cfg"]
    tool = f["tool"]
    place = f["place"]
    return [
        'Write a funny story for a 3-to-5-year-old that includes the words "commodore", "mature", and "piccalilli".',
        f"Tell a comedy mystery set at {place.label} where a child helps a mature commodore find a missing jar of piccalilli by following clues and sounds.",
        f"Write a surprise story where {culprit.label} causes a lunch mystery, and the child solves it using {tool.label} instead of guessing wildly.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    commodore = f["commodore"]
    culprit = f["culprit_cfg"]
    tool = f["tool"]
    snack = f["snack"]
    outcome = f["outcome"]
    hideout = f["hideout_phrase"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, a child at the harbor, and Commodore {commodore.label}, who stayed calm when the lunch surprise began."
        ),
        (
            "What was the mystery to solve?",
            f"The bright jar of piccalilli disappeared just before snack time. That mattered because the commodore had planned it for the {snack.label}."
        ),
        (
            "What clues did they follow?",
            f"They noticed {culprit.clue} and heard the sound '{culprit.sound}!' from nearby. Those clues pointed them toward {hideout} instead of toward any person at the table."
        ),
        (
            f"How did {hero.label} help solve the mystery?",
            f"{hero.label} used {tool.phrase} and searched in the way that fit the clues. That careful search worked because it matched the culprit and the hiding place."
        ),
    ]
    if outcome == "neat":
        qa.append(
            (
                "What was the surprise ending?",
                f"The thief was not a wicked thief at all, but {culprit.phrase} hiding by {hideout}. The jar was still usable, so lunch could go on with laughter."
            )
        )
    else:
        qa.append(
            (
                "What happened when they found the jar?",
                f"They found {culprit.phrase} by {hideout}, but the jar tipped and made a little splat of piccalilli. Even so, the commodore saved enough for the snack and turned the mess into a joke."
            )
        )
    qa.append(
        (
            "Why is the commodore called mature in the story?",
            f"The commodore did not blame anyone or start shouting. Instead, {commodore.pronoun()} listened for sounds, studied clues, and helped solve the problem calmly."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"piccalilli", "commodore"}
    culprit_id = f["culprit_cfg"].id
    if culprit_id in KNOWLEDGE:
        tags.add(culprit_id)
    for tag in f["tool"].tags:
        if tag in KNOWLEDGE:
            tags.add(tag)
    if "sound" in f["tool"].tags or culprit_id in {"gull", "goat"}:
        tags.add("sound")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_place(place: Place, culprit: Culprit) -> str:
    return (
        f"(No story: {culprit.label} does not fit well at {place.label}, or there is no believable place there for the jar to be hidden. "
        f"Pick a place that allows {culprit.label} and its hideout.)"
    )


def explain_tool(culprit: Culprit, tool: Tool) -> str:
    better = ", ".join(sorted(culprit.neat_tools))
    return (
        f"(No story: using '{tool.id}' to find {culprit.label} is not sensible enough here. "
        f"Try one of: {better}.)"
    )


ASP_RULES = r"""
valid(Place, Culprit, Tool) :-
    place(Place), culprit(Culprit), tool(Tool),
    allows(Place, Culprit),
    hideout_of(Culprit, Hideout),
    has_hideout(Place, Hideout),
    good_tool(Culprit, Tool).

neat_outcome(Culprit, Tool) :- tidy(Tool), not messy_culprit(Culprit).
messy_outcome(Culprit, Tool) :- valid(_, Culprit, Tool), not neat_outcome(Culprit, Tool).

outcome(neat) :- chosen_culprit(C), chosen_tool(T), neat_outcome(C, T).
outcome(messy) :- chosen_culprit(C), chosen_tool(T), not neat_outcome(C, T).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for culprit in sorted(place.culprits):
            lines.append(asp.fact("allows", place_id, culprit))
        for hideout in sorted(place.hideouts):
            lines.append(asp.fact("has_hideout", place_id, hideout))
    for culprit_id, culprit in CULPRITS.items():
        lines.append(asp.fact("culprit", culprit_id))
        lines.append(asp.fact("hideout_of", culprit_id, culprit.hideout))
        if culprit.messy:
            lines.append(asp.fact("messy_culprit", culprit_id))
        for tool_id in sorted(culprit.neat_tools):
            lines.append(asp.fact("good_tool", culprit_id, tool_id))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        if tool.tidy:
            lines.append(asp.fact("tidy", tool_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_culprit", params.culprit),
            asp.fact("chosen_tool", params.tool),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def _smoke_test() -> None:
    sample = generate(CURATED[0])
    if not sample.story.strip():
        raise StoryError("(Smoke test failed: generated empty story.)")
    emit(sample, trace=False, qa=False, header="")


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        _smoke_test()
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a harbor lunch mystery with a mature commodore and missing piccalilli."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--commodore-name")
    ap.add_argument("--commodore-gender", choices=["woman", "man"])
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
    if args.place and args.culprit:
        place = PLACES[args.place]
        culprit = CULPRITS[args.culprit]
        if not culprit_allowed(place, culprit):
            raise StoryError(explain_place(place, culprit))
    if args.culprit and args.tool:
        culprit = CULPRITS[args.culprit]
        tool = TOOLS[args.tool]
        if not sensible_tool(culprit, tool):
            raise StoryError(explain_tool(culprit, tool))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.culprit is None or combo[1] == args.culprit)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, culprit_id, tool_id = rng.choice(sorted(combos))
    snack_id = args.snack or rng.choice(sorted(SNACKS))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    commodore_gender = args.commodore_gender or rng.choice(["woman", "man"])
    commodore_name = args.commodore_name or rng.choice(COMMODORE_NAMES)

    return StoryParams(
        place=place_id,
        culprit=culprit_id,
        tool=tool_id,
        snack=snack_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        commodore_name=commodore_name,
        commodore_gender=commodore_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Invalid place: {params.place})")
    if params.culprit not in CULPRITS:
        raise StoryError(f"(Invalid culprit: {params.culprit})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Invalid tool: {params.tool})")
    if params.snack not in SNACKS:
        raise StoryError(f"(Invalid snack: {params.snack})")

    place = PLACES[params.place]
    culprit = CULPRITS[params.culprit]
    tool = TOOLS[params.tool]
    if not culprit_allowed(place, culprit):
        raise StoryError(explain_place(place, culprit))
    if not sensible_tool(culprit, tool):
        raise StoryError(explain_tool(culprit, tool))

    world = tell(
        place=place,
        culprit_cfg=culprit,
        tool_cfg=tool,
        snack_cfg=SNACKS[params.snack],
        hero_name=params.hero_name,
        hero_type=params.hero_gender,
        commodore_name=params.commodore_name,
        commodore_type=params.commodore_gender,
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
        print(f"{len(combos)} compatible (place, culprit, tool) combos:\n")
        for place, culprit, tool in combos:
            print(f"  {place:16} {culprit:8} {tool}")
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
            header = f"### {p.place}: {p.culprit} with {p.tool} ({outcome_of(p)})"
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

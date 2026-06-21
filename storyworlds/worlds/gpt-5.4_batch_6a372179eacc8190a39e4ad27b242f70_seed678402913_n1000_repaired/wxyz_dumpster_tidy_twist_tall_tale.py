#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/wxyz_dumpster_tidy_twist_tall_tale.py
================================================================

A standalone story world for a tall-tale cleanup story built from the seed
words "wxyz", "dumpster", and "tidy", with a clear twist. The domain is small:
a child finds a wild mess beside a big dumpster, imagines something enormous
making the racket inside it, and then discovers a surprising, harmless truth.
The cleanup itself is simulation-driven: different kinds of scattered mess call
for different tools, and the story only exists when the chosen tool can
reasonably gather that mess.

Run it
------
    python storyworlds/worlds/gpt-5.4/wxyz_dumpster_tidy_twist_tall_tale.py
    python storyworlds/worlds/gpt-5.4/wxyz_dumpster_tidy_twist_tall_tale.py --place fairground --mess paper_bits
    python storyworlds/worlds/gpt-5.4/wxyz_dumpster_tidy_twist_tall_tale.py --tool magnet   # rejected for paper
    python storyworlds/worlds/gpt-5.4/wxyz_dumpster_tidy_twist_tall_tale.py --all
    python storyworlds/worlds/gpt-5.4/wxyz_dumpster_tidy_twist_tall_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/wxyz_dumpster_tidy_twist_tall_tale.py --verify
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
    traits: list[str] = field(default_factory=list)
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    opening: str
    image: str
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Mess:
    id: str
    label: str
    phrase: str
    plural_noun: str
    material: str
    amount: int
    tumble: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    handles: set[str] = field(default_factory=set)
    power: int = 1
    sweep: str = ""
    finish: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Twist:
    id: str
    label: str
    clue: str
    reveal: str
    banner_use: str
    place_ok: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
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


def _r_gathered_becomes_tidy(world: World) -> list[str]:
    mess = world.get("mess")
    lot = world.get("lot")
    if mess.meters["gathered"] < THRESHOLD:
        return []
    sig = ("tidy", mess.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    lot.meters["tidy"] += 1
    return ["__tidy__"]


def _r_noise_causes_awe(world: World) -> list[str]:
    hero = world.get("hero")
    if hero.memes["startled"] < THRESHOLD:
        return []
    sig = ("awe", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["awe"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="gathered_becomes_tidy", tag="physical", apply=_r_gathered_becomes_tidy),
    Rule(name="noise_causes_awe", tag="emotion", apply=_r_noise_causes_awe),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tool_fits(tool: Tool, mess: Mess) -> bool:
    return mess.material in tool.handles


def twist_fits(place: Place, twist: Twist) -> bool:
    return place.id in twist.place_ok


def success(tool: Tool, mess: Mess) -> bool:
    return tool.power >= mess.amount


def valid_combo(place_id: str, mess_id: str, tool_id: str, twist_id: str) -> bool:
    place = PLACES[place_id]
    mess = MESSES[mess_id]
    tool = TOOLS[tool_id]
    twist = TWISTS[twist_id]
    return (
        mess_id in place.affords
        and tool_fits(tool, mess)
        and twist_fits(place, twist)
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for mess_id in sorted(place.affords):
            mess = MESSES[mess_id]
            for tool_id, tool in TOOLS.items():
                if not tool_fits(tool, mess):
                    continue
                for twist_id, twist in TWISTS.items():
                    if twist_fits(place, twist):
                        combos.append((place_id, mess_id, tool_id, twist_id))
    return combos


def outcome_of(params: "StoryParams") -> str:
    if not valid_combo(params.place, params.mess, params.tool, params.twist):
        raise StoryError("(No valid story: the place, mess, tool, and twist do not fit together.)")
    return "gleaming" if success(TOOLS[params.tool], MESSES[params.mess]) else "patchy"


def predict_cleanup(world: World, tool: Tool) -> dict:
    sim = world.copy()
    do_cleanup(sim, tool, narrate=False)
    lot = sim.get("lot")
    return {
        "tidy": lot.meters["tidy"] >= THRESHOLD,
        "leftover": sim.get("mess").meters["scattered"],
    }


def introduce(world: World, hero: Entity, place: Place, parent: Entity) -> None:
    hero.memes["pride"] += 1
    world.say(
        f"{hero.id} was the kind of little {hero.type} who believed even a broom straw could become a legend if it worked hard enough."
    )
    world.say(
        f"One bright day, {hero.id} went with {hero.pronoun('possessive')} {parent.label_word} to {place.label}. "
        f"{place.opening} {place.image}"
    )


def spot_mess(world: World, hero: Entity, mess: Mess) -> None:
    world.get("mess").meters["scattered"] = float(mess.amount)
    world.say(
        f"Beside the old dumpster lay {mess.phrase}. They had blown and tumbled so far that they looked big enough to keep a whole town from ever becoming tidy."
    )
    world.say(
        f'"I can fix that," said {hero.id}, puffing up as tall as a fence post in {hero.pronoun("possessive")} own mind.'
    )


def rumble(world: World, hero: Entity, twist: Twist) -> None:
    hero.memes["startled"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Just then the dumpster gave a clang and a wobble. {twist.clue}"
    )
    world.say(
        f"{hero.id} squinted hard and guessed that something as large as a hill might be hiding in there."
    )


def choose_tool(world: World, hero: Entity, tool: Tool, mess: Mess) -> None:
    pred = predict_cleanup(world, tool)
    world.facts["predicted_tidy"] = pred["tidy"]
    world.say(
        f"But tall-tale children do not run from a rattle. {hero.id} grabbed {tool.phrase} and marched toward the mess."
    )
    if pred["tidy"]:
        world.say(
            f"{hero.pronoun().capitalize()} had a feeling {tool.label} could gather every last bit of {mess.plural_noun} before lunchtime sneezed into supper."
        )
    else:
        world.say(
            f"{hero.pronoun().capitalize()} hoped {tool.label} would be enough, though the mess looked deeper than a dragon's pockets."
        )


def do_cleanup(world: World, tool: Tool, narrate: bool = True) -> None:
    mess = world.get("mess")
    taken = min(float(tool.power), mess.meters["scattered"])
    if taken <= 0:
        return
    mess.meters["scattered"] -= taken
    mess.meters["gathered"] += taken
    world.get("hero").memes["effort"] += 1
    if mess.meters["scattered"] <= 0:
        mess.meters["scattered"] = 0.0
    propagate(world, narrate=narrate)


def boastful_cleanup(world: World, hero: Entity, tool: Tool, mess: Mess) -> None:
    do_cleanup(world, tool, narrate=False)
    world.say(tool.sweep)
    if world.get("lot").meters["tidy"] >= THRESHOLD:
        hero.memes["relief"] += 1
        hero.memes["joy"] += 1
        world.say(
            f"In no time at all, the ground beside the dumpster looked so tidy that even the wind seemed to stop and stare."
        )
    else:
        hero.memes["worry"] += 1
        world.say(
            f"A good deal of the mess was caught, but a few stubborn pieces still skittered about like they had tiny shoes on."
        )


def reveal_twist(world: World, hero: Entity, parent: Entity, twist: Twist) -> None:
    hero.memes["fear"] = 0.0
    hero.memes["wonder"] += 1
    world.say(
        f"Then the lid tipped higher, and out came the truth. {twist.reveal}"
    )
    world.say(
        f'{parent.label_word.capitalize()} laughed softly. "So that was the great racket," {parent.pronoun()} said.'
    )


def finish(world: World, hero: Entity, parent: Entity, mess: Mess, tool: Tool, twist: Twist) -> None:
    lot = world.get("lot")
    if lot.meters["tidy"] >= THRESHOLD:
        world.say(
            f"{hero.id} used the funny treasure from the dumpster to {twist.banner_use}. Right across the front marched the letters wxyz, proud as parade horses."
        )
        world.say(
            f"When they stepped back, {parent.label_word} said the place looked so neat that a mayor might have tried to rent it for a moon picnic."
        )
        world.say(
            f"{mess.ending} {tool.finish}"
        )
    else:
        world.say(
            f"{hero.id} still used the funny treasure from the dumpster to {twist.banner_use}, and the bright wxyz letters made the half-tidy corner look brave instead of beaten."
        )
        world.say(
            f"{parent.label_word.capitalize()} promised they would finish the last bits together with one more trip and one more laugh."
        )


def tell(
    place: Place,
    mess: Mess,
    tool: Tool,
    twist: Twist,
    hero_name: str = "Tess",
    hero_type: str = "girl",
    parent_type: str = "mother",
    hero_trait: str = "plucky",
) -> World:
    world = World(place)
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_type,
        label=hero_name,
        phrase=hero_name,
        role="hero",
        traits=[hero_trait],
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label="the parent",
        phrase="the parent",
        role="parent",
    ))
    lot = world.add(Entity(
        id="lot",
        kind="thing",
        type="place",
        label=place.label,
        phrase=place.label,
    ))
    mess_ent = world.add(Entity(
        id="mess",
        kind="thing",
        type="mess",
        label=mess.label,
        phrase=mess.phrase,
        tags=set(mess.tags),
    ))
    tool_ent = world.add(Entity(
        id="tool",
        kind="thing",
        type="tool",
        label=tool.label,
        phrase=tool.phrase,
        tags=set(tool.tags),
    ))
    dump_ent = world.add(Entity(
        id="dumpster",
        kind="thing",
        type="dumpster",
        label="dumpster",
        phrase="the old dumpster",
        tags={"dumpster"},
    ))

    introduce(world, hero, place, parent)
    spot_mess(world, hero, mess)

    world.para()
    rumble(world, hero, twist)
    choose_tool(world, hero, tool, mess)
    boastful_cleanup(world, hero, tool, mess)

    world.para()
    reveal_twist(world, hero, parent, twist)
    finish(world, hero, parent, mess, tool, twist)

    world.facts.update(
        hero=hero,
        parent=parent,
        place=place,
        mess_cfg=mess,
        tool_cfg=tool,
        twist_cfg=twist,
        lot=lot,
        mess=mess_ent,
        tool=tool_ent,
        dumpster=dump_ent,
        tidy=lot.meters["tidy"] >= THRESHOLD,
        outcome="gleaming" if lot.meters["tidy"] >= THRESHOLD else "patchy",
    )
    hero.label = hero_name
    parent.label = "the parent"
    return world


PLACES = {
    "fairground": Place(
        id="fairground",
        label="the fairground lot",
        opening="The grand field spread out wider than a yawn from the sky itself.",
        image="Stray streamers, crooked crates, and a red dumpster stood near the gate like leftover pieces from yesterday's parade.",
        affords={"paper_bits", "tin_lids"},
        tags={"fairground"},
    ),
    "alley": Place(
        id="alley",
        label="the market alley",
        opening="The alley stretched so long that two echoes could play tag in it before breakfast.",
        image="Beside the bakery wall sat a dented dumpster with room enough, it seemed, for three thunderstorms and a wagon.",
        affords={"paper_bits", "apple_cores"},
        tags={"alley"},
    ),
    "riverside": Place(
        id="riverside",
        label="the riverside landing",
        opening="The riverbank ran silver and wide, and the boards of the landing popped in the sun.",
        image="Near the supply shed hunkered a blue dumpster, big as a sleepy whale and twice as grumbly.",
        affords={"tin_lids", "apple_cores"},
        tags={"riverside"},
    ),
}

MESSES = {
    "paper_bits": Mess(
        id="paper_bits",
        label="paper scraps",
        phrase="paper scraps and ribbon bits",
        plural_noun="paper scraps",
        material="light",
        amount=2,
        tumble="whipped through the air like tiny pale fish",
        ending="The ribbons stopped wriggling, the paper scraps sat still, and the whole place looked ready for company.",
        tags={"paper", "tidy"},
    ),
    "tin_lids": Mess(
        id="tin_lids",
        label="tin lids",
        phrase="tin lids and bottle caps",
        plural_noun="tin lids",
        material="metal",
        amount=3,
        tumble="clinked and flashed in the sun",
        ending="The shiny bits quit clattering, and the quiet that followed felt neat enough to fold and keep in a pocket.",
        tags={"metal", "tidy"},
    ),
    "apple_cores": Mess(
        id="apple_cores",
        label="apple cores",
        phrase="apple cores and squashed peels",
        plural_noun="apple cores",
        material="crumbly",
        amount=2,
        tumble="rolled and bobbled along the ground",
        ending="The peels were gone, the flies moved on, and the clean little corner smelled like fresh air again.",
        tags={"food", "tidy"},
    ),
}

TOOLS = {
    "broom": Tool(
        id="broom",
        label="broom",
        phrase="a broom with a handle long enough to poke a cloud",
        handles={"light"},
        power=2,
        sweep="With one sweep, then another, the broom herded the scraps into a pile as if it had been born knowing parade manners.",
        finish="Even the dumpster seemed pleased to stand guard over such order.",
        tags={"broom"},
    ),
    "magnet": Tool(
        id="magnet",
        label="magnet cart",
        phrase="a magnet cart that hummed like a sleepy bee",
        handles={"metal"},
        power=3,
        sweep="The magnet cart rolled forward, and every tin lid skipped after it with little metallic hops, as obedient as ducklings.",
        finish="The ground gleamed where the clatter had been.",
        tags={"magnet"},
    ),
    "rake": Tool(
        id="rake",
        label="rake",
        phrase="a rake with teeth stout enough to comb a hedgehog",
        handles={"crumbly", "light"},
        power=2,
        sweep="The rake scratched once, twice, and then gathered the mess into a striped little hill by the dumpster.",
        finish="Not a peel dared stay behind.",
        tags={"rake"},
    ),
}

TWISTS = {
    "banner": Twist(
        id="banner",
        label="alphabet banner",
        clue="Something inside rustled and thumped as if a giant were sneezing into a brass drum.",
        reveal="It was only a rolled parade banner trapped under a loose crate. When the cloth sprang open, it flashed the letters wxyz in paint as tall as puppies.",
        banner_use="tie the banner across the cleaned space like a victory flag",
        place_ok={"fairground", "alley"},
        tags={"letters", "wxyz"},
    ),
    "kites": Twist(
        id="kites",
        label="kite bundle",
        clue="A stringy flapping came from inside, like wings practicing for a storm.",
        reveal="It was a bunch of lost kites caught on a bent chair. One kite tail spelled wxyz, and the whole bundle came fluttering out like cheerful birds.",
        banner_use="hang the kite tail where everyone could see it",
        place_ok={"fairground", "riverside"},
        tags={"letters", "wxyz"},
    ),
    "sign": Twist(
        id="sign",
        label="school sign",
        clue="A hollow bumping echoed from the dumpster, as if wooden shoes were dancing in there.",
        reveal="It was an old signboard knocking against the side. Painted across it, in crooked but brave letters, were wxyz from some long-ago lesson day.",
        banner_use="lean the sign by the neat corner like the name of a tiny kingdom",
        place_ok={"alley", "riverside"},
        tags={"letters", "wxyz"},
    ),
}


GIRL_NAMES = ["Tess", "Mabel", "Ivy", "Nell", "Ruby", "Dora", "June", "Poppy"]
BOY_NAMES = ["Hank", "Otis", "Beau", "Jesse", "Cal", "Eli", "Wade", "Milo"]
TRAITS = ["plucky", "cheerful", "stout-hearted", "busy", "determined", "brisk"]


@dataclass
class StoryParams:
    place: str
    mess: str
    tool: str
    twist: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "dumpster": [
        (
            "What is a dumpster?",
            "A dumpster is a big trash container people use to hold lots of garbage and scraps. It often has a heavy lid and can make loud clanging sounds."
        )
    ],
    "tidy": [
        (
            "What does tidy mean?",
            "Tidy means neat and put in order instead of scattered around. A tidy place is easier to use and nicer to look at."
        )
    ],
    "broom": [
        (
            "What is a broom good for?",
            "A broom is good for sweeping light things like dust, paper bits, and crumbs into a pile. It works best on things that can be pushed along the ground."
        )
    ],
    "magnet": [
        (
            "What does a magnet pick up?",
            "A magnet pulls certain metal things toward itself. That makes it useful for collecting bits of metal without touching each one by hand."
        )
    ],
    "rake": [
        (
            "What is a rake for?",
            "A rake has teeth that can pull leaves, peels, and other loose things into a pile. It is handy for gathering messy bits from the ground."
        )
    ],
    "wxyz": [
        (
            "What are wxyz?",
            "W, X, Y, and Z are the last four letters of the English alphabet. People sometimes use them on signs, songs, or banners when they want to show the end of the alphabet."
        )
    ],
}
KNOWLEDGE_ORDER = ["dumpster", "tidy", "broom", "magnet", "rake", "wxyz"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    place = f["place"]
    mess = f["mess_cfg"]
    tool = f["tool_cfg"]
    twist = f["twist_cfg"]
    return [
        f'Write a short tall tale for a 3-to-5-year-old that includes the words "wxyz", "dumpster", and "tidy".',
        f"Tell a playful tall tale where a child named {hero.label} cleans {place.label} with {tool.phrase} after finding {mess.phrase} beside a dumpster, then learns the scary noise was really {twist.label}.",
        f"Write a story with a twist ending in which a child bravely tidies a messy place and the surprising thing from the dumpster becomes part of the happy final image.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    place = f["place"]
    mess = f["mess_cfg"]
    tool = f["tool_cfg"]
    twist = f["twist_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about a child named {hero.label} and {hero.pronoun('possessive')} {parent.label_word} at {place.label}. The story follows {hero.label} as {hero.pronoun()} tries to make the messy place tidy."
        ),
        (
            "What was messy beside the dumpster?",
            f"There were {mess.phrase} beside the dumpster. They were scattered so widely that the mess looked huge in the tall-tale way."
        ),
        (
            f"Why did {hero.label} think something big was in the dumpster?",
            f"{hero.label} heard the dumpster clang and wobble, so {hero.pronoun()} imagined something enormous was hiding inside. The noisy clue made an ordinary sound feel giant and mysterious."
        ),
        (
            f"How did {hero.label} try to clean the mess?",
            f"{hero.pronoun().capitalize()} used {tool.phrase} to gather the {mess.plural_noun}. That tool fit the kind of mess on the ground, which is why the cleanup could really work."
        ),
        (
            "What was the twist?",
            f"The frightening racket was not a monster at all. {twist.reveal}"
        ),
    ]
    if outcome == "gleaming":
        qa.append(
            (
                "How did the story end?",
                f"It ended with the place looking truly tidy. The letters wxyz became part of the final picture, which turned the noisy surprise into a cheerful decoration."
            )
        )
    else:
        qa.append(
            (
                "Did the child finish the whole cleanup alone?",
                f"Not quite. {hero.label} made the place much tidier, but a few bits still remained, so {parent.label_word} promised to help finish. The twist still changed the mood from scary to cheerful."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"dumpster", "tidy", "wxyz"}
    tool = f["tool_cfg"]
    if tool.id in KNOWLEDGE:
        tags.add(tool.id)
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
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="fairground",
        mess="paper_bits",
        tool="broom",
        twist="banner",
        name="Tess",
        gender="girl",
        parent="mother",
        trait="plucky",
    ),
    StoryParams(
        place="riverside",
        mess="tin_lids",
        tool="magnet",
        twist="kites",
        name="Hank",
        gender="boy",
        parent="father",
        trait="determined",
    ),
    StoryParams(
        place="alley",
        mess="apple_cores",
        tool="rake",
        twist="sign",
        name="Ruby",
        gender="girl",
        parent="mother",
        trait="busy",
    ),
    StoryParams(
        place="riverside",
        mess="apple_cores",
        tool="rake",
        twist="sign",
        name="Otis",
        gender="boy",
        parent="father",
        trait="cheerful",
    ),
    StoryParams(
        place="fairground",
        mess="tin_lids",
        tool="magnet",
        twist="banner",
        name="June",
        gender="girl",
        parent="mother",
        trait="brisk",
    ),
]


def explain_tool(tool_id: str, mess_id: str) -> str:
    tool = TOOLS[tool_id]
    mess = MESSES[mess_id]
    return (
        f"(No story: {tool.label} does not sensibly gather {mess.plural_noun}. "
        f"Pick a tool that handles {mess.material} mess.)"
    )


def explain_place(place_id: str, mess_id: str) -> str:
    place = PLACES[place_id]
    mess = MESSES[mess_id]
    return (
        f"(No story: {place.label} is not set up for {mess.phrase}. "
        f"Choose a mess the place can plausibly have.)"
    )


def explain_twist(place_id: str, twist_id: str) -> str:
    place = PLACES[place_id]
    twist = TWISTS[twist_id]
    return (
        f"(No story: the twist '{twist.label}' does not fit {place.label}. "
        f"Pick a twist that belongs in that place.)"
    )


ASP_RULES = r"""
available(Place, Mess) :- place(Place), mess(Mess), affords(Place, Mess).
tool_fits(Tool, Mess) :- tool(Tool), mess(Mess), material(Mess, Mat), handles(Tool, Mat).
twist_fits(Place, Twist) :- place(Place), twist(Twist), place_ok(Twist, Place).

valid(Place, Mess, Tool, Twist) :-
    available(Place, Mess),
    tool_fits(Tool, Mess),
    twist_fits(Place, Twist).

gleaming(Tool, Mess) :-
    tool(Tool), mess(Mess),
    power(Tool, P), amount(Mess, A), P >= A.

outcome(gleaming) :- chosen_tool(T), chosen_mess(M), gleaming(T, M).
outcome(patchy) :- chosen_tool(T), chosen_mess(M), not gleaming(T, M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for mess_id in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, mess_id))
    for mess_id, mess in MESSES.items():
        lines.append(asp.fact("mess", mess_id))
        lines.append(asp.fact("material", mess_id, mess.material))
        lines.append(asp.fact("amount", mess_id, mess.amount))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("power", tool_id, tool.power))
        for material in sorted(tool.handles):
            lines.append(asp.fact("handles", tool_id, material))
    for twist_id, twist in TWISTS.items():
        lines.append(asp.fact("twist", twist_id))
        for place_id in sorted(twist.place_ok):
            lines.append(asp.fact("place_ok", twist_id, place_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_tool", params.tool),
        asp.fact("chosen_mess", params.mess),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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
    for s in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)

    bad = 0
    for params in cases:
        py = outcome_of(params)
        cl = asp_outcome(params)
        if py != cl:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Smoke test failed: generated empty story.")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Tall-tale cleanup world: a child tidies a messy place beside a dumpster and discovers a twist."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mess", choices=MESSES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.mess and args.mess not in PLACES[args.place].affords:
        raise StoryError(explain_place(args.place, args.mess))
    if args.tool and args.mess and not tool_fits(TOOLS[args.tool], MESSES[args.mess]):
        raise StoryError(explain_tool(args.tool, args.mess))
    if args.place and args.twist and not twist_fits(PLACES[args.place], TWISTS[args.twist]):
        raise StoryError(explain_twist(args.place, args.twist))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.mess is None or combo[1] == args.mess)
        and (args.tool is None or combo[2] == args.tool)
        and (args.twist is None or combo[3] == args.twist)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, mess_id, tool_id, twist_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(name_pool)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        mess=mess_id,
        tool=tool_id,
        twist=twist_id,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Invalid place: {params.place})")
    if params.mess not in MESSES:
        raise StoryError(f"(Invalid mess: {params.mess})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Invalid tool: {params.tool})")
    if params.twist not in TWISTS:
        raise StoryError(f"(Invalid twist: {params.twist})")
    if not valid_combo(params.place, params.mess, params.tool, params.twist):
        raise StoryError("(No valid story: the chosen place, mess, tool, and twist do not make sense together.)")

    world = tell(
        place=PLACES[params.place],
        mess=MESSES[params.mess],
        tool=TOOLS[params.tool],
        twist=TWISTS[params.twist],
        hero_name=params.name,
        hero_type=params.gender,
        parent_type=params.parent,
        hero_trait=params.trait,
    )

    world.get("hero").label = params.name

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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, mess, tool, twist) combos:\n")
        for place_id, mess_id, tool_id, twist_id in combos:
            print(f"  {place_id:10} {mess_id:12} {tool_id:8} {twist_id}")
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
            header = f"### {p.name}: {p.mess} at {p.place} with {p.tool} ({outcome_of(p)})"
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

#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/yelp_friendship_kindness_surprise_folk_tale.py
=========================================================================

A standalone story world about small woodland friends in a folk-tale mood.

The seed asks for:
- the word "yelp"
- Friendship
- Kindness
- Surprise
- a folk-tale style

This world models a simple tale shape:

    a little friend sets out through a humble place,
    hears a yelp,
    finds another friend in trouble,
    solves the trouble with the one fitting kindness,
    and later receives a gentle surprise that proves kindness traveled onward.

Run it
------
    python storyworlds/worlds/gpt-5.4/yelp_friendship_kindness_surprise_folk_tale.py
    python storyworlds/worlds/gpt-5.4/yelp_friendship_kindness_surprise_folk_tale.py --trouble thorn --aid salve
    python storyworlds/worlds/gpt-5.4/yelp_friendship_kindness_surprise_folk_tale.py --aid bun --trouble cold
    python storyworlds/worlds/gpt-5.4/yelp_friendship_kindness_surprise_folk_tale.py --all
    python storyworlds/worlds/gpt-5.4/yelp_friendship_kindness_surprise_folk_tale.py --qa
    python storyworlds/worlds/gpt-5.4/yelp_friendship_kindness_surprise_folk_tale.py --verify
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

# Make the shared result containers importable when this script is run directly
# from the repo root or from this nested directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
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
        female = {"girl", "mother", "hen"}
        male = {"boy", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


# ---------------------------------------------------------------------------
# Domain configs
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    id: str = ""
    place: str = ""
    path: str = ""
    image: str = ""
    surprise_spot: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Trouble:
    id: str = ""
    friend_type: str = ""
    friend_label: str = ""
    yelp_line: str = ""
    cause: str = ""
    need: str = ""
    pain_meter: str = ""
    relief_line: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str = ""
    label: str = ""
    phrase: str = ""
    fixes: str = ""
    method: str = ""
    result: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Surprise:
    id: str = ""
    label: str = ""
    phrase: str = ""
    fits: set[str] = field(default_factory=set)
    reveal: str = ""
    gift_line: str = ""
    ending: str = ""
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# Per-world params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    trouble: str
    aid: str
    surprise: str
    hero_name: str
    hero_type: str
    hero_trait: str
    parent_type: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "pinewood": Setting(
        id="pinewood",
        place="the pinewood path",
        path="under tall pines where soft needles covered the ground",
        image="The trees stood like old keepers with green hoods on their heads.",
        surprise_spot="the hollow stump",
        tags={"forest"},
    ),
    "riverside": Setting(
        id="riverside",
        place="the riverside lane",
        path="beside the bright river where reeds bowed in the breeze",
        image="The river flashed like a silver ribbon in the morning sun.",
        surprise_spot="the flat stone by the reeds",
        tags={"river"},
    ),
    "hillmeadow": Setting(
        id="hillmeadow",
        place="the hill meadow track",
        path="through the high grass where buttercups nodded at every step",
        image="The hill wore a yellow shawl of flowers.",
        surprise_spot="the old standing stone",
        tags={"meadow"},
    ),
}

TROUBLES = {
    "thorn": Trouble(
        id="thorn",
        friend_type="hedgehog",
        friend_label="a little hedgehog",
        yelp_line='"Yelp!" cried a little hedgehog from the blackberry tangle.',
        cause="A sharp thorn was caught in the hedgehog's paw.",
        need="the paw needed gentle tending",
        pain_meter="pain",
        relief_line="Soon the hedgehog could set the sore paw down again without wincing.",
        tags={"thorn", "hurt"},
    ),
    "cold": Trouble(
        id="cold",
        friend_type="duck",
        friend_label="a small duck",
        yelp_line='"Yelp!" came a small duck from the windy bank.',
        cause="The duck was soaked through and shivering in the cold breeze.",
        need="the duck needed warmth",
        pain_meter="cold",
        relief_line="Soon the shivers slowed, and the duck tucked warm feet beneath a quiet body.",
        tags={"cold", "weather"},
    ),
    "hunger": Trouble(
        id="hunger",
        friend_type="mouse",
        friend_label="a field mouse",
        yelp_line='"Yelp!" squeaked a field mouse beside the path.',
        cause="The mouse had carried a heavy bundle at dawn and missed breakfast.",
        need="the mouse needed food and rest",
        pain_meter="hunger",
        relief_line="Soon the mouse's whiskers lifted, and strength came back to the small legs.",
        tags={"hunger", "food"},
    ),
}

AIDS = {
    "salve": Aid(
        id="salve",
        label="salve",
        phrase="a little tin of pine salve",
        fixes="thorn",
        method="washed the paw with dew from a leaf, drew the thorn out, and dabbed on pine salve",
        result="The smarting eased at once.",
        tags={"salve", "care"},
    ),
    "shawl": Aid(
        id="shawl",
        label="shawl",
        phrase="a soft wool shawl",
        fixes="cold",
        method="wrapped the duck in a soft wool shawl and led the friend to a patch of sun behind the reeds",
        result="Warmth slowly crept back under the feathers.",
        tags={"shawl", "warmth"},
    ),
    "bun": Aid(
        id="bun",
        label="bun",
        phrase="a honey bun from home",
        fixes="hunger",
        method="broke a honey bun in half and waited while the mouse ate every crumb",
        result="Color came back to the friend's face.",
        tags={"bun", "food"},
    ),
}

SURPRISES = {
    "lanterns": Surprise(
        id="lanterns",
        label="paper lanterns",
        phrase="three paper lanterns shaped like acorns",
        fits={"pinewood"},
        reveal="At dusk, little lanterns winked on inside the hollow stump.",
        gift_line='Inside waited three paper lanterns shaped like acorns, and each one glowed as if it had borrowed a star.',
        ending="That night the pinewood path looked less lonely, because kindness had taught even the shadows to shine.",
        tags={"lantern", "surprise"},
    ),
    "reedboat": Surprise(
        id="reedboat",
        label="reed boat",
        phrase="a tiny reed boat with a blue ribbon sail",
        fits={"riverside"},
        reveal="By evening, something small came bobbing down the shallows.",
        gift_line='It was a tiny reed boat with a blue ribbon sail, and on the sail was stitched: "For the friend who came when I called."',
        ending="The river carried the little boat in circles near the bank, as if the water itself wished to say thank you.",
        tags={"boat", "surprise"},
    ),
    "garland": Surprise(
        id="garland",
        label="flower garland",
        phrase="a ring of buttercups and clover",
        fits={"hillmeadow"},
        reveal="When the sun leaned low, a bright ring lay waiting by the old standing stone.",
        gift_line='It was a ring of buttercups and clover, braided so neatly that even the bees came close to admire it.',
        ending="The meadow kept its gold, yet somehow looked richer, because one kind deed had blossomed into many.",
        tags={"flowers", "surprise"},
    ),
}

GIRL_NAMES = ["Lina", "Mara", "Nell", "Ava", "Elsie", "Wren"]
BOY_NAMES = ["Tobin", "Finn", "Milo", "Rowan", "Ben", "Leo"]
HERO_TRAITS = ["kind", "cheerful", "steady", "thoughtful", "gentle", "brave"]


# ---------------------------------------------------------------------------
# Constraints
# ---------------------------------------------------------------------------
def aid_matches(trouble_id: str, aid_id: str) -> bool:
    return aid_id in AIDS and trouble_id in TROUBLES and AIDS[aid_id].fixes == trouble_id


def surprise_fits(setting_id: str, surprise_id: str) -> bool:
    return setting_id in SETTINGS and surprise_id in SURPRISES and setting_id in SURPRISES[surprise_id].fits


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for trouble_id in TROUBLES:
            for aid_id in AIDS:
                for surprise_id in SURPRISES:
                    if aid_matches(trouble_id, aid_id) and surprise_fits(setting_id, surprise_id):
                        combos.append((setting_id, trouble_id, aid_id, surprise_id))
    return combos


def explain_rejection(setting_id: Optional[str], trouble_id: Optional[str],
                      aid_id: Optional[str], surprise_id: Optional[str]) -> str:
    if trouble_id and aid_id and trouble_id in TROUBLES and aid_id in AIDS:
        if not aid_matches(trouble_id, aid_id):
            trouble = TROUBLES[trouble_id]
            aid = AIDS[aid_id]
            right = ", ".join(sorted(a.id for a in AIDS.values() if a.fixes == trouble_id))
            return (
                f"(No story: {aid.phrase} does not solve this trouble. Here the friend needs "
                f"{trouble.need}, so try one of: {right}.)"
            )
    if setting_id and surprise_id and setting_id in SETTINGS and surprise_id in SURPRISES:
        if not surprise_fits(setting_id, surprise_id):
            setting = SETTINGS[setting_id]
            surprise = SURPRISES[surprise_id]
            right = ", ".join(sorted(s.id for s in SURPRISES.values() if setting_id in s.fits))
            return (
                f"(No story: the surprise '{surprise.label}' does not belong naturally in "
                f"{setting.place}. Try one of: {right}.)"
            )
    return "(No valid combination matches the given options.)"


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity, setting: Setting, parent: Entity, aid: Aid) -> None:
    hero.memes["friendship"] += 1
    world.say(
        f"In the old days, when even small paths seemed to remember footsteps, "
        f"there lived {hero.id}, a {hero.traits[0]} little {hero.type}."
    )
    world.say(
        f"One morning {hero.pronoun()} walked along {setting.place}, {setting.path}. {setting.image}"
    )
    world.say(
        f"{hero.id}'s {parent.label} had tucked {aid.phrase} into {hero.pronoun('possessive')} satchel, "
        f"saying, \"A kind traveler should always carry a little help.\""
    )


def hear_yelp(world: World, hero: Entity, trouble: Trouble) -> None:
    hero.memes["alert"] += 1
    world.say(
        f"{hero.pronoun().capitalize()} was thinking friendly thoughts when {trouble.yelp_line}"
    )
    world.say(
        f"{hero.id} stopped at once. A true friend does not pretend not to hear a cry."
    )


def find_friend(world: World, hero: Entity, friend: Entity, trouble: Trouble) -> None:
    friend.memes["fear"] += 1
    friend.meters[trouble.pain_meter] += 1
    world.say(
        f"There {hero.pronoun()} found {friend.label}. {trouble.cause} For such a small creature, "
        f"the trouble felt very big."
    )


def help_friend(world: World, hero: Entity, friend: Entity, trouble: Trouble, aid: Aid) -> None:
    friend.meters[trouble.pain_meter] = 0.0
    friend.memes["relief"] += 1
    hero.memes["kindness"] += 1
    friend.memes["trust"] += 1
    hero.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    world.say(
        f'"Do not be afraid," said {hero.id}. Then {hero.pronoun()} {aid.method}. {aid.result}'
    )
    world.say(trouble.relief_line)


def share_after_help(world: World, hero: Entity, friend: Entity, trouble: Trouble) -> None:
    world.say(
        f"{friend.label.capitalize()} looked at {hero.id} with bright grateful eyes. "
        f"\"You heard me when I gave my yelp,\" {friend.pronoun()} said. "
        f"\"That is how friendship sounds in the world.\""
    )
    world.say(
        f"So the two sat together for a little while, until the frightened feeling had gone and the day felt friendly again."
    )


def surprise_return(world: World, hero: Entity, friend: Entity, setting: Setting, surprise: Surprise) -> None:
    hero.memes["surprise"] += 1
    hero.memes["joy"] += 1
    friend.memes["gratitude"] += 1
    world.say(
        f"Before they parted, {friend.label} only smiled in a secret way and said, "
        f"\"Meet me at {setting.surprise_spot} when the light grows honey-colored.\""
    )
    world.para()
    world.say(
        f"{surprise.reveal} {hero.id} went there wondering what could be waiting."
    )
    world.say(surprise.gift_line)
    world.say(
        f"{friend.label.capitalize()} stepped out and said, "
        f"\"A kind deed should never go home empty-handed.\""
    )
    world.say(surprise.ending)


def tell(setting: Setting, trouble: Trouble, aid: Aid, surprise: Surprise,
         hero_name: str, hero_type: str, hero_trait: str, parent_type: str) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        label=hero_name,
        role="hero",
        traits=[hero_trait],
    ))
    parent_label = "mother" if parent_type == "mother" else "father"
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label=parent_label,
        role="parent",
    ))
    friend = world.add(Entity(
        id="Friend",
        kind="character",
        type=trouble.friend_type,
        label=trouble.friend_label,
        role="friend",
        tags=set(trouble.tags),
    ))
    aid_ent = world.add(Entity(
        id="Aid",
        kind="thing",
        type="aid",
        label=aid.label,
        phrase=aid.phrase,
        tags=set(aid.tags),
    ))

    introduce(world, hero, setting, parent, aid)
    world.para()
    hear_yelp(world, hero, trouble)
    find_friend(world, hero, friend, trouble)
    help_friend(world, hero, friend, trouble, aid)
    share_after_help(world, hero, friend, trouble)
    surprise_return(world, hero, friend, setting, surprise)

    world.facts.update(
        hero=hero,
        parent=parent,
        friend=friend,
        aid=aid,
        aid_entity=aid_ent,
        trouble=trouble,
        setting=setting,
        surprise=surprise,
        healed=friend.meters[trouble.pain_meter] < THRESHOLD,
        friendship=hero.memes["friendship"] >= THRESHOLD and friend.memes["friendship"] >= THRESHOLD,
        surprise_happened=hero.memes["surprise"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "thorn": [(
        "Why does a thorn hurt so much?",
        "A thorn is sharp, so it can poke into skin and make a sore spot. Even a tiny thorn can feel big on a small paw."
    )],
    "cold": [(
        "Why can wet feathers or clothes make someone cold?",
        "Water carries warmth away from the body as it dries. That is why someone who is wet can begin to shiver."
    )],
    "hunger": [(
        "Why does food help when someone feels weak from hunger?",
        "Food gives the body energy to move and think. After eating, a tired person often feels stronger again."
    )],
    "salve": [(
        "What is salve for?",
        "Salve is a soft ointment people put on sore skin. It can help a small hurt feel calmer and less stingy."
    )],
    "shawl": [(
        "What does a shawl do?",
        "A shawl is a soft cloth wrapped around shoulders or wings to keep warmth close. It helps block chilly air."
    )],
    "bun": [(
        "What is a bun?",
        "A bun is a small baked bread, sometimes sweet. It is easy to share and easy to carry on a walk."
    )],
    "friendship": [(
        "What does a good friend do when someone needs help?",
        "A good friend notices the trouble and comes closer instead of walking away. Kind help can make another person feel safe as well as cared for."
    )],
    "surprise": [(
        "Why can a kind surprise feel special?",
        "A kind surprise shows that someone remembered what was done for them. It turns gratitude into something you can see and hold."
    )],
}
KNOWLEDGE_ORDER = ["thorn", "cold", "hunger", "salve", "shawl", "bun", "friendship", "surprise"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    trouble = f["trouble"]
    aid = f["aid"]
    setting = f["setting"]
    return [
        'Write a short folk tale for a 3-to-5-year-old that includes the word "yelp" and centers on friendship, kindness, and a gentle surprise.',
        f"Tell a folk-tale story where {hero.id}, a kind little {hero.type}, hears a yelp on {setting.place} and uses {aid.phrase} to help a friend in trouble.",
        f"Write a simple old-fashioned story where a cry for help leads to friendship, a kind deed, and a thankful surprise at the end.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    trouble = f["trouble"]
    aid = f["aid"]
    setting = f["setting"]
    surprise = f["surprise"]
    parent = f["parent"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a little {hero.type}, and {friend.label} met on {setting.place}. The story also remembers the {parent.label} who sent {hero.id} out carrying a helpful gift."
        ),
        (
            "What happened when the hero heard the yelp?",
            f"When {hero.id} heard the yelp, {hero.pronoun()} stopped right away and went to look. That quick choice mattered because {friend.label} was already frightened and needed help."
        ),
        (
            f"Why did {hero.id} use {aid.label}?",
            f"{hero.id} used {aid.label} because {friend.label} was suffering from {trouble.id}. The help fit the trouble, so the friend's body could calm down and the fear could fade."
        ),
        (
            "How did friendship grow in the story?",
            f"Friendship grew when one small creature answered another creature's cry instead of passing by. After the help was given, both friends felt safer and closer to each other."
        ),
    ]
    if f.get("surprise_happened"):
        qa.append((
            "What was the surprise at the end?",
            f"The surprise was {surprise.phrase} waiting at {setting.surprise_spot}. It was a thankful gift, so the ending showed that kindness had come back in a new shape."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"friendship", "surprise", f["trouble"].id, f["aid"].id}
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
match(T, A) :- trouble(T), aid(A), fixes(A, T).
fit(S, Sp)  :- setting(S), surprise(Sp), belongs(Sp, S).
valid(S, T, A, Sp) :- setting(S), trouble(T), aid(A), surprise(Sp), match(T, A), fit(S, Sp).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for setting_id in SETTINGS:
        lines.append(asp.fact("setting", setting_id))
    for trouble_id in TROUBLES:
        lines.append(asp.fact("trouble", trouble_id))
    for aid_id, aid in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        lines.append(asp.fact("fixes", aid_id, aid.fixes))
    for surprise_id, surprise in SURPRISES.items():
        lines.append(asp.fact("surprise", surprise_id))
        for setting_id in sorted(surprise.fits):
            lines.append(asp.fact("belongs", surprise_id, setting_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        setting="pinewood",
        trouble="thorn",
        aid="salve",
        surprise="lanterns",
        hero_name="Lina",
        hero_type="girl",
        hero_trait="gentle",
        parent_type="mother",
    ),
    StoryParams(
        setting="riverside",
        trouble="cold",
        aid="shawl",
        surprise="reedboat",
        hero_name="Finn",
        hero_type="boy",
        hero_trait="steady",
        parent_type="father",
    ),
    StoryParams(
        setting="hillmeadow",
        trouble="hunger",
        aid="bun",
        surprise="garland",
        hero_name="Nell",
        hero_type="girl",
        hero_trait="kind",
        parent_type="mother",
    ),
]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Folk-tale storyworld: a yelp, a kindness, a friendship, and a surprise."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--hero-name")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.trouble and args.aid:
        if not aid_matches(args.trouble, args.aid):
            raise StoryError(explain_rejection(args.setting, args.trouble, args.aid, args.surprise))
    if args.setting and args.surprise:
        if not surprise_fits(args.setting, args.surprise):
            raise StoryError(explain_rejection(args.setting, args.trouble, args.aid, args.surprise))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.trouble is None or combo[1] == args.trouble)
        and (args.aid is None or combo[2] == args.aid)
        and (args.surprise is None or combo[3] == args.surprise)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, trouble_id, aid_id, surprise_id = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if hero_type == "girl" else BOY_NAMES
    hero_name = args.hero_name or rng.choice(name_pool)
    hero_trait = rng.choice(HERO_TRAITS)
    parent_type = args.parent or rng.choice(["mother", "father"])

    return StoryParams(
        setting=setting_id,
        trouble=trouble_id,
        aid=aid_id,
        surprise=surprise_id,
        hero_name=hero_name,
        hero_type=hero_type,
        hero_trait=hero_trait,
        parent_type=parent_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.trouble not in TROUBLES:
        raise StoryError(f"(Unknown trouble: {params.trouble})")
    if params.aid not in AIDS:
        raise StoryError(f"(Unknown aid: {params.aid})")
    if params.surprise not in SURPRISES:
        raise StoryError(f"(Unknown surprise: {params.surprise})")
    if not aid_matches(params.trouble, params.aid):
        raise StoryError(explain_rejection(params.setting, params.trouble, params.aid, params.surprise))
    if not surprise_fits(params.setting, params.surprise):
        raise StoryError(explain_rejection(params.setting, params.trouble, params.aid, params.surprise))

    world = tell(
        setting=SETTINGS[params.setting],
        trouble=TROUBLES[params.trouble],
        aid=AIDS[params.aid],
        surprise=SURPRISES[params.surprise],
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        hero_trait=params.hero_trait,
        parent_type=params.parent_type,
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
    try:
        clingo_set = set(asp_valid_combos())
        python_set = set(valid_combos())
        if clingo_set == python_set:
            print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
        else:
            rc = 1
            print("MISMATCH between ASP and Python valid_combos():")
            if clingo_set - python_set:
                print("  only in ASP:", sorted(clingo_set - python_set))
            if python_set - clingo_set:
                print("  only in Python:", sorted(python_set - clingo_set))
    except Exception as err:
        rc = 1
        print(f"ASP verification failed: {err}")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        if "yelp" not in sample.story.lower():
            raise StoryError('(Smoke test failed: story does not contain "yelp".)')
        print("OK: smoke test story generated.")
    except Exception as err:
        rc = 1
        print(f"Smoke test failed: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, trouble, aid, surprise) combos:\n")
        for setting_id, trouble_id, aid_id, surprise_id in combos:
            print(f"  {setting_id:10} {trouble_id:8} {aid_id:7} {surprise_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
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
            header = f"### {p.hero_name}: {p.trouble} on {p.setting} with {p.aid}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
storyworlds/worlds/cozy_ship_reading_nook_inner_monologue_fairy_2.py
====================================================================

A standalone storyworld sketch for a fairy-tale voyage on a cozy ship.
Each story begins in a reading nook, turns on an inner monologue, and
resolves when a child checks a real clue in the nook instead of guessing.
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


# ---------------------------------------------------------------------------
# Shared state containers: physical meters and emotional memes live together.
# ---------------------------------------------------------------------------
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
        if self.type == "girl":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type == "boy":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def reflexive(self) -> str:
        if self.type == "girl":
            return "herself"
        if self.type == "boy":
            return "himself"
        return "themself"


# ---------------------------------------------------------------------------
# World parameters and registries.
# ---------------------------------------------------------------------------
@dataclass
class Ship:
    id: str
    name: str
    captain: str
    nook: str
    water: str
    glow: str
    supports: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    object: str
    cue: str
    rhyme: str
    key: str
    hidden_place: str
    instruction: str
    reveal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Challenge:
    id: str
    trouble: str
    need: str
    requires: str
    action: str
    result: str
    destination: str
    final_image: str
    outcome: str
    lesson: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Worry:
    id: str
    thought: str
    body: str
    steadier: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    ship: str
    clue: str
    challenge: str
    worry: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World model and forward rules.
# ---------------------------------------------------------------------------
class World:
    def __init__(self, ship: Ship) -> None:
        self.ship = ship
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def role(self, role: str) -> Optional[Entity]:
        return next((e for e in self.entities.values() if e.role == role), None)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.ship)
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


def _r_notice(world: World) -> list[str]:
    hero = world.role("child")
    clue = world.get("clue")
    sig = ("notice", clue.id)
    if not hero or clue.meters["noticed"] < THRESHOLD or sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["attention"] += 1
    return []


def _r_discern(world: World) -> list[str]:
    hero = world.role("child")
    sig = ("discern", hero.id if hero else "?")
    if not hero or hero.memes["private_worry"] < THRESHOLD or hero.memes["attention"] < THRESHOLD:
        return []
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["discernment"] += 1
    hero.memes["panic"] = max(0.0, hero.memes["panic"] - 0.5)
    return []


def _r_hint_page(world: World) -> list[str]:
    hero = world.role("child")
    clue = world.get("clue")
    page = world.get("page")
    sig = ("hint_page", clue.id)
    if not hero or hero.memes["discernment"] < THRESHOLD:
        return []
    if clue.attrs.get("key") != page.attrs.get("key") or sig in world.fired:
        return []
    world.fired.add(sig)
    page.meters["hinted"] += 1
    hero.memes["hope"] += 1
    return []


def _r_ready_solution(world: World) -> list[str]:
    hero = world.role("child")
    challenge = world.get("challenge")
    ship = world.get("ship")
    page = world.get("page")
    sig = ("ready_solution", challenge.id)
    if not hero or page.meters["retrieved"] < THRESHOLD or sig in world.fired:
        return []
    world.fired.add(sig)
    challenge.meters["solved"] += 1
    ship.meters["guided"] += 1
    hero.memes["courage"] += 1
    hero.memes["relief"] += 1
    return []


CAUSAL_RULES = [
    Rule("notice", "physical", _r_notice),
    Rule("discern", "inner", _r_discern),
    Rule("hint_page", "physical_inner", _r_hint_page),
    Rule("ready_solution", "resolution", _r_ready_solution),
]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            before = len(world.fired)
            rule.apply(world)
            if len(world.fired) != before:
                changed = True


# ---------------------------------------------------------------------------
# Reasonableness gate.
# ---------------------------------------------------------------------------
def clue_fits_ship(ship: Ship, clue: Clue) -> bool:
    return clue.key in ship.supports


def clue_solves_challenge(clue: Clue, challenge: Challenge) -> bool:
    return clue.key == challenge.requires


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for ship_id, ship in SHIPS.items():
        for clue_id, clue in CLUES.items():
            if not clue_fits_ship(ship, clue):
                continue
            for challenge_id, challenge in CHALLENGES.items():
                if clue_solves_challenge(clue, challenge):
                    combos.append((ship_id, clue_id, challenge_id))
    return sorted(combos)


def outcome_of(params: StoryParams) -> str:
    ship = SHIPS[params.ship]
    clue = CLUES[params.clue]
    challenge = CHALLENGES[params.challenge]
    if not clue_fits_ship(ship, clue):
        return "ship_mismatch"
    if not clue_solves_challenge(clue, challenge):
        return "challenge_mismatch"
    return challenge.outcome


def explain_rejection(ship: Ship, clue: Clue, challenge: Challenge) -> str:
    if not clue_fits_ship(ship, clue):
        return (f"(No story: {ship.name} does not have the physical reading-nook "
                f"feature needed for {clue.object}. Pick a clue this ship can truly reveal.)")
    if not clue_solves_challenge(clue, challenge):
        return (f"(No story: {clue.object} reveals a {clue.key} clue, but "
                f"{challenge.trouble} needs a {challenge.requires} answer. The clue "
                f"must solve the voyage problem, not just look magical.)")
    return "(No story: this cozy ship tale falls outside the world rules.)"


# ---------------------------------------------------------------------------
# Story beats.
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity, ship: Ship) -> None:
    ship_ent = world.get("ship")
    ship_ent.meters["cozy"] += 1
    hero.memes["wonder"] += 1
    world.say(
        f"Once upon a moonlit tide, a {hero.traits[0]} little {hero.type} named "
        f"{hero.id} curled up in {ship.nook} aboard {ship.name}."
    )
    world.say(
        f"It was a cozy ship indeed. {ship.glow.capitalize()}, and "
        f"{ship.water}."
    )
    world.say(
        f"Storybooks leaned against quilted pillows there, and {ship.captain} "
        f"liked to say that the nook was the warmest room on the whole sea."
    )


def raise_challenge(world: World, challenge: Challenge) -> None:
    challenge_ent = world.get("challenge")
    challenge_ent.meters["active"] += 1
    world.say(
        f"But that evening, {challenge.trouble}. {challenge.need}."
    )
    world.say(
        f'"Keep your eyes open, little heart," called {world.ship.captain}. '
        f'"A true story always leaves a true sign."'
    )


def inner_worry(world: World, hero: Entity, worry: Worry) -> None:
    hero.memes["private_worry"] += 1
    hero.memes["panic"] += 1
    world.say(
        f'"{worry.thought}?" {hero.id} thought. {worry.body}.'
    )


def notice_clue(world: World, hero: Entity, clue: Clue) -> None:
    clue_ent = world.get("clue")
    clue_ent.meters["noticed"] += 1
    world.say(
        f"Then {hero.id} noticed {clue.object}. {clue.cue}."
    )
    world.say(
        f'The little thing seemed to sing a secret: "{clue.rhyme}"'
    )
    propagate(world)
    if world.get("page").meters["hinted"] >= THRESHOLD:
        world.say(f"As {hero.id} watched, {clue.reveal}.")


def inner_turn(world: World, hero: Entity, clue: Clue, worry: Worry) -> None:
    page = world.get("page")
    if page.meters["hinted"] < THRESHOLD:
        raise StoryError("(No story: the child could not connect the inner thought to a real clue.)")
    world.say(
        f'"A frightened thought wants me to grab any page," {hero.id} told '
        f"{hero.reflexive()}. \"But a real clue points.\""
    )
    world.say(
        f"{worry.steadier}. So {hero.id} {clue.instruction} and found the tucked "
        f"page {clue.hidden_place}."
    )
    page.meters["retrieved"] += 1
    propagate(world)


def solve(world: World, hero: Entity, challenge: Challenge) -> None:
    challenge_ent = world.get("challenge")
    if challenge_ent.meters["solved"] < THRESHOLD:
        raise StoryError("(No story: the hidden page never became a working solution.)")
    world.say(
        f"{hero.id} carried the page to the doorway and {challenge.action}."
    )
    world.say(
        f"At once, {challenge.result}."
    )


def ending(world: World, hero: Entity, challenge: Challenge) -> None:
    world.say(
        f"{world.ship.captain} laughed with relief as {world.ship.name} sailed "
        f"toward {challenge.destination}."
    )
    world.say(
        f"When {hero.id} returned to the reading nook, the same books and quilts "
        f"looked different, because now the child knew {challenge.lesson.lower()}."
    )
    world.say(challenge.final_image)


def tell(ship: Ship, clue: Clue, challenge: Challenge, worry: Worry,
         name: str = "Mira", gender: str = "girl", trait: str = "careful") -> World:
    world = World(ship)
    hero = world.add(Entity(
        id=name, kind="character", type=gender, role="child", traits=[trait]
    ))
    world.add(Entity(
        id="ship", kind="thing", type="ship", role="vessel", label=ship.name
    ))
    world.add(Entity(
        id="clue", kind="thing", type="clue", role="clue", label=clue.object,
        attrs={"key": clue.key}
    ))
    world.add(Entity(
        id="page", kind="thing", type="page", role="page",
        label="the hidden guiding page", attrs={"key": challenge.requires}
    ))
    world.add(Entity(
        id="challenge", kind="thing", type="voyage", role="challenge",
        label=challenge.trouble, attrs={"requires": challenge.requires}
    ))

    introduce(world, hero, ship)
    world.para()
    raise_challenge(world, challenge)
    inner_worry(world, hero, worry)
    notice_clue(world, hero, clue)

    world.para()
    inner_turn(world, hero, clue, worry)
    solve(world, hero, challenge)
    ending(world, hero, challenge)

    world.facts.update(
        hero=hero,
        ship=ship,
        clue=clue,
        challenge=challenge,
        worry=worry,
        outcome=challenge.outcome,
        captain=ship.captain,
        page_found=world.get("page").meters["retrieved"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Content.
# ---------------------------------------------------------------------------
SHIPS = {
    "marigold": Ship(
        "marigold",
        "the cozy ship Marigold",
        "Captain Rowan",
        "a reading nook under a round porthole",
        "outside, the black water wore a silver hem",
        "an amber lantern made the book spines shine like honey",
        supports={"moonbeam", "shell_chime"},
        tags={"ship", "reading", "fairy", "moon", "shell"},
    ),
    "thistledown": Ship(
        "thistledown",
        "the cozy ship Thistledown",
        "Captain Elowen",
        "a reading nook beside the tea shelf and the window seat",
        "outside, little waves patted the hull as gently as kittens",
        "a blue lamp glowed beside a steaming teapot",
        supports={"tea_steam", "moonbeam"},
        tags={"ship", "reading", "fairy", "tea", "moon"},
    ),
    "hearthfin": Ship(
        "hearthfin",
        "the cozy ship Hearthfin",
        "Captain Bramble",
        "a reading nook tucked by the stern shelves and the shell curtain",
        "outside, the tide murmured in a sleepy green voice",
        "a brass stove kept the rug warm under small feet",
        supports={"tea_steam", "shell_chime"},
        tags={"ship", "reading", "fairy", "tea", "shell"},
    ),
}

CLUES = {
    "moon_ribbon": Clue(
        "moon_ribbon",
        "a silver ribbon bookmark on the rug",
        "Its shadow fell straight across one star stitched into the cushion",
        "Moon on page and moon on sea, show the line that shelters me.",
        "moonbeam",
        "inside the cushion pocket under the porthole",
        "followed the silver line across the cushion",
        "the moonbeam sharpened one small stitched star until it almost winked",
        tags={"reading", "moon", "clue"},
    ),
    "steam_saucer": Clue(
        "steam_saucer",
        "a cinnamon teacup saucer beside the lamp",
        "Warm rings blossomed over its painted roses and touched the corner of a folded page",
        "Steam that curls and steam that gleams, wake the ink from drowsy dreams.",
        "tea_steam",
        "inside the kettle cozy beside the lamp",
        "lifted the folded page into the tea steam",
        "the sleepy ink woke in brown-gold letters",
        tags={"reading", "tea", "clue"},
    ),
    "shell_tassel": Clue(
        "shell_tassel",
        "a shell tassel hanging from the tallest shelf",
        "It chimed each time the ship tipped, and one shelf answered with a softer knock",
        "Little shell, softly sing, tell me where the true words cling.",
        "shell_chime",
        "behind a loose board on the story shelf",
        "listened for the shelf that answered the shell song",
        "the shell music pointed to one board that trembled like a tiny bell",
        tags={"reading", "shell", "clue"},
    ),
}

CHALLENGES = {
    "pearl_fog": Challenge(
        "pearl_fog",
        "a pearl fog braided itself across the water ahead",
        "The captain had lost the moon-lane verse that could part the white tangle",
        "moonbeam",
        "read the moon-lane verse in a clear, steady voice",
        "the fog untied itself into shining ribbons and left a bright path",
        "Moonshell Harbor",
        "Far ahead, the harbor lamps floated like stars tucked into wool, and the cozy ship glided between them without a bump.",
        "fog_opened",
        "a careful thought can become a lantern",
        tags={"fairy", "fog", "moon"},
    ),
    "sleepy_sails": Challenge(
        "sleepy_sails",
        "a drizzle sprite had breathed a drowsy spell over the sails",
        "The ship needed the warm-breeze verse before the cloth forgot how to billow",
        "tea_steam",
        "warmed the hidden verse and spoke it toward the mast",
        "the sails puffed out like warm bread and the ship remembered how to move",
        "Cinnamon Quay",
        "By the quay, the mast ribbon danced in the rain-washed air, and the whole cozy ship smelled of tea, bread, and brave work.",
        "sails_woke",
        "warm courage wakes sleepy things",
        tags={"fairy", "tea", "weather"},
    ),
    "hush_bridge": Challenge(
        "hush_bridge",
        "the shell bridge ahead had gone silent and would not lift its pearly arch",
        "Only the bridge-song hidden in the ship's story pages could wake it kindly",
        "shell_chime",
        "sang the bridge-song in time with the shell chimes",
        "the bridge lifted with a silvery laugh and let the ship pass underneath",
        "Bellflower Bay",
        "When they looked back, the open bridge shone over the tide like a necklace laid down by dawn, and every shell on board seemed pleased.",
        "bridge_lifted",
        "listening can open what pushing cannot",
        tags={"fairy", "shell", "bridge"},
    ),
}

WORRIES = {
    "lost_page": Worry(
        "lost_page",
        "What if I have lost the very page the ship needs",
        "The thought folded small and sharp inside the child's chest, like a paper boat with a tear in it",
        "Then the child breathed once and remembered that eyes and ears could test a fear",
        tags={"worry", "reading"},
    ),
    "small_voice": Worry(
        "small_voice",
        "What if my voice is too little to help a whole ship",
        "The child's throat felt as narrow as the ribbon in a story cap",
        "Then the child remembered that even a tiny bell can guide a giant through mist",
        tags={"worry", "voice"},
    ),
    "too_much_magic": Worry(
        "too_much_magic",
        "What if the enchantment is bigger than any child can mend",
        "The room seemed full of too many glimmers at once, and each one looked busy",
        "Then the child remembered that magic still has to leave a footprint somewhere",
        tags={"worry", "magic"},
    ),
}

GIRL_NAMES = ["Mira", "Lina", "Nora", "Poppy", "Elsie", "Wren", "Talia", "Ivy"]
BOY_NAMES = ["Oren", "Milo", "Finn", "Theo", "Alder", "Jules", "Ben", "Otis"]
TRAITS = ["careful", "curious", "gentle", "brave", "quiet", "thoughtful"]

CURATED = [
    StoryParams("marigold", "moon_ribbon", "pearl_fog", "lost_page", "Mira", "girl", "careful"),
    StoryParams("thistledown", "steam_saucer", "sleepy_sails", "small_voice", "Milo", "boy", "thoughtful"),
    StoryParams("hearthfin", "shell_tassel", "hush_bridge", "too_much_magic", "Nora", "girl", "quiet"),
    StoryParams("thistledown", "moon_ribbon", "pearl_fog", "too_much_magic", "Theo", "boy", "curious"),
    StoryParams("hearthfin", "steam_saucer", "sleepy_sails", "lost_page", "Ivy", "girl", "gentle"),
]


# ---------------------------------------------------------------------------
# QA.
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "ship": [("What is a ship's reading nook?",
              "A reading nook is a small cozy place for books, cushions, and quiet thinking. On a ship, it can still help with the voyage if a clue is hidden there.")],
    "reading": [("Why can books matter in a fairy tale?",
                 "A fairy tale often hides help inside songs, pages, or riddles. Reading carefully lets the hero notice help that rushing would miss.")],
    "moon": [("How can moonlight become a clue?",
              "Moonlight can point at something by making a shadow or shining on one exact spot. In stories, careful watching turns that light into guidance.")],
    "tea": [("How can warm steam reveal something?",
             "Warm steam can wake hidden ink or soften a folded page. That makes heat part of the clue instead of just part of the room.")],
    "shell": [("Why would shells help in a fairy-tale ship story?",
               "Shells fit a sea story because they carry sound and memory from the water. A shell chime can become a gentle signal when the hero listens closely.")],
    "fog": [("Why is fog a problem for a ship?",
             "Fog hides the way ahead, so the captain cannot see a safe path clearly. The ship needs some other guide, such as a true clue or a remembered verse.")],
    "weather": [("Why do fairy tales sometimes give weather feelings or spells?",
                 "Fairy tales make the world feel alive, so wind, rain, and fog can act almost like characters. That lets the hero solve a problem with kindness and attention, not only force.")],
    "bridge": [("Why would listening help with a bridge?",
                "Some things respond better to rhythm and timing than to pushing. Listening helps the hero answer the bridge in the way it understands.")],
    "worry": [("Can an inner worry ever help?",
               "Yes, if the child does not obey the worry blindly. A worry can remind the child to check a real sign in the world.")],
}
KNOWLEDGE_ORDER = ["ship", "reading", "moon", "tea", "shell", "fog",
                   "weather", "bridge", "worry"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, ship, clue, challenge = f["hero"], f["ship"], f["clue"], f["challenge"]
    return [
        f'Write a TinyStories-style fairy tale that includes the words "cozy ship" and takes place in a reading nook. Use inner monologue, a hidden clue, and a safe ending at sea.',
        f"Tell a child-facing fairy story about {hero.id} aboard {ship.name}. The turning point should come when {hero.pronoun()} pauses, checks {clue.object}, and uses a real clue instead of a frightened guess.",
        f"Write a gentle sea tale in which {challenge.trouble}, the child searches the reading nook, and the final image proves the voyage has changed.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, ship, clue, challenge, worry = (
        f["hero"], f["ship"], f["clue"], f["challenge"], f["worry"]
    )
    qa = [
        ("Who is the story about?",
         f"It is about {hero.id}, a little {hero.type} on {ship.name}. The child begins in the reading nook while the voyage is in trouble."),
        ("Where does the story happen?",
         f"It happens aboard {ship.name}, especially in {ship.nook}. That cozy place holds the books, cushions, and clue that later save the voyage."),
        (f"What was {hero.id} worried about?",
         f"{hero.id} thought, \"{worry.thought}?\" The worry felt strong at first, but it pushed the child to look for a real sign instead of only guessing."),
        ("What clue did the child notice?",
         f"The child noticed {clue.object}. {clue.reveal.capitalize()}, so the object showed where the hidden page was waiting."),
        ("How did inner monologue change the story?",
         f"The child stopped and named the frightened thought instead of obeying it. That pause turned worry into discernment, which is why the clue could lead to the right page."),
        ("How was the problem solved?",
         f"{hero.id} found the hidden page and {challenge.action}. Because the clue matched the voyage problem, {challenge.result}."),
        ("How did the story end?",
         f"The ship reached {challenge.destination} safely. {challenge.final_image}"),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["ship"].tags) | set(f["clue"].tags) | set(f["challenge"].tags)
    tags |= set(f["worry"].tags) | {"ship", "reading", "worry"}
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
    for ent in world.entities.values():
        bits = []
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        attrs = {k: v for k, v in ent.attrs.items() if v}
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if attrs:
            bits.append(f"attrs={attrs}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid(S, C, H) :-
    ship(S), clue(C), challenge(H),
    supports(S, K), clue_key(C, K), challenge_requires(H, K).

outcome(ship_mismatch) :-
    chosen_ship(S), chosen_clue(C),
    clue_key(C, K), not supports(S, K).

outcome(challenge_mismatch) :-
    chosen_ship(S), chosen_clue(C), chosen_challenge(H),
    clue_key(C, K1), supports(S, K1),
    challenge_requires(H, K2), K1 != K2.

outcome(O) :-
    chosen_ship(S), chosen_clue(C), chosen_challenge(H),
    valid(S, C, H), challenge_outcome(H, O).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for ship_id, ship in SHIPS.items():
        lines.append(asp.fact("ship", ship_id))
        for key in sorted(ship.supports):
            lines.append(asp.fact("supports", ship_id, key))
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue", clue_id))
        lines.append(asp.fact("clue_key", clue_id, clue.key))
    for challenge_id, challenge in CHALLENGES.items():
        lines.append(asp.fact("challenge", challenge_id))
        lines.append(asp.fact("challenge_requires", challenge_id, challenge.requires))
        lines.append(asp.fact("challenge_outcome", challenge_id, challenge.outcome))
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
        asp.fact("chosen_ship", params.ship),
        asp.fact("chosen_clue", params.clue),
        asp.fact("chosen_challenge", params.challenge),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def _story_checks(sample: StorySample) -> list[str]:
    problems: list[str] = []
    text = sample.story
    if "cozy ship" not in text:
        problems.append("story text lost required seed words")
    if "reading nook" not in text:
        problems.append("story text lost required setting phrase")
    if text.count("\n\n") < 2:
        problems.append("story is missing a full beginning-turn-ending paragraph shape")
    if "thought." not in text and 'thought,' not in text and 'thought "' not in text and 'thought. ' not in text:
        if "thought" not in text:
            problems.append("story is missing visible inner monologue")
    if "{" in text or "}" in text:
        problems.append("story leaked unresolved template markers")
    if len(sample.story_qa) < 5 or len(sample.world_qa) < 3 or len(sample.prompts) < 3:
        problems.append("qa or prompt sets are too thin")
    return problems


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
    invalids = [
        StoryParams("marigold", "steam_saucer", "pearl_fog", "lost_page", "Mira", "girl", "careful"),
        StoryParams("thistledown", "shell_tassel", "hush_bridge", "small_voice", "Milo", "boy", "quiet"),
        StoryParams("hearthfin", "moon_ribbon", "sleepy_sails", "too_much_magic", "Nora", "girl", "brave"),
    ]
    cases.extend(invalids)
    empty = build_parser().parse_args([])
    for seed in range(150):
        params = resolve_params(empty, random.Random(seed))
        params.seed = seed
        cases.append(params)

    bad = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not bad:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(bad)}/{len(cases)} outcomes differ.")
        for params in bad[:5]:
            print(" ", params, asp_outcome(params), outcome_of(params))

    sample_issues: list[str] = []
    for params in CURATED:
        sample = generate(params)
        sample_issues.extend(f"{params.name}: {problem}" for problem in _story_checks(sample))
    if not sample_issues:
        print(f"OK: generated stories passed shape/quality checks on {len(CURATED)} curated samples.")
    else:
        rc = 1
        print("QUALITY CHECK FAILURES:")
        for issue in sample_issues:
            print(" ", issue)
    return rc


# ---------------------------------------------------------------------------
# Standard interface.
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a fairy-tale cozy ship, a reading nook, "
                    "and an inner monologue that becomes a real clue."
    )
    ap.add_argument("--ship", choices=SHIPS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--worry", choices=WORRIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible stories derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin against Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP facts and rules")
    return ap


def _pick_name(rng: random.Random, gender: str) -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    return rng.choice(pool)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    ship_id = args.ship or rng.choice(sorted(SHIPS))
    ship = SHIPS[ship_id]

    valid_clues = [cid for cid, clue in CLUES.items() if clue_fits_ship(ship, clue)]
    clue_id = args.clue or rng.choice(sorted(valid_clues))
    clue = CLUES[clue_id]

    valid_challenges = [hid for hid, challenge in CHALLENGES.items()
                        if clue_solves_challenge(clue, challenge)]
    challenge_id = args.challenge or rng.choice(sorted(valid_challenges))
    challenge = CHALLENGES[challenge_id]

    if (ship_id, clue_id, challenge_id) not in set(valid_combos()):
        raise StoryError(explain_rejection(ship, clue, challenge))

    worry_id = args.worry or rng.choice(sorted(WORRIES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or _pick_name(rng, gender)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(ship_id, clue_id, challenge_id, worry_id, name, gender, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SHIPS[params.ship],
        CLUES[params.clue],
        CHALLENGES[params.challenge],
        WORRIES[params.worry],
        params.name,
        params.gender,
        params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (ship, clue, challenge) combos:\n")
        for ship_id, clue_id, challenge_id in combos:
            print(f"  {ship_id:12} {clue_id:12} {challenge_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 80, 80):
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
            header = f"### {p.name}: {p.clue} / {p.challenge} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

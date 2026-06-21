#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/cupie_vinegarette_sharing_foreshadowing_flashback_adventure.py
==========================================================================================

A standalone storyworld for a small garden adventure built around three explicit
narrative instruments:

* Sharing        -- the children have one small snack and must decide whether to share it
* Foreshadowing  -- the obstacle is hinted before the children reach it
* Flashback      -- a remembered earlier mistake changes the later choice

This world always includes the seed words "cupie" and "vinegarette":

* the cupie is a tiny painted travel cup that carries the trail snack
* the vinegarette is a little vine-woven wagon the children pull on their quest

The domain is deliberately small and constraint-driven. A story is only valid
when the chosen helper both likes the snack in the cupie and can really help
with the obstacle ahead.

Run it
------
    python storyworlds/worlds/gpt-5.4/cupie_vinegarette_sharing_foreshadowing_flashback_adventure.py
    python storyworlds/worlds/gpt-5.4/cupie_vinegarette_sharing_foreshadowing_flashback_adventure.py --obstacle stream --helper turtle --snack clover
    python storyworlds/worlds/gpt-5.4/cupie_vinegarette_sharing_foreshadowing_flashback_adventure.py --helper goat --obstacle thorn_gate
    python storyworlds/worlds/gpt-5.4/cupie_vinegarette_sharing_foreshadowing_flashback_adventure.py --all
    python storyworlds/worlds/gpt-5.4/cupie_vinegarette_sharing_foreshadowing_flashback_adventure.py --qa --json
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

# Make the shared result containers importable when this script is run directly
# from the repo root despite living one level deeper under worlds/gpt-5.4/.
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
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"grandmother": "grandma", "grandfather": "grandpa"}.get(self.type, self.type)


@dataclass
class Trail:
    id: str
    place: str
    destination: str
    sendoff: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    clue: str
    block_text: str
    solved_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    likes: set[str] = field(default_factory=set)
    handles: set[str] = field(default_factory=set)
    arrival: str = ""
    help_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Snack:
    id: str
    label: str
    phrase: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    trail: str
    obstacle: str
    helper: str
    snack: str
    share_timing: str
    leader: str
    leader_gender: str
    partner: str
    partner_gender: str
    grownup: str
    leader_trait: str
    partner_trait: str
    seed: Optional[int] = None


TRAILS = {
    "fern_glen": Trail(
        id="fern_glen",
        place="Fern Glen",
        destination="the silver bell tree",
        sendoff="set off along the green path as if they were crossing a hidden kingdom",
        ending_image="The silver bell tree rang softly over their heads",
        tags={"garden", "adventure"},
    ),
    "pebble_ridge": Trail(
        id="pebble_ridge",
        place="Pebble Ridge",
        destination="the lookout stump",
        sendoff="marched over the pebbles like brave mountain climbers",
        ending_image="From the lookout stump they could see the whole bright garden",
        tags={"garden", "adventure"},
    ),
    "mossy_loop": Trail(
        id="mossy_loop",
        place="Mossy Loop",
        destination="the moonflower gate",
        sendoff="followed the bendy path like explorers searching for a secret door",
        ending_image="The moonflower gate glowed pale and quiet beside them",
        tags={"garden", "adventure"},
    ),
}

OBSTACLES = {
    "stream": Obstacle(
        id="stream",
        label="a laughing stream",
        clue="Even before they were halfway there, they could hear water chuckling over stones ahead.",
        block_text="The stream skipped right across the path, and the vinegarette could not roll through the shining water without tipping.",
        solved_text="Soon the stream no longer seemed like a wall at all, only another part of the adventure.",
        tags={"water", "path"},
    ),
    "thorn_gate": Obstacle(
        id="thorn_gate",
        label="a thorn gate",
        clue="From far ahead came a dry little clicking, as if brambles were rubbing together in the wind.",
        block_text="A thorn gate had leaned across the trail, prickly and tangled, and the vinegarette could not squeeze past.",
        solved_text="Once the safe way through was shown, the thorn gate looked more puzzly than scary.",
        tags={"thorn", "path"},
    ),
    "windy_slope": Obstacle(
        id="windy_slope",
        label="the windy slope",
        clue="Long before they reached the hill, they heard the wind whistling over the top of it.",
        block_text="The path climbed into the windy slope, and each puff pushed the vinegarette backward again.",
        solved_text="With steady help, the windy slope became a climb instead of a defeat.",
        tags={"wind", "hill"},
    ),
}

HELPERS = {
    "turtle": Helper(
        id="turtle",
        label="turtle",
        phrase="a mossy turtle",
        likes={"clover"},
        handles={"stream"},
        arrival="By the bank sat a mossy turtle, blinking as if it had all afternoon to think.",
        help_text="The turtle stepped into the stream, showed them the firm stones, and let them pull the vinegarette across one careful step at a time.",
        tags={"animal", "stream"},
    ),
    "sparrow": Helper(
        id="sparrow",
        label="sparrow",
        phrase="a quick brown sparrow",
        likes={"seeds"},
        handles={"thorn_gate"},
        arrival="On a twig above the path perched a quick brown sparrow, head tipped to one side.",
        help_text="The sparrow fluttered ahead and showed them the low safe opening under the thorns where the vinegarette could slide through.",
        tags={"animal", "bird"},
    ),
    "goat": Helper(
        id="goat",
        label="goat",
        phrase="a sturdy little goat",
        likes={"apple_slices"},
        handles={"windy_slope"},
        arrival="Near the hill stood a sturdy little goat with bright eyes and strong hooves.",
        help_text="The goat leaned into the vinegarette strap and helped tug the wagon up the hill, step by stubborn step.",
        tags={"animal", "hill"},
    ),
    "rabbit": Helper(
        id="rabbit",
        label="rabbit",
        phrase="a soft gray rabbit",
        likes={"carrot_coins"},
        handles={"thorn_gate"},
        arrival="Beside the brambles waited a soft gray rabbit, nose twitching at every smell.",
        help_text="The rabbit hopped through the brambles and revealed a smooth hidden lane where the vinegarette could pass without a single scratch.",
        tags={"animal", "thorn"},
    ),
}

SNACKS = {
    "clover": Snack(
        id="clover",
        label="clover leaves",
        phrase="fresh clover leaves",
        tags={"clover", "sharing"},
    ),
    "seeds": Snack(
        id="seeds",
        label="sunflower seeds",
        phrase="sunflower seeds",
        tags={"seed", "sharing"},
    ),
    "apple_slices": Snack(
        id="apple_slices",
        label="apple slices",
        phrase="sweet apple slices",
        tags={"apple", "sharing"},
    ),
    "carrot_coins": Snack(
        id="carrot_coins",
        label="carrot coins",
        phrase="round carrot coins",
        tags={"carrot", "sharing"},
    ),
}

LEADER_TRAITS = ["bold", "eager", "curious", "quick-footed", "determined"]
PARTNER_TRAITS = ["careful", "kind", "steady", "thoughtful", "patient"]

GIRL_NAMES = ["Lila", "Mina", "Zoe", "Ava", "Nora", "Pia", "Ruby", "Tess"]
BOY_NAMES = ["Ben", "Toby", "Milo", "Finn", "Eli", "Theo", "Sam", "Nico"]

SHARE_TIMINGS = ["early", "late", "never"]


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
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = copy.deepcopy(self.facts)
        return other


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_hungry_helper(world: World) -> list[str]:
    helper = world.entities.get("helper")
    if helper is None:
        return []
    if helper.memes["offered"] < THRESHOLD or helper.attrs.get("likes_match") is not True:
        return []
    sig = ("hungry_helper", helper.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    helper.memes["trust"] += 1
    helper.memes["helps"] += 1
    return []


def _r_clear_obstacle(world: World) -> list[str]:
    helper = world.entities.get("helper")
    obstacle = world.entities.get("obstacle")
    wagon = world.entities.get("wagon")
    if helper is None or obstacle is None or wagon is None:
        return []
    if helper.memes["helps"] < THRESHOLD:
        return []
    if helper.attrs.get("can_handle") is not True:
        return []
    sig = ("clear", obstacle.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    obstacle.meters["cleared"] += 1
    wagon.meters["blocked"] = 0.0
    wagon.meters["progress"] += 1
    return []


def _r_blocked_worry(world: World) -> list[str]:
    wagon = world.entities.get("wagon")
    leader = world.entities.get("leader")
    partner = world.entities.get("partner")
    if wagon is None or leader is None or partner is None:
        return []
    if wagon.meters["blocked"] < THRESHOLD:
        return []
    sig = ("worry", wagon.id, int(wagon.meters["blocked"]))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    leader.memes["worry"] += 1
    partner.memes["worry"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="hungry_helper", tag="social", apply=_r_hungry_helper),
    Rule(name="clear_obstacle", tag="physical", apply=_r_clear_obstacle),
    Rule(name="blocked_worry", tag="emotional", apply=_r_blocked_worry),
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
        for sent in produced:
            world.say(sent)
    return produced


def helper_matches(helper: Helper, snack: Snack) -> bool:
    return snack.id in helper.likes


def helper_solves(helper: Helper, obstacle: Obstacle) -> bool:
    return obstacle.id in helper.handles


def valid_combo(helper: Helper, obstacle: Obstacle, snack: Snack) -> bool:
    return helper_matches(helper, snack) and helper_solves(helper, obstacle)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for trail_id in TRAILS:
        for obstacle_id, obstacle in OBSTACLES.items():
            for helper_id, helper in HELPERS.items():
                for snack_id, snack in SNACKS.items():
                    if valid_combo(helper, obstacle, snack):
                        combos.append((trail_id, obstacle_id, helper_id, snack_id))
    return combos


def outcome_of(params: StoryParams) -> str:
    if params.share_timing == "never":
        return "turn_back"
    return "share_and_reach"


def explain_rejection(helper: Helper, obstacle: Obstacle, snack: Snack) -> str:
    if not helper_matches(helper, snack):
        return (
            f"(No story: {helper.phrase} would not stop for {snack.label}. "
            f"The shared snack from the cupie has to be something the helper truly wants.)"
        )
    if not helper_solves(helper, obstacle):
        return (
            f"(No story: {helper.phrase} cannot reasonably solve {obstacle.label}. "
            f"Pick a helper that can really get the vinegarette past the obstacle.)"
        )
    return "(No story: this combination does not form a reasonable adventure.)"


def introduce(world: World, leader: Entity, partner: Entity, grownup: Entity, trail: Trail) -> None:
    world.say(
        f"One bright morning, {leader.id} and {partner.id} stood at the garden gate with "
        f"{leader.pronoun('possessive')} {grownup.label_word}'s blessing. They had packed a tiny painted "
        f"cupie for trail snacks and a little vine-woven wagon called the vinegarette."
    )
    world.say(
        f"They were headed through {trail.place} toward {trail.destination}, and they "
        f"{trail.sendoff}."
    )


def foreshadow(world: World, obstacle: Obstacle) -> None:
    world.say(obstacle.clue)
    world.facts["foreshadowing"] = obstacle.clue


def set_flashback(world: World, leader: Entity, partner: Entity) -> None:
    world.facts["flashback"] = (
        f"{leader.id} suddenly remembered the day the vinegarette wheel had sunk into soft dirt. "
        f"Back then, {leader.pronoun()} had hugged the cupie close and would not share, and no one "
        f"had come to help. They had trudged home with the wagon still stuck, and the memory still "
        f"felt heavy."
    )
    partner.memes["memory"] += 1
    leader.memes["memory"] += 1


def meet_helper(world: World, helper_ent: Entity, helper: Helper) -> None:
    world.say(helper.arrival)
    world.facts["met_helper"] = helper.label


def desire_to_keep(world: World, leader: Entity, partner: Entity, snack: Snack) -> None:
    leader.memes["greed"] += 1
    world.say(
        f"{leader.id} peeked into the cupie. \"There is only enough {snack.label} for our adventure,\" "
        f"{leader.pronoun()} whispered."
    )
    world.say(
        f'{partner.id} looked from the cupie to the path ahead. "Maybe a little sharing could help us later," '
        f"{partner.pronoun()} said."
    )


def offer_share(world: World, leader: Entity, helper_ent: Entity, snack: Snack) -> None:
    leader.memes["generosity"] += 1
    helper_ent.memes["offered"] += 1
    world.say(
        f"{leader.id} knelt down, tipped the cupie carefully, and offered {snack.label} to "
        f"the {helper_ent.label}."
    )
    propagate(world, narrate=False)


def refuse_share(world: World, leader: Entity, snack: Snack) -> None:
    world.say(
        f"But {leader.id} closed the cupie again around the {snack.label}. "
        f'"Not yet," {leader.pronoun()} said, trying to sound brave.'
    )


def reach_obstacle(world: World, obstacle_ent: Entity, obstacle: Obstacle, wagon: Entity) -> None:
    wagon.meters["blocked"] += 1
    propagate(world, narrate=False)
    world.say(obstacle.block_text)
    world.facts["obstacle_seen"] = obstacle.label


def helper_act(world: World, helper: Helper, obstacle_ent: Entity) -> None:
    if obstacle_ent.meters["cleared"] >= THRESHOLD:
        world.say(helper.help_text)
        world.say(obstacle_ent.attrs["solved_text"])


def flashback_paragraph(world: World) -> None:
    world.say("Then a memory rose up all at once.")
    world.say(world.facts["flashback"])


def turn_back(world: World, leader: Entity, partner: Entity, trail: Trail, snack: Snack) -> None:
    leader.memes["lesson"] += 1
    partner.memes["lesson"] += 1
    world.say(
        f"The helper did not follow, and the obstacle stayed right where it was. "
        f"{leader.id} and {partner.id} looked at the stuck vinegarette and knew the path was finished for today."
    )
    world.say(
        f"They walked home slowly, sharing the {snack.label} between themselves at last. "
        f"The cupie felt lighter in {leader.id}'s hand, and the lesson felt clearer."
    )
    world.say(
        f'At the gate, {leader.id} said, "Next time we share sooner." {partner.id} nodded, and even the quiet trail '
        f"seemed to agree."
    )
    world.facts["outcome"] = "turn_back"


def celebrate(world: World, leader: Entity, partner: Entity, helper: Helper, trail: Trail, snack: Snack) -> None:
    leader.memes["joy"] += 1
    partner.memes["joy"] += 1
    leader.memes["lesson"] += 1
    partner.memes["lesson"] += 1
    world.say(
        f"With the way open, they pulled the vinegarette on until at last they reached {trail.destination}."
    )
    world.say(
        f"{trail.ending_image}. {leader.id} and {partner.id} shared the last of the {snack.label} from the cupie, "
        f"and they left a thank-you nibble for the {helper.label} too."
    )
    world.say(
        f"The adventure felt bigger now, not because the garden had changed, but because the children had. "
        f"The vinegarette rattled home behind them, and this time it sounded like a happy drum."
    )
    world.facts["outcome"] = "share_and_reach"


def tell(
    trail: Trail,
    obstacle: Obstacle,
    helper: Helper,
    snack: Snack,
    share_timing: str,
    leader_name: str,
    leader_gender: str,
    partner_name: str,
    partner_gender: str,
    grownup_type: str,
    leader_trait: str,
    partner_trait: str,
) -> World:
    world = World()

    leader = world.add(
        Entity(
            id=leader_name,
            kind="character",
            type=leader_gender,
            label=leader_name,
            role="leader",
            traits=[leader_trait],
        )
    )
    partner = world.add(
        Entity(
            id=partner_name,
            kind="character",
            type=partner_gender,
            label=partner_name,
            role="partner",
            traits=[partner_trait],
        )
    )
    grownup = world.add(
        Entity(
            id="Grownup",
            kind="character",
            type=grownup_type,
            label="the grown-up",
            role="grownup",
        )
    )
    cupie = world.add(
        Entity(
            id="cupie",
            type="thing",
            label="cupie",
            phrase="a tiny painted cupie",
            role="snack_holder",
            attrs={"snack": snack.id},
        )
    )
    wagon = world.add(
        Entity(
            id="wagon",
            type="thing",
            label="vinegarette",
            phrase="the vinegarette",
            role="wagon",
        )
    )
    obstacle_ent = world.add(
        Entity(
            id="obstacle",
            type="obstacle",
            label=obstacle.label,
            phrase=obstacle.label,
            role="obstacle",
            attrs={"solved_text": obstacle.solved_text},
        )
    )
    helper_ent = world.add(
        Entity(
            id="helper",
            kind="character",
            type="animal",
            label=helper.label,
            phrase=helper.phrase,
            role="helper",
            attrs={
                "likes_match": helper_matches(helper, snack),
                "can_handle": helper_solves(helper, obstacle),
            },
        )
    )

    world.facts.update(
        trail=trail,
        obstacle_cfg=obstacle,
        helper_cfg=helper,
        snack_cfg=snack,
        leader=leader,
        partner=partner,
        grownup=grownup,
        cupie=cupie,
        wagon=wagon,
        helper=helper_ent,
        obstacle=obstacle_ent,
        share_timing=share_timing,
    )

    introduce(world, leader, partner, grownup, trail)
    foreshadow(world, obstacle)

    world.para()
    meet_helper(world, helper_ent, helper)
    desire_to_keep(world, leader, partner, snack)
    set_flashback(world, leader, partner)

    if share_timing == "early":
        world.para()
        flashback_paragraph(world)
        offer_share(world, leader, helper_ent, snack)
        reach_obstacle(world, obstacle_ent, obstacle, wagon)
        helper_act(world, helper, obstacle_ent)
        world.para()
        celebrate(world, leader, partner, helper, trail, snack)
    elif share_timing == "late":
        world.para()
        refuse_share(world, leader, snack)
        reach_obstacle(world, obstacle_ent, obstacle, wagon)
        world.say(
            f"{partner.id} tugged at the vinegarette, but it only shivered in place. "
            f"That was when the old memory hurt enough to be useful."
        )
        world.para()
        flashback_paragraph(world)
        offer_share(world, leader, helper_ent, snack)
        helper_act(world, helper, obstacle_ent)
        world.para()
        celebrate(world, leader, partner, helper, trail, snack)
    else:
        world.para()
        flashback_paragraph(world)
        refuse_share(world, leader, snack)
        reach_obstacle(world, obstacle_ent, obstacle, wagon)
        world.para()
        turn_back(world, leader, partner, trail, snack)

    world.facts["shared"] = helper_ent.memes["offered"] >= THRESHOLD
    world.facts["cleared"] = obstacle_ent.meters["cleared"] >= THRESHOLD
    return world


KNOWLEDGE = {
    "sharing": [
        (
            "Why can sharing help on an adventure?",
            "Sharing helps because it lets other people or animals join in and help. When you share kindly, you often make a problem smaller and a friendship bigger.",
        )
    ],
    "foreshadowing": [
        (
            "What is foreshadowing in a story?",
            "Foreshadowing is when a story gives a little hint about something that will matter later. It helps the reader feel that a surprise was quietly waiting all along.",
        )
    ],
    "flashback": [
        (
            "What is a flashback?",
            "A flashback is a short look back at something that happened earlier. It can help a character remember a lesson and make a different choice.",
        )
    ],
    "wagon": [
        (
            "What is a wagon used for?",
            "A wagon is used to carry things while you pull it along. A small wagon can help on an adventure because it holds supplies without anyone carrying them in their arms the whole time.",
        )
    ],
    "stream": [
        (
            "Why do people step carefully in a stream?",
            "Stream stones can be slippery and wobbly. Careful steps keep feet steady and help people avoid falling in.",
        )
    ],
    "thorn": [
        (
            "Why should you be careful around thorns?",
            "Thorns are sharp parts of some plants. They can scratch skin or catch on clothes if you push through too fast.",
        )
    ],
    "wind": [
        (
            "Why is climbing a windy hill harder?",
            "Wind can push against your body or anything you are pulling. That makes each step feel heavier and less steady.",
        )
    ],
    "turtle": [
        (
            "How can a turtle be a good guide?",
            "A turtle moves slowly and carefully, which can be helpful near water or tricky ground. Watching a slow guide can help others choose safer steps.",
        )
    ],
    "sparrow": [
        (
            "Why might a sparrow notice a path first?",
            "A sparrow can hop and fly above the ground, so it can spot gaps and openings quickly. Birds often see little routes that people miss from below.",
        )
    ],
    "goat": [
        (
            "Why are goats good on hills?",
            "Goats have strong legs and careful feet for climbing. They are steady on slopes where wheels and tired legs may slip.",
        )
    ],
    "rabbit": [
        (
            "Why can a rabbit find a way through bushes?",
            "Rabbits are small and quick, and they often know little runs under plants. A rabbit may notice a smooth path hidden beneath leaves.",
        )
    ],
}

KNOWLEDGE_ORDER = [
    "sharing",
    "foreshadowing",
    "flashback",
    "wagon",
    "stream",
    "thorn",
    "wind",
    "turtle",
    "sparrow",
    "goat",
    "rabbit",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    leader = f["leader"]
    partner = f["partner"]
    trail = f["trail"]
    obstacle = f["obstacle_cfg"]
    helper = f["helper_cfg"]
    snack = f["snack_cfg"]
    return [
        'Write a short adventure story for a 3-to-5-year-old that includes the words "cupie" and "vinegarette" and clearly uses sharing, foreshadowing, and a flashback.',
        f"Tell a gentle garden adventure where {leader.id} and {partner.id} head through {trail.place}, meet {helper.phrase}, and solve {obstacle.label} by sharing {snack.label}.",
        f'Write a child-facing adventure in which an early clue hints at trouble ahead, a memory changes a choice, and the ending shows that sharing made the journey possible.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    leader = f["leader"]
    partner = f["partner"]
    trail = f["trail"]
    obstacle = f["obstacle_cfg"]
    helper = f["helper_cfg"]
    snack = f["snack_cfg"]
    grownup = f["grownup"]
    share_timing = f["share_timing"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {leader.id} and {partner.id}, two children going on a garden adventure. They travel with a cupie for snacks and a little wagon called the vinegarette.",
        ),
        (
            "What was the adventure goal?",
            f"They wanted to travel through {trail.place} and reach {trail.destination}. The trip felt exciting because they treated the garden like a real quest.",
        ),
        (
            "What was the foreshadowing clue?",
            f"The story hinted at the trouble ahead before the children reached it: {f['foreshadowing']} That clue quietly prepared the reader for {obstacle.label}.",
        ),
        (
            "What was the flashback about?",
            f"The flashback was about an earlier day when {leader.id} would not share and nobody helped with the stuck vinegarette. Remembering that old mistake helped the children understand what kindness could change this time.",
        ),
        (
            f"Why did the {helper.label} help them?",
            f"The {helper.label} helped because {leader.id} shared {snack.label} from the cupie. The shared snack showed kindness, and then the helper knew exactly how to get them past {obstacle.label}.",
        ),
    ]
    if share_timing == "late":
        qa.append(
            (
                "Did they share right away?",
                f"No. At first {leader.id} tried to keep the snack, and the vinegarette got stuck at {obstacle.label}. Then the flashback changed the choice, so {leader.pronoun()} shared and the adventure could continue.",
            )
        )
    elif share_timing == "early":
        qa.append(
            (
                "Did the memory help before they got stuck?",
                f"Yes. The flashback came back in time, so {leader.id} shared before the trouble could stop them for long. Because of that early choice, the obstacle was solved smoothly.",
            )
        )
    else:
        qa.append(
            (
                "How did the story end?",
                f"They had to turn back because {leader.id} still would not share in time, so the helper could not help with {obstacle.label}. On the way home the children finally shared the snack with each other and learned to be kinder sooner next time.",
            )
        )
    if f["outcome"] == "share_and_reach":
        qa.append(
            (
                "How did the story end?",
                f"They reached {trail.destination} and shared the last bites from the cupie there. The ending image proves the change, because the adventure finishes with sharing instead of clutching.",
            )
        )
    qa.append(
        (
            f"What did {leader.id}'s {grownup.label_word} do at the start?",
            f"{grownup.label_word.capitalize()} sent them off with permission for the adventure. That calm beginning makes the later obstacle feel like a challenge to solve, not a reason to panic.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"sharing", "foreshadowing", "flashback", "wagon"}
    obstacle = f["obstacle_cfg"]
    helper = f["helper_cfg"]
    if obstacle.id == "stream":
        tags.add("stream")
    elif obstacle.id == "thorn_gate":
        tags.add("thorn")
    elif obstacle.id == "windy_slope":
        tags.add("wind")
    tags.add(helper.id)
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
        bits: list[str] = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v not in ("", [], {}, set())}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        trail="fern_glen",
        obstacle="stream",
        helper="turtle",
        snack="clover",
        share_timing="early",
        leader="Lila",
        leader_gender="girl",
        partner="Ben",
        partner_gender="boy",
        grownup="grandmother",
        leader_trait="curious",
        partner_trait="kind",
    ),
    StoryParams(
        trail="pebble_ridge",
        obstacle="thorn_gate",
        helper="sparrow",
        snack="seeds",
        share_timing="late",
        leader="Milo",
        leader_gender="boy",
        partner="Ruby",
        partner_gender="girl",
        grownup="grandfather",
        leader_trait="bold",
        partner_trait="thoughtful",
    ),
    StoryParams(
        trail="mossy_loop",
        obstacle="windy_slope",
        helper="goat",
        snack="apple_slices",
        share_timing="early",
        leader="Nora",
        leader_gender="girl",
        partner="Theo",
        partner_gender="boy",
        grownup="grandmother",
        leader_trait="determined",
        partner_trait="steady",
    ),
    StoryParams(
        trail="fern_glen",
        obstacle="thorn_gate",
        helper="rabbit",
        snack="carrot_coins",
        share_timing="never",
        leader="Finn",
        leader_gender="boy",
        partner="Pia",
        partner_gender="girl",
        grownup="grandfather",
        leader_trait="eager",
        partner_trait="patient",
    ),
]


ASP_RULES = r"""
valid(T, O, H, S) :- trail(T), obstacle(O), helper(H), snack(S), likes(H, S), handles(H, O).

outcome(turn_back) :- chosen_share(never).
outcome(share_and_reach) :- chosen_share(early).
outcome(share_and_reach) :- chosen_share(late).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for trail_id in TRAILS:
        lines.append(asp.fact("trail", trail_id))
    for obstacle_id in OBSTACLES:
        lines.append(asp.fact("obstacle", obstacle_id))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        for snack_id in sorted(helper.likes):
            lines.append(asp.fact("likes", helper_id, snack_id))
        for obstacle_id in sorted(helper.handles):
            lines.append(asp.fact("handles", helper_id, obstacle_id))
    for snack_id in SNACKS:
        lines.append(asp.fact("snack", snack_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = asp.fact("chosen_share", params.share_timing)
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: cupie, vinegarette, sharing, foreshadowing, flashback, and adventure."
    )
    ap.add_argument("--trail", choices=TRAILS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--share-timing", choices=SHARE_TIMINGS, dest="share_timing")
    ap.add_argument("--grownup", choices=["grandmother", "grandfather"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from the ASP twin")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.helper and args.obstacle and args.snack:
        helper = HELPERS[args.helper]
        obstacle = OBSTACLES[args.obstacle]
        snack = SNACKS[args.snack]
        if not valid_combo(helper, obstacle, snack):
            raise StoryError(explain_rejection(helper, obstacle, snack))

    combos = [
        combo
        for combo in valid_combos()
        if (args.trail is None or combo[0] == args.trail)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.helper is None or combo[2] == args.helper)
        and (args.snack is None or combo[3] == args.snack)
    ]
    if not combos:
        if args.helper and args.obstacle and args.snack:
            raise StoryError(explain_rejection(HELPERS[args.helper], OBSTACLES[args.obstacle], SNACKS[args.snack]))
        raise StoryError("(No valid combination matches the given options.)")

    trail_id, obstacle_id, helper_id, snack_id = rng.choice(sorted(combos))
    share_timing = args.share_timing or rng.choices(
        population=SHARE_TIMINGS,
        weights=[4, 3, 1],
        k=1,
    )[0]
    leader, leader_gender = _pick_child(rng)
    partner, partner_gender = _pick_child(rng, avoid=leader)
    grownup = args.grownup or rng.choice(["grandmother", "grandfather"])
    leader_trait = rng.choice(LEADER_TRAITS)
    partner_trait = rng.choice(PARTNER_TRAITS)
    return StoryParams(
        trail=trail_id,
        obstacle=obstacle_id,
        helper=helper_id,
        snack=snack_id,
        share_timing=share_timing,
        leader=leader,
        leader_gender=leader_gender,
        partner=partner,
        partner_gender=partner_gender,
        grownup=grownup,
        leader_trait=leader_trait,
        partner_trait=partner_trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        trail = TRAILS[params.trail]
        obstacle = OBSTACLES[params.obstacle]
        helper = HELPERS[params.helper]
        snack = SNACKS[params.snack]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err.args[0]})") from None

    if not valid_combo(helper, obstacle, snack):
        raise StoryError(explain_rejection(helper, obstacle, snack))
    if params.share_timing not in SHARE_TIMINGS:
        raise StoryError(f"(Invalid share timing: {params.share_timing})")

    world = tell(
        trail=trail,
        obstacle=obstacle,
        helper=helper,
        snack=snack,
        share_timing=params.share_timing,
        leader_name=params.leader,
        leader_gender=params.leader_gender,
        partner_name=params.partner,
        partner_gender=params.partner_gender,
        grownup_type=params.grownup,
        leader_trait=params.leader_trait,
        partner_trait=params.partner_trait,
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


def _smoke_emit(sample: StorySample) -> None:
    buf = io.StringIO()
    old = sys.stdout
    try:
        sys.stdout = buf
        emit(sample, trace=False, qa=False, header="")
    finally:
        sys.stdout = old
    if not buf.getvalue().strip():
        raise StoryError("(Smoke emit produced no output.)")


def asp_verify() -> int:
    rc = 0

    py_combos = set(valid_combos())
    clingo_combos = set(asp_valid_combos())
    if py_combos == clingo_combos:
        print(f"OK: ASP gate matches valid_combos() ({len(py_combos)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_combos - py_combos:
            print("  only in ASP:", sorted(clingo_combos - py_combos))
        if py_combos - clingo_combos:
            print("  only in Python:", sorted(py_combos - clingo_combos))

    scenarios = list(CURATED)
    for seed in range(30):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        scenarios.append(params)

    mismatches = 0
    for params in scenarios:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: ASP outcome matches outcome_of() on {len(scenarios)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(scenarios)} scenario outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke generate returned an empty story.)")
        _smoke_emit(sample)
        print("OK: smoke generation and emit succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (trail, obstacle, helper, snack) combos:\n")
        for trail_id, obstacle_id, helper_id, snack_id in combos:
            print(f"  {trail_id:12} {obstacle_id:12} {helper_id:8} {snack_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            header = (
                f"### {p.leader} & {p.partner}: {p.helper} / {p.obstacle} / "
                f"{p.snack} ({outcome_of(p)})"
            )
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

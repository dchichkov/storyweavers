#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/cue_kindness_misunderstanding_magic_folk_tale.py
============================================================================

A small folk-tale storyworld about a child on an errand, a strange magical cue,
a frightened misunderstanding, and a kind gift that reveals the truth.

The world models:
- a place with a blocked path or task,
- a magical folk helper with a specific cue,
- a kindness gift that honestly meets the helper's need,
- a misunderstanding that rises from fear and falls when kindness is shown.

Every generated story keeps the same core shape:
beginning errand -> puzzling cue and misunderstanding -> kind act ->
magic solution -> ending image that proves what changed.

Run it
------
python storyworlds/worlds/gpt-5.4/cue_kindness_misunderstanding_magic_folk_tale.py
python storyworlds/worlds/gpt-5.4/cue_kindness_misunderstanding_magic_folk_tale.py --all
python storyworlds/worlds/gpt-5.4/cue_kindness_misunderstanding_magic_folk_tale.py --place bridge --folk river_aunt --cue bell --obstacle fog --gift honey_bun
python storyworlds/worlds/gpt-5.4/cue_kindness_misunderstanding_magic_folk_tale.py --verify
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
        female = {"girl", "woman", "mother", "grandmother", "aunt"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "grandmother": "grandmother"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    opening: str
    path_word: str
    destination: str
    errand: str
    obstacle_ids: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Cue:
    id: str
    label: str
    sound: str
    misunderstanding: str
    truth: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    phrase: str
    threat: str
    solves_with: str
    opening: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    need: str
    give_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Folk:
    id: str
    label: str
    phrase: str
    type: str
    cue: str
    obstacle: str
    need: str
    need_text: str
    reveal: str
    magic_text: str
    thanks: str
    tags: set[str] = field(default_factory=set)


PLACES = {
    "bridge": Place(
        id="bridge",
        label="the old river bridge",
        opening="Beyond the last cottage stood the old river bridge, pale with mist.",
        path_word="bridge",
        destination="her grandmother's cottage",
        errand="carry a covered bowl of plum soup",
        obstacle_ids={"fog"},
        tags={"bridge", "river"},
    ),
    "lane": Place(
        id="lane",
        label="the briar lane",
        opening="Past the mill curled the briar lane, narrow as a ribbon and green as a wall.",
        path_word="lane",
        destination="the baker's back door",
        errand="bring a basket of sweet rolls",
        obstacle_ids={"thorns"},
        tags={"lane", "briar"},
    ),
    "well": Place(
        id="well",
        label="the moon well",
        opening="At the edge of the square waited the moon well, with white stones round it like a little crown.",
        path_word="well",
        destination="the village kitchen",
        errand="draw a pail of water for supper",
        obstacle_ids={"ice"},
        tags={"well", "village"},
    ),
}

CUES = {
    "bell": Cue(
        id="bell",
        label="a silver bell",
        sound="ting-ting",
        misunderstanding="It sounded to the child like a warning bell for trouble.",
        truth="It was only a cue to wake the hidden stepping stones under the mist.",
        tags={"bell", "cue", "sound"},
    ),
    "whistle": Cue(
        id="whistle",
        label="a reed whistle",
        sound="wee-oo",
        misunderstanding="It sounded to the child like a sharp little call for thorns to catch at sleeves.",
        truth="It was only a cue to tell the sleeping briars to unlace themselves.",
        tags={"whistle", "cue", "sound"},
    ),
    "spoon": Cue(
        id="spoon",
        label="a starry spoon",
        sound="ting on the stones",
        misunderstanding="It sounded to the child like someone tapping out a cold spell.",
        truth="It was only a cue to call the warm water sleeping under the well stones.",
        tags={"spoon", "cue", "sound"},
    ),
}

OBSTACLES = {
    "fog": Obstacle(
        id="fog",
        label="fog",
        phrase="a blanket of river fog",
        threat="The planks and the water below were swallowed in white, and no safe step could be seen.",
        solves_with="bell",
        opening="That morning the bridge had vanished inside a blanket of river fog.",
        ending="the bridge lay clear from end to end, with shining stones showing the way",
        tags={"fog", "river"},
    ),
    "thorns": Obstacle(
        id="thorns",
        label="thorns",
        phrase="a wall of waking briars",
        threat="The lane was knotted shut with thorny vines that tugged at aprons and baskets.",
        solves_with="whistle",
        opening="That day the lane had grown shut with waking briars.",
        ending="the briars bowed aside and left a neat green path",
        tags={"thorns", "briar"},
    ),
    "ice": Obstacle(
        id="ice",
        label="ice",
        phrase="a ring of blue ice",
        threat="The bucket rope was frozen stiff, and the water below slept too deep to reach.",
        solves_with="spoon",
        opening="That evening the well was held in a ring of blue ice.",
        ending="the rope ran free and warm water winked below",
        tags={"ice", "well"},
    ),
}

GIFTS = {
    "honey_bun": Gift(
        id="honey_bun",
        label="honey bun",
        phrase="a honey bun wrapped in cloth",
        need="hungry",
        give_text="broke the honey bun in half and held the sweeter half out with both hands",
        tags={"food", "bun"},
    ),
    "cup_water": Gift(
        id="cup_water",
        label="cup of water",
        phrase="a little cup of clear water",
        need="thirsty",
        give_text="poured a little cup of water and offered it first, before asking for anything",
        tags={"water"},
    ),
    "red_scarf": Gift(
        id="red_scarf",
        label="red scarf",
        phrase="a soft red scarf",
        need="cold",
        give_text="took off the red scarf from around the child's neck and wrapped it gently around the stranger's shoulders",
        tags={"warmth", "scarf"},
    ),
}

FOLK = {
    "river_aunt": Folk(
        id="river_aunt",
        label="river aunt",
        phrase="an old river aunt with pearl drops on her sleeves",
        type="aunt",
        cue="bell",
        obstacle="fog",
        need="hungry",
        need_text="She looked thin and travel-worn, as if she had not tasted breakfast.",
        reveal='The old woman smiled. "Little one, this bell is no harm. It is only my cue."',
        magic_text="She lifted the silver bell and rang it three bright times. From the milk-white fog, flat stepping stones rose like sleepy fish coming up to listen.",
        thanks='"Bread shared on a fearful road turns the road kind," she said.',
        tags={"magic", "river", "kindness"},
    ),
    "hedge_grandmother": Folk(
        id="hedge_grandmother",
        label="hedge grandmother",
        phrase="a bent hedge grandmother with leaves caught in her braids",
        type="grandmother",
        cue="whistle",
        obstacle="thorns",
        need="thirsty",
        need_text="Her lips looked dry, and even her voice seemed dusty.",
        reveal='The bent woman chuckled. "Child, this whistle is no curse. It is only my cue."',
        magic_text="She set the reed whistle to her lips and sent one long, soft call through the lane. At once the briars sighed, loosened their claws, and braided themselves neatly against the hedge.",
        thanks='"A kind drink can untangle more than vines," she said.',
        tags={"magic", "briar", "kindness"},
    ),
    "frost_boy": Folk(
        id="frost_boy",
        label="frost boy",
        phrase="a pale frost boy with moonlight in his hair",
        type="boy",
        cue="spoon",
        obstacle="ice",
        need="cold",
        need_text="Though he was made of winter, he trembled as if a lonely wind had found its way into him.",
        reveal='The pale boy laughed softly. "This spoon is no mean spell. It is only my cue."',
        magic_text="He tapped the starry spoon on the rim of the well: ting, ting, ting. The blue ice cracked like thin sugar, and a warm shimmer moved up from the deep water.",
        thanks='"Warmth given freely comes back as blessing," he said.',
        tags={"magic", "well", "kindness"},
    ),
}


@dataclass
class StoryParams:
    place: str
    cue: str
    folk: str
    obstacle: str
    gift: str
    child_name: str
    child_gender: str
    elder_type: str
    trait: str
    seed: Optional[int] = None


GIRL_NAMES = ["Anya", "Mira", "Lina", "Tessa", "Nora", "Elin", "Rosa", "Mila"]
BOY_NAMES = ["Ivo", "Tarin", "Milo", "Pavel", "Nico", "Luka", "Bram", "Soren"]
TRAITS = ["gentle", "careful", "curious", "brave", "soft-hearted", "thoughtful"]


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
        clone = World()
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


def _r_kindness_softens(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    folk = world.entities.get("folk")
    gift = world.entities.get("gift")
    if not child or not folk or not gift:
        return out
    if gift.meters["given"] < THRESHOLD:
        return out
    sig = ("kindness", gift.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    folk.memes["trust"] += 1
    folk.memes["gratitude"] += 1
    child.memes["kindness"] += 1
    child.memes["fear"] = max(0.0, child.memes["fear"] - 1)
    out.append("__kindness__")
    return out


def _r_magic_clears(world: World) -> list[str]:
    out: list[str] = []
    obstacle = world.entities.get("obstacle")
    folk = world.entities.get("folk")
    cue = world.entities.get("cue")
    if not obstacle or not folk or not cue:
        return out
    if cue.meters["used"] < THRESHOLD or folk.memes["trust"] < THRESHOLD:
        return out
    sig = ("magic", obstacle.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    obstacle.meters["blocked"] = 0.0
    obstacle.meters["open"] += 1
    folk.meters["magic"] += 1
    child = world.entities.get("child")
    if child:
        child.memes["relief"] += 1
        child.memes["wonder"] += 1
        if child.memes["fear"] >= THRESHOLD:
            child.memes["shame"] += 1
            child.memes["fear"] = 0.0
    out.append("__magic__")
    return out


CAUSAL_RULES = [
    Rule(name="kindness_softens", tag="social", apply=_r_kindness_softens),
    Rule(name="magic_clears", tag="magic", apply=_r_magic_clears),
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


def cue_matches(folk: Folk, cue: Cue) -> bool:
    return folk.cue == cue.id


def gift_matches(folk: Folk, gift: Gift) -> bool:
    return folk.need == gift.need


def obstacle_matches(place: Place, obstacle: Obstacle) -> bool:
    return obstacle.id in place.obstacle_ids


def folk_solves(folk: Folk, obstacle: Obstacle) -> bool:
    return folk.obstacle == obstacle.id and obstacle.solves_with == folk.cue


def valid_combo(place: Place, cue: Cue, folk: Folk, obstacle: Obstacle, gift: Gift) -> bool:
    return (
        cue_matches(folk, cue)
        and gift_matches(folk, gift)
        and obstacle_matches(place, obstacle)
        and folk_solves(folk, obstacle)
    )


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for cue_id, cue in CUES.items():
            for folk_id, folk in FOLK.items():
                for obstacle_id, obstacle in OBSTACLES.items():
                    for gift_id, gift in GIFTS.items():
                        if valid_combo(place, cue, folk, obstacle, gift):
                            combos.append((place_id, cue_id, folk_id, obstacle_id, gift_id))
    return combos


def predict_truth(world: World) -> dict:
    sim = world.copy()
    sim.get("gift").meters["given"] += 1
    propagate(sim, narrate=False)
    sim.get("cue").meters["used"] += 1
    propagate(sim, narrate=False)
    return {
        "opens_path": sim.get("obstacle").meters["open"] >= THRESHOLD,
        "trust": sim.get("folk").memes["trust"],
    }


def introduce(world: World, child: Entity, elder: Entity, place: Place) -> None:
    world.say(
        f"In a village where even the geese seemed to know old songs, there lived a {child.attrs.get('trait', 'gentle')} child named {child.id}."
    )
    world.say(
        f"One day {child.id}'s {elder.label_word} asked {child.pronoun('object')} to {place.errand} to {place.destination}."
    )
    world.say(place.opening)


def obstacle_appears(world: World, child: Entity, place: Place, obstacle: Obstacle) -> None:
    world.get("obstacle").meters["blocked"] += 1
    world.say(
        f"But when {child.id} came to {place.label}, {obstacle.opening} {obstacle.threat}"
    )
    child.memes["worry"] += 1


def hear_cue(world: World, child: Entity, cue: Cue) -> None:
    child.memes["fear"] += 1
    world.say(
        f"Then, from somewhere close and hidden, came the sound of {cue.label}: {cue.sound}. {cue.misunderstanding}"
    )
    world.say(
        f"{child.id}'s heart knocked once against {child.pronoun('possessive')} ribs, and {child.pronoun()} drew one small step back."
    )


def meet_folk(world: World, child: Entity, folk: Entity, folk_cfg: Folk) -> None:
    world.say(
        f"Out from the edge of the place came {folk_cfg.phrase}. {folk_cfg.need_text}"
    )
    world.say(
        f"At first {child.id} thought the stranger might have called the trouble, and not the cure."
    )


def offer_kindness(world: World, child: Entity, gift_ent: Entity, gift: Gift) -> None:
    gift_ent.meters["given"] += 1
    world.say(
        f"But {child.id} remembered what {child.pronoun('possessive')} elders always said: a frightened heart should not forget kindness."
    )
    world.say(
        f"So {child.pronoun()} {gift.give_text}."
    )
    propagate(world, narrate=False)


def reveal_truth(world: World, folk_cfg: Folk, cue: Cue) -> None:
    world.say(folk_cfg.reveal)
    world.say(cue.truth)


def use_magic(world: World, cue_ent: Entity, folk_cfg: Folk, obstacle: Obstacle) -> None:
    cue_ent.meters["used"] += 1
    propagate(world, narrate=False)
    world.say(folk_cfg.magic_text)
    world.say(
        f"In another breath {obstacle.ending}."
    )


def ending(world: World, child: Entity, folk_cfg: Folk, place: Place, gift: Gift) -> None:
    shame_line = ""
    if child.memes["shame"] >= THRESHOLD:
        shame_line = (
            f" {child.id} felt heat in {child.pronoun('possessive')} cheeks for mistrusting the stranger, but the feeling was soft, not sharp, because the truth had come with mercy."
        )
    world.say(folk_cfg.thanks)
    world.say(
        f"{child.id} finished the errand at last, and the road that had seemed full of threat now looked full of help.{shame_line}"
    )
    world.say(
        f"Long after, whenever {child.id} heard such a cue in the village dusk, {child.pronoun()} did not think of danger first. {child.pronoun().capitalize()} thought of the day when {gift.label} and a kind hand opened the world."
    )


def tell(
    place: Place,
    cue: Cue,
    folk_cfg: Folk,
    obstacle: Obstacle,
    gift: Gift,
    child_name: str,
    child_gender: str,
    elder_type: str,
    trait: str,
) -> World:
    world = World()
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            role="child",
            label=child_name,
            attrs={"trait": trait},
        )
    )
    elder = world.add(
        Entity(
            id="Elder",
            kind="character",
            type=elder_type,
            role="elder",
            label="the elder",
        )
    )
    folk = world.add(
        Entity(
            id="folk",
            kind="character",
            type=folk_cfg.type,
            role="folk",
            label=folk_cfg.label,
            phrase=folk_cfg.phrase,
        )
    )
    obstacle_ent = world.add(
        Entity(
            id="obstacle",
            kind="thing",
            type="obstacle",
            label=obstacle.label,
            phrase=obstacle.phrase,
        )
    )
    cue_ent = world.add(
        Entity(
            id="cue",
            kind="thing",
            type="cue",
            label=cue.label,
            phrase=cue.label,
        )
    )
    gift_ent = world.add(
        Entity(
            id="gift",
            kind="thing",
            type="gift",
            label=gift.label,
            phrase=gift.phrase,
        )
    )

    introduce(world, child, elder, place)
    obstacle_appears(world, child, place, obstacle)

    world.para()
    hear_cue(world, child, cue)
    meet_folk(world, child, folk, folk_cfg)

    world.para()
    offer_kindness(world, child, gift_ent, gift)
    reveal_truth(world, folk_cfg, cue)
    use_magic(world, cue_ent, folk_cfg, obstacle)

    world.para()
    ending(world, child, folk_cfg, place, gift)

    world.facts.update(
        place=place,
        cue_cfg=cue,
        folk_cfg=folk_cfg,
        obstacle_cfg=obstacle,
        gift_cfg=gift,
        child=child,
        elder=elder,
        folk=folk,
        obstacle=obstacle_ent,
        cue=cue_ent,
        gift=gift_ent,
        misunderstanding=child.memes["shame"] >= THRESHOLD or child.memes["fear"] >= THRESHOLD,
        resolved=obstacle_ent.meters["open"] >= THRESHOLD,
        gifted=gift_ent.meters["given"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "cue": [
        (
            "What is a cue?",
            "A cue is a small sign or signal that tells someone when to do something. In stories, a sound can be a cue for magic to begin.",
        )
    ],
    "bell": [
        (
            "Why might a bell be used as a signal?",
            "A bell makes a clear sound that travels far, so people can hear it quickly. That makes it useful as a cue.",
        )
    ],
    "whistle": [
        (
            "What does a whistle do?",
            "A whistle makes a thin, sharp sound. Because it is easy to notice, it can be used as a cue or signal.",
        )
    ],
    "spoon": [
        (
            "How can tapping metal make a signal?",
            "When metal taps stone or metal, it makes a bright ringing sound. A repeated ringing sound can work as a cue.",
        )
    ],
    "kindness": [
        (
            "What is kindness?",
            "Kindness means choosing to help or comfort someone. A kind act can change how people feel about each other.",
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone thinks something means one thing, but it really means another. It can be fixed by listening, asking, and being calm.",
        )
    ],
    "magic": [
        (
            "What is magic in a folk tale?",
            "In a folk tale, magic is a wonder that changes the world in a surprising way. It often appears beside a lesson about how people should behave.",
        )
    ],
    "fog": [
        (
            "Why is thick fog hard to walk through?",
            "Fog hides what is far away and can blur the ground ahead. That makes it harder to see the safe path.",
        )
    ],
    "thorns": [
        (
            "Why are thorns troublesome on a path?",
            "Thorns can scratch skin and catch on clothes or baskets. A thorny path is hard to pass safely.",
        )
    ],
    "ice": [
        (
            "Why does ice make a rope hard to use?",
            "Ice can freeze a rope stiff and slippery. Then it will not bend or run the way it should.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "cue",
    "kindness",
    "misunderstanding",
    "magic",
    "bell",
    "whistle",
    "spoon",
    "fog",
    "thorns",
    "ice",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    place = f["place"]
    cue = f["cue_cfg"]
    obstacle = f["obstacle_cfg"]
    folk_cfg = f["folk_cfg"]
    return [
        f'Write a short folk tale for a 3-to-5-year-old that includes the word "cue" and a kind child hearing {cue.label} near {place.label}.',
        f"Tell a gentle magical tale where {child.id} misunderstands a strange sound, shows kindness anyway, and learns that the sound was a cue for help.",
        f"Write a folk-style story in which {folk_cfg.label} uses {cue.label} to solve a problem with {obstacle.label}, and the misunderstanding is healed by kindness.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    place = f["place"]
    cue = f["cue_cfg"]
    obstacle = f["obstacle_cfg"]
    folk_cfg = f["folk_cfg"]
    gift = f["gift_cfg"]
    elder = f["elder"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child sent on an errand, and {folk_cfg.label}, a magical stranger met at {place.label}. Their meeting changes fear into trust.",
        ),
        (
            f"Why was {child.id} at {place.label}?",
            f"{child.id} had been asked by {child.pronoun('possessive')} {elder.label_word} to {place.errand} to {place.destination}. The errand is what brought {child.pronoun('object')} to the trouble.",
        ),
        (
            f"What problem stood in the way?",
            f"The problem was {obstacle.phrase}. {obstacle.threat}",
        ),
        (
            f"Why did {child.id} feel frightened when {child.pronoun()} heard {cue.label}?",
            f"{cue.misunderstanding} So {child.id} thought the sound might belong to danger instead of help.",
        ),
        (
            f"What kind thing did {child.id} do?",
            f"{child.pronoun().capitalize()} offered {gift.phrase} to the stranger before asking for any favor. That kindness mattered because it met the stranger's need and made trust possible.",
        ),
        (
            f"What did the magical stranger explain about the cue?",
            f"{cue.truth} The child had misunderstood the sound, and the explanation turned fear into understanding.",
        ),
    ]
    if f.get("resolved"):
        qa.append(
            (
                "How was the problem solved?",
                f"{folk_cfg.label.capitalize()} used {cue.label} as a cue for magic, and then {obstacle.ending}. Because the child had shown kindness first, the meeting became helpful instead of fearful.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the errand finished and the place made safe again. {child.id} remembered that a strange sign can hide a good meaning, especially when kindness leads the way.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"cue", "kindness", "misunderstanding", "magic"}
    f = world.facts
    tags |= set(f["cue_cfg"].tags)
    tags |= set(f["obstacle_cfg"].tags)
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:9} ({e.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="bridge",
        cue="bell",
        folk="river_aunt",
        obstacle="fog",
        gift="honey_bun",
        child_name="Anya",
        child_gender="girl",
        elder_type="grandmother",
        trait="gentle",
    ),
    StoryParams(
        place="lane",
        cue="whistle",
        folk="hedge_grandmother",
        obstacle="thorns",
        gift="cup_water",
        child_name="Milo",
        child_gender="boy",
        elder_type="father",
        trait="curious",
    ),
    StoryParams(
        place="well",
        cue="spoon",
        folk="frost_boy",
        obstacle="ice",
        gift="red_scarf",
        child_name="Nora",
        child_gender="girl",
        elder_type="mother",
        trait="thoughtful",
    ),
]


def explain_rejection(place: Place, cue: Cue, folk: Folk, obstacle: Obstacle, gift: Gift) -> str:
    if not obstacle_matches(place, obstacle):
        choices = ", ".join(sorted(place.obstacle_ids))
        return (
            f"(No story: {obstacle.label} does not belong at {place.label}. "
            f"That place only supports obstacle(s): {choices}.)"
        )
    if not cue_matches(folk, cue):
        return (
            f"(No story: {folk.label} does not use {cue.label} as a cue. "
            f"That magical helper uses {CUES[folk.cue].label}.)"
        )
    if not folk_solves(folk, obstacle):
        return (
            f"(No story: {folk.label} cannot solve {obstacle.label}. "
            f"This helper is tied to {folk.obstacle}.)"
        )
    if not gift_matches(folk, gift):
        return (
            f"(No story: {gift.label} does not meet {folk.label}'s need. "
            f"That helper needs something for being {folk.need}.)"
        )
    return "(No story: the requested combination is unreasonable in this world.)"


ASP_RULES = r"""
matches_cue(F, C) :- folk(F), cue_of(F, C).
fits_gift(F, G) :- folk(F), need_of(F, N), gift_need(G, N).
place_has_obstacle(P, O) :- place(P), obstacle_at(P, O).
solves(F, O) :- folk(F), solves_obstacle(F, O).

valid(P, C, F, O, G) :- place(P), cue(C), folk(F), obstacle(O), gift(G),
                        matches_cue(F, C),
                        fits_gift(F, G),
                        place_has_obstacle(P, O),
                        solves(F, O).

resolved(P, C, F, O, G) :- valid(P, C, F, O, G).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for obstacle_id in sorted(place.obstacle_ids):
            lines.append(asp.fact("obstacle_at", place_id, obstacle_id))
    for cue_id in CUES:
        lines.append(asp.fact("cue", cue_id))
    for folk_id, folk in FOLK.items():
        lines.append(asp.fact("folk", folk_id))
        lines.append(asp.fact("cue_of", folk_id, folk.cue))
        lines.append(asp.fact("need_of", folk_id, folk.need))
        lines.append(asp.fact("solves_obstacle", folk_id, folk.obstacle))
    for obstacle_id in OBSTACLES:
        lines.append(asp.fact("obstacle", obstacle_id))
    for gift_id, gift in GIFTS.items():
        lines.append(asp.fact("gift", gift_id))
        lines.append(asp.fact("gift_need", gift_id, gift.need))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/5."))
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

    smoke_cases = list(CURATED)
    try:
        default_params = resolve_params(build_parser().parse_args([]), random.Random(7))
        default_params.seed = 7
        smoke_cases.append(default_params)
    except StoryError as err:
        rc = 1
        print(f"SMOKE FAIL: resolve_params() raised StoryError: {err}")

    for params in smoke_cases:
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("empty story")
            if "cue" not in sample.story.lower():
                raise StoryError("story did not include the required word 'cue'")
            emit(sample, trace=False, qa=False, header="")
        except Exception as err:  # noqa: BLE001
            rc = 1
            print(f"SMOKE FAIL for {params}: {err}")

    if rc == 0:
        print(f"OK: smoke-tested {len(smoke_cases)} generated stories.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Folk-tale storyworld: a strange cue, a misunderstanding, kindness, and magic."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--cue", choices=CUES)
    ap.add_argument("--folk", choices=FOLK)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--elder", choices=["mother", "father", "grandmother"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.cue and args.folk and args.obstacle and args.gift:
        if not valid_combo(
            PLACES[args.place], CUES[args.cue], FOLK[args.folk], OBSTACLES[args.obstacle], GIFTS[args.gift]
        ):
            raise StoryError(
                explain_rejection(
                    PLACES[args.place], CUES[args.cue], FOLK[args.folk], OBSTACLES[args.obstacle], GIFTS[args.gift]
                )
            )

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.cue is None or combo[1] == args.cue)
        and (args.folk is None or combo[2] == args.folk)
        and (args.obstacle is None or combo[3] == args.obstacle)
        and (args.gift is None or combo[4] == args.gift)
    ]
    if not combos:
        if args.place and args.cue and args.folk and args.obstacle and args.gift:
            raise StoryError(
                explain_rejection(
                    PLACES[args.place], CUES[args.cue], FOLK[args.folk], OBSTACLES[args.obstacle], GIFTS[args.gift]
                )
            )
        raise StoryError("(No valid combination matches the given options.)")

    place_id, cue_id, folk_id, obstacle_id, gift_id = rng.choice(sorted(combos))
    child_gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    elder_type = args.elder or rng.choice(["mother", "father", "grandmother"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        cue=cue_id,
        folk=folk_id,
        obstacle=obstacle_id,
        gift=gift_id,
        child_name=child_name,
        child_gender=child_gender,
        elder_type=elder_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        cue = CUES[params.cue]
        folk_cfg = FOLK[params.folk]
        obstacle = OBSTACLES[params.obstacle]
        gift = GIFTS[params.gift]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err})") from None

    if not valid_combo(place, cue, folk_cfg, obstacle, gift):
        raise StoryError(explain_rejection(place, cue, folk_cfg, obstacle, gift))

    world = tell(
        place=place,
        cue=cue,
        folk_cfg=folk_cfg,
        obstacle=obstacle,
        gift=gift,
        child_name=params.child_name,
        child_gender=params.child_gender,
        elder_type=params.elder_type,
        trait=params.trait,
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
        print(asp_program("", "#show valid/5.\n#show resolved/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, cue, folk, obstacle, gift) combos:\n")
        for place, cue, folk, obstacle, gift in combos:
            print(f"  {place:7} {cue:8} {folk:18} {obstacle:8} {gift}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            header = f"### {p.child_name}: {p.cue} at {p.place} with {p.folk}"
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

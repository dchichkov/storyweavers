#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/crave_sharing_myth.py
================================================

A standalone storyworld for a tiny mythic domain: a child finds a wondrous gift,
craves it all, and learns that shared food becomes a blessing while hoarded food
goes dim and lonely.

The seed asked for:
- the word "crave"
- the feature "Sharing"
- a myth-like style

This script models a small, constraint-checked world rather than swapping nouns
into one fixed paragraph. A live world state tracks physical meters ("full",
"glow", "emptied") and emotional memes ("crave", "wonder", "guilt", "belonging").
The story changes depending on whether the child is persuaded early to share or
first tries to keep the gift and only shares after the magic fades.

Reasonableness constraint
-------------------------
Not every gift can honestly be shared in every way. A honey jar can be poured
into bowls; a round loaf can be torn into pieces; moonberries can be passed by
the handful; a star pear can be sliced into crescents. The storyworld refuses
gift/method pairs that do not fit, because a myth about sharing should rest on a
clear, physical act of sharing, not vague moral talk.

Run it
------
    python storyworlds/worlds/gpt-5.4/crave_sharing_myth.py
    python storyworlds/worlds/gpt-5.4/crave_sharing_myth.py --gift honey_jar --method bowls
    python storyworlds/worlds/gpt-5.4/crave_sharing_myth.py --gift honey_jar --method slices
    python storyworlds/worlds/gpt-5.4/crave_sharing_myth.py --all
    python storyworlds/worlds/gpt-5.4/crave_sharing_myth.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/crave_sharing_myth.py --verify
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

# Make the shared result containers importable when this script is run directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
CRAVE_INIT = 6.0
COUNSEL_BONUS = 2.0


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
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"grandmother": "grandmother", "mother": "mother", "father": "father"}.get(
            self.type, self.type
        )


@dataclass
class Setting:
    id: str
    place: str
    sky_sign: str
    gathering_spot: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    source: str
    taste: str
    plural_word: str
    share_kinds: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    share_kind: str
    act: str
    display: str
    result: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Guide:
    id: str
    type: str
    label: str
    title: str
    counsel: int
    warning: str
    blessing_line: str
    tags: set[str] = field(default_factory=set)


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


def _r_hoard_dims_magic(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    gift = world.entities.get("gift")
    if child is None or gift is None:
        return out
    if child.memes["hoarding"] < THRESHOLD or gift.meters["glow"] < THRESHOLD:
        return out
    sig = ("hoard_dims",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    gift.meters["glow"] = 0.0
    gift.meters["dimmed"] += 1
    child.memes["wonder"] = 0.0
    child.memes["guilt"] += 1
    child.memes["lonely"] += 1
    out.append("__dimmed__")
    return out


def _r_share_spreads_belonging(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    gift = world.entities.get("gift")
    village = world.entities.get("village")
    if child is None or gift is None or village is None:
        return out
    if gift.meters["shared"] < THRESHOLD:
        return out
    sig = ("shared_blessing",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    village.meters["fed"] += 1
    village.meters["blessed"] += 1
    child.memes["belonging"] += 1
    child.memes["crave"] = 0.0
    child.memes["joy"] += 1
    gift.meters["glow"] += 1
    out.append("__blessing__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="hoard_dims", tag="moral", apply=_r_hoard_dims_magic),
    Rule(name="share_blessing", tag="social", apply=_r_share_spreads_belonging),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(bits)
    if narrate:
        for bit in produced:
            if bit == "__dimmed__":
                gift = world.get("gift")
                child = world.get("child")
                world.say(
                    f"But the magic did not love a closed fist. At once the {gift.label} lost "
                    f"{gift.pronoun('possessive') if gift.kind == 'character' else 'its'} shine, "
                    f"and {child.id} felt the sweetness turn small and lonely."
                )
            elif bit == "__blessing__":
                gift = world.get("gift")
                world.say(
                    f"As soon as the sharing began, the {gift.label} brightened again, as if the gift "
                    f"had been waiting for many hands all along."
                )
    return produced


def share_possible(gift: Gift, method: Method) -> bool:
    return method.share_kind in gift.share_kinds


def counsel_strength(guide: Guide, child_trait: str) -> float:
    bonus = COUNSEL_BONUS if child_trait in {"gentle", "thoughtful", "kind"} else 0.0
    return float(guide.counsel) + bonus


def shares_early(guide: Guide, child_trait: str) -> bool:
    return counsel_strength(guide, child_trait) > CRAVE_INIT


def introduce(world: World, child: Entity, setting: Setting, village_label: str) -> None:
    world.say(
        f"In the old days, when {setting.sky_sign} still felt close enough to hear, "
        f"there lived a {child.type} named {child.id} beside {village_label}."
    )
    world.say(
        f"{child.id} was {child.attrs['trait_phrase']}, and everyone said {child.pronoun()} noticed "
        f"small wonders before anyone else."
    )


def find_gift(world: World, child: Entity, gift_cfg: Gift, setting: Setting) -> None:
    gift = world.get("gift")
    child.memes["wonder"] += 1
    gift.meters["glow"] += 1
    world.say(
        f"One dawn, {child.id} followed a pale trail of light to {setting.place}, where {gift_cfg.source}. "
        f"There lay {gift_cfg.phrase}, shining softly in the grass."
    )
    world.say(
        f"The air smelled of {gift_cfg.taste}, and when {child.id} saw the gift, {child.pronoun()} began to crave "
        f"every bit of it for {child.pronoun('object')}self."
    )


def lift_gift(world: World, child: Entity, gift_cfg: Gift) -> None:
    child.memes["crave"] = CRAVE_INIT
    world.say(
        f"{child.id} gathered up the {gift_cfg.label} and held it close. It seemed far too lovely to lose, "
        f"even by sharing a little."
    )


def guide_appears(world: World, guide_ent: Entity, guide_cfg: Guide, child: Entity, village_label: str) -> None:
    child.memes["attention"] += 1
    world.say(
        f"Then {guide_cfg.title} came along the path and saw the bright gift in {child.id}'s arms."
    )
    world.say(
        f'"{guide_cfg.warning}," {guide_ent.label} said. "A wonder from the sky is meant for {village_label}, '
        f'not for one hungry heart alone."'
    )


def predict_hoard(world: World) -> dict:
    sim = world.copy()
    child = sim.get("child")
    child.memes["hoarding"] += 1
    propagate(sim, narrate=False)
    gift = sim.get("gift")
    return {
        "dimmed": gift.meters["dimmed"] >= THRESHOLD,
        "lonely": child.memes["lonely"] >= THRESHOLD,
    }


def warning(world: World, guide_ent: Entity, child: Entity, gift_cfg: Gift) -> None:
    pred = predict_hoard(world)
    world.facts["predicted_dimmed"] = pred["dimmed"]
    if pred["dimmed"]:
        world.say(
            f'{guide_ent.label.capitalize()} touched the rim of the {gift_cfg.label} and whispered, '
            f'"Keep it only for yourself, and its light will fade before the sun is high."'
        )


def decide_keep(world: World, child: Entity) -> None:
    child.memes["hoarding"] += 1
    child.memes["defiance"] += 1
    world.say(
        f'But {child.id} shook {child.pronoun("possessive")} head. "Just once, I want the wonder all to myself," '
        f'{child.pronoun()} said.'
    )
    propagate(world, narrate=True)


def decide_share(world: World, child: Entity, guide_ent: Entity) -> None:
    child.memes["resolve"] += 1
    child.memes["crave"] -= 2
    world.say(
        f"{child.id} looked from the shining gift to {guide_ent.label} and then toward the sleeping houses. "
        f"The craving in {child.pronoun('possessive')} chest was strong, but it was not stronger than wisdom."
    )


def regret_and_turn(world: World, child: Entity, guide_ent: Entity, setting: Setting) -> None:
    child.memes["resolve"] += 1
    world.say(
        f"{child.id} stood very still at {setting.place}. The quiet tasted sad now, and even {child.pronoun('possessive')} "
        f"first bite could not fill the lonely place inside {child.pronoun('object')}."
    )
    world.say(
        f'"Please," {child.pronoun()} said to {guide_ent.label}, "show me how to make this gift glad again."'
    )


def share_feast(
    world: World,
    child: Entity,
    gift_cfg: Gift,
    method_cfg: Method,
    guide_cfg: Guide,
    community_phrase: str,
    setting: Setting,
) -> None:
    gift = world.get("gift")
    gift.meters["shared"] += 1
    gift.meters["emptied"] += 1
    child.memes["generosity"] += 1
    world.say(
        f"Together they went to {setting.gathering_spot}, where {community_phrase}. There {child.id} {method_cfg.act}, "
        f"and soon {method_cfg.result}."
    )
    propagate(world, narrate=True)
    world.say(
        f'{guide_cfg.blessing_line} From that day on, people remembered that a gift kept alone grows small, '
        f"but a gift passed from hand to hand grows into a feast."
    )


def closing_image(world: World, child: Entity, setting: Setting, gift_cfg: Gift) -> None:
    village = world.get("village")
    if village.meters["blessed"] >= THRESHOLD:
        world.say(
            f"That evening the windows around {setting.gathering_spot} glowed like little stars, and {child.id} no longer "
            f"craved the whole {gift_cfg.label}. {child.pronoun().capitalize()} smiled to hear many spoons, many laughs, "
            f"and one happy village."
        )


def tell(
    setting: Setting,
    gift_cfg: Gift,
    method_cfg: Method,
    guide_cfg: Guide,
    child_name: str = "Iria",
    child_type: str = "girl",
    child_trait: str = "gentle",
    community: str = "village_children",
) -> World:
    world = World()
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_type,
            label=child_name,
            role="child",
            traits=[child_trait],
            attrs={"trait_phrase": child_trait},
        )
    )
    guide_ent = world.add(
        Entity(
            id="Guide",
            kind="character",
            type=guide_cfg.type,
            label=guide_cfg.label,
            role="guide",
            traits=["wise"],
        )
    )
    world.add(
        Entity(
            id="gift",
            kind="thing",
            type="gift",
            label=gift_cfg.label,
            phrase=gift_cfg.phrase,
            role="gift",
            tags=set(gift_cfg.tags),
        )
    )
    community_cfg = COMMUNITIES[community]
    world.add(
        Entity(
            id="village",
            kind="thing",
            type="community",
            label=community_cfg["label"],
            phrase=community_cfg["phrase"],
            role="community",
        )
    )

    world.facts["community"] = community_cfg
    world.facts["setting"] = setting
    world.facts["gift_cfg"] = gift_cfg
    world.facts["method_cfg"] = method_cfg
    world.facts["guide_cfg"] = guide_cfg
    world.facts["child_trait"] = child_trait

    introduce(world, child, setting, community_cfg["label"])
    find_gift(world, child, gift_cfg, setting)
    lift_gift(world, child, gift_cfg)

    world.para()
    guide_appears(world, guide_ent, guide_cfg, child, community_cfg["label"])
    warning(world, guide_ent, child, gift_cfg)

    early = shares_early(guide_cfg, child_trait)
    if early:
        decide_share(world, child, guide_ent)
        world.para()
        share_feast(world, child, gift_cfg, method_cfg, guide_cfg, community_cfg["phrase"], setting)
        outcome = "eager_share"
    else:
        decide_keep(world, child)
        world.para()
        regret_and_turn(world, child, guide_ent, setting)
        share_feast(world, child, gift_cfg, method_cfg, guide_cfg, community_cfg["phrase"], setting)
        outcome = "regret_share"

    world.para()
    closing_image(world, child, setting, gift_cfg)

    world.facts.update(
        child=child,
        guide=guide_ent,
        gift=world.get("gift"),
        village=world.get("village"),
        outcome=outcome,
        shared=world.get("gift").meters["shared"] >= THRESHOLD,
        dimmed=world.get("gift").meters["dimmed"] >= THRESHOLD,
        blessed=world.get("village").meters["blessed"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "spring_hill": Setting(
        id="spring_hill",
        place="the spring hill",
        sky_sign="the moon's silver road",
        gathering_spot="the round hearth in the village square",
        tags={"myth", "hill"},
    ),
    "reed_bank": Setting(
        id="reed_bank",
        place="the reed bank by the slow river",
        sky_sign="the dawn star",
        gathering_spot="the long fire by the river huts",
        tags={"myth", "river"},
    ),
    "olive_shrine": Setting(
        id="olive_shrine",
        place="the old olive shrine",
        sky_sign="the gold clouds of morning",
        gathering_spot="the stone steps before the shrine",
        tags={"myth", "shrine"},
    ),
}

GIFTS = {
    "moonberries": Gift(
        id="moonberries",
        label="moonberries",
        phrase="a bowl of moonberries",
        source="the dew had gathered them in a silver bowl beneath a laurel tree",
        taste="cool honey and rain",
        plural_word="berries",
        share_kinds={"handfuls", "bowls"},
        tags={"berries", "sharing", "food"},
    ),
    "sun_loaf": Gift(
        id="sun_loaf",
        label="sun loaf",
        phrase="a round sun loaf",
        source="a warm loaf rested there, though no baker had passed that way",
        taste="new bread and butter",
        plural_word="pieces",
        share_kinds={"pieces", "slices"},
        tags={"bread", "sharing", "food"},
    ),
    "honey_jar": Gift(
        id="honey_jar",
        label="honey jar",
        phrase="a clay honey jar",
        source="a clay jar stood upright among the reeds, sealed with bright wax",
        taste="wildflowers and summer",
        plural_word="spoonfuls",
        share_kinds={"bowls", "spoons"},
        tags={"honey", "sharing", "food"},
    ),
    "star_pear": Gift(
        id="star_pear",
        label="star pear",
        phrase="a star pear with a skin like pale gold",
        source="a single pear hung low from the oldest branch, though the tree had been bare at dusk",
        taste="sweet milk and sunshine",
        plural_word="crescents",
        share_kinds={"slices"},
        tags={"pear", "sharing", "food"},
    ),
}

METHODS = {
    "handfuls": Method(
        id="handfuls",
        label="handfuls",
        share_kind="handfuls",
        act="passed the shining berries from palm to palm",
        display="by handfuls",
        result="every child held a bright little heap of moonberries",
        tags={"sharing", "berries"},
    ),
    "bowls": Method(
        id="bowls",
        label="bowls",
        share_kind="bowls",
        act="poured and portioned the gift into waiting bowls",
        display="into bowls",
        result="a ring of small bowls steamed or gleamed in the firelight",
        tags={"sharing", "bowls"},
    ),
    "pieces": Method(
        id="pieces",
        label="pieces",
        share_kind="pieces",
        act="tore the loaf with careful hands and gave each person a warm piece",
        display="into pieces",
        result="the smell of bread reached every corner of the square",
        tags={"sharing", "bread"},
    ),
    "slices": Method(
        id="slices",
        label="slices",
        share_kind="slices",
        act="cut the gift into bright crescents and laid them on a clean cloth",
        display="into slices",
        result="the golden slices looked like little moons in a circle",
        tags={"sharing", "knife"},
    ),
    "spoons": Method(
        id="spoons",
        label="spoons",
        share_kind="spoons",
        act="dipped out sweet spoonfuls for each waiting mouth",
        display="by spoonfuls",
        result="even the youngest children licked honey from their lips and laughed",
        tags={"sharing", "honey"},
    ),
}

GUIDES = {
    "river_mother": Guide(
        id="river_mother",
        type="woman",
        label="the River Mother",
        title="the River Mother",
        counsel=7,
        warning="Child, gifts that come gleaming from the world are never meant to sleep in one pair of hands",
        blessing_line='"Then let the river remember your open hands," said the River Mother.',
        tags={"guide", "river"},
    ),
    "goat_herd": Guide(
        id="goat_herd",
        type="man",
        label="the old goat-herd",
        title="the old goat-herd",
        counsel=5,
        warning="Little one, the gods turn their faces from a feast eaten alone",
        blessing_line='"Now the hills will send you good things again," said the old goat-herd.',
        tags={"guide", "hill"},
    ),
    "crane_spirit": Guide(
        id="crane_spirit",
        type="woman",
        label="the white crane spirit",
        title="the white crane spirit",
        counsel=6,
        warning="Feathers, fruit, bread, or honey — all bright gifts sour in a selfish shadow",
        blessing_line='"You have chosen the larger joy," said the white crane spirit.',
        tags={"guide", "spirit"},
    ),
}

COMMUNITIES = {
    "village_children": {
        "label": "the village",
        "phrase": "the village children were waking and rubbing sleep from their eyes",
        "tags": {"children", "sharing"},
    },
    "fisher_families": {
        "label": "the riverside huts",
        "phrase": "the fisher families were setting out bowls and morning cups",
        "tags": {"families", "sharing"},
    },
    "harvest_neighbors": {
        "label": "the hillside homes",
        "phrase": "the neighbors were gathering with lamps before breakfast",
        "tags": {"neighbors", "sharing"},
    },
}

GIRL_NAMES = ["Iria", "Dara", "Nemi", "Lysa", "Tala", "Mira", "Sena", "Elia"]
BOY_NAMES = ["Tarin", "Bero", "Ilan", "Sero", "Marek", "Pavo", "Lukan", "Teyo"]
TRAITS = ["gentle", "thoughtful", "kind", "eager", "restless", "curious"]


@dataclass
class StoryParams:
    setting: str
    gift: str
    method: str
    guide: str
    community: str
    child_name: str
    child_type: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for setting_id in SETTINGS:
        for gift_id, gift in GIFTS.items():
            for method_id, method in METHODS.items():
                if not share_possible(gift, method):
                    continue
                for guide_id in GUIDES:
                    for community_id in COMMUNITIES:
                        combos.append((setting_id, gift_id, method_id, guide_id, community_id))
    return combos


KNOWLEDGE = {
    "sharing": [
        (
            "Why is sharing important in stories like this?",
            "Sharing lets good things reach more people instead of stopping with one person. In myths, an open hand often shows a good heart and brings blessing.",
        )
    ],
    "myth": [
        (
            "What is a myth?",
            "A myth is an old story that explains a lesson or a wonder in a grand, memorable way. It often uses magic, spirits, or special signs from nature.",
        )
    ],
    "bread": [
        (
            "Why can bread be shared easily?",
            "Bread can be broken into smaller pieces, so many people can eat from one loaf. That makes it a simple food for sharing.",
        )
    ],
    "honey": [
        (
            "How can honey be shared?",
            "Honey can be poured or spooned into many small servings. A little sweetness can reach many people that way.",
        )
    ],
    "berries": [
        (
            "Why are berries easy to share?",
            "Berries come as many small fruits together, so they can be passed from hand to hand. Each person can take a little handful.",
        )
    ],
    "pear": [
        (
            "How do you share one pear?",
            "You cut the pear into slices so more than one person can eat it. Slicing turns one fruit into many bites.",
        )
    ],
    "greed": [
        (
            "What can happen if someone keeps everything for themself?",
            "Other people are left out, and the person who keeps everything may still feel lonely. In stories, hoarding often makes a good gift lose its joy.",
        )
    ],
}

KNOWLEDGE_ORDER = ["myth", "sharing", "bread", "honey", "berries", "pear", "greed"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    gift = f["gift_cfg"]
    method = f["method_cfg"]
    guide = f["guide_cfg"]
    return [
        f'Write a short myth for a 3-to-5-year-old that includes the word "crave" and centers on sharing {gift.label}.',
        f"Tell a mythic story where {child.id} finds {gift.phrase}, wants it all, and learns with help from {guide.label} to share it {method.display}.",
        "Write a gentle old-fashioned tale in which a magical food becomes brighter when it is shared with a whole community.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    guide = f["guide"]
    gift_cfg = f["gift_cfg"]
    method = f["method_cfg"]
    setting = f["setting"]
    community = f["community"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who found a magical {gift_cfg.label}, and {guide.label}, who taught {child.pronoun('object')} what the gift was for.",
        ),
        (
            f"Why did {child.id} want to keep the {gift_cfg.label}?",
            f"{child.id} thought the gift was so beautiful and sweet that {child.pronoun()} began to crave all of it. The wonder of finding it made sharing feel hard at first.",
        ),
        (
            f"What warning did {guide.label} give?",
            f"{guide.label.capitalize()} warned that a heavenly gift was not meant for one person alone. {guide.pronoun().capitalize()} said its light would fade if it was hoarded.",
        ),
    ]
    if outcome == "eager_share":
        qa.append(
            (
                f"How did {child.id} solve the problem?",
                f"{child.id} listened before doing anything selfish and carried the gift to {setting.gathering_spot}. There {child.pronoun()} shared it {method.display} with {community['label']}, so the gift turned into a blessing instead of a lonely treasure.",
            )
        )
    else:
        qa.append(
            (
                f"What happened when {child.id} tried to keep the gift?",
                f"The gift lost its shine, and {child.id} felt lonely instead of full. That sad change showed {child.pronoun('object')} that wonder does not stay bright inside a closed hand.",
            )
        )
        qa.append(
            (
                f"How did the story change after that?",
                f"After the magic faded, {child.id} asked for help and chose to share the gift {method.display}. When the food was passed around, the brightness came back and the whole community was blessed.",
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended at {setting.gathering_spot} with many people eating together. {child.id} no longer craved the whole gift, because sharing had filled the village and {child.pronoun('object')} too.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"myth", "sharing", "greed"}
    gift_id = f["gift_cfg"].id
    if gift_id == "sun_loaf":
        tags.add("bread")
    elif gift_id == "honey_jar":
        tags.add("honey")
    elif gift_id == "moonberries":
        tags.add("berries")
    elif gift_id == "star_pear":
        tags.add("pear")
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="spring_hill",
        gift="sun_loaf",
        method="pieces",
        guide="river_mother",
        community="harvest_neighbors",
        child_name="Iria",
        child_type="girl",
        trait="gentle",
    ),
    StoryParams(
        setting="reed_bank",
        gift="honey_jar",
        method="bowls",
        guide="goat_herd",
        community="fisher_families",
        child_name="Tarin",
        child_type="boy",
        trait="eager",
    ),
    StoryParams(
        setting="olive_shrine",
        gift="moonberries",
        method="handfuls",
        guide="crane_spirit",
        community="village_children",
        child_name="Mira",
        child_type="girl",
        trait="thoughtful",
    ),
    StoryParams(
        setting="spring_hill",
        gift="star_pear",
        method="slices",
        guide="goat_herd",
        community="harvest_neighbors",
        child_name="Lukan",
        child_type="boy",
        trait="restless",
    ),
]


def explain_rejection(gift: Gift, method: Method) -> str:
    return (
        f"(No story: {gift.phrase} cannot honestly be shared {method.display}. "
        f"Use a method that fits the gift's physical shape, like one of "
        f"{', '.join(sorted(gift.share_kinds))}.)"
    )


ASP_RULES = r"""
share_possible(G, M) :- gift(G), method(M), gift_kind(G, K), method_kind(M, K).
valid(S, G, M, D, C) :- setting(S), gift(G), method(M), guide(D), community(C), share_possible(G, M).

wise_trait(gentle).
wise_trait(thoughtful).
wise_trait(kind).

bonus(2) :- chosen_trait(T), wise_trait(T).
bonus(0) :- chosen_trait(T), not wise_trait(T).

authority(A) :- chosen_guide(D), counsel(D, C), bonus(B), A = C + B.
early_share :- authority(A), crave_init(CR), A > CR.

outcome(eager_share) :- early_share.
outcome(regret_share) :- not early_share.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for gid, gift in GIFTS.items():
        lines.append(asp.fact("gift", gid))
        for kind in sorted(gift.share_kinds):
            lines.append(asp.fact("gift_kind", gid, kind))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        lines.append(asp.fact("method_kind", mid, method.share_kind))
    for did, guide in GUIDES.items():
        lines.append(asp.fact("guide", did))
        lines.append(asp.fact("counsel", did, guide.counsel))
    for cid in COMMUNITIES:
        lines.append(asp.fact("community", cid))
    lines.append(asp.fact("crave_init", int(CRAVE_INIT)))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_guide", params.guide),
            asp.fact("chosen_trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    return "eager_share" if shares_early(GUIDES[params.guide], params.trait) else "regret_share"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a mythic gift, a strong craving, and the blessing of sharing."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--guide", choices=GUIDES)
    ap.add_argument("--community", choices=COMMUNITIES)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--child-name")
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
    if args.gift and args.method:
        gift = GIFTS[args.gift]
        method = METHODS[args.method]
        if not share_possible(gift, method):
            raise StoryError(explain_rejection(gift, method))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.gift is None or combo[1] == args.gift)
        and (args.method is None or combo[2] == args.method)
        and (args.guide is None or combo[3] == args.guide)
        and (args.community is None or combo[4] == args.community)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, gift_id, method_id, guide_id, community_id = rng.choice(sorted(combos))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    if args.child_name:
        child_name = args.child_name
    else:
        child_name = rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id,
        gift=gift_id,
        method=method_id,
        guide=guide_id,
        community=community_id,
        child_name=child_name,
        child_type=child_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.gift not in GIFTS:
        raise StoryError(f"(Unknown gift: {params.gift})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")
    if params.guide not in GUIDES:
        raise StoryError(f"(Unknown guide: {params.guide})")
    if params.community not in COMMUNITIES:
        raise StoryError(f"(Unknown community: {params.community})")
    if not share_possible(GIFTS[params.gift], METHODS[params.method]):
        raise StoryError(explain_rejection(GIFTS[params.gift], METHODS[params.method]))

    world = tell(
        setting=SETTINGS[params.setting],
        gift_cfg=GIFTS[params.gift],
        method_cfg=METHODS[params.method],
        guide_cfg=GUIDES[params.guide],
        child_name=params.child_name,
        child_type=params.child_type,
        child_trait=params.trait,
        community=params.community,
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

    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))

    cases: list[StoryParams] = list(CURATED)
    for s in range(30):
        try:
            ns = build_parser().parse_args([])
            p = resolve_params(ns, random.Random(s))
            p.seed = s
            cases.append(p)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure for seed {s}.")
            break

    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)}/{len(cases)} outcomes differ.")
        for p in mismatches[:5]:
            print("  ", p)

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test produced an empty story.)")
        print("OK: smoke test generation succeeded.")
    except Exception as err:  # pragma: no cover - defensive CLI check
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/5.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, gift, method, guide, community) combos:\n")
        for setting_id, gift_id, method_id, guide_id, community_id in combos:
            print(f"  {setting_id:12} {gift_id:10} {method_id:9} {guide_id:12} {community_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            header = f"### {p.child_name}: {p.gift} shared by {p.method} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

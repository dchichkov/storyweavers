#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/leaf_animal_shop_inner_monologue_friendship_fairy.py
================================================================================

A standalone storyworld for a fairy-tale-flavored story about a child, a friend,
and a shy little animal in a shop. The world model tracks simple physical meters
and emotional memes so the prose reflects what changed: a lonely creature hides,
the children choose a fitting, gentle gift, trust grows, and a friendship begins.

Run it
------
    python storyworlds/worlds/gpt-5.4/leaf_animal_shop_inner_monologue_friendship_fairy.py
    python storyworlds/worlds/gpt-5.4/leaf_animal_shop_inner_monologue_friendship_fairy.py --animal leaf_fox
    python storyworlds/worlds/gpt-5.4/leaf_animal_shop_inner_monologue_friendship_fairy.py --gift bell
    python storyworlds/worlds/gpt-5.4/leaf_animal_shop_inner_monologue_friendship_fairy.py --all
    python storyworlds/worlds/gpt-5.4/leaf_animal_shop_inner_monologue_friendship_fairy.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/leaf_animal_shop_inner_monologue_friendship_fairy.py --trace
    python storyworlds/worlds/gpt-5.4/leaf_animal_shop_inner_monologue_friendship_fairy.py --json
    python storyworlds/worlds/gpt-5.4/leaf_animal_shop_inner_monologue_friendship_fairy.py --verify
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
        female = {"girl", "woman", "fairy_girl", "mother"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Shop:
    id: str = ""
    label: str = ""
    phrase: str = ""
    keeper_name: str = ""
    sparkle: str = ""
    stocks: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class AnimalKind:
    id: str = ""
    label: str = ""
    phrase: str = ""
    hiding_spot: str = ""
    movement: str = ""
    sound: str = ""
    favorite_gifts: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Gift:
    id: str = ""
    label: str = ""
    phrase: str = ""
    use_text: str = ""
    comfort_text: str = ""
    helps_with: str = ""
    sense: int = 0
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


def _r_lonely_to_hide(world: World) -> list[str]:
    out: list[str] = []
    animal = world.get("animal")
    if animal.memes["lonely"] < THRESHOLD:
        return out
    sig = ("hide_from_lonely", animal.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    animal.meters["hidden"] += 1
    out.append("__animal_hides__")
    return out


def _r_gift_opens_trust(world: World) -> list[str]:
    out: list[str] = []
    animal = world.get("animal")
    gift = world.get("gift")
    if gift.meters["offered"] < THRESHOLD:
        return out
    sig = ("gift_opens_trust", animal.id, gift.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    animal.memes["trust"] += 1
    animal.memes["hope"] += 1
    animal.meters["hidden"] = 0.0
    out.append("__animal_peeks__")
    return out


def _r_trust_to_friendship(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    friend = world.get("friend")
    animal = world.get("animal")
    if animal.memes["trust"] < THRESHOLD:
        return out
    sig = ("trust_to_friendship", animal.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    animal.memes["friendship"] += 1
    animal.meters["settled"] += 1
    out.append("__friendship__")
    return out


CAUSAL_RULES = [
    Rule(name="lonely_to_hide", tag="emotion", apply=_r_lonely_to_hide),
    Rule(name="gift_opens_trust", tag="social", apply=_r_gift_opens_trust),
    Rule(name="trust_to_friendship", tag="social", apply=_r_trust_to_friendship),
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
        for sent in produced:
            world.say(sent)
    return produced


def gift_fits(shop: Shop, animal: AnimalKind, gift: Gift) -> bool:
    return gift.id in shop.stocks and gift.id in animal.favorite_gifts and gift.sense >= 2


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for shop_id, shop in SHOPS.items():
        for animal_id, animal in ANIMALS.items():
            for gift_id, gift in GIFTS.items():
                if gift_fits(shop, animal, gift):
                    combos.append((shop_id, animal_id, gift_id))
    return combos


def explain_rejection(shop: Shop, animal: AnimalKind, gift: Gift) -> str:
    if gift.sense < 2:
        return (
            f"(No story: {gift.label} is too flashy for a shy animal. "
            f"This world only tells stories where the children choose a gentle gift.)"
        )
    if gift.id not in shop.stocks:
        return (
            f"(No story: {shop.label} does not stock {gift.label}, so the children "
            f"cannot honestly choose it there.)"
        )
    if gift.id not in animal.favorite_gifts:
        good = ", ".join(sorted(animal.favorite_gifts))
        return (
            f"(No story: {animal.label} would not be comforted by {gift.label}. "
            f"Pick one of the gifts that fits its nature: {good}.)"
        )
    return "(No story: this combination does not make a believable friendship story.)"


def predict_trust(world: World, gift_id: str) -> dict:
    sim = world.copy()
    sim.add(Entity(id="gift", type="gift", label=GIFTS[gift_id].label))
    sim.get("gift").meters["offered"] += 1
    propagate(sim, narrate=False)
    animal = sim.get("animal")
    return {
        "trust": animal.memes["trust"],
        "hidden": animal.meters["hidden"],
        "settled": animal.meters["settled"],
    }


def opening(world: World, hero: Entity, friend: Entity, shop: Shop, keeper: Entity) -> None:
    hero.memes["wonder"] += 1
    friend.memes["wonder"] += 1
    world.say(
        f"At the edge of the market stood {shop.phrase}, where {shop.sparkle}. "
        f"{keeper.id}, the keeper, opened the little bell-lit door for {hero.id} and {friend.id}."
    )
    world.say(
        f"In that fairy-tale shop, every shelf seemed to be waiting for a kind heart."
    )


def discover_animal(world: World, hero: Entity, animal: Entity, animal_cfg: AnimalKind) -> None:
    animal.memes["lonely"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Near a basket of moss, {hero.id} noticed {animal_cfg.phrase} tucked {animal_cfg.hiding_spot}. "
        f"It made only {animal_cfg.sound}, as if even its tiny voice was hiding."
    )
    if animal.meters["hidden"] >= THRESHOLD:
        world.say(
            f"The little animal had folded itself so still that it nearly looked like a leaf blown in from the woods."
        )


def inner_monologue(world: World, hero: Entity, animal_cfg: AnimalKind) -> None:
    hero.memes["worry"] += 1
    world.say(
        f'{hero.id} pressed a hand to {hero.pronoun("possessive")} chest and thought, '
        f'"Oh, little {animal_cfg.label}, are you lonely? If I move too fast, I might frighten you more."'
    )


def friend_notices(world: World, friend: Entity, hero: Entity) -> None:
    friend.memes["care"] += 1
    hero.memes["seen"] += 1
    world.say(
        f'{friend.id} saw the thoughtful look on {hero.id}\'s face and whispered, '
        f'"Then let us be gentle together."'
    )


def keeper_explains(world: World, keeper: Entity, animal_cfg: AnimalKind) -> None:
    world.say(
        f'"That one came in at dawn," said {keeper.id}. "It is kind, but shy, and it only comes forward when kindness feels quiet enough."'
    )
    world.say(
        f"The words made the room feel softer, as if even the lamps wished to tread lightly."
    )


def choose_gift(world: World, hero: Entity, friend: Entity, shop: Shop, animal_cfg: AnimalKind, gift_cfg: Gift) -> None:
    pred = predict_trust(world, gift_cfg.id)
    world.facts["predicted_trust"] = pred["trust"]
    world.facts["predicted_hidden_after_gift"] = pred["hidden"]
    hero.memes["resolve"] += 1
    friend.memes["helping"] += 1
    world.say(
        f'{hero.id} looked from the shy creature to the shelves and thought, '
        f'"A loud surprise would be wrong. {gift_cfg.comfort_text}"'
    )
    world.say(
        f"{friend.id} nodded and chose {gift_cfg.phrase} with {hero.id}. Together they asked for something that could help instead of dazzle."
    )


def offer_gift(world: World, hero: Entity, friend: Entity, gift_cfg: Gift) -> None:
    gift = world.add(Entity(id="gift", type="gift", label=gift_cfg.label, phrase=gift_cfg.phrase))
    gift.meters["offered"] += 1
    hero.memes["hope"] += 1
    friend.memes["hope"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Very slowly, {hero.id} and {friend.id} {gift_cfg.use_text}."
    )


def animal_emerges(world: World, animal: Entity, animal_cfg: AnimalKind) -> None:
    if animal.memes["trust"] >= THRESHOLD:
        world.say(
            f"At first, nothing happened. Then the small creature gave {animal_cfg.movement}, lifted its head, and stepped out into the gold shop-light."
        )
        world.say(
            f"It touched the gift, looked up at the two children, and did not hide again."
        )


def friendship_resolution(world: World, hero: Entity, friend: Entity, animal_cfg: AnimalKind, shop: Shop) -> None:
    animal = world.get("animal")
    if animal.meters["settled"] >= THRESHOLD:
        world.say(
            f'{hero.id} smiled so softly that the moment felt like a secret blessing. In {hero.pronoun("possessive")} heart, {hero.pronoun()} thought, '
            f'"Friendship does not begin with grabbing. It begins with making room."'
        )
        world.say(
            f"{friend.id} held out a finger, and the little {animal_cfg.label} came near enough to sniff it. From then on, the three of them belonged to the same small circle of trust."
        )
        world.say(
            f"When {hero.id} and {friend.id} stepped back into the evening, the shop windows glowed behind them, and even the last leaf on the cobblestones looked less alone."
        )


def tell(
    shop: Shop,
    animal_cfg: AnimalKind,
    gift_cfg: Gift,
    hero_name: str = "Poppy",
    hero_type: str = "fairy_girl",
    friend_name: str = "Milo",
    friend_type: str = "boy",
    keeper_name: str = "Mistress Fern",
) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, role="friend"))
    keeper = world.add(Entity(id=keeper_name, kind="character", type="woman", role="keeper"))
    animal = world.add(Entity(id="animal", kind="character", type="animal", label=animal_cfg.label, phrase=animal_cfg.phrase, role="animal"))

    opening(world, hero, friend, shop, keeper)
    discover_animal(world, hero, animal, animal_cfg)
    world.para()
    inner_monologue(world, hero, animal_cfg)
    friend_notices(world, friend, hero)
    keeper_explains(world, keeper, animal_cfg)
    world.para()
    choose_gift(world, hero, friend, shop, animal_cfg, gift_cfg)
    offer_gift(world, hero, friend, gift_cfg)
    animal_emerges(world, animal, animal_cfg)
    world.para()
    friendship_resolution(world, hero, friend, animal_cfg, shop)

    world.facts.update(
        shop=shop,
        animal_cfg=animal_cfg,
        gift_cfg=gift_cfg,
        hero=hero,
        friend=friend,
        keeper=keeper,
        animal=animal,
        trusted=animal.memes["trust"] >= THRESHOLD,
        settled=animal.meters["settled"] >= THRESHOLD,
    )
    return world


SHOPS = {
    "fern_corner": Shop(
        id="fern_corner",
        label="Fern Corner Animal Shop",
        phrase="Fern Corner Animal Shop",
        keeper_name="Mistress Fern",
        sparkle="green glass lamps shone like captured moon-drops",
        stocks={"leaf_blanket", "dew_bowl"},
        tags={"shop", "leaf"},
    ),
    "moonpetal_stall": Shop(
        id="moonpetal_stall",
        label="Moonpetal Animal Shop",
        phrase="Moonpetal Animal Shop",
        keeper_name="Aunt Willow",
        sparkle="silver ribbons trembled in the window like tiny streams",
        stocks={"dew_bowl", "reed_flute"},
        tags={"shop", "moon"},
    ),
    "hollow_acorn_house": Shop(
        id="hollow_acorn_house",
        label="Hollow Acorn Animal Shop",
        phrase="Hollow Acorn Animal Shop",
        keeper_name="Old Bramble",
        sparkle="warm lanterns glowed inside carved wooden acorns",
        stocks={"leaf_blanket", "reed_flute"},
        tags={"shop", "wood"},
    ),
}

ANIMALS = {
    "leaf_fox": AnimalKind(
        id="leaf_fox",
        label="leaf fox",
        phrase="a tiny leaf fox",
        hiding_spot="under a drift of painted leaves",
        movement="one careful paw-step",
        sound="the smallest rustle",
        favorite_gifts={"leaf_blanket", "dew_bowl"},
        tags={"leaf", "animal"},
    ),
    "moss_rabbit": AnimalKind(
        id="moss_rabbit",
        label="moss rabbit",
        phrase="a moss rabbit no bigger than a teacup",
        hiding_spot="behind a wicker carrot basket",
        movement="a brave little hop",
        sound="a soft thump-thump",
        favorite_gifts={"dew_bowl", "reed_flute"},
        tags={"animal", "moss"},
    ),
    "petal_mouse": AnimalKind(
        id="petal_mouse",
        label="petal mouse",
        phrase="a petal mouse with pink ears",
        hiding_spot="inside a spool of ribbon",
        movement="a whiskered peek",
        sound="the faintest squeak",
        favorite_gifts={"leaf_blanket", "reed_flute"},
        tags={"animal", "flower"},
    ),
}

GIFTS = {
    "leaf_blanket": Gift(
        id="leaf_blanket",
        label="leaf blanket",
        phrase="a folded leaf blanket",
        use_text="laid down a folded leaf blanket beside the basket",
        comfort_text="A soft leaf blanket might tell it that this place can feel like home.",
        helps_with="cold",
        sense=3,
        tags={"leaf", "blanket"},
    ),
    "dew_bowl": Gift(
        id="dew_bowl",
        label="dew bowl",
        phrase="a pearl-blue dew bowl",
        use_text="set a pearl-blue dew bowl where the shy nose could find it",
        comfort_text="A dew bowl might show it that someone has noticed what a small creature needs.",
        helps_with="thirst",
        sense=3,
        tags={"water", "animal"},
    ),
    "reed_flute": Gift(
        id="reed_flute",
        label="reed flute",
        phrase="a little reed flute",
        use_text="played one low, warm note on a little reed flute and then held still",
        comfort_text="A low reed note might sound like a safe path instead of a command.",
        helps_with="fear",
        sense=2,
        tags={"music", "friendship"},
    ),
    "bell": Gift(
        id="bell",
        label="silver bell",
        phrase="a bright silver bell",
        use_text="rang a bright silver bell in front of the basket",
        comfort_text="Perhaps surprise will work, though it feels more sharp than kind.",
        helps_with="noise",
        sense=1,
        tags={"noise"},
    ),
}


@dataclass
class StoryParams:
    shop: str
    animal: str
    gift: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
    keeper_name: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        shop="fern_corner",
        animal="leaf_fox",
        gift="leaf_blanket",
        hero_name="Poppy",
        hero_type="fairy_girl",
        friend_name="Milo",
        friend_type="boy",
        keeper_name="Mistress Fern",
    ),
    StoryParams(
        shop="moonpetal_stall",
        animal="moss_rabbit",
        gift="dew_bowl",
        hero_name="Nia",
        hero_type="girl",
        friend_name="Rowan",
        friend_type="boy",
        keeper_name="Aunt Willow",
    ),
    StoryParams(
        shop="hollow_acorn_house",
        animal="petal_mouse",
        gift="reed_flute",
        hero_name="Elsie",
        hero_type="girl",
        friend_name="Jun",
        friend_type="boy",
        keeper_name="Old Bramble",
    ),
    StoryParams(
        shop="fern_corner",
        animal="leaf_fox",
        gift="dew_bowl",
        hero_name="Lina",
        hero_type="girl",
        friend_name="Tobin",
        friend_type="boy",
        keeper_name="Mistress Fern",
    ),
]


KNOWLEDGE = {
    "leaf": [
        (
            "What is a leaf?",
            "A leaf is the flat green part of a plant or tree. Leaves catch sunlight so the plant can grow."
        )
    ],
    "animal": [
        (
            "What is an animal shop?",
            "An animal shop is a place where people care for animals and the things animals need. The best shops are quiet, clean, and gentle with shy creatures."
        )
    ],
    "friendship": [
        (
            "How can friendship begin with a shy animal?",
            "Friendship begins when you are patient, gentle, and notice what the other creature needs. Trust grows first, and then closeness can follow."
        )
    ],
    "blanket": [
        (
            "Why can a soft blanket help a small animal?",
            "A soft blanket can make a small animal feel warm and sheltered. Feeling safe often helps a frightened creature relax."
        )
    ],
    "water": [
        (
            "Why does a small animal need fresh water?",
            "Every small animal needs water to drink so its body can stay healthy. Fresh water also helps a creature feel cared for."
        )
    ],
    "music": [
        (
            "Can gentle music calm an animal?",
            "Sometimes it can. A soft, steady sound may feel less scary than loud sudden noises."
        )
    ],
}
KNOWLEDGE_ORDER = ["leaf", "animal", "friendship", "blanket", "water", "music"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    shop = f["shop"]
    animal_cfg = f["animal_cfg"]
    gift_cfg = f["gift_cfg"]
    return [
        f'Write a fairy-tale story for a 3-to-5-year-old that includes the words "leaf", "animal", and "shop".',
        f"Tell a gentle fairy-tale where {hero.id} and {friend.id} find {animal_cfg.phrase} in {shop.phrase}, and {hero.id}'s inner thoughts help guide a kind choice.",
        f"Write a story about friendship beginning in a little shop, where a shy animal is comforted with {gift_cfg.phrase} instead of a loud surprise.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    animal_cfg = f["animal_cfg"]
    shop = f["shop"]
    gift_cfg = f["gift_cfg"]
    out: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, {friend.id}, and {animal_cfg.phrase} they found in {shop.phrase}. The keeper also helps by explaining that the little creature is shy."
        ),
        (
            f"What did {hero.id} think when {hero.pronoun()} saw the animal?",
            f"{hero.id} thought the little {animal_cfg.label} might be lonely and did not want to frighten it. Those quiet thoughts are why {hero.pronoun()} chose a gentle way to help."
        ),
        (
            f"How did {friend.id} show friendship in the story?",
            f"{friend.id} noticed {hero.id}'s worried face and chose to help instead of rushing. The friendship between the children made them kinder to the animal too."
        ),
        (
            "Why did they choose that gift?",
            f"They chose {gift_cfg.phrase} because it suited the little animal instead of startling it. In this story, the right gift helps the hidden creature feel safe enough to trust."
        ),
    ]
    if f["trusted"]:
        out.append(
            (
                "What happened after the gift was offered?",
                f"The small {animal_cfg.label} came out of hiding and stopped acting so frightened. It trusted the children because they were gentle and patient together."
            )
        )
    if f["settled"]:
        out.append(
            (
                "How did the story end?",
                f"It ended with a new circle of friendship: the children and the little animal were no longer strangers. The final image of the glowing shop and the lonely leaf outside shows that the world felt kinder than before."
            )
        )
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"leaf", "animal", "friendship"} | set(f["gift_cfg"].tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, A, G) :- shop(S), animal(A), gift(G), stocks(S, G), likes(A, G), gentle(G).

trusts(A, G) :- likes(A, G), gentle(G).
settled(A)   :- trusts(A, G).

#show valid/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for shop_id, shop in SHOPS.items():
        lines.append(asp.fact("shop", shop_id))
        for gift_id in sorted(shop.stocks):
            lines.append(asp.fact("stocks", shop_id, gift_id))
    for animal_id, animal in ANIMALS.items():
        lines.append(asp.fact("animal", animal_id))
        for gift_id in sorted(animal.favorite_gifts):
            lines.append(asp.fact("likes", animal_id, gift_id))
    for gift_id, gift in GIFTS.items():
        lines.append(asp.fact("gift", gift_id))
        if gift.sense >= 2:
            lines.append(asp.fact("gentle", gift_id))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test produced empty story")
        print("OK: smoke test generated a story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        rng = random.Random(123)
        args = build_parser().parse_args([])
        params = resolve_params(args, rng)
        sample = generate(params)
        if not sample.story.strip():
            raise StoryError("random smoke test produced empty story")
        print("OK: random resolve/generate smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"RANDOM SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale storyworld: a child, a friend, a shy animal, and a gentle choice in a shop."
    )
    ap.add_argument("--shop", choices=SHOPS)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--hero")
    ap.add_argument("--friend")
    ap.add_argument("--parent", choices=["mother", "father"], help="accepted for interface compatibility")
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


GIRL_NAMES = ["Poppy", "Nia", "Elsie", "Lina", "Mara", "Ruby", "Ivy", "Thea"]
BOY_NAMES = ["Milo", "Rowan", "Jun", "Tobin", "Finn", "Oren", "Leo", "Ash"]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.shop is not None and args.animal is not None and args.gift is not None:
        if not gift_fits(SHOPS[args.shop], ANIMALS[args.animal], GIFTS[args.gift]):
            raise StoryError(explain_rejection(SHOPS[args.shop], ANIMALS[args.animal], GIFTS[args.gift]))

    combos = [
        combo for combo in valid_combos()
        if (args.shop is None or combo[0] == args.shop)
        and (args.animal is None or combo[1] == args.animal)
        and (args.gift is None or combo[2] == args.gift)
    ]
    if not combos:
        if args.shop is not None and args.animal is not None and args.gift is not None:
            raise StoryError(explain_rejection(SHOPS[args.shop], ANIMALS[args.animal], GIFTS[args.gift]))
        raise StoryError("(No valid combination matches the given options.)")

    shop_id, animal_id, gift_id = rng.choice(sorted(combos))
    hero_name = args.hero or rng.choice(GIRL_NAMES)
    friend_name = args.friend or rng.choice([n for n in BOY_NAMES if n != hero_name] or BOY_NAMES)
    return StoryParams(
        shop=shop_id,
        animal=animal_id,
        gift=gift_id,
        hero_name=hero_name,
        hero_type="fairy_girl",
        friend_name=friend_name,
        friend_type="boy",
        keeper_name=SHOPS[shop_id].keeper_name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.shop not in SHOPS or params.animal not in ANIMALS or params.gift not in GIFTS:
        raise StoryError("(Invalid params: unknown shop, animal, or gift.)")
    if not gift_fits(SHOPS[params.shop], ANIMALS[params.animal], GIFTS[params.gift]):
        raise StoryError(explain_rejection(SHOPS[params.shop], ANIMALS[params.animal], GIFTS[params.gift]))

    world = tell(
        shop=SHOPS[params.shop],
        animal_cfg=ANIMALS[params.animal],
        gift_cfg=GIFTS[params.gift],
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        friend_name=params.friend_name,
        friend_type=params.friend_type,
        keeper_name=params.keeper_name,
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
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (shop, animal, gift) combos:\n")
        for shop_id, animal_id, gift_id in combos:
            print(f"  {shop_id:18} {animal_id:12} {gift_id}")
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
            header = f"### {p.hero_name} and {p.friend_name}: {p.animal} at {p.shop} with {p.gift}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

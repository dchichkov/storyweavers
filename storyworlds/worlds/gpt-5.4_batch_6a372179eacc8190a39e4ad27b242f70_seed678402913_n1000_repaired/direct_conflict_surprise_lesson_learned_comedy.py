#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/direct_conflict_surprise_lesson_learned_comedy.py
=============================================================================

A standalone story world about a child who is *too direct* at a tiny produce
stand, causing a funny conflict, until a surprising customer shows that honesty
works best when it is kind.

The domain is intentionally small and constraint-checked:

- The children are selling **odd-looking vegetables**.
- One child blurts out the flaw too bluntly.
- The other child feels embarrassed, so there is direct conflict.
- A grown-up helps them turn the same truth into a kinder, funnier message.
- A surprising customer arrives who wants exactly that odd produce.
- The lesson is stable across variants: **you can be direct without being mean**.

Run it
------
    python storyworlds/worlds/gpt-5.4/direct_conflict_surprise_lesson_learned_comedy.py
    python storyworlds/worlds/gpt-5.4/direct_conflict_surprise_lesson_learned_comedy.py --produce cucumbers --customer pickler
    python storyworlds/worlds/gpt-5.4/direct_conflict_surprise_lesson_learned_comedy.py --repair rude_sign
    python storyworlds/worlds/gpt-5.4/direct_conflict_surprise_lesson_learned_comedy.py --all
    python storyworlds/worlds/gpt-5.4/direct_conflict_surprise_lesson_learned_comedy.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/direct_conflict_surprise_lesson_learned_comedy.py --verify
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
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
SUCCESS_MIN = 5


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
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "chef"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    opener: str
    bustle: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Produce:
    id: str
    label: str
    phrase: str
    flaw: str
    blurting: str
    kinder: str
    basket: str
    likes: set[str] = field(default_factory=set)
    ending_image: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Customer:
    id: str
    label: str
    type: str
    phrase: str
    likes: set[str] = field(default_factory=set)
    eagerness: int = 2
    entrance: str = ""
    reason: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Repair:
    id: str
    sense: int
    charm: int
    line: str
    sign_text: str
    action: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_blunt_conflict(world: World) -> list[str]:
    sign = world.entities.get("sign")
    direct_child = world.entities.get("direct_child")
    partner = world.entities.get("partner")
    if not sign or not direct_child or not partner:
        return []
    if sign.meters["blunt"] < THRESHOLD:
        return []
    sig = ("blunt_conflict",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    partner.memes["embarrassment"] += 1
    direct_child.memes["stubborn"] += 1
    direct_child.memes["conflict"] += 1
    partner.memes["conflict"] += 1
    return ["__conflict__"]


def _r_kind_repair(world: World) -> list[str]:
    sign = world.entities.get("sign")
    direct_child = world.entities.get("direct_child")
    partner = world.entities.get("partner")
    if not sign or not direct_child or not partner:
        return []
    if sign.meters["kind"] < THRESHOLD:
        return []
    sig = ("kind_repair",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    direct_child.memes["understanding"] += 1
    partner.memes["hope"] += 1
    direct_child.memes["conflict"] = 0.0
    partner.memes["conflict"] = 0.0
    return []


def _r_customer_sale(world: World) -> list[str]:
    produce = world.entities.get("produce")
    customer = world.entities.get("customer")
    sign = world.entities.get("sign")
    direct_child = world.entities.get("direct_child")
    partner = world.entities.get("partner")
    if not produce or not customer or not sign or not direct_child or not partner:
        return []
    if produce.meters["matched"] < THRESHOLD or sign.meters["kind"] < THRESHOLD:
        return []
    sig = ("customer_sale",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    score = int(sign.meters["charm"] + customer.meters["eagerness"])
    sold = 3 if score >= SUCCESS_MIN else 1
    produce.meters["sold"] += sold
    direct_child.memes["relief"] += 1
    partner.memes["relief"] += 1
    direct_child.memes["joy"] += 1
    partner.memes["joy"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="blunt_conflict", tag="social", apply=_r_blunt_conflict),
    Rule(name="kind_repair", tag="social", apply=_r_kind_repair),
    Rule(name="customer_sale", tag="economic", apply=_r_customer_sale),
]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            produced = rule.apply(world)
            if produced:
                changed = True


def compatible_customer(produce: Produce, customer: Customer) -> bool:
    return bool(set(produce.likes) & set(customer.likes))


def sensible_repairs() -> list[Repair]:
    return [r for r in REPAIRS.values() if r.sense >= SENSE_MIN]


def sale_score(customer: Customer, repair: Repair) -> int:
    return customer.eagerness + repair.charm


def outcome_for(customer: Customer, repair: Repair) -> str:
    return "sold_out" if sale_score(customer, repair) >= SUCCESS_MIN else "sold_some"


def explain_customer_rejection(produce: Produce, customer: Customer) -> str:
    return (
        f"(No story: {customer.label} would not especially want {produce.phrase}. "
        f"The surprise only works when the customer's reason matches the produce's odd shape.)"
    )


def explain_repair_rejection(repair: Repair) -> str:
    return (
        f"(Refusing repair '{repair.id}': it scores too low on common sense "
        f"(sense={repair.sense} < {SENSE_MIN}). The story wants honest, kind comedy, not cruelty.)"
    )


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    if not sensible_repairs():
        return combos
    for setting_id in SETTINGS:
        for produce_id, produce in PRODUCE.items():
            for customer_id, customer in CUSTOMERS.items():
                if compatible_customer(produce, customer):
                    combos.append((setting_id, produce_id, customer_id))
    return combos


def open_stand(world: World, direct_child: Entity, partner: Entity, adult: Entity,
               setting: Setting, produce: Produce) -> None:
    crate = world.add(Entity(id="crate", type="crate", label="wooden crate", role="crate"))
    produce_ent = world.add(Entity(
        id="produce",
        type="produce",
        label=produce.label,
        phrase=produce.phrase,
        role="produce",
        tags=set(produce.tags),
    ))
    sign = world.add(Entity(id="sign", type="sign", label="sign", phrase="a little cardboard sign", role="sign"))
    world.say(
        f"{setting.opener} {direct_child.id} and {partner.id} stood behind a wobbling table with {produce.phrase} in a wooden crate."
    )
    world.say(
        f"{adult.label_word.capitalize()} had said they could try selling one small crate all by themselves, and that made both children stand a little taller."
    )
    world.say(setting.bustle)
    world.facts["crate"] = crate
    world.facts["sign"] = sign
    world.facts["produce_ent"] = produce_ent


def plan_sale(world: World, direct_child: Entity, partner: Entity, produce: Produce) -> None:
    direct_child.memes["confidence"] += 1
    partner.memes["confidence"] += 1
    world.say(
        f'{partner.id} carefully lined up the {produce.label}, but {direct_child.id} tapped the blank sign and whispered, '
        f'"We should be direct so people know what they are buying."'
    )
    world.say(f"For one moment, that sounded sensible.")


def blunt_pitch(world: World, direct_child: Entity, partner: Entity, produce: Produce) -> None:
    sign = world.get("sign")
    sign.meters["blunt"] += 1
    sign.meters["truth"] += 1
    propagate(world)
    world.say(
        f'Then {direct_child.id} grabbed the marker and wrote, "{produce.blurting}"'
    )
    world.say(
        f'Right after that, {direct_child.pronoun()} called to the path, "Come buy our {produce.label}! They are {produce.flaw}!"'
    )
    if partner.memes["embarrassment"] >= THRESHOLD:
        world.say(
            f"{partner.id}'s eyes went wide. \"That is true,\" {partner.pronoun()} said, \"but it is a little too direct.\""
        )


def quarrel(world: World, direct_child: Entity, partner: Entity) -> None:
    if partner.memes["conflict"] >= THRESHOLD or partner.memes["embarrassment"] >= THRESHOLD:
        world.say(
            f"{partner.id} tried to turn the sign around. {direct_child.id} tried to turn it back. For one silly second, the cardboard spun between them like a tiny steering wheel."
        )
        world.say(
            f'Neither child was yelling, but both were very sure. That was the conflict: {partner.id} wanted kind words, and {direct_child.id} wanted plain ones.'
        )


def grownup_reframe(world: World, adult: Entity, direct_child: Entity, partner: Entity,
                    produce: Produce, repair: Repair) -> None:
    sign = world.get("sign")
    sign.meters["kind"] += 1
    sign.meters["charm"] = float(repair.charm)
    sign.attrs["text"] = repair.sign_text
    propagate(world)
    adult.memes["calm"] += 1
    world.say(
        f"{adult.label_word.capitalize()} came over, read the sign, and had to hide a smile."
    )
    world.say(
        f'"The truth is useful," {adult.pronoun()} said, "but truth sounds better when it is wearing good manners."'
    )
    world.say(repair.line)
    world.say(
        f"{direct_child.id} looked at the crate, then at {partner.id}, and nodded. Together they changed the sign to say, \"{repair.sign_text}\""
    )
    world.say(repair.action)


def surprise_customer(world: World, direct_child: Entity, partner: Entity,
                      produce: Produce, customer_cfg: Customer) -> None:
    customer = world.add(Entity(
        id="customer",
        kind="character",
        type=customer_cfg.type,
        label=customer_cfg.label,
        phrase=customer_cfg.phrase,
        role="customer",
        tags=set(customer_cfg.tags),
    ))
    customer.meters["eagerness"] = float(customer_cfg.eagerness)
    produce_ent = world.get("produce")
    produce_ent.meters["matched"] += 1
    propagate(world)
    world.say(customer_cfg.entrance)
    world.say(
        f'"Wait," {customer.label} said, leaning close to the crate. "{customer_cfg.reason}"'
    )
    if produce_ent.meters["sold"] >= 3:
        world.say(
            f"{customer.label} bought a whole armful, and the funny sign made two more people stop and laugh kindly before buying some too."
        )
    else:
        world.say(
            f"{customer.label} bought the first bag, which felt almost magical after such a wobbly start."
        )


def ending(world: World, adult: Entity, direct_child: Entity, partner: Entity,
           setting: Setting, produce: Produce, customer_cfg: Customer, repair: Repair) -> None:
    outcome = "sold_out" if world.get("produce").meters["sold"] >= 3 else "sold_some"
    direct_child.memes["lesson"] += 1
    partner.memes["lesson"] += 1
    adult.memes["pride"] += 1
    world.say(
        f'When the little rush was over, {adult.label_word} bent down beside them. "You were right to be direct about what was true," {adult.pronoun()} said. "You just learned that direct and kind can walk together."'
    )
    world.say(
        f'{direct_child.id} grinned. "{repair.sign_text}"'
    )
    world.say(
        f'{partner.id} laughed. "That sounds much better than shouting about {produce.flaw}."'
    )
    if outcome == "sold_out":
        world.say(
            f"{setting.ending} By the time they packed up, the crate was empty except for one leaf, one coin under the table, and a marker with no cap."
        )
    else:
        world.say(
            f"{setting.ending} They still had some {produce.label} left, but now the children knew how to invite people over without poking feelings."
        )
    world.facts["outcome"] = outcome
    world.facts["lesson_text"] = "You can be direct and still be kind."
    world.facts["repair_text"] = repair.sign_text
    world.facts["surprise_reason"] = customer_cfg.reason


def tell(setting: Setting, produce: Produce, customer_cfg: Customer, repair: Repair,
         direct_name: str = "Ben", direct_gender: str = "boy",
         partner_name: str = "Lily", partner_gender: str = "girl",
         adult_type: str = "mother") -> World:
    world = World(setting=setting)
    direct_child = world.add(Entity(
        id=direct_name,
        kind="character",
        type=direct_gender,
        role="direct_child",
        traits=["honest", "eager"],
    ))
    partner = world.add(Entity(
        id=partner_name,
        kind="character",
        type=partner_gender,
        role="partner",
        traits=["careful", "kind"],
    ))
    adult = world.add(Entity(
        id="Adult",
        kind="character",
        type=adult_type,
        label="the grown-up",
        role="adult",
    ))

    open_stand(world, direct_child, partner, adult, setting, produce)
    plan_sale(world, direct_child, partner, produce)

    world.para()
    blunt_pitch(world, direct_child, partner, produce)
    quarrel(world, direct_child, partner)

    world.para()
    grownup_reframe(world, adult, direct_child, partner, produce, repair)

    world.para()
    surprise_customer(world, direct_child, partner, produce, customer_cfg)

    world.para()
    ending(world, adult, direct_child, partner, setting, produce, customer_cfg, repair)

    world.facts.update(
        setting=setting,
        produce_cfg=produce,
        customer_cfg=customer_cfg,
        repair_cfg=repair,
        direct_child=direct_child,
        partner=partner,
        adult=adult,
        conflict=partner.memes["embarrassment"] >= THRESHOLD,
        sold=int(world.get("produce").meters["sold"]),
        direct_too_sharp=True,
    )
    return world


SETTINGS = {
    "farm_gate": Setting(
        id="farm_gate",
        place="the farm gate",
        opener="On Saturday morning at the farm gate,",
        bustle="A bicycle bell rang down the lane, and a hen on the fence looked interested in everything.",
        ending="The lane smelled like dirt and dill, and even the hen looked pleased.",
        tags={"market"},
    ),
    "sidewalk": Setting(
        id="sidewalk",
        place="the sunny sidewalk",
        opener="On a bright afternoon on the sunny sidewalk,",
        bustle="A bus hissed at the corner, a dog sneezed, and the little table kept wobbling every time someone walked past.",
        ending="The afternoon light turned gold on the sidewalk, and the sign fluttered proudly against the crate.",
        tags={"market"},
    ),
    "school_fair": Setting(
        id="school_fair",
        place="the school fair",
        opener="At the school fair after lunch,",
        bustle="Paper streamers shook in the breeze, and somebody nearby kept missing the beanbag toss by exactly one inch.",
        ending="The fair sounded full of giggles and clapping as they carried the empty marker home.",
        tags={"market"},
    ),
}

PRODUCE = {
    "carrots": Produce(
        id="carrots",
        label="carrots",
        phrase="a crate of twisty carrots",
        flaw="twisty",
        blurting="TWISTY CARROTS",
        kinder="Funny carrots for soup and smiles",
        basket="funny carrots",
        likes={"soup", "odd_shapes"},
        ending_image="orange tops sticking out of a paper bag",
        tags={"carrot", "vegetable"},
    ),
    "cucumbers": Produce(
        id="cucumbers",
        label="cucumbers",
        phrase="a crate of bendy cucumbers",
        flaw="bendy",
        blurting="BENDY CUCUMBERS",
        kinder="Bendy cucumbers for crunchy pickles",
        basket="bendy cucumbers",
        likes={"pickles", "odd_shapes"},
        ending_image="green curls in a jar basket",
        tags={"cucumber", "vegetable"},
    ),
    "pumpkins": Produce(
        id="pumpkins",
        label="pumpkins",
        phrase="three lumpy little pumpkins",
        flaw="lumpy",
        blurting="LUMPY PUMPKINS",
        kinder="Lumpy pumpkins, lovely pies",
        basket="lumpy pumpkins",
        likes={"pie", "odd_shapes"},
        ending_image="round pumpkins with crooked stems",
        tags={"pumpkin", "vegetable"},
    ),
}

CUSTOMERS = {
    "soup_chef": Customer(
        id="soup_chef",
        label="the soup chef",
        type="chef",
        phrase="a chef with a striped bag",
        likes={"soup"},
        eagerness=2,
        entrance="Just then, a chef in a tall paper hat hurried over with a striped shopping bag.",
        reason="Twisty carrots are perfect for soup. I chop them anyway, and funny carrots make the best stories in my kitchen.",
        tags={"chef", "soup"},
    ),
    "pickler": Customer(
        id="pickler",
        label="Aunt June",
        type="aunt",
        phrase="a neighbor carrying empty pickle jars",
        likes={"pickles"},
        eagerness=3,
        entrance="Just then, Aunt June came along with three empty pickle jars clinking in her basket.",
        reason="Bendy cucumbers fit my pickle jars better than stiff ones do.",
        tags={"pickles"},
    ),
    "pie_baker": Customer(
        id="pie_baker",
        label="Mr. Bell",
        type="man",
        phrase="an old baker in a floury apron",
        likes={"pie"},
        eagerness=2,
        entrance="Just then, Mr. Bell from the bakery stopped by, still wearing a floury apron.",
        reason="Once a pumpkin is in a pie, nobody asks whether it was lumpy first.",
        tags={"pie"},
    ),
    "art_teacher": Customer(
        id="art_teacher",
        label="the art teacher",
        type="woman",
        phrase="the art teacher with a big canvas tote",
        likes={"odd_shapes"},
        eagerness=3,
        entrance="Just then, the art teacher wandered over, peering at the crate as if it were a tiny museum.",
        reason="Odd shapes are the most interesting shapes. My class is drawing vegetables today, and these are perfect models.",
        tags={"art", "odd_shapes"},
    ),
}

REPAIRS = {
    "kind_sign": Repair(
        id="kind_sign",
        sense=3,
        charm=2,
        line='"Try the same truth with a smile," the grown-up suggested.',
        sign_text="Funny shapes, fresh taste!",
        action="The new sign still told the truth, but now it sounded like an invitation instead of a poke.",
        qa_text="They rewrote the sign so it stayed honest but sounded friendly.",
        tags={"sign", "kindness", "honesty"},
    ),
    "recipe_sign": Repair(
        id="recipe_sign",
        sense=3,
        charm=3,
        line='"Tell people what the funny shape is good for," the grown-up suggested.',
        sign_text="Funny shapes for good soup, pickles, and pies!",
        action="Now the sign did more than point at the flaw. It gave the vegetables a job to be proud of.",
        qa_text="They changed the sign to explain what the vegetables were good for.",
        tags={"sign", "kindness", "honesty"},
    ),
    "joke_basket": Repair(
        id="joke_basket",
        sense=2,
        charm=2,
        line='"Let the basket do the joke, not your voices," the grown-up said.',
        sign_text="The Funny-Shape Basket",
        action="They grouped the odd vegetables together, and suddenly the whole crate looked cheerful instead of apologetic.",
        qa_text="They made a cheerful basket label so the honesty felt playful instead of mean.",
        tags={"sign", "kindness", "honesty"},
    ),
    "rude_sign": Repair(
        id="rude_sign",
        sense=1,
        charm=1,
        line='"Well, you could call them ugly," the grown-up joked, then immediately shook that idea away.',
        sign_text="WEIRD STUFF CHEAP",
        action="That wording would sting, so the world refuses it.",
        qa_text="They did not use a rude sign.",
        tags={"rude"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo", "Owen"]


@dataclass
class StoryParams:
    setting: str
    produce: str
    customer: str
    repair: str
    direct_name: str
    direct_gender: str
    partner_name: str
    partner_gender: str
    adult: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "honesty": [
        (
            "What does it mean to be direct?",
            "Being direct means saying something clearly and plainly. It can be helpful, but it should still sound kind."
        ),
        (
            "Can honesty and kindness go together?",
            "Yes. You can tell the truth and still choose gentle words, so the truth helps instead of hurting."
        ),
    ],
    "market": [
        (
            "What is a market stand?",
            "A market stand is a small table or booth where people sell things like fruit, vegetables, or bread."
        ),
    ],
    "carrot": [
        (
            "Do twisty carrots still taste like carrots?",
            "Yes. A twisty carrot can still taste fresh and sweet even if it is not perfectly straight."
        ),
    ],
    "cucumber": [
        (
            "Can a bendy cucumber still be good to eat?",
            "Yes. A cucumber can be curved and still be crisp and tasty."
        ),
    ],
    "pumpkin": [
        (
            "Does a lumpy pumpkin still work for pie?",
            "Yes. The shape on the outside does not stop the pumpkin inside from being good for pie."
        ),
    ],
    "pickles": [
        (
            "What are pickles?",
            "Pickles are cucumbers kept in a salty or vinegary liquid until they turn tangy and crunchy."
        ),
    ],
    "soup": [
        (
            "Why can funny-shaped vegetables still be good for soup?",
            "Soup vegetables get washed, cut, and cooked. Once they are chopped, the funny outside shape matters much less."
        ),
    ],
    "pie": [
        (
            "Why does shape matter less for pie pumpkins?",
            "Pie pumpkins are cut open and cooked down. The baker uses the inside, not the outside shape."
        ),
    ],
    "sign": [
        (
            "Why does a sign matter at a little stand?",
            "A sign tells people what is there and how to feel about it. Friendly words can make people curious enough to stop."
        ),
    ],
}
KNOWLEDGE_ORDER = ["honesty", "market", "carrot", "cucumber", "pumpkin", "pickles", "soup", "pie", "sign"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    produce = f["produce_cfg"]
    customer = f["customer_cfg"]
    return [
        f'Write a funny story for a 3-to-5-year-old that includes the word "direct" and is about children selling {produce.label}.',
        f"Tell a comedy story where one child is too direct at a tiny stand, another child disagrees, and a surprising customer proves there is a kinder way to tell the truth.",
        f"Write a short story with conflict, surprise, and a lesson learned, where {customer.label} ends up wanting the odd-looking {produce.label} after all.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    direct_child = f["direct_child"]
    partner = f["partner"]
    adult = f["adult"]
    produce = f["produce_cfg"]
    customer = f["customer_cfg"]
    repair = f["repair_cfg"]
    adult_word = adult.label_word

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {direct_child.id} and {partner.id}, two children running a tiny produce stand, and their {adult_word} who helps them. A surprising customer changes the whole mood later."
        ),
        (
            f"Why did {partner.id} get upset?",
            f"{direct_child.id} told the truth, but did it too sharply by calling the {produce.label} {produce.flaw} out loud. {partner.id} felt embarrassed because the words sounded like teasing instead of helping."
        ),
        (
            "What was the conflict?",
            f"The conflict was about how to speak. {direct_child.id} wanted to be direct, while {partner.id} wanted the truth to sound kinder."
        ),
        (
            f"How did {adult_word} help?",
            f"{adult_word.capitalize()} did not say the children had to hide the truth. Instead, {adult.pronoun()} helped them rewrite the sign so it stayed honest and also felt welcoming."
        ),
        (
            "What was the surprise?",
            f"The surprise was that {customer.label} wanted those odd-looking {produce.label} on purpose. {customer.reason}"
        ),
        (
            "What lesson did the children learn?",
            f"They learned that being direct is fine when it is also kind. The new sign worked better because it told the truth without poking fun."
        ),
    ]
    if f.get("outcome") == "sold_out":
        qa.append(
            (
                "How did the story end?",
                f"It ended with the crate nearly empty and everyone laughing in a good way. The kind, honest sign brought people over once the first customer stopped."
            )
        )
    else:
        qa.append(
            (
                "How did the story end?",
                f"It ended with at least one happy sale and a calmer feeling at the stand. Even though not everything sold, the children had learned a better way to talk to people."
            )
        )
    qa.append(
        (
            f"What did they change on the sign?",
            f'They changed it to "{repair.sign_text}". That let the sign stay honest while sounding friendly and funny.'
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"honesty", "market"}
    produce = f["produce_cfg"]
    customer = f["customer_cfg"]
    repair = f["repair_cfg"]
    tags |= set(produce.tags)
    tags |= set(customer.tags)
    if "sign" in repair.tags or repair.id in {"kind_sign", "recipe_sign", "joke_basket"}:
        tags.add("sign")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="farm_gate",
        produce="cucumbers",
        customer="pickler",
        repair="recipe_sign",
        direct_name="Ben",
        direct_gender="boy",
        partner_name="Lily",
        partner_gender="girl",
        adult="mother",
    ),
    StoryParams(
        setting="sidewalk",
        produce="carrots",
        customer="soup_chef",
        repair="kind_sign",
        direct_name="Mia",
        direct_gender="girl",
        partner_name="Max",
        partner_gender="boy",
        adult="father",
    ),
    StoryParams(
        setting="school_fair",
        produce="pumpkins",
        customer="pie_baker",
        repair="joke_basket",
        direct_name="Theo",
        direct_gender="boy",
        partner_name="Nora",
        partner_gender="girl",
        adult="mother",
    ),
    StoryParams(
        setting="sidewalk",
        produce="cucumbers",
        customer="art_teacher",
        repair="kind_sign",
        direct_name="Ava",
        direct_gender="girl",
        partner_name="Finn",
        partner_gender="boy",
        adult="father",
    ),
]


ASP_RULES = r"""
compatible(P, C) :- produce(P), customer(C), produce_like(P, T), customer_like(C, T).
sensible(R) :- repair(R), sense(R, S), sense_min(M), S >= M.
valid(S, P, C) :- setting(S), compatible(P, C).

repair_charm(V) :- chosen_repair(R), charm(R, V).
customer_eager(V) :- chosen_customer(C), eagerness(C, V).
score(S) :- repair_charm(R), customer_eager(C), S = R + C.

outcome(sold_out) :- score(S), success_min(M), S >= M.
outcome(sold_some) :- score(S), success_min(M), S < M.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id in SETTINGS:
        lines.append(asp.fact("setting", setting_id))
    for produce_id, produce in PRODUCE.items():
        lines.append(asp.fact("produce", produce_id))
        for tag in sorted(produce.likes):
            lines.append(asp.fact("produce_like", produce_id, tag))
    for customer_id, customer in CUSTOMERS.items():
        lines.append(asp.fact("customer", customer_id))
        lines.append(asp.fact("eagerness", customer_id, customer.eagerness))
        for tag in sorted(customer.likes):
            lines.append(asp.fact("customer_like", customer_id, tag))
    for repair_id, repair in REPAIRS.items():
        lines.append(asp.fact("repair", repair_id))
        lines.append(asp.fact("sense", repair_id, repair.sense))
        lines.append(asp.fact("charm", repair_id, repair.charm))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("success_min", SUCCESS_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_repair", params.repair),
        asp.fact("chosen_customer", params.customer),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a too-direct child, a funny conflict, and a kind surprise."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--produce", choices=PRODUCE)
    ap.add_argument("--customer", choices=CUSTOMERS)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--adult", choices=["mother", "father"])
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


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.produce and args.customer:
        produce = PRODUCE[args.produce]
        customer = CUSTOMERS[args.customer]
        if not compatible_customer(produce, customer):
            raise StoryError(explain_customer_rejection(produce, customer))
    if args.repair and REPAIRS[args.repair].sense < SENSE_MIN:
        raise StoryError(explain_repair_rejection(REPAIRS[args.repair]))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.produce is None or combo[1] == args.produce)
        and (args.customer is None or combo[2] == args.customer)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, produce_id, customer_id = rng.choice(sorted(combos))
    repair_id = args.repair or rng.choice(sorted(r.id for r in sensible_repairs()))
    direct_name, direct_gender = _pick_child(rng)
    partner_name, partner_gender = _pick_child(rng, avoid=direct_name)
    adult = args.adult or rng.choice(["mother", "father"])
    return StoryParams(
        setting=setting_id,
        produce=produce_id,
        customer=customer_id,
        repair=repair_id,
        direct_name=direct_name,
        direct_gender=direct_gender,
        partner_name=partner_name,
        partner_gender=partner_gender,
        adult=adult,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.produce not in PRODUCE:
        raise StoryError(f"(Unknown produce: {params.produce})")
    if params.customer not in CUSTOMERS:
        raise StoryError(f"(Unknown customer: {params.customer})")
    if params.repair not in REPAIRS:
        raise StoryError(f"(Unknown repair: {params.repair})")

    produce = PRODUCE[params.produce]
    customer = CUSTOMERS[params.customer]
    repair = REPAIRS[params.repair]

    if not compatible_customer(produce, customer):
        raise StoryError(explain_customer_rejection(produce, customer))
    if repair.sense < SENSE_MIN:
        raise StoryError(explain_repair_rejection(repair))

    world = tell(
        setting=SETTINGS[params.setting],
        produce=produce,
        customer_cfg=customer,
        repair=repair,
        direct_name=params.direct_name,
        direct_gender=params.direct_gender,
        partner_name=params.partner_name,
        partner_gender=params.partner_gender,
        adult_type=params.adult,
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

    py_valid = set(valid_combos())
    clingo_valid = set(asp_valid_combos())
    if py_valid == clingo_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_valid - py_valid:
            print("  only in clingo:", sorted(clingo_valid - py_valid))
        if py_valid - clingo_valid:
            print("  only in python:", sorted(py_valid - clingo_valid))

    py_sensible = {r.id for r in sensible_repairs()}
    clingo_sensible = set(asp_sensible())
    if py_sensible == clingo_sensible:
        print(f"OK: sensible repairs match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print("MISMATCH in sensible repairs:")
        print("  python:", sorted(py_sensible))
        print("  clingo:", sorted(clingo_sensible))

    cases = list(CURATED)
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure at seed {seed}.")
            break

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_for(CUSTOMERS[params.customer], REPAIRS[params.repair]):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True, header="smoke")
        if not sample.story.strip():
            raise StoryError("(Smoke test generated an empty story.)")
        print("OK: smoke test generate/emit passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible repairs: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, produce, customer) combos:\n")
        for setting_id, produce_id, customer_id in combos:
            print(f"  {setting_id:11} {produce_id:10} {customer_id}")
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
            header = f"### {p.direct_name} & {p.partner_name}: {p.produce} at {p.setting} ({p.customer}, {p.repair})"
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

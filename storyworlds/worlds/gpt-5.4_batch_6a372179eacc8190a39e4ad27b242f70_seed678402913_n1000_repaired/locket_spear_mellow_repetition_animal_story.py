#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/locket_spear_mellow_repetition_animal_story.py
========================================================================

A small animal-story world about a young animal, a lost locket, one unwise idea
with a spear, and a mellow helper who shows a gentler way.

The domain is intentionally narrow: a treasured locket gets snagged in one
tricky place, a child animal is tempted to jab at it with a little spear, and a
mellow grown-up or older helper either talks the child out of it or helps after
one hasty poke. The story uses repetition as part of the warning and the
resolution.

Run it
------
python storyworlds/worlds/gpt-5.4/locket_spear_mellow_repetition_animal_story.py
python storyworlds/worlds/gpt-5.4/locket_spear_mellow_repetition_animal_story.py --place reeds
python storyworlds/worlds/gpt-5.4/locket_spear_mellow_repetition_animal_story.py --retrieval patient_paws --place log_crack
python storyworlds/worlds/gpt-5.4/locket_spear_mellow_repetition_animal_story.py --all
python storyworlds/worlds/gpt-5.4/locket_spear_mellow_repetition_animal_story.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/locket_spear_mellow_repetition_animal_story.py --verify
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
SENSE_MIN = 2
CALM_MIN = 7


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "sister", "doe", "hen"}
        male = {"boy", "father", "uncle", "brother", "buck"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Animal:
    id: str
    species: str
    home: str
    likes: str
    tags: set[str] = field(default_factory=set)


@dataclass
class LostPlace:
    id: str
    label: str
    phrase: str
    snag_text: str
    warning_text: str
    ending_image: str
    difficulty: int
    risky: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Retrieval:
    id: str
    sense: int
    power: int
    setup: str
    action: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]


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


def _r_worry(world: World) -> list[str]:
    locket = world.get("locket")
    hero = world.get("hero")
    if locket.meters["snagged"] >= THRESHOLD:
        sig = ("worry",)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["worry"] += 1
    return []


def _r_spear_mishap(world: World) -> list[str]:
    locket = world.get("locket")
    hero = world.get("hero")
    if hero.meters["poked"] < THRESHOLD:
        return []
    sig = ("mishap",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    place = world.facts["place_cfg"]
    if place.risky:
        locket.meters["scratched"] += 1
        locket.meters["deeper"] += 1
        hero.memes["fear"] += 1
        hero.memes["regret"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="worry", tag="emotional", apply=_r_worry),
    Rule(name="spear_mishap", tag="physical", apply=_r_spear_mishap),
]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        before = len(world.fired)
        for rule in CAUSAL_RULES:
            rule.apply(world)
        changed = len(world.fired) != before


def danger_exists(place: LostPlace) -> bool:
    return place.risky


def sensible_retrievals() -> list[Retrieval]:
    return [r for r in RETRIEVALS.values() if r.sense >= SENSE_MIN]


def can_listen(trust: int, helper_age: int, hero_age: int) -> bool:
    authority = trust + (2 if helper_age > hero_age else 0) + 1
    return authority >= CALM_MIN


def is_retrieved(place: LostPlace, retrieval: Retrieval, after_poke: bool) -> bool:
    need = place.difficulty + (1 if after_poke else 0)
    return retrieval.power >= need


def predict_poke(place: LostPlace) -> dict:
    return {
        "scratched": place.risky,
        "deeper": place.risky,
    }


def introduce(world: World, hero: Entity, animal: Animal, helper: Entity) -> None:
    world.say(
        f"In {animal.home}, {hero.id} the little {animal.species} liked {animal.likes}. "
        f"Near the mossy path, {helper.id}, a mellow {helper.type}, liked doing things slowly and well."
    )


def gift_locket(world: World, hero: Entity) -> None:
    locket = world.get("locket")
    hero.memes["love"] += 1
    world.say(
        f"A shining locket hung on a blue ribbon around {hero.id}'s neck. "
        f"It had belonged to {hero.pronoun('possessive')} grandmother, so {hero.id} touched it again and again, "
        f"just to feel that it was there."
    )
    locket.meters["worn"] += 1


def lose_locket(world: World, hero: Entity, place: LostPlace) -> None:
    locket = world.get("locket")
    locket.meters["snagged"] += 1
    propagate(world)
    world.say(
        f"Then, with one hop too quick and one turn too bright, the ribbon slipped, "
        f"and the locket caught in {place.phrase}. {place.snag_text}"
    )


def want_spear(world: World, hero: Entity) -> None:
    hero.memes["impulse"] += 1
    spear = world.get("spear")
    world.say(
        f'{hero.id} gasped. "My locket! My locket!" {hero.pronoun()} cried. '
        f'Then {hero.pronoun()} spotted {spear.phrase} leaning by a stump. '
        f'"I can poke it out with the spear," {hero.pronoun()} said.'
    )


def warn(world: World, helper: Entity, hero: Entity, place: LostPlace) -> None:
    pred = predict_poke(place)
    world.facts["predicted"] = pred
    helper.memes["calm"] += 1
    world.say(
        f'{helper.id} lifted one soft paw. "Not with a poke, not with a prod, not with a spear," '
        f'{helper.pronoun()} said. "{place.warning_text}"'
    )


def back_down(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["relief"] += 1
    hero.memes["trust"] += 1
    world.say(
        f'{hero.id} looked at the spear, looked at the locket, and looked at {helper.id} once more. '
        f'"Not with a poke, not with a prod, not with a spear," {hero.pronoun()} repeated, softer this time. '
        f'Then {hero.pronoun()} set the spear down in the clover.'
    )


def poke_anyway(world: World, hero: Entity, place: LostPlace) -> None:
    hero.meters["poked"] += 1
    propagate(world)
    world.say(
        f"But {hero.id}'s paws were quicker than {hero.pronoun('possessive')} thoughts. "
        f"{hero.pronoun().capitalize()} reached with the spear and gave one hasty jab."
    )
    if place.risky:
        world.say(
            f"The locket did not come free. Instead, it slipped deeper, and the little gold heart got a scratch. "
            f'{hero.id} pulled the spear back at once. "Oh no," {hero.pronoun()} whispered.'
        )


def prepare_retrieval(world: World, helper: Entity, retrieval: Retrieval) -> None:
    world.say(
        f'{helper.id} did not scold. The mellow helper only breathed in, breathed out, '
        f'and {retrieval.setup}.'
    )


def retrieve_success(world: World, helper: Entity, hero: Entity, place: LostPlace, retrieval: Retrieval, after_poke: bool) -> None:
    locket = world.get("locket")
    locket.meters["snagged"] = 0.0
    locket.meters["retrieved"] += 1
    hero.memes["joy"] += 1
    hero.memes["relief"] += 1
    helper.memes["care"] += 1
    world.say(
        f"{helper.id} {retrieval.action}. Out came the locket at last."
    )
    if after_poke and locket.meters["scratched"] >= THRESHOLD:
        world.say(
            f'The scratch was tiny, but {hero.id} saw it. {helper.id} rubbed the locket clean with a leaf and said, '
            f'"A quick jab can make a small trouble bigger. A careful try can make a hard trouble smaller."'
        )
    else:
        world.say(
            f'{hero.id} let out a long breath. "Out at last, out at last, out at last," {hero.pronoun()} said.'
        )
    world.say(
        f"{hero.id} slipped the ribbon back around {hero.pronoun('possessive')} neck, and the locket rested warm and safe once more."
    )
    world.say(
        f"By evening, {place.ending_image}, and even the whole forest seemed mellow."
    )


def retrieve_fail(world: World, helper: Entity, hero: Entity, retrieval: Retrieval) -> None:
    hero.memes["sadness"] += 1
    world.say(
        f"{helper.id} {retrieval.action}, but the locket stayed hidden where it was. "
        f"The place had folded around it too tightly."
    )
    world.say(
        f'{hero.id} leaned against {helper.id} and sniffled. The mellow helper said, '
        f'"We will come back with brighter light and more help in the morning."'
    )
    world.say(
        "That night the moon shone on the empty ribbon, and the little forest felt very still."
    )


def closing_lesson(world: World, helper: Entity, hero: Entity) -> None:
    hero.memes["lesson"] += 1
    world.say(
        f'Before they walked home, {helper.id} tapped the spear with one toe and smiled. '
        f'"For berries, for leaves, for games in the mud perhaps. But not for a treasure on a ribbon."'
    )
    world.say(
        f'{hero.id} nodded. "Not with a poke, not with a prod, not with a spear," {hero.pronoun()} said again, '
        f'and this time the words sounded wise.'
    )


def tell(
    animal: Animal,
    place: LostPlace,
    retrieval: Retrieval,
    hero_name: str = "Pip",
    helper_name: str = "Moss",
    parent_type: str = "tortoise",
    trust: int = 5,
    hero_age: int = 4,
    helper_age: int = 7,
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type="child", label=hero_name, role="hero", age=hero_age))
    helper = world.add(Entity(id="helper", kind="character", type=parent_type, label=helper_name, role="helper", age=helper_age))
    locket = world.add(Entity(id="locket", type="locket", label="locket", phrase="the locket"))
    spear = world.add(Entity(id="spear", type="tool", label="spear", phrase="a little reed spear"))
    hero.attrs["display"] = hero_name
    helper.attrs["display"] = helper_name
    hero.memes["trust_seed"] = float(trust)
    world.facts.update(
        animal=animal,
        place_cfg=place,
        retrieval=retrieval,
        hero=hero,
        helper=helper,
        locket=locket,
        spear=spear,
        trust=trust,
    )

    introduce(world, hero, animal, helper)
    gift_locket(world, hero)

    world.para()
    lose_locket(world, hero, place)
    want_spear(world, hero)
    warn(world, helper, hero, place)

    listened = can_listen(trust, helper_age, hero_age)
    after_poke = False

    world.para()
    if listened:
        back_down(world, hero, helper)
    else:
        after_poke = True
        poke_anyway(world, hero, place)

    prepare_retrieval(world, helper, retrieval)
    success = is_retrieved(place, retrieval, after_poke)

    world.para()
    if success:
        retrieve_success(world, helper, hero, place, retrieval, after_poke)
        closing_lesson(world, helper, hero)
        outcome = "averted" if not after_poke else "rescued"
    else:
        retrieve_fail(world, helper, hero, retrieval)
        closing_lesson(world, helper, hero)
        outcome = "lost"

    world.facts.update(
        listened=listened,
        after_poke=after_poke,
        outcome=outcome,
        success=success,
        scratched=locket.meters["scratched"] >= THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    animal: str
    place: str
    retrieval: str
    hero_name: str
    helper_name: str
    helper_type: str
    trust: int
    hero_age: int
    helper_age: int
    seed: Optional[int] = None


ANIMALS = {
    "rabbit": Animal(
        id="rabbit",
        species="rabbit",
        home="a ferny glen",
        likes="hopping in circles and listening to creek songs",
        tags={"rabbit", "forest"},
    ),
    "squirrel": Animal(
        id="squirrel",
        species="squirrel",
        home="an oak grove",
        likes="racing along roots and counting acorns twice",
        tags={"squirrel", "forest"},
    ),
    "otter": Animal(
        id="otter",
        species="otter",
        home="a willow bend by the stream",
        likes="sliding on wet banks and watching silver fish flicker",
        tags={"otter", "stream"},
    ),
}

PLACES = {
    "reeds": LostPlace(
        id="reeds",
        label="reeds",
        phrase="the tall reeds by the pond",
        snag_text="The ribbon looped around two green stems and swayed just above the water.",
        warning_text="If you jab there, you will push it into the water.",
        ending_image="the pond reeds nodded in the dusk with one small gold glint safely gone from between them",
        difficulty=1,
        risky=True,
        tags={"pond", "reeds"},
    ),
    "berry_bush": LostPlace(
        id="berry_bush",
        label="berry bush",
        phrase="a blackberry bush",
        snag_text="The ribbon tangled among thorny twigs where shiny berries hung like beads.",
        warning_text="Those thorns will scratch the locket and tangle it even tighter.",
        ending_image="the thorn bush held only black berries and dew, not one lost treasure",
        difficulty=2,
        risky=True,
        tags={"bush", "thorns"},
    ),
    "log_crack": LostPlace(
        id="log_crack",
        label="log crack",
        phrase="the narrow crack of an old log",
        snag_text="The gold heart slid into the split wood until only one edge winked in the dark.",
        warning_text="A spear will wedge it deeper in the wood.",
        ending_image="the old log lay quiet, with crickets singing over the place where the locket had been",
        difficulty=3,
        risky=True,
        tags={"log", "wood"},
    ),
    "sunny_path": LostPlace(
        id="sunny_path",
        label="sunny path",
        phrase="the sunny path",
        snag_text="Nothing there could catch a ribbon at all.",
        warning_text="There is nothing to poke there.",
        ending_image="the path stayed bright and empty",
        difficulty=0,
        risky=False,
        tags={"path"},
    ),
}

RETRIEVALS = {
    "patient_paws": Retrieval(
        id="patient_paws",
        sense=2,
        power=1,
        setup="knelt close and used two patient paws",
        action="used two patient paws to loosen the ribbon a little at a time",
        qa_text="used two patient paws to loosen the ribbon",
        tags={"paws", "gentle"},
    ),
    "hook_branch": Retrieval(
        id="hook_branch",
        sense=3,
        power=2,
        setup="bent a fallen twig into a tiny hook",
        action="slipped the hook under the ribbon and lifted carefully",
        qa_text="lifted the ribbon with a tiny hooked branch",
        tags={"branch", "gentle"},
    ),
    "ribbon_loop": Retrieval(
        id="ribbon_loop",
        sense=3,
        power=4,
        setup="threaded a longer ribbon through a forked stick",
        action="looped the longer ribbon under the locket and drew it up slowly, slowly, slowly",
        qa_text="looped a longer ribbon under the locket and drew it up slowly",
        tags={"ribbon", "careful"},
    ),
    "shake_log": Retrieval(
        id="shake_log",
        sense=1,
        power=1,
        setup="gripped the place and gave it a hard shake",
        action="shook and shook and shook",
        qa_text="shook the place hard",
        tags={"rough"},
    ),
}

HERO_NAMES = ["Pip", "Nim", "Tuck", "Mimi", "Dot", "Bram"]
HELPER_NAMES = ["Moss", "Fern", "Willow", "Pebble", "Clover", "Tansy"]
HELPER_TYPES = ["tortoise", "badger", "beaver"]
CURATED = [
    StoryParams(
        animal="rabbit",
        place="reeds",
        retrieval="patient_paws",
        hero_name="Pip",
        helper_name="Moss",
        helper_type="tortoise",
        trust=8,
        hero_age=4,
        helper_age=7,
    ),
    StoryParams(
        animal="squirrel",
        place="berry_bush",
        retrieval="hook_branch",
        hero_name="Dot",
        helper_name="Fern",
        helper_type="badger",
        trust=4,
        hero_age=5,
        helper_age=6,
    ),
    StoryParams(
        animal="otter",
        place="log_crack",
        retrieval="ribbon_loop",
        hero_name="Tuck",
        helper_name="Willow",
        helper_type="beaver",
        trust=6,
        hero_age=4,
        helper_age=8,
    ),
    StoryParams(
        animal="rabbit",
        place="log_crack",
        retrieval="hook_branch",
        hero_name="Mimi",
        helper_name="Pebble",
        helper_type="tortoise",
        trust=3,
        hero_age=5,
        helper_age=6,
    ),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for animal in ANIMALS:
        for place_id, place in PLACES.items():
            if not danger_exists(place):
                continue
            for retrieval_id, retrieval in RETRIEVALS.items():
                if retrieval.sense >= SENSE_MIN:
                    combos.append((animal, place_id, retrieval_id))
    return combos


def explain_place(place: LostPlace) -> str:
    return (
        f"(No story: {place.label} is not a real snagging danger for a locket here. "
        f"The world needs a place where a spear would make the problem worse.)"
    )


def explain_retrieval(rid: str) -> str:
    retrieval = RETRIEVALS[rid]
    better = ", ".join(sorted(r.id for r in sensible_retrievals()))
    return (
        f"(Refusing retrieval '{rid}': it scores too low on common sense "
        f"(sense={retrieval.sense} < {SENSE_MIN}). Try a gentler method such as {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    listened = can_listen(params.trust, params.helper_age, params.hero_age)
    after_poke = not listened
    success = is_retrieved(PLACES[params.place], RETRIEVALS[params.retrieval], after_poke)
    if success and not after_poke:
        return "averted"
    if success and after_poke:
        return "rescued"
    return "lost"


KNOWLEDGE = {
    "locket": [
        (
            "What is a locket?",
            "A locket is a little piece of jewelry that opens or hangs on a ribbon or chain. People often keep it because it reminds them of someone they love.",
        )
    ],
    "spear": [
        (
            "What is a spear?",
            "A spear is a long, pointed tool. Because the tip is sharp, it is not a good toy and it is not safe for solving delicate problems.",
        )
    ],
    "mellow": [
        (
            "What does mellow mean?",
            "Mellow means calm, gentle, and not harsh. A mellow helper speaks softly and does not rush.",
        )
    ],
    "reeds": [
        (
            "What are reeds?",
            "Reeds are tall water plants that grow near ponds and streams. Ribbons and strings can catch around their stems.",
        )
    ],
    "thorns": [
        (
            "Why are thorns tricky?",
            "Thorns are sharp little points on some plants. They can scratch skin or snag ribbons and cloth.",
        )
    ],
    "careful": [
        (
            "Why can going slowly help with a tricky problem?",
            "Going slowly helps you see what is caught and where it is caught. Careful hands can free something without making the trouble bigger.",
        )
    ],
    "pond": [
        (
            "Why can things get lost near a pond?",
            "Near a pond, things can slip into water or tangle in plants. Wet edges are also slippery, so rushing is a poor idea.",
        )
    ],
    "wood": [
        (
            "Why can a crack in a log hold things tightly?",
            "Wood cracks can pinch small objects. If you push the object the wrong way, it can slide deeper into the narrow space.",
        )
    ],
}

KNOWLEDGE_ORDER = ["locket", "spear", "mellow", "reeds", "thorns", "pond", "wood", "careful"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    place = f["place_cfg"]
    return [
        'Write a short animal story for a 3-to-5-year-old that includes the words "locket", "spear", and "mellow", and uses repetition in the warning.',
        f"Tell a gentle forest story where {hero.label}, a young {f['animal'].species}, loses a locket in {place.phrase} and wants to use a spear, but {helper.label}, a mellow {helper.type}, teaches a calmer way.",
        'Write a TinyStories-style animal tale with a repeated line like "Not with a poke, not with a prod, not with a spear," and end with an image that shows the forest is calm again.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    animal = f["animal"]
    place = f["place_cfg"]
    retrieval = f["retrieval"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, a little {animal.species}, and {helper.label}, a mellow {helper.type}. They are trying to get a treasured locket back.",
        ),
        (
            "Where did the locket get stuck?",
            f"The locket got stuck in {place.phrase}. That place could hold the ribbon tightly, which is why the problem felt urgent.",
        ),
        (
            f"Why did {helper.label} say not to use the spear?",
            f"{helper.label} knew a quick jab would make the trouble worse. In this place, the spear could push the locket deeper or scratch it instead of freeing it.",
        ),
    ]
    if f["listened"]:
        qa.append(
            (
                f"What did {hero.label} do after the warning?",
                f"{hero.label} listened and put the spear down. The repeated warning slowed {hero.pronoun('object')} enough to choose the careful plan instead.",
            )
        )
    else:
        qa.append(
            (
                f"What happened when {hero.label} used the spear?",
                f"{hero.label} gave one hasty jab, and the locket slipped deeper instead of coming free. That is why {hero.label} felt scared and sorry right away.",
            )
        )
    if outcome in {"averted", "rescued"}:
        qa.append(
            (
                "How did they get the locket back?",
                f"{helper.label} {retrieval.qa_text}. The gentle method worked because it matched the place better than a sharp, rushing spear.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the locket safe again and the forest feeling mellow. The ending image shows that calm, careful actions changed the trouble into relief.",
            )
        )
    else:
        qa.append(
            (
                "Did they get the locket back right away?",
                f"No. Even the careful try was not strong enough that day, so the locket stayed hidden for the night. Still, the helper made a safer plan for morning instead of letting anyone keep jabbing with the spear.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"locket", "spear", "mellow", "careful"}
    place = world.facts["place_cfg"]
    if place.id == "reeds":
        tags |= {"reeds", "pond"}
    if place.id == "berry_bush":
        tags |= {"thorns"}
    if place.id == "log_crack":
        tags |= {"wood"}
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
    for ent in list(world.entities.values()):
        bits = []
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.age:
            bits.append(f"age={ent.age}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    lines.append(f"  outcome: {world.facts.get('outcome')}")
    return "\n".join(lines)


ASP_RULES = r"""
dangerous_place(P) :- place(P), risky(P).
sensible(R) :- retrieval(R), sense(R,S), sense_min(M), S >= M.
valid(A,P,R) :- animal(A), dangerous_place(P), sensible(R).

listened :- trust(T), helper_age(HA), hero_age(HR), T + 1 + bonus(B) >= calm_min,
            older(HA, HR, B).
older(HA, HR, 2) :- helper_age(HA), hero_age(HR), HA > HR.
older(HA, HR, 0) :- helper_age(HA), hero_age(HR), HA <= HR.

after_poke :- not listened.
need(D) :- chosen_place(P), difficulty(P,D), listened.
need(D + 1) :- chosen_place(P), difficulty(P,D), after_poke.
success :- chosen_retrieval(R), power(R,P), need(N), P >= N.

outcome(averted) :- listened, success.
outcome(rescued) :- after_poke, success.
outcome(lost) :- not success.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for aid in ANIMALS:
        lines.append(asp.fact("animal", aid))
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("difficulty", pid, place.difficulty))
        if place.risky:
            lines.append(asp.fact("risky", pid))
    for rid, retrieval in RETRIEVALS.items():
        lines.append(asp.fact("retrieval", rid))
        lines.append(asp.fact("sense", rid, retrieval.sense))
        lines.append(asp.fact("power", rid, retrieval.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("calm_min", CALM_MIN))
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

    extra = "\n".join(
        [
            asp.fact("chosen_place", params.place),
            asp.fact("chosen_retrieval", params.retrieval),
            asp.fact("trust", params.trust),
            asp.fact("hero_age", params.hero_age),
            asp.fact("helper_age", params.helper_age),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def _smoke_story() -> None:
    sample = generate(CURATED[0])
    if not sample.story or "locket" not in sample.story or "spear" not in sample.story:
        raise StoryError("(Smoke test failed: expected story words missing.)")
    _ = sample.to_dict()


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_sens = {r.id for r in sensible_retrievals()}
    asp_sens = set(asp_sensible())
    if py_sens == asp_sens:
        print(f"OK: sensible retrievals match ({sorted(py_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible retrievals: clingo={sorted(asp_sens)} python={sorted(py_sens)}")

    cases = list(CURATED)
    for seed in range(100):
        try:
            args = build_parser().parse_args([])
            params = resolve_params(args, random.Random(seed))
            cases.append(params)
        except StoryError:
            continue

    bad = 0
    for params in cases:
        py = outcome_of(params)
        cl = asp_outcome(params)
        if py != cl:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        _smoke_story()
        print("OK: smoke story generation passed.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal story world: a lost locket, a spear that should not be used, and a mellow helper."
    )
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--retrieval", choices=RETRIEVALS)
    ap.add_argument("--hero-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=HELPER_TYPES)
    ap.add_argument("--trust", type=int, choices=list(range(0, 11)))
    ap.add_argument("--hero-age", type=int, choices=[3, 4, 5, 6])
    ap.add_argument("--helper-age", type=int, choices=[5, 6, 7, 8, 9])
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
    if args.place is not None and not danger_exists(PLACES[args.place]):
        raise StoryError(explain_place(PLACES[args.place]))
    if args.retrieval is not None and RETRIEVALS[args.retrieval].sense < SENSE_MIN:
        raise StoryError(explain_retrieval(args.retrieval))
    combos = [
        combo
        for combo in valid_combos()
        if (args.animal is None or combo[0] == args.animal)
        and (args.place is None or combo[1] == args.place)
        and (args.retrieval is None or combo[2] == args.retrieval)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    animal, place, retrieval = rng.choice(sorted(combos))
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    helper_name = args.helper_name or rng.choice([n for n in HELPER_NAMES if n != hero_name] or HELPER_NAMES)
    helper_type = args.helper_type or rng.choice(HELPER_TYPES)
    trust = args.trust if args.trust is not None else rng.randint(2, 9)
    hero_age = args.hero_age if args.hero_age is not None else rng.choice([3, 4, 5, 6])
    helper_age = args.helper_age if args.helper_age is not None else rng.choice([age for age in [5, 6, 7, 8, 9] if age >= hero_age])
    return StoryParams(
        animal=animal,
        place=place,
        retrieval=retrieval,
        hero_name=hero_name,
        helper_name=helper_name,
        helper_type=helper_type,
        trust=trust,
        hero_age=hero_age,
        helper_age=helper_age,
    )


def generate(params: StoryParams) -> StorySample:
    if params.animal not in ANIMALS:
        raise StoryError(f"(Unknown animal: {params.animal})")
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.retrieval not in RETRIEVALS:
        raise StoryError(f"(Unknown retrieval: {params.retrieval})")
    if not danger_exists(PLACES[params.place]):
        raise StoryError(explain_place(PLACES[params.place]))
    if RETRIEVALS[params.retrieval].sense < SENSE_MIN:
        raise StoryError(explain_retrieval(params.retrieval))

    world = tell(
        animal=ANIMALS[params.animal],
        place=PLACES[params.place],
        retrieval=RETRIEVALS[params.retrieval],
        hero_name=params.hero_name,
        helper_name=params.helper_name,
        parent_type=params.helper_type,
        trust=params.trust,
        hero_age=params.hero_age,
        helper_age=params.helper_age,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible retrievals: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (animal, place, retrieval) combos:\n")
        for animal, place, retrieval in combos:
            print(f"  {animal:8} {place:11} {retrieval}")
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
            header = f"### {p.hero_name}: {p.place} with {p.retrieval} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

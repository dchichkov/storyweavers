#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/yorkie_cutter_sharing_flashback_lesson_learned_tall.py
=================================================================================

A standalone storyworld for a child-facing Tall Tale about a tiny yorkie, one
oversized cutter, a moment of sharing, a flashback, and a lesson learned.

The world models a giant baking day in exaggerated storybook style:
a child and a friend are making enormous treats for a town gathering, but they
have only one special cutter. If the child shares it, teamwork fills the trays.
If the child refuses and works alone, the waiting dough begins to dry; with some
dough-and-cutter combinations the cutter jams badly and the batch flops. A
flashback to an earlier selfish mistake gives the child a chance to choose
better this time.

Run it
------
    python storyworlds/worlds/gpt-5.4/yorkie_cutter_sharing_flashback_lesson_learned_tall.py
    python storyworlds/worlds/gpt-5.4/yorkie_cutter_sharing_flashback_lesson_learned_tall.py --all
    python storyworlds/worlds/gpt-5.4/yorkie_cutter_sharing_flashback_lesson_learned_tall.py --qa
    python storyworlds/worlds/gpt-5.4/yorkie_cutter_sharing_flashback_lesson_learned_tall.py --verify
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
        return {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    opening: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Dough:
    id: str
    label: str
    phrase: str
    treat: str
    firmness: int
    drying: int
    tags: set[str] = field(default_factory=set)


@dataclass
class CutterCfg:
    id: str
    label: str
    phrase: str
    shape: str
    demand: int
    boast: str
    imprint: str
    tags: set[str] = field(default_factory=set)


@dataclass
class PastEvent:
    id: str
    object_label: str
    setting: str
    mistake: str
    loss: str
    lesson: str
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


def _r_dry(world: World) -> list[str]:
    dough = world.get("dough")
    if dough.meters["waiting"] < THRESHOLD:
        return []
    sig = ("dry", int(dough.meters["waiting"]))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    pace = int(dough.attrs.get("drying", 1))
    dough.meters["dry"] += float(pace)
    hero = world.get("hero")
    hero.memes["worry"] += 1
    return []


def _r_jam(world: World) -> list[str]:
    dough = world.get("dough")
    cutter = world.get("cutter")
    if dough.meters["dry"] < THRESHOLD or cutter.meters["used"] < THRESHOLD:
        return []
    sig = ("jam", int(dough.meters["dry"]), int(cutter.meters["used"]))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if trouble_score_from_world(world) >= 1:
        cutter.meters["stuck"] += 1
        world.get("hero").memes["regret"] += 1
    else:
        cutter.meters["wobble"] += 1
        world.get("hero").memes["worry"] += 1
    return []


def _r_teamwork(world: World) -> list[str]:
    hero = world.get("hero")
    friend = world.get("friend")
    tray = world.get("tray")
    if hero.memes["shared"] < THRESHOLD or friend.memes["working"] < THRESHOLD:
        return []
    sig = ("teamwork",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    tray.meters["full"] += 1
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.get("yorkie").memes["proud"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="dry", tag="physical", apply=_r_dry),
    Rule(name="jam", tag="physical", apply=_r_jam),
    Rule(name="teamwork", tag="social", apply=_r_teamwork),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
        if any(sig[0] in {"dry", "jam", "teamwork"} for sig in world.fired):
            changed = False
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combo(dough: Dough, cutter: CutterCfg) -> bool:
    return dough.firmness >= cutter.demand


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id in PLACES:
        for dough_id, dough in DOUGHS.items():
            for cutter_id, cutter in CUTTERS.items():
                if valid_combo(dough, cutter):
                    combos.append((place_id, dough_id, cutter_id))
    return combos


def trouble_score(dough: Dough, cutter: CutterCfg) -> int:
    return max(0, dough.drying + cutter.demand - dough.firmness)


def outcome_of(params: "StoryParams") -> str:
    if params.share_mode == "share":
        return "feast"
    return "flop" if trouble_score(DOUGHS[params.dough], CUTTERS[params.cutter]) >= 1 else "patch_up"


def trouble_score_from_world(world: World) -> int:
    dough = world.get("dough")
    cutter = world.get("cutter")
    return max(0, int(dough.attrs.get("drying", 1)) + int(cutter.attrs.get("demand", 1)) - int(dough.attrs.get("firmness", 1)))


def predict_solo(world: World) -> dict:
    sim = world.copy()
    sim.get("dough").meters["waiting"] += 1
    sim.get("cutter").meters["used"] += 1
    propagate(sim, narrate=False)
    return {
        "dry": sim.get("dough").meters["dry"],
        "stuck": sim.get("cutter").meters["stuck"],
        "score": trouble_score_from_world(sim),
    }


def introduction(world: World, hero: Entity, friend: Entity, yorkie: Entity, place: Place, dough: Dough, cutter: CutterCfg) -> None:
    hero.memes["hope"] += 1
    friend.memes["hope"] += 1
    yorkie.memes["bounce"] += 1
    world.say(
        f"In {place.label}, {hero.id} could tell a baking tale so tall that even the fence posts seemed to stand up straighter to hear it. "
        f"That morning, {hero.id}, {friend.id}, and a whiskery yorkie named {yorkie.id} set out to make {dough.treat} big enough to feed half the county."
    )
    world.say(
        f"They lugged out {dough.phrase} and {cutter.phrase}. Folks said that cutter was {cutter.boast}, and when it came down it left {cutter.imprint}."
    )
    world.say(place.opening)


def request_turn(world: World, hero: Entity, friend: Entity, cutter: CutterCfg) -> None:
    friend.memes["need"] += 1
    world.say(
        f'Before the first round was cut, {friend.id} pointed at the {cutter.label}. '
        f'"After your turn, may I use the cutter too?" {friend.pronoun()} asked.'
    )


def flashback(world: World, hero: Entity, yorkie: Entity, past: PastEvent) -> None:
    hero.memes["memory"] += 1
    world.say(
        f"At that question, the day seemed to blink backward. {hero.id} remembered {past.setting}, when {hero.pronoun()} had clutched {past.object_label} all to {hero.pronoun('object')}self."
    )
    world.say(
        f"{past.mistake} Then {past.loss}. {yorkie.id} had given one sharp bark that sounded almost like a scolding bell."
    )
    world.say(
        f"Ever since then, {hero.id} had carried this thought around like a shiny button in a pocket: {past.lesson}"
    )


def choose_share(world: World, hero: Entity, friend: Entity, yorkie: Entity, cutter: CutterCfg) -> None:
    hero.memes["shared"] += 1
    hero.memes["kindness"] += 1
    friend.memes["working"] += 1
    friend.memes["trust"] += 1
    world.get("tray").meters["count"] += 2
    world.say(
        f'{hero.id} looked at the cutter, then at {friend.id}, and remembered better. '
        f'"A cutter works fastest when two kind hands take turns," {hero.pronoun()} said.'
    )
    world.say(
        f"{hero.pronoun().capitalize()} passed over the big {cutter.label}, and the whole table changed at once. "
        f"While one child pressed shapes, the other dusted flour, turned the rounds, and kept the edges neat."
    )
    world.say(
        f"{yorkie.id} trotted crumbs from one end of the board to the other like a tiny foreman with four velvet feet."
    )
    propagate(world, narrate=False)


def choose_keep(world: World, hero: Entity, friend: Entity, yorkie: Entity, cutter: CutterCfg, dough: Dough) -> None:
    hero.memes["greed"] += 1
    friend.memes["sad"] += 1
    world.get("dough").meters["waiting"] += 1
    world.get("cutter").meters["used"] += 1
    world.get("tray").meters["count"] += 1
    world.say(
        f'But {hero.id} tightened {hero.pronoun("possessive")} grip on the {cutter.label}. '
        f'"I can finish quicker alone," {hero.pronoun()} said, though the words sounded smaller than before.'
    )
    world.say(
        f"{friend.id} stepped back, and the extra rounds of {dough.label} had to wait on the board. "
        f"{yorkie.id} sat down with one ear up, as if even that little dog knew waiting dough could turn stubborn."
    )
    propagate(world, narrate=False)


def resolve_feast(world: World, hero: Entity, friend: Entity, adult: Entity, yorkie: Entity, dough: Dough, cutter: CutterCfg, place: Place) -> None:
    hero.memes["lesson"] += 1
    friend.memes["lesson"] += 1
    world.say(
        f"Soon the pans were so full that the oven door had to make room the way a barn door makes room for a wagon. "
        f"The {cutter.shape}-shaped {dough.treat} came out puffed and shining, row after row."
    )
    world.say(
        f"{adult.label_word.capitalize()} laughed to see it. {yorkie.id} stood on tiptoe, nose twitching, as if the smell itself were lifting that little yorkie an inch off the floor."
    )
    world.say(
        f"When the town gathered at {place.ending}, {hero.id} made sure the first warm piece went to {friend.id}. "
        f"That was the biggest thing on the table: not the treat, but the sharing."
    )


def resolve_patch_up(world: World, hero: Entity, friend: Entity, adult: Entity, yorkie: Entity, dough: Dough, cutter: CutterCfg, place: Place) -> None:
    hero.memes["lesson"] += 1
    hero.memes["regret"] += 1
    friend.memes["forgive"] += 1
    world.say(
        f"The {cutter.label} did not stick fast, but it wobbled enough to leave a few lopsided edges. "
        f"There were only a handful of {dough.treat} instead of a mountain."
    )
    world.say(
        f"{hero.id} stared at the short stack and felt the flashback lesson come true all over again. "
        f'"I should have shared sooner," {hero.pronoun()} admitted.'
    )
    world.say(
        f"{friend.id} helped brush the crumbs together anyway, and {adult.label_word} split the warm pieces into careful halves. "
        f"At {place.ending}, every bite was small, but the apology was honest and the sharing finally came before the last crumb."
    )


def resolve_flop(world: World, hero: Entity, friend: Entity, adult: Entity, yorkie: Entity, dough: Dough, cutter: CutterCfg, place: Place) -> None:
    hero.memes["lesson"] += 1
    hero.memes["regret"] += 2
    friend.memes["forgive"] += 1
    world.say(
        f"Then the trouble came. The waiting dough turned tight and springy, and when {hero.id} shoved down the {cutter.label}, it stuck there like a wagon wheel in river mud."
    )
    world.say(
        f"{yorkie.id} barked, {friend.id} rushed in, and even {adult.label_word} had to help tug it loose. "
        f"When it finally popped free, the grand round was bent, cracked, and no use for a proud tray."
    )
    world.say(
        f"{hero.id} sighed clear down to {hero.pronoun('possessive')} boots. "
        f'"The cutter was never the biggest thing here," {hero.pronoun()} said. "The lesson was."'
    )
    world.say(
        f"Together they rolled the scraps again and made a smaller, humbler batch to share at {place.ending}. "
        f"It was not a tall-tale triumph, but it was enough to prove {past_tense_lesson(world)}"
    )


def past_tense_lesson(world: World) -> str:
    return "that a shared job rises better than a selfish one."


def tell(
    place: Place,
    dough_cfg: Dough,
    cutter_cfg: CutterCfg,
    past_cfg: PastEvent,
    share_mode: str,
    hero_name: str,
    hero_gender: str,
    friend_name: str,
    friend_gender: str,
    adult_type: str,
    yorkie_name: str,
) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero", label=hero_name))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend", label=friend_name))
    adult = world.add(Entity(id="Adult", kind="character", type=adult_type, role="adult", label="the grown-up"))
    yorkie = world.add(Entity(id=yorkie_name, kind="character", type="dog", role="yorkie", label="the yorkie"))
    dough = world.add(
        Entity(
            id="dough",
            kind="thing",
            type="dough",
            label=dough_cfg.label,
            phrase=dough_cfg.phrase,
            attrs={"firmness": dough_cfg.firmness, "drying": dough_cfg.drying},
            tags=set(dough_cfg.tags),
        )
    )
    cutter = world.add(
        Entity(
            id="cutter",
            kind="thing",
            type="cutter",
            label=cutter_cfg.label,
            phrase=cutter_cfg.phrase,
            attrs={"demand": cutter_cfg.demand, "shape": cutter_cfg.shape},
            tags=set(cutter_cfg.tags),
        )
    )
    tray = world.add(Entity(id="tray", kind="thing", type="tray", label="tray"))

    introduction(world, hero, friend, yorkie, place, dough_cfg, cutter_cfg)
    world.para()
    request_turn(world, hero, friend, cutter_cfg)
    flashback(world, hero, yorkie, past_cfg)
    world.para()

    if share_mode == "share":
        choose_share(world, hero, friend, yorkie, cutter_cfg)
        world.para()
        resolve_feast(world, hero, friend, adult, yorkie, dough_cfg, cutter_cfg, place)
    else:
        choose_keep(world, hero, friend, yorkie, cutter_cfg, dough_cfg)
        world.para()
        if trouble_score(dough_cfg, cutter_cfg) >= 1:
            resolve_flop(world, hero, friend, adult, yorkie, dough_cfg, cutter_cfg, place)
        else:
            resolve_patch_up(world, hero, friend, adult, yorkie, dough_cfg, cutter_cfg, place)

    world.facts.update(
        hero=hero,
        friend=friend,
        adult=adult,
        yorkie=yorkie,
        place=place,
        dough_cfg=dough_cfg,
        cutter_cfg=cutter_cfg,
        past_cfg=past_cfg,
        share_mode=share_mode,
        outcome="feast" if share_mode == "share" else ("flop" if trouble_score(dough_cfg, cutter_cfg) >= 1 else "patch_up"),
        predicted_solo=predict_solo(world),
        tray_count=int(world.get("tray").meters["count"]),
        tray_full=world.get("tray").meters["full"] >= THRESHOLD,
        cutter_stuck=world.get("cutter").meters["stuck"] >= THRESHOLD,
        dry_amount=world.get("dough").meters["dry"],
        lesson_learned=hero.memes["lesson"] >= THRESHOLD,
    )
    return world


PLACES = {
    "ranch": Place(
        id="ranch",
        label="a wind-bent ranch kitchen at the edge of the prairie",
        opening="The mixing bowl was so wide that the children could have floated hats in it.",
        ending="the long supper table under the cottonwoods",
        tags={"kitchen", "prairie"},
    ),
    "fair": Place(
        id="fair",
        label="the county fair bake tent",
        opening="The flour rose in such soft clouds that the bunting overhead looked ready to snow.",
        ending="the fair's blue ribbon table",
        tags={"fair", "kitchen"},
    ),
    "camp": Place(
        id="camp",
        label="a chuckwagon camp beside a red canyon",
        opening="The rolling board lay across two barrels like a bridge built just for hungry people.",
        ending="the campfire feast",
        tags={"camp", "kitchen"},
    ),
}

DOUGHS = {
    "thunder_biscuit": Dough(
        id="thunder_biscuit",
        label="thunder-biscuit dough",
        phrase="a tub of thunder-biscuit dough",
        treat="biscuits",
        firmness=3,
        drying=1,
        tags={"biscuit", "baking"},
    ),
    "apple_scone": Dough(
        id="apple_scone",
        label="apple-scone dough",
        phrase="a pan of apple-scone dough",
        treat="scones",
        firmness=2,
        drying=1,
        tags={"scone", "baking"},
    ),
    "cloud_shortcake": Dough(
        id="cloud_shortcake",
        label="cloud-shortcake dough",
        phrase="a tableful of cloud-shortcake dough",
        treat="shortcakes",
        firmness=2,
        drying=2,
        tags={"shortcake", "baking"},
    ),
}

CUTTERS = {
    "moon": CutterCfg(
        id="moon",
        label="moon cutter",
        phrase="one silver moon cutter",
        shape="moon",
        demand=1,
        boast="so broad it could have clipped a hole in the night sky",
        imprint="a clean crescent big enough for a kitten to nap in",
        tags={"cutter", "shape"},
    ),
    "star": CutterCfg(
        id="star",
        label="star cutter",
        phrase="one brass star cutter",
        shape="star",
        demand=2,
        boast="sharp enough to cut a star out of sunrise",
        imprint="five bright points as crisp as frost on a window",
        tags={"cutter", "shape"},
    ),
    "wagon": CutterCfg(
        id="wagon",
        label="wagon-wheel cutter",
        phrase="one iron wagon-wheel cutter",
        shape="wagon-wheel",
        demand=3,
        boast="heavy enough to make a tabletop creak its opinion",
        imprint="a ring so round it looked borrowed from a giant's cart",
        tags={"cutter", "shape"},
    ),
}

PAST_EVENTS = {
    "berry_bucket": PastEvent(
        id="berry_bucket",
        object_label="the only berry bucket",
        setting="last summer by the blackberry fence",
        mistake="Hero or not, sharing should have started there, but it did not: one child reached, and the other pulled the bucket away",
        loss="the berries tipped, rolled into the dust, and not one pie got made",
        lesson="good things grow faster when they are passed along",
        tags={"sharing", "flashback"},
    ),
    "kite_spool": PastEvent(
        id="kite_spool",
        object_label="the bright red kite spool",
        setting="one windy afternoon on the school hill",
        mistake="Instead of taking turns, the spool was hugged tight against a proud chest",
        loss="the string snarled, the kite dove nose-first, and all the wind in the world could not lift it again that day",
        lesson="holding too tight can leave everyone with less",
        tags={"sharing", "flashback"},
    ),
    "jam_ladle": PastEvent(
        id="jam_ladle",
        object_label="the long jam ladle",
        setting="a sticky autumn morning near the stove",
        mistake="One child kept dipping first and would not pass the ladle across",
        loss="the jam cooled in clumps before the jars were filled",
        lesson="a passed tool keeps a good day moving",
        tags={"sharing", "flashback"},
    ),
}


@dataclass
class StoryParams:
    place: str
    dough: str
    cutter: str
    past_event: str
    share_mode: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    adult_type: str
    yorkie_name: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="ranch",
        dough="thunder_biscuit",
        cutter="wagon",
        past_event="berry_bucket",
        share_mode="share",
        hero_name="Mabel",
        hero_gender="girl",
        friend_name="Otis",
        friend_gender="boy",
        adult_type="grandmother",
        yorkie_name="Pepper",
    ),
    StoryParams(
        place="fair",
        dough="apple_scone",
        cutter="moon",
        past_event="kite_spool",
        share_mode="keep",
        hero_name="Finn",
        hero_gender="boy",
        friend_name="Nell",
        friend_gender="girl",
        adult_type="father",
        yorkie_name="Button",
    ),
    StoryParams(
        place="camp",
        dough="cloud_shortcake",
        cutter="star",
        past_event="jam_ladle",
        share_mode="keep",
        hero_name="June",
        hero_gender="girl",
        friend_name="Toby",
        friend_gender="boy",
        adult_type="grandfather",
        yorkie_name="Pip",
    ),
]


KNOWLEDGE = {
    "yorkie": [
        (
            "What is a yorkie?",
            "A yorkie is a Yorkshire terrier, which is a very small kind of dog. Yorkies can be tiny, lively, and brave even though they are not big.",
        )
    ],
    "cutter": [
        (
            "What does a cutter do in baking?",
            "A cutter presses through dough to make a shape before the dough is baked. Bakers use cutters to make pieces that are neat and even.",
        )
    ],
    "sharing": [
        (
            "Why is sharing helpful when two people work together?",
            "Sharing lets more than one person help, so the job can go faster and more smoothly. It also helps everyone feel included and cared for.",
        )
    ],
    "flashback": [
        (
            "What is a flashback in a story?",
            "A flashback is a part of a story that looks back at something that happened earlier. It helps explain why a character thinks or acts a certain way now.",
        )
    ],
    "baking": [
        (
            "Why can dough get harder to use if it sits too long?",
            "When dough sits too long, it can dry out or lose the soft texture that makes it easy to shape. Then it may crack, stick, or stop holding the shape you want.",
        )
    ],
}
KNOWLEDGE_ORDER = ["yorkie", "cutter", "sharing", "flashback", "baking"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    cutter = f["cutter_cfg"]
    past = f["past_cfg"]
    dough = f["dough_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write a Tall Tale for a 3-to-5-year-old that includes the words "yorkie" and '
        f'"cutter", plus Sharing, Flashback, and a Lesson Learned.'
    )
    if outcome == "feast":
        return [
            base,
            f"Tell a giant baking story where {hero.id} and {friend.id} have only one {cutter.label}, and a flashback about {past.object_label} helps {hero.id} choose to share.",
            f"Write a warm Tall Tale where children use {dough.label} to make huge treats, and the happy ending proves that sharing made the work better.",
        ]
    return [
        base,
        f"Tell a Tall Tale where {hero.id} remembers {past.setting} but does not choose well at first, and the trouble with the {cutter.label} turns into a lesson learned.",
        f"Write a child-facing story in which waiting {dough.label} becomes part of the problem, and the ending explains why sharing should have happened sooner.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    yorkie = f["yorkie"]
    adult = f["adult"]
    dough = f["dough_cfg"]
    cutter = f["cutter_cfg"]
    past = f["past_cfg"]
    place = f["place"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, {friend.id}, and a tiny yorkie named {yorkie.id}. They are baking together in {place.label}.",
        ),
        (
            "What was the problem in the story?",
            f"There was only one {cutter.label}, and both children needed it for the baking. That made sharing the big problem they had to solve.",
        ),
        (
            "What was the flashback about?",
            f"The flashback was about {past.setting}, when {hero.id} did not share {past.object_label}. That old mistake helped explain why the choice about the cutter mattered so much now.",
        ),
    ]
    if outcome == "feast":
        qa.append(
            (
                f"Why did the baking go so well?",
                f"It went well because {hero.id} shared the {cutter.label} instead of keeping it. Then both children could work, and the trays filled much faster.",
            )
        )
        qa.append(
            (
                "What lesson did the story teach?",
                f"It taught that sharing makes a hard job lighter and kinder. The happy ending showed the lesson by giving the first warm piece to {friend.id}.",
            )
        )
    elif outcome == "patch_up":
        qa.append(
            (
                f"What happened when {hero.id} tried to work alone?",
                f"The cutter did not jam, but the batch came out smaller and uneven. {hero.id} saw that keeping the tool back had slowed the work and left less for everyone.",
            )
        )
        qa.append(
            (
                "How was the problem fixed in the end?",
                f"{hero.id} admitted the mistake, and {friend.id} still helped share the finished pieces. The food was small, but the apology and the sharing at the end were real.",
            )
        )
    else:
        qa.append(
            (
                f"Why did the cutter get stuck?",
                f"The dough had to wait while {hero.id} tried to do the whole job alone, so it grew harder to shape. Then the {cutter.label} caught in the dough and spoiled the proud round.",
            )
        )
        qa.append(
            (
                "What lesson did the child learn?",
                f"{hero.id} learned that a shared job goes better than a selfish one. The trouble with the stuck cutter made the old flashback lesson feel true all over again.",
            )
        )
    qa.append(
        (
            f"What did the yorkie do?",
            f"The little yorkie, {yorkie.id}, stayed close all through the baking. That tiny dog helped the story feel lively and made the lesson easier to remember.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    tags = {"yorkie", "cutter", "sharing", "flashback", "baking"}
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        if ent.role:
            bits.append(f"role={ent.role}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    return "\n".join(lines)


def explain_rejection(dough: Dough, cutter: CutterCfg) -> str:
    return (
        f"(No story: {dough.label} is too soft for the {cutter.label}. "
        f"The dough has firmness {dough.firmness}, but that cutter needs {cutter.demand}, "
        f"so the shapes would not hold and the world refuses the setup.)"
    )


ASP_RULES = r"""
valid(Place, Dough, Cutter) :- place(Place), dough(Dough), cutter(Cutter),
                               firmness(Dough, F), demand(Cutter, D), F >= D.

trouble(Dough, Cutter, S) :- valid(_, Dough, Cutter),
                             drying(Dough, Dr), firmness(Dough, F), demand(Cutter, D),
                             S = Dr + D - F, S > 0.
trouble(Dough, Cutter, 0) :- valid(_, Dough, Cutter),
                             drying(Dough, Dr), firmness(Dough, F), demand(Cutter, D),
                             Dr + D - F <= 0.

outcome(feast)    :- share_mode(share).
outcome(flop)     :- share_mode(keep), chosen(Dough, Cutter), trouble(Dough, Cutter, S), S >= 1.
outcome(patch_up) :- share_mode(keep), chosen(Dough, Cutter), trouble(Dough, Cutter, 0).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for dough_id, dough in DOUGHS.items():
        lines.append(asp.fact("dough", dough_id))
        lines.append(asp.fact("firmness", dough_id, dough.firmness))
        lines.append(asp.fact("drying", dough_id, dough.drying))
    for cutter_id, cutter in CUTTERS.items():
        lines.append(asp.fact("cutter", cutter_id))
        lines.append(asp.fact("demand", cutter_id, cutter.demand))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen", params.dough, params.cutter),
            asp.fact("share_mode", params.share_mode),
        ]
    )
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
    for seed in range(100):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story from smoke test")
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            emit(sample, trace=False, qa=False, header="")
        finally:
            sys.stdout = old
        print("OK: smoke test generate/emit passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall Tale storyworld: a yorkie, one cutter, sharing, a flashback, and a lesson learned."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--dough", choices=DOUGHS)
    ap.add_argument("--cutter", choices=CUTTERS)
    ap.add_argument("--past-event", dest="past_event", choices=PAST_EVENTS)
    ap.add_argument("--share-mode", choices=["share", "keep"])
    ap.add_argument("--adult", dest="adult_type", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--yorkie-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (place, dough, cutter) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check inline ASP parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


GIRL_NAMES = ["Mabel", "June", "Nora", "Elsie", "Willa", "Ruby", "Clara", "Mae"]
BOY_NAMES = ["Finn", "Otis", "Jasper", "Toby", "Eli", "Beau", "Cal", "Arlo"]
YORKIE_NAMES = ["Pip", "Pepper", "Button", "Tizzy", "Dot", "Midge"]


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.dough and args.cutter:
        if not valid_combo(DOUGHS[args.dough], CUTTERS[args.cutter]):
            raise StoryError(explain_rejection(DOUGHS[args.dough], CUTTERS[args.cutter]))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.dough is None or combo[1] == args.dough)
        and (args.cutter is None or combo[2] == args.cutter)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, dough, cutter = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or _pick_name(rng, hero_gender)
    friend_name = args.friend_name or _pick_name(rng, friend_gender, avoid=hero_name)
    return StoryParams(
        place=place,
        dough=dough,
        cutter=cutter,
        past_event=args.past_event or rng.choice(sorted(PAST_EVENTS)),
        share_mode=args.share_mode or rng.choice(["share", "keep"]),
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        adult_type=args.adult_type or rng.choice(["mother", "father", "grandmother", "grandfather"]),
        yorkie_name=args.yorkie_name or rng.choice(YORKIE_NAMES),
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Invalid place: {params.place})")
    if params.dough not in DOUGHS:
        raise StoryError(f"(Invalid dough: {params.dough})")
    if params.cutter not in CUTTERS:
        raise StoryError(f"(Invalid cutter: {params.cutter})")
    if params.past_event not in PAST_EVENTS:
        raise StoryError(f"(Invalid past event: {params.past_event})")
    if params.share_mode not in {"share", "keep"}:
        raise StoryError(f"(Invalid share mode: {params.share_mode})")
    if not valid_combo(DOUGHS[params.dough], CUTTERS[params.cutter]):
        raise StoryError(explain_rejection(DOUGHS[params.dough], CUTTERS[params.cutter]))

    world = tell(
        place=PLACES[params.place],
        dough_cfg=DOUGHS[params.dough],
        cutter_cfg=CUTTERS[params.cutter],
        past_cfg=PAST_EVENTS[params.past_event],
        share_mode=params.share_mode,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        adult_type=params.adult_type,
        yorkie_name=params.yorkie_name,
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
        print(f"{len(combos)} compatible (place, dough, cutter) combos:\n")
        for place, dough, cutter in combos:
            print(f"  {place:8} {dough:16} {cutter}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.dough} with {p.cutter} at {p.place} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

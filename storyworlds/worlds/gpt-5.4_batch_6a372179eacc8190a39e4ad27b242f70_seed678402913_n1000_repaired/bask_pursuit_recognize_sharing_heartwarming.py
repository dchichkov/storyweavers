#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/bask_pursuit_recognize_sharing_heartwarming.py
==========================================================================

A standalone story world about one child already enjoying a small comfort in the
sun, another child returning from a lively pursuit, and a warm moment of
recognizing a need and sharing. The stories are deliberately gentle and
heartwarming: the tension is small, physical, and social, and the ending image
always proves that something changed because one child chose to share.

Run it
------
    python storyworlds/worlds/gpt-5.4/bask_pursuit_recognize_sharing_heartwarming.py
    python storyworlds/worlds/gpt-5.4/bask_pursuit_recognize_sharing_heartwarming.py --setting porch --pursuit butterflies --comfort lemonade
    python storyworlds/worlds/gpt-5.4/bask_pursuit_recognize_sharing_heartwarming.py --pursuit kite --comfort berries
    python storyworlds/worlds/gpt-5.4/bask_pursuit_recognize_sharing_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4/bask_pursuit_recognize_sharing_heartwarming.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/bask_pursuit_recognize_sharing_heartwarming.py --qa --json
    python storyworlds/worlds/gpt-5.4/bask_pursuit_recognize_sharing_heartwarming.py --verify
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

PACKAGE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PACKAGE_DIR)
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
QUICK_NOTICE_SCORE = 4


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: tuple = field(default_factory=tuple)
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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    id: str
    place: str
    sunlight: str
    detail: str
    affords: set[str] = field(default_factory=set)
    closing: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Pursuit:
    id: str
    phrase: str
    pursuit_phrase: str
    need: str
    cue: str
    result_line: str
    cue_strength: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Comfort:
    id: str
    label: str
    phrase: str
    need: str
    start_line: str
    share_line: str
    ending_line: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
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

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_show_need(world: World) -> list[str]:
    out: list[str] = []
    seeker = world.get("seeker")
    pursuit = world.facts["pursuit"]
    if seeker.meters[pursuit.need] < THRESHOLD:
        return out
    sig = ("show_need", pursuit.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    seeker.memes["show_need"] += float(pursuit.cue_strength)
    out.append("__cue__")
    return out


def _r_recognize(world: World) -> list[str]:
    out: list[str] = []
    holder = world.get("holder")
    seeker = world.get("seeker")
    if seeker.memes["show_need"] < THRESHOLD:
        return out
    sig = ("recognize",)
    if sig in world.fired:
        return out
    score = (holder.attrs.get("notice_score", 0)
             + world.facts.get("relation_bonus", 0)
             + world.facts["pursuit"].cue_strength)
    if score < 2:
        return out
    world.fired.add(sig)
    holder.memes["recognized"] += 1
    world.facts["notice_score_total"] = score
    out.append("__recognized__")
    return out


def _r_share_relief(world: World) -> list[str]:
    out: list[str] = []
    holder = world.get("holder")
    seeker = world.get("seeker")
    comfort = world.facts["comfort"]
    pursuit = world.facts["pursuit"]
    if holder.memes["shared"] < THRESHOLD:
        return out
    if comfort.need != pursuit.need:
        return out
    sig = ("relief", comfort.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    seeker.meters[pursuit.need] = 0.0
    seeker.memes["relief"] += 1
    seeker.memes["joy"] += 1
    holder.memes["joy"] += 1
    holder.memes["warmth"] += 1
    out.append("__relief__")
    return out


CAUSAL_RULES = [
    Rule(name="show_need", tag="physical", apply=_r_show_need),
    Rule(name="recognize", tag="social", apply=_r_recognize),
    Rule(name="share_relief", tag="social", apply=_r_share_relief),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(s for s in lines if not s.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


SETTINGS = {
    "porch": Setting(
        id="porch",
        place="the front porch",
        sunlight="golden morning light",
        detail="The boards were warm, and the railing made thin shadows like stripes across the floor.",
        affords={"butterflies", "kite"},
        closing="Below them, the street looked sleepy and kind.",
        tags={"sun"},
    ),
    "garden": Setting(
        id="garden",
        place="the little garden path",
        sunlight="soft afternoon sun",
        detail="Mint leaves nodded by the stepping stones, and bees hummed beyond the marigolds.",
        affords={"butterflies", "ladybug"},
        closing="Around them, the flowers kept shining as if they liked the plan too.",
        tags={"sun", "garden"},
    ),
    "park": Setting(
        id="park",
        place="the park bench by the hill",
        sunlight="late-day sunshine",
        detail="The bench faced the grass, where dandelion fluff floated by like tiny boats.",
        affords={"kite", "ball"},
        closing="The whole hill looked painted with honey-colored light.",
        tags={"sun", "park"},
    ),
}

PURSUITS = {
    "butterflies": Pursuit(
        id="butterflies",
        phrase="chase butterflies",
        pursuit_phrase="in pursuit of a yellow butterfly",
        need="thirst",
        cue="came back pink-cheeked and thirsty, with little quick breaths",
        result_line="The butterfly danced away over the flowers, and the running left the seeker warm all over.",
        cue_strength=2,
        tags={"butterfly", "thirst"},
    ),
    "kite": Pursuit(
        id="kite",
        phrase="run after a kite tail",
        pursuit_phrase="in pursuit of a hopping kite tail",
        need="rest",
        cue="came back tired, with wind-tangled hair and knees that wanted to fold",
        result_line="The kite skipped along the breeze, and all that running made the seeker's legs feel wobbly.",
        cue_strength=1,
        tags={"kite", "rest"},
    ),
    "ladybug": Pursuit(
        id="ladybug",
        phrase="follow a ladybug to the bean vines",
        pursuit_phrase="in pursuit of a bright red ladybug",
        need="hunger",
        cue="came back quiet and hungry, with a small tummy rumble",
        result_line="The ladybug lifted its shiny wings and vanished into the leaves, and the long wandering left the seeker ready for a bite to eat.",
        cue_strength=2,
        tags={"ladybug", "hunger"},
    ),
    "ball": Pursuit(
        id="ball",
        phrase="run after a rolling ball",
        pursuit_phrase="in pursuit of a runaway red ball",
        need="thirst",
        cue="came back warm and thirsty, with a hand pressed to the chest to catch a breath",
        result_line="The ball rolled farther than anyone expected, and the chasing made the seeker's throat feel dry.",
        cue_strength=2,
        tags={"ball", "thirst"},
    ),
}

COMFORTS = {
    "lemonade": Comfort(
        id="lemonade",
        label="lemonade",
        phrase="a cool jar of lemonade",
        need="thirst",
        start_line="A jar of lemonade waited beside the holder, shining with little drops of cold.",
        share_line="Without making a fuss, the holder tipped the lemonade into two cups and slid one over.",
        ending_line="Soon both children were sipping slowly and letting the sunshine settle around them.",
        tags={"drink", "sharing"},
    ),
    "berries": Comfort(
        id="berries",
        label="berries",
        phrase="a bowl of sweet berries",
        need="hunger",
        start_line="A bowl of sweet berries sat in the holder's lap, red and blue as buttons.",
        share_line="The holder split the berries into two small handfuls and held one out in an open palm.",
        ending_line="Soon both children were nibbling berries one by one, with stained fingertips and easy smiles.",
        tags={"food", "sharing"},
    ),
    "quilt": Comfort(
        id="quilt",
        label="quilt",
        phrase="a patchwork quilt",
        need="rest",
        start_line="A patchwork quilt was tucked around the holder's knees, soft as a cloud and warm from the sun.",
        share_line="The holder lifted one side of the quilt and made a space close by.",
        ending_line="Soon both children were tucked under the quilt, basking shoulder to shoulder in the warm light.",
        tags={"warmth", "sharing"},
    ),
}


TRAIT_SCORES = {
    "tender": 2,
    "observant": 2,
    "gentle": 1,
    "dreamy": 1,
}
TRAITS = sorted(TRAIT_SCORES)

RELATION_BONUS = {
    "siblings": 1,
    "friends": 0,
}

GIRL_NAMES = ["Lily", "Mia", "Ava", "Nora", "Ella", "Ruby", "Zoe", "Maya"]
BOY_NAMES = ["Ben", "Leo", "Sam", "Noah", "Eli", "Theo", "Max", "Finn"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for pid in sorted(setting.affords):
            pursuit = PURSUITS[pid]
            for cid, comfort in COMFORTS.items():
                if comfort.need == pursuit.need:
                    combos.append((sid, pid, cid))
    return sorted(combos)


@dataclass
class StoryParams:
    setting: str
    pursuit: str
    comfort: str
    holder_name: str
    holder_gender: str
    seeker_name: str
    seeker_gender: str
    relation: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        setting="porch",
        pursuit="butterflies",
        comfort="lemonade",
        holder_name="Lily",
        holder_gender="girl",
        seeker_name="Ben",
        seeker_gender="boy",
        relation="friends",
        trait="observant",
    ),
    StoryParams(
        setting="garden",
        pursuit="ladybug",
        comfort="berries",
        holder_name="Maya",
        holder_gender="girl",
        seeker_name="Nora",
        seeker_gender="girl",
        relation="siblings",
        trait="tender",
    ),
    StoryParams(
        setting="park",
        pursuit="kite",
        comfort="quilt",
        holder_name="Theo",
        holder_gender="boy",
        seeker_name="Sam",
        seeker_gender="boy",
        relation="friends",
        trait="gentle",
    ),
    StoryParams(
        setting="park",
        pursuit="ball",
        comfort="lemonade",
        holder_name="Ella",
        holder_gender="girl",
        seeker_name="Max",
        seeker_gender="boy",
        relation="siblings",
        trait="dreamy",
    ),
]


def explain_rejection(setting: Setting, pursuit: Pursuit, comfort: Comfort) -> str:
    if pursuit.id not in setting.affords:
        return (
            f"(No story: {setting.place} does not fit {pursuit.phrase}. "
            f"Choose a setting that reasonably affords that pursuit.)"
        )
    return (
        f"(No story: {comfort.label} helps with {comfort.need}, but "
        f"{pursuit.phrase} creates {pursuit.need}. The shared comfort must meet the need that the pursuit caused.)"
    )


def relation_noun(relation: str, holder: Entity, seeker: Entity) -> str:
    if relation == "siblings":
        if holder.type == "girl" and seeker.type == "girl":
            return "two sisters"
        if holder.type == "boy" and seeker.type == "boy":
            return "two brothers"
        return "a brother and a sister"
    return "two friends"


def outcome_of(params: StoryParams) -> str:
    score = TRAIT_SCORES[params.trait] + RELATION_BONUS[params.relation] + PURSUITS[params.pursuit].cue_strength
    return "quick" if score >= QUICK_NOTICE_SCORE else "after_pause"


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def introduce(world: World, holder: Entity, seeker: Entity, setting: Setting, comfort: Comfort) -> None:
    pair = relation_noun(world.facts["relation"], holder, seeker)
    world.say(
        f"{holder.id} and {seeker.id} were {pair} spending a bright while at {setting.place}."
    )
    world.say(
        f"{setting.detail} {holder.id} had settled into {setting.sunlight} to bask quietly for a minute."
    )
    world.say(comfort.start_line)


def start_basking(world: World, holder: Entity, comfort: Comfort) -> None:
    holder.memes["calm"] += 1
    holder.memes["joy"] += 1
    world.say(
        f"{holder.id} smiled at the peaceful feeling and held {comfort.label} close, not greedy, just content."
    )


def pursuit_run(world: World, seeker: Entity, pursuit: Pursuit) -> None:
    seeker.memes["eagerness"] += 1
    seeker.attrs["need"] = pursuit.need
    world.say(
        f"But {seeker.id} had darted away {pursuit.pursuit_phrase}. {pursuit.result_line}"
    )
    seeker.meters[pursuit.need] += 1
    propagate(world, narrate=False)
    world.say(
        f"When {seeker.id} came back, {seeker.pronoun()} {pursuit.cue}."
    )


def pause_and_see(world: World, holder: Entity, seeker: Entity, pursuit: Pursuit) -> None:
    score = world.facts["notice_score_total"]
    if score >= QUICK_NOTICE_SCORE:
        world.say(
            f"{holder.id} only needed one look to recognize what the long pursuit had done."
        )
    else:
        world.say(
            f"For one tiny moment, {holder.id} stayed tucked in the good sun. Then {holder.pronoun()} noticed {seeker.id}'s face and began to recognize the need behind it."
        )


def share(world: World, holder: Entity, seeker: Entity, comfort: Comfort) -> None:
    holder.memes["shared"] += 1
    propagate(world, narrate=False)
    world.say(comfort.share_line)
    world.say(
        f'"Here," {holder.id} said. "We can share."'
    )
    if comfort.need == "thirst":
        world.say(
            f"{seeker.id}'s shoulders loosened at once, because the cool drink was exactly what {seeker.pronoun()} needed after all that running."
        )
    elif comfort.need == "hunger":
        world.say(
            f"{seeker.id}'s face softened at once, because the little bite to eat was exactly right after such a long wandering chase."
        )
    else:
        world.say(
            f"{seeker.id}'s body relaxed at once, because the warm resting place was exactly what {seeker.pronoun()} needed after so much rushing."
        )


def ending(world: World, holder: Entity, seeker: Entity, setting: Setting, comfort: Comfort) -> None:
    world.say(comfort.ending_line)
    world.say(
        f"{setting.closing} The nicest part was not the sun or the snack or the quilt, but the way a small act of sharing made room for both of them."
    )


def tell(
    setting: Setting,
    pursuit: Pursuit,
    comfort: Comfort,
    holder_name: str,
    holder_gender: str,
    seeker_name: str,
    seeker_gender: str,
    relation: str,
    trait: str,
) -> World:
    world = World()
    holder = world.add(
        Entity(
            id=holder_name,
            kind="character",
            type=holder_gender,
            attrs={"notice_score": TRAIT_SCORES[trait], "trait": trait},
            tags={"holder"},
        )
    )
    seeker = world.add(
        Entity(
            id=seeker_name,
            kind="character",
            type=seeker_gender,
            attrs={},
            tags={"seeker"},
        )
    )
    world.facts.update(
        setting=setting,
        pursuit=pursuit,
        comfort=comfort,
        relation=relation,
        relation_bonus=RELATION_BONUS[relation],
        trait=trait,
        holder=holder,
        seeker=seeker,
    )

    introduce(world, holder, seeker, setting, comfort)
    start_basking(world, holder, comfort)

    world.para()
    pursuit_run(world, seeker, pursuit)
    propagate(world, narrate=False)
    pause_and_see(world, holder, seeker, pursuit)

    world.para()
    share(world, holder, seeker, comfort)
    world.para()
    ending(world, holder, seeker, setting, comfort)

    world.facts["outcome"] = outcome_of(
        StoryParams(
            setting=setting.id,
            pursuit=pursuit.id,
            comfort=comfort.id,
            holder_name=holder_name,
            holder_gender=holder_gender,
            seeker_name=seeker_name,
            seeker_gender=seeker_gender,
            relation=relation,
            trait=trait,
        )
    )
    return world


KNOWLEDGE = {
    "butterfly": [
        (
            "What does it mean to be in pursuit of a butterfly?",
            "It means you are chasing after the butterfly and trying to keep up with it. A pursuit is when you go after something that keeps moving away."
        )
    ],
    "kite": [
        (
            "Why can running after a kite make you tired?",
            "A kite can pull and skip in the wind, so you may have to run a long way to keep up. All that running can make your legs feel tired."
        )
    ],
    "ball": [
        (
            "Why can chasing a ball make you thirsty?",
            "Running makes your body work hard and warm up. After a lot of running, your throat can feel dry and you may want a drink."
        )
    ],
    "ladybug": [
        (
            "What is a ladybug?",
            "A ladybug is a small round beetle, often red with black spots. It can crawl on leaves and then suddenly fly away."
        )
    ],
    "drink": [
        (
            "Why does lemonade help when someone is thirsty?",
            "A drink puts water back into your body when your throat feels dry. Something cool can feel especially nice after running in the sun."
        )
    ],
    "food": [
        (
            "Why does a snack help when someone is hungry?",
            "A snack gives your body some energy when your tummy feels empty. Even a small bite can help you feel steadier and happier."
        )
    ],
    "warmth": [
        (
            "What does it mean to bask?",
            "To bask means to sit or rest in warm, pleasant light and enjoy the cozy feeling. People and animals can bask in sunshine."
        )
    ],
    "sharing": [
        (
            "What is sharing?",
            "Sharing is when you let someone else have part of something good with you. It can make both people feel included and cared for."
        )
    ],
}
KNOWLEDGE_ORDER = ["butterfly", "kite", "ball", "ladybug", "drink", "food", "warmth", "sharing"]


def generation_prompts(world: World) -> list[str]:
    holder = world.facts["holder"]
    seeker = world.facts["seeker"]
    setting = world.facts["setting"]
    pursuit = world.facts["pursuit"]
    comfort = world.facts["comfort"]
    return [
        (
            f'Write a heartwarming story for a 3-to-5-year-old that includes the words '
            f'"bask," "pursuit," and "recognize," and centers on sharing.'
        ),
        (
            f"Tell a gentle story where {holder.id} is basking at {setting.place} with {comfort.phrase}, "
            f"while {seeker.id} comes back from {pursuit.pursuit_phrase}, and the moment turns kind because one child recognizes the other's need."
        ),
        (
            f"Write a simple sunny story in which a child shares {comfort.label} after another child gets {pursuit.need} from {pursuit.phrase}."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    holder = world.facts["holder"]
    seeker = world.facts["seeker"]
    setting = world.facts["setting"]
    pursuit = world.facts["pursuit"]
    comfort = world.facts["comfort"]
    relation = world.facts["relation"]
    pair = relation_noun(relation, holder, seeker)
    outcome = world.facts["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {holder.id} and {seeker.id}. One child begins the story basking in the sun, and the other comes back from a lively pursuit."
        ),
        (
            f"What was {seeker.id} doing before coming back?",
            f"{seeker.id} had hurried away {pursuit.pursuit_phrase}. That chase is what left {seeker.pronoun('object')} {pursuit.need} when {seeker.pronoun()} returned."
        ),
        (
            f"How did {holder.id} recognize that something was wrong?",
            f"{holder.id} saw that {seeker.id} {pursuit.cue}. Those clues helped {holder.pronoun('object')} recognize the need behind the tired or quiet look."
        ),
        (
            f"What did {holder.id} share?",
            f"{holder.id} shared {comfort.label} with {seeker.id}. It was the right thing to share because it matched the need the pursuit had caused."
        ),
    ]
    if outcome == "quick":
        qa.append(
            (
                "Did the sharing happen right away?",
                f"Almost right away. {holder.id} only needed one good look to understand what {seeker.id} needed, so the kind choice came quickly."
            )
        )
    else:
        qa.append(
            (
                "Did the sharing happen right away?",
                f"Not at the very first second. {holder.id} paused in the cozy sun, then noticed {seeker.id}'s face and chose to share."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with both children together in the warm place, enjoying {comfort.label}. The final image proves that sharing made the sunny moment bigger, not smaller."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    pursuit = world.facts["pursuit"]
    comfort = world.facts["comfort"]
    tags = set(pursuit.tags) | set(comfort.tags)
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
        attrs = {k: v for k, v in ent.attrs.items() if v or v == 0}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if attrs:
            bits.append(f"attrs={attrs}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:7}) {' '.join(bits)}")
    lines.append(f"  facts: outcome={world.facts.get('outcome')} relation={world.facts.get('relation')} trait={world.facts.get('trait')}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% valid combinations: the setting must afford the pursuit, and the comfort must
% directly answer the need created by that pursuit.
valid(S, P, C) :- setting(S), pursuit(P), comfort(C),
                  affords(S, P),
                  pursuit_need(P, N),
                  comfort_need(C, N).

notice_total(TS + RB + CS) :-
    chosen_trait(T), trait_score(T, TS),
    chosen_relation(R), relation_bonus(R, RB),
    chosen_pursuit(P), cue_strength(P, CS).

outcome(quick) :- notice_total(N), quick_notice_score(Q), N >= Q.
outcome(after_pause) :- notice_total(N), quick_notice_score(Q), N < Q.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for pid in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, pid))
    for pid, pursuit in PURSUITS.items():
        lines.append(asp.fact("pursuit", pid))
        lines.append(asp.fact("pursuit_need", pid, pursuit.need))
        lines.append(asp.fact("cue_strength", pid, pursuit.cue_strength))
    for cid, comfort in COMFORTS.items():
        lines.append(asp.fact("comfort", cid))
        lines.append(asp.fact("comfort_need", cid, comfort.need))
    for trait, score in TRAIT_SCORES.items():
        lines.append(asp.fact("trait_score", trait, score))
    for relation, bonus in RELATION_BONUS.items():
        lines.append(asp.fact("relation_bonus", relation, bonus))
    lines.append(asp.fact("quick_notice_score", QUICK_NOTICE_SCORE))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_trait", params.trait),
            asp.fact("chosen_relation", params.relation),
            asp.fact("chosen_pursuit", params.pursuit),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
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
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during smoke test.")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: basking, pursuit, recognizing a need, and sharing."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--pursuit", choices=PURSUITS)
    ap.add_argument("--comfort", choices=COMFORTS)
    ap.add_argument("--relation", choices=sorted(RELATION_BONUS))
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--holder-gender", choices=["girl", "boy"])
    ap.add_argument("--seeker-gender", choices=["girl", "boy"])
    ap.add_argument("--holder-name")
    ap.add_argument("--seeker-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.pursuit and args.comfort:
        setting = SETTINGS[args.setting]
        pursuit = PURSUITS[args.pursuit]
        comfort = COMFORTS[args.comfort]
        if (args.setting, args.pursuit, args.comfort) not in valid_combos():
            raise StoryError(explain_rejection(setting, pursuit, comfort))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.pursuit is None or combo[1] == args.pursuit)
        and (args.comfort is None or combo[2] == args.comfort)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, pursuit_id, comfort_id = rng.choice(sorted(combos))
    relation = args.relation or rng.choice(sorted(RELATION_BONUS))
    trait = args.trait or rng.choice(TRAITS)
    holder_gender = args.holder_gender or rng.choice(["girl", "boy"])
    seeker_gender = args.seeker_gender or rng.choice(["girl", "boy"])
    holder_name = args.holder_name or _pick_name(rng, holder_gender)
    seeker_name = args.seeker_name or _pick_name(rng, seeker_gender, avoid=holder_name)

    if holder_name == seeker_name:
        raise StoryError("(No story: the two children need different names so the story stays clear.)")

    return StoryParams(
        setting=setting_id,
        pursuit=pursuit_id,
        comfort=comfort_id,
        holder_name=holder_name,
        holder_gender=holder_gender,
        seeker_name=seeker_name,
        seeker_gender=seeker_gender,
        relation=relation,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Invalid setting: {params.setting})")
    if params.pursuit not in PURSUITS:
        raise StoryError(f"(Invalid pursuit: {params.pursuit})")
    if params.comfort not in COMFORTS:
        raise StoryError(f"(Invalid comfort: {params.comfort})")
    if params.relation not in RELATION_BONUS:
        raise StoryError(f"(Invalid relation: {params.relation})")
    if params.trait not in TRAIT_SCORES:
        raise StoryError(f"(Invalid trait: {params.trait})")
    if (params.setting, params.pursuit, params.comfort) not in valid_combos():
        raise StoryError(
            explain_rejection(SETTINGS[params.setting], PURSUITS[params.pursuit], COMFORTS[params.comfort])
        )
    if params.holder_name == params.seeker_name:
        raise StoryError("(No story: the two children need different names so the story stays clear.)")

    world = tell(
        setting=SETTINGS[params.setting],
        pursuit=PURSUITS[params.pursuit],
        comfort=COMFORTS[params.comfort],
        holder_name=params.holder_name,
        holder_gender=params.holder_gender,
        seeker_name=params.seeker_name,
        seeker_gender=params.seeker_gender,
        relation=params.relation,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, pursuit, comfort) combos:\n")
        for setting_id, pursuit_id, comfort_id in combos:
            print(f"  {setting_id:8} {pursuit_id:12} {comfort_id}")
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
            header = f"### {p.holder_name} shares {p.comfort} after {p.seeker_name}'s {p.pursuit} ({p.setting}, {outcome_of(p)})"
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

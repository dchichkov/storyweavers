#!/usr/bin/env python3
"""
storyworlds/worlds/icy_cloud_friend_s_backyard_rhyme_kindness_2.py
==================================================================

A small standalone storyworld about a visiting child, a friend's backyard, and
an icy cloud that starts as a comedy problem and ends with a kind rhymed turn.
The world tracks both physical state (frost, height, warmth, slipperiness) and
emotional state (worry, trust, relief, gratitude), then renders a complete
TinyStories-style story from that simulation.
"""

from __future__ import annotations

import argparse
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
SAFE_ALTITUDE = 1.2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    subject: str = "they"
    object: str = "them"
    possessive: str = "their"
    location: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass(frozen=True)
class Child:
    id: str
    name: str
    phrase: str
    subject: str
    object: str
    possessive: str
    trait: str
    joke_style: str


@dataclass(frozen=True)
class Friend:
    id: str
    name: str
    phrase: str
    subject: str
    object: str
    possessive: str
    trait: str
    laugh: str


@dataclass(frozen=True)
class Backyard:
    id: str
    label: str
    opening_detail: str
    cold_target: str
    warm_spot: str
    final_spot: str
    tags: frozenset[str]


@dataclass(frozen=True)
class FailedTrick:
    id: str
    label: str
    setup: str
    motion: str
    backfire: str
    required_tags: frozenset[str] = frozenset()


@dataclass(frozen=True)
class KindAct:
    id: str
    label: str
    setup: str
    rhyme: str
    method: str
    success: str
    required_tags: frozenset[str]
    warmth_gain: float
    kindness_gain: float
    rise_gain: float


@dataclass(frozen=True)
class Ending:
    id: str
    reveal: str
    rhyme: str
    final_image: str


class World:
    def __init__(self, backyard: Backyard) -> None:
        self.backyard = backyard
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple[str, str]] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.history: list[dict[str, str]] = []
        self.facts: dict[str, object] = {}

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

    def note(self, event: str, **fields: str) -> None:
        row = {"event": event}
        row.update(fields)
        self.history.append(row)

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


@dataclass(frozen=True)
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_frost(world: World) -> list[str]:
    cloud = world.get("cloud")
    yard = world.get("yard")
    target = world.get("target")
    friend = world.get("friend")
    if cloud.meters["altitude"] >= SAFE_ALTITUDE or cloud.meters["cold"] < THRESHOLD:
        return []
    if yard.meters["frost"] >= THRESHOLD:
        return []
    sig = ("frost", "1")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    yard.meters["frost"] += 1.0
    yard.meters["slippery"] += 1.0
    target.meters["frost"] += 1.0
    friend.memes["worry"] += 1.0
    world.note(
        "frost",
        cause="low icy cloud",
        target=target.label,
        place=world.backyard.label,
    )
    return [
        f"The icy cloud sagged so low that frost whiskers crept over {target.label}.",
        f"Soon the grass in {world.backyard.label} turned slick, and {friend.label} did a startled little skate."
    ]


def _r_backfire(world: World) -> list[str]:
    cloud = world.get("cloud")
    yard = world.get("yard")
    if cloud.memes["spooked"] < THRESHOLD:
        return []
    sig = ("backfire", str(int(cloud.memes["spooked"])))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    cloud.meters["cold"] += 0.8
    cloud.meters["altitude"] = max(0.3, cloud.meters["altitude"] - 0.1)
    cloud.memes["embarrassed"] += 1.0
    yard.meters["slippery"] += 0.5
    world.note("backfire", effect="cloud got colder and lower")
    return [
        "Instead of leaving, the cloud wobbled, sneezed, and sprayed tiny crunchy ice bits.",
        "That only made the backyard sillier and slipperier."
    ]


def _r_soften(world: World) -> list[str]:
    cloud = world.get("cloud")
    if (
        cloud.meters["warmth"] < THRESHOLD
        or cloud.memes["trusted"] < THRESHOLD
        or cloud.meters["kindness"] < THRESHOLD
    ):
        return []
    sig = ("soften", "1")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    cloud.meters["cold"] = max(0.0, cloud.meters["cold"] - 1.6)
    cloud.meters["altitude"] += max(0.9, cloud.meters["rise"])
    cloud.meters["drips"] += 1.0
    cloud.memes["gratitude"] += 1.0
    world.note("soften", effect="cloud warmed and floated higher")
    return [
        "The warm air curled up through the icy puff, and the cloud stopped chattering.",
        "Its hard blue edges turned soft and pearly as it lifted a little higher."
    ]


def _r_relief(world: World) -> list[str]:
    cloud = world.get("cloud")
    yard = world.get("yard")
    hero = world.get("hero")
    friend = world.get("friend")
    target = world.get("target")
    if cloud.meters["altitude"] < SAFE_ALTITUDE or cloud.meters["cold"] >= THRESHOLD:
        return []
    sig = ("relief", "1")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    yard.meters["slippery"] = 0.0
    yard.meters["frost"] = 0.0
    target.meters["frost"] = 0.0
    hero.memes["lesson"] += 1.0
    hero.memes["relief"] += 1.0
    friend.memes["relief"] += 1.0
    friend.memes["joy"] += 1.0
    world.note("relief", result="yard safe again")
    return [
        f"The frost let go of {target.label}, and the slick grass turned springy again.",
        f"{friend.label} laughed instead of sliding, because the backyard finally felt safe."
    ]


CAUSAL_RULES = [
    Rule("frost", _r_frost),
    Rule("backfire", _r_backfire),
    Rule("soften", _r_soften),
    Rule("relief", _r_relief),
]


def propagate(world: World, *, narrate: bool = False) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            before = len(world.fired)
            lines = rule.apply(world)
            if len(world.fired) != before:
                changed = True
            if narrate:
                out.extend(lines)
    return out


def trick_available(trick: FailedTrick, backyard: Backyard) -> bool:
    return trick.required_tags.issubset(backyard.tags)


def comforts_cloud(act: KindAct, backyard: Backyard) -> bool:
    return (
        act.required_tags.issubset(backyard.tags)
        and act.warmth_gain >= THRESHOLD
        and act.kindness_gain >= THRESHOLD
        and act.rise_gain >= 0.6
    )


def valid_transition(backyard: Backyard, trick: FailedTrick, act: KindAct) -> bool:
    return trick_available(trick, backyard) and comforts_cloud(act, backyard)


def predict_kindness(backyard: Backyard, act: KindAct) -> dict[str, float]:
    if not act.required_tags.issubset(backyard.tags):
        return {"cold": 1.6, "altitude": 0.5, "grateful": 0.0}
    world = World(backyard)
    world.add(Entity("hero", kind="character", type="child", label="hero"))
    world.add(Entity("friend", kind="character", type="child", label="friend"))
    world.add(Entity("yard", kind="place", type="backyard", label=backyard.label))
    world.add(Entity("target", kind="thing", type="prop", label=backyard.cold_target))
    world.add(Entity(
        "cloud",
        kind="weather",
        type="cloud",
        label="icy cloud",
        meters=defaultdict(float, {"cold": 1.6, "altitude": 0.5}),
        memes=defaultdict(float),
    ))
    world.get("cloud").meters["warmth"] += act.warmth_gain
    world.get("cloud").meters["kindness"] += act.kindness_gain
    world.get("cloud").meters["rise"] += act.rise_gain
    world.get("cloud").memes["trusted"] += act.kindness_gain
    propagate(world)
    cloud = world.get("cloud")
    return {
        "cold": cloud.meters["cold"],
        "altitude": cloud.meters["altitude"],
        "grateful": cloud.memes["gratitude"],
    }


def introduce(world: World, hero: Entity, friend: Entity, child: Child, pal: Friend,
              backyard: Backyard) -> None:
    hero.memes["curiosity"] += 1.0
    friend.memes["joy"] += 0.5
    world.say(
        f"One bright afternoon, {child.name} went to {pal.name}'s backyard."
    )
    world.say(
        f"It was full of {backyard.opening_detail}, and {child.name} planned to trade "
        f"{child.joke_style} rhymes with {pal.name}."
    )
    world.note("premise", place=f"{pal.name}'s backyard", activity="trading rhymes")


def cloud_arrives(world: World, hero: Entity, friend: Entity, child: Child, pal: Friend,
                  backyard: Backyard) -> None:
    cloud = world.get("cloud")
    cloud.meters["cold"] = 1.6
    cloud.meters["altitude"] = 0.5
    cloud.memes["lonely"] += 1.0
    friend.memes["worry"] += 0.5
    world.say(
        "Before anyone could start, an icy cloud bumped over the fence like a grumpy scoop of sherbet."
    )
    world.say(
        f"It parked itself above {backyard.cold_target}, so low that even the air looked ready to squeak."
    )
    for line in propagate(world, narrate=True):
        world.say(line)


def failed_attempt(world: World, hero: Entity, friend: Entity, child: Child, pal: Friend,
                   trick: FailedTrick) -> None:
    cloud = world.get("cloud")
    hero.memes["determination"] += 1.0
    cloud.memes["spooked"] += 1.0
    world.say(f'"Let us shoo it with style," said {child.name}.')
    world.say(trick.setup)
    world.say(trick.motion)
    for line in propagate(world, narrate=True):
        world.say(line)
    world.say(trick.backfire)
    world.note("failed_trick", trick=trick.label)


def noticing_turn(world: World, hero: Entity, friend: Entity, child: Child, pal: Friend) -> None:
    cloud = world.get("cloud")
    hero.memes["care"] += 1.0
    cloud.memes["embarrassed"] += 0.5
    world.say(
        f"Then {child.name} heard a tiny chittering sound, almost like teeth clicking in a cup."
    )
    world.say(
        f'"Wait," said {child.name}. "It is not acting mean. It is acting cold and embarrassed."'
    )
    world.note("turn", realization="cloud needs comfort, not shooing")


def kind_attempt(world: World, hero: Entity, friend: Entity, child: Child, pal: Friend,
                 backyard: Backyard, act: KindAct) -> None:
    cloud = world.get("cloud")
    prediction = predict_kindness(backyard, act)
    world.facts["prediction"] = prediction
    hero.memes["kindness"] += 1.0
    friend.memes["kindness"] += 1.0
    cloud.meters["warmth"] += act.warmth_gain
    cloud.meters["kindness"] += act.kindness_gain
    cloud.meters["rise"] += act.rise_gain
    cloud.memes["trusted"] += act.kindness_gain
    world.say(act.setup.format(hero=child.name, friend=pal.name, warm_spot=backyard.warm_spot))
    world.say(f'"{act.rhyme}"')
    world.say(act.method.format(hero=child.name, friend=pal.name, warm_spot=backyard.warm_spot))
    for line in propagate(world, narrate=True):
        world.say(line)
    world.say(act.success.format(target=backyard.cold_target))
    world.note("kindness", method=act.label, spot=backyard.warm_spot)


def ending_scene(world: World, hero: Entity, friend: Entity, child: Child, pal: Friend,
                 backyard: Backyard, ending: Ending) -> None:
    cloud = world.get("cloud")
    if cloud.memes["gratitude"] >= THRESHOLD:
        cloud.memes["play"] += 1.0
    world.say(ending.reveal.format(final_spot=backyard.final_spot))
    world.say(f'"{ending.rhyme}"')
    world.say(
        ending.final_image.format(
            hero=child.name,
            friend=pal.name,
            final_spot=backyard.final_spot,
        )
    )
    world.note("ending", image=backyard.final_spot)


def tell(child: Child, pal: Friend, backyard: Backyard, trick: FailedTrick,
         act: KindAct, ending: Ending) -> World:
    world = World(backyard)
    hero = world.add(Entity(
        "hero",
        kind="character",
        type="child",
        label=child.name,
        phrase=child.phrase,
        role="hero",
        subject=child.subject,
        object=child.object,
        possessive=child.possessive,
        location="yard",
    ))
    friend = world.add(Entity(
        "friend",
        kind="character",
        type="child",
        label=pal.name,
        phrase=pal.phrase,
        role="friend",
        subject=pal.subject,
        object=pal.object,
        possessive=pal.possessive,
        location="yard",
    ))
    world.add(Entity(
        "cloud",
        kind="weather",
        type="cloud",
        label="the icy cloud",
        phrase="the icy cloud",
        location="yard",
        meters=defaultdict(float),
        memes=defaultdict(float),
    ))
    world.add(Entity(
        "yard",
        kind="place",
        type="backyard",
        label=f"{pal.name}'s backyard",
        phrase=backyard.label,
        meters=defaultdict(float),
        memes=defaultdict(float),
    ))
    world.add(Entity(
        "target",
        kind="thing",
        type="prop",
        label=backyard.cold_target,
        phrase=backyard.cold_target,
        location="yard",
        meters=defaultdict(float),
        memes=defaultdict(float),
    ))

    introduce(world, hero, friend, child, pal, backyard)
    cloud_arrives(world, hero, friend, child, pal, backyard)

    world.para()
    failed_attempt(world, hero, friend, child, pal, trick)
    noticing_turn(world, hero, friend, child, pal)

    world.para()
    kind_attempt(world, hero, friend, child, pal, backyard, act)
    ending_scene(world, hero, friend, child, pal, backyard, ending)

    world.facts.update(
        child=child,
        friend_profile=pal,
        backyard=backyard,
        trick=trick,
        kind_act=act,
        ending=ending,
        resolved=world.get("cloud").meters["altitude"] >= SAFE_ALTITUDE
        and world.get("cloud").meters["cold"] < THRESHOLD,
        lesson=hero.memes["lesson"] >= THRESHOLD,
        target_saved=world.get("target").meters["frost"] == 0.0,
    )
    return world


CHILDREN = {
    "june": Child("june", "June", "a quick-thinking girl", "she", "her", "her", "quick-thinking", "snappy"),
    "theo": Child("theo", "Theo", "a cheerful boy", "he", "him", "his", "cheerful", "goofy"),
    "mina": Child("mina", "Mina", "an observant girl", "she", "her", "her", "observant", "sing-song"),
}

FRIENDS = {
    "ravi": Friend("ravi", "Ravi", "a generous boy", "he", "him", "his", "generous", "a donkey-bray laugh"),
    "lila": Friend("lila", "Lila", "a giggly girl", "she", "her", "her", "giggly", "a hiccupy laugh"),
    "benji": Friend("benji", "Benji", "an inventive boy", "he", "him", "his", "inventive", "a trumpet laugh"),
}

BACKYARDS = {
    "pear_line": Backyard(
        "pear_line",
        "the pear-tree backyard",
        "a clothesline between two pear trees, a birdbath, and chalk jokes on the path",
        "the paper rhyme cards clipped to the line",
        "the porch bricks that had been warming in the sun",
        "the birdbath rim",
        frozenset({"line", "porch", "birdbath"}),
    ),
    "tomato_patch": Backyard(
        "tomato_patch",
        "the tomato-patch backyard",
        "tomato boxes, a crate stage, and a compost bin puffing sleepy steam",
        "the berry muffins on the crate stage",
        "the compost side where the warm steam rose",
        "the crate stage",
        frozenset({"compost", "crates"}),
    ),
    "trampoline_corner": Backyard(
        "trampoline_corner",
        "the trampoline-corner backyard",
        "a trampoline, a picnic bench, and chalk arrows curling by the fence",
        "the lemon ice pops lined on the picnic bench",
        "the sun-striped picnic bench by the fence",
        "the fence top",
        frozenset({"trampoline", "bench"}),
    ),
}

FAILED_TRICKS = {
    "bounce_chant": FailedTrick(
        "bounce_chant",
        "trampoline bounce chant",
        "They climbed onto the trampoline and bounced in a circle, flapping their arms like excited chickens.",
        '"Boing away, cloud today!" they sang, louder and louder.',
        "The cloud answered with a frosty sneeze that powdered their hair white.",
        frozenset({"trampoline"}),
    ),
    "pinwheel_parade": FailedTrick(
        "pinwheel_parade",
        "pinwheel parade",
        "They marched under the cloud with pinwheels, colanders on their heads, and a bucket for a drum.",
        "The faster they spun, the more the icy puff shivered above them.",
        "Soon the pinwheels were clicking with ice, and the parade looked even sillier than before.",
    ),
    "ladle_band": FailedTrick(
        "ladle_band",
        "ladle band",
        "They tapped soup ladles on mixing bowls and made a backyard boom-bom band.",
        "Every clang made the icy cloud scrunch up tighter, as if it wanted to hide inside itself.",
        "Instead of floating away, it squeezed out crunchy little sleet crumbs onto the grass.",
    ),
}

KIND_ACTS = {
    "cocoa_wagon": KindAct(
        "cocoa_wagon",
        "cocoa steam wagon",
        "So {hero} and {friend} rolled out a red wagon of cocoa and parked it by {warm_spot}.",
        "Little cloud, do not crowd. Warm your shivers, soft and proud.",
        "{hero} held the mugs high enough for the sweet steam to curl into the chilly puff.",
        "Warm brown steam drifted upward, and even {target} stopped looking stiff.",
        frozenset({"porch"}),
        warmth_gain=1.7,
        kindness_gain=1.4,
        rise_gain=0.8,
    ),
    "quilt_canopy": KindAct(
        "quilt_canopy",
        "sunny quilt canopy",
        "So {hero} and {friend} clipped a yellow picnic quilt to the line and made a bright tent over {warm_spot}.",
        "Little cloud, float and rest. Kind warm sunshine suits you best.",
        "The quilt caught the sun and tossed a gentle gold glow up into the icy puff.",
        "The bright cloth made the whole corner look cozy instead of cranky, even around {target}.",
        frozenset({"line"}),
        warmth_gain=1.3,
        kindness_gain=1.6,
        rise_gain=0.8,
    ),
    "compost_song": KindAct(
        "compost_song",
        "compost steam song",
        "So {hero} and {friend} stood beside {warm_spot}, where the compost gave off a small warm puff.",
        "Cloud so cold, you need not scold. Stay with friends and lose your hold.",
        "{hero} sang softly while the warm earthy steam drifted through the blue-white chill.",
        "The warm puff rose around {target}, and the whole yard smelled like wet leaves and comfort.",
        frozenset({"compost"}),
        warmth_gain=1.8,
        kindness_gain=1.3,
        rise_gain=0.9,
    ),
}

ENDINGS = {
    "bell_drip": Ending(
        "bell_drip",
        "The cloud gave one shy laugh and dropped three bell-shaped drips that rang on {final_spot}.",
        "High went the cold, kind went the bold, and now the shivers cannot hold.",
        "{hero} and {friend} looked up from {final_spot} and laughed so hard that the whole backyard felt warmer than before.",
    ),
    "snow_hat": Ending(
        "snow_hat",
        "Then the cloud spun once and plopped a tiny snow hat where everyone could see it on {final_spot}.",
        "Kind words rise, warm the skies, and turn grumpy puffs to friendly size.",
        "By {final_spot}, {friend} bowed to the silly snow hat while {hero} almost laughed out of a hiccup.",
    ),
    "mist_heart": Ending(
        "mist_heart",
        "At last the cloud curled into a misty heart and drifted a silver loop above {final_spot}.",
        "Rhymes can play, care can stay, and kindness lifts the frost away.",
        "{hero} pointed at {final_spot}, and {friend} said the backyard looked as if it had learned the rhyme too.",
    ),
}


@dataclass
class StoryParams:
    child: str
    friend: str
    backyard: str
    trick: str
    kind_act: str
    ending: str
    seed: Optional[int] = None


CURATED = [
    StoryParams("june", "ravi", "pear_line", "pinwheel_parade", "cocoa_wagon", "bell_drip"),
    StoryParams("mina", "lila", "pear_line", "ladle_band", "quilt_canopy", "mist_heart"),
    StoryParams("theo", "benji", "tomato_patch", "pinwheel_parade", "compost_song", "snow_hat"),
    StoryParams("theo", "ravi", "trampoline_corner", "bounce_chant", "cocoa_wagon", "bell_drip"),
]


def valid_combos() -> list[tuple[str, str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str, str]] = []
    for child in CHILDREN:
        for friend in FRIENDS:
            for backyard_id, backyard in BACKYARDS.items():
                for trick_id, trick in FAILED_TRICKS.items():
                    if not trick_available(trick, backyard):
                        continue
                    for act_id, act in KIND_ACTS.items():
                        if not valid_transition(backyard, trick, act):
                            continue
                        for ending in ENDINGS:
                            combos.append((child, friend, backyard_id, trick_id, act_id, ending))
    return combos


KNOWLEDGE = {
    "cloud": [
        (
            "What is an icy cloud?",
            "An icy cloud is a very cold cloud with tiny frozen bits inside it. When it hangs low, it can help frost form on things below."
        )
    ],
    "frost": [
        (
            "What is frost?",
            "Frost is a thin layer of ice crystals that forms when the air and a surface get very cold. It can make grass slippery and snacks stiff."
        )
    ],
    "steam": [
        (
            "Why can warm steam help cold air?",
            "Warm steam carries heat upward. When it reaches something colder, it can help that cold thing warm up."
        )
    ],
    "sun": [
        (
            "How can sunshine make a place feel warmer?",
            "Sunshine warms surfaces like bricks and cloth. Those warm surfaces can then share their heat with the air nearby."
        )
    ],
    "kindness": [
        (
            "Why can kind words help someone calm down?",
            "Kind words can make someone feel safe instead of scared. Feeling safe can help a body relax and stop reacting so sharply."
        )
    ],
    "rhyme": [
        (
            "What is a rhyme?",
            "A rhyme is a pair or group of words that sound alike at the end. Rhymes can make a chant feel playful and easy to remember."
        )
    ],
    "compost": [
        (
            "Why can a compost bin feel warm?",
            "Tiny living things break down old leaves and scraps inside a compost pile. That work gives off a little heat."
        )
    ],
    "trampoline": [
        (
            "Why is a trampoline bouncy?",
            "A trampoline stretches and springs back. That springy mat pushes people upward when they jump."
        )
    ],
}

KNOWLEDGE_ORDER = ["cloud", "frost", "kindness", "rhyme", "steam", "sun", "compost", "trampoline"]


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    pal = world.facts["friend_profile"]
    backyard = world.facts["backyard"]
    act = world.facts["kind_act"]
    return [
        'Write a TinyStories-style comedy that includes the words "icy cloud" and is set in a friend\'s backyard.',
        f"Tell a child-facing story where {child.name} visits {pal.name}'s backyard, a silly trick fails, and {act.label} helps the icy cloud calm down.",
        f"Write a funny but gentle story with rhyme and kindness, ending with the backyard changed for the better near {backyard.final_spot}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    pal = world.facts["friend_profile"]
    backyard = world.facts["backyard"]
    trick = world.facts["trick"]
    act = world.facts["kind_act"]
    ending = world.facts["ending"]
    prediction = world.facts["prediction"]
    qa = [
        (
            "Where does the story happen?",
            f"The story happens in {pal.name}'s backyard. It is the place with {backyard.opening_detail}, so the icy cloud can freeze things the children were already using there."
        ),
        (
            "What problem did the icy cloud cause?",
            f"The icy cloud frosted over {backyard.cold_target} and made the grass slippery. That mattered because the children had come to play and trade rhymes in the backyard."
        ),
        (
            "What did the children try first?",
            f"They first tried {trick.label}. It was funny to watch, but it scared the cloud instead of helping it, so the cold only got worse."
        ),
        (
            "How did kindness change the story?",
            f"The children used {act.label} and spoke to the cloud with a gentle rhyme. The warmth and kindness helped the cloud trust them, so it floated higher and stopped frosting the yard."
        ),
    ]
    if prediction["altitude"] >= SAFE_ALTITUDE:
        qa.append(
            (
                "How do we know the backyard was safe again?",
                f"We know because the cloud rose higher and the frost let go of {backyard.cold_target}. After that, {pal.name} could laugh instead of sliding around."
            )
        )
    qa.append(
        (
            "What was funny about the ending?",
            f"The ending is funny because {ending.reveal.format(final_spot=backyard.final_spot).lower()} It turns the cloud from a backyard nuisance into part of the joke."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    backyard = world.facts["backyard"]
    act = world.facts["kind_act"]
    tags = {"cloud", "frost", "kindness", "rhyme"}
    if act.id in {"cocoa_wagon", "compost_song"}:
        tags.add("steam")
    if act.id == "quilt_canopy":
        tags.add("sun")
    if "compost" in backyard.tags:
        tags.add("compost")
    if "trampoline" in backyard.tags:
        tags.add("trampoline")
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
        meters = {k: round(v, 3) for k, v in ent.meters.items() if v}
        memes = {k: round(v, 3) for k, v in ent.memes.items() if v}
        bits: list[str] = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if ent.location:
            bits.append(f"location={ent.location}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    if world.history:
        lines.append("  history:")
        for item in world.history:
            detail = ", ".join(f"{k}={v}" for k, v in item.items() if k != "event")
            lines.append(f"    - {item['event']}: {detail}")
    return "\n".join(lines)


def explain_rejection(backyard: Backyard, trick: FailedTrick, act: KindAct) -> str:
    if not trick_available(trick, backyard):
        return f"(No story: {trick.label} does not fit {backyard.label}.)"
    if not act.required_tags.issubset(backyard.tags):
        return f"(No story: {act.label} needs features that {backyard.label} does not have.)"
    if not comforts_cloud(act, backyard):
        return f"(No story: {act.label} is not warm or kind enough to change the icy cloud.)"
    return "(No story: these options do not create the required comedy-to-kindness turn.)"


ASP_RULES = r"""
trick_ok(T, B) :- failed_trick(T), backyard(B), requires_trick(T, Tag), has_tag(B, Tag).
trick_ok(T, B) :- failed_trick(T), backyard(B), not requires_any_trick(T).
requires_any_trick(T) :- requires_trick(T, _).

kind_ok(K, B) :- kind_act(K), backyard(B), warm_enough(K), kind_enough(K), rise_enough(K),
                 not missing_kind_tag(K, B).
missing_kind_tag(K, B) :- kind_act(K), backyard(B), requires_kind(K, Tag), not has_tag(B, Tag).

valid(C, F, B, T, K, E) :- child(C), friend(F), backyard(B), failed_trick(T), kind_act(K), ending(E),
                           trick_ok(T, B), kind_ok(K, B).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for child in CHILDREN:
        lines.append(asp.fact("child", child))
    for friend in FRIENDS:
        lines.append(asp.fact("friend", friend))
    for backyard_id, backyard in BACKYARDS.items():
        lines.append(asp.fact("backyard", backyard_id))
        for tag in sorted(backyard.tags):
            lines.append(asp.fact("has_tag", backyard_id, tag))
    for trick_id, trick in FAILED_TRICKS.items():
        lines.append(asp.fact("failed_trick", trick_id))
        for tag in sorted(trick.required_tags):
            lines.append(asp.fact("requires_trick", trick_id, tag))
    for act_id, act in KIND_ACTS.items():
        lines.append(asp.fact("kind_act", act_id))
        if act.warmth_gain >= THRESHOLD:
            lines.append(asp.fact("warm_enough", act_id))
        if act.kindness_gain >= THRESHOLD:
            lines.append(asp.fact("kind_enough", act_id))
        if act.rise_gain >= 0.6:
            lines.append(asp.fact("rise_enough", act_id))
        for tag in sorted(act.required_tags):
            lines.append(asp.fact("requires_kind", act_id, tag))
    for ending in ENDINGS:
        lines.append(asp.fact("ending", ending))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/6."))
    return sorted(set(asp.atoms(model, "valid")))


def verify_sample(sample: StorySample) -> list[str]:
    problems: list[str] = []
    story = sample.story
    world = sample.world
    if "icy cloud" not in story:
        problems.append("story text missing seed phrase 'icy cloud'")
    if "backyard" not in story:
        problems.append("story text missing backyard grounding")
    if "{" in story or "}" in story:
        problems.append("story text leaked template braces")
    if not sample.story_qa or not sample.world_qa or not sample.prompts:
        problems.append("missing one or more QA/prompt sections")
    if world is None or not world.facts.get("resolved"):
        problems.append("world did not resolve to a safe ending")
    if world is None or not world.facts.get("lesson"):
        problems.append("hero never reached the kindness lesson")
    return problems


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combo gate:")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    prediction_errors: list[str] = []
    for backyard in BACKYARDS.values():
        for act in KIND_ACTS.values():
            predicted = predict_kindness(backyard, act)
            py = comforts_cloud(act, backyard)
            simulated = predicted["altitude"] >= SAFE_ALTITUDE and predicted["cold"] < THRESHOLD
            if py != simulated:
                prediction_errors.append(
                    f"{backyard.id}/{act.id}: comforts_cloud={py}, predicted={predicted}"
                )
    if prediction_errors:
        rc = 1
        print("MISMATCH in kindness simulation:")
        for row in prediction_errors:
            print(" ", row)
    else:
        print("OK: kindness simulation matches comforts_cloud().")

    exercised: list[StoryParams] = list(CURATED)
    rng = random.Random(777)
    extra = sorted(valid_combos())
    for combo in rng.sample(extra, min(4, len(extra))):
        exercised.append(StoryParams(*combo))
    failures: list[str] = []
    for params in exercised:
        sample = generate(params)
        issues = verify_sample(sample)
        if issues:
            failures.append(f"{params}: {'; '.join(issues)}")
    if failures:
        rc = 1
        print("Generated story verification failures:")
        for row in failures:
            print(" ", row)
    else:
        print(f"OK: exercised {len(exercised)} generated stories.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Storyworld comedy: a child in a friend\'s backyard calms an "icy cloud" with rhyme and kindness.'
    )
    parser.add_argument("--child", choices=CHILDREN)
    parser.add_argument("--friend", choices=FRIENDS)
    parser.add_argument("--backyard", choices=BACKYARDS)
    parser.add_argument("--trick", choices=FAILED_TRICKS)
    parser.add_argument("--kind-act", choices=KIND_ACTS, dest="kind_act")
    parser.add_argument("--ending", choices=ENDINGS)
    parser.add_argument("-n", type=int, default=1, help="number of stories to generate")
    parser.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    parser.add_argument("--all", action="store_true", help="render the curated set")
    parser.add_argument("--trace", action="store_true", help="dump world-model state")
    parser.add_argument("--qa", action="store_true", help="include the three QA sections")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of text")
    parser.add_argument("--asp", action="store_true", help="list compatible combos from ASP")
    parser.add_argument("--verify", action="store_true", help="check ASP/Python parity and story validity")
    parser.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.backyard and args.trick and args.kind_act:
        backyard = BACKYARDS[args.backyard]
        trick = FAILED_TRICKS[args.trick]
        act = KIND_ACTS[args.kind_act]
        if not valid_transition(backyard, trick, act):
            raise StoryError(explain_rejection(backyard, trick, act))

    combos = [
        combo for combo in valid_combos()
        if (args.child is None or combo[0] == args.child)
        and (args.friend is None or combo[1] == args.friend)
        and (args.backyard is None or combo[2] == args.backyard)
        and (args.trick is None or combo[3] == args.trick)
        and (args.kind_act is None or combo[4] == args.kind_act)
        and (args.ending is None or combo[5] == args.ending)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    child, friend, backyard, trick, kind_act, ending = rng.choice(sorted(combos))
    return StoryParams(child, friend, backyard, trick, kind_act, ending)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        CHILDREN[params.child],
        FRIENDS[params.friend],
        BACKYARDS[params.backyard],
        FAILED_TRICKS[params.trick],
        KIND_ACTS[params.kind_act],
        ENDINGS[params.ending],
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
        print(asp_program("#show valid/6."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (child, friend, backyard, trick, kind_act, ending) combos:\n")
        for child, friend, backyard, trick, kind_act, ending in combos:
            print(f"  {child:5} {friend:5} {backyard:18} {trick:16} -> {kind_act:14} {ending}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 60):
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
                f"### {p.child}/{p.friend}: {p.backyard} {p.trick} -> "
                f"{p.kind_act} ({p.ending})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

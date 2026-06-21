#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/heck_chick_dim_vicinity_humor_adventure.py
=====================================================================

A small storyworld about a funny little rescue adventure in the farmyard
vicinity. Two children go looking for a missing chick at dusk, joke about their
tiny pool of light being "chick-dim", and learn that a gentle rescue works
better than a noisy one.

The world model prefers sensible rescue plans and rejects silly ones that would
only frighten the chick. It also includes an inline ASP twin for the
reasonableness gate and the outcome model.

Run it
------
    python storyworlds/worlds/gpt-5.4/heck_chick_dim_vicinity_humor_adventure.py
    python storyworlds/worlds/gpt-5.4/heck_chick_dim_vicinity_humor_adventure.py --all
    python storyworlds/worlds/gpt-5.4/heck_chick_dim_vicinity_humor_adventure.py --qa
    python storyworlds/worlds/gpt-5.4/heck_chick_dim_vicinity_humor_adventure.py --trace
    python storyworlds/worlds/gpt-5.4/heck_chick_dim_vicinity_humor_adventure.py --verify
"""

from __future__ import annotations

import argparse
import contextlib
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
SENSE_MIN = 2


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
        female = {"girl", "mother", "aunt", "woman"}
        male = {"boy", "father", "uncle", "man"}
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
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    opening: str
    clue: str
    hideouts: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Hideout:
    id: str
    label: str
    phrase: str
    approach: str
    need: str
    difficulty: int
    snaggy: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Light:
    id: str
    label: str
    phrase: str
    glow: str
    strength: int
    joke: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    sense: int
    power: int
    covers: set[str] = field(default_factory=set)
    setup: str = ""
    success: str = ""
    scramble: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    hideout: str
    light: str
    method: str
    child1: str
    child1_gender: str
    child2: str
    child2_gender: str
    helper: str
    helper_type: str
    chick_name: str
    delay: int = 0
    seed: Optional[int] = None


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
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"leader", "sidekick"}]

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


def _r_dark_worry(world: World) -> list[str]:
    if "light" not in world.entities or "chick" not in world.entities:
        return []
    light = world.get("light")
    chick = world.get("chick")
    if chick.meters["lost"] < THRESHOLD:
        return []
    if light.meters["brightness"] > 1:
        return []
    sig = ("dark_worry",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["worry"] += 1
    return ["__dark__"]


def _r_scramble(world: World) -> list[str]:
    chick = world.get("chick")
    if chick.meters["startled"] < THRESHOLD:
        return []
    sig = ("scramble",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    chick.meters["scrambled"] += 1
    if world.facts.get("hideout_cfg") and world.facts["hideout_cfg"].snaggy:
        chick.meters["snagged"] += 1
    for kid in world.kids():
        kid.memes["alarm"] += 1
    return ["__scramble__"]


def _r_rescue_relief(world: World) -> list[str]:
    chick = world.get("chick")
    if chick.meters["rescued"] < THRESHOLD:
        return []
    sig = ("relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    chick.meters["lost"] = 0.0
    chick.meters["startled"] = 0.0
    for kid in world.kids():
        kid.memes["relief"] += 1
        kid.memes["joy"] += 1
        kid.memes["worry"] = 0.0
    helper = world.get("helper")
    helper.memes["pride"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="dark_worry", tag="meme", apply=_r_dark_worry),
    Rule(name="scramble", tag="physical", apply=_r_scramble),
    Rule(name="relief", tag="meme", apply=_r_rescue_relief),
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
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


PLACES = {
    "barnyard": Place(
        id="barnyard",
        label="the barnyard",
        opening="Beyond the gate, the barnyard smelled of straw and warm wood.",
        clue="A trail of tiny prints danced past the feed room and vanished near the coop fence.",
        hideouts={"crate", "barrel", "hedge"},
        tags={"farm", "vicinity"},
    ),
    "orchard": Place(
        id="orchard",
        label="the orchard",
        opening="The orchard leaned full of crooked shadows and sweet apple smell.",
        clue="A squeaky peep came from the grass where fallen apples lay in the evening dew.",
        hideouts={"barrel", "hedge"},
        tags={"farm", "vicinity"},
    ),
    "pumpkin_patch": Place(
        id="pumpkin_patch",
        label="the pumpkin patch",
        opening="Round pumpkins sat like orange boulders, and the vines made twisty paths for explorers.",
        clue="Something small had waddled through the dusty leaves and disappeared with one last peep.",
        hideouts={"crate", "hedge"},
        tags={"farm", "vicinity"},
    ),
}

HIDEOUTS = {
    "crate": Hideout(
        id="crate",
        label="wooden crate",
        phrase="under a tippy wooden crate",
        approach="The crate sat at a slant, making a little cave just big enough for a chick.",
        need="trail",
        difficulty=1,
        snaggy=False,
        tags={"crate", "chick"},
    ),
    "barrel": Hideout(
        id="barrel",
        label="rain barrel",
        phrase="behind the old rain barrel",
        approach="The barrel cast a round shadow, and the ground beside it was cluttered with twigs.",
        need="call",
        difficulty=2,
        snaggy=False,
        tags={"barrel", "chick"},
    ),
    "hedge": Hideout(
        id="hedge",
        label="berry hedge",
        phrase="inside the scratchy berry hedge",
        approach="The hedge made a prickly tunnel with leaves that rustled at every breath.",
        need="tunnel",
        difficulty=2,
        snaggy=True,
        tags={"hedge", "chick"},
    ),
}

LIGHTS = {
    "pocket_lamp": Light(
        id="pocket_lamp",
        label="pocket lamp",
        phrase="a little pocket lamp",
        glow="made only a tiny yellow puddle on the ground",
        strength=1,
        joke='it was so small that they called it their "chick-dim" light',
        tags={"light", "dim"},
    ),
    "lantern": Light(
        id="lantern",
        label="lantern",
        phrase="a tin lantern",
        glow="spread a warm round glow over boots, straw, and fallen leaves",
        strength=2,
        joke='it was bright enough that the old "chick-dim" joke made them snort anyway',
        tags={"light", "lantern"},
    ),
    "headlamp": Light(
        id="headlamp",
        label="headlamp",
        phrase="a bouncy headlamp",
        glow="sent a clear beam hopping wherever they turned their heads",
        strength=2,
        joke='it was bright, but they still whispered "chick-dim" just to make each other laugh',
        tags={"light", "headlamp"},
    ),
}

METHODS = {
    "feed_trail": Method(
        id="feed_trail",
        label="feed trail",
        sense=3,
        power=2,
        covers={"trail"},
        setup="sprinkled a neat little line of corn crumbs from the open ground to the hiding place",
        success="The chick peeped, poked out a beak, and followed the crunchy trail step by step into the light",
        scramble="The first crumbs worked, but the shadows were confusing, and the chick popped out too fast and skittered in a loop around their boots",
        qa_text="made a crumb trail for the chick to follow",
        tags={"feed", "gentle"},
    ),
    "soft_call": Method(
        id="soft_call",
        label="soft call",
        sense=3,
        power=2,
        covers={"call"},
        setup='cupped their hands and made the same soft peeping sound the chick heard at feeding time',
        success="The chick answered with a squeak and came hurrying out as if it had found its own little song again",
        scramble="The chick answered, but then darted the wrong way first and made everybody spin in a silly circle before it stopped",
        qa_text="called softly so the chick would recognize a friendly sound",
        tags={"call", "gentle"},
    ),
    "basket_tunnel": Method(
        id="basket_tunnel",
        label="basket tunnel",
        sense=3,
        power=3,
        covers={"tunnel"},
        setup="set down a laundry basket on its side and made a calm little tunnel of open space leading out of the leaves",
        success="The chick blinked at the safe tunnel, gave one brave hop, and trotted right through it into waiting hands",
        scramble="The tunnel helped, but the chick still burst out in a feathery blur and landed where nobody expected",
        qa_text="used a laundry basket to make a safe tunnel out of the hedge",
        tags={"basket", "gentle"},
    ),
    "shout_and_chase": Method(
        id="shout_and_chase",
        label="shout and chase",
        sense=1,
        power=1,
        covers={"trail", "call", "tunnel"},
        setup='shouted "Boo!" and rushed forward',
        success="The chick did not feel rescued at all; it only panicked",
        scramble="The chick exploded out of hiding like a popcorn kernel with feet",
        qa_text="tried to scare the chick out by shouting",
        tags={"noisy"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Maya"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Finn", "Eli", "Theo"]
CHICK_NAMES = ["Pip", "Dot", "Button", "Sunny", "Pebble"]
HELPERS = [("mother", "Mom"), ("father", "Dad"), ("aunt", "Aunt May"), ("uncle", "Uncle Ray")]


CURATED = [
    StoryParams(
        place="barnyard",
        hideout="crate",
        light="pocket_lamp",
        method="feed_trail",
        child1="Lily",
        child1_gender="girl",
        child2="Tom",
        child2_gender="boy",
        helper="Mom",
        helper_type="mother",
        chick_name="Pip",
        delay=0,
    ),
    StoryParams(
        place="orchard",
        hideout="barrel",
        light="lantern",
        method="soft_call",
        child1="Ben",
        child1_gender="boy",
        child2="Mia",
        child2_gender="girl",
        helper="Aunt May",
        helper_type="aunt",
        chick_name="Pebble",
        delay=1,
    ),
    StoryParams(
        place="pumpkin_patch",
        hideout="hedge",
        light="pocket_lamp",
        method="basket_tunnel",
        child1="Zoe",
        child1_gender="girl",
        child2="Max",
        child2_gender="boy",
        helper="Dad",
        helper_type="father",
        chick_name="Button",
        delay=1,
    ),
    StoryParams(
        place="barnyard",
        hideout="hedge",
        light="headlamp",
        method="basket_tunnel",
        child1="Ella",
        child1_gender="girl",
        child2="Finn",
        child2_gender="boy",
        helper="Uncle Ray",
        helper_type="uncle",
        chick_name="Sunny",
        delay=0,
    ),
]


def place_supports(place_id: str, hideout_id: str) -> bool:
    return hideout_id in PLACES[place_id].hideouts


def method_fits(method: Method, hideout: Hideout) -> bool:
    return hideout.need in method.covers


def sensible_methods() -> list[Method]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for hideout_id in sorted(place.hideouts):
            hideout = HIDEOUTS[hideout_id]
            for method_id, method in METHODS.items():
                if method.sense >= SENSE_MIN and method_fits(method, hideout):
                    combos.append((place_id, hideout_id, method_id))
    return combos


def rescue_difficulty(hideout: Hideout, light: Light, delay: int) -> int:
    return hideout.difficulty + delay + (1 if light.strength <= 1 else 0)


def smooth_rescue(params: StoryParams) -> bool:
    hideout = HIDEOUTS[params.hideout]
    light = LIGHTS[params.light]
    method = METHODS[params.method]
    return method.power >= rescue_difficulty(hideout, light, params.delay)


def predict_outcome(hideout: Hideout, light: Light, method: Method, delay: int) -> dict:
    return {
        "difficulty": rescue_difficulty(hideout, light, delay),
        "smooth": method.power >= rescue_difficulty(hideout, light, delay),
    }


def introduce(world: World, a: Entity, b: Entity, helper: Entity, chick: Entity, light: Light) -> None:
    place = world.place
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["brave"] += 1
    world.say(
        f"{a.id} and {b.id} were the kind of children who could turn an ordinary evening into an expedition."
    )
    world.say(place.opening)
    world.say(
        f"That was when {helper.id} looked toward the coop and said, "
        f'"Oh heck, I can\'t see {chick.id} anywhere in the vicinity."'
    )
    world.say(
        f"{a.id} lifted {light.phrase}, which {light.glow}; {light.joke}."
    )
    world.say(
        f'"Then the {chick.id} Rescue Club is on the case," {b.id} said, puffing out {b.pronoun("possessive")} chest.'
    )


def find_clue(world: World, a: Entity, b: Entity, hideout: Hideout, chick: Entity) -> None:
    world.say(world.place.clue)
    world.say(
        f"The children followed the sound until they reached {hideout.phrase}. {hideout.approach}"
    )
    world.say(
        f'From somewhere inside, {chick.id} gave one worried peep, and both children froze as if they had found treasure.'
    )


def worry_beat(world: World, a: Entity, b: Entity) -> None:
    propagate(world, narrate=False)
    if a.memes["worry"] >= THRESHOLD or b.memes["worry"] >= THRESHOLD:
        world.say(
            f'The dark made the whole search feel bigger, and for a second {a.id} whispered, "What the heck if we lose the peep again?"'
        )
        world.say(
            f'"We won\'t," {b.id} said, though {b.pronoun()} held the light a little tighter.'
        )


def plan(world: World, a: Entity, b: Entity, helper: Entity, method: Method, hideout: Hideout) -> None:
    pred = predict_outcome(hideout, world.facts["light_cfg"], method, world.facts["delay"])
    world.facts["predicted_difficulty"] = pred["difficulty"]
    world.facts["predicted_smooth"] = pred["smooth"]
    a.memes["focus"] += 1
    b.memes["focus"] += 1
    world.say(
        f"{helper.id} crouched beside them and did not grab or rush. Together they {method.setup}."
    )
    if hideout.need == "trail":
        world.say(
            f'"Tiny feet, tiny steps," {helper.id} murmured. "Let {world.get("chick").id} choose the brave part."'
        )
    elif hideout.need == "call":
        world.say(
            f'"Soft sounds only," {helper.id} said. "A chick listens better than it argues."'
        )
    else:
        world.say(
            f'"No poking in the leaves," {helper.id} said. "We make the safe path, and the chick can take it."'
        )


def rescue_smooth(world: World, a: Entity, b: Entity, helper: Entity, chick: Entity, method: Method) -> None:
    chick.meters["rescued"] += 1
    propagate(world, narrate=False)
    world.say(method.success + ".")
    world.say(
        f"{a.id} scooped {chick.id} up with both hands, surprised at how warm and light {chick.pronoun()} felt."
    )
    world.say(
        f"{helper.id} laughed softly, and {b.id} laughed too, mostly because everybody had been so serious about someone so fluffy."
    )


def rescue_scramble(world: World, a: Entity, b: Entity, helper: Entity, chick: Entity, method: Method, hideout: Hideout) -> None:
    chick.meters["startled"] += 1
    propagate(world, narrate=False)
    line = method.scramble
    if hideout.snaggy:
        line += ", then got one foot tangled in a twig"
    world.say(line + ".")
    if hideout.snaggy:
        world.say(
            f'{a.id} made a tiny gasp, but {helper.id} slipped a sleeve under the branches and freed {chick.id} before the poor bird could panic.'
        )
    else:
        world.say(
            f"Instead of running away, {chick.id} bounced onto {b.id}'s shoe and then, for one ridiculous second, onto {a.id}'s head."
        )
    chick.meters["rescued"] += 1
    propagate(world, narrate=False)
    world.say(
        f"That was enough to make even worried people snort. Then {helper.id} lifted {chick.id} down gently and tucked {chick.pronoun('object')} against {helper.pronoun('possessive')} coat."
    )


def ending(world: World, a: Entity, b: Entity, helper: Entity, chick: Entity, light: Light) -> None:
    world.say(
        f"Back at the coop, {chick.id} hurried under {chick.pronoun('possessive')} mother's wing as if the whole adventure had only been a windy dream."
    )
    world.say(
        f'{helper.id} tapped the little light and smiled. "Next mission," {helper.pronoun()} said, "we bring the bright lamp before the chick-dim one."'
    )
    world.say(
        f'{a.id} and {b.id} saluted the coop like explorers finishing a grand map. The barnyard vicinity no longer felt spooky at all; it felt known.'
    )


def tell(
    place: Place,
    hideout: Hideout,
    light_cfg: Light,
    method_cfg: Method,
    child1: str,
    child1_gender: str,
    child2: str,
    child2_gender: str,
    helper_name: str,
    helper_type: str,
    chick_name: str,
    delay: int,
) -> World:
    world = World(place)
    a = world.add(Entity(id=child1, kind="character", type=child1_gender, role="leader"))
    b = world.add(Entity(id=child2, kind="character", type=child2_gender, role="sidekick"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper"))
    chick = world.add(
        Entity(
            id=chick_name,
            kind="character",
            type="chick",
            role="chick",
            label="chick",
            phrase="the missing chick",
            tags={"chick"},
        )
    )
    light = world.add(
        Entity(
            id="light",
            type="light",
            label=light_cfg.label,
            phrase=light_cfg.phrase,
            role="light",
            tags=set(light_cfg.tags),
        )
    )
    light.meters["brightness"] = float(light_cfg.strength)
    chick.meters["lost"] = 1.0

    world.facts.update(
        place_cfg=place,
        hideout_cfg=hideout,
        light_cfg=light_cfg,
        method_cfg=method_cfg,
        delay=delay,
    )

    introduce(world, a, b, helper, chick, light_cfg)
    find_clue(world, a, b, hideout, chick)

    world.para()
    worry_beat(world, a, b)
    plan(world, a, b, helper, method_cfg, hideout)

    world.para()
    if smooth_rescue(
        StoryParams(
            place=place.id,
            hideout=hideout.id,
            light=light_cfg.id,
            method=method_cfg.id,
            child1=child1,
            child1_gender=child1_gender,
            child2=child2,
            child2_gender=child2_gender,
            helper=helper_name,
            helper_type=helper_type,
            chick_name=chick_name,
            delay=delay,
        )
    ):
        rescue_smooth(world, a, b, helper, chick, method_cfg)
        outcome = "smooth"
    else:
        rescue_scramble(world, a, b, helper, chick, method_cfg, hideout)
        outcome = "scramble"

    world.para()
    ending(world, a, b, helper, chick, light_cfg)

    world.facts.update(
        child1=a,
        child2=b,
        helper=helper,
        chick=chick,
        outcome=outcome,
        rescued=chick.meters["rescued"] >= THRESHOLD,
        snagged=chick.meters["snagged"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "chick": [
        (
            "What is a chick?",
            "A chick is a baby chicken. It is small, soft, and needs warmth and careful handling."
        )
    ],
    "vicinity": [
        (
            "What does vicinity mean?",
            "Vicinity means the area nearby. If something is in the vicinity, it is somewhere close around you."
        )
    ],
    "light": [
        (
            "Why is a bright light helpful when it gets dark?",
            "A brighter light helps you see where you are stepping and what is around you. That makes searching safer and calmer."
        )
    ],
    "feed": [
        (
            "Why would a chick follow crumbs or feed?",
            "Chicks know their food by sight and sound, so a little trail can guide them without frightening them."
        )
    ],
    "call": [
        (
            "Why should you use a soft voice around a scared animal?",
            "A soft voice is less startling than a shout. Scared animals often come closer when they feel safe."
        )
    ],
    "basket": [
        (
            "How can a basket help rescue a small animal?",
            "A basket can make a gentle path or barrier. It helps guide a tiny animal without grabbing or squeezing it."
        )
    ],
    "hedge": [
        (
            "Why can a hedge be tricky for a tiny chick?",
            "A hedge has twigs and scratchy branches. A little chick can get confused or caught there more easily than in open ground."
        )
    ],
    "humor": [
        (
            'Why can a funny joke help during a scary moment?',
            "A small joke can loosen tight feelings and help people stay calm. Laughing a little can make it easier to think clearly."
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place_cfg"]
    hideout = f["hideout_cfg"]
    light = f["light_cfg"]
    chick = f["chick"]
    return [
        'Write a funny adventure story for a 3-to-5-year-old that includes the words "heck", "chick-dim", and "vicinity".',
        f"Tell a gentle rescue adventure where two children search {place.label} for a missing chick named {chick.id} and find {chick.pronoun('object')} {hideout.phrase}.",
        f"Write a child-facing story with a little humor, a careful grown-up, and a small light called {light.label} that helps turn a spooky search into a happy ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["child1"]
    b = f["child2"]
    helper = f["helper"]
    chick = f["chick"]
    hideout = f["hideout_cfg"]
    light = f["light_cfg"]
    method = f["method_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {a.id} and {b.id}, who go on a rescue adventure with {helper.id}. They are trying to find a missing chick named {chick.id}."
        ),
        (
            f"Where did they look for {chick.id}?",
            f"They searched in the vicinity of {world.place.label} and followed peeps until they reached {hideout.phrase}. The place looked dark and tricky, which made the search feel like a real adventure."
        ),
        (
            'Why did they call the light "chick-dim"?',
            f"They joked that the light was " + ('very tiny and dim' if light.strength <= 1 else 'part of their old dim-light joke') + f". The joke added humor, but it also showed they knew the search would be harder in weak light."
        ),
        (
            f"How did {helper.id} help?",
            f"{helper.id} stayed calm and helped them {method.qa_text}. The plan worked because it guided {chick.id} gently instead of scaring {chick.pronoun('object')}."
        ),
    ]
    if f["outcome"] == "smooth":
        qa.append(
            (
                f"Did the rescue go smoothly?",
                f"Yes. {chick.id} came out without a wild dash, and {a.id} was able to scoop {chick.pronoun('object')} up safely. The gentle method matched the hiding place, so the rescue stayed calm."
            )
        )
    else:
        qa.append(
            (
                f"What funny thing happened during the rescue?",
                f"The rescue turned into a silly scramble before it ended safely. That happened because the hiding place and the darkness made {chick.id} pop out in a burst instead of stepping out neatly."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with {chick.id} back at the coop and everyone feeling relieved. The spooky search changed into a happy memory, and the barnyard vicinity no longer felt mysterious."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"chick", "vicinity", "humor", "light"}
    hideout = f["hideout_cfg"]
    method = f["method_cfg"]
    if hideout.id == "hedge":
        tags.add("hedge")
    if method.id == "feed_trail":
        tags.add("feed")
    if method.id == "soft_call":
        tags.add("call")
    if method.id == "basket_tunnel":
        tags.add("basket")
    order = ["chick", "vicinity", "light", "feed", "call", "basket", "hedge", "humor"]
    out: list[tuple[str, str]] = []
    for tag in order:
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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_place(place_id: str, hideout_id: str) -> str:
    return (
        f"(No story: {HIDEOUTS[hideout_id].label} is not a supported hiding place in {PLACES[place_id].label}. "
        f"Pick one of {sorted(PLACES[place_id].hideouts)} instead.)"
    )


def explain_method(method_id: str) -> str:
    method = METHODS[method_id]
    if method.sense < SENSE_MIN:
        better = ", ".join(sorted(m.id for m in sensible_methods()))
        return (
            f"(Refusing method '{method_id}': it is too noisy and low-sense for a scared chick "
            f"(sense={method.sense} < {SENSE_MIN}). Try one of: {better}.)"
        )
    return (
        f"(No story: {method.label} does not fit this hiding place. The rescue should match what the chick needs.)"
    )


ASP_RULES = r"""
sensible(M) :- method(M), sense(M, S), sense_min(Min), S >= Min.
valid(P, H, M) :- place(P), hideout(H), method(M),
                  supports(P, H), sensible(M), needs(H, N), covers(M, N).

difficulty(D + Delay + 1) :- chosen_hideout(H), hideout_difficulty(H, D),
                             chosen_light(L), light_strength(L, S), S <= 1, delay(Delay).
difficulty(D + Delay) :- chosen_hideout(H), hideout_difficulty(H, D),
                         chosen_light(L), light_strength(L, S), S > 1, delay(Delay).

smooth :- chosen_method(M), method_power(M, P), difficulty(D), P >= D.
outcome(smooth) :- smooth.
outcome(scramble) :- not smooth.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for hideout_id in sorted(place.hideouts):
            lines.append(asp.fact("supports", place_id, hideout_id))
    for hideout_id, hideout in HIDEOUTS.items():
        lines.append(asp.fact("hideout", hideout_id))
        lines.append(asp.fact("needs", hideout_id, hideout.need))
        lines.append(asp.fact("hideout_difficulty", hideout_id, hideout.difficulty))
    for light_id, light in LIGHTS.items():
        lines.append(asp.fact("light", light_id))
        lines.append(asp.fact("light_strength", light_id, light.strength))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("sense", method_id, method.sense))
        lines.append(asp.fact("method_power", method_id, method.power))
        for need in sorted(method.covers):
            lines.append(asp.fact("covers", method_id, need))
    lines.append(asp.fact("sense_min", SENSE_MIN))
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
            asp.fact("chosen_hideout", params.hideout),
            asp.fact("chosen_light", params.light),
            asp.fact("chosen_method", params.method),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Funny rescue adventure storyworld: a missing chick, a dim light, and a gentle plan."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hideout", choices=HIDEOUTS)
    ap.add_argument("--light", choices=LIGHTS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--helper", choices=[h[0] for h in HELPERS])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="extra time before the children find the chick")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    names = [n for n in pool if n != avoid]
    return rng.choice(names), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.hideout and not place_supports(args.place, args.hideout):
        raise StoryError(explain_place(args.place, args.hideout))
    if args.method and METHODS[args.method].sense < SENSE_MIN:
        raise StoryError(explain_method(args.method))

    combos = [
        c
        for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.hideout is None or c[1] == args.hideout)
        and (args.method is None or c[2] == args.method)
    ]
    if not combos:
        if args.place and args.hideout and not place_supports(args.place, args.hideout):
            raise StoryError(explain_place(args.place, args.hideout))
        if args.hideout and args.method:
            raise StoryError(explain_method(args.method))
        raise StoryError("(No valid combination matches the given options.)")

    place_id, hideout_id, method_id = rng.choice(sorted(combos))
    light_id = args.light or rng.choice(sorted(LIGHTS))
    child1, g1 = _pick_child(rng)
    child2, g2 = _pick_child(rng, avoid=child1)
    helper_type, helper_name = rng.choice(HELPERS)
    if args.helper:
        helper_type = args.helper
        helper_name = next(name for kind, name in HELPERS if kind == helper_type)
    chick_name = rng.choice(CHICK_NAMES)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        place=place_id,
        hideout=hideout_id,
        light=light_id,
        method=method_id,
        child1=child1,
        child1_gender=g1,
        child2=child2,
        child2_gender=g2,
        helper=helper_name,
        helper_type=helper_type,
        chick_name=chick_name,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.hideout not in HIDEOUTS:
        raise StoryError(f"(Unknown hideout: {params.hideout})")
    if params.light not in LIGHTS:
        raise StoryError(f"(Unknown light: {params.light})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")
    if not place_supports(params.place, params.hideout):
        raise StoryError(explain_place(params.place, params.hideout))
    if METHODS[params.method].sense < SENSE_MIN:
        raise StoryError(explain_method(params.method))
    if not method_fits(METHODS[params.method], HIDEOUTS[params.hideout]):
        raise StoryError(explain_method(params.method))

    world = tell(
        place=PLACES[params.place],
        hideout=HIDEOUTS[params.hideout],
        light_cfg=LIGHTS[params.light],
        method_cfg=METHODS[params.method],
        child1=params.child1,
        child1_gender=params.child1_gender,
        child2=params.child2,
        child2_gender=params.child2_gender,
        helper_name=params.helper,
        helper_type=params.helper_type,
        chick_name=params.chick_name,
        delay=params.delay,
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


def outcome_of(params: StoryParams) -> str:
    return "smooth" if smooth_rescue(params) else "scramble"


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
    for seed in range(40):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(seed))
            p.seed = seed
            cases.append(p)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure at seed {seed}.")
            break

    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)} outcomes differ.")
        for p in mismatches[:5]:
            print(" ", p)

    try:
        smoke = generate(CURATED[0])
        with contextlib.redirect_stdout(io.StringIO()):
            emit(smoke, trace=True, qa=True, header="### smoke")
        print("OK: smoke test generate()/emit() passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, hideout, method) combos:\n")
        for place, hideout, method in combos:
            print(f"  {place:13} {hideout:8} {method}")
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
            header = f"### {p.child1} & {p.child2}: {p.hideout} at {p.place} ({p.method}, {outcome_of(p)})"
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

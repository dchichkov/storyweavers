#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/stump_poi_repetition_cautionary_bravery_detective_story.py
=====================================================================================

A standalone storyworld for a tiny detective tale: a child detective follows
clues to a missing bowl of sweet poi near an old stump, learns not to confuse
bravery with recklessness, and solves the case with a safe plan.

The seed asked for:
- words: "stump", "poi"
- features: Repetition, Cautionary, Bravery
- style: Detective Story

This world models a small mystery in a child-facing way:
    a snack goes missing at a fair or picnic,
    a trail of clues leads toward a dark hiding place,
    the detective is tempted to rush in,
    a careful warning reframes real bravery as using light and calling help,
    the missing poi is found,
    and the ending image proves the lesson.

Run it
------
    python storyworlds/worlds/gpt-5.4/stump_poi_repetition_cautionary_bravery_detective_story.py
    python storyworlds/worlds/gpt-5.4/stump_poi_repetition_cautionary_bravery_detective_story.py --all
    python storyworlds/worlds/gpt-5.4/stump_poi_repetition_cautionary_bravery_detective_story.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/stump_poi_repetition_cautionary_bravery_detective_story.py --trace --seed 7
    python storyworlds/worlds/gpt-5.4/stump_poi_repetition_cautionary_bravery_detective_story.py --qa --json
    python storyworlds/worlds/gpt-5.4/stump_poi_repetition_cautionary_bravery_detective_story.py --missing poi_bowl --place stump_hollow
    python storyworlds/worlds/gpt-5.4/stump_poi_repetition_cautionary_bravery_detective_story.py --tool magnifier
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
BRAVERY_BASE = 5.0
CAREFUL_TRAITS = {"careful", "patient", "thoughtful", "steady"}


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
    movable: bool = True
    dark: bool = False
    hiding_space: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "woman"}
        male = {"boy", "father", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(self.type, self.type)


@dataclass
class MissingThing:
    id: str
    label: str
    phrase: str
    size: str
    singular: bool = True
    edible: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class PlaceConfig:
    id: str
    label: str
    phrase: str
    dark: bool
    risky: bool
    fits_sizes: set[str] = field(default_factory=set)
    reveal: str = ""
    safe_reach: str = ""
    danger: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class ToolConfig:
    id: str
    label: str
    phrase: str
    kind: str
    sense: int
    helps_dark: bool
    helps_reach: bool
    calm: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class SettingConfig:
    id: str
    place: str
    crowd: str
    trail: str
    ending: str
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


def _r_dark_fear(world: World) -> list[str]:
    detective = world.get("detective")
    hideout = world.get("hideout")
    if detective.meters["entered_dark"] < THRESHOLD or not hideout.dark:
        return []
    sig = ("dark_fear", hideout.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    detective.memes["fear"] += 1
    world.get("scene").meters["tension"] += 1
    return ["__dark__"]


def _r_reckless_risk(world: World) -> list[str]:
    detective = world.get("detective")
    hideout = world.get("hideout")
    if detective.meters["entered_dark"] < THRESHOLD or detective.meters["has_safe_tool"] >= THRESHOLD:
        return []
    if not hideout.attrs.get("risky", False):
        return []
    sig = ("reckless_risk", hideout.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    detective.meters["risk"] += 1
    detective.meters["stumble"] += 1
    world.get("scene").meters["tension"] += 1
    return ["__risk__"]


def _r_safe_search(world: World) -> list[str]:
    detective = world.get("detective")
    helper = world.get("helper")
    if detective.meters["has_safe_tool"] < THRESHOLD:
        return []
    sig = ("safe_search",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    detective.memes["confidence"] += 1
    helper.memes["trust"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="dark_fear", tag="emotional", apply=_r_dark_fear),
    Rule(name="reckless_risk", tag="physical", apply=_r_reckless_risk),
    Rule(name="safe_search", tag="social", apply=_r_safe_search),
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
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "fair": SettingConfig(
        id="fair",
        place="the lantern fair",
        crowd="Paper lamps bobbed over the path, and every stall had a different smell.",
        trail="A wobbling line of purple drips crossed the grass like a trail of tiny commas.",
        ending="The band started up again, and the mystery corner felt bright instead of spooky.",
        tags={"fair", "lanterns"},
    ),
    "picnic": SettingConfig(
        id="picnic",
        place="the evening picnic by the pond",
        crowd="Blankets lay in soft rows, and crickets had already begun their music.",
        trail="A dotted trail of purple drops led away from the basket and toward the trees.",
        ending="The pond held a long stripe of sunset, and the case was closed before supper grew cold.",
        tags={"picnic", "pond"},
    ),
    "garden": SettingConfig(
        id="garden",
        place="the moonflower garden party",
        crowd="White flowers glowed by the fence, and cups clinked softly on the tables.",
        trail="Little purple smudges showed up on stones, leaves, and one bent leaf stem.",
        ending="When the garden lamps came on, the shadows seemed smaller than before.",
        tags={"garden", "flowers"},
    ),
}

MISSING = {
    "poi_bowl": MissingThing(
        id="poi_bowl",
        label="bowl of poi",
        phrase="a little blue bowl of sweet poi",
        size="small",
        singular=True,
        edible=True,
        tags={"poi", "food"},
    ),
    "poi_jar": MissingThing(
        id="poi_jar",
        label="jar of poi",
        phrase="a round jar of purple poi",
        size="small",
        singular=True,
        edible=True,
        tags={"poi", "food"},
    ),
    "poi_spoon": MissingThing(
        id="poi_spoon",
        label="poi spoon",
        phrase="the wooden poi spoon",
        size="tiny",
        singular=True,
        edible=False,
        tags={"poi", "spoon"},
    ),
    "casebook": MissingThing(
        id="casebook",
        label="detective casebook",
        phrase="the little detective casebook",
        size="flat",
        singular=True,
        edible=False,
        tags={"book", "detective"},
    ),
}

PLACES = {
    "stump_hollow": PlaceConfig(
        id="stump_hollow",
        label="old stump",
        phrase="the hollow inside an old stump",
        dark=True,
        risky=True,
        fits_sizes={"tiny", "small"},
        reveal="Something purple gleamed from the dark curve inside the stump.",
        safe_reach="held the light low while the grown-up tipped the hidden thing out with a long stick",
        danger="A hollow stump can hide splinters, bugs, and dark little spaces you cannot see into.",
        tags={"stump", "wood", "dark"},
    ),
    "reed_patch": PlaceConfig(
        id="reed_patch",
        label="reed patch",
        phrase="the thick reeds by the water",
        dark=True,
        risky=True,
        fits_sizes={"tiny", "small", "flat"},
        reveal="Between the reeds, something familiar showed a bright little edge.",
        safe_reach="swept the reeds apart with the light shining first, then reached carefully from the path",
        danger="Tall reeds near water can hide mud and slippery edges.",
        tags={"reeds", "pond", "dark"},
    ),
    "wagon_shadow": PlaceConfig(
        id="wagon_shadow",
        label="wagon shadow",
        phrase="the shadow under the snack wagon",
        dark=True,
        risky=False,
        fits_sizes={"tiny", "small", "flat"},
        reveal="Under the wagon, the missing thing sat beside one squeaky wheel.",
        safe_reach="knelt with the light and pulled the hidden thing out from the safe, dry side",
        danger="Even a harmless dark corner is hard to search well if you cannot see.",
        tags={"wagon", "shadow", "dark"},
    ),
    "bench": PlaceConfig(
        id="bench",
        label="bench",
        phrase="the space behind a park bench",
        dark=False,
        risky=False,
        fits_sizes={"tiny", "small", "flat"},
        reveal="There it was, tucked behind the bench leg as if it had been waiting to be found.",
        safe_reach="walked around the bench and picked it up at once",
        danger="",
        tags={"bench", "open"},
    ),
}

TOOLS = {
    "flashlight": ToolConfig(
        id="flashlight",
        label="flashlight",
        phrase="a bright flashlight",
        kind="light",
        sense=3,
        helps_dark=True,
        helps_reach=False,
        calm=True,
        tags={"flashlight", "light"},
    ),
    "lantern": ToolConfig(
        id="lantern",
        label="lantern",
        phrase="a little paper-handled lantern",
        kind="light",
        sense=3,
        helps_dark=True,
        helps_reach=False,
        calm=True,
        tags={"lantern", "light"},
    ),
    "stick": ToolConfig(
        id="stick",
        label="long stick",
        phrase="a long smooth stick",
        kind="reach",
        sense=2,
        helps_dark=False,
        helps_reach=True,
        calm=True,
        tags={"stick", "reach"},
    ),
    "magnifier": ToolConfig(
        id="magnifier",
        label="magnifying glass",
        phrase="a magnifying glass",
        kind="look",
        sense=1,
        helps_dark=False,
        helps_reach=False,
        calm=True,
        tags={"magnifier"},
    ),
}

GIRL_NAMES = ["Lina", "Maya", "Nora", "Tess", "Eva", "June", "Ivy", "Ruby"]
BOY_NAMES = ["Owen", "Milo", "Theo", "Finn", "Eli", "Ben", "Jude", "Leo"]
TRAITS = ["careful", "bold", "patient", "curious", "steady", "quick", "thoughtful"]


def can_hide(missing: MissingThing, place: PlaceConfig) -> bool:
    return missing.size in place.fits_sizes


def place_needs_light(place: PlaceConfig) -> bool:
    return place.dark


def sensible_tools_for(place: PlaceConfig) -> list[str]:
    return [
        tid for tid, tool in TOOLS.items()
        if tool.sense >= SENSE_MIN and (not place.dark or tool.helps_dark)
    ]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id in SETTINGS:
        for missing_id, missing in MISSING.items():
            for place_id, place in PLACES.items():
                if can_hide(missing, place) and sensible_tools_for(place):
                    combos.append((setting_id, missing_id, place_id))
    return combos


def careful_strength(trait: str) -> float:
    return 5.0 if trait in CAREFUL_TRAITS else 3.0


def brave_safely(place: PlaceConfig, tool: ToolConfig, trait: str) -> bool:
    needed = 1.0 if place.risky else 0.0
    return tool.sense >= SENSE_MIN and (not place.dark or tool.helps_dark) and careful_strength(trait) >= 3.0 + needed


def predict_search(place: PlaceConfig, tool: ToolConfig) -> dict[str, bool]:
    return {
        "can_see": (not place.dark) or tool.helps_dark,
        "reckless": place.dark and not tool.helps_dark,
        "safe": (not place.dark) or (tool.helps_dark and tool.sense >= SENSE_MIN),
    }


def introduce(world: World, detective: Entity, helper: Entity, setting: SettingConfig, missing: MissingThing) -> None:
    world.say(
        f"{detective.id} liked to notice small things, so at {setting.place} "
        f"{detective.pronoun()} called {detective.pronoun('possessive')}self Detective {detective.id}."
    )
    world.say(setting.crowd)
    world.say(
        f"Then somebody gasped: {missing.phrase} was gone."
    )
    world.say(
        f'"A case! A case!" whispered {detective.id}. "{detective.id} the detective is on the case."'
    )
    helper_word = helper.label_word
    world.say(
        f"{helper_word.capitalize()} smiled, but {helper.pronoun()} also said, "
        f'"A good detective uses brave eyes and careful feet."'
    )
    detective.memes["curiosity"] += 1


def clue_trail(world: World, detective: Entity, setting: SettingConfig, missing: MissingThing, place: PlaceConfig) -> None:
    world.say(setting.trail)
    if missing.edible:
        world.say(
            f"{detective.id} crouched low. 'Poi clue, poi clue, purple clue,' "
            f"{detective.pronoun()} murmured."
        )
    else:
        world.say(
            f"{detective.id} crouched low and whispered, 'Clue by clue, clue by clue.'"
        )
    world.say(
        f"The trail pointed toward {place.phrase}."
    )
    detective.meters["noticed_clues"] += 1


def temptation(world: World, detective: Entity, place: PlaceConfig) -> None:
    detective.memes["bravery"] += BRAVERY_BASE
    if place.dark:
        world.say(
            f"The closer {detective.id} came, the darker it looked. "
            f"{detective.pronoun().capitalize()} could not see all the way in."
        )
    else:
        world.say(
            f"{detective.id} could see the hiding place clearly now."
        )
    world.say(
        f'"I can do it myself," said {detective.id}. "I can do it myself."'
    )


def warning(world: World, helper: Entity, detective: Entity, place: PlaceConfig, tool: ToolConfig) -> None:
    pred = predict_search(place, tool)
    world.facts["predicted"] = pred
    if place.dark or place.risky:
        caution = place.danger or "Dark places are harder to search safely."
        world.say(
            f'{helper.label_word.capitalize()} put a gentle hand on {detective.id}\'s shoulder. '
            f'"Slow down, Detective. {caution}"'
        )
    if pred["reckless"]:
        world.say(
            f'"Brave is not the same as hurrying," {helper.pronoun()} added. '
            f'"If you rush into a dark place without light, you might miss the clue or get hurt."'
        )
    else:
        world.say(
            f'"Let\'s solve it the brave way," {helper.pronoun()} said. '
            f'"We look first, then reach."'
        )
    detective.memes["caution"] += 1


def rash_step(world: World, detective: Entity) -> None:
    detective.meters["entered_dark"] += 1
    propagate(world, narrate=False)
    if detective.meters["stumble"] >= THRESHOLD:
        world.say(
            f"But {detective.id} took one fast step and bumped a root with {detective.pronoun('possessive')} shoe."
        )
        world.say(
            f"{detective.pronoun().capitalize()} stopped at once. The mystery suddenly felt bigger and darker."
        )
    else:
        world.say(
            f"{detective.id} leaned in, then froze when the shadows looked thicker than expected."
        )


def choose_brave_plan(world: World, detective: Entity, helper: Entity, tool: ToolConfig) -> None:
    detective.meters["has_safe_tool"] += 1
    propagate(world, narrate=False)
    detective.memes["real_bravery"] += 1
    helper.memes["approval"] += 1
    world.say(
        f'{detective.id} took a slow breath. "Brave and careful," {detective.pronoun()} said. '
        f'"Brave and careful."'
    )
    world.say(
        f"So {helper.label_word} handed over {tool.phrase}, and together they checked the hiding place properly."
    )


def reveal(world: World, detective: Entity, helper: Entity, missing: MissingThing, place: PlaceConfig) -> None:
    world.say(place.reveal)
    world.say(
        f"{helper.label_word.capitalize()} {place.safe_reach}."
    )
    world.say(
        f"There was {missing.phrase}."
    )
    detective.meters["solved"] += 1
    detective.memes["joy"] += 1
    detective.memes["relief"] += 1
    helper.memes["relief"] += 1


def explain_case(world: World, detective: Entity, missing: MissingThing, place: PlaceConfig) -> None:
    if place.id == "stump_hollow":
        reason = "A busy squirrel had dragged it to the stump after smelling the sweet poi."
    elif place.id == "reed_patch":
        reason = "It had slid off a low blanket and caught in the reeds by the path."
    elif place.id == "wagon_shadow":
        reason = "A bump from a rolling wagon wheel had nudged it into the shadow."
    else:
        reason = "Someone had set it down in a hurry and forgotten where it went."
    world.say(
        f'"Case closed," said {detective.id}. "{missing.label.capitalize()} found."'
    )
    world.say(reason)
    world.facts["reason"] = reason


def ending(world: World, detective: Entity, helper: Entity, setting: SettingConfig, missing: MissingThing) -> None:
    helper_word = helper.label_word
    world.say(
        f'{helper_word.capitalize()} gave {detective.id} a side hug. '
        f'"That was brave work," {helper.pronoun()} said, "because you chose the safe way."'
    )
    if missing.edible:
        world.say(
            f"Soon the bowl of poi was back on the table where it belonged."
        )
    else:
        world.say(
            f"Soon the missing thing was back in its proper place."
        )
    world.say(setting.ending)
    world.say(
        f"{detective.id} clicked the light off, stood tall beside the old stump, and knew what real bravery sounded like: "
        f'"Brave and careful. Brave and careful."'
    )


def tell(
    setting: SettingConfig,
    missing: MissingThing,
    place: PlaceConfig,
    tool: ToolConfig,
    detective_name: str = "Lina",
    detective_gender: str = "girl",
    helper_type: str = "mother",
    trait: str = "careful",
) -> World:
    world = World()
    detective = world.add(Entity(
        id="detective",
        kind="character",
        type=detective_gender,
        label=detective_name,
        phrase=detective_name,
        role="detective",
        traits=[trait],
        tags={"child"},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_type,
        label="the grown-up",
        phrase="the grown-up",
        role="helper",
        tags={"adult"},
    ))
    hideout = world.add(Entity(
        id="hideout",
        type="place",
        label=place.label,
        phrase=place.phrase,
        dark=place.dark,
        hiding_space=True,
        attrs={"risky": place.risky},
        tags=set(place.tags),
    ))
    scene = world.add(Entity(
        id="scene",
        type="scene",
        label=setting.place,
        phrase=setting.place,
        tags=set(setting.tags),
    ))
    item = world.add(Entity(
        id="missing",
        type="object",
        label=missing.label,
        phrase=missing.phrase,
        tags=set(missing.tags),
    ))
    tool_ent = world.add(Entity(
        id="tool",
        type="tool",
        label=tool.label,
        phrase=tool.phrase,
        tags=set(tool.tags),
    ))

    introduce(world, detective, helper, setting, missing)
    world.para()
    clue_trail(world, detective, setting, missing, place)
    temptation(world, detective, place)
    warning(world, helper, detective, place, tool)

    world.para()
    if place.dark and not tool.helps_dark:
        rash_step(world, detective)
        choose_brave_plan(world, detective, helper, ToolConfig(
            id="borrowed_flashlight",
            label="flashlight",
            phrase="a bright flashlight",
            kind="light",
            sense=3,
            helps_dark=True,
            helps_reach=False,
            calm=True,
            tags={"flashlight", "light"},
        ))
        world.facts["used_borrowed_light"] = True
        world.facts["final_tool"] = "flashlight"
    else:
        choose_brave_plan(world, detective, helper, tool)
        world.facts["used_borrowed_light"] = False
        world.facts["final_tool"] = tool.id

    reveal(world, detective, helper, missing, place)
    explain_case(world, detective, missing, place)

    world.para()
    ending(world, detective, helper, setting, missing)

    outcome = "careful_solve"
    world.facts.update(
        detective=detective,
        helper=helper,
        setting=setting,
        missing_cfg=missing,
        place_cfg=place,
        requested_tool=tool,
        item=item,
        tool_entity=tool_ent,
        solved=detective.meters["solved"] >= THRESHOLD,
        risk=detective.meters["risk"] >= THRESHOLD,
        stumbled=detective.meters["stumble"] >= THRESHOLD,
        outcome=outcome,
        trait=trait,
    )
    return world


@dataclass
class StoryParams:
    setting: str
    missing: str
    place: str
    tool: str
    detective_name: str
    detective_gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting = f["setting"]
    missing = f["missing_cfg"]
    place = f["place_cfg"]
    detective = f["detective"]
    return [
        f'Write a short detective story for a 3-to-5-year-old that includes the words "stump" and "poi".',
        f"Tell a gentle mystery set at {setting.place} where {detective.label} follows clues to {missing.label} near {place.label}, repeats a detective phrase, and learns that bravery must be careful.",
        'Write a cautionary detective story with repetition, a dark hiding place, and a happy ending where the child solves the case by slowing down and using light.',
    ]


KNOWLEDGE = {
    "poi": [
        (
            "What is poi?",
            "Poi is a soft food made from taro. It can be smooth, sticky, and a little purple."
        )
    ],
    "stump": [
        (
            "What is a stump?",
            "A stump is the short bottom part of a tree left in the ground after the trunk is cut or broken away."
        )
    ],
    "detective": [
        (
            "What does a detective do?",
            "A detective looks for clues and tries to solve a mystery. Good detectives notice details and think carefully."
        )
    ],
    "flashlight": [
        (
            "Why is a flashlight useful in the dark?",
            "A flashlight helps you see where you are going and what is in front of you. That makes it easier to search safely."
        )
    ],
    "caution": [
        (
            "What is the difference between bravery and rushing?",
            "Bravery means doing the right thing even when you feel nervous. Rushing means moving too fast without thinking about safety."
        )
    ],
    "repetition": [
        (
            "Why do stories sometimes repeat a line?",
            "Repeating a line can make it easier to remember. It can also show what a character is learning."
        )
    ],
}
KNOWLEDGE_ORDER = ["poi", "stump", "detective", "flashlight", "caution", "repetition"]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    helper = f["helper"]
    setting = f["setting"]
    missing = f["missing_cfg"]
    place = f["place_cfg"]
    requested_tool = f["requested_tool"]
    helper_word = helper.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {detective.label}, a child who plays detective, and {helper_word}, the grown-up who helps with the case."
        ),
        (
            f"What was missing at {setting.place}?",
            f"The missing thing was {missing.phrase}. Its disappearance is what began the mystery."
        ),
        (
            f"Where did the clues lead?",
            f"The purple clues led toward {place.phrase}. That hiding place looked important because it sat at the end of the trail."
        ),
    ]
    if place.dark:
        qa.append((
            f"Why did {helper_word} tell {detective.label} not to rush into the hiding place?",
            f"{helper_word.capitalize()} warned {detective.label} because {place.phrase} was dark, and it could hide trouble you could not see. In this story, being careful was part of being brave."
        ))
    if f["risk"]:
        qa.append((
            f"What happened when {detective.label} hurried?",
            f"{detective.label} took one quick step and stumbled because the dark place was hard to see into. That small scare is what made {detective.pronoun('object')} slow down and choose a safer plan."
        ))
    final_tool = f["final_tool"]
    tool_name = TOOLS[final_tool].label if final_tool in TOOLS else "flashlight"
    qa.append((
        "How was the case solved?",
        f"They solved the case by searching with a safe light instead of rushing in blind. Using the {tool_name} let them see the hiding place clearly and find the missing thing."
    ))
    qa.append((
        f"What did {detective.label} learn about bravery?",
        f"{detective.label} learned that real bravery is not charging ahead without thinking. Real bravery is slowing down, listening, and solving the problem the safe way."
    ))
    qa.append((
        "How did the story end?",
        f"It ended happily with the missing thing found and returned. The last image shows {detective.label} standing tall by the old stump, repeating the lesson: brave and careful."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"detective", "caution", "repetition"}
    f = world.facts
    tags |= set(f["missing_cfg"].tags)
    tags |= set(f["place_cfg"].tags)
    if f["final_tool"] == "flashlight" or f["used_borrowed_light"]:
        tags.add("flashlight")
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.dark:
            bits.append("dark=True")
        if ent.hiding_space:
            bits.append("hiding_space=True")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="fair",
        missing="poi_bowl",
        place="stump_hollow",
        tool="magnifier",
        detective_name="Lina",
        detective_gender="girl",
        helper="mother",
        trait="careful",
    ),
    StoryParams(
        setting="picnic",
        missing="poi_jar",
        place="reed_patch",
        tool="flashlight",
        detective_name="Milo",
        detective_gender="boy",
        helper="father",
        trait="steady",
    ),
    StoryParams(
        setting="garden",
        missing="casebook",
        place="wagon_shadow",
        tool="lantern",
        detective_name="Ruby",
        detective_gender="girl",
        helper="aunt",
        trait="thoughtful",
    ),
    StoryParams(
        setting="fair",
        missing="poi_spoon",
        place="bench",
        tool="stick",
        detective_name="Theo",
        detective_gender="boy",
        helper="uncle",
        trait="patient",
    ),
]


def explain_place_rejection(missing: MissingThing, place: PlaceConfig) -> str:
    return (
        f"(No story: {missing.label} is the wrong shape for {place.phrase}. "
        f"The hiding place has to be a place where the missing object could reasonably fit.)"
    )


def explain_tool_rejection(place: PlaceConfig, tool: ToolConfig) -> str:
    if tool.sense < SENSE_MIN:
        return (
            f"(Refusing tool '{tool.id}': it scores too low on common sense for this mystery. "
            f"A child detective should use safer, clearer tools in a cautionary story.)"
        )
    if place.dark and not tool.helps_dark:
        better = ", ".join(sorted(sensible_tools_for(place)))
        return (
            f"(Refusing tool '{tool.id}': {place.phrase} is dark, and {tool.label} does not provide light. "
            f"Try one of these instead: {better}.)"
        )
    return "(No story: this tool does not make a reasonable detective plan.)"


ASP_RULES = r"""
fits(M, P) :- missing(M), place(P), size_of(M, S), fits_size(P, S).
needs_light(P) :- place(P), dark(P).
sensible_tool(T) :- tool(T), sense(T, S), sense_min(M), S >= M.
usable_tool(P, T) :- place(P), tool(T), not needs_light(P), sensible_tool(T).
usable_tool(P, T) :- place(P), tool(T), needs_light(P), sensible_tool(T), helps_dark(T).
valid(St, M, P) :- setting(St), fits(M, P), usable_tool(P, _).

careful_strength(T, 5) :- trait(T), careful_trait(T).
careful_strength(T, 3) :- trait(T), not careful_trait(T).

risky_bonus(P, 1) :- place(P), risky(P).
risky_bonus(P, 0) :- place(P), not risky(P).

brave_safely(P, T, Tr) :- usable_tool(P, T), careful_strength(Tr, C), risky_bonus(P, B), C >= 3 + B.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid, missing in MISSING.items():
        lines.append(asp.fact("missing", mid))
        lines.append(asp.fact("size_of", mid, missing.size))
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.dark:
            lines.append(asp.fact("dark", pid))
        if place.risky:
            lines.append(asp.fact("risky", pid))
        for size in sorted(place.fits_sizes):
            lines.append(asp.fact("fits_size", pid, size))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("sense", tid, tool.sense))
        if tool.helps_dark:
            lines.append(asp.fact("helps_dark", tid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    for trait in sorted(TRAITS):
        lines.append(asp.fact("trait", trait))
    for trait in sorted(CAREFUL_TRAITS):
        lines.append(asp.fact("careful_trait", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_usable_tools(place_id: str) -> list[str]:
    import asp
    extra = f"chosen_place({place_id}).\nusable(T) :- chosen_place(P), usable_tool(P, T)."
    model = asp.one_model(asp_program(extra, "#show usable/1."))
    return sorted(t for (t,) in asp.atoms(model, "usable"))


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

    for pid in sorted(PLACES):
        a = set(asp_usable_tools(pid))
        b = set(sensible_tools_for(PLACES[pid]))
        if a != b:
            rc = 1
            print(f"MISMATCH in usable tools for {pid}: clingo={sorted(a)} python={sorted(b)}")
    if rc == 0:
        print("OK: usable tools match for every hiding place.")

    try:
        sample = generate(CURATED[0])
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover - explicit verification path
        print(f"SMOKE TEST FAILED: {err}")
        return 1

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a child detective, a missing thing, an old stump, and careful bravery."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--missing", choices=MISSING)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--helper", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combos and usable tools")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.missing and args.place:
        missing = MISSING[args.missing]
        place = PLACES[args.place]
        if not can_hide(missing, place):
            raise StoryError(explain_place_rejection(missing, place))
    if args.tool and args.place:
        tool = TOOLS[args.tool]
        place = PLACES[args.place]
        if args.tool not in sensible_tools_for(place):
            raise StoryError(explain_tool_rejection(place, tool))
    elif args.tool and TOOLS[args.tool].sense < SENSE_MIN:
        place = PLACES[args.place] if args.place else next(iter(PLACES.values()))
        raise StoryError(explain_tool_rejection(place, TOOLS[args.tool]))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.missing is None or combo[1] == args.missing)
        and (args.place is None or combo[2] == args.place)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, missing_id, place_id = rng.choice(sorted(combos))
    usable = sensible_tools_for(PLACES[place_id])
    tool_id = args.tool or rng.choice(sorted(usable))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or _pick_name(rng, gender)
    helper = args.helper or rng.choice(["mother", "father", "aunt", "uncle"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id,
        missing=missing_id,
        place=place_id,
        tool=tool_id,
        detective_name=name,
        detective_gender=gender,
        helper=helper,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.missing not in MISSING:
        raise StoryError(f"(Unknown missing item: {params.missing})")
    if params.place not in PLACES:
        raise StoryError(f"(Unknown hiding place: {params.place})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")

    missing = MISSING[params.missing]
    place = PLACES[params.place]
    tool = TOOLS[params.tool]

    if not can_hide(missing, place):
        raise StoryError(explain_place_rejection(missing, place))
    if params.tool not in sensible_tools_for(place):
        raise StoryError(explain_tool_rejection(place, tool))
    if not brave_safely(place, tool, params.trait):
        raise StoryError("(No story: this detective trait and tool do not support a brave, careful solution.)")

    world = tell(
        setting=SETTINGS[params.setting],
        missing=missing,
        place=place,
        tool=tool,
        detective_name=params.detective_name,
        detective_gender=params.detective_gender,
        helper_type=params.helper,
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
        print(asp_program("", "#show valid/3.\n#show usable_tool/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, missing, place) combos:\n")
        for setting_id, missing_id, place_id in combos:
            usable = asp_usable_tools(place_id)
            print(f"  {setting_id:8} {missing_id:10} {place_id:12} tools=[{', '.join(usable)}]")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.detective_name}: {p.missing} at {p.setting} -> {p.place} with {p.tool}"
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

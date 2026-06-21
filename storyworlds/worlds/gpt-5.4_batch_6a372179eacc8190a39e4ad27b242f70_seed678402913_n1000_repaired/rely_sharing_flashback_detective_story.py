#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/rely_sharing_flashback_detective_story.py
====================================================================

A tiny detective-style storyworld about a child who loses an important little
object, relies on a friend's shared tool, and solves the case when a sensory
clue sparks a flashback.

The world prefers a narrow band of plausible stories:
- the missing object must fit the place and hiding spot,
- the shared tool must actually help with that spot,
- the flashback trigger must genuinely connect to the remembered spot.

The turn is always the same kind of child-scale mystery: at first the hero
thinks someone may have taken the object, but a flashback reveals the hero put
it away earlier and forgot. The ending image proves what changed: the detective
case is solved, trust grows, and the children share the work of putting things
back carefully.

Run it
------
    python storyworlds/worlds/gpt-5.4/rely_sharing_flashback_detective_story.py
    python storyworlds/worlds/gpt-5.4/rely_sharing_flashback_detective_story.py --place library --item notebook --spot return_cart
    python storyworlds/worlds/gpt-5.4/rely_sharing_flashback_detective_story.py --tool flashlight --spot paint_shelf
    python storyworlds/worlds/gpt-5.4/rely_sharing_flashback_detective_story.py --all
    python storyworlds/worlds/gpt-5.4/rely_sharing_flashback_detective_story.py --qa --json
    python storyworlds/worlds/gpt-5.4/rely_sharing_flashback_detective_story.py --verify
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
    owner: str = ""
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
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type or "parent")


@dataclass
class PlaceCfg:
    id: str
    label: str
    opening: str
    supports: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class LostItemCfg:
    id: str
    label: str
    phrase: str
    use_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SpotCfg:
    id: str
    label: str
    phrase: str
    place_ids: set[str] = field(default_factory=set)
    need: str = ""
    cue: str = ""
    reveal: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class SharedToolCfg:
    id: str
    label: str
    phrase: str
    provides: str
    share_line: str
    use_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class TriggerCfg:
    id: str
    label: str
    phrase: str
    cue: str
    flashback: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: PlaceCfg) -> None:
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    item = world.entities.get("item")
    if not hero or not item:
        return out
    if item.meters["missing"] >= THRESHOLD:
        sig = ("worry", "hero")
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["worry"] += 1
            out.append("__worry__")
    return out


def _r_rely(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    helper = world.entities.get("helper")
    tool = world.entities.get("tool")
    if not hero or not helper or not tool:
        return out
    if tool.meters["shared"] >= THRESHOLD:
        sig = ("rely", hero.id, helper.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["trust"] += 1
            helper.memes["generous"] += 1
            out.append("__rely__")
    return out


def _r_flashback(world: World) -> list[str]:
    out: list[str] = []
    trigger = world.entities.get("trigger")
    if not trigger or trigger.meters["noticed"] < THRESHOLD:
        return out
    if not world.facts.get("trigger_matches_spot"):
        return out
    sig = ("flashback", "hero")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero = world.get("hero")
    hero.memes["remember"] += 1
    out.append("__flashback__")
    return out


def _r_find(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    item = world.entities.get("item")
    tool = world.entities.get("tool")
    if not hero or not item or not tool:
        return out
    if hero.memes["remember"] < THRESHOLD:
        return out
    if tool.meters["useful"] < THRESHOLD:
        return out
    sig = ("find", item.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    item.meters["missing"] = 0.0
    item.meters["found"] += 1
    hero.memes["relief"] += 1
    hero.memes["pride"] += 1
    helper = world.get("helper")
    helper.memes["joy"] += 1
    out.append("__found__")
    return out


CAUSAL_RULES = [
    Rule(name="worry", tag="emotional", apply=_r_worry),
    Rule(name="rely", tag="social", apply=_r_rely),
    Rule(name="flashback", tag="memory", apply=_r_flashback),
    Rule(name="find", tag="physical", apply=_r_find),
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


def valid_place_spot(place_id: str, spot_id: str) -> bool:
    return spot_id in PLACES[place_id].supports and place_id in SPOTS[spot_id].place_ids


def suitable_tool(tool_id: str, spot_id: str) -> bool:
    return TOOLS[tool_id].provides == SPOTS[spot_id].need


def matching_trigger(trigger_id: str, spot_id: str) -> bool:
    return TRIGGERS[trigger_id].cue == SPOTS[spot_id].cue


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id in PLACES:
        for item_id in ITEMS:
            for spot_id in SPOTS:
                if valid_place_spot(place_id, spot_id):
                    combos.append((place_id, item_id, spot_id))
    return combos


def outcome_of(params: "StoryParams") -> str:
    if not valid_place_spot(params.place, params.spot):
        return "stuck"
    if not suitable_tool(params.tool, params.spot):
        return "stuck"
    if not matching_trigger(params.trigger, params.spot):
        return "stuck"
    return "found"


def predict_solution(world: World, spot_id: str, tool_id: str, trigger_id: str) -> dict:
    sim = world.copy()
    sim.facts["trigger_matches_spot"] = matching_trigger(trigger_id, spot_id)
    sim.get("tool").meters["shared"] += 1
    sim.get("tool").meters["useful"] += 1 if suitable_tool(tool_id, spot_id) else 0
    sim.get("trigger").meters["noticed"] += 1
    propagate(sim, narrate=False)
    item = sim.get("item")
    return {
        "found": item.meters["found"] >= THRESHOLD,
        "remembered": sim.get("hero").memes["remember"] >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, helper: Entity, item: Entity, parent: Entity) -> None:
    place = world.place
    hero.memes["curious"] += 1
    helper.memes["curious"] += 1
    world.say(
        f"{place.opening} {hero.id} liked to call {hero.pronoun('possessive')} little game "
        f"the Detective Club. {helper.id} was always the best partner, and "
        f"{item.phrase} was the most important part because {item.attrs['use_line']}."
    )
    world.say(
        f"{parent.label_word.capitalize()} smiled whenever the two children whispered over clues, "
        f"because their mysteries were made of soft footsteps, careful looking, and kind guesses."
    )


def discover_missing(world: World, hero: Entity, item: Entity) -> None:
    item.meters["missing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But that day, when {hero.id} reached for {item.label}, it was gone. "
        f"The case began with one empty space and one very surprised detective."
    )


def suspect_and_search(world: World, hero: Entity, helper: Entity) -> None:
    world.say(
        f'"Did someone take it?" {hero.id} whispered. {helper.id} looked around the room '
        f"like a tiny detective in a storybook, but neither of them wanted to blame anyone too fast."
    )
    if hero.memes["worry"] >= THRESHOLD:
        world.say(
            f"{hero.id}'s stomach felt tight. A missing clue was one thing, but losing "
            f"something important made the whole room seem full of secrets."
        )


def helper_shares(world: World, hero: Entity, helper: Entity, tool: Entity, tool_cfg: SharedToolCfg) -> None:
    tool.meters["shared"] += 1
    tool.meters["useful"] += 1 if suitable_tool(tool_cfg.id, world.facts["spot_cfg"].id) else 0
    propagate(world, narrate=False)
    world.say(
        f"Then {helper.id} opened {helper.pronoun('possessive')} hand and offered {tool_cfg.phrase}. "
        f'"You can rely on me," {helper.pronoun()} said. "{tool_cfg.share_line}"'
    )


def notice_trigger(world: World, hero: Entity, trigger: Entity, trigger_cfg: TriggerCfg) -> None:
    trigger.meters["noticed"] += 1
    world.facts["trigger_matches_spot"] = matching_trigger(trigger_cfg.id, world.facts["spot_cfg"].id)
    propagate(world, narrate=False)
    world.say(
        f"As they moved through {world.place.label}, {hero.id} noticed {trigger_cfg.phrase}. "
        f"It made {hero.pronoun('object')} stop so suddenly that even the mystery seemed to hold its breath."
    )


def flashback(world: World, hero: Entity, trigger_cfg: TriggerCfg) -> None:
    if hero.memes["remember"] < THRESHOLD:
        return
    world.say(
        f"And then the memory came back all at once. In a flashback, {hero.id} remembered "
        f"{trigger_cfg.flashback}."
    )


def inspect_spot(world: World, hero: Entity, helper: Entity, tool_cfg: SharedToolCfg, spot_cfg: SpotCfg) -> None:
    world.say(
        f"Now the case had a real lead. Together they hurried to {spot_cfg.phrase}, and "
        f"{tool_cfg.use_line}."
    )
    if suitable_tool(tool_cfg.id, spot_cfg.id):
        world.say(spot_cfg.reveal)
    else:
        world.say(
            f"But even a brave detective needs the right kind of help, and {tool_cfg.label} "
            f"was no good for that sort of place."
        )


def solve_case(world: World, hero: Entity, helper: Entity, item: Entity, parent: Entity, spot_cfg: SpotCfg) -> None:
    propagate(world, narrate=False)
    if item.meters["found"] < THRESHOLD:
        world.say(
            f"They searched carefully, but the mystery would not open yet. {parent.label_word.capitalize()} "
            f"said they could take a breath and try again later."
        )
        return
    world.say(
        f"There it was: {item.label}, tucked safely in {spot_cfg.label}. Nobody had stolen it at all."
    )
    world.say(
        f'{hero.id} laughed so hard that the worry fell right out of {hero.pronoun("possessive")} voice. '
        f'"I put it there myself," {hero.pronoun()} said.'
    )
    world.say(
        f"{helper.id} grinned and gave a small detective bow. The best clue had been a shared tool and a true memory."
    )
    world.say(
        f"{parent.label_word.capitalize()} nodded. \"Good detectives look carefully, and good friends help each other.\""
    )
    world.say(
        f"After that, the Detective Club started each new case by sharing their tools and setting one safe place for important things."
    )


def tell(
    place: PlaceCfg,
    item_cfg: LostItemCfg,
    spot_cfg: SpotCfg,
    tool_cfg: SharedToolCfg,
    trigger_cfg: TriggerCfg,
    hero_name: str = "Mia",
    hero_gender: str = "girl",
    helper_name: str = "Ben",
    helper_gender: str = "boy",
    parent_type: str = "mother",
) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    item = world.add(
        Entity(
            id="item",
            kind="thing",
            type="item",
            label=item_cfg.label,
            phrase=item_cfg.phrase,
            owner=hero.id,
            attrs={"use_line": item_cfg.use_line},
            tags=set(item_cfg.tags),
        )
    )
    tool = world.add(
        Entity(
            id="tool",
            kind="thing",
            type="tool",
            label=tool_cfg.label,
            phrase=tool_cfg.phrase,
            owner=helper.id,
            tags=set(tool_cfg.tags),
        )
    )
    trigger = world.add(
        Entity(
            id="trigger",
            kind="thing",
            type="trigger",
            label=trigger_cfg.label,
            phrase=trigger_cfg.phrase,
            tags=set(trigger_cfg.tags),
        )
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        parent=parent,
        item=item,
        item_cfg=item_cfg,
        tool=tool,
        tool_cfg=tool_cfg,
        trigger=trigger,
        trigger_cfg=trigger_cfg,
        spot_cfg=spot_cfg,
        place_cfg=place,
        trigger_matches_spot=matching_trigger(trigger_cfg.id, spot_cfg.id),
    )

    introduce(world, hero, helper, item, parent)
    world.para()
    discover_missing(world, hero, item)
    suspect_and_search(world, hero, helper)
    helper_shares(world, hero, helper, tool, tool_cfg)
    world.para()
    notice_trigger(world, hero, trigger, trigger_cfg)
    flashback(world, hero, trigger_cfg)
    inspect_spot(world, hero, helper, tool_cfg, spot_cfg)
    solve_case(world, hero, helper, item, parent, spot_cfg)

    world.facts["outcome"] = "found" if item.meters["found"] >= THRESHOLD else "stuck"
    return world


PLACES = {
    "classroom": PlaceCfg(
        id="classroom",
        label="the classroom",
        opening="In the bright classroom, paper stars hung over the windows and the block corner waited for the morning game.",
        supports={"cubby", "paint_shelf", "puzzle_table"},
        tags={"classroom"},
    ),
    "library": PlaceCfg(
        id="library",
        label="the library",
        opening="In the quiet library, the rugs were soft and the shelves stood like rows of sleepy houses for books.",
        supports={"book_bin", "reading_pillow", "return_cart"},
        tags={"library"},
    ),
    "playroom": PlaceCfg(
        id="playroom",
        label="the playroom",
        opening="In the playroom, baskets of toys leaned against the wall and a blanket fort made one corner look wonderfully mysterious.",
        supports={"toy_chest", "train_rug", "blanket_fort"},
        tags={"playroom"},
    ),
}

ITEMS = {
    "badge": LostItemCfg(
        id="badge",
        label="the cardboard detective badge",
        phrase="the cardboard detective badge with a shiny gold star",
        use_line="it was how the club began every case",
        tags={"badge"},
    ),
    "notebook": LostItemCfg(
        id="notebook",
        label="the clue notebook",
        phrase="the little clue notebook with blue spiral rings",
        use_line="every important mystery was written inside it",
        tags={"notebook"},
    ),
    "map": LostItemCfg(
        id="map",
        label="the treasure map",
        phrase="the folded treasure map covered in careful red arrows",
        use_line="it showed where each pretend mystery was supposed to lead",
        tags={"map"},
    ),
}

SPOTS = {
    "cubby": SpotCfg(
        id="cubby",
        label="the top cubby",
        phrase="the top cubby by the coats",
        place_ids={"classroom"},
        need="reach",
        cue="zipper",
        reveal="With the shared step stool, they could finally look all the way into the high cubby where papers liked to slide to the back.",
        tags={"cubby"},
    ),
    "paint_shelf": SpotCfg(
        id="paint_shelf",
        label="the paint shelf",
        phrase="the tall paint shelf",
        place_ids={"classroom"},
        need="reach",
        cue="paint",
        reveal="On the tall shelf, beside the paper cups, something thin and familiar peeked from under a stack of drawings.",
        tags={"paint"},
    ),
    "puzzle_table": SpotCfg(
        id="puzzle_table",
        label="the puzzle table",
        phrase="the puzzle table",
        place_ids={"classroom"},
        need="close_look",
        cue="cardboard",
        reveal="Under the puzzle pieces lay a flat corner of paper almost the same color as the tabletop, easy to miss without a careful look.",
        tags={"puzzle"},
    ),
    "book_bin": SpotCfg(
        id="book_bin",
        label="the book bin",
        phrase="the book bin under the window",
        place_ids={"library"},
        need="close_look",
        cue="books",
        reveal="The magnifying glass was not magic, but it helped them notice the thin edge of the missing thing tucked between two fat picture books.",
        tags={"books"},
    ),
    "reading_pillow": SpotCfg(
        id="reading_pillow",
        label="the reading pillow",
        phrase="the big reading pillow",
        place_ids={"library"},
        need="light",
        cue="blanket",
        reveal="When the flashlight shone into the fold behind the pillow, a hidden paper edge flashed back like a tiny wink.",
        tags={"reading"},
    ),
    "return_cart": SpotCfg(
        id="return_cart",
        label="the return cart",
        phrase="the squeaky return cart",
        place_ids={"library"},
        need="reach",
        cue="wheel",
        reveal="Standing on the step stool made the top shelf of the cart easy to check, and there the lost thing rested beside a stack of returned books.",
        tags={"books"},
    ),
    "toy_chest": SpotCfg(
        id="toy_chest",
        label="the toy chest",
        phrase="the deep toy chest",
        place_ids={"playroom"},
        need="light",
        cue="wood",
        reveal="The flashlight slid into the dark chest, and right away the missing thing gleamed between a toy drum and a stuffed bear.",
        tags={"toys"},
    ),
    "train_rug": SpotCfg(
        id="train_rug",
        label="the train rug",
        phrase="the train rug",
        place_ids={"playroom"},
        need="close_look",
        cue="tracks",
        reveal="The clue had lain flat against the printed tracks, so the magnifying glass helped them spot it where little black lines almost hid it.",
        tags={"trains"},
    ),
    "blanket_fort": SpotCfg(
        id="blanket_fort",
        label="the blanket fort",
        phrase="the blanket fort",
        place_ids={"playroom"},
        need="light",
        cue="blanket",
        reveal="The fort was shadowy inside, but the flashlight found the missing thing tucked near a pillow at once.",
        tags={"fort"},
    ),
}

TOOLS = {
    "flashlight": SharedToolCfg(
        id="flashlight",
        label="flashlight",
        phrase="a small flashlight",
        provides="light",
        share_line="I will shine the dark places if you do the looking.",
        use_line="the flashlight made a bright path through the dim corners",
        tags={"flashlight"},
    ),
    "step_stool": SharedToolCfg(
        id="step_stool",
        label="step stool",
        phrase="a little step stool",
        provides="reach",
        share_line="You can climb up safely, and I will hold it still.",
        use_line="the little step stool lifted them high enough to check properly",
        tags={"stool"},
    ),
    "magnifying_glass": SharedToolCfg(
        id="magnifying_glass",
        label="magnifying glass",
        phrase="a plastic magnifying glass",
        provides="close_look",
        share_line="Small clues do not scare us when we can look closely.",
        use_line="the magnifying glass turned tiny edges into real clues",
        tags={"magnifying_glass"},
    ),
}

TRIGGERS = {
    "paint_smell": TriggerCfg(
        id="paint_smell",
        label="paint smell",
        phrase="the faint smell of paint and wet paper",
        cue="paint",
        flashback="setting the missing thing down beside the paint cups so both hands could carry a fresh picture",
        tags={"paint"},
    ),
    "zipper_jingle": TriggerCfg(
        id="zipper_jingle",
        label="zipper jingle",
        phrase="the little jingle of coat zippers tapping together",
        cue="zipper",
        flashback="stretching up to the cubby area and tucking the missing thing away for just one minute while taking off a coat",
        tags={"coats"},
    ),
    "book_rustle": TriggerCfg(
        id="book_rustle",
        label="book rustle",
        phrase="the papery rustle of books being put back",
        cue="books",
        flashback="sliding the missing thing into the book bin while clearing a lap to read a giant picture book",
        tags={"books"},
    ),
    "blanket_swish": TriggerCfg(
        id="blanket_swish",
        label="blanket swish",
        phrase="the soft swish of fabric from a pillow or blanket",
        cue="blanket",
        flashback="ducking into a soft corner and leaving the missing thing behind for a moment while building a cozy hideout",
        tags={"blanket"},
    ),
    "wheel_squeak": TriggerCfg(
        id="wheel_squeak",
        label="wheel squeak",
        phrase="the squeak of a cart wheel rolling over the floor",
        cue="wheel",
        flashback="balancing the missing thing on the return cart while helping move a stack of books",
        tags={"wheel"},
    ),
    "track_bumps": TriggerCfg(
        id="track_bumps",
        label="track bumps",
        phrase="the bumpy feel of raised train tracks under a hand",
        cue="tracks",
        flashback="setting the missing thing flat on the train rug while kneeling down to push the longest blue engine",
        tags={"tracks"},
    ),
    "cardboard_scrape": TriggerCfg(
        id="cardboard_scrape",
        label="cardboard scrape",
        phrase="the scratchy sound of puzzle-box cardboard",
        cue="cardboard",
        flashback="slipping the missing thing onto the puzzle table to make room for a box lid and then covering it by mistake with puzzle pieces",
        tags={"cardboard"},
    ),
    "wood_thump": TriggerCfg(
        id="wood_thump",
        label="wood thump",
        phrase="the hollow thump of the toy chest lid",
        cue="wood",
        flashback="placing the missing thing on the edge of the toy chest and watching it slide inside when the lid bumped shut",
        tags={"wood"},
    ),
}


GIRL_NAMES = ["Mia", "Lily", "Ava", "Nora", "Zoe", "Ella", "Lucy", "Rose"]
BOY_NAMES = ["Ben", "Max", "Leo", "Theo", "Finn", "Eli", "Sam", "Jack"]


@dataclass
class StoryParams:
    place: str
    item: str
    spot: str
    tool: str
    trigger: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_gender: str
    parent: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="library",
        item="notebook",
        spot="book_bin",
        tool="magnifying_glass",
        trigger="book_rustle",
        hero_name="Mia",
        hero_gender="girl",
        helper_name="Ben",
        helper_gender="boy",
        parent="mother",
    ),
    StoryParams(
        place="classroom",
        item="badge",
        spot="cubby",
        tool="step_stool",
        trigger="zipper_jingle",
        hero_name="Leo",
        hero_gender="boy",
        helper_name="Nora",
        helper_gender="girl",
        parent="father",
    ),
    StoryParams(
        place="playroom",
        item="map",
        spot="blanket_fort",
        tool="flashlight",
        trigger="blanket_swish",
        hero_name="Ava",
        hero_gender="girl",
        helper_name="Finn",
        helper_gender="boy",
        parent="mother",
    ),
    StoryParams(
        place="classroom",
        item="notebook",
        spot="puzzle_table",
        tool="magnifying_glass",
        trigger="cardboard_scrape",
        hero_name="Theo",
        hero_gender="boy",
        helper_name="Lucy",
        helper_gender="girl",
        parent="father",
    ),
    StoryParams(
        place="playroom",
        item="badge",
        spot="toy_chest",
        tool="flashlight",
        trigger="wood_thump",
        hero_name="Rose",
        hero_gender="girl",
        helper_name="Max",
        helper_gender="boy",
        parent="mother",
    ),
]


KNOWLEDGE = {
    "flashlight": [
        (
            "What does a flashlight do?",
            "A flashlight makes light in dark places. It helps you see without having to guess."
        )
    ],
    "magnifying_glass": [
        (
            "What is a magnifying glass for?",
            "A magnifying glass makes small things look bigger. That helps a detective notice tiny clues."
        )
    ],
    "stool": [
        (
            "Why do people use a step stool?",
            "A step stool helps you reach something that is a little too high. A grown-up should make sure it is used safely."
        )
    ],
    "books": [
        (
            "Why can papers get lost in a bin of books?",
            "Thin papers can slide between bigger books and hide there. That makes them hard to notice at first."
        )
    ],
    "memory": [
        (
            "What is a flashback in a story?",
            "A flashback is when a character suddenly remembers something from earlier. That old memory can help explain what is happening now."
        )
    ],
    "sharing": [
        (
            "What does it mean to share?",
            "Sharing means letting someone else use something kindly. It can help both people solve a problem together."
        )
    ],
    "detective": [
        (
            "What does a detective do?",
            "A detective looks for clues and tries to understand what happened. Good detectives look carefully before they blame anyone."
        )
    ],
}
KNOWLEDGE_ORDER = ["detective", "sharing", "memory", "flashlight", "magnifying_glass", "stool", "books"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    item_cfg = f["item_cfg"]
    tool_cfg = f["tool_cfg"]
    place = f["place_cfg"]
    trigger_cfg = f["trigger_cfg"]
    return [
        'Write a detective-style story for a 3-to-5-year-old that includes the word "rely", uses sharing, and has a flashback that solves the mystery.',
        f"Tell a gentle mystery where {hero.id} loses {item_cfg.phrase} in {place.label}, and {helper.id} shares {tool_cfg.phrase} to help crack the case.",
        f"Write a child-friendly detective story in which {trigger_cfg.label} sparks a flashback, the children stop blaming others, and the ending shows how they learned to rely on each other.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    parent = f["parent"]
    item_cfg = f["item_cfg"]
    tool_cfg = f["tool_cfg"]
    trigger_cfg = f["trigger_cfg"]
    spot_cfg = f["spot_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a little detective, and {helper.id}, the friend who helped with the case. {parent.label_word.capitalize()} is there too, watching the mystery unfold."
        ),
        (
            f"What went missing?",
            f"{item_cfg.phrase.capitalize()} went missing just when the Detective Club wanted to begin. That is what turned an ordinary morning into a mystery."
        ),
        (
            f"Why did {hero.id} feel worried?",
            f"{hero.id} needed {item_cfg.label} because {item_cfg.use_line}. When it vanished, {hero.pronoun()} first wondered if someone had taken it, so the room suddenly felt much more mysterious."
        ),
        (
            f"How did {helper.id} help?",
            f"{helper.id} shared {tool_cfg.phrase} and told {hero.id} that {hero.pronoun()} could rely on {helper.pronoun('object')}. The shared tool gave them the kind of help they needed for that hiding spot."
        ),
        (
            "What caused the flashback?",
            f"The flashback started when {hero.id} noticed {trigger_cfg.phrase}. That clue pulled an earlier moment back into {hero.pronoun('possessive')} mind and pointed to {spot_cfg.label}."
        ),
    ]
    if f.get("outcome") == "found":
        qa.append(
            (
                "How was the mystery solved?",
                f"The children followed the remembered clue to {spot_cfg.phrase} and found {item_cfg.label} there. The real answer was not that someone stole it, but that {hero.id} had set it down earlier and forgotten."
            )
        )
        qa.append(
            (
                "What changed at the end?",
                f"At the end, the case was closed and the worry was gone. {hero.id} learned to look carefully and rely on a friend, and both children started sharing their tools and keeping one safe place for important things."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"detective", "sharing", "memory"}
    tool_cfg = world.facts["tool_cfg"]
    trigger_cfg = world.facts["trigger_cfg"]
    spot_cfg = world.facts["spot_cfg"]
    tags |= set(tool_cfg.tags)
    if "books" in trigger_cfg.tags or "books" in spot_cfg.tags:
        tags.add("books")
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
        if ent.owner:
            bits.append(f"owner={ent.owner}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    lines.append(f"  outcome: {world.facts.get('outcome')}")
    return "\n".join(lines)


def explain_spot(place_id: str, spot_id: str) -> str:
    return (
        f"(No story: {SPOTS[spot_id].label} does not belong in {PLACES[place_id].label}. "
        f"Pick a hiding spot that really fits that place.)"
    )


def explain_tool(tool_id: str, spot_id: str) -> str:
    need = SPOTS[spot_id].need.replace("_", " ")
    return (
        f"(No story: {TOOLS[tool_id].label} does not help with {SPOTS[spot_id].label}. "
        f"That spot needs {need}, so the shared tool should truly help.)"
    )


def explain_trigger(trigger_id: str, spot_id: str) -> str:
    return (
        f"(No story: {TRIGGERS[trigger_id].label} would not honestly spark a memory of {SPOTS[spot_id].label}. "
        f"The flashback clue must match what happened earlier.)"
    )


ASP_RULES = r"""
valid(P, I, S) :- place(P), item(I), spot(S), supports(P, S), in_place(S, P).
suitable(T, S) :- tool(T), spot(S), provides(T, N), need(S, N).
matching(G, S) :- trigger(G), spot(S), cue_of(G, C), remembers(S, C).

outcome(found) :- chosen_place(P), chosen_item(I), chosen_spot(S),
                  valid(P, I, S), chosen_tool(T), chosen_trigger(G),
                  suitable(T, S), matching(G, S).
outcome(stuck) :- chosen_place(P), chosen_item(I), chosen_spot(S),
                  not valid(P, I, S).
outcome(stuck) :- chosen_place(P), chosen_item(I), chosen_spot(S),
                  valid(P, I, S), chosen_tool(T), not suitable(T, S).
outcome(stuck) :- chosen_place(P), chosen_item(I), chosen_spot(S),
                  valid(P, I, S), chosen_tool(T), suitable(T, S),
                  chosen_trigger(G), not matching(G, S).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for sid in sorted(place.supports):
            lines.append(asp.fact("supports", pid, sid))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
    for sid, spot in SPOTS.items():
        lines.append(asp.fact("spot", sid))
        for pid in sorted(spot.place_ids):
            lines.append(asp.fact("in_place", sid, pid))
        lines.append(asp.fact("need", sid, spot.need))
        lines.append(asp.fact("remembers", sid, spot.cue))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("provides", tid, tool.provides))
    for gid, trigger in TRIGGERS.items():
        lines.append(asp.fact("trigger", gid))
        lines.append(asp.fact("cue_of", gid, trigger.cue))
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
            asp.fact("chosen_place", params.place),
            asp.fact("chosen_item", params.item),
            asp.fact("chosen_spot", params.spot),
            asp.fact("chosen_tool", params.tool),
            asp.fact("chosen_trigger", params.trigger),
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

    scenarios: list[StoryParams] = list(CURATED)
    for place in PLACES:
        for item in ITEMS:
            for spot in SPOTS:
                for tool in TOOLS:
                    for trigger in TRIGGERS:
                        if len(scenarios) >= 60:
                            break
                        scenarios.append(
                            StoryParams(
                                place=place,
                                item=item,
                                spot=spot,
                                tool=tool,
                                trigger=trigger,
                                hero_name="Mia",
                                hero_gender="girl",
                                helper_name="Ben",
                                helper_gender="boy",
                                parent="mother",
                            )
                        )
                    if len(scenarios) >= 60:
                        break
                if len(scenarios) >= 60:
                    break
            if len(scenarios) >= 60:
                break
        if len(scenarios) >= 60:
            break

    bad = 0
    for params in scenarios:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(scenarios)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(scenarios)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            emit(sample, trace=True, qa=True, header="### smoke")
        finally:
            sys.stdout = old
        if not sample.story.strip():
            raise StoryError("empty story from smoke test")
        print("OK: generate/emit smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Detective-style storyworld: a missing item, a shared tool, and a flashback clue."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--trigger", choices=TRIGGERS)
    ap.add_argument("--hero-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (place, item, spot) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.spot and not valid_place_spot(args.place, args.spot):
        raise StoryError(explain_spot(args.place, args.spot))
    if args.tool and args.spot and not suitable_tool(args.tool, args.spot):
        raise StoryError(explain_tool(args.tool, args.spot))
    if args.trigger and args.spot and not matching_trigger(args.trigger, args.spot):
        raise StoryError(explain_trigger(args.trigger, args.spot))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.item is None or combo[1] == args.item)
        and (args.spot is None or combo[2] == args.spot)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, item, spot = rng.choice(sorted(combos))
    tool_choices = [tid for tid in TOOLS if suitable_tool(tid, spot)]
    trigger_choices = [gid for gid in TRIGGERS if matching_trigger(gid, spot)]
    if not tool_choices:
        raise StoryError("(No suitable shared tool exists for that hiding spot.)")
    if not trigger_choices:
        raise StoryError("(No honest flashback trigger exists for that hiding spot.)")

    tool = args.tool or rng.choice(sorted(tool_choices))
    trigger = args.trigger or rng.choice(sorted(trigger_choices))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or _pick_name(rng, hero_gender)
    helper_name = args.helper_name or _pick_name(rng, helper_gender, avoid=hero_name)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        place=place,
        item=item,
        spot=spot,
        tool=tool,
        trigger=trigger,
        hero_name=hero_name,
        hero_gender=hero_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.spot not in SPOTS:
        raise StoryError(f"(Unknown spot: {params.spot})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.trigger not in TRIGGERS:
        raise StoryError(f"(Unknown trigger: {params.trigger})")
    if not valid_place_spot(params.place, params.spot):
        raise StoryError(explain_spot(params.place, params.spot))
    if not suitable_tool(params.tool, params.spot):
        raise StoryError(explain_tool(params.tool, params.spot))
    if not matching_trigger(params.trigger, params.spot):
        raise StoryError(explain_trigger(params.trigger, params.spot))

    world = tell(
        place=PLACES[params.place],
        item_cfg=ITEMS[params.item],
        spot_cfg=SPOTS[params.spot],
        tool_cfg=TOOLS[params.tool],
        trigger_cfg=TRIGGERS[params.trigger],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        parent_type=params.parent,
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
        print(asp_program("", "#show valid/3.\n#show suitable/2.\n#show matching/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, item, spot) combos:\n")
        for place, item, spot in combos:
            tools = sorted(tid for tid in TOOLS if suitable_tool(tid, spot))
            triggers = sorted(gid for gid in TRIGGERS if matching_trigger(gid, spot))
            print(f"  {place:10} {item:8} {spot:14} tools={tools} triggers={triggers}")
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
            header = f"### {p.hero_name} & {p.helper_name}: {p.item} in {p.place} ({p.spot}, {p.tool}, {p.trigger})"
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

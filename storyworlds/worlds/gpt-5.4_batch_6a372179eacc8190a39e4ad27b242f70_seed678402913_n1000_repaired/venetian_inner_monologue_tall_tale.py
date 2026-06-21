#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/venetian_inner_monologue_tall_tale.py
================================================================

A standalone storyworld for a tall-tale-flavored, first-person story about a
child whose little treasure gets stuck in venetian blinds. The world model
tracks height, wobble, bent slats, courage, caution, and relief. Stories are
rendered from simulated state, not from a frozen template.

Premise
-------
A child narrator sees something precious caught high in the venetian blinds and
at first feels grand enough to solve it alone. The room becomes enormous in the
narrator's imagination, and the prose includes inner monologue as the child
thinks through the danger. The turn comes when the slats rattle, the child
reconsiders, and the right tool is used either by the child or with a helper.

Run it
------
    python storyworlds/worlds/gpt-5.4/venetian_inner_monologue_tall_tale.py
    python storyworlds/worlds/gpt-5.4/venetian_inner_monologue_tall_tale.py --item paper_star
    python storyworlds/worlds/gpt-5.4/venetian_inner_monologue_tall_tale.py --tool swivel_chair
    python storyworlds/worlds/gpt-5.4/venetian_inner_monologue_tall_tale.py --all
    python storyworlds/worlds/gpt-5.4/venetian_inner_monologue_tall_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/venetian_inner_monologue_tall_tale.py --trace
    python storyworlds/worlds/gpt-5.4/venetian_inner_monologue_tall_tale.py --verify
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

# Make the shared result containers importable when this script is run directly
# from the repo root or from inside storyworlds/worlds/gpt-5.4/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
CHILD_REACH = 1


@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
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
        female = {"girl", "mother", "aunt", "woman"}
        male = {"boy", "father", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.label or self.type)


@dataclass
class RoomCfg:
    id: str
    label: str
    window_desc: str
    echo_desc: str
    tallness: str
    light_desc: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ItemCfg:
    id: str
    label: str
    phrase: str
    caught_in: str
    height: int
    precious: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ToolCfg:
    id: str
    label: str
    phrase: str
    reach: int
    wobble: int
    sense: int
    method: str
    helper_method: str
    qa_method: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperCfg:
    id: str
    type: str
    label: str
    reach_bonus: int
    calm_line: str
    gift_line: str
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


def _r_wobble(world: World) -> list[str]:
    narrator = world.get("narrator")
    tool = world.get("tool")
    blind = world.get("blind")
    if narrator.meters["climbing"] < THRESHOLD:
        return []
    if tool.meters["wobble"] < THRESHOLD:
        return []
    sig = ("wobble", tool.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    narrator.memes["fear"] += 1
    blind.meters["rattle"] += 1
    return ["__wobble__"]


def _r_rattle_bend(world: World) -> list[str]:
    blind = world.get("blind")
    if blind.meters["rattle"] < THRESHOLD:
        return []
    sig = ("bend", blind.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    blind.meters["bent"] += 1
    narrator = world.get("narrator")
    narrator.memes["caution"] += 1
    return ["__bend__"]


CAUSAL_RULES = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="bend", tag="physical", apply=_r_rattle_bend),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sent = rule.apply(world)
            if sent:
                changed = True
                produced.extend(sent)
    if narrate:
        for s in produced:
            if s == "__wobble__":
                world.say("The world gave one tiny wobble under me, and the bravest part of my chest shrank to button-size.")
            elif s == "__bend__":
                world.say("The venetian slats clicked together with a thin, unhappy sound, and I knew the blind was not a mountain after all. It was just a real thing that could get bent.")
    return produced


def tool_is_sensible(tool: ToolCfg) -> bool:
    return tool.sense >= SENSE_MIN


def can_self_reach(item: ItemCfg, tool: ToolCfg) -> bool:
    return CHILD_REACH + tool.reach >= item.height


def can_helper_reach(item: ItemCfg, tool: ToolCfg, helper: HelperCfg) -> bool:
    return CHILD_REACH + tool.reach + helper.reach_bonus >= item.height


def valid_combo(room: RoomCfg, item: ItemCfg, tool: ToolCfg, helper: HelperCfg) -> bool:
    del room
    return tool_is_sensible(tool) and (can_self_reach(item, tool) or can_helper_reach(item, tool, helper))


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for room_id, room in ROOMS.items():
        for item_id, item in ITEMS.items():
            for tool_id, tool in TOOLS.items():
                for helper_id, helper in HELPERS.items():
                    if valid_combo(room, item, tool, helper):
                        combos.append((room_id, item_id, tool_id, helper_id))
    return combos


def outcome_of(params: "StoryParams") -> str:
    item = ITEMS[params.item]
    tool = TOOLS[params.tool]
    helper = HELPERS[params.helper]
    if can_self_reach(item, tool):
        return "self"
    return "helper"


def predict_risk(world: World, tool: ToolCfg) -> dict:
    sim = world.copy()
    sim.get("tool").meters["wobble"] = float(tool.wobble)
    sim.get("narrator").meters["climbing"] += 1
    propagate(sim, narrate=False)
    return {
        "wobble": sim.get("tool").meters["wobble"],
        "rattle": sim.get("blind").meters["rattle"],
        "bent": sim.get("blind").meters["bent"],
        "fear": sim.get("narrator").memes["fear"],
    }


def introduce(world: World, narrator: Entity, room: RoomCfg, item: ItemCfg) -> None:
    narrator.memes["wonder"] += 1
    world.say(
        f"My name was {narrator.id}, and that afternoon {room.label} felt as wide as three counties and twice as sunny. "
        f"{room.light_desc} The window wore a neat set of venetian blinds, and up in {item.caught_in} hung {item.phrase}."
    )
    world.say(
        f"To anybody else it might have looked small, but to me {item.precious}. "
        f"{room.echo_desc}"
    )


def boast(world: World, narrator: Entity, item: ItemCfg, room: RoomCfg) -> None:
    narrator.memes["bravado"] += 1
    world.say(
        f'I drew in a breath and thought, "I could fetch that {item.label} if it were hanging from the moon. '
        f'In a room this {room.tallness}, a person has to think giant thoughts."'
    )


def spot_tool(world: World, narrator: Entity, tool: ToolCfg) -> None:
    world.say(
        f"Near the wall stood {tool.phrase}. It looked ordinary enough, but in my head it grew into a hero's ladder."
    )
    world.say(
        f'I told myself, "If I use {tool.label}, this rescue will be quicker than a hiccup and grander than a parade."'
    )


def climb_and_reconsider(world: World, narrator: Entity, tool: ToolCfg) -> None:
    narrator.meters["climbing"] += 1
    world.get("tool").meters["wobble"] = float(tool.wobble)
    propagate(world, narrate=True)
    if tool.wobble >= THRESHOLD:
        narrator.memes["caution"] += 1
        world.say(
            f'I thought, "Maybe a real giant would keep going. But I am only me, and {tool.label} is talking back with its knees."'
        )
    else:
        narrator.memes["steady"] += 1
        world.say(
            f'I set my feet carefully and thought, "Slow is stronger than showing off."'
        )


def ask_for_help(world: World, narrator: Entity, helper: Entity, helper_cfg: HelperCfg, item: ItemCfg, tool: ToolCfg) -> None:
    narrator.memes["trust"] += 1
    narrator.memes["fear"] = 0.0
    world.say(
        f'So I stepped down and called for my {helper.label_word}. "{helper.label_word.capitalize()}, will you help me get my {item.label} from the venetian blinds?"'
    )
    world.say(
        f"{helper.label_word.capitalize()} came in at once. {helper_cfg.calm_line}"
    )
    world.say(
        f"I pointed up. {helper.pronoun().capitalize()} took {tool.phrase} and {tool.helper_method}."
    )


def self_rescue(world: World, narrator: Entity, item: ItemCfg, tool: ToolCfg) -> None:
    narrator.memes["pride"] += 1
    world.say(
        f"I breathed once, then once again, and {tool.method}. "
        f"{item.phrase.capitalize()} slipped free as neatly as a fish from a net."
    )


def helper_rescue(world: World, narrator: Entity, helper: Entity, item: ItemCfg, tool: ToolCfg, helper_cfg: HelperCfg) -> None:
    helper.memes["care"] += 1
    narrator.memes["relief"] += 1
    world.say(
        f"{helper.pronoun().capitalize()} moved slowly, not like a giant in a hurry but like somebody who knew how to keep small things safe. "
        f"In one easy reach, {item.phrase} came free."
    )
    world.say(
        f'I thought, "Well now. Maybe the biggest people in the world are the ones who do not have to brag before they help."'
    )
    world.say(helper_cfg.gift_line)


def settle(world: World, narrator: Entity, blind: Entity, item: Entity, item_cfg: ItemCfg) -> None:
    item.meters["rescued"] += 1
    narrator.memes["relief"] += 1
    narrator.memes["lesson"] += 1
    if blind.meters["bent"] >= THRESHOLD:
        world.say(
            "The blind was straightened gently, slat by slat, until the window looked peaceful again."
        )
    world.say(
        f"I held {item_cfg.phrase} against my shirt and felt my thoughts quit stomping around. "
        f"{item_cfg.ending_image}"
    )


def tell(
    room: RoomCfg,
    item_cfg: ItemCfg,
    tool_cfg: ToolCfg,
    helper_cfg: HelperCfg,
    narrator_name: str = "Mabel",
    narrator_type: str = "girl",
) -> World:
    world = World()
    narrator = world.add(Entity(id="narrator", kind="character", type=narrator_type, label=narrator_name, role="narrator"))
    helper = world.add(Entity(id="helper", kind="character", type=helper_cfg.type, label=helper_cfg.label, role="helper"))
    item = world.add(Entity(id="item", kind="thing", type="keepsake", label=item_cfg.label, phrase=item_cfg.phrase))
    blind = world.add(Entity(id="blind", kind="thing", type="blind", label="venetian blinds", phrase="the venetian blinds"))
    tool = world.add(Entity(id="tool", kind="thing", type="tool", label=tool_cfg.label, phrase=tool_cfg.phrase))
    room_ent = world.add(Entity(id="room", kind="thing", type="room", label=room.label, phrase=room.label))

    room_ent.meters["height"] = float(item_cfg.height)
    blind.meters["height"] = float(item_cfg.height)
    world.facts["room_cfg"] = room
    world.facts["item_cfg"] = item_cfg
    world.facts["tool_cfg"] = tool_cfg
    world.facts["helper_cfg"] = helper_cfg

    introduce(world, narrator, room, item_cfg)
    boast(world, narrator, item_cfg, room)

    world.para()
    spot_tool(world, narrator, tool_cfg)
    risk = predict_risk(world, tool_cfg)
    world.facts["predicted_rattle"] = risk["rattle"]
    world.facts["predicted_bent"] = risk["bent"]
    climb_and_reconsider(world, narrator, tool_cfg)

    world.para()
    outcome = "self" if can_self_reach(item_cfg, tool_cfg) else "helper"
    if outcome == "self":
        self_rescue(world, narrator, item_cfg, tool_cfg)
    else:
        ask_for_help(world, narrator, helper, helper_cfg, item_cfg, tool_cfg)
        helper_rescue(world, narrator, helper, item_cfg, tool_cfg, helper_cfg)
    settle(world, narrator, blind, item, item_cfg)

    world.facts.update(
        narrator=narrator,
        helper=helper,
        blind=blind,
        item=item,
        tool=tool,
        room=room_ent,
        outcome=outcome,
        bent=blind.meters["bent"] >= THRESHOLD,
        rescued=item.meters["rescued"] >= THRESHOLD,
    )
    return world


ROOMS = {
    "parlor": RoomCfg(
        id="parlor",
        label="the parlor",
        window_desc="a tall window",
        echo_desc="Every little sound in there seemed to roll around like thunder looking for a hill.",
        tallness="long-legged and sky-high",
        light_desc="Sunbeams lay across the rug in bright railroad tracks.",
        tags={"window", "sunlight"},
    ),
    "kitchen": RoomCfg(
        id="kitchen",
        label="the kitchen",
        window_desc="the big breakfast window",
        echo_desc="The spoons in the drawer gave tiny silver shivers whenever the room went still.",
        tallness="high as a grain silo in my imagination",
        light_desc="Warm light slid across the table and made the jam jar wink.",
        tags={"window", "home"},
    ),
    "sunroom": RoomCfg(
        id="sunroom",
        label="the sunroom",
        window_desc="a whole wall of windows",
        echo_desc="Even the potted fern seemed to be listening.",
        tallness="stretched and shining like a glass canyon",
        light_desc="The whole room glowed so bright it felt as if morning had decided to stay all day.",
        tags={"window", "sunlight"},
    ),
}

ITEMS = {
    "paper_star": ItemCfg(
        id="paper_star",
        label="paper star",
        phrase="my gold paper star",
        caught_in="the top slats",
        height=2,
        precious="it was the very star I had cut out after promising I could make my own little sky",
        ending_image="The gold points shone beside the window, no longer trapped, and the whole room seemed to breathe easy with me.",
        tags={"craft", "star"},
    ),
    "blue_ribbon": ItemCfg(
        id="blue_ribbon",
        label="blue ribbon",
        phrase="my blue ribbon",
        caught_in="a high crooked slat",
        height=2,
        precious="I had won it at the fair for carrying a pie without dropping so much as one crumb",
        ending_image="The ribbon lay smooth in my hand like a strip of sky, and even the venetian blinds looked pleased to let it go.",
        tags={"ribbon", "fair"},
    ),
    "sparrow_note": ItemCfg(
        id="sparrow_note",
        label="sparrow note",
        phrase="my tiny sparrow note",
        caught_in="the very highest slats",
        height=3,
        precious="I had folded it into a bird shape and written a brave secret inside",
        ending_image="The little paper bird rested safely in my palm, and the bright window no longer looked like a place for losing things.",
        tags={"paper", "note"},
    ),
}

TOOLS = {
    "step_stool": ToolCfg(
        id="step_stool",
        label="the step stool",
        phrase="a sturdy little step stool",
        reach=1,
        wobble=0,
        sense=3,
        method="I climbed onto the step stool, stretched with two careful fingers, and pinched the string free",
        helper_method="stood on the step stool and lifted the caught edge loose with two calm fingers",
        qa_method="used a steady step stool and reached carefully",
        tags={"step_stool", "safe"},
    ),
    "grabber": ToolCfg(
        id="grabber",
        label="the grabber",
        phrase="the long grabber from the hall closet",
        reach=2,
        wobble=0,
        sense=3,
        method="I raised the grabber like a crane, squeezed gently, and drew the caught bit down",
        helper_method="used the long grabber to pinch the trapped part and guide it down",
        qa_method="used a long grabber instead of climbing higher",
        tags={"grabber", "safe"},
    ),
    "wooden_chair": ToolCfg(
        id="wooden_chair",
        label="the wooden chair",
        phrase="a wooden chair with a straight back",
        reach=1,
        wobble=1,
        sense=2,
        method="I climbed onto the chair, kept one hand on the window frame, and eased the caught corner loose",
        helper_method="held the chair steady, stepped up, and freed the caught corner",
        qa_method="used a plain chair very carefully",
        tags={"chair", "careful"},
    ),
    "swivel_chair": ToolCfg(
        id="swivel_chair",
        label="the swivel chair",
        phrase="the rolling swivel chair",
        reach=1,
        wobble=2,
        sense=1,
        method="I tried to stand on the chair and grab upward",
        helper_method="tried to use the rolling chair anyway",
        qa_method="tried a rolling chair",
        tags={"chair", "unsafe"},
    ),
    "tower_of_books": ToolCfg(
        id="tower_of_books",
        label="the tower of books",
        phrase="a tower of books with a saucy lean to it",
        reach=2,
        wobble=3,
        sense=1,
        method="I tried to balance on the books and snatch the prize",
        helper_method="stacked books and reached up",
        qa_method="stacked wobbly books",
        tags={"books", "unsafe"},
    ),
}

HELPERS = {
    "mother": HelperCfg(
        id="mother",
        type="mother",
        label="the parent",
        reach_bonus=1,
        calm_line='"Let us do this without turning the window into a wrestling match," she said.',
        gift_line='Then she smiled and said, "Next time, brave heart, we ask for steady help before the venetian blinds have to sing about it."',
        tags={"call_adult", "mother"},
    ),
    "father": HelperCfg(
        id="father",
        type="father",
        label="the parent",
        reach_bonus=1,
        calm_line='"A slow hand beats a wild hand every time," he said.',
        gift_line='Then he grinned and said, "That is how you rescue things without making a legend out of a mess."',
        tags={"call_adult", "father"},
    ),
    "aunt": HelperCfg(
        id="aunt",
        type="aunt",
        label="the helper",
        reach_bonus=1,
        calm_line='"Windows like patience better than wrestling," she said.',
        gift_line='Then she winked and said, "A fine tall tale is nice, but a straight blind is nicer."',
        tags={"call_adult", "aunt"},
    ),
}

GIRL_NAMES = ["Mabel", "Ada", "Nora", "Elsie", "Lula", "Ruby", "Clara", "June"]
BOY_NAMES = ["Eli", "Jasper", "Theo", "Cal", "Milo", "Otis", "Benji", "Roy"]


@dataclass
class StoryParams:
    room: str
    item: str
    tool: str
    helper: str
    narrator_name: str
    narrator_type: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "venetian": [
        (
            "What are venetian blinds?",
            "Venetian blinds are window covers made from many thin slats. You can tilt the slats to let light in or keep it out."
        )
    ],
    "step_stool": [
        (
            "What is a step stool for?",
            "A step stool is a small steady platform that helps you reach something a little higher. It is safer than climbing on wobbly things."
        )
    ],
    "grabber": [
        (
            "What is a grabber tool?",
            "A grabber is a long tool that can pinch and hold something far away. It helps you reach without climbing too high."
        )
    ],
    "chair": [
        (
            "Why can a rolling chair be dangerous to stand on?",
            "A rolling chair can slide or spin when you put weight on it. That makes it easy to lose your balance."
        )
    ],
    "call_adult": [
        (
            "When should a child ask a grown-up for help reaching something high?",
            "A child should ask for help when the thing is too high or the way up looks wobbly. A grown-up can use a steadier method and keep the child safe."
        )
    ],
    "paper": [
        (
            "Why can paper tear when it gets caught?",
            "Paper is light and thin, so a hard tug can crease it or rip it. Gentle hands work better."
        )
    ],
    "window": [
        (
            "Why should you be careful around window blinds?",
            "Blinds have thin slats that can bend if they are yanked or pushed too hard. Using gentle hands keeps them working."
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    item = f["item_cfg"]
    room = f["room_cfg"]
    outcome = f["outcome"]
    narrator = f["narrator"]
    helper = f["helper"]
    if outcome == "self":
        return [
            f'Write a tall-tale style story with inner monologue that includes the word "venetian".',
            f"Tell a first-person story where {narrator.label} thinks {room.label} is enormous, talks grandly inside {narrator.pronoun('possessive')} own head, and carefully rescues {item.phrase} from venetian blinds.",
            f"Write a child-facing story in which bragging shrinks into careful thinking, and the ending image shows the room peaceful again."
        ]
    return [
        f'Write a tall-tale style story with inner monologue that includes the word "venetian".',
        f"Tell a first-person story where {narrator.label} wants to rescue {item.phrase} from the venetian blinds alone, then calls {helper.label_word} when the window begins to rattle.",
        f"Write a story where the narrator's thoughts start huge and boastful, but the calm ending proves that steady help was stronger than showing off."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    narrator = f["narrator"]
    helper = f["helper"]
    item = f["item_cfg"]
    tool = f["tool_cfg"]
    room = f["room_cfg"]
    outcome = f["outcome"]
    helper_word = helper.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is telling the story?",
            f"The child narrator, {narrator.label}, tells the story in first person. That is why we hear the adventure as thoughts inside {narrator.pronoun('possessive')} own head."
        ),
        (
            f"What was stuck in the venetian blinds?",
            f"{item.phrase.capitalize()} was caught high in the venetian blinds. It mattered a lot to {narrator.label}, so the window problem felt enormous."
        ),
        (
            f"Why did the room feel so big to {narrator.label}?",
            f"The story is told like a tall tale, so {room.label} grows huge in the child's imagination. We can hear that in the inner monologue, where an ordinary rescue starts to sound as grand as climbing a mountain."
        ),
        (
            f"What made {narrator.label} slow down?",
            f"The tool began to wobble or the blinds rattled, and that broke the spell of showing off. In that moment, {narrator.label} understood that the venetian blinds were real and could be bent."
        ),
    ]
    if outcome == "self":
        qa.append(
            (
                f"How did {narrator.label} get the {item.label} down?",
                f"{narrator.label} {tool.qa_method} and moved slowly instead of bragging. That careful method was enough to reach the stuck thing without hurting the blinds."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended quietly and safely, with {item.phrase} back in {narrator.label}'s hands. The final image of the calm window shows that careful thinking changed the whole adventure."
            )
        )
    else:
        qa.append(
            (
                f"Why did {narrator.label} call {helper_word}?",
                f"{narrator.label} realized the job was too high or too shaky to handle alone. Calling {helper_word} was the turning point, because it traded bragging for a steady rescue."
            )
        )
        qa.append(
            (
                f"How did {helper_word} help?",
                f"{helper_word.capitalize()} used {tool.phrase} in a calm, controlled way and freed the trapped {item.label}. The help mattered because the grown-up kept the blinds safe while solving the problem."
            )
        )
        qa.append(
            (
                "What changed by the ending?",
                f"At first the child wanted to be giant all alone, but by the end steady help felt stronger than showing off. The calm window and the rescued keepsake prove the lesson."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"venetian", "window"}
    tags |= set(f["tool_cfg"].tags)
    tags |= set(f["helper_cfg"].tags)
    tags |= set(f["item_cfg"].tags)
    out: list[tuple[str, str]] = []
    order = ["venetian", "window", "step_stool", "grabber", "chair", "call_adult", "paper"]
    for tag in order:
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        room="parlor",
        item="paper_star",
        tool="step_stool",
        helper="mother",
        narrator_name="Mabel",
        narrator_type="girl",
    ),
    StoryParams(
        room="kitchen",
        item="blue_ribbon",
        tool="wooden_chair",
        helper="father",
        narrator_name="Jasper",
        narrator_type="boy",
    ),
    StoryParams(
        room="sunroom",
        item="sparrow_note",
        tool="grabber",
        helper="aunt",
        narrator_name="Ruby",
        narrator_type="girl",
    ),
]


def explain_tool(tool_id: str) -> str:
    tool = TOOLS[tool_id]
    return (
        f"(No story: {tool.label} is too wobbly for a child-facing rescue tale "
        f"(sense={tool.sense} < {SENSE_MIN}). Choose a steadier tool like "
        f"{', '.join(t.id for t in TOOLS.values() if t.sense >= SENSE_MIN)}.)"
    )


def explain_reach(item: ItemCfg, tool: ToolCfg, helper: HelperCfg) -> str:
    return (
        f"(No story: {item.phrase} is too high for {tool.label}, even with help from "
        f"{helper.label}. Pick a longer-reaching tool or a lower item.)"
    )


ASP_RULES = r"""
sensible(Tool) :- tool(Tool), sense(Tool, S), sense_min(M), S >= M.
reachable_self(Item, Tool) :- item(Item), tool(Tool), item_height(Item, H), child_reach(C), reach(Tool, R), C + R >= H.
reachable_help(Item, Tool, Helper) :- item(Item), tool(Tool), helper(Helper),
                                      item_height(Item, H), child_reach(C), reach(Tool, R), bonus(Helper, B), C + R + B >= H.
valid(Room, Item, Tool, Helper) :- room(Room), item(Item), tool(Tool), helper(Helper),
                                   sensible(Tool),
                                   reachable_self(Item, Tool).
valid(Room, Item, Tool, Helper) :- room(Room), item(Item), tool(Tool), helper(Helper),
                                   sensible(Tool),
                                   reachable_help(Item, Tool, Helper).

outcome(self) :- chosen_item(I), chosen_tool(T), reachable_self(I, T).
outcome(helper) :- chosen_item(I), chosen_tool(T), chosen_helper(H),
                   not reachable_self(I, T), reachable_help(I, T, H).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("child_reach", CHILD_REACH))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    for room_id in ROOMS:
        lines.append(asp.fact("room", room_id))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        lines.append(asp.fact("item_height", item_id, item.height))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("reach", tool_id, tool.reach))
        lines.append(asp.fact("sense", tool_id, tool.sense))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("bonus", helper_id, helper.reach_bonus))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_item", params.item),
        asp.fact("chosen_tool", params.tool),
        asp.fact("chosen_helper", params.helper),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale storyworld with inner monologue: a child, venetian blinds, and a high little treasure."
    )
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.tool and not tool_is_sensible(TOOLS[args.tool]):
        raise StoryError(explain_tool(args.tool))
    if args.item and args.tool and args.helper:
        if not valid_combo(ROOMS[args.room] if args.room else next(iter(ROOMS.values())), ITEMS[args.item], TOOLS[args.tool], HELPERS[args.helper]):
            raise StoryError(explain_reach(ITEMS[args.item], TOOLS[args.tool], HELPERS[args.helper]))

    combos = [
        c for c in valid_combos()
        if (args.room is None or c[0] == args.room)
        and (args.item is None or c[1] == args.item)
        and (args.tool is None or c[2] == args.tool)
        and (args.helper is None or c[3] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    room_id, item_id, tool_id, helper_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(
        room=room_id,
        item=item_id,
        tool=tool_id,
        helper=helper_id,
        narrator_name=name,
        narrator_type=gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.room not in ROOMS:
        raise StoryError(f"(Unknown room '{params.room}'.)")
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item '{params.item}'.)")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool '{params.tool}'.)")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper '{params.helper}'.)")
    room = ROOMS[params.room]
    item = ITEMS[params.item]
    tool = TOOLS[params.tool]
    helper = HELPERS[params.helper]
    if not tool_is_sensible(tool):
        raise StoryError(explain_tool(params.tool))
    if not valid_combo(room, item, tool, helper):
        raise StoryError(explain_reach(item, tool, helper))

    world = tell(
        room=room,
        item_cfg=item,
        tool_cfg=tool,
        helper_cfg=helper,
        narrator_name=params.narrator_name,
        narrator_type=params.narrator_type,
    )
    world.get("narrator").label = params.narrator_name
    return StorySample(
        params=params,
        story=world.render().replace("My name was narrator", f"My name was {params.narrator_name}"),
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
    for seed in range(30):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = 0
    for params in cases:
        py = outcome_of(params)
        asp = asp_outcome(params)
        if py != asp:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke generate/emit passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (room, item, tool, helper) combos:\n")
        for room_id, item_id, tool_id, helper_id in combos:
            print(f"  {room_id:8} {item_id:12} {tool_id:13} {helper_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.narrator_name}: {p.item} in {p.room} ({p.tool}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

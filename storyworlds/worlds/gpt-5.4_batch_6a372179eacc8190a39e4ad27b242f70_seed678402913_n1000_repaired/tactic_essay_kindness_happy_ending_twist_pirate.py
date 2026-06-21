#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/tactic_essay_kindness_happy_ending_twist_pirate.py
================================================================================

A standalone storyworld about two children playing pirates who think they are
hunting treasure, but discover that the true "treasure" is helping someone in
need and then writing a kindness essay about it.

Seed requirements carried into the world model
----------------------------------------------
- includes the words "tactic" and "essay"
- features Kindness, Happy Ending, Twist
- style close to a Pirate Tale

World premise
-------------
Two children build a pirate game near the harbor. A bottle map seems to promise
treasure. They follow it with pirate excitement, but the map's X leads not to a
chest of gold. The twist is that someone nearby needs help: a stuck boat, a
spilled basket, or a snapped dock line. The children must choose a sensible
kindness tactic and the right helper tool. If the tactic truly fits the need,
they solve the problem, learn that kindness can be the best treasure, and later
write a school essay about it. Unreasonable pairings are refused.

Run it
------
python storyworlds/worlds/gpt-5.4/tactic_essay_kindness_happy_ending_twist_pirate.py
python storyworlds/worlds/gpt-5.4/tactic_essay_kindness_happy_ending_twist_pirate.py --need beached_boat --tactic teamwork
python storyworlds/worlds/gpt-5.4/tactic_essay_kindness_happy_ending_twist_pirate.py --need beached_boat --tool basket
python storyworlds/worlds/gpt-5.4/tactic_essay_kindness_happy_ending_twist_pirate.py --all --qa
python storyworlds/worlds/gpt-5.4/tactic_essay_kindness_happy_ending_twist_pirate.py --verify
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

# Make the shared result containers importable when this script is run directly.
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    movable: bool = False
    heavy: bool = False
    tied: bool = False
    carrying: bool = False
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

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class HarborTheme:
    id: str
    scene: str
    rig: str
    title_a: str
    title_b: str
    goal: str
    sendoff: str


@dataclass
class Need:
    id: str
    label: str
    phrase: str
    owner_label: str
    owner_type: str
    place_detail: str
    problem_line: str
    ask_line: str
    solved_line: str
    essay_lesson: str
    obstacle: str
    tags: set[str] = field(default_factory=set)
    required_tactics: set[str] = field(default_factory=set)
    required_tools: set[str] = field(default_factory=set)
    difficulty: int = 1


@dataclass
class Tactic:
    id: str
    label: str
    text: str
    qa_text: str
    sense: int
    tags: set[str] = field(default_factory=set)
    strengths: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    plural: bool = False
    tags: set[str] = field(default_factory=set)
    helps_with: set[str] = field(default_factory=set)


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


def _r_notice_need(world: World) -> list[str]:
    out: list[str] = []
    need = world.get("need")
    if need.meters["trouble"] < THRESHOLD:
        return out
    sig = ("notice", "need")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for eid in ("a", "b"):
        if eid in world.entities:
            world.get(eid).memes["concern"] += 1
    out.append("__noticed__")
    return out


def _r_help_success(world: World) -> list[str]:
    out: list[str] = []
    need = world.get("need")
    if need.meters["aid"] < THRESHOLD:
        return out
    if need.meters["trouble"] < THRESHOLD:
        return out
    sig = ("resolve", "need")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    need.meters["trouble"] = 0.0
    need.meters["solved"] += 1
    for eid in ("a", "b"):
        if eid in world.entities:
            kid = world.get(eid)
            kid.memes["joy"] += 1
            kid.memes["pride"] += 1
            kid.memes["kindness"] += 1
    owner = world.get("owner")
    owner.memes["gratitude"] += 1
    out.append("__solved__")
    return out


CAUSAL_RULES = [
    Rule(name="notice_need", tag="social", apply=_r_notice_need),
    Rule(name="help_success", tag="social", apply=_r_help_success),
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


THEMES = {
    "harbor_pirates": HarborTheme(
        id="harbor_pirates",
        scene="a bright little harbor kingdom",
        rig="The bench was their pirate ship, a striped towel was their sail, and a bottle map showed where the day's secret treasure waited.",
        title_a="Captain",
        title_b="Scout",
        goal="the hidden X by the shore",
        sendoff="went skipping home with a story worth telling",
    ),
    "cove_pirates": HarborTheme(
        id="cove_pirates",
        scene="a windy cove full of pretend waves",
        rig="A driftwood log was their pirate ship, a blue scarf was their flag, and a bottle map promised a secret prize beyond the rocks.",
        title_a="Captain",
        title_b="Matey",
        goal="the marked place in the cove",
        sendoff="trotted home feeling richer than any captain with coins",
    ),
}

NEEDS = {
    "beached_boat": Need(
        id="beached_boat",
        label="beached boat",
        phrase="a little fishing boat stuck high on the sand",
        owner_label="old sailor",
        owner_type="man",
        place_detail="beside a curl of foamy water",
        problem_line='An old sailor stood there, tugging at a little fishing boat stuck high on the sand.',
        ask_line='"Oh dear," the sailor said. "The tide slipped away before I could push my boat back in."',
        solved_line="Together they shoved and heaved until the little boat slid free and kissed the water again.",
        essay_lesson="that the best treasure could be helping somebody get back on the water",
        obstacle="the boat was too stuck for one tired person alone",
        tags={"boat", "harbor", "kindness"},
        required_tactics={"teamwork"},
        required_tools={"rope"},
        difficulty=2,
    ),
    "spilled_oranges": Need(
        id="spilled_oranges",
        label="spilled oranges",
        phrase="a market basket tipped over with oranges rolling everywhere",
        owner_label="fruit seller",
        owner_type="woman",
        place_detail="near the quay steps",
        problem_line='A fruit seller knelt there with a basket on its side and oranges bumping away in every direction.',
        ask_line='"My basket strap snapped," she said. "I cannot catch them all before they roll into the water."',
        solved_line="The children hurried this way and that until every orange was safe in the basket again.",
        essay_lesson="that quick kind hands can save a stranger's hard work",
        obstacle="the rolling fruit needed calm, quick collecting",
        tags={"market", "fruit", "kindness"},
        required_tactics={"quick_sorting"},
        required_tools={"basket"},
        difficulty=1,
    ),
    "loose_mooring": Need(
        id="loose_mooring",
        label="loose mooring line",
        phrase="a small boat bumping against the dock because its mooring line had come loose",
        owner_label="dock keeper",
        owner_type="man",
        place_detail="by the wooden posts at the dock",
        problem_line='The dock keeper was reaching for a loose line while a small boat bumped sadly against the dock.',
        ask_line='"If that line slips farther, the boat may drift away," he said.',
        solved_line="The rope went snug, the boat stopped bumping, and the dock keeper let out a long relieved breath.",
        essay_lesson="that noticing trouble quickly and tying it safe can keep bigger trouble away",
        obstacle="the line had to be reached and looped back safely",
        tags={"dock", "rope", "kindness"},
        required_tactics={"careful_knot"},
        required_tools={"rope"},
        difficulty=1,
    ),
}

TACTICS = {
    "teamwork": Tactic(
        id="teamwork",
        label="teamwork",
        text="used a kindness tactic: they counted together, leaned together, and pulled together instead of each trying alone",
        qa_text="They used teamwork, moving at the same time so the hard job became possible.",
        sense=3,
        tags={"teamwork", "kindness"},
        strengths={"push", "steady"},
    ),
    "quick_sorting": Tactic(
        id="quick_sorting",
        label="quick sorting",
        text="used a kindness tactic: one child blocked the rolling fruit while the other scooped it up fast",
        qa_text="They split the job into two quick parts, which stopped the oranges from rolling farther away.",
        sense=3,
        tags={"sorting", "kindness"},
        strengths={"collect", "fast"},
    ),
    "careful_knot": Tactic(
        id="careful_knot",
        label="careful knot",
        text="used a kindness tactic: first they steadied the line, then they looped it back with slow careful fingers",
        qa_text="They worked carefully instead of rushing, because a neat knot was the safe way to stop the boat from drifting.",
        sense=3,
        tags={"rope", "kindness"},
        strengths={"tie", "steady"},
    ),
    "shout_orders": Tactic(
        id="shout_orders",
        label="shout orders",
        text="started barking pirate orders at the trouble as if loud voices alone could fix it",
        qa_text="They only shouted commands, which did not really help.",
        sense=1,
        tags={"bad_idea"},
        strengths={"noise"},
    ),
}

TOOLS = {
    "rope": Tool(
        id="rope",
        label="rope",
        phrase="a coil of rope from their pirate play",
        plural=False,
        tags={"rope"},
        helps_with={"beached_boat", "loose_mooring"},
    ),
    "basket": Tool(
        id="basket",
        label="basket",
        phrase="their spare treasure basket",
        plural=False,
        tags={"basket"},
        helps_with={"spilled_oranges"},
    ),
    "chalk": Tool(
        id="chalk",
        label="chalk",
        phrase="a stub of blue chalk for drawing maps",
        plural=False,
        tags={"chalk"},
        helps_with=set(),
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Theo"]
TRAITS = ["careful", "cheerful", "thoughtful", "brave", "kind", "curious"]


def sensible_tactics() -> list[Tactic]:
    return [t for t in TACTICS.values() if t.sense >= SENSE_MIN]


def need_matches(need: Need, tactic: Tactic, tool: Tool) -> bool:
    return tactic.id in need.required_tactics and tool.id in need.required_tools


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for theme_id in THEMES:
        for need_id, need in NEEDS.items():
            for tactic_id, tactic in TACTICS.items():
                for tool_id, tool in TOOLS.items():
                    if tactic.sense >= SENSE_MIN and need_matches(need, tactic, tool):
                        combos.append((theme_id, need_id, tactic_id, tool_id))
    return combos


def predict_success(world: World, need_id: str, tactic_id: str, tool_id: str) -> bool:
    sim = world.copy()
    need = sim.get("need")
    if need_matches(NEEDS[need_id], TACTICS[tactic_id], TOOLS[tool_id]):
        need.meters["aid"] += 1
    propagate(sim, narrate=False)
    return sim.get("need").meters["solved"] >= THRESHOLD


def play_setup(world: World, a: Entity, b: Entity, theme: HarborTheme) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"On a sunny afternoon, {a.id} and {b.id} turned the harbor path into {theme.scene}. {theme.rig}"
    )
    world.say(
        f'"{theme.title_a} {a.id} and {theme.title_b} {b.id}!" {a.id} cried. "Today we sail to {theme.goal}!"'
    )


def mention_essay(world: World, a: Entity, b: Entity) -> None:
    world.say(
        f"In {b.id}'s pocket was a folded school paper for tomorrow's kindness essay."
    )
    world.say(
        f'"Maybe our pirate hunt can give us something wonderful to write about," {b.id} said.'
    )


def find_map(world: World) -> None:
    world.say(
        "The bottle map showed a fat red X and a curling note that said, "
        '"True treasure waits where help is needed most."'
    )


def follow_map(world: World, need: Need) -> None:
    world.say(
        f"They followed the map along the shore until they reached {need.place_detail}."
    )


def reveal_twist(world: World, need: Need) -> None:
    need_ent = world.get("need")
    need_ent.meters["trouble"] += 1
    propagate(world, narrate=False)
    world.say("The children expected a chest full of gold.")
    world.say(f"Instead, they found {need.phrase}.")
    world.say(need.problem_line)
    world.say(need.ask_line)


def decide_to_help(world: World, a: Entity, b: Entity, need: Need, owner: Entity) -> None:
    a.memes["kindness"] += 1
    b.memes["kindness"] += 1
    world.say(
        f'{b.id} looked at the trouble, then at the map. "That was the twist," {b.id} whispered. "The X was not for coins at all."'
    )
    world.say(
        f'"It is for helping," {a.id} said. "Come on. Let\'s be the kind sort of pirates."'
    )
    owner.memes["hope"] += 1


def use_tactic(world: World, tactic: Tactic, tool: Tool, need: Need) -> None:
    world.say(
        f"They grabbed {tool.phrase} and {tactic.text}."
    )
    if need_matches(need, tactic, tool):
        world.get("need").meters["aid"] += 1
        propagate(world, narrate=False)
        world.say(need.solved_line)
    else:
        world.say(
            "But the plan did not fit the trouble, and the mess stayed just as stuck as before."
        )


def thanks_and_treasure(world: World, owner: Entity, need: Need) -> None:
    owner_phrase = owner.label if owner.label else need.owner_label
    world.say(
        f'"Thank you, little pirates," the {owner_phrase} said with a warm smile.'
    )
    world.say(
        'Then the grown-up pressed two bright chocolate coins into their hands. "Here is a tiny captain\'s prize."'
    )
    world.say(
        "The children laughed, but by then they already knew the sweeter part was the helping."
    )


def essay_ending(world: World, a: Entity, b: Entity, need: Need) -> None:
    world.say(
        f"That evening they sat at the kitchen table, still sandy and smiling, and began the kindness essay together."
    )
    world.say(
        f'{a.id} wrote the word "tactic" very carefully and said, "Our best pirate tactic was helping first."'
    )
    world.say(
        f"{b.id} wrote that they had learned {need.essay_lesson}."
    )
    world.say(
        f"When the moon shone in the window, the two young pirates grinned at their page and {world.facts['theme'].sendoff}."
    )


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
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


@dataclass
class StoryParams:
    theme: str
    need: str
    tactic: str
    tool: str
    child_a: str
    gender_a: str
    child_b: str
    gender_b: str
    parent: str
    trait_a: str
    trait_b: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        theme="harbor_pirates",
        need="beached_boat",
        tactic="teamwork",
        tool="rope",
        child_a="Tom",
        gender_a="boy",
        child_b="Lily",
        gender_b="girl",
        parent="mother",
        trait_a="brave",
        trait_b="thoughtful",
    ),
    StoryParams(
        theme="harbor_pirates",
        need="spilled_oranges",
        tactic="quick_sorting",
        tool="basket",
        child_a="Mia",
        gender_a="girl",
        child_b="Ben",
        gender_b="boy",
        parent="father",
        trait_a="cheerful",
        trait_b="kind",
    ),
    StoryParams(
        theme="cove_pirates",
        need="loose_mooring",
        tactic="careful_knot",
        tool="rope",
        child_a="Sam",
        gender_a="boy",
        child_b="Zoe",
        gender_b="girl",
        parent="mother",
        trait_a="curious",
        trait_b="careful",
    ),
]


KNOWLEDGE = {
    "pirates": [(
        "What is a pirate in a pretend game?",
        "In a pretend game, a pirate is make-believe sailor adventurer. Children can play pirates with maps and boats without doing anything mean."
    )],
    "kindness": [(
        "What is kindness?",
        "Kindness is choosing to help, comfort, or care for someone. Small kind actions can change another person's whole day."
    )],
    "essay": [(
        "What is an essay?",
        "An essay is a piece of writing where you explain an idea or tell about something. A school essay can share what you learned."
    )],
    "tactic": [(
        "What is a tactic?",
        "A tactic is a careful way to do something. It is like a plan for one part of a job."
    )],
    "rope": [(
        "What can rope be used for?",
        "Rope can pull, tie, or hold things in place. People must use it carefully so it helps instead of tangling."
    )],
    "boat": [(
        "Why can a boat get stuck or drift away?",
        "A boat can get stuck when the water goes out and leaves it on sand. A boat can drift away if its line comes loose."
    )],
    "market": [(
        "Why do rolling fruits need quick help?",
        "Round fruits can roll far and fast. Picking them up quickly stops them from getting lost or squished."
    )],
}
KNOWLEDGE_ORDER = ["pirates", "kindness", "essay", "tactic", "rope", "boat", "market"]


def pair_noun(a: Entity, b: Entity) -> str:
    if a.type == "boy" and b.type == "boy":
        return "two young friends"
    if a.type == "girl" and b.type == "girl":
        return "two young friends"
    return "two young pirate friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["a"]
    b = f["b"]
    need = f["need_cfg"]
    tactic = f["tactic_cfg"]
    return [
        'Write a pirate-style story for a 3-to-5-year-old that includes the words "tactic" and "essay" and has a kindness twist.',
        f"Tell a gentle harbor pirate tale where {a.id} and {b.id} hunt treasure, but the twist is that the X leads to someone who needs help with {need.label}.",
        f"Write a happy story where children use {tactic.label} as a kindness tactic, then write an essay about what real treasure means.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["a"]
    b = f["b"]
    need = f["need_cfg"]
    tool = f["tool_cfg"]
    tactic = f["tactic_cfg"]
    owner = f["owner"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(a, b)}, {a.id} and {b.id}, who were pretending to be pirates by the harbor. It is also about the {need.owner_label} they decided to help."
        ),
        (
            "What did the children think they were going to find?",
            "They thought the bottle map would lead them to treasure. The pirate game made them expect a chest of gold or some other shiny prize."
        ),
        (
            "What was the twist?",
            f"The twist was that the X did not lead to gold at all. It led them to {need.phrase} and a grown-up who needed help."
        ),
        (
            "Why did they decide to help?",
            f"They understood that the map's message meant true treasure was kindness. Once they saw the trouble, helping felt more important than hunting coins."
        ),
    ]
    if f.get("solved"):
        qa.append(
            (
                f"How did {a.id} and {b.id} solve the problem?",
                f"They used {tool.phrase} and {tactic.qa_text} Then {need.solved_line[0].lower() + need.solved_line[1:]}"
            )
        )
        qa.append(
            (
                "What did they write in the essay?",
                f"They wrote that their best pirate tactic was helping first and that {need.essay_lesson}. The essay turned the adventure into a lesson they could remember."
            )
        )
        qa.append(
            (
                "How did the story end?",
                "It ended happily with smiles, a finished kindness essay, and the feeling that helping someone was better than finding gold. The ending image shows that the children went home richer in heart."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"pirates", "kindness", "essay", "tactic"} | set(f["need_cfg"].tags) | set(f["tool_cfg"].tags)
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


def tell(
    theme: HarborTheme,
    need_cfg: Need,
    tactic_cfg: Tactic,
    tool_cfg: Tool,
    child_a: str,
    gender_a: str,
    child_b: str,
    gender_b: str,
    parent_type: str,
    trait_a: str,
    trait_b: str,
) -> World:
    world = World()
    a = world.add(Entity(id="a", kind="character", type=gender_a, label=child_a, role="lead", traits=[trait_a]))
    b = world.add(Entity(id="b", kind="character", type=gender_b, label=child_b, role="mate", traits=[trait_b]))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent", role="parent"))
    owner = world.add(Entity(id="owner", kind="character", type=need_cfg.owner_type, label=need_cfg.owner_label, role="stranger"))
    need = world.add(Entity(id="need", type="problem", label=need_cfg.label, phrase=need_cfg.phrase, role="need"))
    tool = world.add(Entity(id="tool", type="tool", label=tool_cfg.label, phrase=tool_cfg.phrase, tags=set(tool_cfg.tags)))
    world.facts["theme"] = theme

    play_setup(world, a, b, theme)
    mention_essay(world, a, b)
    world.para()
    find_map(world)
    follow_map(world, need_cfg)
    reveal_twist(world, need_cfg)
    world.para()
    decide_to_help(world, a, b, need_cfg, owner)
    use_tactic(world, tactic_cfg, tool_cfg, need_cfg)
    if need.meters["solved"] < THRESHOLD:
        raise StoryError(
            f"(No story: {tactic_cfg.label} with {tool_cfg.label} does not honestly solve {need_cfg.label}. Try a sensible matching tactic and tool.)"
        )
    thanks_and_treasure(world, owner, need_cfg)
    world.para()
    essay_ending(world, a, b, need_cfg)

    world.facts.update(
        a=a,
        b=b,
        parent=parent,
        owner=owner,
        need_cfg=need_cfg,
        tactic_cfg=tactic_cfg,
        tool_cfg=tool_cfg,
        solved=need.meters["solved"] >= THRESHOLD,
    )
    return world


ASP_RULES = r"""
sensible_tactic(T) :- tactic(T), sense(T, S), sense_min(M), S >= M.
matches(N, T, U) :- need_tactic(N, T), need_tool(N, U).
valid(Theme, Need, Tactic, Tool) :- theme(Theme), need(Need), tool(Tool),
                                    sensible_tactic(Tactic),
                                    matches(Need, Tactic, Tool).
solved :- chosen_need(N), chosen_tactic(T), chosen_tool(U), matches(N, T, U), sensible_tactic(T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for theme_id in THEMES:
        lines.append(asp.fact("theme", theme_id))
    for need_id, need in NEEDS.items():
        lines.append(asp.fact("need", need_id))
        for tactic_id in sorted(need.required_tactics):
            lines.append(asp.fact("need_tactic", need_id, tactic_id))
        for tool_id in sorted(need.required_tools):
            lines.append(asp.fact("need_tool", need_id, tool_id))
    for tactic_id, tactic in TACTICS.items():
        lines.append(asp.fact("tactic", tactic_id))
        lines.append(asp.fact("sense", tactic_id, tactic.sense))
    for tool_id in TOOLS:
        lines.append(asp.fact("tool", tool_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_solved(params: StoryParams) -> bool:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_need", params.need),
        asp.fact("chosen_tactic", params.tactic),
        asp.fact("chosen_tool", params.tool),
    ])
    model = asp.one_model(asp_program(scenario, "#show solved/0."))
    return bool(asp.atoms(model, "solved"))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: pirate children discover that kindness is the real treasure."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--need", choices=NEEDS)
    ap.add_argument("--tactic", choices=TACTICS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def explain_rejection(need: Need, tactic: Tactic, tool: Tool) -> str:
    if tactic.sense < SENSE_MIN:
        return (
            f"(No story: the tactic '{tactic.id}' is too silly to count as real help here. "
            f"Pick a sensible kindness tactic instead.)"
        )
    return (
        f"(No story: {tactic.label} with {tool.label} does not fit {need.label}. "
        f"The problem is that {need.obstacle}, so the help plan must honestly match the need.)"
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.need and args.tactic and args.tool:
        need = NEEDS[args.need]
        tactic = TACTICS[args.tactic]
        tool = TOOLS[args.tool]
        if not (tactic.sense >= SENSE_MIN and need_matches(need, tactic, tool)):
            raise StoryError(explain_rejection(need, tactic, tool))
    if args.tactic and TACTICS[args.tactic].sense < SENSE_MIN:
        raise StoryError(explain_rejection(NEEDS[args.need] if args.need else next(iter(NEEDS.values())), TACTICS[args.tactic], TOOLS[args.tool] if args.tool else next(iter(TOOLS.values()))))

    combos = [
        c for c in valid_combos()
        if (args.theme is None or c[0] == args.theme)
        and (args.need is None or c[1] == args.need)
        and (args.tactic is None or c[2] == args.tactic)
        and (args.tool is None or c[3] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme_id, need_id, tactic_id, tool_id = rng.choice(sorted(combos))
    child_a, gender_a = _pick_kid(rng)
    child_b, gender_b = _pick_kid(rng, avoid=child_a)
    parent = args.parent or rng.choice(["mother", "father"])
    trait_a = rng.choice(TRAITS)
    trait_b = rng.choice(TRAITS)
    return StoryParams(
        theme=theme_id,
        need=need_id,
        tactic=tactic_id,
        tool=tool_id,
        child_a=child_a,
        gender_a=gender_a,
        child_b=child_b,
        gender_b=gender_b,
        parent=parent,
        trait_a=trait_a,
        trait_b=trait_b,
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES:
        raise StoryError(f"(Unknown theme: {params.theme})")
    if params.need not in NEEDS:
        raise StoryError(f"(Unknown need: {params.need})")
    if params.tactic not in TACTICS:
        raise StoryError(f"(Unknown tactic: {params.tactic})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    need = NEEDS[params.need]
    tactic = TACTICS[params.tactic]
    tool = TOOLS[params.tool]
    if tactic.sense < SENSE_MIN or not need_matches(need, tactic, tool):
        raise StoryError(explain_rejection(need, tactic, tool))

    world = tell(
        theme=THEMES[params.theme],
        need_cfg=need,
        tactic_cfg=tactic,
        tool_cfg=tool,
        child_a=params.child_a,
        gender_a=params.gender_a,
        child_b=params.child_b,
        gender_b=params.gender_b,
        parent_type=params.parent,
        trait_a=params.trait_a,
        trait_b=params.trait_b,
    )

    story = world.render().replace("a and b", "")
    story = story.replace("a ", "")
    story = story.replace(" b ", " ")
    story = story.replace("a,", "")
    story = story.replace("b,", "")

    # Replace internal ids with display names safely after rendering.
    story = story.replace("a", params.child_a)
    story = story.replace("b", params.child_b)

    # Keep fact entities using display labels for QA.
    world.facts["a"].id = params.child_a
    world.facts["b"].id = params.child_b

    return StorySample(
        params=params,
        story=story,
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
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for seed in range(20):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(seed))
            p.seed = seed
            cases.append(p)
        except StoryError:
            rc = 1
            print(f"Random resolve failed for seed {seed}.")
    bad = 0
    for params in cases:
        py = params.tactic in NEEDS[params.need].required_tactics and params.tool in NEEDS[params.need].required_tools and TACTICS[params.tactic].sense >= SENSE_MIN
        asp_ok = asp_solved(params)
        if py != asp_ok:
            bad += 1
    if bad == 0:
        print(f"OK: ASP outcome matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} solve checks differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show solved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, need, tactic, tool) combos:\n")
        for theme, need, tactic, tool in combos:
            print(f"  {theme:15} {need:16} {tactic:14} {tool}")
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
            header = f"### {p.child_a} & {p.child_b}: {p.need} with {p.tactic}/{p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

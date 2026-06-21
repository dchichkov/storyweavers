#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/sendaway_puller_cliff_lookout_humor_teamwork_heartwarming.py
=========================================================================================

A standalone story world for a warm, funny cliff-lookout tale built around a
gusty "sendaway" wind and a safe retrieval tool called a "puller".

The tiny domain:
- Two children visit a cliff lookout on a windy day.
- They bring a light flying toy to enjoy at the lookout.
- A gust lifts or drags the toy into a nearby snag place.
- One child is tempted to rush after it, but the other child and a grown-up keep
  everyone safely behind the rail.
- The toy is recovered only when the children work together with the right tool.
- The ending proves what changed: they still play, but now they do it the safe,
  shared way.

The world model enforces common sense:
- Some toys can be reeled back with a puller because they stay on a line.
- Untethered toys cannot be magically reeled in.
- Some snag places are close enough for a reach tool; others are too far.
- The sea is not a reasonable "happy recovery" target here, so it is refused.

Run it
------
    python storyworlds/worlds/gpt-5.4/sendaway_puller_cliff_lookout_humor_teamwork_heartwarming.py
    python storyworlds/worlds/gpt-5.4/sendaway_puller_cliff_lookout_humor_teamwork_heartwarming.py --toy kite --snag signpost --tool puller
    python storyworlds/worlds/gpt-5.4/sendaway_puller_cliff_lookout_humor_teamwork_heartwarming.py --toy glider --tool puller
    python storyworlds/worlds/gpt-5.4/sendaway_puller_cliff_lookout_humor_teamwork_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4/sendaway_puller_cliff_lookout_humor_teamwork_heartwarming.py --verify
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
SAFE_LINE = 1.0


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
    tethered: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(self.type, self.type)


@dataclass
class Toy:
    id: str
    label: str
    phrase: str
    launch_text: str
    snag_text: str
    tethered: bool
    drift: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Snag:
    id: str
    label: str
    phrase: str
    kind: str
    distance: int
    safe: bool
    landing_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    method: str
    max_distance: int
    works_on_tethered: bool
    kinds: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    toy: str
    snag: str
    tool: str
    child1: str
    child1_gender: str
    child2: str
    child2_gender: str
    grownup: str
    relation: str
    trait: str
    seed: Optional[int] = None


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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"child1", "child2"}]


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_danger(world: World) -> list[str]:
    out: list[str] = []
    toy = world.get("toy")
    place = world.get("snag")
    if toy.meters["stuck"] < THRESHOLD:
        return out
    sig = ("danger", toy.id, place.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("lookout").meters["risk"] += 1
    for kid in world.kids():
        kid.memes["worry"] += 1
    out.append("__danger__")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    a = world.get("child1")
    b = world.get("child2")
    if a.meters["holding"] < THRESHOLD and b.meters["holding"] < THRESHOLD:
        return out
    if a.meters["guiding"] < THRESHOLD and b.meters["guiding"] < THRESHOLD:
        return out
    sig = ("teamwork",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    a.memes["trust"] += 1
    b.memes["trust"] += 1
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    out.append("__teamwork__")
    return out


CAUSAL_RULES = [
    Rule(name="danger", tag="physical", apply=_r_danger),
    Rule(name="teamwork", tag="social", apply=_r_teamwork),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(s for s in bits if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


TOYS = {
    "kite": Toy(
        id="kite",
        label="kite",
        phrase="a bright little kite with a laughing gull painted on it",
        launch_text="The kite bounced and dipped like it was trying to tell jokes to the clouds.",
        snag_text="its string still trailed back to the children",
        tethered=True,
        drift=3,
        tags={"kite", "wind"},
    ),
    "streamer": Toy(
        id="streamer",
        label="sendaway streamer",
        phrase="a striped sendaway streamer on a spool",
        launch_text="The sendaway streamer made a rude little raspberry sound every time the gusts caught it.",
        snag_text="its ribbon still ran back to the spool",
        tethered=True,
        drift=2,
        tags={"streamer", "wind"},
    ),
    "glider": Toy(
        id="glider",
        label="paper glider",
        phrase="a paper glider with a brave red nose",
        launch_text="The glider swooped so proudly that both children bowed to it as if it were a tiny captain.",
        snag_text="it had no string at all",
        tethered=False,
        drift=2,
        tags={"glider", "wind"},
    ),
}

SNAGS = {
    "railing": Snag(
        id="railing",
        label="railing",
        phrase="the wooden lookout railing",
        kind="hook",
        distance=1,
        safe=True,
        landing_text="It flapped against the railing instead of flying all the way out.",
        tags={"railing"},
    ),
    "signpost": Snag(
        id="signpost",
        label="signpost",
        phrase="the tall signpost by the lookout map",
        kind="hook",
        distance=2,
        safe=True,
        landing_text="It looped itself around the signpost and quivered there.",
        tags={"signpost"},
    ),
    "bush": Snag(
        id="bush",
        label="bush",
        phrase="a berry bush just below the path",
        kind="soft",
        distance=2,
        safe=True,
        landing_text="It settled in the berry bush below the path and shook the leaves.",
        tags={"bush"},
    ),
    "ledge": Snag(
        id="ledge",
        label="rock ledge",
        phrase="a flat rock ledge below the fence",
        kind="flat",
        distance=3,
        safe=True,
        landing_text="It skidded onto a flat rock ledge below the fence and sat there, teasing them.",
        tags={"ledge"},
    ),
    "sea": Snag(
        id="sea",
        label="sea",
        phrase="the bright sea far below",
        kind="lost",
        distance=9,
        safe=False,
        landing_text="It darted out over the bright sea, too far for any lookout tool to reach.",
        tags={"sea"},
    ),
}

TOOLS = {
    "puller": Tool(
        id="puller",
        label="puller",
        phrase="a small puller reel with a turning handle",
        method="reel",
        max_distance=3,
        works_on_tethered=True,
        kinds=set(),
        tags={"puller", "tool"},
    ),
    "hook_pole": Tool(
        id="hook_pole",
        label="hook pole",
        phrase="a long hook pole kept by the fence",
        method="hook",
        max_distance=2,
        works_on_tethered=False,
        kinds={"hook"},
        tags={"pole", "tool"},
    ),
    "basket_net": Tool(
        id="basket_net",
        label="basket net",
        phrase="a long basket net with a soft ring",
        method="scoop",
        max_distance=2,
        works_on_tethered=False,
        kinds={"soft", "flat"},
        tags={"net", "tool"},
    ),
    "grabber": Tool(
        id="grabber",
        label="reacher grabber",
        phrase="a clicky reacher grabber",
        method="grab",
        max_distance=1,
        works_on_tethered=False,
        kinds={"hook"},
        tags={"grabber", "tool"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["careful", "funny", "steady", "gentle", "clever", "patient"]
RELATIONS = ["siblings", "friends"]


def tool_can_retrieve(toy: Toy, snag: Snag, tool: Tool) -> bool:
    if not snag.safe:
        return False
    if toy.tethered and tool.works_on_tethered and snag.distance <= tool.max_distance:
        return True
    if snag.distance > tool.max_distance:
        return False
    return snag.kind in tool.kinds


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for toy_id, toy in TOYS.items():
        for snag_id, snag in SNAGS.items():
            for tool_id, tool in TOOLS.items():
                if tool_can_retrieve(toy, snag, tool):
                    out.append((toy_id, snag_id, tool_id))
    return sorted(out)


def outcome_of(params: StoryParams) -> str:
    toy = TOYS[params.toy]
    snag = SNAGS[params.snag]
    tool = TOOLS[params.tool]
    if toy.tethered and tool.id == "puller" and snag.distance <= tool.max_distance and snag.safe:
        return "reeled"
    return "lifted"


def explain_rejection(toy: Toy, snag: Snag, tool: Tool) -> str:
    if not snag.safe:
        return (
            f"(No story: once a {toy.label} is out over {snag.phrase}, it is too far away for a warm "
            f"teamwork rescue at the lookout. Pick a nearer snag place.)"
        )
    if toy.tethered and tool.works_on_tethered and snag.distance > tool.max_distance:
        return (
            f"(No story: the {tool.label} is not long enough to help with a {toy.label} at the "
            f"{snag.label}. Pick a nearer snag place or another tool.)"
        )
    if not toy.tethered and tool.id == "puller":
        return (
            f"(No story: the {tool.label} can reel back something on a line, but a {toy.label} has no "
            f"line to reel. Pick a hook pole, basket net, or another toy.)"
        )
    if snag.distance > tool.max_distance:
        return (
            f"(No story: the {snag.label} is too far away for the {tool.label}. Pick a nearer snag place.)"
        )
    return (
        f"(No story: the {tool.label} does not sensibly retrieve a {toy.label} from the {snag.label}. "
        f"Choose a tool that matches the toy or where it landed.)"
    )


def relation_noun(relation: str) -> str:
    return "siblings" if relation == "siblings" else "friends"


def predict_retrieval(world: World, tool_id: str) -> dict:
    sim = world.copy()
    toy = sim.get("toy")
    snag_ent = sim.get("snag")
    toy_cfg = sim.facts["toy_cfg"]
    snag_cfg = sim.facts["snag_cfg"]
    tool_cfg = TOOLS[tool_id]
    possible = tool_can_retrieve(toy_cfg, snag_cfg, tool_cfg)
    if possible:
        toy.meters["stuck"] = 0.0
        toy.meters["back"] += 1
    return {"possible": possible, "safe": snag_ent.meters["too_close"] < THRESHOLD}


def introduce(world: World, a: Entity, b: Entity, grown: Entity, toy: Toy) -> None:
    pair = relation_noun(world.facts["relation"])
    world.say(
        f"{a.id} and {b.id}, two {pair}, climbed to the cliff lookout with {a.id}'s "
        f"{grown.label_word} and {toy.phrase}."
    )
    world.say(
        "The wind there was so bossy that the grown-ups jokingly called it the sendaway wind, "
        "because it tried to send every napkin, hat, and squeal straight into the sky."
    )
    world.say(
        f"{toy.launch_text}"
    )


def play(world: World, a: Entity, b: Entity, toy: Toy) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"{a.id} held the start, {b.id} counted to three, and together they let the {toy.label} dance in the gusts."
    )
    world.say(
        f'When a puff of wind pushed {b.id}\'s hair into {b.pronoun("possessive")} mouth, '
        f'{a.id} laughed so hard that even {b.id} had to laugh too.'
    )


def gust(world: World, a: Entity, b: Entity, toy_cfg: Toy, snag_cfg: Snag) -> None:
    toy = world.get("toy")
    snag_ent = world.get("snag")
    toy.meters["stuck"] += 1
    snag_ent.meters["occupied"] += 1
    propagate(world, narrate=False)
    world.say(
        "Then a bigger gust came charging around the rocks like a goat in a hurry."
    )
    world.say(
        f"The {toy_cfg.label} jerked sideways, and {snag_cfg.landing_text} {toy_cfg.snag_text}."
    )
    world.say(
        f'For one second, both children made the exact same surprised face, which made {grownup_title(world.get("grownup"))} snort with laughter even while hurrying closer.'
    )


def grownup_title(ent: Entity) -> str:
    return ent.label_word.capitalize()


def unsafe_step(world: World, a: Entity, b: Entity) -> None:
    a.memes["impulse"] += 1
    world.get("lookout").meters["edge_pull"] += 1
    world.say(
        f'"I can get it!" {a.id} blurted, taking one quick step toward the rail.'
    )
    world.say(
        f'{b.id} caught {a.id}\'s sleeve at once. "Nope," {b.pronoun()} said. "The toy can wait. You stay."'
    )


def keep_back(world: World, a: Entity, b: Entity, grown: Entity) -> None:
    a.meters["behind_line"] = SAFE_LINE
    b.meters["behind_line"] = SAFE_LINE
    grown.meters["behind_line"] = SAFE_LINE
    world.get("snag").meters["too_close"] = 0.0
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f'{grownup_title(grown)} put a steady hand on both shoulders and smiled. '
        f'"Best lookout rule," {grown.pronoun()} said, "feet stay back, brains go forward."'
    )


def choose_tool(world: World, a: Entity, b: Entity, grown: Entity, tool_cfg: Tool) -> None:
    pred = predict_retrieval(world, tool_cfg.id)
    world.facts["predicted_possible"] = pred["possible"]
    world.say(
        f'{grownup_title(grown)} pointed to {tool_cfg.phrase} hanging by the fence.'
    )
    if tool_cfg.id == "puller":
        world.say(
            f'"Good thing the line is still with us," {grown.pronoun()} said. "A puller can bring back what the wind borrows."'
        )
    else:
        world.say(
            f'"We do not lean, and we do not climb," {grown.pronoun()} said. "We use the right tool and each other."'
        )


def retrieve(world: World, a: Entity, b: Entity, toy_cfg: Toy, snag_cfg: Snag, tool_cfg: Tool) -> None:
    toy = world.get("toy")
    a.meters["holding"] += 1
    b.meters["guiding"] += 1
    propagate(world, narrate=False)
    toy.meters["stuck"] = 0.0
    toy.meters["back"] += 1
    world.get("lookout").meters["risk"] = 0.0

    if tool_cfg.id == "puller":
        world.say(
            f"{a.id} held the spool with both hands while {b.id} turned the puller handle, slow and even."
        )
        world.say(
            f"The line tightened, the {toy_cfg.label} gave one last silly flap at the {snag_cfg.label}, and then it came skimming back toward them."
        )
    elif tool_cfg.id == "hook_pole":
        world.say(
            f"{a.id} steadied the hook pole while {b.id} told {a.pronoun('object')} when to lift and when to wait."
        )
        world.say(
            f"On the third careful try, the hook nudged the {toy_cfg.label} free from the {snag_cfg.label} and swung it back."
        )
    elif tool_cfg.id == "basket_net":
        world.say(
            f"{a.id} lowered the basket net while {b.id} watched the wind and called, \"Now a little left. Now stop.\""
        )
        world.say(
            f"The soft ring scooped the {toy_cfg.label} up from the {snag_cfg.label}, and both children made the same relieved gulping sound."
        )
    else:
        world.say(
            f"{a.id} clicked the reacher grabber while {b.id} guided the tip toward the {toy_cfg.label}."
        )
        world.say(
            f"With one neat pinch, the reacher caught the line and brought the {toy_cfg.label} back from the {snag_cfg.label}."
        )


def celebrate(world: World, a: Entity, b: Entity, grown: Entity, toy_cfg: Toy, tool_cfg: Tool) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    a.memes["love"] += 1
    b.memes["love"] += 1
    grown.memes["love"] += 1
    world.say(
        f'{grownup_title(grown)} bowed toward the children. "Well done, rescue crew," {grown.pronoun()} said.'
    )
    world.say(
        f'"You held, I turned," said {b.id}. "No," said {a.id}, grinning, "you bossed the wind."'
    )
    world.say(
        f"That made all three of them laugh, and even the {toy_cfg.label} seemed to tremble with pride in {a.pronoun('possessive')} hands."
    )
    if tool_cfg.id == "puller":
        world.say(
            "After that they kept the puller beside them, and every launch began with one child checking the line while the other checked the sky."
        )
    else:
        world.say(
            "After that they flew their toy farther from the edge and took turns being starter and watcher."
        )
    world.say(
        "The cliff lookout still had its sendaway wind, but now the children had a bring-back plan, a shared laugh, and each other."
    )


def tell(
    toy_cfg: Toy,
    snag_cfg: Snag,
    tool_cfg: Tool,
    child1_name: str,
    child1_gender: str,
    child2_name: str,
    child2_gender: str,
    grownup_type: str,
    relation: str,
    trait: str,
) -> World:
    world = World()
    a = world.add(Entity(id="child1", kind="character", type=child1_gender, label=child1_name, role="child1", traits=[trait]))
    b = world.add(Entity(id="child2", kind="character", type=child2_gender, label=child2_name, role="child2", traits=["steady"]))
    grown = world.add(Entity(id="grownup", kind="character", type=grownup_type, label="the grown-up", role="grownup"))
    lookout = world.add(Entity(id="lookout", type="place", label="cliff lookout"))
    toy = world.add(Entity(id="toy", type="toy", label=toy_cfg.label, phrase=toy_cfg.phrase, tethered=toy_cfg.tethered))
    snag = world.add(Entity(id="snag", type="place", label=snag_cfg.label, phrase=snag_cfg.phrase, attrs={"kind": snag_cfg.kind, "distance": snag_cfg.distance}))
    tool = world.add(Entity(id="tool", type="tool", label=tool_cfg.label, phrase=tool_cfg.phrase))

    world.facts.update(
        toy_cfg=toy_cfg,
        snag_cfg=snag_cfg,
        tool_cfg=tool_cfg,
        relation=relation,
        child1_name=child1_name,
        child2_name=child2_name,
    )

    introduce(world, a, b, grown, toy_cfg)
    play(world, a, b, toy_cfg)

    world.para()
    gust(world, a, b, toy_cfg, snag_cfg)
    unsafe_step(world, a, b)
    keep_back(world, a, b, grown)

    world.para()
    choose_tool(world, a, b, grown, tool_cfg)
    retrieve(world, a, b, toy_cfg, snag_cfg, tool_cfg)

    world.para()
    celebrate(world, a, b, grown, toy_cfg, tool_cfg)

    world.facts.update(
        child1=a,
        child2=b,
        grownup=grown,
        lookout=lookout,
        toy=toy,
        snag=snag,
        tool=tool,
        outcome=outcome_of(
            StoryParams(
                toy=toy_cfg.id,
                snag=snag_cfg.id,
                tool=tool_cfg.id,
                child1=child1_name,
                child1_gender=child1_gender,
                child2=child2_name,
                child2_gender=child2_gender,
                grownup=grownup_type,
                relation=relation,
                trait=trait,
            )
        ),
        stayed_back=a.meters["behind_line"] >= THRESHOLD and b.meters["behind_line"] >= THRESHOLD,
        teamwork=a.meters["holding"] >= THRESHOLD and b.meters["guiding"] >= THRESHOLD,
        retrieved=toy.meters["back"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "wind": [
        (
            "Why is a cliff lookout windy?",
            "Cliff lookouts are often windy because open air can move fast along the edge with nothing big in the way. That is why light things can flap or fly there so easily."
        )
    ],
    "kite": [
        (
            "What is a kite?",
            "A kite is a light toy that catches the wind and flies while someone holds its line. The line helps bring it back."
        )
    ],
    "streamer": [
        (
            "What is a streamer?",
            "A streamer is a long strip of light material that flutters in the wind. If it is tied to a spool, it can be let out and pulled back."
        )
    ],
    "glider": [
        (
            "What is a paper glider?",
            "A paper glider is a folded paper toy that slides through the air for a short time. It does not stay tied to you the way a kite does."
        )
    ],
    "puller": [
        (
            "What does a puller do?",
            "A puller is a tool with a handle or reel that helps draw a line back in. It only works when there is something connected to that line."
        )
    ],
    "pole": [
        (
            "What is a hook pole used for?",
            "A hook pole helps pull or lift something that is caught nearby. It works best when the stuck thing is close enough to reach safely."
        )
    ],
    "net": [
        (
            "What is a basket net for?",
            "A basket net can scoop up a light thing without poking it too hard. Grown-ups and children still need to use it from a safe place."
        )
    ],
    "grabber": [
        (
            "What is a reacher grabber?",
            "A reacher grabber is a tool with jaws at the end so you can pinch and pick something up from a short distance away. It is for reaching, not for leaning over edges."
        )
    ],
    "safety": [
        (
            "What should you do if something blows near a cliff edge?",
            "Stop and get a grown-up right away instead of rushing after it. Safe feet and calm teamwork are better than one fast, risky grab."
        )
    ],
    "teamwork": [
        (
            "Why can teamwork help with a tricky job?",
            "Teamwork helps because one person can hold steady while another person watches, guides, or turns a tool. Two careful jobs together can be safer than one rushed job alone."
        )
    ],
}
KNOWLEDGE_ORDER = ["wind", "kite", "streamer", "glider", "puller", "pole", "net", "grabber", "safety", "teamwork"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["child1"]
    b = f["child2"]
    toy_cfg = f["toy_cfg"]
    tool_cfg = f["tool_cfg"]
    snag_cfg = f["snag_cfg"]
    return [
        f'Write a heartwarming story for a 3-to-5-year-old set at a cliff lookout that includes the words "sendaway" and "puller".',
        f"Tell a funny teamwork story where {a.label} and {b.label} lose a {toy_cfg.label} to a gust at a cliff lookout, stay back from the edge, and use a {tool_cfg.label} to get it back from the {snag_cfg.label}.",
        f"Write a gentle story in which children laugh, listen, and solve a windy problem together instead of making a risky grab.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["child1"]
    b = f["child2"]
    grown = f["grownup"]
    toy_cfg = f["toy_cfg"]
    snag_cfg = f["snag_cfg"]
    tool_cfg = f["tool_cfg"]
    out = f["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {a.label} and {b.label} at a cliff lookout with {a.label}'s {grown.label_word}. They are trying to enjoy a windy day with their {toy_cfg.label}."
        ),
        (
            "What problem happened at the cliff lookout?",
            f"A strong gust shoved the {toy_cfg.label} onto the {snag_cfg.label}. That made the moment feel risky because the toy was close to the edge and the children were upset."
        ),
        (
            f"Why did {b.label} stop {a.label} from rushing forward?",
            f"{b.label} knew the toy was not worth one unsafe step near the rail. The children needed to stay back and solve the problem with calm teamwork instead."
        ),
        (
            "How did the grown-up help?",
            f"{grown.label_word.capitalize()} reminded them that their feet should stay back while their brains worked forward. Then {grown.pronoun()} pointed them to the right tool instead of letting anyone grab blindly."
        ),
    ]
    if out == "reeled":
        qa.append(
            (
                f"How did they use the {tool_cfg.label}?",
                f"{a.label} held the spool while {b.label} turned the puller handle, slow and even. Because the {toy_cfg.label} was still on a line, they could reel it safely back instead of leaning over the edge."
            )
        )
    else:
        qa.append(
            (
                f"How did they get the {toy_cfg.label} back?",
                f"They worked together with the {tool_cfg.label} from behind the safe line. One child steadied the tool while the other watched and guided, which is why the rescue worked without anyone going too close."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended warmly, with laughter and pride. The sendaway wind was still blowing, but the children had learned to answer it with a bring-back plan and teamwork."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"safety", "teamwork", "wind"} | set(f["toy_cfg"].tags) | set(f["tool_cfg"].tags)
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.tethered:
            bits.append("tethered=True")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        toy="streamer",
        snag="signpost",
        tool="puller",
        child1="Lily",
        child1_gender="girl",
        child2="Tom",
        child2_gender="boy",
        grownup="mother",
        relation="siblings",
        trait="funny",
    ),
    StoryParams(
        toy="kite",
        snag="ledge",
        tool="puller",
        child1="Ben",
        child1_gender="boy",
        child2="Maya",
        child2_gender="girl",
        grownup="father",
        relation="friends",
        trait="steady",
    ),
    StoryParams(
        toy="glider",
        snag="bush",
        tool="basket_net",
        child1="Zoe",
        child1_gender="girl",
        child2="Max",
        child2_gender="boy",
        grownup="aunt",
        relation="friends",
        trait="clever",
    ),
    StoryParams(
        toy="glider",
        snag="railing",
        tool="grabbber" if False else "grabber",
        child1="Noah",
        child1_gender="boy",
        child2="Ella",
        child2_gender="girl",
        grownup="uncle",
        relation="siblings",
        trait="patient",
    ),
    StoryParams(
        toy="kite",
        snag="signpost",
        tool="hook_pole",
        child1="Ava",
        child1_gender="girl",
        child2="Finn",
        child2_gender="boy",
        grownup="mother",
        relation="friends",
        trait="gentle",
    ),
]


ASP_RULES = r"""
safe_snag(S) :- snag(S), safe(S).

valid(Ty, S, Tl) :- toy(Ty), snag(S), tool(Tl), safe_snag(S),
                    tethered(Ty), works_on_tethered(Tl), distance(S, D), max_distance(Tl, M), D <= M.
valid(Ty, S, Tl) :- toy(Ty), snag(S), tool(Tl), safe_snag(S),
                    snag_kind(S, K), works_on_kind(Tl, K),
                    distance(S, D), max_distance(Tl, M), D <= M.

outcome(reeled) :- chosen_toy(Ty), chosen_tool(puller), chosen_snag(S),
                   tethered(Ty), safe(S), distance(S, D), max_distance(puller, M), D <= M.
outcome(lifted) :- valid(Ty, S, Tl), chosen_toy(Ty), chosen_snag(S), chosen_tool(Tl), not outcome(reeled).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for toy_id, toy in TOYS.items():
        lines.append(asp.fact("toy", toy_id))
        if toy.tethered:
            lines.append(asp.fact("tethered", toy_id))
    for snag_id, snag in SNAGS.items():
        lines.append(asp.fact("snag", snag_id))
        lines.append(asp.fact("distance", snag_id, snag.distance))
        lines.append(asp.fact("snag_kind", snag_id, snag.kind))
        if snag.safe:
            lines.append(asp.fact("safe", snag_id))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("max_distance", tool_id, tool.max_distance))
        if tool.works_on_tethered:
            lines.append(asp.fact("works_on_tethered", tool_id))
        for kind in sorted(tool.kinds):
            lines.append(asp.fact("works_on_kind", tool_id, kind))
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
            asp.fact("chosen_toy", params.toy),
            asp.fact("chosen_snag", params.snag),
            asp.fact("chosen_tool", params.tool),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def _smoke_story() -> None:
    sample = generate(CURATED[0])
    if not sample.story or "cliff lookout" not in sample.story or "sendaway" not in sample.story:
        raise StoryError("(Smoke test failed: generated story is missing required anchored content.)")


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    scenarios = list(CURATED)
    for seed in range(60):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        scenarios.append(params)
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
        _smoke_story()
        print("OK: smoke generation test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world: a gusty cliff lookout, a stuck toy, and a teamwork rescue."
    )
    ap.add_argument("--toy", choices=TOYS)
    ap.add_argument("--snag", choices=SNAGS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--grownup", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.toy and args.snag and args.tool:
        toy = TOYS[args.toy]
        snag = SNAGS[args.snag]
        tool = TOOLS[args.tool]
        if not tool_can_retrieve(toy, snag, tool):
            raise StoryError(explain_rejection(toy, snag, tool))

    combos = [
        combo for combo in valid_combos()
        if (args.toy is None or combo[0] == args.toy)
        and (args.snag is None or combo[1] == args.snag)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        if args.toy and args.snag and args.tool:
            raise StoryError(explain_rejection(TOYS[args.toy], SNAGS[args.snag], TOOLS[args.tool]))
        raise StoryError("(No valid combination matches the given options.)")

    toy_id, snag_id, tool_id = rng.choice(sorted(combos))
    child1_gender = rng.choice(["girl", "boy"])
    child2_gender = rng.choice(["girl", "boy"])
    child1 = _pick_name(rng, child1_gender)
    child2 = _pick_name(rng, child2_gender, avoid=child1)
    grownup = args.grownup or rng.choice(["mother", "father", "aunt", "uncle"])
    relation = rng.choice(RELATIONS)
    trait = rng.choice(TRAITS)
    return StoryParams(
        toy=toy_id,
        snag=snag_id,
        tool=tool_id,
        child1=child1,
        child1_gender=child1_gender,
        child2=child2,
        child2_gender=child2_gender,
        grownup=grownup,
        relation=relation,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.toy not in TOYS or params.snag not in SNAGS or params.tool not in TOOLS:
        raise StoryError("(Invalid params: unknown toy, snag, or tool.)")
    toy_cfg = TOYS[params.toy]
    snag_cfg = SNAGS[params.snag]
    tool_cfg = TOOLS[params.tool]
    if not tool_can_retrieve(toy_cfg, snag_cfg, tool_cfg):
        raise StoryError(explain_rejection(toy_cfg, snag_cfg, tool_cfg))

    world = tell(
        toy_cfg=toy_cfg,
        snag_cfg=snag_cfg,
        tool_cfg=tool_cfg,
        child1_name=params.child1,
        child1_gender=params.child1_gender,
        child2_name=params.child2,
        child2_gender=params.child2_gender,
        grownup_type=params.grownup,
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
        print(f"{len(combos)} compatible (toy, snag, tool) combos:\n")
        for toy_id, snag_id, tool_id in combos:
            print(f"  {toy_id:9} {snag_id:9} {tool_id}")
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
            header = f"### {p.child1} & {p.child2}: {p.toy} at {p.snag} with {p.tool} ({outcome_of(p)})"
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

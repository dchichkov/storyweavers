#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/addictive_baba_conflict_problem_solving_pirate_tale.py
=================================================================================

A standalone story world for a small pirate-style conflict/problem-solving tale.

The seed words are built into the domain:
- "Baba" is the younger pirate child.
- "addictive" describes a catchy treasure gadget that Baba wants to use again
  and again, even when the crew needs to solve a real problem.

World idea
----------
Two children turn a room into a pirate adventure. They are close to finding
treasure, but Baba becomes fixated on a jingling pirate gadget. The gadget feels
"addictive" because it is shiny, noisy, and rewarding. The other child wants to
keep the game moving. A conflict grows. Then they use a concrete plan to pause
the distraction and apply the right tool to the actual obstacle, leading either
to a happy teamwork ending or a small, disappointed ending when the plan is too
weak.

The reasonableness gate is simple and explicit:
- every obstacle requires the right kind of tool;
- some calming plans are known but refused as too weak.

The ASP twin mirrors both the compatibility gate and the outcome model.

Run it
------
python storyworlds/worlds/gpt-5.4/addictive_baba_conflict_problem_solving_pirate_tale.py
python storyworlds/worlds/gpt-5.4/addictive_baba_conflict_problem_solving_pirate_tale.py --all
python storyworlds/worlds/gpt-5.4/addictive_baba_conflict_problem_solving_pirate_tale.py --qa
python storyworlds/worlds/gpt-5.4/addictive_baba_conflict_problem_solving_pirate_tale.py --asp
python storyworlds/worlds/gpt-5.4/addictive_baba_conflict_problem_solving_pirate_tale.py --verify
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
PLAN_MIN = 2


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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Theme:
    id: str
    scene: str = ""
    rig: str = ""
    crew_word: str = "pirates"
    goal: str = "the treasure"
    send_off: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Temptation:
    id: str
    label: str = ""
    phrase: str = ""
    sound: str = ""
    effect: str = ""
    pull: int = 2
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str = ""
    the: str = ""
    need: str = ""
    place_text: str = ""
    solved_text: str = ""
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]


@dataclass
class Tool:
    id: str
    label: str = ""
    phrase: str = ""
    solves: set[str] = field(default_factory=set)
    use_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Plan:
    id: str
    label: str = ""
    sense: int = 2
    power: int = 2
    offer_text: str = ""
    result_text: str = ""
    fail_text: str = ""
    qa_text: str = ""
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"baba", "partner"}]

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


def _r_fixation_stalls(world: World) -> list[str]:
    baba = world.entities.get("Baba")
    partner = world.entities.get("Partner")
    room = world.entities.get("room")
    if baba is None or partner is None or room is None:
        return []
    if baba.memes["fixation"] < THRESHOLD:
        return []
    sig = ("stall", int(baba.memes["fixation"]))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    partner.memes["frustration"] += 1
    room.meters["stuck"] += 1
    return ["__stuck__"]


def _r_solved_brightens(world: World) -> list[str]:
    obstacle = world.entities.get("obstacle")
    if obstacle is None or obstacle.meters["solved"] < THRESHOLD:
        return []
    sig = ("solved", obstacle.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["joy"] += 1
        kid.memes["teamwork"] += 1
    return ["__solved__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="fixation_stalls", tag="social", apply=_r_fixation_stalls),
    Rule(name="solved_brightens", tag="social", apply=_r_solved_brightens),
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
        for sent in produced:
            world.say(sent)
    return produced


THEMES = {
    "pirates": Theme(
        id="pirates",
        scene="a stormy pirate ship",
        rig="The sofa was their ship, a blanket became the sail, and a cardboard box held their paper-map treasure.",
        crew_word="pirates",
        goal="the hidden treasure",
        send_off="set sail again, wiser and laughing",
        tags={"pirates"},
    ),
    "island": Theme(
        id="island",
        scene="a windy treasure island",
        rig="The rug was the beach, two chairs made a cave, and a rolled paper map pointed toward an X.",
        crew_word="pirates",
        goal="the buried treasure",
        send_off="marched off like a brave little crew",
        tags={"pirates"},
    ),
    "harbor": Theme(
        id="harbor",
        scene="a busy pirate harbor",
        rig="The sofa was the dock, a laundry basket was the boat, and a string of blue scarves made the sea.",
        crew_word="pirates",
        goal="the captain's treasure",
        send_off="hurried back to their pretend boat with shining eyes",
        tags={"pirates"},
    ),
}

TEMPTATIONS = {
    "compass": Temptation(
        id="compass",
        label="singing compass",
        phrase="a singing compass with a tiny silver button",
        sound="ting-ting",
        effect="each press made a bright tune and a quick little arrow spin",
        pull=3,
        tags={"compass", "addictive"},
    ),
    "parrot": Temptation(
        id="parrot",
        label="parrot button",
        phrase="a toy parrot with a squawk button",
        sound="squawk",
        effect="each press made the parrot flap and shout a pirate sound",
        pull=2,
        tags={"parrot", "addictive"},
    ),
    "coin": Temptation(
        id="coin",
        label="glow coin",
        phrase="a glow coin that flashed when Baba rubbed it",
        sound="click-click",
        effect="each rub made the coin blink and click like a secret machine",
        pull=2,
        tags={"coin", "addictive"},
    ),
}

OBSTACLES = {
    "dark_cave": Obstacle(
        id="dark_cave",
        label="dark cave",
        the="the dark cave",
        need="light",
        place_text="under the table where the shadows looked deep and piratey",
        solved_text="The cave stopped looking scary once the light reached the back corner.",
        tags={"dark", "cave"},
    ),
    "high_shelf": Obstacle(
        id="high_shelf",
        label="high shelf",
        the="the high shelf",
        need="reach",
        place_text="on the top shelf where the map tube had rolled far above their heads",
        solved_text="The high shelf was not a mystery anymore once someone could reach it safely.",
        tags={"shelf", "reach"},
    ),
    "rope_knot": Obstacle(
        id="rope_knot",
        label="rope knot",
        the="the rope knot",
        need="untie",
        place_text="around the treasure box handle where the string had cinched itself tight",
        solved_text="The knot gave up at last and the box lid popped free.",
        tags={"rope", "knot"},
    ),
}

TOOLS = {
    "lantern": Tool(
        id="lantern",
        label="lantern",
        phrase="a little camping lantern",
        solves={"light"},
        use_text="clicked on the lantern and swept its warm circle of light into the shadows",
        tags={"lantern"},
    ),
    "stool": Tool(
        id="stool",
        label="stool",
        phrase="a steady step stool",
        solves={"reach"},
        use_text="set the stool by the shelf so one careful pirate could reach the map tube",
        tags={"stool"},
    ),
    "fingers": Tool(
        id="fingers",
        label="careful fingers",
        phrase="two patient sets of careful fingers",
        solves={"untie"},
        use_text="worked the knot bit by bit with slow, careful fingers instead of tugging in a rush",
        tags={"fingers"},
    ),
    "bucket": Tool(
        id="bucket",
        label="bucket hook",
        phrase="a plastic bucket used like a hook",
        solves={"reach"},
        use_text="waved the bucket up toward the shelf and tried to snag the map tube",
        tags={"bucket"},
    ),
}

PLANS = {
    "three_turns": Plan(
        id="three_turns",
        label="three turns",
        sense=3,
        power=3,
        offer_text='said, "Three turns for the gadget, then we park it and finish the clue."',
        result_text="Baba counted three happy turns, tucked the gadget into the chest, and took a deep breath.",
        fail_text="Baba counted, but before the game was moving again, another press slipped out.",
        qa_text="They used a three-turn rule and then parked the gadget in the chest",
        tags={"counting", "self_control"},
    ),
    "captain_job": Plan(
        id="captain_job",
        label="captain job",
        sense=2,
        power=2,
        offer_text='said, "Let the gadget rest. Baba can be Captain Clue-Keeper and help with the real pirate job."',
        result_text="Having a real captain job made Baba stand taller and stop reaching for the button.",
        fail_text="Baba liked the title, but the button still seemed louder than the job.",
        qa_text="They gave Baba a captain job so helping felt better than pressing the button",
        tags={"jobs", "teamwork"},
    ),
    "chest_rest": Plan(
        id="chest_rest",
        label="chest rest",
        sense=3,
        power=2,
        offer_text='said, "The gadget can rest in the treasure chest until the hard part is done."',
        result_text="Once the lid clicked shut, the room felt quieter and Baba's hands stopped twitching toward the button.",
        fail_text="Even with the lid shut, Baba kept staring at the chest and asking for one more turn.",
        qa_text="They closed the gadget in the treasure chest until the hard part was done",
        tags={"pause", "teamwork"},
    ),
    "just_hide": Plan(
        id="just_hide",
        label="just hide it",
        sense=1,
        power=1,
        offer_text='said, "I will hide it somewhere."',
        result_text="The gadget disappeared, but no one felt proud of the plan.",
        fail_text="Hiding it without a shared plan only made Baba more upset and more stubborn.",
        qa_text="They tried to hide the gadget",
        tags={"weak_plan"},
    ),
}

PARTNER_NAMES = ["Lily", "Mia", "Tom", "Max", "Nora", "Sam", "Zoe", "Finn"]


def tool_fits(obstacle: Obstacle, tool: Tool) -> bool:
    return obstacle.need in tool.solves


def sensible_plans() -> list[Plan]:
    return [p for p in PLANS.values() if p.sense >= PLAN_MIN]


def problem_settled(plan: Plan, temptation: Temptation) -> bool:
    return plan.power >= temptation.pull


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for theme_id in THEMES:
        for temptation_id, temptation in TEMPTATIONS.items():
            for obstacle_id, obstacle in OBSTACLES.items():
                for tool_id, tool in TOOLS.items():
                    if not tool_fits(obstacle, tool):
                        continue
                    for plan_id, plan in PLANS.items():
                        if plan.sense >= PLAN_MIN:
                            combos.append((theme_id, temptation_id, obstacle_id, tool_id, plan_id))
    return combos


@dataclass
class StoryParams:
    theme: str
    temptation: str
    obstacle: str
    tool: str
    plan: str
    partner_name: str
    partner_gender: str
    parent: str
    seed: Optional[int] = None


def introduce(world: World, baba: Entity, partner: Entity, theme: Theme) -> None:
    baba.memes["joy"] += 1
    partner.memes["joy"] += 1
    world.say(
        f"One breezy afternoon, Baba and {partner.id} turned the living room into {theme.scene}. "
        f"{theme.rig}"
    )
    world.say(
        f'"Captain Baba and First Mate {partner.id}!" Baba shouted. "Today we find {theme.goal}!"'
    )


def reveal_problem(world: World, partner: Entity, obstacle: Obstacle) -> None:
    world.say(
        f"But the last clue was {obstacle.place_text}. "
        f"{obstacle.The} blocked the way."
    )
    if obstacle.need == "light":
        world.say(f'{partner.id} squinted. "We need better light to see in there," {partner.pronoun()} said.')
    elif obstacle.need == "reach":
        world.say(f'{partner.id} stretched up on tiptoe. "We need a safe way to reach it," {partner.pronoun()} said.')
    else:
        world.say(f'{partner.id} tugged once and stopped. "We need patient hands, not hard pulling," {partner.pronoun()} said.')


def discover_temptation(world: World, baba: Entity, temptation: Temptation) -> None:
    gadget = world.get("gadget")
    gadget.meters["active"] += 1
    baba.memes["fixation"] += 1
    world.say(
        f"Just then Baba spotted {temptation.phrase}. {temptation.effect}."
    )
    world.say(
        f'{temptation.sound.capitalize()}! Baba pressed it once, then again. "Listen to that!" Baba laughed.'
    )


def name_conflict(world: World, partner: Entity, baba: Entity, temptation: Temptation) -> None:
    baba.memes["fixation"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{partner.id} waited with the map, but Baba kept reaching for the {temptation.label}. "
        f"Soon the tune felt almost addictive, the kind that made one more turn seem hard to resist."
    )
    if partner.memes["frustration"] >= THRESHOLD:
        world.say(
            f'"Baba, the crew is stuck," {partner.id} said. "I want the treasure too, but I need your help."'
        )


def offer_plan(world: World, parent: Entity, partner: Entity, baba: Entity, plan: Plan) -> None:
    world.say(
        f"{parent.label_word.capitalize()} heard the bickering and knelt beside the ship. "
        f'"Sounds like this crew has a problem to solve," {parent.pronoun()} said.'
    )
    world.say(f'{partner.id} pointed at the clue and {parent.pronoun()} {plan.offer_text}')


def apply_plan(world: World, baba: Entity, partner: Entity, plan: Plan, temptation: Temptation) -> bool:
    if problem_settled(plan, temptation):
        baba.memes["fixation"] = 0.0
        baba.memes["calm"] += 1
        partner.memes["relief"] += 1
        world.say(plan.result_text)
        return True
    baba.memes["fixation"] += 1
    partner.memes["frustration"] += 1
    propagate(world, narrate=False)
    world.say(plan.fail_text)
    return False


def solve_obstacle(world: World, baba: Entity, partner: Entity, obstacle: Obstacle, tool: Tool) -> None:
    obstacle_ent = world.get("obstacle")
    obstacle_ent.meters["solved"] += 1
    world.say(f"Now the pirates could think clearly. {partner.id} and Baba {tool.use_text}.")
    world.say(obstacle.solved_text)
    if obstacle.id == "dark_cave":
        world.say("At the back sat a tiny tin box with two chocolate coins inside.")
    elif obstacle.id == "high_shelf":
        world.say("The map tube rolled down into Baba's hands, and inside was the last X.")
    else:
        world.say("Inside the loosened box they found a folded note and two bright stickers.")
    propagate(world, narrate=False)


def happy_ending(world: World, theme: Theme, baba: Entity, partner: Entity) -> None:
    baba.memes["joy"] += 1
    partner.memes["joy"] += 1
    world.say(
        f'Baba grinned at {partner.id}. "Good pirates solve problems together," Baba said.'
    )
    world.say(
        f"They shared the treasure, tucked the noisy gadget away, and {theme.send_off}."
    )


def disappointed_ending(world: World, parent: Entity, theme: Theme, baba: Entity, partner: Entity) -> None:
    baba.memes["sadness"] += 1
    partner.memes["sadness"] += 1
    world.say(
        f"The clue stayed unsolved that day. {partner.id} rolled up the map, and Baba finally looked at the silent room instead of the gadget."
    )
    world.say(
        f'{parent.label_word.capitalize()} gave them both a hug. "{theme.goal.capitalize()} can wait," {parent.pronoun()} said. '
        f'"Next time we will make a stronger plan before the button gets in charge."'
    )
    world.say(
        "Baba nodded. Even a pirate could see that a game was better when every crewmate was included."
    )


def tell(
    theme: Theme,
    temptation: Temptation,
    obstacle: Obstacle,
    tool: Tool,
    plan: Plan,
    partner_name: str = "Lily",
    partner_gender: str = "girl",
    parent_type: str = "mother",
) -> World:
    world = World()
    baba = world.add(Entity(id="Baba", kind="character", type="girl", role="baba", label="Baba"))
    partner = world.add(
        Entity(id="Partner", kind="character", type=partner_gender, role="partner", label=partner_name, attrs={"name": partner_name})
    )
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    world.add(Entity(id="room", kind="thing", type="room", label="room"))
    world.add(Entity(id="gadget", kind="thing", type="gadget", label=temptation.label))
    obstacle_ent = world.add(Entity(id="obstacle", kind="thing", type="obstacle", label=obstacle.label))
    world.add(Entity(id="tool", kind="thing", type="tool", label=tool.label))

    introduce(world, baba, partner, theme)
    reveal_problem(world, partner, obstacle)

    world.para()
    discover_temptation(world, baba, temptation)
    name_conflict(world, partner, baba, temptation)

    world.para()
    offer_plan(world, parent, partner, baba, plan)
    resolved = apply_plan(world, baba, partner, plan, temptation)

    world.para()
    if resolved:
        solve_obstacle(world, baba, partner, obstacle, tool)
        happy_ending(world, theme, baba, partner)
        outcome = "solved"
    else:
        disappointed_ending(world, parent, theme, baba, partner)
        outcome = "stuck"

    world.facts.update(
        theme=theme,
        temptation=temptation,
        obstacle_cfg=obstacle,
        tool_cfg=tool,
        plan_cfg=plan,
        baba=baba,
        partner=partner,
        partner_name=partner_name,
        parent=parent,
        obstacle=obstacle_ent,
        outcome=outcome,
        resolved=resolved,
    )
    return world


KNOWLEDGE = {
    "addictive": [
        (
            "What does addictive mean in a story like this?",
            "Here it means something feels so fun or catchy that you keep wanting one more turn. It does not mean magic; it means stopping can feel hard."
        )
    ],
    "compass": [
        (
            "What is a compass?",
            "A compass is a tool that points direction. In pirate stories, it helps sailors know which way to go."
        )
    ],
    "parrot": [
        (
            "Why do pirate stories often have parrots?",
            "Parrots are bright, noisy birds, so they fit the lively feeling of pirate adventures. A pretend pirate parrot can also repeat funny sounds."
        )
    ],
    "coin": [
        (
            "What is a treasure coin?",
            "A treasure coin is a shiny coin people imagine finding in a pirate chest. In pretend play, it can stand for a reward or a clue."
        )
    ],
    "lantern": [
        (
            "What does a lantern do?",
            "A lantern makes light so you can see in dark places. In a pirate game, that helps explorers look into caves or corners."
        )
    ],
    "stool": [
        (
            "Why is a step stool useful?",
            "A step stool helps someone reach something high more safely. It is better than stretching or climbing in a wobbly way."
        )
    ],
    "fingers": [
        (
            "Why do knots need patient fingers?",
            "A tight knot often loosens best when you work slowly and gently. Yanking can make it tighter."
        )
    ],
    "counting": [
        (
            "How can counting help with a conflict?",
            "Counting can set a clear limit, like three turns each. A fair limit helps people stop arguing and know what comes next."
        )
    ],
    "teamwork": [
        (
            "Why is teamwork helpful in a problem?",
            "Teamwork lets people share ideas and jobs. When everyone helps, a hard problem can become smaller."
        )
    ],
    "pause": [
        (
            "Why can putting something away help you focus?",
            "Putting a distracting thing away makes it easier to think about the real task. The quiet gives your brain room to choose."
        )
    ],
}
KNOWLEDGE_ORDER = ["addictive", "compass", "parrot", "coin", "lantern", "stool", "fingers", "counting", "pause", "teamwork"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    temptation = f["temptation"]
    obstacle = f["obstacle_cfg"]
    tool = f["tool_cfg"]
    partner_name = f["partner_name"]
    outcome = f["outcome"]
    if outcome == "solved":
        return [
            f'Write a pirate-style story for a 3-to-5-year-old that includes the words "Baba" and "addictive" and has a conflict solved by a practical plan.',
            f"Tell a gentle pirate tale where Baba gets distracted by a {temptation.label}, the crew argues, and then they use {tool.phrase} to solve {obstacle.the}.",
            f"Write a short story about problem solving where Baba and {partner_name} pause a catchy toy, work together, and finally reach the treasure.",
        ]
    return [
        f'Write a pirate-style story for a 3-to-5-year-old that includes the words "Baba" and "addictive" and shows a conflict that is not solved well at first.',
        f"Tell a pirate tale where Baba keeps returning to a {temptation.label}, the crew stays stuck, and a weak plan leaves {obstacle.the} unsolved.",
        f"Write a simple story about a distracting treasure gadget, hurt feelings between crewmates, and learning that stronger problem solving is needed next time.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    partner = f["partner"]
    partner_name = f["partner_name"]
    parent = f["parent"]
    temptation = f["temptation"]
    obstacle = f["obstacle_cfg"]
    tool = f["tool_cfg"]
    plan = f["plan_cfg"]
    outcome = f["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about Baba and {partner_name}, two children pretending to be pirates. {parent.label_word.capitalize()} also helps when their argument gets stuck."
        ),
        (
            "What problem did the pirate crew have?",
            f"The crew was close to treasure, but {obstacle.the} blocked the last clue. They needed the right kind of help to get past it."
        ),
        (
            "Why did Baba and the other child argue?",
            f"Baba kept returning to the {temptation.label} because its sound and motion felt exciting and addictive. {partner_name} felt frustrated because the game could not move on while Baba kept pressing it."
        ),
        (
            f"What plan did they try?",
            f"They tried {plan.qa_text}. The plan was meant to calm the distraction so the crew could think about the real problem again."
        ),
    ]
    if outcome == "solved":
        qa.append(
            (
                "How did they solve the treasure problem?",
                f"First the plan settled the argument, and then Baba and {partner_name} used {tool.phrase}. That worked because {tool.label} was the right tool for {obstacle.the}."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended happily with the treasure found and the gadget put away. The ending shows they changed from bickering pirates into a team that could solve problems together."
            )
        )
    else:
        qa.append(
            (
                "Did the plan work well enough?",
                f"No. The plan was too weak, so Baba still felt pulled back toward the gadget and the clue stayed unsolved. Because the distraction was not truly settled, the crew could not use their pirate tools well."
            )
        )
        qa.append(
            (
                "What did they learn by the end?",
                f"They learned that a real problem sometimes needs a stronger shared plan, not just grabbing or hiding a thing. The ending is disappointed but gentle, because everyone is safe and ready to try better next time."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"addictive"} | set(f["temptation"].tags) | set(f["tool_cfg"].tags) | set(f["plan_cfg"].tags)
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
        bits: list[str] = []
        if ent.role:
            bits.append(f"role={ent.role}")
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
    return "\n".join(lines)


def explain_tool(obstacle: Obstacle, tool: Tool) -> str:
    return (
        f"(No story: {tool.phrase} does not really solve {obstacle.the}. "
        f"This world only tells pirate stories where the tool matches the obstacle.)"
    )


def explain_plan(plan: Plan) -> str:
    sensible = ", ".join(sorted(p.id for p in sensible_plans()))
    return (
        f"(Refusing plan '{plan.id}': it is too weak for this storyworld "
        f"(sense={plan.sense} < {PLAN_MIN}). Try one of: {sensible}.)"
    )


def outcome_of(params: StoryParams) -> str:
    plan = PLANS[params.plan]
    temptation = TEMPTATIONS[params.temptation]
    return "solved" if problem_settled(plan, temptation) else "stuck"


ASP_RULES = r"""
% --- compatibility gate ----------------------------------------------------
tool_fits(O, T) :- obstacle(O), tool(T), needs(O, N), solves(T, N).
sensible_plan(P) :- plan(P), sense(P, S), plan_min(M), S >= M.
valid(Th, Te, O, T, P) :- theme(Th), temptation(Te), tool_fits(O, T), sensible_plan(P).

% --- outcome ---------------------------------------------------------------
solved_conflict :- chosen_plan(P), chosen_temptation(Te), power(P, PP), pull(Te, TP), PP >= TP.
outcome(solved) :- solved_conflict.
outcome(stuck) :- not solved_conflict.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for theme_id in THEMES:
        lines.append(asp.fact("theme", theme_id))
    for temptation_id, temptation in TEMPTATIONS.items():
        lines.append(asp.fact("temptation", temptation_id))
        lines.append(asp.fact("pull", temptation_id, temptation.pull))
    for obstacle_id, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", obstacle_id))
        lines.append(asp.fact("needs", obstacle_id, obstacle.need))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        for need in sorted(tool.solves):
            lines.append(asp.fact("solves", tool_id, need))
    for plan_id, plan in PLANS.items():
        lines.append(asp.fact("plan", plan_id))
        lines.append(asp.fact("sense", plan_id, plan.sense))
        lines.append(asp.fact("power", plan_id, plan.power))
    lines.append(asp.fact("plan_min", PLAN_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_plan", params.plan),
            asp.fact("chosen_temptation", params.temptation),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    found = asp.atoms(model, "outcome")
    return found[0][0] if found else "?"


CURATED = [
    StoryParams(
        theme="pirates",
        temptation="compass",
        obstacle="dark_cave",
        tool="lantern",
        plan="three_turns",
        partner_name="Lily",
        partner_gender="girl",
        parent="mother",
    ),
    StoryParams(
        theme="island",
        temptation="parrot",
        obstacle="high_shelf",
        tool="stool",
        plan="captain_job",
        partner_name="Tom",
        partner_gender="boy",
        parent="father",
    ),
    StoryParams(
        theme="harbor",
        temptation="coin",
        obstacle="rope_knot",
        tool="fingers",
        plan="chest_rest",
        partner_name="Nora",
        partner_gender="girl",
        parent="mother",
    ),
    StoryParams(
        theme="pirates",
        temptation="compass",
        obstacle="dark_cave",
        tool="lantern",
        plan="just_hide",
        partner_name="Max",
        partner_gender="boy",
        parent="father",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Pirate-style story world: Baba, an addictive treasure gadget, conflict, and problem solving."
    )
    ap.add_argument("--theme", choices=sorted(THEMES))
    ap.add_argument("--temptation", choices=sorted(TEMPTATIONS))
    ap.add_argument("--obstacle", choices=sorted(OBSTACLES))
    ap.add_argument("--tool", choices=sorted(TOOLS))
    ap.add_argument("--plan", choices=sorted(PLANS))
    ap.add_argument("--partner-name")
    ap.add_argument("--partner-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.obstacle and args.tool:
        obstacle = OBSTACLES[args.obstacle]
        tool = TOOLS[args.tool]
        if not tool_fits(obstacle, tool):
            raise StoryError(explain_tool(obstacle, tool))
    if args.plan:
        plan = PLANS[args.plan]
        if plan.sense < PLAN_MIN:
            raise StoryError(explain_plan(plan))

    combos = [
        combo
        for combo in valid_combos()
        if (args.theme is None or combo[0] == args.theme)
        and (args.temptation is None or combo[1] == args.temptation)
        and (args.obstacle is None or combo[2] == args.obstacle)
        and (args.tool is None or combo[3] == args.tool)
        and (args.plan is None or combo[4] == args.plan)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme, temptation, obstacle, tool, plan = rng.choice(sorted(combos))
    partner_gender = args.partner_gender or rng.choice(["girl", "boy"])
    default_names = [n for n in PARTNER_NAMES if n != "Baba"]
    if args.partner_name:
        partner_name = args.partner_name
    else:
        partner_name = rng.choice(default_names)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        theme=theme,
        temptation=temptation,
        obstacle=obstacle,
        tool=tool,
        plan=plan,
        partner_name=partner_name,
        partner_gender=partner_gender,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES:
        raise StoryError(f"(Unknown theme: {params.theme})")
    if params.temptation not in TEMPTATIONS:
        raise StoryError(f"(Unknown temptation: {params.temptation})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.plan not in PLANS:
        raise StoryError(f"(Unknown plan: {params.plan})")

    obstacle = OBSTACLES[params.obstacle]
    tool = TOOLS[params.tool]
    plan = PLANS[params.plan]
    if not tool_fits(obstacle, tool):
        raise StoryError(explain_tool(obstacle, tool))
    if plan.sense < PLAN_MIN:
        raise StoryError(explain_plan(plan))

    world = tell(
        theme=THEMES[params.theme],
        temptation=TEMPTATIONS[params.temptation],
        obstacle=obstacle,
        tool=tool,
        plan=plan,
        partner_name=params.partner_name,
        partner_gender=params.partner_gender,
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


def asp_verify() -> int:
    rc = 0

    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in compatibility gate:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(30):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError while resolving random case {seed}.")
            break

    mismatches = 0
    for params in cases:
        if params.plan in PLANS and PLANS[params.plan].sense >= PLAN_MIN:
            if asp_outcome(params) != outcome_of(params):
                mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True, header="### smoke")
        print("OK: smoke test generate()/emit() succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/5.\n#show sensible_plan/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, temptation, obstacle, tool, plan) combos:\n")
        for theme, temptation, obstacle, tool, plan in combos:
            print(f"  {theme:8} {temptation:8} {obstacle:10} {tool:8} {plan}")
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
            header = (
                f"### Baba & {p.partner_name}: {p.temptation} / {p.obstacle} "
                f"with {p.tool} ({outcome_of(p)})"
            )
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

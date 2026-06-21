#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/indignation_profession_friendship_sound_effects_space_adventure.py
================================================================================================

A standalone storyworld about two friends on a pretend space adventure.

This little domain rebuilds a simple shape:

- two children turn an ordinary place into a spaceship
- one child proudly takes charge
- a noisy mission problem appears
- the captain brushes off the friend's chosen profession
- the friend feels indignation because their job matters
- the captain listens, apologizes, and the two solve the problem together
- the ending image proves the friendship and the mission both recovered

The world model keeps both physical meters (noise, stuckness, progress) and
emotional memes (pride, indignation, trust, relief). The prose is driven by
that state rather than by a single frozen template.

Run it
------
python storyworlds/worlds/gpt-5.4/indignation_profession_friendship_sound_effects_space_adventure.py
python storyworlds/worlds/gpt-5.4/indignation_profession_friendship_sound_effects_space_adventure.py --all
python storyworlds/worlds/gpt-5.4/indignation_profession_friendship_sound_effects_space_adventure.py --qa --json
python storyworlds/worlds/gpt-5.4/indignation_profession_friendship_sound_effects_space_adventure.py --asp
python storyworlds/worlds/gpt-5.4/indignation_profession_friendship_sound_effects_space_adventure.py --verify
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
class Setting:
    id: str
    place: str
    scene: str
    afford_missions: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Mission:
    id: str
    goal: str
    cargo: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    sound: str
    issue_line: str
    need_skill: str
    fix_verb: str
    consequence: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Profession:
    id: str
    label: str
    phrase: str
    skill: str
    boast: str
    calm_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    skill: str
    action_sound: str
    use_line: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        return [e for e in self.entities.values() if e.role in {"captain", "friend"}]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
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


def _r_problem_pressure(world: World) -> list[str]:
    ship = world.get("ship")
    problem = world.get("problem")
    if problem.meters["active"] < THRESHOLD:
        return []
    sig = ("pressure",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    ship.meters["trouble"] += 1
    for kid in world.kids():
        kid.memes["worry"] += 1
    return ["__pressure__"]


def _r_hurt_friendship(world: World) -> list[str]:
    friend = world.get("friend")
    if friend.memes["indignation"] < THRESHOLD:
        return []
    sig = ("strain",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("bond").meters["strain"] += 1
    return ["__strain__"]


def _r_apology_mends(world: World) -> list[str]:
    captain = world.get("captain")
    friend = world.get("friend")
    bond = world.get("bond")
    if captain.memes["apology"] < THRESHOLD or friend.memes["indignation"] < THRESHOLD:
        return []
    sig = ("mend",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    bond.meters["strain"] = 0.0
    friend.memes["indignation"] = 0.0
    captain.memes["humility"] += 1
    friend.memes["trust"] += 1
    return ["__mend__"]


CAUSAL_RULES = [
    Rule(name="problem_pressure", tag="physical", apply=_r_problem_pressure),
    Rule(name="hurt_friendship", tag="social", apply=_r_hurt_friendship),
    Rule(name="apology_mends", tag="social", apply=_r_apology_mends),
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
                produced.extend([s for s in out if not s.startswith("__")])
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def mission_supported(setting: Setting, mission: Mission) -> bool:
    return mission.id in setting.afford_missions


def problem_match(problem: Problem, profession: Profession, tool: Tool) -> bool:
    return problem.need_skill == profession.skill == tool.skill


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for mission_id, mission in MISSIONS.items():
            if not mission_supported(setting, mission):
                continue
            for problem_id, problem in PROBLEMS.items():
                for profession_id, profession in PROFESSIONS.items():
                    for tool_id, tool in TOOLS.items():
                        if problem_match(problem, profession, tool):
                            combos.append((setting_id, mission_id, problem_id, profession_id, tool_id))
    return combos


def predict_success(world: World, profession: Profession, tool: Tool) -> dict:
    sim = world.copy()
    problem = sim.get("problem")
    ship = sim.get("ship")
    if profession.skill == tool.skill == sim.facts["problem_cfg"].need_skill:
        problem.meters["active"] = 0.0
        ship.meters["trouble"] = 0.0
        ship.meters["progress"] += 1
    return {
        "can_fix": ship.meters["progress"] >= THRESHOLD,
        "trouble": ship.meters["trouble"],
    }


def opening(world: World, captain: Entity, friend: Entity, setting: Setting, mission: Mission,
            profession: Profession, tool: Tool) -> None:
    ship = world.get("ship")
    captain.memes["joy"] += 1
    friend.memes["joy"] += 1
    friend.memes["trust"] += 1
    ship.meters["ready"] += 1
    world.say(
        f"On a bright afternoon, {captain.id} and {friend.id} turned {setting.place} into {setting.scene}. "
        f"A laundry basket became the cockpit, pillows became moon rocks, and a silver blanket became the stars."
    )
    world.say(
        f'"Captain {captain.id}!" {captain.id} shouted. "{mission.goal}!"'
    )
    world.say(
        f'{friend.id} climbed in beside {captain.pronoun("object")} and held {tool.phrase}. '
        f'"Then I am the {profession.label}," {friend.pronoun()} said. '
        f'"That is my profession for this mission."'
    )


def problem_appears(world: World, friend: Entity, mission: Mission, problem: Problem) -> None:
    problem_ent = world.get("problem")
    ship = world.get("ship")
    problem_ent.meters["active"] += 1
    ship.meters["noise"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Just as they pretended to lift off, {problem.sound} came from the side of the ship. "
        f"{problem.issue_line}"
    )
    world.say(
        f'{friend.id} sat up straight. "{problem.consequence}," {friend.pronoun()} said.'
    )


def captain_brushes_off(world: World, captain: Entity, friend: Entity, profession: Profession) -> None:
    captain.memes["pride"] += 1
    world.say(
        f'{captain.id} gave the cardboard dashboard a quick pat. "{profession.boast} We do not need to stop."'
    )
    world.say(
        f'{captain.pronoun().capitalize()} tried a wild extra button press of {captain.attrs.get("button_sound", "beep-beep")}, '
        f"but the sound only rattled harder."
    )
    world.get("ship").meters["noise"] += 1
    world.get("problem").meters["active"] += 1


def friend_feels_indignation(world: World, friend: Entity, profession: Profession) -> None:
    pred = predict_success(world, profession, TOOLS[world.facts["tool_cfg"].id])
    friend.memes["indignation"] += 1
    propagate(world, narrate=False)
    world.facts["predicted_fix"] = pred["can_fix"]
    world.say(
        f"{friend.id} felt a hot puff of indignation. {friend.pronoun().capitalize()} was trying to help, "
        f"and the mission really did need that job."
    )
    world.say(
        f'"{profession.calm_line}" {friend.pronoun()} said. "A real crew listens when a friend has the right tool."'
    )


def apology(world: World, captain: Entity, friend: Entity) -> None:
    captain.memes["apology"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{captain.id} heard the hurt in {friend.id}\'s voice and stopped tapping buttons. '
        f'"I am sorry," {captain.pronoun()} said. "I was acting like the captain mattered more than the crew."'
    )
    world.say(
        f'"You are my friend first," {captain.pronoun()} added. "Please show me."'
    )


def solve_problem(world: World, captain: Entity, friend: Entity, problem: Problem,
                  profession: Profession, tool: Tool, mission: Mission) -> None:
    ship = world.get("ship")
    problem_ent = world.get("problem")
    if not problem_match(problem, profession, tool):
        raise StoryError(
            f"(No story: a {profession.label} using {tool.label} cannot solve {problem.label}. "
            f"Pick a profession and tool with the needed skill '{problem.need_skill}'.)"
        )
    tool_ent = world.get("tool")
    tool_ent.meters["used"] += 1
    ship.meters["noise"] = 0.0
    ship.meters["trouble"] = 0.0
    ship.meters["progress"] += 1
    problem_ent.meters["active"] = 0.0
    friend.memes["pride"] += 1
    captain.memes["respect"] += 1
    for kid in world.kids():
        kid.memes["relief"] += 1
        kid.memes["joy"] += 1
    world.say(
        f'{friend.id} took a deep breath, lifted {tool.phrase}, and went to work. '
        f'{tool.action_sound} {tool.use_line}'
    )
    world.say(
        f"Soon the trouble was gone. The ship was ready again, and the crew could {problem.fix_verb}."
    )
    world.say(
        f'Together they finished the mission and {mission.ending}.'
    )


def closing(world: World, captain: Entity, friend: Entity, mission: Mission, profession: Profession) -> None:
    world.say(
        f"When they climbed out at last, {captain.id} bumped {friend.id}'s shoulder with a grin."
    )
    world.say(
        f'"Best {profession.label} in the galaxy," {captain.pronoun()} said.'
    )
    world.say(
        f"{friend.id} grinned back. Their rocket still looked like a pile of pillows, "
        f"but now it also looked like friendship doing its job."
    )
    world.say(
        f"That made the whole adventure feel bigger than pretend."
    )


def tell(setting: Setting, mission: Mission, problem: Problem, profession: Profession, tool: Tool,
         captain_name: str = "Nora", captain_gender: str = "girl",
         friend_name: str = "Max", friend_gender: str = "boy",
         parent_type: str = "mother") -> World:
    world = World(setting)
    captain = world.add(Entity(
        id="captain",
        kind="character",
        type=captain_gender,
        label=captain_name,
        role="captain",
        attrs={"button_sound": random.choice(["beep-beep", "click-click", "tap-tap"])},
    ))
    friend = world.add(Entity(
        id="friend",
        kind="character",
        type=friend_gender,
        label=friend_name,
        role="friend",
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
    ))
    ship = world.add(Entity(id="ship", type="ship", label="ship"))
    bond = world.add(Entity(id="bond", type="bond", label="friendship"))
    world.add(Entity(id="problem", type="problem", label=problem.label))
    world.add(Entity(id="tool", type="tool", label=tool.label))
    world.facts["button_sound"] = captain.attrs["button_sound"]

    opening(world, captain, friend, setting, mission, profession, tool)
    world.para()
    problem_appears(world, friend, mission, problem)
    captain_brushes_off(world, captain, friend, profession)
    friend_feels_indignation(world, friend, profession)
    world.para()
    apology(world, captain, friend)
    solve_problem(world, captain, friend, problem, profession, tool, mission)
    closing(world, captain, friend, mission, profession)

    world.facts.update(
        captain=captain,
        friend=friend,
        parent=parent,
        ship=ship,
        bond=bond,
        setting=setting,
        mission=mission,
        problem_cfg=problem,
        profession_cfg=profession,
        tool_cfg=tool,
        mission_done=ship.meters["progress"] >= THRESHOLD,
        friendship_mended=bond.meters["strain"] < THRESHOLD and captain.memes["apology"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "bedroom": Setting(
        id="bedroom",
        place="the bedroom floor",
        scene="a moon-bright rocket port under a blanket sky",
        afford_missions={"moon_mail", "ring_picnic"},
        tags={"indoors", "pretend"},
    ),
    "backyard": Setting(
        id="backyard",
        place="the backyard",
        scene="a launch field beside the swing-set planets",
        afford_missions={"moon_mail", "comet_rescue"},
        tags={"outdoors", "pretend"},
    ),
    "attic": Setting(
        id="attic",
        place="the attic",
        scene="a secret star dock full of boxes and dusty treasure",
        afford_missions={"ring_picnic", "comet_rescue"},
        tags={"indoors", "pretend"},
    ),
}

MISSIONS = {
    "moon_mail": Mission(
        id="moon_mail",
        goal="Take the silver letter to Moon Rabbit before supper",
        cargo="a silver letter",
        ending="set the silver letter beside a paper moon on the dresser",
        tags={"moon"},
    ),
    "comet_rescue": Mission(
        id="comet_rescue",
        goal="Rescue the lost kite-comet from the dark side of the yard",
        cargo="the lost kite-comet",
        ending="dragged the kite-comet home with a string of shining yarn",
        tags={"comet"},
    ),
    "ring_picnic": Mission(
        id="ring_picnic",
        goal="Carry berry biscuits to the ring picnic around Saturn",
        cargo="berry biscuits",
        ending="served the berry biscuits to three stuffed animals waiting on a hatbox ring",
        tags={"saturn"},
    ),
}

PROBLEMS = {
    "static": Problem(
        id="static",
        label="space static",
        sound="BZZZT! CRACKLE!",
        issue_line="The pretend radio filled with scratchy space static and drowned out the map directions.",
        need_skill="signal",
        fix_verb="hear the route again",
        consequence="If we cannot hear the guide, we may fly in circles",
        tags={"radio", "sound"},
    ),
    "jammed_hatch": Problem(
        id="jammed_hatch",
        label="a jammed hatch",
        sound="CLANG! KUNK!",
        issue_line="The cargo hatch stuck halfway open, wobbling like it wanted to bite the mission box.",
        need_skill="repair",
        fix_verb="close the hatch tight",
        consequence="If the hatch stays loose, our cargo may tumble into space",
        tags={"repair", "sound"},
    ),
    "lost_route": Problem(
        id="lost_route",
        label="a tangled star route",
        sound="BEEP-BEEP? BEEP?",
        issue_line="The star board blinked in every direction at once, and the route lines crossed into a glittery knot.",
        need_skill="navigation",
        fix_verb="find the safe path",
        consequence="If we pick the wrong line, we will miss the picnic ring",
        tags={"map", "sound"},
    ),
}

PROFESSIONS = {
    "signal_officer": Profession(
        id="signal_officer",
        label="signal officer",
        phrase="the crew's signal officer",
        skill="signal",
        boast="I can steer by guesswork",
        calm_line="Signal officers are for listening carefully, not guessing loudly",
        tags={"radio", "profession"},
    ),
    "space_mechanic": Profession(
        id="space_mechanic",
        label="space mechanic",
        phrase="the crew's space mechanic",
        skill="repair",
        boast="I can thump any panel and make it behave",
        calm_line="Space mechanics fix what is loose before it breaks more",
        tags={"repair", "profession"},
    ),
    "star_navigator": Profession(
        id="star_navigator",
        label="star navigator",
        phrase="the crew's star navigator",
        skill="navigation",
        boast="I already know the whole sky",
        calm_line="Star navigators look closely so everyone reaches the right place",
        tags={"map", "profession"},
    ),
}

TOOLS = {
    "headset": Tool(
        id="headset",
        label="headset",
        phrase="the foam headset",
        skill="signal",
        action_sound="Click! Hummm!",
        use_line="The scratchy noise softened until a clean little beep led the way",
        tags={"radio"},
    ),
    "wrench": Tool(
        id="wrench",
        label="moon wrench",
        phrase="the blue moon wrench",
        skill="repair",
        action_sound="Clink-clink! Twist!",
        use_line="The hatch gave one last grumble and then sat neatly in place",
        tags={"repair"},
    ),
    "star_map": Tool(
        id="star_map",
        label="star map",
        phrase="the folded star map",
        skill="navigation",
        action_sound="Flip-flip! Tap!",
        use_line="The crossed lines untangled into one bright path straight ahead",
        tags={"map"},
    ),
}

GIRL_NAMES = ["Nora", "Mia", "Luna", "Ivy", "Ava", "Zoe", "Ella", "Ruby"]
BOY_NAMES = ["Max", "Leo", "Finn", "Theo", "Ben", "Sam", "Eli", "Owen"]


@dataclass
class StoryParams:
    setting: str
    mission: str
    problem: str
    profession: str
    tool: str
    captain_name: str
    captain_gender: str
    friend_name: str
    friend_gender: str
    parent: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "profession": [
        (
            "What is a profession?",
            "A profession is a job that a person learns to do well. In pretend play, children often use profession words like mechanic or navigator to imagine helping in different ways.",
        )
    ],
    "friendship": [
        (
            "What helps a friendship when someone feels hurt?",
            "Listening, apologizing, and speaking kindly help a friendship feel strong again. Friends do better when they treat each other's ideas as important.",
        )
    ],
    "indignation": [
        (
            "What is indignation?",
            "Indignation is the feeling you get when something seems unfair or disrespectful. It can make your face feel hot and your words come out stiff until someone listens.",
        )
    ],
    "radio": [
        (
            "What does a radio do?",
            "A radio sends or receives sound from far away. In stories about spaceships, a radio helps the crew hear messages and directions.",
        )
    ],
    "repair": [
        (
            "What does a mechanic do?",
            "A mechanic fixes parts that are loose or broken so they work again. Mechanics look closely and use tools carefully.",
        )
    ],
    "map": [
        (
            "What does a navigator do?",
            "A navigator helps people find the right path. A navigator reads signs, stars, or maps so the group does not get lost.",
        )
    ],
}

KNOWLEDGE_ORDER = ["profession", "friendship", "indignation", "radio", "repair", "map"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    captain = f["captain"]
    friend = f["friend"]
    profession = f["profession_cfg"]
    problem = f["problem_cfg"]
    mission = f["mission"]
    return [
        'Write a short story for a 3-to-5-year-old that includes the words "indignation" and "profession" and feels like a space adventure.',
        f"Tell a gentle friendship story where {captain.label} and {friend.label} pretend to be a space crew, a noisy problem appears, and {friend.label}'s job as {profession.label} saves the mission.",
        f"Write a child-facing story with sound effects like {problem.sound} where a proud captain learns to listen, apologizes, and still finishes {mission.goal.lower()}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    captain = f["captain"]
    friend = f["friend"]
    mission = f["mission"]
    problem = f["problem_cfg"]
    profession = f["profession_cfg"]
    tool = f["tool_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two friends, {captain.label} and {friend.label}, who turned {world.setting.place} into a pretend spaceship. They were trying to {mission.goal.lower()}.",
        ),
        (
            "What problem happened during the mission?",
            f"{problem.label.capitalize()} interrupted the game, and {problem.issue_line.lower()} That made the mission feel wobbly and urgent.",
        ),
        (
            f"Why did {friend.label} feel indignation?",
            f"{friend.label} felt indignation because {captain.label} brushed off {friend.pronoun('possessive')} profession and did not listen. That felt unfair, especially because {friend.pronoun('possessive')} job was exactly the one the mission needed.",
        ),
        (
            f"How was the problem solved?",
            f"{captain.label} apologized and asked {friend.label} to help. Then {friend.label} used {tool.phrase}, because a {profession.label} had the right skill for {problem.label}.",
        ),
        (
            "What changed by the end?",
            f"The mission was finished, and the friendship felt strong again. The ending shows that listening and apologizing mattered just as much as fixing the spaceship.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"profession", "friendship", "indignation"}
    tags |= set(world.facts["profession_cfg"].tags)
    tags |= set(world.facts["problem_cfg"].tags)
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            out.extend(KNOWLEDGE[key])
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
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *rest in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="bedroom",
        mission="moon_mail",
        problem="static",
        profession="signal_officer",
        tool="headset",
        captain_name="Nora",
        captain_gender="girl",
        friend_name="Max",
        friend_gender="boy",
        parent="mother",
    ),
    StoryParams(
        setting="backyard",
        mission="comet_rescue",
        problem="jammed_hatch",
        profession="space_mechanic",
        tool="wrench",
        captain_name="Leo",
        captain_gender="boy",
        friend_name="Mia",
        friend_gender="girl",
        parent="father",
    ),
    StoryParams(
        setting="attic",
        mission="ring_picnic",
        problem="lost_route",
        profession="star_navigator",
        tool="star_map",
        captain_name="Ava",
        captain_gender="girl",
        friend_name="Finn",
        friend_gender="boy",
        parent="mother",
    ),
]


def explain_rejection(setting: Setting, mission: Mission, problem: Problem,
                      profession: Profession, tool: Tool) -> str:
    if not mission_supported(setting, mission):
        return (
            f"(No story: {mission.goal} does not fit {setting.place} in this tiny world. "
            f"Pick a mission that belongs in that setting.)"
        )
    if problem.need_skill != profession.skill:
        return (
            f"(No story: {problem.label} needs a {problem.need_skill} skill, but "
            f"{profession.label} uses {profession.skill}. Pick the matching profession.)"
        )
    if tool.skill != profession.skill:
        return (
            f"(No story: {tool.label} works for {tool.skill}, but {profession.label} uses "
            f"{profession.skill}. Pick the matching tool.)"
        )
    return "(No story: that combination is not supported.)"


ASP_RULES = r"""
mission_supported(S, M) :- setting(S), mission(M), affords(S, M).
skill_match(Pb, Pr, Tl) :- problem(Pb), profession(Pr), tool(Tl),
                           needs(Pb, K), has_skill(Pr, K), tool_skill(Tl, K).
valid(S, M, Pb, Pr, Tl) :- mission_supported(S, M), skill_match(Pb, Pr, Tl).

resolved(Pr, Tl, Pb) :- has_skill(Pr, K), tool_skill(Tl, K), needs(Pb, K).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        for mission_id in sorted(setting.afford_missions):
            lines.append(asp.fact("affords", setting_id, mission_id))
    for mission_id in MISSIONS:
        lines.append(asp.fact("mission", mission_id))
    for problem_id, problem in PROBLEMS.items():
        lines.append(asp.fact("problem", problem_id))
        lines.append(asp.fact("needs", problem_id, problem.need_skill))
    for profession_id, profession in PROFESSIONS.items():
        lines.append(asp.fact("profession", profession_id))
        lines.append(asp.fact("has_skill", profession_id, profession.skill))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("tool_skill", tool_id, tool.skill))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_resolved(problem_id: str, profession_id: str, tool_id: str) -> bool:
    import asp

    extra = "\n".join(
        [
            f"chosen_problem({problem_id}).",
            f"chosen_profession({profession_id}).",
            f"chosen_tool({tool_id}).",
            "ok :- chosen_problem(Pb), chosen_profession(Pr), chosen_tool(Tl), resolved(Pr, Tl, Pb).",
        ]
    )
    model = asp.one_model(asp_program(extra, "#show ok/0."))
    return bool(getattr(model, "symbols", lambda shown=True: [])(shown=True))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: valid_combos() matches ASP ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    for params in CURATED:
        py_ok = problem_match(PROBLEMS[params.problem], PROFESSIONS[params.profession], TOOLS[params.tool])
        asp_ok = asp_resolved(params.problem, params.profession, params.tool)
        if py_ok != asp_ok:
            rc = 1
            print(f"MISMATCH in resolved check for curated params: {params}")
            break
    else:
        print(f"OK: ASP resolution check matches Python on {len(CURATED)} curated stories.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during smoke test.")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test story generated and emitted.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: friends on a pretend space mission learn to listen to each other's professions."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--profession", choices=PROFESSIONS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from the ASP twin")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.mission and args.problem and args.profession and args.tool:
        setting = SETTINGS[args.setting]
        mission = MISSIONS[args.mission]
        problem = PROBLEMS[args.problem]
        profession = PROFESSIONS[args.profession]
        tool = TOOLS[args.tool]
        if not (mission_supported(setting, mission) and problem_match(problem, profession, tool)):
            raise StoryError(explain_rejection(setting, mission, problem, profession, tool))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.mission is None or combo[1] == args.mission)
        and (args.problem is None or combo[2] == args.problem)
        and (args.profession is None or combo[3] == args.profession)
        and (args.tool is None or combo[4] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, mission_id, problem_id, profession_id, tool_id = rng.choice(sorted(combos))
    captain_gender = rng.choice(["girl", "boy"])
    friend_gender = rng.choice(["girl", "boy"])
    captain_name = _pick_name(rng, captain_gender)
    friend_name = _pick_name(rng, friend_gender, avoid=captain_name)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        setting=setting_id,
        mission=mission_id,
        problem=problem_id,
        profession=profession_id,
        tool=tool_id,
        captain_name=captain_name,
        captain_gender=captain_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        mission = MISSIONS[params.mission]
        problem = PROBLEMS[params.problem]
        profession = PROFESSIONS[params.profession]
        tool = TOOLS[params.tool]
    except KeyError as err:
        raise StoryError(f"(No story: invalid parameter key {err!s}.)") from None

    if not mission_supported(setting, mission) or not problem_match(problem, profession, tool):
        raise StoryError(explain_rejection(setting, mission, problem, profession, tool))

    world = tell(
        setting=setting,
        mission=mission,
        problem=problem,
        profession=profession,
        tool=tool,
        captain_name=params.captain_name,
        captain_gender=params.captain_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        parent_type=params.parent,
    )

    captain = world.facts["captain"]
    friend = world.facts["friend"]

    story_text = world.render()
    story_text = story_text.replace("captain", captain.label).replace("friend", friend.label)

    return StorySample(
        params=params,
        story=story_text,
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
        print(asp_program("", "#show valid/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (setting, mission, problem, profession, tool) combos:\n")
        for item in combos:
            print("  " + " ".join(f"{part:14}" for part in item))
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
                f"### {p.captain_name} and {p.friend_name}: {p.problem} on {p.mission} "
                f"({p.profession}, {p.tool})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

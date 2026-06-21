#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/illustrator_dialogue_quest_superhero_story.py
========================================================================

A standalone story world about a small superhero quest. A child hero and an
illustrator friend hear a neighborhood call for help, face one sensible
obstacle, and solve it with the right tool. The illustrator's sketch matters:
when the hero listens early, the quest goes smoothly; when the hero rushes, the
pair has a wobble, then recovers by trusting the drawing and each other.

Run it
------
    python storyworlds/worlds/gpt-5.4/illustrator_dialogue_quest_superhero_story.py
    python storyworlds/worlds/gpt-5.4/illustrator_dialogue_quest_superhero_story.py --quest library_key --obstacle dark_tunnel --tool lantern_visor
    python storyworlds/worlds/gpt-5.4/illustrator_dialogue_quest_superhero_story.py --obstacle high_wall --tool lantern_visor
    python storyworlds/worlds/gpt-5.4/illustrator_dialogue_quest_superhero_story.py --all
    python storyworlds/worlds/gpt-5.4/illustrator_dialogue_quest_superhero_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/illustrator_dialogue_quest_superhero_story.py --verify
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
from contextlib import redirect_stdout
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
class Quest:
    id: str
    item: str
    owner: str
    place: str
    call: str
    result_line: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    scene: str
    warning: str
    fail_step: str
    fix_line: str
    solved_by: str
    difficulty: int = 1
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    handles: set[str] = field(default_factory=set)
    action: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    quest: str
    obstacle: str
    tool: str
    hero_name: str
    hero_gender: str
    illustrator_name: str
    illustrator_gender: str
    parent: str
    style: str = "heed"
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


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_obstacle_worry(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    obstacle = world.entities.get("obstacle")
    if hero is None or obstacle is None:
        return out
    if obstacle.meters["blocked"] < THRESHOLD:
        return out
    sig = ("worry", obstacle.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["fear"] += 1
    hero.memes["bravery"] += 1
    out.append("__blocked__")
    return out


def _r_return_joy(world: World) -> list[str]:
    out: list[str] = []
    item = world.entities.get("item")
    hero = world.entities.get("hero")
    illustrator = world.entities.get("illustrator")
    if item is None or hero is None or illustrator is None:
        return out
    if item.meters["returned"] < THRESHOLD:
        return out
    sig = ("joy", item.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["relief"] += 1
    illustrator.memes["pride"] += 1
    world.get("city").memes["cheer"] += 1
    out.append("__returned__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="obstacle_worry", tag="emotional", apply=_r_obstacle_worry),
    Rule(name="return_joy", tag="emotional", apply=_r_return_joy),
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


QUESTS = {
    "library_key": Quest(
        id="library_key",
        item="the silver library key",
        owner="Ms. Vale",
        place="the rooftop reading tent",
        call="\"The reading tent is locked, and the little listeners are waiting!\"",
        result_line="Ms. Vale could open the rooftop reading tent before the first child yawned.",
        ending_image="Below them, story pages fluttered like tiny flags while children cheered from their blankets.",
        tags={"library", "key", "helping"},
    ),
    "clinic_bandages": Quest(
        id="clinic_bandages",
        item="the red bandage box",
        owner="Dr. Poppy",
        place="the puppy clinic on Lantern Lane",
        call="\"My puppy patients need their bandages before nap time!\"",
        result_line="Dr. Poppy could wrap every sleepy paw at the puppy clinic.",
        ending_image="Soon the clinic window glowed warm, and three patched-up puppies thumped their tails at the glass.",
        tags={"clinic", "bandage", "helping"},
    ),
    "garden_seeds": Quest(
        id="garden_seeds",
        item="the moonflower seed packet",
        owner="Mr. Reed",
        place="the glass garden dome",
        call="\"Without those seeds, the moonflower beds will stay empty tonight!\"",
        result_line="Mr. Reed could plant the moonflowers in the glass garden dome before dusk.",
        ending_image="By evening, the dome shone green and silver, and the first watering can made a soft shining arc.",
        tags={"garden", "seed", "helping"},
    ),
}

OBSTACLES = {
    "dark_tunnel": Obstacle(
        id="dark_tunnel",
        label="dark tunnel",
        scene="a tunnel under the tram tracks where the noon light vanished in two steps",
        warning="\"The shadows are thick in there,\"",
        fail_step="raced into the dark and almost missed the painted arrow on the wall",
        fix_line="\"Use the light first,\"",
        solved_by="light",
        difficulty=1,
        tags={"dark", "tunnel"},
    ),
    "high_wall": Obstacle(
        id="high_wall",
        label="high wall",
        scene="a tall brick wall with ivy shaking at the top",
        warning="\"That wall is too high for guessing,\"",
        fail_step="jumped for the first ledge and slid back down with dusty knees",
        fix_line="\"Climb with a plan,\"",
        solved_by="climb",
        difficulty=2,
        tags={"wall", "climb"},
    ),
    "wind_gap": Obstacle(
        id="wind_gap",
        label="wind gap",
        scene="a broken skywalk with a humming gap in the middle",
        warning="\"The wind is shoving hard across that space,\"",
        fail_step="ran toward the gap and skidded to a stop when the gusts shoved at the cape",
        fix_line="\"Glide on the wide gust, not the first gust,\"",
        solved_by="glide",
        difficulty=2,
        tags={"wind", "bridge"},
    ),
}

TOOLS = {
    "lantern_visor": Tool(
        id="lantern_visor",
        label="lantern visor",
        phrase="a blue lantern visor",
        handles={"dark_tunnel"},
        action="clicked on the lantern visor, and a clean golden beam painted the floor all the way ahead",
        tags={"light", "superhero_gear"},
    ),
    "grip_gloves": Tool(
        id="grip_gloves",
        label="grip gloves",
        phrase="a pair of grip gloves",
        handles={"high_wall"},
        action="pressed the grip gloves to the bricks, and the gloves held fast while careful feet climbed after them",
        tags={"climb", "superhero_gear"},
    ),
    "glide_cape": Tool(
        id="glide_cape",
        label="glide cape",
        phrase="a silver glide cape",
        handles={"wind_gap"},
        action="spread the glide cape wide, caught the steady gust, and sailed over the gap in one smooth shining arc",
        tags={"glide", "superhero_gear"},
    ),
}

GIRL_NAMES = ["Nova", "Mia", "Zuri", "Lena", "Ruby", "Ava", "Nora", "Ivy"]
BOY_NAMES = ["Max", "Leo", "Finn", "Theo", "Eli", "Kai", "Noah", "Jude"]
TRAITS = ["heed", "rush"]


def tool_works(tool: Tool, obstacle: Obstacle) -> bool:
    return obstacle.id in tool.handles


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for qid in QUESTS:
        for oid, obstacle in OBSTACLES.items():
            for tid, tool in TOOLS.items():
                if tool_works(tool, obstacle):
                    combos.append((qid, oid, tid))
    return combos


def outcome_of(params: StoryParams) -> str:
    obstacle = OBSTACLES[params.obstacle]
    tool = TOOLS[params.tool]
    if not tool_works(tool, obstacle):
        return "impossible"
    return "smooth" if params.style == "heed" else "late"


def predict_path(world: World, obstacle_id: str, tool_id: str) -> dict:
    sim = world.copy()
    sim.facts["listening"] = True
    obstacle = sim.get("obstacle")
    tool = sim.get("tool")
    use_tool(sim, tool, obstacle, narrate=False)
    return {
        "cleared": obstacle.meters["blocked"] < THRESHOLD,
        "fear": sim.get("hero").memes["fear"],
    }


def introduce(world: World, hero: Entity, illustrator: Entity) -> None:
    hero.memes["bravery"] += 1
    illustrator.memes["care"] += 1
    world.say(
        f"In Brightblock City, {hero.id} liked to call {hero.pronoun('object')}self Star Sprint, "
        f"because every ordinary street looked like the start of an adventure."
    )
    world.say(
        f"{illustrator.id} was {hero.id}'s best friend and the best illustrator on the block. "
        f"When other children saw sidewalks, {illustrator.pronoun()} saw posters, maps, and secret arrows hiding in plain sight."
    )


def call_for_help(world: World, hero: Entity, illustrator: Entity, quest: Quest) -> None:
    hero.memes["duty"] += 1
    world.say(
        f"After lunch, the cloud-bell on City Hall flashed a silver star. "
        f"That meant somebody nearby needed help."
    )
    world.say(
        f"{hero.id} pointed at the sky. \"A quest!\" {hero.pronoun()} cried."
    )
    world.say(
        f"At the bottom of the bell, a paper message twirled down: {quest.call}"
    )
    world.say(
        f"\"Then we have to carry {quest.item} back to {quest.owner} at {quest.place},\" "
        f"said {illustrator.id}."
    )


def plan(world: World, hero: Entity, illustrator: Entity, quest: Quest, obstacle: Obstacle, tool: Tool) -> None:
    pred = predict_path(world, obstacle.id, tool.id)
    world.facts["predicted_clear"] = pred["cleared"]
    illustrator.memes["focus"] += 1
    world.say(
        f"{illustrator.id} knelt on the curb, pulled a pencil from {illustrator.pronoun('possessive')} pocket, "
        f"and drew a fast superhero route card."
    )
    world.say(
        f"On the card, {illustrator.pronoun()} sketched {obstacle.scene}, then circled {tool.label} with a bright looping line."
    )
    world.say(
        f'{obstacle.warning} {illustrator.id} said. "{tool.label.capitalize()} is the right answer."'
    )


def choose_approach(world: World, hero: Entity, illustrator: Entity, style: str) -> None:
    if style == "heed":
        world.facts["listening"] = True
        hero.memes["trust"] += 1
        world.say(
            f"\"Got it,\" said {hero.id}. {hero.pronoun().capitalize()} tucked the route card inside "
            f"{hero.pronoun('possessive')} belt and nodded like a real team captain."
        )
    else:
        world.facts["listening"] = False
        hero.memes["impulse"] += 1
        world.say(
            f"\"We don't have one second to waste!\" said {hero.id}."
        )
        world.say(
            f"{illustrator.id} held up the card, but {hero.id} was already running, cape bouncing behind {hero.pronoun('object')}."
        )


def approach_obstacle(world: World, hero: Entity, illustrator: Entity, obstacle: Obstacle) -> None:
    obstacle_ent = world.get("obstacle")
    obstacle_ent.meters["blocked"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Soon they reached {obstacle.scene}. The way to the lost package stopped there."
    )


def stumble(world: World, hero: Entity, illustrator: Entity, obstacle: Obstacle) -> None:
    hero.memes["fear"] += 1
    hero.meters["delay"] += 1
    world.say(
        f"{hero.id} {obstacle.fail_step}."
    )
    world.say(
        f"\"Whoa,\" {hero.pronoun()} said, taking one careful breath instead of another wild one."
    )
    world.say(
        f"{illustrator.id} caught up and opened the route card again. \"{obstacle.fix_line}\" {illustrator.pronoun()} told {hero.pronoun('object')}."
    )
    world.facts["listening"] = True
    hero.memes["trust"] += 1


def use_tool(world: World, tool_ent: Entity, obstacle_ent: Entity, narrate: bool = True) -> None:
    obstacle_ent.meters["blocked"] = 0.0
    obstacle_ent.meters["cleared"] += 1
    hero = world.get("hero")
    hero.memes["confidence"] += 1
    if narrate:
        world.say(tool_ent.attrs["action"] + ".")


def recover_item(world: World, hero: Entity, illustrator: Entity, quest: Quest) -> None:
    item = world.get("item")
    item.meters["returned"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Beyond the obstacle, {quest.item} was waiting on a little ledge of sunlight as if it had been hoping for them."
    )
    world.say(
        f"{hero.id} scooped it up. \"Quest item secured!\" {hero.pronoun()} shouted."
    )
    world.say(
        f"\"And not one second too soon,\" said {illustrator.id} with a grin."
    )


def deliver(world: World, hero: Entity, illustrator: Entity, quest: Quest, style: str) -> None:
    if style == "late":
        world.say(
            f"They hurried the rest of the way, no longer rushing in the wrong direction but moving together, shoulder to shoulder."
        )
    world.say(
        f"When they reached {quest.place}, {quest.owner} clapped both hands. \"You found it!\""
    )
    world.say(quest.result_line)
    world.say(
        f"{illustrator.id} lifted the route card, now smudged at the corners. "
        f"\"A good drawing can be a kind of superpower too,\" {illustrator.pronoun()} said."
    )
    world.say(
        f"\"And listening is one too,\" said {hero.id}."
    )
    world.say(quest.ending_image)


def tell(
    quest: Quest,
    obstacle: Obstacle,
    tool: Tool,
    hero_name: str = "Nova",
    hero_gender: str = "girl",
    illustrator_name: str = "Max",
    illustrator_gender: str = "boy",
    parent_type: str = "mother",
    style: str = "heed",
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="hero"))
    illustrator = world.add(
        Entity(id="illustrator", kind="character", type=illustrator_gender, label=illustrator_name, role="illustrator")
    )
    world.add(Entity(id="city", type="city", label="Brightblock City"))
    world.add(Entity(id="obstacle", type="obstacle", label=obstacle.label, attrs={"solved_by": obstacle.solved_by}))
    world.add(Entity(id="tool", type="tool", label=tool.label, attrs={"action": tool.action}))
    world.add(Entity(id="item", type="item", label=quest.item))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent"))

    world.facts["hero_name"] = hero_name
    world.facts["illustrator_name"] = illustrator_name

    introduce(world, hero, illustrator)
    call_for_help(world, hero, illustrator, quest)

    world.para()
    plan(world, hero, illustrator, quest, obstacle, tool)
    choose_approach(world, hero, illustrator, style)

    world.para()
    approach_obstacle(world, hero, illustrator, obstacle)
    if style == "rush":
        stumble(world, hero, illustrator, obstacle)
    use_tool(world, world.get("tool"), world.get("obstacle"))

    world.para()
    recover_item(world, hero, illustrator, quest)
    deliver(world, hero, illustrator, quest, "late" if style == "rush" else "smooth")

    world.facts.update(
        quest=quest,
        obstacle_cfg=obstacle,
        tool_cfg=tool,
        hero=hero,
        illustrator=illustrator,
        parent=parent,
        style="late" if style == "rush" else "smooth",
        delay=hero.meters["delay"],
        returned=world.get("item").meters["returned"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "illustrator": [
        (
            "What does an illustrator do?",
            "An illustrator makes pictures to help tell an idea or a story. A good drawing can show people where to look or what to do next.",
        )
    ],
    "quest": [
        (
            "What is a quest?",
            "A quest is a special trip with a goal at the end. Someone sets out to solve a problem, find something important, or help another person.",
        )
    ],
    "superhero_gear": [
        (
            "Why do superheroes use gear?",
            "Superhero gear helps with a hard job, like seeing in the dark or climbing safely. The best gear matches the problem instead of being picked at random.",
        )
    ],
    "dark": [
        (
            "Why is a dark tunnel hard to cross?",
            "A dark tunnel is hard to cross because you cannot see the floor, signs, or turns clearly. Good light helps you move safely and notice the right path.",
        )
    ],
    "wall": [
        (
            "Why is a high wall a problem?",
            "A high wall blocks the way because you cannot simply walk through it. You need a safe way to climb over it or go around it.",
        )
    ],
    "wind": [
        (
            "Why can strong wind be tricky?",
            "Strong wind can push your body or your clothes and change where you move. That is why people need to watch the wind carefully before jumping or gliding.",
        )
    ],
    "library": [
        (
            "Why do libraries need keys and helpers?",
            "Keys open doors so people can get to books and reading spaces. Helpers make sure everyone can still enjoy stories when something goes missing.",
        )
    ],
    "clinic": [
        (
            "Why do animal clinics use bandages?",
            "Bandages cover little hurts and help them stay clean while they heal. A clinic needs its supplies ready so it can help animals quickly.",
        )
    ],
    "garden": [
        (
            "What do seeds need to become flowers?",
            "Seeds need the right place, water, and time to grow. If gardeners get them planted on time, they can sprout into healthy flowers later.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "illustrator",
    "quest",
    "superhero_gear",
    "dark",
    "wall",
    "wind",
    "library",
    "clinic",
    "garden",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    quest = f["quest"]
    obstacle = f["obstacle_cfg"]
    tool = f["tool_cfg"]
    hero = f["hero"]
    illustrator = f["illustrator"]
    return [
        f'Write a short superhero story for a 3-to-5-year-old that includes the word "illustrator", a quest, and dialogue.',
        f"Tell a child-friendly superhero quest where {hero.label} teams up with {illustrator.label}, an illustrator, to return {quest.item} after facing a {obstacle.label}.",
        f"Write a gentle action story where the right tool is {tool.label}, the obstacle is {obstacle.label}, and the ending shows what changed in the city.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    illustrator = f["illustrator"]
    quest = f["quest"]
    obstacle = f["obstacle_cfg"]
    tool = f["tool_cfg"]
    outcome = f["style"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, who pretended to be a superhero, and {illustrator.label}, an illustrator friend. Together they answered a call for help in Brightblock City.",
        ),
        (
            "What was their quest?",
            f"Their quest was to carry {quest.item} back to {quest.owner} at {quest.place}. They hurried because someone was waiting and needed it soon.",
        ),
        (
            f"How did the illustrator help?",
            f"{illustrator.label} drew a route card and warned them about the {obstacle.label}. The drawing turned the problem into a plan, so the team knew which tool to trust.",
        ),
        (
            f"Why was {tool.label} the right tool?",
            f"It was the right tool because the trouble on this quest was {obstacle.label}. {tool.label.capitalize()} matched that exact problem instead of being a random gadget.",
        ),
    ]
    if outcome == "smooth":
        qa.append(
            (
                f"Did {hero.label} listen right away?",
                f"Yes. {hero.label} listened when {illustrator.label} explained the plan, so the team cleared the obstacle smoothly. Trusting the illustrator saved time on the quest.",
            )
        )
    else:
        qa.append(
            (
                f"What went wrong before the quest was solved?",
                f"{hero.label} rushed ahead before really listening and lost a little time at the {obstacle.label}. Then {illustrator.label} opened the route card again, and the team fixed the problem by following the plan.",
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the lost item safely returned and the neighborhood working again. {quest.ending_image}",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"illustrator", "quest"} | set(f["tool_cfg"].tags) | set(f["obstacle_cfg"].tags) | set(f["quest"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE.get(tag, []))
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
    hero_name = world.facts.get("hero_name", "Hero")
    illustrator_name = world.facts.get("illustrator_name", "Illustrator")
    lines = ["--- world model state ---"]
    for eid, ent in world.entities.items():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.kind == "character":
            display = hero_name if eid == "hero" else illustrator_name if eid == "illustrator" else ent.label
        else:
            display = ent.label or eid
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        if ent.role:
            bits.append(f"role={ent.role}")
        lines.append(f"  {display:14} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        quest="library_key",
        obstacle="dark_tunnel",
        tool="lantern_visor",
        hero_name="Nova",
        hero_gender="girl",
        illustrator_name="Max",
        illustrator_gender="boy",
        parent="mother",
        style="heed",
    ),
    StoryParams(
        quest="clinic_bandages",
        obstacle="high_wall",
        tool="grip_gloves",
        hero_name="Leo",
        hero_gender="boy",
        illustrator_name="Ruby",
        illustrator_gender="girl",
        parent="father",
        style="rush",
    ),
    StoryParams(
        quest="garden_seeds",
        obstacle="wind_gap",
        tool="glide_cape",
        hero_name="Ivy",
        hero_gender="girl",
        illustrator_name="Finn",
        illustrator_gender="boy",
        parent="mother",
        style="heed",
    ),
    StoryParams(
        quest="library_key",
        obstacle="high_wall",
        tool="grip_gloves",
        hero_name="Theo",
        hero_gender="boy",
        illustrator_name="Mia",
        illustrator_gender="girl",
        parent="father",
        style="rush",
    ),
]


def explain_rejection(obstacle: Obstacle, tool: Tool) -> str:
    return (
        f"(No story: {tool.label} is not a sensible answer to a {obstacle.label}. "
        f"This quest world only allows tools that actually solve the obstacle in front of the hero.)"
    )


ASP_RULES = r"""
works(T, O) :- handles(T, O).
valid(Q, O, T) :- quest(Q), obstacle(O), tool(T), works(T, O).

outcome(smooth) :- chosen_style(heed), chosen_tool(T), chosen_obstacle(O), works(T, O).
outcome(late)   :- chosen_style(rush), chosen_tool(T), chosen_obstacle(O), works(T, O).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for oid in OBSTACLES:
        lines.append(asp.fact("obstacle", oid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for oid in sorted(tool.handles):
            lines.append(asp.fact("handles", tid, oid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    style_atom = "heed" if params.style == "heed" else "rush"
    scenario = "\n".join(
        [
            asp.fact("chosen_tool", params.tool),
            asp.fact("chosen_obstacle", params.obstacle),
            asp.fact("chosen_style", style_atom),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

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
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        buf = io.StringIO()
        with redirect_stdout(buf):
            emit(sample, trace=True, qa=True, header="### smoke")
        if "illustrator" not in sample.story.lower():
            raise StoryError("smoke test story did not include required seed word")
        print("OK: smoke generate/emit passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a superhero quest with an illustrator friend. "
        "Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--style", choices=TRAITS, help="heed the illustrator at once, or rush first")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--hero-name")
    ap.add_argument("--illustrator-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--illustrator-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.obstacle and args.tool:
        obstacle = OBSTACLES[args.obstacle]
        tool = TOOLS[args.tool]
        if not tool_works(tool, obstacle):
            raise StoryError(explain_rejection(obstacle, tool))

    combos = [
        combo
        for combo in valid_combos()
        if (args.quest is None or combo[0] == args.quest)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    quest, obstacle, tool = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    illustrator_gender = args.illustrator_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or _pick_name(rng, hero_gender)
    illustrator_name = args.illustrator_name or _pick_name(rng, illustrator_gender, avoid=hero_name)
    parent = args.parent or rng.choice(["mother", "father"])
    style = args.style or rng.choice(TRAITS)

    return StoryParams(
        quest=quest,
        obstacle=obstacle,
        tool=tool,
        hero_name=hero_name,
        hero_gender=hero_gender,
        illustrator_name=illustrator_name,
        illustrator_gender=illustrator_gender,
        parent=parent,
        style=style,
    )


def _safe_lookup(table: dict, key: str, field: str):
    if key not in table:
        raise StoryError(f"(Unknown {field}: {key})")
    return table[key]


def generate(params: StoryParams) -> StorySample:
    quest = _safe_lookup(QUESTS, params.quest, "quest")
    obstacle = _safe_lookup(OBSTACLES, params.obstacle, "obstacle")
    tool = _safe_lookup(TOOLS, params.tool, "tool")
    if not tool_works(tool, obstacle):
        raise StoryError(explain_rejection(obstacle, tool))

    world = tell(
        quest=quest,
        obstacle=obstacle,
        tool=tool,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        illustrator_name=params.illustrator_name,
        illustrator_gender=params.illustrator_gender,
        parent_type=params.parent,
        style=params.style,
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
        print(f"{len(combos)} compatible (quest, obstacle, tool) combos:\n")
        for quest, obstacle, tool in combos:
            print(f"  {quest:16} {obstacle:12} {tool}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
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
            header = f"### {p.hero_name} + {p.illustrator_name}: {p.quest}, {p.obstacle}, {p.tool}, {outcome_of(p)}"
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

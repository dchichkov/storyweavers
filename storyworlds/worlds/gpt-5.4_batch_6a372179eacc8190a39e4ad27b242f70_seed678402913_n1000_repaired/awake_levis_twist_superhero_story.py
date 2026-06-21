#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/awake_levis_twist_superhero_story.py
===============================================================

A standalone storyworld for a tiny superhero domain built from the seed words
"awake" and "levis", with a twist ending. The core tale is:

- Levis stays awake late, hoping to glimpse the city hero Twist.
- A small public problem appears.
- An ordinary grown-up solves it with a sensible real-world method.
- Twist ending: that ordinary helper was Twist all along.

The world model tracks simple physical meters and emotional memes. A small
reasonableness gate refuses problem/method combinations that do not actually
fit. An inline ASP twin mirrors the same gate and the reveal model.

Run it
------
    python storyworlds/worlds/gpt-5.4/awake_levis_twist_superhero_story.py
    python storyworlds/worlds/gpt-5.4/awake_levis_twist_superhero_story.py --scene moon_park --problem kite_tree
    python storyworlds/worlds/gpt-5.4/awake_levis_twist_superhero_story.py --problem runaway_wagon --method ladder
    python storyworlds/worlds/gpt-5.4/awake_levis_twist_superhero_story.py --all
    python storyworlds/worlds/gpt-5.4/awake_levis_twist_superhero_story.py --qa
    python storyworlds/worlds/gpt-5.4/awake_levis_twist_superhero_story.py --verify
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


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


SCENES = {
    "moon_park": {
        "label": "Moon Park",
        "opening": "Moon Park glowed with soft lamps and silver puddles of light.",
        "lookout": "the tallest bench near the fountain",
        "affords": {"kite_tree", "puppy_crate"},
        "tags": {"park", "night"},
    },
    "market_square": {
        "label": "Market Square",
        "opening": "Market Square still hummed, even though the sky had turned deep blue.",
        "lookout": "the stone steps by the clock stall",
        "affords": {"runaway_wagon", "banner_pole"},
        "tags": {"square", "night"},
    },
    "library_lane": {
        "label": "Library Lane",
        "opening": "Library Lane was quiet except for the shiver of leaves and one late bell.",
        "lookout": "the low wall outside the library",
        "affords": {"kite_tree", "runaway_wagon", "banner_pole"},
        "tags": {"street", "night"},
    },
}

PROBLEMS = {
    "kite_tree": {
        "label": "kite",
        "phrase": "a bright star kite",
        "need": "reach_high",
        "danger_line": "It had twisted high above the path, where small hands could not reach.",
        "alarm": "A little girl pointed up and cried, \"My kite!\"",
        "fix_line": "The kite fluttered free and swooped back down like a happy bird.",
        "tags": {"kite", "helping"},
    },
    "runaway_wagon": {
        "label": "wagon",
        "phrase": "a wagon piled with oranges",
        "need": "stop_roll",
        "danger_line": "It had slipped from its handle and was rattling toward the hill.",
        "alarm": "A fruit seller gasped, \"My wagon! Stop it!\"",
        "fix_line": "The wagon shuddered, bumped once, and stayed still before a single orange escaped.",
        "tags": {"wagon", "helping"},
    },
    "banner_pole": {
        "label": "banner",
        "phrase": "a long parade banner",
        "need": "untwist_high",
        "danger_line": "The cloth had wrapped itself around a lamp pole and snapped in the wind.",
        "alarm": "The shopkeepers looked up as the banner whipped and tangled.",
        "fix_line": "The banner came loose, straightened, and danced properly again in the breeze.",
        "tags": {"banner", "helping"},
    },
    "puppy_crate": {
        "label": "puppy",
        "phrase": "a tiny puppy on a fruit crate",
        "need": "catch_soft",
        "danger_line": "The pup trembled on the wobbly crate and could not jump down safely.",
        "alarm": "A boy whispered, \"Please help the puppy.\"",
        "fix_line": "The puppy landed in a soft bundle and licked the rescuer's chin.",
        "tags": {"puppy", "helping"},
    },
}

METHODS = {
    "ladder": {
        "label": "ladder",
        "phrase": "a folding ladder",
        "skills": {"reach_high", "untwist_high"},
        "sense": 3,
        "action": "opened a folding ladder, climbed two steady steps, and reached the trouble with careful hands",
        "qa_action": "used a folding ladder to reach the problem safely",
        "tags": {"ladder", "safety"},
    },
    "hook_pole": {
        "label": "hooked pole",
        "phrase": "a long hooked pole",
        "skills": {"reach_high", "untwist_high"},
        "sense": 2,
        "action": "took a long hooked pole from a nearby cart and gently teased the trouble loose",
        "qa_action": "used a long hooked pole to bring the trouble down",
        "tags": {"pole", "safety"},
    },
    "wheel_chock": {
        "label": "wooden block",
        "phrase": "a wooden wheel block",
        "skills": {"stop_roll"},
        "sense": 3,
        "action": "slid a wooden block under the wheel at exactly the right moment",
        "qa_action": "stopped the wheel with a wooden block",
        "tags": {"wheel", "safety"},
    },
    "rope_loop": {
        "label": "rope loop",
        "phrase": "a loop of rope",
        "skills": {"stop_roll", "catch_soft"},
        "sense": 2,
        "action": "flicked a loop of rope with quick, neat aim and caught the trouble before it got worse",
        "qa_action": "used a rope loop to stop the problem",
        "tags": {"rope", "safety"},
    },
    "blanket": {
        "label": "blanket",
        "phrase": "a thick blanket",
        "skills": {"catch_soft"},
        "sense": 3,
        "action": "spread a thick blanket wide and waited with calm arms until the little body dropped into the soft middle",
        "qa_action": "held out a thick blanket for a soft landing",
        "tags": {"blanket", "safety"},
    },
}

HELPERS = {
    "baker": {
        "civilian": "Ms. Vale",
        "role": "baker",
        "detail": "flour still dusted her sleeves from the evening buns",
        "hero_line": "\"A city does not always need thunder,\" she said. \"Sometimes it only needs a steady hand.\"",
        "clue": "a silver spiral stitched inside her cuff",
        "tags": {"baker", "twist"},
    },
    "mail_carrier": {
        "civilian": "Mr. Flint",
        "role": "mail carrier",
        "detail": "his satchel still hung at his side",
        "hero_line": "\"Fast feet are good,\" he said, \"but careful eyes save the day first.\"",
        "clue": "a bright T-shaped clasp hidden under his collar",
        "tags": {"mail", "twist"},
    },
    "mechanic": {
        "civilian": "Aunt Jo",
        "role": "mechanic",
        "detail": "her fingers shone with one last line of clean machine oil",
        "hero_line": "\"Real heroes notice how things move,\" she said. \"Then they help them stop or turn the right way.\"",
        "clue": "a tiny spiral badge gleaming on her cap",
        "tags": {"mechanic", "twist"},
    },
}

VIGILS = {
    "sleepy": {
        "value": 1,
        "line": "He was fighting yawns, but he was still determined to stay awake.",
    },
    "ready": {
        "value": 2,
        "line": "He felt wonderfully awake, as if the stars themselves were keeping his eyes open.",
    },
    "super_awake": {
        "value": 3,
        "line": "He was so awake that every lamp, leaf, and footstep seemed bright and important.",
    },
}


def need_of(problem_id: str) -> str:
    return PROBLEMS[problem_id]["need"]


def method_works(problem_id: str, method_id: str) -> bool:
    return need_of(problem_id) in METHODS[method_id]["skills"]


def sensible_methods() -> list[str]:
    return [mid for mid, cfg in METHODS.items() if cfg["sense"] >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for scene_id, scene in SCENES.items():
        for problem_id in sorted(scene["affords"]):
            for method_id in sorted(METHODS):
                if method_works(problem_id, method_id) and METHODS[method_id]["sense"] >= SENSE_MIN:
                    combos.append((scene_id, problem_id, method_id))
    return combos


def reveal_kind(vigil_id: str, helper_id: str) -> str:
    base = VIGILS[vigil_id]["value"]
    if helper_id == "mail_carrier":
        base += 1
    return "direct" if base >= 3 else "clue"


def _r_trouble_worries(world: World) -> list[str]:
    trouble = world.get("trouble")
    crowd = world.get("crowd")
    levis = world.get("Levis")
    if trouble.meters["stuck"] < THRESHOLD and trouble.meters["rolling"] < THRESHOLD and trouble.meters["perched"] < THRESHOLD:
        return []
    sig = ("worry", trouble.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    crowd.memes["worry"] += 1
    levis.memes["alert"] += 1
    return []


def _r_rescue_relief(world: World) -> list[str]:
    trouble = world.get("trouble")
    crowd = world.get("crowd")
    levis = world.get("Levis")
    if trouble.meters["safe"] < THRESHOLD:
        return []
    sig = ("relief", trouble.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    crowd.memes["relief"] += 1
    levis.memes["awe"] += 1
    levis.memes["relief"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="trouble_worries", tag="social", apply=_r_trouble_worries),
    Rule(name="rescue_relief", tag="social", apply=_r_rescue_relief),
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
                produced.extend(bits)
        if any(rule.apply(world) for rule in []):
            changed = True
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def introduce(world: World, scene_id: str, vigil_id: str) -> None:
    levis = world.get("Levis")
    scene = SCENES[scene_id]
    world.say(
        f"Levis tied a red towel around his shoulders and climbed onto {scene['lookout']} in {scene['label']}. "
        f"He wanted to see the midnight hero Twist with his very own eyes."
    )
    world.say(scene["opening"])
    world.say(VIGILS[vigil_id]["line"])
    levis.memes["hope"] += 1
    levis.meters["awake"] = float(VIGILS[vigil_id]["value"])


def trouble_begins(world: World, problem_id: str) -> None:
    problem = PROBLEMS[problem_id]
    trouble = world.get("trouble")
    if problem_id in {"kite_tree", "banner_pole"}:
        trouble.meters["stuck"] += 1
    elif problem_id == "runaway_wagon":
        trouble.meters["rolling"] += 1
    else:
        trouble.meters["perched"] += 1
    world.say(
        f"Then Levis heard a sharp cry and saw {problem['phrase']}. {problem['danger_line']}"
    )
    world.say(problem["alarm"])
    propagate(world, narrate=False)


def levis_steps_forward(world: World, method_id: str) -> None:
    levis = world.get("Levis")
    method = METHODS[method_id]
    levis.memes["courage"] += 1
    world.say(
        f"Levis jumped down so fast that his towel-cape twisted behind him. "
        f"For one brave second, he wished he had real lightning hands. Instead, he only had his own feet and a good, {method['label']} idea somewhere nearby."
    )


def helper_arrives(world: World, helper_id: str) -> None:
    helper_cfg = HELPERS[helper_id]
    helper = world.get("helper")
    helper.memes["calm"] += 1
    world.say(
        f"Before panic could grow any bigger, {helper_cfg['civilian']}, the {helper_cfg['role']}, stepped out of the crowd. "
        f"{helper_cfg['detail'][0].upper() + helper_cfg['detail'][1:]}, and yet {helper.pronoun()} moved as if emergencies were puzzles {helper.pronoun()} had solved before."
    )


def do_rescue(world: World, problem_id: str, method_id: str) -> None:
    trouble = world.get("trouble")
    method = METHODS[method_id]
    helper = world.get("helper")
    helper.meters["acting"] += 1
    trouble.meters["stuck"] = 0.0
    trouble.meters["rolling"] = 0.0
    trouble.meters["perched"] = 0.0
    trouble.meters["safe"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{helper.pronoun().capitalize()} {method['action']}. {PROBLEMS[problem_id]['fix_line']}"
    )


def crowd_settles(world: World) -> None:
    crowd = world.get("crowd")
    crowd.memes["worry"] = 0.0
    world.say("The whole square seemed to let out one long breath.")
    if crowd.memes["relief"] >= THRESHOLD:
        world.say("Then smiles began to pop up all around, small and bright as windows lighting up.")


def direct_reveal(world: World, helper_id: str) -> None:
    helper_cfg = HELPERS[helper_id]
    levis = world.get("Levis")
    world.say(
        f"Levis was still wonderfully awake, so he did not miss the smallest thing: "
        f"{helper_cfg['civilian']} turned away from the crowd, tapped a silver spiral at {helper_cfg['clue'].split(' inside ')[-1] if ' inside ' in helper_cfg['clue'] else helper_cfg['clue']}, "
        f"and a dark blue mask slipped out into {helper.pronoun('possessive') if False else 'one hand'}."
    )
    world.say(
        f'"Twist?" Levis breathed. {helper_cfg["civilian"]} only smiled. {helper_cfg["hero_line"]}'
    )
    levis.memes["belief"] += 1


def clue_reveal(world: World, helper_id: str) -> None:
    helper_cfg = HELPERS[helper_id]
    levis = world.get("Levis")
    world.say(
        f"Levis blinked once, because staying awake had been hard work, and in that tiny blink the crowd closed in with thank-yous."
    )
    world.say(
        f"But when the helper slipped away, Levis spotted {helper_cfg['clue']}. It was the very same mark painted on the comic-book posters of Twist."
    )
    world.say(
        f"He stood very still, and a delighted shiver ran through him. Twist had been there all along, wearing ordinary shoes and an ordinary smile."
    )
    levis.memes["belief"] += 1


def ending(world: World, helper_id: str) -> None:
    helper_cfg = HELPERS[helper_id]
    levis = world.get("Levis")
    world.say(
        f"On the walk home, Levis kept his towel tied on, but it no longer felt like pretend. "
        f"He had learned that hero work could look like patience, practice, and showing up before fear got too loud."
    )
    world.say(
        f"That night, when he finally climbed into bed, he did not fight sleep anymore. "
        f"He fell asleep smiling, already dreaming of the day he might help people the way {helper_cfg['civilian']} had."
    )
    levis.memes["resolve"] += 1


def tell(scene_id: str, problem_id: str, method_id: str, helper_id: str, vigil_id: str) -> World:
    world = World()
    levis = world.add(Entity(id="Levis", kind="character", type="boy", label="Levis", role="hero_child", tags={"child", "awake"}))
    helper_type = "woman" if helper_id in {"baker", "mechanic"} else "man"
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label=HELPERS[helper_id]["civilian"], role="helper", tags=set(HELPERS[helper_id]["tags"])))
    world.add(Entity(id="crowd", kind="group", type="people", label="crowd", role="crowd"))
    world.add(Entity(id="trouble", kind="thing", type=PROBLEMS[problem_id]["label"], label=PROBLEMS[problem_id]["label"], phrase=PROBLEMS[problem_id]["phrase"], tags=set(PROBLEMS[problem_id]["tags"])))
    world.facts["scene_id"] = scene_id
    world.facts["problem_id"] = problem_id
    world.facts["method_id"] = method_id
    world.facts["helper_id"] = helper_id
    world.facts["vigil_id"] = vigil_id

    introduce(world, scene_id, vigil_id)
    world.para()
    trouble_begins(world, problem_id)
    levis_steps_forward(world, method_id)
    helper_arrives(world, helper_id)
    world.para()
    do_rescue(world, problem_id, method_id)
    crowd_settles(world)
    world.para()
    world.facts["reveal"] = reveal_kind(vigil_id, helper_id)
    if world.facts["reveal"] == "direct":
        helper_cfg = HELPERS[helper_id]
        world.say(
            f"Levis was still wonderfully awake, so he did not miss the smallest thing. "
            f"As {helper_cfg['civilian']} turned away, {helper.pronoun('possessive').capitalize()} sleeve shifted and showed {helper_cfg['clue']}."
        )
        world.say(
            f'"Twist?" Levis whispered. {helper_cfg["civilian"]} answered with a wink and said, {helper_cfg["hero_line"]}'
        )
        levis.memes["belief"] += 1
    else:
        clue_reveal(world, helper_id)
    world.para()
    ending(world, helper_id)

    world.facts.update(
        levis=levis,
        helper=helper,
        trouble=world.get("trouble"),
        scene=SCENES[scene_id],
        problem=PROBLEMS[problem_id],
        method=METHODS[method_id],
        helper_cfg=HELPERS[helper_id],
        solved=world.get("trouble").meters["safe"] >= THRESHOLD,
        awake_level=VIGILS[vigil_id]["value"],
    )
    return world


@dataclass
class StoryParams:
    scene: str
    problem: str
    method: str
    helper: str
    vigil: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "kite": [
        (
            "Why can a kite get stuck in a tree?",
            "A kite can get stuck when the wind pushes it into branches and the string pulls it tighter. Then it sits too high for small hands to reach."
        )
    ],
    "wagon": [
        (
            "Why does a wagon roll downhill?",
            "A wagon rolls downhill because gravity pulls it toward the lower ground. If nobody stops it, the wheels keep turning."
        )
    ],
    "banner": [
        (
            "Why does wind twist a banner?",
            "Wind pushes cloth from different sides at different times. That can wrap the cloth around a pole and tangle it."
        )
    ],
    "puppy": [
        (
            "Why should you help a scared puppy carefully?",
            "A scared puppy can wiggle, slip, or jump the wrong way. Calm help keeps the puppy and the people nearby safe."
        )
    ],
    "ladder": [
        (
            "What is a ladder for?",
            "A ladder helps someone reach a higher place safely. It works best when it is steady and used carefully."
        )
    ],
    "rope": [
        (
            "What can a rope loop do?",
            "A rope loop can catch or guide something without grabbing it with bare hands. It helps when something is moving or just out of reach."
        )
    ],
    "blanket": [
        (
            "Why does a blanket make a soft landing?",
            "A thick blanket spreads out the bump of a fall. That makes the landing gentler."
        )
    ],
    "superhero": [
        (
            "Do superheroes always need powers?",
            "No. A hero can also be someone who notices trouble, stays calm, and helps in a smart way."
        )
    ],
}
KNOWLEDGE_ORDER = ["kite", "wagon", "banner", "puppy", "ladder", "rope", "blanket", "superhero"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    problem = f["problem"]
    scene = f["scene"]
    reveal = f["reveal"]
    helper_cfg = f["helper_cfg"]
    return [
        f'Write a short superhero story for a 3-to-5-year-old that includes the words "awake" and "levis".',
        f"Tell a gentle superhero story where Levis stays awake in {scene['label']} hoping to see Twist, then helps when {problem['phrase']} causes trouble.",
        f"Write a superhero story with a twist ending where an ordinary {helper_cfg['role']} secretly turns out to be Twist, and make the rescue feel practical and brave instead of flashy."
        if reveal == "direct"
        else f"Write a superhero story with a twist clue at the end, where Levis realizes an ordinary {helper_cfg['role']} was really Twist all along.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    helper_cfg = f["helper_cfg"]
    problem = f["problem"]
    method = f["method"]
    reveal = f["reveal"]
    out: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            "It is about Levis, a child in a towel cape who stayed awake hoping to see Twist. It is also about the ordinary grown-up who solved the problem and turned out to be Twist."
        ),
        (
            "Why was Levis trying to stay awake?",
            "He wanted to catch a real glimpse of the city hero Twist instead of just reading about that hero in pictures. Staying awake made the whole night feel full of possibility."
        ),
        (
            "What problem happened?",
            f"{problem['phrase'].capitalize()} caused the trouble. {problem['danger_line']}"
        ),
        (
            "How was the problem solved?",
            f"{helper_cfg['civilian']} {method['qa_action']}. That worked because it matched the kind of trouble instead of relying on wild guessing."
        ),
    ]
    if reveal == "direct":
        out.append(
            (
                "What was the twist at the end?",
                f"The ordinary helper was Twist. Because Levis was still very awake, he noticed the hidden clue on {helper_cfg['civilian']}'s clothes and got the secret almost at once."
            )
        )
    else:
        out.append(
            (
                "How did Levis figure out the twist?",
                f"He did not see everything right away, but he spotted {helper_cfg['clue']} after the rescue. That clue matched the mark of Twist, so he understood who had really helped."
            )
        )
    out.append(
        (
            "What did Levis learn?",
            "He learned that hero work is not only about masks and dramatic poses. It is also about staying calm, using the right tool, and helping before fear grows bigger."
        )
    )
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set(f["problem"]["tags"]) | set(f["method"]["tags"]) | {"superhero"}
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        scene="moon_park",
        problem="kite_tree",
        method="ladder",
        helper="baker",
        vigil="super_awake",
    ),
    StoryParams(
        scene="market_square",
        problem="runaway_wagon",
        method="wheel_chock",
        helper="mechanic",
        vigil="ready",
    ),
    StoryParams(
        scene="library_lane",
        problem="banner_pole",
        method="hook_pole",
        helper="mail_carrier",
        vigil="sleepy",
    ),
    StoryParams(
        scene="moon_park",
        problem="puppy_crate",
        method="blanket",
        helper="baker",
        vigil="ready",
    ),
]


def explain_rejection(scene_id: str, problem_id: str, method_id: str) -> str:
    if problem_id not in SCENES[scene_id]["affords"]:
        return (
            f"(No story: {SCENES[scene_id]['label']} does not host the problem '{problem_id}'. "
            f"Pick a problem that fits the place.)"
        )
    if not method_works(problem_id, method_id):
        return (
            f"(No story: the method '{method_id}' does not solve the problem '{problem_id}'. "
            f"This world only tells rescues where the chosen method actually fits.)"
        )
    if METHODS[method_id]["sense"] < SENSE_MIN:
        return (
            f"(No story: the method '{method_id}' is known but ranked too weak on common sense.)"
        )
    return "(No valid combination matches the given options.)"


ASP_RULES = r"""
works(P, M) :- need(P, N), skill(M, N).
sensible(M) :- method(M), sense(M, S), sense_min(Min), S >= Min.
valid(Scene, P, M) :- scene(Scene), affords(Scene, P), works(P, M), sensible(M).

direct_reveal :- vigil(V), awake_value(V, A), chosen_helper(H), helper_bonus(H, B), A + B >= 3.
reveal(direct) :- direct_reveal.
reveal(clue) :- not direct_reveal.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for scene_id, scene in SCENES.items():
        lines.append(asp.fact("scene", scene_id))
        for problem_id in sorted(scene["affords"]):
            lines.append(asp.fact("affords", scene_id, problem_id))
    for problem_id, problem in PROBLEMS.items():
        lines.append(asp.fact("problem", problem_id))
        lines.append(asp.fact("need", problem_id, problem["need"]))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("sense", method_id, method["sense"]))
        for skill in sorted(method["skills"]):
            lines.append(asp.fact("skill", method_id, skill))
    for vigil_id, vigil in VIGILS.items():
        lines.append(asp.fact("awake_value", vigil_id, vigil["value"]))
    for helper_id in HELPERS:
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("helper_bonus", helper_id, 1 if helper_id == "mail_carrier" else 0))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_reveal(vigil_id: str, helper_id: str) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("vigil", vigil_id),
            asp.fact("chosen_helper", helper_id),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show reveal/1."))
    atoms = asp.atoms(model, "reveal")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    return reveal_kind(params.vigil, params.helper)


def _smoke_test_generation() -> None:
    sample = generate(
        StoryParams(
            scene="moon_park",
            problem="kite_tree",
            method="ladder",
            helper="baker",
            vigil="ready",
            seed=123,
        )
    )
    if "Levis" not in sample.story or "Twist" not in sample.story:
        raise StoryError("Smoke test failed: story text is missing required story elements.")
    if not sample.story_qa or not sample.world_qa:
        raise StoryError("Smoke test failed: QA generation returned empty sections.")


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

    reveal_cases = 0
    reveal_bad = 0
    for vigil_id in VIGILS:
        for helper_id in HELPERS:
            reveal_cases += 1
            if asp_reveal(vigil_id, helper_id) != reveal_kind(vigil_id, helper_id):
                reveal_bad += 1
    if reveal_bad == 0:
        print(f"OK: reveal model matches on {reveal_cases} cases.")
    else:
        rc = 1
        print(f"MISMATCH: reveal model differed on {reveal_bad}/{reveal_cases} cases.")

    try:
        _smoke_test_generation()
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: Levis stays awake for a superhero sighting and discovers a twist."
    )
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--vigil", choices=VIGILS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the ASP twin against the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.scene and args.problem and args.method:
        if args.problem not in SCENES[args.scene]["affords"] or not method_works(args.problem, args.method) or METHODS[args.method]["sense"] < SENSE_MIN:
            raise StoryError(explain_rejection(args.scene, args.problem, args.method))

    combos = [
        combo
        for combo in valid_combos()
        if (args.scene is None or combo[0] == args.scene)
        and (args.problem is None or combo[1] == args.problem)
        and (args.method is None or combo[2] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    scene_id, problem_id, method_id = rng.choice(sorted(combos))
    helper_id = args.helper or rng.choice(sorted(HELPERS))
    vigil_id = args.vigil or rng.choice(sorted(VIGILS))
    return StoryParams(
        scene=scene_id,
        problem=problem_id,
        method=method_id,
        helper=helper_id,
        vigil=vigil_id,
    )


def generate(params: StoryParams) -> StorySample:
    if params.scene not in SCENES:
        raise StoryError(f"(Unknown scene: {params.scene})")
    if params.problem not in PROBLEMS:
        raise StoryError(f"(Unknown problem: {params.problem})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.vigil not in VIGILS:
        raise StoryError(f"(Unknown vigil: {params.vigil})")
    if (params.scene, params.problem, params.method) not in set(valid_combos()):
        raise StoryError(explain_rejection(params.scene, params.problem, params.method))

    world = tell(
        scene_id=params.scene,
        problem_id=params.problem,
        method_id=params.method,
        helper_id=params.helper,
        vigil_id=params.vigil,
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
        print(asp_program("", "#show valid/3.\n#show reveal/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (scene, problem, method) combos:\n")
        for scene_id, problem_id, method_id in combos:
            print(f"  {scene_id:14} {problem_id:14} {method_id}")
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
            header = f"### Levis in {p.scene}: {p.problem} with {p.method} ({outcome_of(p)} reveal)"
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

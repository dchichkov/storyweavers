#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/commando_fisted_humor_teamwork_surprise_rhyming_story.py
===================================================================================

A standalone storyworld for playful, rhyming rescue stories built from the seed
words "commando" and "fisted", with humor, teamwork, and a surprise ending.

Premise
-------
Two children turn a small mishap into a make-believe rescue mission. Something
they care about gets stuck in a silly place. One child first tries a rough or
lonely fix, which does not work. Then the pair choose a teamwork plan that
actually fits the place and the object. Together they succeed, and the rescued
thing brings an extra surprise.

World logic
-----------
A scene has physical needs: light+reach, height+catch, or climb+steady.
A rescue plan is only reasonable when it:
- provides every need the scene demands,
- has enough strength for the target,
- is gentle enough for delicate targets,
- and passes a small common-sense gate.

That gate exists so the world refuses weak "poke it and hope" plans.

Run it
------
python storyworlds/worlds/gpt-5.4/commando_fisted_humor_teamwork_surprise_rhyming_story.py
python storyworlds/worlds/gpt-5.4/commando_fisted_humor_teamwork_surprise_rhyming_story.py --scene under_sofa --plan flashlight_grabber
python storyworlds/worlds/gpt-5.4/commando_fisted_humor_teamwork_surprise_rhyming_story.py --plan broom_poke
python storyworlds/worlds/gpt-5.4/commando_fisted_humor_teamwork_surprise_rhyming_story.py --all
python storyworlds/worlds/gpt-5.4/commando_fisted_humor_teamwork_surprise_rhyming_story.py --qa --json
python storyworlds/worlds/gpt-5.4/commando_fisted_humor_teamwork_surprise_rhyming_story.py --verify
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
class Scene:
    id: str
    place: str
    intro: str
    stuck_spot: str
    needs: set[str] = field(default_factory=set)
    silliness: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Target:
    id: str
    label: str
    phrase: str
    article: str
    strength_need: int = 1
    delicate: bool = False
    surprise_text: str = ""
    tags: set[str] = field(default_factory=set)

    @property
    def the(self) -> str:
        return f"the {self.label}"

    @property
    def The(self) -> str:
        return f"The {self.label}"


@dataclass
class Plan:
    id: str
    label: str
    phrase: str
    needs: set[str] = field(default_factory=set)
    sense: int = 2
    strength: int = 1
    gentle: bool = True
    role_a: str = ""
    role_b: str = ""
    setup_text: str = ""
    action_text: str = ""
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
        return [e for e in self.entities.values() if e.role in {"lead", "mate"}]

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


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    target = world.entities.get("target")
    if target is None or target.meters["stuck"] < THRESHOLD:
        return out
    sig = ("worry", "target")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["worry"] += 1
    out.append("__worry__")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    a = world.entities.get("lead")
    b = world.entities.get("mate")
    if a is None or b is None:
        return out
    if a.memes["assigned"] < THRESHOLD or b.memes["assigned"] < THRESHOLD:
        return out
    sig = ("teamwork", "kids")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    a.memes["teamwork"] += 1
    b.memes["teamwork"] += 1
    out.append("__teamwork__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    target = world.entities.get("target")
    if target is None or target.meters["rescued"] < THRESHOLD:
        return out
    sig = ("relief", "kids")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["worry"] = 0.0
        kid.memes["joy"] += 1
        kid.memes["relief"] += 1
    out.append("__relief__")
    return out


CAUSAL_RULES = [
    Rule(name="worry", tag="emotion", apply=_r_worry),
    Rule(name="teamwork", tag="social", apply=_r_teamwork),
    Rule(name="relief", tag="emotion", apply=_r_relief),
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


def scene_needs_met(scene: Scene, plan: Plan) -> bool:
    return set(scene.needs).issubset(plan.needs)


def plan_is_reasonable(scene: Scene, target: Target, plan: Plan) -> bool:
    if plan.sense < SENSE_MIN:
        return False
    if not scene_needs_met(scene, plan):
        return False
    if plan.strength < target.strength_need:
        return False
    if target.delicate and not plan.gentle:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for scene_id, scene in SCENES.items():
        for target_id, target in TARGETS.items():
            for plan_id, plan in PLANS.items():
                if plan_is_reasonable(scene, target, plan):
                    combos.append((scene_id, target_id, plan_id))
    return combos


def explain_plan_rejection(scene: Scene, target: Target, plan: Plan) -> str:
    if plan.sense < SENSE_MIN:
        return (
            f"(No story: the plan '{plan.label}' is too weak or too wild for this world. "
            f"A better rescue should use real teamwork, not just a random poke.)"
        )
    if not scene_needs_met(scene, plan):
        missing = sorted(scene.needs - plan.needs)
        return (
            f"(No story: rescuing something from {scene.place} needs {missing}, "
            f"but '{plan.label}' does not provide that.)"
        )
    if plan.strength < target.strength_need:
        return (
            f"(No story: {target.the} is too heavy for '{plan.label}'. "
            f"The plan needs more pulling or lifting power.)"
        )
    if target.delicate and not plan.gentle:
        return (
            f"(No story: {target.the} is delicate, and '{plan.label}' is too rough. "
            f"This rescue needs a gentler plan.)"
        )
    return "(No story: this rescue combination is unreasonable.)"


def predict_success(world: World, scene: Scene, target: Target, plan: Plan) -> dict:
    return {
        "works": plan_is_reasonable(scene, target, plan),
        "needs": sorted(scene.needs),
        "surprise": bool(target.surprise_text),
    }


def setup_play(world: World, a: Entity, b: Entity, scene: Scene) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"One bright afternoon, {a.id} and {b.id} made a commando game with a stripey scarf and a cardboard tube. "
        f'"Quiet feet, neat feet, rescue on the way!" they sang, and the room felt ready to play.'
    )
    world.say(
        f"They marched to {scene.place}, where {scene.intro} "
        f"The whole thing felt funny, and a little bit grand, like a drum in a marching band."
    )


def discover_problem(world: World, a: Entity, b: Entity, scene: Scene, target_ent: Entity, target_cfg: Target) -> None:
    target_ent.meters["stuck"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {b.id} gasped, for there in {scene.stuck_spot} sat {target_cfg.article} {target_cfg.label}. "
        f'"Oh crumbs and clatter, it truly is stuck! If we yank the wrong way, we may lose our luck."'
    )
    if scene.silliness:
        world.say(scene.silliness)


def solo_try(world: World, a: Entity, b: Entity, scene: Scene, target_cfg: Target) -> None:
    a.memes["bravery"] += 1
    a.memes["frustration"] += 1
    world.say(
        f'{a.id} made a tiny fisted pose and whispered, "I can do it alone." '
        f"But {a.pronoun()} stretched and scrunched and wiggled with a grunt, and only made the dust dance up front."
    )
    world.say(
        f'{b.id} giggled first, then shook {b.pronoun("possessive")} head. '
        f'"A mission this snug needs two minds, not one. Let\'s plan it with care, and then it\'ll be fun."'
    )


def assign_roles(world: World, a: Entity, b: Entity, plan: Plan) -> None:
    a.memes["assigned"] += 1
    b.memes["assigned"] += 1
    propagate(world, narrate=False)
    world.say(
        f"They picked {plan.phrase}. {a.id} would {plan.role_a}, and {b.id} would {plan.role_b}. "
        f"{plan.setup_text}"
    )


def execute_plan(world: World, a: Entity, b: Entity, scene: Scene, target_ent: Entity, target_cfg: Target, plan: Plan) -> None:
    works = plan_is_reasonable(scene, target_cfg, plan)
    world.facts["predicted_works"] = works
    if works:
        target_ent.meters["stuck"] = 0.0
        target_ent.meters["rescued"] += 1
        propagate(world, narrate=False)
        world.say(
            f"Then came the tug and the tap and the clever little clap: {plan.action_text} "
            f"Out slid {target_cfg.article} {target_cfg.label}, safe from the trap."
        )
    else:
        a.memes["frustration"] += 1
        b.memes["frustration"] += 1
        world.say(plan.fail_text)


def surprise_ending(world: World, a: Entity, b: Entity, target_cfg: Target) -> None:
    a.memes["surprise"] += 1
    b.memes["surprise"] += 1
    world.say(
        f"But rescue had one more twist to bring: {target_cfg.surprise_text} "
        f'{a.id} blinked, then laughed so hard {a.pronoun()} nearly sat on the rug.'
    )
    world.say(
        f'"So that was the prize inside the prize!" said {b.id}. '
        f"They bowed to each other, two teammates wise, and sang, "
        f'"When hands work together, small troubles grow light; a giggle can turn them bright."'
    )


def tell(
    scene: Scene,
    target_cfg: Target,
    plan: Plan,
    lead_name: str,
    lead_type: str,
    mate_name: str,
    mate_type: str,
) -> World:
    world = World()
    a = world.add(Entity(id="lead", kind="character", type=lead_type, label=lead_name, role="lead"))
    b = world.add(Entity(id="mate", kind="character", type=mate_type, label=mate_name, role="mate"))
    target_ent = world.add(Entity(id="target", kind="thing", type="target", label=target_cfg.label, phrase=target_cfg.phrase))

    setup_play(world, a, b, scene)
    world.para()
    discover_problem(world, a, b, scene, target_ent, target_cfg)
    solo_try(world, a, b, scene, target_cfg)
    world.para()
    assign_roles(world, a, b, plan)
    execute_plan(world, a, b, scene, target_ent, target_cfg, plan)
    if target_ent.meters["rescued"] >= THRESHOLD:
        world.para()
        surprise_ending(world, a, b, target_cfg)

    world.facts.update(
        scene=scene,
        target_cfg=target_cfg,
        plan=plan,
        lead=a,
        mate=b,
        target=target_ent,
        rescued=target_ent.meters["rescued"] >= THRESHOLD,
        teamwork=a.memes["teamwork"] >= THRESHOLD and b.memes["teamwork"] >= THRESHOLD,
        surprise=bool(target_cfg.surprise_text),
    )
    return world


SCENES = {
    "under_sofa": Scene(
        id="under_sofa",
        place="the living-room sofa",
        intro="a row of crayons had rolled away like runaway boats.",
        stuck_spot="the shadow under the sofa",
        needs={"light", "reach"},
        silliness="A sock bunny peeped from one side, and a dusty marble winked from the other.",
        tags={"sofa", "rescue"},
    ),
    "apple_tree": Scene(
        id="apple_tree",
        place="the apple tree in the yard",
        intro="the branches bobbed in the breeze like green umbrellas on parade.",
        stuck_spot="the fork of two springy branches",
        needs={"height", "catch"},
        silliness="A leaf landed on {mate}'s nose, and even the tree seemed to snicker.",
        tags={"tree", "rescue"},
    ),
    "laundry_hamper": Scene(
        id="laundry_hamper",
        place="the tall laundry hamper",
        intro="its mountain of shirts leaned this way and that like sleepy clouds.",
        stuck_spot="the deep clothy middle",
        needs={"climb", "steady"},
        silliness="One striped sock flopped over the rim like a flag for the silliest kingdom.",
        tags={"laundry", "rescue"},
    ),
}

TARGETS = {
    "robot": Target(
        id="robot",
        label="tin robot",
        phrase="a tin robot with red wheels",
        article="a",
        strength_need=1,
        delicate=False,
        surprise_text='when the little robot bumped the floor, its springy chest popped open and out fluttered a paper star that said, "TEAM OF THE DAY."',
        tags={"robot", "surprise_note"},
    ),
    "kite": Target(
        id="kite",
        label="paper kite",
        phrase="a paper kite with a tail of bows",
        article="a",
        strength_need=1,
        delicate=True,
        surprise_text="a hidden pocket in the tail burst into a puff of bright confetti, sprinkling their hair like party snow.",
        tags={"kite", "confetti"},
    ),
    "cookie_tin": Target(
        id="cookie_tin",
        label="round cookie tin",
        phrase="a round cookie tin with moon-blue paint",
        article="a",
        strength_need=2,
        delicate=False,
        surprise_text="the lid gave a happy plink and revealed one last cinnamon cookie wrapped in a napkin for sharing.",
        tags={"cookie", "share"},
    ),
}

PLANS = {
    "flashlight_grabber": Plan(
        id="flashlight_grabber",
        label="flashlight and grabber",
        phrase="a flashlight and a kitchen grabber",
        needs={"light", "reach"},
        sense=3,
        strength=1,
        gentle=True,
        role_a="shine the light low and slow",
        role_b="reach with the grabber, steady and neat",
        setup_text="Their whispers rhymed with their steps, and even the dust motes seemed to wait.",
        action_text="the beam held still, the grabber curled true, and together they nudged and lifted in one smooth swoop.",
        fail_text="The light bobbled, the grabber slipped, and the rescue stayed stuck in the shade.",
        qa_text="used a flashlight to see and a grabber to lift it out",
        tags={"flashlight", "grabber", "teamwork"},
    ),
    "stool_blanket": Plan(
        id="stool_blanket",
        label="stool and blanket",
        phrase="a little stool and a blanket held wide",
        needs={"height", "catch"},
        sense=3,
        strength=1,
        gentle=True,
        role_a="climb the stool with careful toes",
        role_b="hold the blanket open below",
        setup_text="One counted, one watched, and both kept their knees from wobbling.",
        action_text="up reached one friend, down waited the blanket, and the falling thing landed with a soft flump instead of a bump.",
        fail_text="The stool squeaked, the blanket drooped, and the rescue was still perched above.",
        qa_text="used a stool to reach up while the other held a blanket to catch it",
        tags={"stool", "blanket", "teamwork"},
    ),
    "chair_hold": Plan(
        id="chair_hold",
        label="chair-hold climb",
        phrase="a sturdy chair-hold climb",
        needs={"climb", "steady"},
        sense=3,
        strength=2,
        gentle=True,
        role_a="lean in and lift with both hands",
        role_b="brace the chair and the hamper so nothing slid",
        setup_text="They checked the chair feet, then checked them twice, because brave can still be nice.",
        action_text="one climbed just enough, one held everything firm, and the treasure rose up with hardly a squirm.",
        fail_text="The chair wobbled and the cloth slumped, so they wisely stepped back at once.",
        qa_text="had one child climb carefully while the other steadied everything",
        tags={"chair", "steady", "teamwork"},
    ),
    "broom_poke": Plan(
        id="broom_poke",
        label="broom poke",
        phrase="a broom poked from far away",
        needs={"reach"},
        sense=1,
        strength=1,
        gentle=False,
        role_a="jab with the broom",
        role_b="hope for the best",
        setup_text="It was the kind of idea that sounded big and thought very small.",
        action_text="the broom thumped and everything bounced about.",
        fail_text="They only stirred dust and chaos, and nothing was rescued at all.",
        qa_text="poked with a broom",
        tags={"broom"},
    ),
    "jump_and_snatch": Plan(
        id="jump_and_snatch",
        label="jump and snatch",
        phrase="a jumpy grab in the air",
        needs={"height"},
        sense=1,
        strength=1,
        gentle=False,
        role_a="jump",
        role_b="grab",
        setup_text="It was more bounce than brain.",
        action_text="they leapt and flapped and missed.",
        fail_text="The leap was too wild to count as a real plan.",
        qa_text="jumped and tried to snatch it",
        tags={"jump"},
    ),
}


GIRL_NAMES = ["Lila", "Mina", "Tess", "Nora", "Ivy", "Ruby", "Pia", "Zoe"]
BOY_NAMES = ["Bo", "Finn", "Milo", "Toby", "Ned", "Max", "Eli", "Theo"]


@dataclass
class StoryParams:
    scene: str
    target: str
    plan: str
    lead_name: str
    lead_type: str
    mate_name: str
    mate_type: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        scene="under_sofa",
        target="robot",
        plan="flashlight_grabber",
        lead_name="Lila",
        lead_type="girl",
        mate_name="Bo",
        mate_type="boy",
        seed=101,
    ),
    StoryParams(
        scene="apple_tree",
        target="kite",
        plan="stool_blanket",
        lead_name="Milo",
        lead_type="boy",
        mate_name="Tess",
        mate_type="girl",
        seed=102,
    ),
    StoryParams(
        scene="laundry_hamper",
        target="cookie_tin",
        plan="chair_hold",
        lead_name="Nora",
        lead_type="girl",
        mate_name="Finn",
        mate_type="boy",
        seed=103,
    ),
]


KNOWLEDGE = {
    "flashlight": [
        (
            "What does a flashlight do?",
            "A flashlight makes light so you can see in dark places. It helps you look without having to guess.",
        )
    ],
    "grabber": [
        (
            "What is a grabber tool?",
            "A grabber is a long tool with a pinching end. It helps you reach things that are too far away for your hand.",
        )
    ],
    "blanket": [
        (
            "Why might someone hold a blanket under a falling thing?",
            "A blanket can soften a fall. That helps catch something gently instead of letting it bump the ground.",
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork means people help each other do one job. One person can do one part while another does the next part.",
        )
    ],
    "gentle": [
        (
            "Why should you be gentle with a paper thing?",
            "Paper can tear or crumple easily. Gentle hands help keep it safe.",
        )
    ],
    "sharing": [
        (
            "Why is sharing a treat kind?",
            "Sharing lets more than one person enjoy something nice. It can make a happy surprise feel even happier.",
        )
    ],
}
KNOWLEDGE_ORDER = ["flashlight", "grabber", "blanket", "teamwork", "gentle", "sharing"]


def safe_lookup(mapping: dict, key: str, label: str):
    if key not in mapping:
        raise StoryError(f"(No story: unknown {label} '{key}'.)")
    return mapping[key]


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["lead"]
    b = f["mate"]
    scene = f["scene"]
    target = f["target_cfg"]
    return [
        f'Write a short rhyming story for a 3-to-5-year-old that includes the word "commando" and the word "fisted".',
        f"Tell a playful rescue story where {a.label} and {b.label} work together to get {target.article} {target.label} out of {scene.stuck_spot}, and end with a surprise.",
        f"Write a humorous teamwork story in rhyme where two children turn a small stuck problem into a grand pretend mission.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["lead"]
    b = f["mate"]
    scene = f["scene"]
    target = f["target_cfg"]
    plan = f["plan"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {a.label} and {b.label}, two children who turned a little problem into a make-believe rescue. They played a commando game and tried to help together.",
        ),
        (
            f"What got stuck, and where was it?",
            f"{target.article.capitalize()} {target.label} got stuck in {scene.stuck_spot}. That is why the children stopped playing and started planning.",
        ),
        (
            "Why did one child stop trying alone?",
            f"The first lonely try did not work, and it only made the moment sillier. The problem needed more than brave feelings; it needed two jobs done together.",
        ),
    ]
    if f.get("rescued"):
        qa.append(
            (
                "How did they rescue it?",
                f"They used {plan.phrase}. {a.label} and {b.label} split the job into two parts, and that teamwork is what made the rescue work.",
            )
        )
        qa.append(
            (
                "Why was teamwork important in this story?",
                f"The place where the object was stuck needed {', '.join(sorted(scene.needs))}, and one child could not do every part at once. By sharing the jobs, they stayed careful and solved the problem together.",
            )
        )
        qa.append(
            (
                "What was the surprise at the end?",
                f"{target.surprise_text[0].upper()}{target.surprise_text[1:]} The surprise made the ending feel funny and joyful after the tense rescue.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"teamwork"}
    plan = f["plan"]
    target = f["target_cfg"]
    if "flashlight" in plan.tags:
        tags.add("flashlight")
    if "grabber" in plan.tags:
        tags.add("grabber")
    if "blanket" in plan.tags:
        tags.add("blanket")
    if target.delicate:
        tags.add("gentle")
    if "share" in target.tags:
        tags.add("sharing")
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
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
need_met(S, P, N) :- scene_needs(S, N), provides(P, N).
all_needs_met(S, P) :- scene(S), plan(P), not missing_need(S, P).
missing_need(S, P) :- scene_needs(S, N), not provides(P, N).

strong_enough(T, P) :- target(T), plan(P), strength_need(T, Need), strength(P, Have), Have >= Need.
gentle_enough(T, P) :- target(T), not delicate(T), plan(P).
gentle_enough(T, P) :- target(T), delicate(T), gentle(P).

sensible(P) :- plan(P), sense(P, S), sense_min(M), S >= M.

valid(S, T, P) :- scene(S), target(T), plan(P), sensible(P),
                  all_needs_met(S, P), strong_enough(T, P), gentle_enough(T, P).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for scene_id, scene in SCENES.items():
        lines.append(asp.fact("scene", scene_id))
        for need in sorted(scene.needs):
            lines.append(asp.fact("scene_needs", scene_id, need))
    for target_id, target in TARGETS.items():
        lines.append(asp.fact("target", target_id))
        lines.append(asp.fact("strength_need", target_id, target.strength_need))
        if target.delicate:
            lines.append(asp.fact("delicate", target_id))
    for plan_id, plan in PLANS.items():
        lines.append(asp.fact("plan", plan_id))
        lines.append(asp.fact("sense", plan_id, plan.sense))
        lines.append(asp.fact("strength", plan_id, plan.strength))
        if plan.gentle:
            lines.append(asp.fact("gentle", plan_id))
        for need in sorted(plan.needs):
            lines.append(asp.fact("provides", plan_id, need))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in ASP:", sorted(cl - py))
        if py - cl:
            print("  only in Python:", sorted(py - cl))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Verify failed: generated empty story.)")
        print("OK: generate() smoke test passed.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming teamwork rescue stories with a commando game, a fisted pose, and a surprise ending."
    )
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--lead-name")
    ap.add_argument("--mate-name")
    ap.add_argument("--lead-type", choices=["girl", "boy"])
    ap.add_argument("--mate-type", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python gate")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.scene is not None:
        safe_lookup(SCENES, args.scene, "scene")
    if args.target is not None:
        safe_lookup(TARGETS, args.target, "target")
    if args.plan is not None:
        safe_lookup(PLANS, args.plan, "plan")

    if args.scene and args.target and args.plan:
        scene = SCENES[args.scene]
        target = TARGETS[args.target]
        plan = PLANS[args.plan]
        if not plan_is_reasonable(scene, target, plan):
            raise StoryError(explain_plan_rejection(scene, target, plan))

    combos = [
        combo
        for combo in valid_combos()
        if (args.scene is None or combo[0] == args.scene)
        and (args.target is None or combo[1] == args.target)
        and (args.plan is None or combo[2] == args.plan)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    scene_id, target_id, plan_id = rng.choice(sorted(combos))
    lead_type = args.lead_type or rng.choice(["girl", "boy"])
    mate_type = args.mate_type or rng.choice(["girl", "boy"])
    lead_name = args.lead_name or _pick_name(rng, lead_type)
    mate_name = args.mate_name or _pick_name(rng, mate_type, avoid=lead_name)
    return StoryParams(
        scene=scene_id,
        target=target_id,
        plan=plan_id,
        lead_name=lead_name,
        lead_type=lead_type,
        mate_name=mate_name,
        mate_type=mate_type,
    )


def _render_scene_silliness(world: World) -> None:
    scene = world.facts.get("scene")
    mate = world.facts.get("mate")
    if scene and mate and "{mate}" in scene.silliness:
        rendered = scene.silliness.replace("{mate}", mate.label)
        story = world.render().replace(scene.silliness, rendered)
        world.paragraphs = [paragraph.split(" ") for paragraph in story.split("\n\n")]


def generate(params: StoryParams) -> StorySample:
    scene = safe_lookup(SCENES, params.scene, "scene")
    target = safe_lookup(TARGETS, params.target, "target")
    plan = safe_lookup(PLANS, params.plan, "plan")
    if not plan_is_reasonable(scene, target, plan):
        raise StoryError(explain_plan_rejection(scene, target, plan))

    world = tell(
        scene=scene,
        target_cfg=target,
        plan=plan,
        lead_name=params.lead_name,
        lead_type=params.lead_type,
        mate_name=params.mate_name,
        mate_type=params.mate_type,
    )
    world.facts["lead"].label = params.lead_name
    world.facts["mate"].label = params.mate_name
    _render_scene_silliness(world)

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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (scene, target, plan) combos:\n")
        for scene_id, target_id, plan_id in combos:
            print(f"  {scene_id:14} {target_id:10} {plan_id}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.lead_name} & {p.mate_name}: {p.target} at {p.scene} with {p.plan}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

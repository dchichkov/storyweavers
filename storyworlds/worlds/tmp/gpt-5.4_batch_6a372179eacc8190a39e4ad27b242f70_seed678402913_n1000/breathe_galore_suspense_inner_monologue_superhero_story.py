#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/breathe_galore_suspense_inner_monologue_superhero_story.py
======================================================================================

A standalone storyworld for a tiny superhero domain built from the seed words
"breathe" and "galore", with suspense and inner monologue.

Core premise
------------
A young superhero-in-training hears a cry for help in a busy, decoration-filled
public scene. The place has color and motion galore, but something small and
important is stuck in a scary spot. The hero feels fear rise, pauses to think
inside their own head, remembers to breathe, and then chooses a fitting rescue
tool. Sometimes the hero can finish the rescue alone; sometimes asking a trusted
ally for help is the brave move that completes it.

This world is intentionally narrow:
- each scene only supports certain rescue problems;
- each problem requires specific rescue capabilities;
- each method has a common-sense score and limited power;
- an ally can add backup power when the rescue is a little too hard.

Run it
------
    python storyworlds/worlds/gpt-5.4/breathe_galore_suspense_inner_monologue_superhero_story.py
    python storyworlds/worlds/gpt-5.4/breathe_galore_suspense_inner_monologue_superhero_story.py --scene parade --problem ribbons --method rescue_snips
    python storyworlds/worlds/gpt-5.4/breathe_galore_suspense_inner_monologue_superhero_story.py --problem vent --method blind_grab
    python storyworlds/worlds/gpt-5.4/breathe_galore_suspense_inner_monologue_superhero_story.py --all
    python storyworlds/worlds/gpt-5.4/breathe_galore_suspense_inner_monologue_superhero_story.py --qa --json
    python storyworlds/worlds/gpt-5.4/breathe_galore_suspense_inner_monologue_superhero_story.py --verify
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
# from the nested world directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
SENSE_MIN = 2
BASE_NERVE = 2.0
STEADY_TRAITS = {"steady", "careful", "focused", "patient"}


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
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
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
class Scene:
    id: str
    label: str
    opening: str
    detail: str
    supports: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    target_label: str
    target_phrase: str
    cry: str
    spot: str
    danger_line: str
    need: set[str] = field(default_factory=set)
    severity: int = 1
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    phrase: str
    sense: int
    power: int
    provides: set[str] = field(default_factory=set)
    action: str = ""
    team_action: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Ally:
    id: str
    name: str
    type: str
    phrase: str
    boost: int
    comfort: str
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


def _r_stuck_scares(world: World) -> list[str]:
    target = world.entities.get("target")
    hero = world.entities.get("hero")
    if target is None or hero is None:
        return []
    if target.meters["stuck"] < THRESHOLD:
        return []
    sig = ("fear_from_stuck", target.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["fear"] += 1
    hero.memes["care"] += 1
    if "scene" in world.entities:
        world.get("scene").meters["danger"] += 1
    return ["__fear__"]


def _r_breathe_steadies(world: World) -> list[str]:
    hero = world.entities.get("hero")
    if hero is None:
        return []
    if hero.memes["breathed"] < THRESHOLD:
        return []
    sig = ("breathe_steadies", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["fear"] = max(0.0, hero.memes["fear"] - 1.0)
    hero.memes["focus"] += 1
    hero.memes["courage"] += 1
    return ["__calm__"]


def _r_rescue_relieves(world: World) -> list[str]:
    target = world.entities.get("target")
    hero = world.entities.get("hero")
    if target is None or hero is None:
        return []
    if target.meters["safe"] < THRESHOLD:
        return []
    sig = ("relief_after_rescue", target.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["relief"] += 1
    hero.memes["joy"] += 1
    if "ally" in world.entities:
        world.get("ally").memes["pride"] += 1
    return ["__relief__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="stuck_scares", tag="emotion", apply=_r_stuck_scares),
    Rule(name="breathe_steadies", tag="emotion", apply=_r_breathe_steadies),
    Rule(name="rescue_relieves", tag="emotion", apply=_r_rescue_relieves),
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


def problem_supported(scene: Scene, problem: Problem) -> bool:
    return problem.id in scene.supports


def method_fits(problem: Problem, method: Method) -> bool:
    return problem.need.issubset(method.provides)


def sensible_methods() -> list[Method]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def total_power(method: Method, ally: Ally) -> int:
    return method.power + ally.boost


def base_focus(trait: str) -> float:
    return 2.0 if trait in STEADY_TRAITS else 1.0


def can_solve(scene: Scene, problem: Problem, method: Method, ally: Ally) -> bool:
    return (
        problem_supported(scene, problem)
        and method_fits(problem, method)
        and method.sense >= SENSE_MIN
        and total_power(method, ally) >= problem.severity
    )


def outcome_of(params: "StoryParams") -> str:
    problem = PROBLEMS[params.problem]
    method = METHODS[params.method]
    ally = ALLIES[params.ally]
    return "solo" if method.power >= problem.severity else "team"


def predict_rescue(world: World, method_id: str, ally_id: str) -> dict:
    sim = world.copy()
    problem = sim.facts["problem_cfg"]
    method = METHODS[method_id]
    ally = ALLIES[ally_id]
    solved = total_power(method, ally) >= problem.severity and method_fits(problem, method)
    if solved:
        sim.get("target").meters["safe"] += 1
        sim.get("target").meters["stuck"] = 0.0
        propagate(sim, narrate=False)
    return {
        "solved": solved,
        "outcome": "solo" if method.power >= problem.severity else "team",
        "remaining_danger": sim.get("scene").meters["danger"],
    }


def introduce(world: World, hero: Entity, scene: Scene) -> None:
    world.say(
        f"{hero.id} wore a homemade cape and liked to imagine that being brave meant shining at exactly the right moment."
    )
    world.say(
        f"That afternoon, {scene.opening}. {scene.detail}"
    )


def hear_cry(world: World, hero: Entity, target: Entity, problem: Problem) -> None:
    target.meters["stuck"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then a small voice broke through the happy noise. {problem.cry}"
    )
    world.say(
        f"{hero.id} spun toward {problem.spot}, where {target.phrase} was stuck and couldn't get free."
    )


def suspense_beat(world: World, hero: Entity, problem: Problem) -> None:
    hero.memes["doubt"] += 1
    world.say(problem.danger_line)
    world.say(
        f"For one long second, {hero.id}'s stomach flipped. The world still had color galore, but now every flutter and clang seemed louder."
    )


def inner_monologue(world: World, hero: Entity, ally: Entity, trait: str) -> None:
    hero.memes["inner_voice"] += 1
    steady = trait in STEADY_TRAITS
    first = "I want to run, but that will not help." if steady else "What if I mess this up?"
    second = "Breathe. Look. Think." if steady else "Breathe, breathe. One brave step first."
    world.say(
        f'Inside {hero.pronoun("possessive")} head, {hero.id} told {hero.pronoun("object")}: "{first} {second}"'
    )
    hero.memes["breathed"] += 1
    hero.memes["courage"] += base_focus(trait)
    propagate(world, narrate=False)
    if ally.id != "Ally":
        world.say(
            f"{ally.id} was already hurrying over, and just seeing {ally.pronoun('object')} nearby made the moment feel a little less lonely."
        )


def choose_method(world: World, hero: Entity, method: Method) -> None:
    world.say(
        f"{hero.id} reached for {method.phrase}. It was the right tool for this kind of rescue, not just the fastest-looking one."
    )


def solo_rescue(world: World, hero: Entity, target: Entity, method: Method) -> None:
    hero.meters["effort"] += 1
    target.meters["safe"] += 1
    target.meters["stuck"] = 0.0
    world.get("scene").meters["danger"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"With a deep breath, {hero.id} {method.action}."
    )
    world.say(
        f"A tiny pause came next, so quiet it felt enormous. Then {target.label} was free."
    )


def team_rescue(world: World, hero: Entity, ally_ent: Entity, target: Entity,
                method: Method, ally: Ally) -> None:
    hero.meters["effort"] += 1
    ally_ent.meters["effort"] += 1
    target.meters["safe"] += 1
    target.meters["stuck"] = 0.0
    world.get("scene").meters["danger"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} started the rescue, but the job was just a little too hard for one pair of hands."
    )
    world.say(
        f'"{ally.comfort}" said {ally.id}. Together they {method.team_action}.'
    )
    world.say(
        f"The scary second stretched and stretched, and then it broke. {target.label} was safe."
    )


def comfort_and_lesson(world: World, hero: Entity, ally_ent: Entity, target: Entity,
                       ally: Ally, outcome: str) -> None:
    hero.memes["lesson"] += 1
    hero.memes["love"] += 1
    world.say(
        f"{target.label.capitalize()} trembled for a moment, then leaned right into {hero.id}."
    )
    if outcome == "solo":
        world.say(
            f'{ally.id} smiled at {hero.id}. "{ally.comfort} You listened to your brave thoughts instead of your scared ones."'
        )
    else:
        world.say(
            f'{ally.id} squeezed {hero.pronoun("possessive")} shoulder. "That was real hero work. You knew when to ask for help, and that made the rescue stronger."'
        )


def ending_image(world: World, hero: Entity, scene: Scene, target: Entity) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"Soon the noise of {scene.label} sounded cheerful again instead of sharp."
    )
    world.say(
        f"{target.label.capitalize()} stayed close beside {hero.id}, and the cape on {hero.pronoun('possessive')} back did not feel like pretend at all."
    )


def tell(scene: Scene, problem: Problem, method: Method, ally: Ally,
         hero_name: str = "Maya", hero_gender: str = "girl",
         hero_trait: str = "steady", delay: int = 0) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        label=hero_name,
        role="hero",
        traits=[hero_trait],
        tags={"hero"},
    ))
    ally_ent = world.add(Entity(
        id=ally.name,
        kind="character",
        type=ally.type,
        label=ally.name,
        phrase=ally.phrase,
        role="ally",
        tags=set(ally.tags),
    ))
    target = world.add(Entity(
        id="target",
        kind="character",
        type="animal" if "animal" in problem.tags else "child",
        label=problem.target_label,
        phrase=problem.target_phrase,
        role="target",
        tags=set(problem.tags),
    ))
    world.add(Entity(
        id="scene",
        kind="thing",
        type="scene",
        label=scene.label,
        tags=set(scene.tags),
    ))

    hero.memes["nerve"] = BASE_NERVE
    hero.memes["focus"] = base_focus(hero_trait)
    target.meters["risk"] = float(problem.severity + delay)

    world.facts.update(
        scene_cfg=scene,
        problem_cfg=problem,
        method_cfg=method,
        ally_cfg=ally,
        delay=delay,
    )

    introduce(world, hero, scene)
    world.para()
    hear_cry(world, hero, target, problem)
    suspense_beat(world, hero, problem)
    inner_monologue(world, hero, ally_ent, hero_trait)

    world.para()
    prediction = predict_rescue(world, method.id, ally.id)
    world.facts["predicted_solved"] = prediction["solved"]
    choose_method(world, hero, method)

    if method.power >= problem.severity:
        solo_rescue(world, hero, target, method)
        outcome = "solo"
    else:
        team_rescue(world, hero, ally_ent, target, method, ally)
        outcome = "team"

    world.para()
    comfort_and_lesson(world, hero, ally_ent, target, ally, outcome)
    ending_image(world, hero, scene, target)

    world.facts.update(
        hero=hero,
        ally=ally_ent,
        target=target,
        solved=target.meters["safe"] >= THRESHOLD,
        outcome=outcome,
        asked_help=outcome == "team",
    )
    return world


SCENES = {
    "parade": Scene(
        id="parade",
        label="the town parade",
        opening="the town parade was rolling down Main Street with drums, banners, and balloons galore",
        detail="Children waved from the sidewalk, and even the paper stars tied to the floats kept dancing in the wind.",
        supports={"ribbons", "ledge"},
        tags={"parade", "crowd"},
    ),
    "fair": Scene(
        id="fair",
        label="the school science fair",
        opening="the school science fair buzzed with posters, blinking projects, and inventions galore",
        detail="Every table seemed to hum or sparkle, and the whole gym felt busy enough to hide one important sound.",
        supports={"vent"},
        tags={"fair", "machines"},
    ),
    "market": Scene(
        id="market",
        label="the moonlight market",
        opening="the moonlight market glowed with lanterns, capes, and sweet buns galore",
        detail="Strings of little lights swayed overhead while neighbors talked in soft happy bursts.",
        supports={"ledge", "ribbons"},
        tags={"market", "lanterns"},
    ),
}

PROBLEMS = {
    "vent": Problem(
        id="vent",
        target_label="the kitten",
        target_phrase="a striped kitten with wide round eyes",
        cry='"Mew! Mew!" came a tiny cry from behind a rattly vent cover.',
        spot="the shadowy side of a humming project booth",
        danger_line="The vent shook each time the machine beside it buzzed, and the dark opening looked too small and too deep.",
        need={"light", "reach"},
        severity=2,
        tags={"animal", "kitten", "dark"},
    ),
    "ledge": Problem(
        id="ledge",
        target_label="the puppy",
        target_phrase="a little puppy with one paw slipping on the narrow ledge",
        cry='"Yip! Yip!" barked a puppy from high above the crowd.',
        spot="a narrow ledge over a striped awning",
        danger_line="Below the ledge, people were hurrying past and never looking up, and one gust of wind made the awning snap hard.",
        need={"height"},
        severity=2,
        tags={"animal", "puppy", "heights"},
    ),
    "ribbons": Problem(
        id="ribbons",
        target_label="the little girl",
        target_phrase="a little girl whose cape had been looped into fluttering parade ribbons",
        cry='"Help!" squeaked a little girl, stuck beside the float steps.',
        spot="a knot of shiny ribbons near the side of a float",
        danger_line="The ribbons were bright and pretty, but they had wrapped tight, and every tug made the knot worse.",
        need={"careful"},
        severity=1,
        tags={"child", "ribbons"},
    ),
}

METHODS = {
    "glow_grapple": Method(
        id="glow_grapple",
        label="glow grapple",
        phrase="the glow grapple clipped at the hero belt",
        sense=3,
        power=2,
        provides={"light", "reach"},
        action="snapped the bright line into place, lit the dark opening, and guided the kitten gently out",
        team_action="used the glowing line to light the space while guiding the little one free",
        qa_text="used the glow grapple to light the dark space and guide the trapped one out",
        tags={"tool", "light"},
    ),
    "sky_cape": Method(
        id="sky_cape",
        label="sky cape",
        phrase="the sky cape buckles across the shoulders",
        sense=3,
        power=2,
        provides={"height"},
        action="rose in one careful sweep, steadied in the wind, and lifted the puppy down against the hero's chest",
        team_action="rose to the ledge while the ally steadied the landing below",
        qa_text="used the sky cape to reach the high ledge and bring the stranded one down",
        tags={"cape", "flight"},
    ),
    "rescue_snips": Method(
        id="rescue_snips",
        label="rescue snips",
        phrase="the round-tipped rescue snips from the side pouch",
        sense=3,
        power=1,
        provides={"careful"},
        action="slipped the round tips into the knot and snipped the ribbon loops apart without nicking the cape at all",
        team_action="held the knot still while the ally eased the loops apart with the rescue snips",
        qa_text="used the rescue snips to cut the tight ribbon loops free",
        tags={"tool", "careful"},
    ),
    "blind_grab": Method(
        id="blind_grab",
        label="blind grab",
        phrase="a quick blind grab with no plan",
        sense=1,
        power=1,
        provides={"reach"},
        action="reached in without seeing and hoped for the best",
        team_action="grabbed wildly until something came loose",
        qa_text="grabbed without being able to see clearly",
        tags={"unsafe"},
    ),
    "hard_yank": Method(
        id="hard_yank",
        label="hard yank",
        phrase="a hard yank on whatever was tangled",
        sense=1,
        power=2,
        provides={"careful"},
        action="pulled at the knot as hard as possible",
        team_action="yanked the tangle together",
        qa_text="pulled hard on the tangle",
        tags={"unsafe"},
    ),
}

ALLIES = {
    "captain_ray": Ally(
        id="captain_ray",
        name="Captain Ray",
        type="man",
        phrase="the neighborhood hero Captain Ray",
        boost=1,
        comfort="Steady now. Brave first, fast second.",
        tags={"mentor"},
    ),
    "aunt_beacon": Ally(
        id="aunt_beacon",
        name="Aunt Beacon",
        type="aunt",
        phrase="Aunt Beacon with her shining safety lamp",
        boost=1,
        comfort="Good. Keep breathing, and keep thinking.",
        tags={"mentor"},
    ),
    "robo_pup": Ally(
        id="robo_pup",
        name="Robo Pup",
        type="thing",
        phrase="Robo Pup, the little helper robot",
        boost=1,
        comfort="Beep-beep! Brave brain online!",
        tags={"robot"},
    ),
}

GIRL_NAMES = ["Maya", "Luna", "Ava", "Nia", "Ruby", "Zoe", "Ivy", "Skye"]
BOY_NAMES = ["Max", "Leo", "Finn", "Noah", "Eli", "Theo", "Kai", "Jude"]
TRAITS = ["steady", "careful", "focused", "patient", "jumpy", "restless"]


@dataclass
class StoryParams:
    scene: str
    problem: str
    method: str
    ally: str
    hero_name: str
    hero_gender: str
    trait: str
    delay: int = 0
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        scene="fair",
        problem="vent",
        method="glow_grapple",
        ally="captain_ray",
        hero_name="Maya",
        hero_gender="girl",
        trait="steady",
        delay=0,
    ),
    StoryParams(
        scene="market",
        problem="ledge",
        method="sky_cape",
        ally="aunt_beacon",
        hero_name="Leo",
        hero_gender="boy",
        trait="focused",
        delay=0,
    ),
    StoryParams(
        scene="parade",
        problem="ribbons",
        method="rescue_snips",
        ally="robo_pup",
        hero_name="Ruby",
        hero_gender="girl",
        trait="jumpy",
        delay=0,
    ),
    StoryParams(
        scene="market",
        problem="ribbons",
        method="rescue_snips",
        ally="captain_ray",
        hero_name="Finn",
        hero_gender="boy",
        trait="careful",
        delay=1,
    ),
]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for scene_id, scene in SCENES.items():
        for problem_id, problem in PROBLEMS.items():
            if not problem_supported(scene, problem):
                continue
            for method_id, method in METHODS.items():
                if method.sense < SENSE_MIN or not method_fits(problem, method):
                    continue
                for ally_id, ally in ALLIES.items():
                    if total_power(method, ally) >= problem.severity:
                        combos.append((scene_id, problem_id, method_id, ally_id))
    return combos


def explain_rejection(scene: Scene, problem: Problem, method: Method, ally: Ally) -> str:
    if not problem_supported(scene, problem):
        return (
            f"(No story: {problem.id} does not fit {scene.label}. Pick a problem the scene can honestly support.)"
        )
    if method.sense < SENSE_MIN:
        return (
            f"(Refusing method '{method.id}': it scores too low on common sense "
            f"(sense={method.sense} < {SENSE_MIN}). The hero should use a safer plan.)"
        )
    if not method_fits(problem, method):
        needs = ", ".join(sorted(problem.need))
        gives = ", ".join(sorted(method.provides))
        return (
            f"(No story: {problem.target_label} needs [{needs}], but {method.label} only provides [{gives}].)"
        )
    if total_power(method, ally) < problem.severity:
        return (
            f"(No story: even with {ally.name}, {method.label} is too weak for this rescue.)"
        )
    return "(No story: this combination is not reasonable.)"


KNOWLEDGE = {
    "breathing": [
        (
            "Why does it help to breathe slowly when you feel scared?",
            "Slow breathing can help your body calm down. When your body feels calmer, it becomes easier to think clearly about what to do next.",
        )
    ],
    "kitten": [
        (
            "Why might a kitten hide in a dark space?",
            "Kittens often hide when they are frightened because small dark places can feel safer to them. But they can still get stuck and need gentle help."
        )
    ],
    "puppy": [
        (
            "Why can a high ledge be dangerous for a puppy?",
            "A puppy can slip because its paws are small and it may not know how to climb down. Wind and noise can also make it panic."
        )
    ],
    "ribbons": [
        (
            "Why can ribbons become a problem even when they look pretty?",
            "Ribbons can twist around hands, clothes, or feet if they flap in the wind. When that happens, tugging too hard can make the knot tighter."
        )
    ],
    "cape": [
        (
            "What does a cape do in a superhero story?",
            "In a superhero story, a cape often shows courage and style. It does not make someone brave by itself, but it can remind them to act bravely."
        )
    ],
    "light": [
        (
            "Why is light useful in a rescue?",
            "Light helps you see where someone is stuck and what might hurt them. Seeing clearly helps people make safer choices."
        )
    ],
    "careful": [
        (
            "Why is being careful sometimes braver than being fast?",
            "Careful actions protect people from getting hurt. Real bravery means choosing what works safely, not just what looks bold."
        )
    ],
    "help": [
        (
            "When is asking for help a brave thing to do?",
            "Asking for help is brave when a problem is too big for one person alone. A real hero wants everyone safe more than they want to look impressive."
        )
    ],
}
KNOWLEDGE_ORDER = ["breathing", "kitten", "puppy", "ribbons", "light", "cape", "careful", "help"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    scene = f["scene_cfg"]
    problem = f["problem_cfg"]
    method = f["method_cfg"]
    outcome = f["outcome"]
    if outcome == "solo":
        return [
            f'Write a short superhero story for a 3-to-5-year-old that includes the word "breathe" and the word "galore".',
            f"Tell a suspenseful story with inner monologue where {hero.id} hears trouble at {scene.label}, calms down, and rescues {problem.target_label} using {method.label}.",
            f"Write a gentle superhero rescue where the hero feels scared for a moment, thinks quietly inside their head, and then solves the problem alone."
        ]
    return [
        f'Write a short superhero story for a 3-to-5-year-old that includes the word "breathe" and the word "galore".',
        f"Tell a suspenseful story with inner monologue where {hero.id} starts a rescue at {scene.label} and then bravely asks a helper to finish it together.",
        f"Write a superhero story that shows asking for help can be part of being brave, with a worried moment, calm breathing, and a happy rescue ending."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    target = f["target"]
    ally = f["ally"]
    scene = f["scene_cfg"]
    problem = f["problem_cfg"]
    method = f["method_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about a young hero named {hero.id}, {target.label}, and {ally.id}. The story happens at {scene.label}."
        ),
        (
            f"What problem did {hero.id} notice?",
            f"{hero.id} heard that {target.label} was stuck at {problem.spot}. The rescue felt scary because {problem.danger_line.lower()}"
        ),
        (
            f"What did {hero.id} say inside {hero.pronoun('possessive')} own head?",
            f"{hero.id} used an inner thought to slow down and breathe before acting. That helped {hero.pronoun('object')} think about the rescue instead of only feeling scared."
        ),
        (
            f"Why was the moment suspenseful?",
            f"It felt suspenseful because {target.label} was trapped in a risky place and the happy noise around them suddenly sounded sharp and urgent. {hero.id} had to decide quickly, but also carefully."
        ),
    ]
    if outcome == "solo":
        qa.append(
            (
                f"How did {hero.id} save {target.label}?",
                f"{hero.id} {method.qa_text}. The rescue worked because {method.label} matched the problem instead of making it rougher."
            )
        )
        qa.append(
            (
                f"What changed by the end of the story?",
                f"At the end, {target.label} was safe and {scene.label} felt cheerful again. {hero.id}'s cape stopped feeling like dress-up and started feeling earned."
            )
        )
    else:
        qa.append(
            (
                f"Did {hero.id} finish the rescue alone?",
                f"No. {hero.id} began the rescue, but then worked together with {ally.id}. Asking for help made the rescue stronger and safer."
            )
        )
        qa.append(
            (
                f"What changed by the end of the story?",
                f"At the end, {target.label} was safe and {hero.id} felt proud instead of shaky. The story shows that teamwork can be superhero work too."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    problem = f["problem_cfg"]
    method = f["method_cfg"]
    tags: set[str] = {"breathing", "help"}
    if "kitten" in problem.tags:
        tags.add("kitten")
    if "puppy" in problem.tags:
        tags.add("puppy")
    if "ribbons" in problem.tags:
        tags.add("ribbons")
    if "light" in method.provides:
        tags.add("light")
    if "careful" in method.provides:
        tags.add("careful")
    if method.id == "sky_cape":
        tags.add("cape")
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
supported(S, P) :- scene_supports(S, P).
fits(P, M) :- need(P, N), provides(M, N), not missing_need(P, M).
missing_need(P, M) :- need(P, N), not provides(M, N).
sensible(M) :- method(M), sense(M, S), sense_min(Min), S >= Min.
strong_enough(P, M, A) :- severity(P, V), power(M, PM), boost(A, BA), PM + BA >= V.
valid(S, P, M, A) :- scene(S), problem(P), method(M), ally(A),
                     supported(S, P), fits(P, M), sensible(M), strong_enough(P, M, A).

solo(P, M) :- severity(P, V), power(M, PM), PM >= V.
team(P, M, A) :- valid(_, P, M, A), not solo(P, M).

outcome(solo) :- chosen_problem(P), chosen_method(M), solo(P, M).
outcome(team) :- chosen_scene(S), chosen_problem(P), chosen_method(M), chosen_ally(A),
                 valid(S, P, M, A), not solo(P, M).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for scene_id, scene in SCENES.items():
        lines.append(asp.fact("scene", scene_id))
        for problem_id in sorted(scene.supports):
            lines.append(asp.fact("scene_supports", scene_id, problem_id))
    for problem_id, problem in PROBLEMS.items():
        lines.append(asp.fact("problem", problem_id))
        lines.append(asp.fact("severity", problem_id, problem.severity))
        for need in sorted(problem.need):
            lines.append(asp.fact("need", problem_id, need))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("sense", method_id, method.sense))
        lines.append(asp.fact("power", method_id, method.power))
        for prov in sorted(method.provides):
            lines.append(asp.fact("provides", method_id, prov))
    for ally_id, ally in ALLIES.items():
        lines.append(asp.fact("ally", ally_id))
        lines.append(asp.fact("boost", ally_id, ally.boost))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(m for (m,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_scene", params.scene),
        asp.fact("chosen_problem", params.problem),
        asp.fact("chosen_method", params.method),
        asp.fact("chosen_ally", params.ally),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a young superhero hears a cry for help, remembers to breathe, and makes a fitting rescue."
    )
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--ally", choices=ALLIES)
    ap.add_argument("--hero")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--delay", type=int, choices=[0, 1], default=0)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.scene and args.problem and args.method and args.ally:
        scene = SCENES[args.scene]
        problem = PROBLEMS[args.problem]
        method = METHODS[args.method]
        ally = ALLIES[args.ally]
        if not can_solve(scene, problem, method, ally):
            raise StoryError(explain_rejection(scene, problem, method, ally))

    combos = [
        combo for combo in valid_combos()
        if (args.scene is None or combo[0] == args.scene)
        and (args.problem is None or combo[1] == args.problem)
        and (args.method is None or combo[2] == args.method)
        and (args.ally is None or combo[3] == args.ally)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    scene_id, problem_id, method_id, ally_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    hero_name = args.hero or rng.choice(name_pool)
    trait = args.trait or rng.choice(TRAITS)

    params = StoryParams(
        scene=scene_id,
        problem=problem_id,
        method=method_id,
        ally=ally_id,
        hero_name=hero_name,
        hero_gender=gender,
        trait=trait,
        delay=args.delay,
    )
    if not can_solve(SCENES[params.scene], PROBLEMS[params.problem], METHODS[params.method], ALLIES[params.ally]):
        raise StoryError(explain_rejection(
            SCENES[params.scene], PROBLEMS[params.problem], METHODS[params.method], ALLIES[params.ally]
        ))
    return params


def generate(params: StoryParams) -> StorySample:
    if params.scene not in SCENES:
        raise StoryError(f"(Unknown scene: {params.scene})")
    if params.problem not in PROBLEMS:
        raise StoryError(f"(Unknown problem: {params.problem})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")
    if params.ally not in ALLIES:
        raise StoryError(f"(Unknown ally: {params.ally})")

    scene = SCENES[params.scene]
    problem = PROBLEMS[params.problem]
    method = METHODS[params.method]
    ally = ALLIES[params.ally]
    if not can_solve(scene, problem, method, ally):
        raise StoryError(explain_rejection(scene, problem, method, ally))

    world = tell(
        scene=scene,
        problem=problem,
        method=method,
        ally=ally,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        hero_trait=params.trait,
        delay=params.delay,
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

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combinations:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_sensible = {m.id for m in sensible_methods()}
    asp_sens = set(asp_sensible())
    if py_sensible == asp_sens:
        print(f"OK: sensible methods match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible methods: clingo={sorted(asp_sens)} python={sorted(py_sensible)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure for seed {seed}.")
            break

    bad = 0
    for params in cases:
        try:
            py_out = outcome_of(params)
            asp_out = asp_outcome(params)
            if py_out != asp_out:
                bad += 1
        except Exception as err:  # pragma: no cover - verification path
            rc = 1
            bad += 1
            print(f"Outcome check crashed for {params}: {err}")
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    # Smoke test normal generation and emit.
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated empty story.)")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test generation/emit passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible methods: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} valid (scene, problem, method, ally) combos:\n")
        for scene, problem, method, ally in combos:
            print(f"  {scene:8} {problem:8} {method:13} {ally}")
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
            header = f"### {p.hero_name}: {p.problem} at {p.scene} with {p.method} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

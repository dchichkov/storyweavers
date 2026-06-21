#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/paella_lesson_learned_superhero_story.py
===================================================================

A small storyworld about a child in superhero mode who wants to save supper by
making paella, tries an unreasonable shortcut, and learns that real heroes cook
carefully, wait when food needs time, and ask for help.

Run it
------
python storyworlds/worlds/gpt-5.4/paella_lesson_learned_superhero_story.py
python storyworlds/worlds/gpt-5.4/paella_lesson_learned_superhero_story.py --shortcut blast_heat --response lower_heat
python storyworlds/worlds/gpt-5.4/paella_lesson_learned_superhero_story.py --shortcut extra_salt --response hero_blow
python storyworlds/worlds/gpt-5.4/paella_lesson_learned_superhero_story.py --all
python storyworlds/worlds/gpt-5.4/paella_lesson_learned_superhero_story.py --verify
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
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
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
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)


@dataclass
class Mission:
    id: str
    alarm: str
    goal: str
    boast: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Shortcut:
    id: str
    risky_action: str
    warning: str
    problem: str
    result_line: str
    lesson: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    fixes: str
    help_line: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


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


def _r_problem_changes_feelings(world: World) -> list[str]:
    rice = world.get("rice")
    hero = world.get("hero")
    if rice.meters["problem"] < THRESHOLD:
        return []
    sig = ("problem_feelings", world.facts.get("problem"))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["worry"] += 1
    hero.memes["pride"] = 0.0
    return []


def _r_help_brings_relief(world: World) -> list[str]:
    hero = world.get("hero")
    helper = world.get("helper")
    rice = world.get("rice")
    if helper.memes["helping"] < THRESHOLD or rice.meters["fixed"] < THRESHOLD:
        return []
    sig = ("help_relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["relief"] += 1
    hero.memes["trust"] += 1
    helper.memes["care"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="problem_changes_feelings", tag="emotional", apply=_r_problem_changes_feelings),
    Rule(name="help_brings_relief", tag="emotional", apply=_r_help_brings_relief),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def response_fits(shortcut: Shortcut, response: Response) -> bool:
    return response.fixes == shortcut.problem


def sensible_responses() -> list[Response]:
    return [resp for resp in RESPONSES.values() if resp.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for mission_id in MISSIONS:
        for shortcut_id, shortcut in SHORTCUTS.items():
            for response_id, response in RESPONSES.items():
                if response_fits(shortcut, response) and response.sense >= SENSE_MIN:
                    out.append((mission_id, shortcut_id, response_id))
    return out


def predict_problem(world: World, shortcut: Shortcut) -> str:
    sim = world.copy()
    rice = sim.get("rice")
    _do_shortcut(sim, shortcut, rice, narrate=False)
    return sim.facts.get("problem", "none")


def _do_shortcut(world: World, shortcut: Shortcut, rice: Entity, narrate: bool = True) -> None:
    world.facts["problem"] = shortcut.problem
    rice.meters["problem"] += 1
    if shortcut.problem == "scorched":
        rice.meters["scorched"] += 1
        world.get("pan").meters["too_hot"] += 1
    elif shortcut.problem == "crunchy":
        rice.meters["crunchy"] += 1
        world.get("pan").meters["too_early"] += 1
    elif shortcut.problem == "salty":
        rice.meters["salty"] += 1
        world.get("pan").meters["overseasoned"] += 1
    propagate(world, narrate=narrate)


def intro(world: World, hero: Entity, helper: Entity, mission: Mission) -> None:
    hero.memes["joy"] += 1
    hero.memes["pride"] += 1
    world.say(
        f"One evening, {hero.id} tied on {hero.pronoun('possessive')} red cape and heard "
        f"{mission.alarm}. At once, {hero.pronoun()} struck a pose and announced, "
        f'"{mission.boast}"'
    )
    world.say(
        f"In the kitchen, a wide pan waited on the stove, and saffron-tinted paella "
        f"glowed like a golden shield. {helper.label_word.capitalize()} smiled and said "
        f"that real supper still needed calm hands."
    )


def mission_setup(world: World, hero: Entity, helper: Entity, mission: Mission) -> None:
    world.say(
        f"{hero.id} wanted to {mission.goal}. Peas, rice, and bright strips of pepper "
        f"sat ready like a superhero team waiting for orders."
    )
    world.say(
        f'"I can do it fast," {hero.id} said. But {helper.label_word} rested a hand on '
        f"the spoon and reminded {hero.pronoun('object')} that paella tastes best when it "
        f"is made with care."
    )


def temptation(world: World, hero: Entity, helper: Entity, shortcut: Shortcut) -> None:
    predicted = predict_problem(world, shortcut)
    world.facts["predicted_problem"] = predicted
    hero.memes["impatience"] += 1
    world.say(
        f"Then {hero.id} spotted a shortcut. {shortcut.risky_action} sounded exactly like "
        f"a superhero trick."
    )
    world.say(
        f'{helper.label_word.capitalize()} shook {helper.pronoun("possessive")} head. '
        f'"{shortcut.warning}"'
    )


def mistake(world: World, hero: Entity, shortcut: Shortcut, rice: Entity) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f"But {hero.id} wanted to save the day in one dazzling move, so {hero.pronoun()} "
        f"tried it anyway."
    )
    _do_shortcut(world, shortcut, rice, narrate=False)
    world.say(shortcut.result_line)


def ask_for_help(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["humility"] += 1
    world.say(
        f"For a tiny moment, {hero.id} looked as if {hero.pronoun()} might cry. Then "
        f"{hero.pronoun()} took a breath and called, "
        f'"{helper.label_word.capitalize()}, will you help me fix it?"'
    )


def repair(world: World, hero: Entity, helper: Entity, response: Response, shortcut: Shortcut) -> None:
    rice = world.get("rice")
    rice.meters["fixed"] += 1
    rice.meters["problem"] = 0.0
    helper.memes["helping"] += 1
    if shortcut.problem == "scorched":
        rice.meters["scorched"] = 0.0
        world.get("pan").meters["too_hot"] = 0.0
    elif shortcut.problem == "crunchy":
        rice.meters["crunchy"] = 0.0
        world.get("pan").meters["too_early"] = 0.0
    elif shortcut.problem == "salty":
        rice.meters["salty"] = 0.0
        world.get("pan").meters["overseasoned"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"{helper.label_word.capitalize()} stayed calm. {response.help_line}"
    )
    world.say(
        f"Slowly the kitchen smell turned warm and rich again, and the paella looked ready "
        f"for dinner instead of disaster."
    )


def lesson(world: World, hero: Entity, helper: Entity, shortcut: Shortcut) -> None:
    hero.memes["lesson"] += 1
    hero.memes["gratitude"] += 1
    world.say(
        f'{helper.label_word.capitalize()} knelt beside {hero.id} and said, '
        f'"A real hero does not need a wild shortcut. {shortcut.lesson}"'
    )
    world.say(
        f'{hero.id} touched the spoon gently this time. "I learned it," {hero.pronoun()} '
        f"said. \"Heroes can be brave and patient at the same time.\""
    )


def ending(world: World, hero: Entity, helper: Entity, mission: Mission) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"When the family sat down, {mission.ending} {hero.id} served the paella with a "
        f"careful smile instead of a flashy flourish."
    )
    world.say(
        f"The cape still fluttered behind {hero.pronoun('object')}, but now it looked less "
        f"like a costume and more like a promise to do things the right way."
    )


def tell(
    mission: Mission,
    shortcut: Shortcut,
    response: Response,
    hero_name: str = "Nico",
    hero_type: str = "boy",
    helper_type: str = "mother",
    sidekick: str = "Patch",
) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        label=hero_name,
        role="hero",
        traits=["eager", "imaginative"],
        attrs={"sidekick": sidekick},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_type,
        label="the helper",
        role="helper",
        traits=["calm", "wise"],
    ))
    world.add(Entity(
        id="pan",
        kind="thing",
        type="pan",
        label="pan",
        phrase="the wide paella pan",
        tags={"pan", "kitchen"},
    ))
    rice = world.add(Entity(
        id="rice",
        kind="thing",
        type="food",
        label="paella",
        phrase="the paella",
        tags={"paella", "rice", "dinner"},
    ))
    sidekick_ent = world.add(Entity(
        id="sidekick",
        kind="thing",
        type="toy",
        label=sidekick,
        phrase=sidekick,
        tags={"toy"},
    ))

    intro(world, hero, helper, mission)
    mission_setup(world, hero, helper, mission)

    world.para()
    temptation(world, hero, helper, shortcut)
    mistake(world, hero, shortcut, rice)
    ask_for_help(world, hero, helper)

    world.para()
    repair(world, hero, helper, response, shortcut)
    lesson(world, hero, helper, shortcut)

    world.para()
    if sidekick_ent.label:
        world.say(
            f"{hero.id} set {sidekick_ent.label} near the napkins to guard the table "
            f"while supper was carried in."
        )
    ending(world, hero, helper, mission)

    world.facts.update(
        mission=mission,
        shortcut=shortcut,
        response=response,
        hero=hero,
        helper=helper,
        rice=rice,
        sidekick=sidekick_ent,
        problem=shortcut.problem,
        fixed=rice.meters["fixed"] >= THRESHOLD,
        learned=hero.memes["lesson"] >= THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    mission: str
    shortcut: str
    response: str
    hero_name: str
    hero_type: str
    helper_type: str
    sidekick: str
    seed: Optional[int] = None


MISSIONS = {
    "family_supper": Mission(
        id="family_supper",
        alarm="every tummy in the house give a little hungry rumble",
        goal="save family supper before everyone got too hungry",
        boast="Captain Saffron will rescue dinner!",
        ending="plates clinked, hungry faces brightened, and the whole table cheered.",
        tags={"family", "dinner"},
    ),
    "neighbor_share": Mission(
        id="neighbor_share",
        alarm="the doorbell ring with kind neighbors dropping by",
        goal="make enough supper to share with the neighbors too",
        boast="The Paella Protector is on the job!",
        ending="an extra plate was carried next door, and even the neighbors grinned at the smell.",
        tags={"neighbor", "sharing"},
    ),
    "rainy_night": Mission(
        id="rainy_night",
        alarm="rain tap on the windows while the house grew cozy and hungry",
        goal="bring a warm, bright dinner to the table on a gray night",
        boast="No storm can stop Supper Shield!",
        ending="steam curled up from every bowl, and the rainy night felt small and friendly outside.",
        tags={"rain", "cozy"},
    ),
}

SHORTCUTS = {
    "blast_heat": Shortcut(
        id="blast_heat",
        risky_action="turning the burner up high to superhero level",
        warning="Too much heat can scorch the rice before the paella is ready.",
        problem="scorched",
        result_line="A sharp hiss came from the pan, and a toasty smell slipped into the air. The rice at the bottom was starting to scorch.",
        lesson="Heat is not a superpower if it hurts the food. Good cooks use steady fire and watch closely.",
        tags={"heat", "kitchen", "patience"},
    ),
    "peek_early": Shortcut(
        id="peek_early",
        risky_action="lifting the lid again and again to check if supper was done",
        warning="Paella needs time to steam. If you keep opening it too soon, the rice will stay crunchy.",
        problem="crunchy",
        result_line="When {hero} peeked too early, puffs of steam ran away. A quick taste showed the rice was still crunchy in the middle.",
        lesson="Waiting can be part of the rescue. Food cannot hurry just because we want it to.",
        tags={"waiting", "steam", "patience"},
    ),
    "extra_salt": Shortcut(
        id="extra_salt",
        risky_action="shaking in a giant shower of salt so the paella would taste heroic at once",
        warning="A little seasoning helps, but too much salt can hide every other flavor.",
        problem="salty",
        result_line="The spoon came up sparkling, but one tiny taste made {hero} blink. The paella had turned much too salty.",
        lesson="Big flavor does not come from dumping more in. Good cooks taste, think, and add only what is needed.",
        tags={"salt", "taste", "care"},
    ),
}

RESPONSES = {
    "lower_heat": Response(
        id="lower_heat",
        sense=3,
        fixes="scorched",
        help_line="Together they turned the burner down, scraped away the dark bits, and added a splash of broth before stirring softly.",
        qa_text="They turned the heat down, removed the scorched part, and added broth to save the paella.",
        tags={"broth", "heat", "fix"},
    ),
    "wait_and_cover": Response(
        id="wait_and_cover",
        sense=3,
        fixes="crunchy",
        help_line="Together they tucked the lid back on, added a spoonful of broth, and let the rice steam a little longer without peeking.",
        qa_text="They covered the pan again, added a little broth, and waited so the rice could finish steaming.",
        tags={"waiting", "steam", "fix"},
    ),
    "balance_flavor": Response(
        id="balance_flavor",
        sense=3,
        fixes="salty",
        help_line="Together they stirred in more rice, peas, and broth, then tasted carefully until the flavors came back into balance.",
        qa_text="They added more rice, peas, and broth to balance the salty taste.",
        tags={"taste", "broth", "fix"},
    ),
    "hero_blow": Response(
        id="hero_blow",
        sense=1,
        fixes="scorched",
        help_line="They blew superhero breaths at the pan, which looked dramatic but did not really solve kitchen trouble.",
        qa_text="They tried blowing at the pan.",
        tags={"silly"},
    ),
}

GIRL_NAMES = ["Luna", "Mia", "Sofia", "Nora", "Zoe", "Eva"]
BOY_NAMES = ["Nico", "Leo", "Tomas", "Max", "Eli", "Hugo"]
SIDEKICKS = ["Patch", "Comet", "Spark", "Button"]


KNOWLEDGE = {
    "paella": [
        (
            "What is paella?",
            "Paella is a rice dish cooked in a wide pan. It often has broth, vegetables, and other tasty ingredients mixed together."
        )
    ],
    "saffron": [
        (
            "Why is paella often yellow or golden?",
            "Paella is often colored by saffron or other seasonings in the broth. That is what can give the rice a warm golden color."
        )
    ],
    "heat": [
        (
            "Why can cooking on very high heat be a problem?",
            "Very high heat can burn the food before the middle is ready. Good cooking often uses the right amount of heat, not the biggest amount."
        )
    ],
    "steam": [
        (
            "Why does rice need time to steam?",
            "Steam and hot liquid help the rice soften all the way through. If you stop too soon, the middle can stay hard and crunchy."
        )
    ],
    "salt": [
        (
            "Why should you add salt carefully?",
            "Salt can make food taste better, but too much can cover up the other flavors. That is why cooks add a little, then taste."
        )
    ],
    "broth": [
        (
            "What does broth do in a pan of rice?",
            "Broth adds moisture and flavor while the rice cooks. The rice drinks it up as it gets soft."
        )
    ],
    "patience": [
        (
            "Why is patience useful when cooking?",
            "Cooking takes time, and some foods cannot be rushed. Patience helps you wait, watch, and fix small problems before they grow."
        )
    ],
}
KNOWLEDGE_ORDER = ["paella", "saffron", "heat", "steam", "salt", "broth", "patience"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    mission = f["mission"]
    shortcut = f["shortcut"]
    return [
        'Write a short superhero story for a 3-to-5-year-old that includes the word "paella" and ends with a lesson learned.',
        f"Tell a gentle kitchen adventure where {hero.id} acts like a superhero and tries {shortcut.risky_action}, then learns a wiser way to finish dinner.",
        f"Write a story where a child wants to {mission.goal}, but a cooking mistake leads to a calm lesson about patience and asking for help.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    mission = f["mission"]
    shortcut = f["shortcut"]
    response = f["response"]
    helper_word = helper.label_word
    answer_set: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child pretending to be a superhero, and {helper_word} who helps in the kitchen. Together they are trying to finish a pan of paella."
        ),
        (
            f"What was {hero.id} trying to do?",
            f"{hero.id} wanted to {mission.goal}. The superhero game made the job feel like an exciting rescue mission."
        ),
        (
            f"What mistake did {hero.id} make?",
            f"{hero.id} tried {shortcut.risky_action}. That caused the paella to become {shortcut.problem}, just as {helper_word} had warned."
        ),
        (
            f"How was the problem fixed?",
            f"{helper_word.capitalize()} helped calmly instead of scolding. {response.qa_text}."
        ),
        (
            f"What lesson did {hero.id} learn?",
            f"{hero.id} learned that real heroes do not rush or show off in the kitchen. {shortcut.lesson}"
        ),
    ]
    if f.get("fixed"):
        answer_set.append(
            (
                "How did the story end?",
                f"It ended with the paella ready for dinner and everyone calmer than before. The final image shows {hero.id} serving supper carefully, which proves the lesson stuck."
            )
        )
    return answer_set


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"paella", "saffron", "patience"}
    shortcut = world.facts["shortcut"]
    response = world.facts["response"]
    tags |= set(shortcut.tags)
    tags |= set(response.tags)
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
        bits = []
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
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        mission="family_supper",
        shortcut="blast_heat",
        response="lower_heat",
        hero_name="Nico",
        hero_type="boy",
        helper_type="mother",
        sidekick="Patch",
    ),
    StoryParams(
        mission="neighbor_share",
        shortcut="peek_early",
        response="wait_and_cover",
        hero_name="Luna",
        hero_type="girl",
        helper_type="grandmother",
        sidekick="Comet",
    ),
    StoryParams(
        mission="rainy_night",
        shortcut="extra_salt",
        response="balance_flavor",
        hero_name="Leo",
        hero_type="boy",
        helper_type="father",
        sidekick="Spark",
    ),
]


def explain_response(response_id: str) -> str:
    response = RESPONSES[response_id]
    good = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{response_id}': it scores too low on common sense "
        f"(sense={response.sense} < {SENSE_MIN}). Try one of: {good}.)"
    )


def explain_rejection(shortcut: Shortcut, response: Response) -> str:
    return (
        f"(No story: {response.id} does not reasonably fix the '{shortcut.problem}' paella problem. "
        f"Choose a response that actually matches the mistake.)"
    )


ASP_RULES = r"""
fixes_problem(S, R) :- shortcut(S), response(R), problem_of(S, P), fixes(R, P).
sensible(R) :- response(R), sense(R, N), sense_min(M), N >= M.
valid(Ms, S, R) :- mission(Ms), shortcut(S), response(R), fixes_problem(S, R), sensible(R).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for mission_id in MISSIONS:
        lines.append(asp.fact("mission", mission_id))
    for shortcut_id, shortcut in SHORTCUTS.items():
        lines.append(asp.fact("shortcut", shortcut_id))
        lines.append(asp.fact("problem_of", shortcut_id, shortcut.problem))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        lines.append(asp.fact("fixes", response_id, response.fixes))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a superhero-minded child learns a kitchen lesson while making paella."
    )
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--shortcut", choices=SHORTCUTS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid combo set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    if args.shortcut and args.response:
        shortcut = SHORTCUTS[args.shortcut]
        response = RESPONSES[args.response]
        if not response_fits(shortcut, response):
            raise StoryError(explain_rejection(shortcut, response))

    combos = [
        combo for combo in valid_combos()
        if (args.mission is None or combo[0] == args.mission)
        and (args.shortcut is None or combo[1] == args.shortcut)
        and (args.response is None or combo[2] == args.response)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    mission_id, shortcut_id, response_id = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    helper_type = args.helper_type or rng.choice(["mother", "father", "grandmother", "grandfather"])
    sidekick = rng.choice(SIDEKICKS)
    return StoryParams(
        mission=mission_id,
        shortcut=shortcut_id,
        response=response_id,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_type=helper_type,
        sidekick=sidekick,
    )


def generate(params: StoryParams) -> StorySample:
    if params.mission not in MISSIONS:
        raise StoryError(f"(Unknown mission: {params.mission})")
    if params.shortcut not in SHORTCUTS:
        raise StoryError(f"(Unknown shortcut: {params.shortcut})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")

    shortcut = SHORTCUTS[params.shortcut]
    response = RESPONSES[params.response]
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    if not response_fits(shortcut, response):
        raise StoryError(explain_rejection(shortcut, response))

    world = tell(
        mission=MISSIONS[params.mission],
        shortcut=shortcut,
        response=response,
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        helper_type=params.helper_type,
        sidekick=params.sidekick,
    )

    story_text = world.render()
    hero_name = world.facts["hero"].id
    story_text = story_text.replace("{hero}", hero_name)

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


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_sensible = {r.id for r in sensible_responses()}
    asp_sens = set(asp_sensible())
    if py_sensible == asp_sens:
        print(f"OK: sensible responses match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print("MISMATCH in sensible responses:")
        print("  python:", sorted(py_sensible))
        print("  clingo:", sorted(asp_sens))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        rng = random.Random(7)
        params = resolve_params(build_parser().parse_args([]), rng)
        sample = generate(params)
        if not sample.story.strip():
            raise StoryError("(Random smoke test failed: empty story.)")
        print("OK: random resolve/generate smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"RANDOM SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (mission, shortcut, response) combos:\n")
        for mission, shortcut, response in combos:
            print(f"  {mission:14} {shortcut:12} {response}")
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
            header = f"### {p.hero_name}: {p.mission} / {p.shortcut} / {p.response}"
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

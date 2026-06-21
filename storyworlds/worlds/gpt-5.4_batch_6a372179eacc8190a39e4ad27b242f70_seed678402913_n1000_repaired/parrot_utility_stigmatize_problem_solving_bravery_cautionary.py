#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/parrot_utility_stigmatize_problem_solving_bravery_cautionary.py
================================================================================================

A standalone storyworld for a small folk-tale domain built from the seed words
"parrot", "utility", and "stigmatize", with the narrative features Problem
Solving, Bravery, and Cautionary.

Premise
-------
In a small village, a child keeps a plain utility satchel full of useful bits:
rope, patches, and hooked tools. The child's bright parrot notices trouble early,
but some villagers mock both the bird and the satchel as noisy and odd. When a
real village problem appears, the child must be brave, use the right tool, and
show that it is foolish to stigmatize humble helpers.

Run it
------
    python storyworlds/worlds/gpt-5.4/parrot_utility_stigmatize_problem_solving_bravery_cautionary.py
    python storyworlds/worlds/gpt-5.4/parrot_utility_stigmatize_problem_solving_bravery_cautionary.py --setting riverside --problem sluice_gate --utility hook_pole
    python storyworlds/worlds/gpt-5.4/parrot_utility_stigmatize_problem_solving_bravery_cautionary.py --problem roof_thatch --utility spare_rope
    python storyworlds/worlds/gpt-5.4/parrot_utility_stigmatize_problem_solving_bravery_cautionary.py --all
    python storyworlds/worlds/gpt-5.4/parrot_utility_stigmatize_problem_solving_bravery_cautionary.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/parrot_utility_stigmatize_problem_solving_bravery_cautionary.py --verify
"""

from __future__ import annotations

import argparse
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
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "elder"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "elder": "elder"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    image: str
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    target: str
    sign: str
    risk: str
    danger: int
    action_place: str
    brave_step: str
    clue: str
    solved_text: str
    loss_text: str
    lesson_detail: str
    tags: set[str] = field(default_factory=set)


@dataclass
class UtilityItem:
    id: str
    label: str
    phrase: str
    power: int
    solves: set[str] = field(default_factory=set)
    use_text: str = ""
    fail_text: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class ParrotKind:
    id: str
    color: str
    cry: str
    talent: str
    scout_text: str
    carry_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_warning_spreads(world: World) -> list[str]:
    out: list[str] = []
    problem = world.facts.get("problem")
    if problem is None:
        return out
    target = world.get("target")
    village = world.get("village")
    if target.meters["threat"] < THRESHOLD:
        return out
    sig = ("warning_spreads", problem.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    village.meters["worry"] += 1
    hero = world.get("hero")
    parrot = world.get("parrot")
    hero.memes["resolve"] += 1
    parrot.memes["alarm"] += 1
    out.append("__warning__")
    return out


def _r_mockery_hurts(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    village = world.get("village")
    if hero.memes["mocked"] < THRESHOLD:
        return out
    sig = ("mockery_hurts", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["sting"] += 1
    village.memes["scorn"] += 1
    out.append("__mockery__")
    return out


CAUSAL_RULES = [
    Rule(name="warning_spreads", tag="physical", apply=_r_warning_spreads),
    Rule(name="mockery_hurts", tag="social", apply=_r_mockery_hurts),
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


def valid_combo(setting_id: str, problem_id: str, utility_id: str) -> bool:
    if setting_id not in SETTINGS or problem_id not in PROBLEMS or utility_id not in UTILITIES:
        return False
    setting = SETTINGS[setting_id]
    utility = UTILITIES[utility_id]
    return problem_id in setting.affords and problem_id in utility.solves


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for pid in setting.affords:
            for uid, utility in UTILITIES.items():
                if pid in utility.solves:
                    combos.append((sid, pid, uid))
    return sorted(combos)


def severity(problem: Problem, delay: int) -> int:
    return problem.danger + delay


def is_saved(problem: Problem, utility: UtilityItem, delay: int) -> bool:
    return utility.power >= severity(problem, delay)


def explain_rejection(setting_id: str, problem_id: str, utility_id: str) -> str:
    if setting_id not in SETTINGS:
        return f"(No story: unknown setting '{setting_id}'.)"
    if problem_id not in PROBLEMS:
        return f"(No story: unknown problem '{problem_id}'.)"
    if utility_id not in UTILITIES:
        return f"(No story: unknown utility item '{utility_id}'.)"
    setting = SETTINGS[setting_id]
    problem = PROBLEMS[problem_id]
    utility = UTILITIES[utility_id]
    if problem_id not in setting.affords:
        return (
            f"(No story: {problem.label} does not fit {setting.place}. "
            f"That place cannot honestly host that kind of trouble.)"
        )
    return (
        f"(No story: {utility.label} is not the right utility for {problem.label}. "
        f"This world only accepts fixes that truly match the problem.)"
    )


def outcome_of(params: "StoryParams") -> str:
    utility = UTILITIES[params.utility]
    problem = PROBLEMS[params.problem]
    return "saved" if is_saved(problem, utility, params.delay) else "loss"


def introduce(world: World, hero: Entity, elder: Entity, parrot: Entity, setting: Setting) -> None:
    world.say(
        f"In the days when each village kept its own weather wisdom, {hero.id} lived in "
        f"{setting.place}. {setting.image}"
    )
    world.say(
        f"{hero.id} was known for carrying {hero.attrs['satchel_phrase']}, while {parrot.phrase} "
        f"rode on {hero.pronoun('possessive')} shoulder and watched the world with bright eyes."
    )
    world.say(
        f"The village elder, {elder.id}, liked quiet order better than surprises, and many neighbors "
        f"copied {elder.pronoun('possessive')} frown."
    )


def daily_mockery(world: World, hero: Entity, elder: Entity, parrot: Entity) -> None:
    hero.memes["mocked"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Some children laughed at the satchel and called it a bag of scraps. "
        f'Even {elder.id} said, "That noisy parrot and that utility bag are more bother than help."'
    )
    world.say(
        f"{hero.id} felt the words sting, for it is easy for a crowd to stigmatize what looks plain or odd. "
        f"Still, {hero.pronoun()} kept the satchel closed and spoke softly to {parrot.label}."
    )


def sign_of_trouble(world: World, hero: Entity, parrot: Entity, problem: Problem) -> None:
    target = world.get("target")
    target.meters["threat"] += 1
    propagate(world, narrate=False)
    parrot.memes["alert"] += 1
    world.say(
        f"Before noon, {parrot.label.capitalize()} flapped up with a harsh cry of "
        f'"{parrot.attrs["cry"]}! {parrot.attrs["cry"]}!"'
    )
    world.say(f"{parrot.attrs['scout_text']} {problem.clue}")
    world.say(f"Soon everyone could see it too: {problem.sign} {problem.risk}")


def choice_of_courage(world: World, hero: Entity, elder: Entity, problem: Problem) -> None:
    hero.memes["fear"] += 1
    hero.memes["bravery"] += 1
    world.say(
        f'People stepped back from {problem.action_place}. "{problem.label.capitalize()}!" someone cried.'
    )
    world.say(
        f"{hero.id} was afraid, but bravery does not mean having no fear. It means taking one careful step "
        f"toward the right work when others freeze."
    )
    world.say(problem.brave_step)
    world.say(
        f"{elder.id} began to say, 'Stay back,' but the village had no quicker pair of hands."
    )


def use_utility(world: World, hero: Entity, parrot: Entity, utility: UtilityItem, problem: Problem, delay: int) -> bool:
    target = world.get("target")
    target.meters["damage"] = float(severity(problem, delay))
    hero.memes["problem_solving"] += 1
    parrot.memes["helping"] += 1
    success = is_saved(problem, utility, delay)
    if success:
        target.meters["saved"] += 1
        world.say(
            f"From the satchel {hero.pronoun()} drew {utility.phrase}. {parrot.attrs['carry_text']} "
            f"{utility.use_text}"
        )
        world.say(problem.solved_text)
    else:
        target.meters["lost"] += 1
        world.say(
            f"From the satchel {hero.pronoun()} drew {utility.phrase}. {parrot.attrs['carry_text']} "
            f"{utility.fail_text}"
        )
        world.say(problem.loss_text)
    return success


def reversal(world: World, hero: Entity, elder: Entity, parrot: Entity, success: bool) -> None:
    if success:
        elder.memes["remorse"] += 1
        hero.memes["honor"] += 1
        parrot.memes["pride"] += 1
        world.say(
            f"Then the square grew quiet. The same mouths that had mocked the parrot and the satchel now opened "
            f"in wonder."
        )
        world.say(
            f'{elder.id} bowed {elder.pronoun("possessive")} head and said, '
            f'"We were wrong to stigmatize what was useful. A wise village must look for help, not for someone '
            f'to shame."'
        )
    else:
        elder.memes["sorrow"] += 1
        hero.memes["weariness"] += 1
        world.say(
            f"The village was not ruined, but the harm could not be hidden. Faces turned pale, and even "
            f"{elder.id} could not keep pride in {elder.pronoun('possessive')} voice."
        )
        world.say(
            f'{elder.id} said, "We spent too long sneering at the warning bird and the plain utility satchel. '
            f'When good help is mocked, good time is wasted."'
        )


def ending(world: World, hero: Entity, parrot: Entity, problem: Problem, utility: UtilityItem, success: bool) -> None:
    if success:
        world.say(
            f"That evening, children asked to look inside the satchel, and {hero.id} showed them the humble tool "
            f"that had saved the village. {parrot.label.capitalize()} perched on the well-stone like a little green "
            f"judge who had finally been heard."
        )
        world.say(
            f"And from that day on, when a strange helper came with honest warning, the people remembered "
            f"{problem.lesson_detail}"
        )
    else:
        world.say(
            f"That night, the villagers worked together to mend what they could. {hero.id} and {parrot.label} kept "
            f"working too, though their shoulders were tired."
        )
        world.say(
            f"And from that day on, the people remembered the caution: {problem.lesson_detail}"
        )


def tell(
    setting: Setting,
    problem: Problem,
    utility: UtilityItem,
    parrot_kind: ParrotKind,
    *,
    hero_name: str,
    hero_gender: str,
    elder_name: str,
    elder_type: str,
    trait: str,
    delay: int,
) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        label=hero_name,
        role="hero",
        traits=[trait, "careful"],
        attrs={"satchel_phrase": "a little brown utility satchel with room for useful things"},
    ))
    parrot = world.add(Entity(
        id="Parrot",
        kind="character",
        type="bird",
        label="the parrot",
        phrase=f"a {parrot_kind.color} parrot named Pip",
        role="helper",
        attrs={
            "cry": parrot_kind.cry,
            "scout_text": parrot_kind.scout_text,
            "carry_text": parrot_kind.carry_text,
        },
        tags=set(parrot_kind.tags),
    ))
    elder = world.add(Entity(
        id=elder_name,
        kind="character",
        type=elder_type,
        label="the elder",
        role="elder",
    ))
    village = world.add(Entity(
        id="village",
        kind="thing",
        type="village",
        label="the village",
    ))
    target = world.add(Entity(
        id="target",
        kind="thing",
        type="target",
        label=problem.target,
    ))

    world.facts.update(
        setting=setting,
        problem=problem,
        utility=utility,
        parrot_kind=parrot_kind,
        delay=delay,
    )

    introduce(world, hero, elder, parrot, setting)
    world.para()
    daily_mockery(world, hero, elder, parrot)
    sign_of_trouble(world, hero, parrot, problem)
    world.para()
    choice_of_courage(world, hero, elder, problem)
    success = use_utility(world, hero, parrot, utility, problem, delay)
    world.para()
    reversal(world, hero, elder, parrot, success)
    ending(world, hero, parrot, problem, utility, success)

    world.facts.update(
        hero=hero,
        elder=elder,
        parrot=parrot,
        village=village,
        target=target,
        success=success,
        outcome="saved" if success else "loss",
    )
    return world


SETTINGS = {
    "riverside": Setting(
        id="riverside",
        place="Riverside Hollow",
        image="Mud-brick homes leaned beside a singing river, and the mill wheel turned day and night.",
        affords={"sluice_gate"},
        tags={"river", "village"},
    ),
    "granary": Setting(
        id="granary",
        place="Thatch Hill",
        image="Round granaries stood on stone feet, and every roof smelled of straw warmed by the sun.",
        affords={"roof_thatch"},
        tags={"storm", "village"},
    ),
    "wellside": Setting(
        id="wellside",
        place="Wellspring Hamlet",
        image="The houses circled a deep old well, and every bucket-song mattered in the dry season.",
        affords={"well_rope"},
        tags={"well", "village"},
    ),
}

PROBLEMS = {
    "sluice_gate": Problem(
        id="sluice_gate",
        label="the mill gate was jammed",
        target="the mill stream",
        sign="reeds and branches had jammed the sluice gate, and the mill water began to climb over its banks.",
        risk="If the gate stayed shut, the mill floor and the grain sacks would be soaked.",
        danger=2,
        action_place="the slick mill ledge",
        brave_step="So the child edged onto the slick mill ledge, one hand on wet stone and one hand on the satchel strap.",
        clue="Pip had seen the water bunch up dark and angry beside the wheel.",
        solved_text="The hooked pull came free with a muddy jerk, the gate lifted, and the trapped water rushed where it should.",
        loss_text="But the reach was short, and by the time the reeds were shifted, brown water had already swept through the mill floor.",
        lesson_detail="plain tools and plain warnings can guard a whole town",
        tags={"river", "flood", "mill"},
    ),
    "roof_thatch": Problem(
        id="roof_thatch",
        label="the granary roof was torn",
        target="the winter grain",
        sign="a storm wind had ripped open the granary thatch, and the first hard drops drummed through the hole.",
        risk="If the hole stayed open, the winter grain would swell, spoil, and rot.",
        danger=1,
        action_place="the tall ladder by the granary",
        brave_step="So the child climbed the tall ladder while the wind tugged at sleeves and the village looked up with held breath.",
        clue="Pip had circled above the roof and would not stop shrieking at the torn place.",
        solved_text="The patch spread flat, the cords pulled tight, and the grain below stayed dry while the storm passed over.",
        loss_text="But the patch was too small for the torn space, and rain still slipped through long enough to spoil several grain sacks.",
        lesson_detail="mockery is a poor shield against weather, while good preparation is a strong one",
        tags={"storm", "grain", "roof"},
    ),
    "well_rope": Problem(
        id="well_rope",
        label="the well line had snapped",
        target="the village well",
        sign="the old well rope had snapped and the bucket had sunk with a hollow splash into the dark.",
        risk="If no new line was fixed before dusk, the village would have little water for cooking and drinking.",
        danger=1,
        action_place="the well-stone rim",
        brave_step="So the child knelt at the worn well-stone rim and leaned over the dark mouth farther than anyone else dared.",
        clue="Pip had been peering straight down and squawking at the broken end.",
        solved_text="The new line bit firm, the bucket rose dripping from the dark, and clear water shone in its mouth again.",
        loss_text="But the line was thin and the knot slipped, so the bucket was recovered only after dusk, when many homes had already gone without water.",
        lesson_detail="a village should honor careful helpers before need turns sharp",
        tags={"well", "water", "village"},
    ),
}

UTILITIES = {
    "hook_pole": UtilityItem(
        id="hook_pole",
        label="hook pole",
        phrase="a long hook pole",
        power=3,
        solves={"sluice_gate"},
        use_text="With a steady breath and a brave pull, the child caught the buried latch and dragged the choking reeds aside.",
        fail_text="The pole found the reeds, yet the child could not quite reach the buried latch before the water spilled over.",
        qa_text="used the hook pole to pull the jam loose",
        tags={"tool", "problem_solving"},
    ),
    "patch_kit": UtilityItem(
        id="patch_kit",
        label="patch kit",
        phrase="a waxed patch kit of cloth and cord",
        power=2,
        solves={"roof_thatch"},
        use_text="The parrot dropped one end of the cord into waiting fingers, and the child tied the patch over the torn place with quick, clever knots.",
        fail_text="The child tied the patch on bravely, but the tear was wider than the cloth and the rain still found a way through.",
        qa_text="tied the patch kit over the torn roof",
        tags={"tool", "problem_solving"},
    ),
    "spare_rope": UtilityItem(
        id="spare_rope",
        label="spare rope",
        phrase="a coil of spare rope",
        power=2,
        solves={"well_rope"},
        use_text="Guided by the parrot's shrill calls, the child looped a sure knot, lowered the line, and drew the lost bucket home.",
        fail_text="The child lowered the new rope, but the worn knot slipped once before it held, and precious time went by.",
        qa_text="used spare rope to bring the bucket back up",
        tags={"tool", "problem_solving"},
    ),
}

PARROTS = {
    "green": ParrotKind(
        id="green",
        color="green",
        cry="Look there",
        talent="sharp eyes",
        scout_text="The parrot had seen the trouble before any grown-up did.",
        carry_text="Pip fluttered at the child's cheek and kept calling the true place to aim.",
        tags={"parrot"},
    ),
    "gold": ParrotKind(
        id="gold",
        color="gold-winged",
        cry="Quick now",
        talent="loud warning calls",
        scout_text="The parrot had marked the danger from above and would not stop shouting toward it.",
        carry_text="Pip wheeled once over the danger and cried again, showing exactly where help was needed.",
        tags={"parrot"},
    ),
    "blue": ParrotKind(
        id="blue",
        color="blue-feathered",
        cry="This way",
        talent="steady circling",
        scout_text="The parrot kept circling the bad place until everyone finally looked where it looked.",
        carry_text="Pip beat the air above the child, turning fear into a kind of direction.",
        tags={"parrot"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Nala", "Tavi", "Suri", "Asha", "Rina", "Luma"]
BOY_NAMES = ["Kiran", "Batu", "Hari", "Milo", "Tarin", "Ravi", "Jorin", "Niko"]
ELDER_NAMES = ["Old Beren", "Edda", "Marta", "Tomas", "Sela", "Harin"]
TRAITS = ["patient", "quick-minded", "steady", "careful", "resourceful"]


@dataclass
class StoryParams:
    setting: str
    problem: str
    utility: str
    parrot: str
    hero_name: str
    hero_gender: str
    elder_name: str
    elder_type: str
    trait: str
    delay: int = 0
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        setting="riverside",
        problem="sluice_gate",
        utility="hook_pole",
        parrot="green",
        hero_name="Lina",
        hero_gender="girl",
        elder_name="Old Beren",
        elder_type="elder",
        trait="steady",
        delay=0,
    ),
    StoryParams(
        setting="granary",
        problem="roof_thatch",
        utility="patch_kit",
        parrot="gold",
        hero_name="Kiran",
        hero_gender="boy",
        elder_name="Marta",
        elder_type="elder",
        trait="resourceful",
        delay=0,
    ),
    StoryParams(
        setting="wellside",
        problem="well_rope",
        utility="spare_rope",
        parrot="blue",
        hero_name="Asha",
        hero_gender="girl",
        elder_name="Tomas",
        elder_type="elder",
        trait="patient",
        delay=1,
    ),
    StoryParams(
        setting="riverside",
        problem="sluice_gate",
        utility="hook_pole",
        parrot="gold",
        hero_name="Hari",
        hero_gender="boy",
        elder_name="Sela",
        elder_type="elder",
        trait="quick-minded",
        delay=2,
    ),
]


KNOWLEDGE = {
    "parrot": [
        (
            "What is a parrot?",
            "A parrot is a bird with a curved beak and strong feet. Many parrots can copy sounds, and they are often very alert."
        )
    ],
    "tool": [
        (
            "What is a tool?",
            "A tool is something you use to do a job more easily. A good tool helps your hands solve a problem."
        )
    ],
    "problem_solving": [
        (
            "What is problem solving?",
            "Problem solving means noticing what is wrong, thinking about what could help, and then trying the best useful step."
        )
    ],
    "river": [
        (
            "Why can a river be dangerous near a mill?",
            "If water is blocked, it can rise and spill where it should not go. Fast water can soak grain and damage buildings."
        )
    ],
    "storm": [
        (
            "Why should people fix a roof before rain?",
            "A hole in a roof lets water in. Rain can spoil food, bedding, and other things that need to stay dry."
        )
    ],
    "well": [
        (
            "Why is a well important in a village?",
            "A well gives people water for drinking and cooking. Without a working bucket and rope, getting water becomes hard."
        )
    ],
    "water": [
        (
            "Why do people need water every day?",
            "People need water to drink and to make food. Villages also use water for washing and other daily work."
        )
    ],
    "grain": [
        (
            "Why must grain stay dry?",
            "Dry grain can be stored for a long time. Wet grain can swell, spoil, and become useless for bread or porridge."
        )
    ],
    "flood": [
        (
            "What is a flood?",
            "A flood is water spilling over onto land where it should not be. Floods can ruin things very quickly."
        )
    ],
    "roof": [
        (
            "What does a roof do?",
            "A roof covers a building and helps keep rain, wind, and sun off the things inside."
        )
    ],
    "village": [
        (
            "What is a village elder?",
            "A village elder is an older person people listen to for guidance. Good elders should be fair and wise."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "parrot",
    "tool",
    "problem_solving",
    "river",
    "flood",
    "storm",
    "roof",
    "well",
    "water",
    "grain",
    "village",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    problem = f["problem"]
    utility = f["utility"]
    setting = f["setting"]
    parrot = f["parrot"]
    return [
        'Write a short folk tale for a 3-to-5-year-old that includes the words "parrot", "utility", and "stigmatize".',
        f"Tell a folk-tale story where a child named {hero.id} is mocked for carrying a utility satchel and listening to a parrot, but uses {utility.label} to solve {problem.label} in {setting.place}.",
        f"Write a cautionary village tale about bravery and problem solving, where people learn not to stigmatize a humble helper after {parrot.label} warns of danger.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    parrot = f["parrot"]
    problem = f["problem"]
    utility = f["utility"]
    setting = f["setting"]
    success = f["success"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child in {setting.place}, and Pip the parrot. It is also about the villagers who first mocked them and later learned from them."
        ),
        (
            "Why did the villagers hurt the child's feelings?",
            f"They laughed at the utility satchel and the noisy parrot and treated them as if they were foolish. The story says it is wrong to stigmatize something useful just because it looks strange or plain."
        ),
        (
            "What problem did Pip notice?",
            f"Pip noticed that {problem.sign[0].lower() + problem.sign[1:]} {problem.risk} The parrot's warning mattered because it gave the village a chance to act."
        ),
        (
            f"How was {hero.id} brave?",
            f"{hero.id} was brave because {hero.pronoun()} stepped toward {problem.action_place} even while feeling afraid. {hero.pronoun().capitalize()} chose careful action instead of hiding from the danger."
        ),
    ]
    if success:
        qa.append(
            (
                f"How did {hero.id} solve the problem?",
                f"{hero.pronoun().capitalize()} {utility.qa_text}. The satchel was useful because it held the exact thing the problem needed."
            )
        )
        qa.append(
            (
                "What did the elder learn?",
                f"{elder.id} learned that the village had been unfair. {elder.pronoun().capitalize()} admitted it was wrong to stigmatize the parrot and the plain utility satchel after they helped save everyone from trouble."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the village safe and the child finally honored. Pip perched proudly where everyone could see that the warning bird had told the truth."
            )
        )
    else:
        qa.append(
            (
                f"Did the child still help even though some harm happened?",
                f"Yes. {hero.id} worked bravely with {utility.label}, but the danger had already grown too strong. The story is cautionary because delay and mockery cost the village precious time."
            )
        )
        qa.append(
            (
                "What lesson did the village learn after the loss?",
                f"They learned that sneering at good help wastes time. By the time they stopped mocking and started listening, part of the damage had already happened."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with tired people mending what they could and remembering the warning. The ending is sadder, but it still shows the child and parrot as honest helpers."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set()
    tags |= set(f["setting"].tags)
    tags |= set(f["problem"].tags)
    tags |= set(f["utility"].tags)
    tags |= set(f["parrot_kind"].tags)
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
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% valid choices: the setting must host the problem, and the utility must truly solve it
valid(S, P, U) :- setting(S), affords(S, P), utility(U), solves(U, P).

% outcome model: a matching utility saves the village if its power reaches the danger + delay
severity(V) :- chosen_problem(P), danger(P, D), delay(L), V = D + L.
saved :- chosen_utility(U), power(U, P), severity(V), P >= V.
outcome(saved) :- saved.
outcome(loss) :- not saved.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for sid, setting in SETTINGS.items():
        for pid in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, pid))
    for pid, problem in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("danger", pid, problem.danger))
    for uid, utility in UTILITIES.items():
        lines.append(asp.fact("utility", uid))
        lines.append(asp.fact("power", uid, utility.power))
        for pid in sorted(utility.solves):
            lines.append(asp.fact("solves", uid, pid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_problem", params.problem),
        asp.fact("chosen_utility", params.utility),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combinations:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(30):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    mismatches = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a folk tale about a parrot, a utility satchel, bravery, and the danger of stigmatizing humble help."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--utility", choices=UTILITIES)
    ap.add_argument("--parrot", choices=PARROTS)
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--hero-name")
    ap.add_argument("--elder-name")
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long people hesitate before acting")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.problem and args.utility:
        if not valid_combo(args.setting, args.problem, args.utility):
            raise StoryError(explain_rejection(args.setting, args.problem, args.utility))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.problem is None or combo[1] == args.problem)
        and (args.utility is None or combo[2] == args.utility)
    ]
    if not combos:
        if args.setting and args.problem and args.utility:
            raise StoryError(explain_rejection(args.setting, args.problem, args.utility))
        raise StoryError("(No valid combination matches the given options.)")

    setting, problem, utility = rng.choice(combos)
    parrot = args.parrot or rng.choice(sorted(PARROTS))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    elder_name = args.elder_name or rng.choice(ELDER_NAMES)
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.choice([0, 0, 1, 2])

    return StoryParams(
        setting=setting,
        problem=problem,
        utility=utility,
        parrot=parrot,
        hero_name=hero_name,
        hero_gender=hero_gender,
        elder_name=elder_name,
        elder_type="elder",
        trait=trait,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(No story: unknown setting '{params.setting}'.)")
    if params.problem not in PROBLEMS:
        raise StoryError(f"(No story: unknown problem '{params.problem}'.)")
    if params.utility not in UTILITIES:
        raise StoryError(f"(No story: unknown utility item '{params.utility}'.)")
    if params.parrot not in PARROTS:
        raise StoryError(f"(No story: unknown parrot kind '{params.parrot}'.)")
    if params.hero_gender not in {"girl", "boy"}:
        raise StoryError(f"(No story: unknown hero gender '{params.hero_gender}'.)")
    if not valid_combo(params.setting, params.problem, params.utility):
        raise StoryError(explain_rejection(params.setting, params.problem, params.utility))

    world = tell(
        SETTINGS[params.setting],
        PROBLEMS[params.problem],
        UTILITIES[params.utility],
        PARROTS[params.parrot],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        elder_name=params.elder_name,
        elder_type=params.elder_type,
        trait=params.trait,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, problem, utility) combos:\n")
        for setting, problem, utility in combos:
            print(f"  {setting:10} {problem:12} {utility}")
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
            header = f"### {p.hero_name}: {p.problem} at {p.setting} with {p.utility} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

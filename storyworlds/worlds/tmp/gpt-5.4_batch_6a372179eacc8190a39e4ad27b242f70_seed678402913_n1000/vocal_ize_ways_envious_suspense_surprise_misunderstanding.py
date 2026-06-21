#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/vocal_ize_ways_envious_suspense_surprise_misunderstanding.py
=======================================================================================

A standalone story world about two children playing superheroes when a small
"city emergency" interrupts their game. One child is given the loud signaling
job, the other is given the less flashy rescue job. The second child grows
envious and misunderstands the assignment as favoritism. Suspense rises while a
missing creature stays hidden. Then comes a surprise: the glittery signal role
was not the whole mission at all, and the supposedly plain rescue skill is what
actually saves the day.

This world keeps a small reasonableness gate:

    setting + problem + signal + skill

A story is only valid when:
- the setting can host that problem,
- the chosen signal can truly reach the hidden target in that kind of place,
- and the chosen rescue skill can actually solve the physical snag.

The prose is state-driven: envy, misunderstanding, worry, clue-finding, rescue,
and relief all come from the simulated world model.

Run it
------
    python storyworlds/worlds/gpt-5.4/vocal_ize_ways_envious_suspense_surprise_misunderstanding.py
    python storyworlds/worlds/gpt-5.4/vocal_ize_ways_envious_suspense_surprise_misunderstanding.py --setting playground --problem roof_puppy
    python storyworlds/worlds/gpt-5.4/vocal_ize_ways_envious_suspense_surprise_misunderstanding.py --signal whistle --problem stage_bunny
    python storyworlds/worlds/gpt-5.4/vocal_ize_ways_envious_suspense_surprise_misunderstanding.py --all
    python storyworlds/worlds/gpt-5.4/vocal_ize_ways_envious_suspense_surprise_misunderstanding.py --qa --json
    python storyworlds/worlds/gpt-5.4/vocal_ize_ways_envious_suspense_surprise_misunderstanding.py --verify
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
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(
            self.type, self.type
        )


@dataclass
class Setting:
    id: str
    place: str
    scene: str
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    target_label: str
    target_phrase: str
    cry: str
    place_detail: str
    signal_need: str
    skill_need: str
    suspense: str
    clue: str
    rescue_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Signal:
    id: str
    label: str
    phrase: str
    verb: str
    supports: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Skill:
    id: str
    label: str
    phrase: str
    helps: set[str] = field(default_factory=set)
    action: str = ""
    reveal: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        return World(
            setting=self.setting,
            entities=copy.deepcopy(self.entities),
            fired=set(self.fired),
            paragraphs=[[]],
            facts=copy.deepcopy(self.facts),
        )


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_missing_worry(world: World) -> list[str]:
    target = world.entities.get("target")
    if target is None or target.meters["missing"] < THRESHOLD:
        return []
    sig = ("missing_worry", target.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for ent in world.characters():
        if ent.role in {"captain", "rescuer", "organizer"}:
            ent.memes["worry"] += 1
    return []


def _r_envy_to_misunderstanding(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.memes["envy"] < THRESHOLD or ent.memes["left_out"] < THRESHOLD:
            continue
        sig = ("misunderstanding", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["misunderstanding"] += 1
        out.append("__misunderstanding__")
    return out


def _r_found_relief(world: World) -> list[str]:
    target = world.entities.get("target")
    if target is None or target.meters["found"] < THRESHOLD:
        return []
    sig = ("found_relief", target.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for ent in world.characters():
        if ent.role in {"captain", "rescuer", "organizer"}:
            ent.memes["relief"] += 1
            ent.memes["worry"] = 0.0
    return []


CAUSAL_RULES = [
    Rule(name="missing_worry", tag="emotion", apply=_r_missing_worry),
    Rule(name="envy_to_misunderstanding", tag="emotion", apply=_r_envy_to_misunderstanding),
    Rule(name="found_relief", tag="emotion", apply=_r_found_relief),
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


SETTINGS = {
    "playground": Setting(
        id="playground",
        place="the playground",
        scene="The slide was a silver launch ramp, the sandbox was Moon Dust Square, and the benches were watchtowers.",
        affords={"roof_puppy", "hedge_kitten"},
        tags={"playground", "outside"},
    ),
    "courtyard": Setting(
        id="courtyard",
        place="the apartment courtyard",
        scene="The brick walls rose like a hero canyon, and every balcony looked like a secret headquarters.",
        affords={"hedge_kitten", "balcony_parrot"},
        tags={"courtyard", "outside"},
    ),
    "hall": Setting(
        id="hall",
        place="the community hall",
        scene="The folding chairs became city blocks, the little stage became Hero Plaza, and the curtains hid a thousand shadows.",
        affords={"stage_bunny"},
        tags={"hall", "inside"},
    ),
}

PROBLEMS = {
    "hedge_kitten": Problem(
        id="hedge_kitten",
        target_label="kitten",
        target_phrase="the mayor's striped kitten",
        cry='"The mayor\'s kitten is gone!"',
        place_detail="inside a prickly hedge tunnel where only a small hero could fit",
        signal_need="near_hidden",
        skill_need="crawl",
        suspense="Every rustle in the leaves made the children freeze for a second.",
        clue="a tiny mew from deep inside the hedge",
        rescue_image="came out with the kitten blinking in the green shade",
        tags={"kitten", "pet", "rescue"},
    ),
    "roof_puppy": Problem(
        id="roof_puppy",
        target_label="puppy",
        target_phrase="the bakery's little puppy",
        cry='"The bakery puppy is on the snack shed!"',
        place_detail="on the flat roof of the low snack shed, too far for a normal shout in the wind",
        signal_need="far_open",
        skill_need="balance",
        suspense="The puppy's paws scritched on the roof, and nobody wanted it to slip.",
        clue="a scared yip above the bunting",
        rescue_image="reached the puppy by stepping carefully along the wide practice beam while a grown-up steadied the ladder",
        tags={"puppy", "pet", "rescue"},
    ),
    "stage_bunny": Problem(
        id="stage_bunny",
        target_label="bunny",
        target_phrase="the white rabbit mascot puppet",
        cry='"The parade bunny has vanished before the show!"',
        place_detail="under the stage curtain in a dim pocket of dust and chair legs",
        signal_need="echo_corners",
        skill_need="crawl",
        suspense="The curtain twitched whenever someone walked by, but nobody could see what was under it.",
        clue="a soft thump and the tip of a white ear under the curtain hem",
        rescue_image="ducked low, slid under the stage, and lifted the bunny puppet out by its blue cape",
        tags={"bunny", "puppet", "rescue"},
    ),
    "balcony_parrot": Problem(
        id="balcony_parrot",
        target_label="parrot",
        target_phrase="Mrs. Vale's bright green parrot",
        cry='"Mrs. Vale\'s parrot flew into the ivy!"',
        place_detail="in the ivy by the first-floor balcony, where a harsh noise would only frighten it more",
        signal_need="courtyard_call",
        skill_need="gentle",
        suspense="The ivy shook, then went still, and the children stared upward without breathing.",
        clue="a tiny green tail feather between the leaves",
        rescue_image="held out a sunflower seed on a flat palm until the parrot stepped down softly",
        tags={"parrot", "pet", "rescue"},
    ),
}

SIGNALS = {
    "whistle": Signal(
        id="whistle",
        label="whistle",
        phrase="a silver hero whistle",
        verb="blew a sharp bright note",
        supports={"far_open"},
        tags={"whistle", "sound"},
    ),
    "megaphone": Signal(
        id="megaphone",
        label="megaphone",
        phrase="a red thunder megaphone",
        verb="vocal-ized clues through the thunder megaphone",
        supports={"far_open", "echo_corners", "courtyard_call"},
        tags={"megaphone", "sound"},
    ),
    "hero_call": Signal(
        id="hero_call",
        label="hero call",
        phrase="a hand-cupped hero call",
        verb="called in a calm superhero voice",
        supports={"near_hidden", "courtyard_call"},
        tags={"call", "sound"},
    ),
}

SKILLS = {
    "crawl": Skill(
        id="crawl",
        label="small-crawl skill",
        phrase="knee pads and a tiny hero flashlight",
        helps={"crawl"},
        action="got down on careful knees and crawled where the bigger hero could not go",
        reveal="the rescue needed a slim, patient hero more than a loud one",
        tags={"crawl", "teamwork"},
    ),
    "balance": Skill(
        id="balance",
        label="steady-balance skill",
        phrase="grippy shoes and brave, slow feet",
        helps={"balance"},
        action="spread both arms and moved in one slow, steady line",
        reveal="the rescue needed calm balance more than flashy gear",
        tags={"balance", "teamwork"},
    ),
    "gentle": Skill(
        id="gentle",
        label="gentle-hands skill",
        phrase="a sunflower seed and extra-soft hands",
        helps={"gentle"},
        action="kept still, lowered the voice, and offered one patient hand",
        reveal="the rescue needed gentleness more than noise",
        tags={"gentle", "teamwork"},
    ),
}

GIRL_NAMES = ["Maya", "Lila", "Nora", "Ava", "Ruby", "Zoe", "Mina", "Ella"]
BOY_NAMES = ["Kai", "Leo", "Max", "Finn", "Owen", "Eli", "Theo", "Jude"]
TRAITS = ["brisk", "bright", "careful", "bold", "kind", "quick"]


@dataclass
class StoryParams:
    setting: str
    problem: str
    signal: str
    skill: str
    captain_name: str
    captain_gender: str
    rescuer_name: str
    rescuer_gender: str
    organizer: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        setting="playground",
        problem="roof_puppy",
        signal="whistle",
        skill="balance",
        captain_name="Kai",
        captain_gender="boy",
        rescuer_name="Maya",
        rescuer_gender="girl",
        organizer="aunt",
        trait="careful",
    ),
    StoryParams(
        setting="courtyard",
        problem="balcony_parrot",
        signal="hero_call",
        skill="gentle",
        captain_name="Ruby",
        captain_gender="girl",
        rescuer_name="Leo",
        rescuer_gender="boy",
        organizer="father",
        trait="kind",
    ),
    StoryParams(
        setting="hall",
        problem="stage_bunny",
        signal="megaphone",
        skill="crawl",
        captain_name="Finn",
        captain_gender="boy",
        rescuer_name="Lila",
        rescuer_gender="girl",
        organizer="mother",
        trait="bright",
    ),
    StoryParams(
        setting="courtyard",
        problem="hedge_kitten",
        signal="hero_call",
        skill="crawl",
        captain_name="Nora",
        captain_gender="girl",
        rescuer_name="Max",
        rescuer_gender="boy",
        organizer="uncle",
        trait="quick",
    ),
]


def signal_fits(problem: Problem, signal: Signal) -> bool:
    return problem.signal_need in signal.supports


def skill_fits(problem: Problem, skill: Skill) -> bool:
    return problem.skill_need in skill.helps


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for problem_id in sorted(setting.affords):
            problem = PROBLEMS[problem_id]
            for signal_id, signal in SIGNALS.items():
                if not signal_fits(problem, signal):
                    continue
                for skill_id, skill in SKILLS.items():
                    if skill_fits(problem, skill):
                        combos.append((setting_id, problem_id, signal_id, skill_id))
    return sorted(combos)


def explain_rejection(setting: Setting, problem: Problem, signal: Signal, skill: Skill) -> str:
    if problem.id not in setting.affords:
        return (
            f"(No story: {setting.place} does not host the {problem.target_label} problem here. "
            f"Pick a problem that fits the place.)"
        )
    if not signal_fits(problem, signal):
        return (
            f"(No story: {signal.label} is not a sensible way to reach someone {problem.place_detail}. "
            f"The signal has to match how the clue can travel.)"
        )
    if not skill_fits(problem, skill):
        return (
            f"(No story: {skill.label} cannot solve a rescue that needs {problem.skill_need}. "
            f"The rescuer's special move must truly fit the snag.)"
        )
    return "(No story: that combination is not supported.)"


def organizer_word(org_type: str) -> str:
    return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}[org_type]


def introduce(world: World, captain: Entity, rescuer: Entity, organizer: Entity) -> None:
    world.say(
        f"On Hero Day at {world.setting.place}, {captain.id} and {rescuer.id} were not ordinary children. "
        f"They were cape-swirling protectors of the neighborhood. {world.setting.scene}"
    )
    world.say(
        f"{captain.id} loved big announcements, and {rescuer.id} loved clever little rescue moves. "
        f"{organizer.label_word.capitalize()} watched with a smile and called them the Sky Team."
    )


def mission_arrives(world: World, problem: Problem, target: Entity) -> None:
    target.meters["missing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then the game turned into a real mission. Someone ran across the square and cried, {problem.cry}"
    )
    world.say(
        f"In one breath the pretend city felt serious. {problem.suspense}"
    )


def assign_roles(
    world: World,
    captain: Entity,
    rescuer: Entity,
    organizer: Entity,
    signal: Signal,
    skill: Skill,
    problem: Problem,
) -> None:
    captain.attrs["signal"] = signal.id
    rescuer.attrs["skill"] = skill.id
    captain.memes["pride"] += 1
    rescuer.memes["left_out"] += 1
    world.say(
        f'{organizer.label_word.capitalize()} handed {captain.id} {signal.phrase} and said, '
        f'"You take the sky voice. In this mission, we need someone to vocal-ize clues the right way."'
    )
    world.say(
        f'Then {organizer.pronoun()} knelt beside {rescuer.id} and tapped {skill.phrase}. '
        f'"And you take the rescue job. There are different ways to be a hero today."'
    )
    world.facts["assignment_reason"] = (
        f"The signal had to fit a target hidden {problem.place_detail}, and the rescue needed {skill.label}."
    )


def grow_envy(world: World, rescuer: Entity, captain: Entity, signal: Signal, skill: Skill) -> None:
    rescuer.memes["envy"] += 1
    propagate(world, narrate=False)
    rescuer.attrs["misread"] = "favorite"
    world.say(
        f"{rescuer.id} stared at the shiny {signal.label}. To {rescuer.pronoun('object')}, the loud job looked grander than {skill.phrase}."
    )
    world.say(
        f"{rescuer.pronoun().capitalize()} felt envious and made a mistake inside {rescuer.pronoun('possessive')} own mind: "
        f"{rescuer.pronoun()} decided {captain.id} must be the favorite hero."
    )


def search(world: World, captain: Entity, rescuer: Entity, problem: Problem, signal: Signal) -> None:
    world.say(
        f"They hurried toward the clue zone. {captain.id} {signal.verb}, and the sound moved exactly the way the mission needed."
    )
    world.say(
        f"For a moment nothing answered. That quiet stretch made the search feel even more suspenseful."
    )
    world.say(
        f"Then at last they heard {problem.clue}."
    )
    target = world.get("target")
    target.meters["located"] += 1
    world.facts["clue_found"] = True


def rescue(
    world: World,
    rescuer: Entity,
    captain: Entity,
    organizer: Entity,
    problem: Problem,
    skill: Skill,
) -> None:
    target = world.get("target")
    world.say(
        f"But finding the clue was only half the mission. {problem.place_detail[0].upper()}{problem.place_detail[1:]}, and {captain.id} could not finish the rescue alone."
    )
    world.say(
        f"That was the surprise. {rescuer.id}'s plain-looking job was the key one."
    )
    world.say(
        f"{rescuer.id} {skill.action}. A second later, {rescuer.pronoun()} {problem.rescue_image}."
    )
    target.meters["found"] += 1
    target.meters["missing"] = 0.0
    propagate(world, narrate=False)
    rescuer.memes["pride"] += 1
    captain.memes["admiration"] += 1
    world.facts["surprise_line"] = skill.reveal


def reconcile(world: World, rescuer: Entity, captain: Entity, organizer: Entity, target: Entity, problem: Problem) -> None:
    rescuer.memes["envy"] = 0.0
    rescuer.memes["misunderstanding"] = 0.0
    rescuer.memes["understanding"] += 1
    captain.memes["love"] += 1
    rescuer.memes["love"] += 1
    world.say(
        f'{captain.id} grinned so hard that the cape on {captain.pronoun("possessive")} shoulders bounced. '
        f'"You saved {target.label}!" {captain.pronoun()} shouted.'
    )
    world.say(
        f'{organizer.label_word.capitalize()} pulled both children close and said, '
        f'"A superhero team is not built from one glittery job. It is built from the right jobs."'
    )
    world.say(
        f"At last {rescuer.id} understood. {rescuer.pronoun().capitalize()} had not been pushed aside at all. "
        f"{rescuer.pronoun().capitalize()} had been trusted with the part only {rescuer.pronoun()} could do."
    )
    world.say(
        f"When the cheers spread across {world.setting.place}, the two heroes stood shoulder to shoulder, "
        f"and even the rescued {problem.target_label} seemed to know the city was safe again."
    )


def tell(
    setting: Setting,
    problem: Problem,
    signal: Signal,
    skill: Skill,
    captain_name: str = "Kai",
    captain_gender: str = "boy",
    rescuer_name: str = "Maya",
    rescuer_gender: str = "girl",
    organizer_type: str = "aunt",
    trait: str = "kind",
) -> World:
    world = World(setting=setting)
    captain = world.add(
        Entity(
            id=captain_name,
            kind="character",
            type=captain_gender,
            role="captain",
            label=captain_name,
            traits=["loud", trait],
        )
    )
    rescuer = world.add(
        Entity(
            id=rescuer_name,
            kind="character",
            type=rescuer_gender,
            role="rescuer",
            label=rescuer_name,
            traits=["nimble", trait],
        )
    )
    organizer = world.add(
        Entity(
            id="Organizer",
            kind="character",
            type=organizer_type,
            role="organizer",
            label="the organizer",
        )
    )
    target = world.add(
        Entity(
            id="target",
            kind="thing",
            type="target",
            label=problem.target_label,
            phrase=problem.target_phrase,
            tags=set(problem.tags),
        )
    )

    introduce(world, captain, rescuer, organizer)
    world.para()
    mission_arrives(world, problem, target)
    assign_roles(world, captain, rescuer, organizer, signal, skill, problem)
    grow_envy(world, rescuer, captain, signal, skill)
    world.para()
    search(world, captain, rescuer, problem, signal)
    rescue(world, rescuer, captain, organizer, problem, skill)
    world.para()
    reconcile(world, rescuer, captain, organizer, target, problem)

    world.facts.update(
        captain=captain,
        rescuer=rescuer,
        organizer=organizer,
        target=target,
        setting=setting,
        problem=problem,
        signal=signal,
        skill=skill,
        misunderstanding=rescuer.attrs.get("misread", "") == "favorite",
        rescued=target.meters["found"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "whistle": [
        (
            "What does a whistle do?",
            "A whistle makes a sharp sound that travels far, so people can hear it across an open place.",
        )
    ],
    "megaphone": [
        (
            "What is a megaphone?",
            "A megaphone makes a voice louder, so a person can call directions for a crowd or across a big room.",
        )
    ],
    "call": [
        (
            "What does it mean to vocal-ize a clue?",
            "It means to say the clue out loud so teammates can hear it clearly. Heroes and helpers use their voices on purpose.",
        )
    ],
    "crawl": [
        (
            "Why is crawling useful in a rescue?",
            "Crawling helps someone get into a low or narrow place safely. Sometimes the smallest careful move solves the biggest problem.",
        )
    ],
    "balance": [
        (
            "Why does balance matter?",
            "Good balance helps you move slowly and carefully without wobbling. That is important when someone is up high or scared.",
        )
    ],
    "gentle": [
        (
            "Why do gentle hands help with animals?",
            "Gentle hands and a calm body help frightened animals feel safe. Loud grabbing can scare them more.",
        )
    ],
    "envy": [
        (
            "What does envious mean?",
            "Envious means wishing you had someone else's special thing or job. The feeling can make you misunderstand what is really happening.",
        )
    ],
    "teamwork": [
        (
            "Why do teams use different ways to help?",
            "Different jobs fit different problems. A good team does not need everyone to do the same thing; it needs the right person in the right place.",
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone thinks something means one thing, but it really means another. Talking and listening can clear it up.",
        )
    ],
}
KNOWLEDGE_ORDER = ["call", "whistle", "megaphone", "crawl", "balance", "gentle", "envy", "misunderstanding", "teamwork"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    captain = f["captain"]
    rescuer = f["rescuer"]
    problem = f["problem"]
    signal = f["signal"]
    return [
        (
            'Write a short superhero story for a 3-to-5-year-old that includes the words '
            '"vocal-ize", "ways", and "envious", and uses suspense, surprise, and a misunderstanding.'
        ),
        (
            f"Tell a gentle superhero rescue story where {rescuer.id} feels envious when {captain.id} gets {signal.phrase}, "
            f"but the surprise is that {rescuer.id} is the one who can finally save {problem.target_phrase}."
        ),
        (
            f"Write a story about two child heroes learning that there are different ways to help, "
            f"and that the loudest-looking job is not always the most important one."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    captain = f["captain"]
    rescuer = f["rescuer"]
    organizer = f["organizer"]
    problem = f["problem"]
    signal = f["signal"]
    skill = f["skill"]
    target = f["target"]

    qa: list[tuple[str, str]] = [
        (
            "Who are the main heroes in the story?",
            f"The main heroes are {captain.id} and {rescuer.id}, two children playing superheroes together. "
            f"{organizer.label_word.capitalize()} guides them when the rescue begins.",
        ),
        (
            f"What was the emergency?",
            f"The emergency was that {problem.target_phrase} was missing. "
            f"That turned their superhero game into a real mission and made everyone worry.",
        ),
        (
            f"Why did {rescuer.id} feel envious?",
            f"{rescuer.id} saw {captain.id} get {signal.phrase} and thought that shiny job meant {captain.id} was the favorite hero. "
            f"That was the misunderstanding, because the jobs were chosen to fit the rescue, not to choose a favorite.",
        ),
        (
            f"Why was {signal.label} given to {captain.id}?",
            f"It was given to {captain.id} because the clue had to travel the right way to reach a target hidden {problem.place_detail}. "
            f"The signal job matched the place, so it helped the team find the missing {target.label}.",
        ),
        (
            "What was the surprise in the middle of the story?",
            f"The surprise was that finding the clue did not finish the mission. "
            f"The real rescue needed {rescuer.id}'s {skill.label}, so the less flashy job became the most important one.",
        ),
        (
            f"How was the rescue finished?",
            f"{rescuer.id} used {skill.phrase} and {skill.action}. "
            f"That is how {rescuer.pronoun()} brought the {target.label} back safely.",
        ),
        (
            "How did the misunderstanding end?",
            f"It ended when {rescuer.id} saw that the team needed different ways to help. "
            f"After the rescue, {rescuer.pronoun()} understood that being trusted with the right job is another kind of superhero honor.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = set()
    tags |= world.facts["signal"].tags
    tags |= world.facts["skill"].tags
    tags |= {"envy", "misunderstanding"}
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
    for ent in world.entities.values():
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
        lines.append(f"  {ent.id:10} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
signal_fits(P, S) :- needs_signal(P, Need), supports(S, Need).
skill_fits(P, K)  :- needs_skill(P, Need), helps(K, Need).
valid(St, P, S, K) :- affords(St, P), signal_fits(P, S), skill_fits(P, K).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        for problem_id in sorted(setting.affords):
            lines.append(asp.fact("affords", setting_id, problem_id))
    for problem_id, problem in PROBLEMS.items():
        lines.append(asp.fact("problem", problem_id))
        lines.append(asp.fact("needs_signal", problem_id, problem.signal_need))
        lines.append(asp.fact("needs_skill", problem_id, problem.skill_need))
    for signal_id, signal in SIGNALS.items():
        lines.append(asp.fact("signal", signal_id))
        for need in sorted(signal.supports):
            lines.append(asp.fact("supports", signal_id, need))
    for skill_id, skill in SKILLS.items():
        lines.append(asp.fact("skill", skill_id))
        for need in sorted(skill.helps):
            lines.append(asp.fact("helps", skill_id, need))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid combos:")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated empty story.)")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        params = resolve_params(build_parser().parse_args([]), random.Random(7))
        sample = generate(params)
        if not sample.story.strip():
            raise StoryError("(Random smoke test failed: generated empty story.)")
        print("OK: random seeded generation succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"RANDOM SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: superhero children, envy, misunderstanding, suspense, and a surprise rescue."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--signal", choices=SIGNALS)
    ap.add_argument("--skill", choices=SKILLS)
    ap.add_argument("--captain")
    ap.add_argument("--rescuer")
    ap.add_argument("--captain-gender", choices=["girl", "boy"])
    ap.add_argument("--rescuer-gender", choices=["girl", "boy"])
    ap.add_argument("--organizer", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.problem and args.problem not in SETTINGS[args.setting].affords:
        raise StoryError(
            f"(No story: {SETTINGS[args.setting].place} does not host the problem '{args.problem}'.)"
        )

    if args.problem and args.signal:
        problem = PROBLEMS[args.problem]
        signal = SIGNALS[args.signal]
        if not signal_fits(problem, signal):
            setting = SETTINGS[args.setting] if args.setting else next(iter(SETTINGS.values()))
            skill = SKILLS[args.skill] if args.skill else next(iter(SKILLS.values()))
            raise StoryError(explain_rejection(setting, problem, signal, skill))

    if args.problem and args.skill:
        problem = PROBLEMS[args.problem]
        skill = SKILLS[args.skill]
        if not skill_fits(problem, skill):
            setting = SETTINGS[args.setting] if args.setting else next(iter(SETTINGS.values()))
            signal = SIGNALS[args.signal] if args.signal else next(iter(SIGNALS.values()))
            raise StoryError(explain_rejection(setting, problem, signal, skill))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.problem is None or combo[1] == args.problem)
        and (args.signal is None or combo[2] == args.signal)
        and (args.skill is None or combo[3] == args.skill)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, problem_id, signal_id, skill_id = rng.choice(sorted(combos))
    captain_gender = args.captain_gender or rng.choice(["girl", "boy"])
    rescuer_gender = args.rescuer_gender or rng.choice(["girl", "boy"])
    captain_name = args.captain or _pick_name(rng, captain_gender)
    rescuer_name = args.rescuer or _pick_name(rng, rescuer_gender, avoid=captain_name)
    organizer = args.organizer or rng.choice(["mother", "father", "aunt", "uncle"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id,
        problem=problem_id,
        signal=signal_id,
        skill=skill_id,
        captain_name=captain_name,
        captain_gender=captain_gender,
        rescuer_name=rescuer_name,
        rescuer_gender=rescuer_gender,
        organizer=organizer,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Invalid setting: {params.setting})")
    if params.problem not in PROBLEMS:
        raise StoryError(f"(Invalid problem: {params.problem})")
    if params.signal not in SIGNALS:
        raise StoryError(f"(Invalid signal: {params.signal})")
    if params.skill not in SKILLS:
        raise StoryError(f"(Invalid skill: {params.skill})")

    setting = SETTINGS[params.setting]
    problem = PROBLEMS[params.problem]
    signal = SIGNALS[params.signal]
    skill = SKILLS[params.skill]
    if params.problem not in setting.affords or not signal_fits(problem, signal) or not skill_fits(problem, skill):
        raise StoryError(explain_rejection(setting, problem, signal, skill))

    world = tell(
        setting=setting,
        problem=problem,
        signal=signal,
        skill=skill,
        captain_name=params.captain_name,
        captain_gender=params.captain_gender,
        rescuer_name=params.rescuer_name,
        rescuer_gender=params.rescuer_gender,
        organizer_type=params.organizer,
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, problem, signal, skill) combos:\n")
        for setting_id, problem_id, signal_id, skill_id in combos:
            print(f"  {setting_id:10} {problem_id:14} {signal_id:10} {skill_id}")
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
                f"### {p.captain_name} & {p.rescuer_name}: "
                f"{p.problem} at {p.setting} ({p.signal}, {p.skill})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

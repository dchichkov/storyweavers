#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.3-codex-spark/jeans_whirl_humor_happy_ending_problem_solving_2.py
==============================================================================

A fairy-tale style standalone storyworld from a short internal source tale:

Once upon a time, an inventive child came to the Lantern Fair wearing lucky jeans,
and a giant festival whirl began to pull at those jeans. With humor, a helper,
and careful thinking, the child fixed the snag and turned danger into a
celebration.

The implementation turns that source tale into a typed world simulation with
physical meters, emotional memes, and a reasonableness gate backed by ASP.
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    kind_word: str
    label: str
    traits: list[str] = field(default_factory=list)
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def __str__(self) -> str:
        return self.label

    def __post_init__(self) -> None:
        self.meters = defaultdict(float, self.meters)
        self.memes = defaultdict(float, self.memes)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind_word in {"girl", "mother", "aunt", "princess", "queen"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind_word in {"boy", "king", "carpenter", "villager", "fox", "dragon"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    id: str
    place: str
    wind: str
    has_water: bool
    music: str
    note: str


@dataclass
class JeansSpec:
    id: str
    adjective: str
    snugness: float
    tie_ready: bool
    loops: str
    laugh: str


@dataclass
class FixMethod:
    id: str
    label: str
    intro: str
    action: str
    needs_water: bool = False


@dataclass
class StoryParams:
    place: str
    jeans: str
    method: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


@dataclass
class StoryWorld:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    trace: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def new_paragraph(self) -> None:
        if self.paragraphs and self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def get(self, eid: str) -> Optional[Entity]:
        return self.entities.get(eid)

    def copy(self) -> "StoryWorld":
        other = StoryWorld(self.setting)
        other.entities = copy.deepcopy(self.entities)
        other.facts = copy.deepcopy(self.facts)
        return other


SOURCE_TALE = (
    "Once upon a time, a child went to the Lantern Fair in lucky jeans. When the \n"
    "festival's whirl began to roar, the child kept a brave and playful heart, and\
"
    "by thinking clearly solved the snag before anyone was hurt."
)


SETTINGS = {
    "lantern_square": Setting(
        id="lantern_square",
        place="the Lantern Square",
        wind="breezy",
        has_water=False,
        music="drums and marimbas",
        note="The lanterns blinked like tiny stars while children danced.",
    ),
    "weaving_glen": Setting(
        id="weaving_glen",
        place="weaving glen",
        wind="windy",
        has_water=True,
        music="reed flutes and laughter",
        note="A small stream ran past the festival carts.",
    ),
    "storm_knoll": Setting(
        id="storm_knoll",
        place="Storm Knoll",
        wind="gale",
        has_water=True,
        music="a brass bugle that sang like a thunderbird",
        note="The gusts made banners snap and challenge everyone to keep calm.",
    ),
}

JEANS = {
    "patch": JeansSpec(
        id="patch",
        adjective="patch-work",
        snugness=0.55,
        tie_ready=False,
        loops="loopy pockets and uneven seams",
        laugh="one pocket was so proud it sat where the zipper should be.",
    ),
    "comet": JeansSpec(
        id="comet",
        adjective="comet blue",
        snugness=0.72,
        tie_ready=True,
        loops="quick knots and strong side seams",
        laugh="the right pocket always caught left socks and called it destiny.",
    ),
    "sunset": JeansSpec(
        id="sunset",
        adjective="sunset-stitch",
        snugness=0.93,
        tie_ready=True,
        loops="smooth hem and sturdy seamwork",
        laugh="the hem made a proud little flute sound whenever it brushed a floor stone.",
    ),
}

METHODS = {
    "tail_twist": FixMethod(
        id="tail_twist",
        label="a careful tail-twist tie",
        intro=(
            "They rolled the bottom hem into a neat loop, looped it around a brass peg, "
            "and made sure every knot had room to breathe."
        ),
        action=(
            "The tail no longer whipped at the Whirl's moving edge; it now swung like a sleepy ribbon."
        ),
        needs_water=False,
    ),
    "mist_crown": FixMethod(
        id="mist_crown",
        label="a crowned mist trick",
        intro=(
            "They fetched warm water from the stream and sprinkled short circles of mist "
            "while the helper kept everyone stepping back."
        ),
        action=(
            "The cloth slipped from dangerous contact and glided away from the turning board."
        ),
        needs_water=True,
    ),
    "pause_song": FixMethod(
        id="pause_song",
        label="a pause-and-song rhythm",
        intro=(
            "They and the helper led a slow, silly song that counted breaths and steps."
        ),
        action=(
            "The spinning rhythm settled, then the snag slowly dropped away as everyone waited."
        ),
        needs_water=False,
    ),
}

NAMES_BY_GENDER = {
    "girl": ["Mira", "Lina", "Tara", "Nora", "Iris", "Kira"],
    "boy": ["Theo", "Oren", "Finn", "Jude", "Leif", "Milo"],
}
TRAITS = ["clever", "curious", "bright", "kind", "playful", "brave"]

KNOWLEDGE = {
    "jeans": [
        (
            "How does snugness of jeans help during a festival whirl?",
            "A snug fit keeps cloth from being pulled into moving parts. It lowers the chance of a snag becoming a real snag in a crowded turn."
        ),
        (
            "Can loops be repaired during action without panic?",
            "Yes. A helper can make space, clear the moving edge, and stabilize the cloth. Slow, structured steps are safer than rushing."
        ),
    ],
    "whirl": [
        (
            "What makes a festival whirl dangerous when wind is strong?",
            "A strong pull can make loose fabric grab a turning surface repeatedly. Each grab adds imbalance and can throw the spin out of control."
        ),
        (
            "What usually calms a machine that began to wobble?",
            "Clear the snag source, reduce side pull, and synchronize movements with the spin rhythm. If all three happen, wobble drops quickly."
        ),
    ],
    "water": [
        (
            "Why can a mist trick work near a moving whirl?",
            "A short mist burst lowers grip and friction near the contact edge. It lets operators make safe adjustments instead of fighting a hard snag."
        )
    ],
    "wind": [
        (
            "Why did the plan differ at Storm Knoll?",
            "Strong wind makes tying less predictable, so counting and timing become safer than tugging hard on fabric."
        )
    ],
    "humor": [
        (
            "Why is humor useful in a tense moment?",
            "It lowers panic so attention stays on steps, tools, and safety. The problem is still serious, but laughter can keep hands steady."
        )
    ],
}

WIND_STEPS = {
    "breezy": 1.0,
    "windy": 1.4,
    "gale": 2.0,
}

SOURCE_TALE_NOTE = (
    "The source tale that drove this world uses one child, one risky whirl, and one kind helper "
    "solving the fabric snag with a method matched to wind, jeans, and safety."
)



def _article(word: str) -> str:
    return "an" if word[:1].lower() in {"a", "e", "i", "o", "u"} else "a"


def _clamp(v: float, minimum: float = 0.0, maximum: float = 10.0) -> float:
    return max(minimum, min(maximum, v))


def _character_word(gender: str) -> str:
    return "girl" if gender == "girl" else "boy"


def valid_plan(setting: Setting, jeans: JeansSpec, method: FixMethod) -> bool:
    if method.id == "pause_song":
        return setting.wind == "gale"
    if method.id == "tail_twist":
        return setting.wind in {"breezy", "windy"} and jeans.tie_ready and jeans.snugness >= 0.7
    if method.id == "mist_crown":
        return setting.has_water and setting.wind in {"breezy", "windy"} and jeans.snugness >= 0.55
    return False


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for jeans_id, jeans in JEANS.items():
            for method_id, method in METHODS.items():
                if valid_plan(setting, jeans, method):
                    out.append((setting_id, jeans_id, method_id))
    return sorted(out)


def explain_rejection(setting: Setting, jeans: JeansSpec, method: FixMethod) -> str:
    if method.id == "tail_twist" and not jeans.tie_ready:
        return f"No story: {jeans.adjective} jeans do not hold a reliable tail tie."
    if method.id == "tail_twist" and jeans.snugness < 0.7:
        return f"No story: {jeans.adjective} jeans are too loose for the tail-twist method."
    if method.id == "mist_crown" and not setting.has_water:
        return f"No story: mist-crown requires water and {setting.place} has none."
    if method.id == "mist_crown" and jeans.snugness < 0.55:
        return f"No story: {jeans.adjective} jeans are too frayed for a reliable mist crown."
    if method.id == "pause_song" and setting.wind != "gale":
        return f"No story: pause-and-song method is meant for gale wind, not {setting.wind} wind."
    return "No story: this exact configuration is not currently modeled."


def build_world(
    setting: Setting,
    jeans_spec: JeansSpec,
    method: FixMethod,
    name: str,
    gender: str,
    trait: str,
) -> StoryWorld:
    world = StoryWorld(setting)

    hero = world.add(
        Entity(
            id=name,
            kind="person",
            kind_word=_character_word(gender),
            label=name,
            traits=[trait],
            role="hero",
            meters={"focus": 1.0},
            memes={"curiosity": 1.0, "joy": 0.8},
        )
    )
    helper = world.add(
        Entity(
            id="Pippin",
            kind="person",
            kind_word="fox",
            label="Pippin the helper fox",
            traits=["quick", "helpful"],
            role="helper",
            meters={"focus": 0.8},
            memes={"humor": 0.9},
        )
    )
    jeans = world.add(
        Entity(
            id="hero_jeans",
            kind="thing",
            kind_word="clothing",
            label=f"{_article(jeans_spec.adjective)} {jeans_spec.adjective} pair of jeans",
            traits=[jeans_spec.adjective, "jeans", jeans_spec.loops.split(" ")[0]],
            role="gear",
            meters={"snag": 0.08, "tension": jeans_spec.snugness, "fray": 0.0},
            memes={"comfort": 0.4},
        )
    )
    whirl = world.add(
        Entity(
            id="The_Whirl",
            kind="thing",
            kind_word="whirl",
            label="the lantern Whirl",
            traits=["spinning", "festival", "metal"],
            role="device",
            meters={"spin": WIND_STEPS[setting.wind], "wobble": 0.2, "safety": 0.0},
            memes={"focus": 0.0},
        )
    )

    world.facts.update(
        setting=setting,
        hero=hero,
        helper=helper,
        jeans=jeans,
        jeans_spec=jeans_spec,
        whirl=whirl,
        method=method,
        source_tale=SOURCE_TALE_NOTE,
    )

    world.say(
        f"Once upon a time, there was {_article(trait)} {trait} {hero.kind_word} named {hero.id}. "
        f"{hero.id} loved the Lantern Fair and believed a good day always began with a funny idea and a full pair of {jeans_spec.adjective} jeans."
    )
    world.say(
        f"At {setting.place}, lanterns swayed above sweet-scented carts, and the music was {setting.music}. "
        f"{hero.id} heard Pippin whisper, '{hero.id}, if anything goes wrong, we will laugh first and think second.'"
    )
    world.say(setting.note)

    world.new_paragraph()
    world.say(
        f"When night arrived, the giant lantern Whirl spun bright rings of light. "
        f"Its spin was {setting.wind} but joyful, until a sudden burst of wind tugged {hero.id}'s jeans hem. "
        f"The cloth snagged once, then twice, and the Whirl wobbled out of rhythm."
    )
    world.say(f"{hero.id} felt the worry rise, but kept {hero.pronoun('possessive')} breath steady and said a joke about the Whirl looking for a hat rack.")
    hero.memes["worry"] = 1.6
    hero.memes["humor"] = 1.1
    jeans.meters["snag"] = 0.72
    whirl.meters["wobble"] = 1.2
    whirl.meters["safety"] = 0.1
    world.trace.append(f"diagnostic: jeans_snag={jeans.meters['snag']:.2f}, whirl_wobble={whirl.meters['wobble']:.2f}")

    world.new_paragraph()
    world.say(f"{hero.id} chose {method.label}. {method.intro}")
    if method.id == "tail_twist":
        apply_tail_twist(world)
    elif method.id == "mist_crown":
        apply_mist_crown(world)
    else:
        apply_pause_song(world)
    world.say(method.action)
    world.say(f"Then {helper.label} added, 'Now our plan has both wisdom and giggles; no one runs to the machine.'")

    world.new_paragraph()
    settle(world)

    return world


def apply_tail_twist(world: StoryWorld) -> None:
    hero = world.facts.get("hero")
    jeans = world.facts.get("jeans")
    whirl = world.facts.get("whirl")
    setting = world.setting

    if hero is None or jeans is None or whirl is None:
        raise StoryError("World state is missing required entities for tail-twist.")

    # State-driven outcomes.
    hero.memes["focus"] += 0.9
    hero.memes["courage"] += 0.7
    hero.memes["joy"] += 0.8
    jeans.meters["snag"] = _clamp(jeans.meters["snag"] * 0.18)
    whirl.meters["wobble"] = _clamp(whirl.meters["wobble"] - 0.7)
    whirl.meters["safety"] = _clamp(whirl.meters["safety"] + 0.8)
    if setting.wind == "windy":
        whirl.meters["spin"] = _clamp(whirl.meters["spin"] - 0.2)
    jeans.memes["comfort"] = _clamp(jeans.memes["comfort"] + 0.3)
    world.facts["method_effect"] = "the hem was pulled away from the moving edge and secured in place"
    world.facts["method_matter"] = "tail-twist"


def apply_mist_crown(world: StoryWorld) -> None:
    hero = world.facts.get("hero")
    jeans = world.facts.get("jeans")
    whirl = world.facts.get("whirl")

    if hero is None or jeans is None or whirl is None:
        raise StoryError("World state is missing required entities for mist-crown.")

    hero.memes["focus"] += 0.7
    hero.memes["cleverness"] += 0.9
    hero.memes["joy"] += 0.6
    jeans.meters["snag"] = _clamp(jeans.meters["snag"] * 0.24)
    jeans.meters["fray"] = _clamp(jeans.meters["fray"] + 0.1)
    whirl.meters["wobble"] = _clamp(whirl.meters["wobble"] - 0.9)
    whirl.meters["safety"] = _clamp(whirl.meters["safety"] + 0.9)
    world.facts["method_effect"] = "mist kept the fabric from sticking and gave everyone time to cool the edge"
    world.facts["method_matter"] = "mist-crown"


def apply_pause_song(world: StoryWorld) -> None:
    hero = world.facts.get("hero")
    jeans = world.facts.get("jeans")
    whirl = world.facts.get("whirl")

    if hero is None or jeans is None or whirl is None:
        raise StoryError("World state is missing required entities for pause-song.")

    hero.memes["confidence"] += 1.0
    hero.memes["humor"] += 1.0
    hero.memes["joy"] += 0.9
    jeans.meters["snag"] = _clamp(jeans.meters["snag"] * 0.12)
    whirl.meters["wobble"] = _clamp(whirl.meters["wobble"] - 1.1)
    whirl.meters["spin"] = _clamp(whirl.meters["spin"] - 0.35)
    whirl.meters["safety"] = _clamp(whirl.meters["safety"] + 1.0)
    world.facts["method_effect"] = "timed pauses cut the side pull while rhythm restored balance"
    world.facts["method_matter"] = "pause-and-song"


def settle(world: StoryWorld) -> None:
    hero = world.facts.get("hero")
    jeans = world.facts.get("jeans")
    whirl = world.facts.get("whirl")

    if hero is None or jeans is None or whirl is None:
        raise StoryError("World state is missing required entities for settlement.")

    success = jeans.meters["snag"] <= 0.32 and whirl.meters["wobble"] <= 0.55
    world.facts["snag_severity"] = round(jeans.meters["snag"], 2)
    world.facts["wobble_severity"] = round(whirl.meters["wobble"], 2)
    world.facts["spin_level"] = round(whirl.meters["spin"], 2)
    world.facts["resolved"] = bool(success)

    if not success:
        # This should be rare in configured worlds; keep explicit recovery narrative.
        world.say(
            f"The Whirl still looked restless, so {hero.id} promised to return after gathering stronger ropes and help. "
            f"The helpers kept laughing, not because it was funny now, but because hope was funny to hold on to."
        )
        hero.memes["concern"] += 0.7
        return

    hero.memes["joy"] += 1.2
    hero.memes["thankfulness"] += 0.9
    hero.memes["relief"] = _clamp(hero.memes["relief"] + 0.8)
    world.say(
        f"The last great circle came smooth and low. The Whirl steadied into gentle bells, and no part of {hero.id}'s jeans caught again. "
        f"At the ending image, {hero.id} stepped into the lantern circle wearing tidy jeans, while Pippin handed over a ribbon and everyone cheered." 
    )
    world.say(
        f"The two-word ending was clear without saying a word: the problem was solved, and the night became a story of kindness and clever play."
    )


def generation_prompts(world: StoryWorld) -> list[str]:
    hero = world.facts["hero"]
    setting = world.facts["setting"]
    method = world.facts["method"]
    jeans = world.facts["jeans_spec"]
    return [
        (
            f"Write a fairy tale about {hero.id}, who wears {jeans.adjective} jeans and keeps humor during a problem at {setting.place}."
        ),
        f"Show how the Whirl became risky and how {hero.id} used {method.label} to solve it calmly.",
        (
            "End with a concrete image proving the fabric is safe and the crowd is safe too, "
            "instead of just saying everything is fine."
        ),
    ]


def story_grounded_qa(world: StoryWorld) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    jeans = world.facts["jeans"]
    jeans_spec = world.facts["jeans_spec"]
    whirl = world.facts["whirl"]
    method = world.facts["method"]
    resolved = bool(world.facts["resolved"])
    why = world.facts.get("method_matter", "a chosen method")
    return [
        (
            f"Who is the main character in the story?",
            f"The main character is {hero.id}, a {hero.traits[0]} {hero.kind_word}. "
            f"A close companion was {helper.id}, who helped keep the crowd calm and the steps safe.",
        ),
        (
            "What problem did the Whirl create?",
            f"The Whirl snagged {hero.id}'s jeans on one of its spinning edges. "
            f"That snag increased wobble, and the growing wobble was what made the situation feel dangerous before anyone could touch it.",
        ),
        (
            "How was the problem solved?",
            f"{hero.id} used {method.label}. That action reduced the fabric snag and helped the Whirl's wobble drop, which prevented another catch.",
        ),
        (
            "Why was that method sensible for this scene?",
            f"This scene was in {world.setting.place} with {world.setting.wind} wind, and the story state included {jeans_spec.adjective} jeans with snugness {jeans_spec.snugness:.2f}. "
            f"The chosen approach {why} addressed the cause directly instead of trying to force the spinning machine to stop by brute force.",
        ),
        (
            "What changed in the ending image?",
            f"By the end, the Whirl was steady and making gentle sounds, and {hero.id}'s jeans were safe and tidy. "
            f"You can see the change in the last paragraph: the ending image explicitly shows a calm circle and a cheering crowd after the helper gives a ribbon.",
        ),
    ] + ([
        (
            "How did humor affect the outcome?",
            f"Humor kept the helper and {hero.id} from panicking. When worry stays lower, they could choose quieter steps, and those calmer steps made the fix effective.",
        )
    ] if resolved else [])


def world_knowledge_qa(world: StoryWorld) -> list[tuple[str, str]]:
    tags = {"jeans", "whirl", "humor"}
    if world.setting.has_water:
        tags.add("water")
    if world.setting.wind == "gale":
        tags.add("wind")

    out: list[tuple[str, str]] = []
    for tag in ("jeans", "whirl", "water", "wind", "humor"):
        if tag in tags:
            out.extend(KNOWLEDGE.get(tag, []))

    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
    lines.append("")
    lines.append("== (2) Story-grounded QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: StoryWorld) -> str:
    lines = ["--- storyworld trace ---"]
    lines.append(f"source_tale: {world.facts.get('source_tale')}")
    lines.append(f"method: {world.facts['method'].id}")
    lines.append(f"resolved: {world.facts.get('resolved', False)}")
    lines.append(f"snag: {world.facts.get('snag_severity', 0)}")
    lines.append(f"wobble: {world.facts.get('wobble_severity', 0)}")
    lines.append("entities:")
    for ent in world.entities.values():
        meters = {k: round(v, 2) for k, v in ent.meters.items() if v}
        memes = {k: round(v, 2) for k, v in ent.memes.items() if v}
        lines.append(
            f"  {ent.id} kind={ent.kind_word} meters={meters} memes={memes} traits={','.join(ent.traits)}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,J,M) :- place(P), has_wind(P,breezy), jeans(J), method(M), can_tie(M), tie_ready(J).
valid(P,J,M) :- place(P), has_wind(P,windy), jeans(J), method(M), can_tie(M), tie_ready(J).
valid(P,J,M) :- place(P), has_wind(P,breezy), has_water(P), jeans(J), method(M), can_mist(M), snug_enough(J).
valid(P,J,M) :- place(P), has_water(P), has_wind(P,windy), jeans(J), method(M), can_mist(M), snug_enough(J).
valid(P,J,M) :- place(P), has_wind(P,gale), jeans(J), method(M), is_song(M).
"""


def asp_facts(params: StoryParams | None = None) -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("place", setting_id))
        lines.append(asp.fact("has_wind", setting_id, setting.wind))
        if setting.has_water:
            lines.append(asp.fact("has_water", setting_id))
    for jeans_id, jeans in JEANS.items():
        lines.append(asp.fact("jeans", jeans_id))
        if jeans.tie_ready and jeans.snugness >= 0.7:
            lines.append(asp.fact("tie_ready", jeans_id))
        if jeans.snugness >= 0.55:
            lines.append(asp.fact("snug_enough", jeans_id))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        if method_id == "tail_twist":
            lines.append(asp.fact("can_tie", method_id))
        if method_id == "mist_crown":
            lines.append(asp.fact("can_mist", method_id))
        if method_id == "pause_song":
            lines.append(asp.fact("is_song", method_id))

    if params is not None:
        lines.append(f"#show valid({params.place},{params.jeans},{params.method}).")
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    out = asp.atoms(model, "valid")
    return sorted(set((a, b, c) for a, b, c in out))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if python_set != asp_set:
        print("Mismatch between Python and ASP generation rules.")
        print("  In Python only:", sorted(python_set - asp_set))
        print("  In ASP only:", sorted(asp_set - python_set))
        return 1
    print(f"OK: ASP and Python describe {len(python_set)} valid combos identically.")

    sample_targets = sorted(python_set)[: min(6, len(python_set))]
    for place_id, jeans_id, method_id in sample_targets:
        params = StoryParams(
            place=place_id,
            jeans=jeans_id,
            method=method_id,
            name=random.choice(NAMES_BY_GENDER["girl"]),
            gender="girl",
            trait=random.choice(TRAITS),
        )
        sample = generate(params)
        text = sample.story.lower()
        if "jeans" not in text or "whirl" not in text:
            print("FAILED: story text must mention jeans and whirl for", params)
            return 2
    print("OK: verification ran sample generation for representative valid combinations.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale storyworld: jeans, whirl, humor, and problem solving"
    )
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--jeans", choices=sorted(JEANS))
    ap.add_argument("--method", choices=sorted(METHODS))
    ap.add_argument("--gender", choices=["girl", "boy"], default=None)
    ap.add_argument("--name")
    ap.add_argument("--trait")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.jeans and args.method:
        setting = SETTINGS[args.place]
        jeans = JEANS[args.jeans]
        method = METHODS[args.method]
        if not valid_plan(setting, jeans, method):
            raise StoryError(explain_rejection(setting, jeans, method))

    candidates = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.jeans is None or combo[1] == args.jeans)
        and (args.method is None or combo[2] == args.method)
    ]

    if not candidates:
        raise StoryError("No valid place/jeans/method combination is available for those filters.")

    place_id, jeans_id, method_id = rng.choice(candidates)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_BY_GENDER[gender])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place_id, jeans_id, method_id, name, gender, trait)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    jeans = JEANS[params.jeans]
    method = METHODS[params.method]

    if not valid_plan(setting, jeans, method):
        raise StoryError(explain_rejection(setting, jeans, method))

    world = build_world(setting, jeans, method, params.name, params.gender, params.trait)
    story = world.render()
    if "jeans" not in story.lower() or "whirl" not in story.lower():
        raise StoryError("Generated story did not include required seed concepts.")

    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_grounded_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def emit(sample: StorySample, args: argparse.Namespace, label: str | None = None) -> None:
    if label:
        print(label)
    print(sample.story)
    if args.trace and sample.world is not None:
        print()
        print(dump_trace(sample.world))
    if args.qa:
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
        for combo in asp_valid_combos():
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [
            generate(StoryParams("lantern_square", "sunset", "tail_twist", "Mira", "girl", "kind", seed=1)),
            generate(StoryParams("weaving_glen", "comet", "mist_crown", "Theo", "boy", "curious", seed=2)),
            generate(StoryParams("storm_knoll", "comet", "pause_song", "Lina", "girl", "brave", seed=3)),
            generate(StoryParams("weaving_glen", "sunset", "tail_twist", "Finn", "boy", "playful", seed=4)),
        ]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 80, 200):
            i += 1
            local_rng = random.Random(base_seed + i)
            params = resolve_params(args, local_rng)
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

    if args.json:
        out = samples[0].to_dict() if len(samples) == 1 else [s.to_dict() for s in samples]
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return

    for i, sample in enumerate(samples, 1):
        label = f"--- story {i} ---" if len(samples) > 1 else ""
        emit(sample, args, label=label)
        if i != len(samples):
            print()


if __name__ == "__main__":
    try:
        main()
    except StoryError as exc:
        print(exc)
        sys.exit(2)

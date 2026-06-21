#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/ecosystem_lesson_learned_cautionary_tall_tale.py
==============================================================================

A standalone story world about a child who thinks nature would be neater without
one annoying little creature, chases it away, and learns the hard way that an
ecosystem works because many living things help one another.

The tone leans tall-tale: gardens stretch wide as counties, buzzing sounds shake
the spoons, and tiny troubles arrive in ridiculous swarms. But the causal model
stays grounded: a helper species keeps a trouble species in check, and a sensible
restoration can bring balance back.

Run it
------
    python storyworlds/worlds/gpt-5.4/ecosystem_lesson_learned_cautionary_tall_tale.py
    python storyworlds/worlds/gpt-5.4/ecosystem_lesson_learned_cautionary_tall_tale.py --habitat pond --helper frogs
    python storyworlds/worlds/gpt-5.4/ecosystem_lesson_learned_cautionary_tall_tale.py --restore sugar_bowl
    python storyworlds/worlds/gpt-5.4/ecosystem_lesson_learned_cautionary_tall_tale.py --all
    python storyworlds/worlds/gpt-5.4/ecosystem_lesson_learned_cautionary_tall_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/ecosystem_lesson_learned_cautionary_tall_tale.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
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
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Habitat:
    id: str
    label: str
    phrase: str
    tall_line: str
    prize: str
    prize_phrase: str
    helpers: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Helper:
    id: str
    label: str
    plural_label: str
    entrance: str
    disliked_as: str
    controls: str
    boast: str
    return_line: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Trouble:
    id: str
    label: str
    plural_label: str
    surge: str
    harm: str
    lesson: str
    fierce: int
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Restore:
    id: str
    label: str
    phrase: str
    build: str
    supports: set[str] = field(default_factory=set)
    sense: int = 0
    power: int = 0
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class StoryParams:
    habitat: str
    helper: str
    restore: str
    child: str
    child_gender: str
    grownup: str
    trait: str
    delay: int = 0
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


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
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_trouble_blooms(world: World) -> list[str]:
    helper = world.get("helper")
    trouble = world.get("trouble")
    if helper.meters["present"] >= THRESHOLD:
        return []
    sig = ("trouble_blooms",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    trouble.meters["swarm"] += 1
    world.get("habitat").meters["balance"] -= 1
    world.get("prize").meters["risk"] += 1
    world.get("child").memes["worry"] += 1
    world.get("grownup").memes["concern"] += 1
    return ["__trouble__"]


def _r_trouble_harms(world: World) -> list[str]:
    trouble = world.get("trouble")
    if trouble.meters["swarm"] < THRESHOLD:
        return []
    sig = ("trouble_harms",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("prize").meters["hurt"] += 1
    world.get("child").memes["regret"] += 1
    return ["__harm__"]


def _r_restore_returns_helper(world: World) -> list[str]:
    restore = world.get("restore")
    helper = world.get("helper")
    if restore.meters["built"] < THRESHOLD:
        return []
    if helper.meters["present"] >= THRESHOLD:
        return []
    sig = ("restore_returns_helper",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    helper.meters["present"] = 1
    world.get("child").memes["hope"] += 1
    return ["__return__"]


def _r_helper_rebalances(world: World) -> list[str]:
    helper = world.get("helper")
    trouble = world.get("trouble")
    if helper.meters["present"] < THRESHOLD or trouble.meters["swarm"] < THRESHOLD:
        return []
    sig = ("helper_rebalances",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    trouble.meters["swarm"] = 0.0
    world.get("habitat").meters["balance"] += 2
    world.get("child").memes["relief"] += 1
    world.get("grownup").memes["relief"] += 1
    return ["__balance__"]


CAUSAL_RULES = [
    Rule(name="trouble_blooms", tag="physical", apply=_r_trouble_blooms),
    Rule(name="trouble_harms", tag="physical", apply=_r_trouble_harms),
    Rule(name="restore_returns_helper", tag="physical", apply=_r_restore_returns_helper),
    Rule(name="helper_rebalances", tag="physical", apply=_r_helper_rebalances),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


HABITATS = {
    "garden": Habitat(
        id="garden",
        label="garden",
        phrase="the backyard garden",
        tall_line="the bean rows stood so tall they seemed to tickle the bottom of the clouds",
        prize="bean patch",
        prize_phrase="the climbing bean patch",
        helpers={"ladybugs"},
        tags={"garden", "ecosystem"},
    ),
    "pond": Habitat(
        id="pond",
        label="pond",
        phrase="the pond behind the shed",
        tall_line="the pond was so round and bright it looked like somebody had dropped a piece of sky onto the grass",
        prize="picnic blanket",
        prize_phrase="the red-checkered picnic blanket by the water",
        helpers={"frogs"},
        tags={"pond", "ecosystem"},
    ),
    "orchard": Habitat(
        id="orchard",
        label="orchard",
        phrase="the little orchard past the gate",
        tall_line="the apple trees were so full of leaves that the wind had to squeeze sideways to get through",
        prize="apple trees",
        prize_phrase="the row of shiny apple trees",
        helpers={"wrens"},
        tags={"orchard", "ecosystem"},
    ),
}

HELPERS = {
    "ladybugs": Helper(
        id="ladybugs",
        label="ladybug",
        plural_label="ladybugs",
        entrance="red-backed ladybugs sailed from leaf to leaf like tiny painted kites",
        disliked_as="too many spots and too much fluttering",
        controls="aphids",
        boast="Those little spotted things are doing nothing but showing off",
        return_line="Soon the ladybugs came drifting back, calm and busy, landing wherever the green pests had gathered",
        tags={"ladybug", "ecosystem"},
    ),
    "frogs": Helper(
        id="frogs",
        label="frog",
        plural_label="frogs",
        entrance="green frogs sat along the water like a row of squishy marshals keeping watch",
        disliked_as="too slimy and too croaky",
        controls="mosquitoes",
        boast="Those croakers are all noise and no use",
        return_line="Before long the frogs plopped back to the pond edge and began snapping up the whining bugs",
        tags={"frog", "ecosystem"},
    ),
    "wrens": Helper(
        id="wrens",
        label="wren",
        plural_label="wrens",
        entrance="little wrens flashed through the branches like brown stitches sewing the air together",
        disliked_as="too pecky and too fussy",
        controls="caterpillars",
        boast="Those pecky birds only fuss and flap",
        return_line="In a little while the wrens zipped back through the branches, quick as tossed needles",
        tags={"bird", "ecosystem"},
    ),
}

TROUBLES = {
    "aphids": Trouble(
        id="aphids",
        label="aphid",
        plural_label="aphids",
        surge="the aphids came crowding over the leaves until the vines looked as if someone had shaken green pepper over every inch of them",
        harm="The bean leaves curled, and the patch that had looked ready to climb the moon began to sag.",
        lesson="ladybugs eat many aphids and help protect garden plants",
        fierce=2,
        tags={"aphid", "garden_pests"},
    ),
    "mosquitoes": Trouble(
        id="mosquitoes",
        label="mosquito",
        plural_label="mosquitoes",
        surge="mosquitoes whined up from the water in such a cloud that the air sounded like a hundred toy fiddles played all at once",
        harm="Nobody could sit on the picnic blanket for even a minute without flapping and scooting away.",
        lesson="frogs eat many insects and help keep pond life balanced",
        fierce=2,
        tags={"mosquito", "pond_life"},
    ),
    "caterpillars": Trouble(
        id="caterpillars",
        label="caterpillar",
        plural_label="caterpillars",
        surge="caterpillars appeared on the branches in a soft green parade, chewing so steadily it sounded like tiny scissors snipping all day long",
        harm="The apple leaves turned ragged, and even the fruit looked worried under all that nibbling.",
        lesson="small birds eat leaf-chewing insects and help orchard trees stay healthy",
        fierce=2,
        tags={"caterpillar", "orchard"},
    ),
}

RESTORES = {
    "wildflowers": Restore(
        id="wildflowers",
        label="wildflowers",
        phrase="a ribbon of wildflowers",
        build="planted a bright ribbon of wildflowers beside the beans so the helpful insects would want to stay",
        supports={"ladybugs"},
        sense=3,
        power=3,
        qa_text="planted wildflowers to welcome the ladybugs back",
        tags={"wildflowers", "habitat_help"},
    ),
    "reeds": Restore(
        id="reeds",
        label="reeds",
        phrase="a patch of reeds and flat stones",
        build="set flat stones by the edge and tucked in a patch of reeds so the frogs would have a fine place to rest and hide",
        supports={"frogs"},
        sense=3,
        power=3,
        qa_text="added reeds and flat stones to make the pond friendly for frogs again",
        tags={"reeds", "habitat_help"},
    ),
    "birdhouse": Restore(
        id="birdhouse",
        label="birdhouse",
        phrase="a snug birdhouse",
        build="hung a snug little birdhouse and promised the orchard some quieter hands",
        supports={"wrens"},
        sense=3,
        power=3,
        qa_text="hung a birdhouse so the wrens would come back to the orchard",
        tags={"birdhouse", "habitat_help"},
    ),
    "sugar_bowl": Restore(
        id="sugar_bowl",
        label="sugar bowl",
        phrase="a sugar bowl on a stump",
        build="set out a sugar bowl on a stump and hoped that would fix everything",
        supports={"ladybugs"},
        sense=1,
        power=1,
        qa_text="set out a sugar bowl",
        tags={"sugar", "habitat_help"},
    ),
}

GIRL_NAMES = ["Molly", "Tess", "Lila", "June", "Poppy", "Nell", "Daisy", "Wren"]
BOY_NAMES = ["Bo", "Hank", "Jude", "Finn", "Otis", "Cal", "Toby", "Rex"]
TRAITS = ["boastful", "hasty", "stubborn", "showy", "spirited"]


def helper_fits(habitat: Habitat, helper: Helper) -> bool:
    return helper.id in habitat.helpers


def sensible_restores() -> list[Restore]:
    return [r for r in RESTORES.values() if r.sense >= SENSE_MIN]


def restore_supports(helper: Helper, restore: Restore) -> bool:
    return helper.id in restore.supports


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for habitat_id, habitat in HABITATS.items():
        for helper_id, helper in HELPERS.items():
            if not helper_fits(habitat, helper):
                continue
            for restore_id, restore in RESTORES.items():
                if restore.sense >= SENSE_MIN and restore_supports(helper, restore):
                    combos.append((habitat_id, helper_id, restore_id))
    return combos


def severity_for(helper: Helper, delay: int) -> int:
    trouble = TROUBLES[helper.controls]
    return trouble.fierce + delay


def recovers_well(helper: Helper, restore: Restore, delay: int) -> bool:
    return restore.power >= severity_for(helper, delay)


def explain_combo_rejection(habitat: Habitat, helper: Helper) -> str:
    return (
        f"(No story: {helper.plural_label} do not belong as the balancing helper in "
        f"{habitat.phrase} here. Pick a helper that actually belongs in that ecosystem.)"
    )


def explain_restore_rejection(helper: Helper, restore: Restore) -> str:
    if restore.sense < SENSE_MIN:
        return (
            f"(Refusing restore '{restore.id}': it scores too low on common sense "
            f"(sense={restore.sense} < {SENSE_MIN}). A story should use a real habitat fix, "
            f"not wishful tinkering.)"
        )
    return (
        f"(No story: {restore.label} does not make sense for bringing back "
        f"{helper.plural_label}. Choose a restoration that truly helps that helper live there.)"
    )


def introduce(world: World, child: Entity, grownup: Entity, habitat: Habitat) -> None:
    world.say(
        f"{child.id} was a {child.traits[0]} little {child.type} with a voice big enough "
        f"to make fence posts seem to stand straighter. Behind the house lay {habitat.phrase}, "
        f"and {habitat.tall_line}."
    )
    world.say(
        f"{grownup.label_word.capitalize()} called it a small ecosystem, but to {child.id} it felt "
        f"bigger than three counties and twice as interesting."
    )


def show_balance(world: World, child: Entity, helper: Helper) -> None:
    world.say(
        f"That morning, {helper.entrance}. {child.id} watched them for a while, but soon "
        f"decided they were {helper.disliked_as}."
    )


def boast(world: World, child: Entity, helper: Helper) -> None:
    child.memes["pride"] += 1
    world.say(
        f'"{helper.boast}," {child.id} declared. "{child.pronoun("subject").capitalize()} can run this place better without them."'
    )


def warn(world: World, grownup: Entity, child: Entity, habitat: Habitat, helper: Helper, trouble: Trouble) -> None:
    child.memes["warning_heard"] += 1
    world.say(
        f'But {grownup.label_word} shook {grownup.pronoun("possessive")} head. '
        f'"Every part of an ecosystem has a job," {grownup.pronoun()} said. '
        f'"If you chase away the {helper.plural_label}, something else may grow too bold."'
    )
    world.say(
        f'{child.id} heard the warning, but pride puffed up inside {child.pronoun("object")} like a parade balloon.'
    )


def chase(world: World, child: Entity, helper_ent: Entity, helper: Helper) -> None:
    helper_ent.meters["present"] = 0.0
    child.memes["defiance"] += 1
    world.say(
        f"So {child.id} clapped pots, flapped a sunhat, and stomped about until the "
        f"{helper.plural_label} scattered away."
    )


def trouble_turn(world: World, trouble: Trouble, habitat: Habitat) -> None:
    propagate(world, narrate=False)
    world.say(
        f"At first {world.get('child').id} grinned. Then, by dinnertime, {trouble.surge}"
    )
    world.say(trouble.harm)


def remorse(world: World, child: Entity, grownup: Entity) -> None:
    child.memes["remorse"] += 1
    world.say(
        f"{child.id}'s grin folded up small. {child.pronoun('subject').capitalize()} went to "
        f"{grownup.label_word} and whispered that maybe the place had been doing a better job "
        f"before {child.pronoun('subject')} tried to boss it around."
    )


def restore_scene(world: World, child: Entity, grownup: Entity, restore_ent: Entity, restore: Restore) -> None:
    restore_ent.meters["built"] = 1.0
    world.say(
        f'{grownup.label_word.capitalize()} did not scold. Instead {grownup.pronoun()} handed '
        f'{child.pronoun("object")} a small shovel and said, "Then let us mend what you disturbed."'
    )
    world.say(
        f"Together they {restore.build}."
    )
    propagate(world, narrate=False)


def balance_return(world: World, child: Entity, helper: Helper, trouble: Trouble, outcome: str, habitat: Habitat) -> None:
    world.say(helper.return_line)
    if outcome == "recovered":
        world.say(
            f"After that, the {trouble.plural_label} thinned and thinned until {habitat.phrase} "
            f"could breathe easy again."
        )
    else:
        world.say(
            f"The {trouble.plural_label} thinned at last, but they had already left a rough lesson behind."
        )


def ending_good(world: World, child: Entity, habitat: Habitat) -> None:
    child.memes["lesson"] += 1
    world.say(
        f"Soon {habitat.prize_phrase} looked lively again, and {child.id} never again called a small helper useless."
    )
    world.say(
        f"After that, whenever {child.pronoun('subject')} stepped into the yard, {child.pronoun('subject')} tipped "
        f"{child.pronoun('possessive')} chin and said the word ecosystem with real respect, as if it were the name of a giant machine made of wings, roots, mud, and patience."
    )


def ending_scarred(world: World, child: Entity, habitat: Habitat) -> None:
    child.memes["lesson"] += 1
    world.say(
        f"The place was calmer again, but {habitat.prize_phrase} bore the marks of that foolish week."
    )
    world.say(
        f"{child.id} learned the lesson so thoroughly that {child.pronoun('subject')} never chased a helpful creature from the yard again. In a world as large as a tall tale, even one little missing neighbor can tip an ecosystem off balance."
    )


def tell(
    habitat: Habitat,
    helper: Helper,
    restore: Restore,
    child_name: str = "Molly",
    child_gender: str = "girl",
    grownup_type: str = "mother",
    trait: str = "boastful",
    delay: int = 0,
) -> World:
    trouble = TROUBLES[helper.controls]
    world = World()

    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name, traits=[trait], role="child"))
    grownup = world.add(Entity(id="grownup", kind="character", type=grownup_type, label="the grown-up", role="grownup"))
    habitat_ent = world.add(Entity(id="habitat", type="place", label=habitat.label, tags=set(habitat.tags)))
    helper_ent = world.add(Entity(id="helper", type="animal", label=helper.plural_label, tags=set(helper.tags)))
    trouble_ent = world.add(Entity(id="trouble", type="animal", label=trouble.plural_label, tags=set(trouble.tags)))
    prize_ent = world.add(Entity(id="prize", type="thing", label=habitat.prize, tags=set(habitat.tags)))
    restore_ent = world.add(Entity(id="restore", type="thing", label=restore.label, tags=set(restore.tags)))

    helper_ent.meters["present"] = 1.0
    habitat_ent.meters["balance"] = 1.0
    trouble_ent.meters["swarm"] = 0.0
    prize_ent.meters["risk"] = 0.0
    prize_ent.meters["hurt"] = 0.0
    restore_ent.meters["built"] = 0.0

    world.facts.update(
        habitat=habitat,
        helper_cfg=helper,
        trouble_cfg=trouble,
        restore_cfg=restore,
        child_name=child_name,
        delay=delay,
    )

    introduce(world, child, grownup, habitat)
    show_balance(world, child, helper)

    world.para()
    boast(world, child, helper)
    warn(world, grownup, child, habitat, helper, trouble)
    chase(world, child, helper_ent, helper)

    world.para()
    trouble_turn(world, trouble, habitat)
    for _ in range(delay):
        trouble_ent.meters["swarm"] += 1
        prize_ent.meters["hurt"] += 1
    world.facts["severity"] = severity_for(helper, delay)
    remorse(world, child, grownup)

    world.para()
    restore_scene(world, child, grownup, restore_ent, restore)
    outcome = "recovered" if recovers_well(helper, restore, delay) else "scarred"
    balance_return(world, child, helper, trouble, outcome, habitat)

    world.para()
    if outcome == "recovered":
        ending_good(world, child, habitat)
    else:
        ending_scarred(world, child, habitat)

    world.facts.update(
        child=child,
        grownup=grownup,
        habitat_ent=habitat_ent,
        helper=helper_ent,
        trouble=trouble_ent,
        prize=prize_ent,
        restore=restore_ent,
        outcome=outcome,
        caused_trouble=prize_ent.meters["hurt"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "ecosystem": [
        (
            "What is an ecosystem?",
            "An ecosystem is a living neighborhood where plants, animals, water, soil, and air all affect one another. When one part changes, other parts can change too.",
        )
    ],
    "ladybug": [
        (
            "Why are ladybugs helpful in a garden?",
            "Ladybugs eat tiny plant pests such as aphids. That helps leaves and stems stay healthier.",
        )
    ],
    "frog": [
        (
            "Why can frogs be helpful near a pond?",
            "Frogs eat many insects, including mosquitoes. That helps keep pond life more balanced.",
        )
    ],
    "bird": [
        (
            "Why are small birds helpful in an orchard?",
            "Small birds often eat insects that chew leaves and fruit. That can help trees stay healthier.",
        )
    ],
    "aphid": [
        (
            "What are aphids?",
            "Aphids are tiny bugs that suck juice from plants. When there are too many, plants can wilt or curl.",
        )
    ],
    "mosquito": [
        (
            "Why do mosquitoes bother people?",
            "Mosquitoes bite and leave itchy bumps. They also gather in wet places if nothing is keeping their numbers down.",
        )
    ],
    "caterpillar": [
        (
            "Why can too many caterpillars be a problem for trees?",
            "Caterpillars chew leaves. If there are too many, they can leave a tree ragged and weak.",
        )
    ],
    "wildflowers": [
        (
            "Why do wildflowers help many helpful insects?",
            "Wildflowers give food and shelter to many insects. That makes a place friendlier for the creatures that help plants.",
        )
    ],
    "reeds": [
        (
            "Why do reeds help pond animals?",
            "Reeds give small pond animals places to hide and rest. They make the edge of a pond feel safer and more useful.",
        )
    ],
    "birdhouse": [
        (
            "Why might a birdhouse help birds stay nearby?",
            "A birdhouse can give birds a place to rest or nest. If the area is safe, that can help them stay close.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "ecosystem",
    "ladybug",
    "frog",
    "bird",
    "aphid",
    "mosquito",
    "caterpillar",
    "wildflowers",
    "reeds",
    "birdhouse",
]


def generation_prompts(world: World) -> list[str]:
    habitat = world.facts["habitat"]
    helper = world.facts["helper_cfg"]
    trouble = world.facts["trouble_cfg"]
    restore = world.facts["restore_cfg"]
    child = world.facts["child"]
    outcome = world.facts["outcome"]
    if outcome == "recovered":
        return [
            f'Write a tall-tale-style cautionary story for a 3-to-5-year-old that uses the word "ecosystem" and features {helper.plural_label} in {habitat.phrase}.',
            f"Tell a story where {child.label} chases away the {helper.plural_label}, {trouble.plural_label} grow bold, and a grown-up helps mend the place with {restore.label}.",
            f"Write a lesson-learned story about a child who thinks nature would work better without one small creature, then learns that an ecosystem depends on helpers.",
        ]
    return [
        f'Write a tall-tale cautionary story that includes the word "ecosystem" and ends with a mark left by the trouble after the helper returns.',
        f"Tell a story where {child.label} chases away the {helper.plural_label}, the {trouble.plural_label} do real damage, and the lesson lasts longer than the mess.",
        f"Write a child-facing story about a boastful mistake in nature and how even a repaired ecosystem can show what happened.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    grownup = world.facts["grownup"]
    habitat = world.facts["habitat"]
    helper = world.facts["helper_cfg"]
    trouble = world.facts["trouble_cfg"]
    restore = world.facts["restore_cfg"]
    outcome = world.facts["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.label}, a little {child.type}, and {child.pronoun('possessive')} {grownup.label_word}. The story also follows the small creatures in {habitat.phrase} that keep the ecosystem balanced.",
        ),
        (
            f"Why did {child.label} chase away the {helper.plural_label}?",
            f"{child.label} thought the {helper.plural_label} were annoying and useless. Pride made {child.pronoun('object')} believe {child.pronoun('subject')} could run the place better alone.",
        ),
        (
            "What went wrong after that?",
            f"Once the {helper.plural_label} were gone, the {trouble.plural_label} grew bold and spread. That happened because the helper creatures had been quietly keeping that trouble in check.",
        ),
        (
            "What does the word ecosystem mean in this story?",
            f"In this story, ecosystem means the whole living neighborhood working together in {habitat.phrase}. When {child.label} removed one helpful part, other parts changed too.",
        ),
        (
            f"How did the grown-up try to fix the problem?",
            f"{grownup.label_word.capitalize()} helped {child.label} {restore.qa_text}. They did not just chase the trouble away; they repaired the place so the helpful creatures could come back.",
        ),
    ]
    if outcome == "recovered":
        qa.append(
            (
                "How did the story end?",
                f"The helper creatures returned, the trouble thinned out, and {habitat.prize_phrase} grew lively again. {child.label} learned to respect the ecosystem instead of bossing it around.",
            )
        )
    else:
        qa.append(
            (
                "How did the story end?",
                f"The ecosystem settled down again, but the damage stayed visible for a while. That lasting mark taught {child.label} that one proud mistake can hurt a place even after help comes back.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    helper = world.facts["helper_cfg"]
    trouble = world.facts["trouble_cfg"]
    restore = world.facts["restore_cfg"]
    tags = {"ecosystem"} | set(helper.tags) | set(trouble.tags) | set(restore.tags)
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
        if ent.label:
            bits.append(f"label={ent.label!r}")
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
helper_fits(H, He) :- habitat(H), helper(He), supports_habitat(H, He).
sensible_restore(R) :- restore(R), sense(R, S), sense_min(M), S >= M.
supports_helper(He, R) :- restore_support(R, He).

valid(H, He, R) :- helper_fits(H, He), sensible_restore(R), supports_helper(He, R).

severity(V) :- chosen_helper(He), fierce(He, F), delay(D), V = F + D.
good_recovery :- chosen_restore(R), power(R, P), severity(V), P >= V.
outcome(recovered) :- good_recovery.
outcome(scarred) :- not good_recovery.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for hid in HABITATS:
        lines.append(asp.fact("habitat", hid))
    for hid, habitat in HABITATS.items():
        for helper_id in sorted(habitat.helpers):
            lines.append(asp.fact("supports_habitat", hid, helper_id))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("fierce", helper_id, TROUBLES[helper.controls].fierce))
    for restore_id, restore in RESTORES.items():
        lines.append(asp.fact("restore", restore_id))
        lines.append(asp.fact("sense", restore_id, restore.sense))
        lines.append(asp.fact("power", restore_id, restore.power))
        for helper_id in sorted(restore.supports):
            lines.append(asp.fact("restore_support", restore_id, helper_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_helper", params.helper),
            asp.fact("chosen_restore", params.restore),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    helper = HELPERS[params.helper]
    restore = RESTORES[params.restore]
    return "recovered" if recovers_well(helper, restore, params.delay) else "scarred"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child chases away a helpful creature, harms an ecosystem, and learns better."
    )
    ap.add_argument("--habitat", choices=HABITATS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--restore", choices=RESTORES)
    ap.add_argument("--grownup", choices=["mother", "father"])
    ap.add_argument("--child")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the trouble gets to grow before repair")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible stories derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.habitat and args.helper:
        habitat = HABITATS[args.habitat]
        helper = HELPERS[args.helper]
        if not helper_fits(habitat, helper):
            raise StoryError(explain_combo_rejection(habitat, helper))
    if args.helper and args.restore:
        helper = HELPERS[args.helper]
        restore = RESTORES[args.restore]
        if not restore_supports(helper, restore) or restore.sense < SENSE_MIN:
            raise StoryError(explain_restore_rejection(helper, restore))
    if args.restore and args.restore in RESTORES and RESTORES[args.restore].sense < SENSE_MIN:
        helper = HELPERS[args.helper] if args.helper else next(iter(HELPERS.values()))
        raise StoryError(explain_restore_rejection(helper, RESTORES[args.restore]))

    combos = [
        combo
        for combo in valid_combos()
        if (args.habitat is None or combo[0] == args.habitat)
        and (args.helper is None or combo[1] == args.helper)
        and (args.restore is None or combo[2] == args.restore)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    habitat_id, helper_id, restore_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.child or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    grownup = args.grownup or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)

    return StoryParams(
        habitat=habitat_id,
        helper=helper_id,
        restore=restore_id,
        child=child_name,
        child_gender=gender,
        grownup=grownup,
        trait=trait,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.habitat not in HABITATS:
        raise StoryError(f"(Unknown habitat: {params.habitat})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.restore not in RESTORES:
        raise StoryError(f"(Unknown restore: {params.restore})")

    habitat = HABITATS[params.habitat]
    helper = HELPERS[params.helper]
    restore = RESTORES[params.restore]

    if not helper_fits(habitat, helper):
        raise StoryError(explain_combo_rejection(habitat, helper))
    if not restore_supports(helper, restore) or restore.sense < SENSE_MIN:
        raise StoryError(explain_restore_rejection(helper, restore))

    world = tell(
        habitat=habitat,
        helper=helper,
        restore=restore,
        child_name=params.child,
        child_gender=params.child_gender,
        grownup_type=params.grownup,
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


CURATED = [
    StoryParams(
        habitat="garden",
        helper="ladybugs",
        restore="wildflowers",
        child="Molly",
        child_gender="girl",
        grownup="mother",
        trait="boastful",
        delay=0,
    ),
    StoryParams(
        habitat="pond",
        helper="frogs",
        restore="reeds",
        child="Bo",
        child_gender="boy",
        grownup="father",
        trait="hasty",
        delay=1,
    ),
    StoryParams(
        habitat="orchard",
        helper="wrens",
        restore="birdhouse",
        child="Lila",
        child_gender="girl",
        grownup="father",
        trait="showy",
        delay=2,
    ),
]


def asp_verify() -> int:
    rc = 0

    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for seed in range(40):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        p.seed = seed
        cases.append(p)

    bad = 0
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(cases[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test produced an empty story.)")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (habitat, helper, restore) combos:\n")
        for habitat, helper, restore in combos:
            print(f"  {habitat:8} {helper:10} {restore}")
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
            header = f"### {p.child}: {p.helper} in {p.habitat} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

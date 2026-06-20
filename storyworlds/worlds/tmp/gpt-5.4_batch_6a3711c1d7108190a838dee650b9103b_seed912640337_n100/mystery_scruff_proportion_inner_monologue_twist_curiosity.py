#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/mystery_scruff_proportion_inner_monologue_twist_curiosity.py
=================================================================================================

A standalone storyworld for a small myth-like mystery tale: a curious child
finds a bit of scruff at a shrine, follows the clue, learns the old rule of
proportion, and discovers that the scruffy thief is really a guardian in
disguise.

This world aims for a child-facing myth tone with:
- mystery: the dawn blessing has faded and nobody knows why
- scruff: the first clue is a tuft of rough fur near the offering stone
- proportion: the hidden rule is that the gift must be measured in the old balance
- inner monologue: the child wonders and reasons in thought
- twist: the shabby animal is the spirit of the place

Run it
------
    python storyworlds/worlds/gpt-5.4/mystery_scruff_proportion_inner_monologue_twist_curiosity.py
    python storyworlds/worlds/gpt-5.4/mystery_scruff_proportion_inner_monologue_twist_curiosity.py --sanctuary moon_pool --guise scruffy_pup
    python storyworlds/worlds/gpt-5.4/mystery_scruff_proportion_inner_monologue_twist_curiosity.py --response chase_with_stick
    python storyworlds/worlds/gpt-5.4/mystery_scruff_proportion_inner_monologue_twist_curiosity.py --all
    python storyworlds/worlds/gpt-5.4/mystery_scruff_proportion_inner_monologue_twist_curiosity.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/mystery_scruff_proportion_inner_monologue_twist_curiosity.py --verify
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt", "priestess"}
        male = {"boy", "father", "man", "uncle", "priest"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mother",
            "father": "father",
            "priestess": "priestess",
            "priest": "priest",
        }.get(self.type, self.type)


@dataclass
class Sanctuary:
    id: str
    title: str
    place: str
    deity: str
    secret_name: str
    visible_blessing: str
    faded_sign: str
    offering_a: str
    offering_b: str
    ratio_a: int
    ratio_b: int
    ratio_words: str
    bowl: str
    domain: str
    opening_image: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Guise:
    id: str
    label: str
    scruff: str
    tracks: str
    sound: str
    reveal_form: str
    domain: str
    likes_a: str
    likes_b: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    solves: bool
    helper: bool
    text: str
    qa_text: str
    fail_text: str
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


def _r_imbalance_dims(world: World) -> list[str]:
    shrine = world.entities.get("shrine")
    village = world.entities.get("village")
    hero = world.entities.get("hero")
    if not shrine or not village or not hero:
        return []
    if shrine.meters["imbalance"] < THRESHOLD:
        return []
    sig = ("imbalance_dims",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    village.meters["dimness"] += 1
    hero.memes["curiosity"] += 1
    hero.memes["wonder"] += 1
    return []


def _r_kindness_builds_trust(world: World) -> list[str]:
    creature = world.entities.get("creature")
    hero = world.entities.get("hero")
    if not creature or not hero:
        return []
    if hero.memes["kindness"] < THRESHOLD or hero.meters["balanced_offering"] < THRESHOLD:
        return []
    sig = ("kindness_builds_trust",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    creature.memes["trust"] += 1
    return []


def _r_reveal(world: World) -> list[str]:
    shrine = world.entities.get("shrine")
    creature = world.entities.get("creature")
    village = world.entities.get("village")
    if not shrine or not creature or not village:
        return []
    if creature.memes["trust"] < THRESHOLD or shrine.meters["balanced"] < THRESHOLD:
        return []
    sig = ("reveal",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    shrine.meters["revealed"] += 1
    shrine.meters["imbalance"] = 0.0
    village.meters["dimness"] = 0.0
    village.meters["blessing"] += 1
    return []


CAUSAL_RULES = [
    Rule("imbalance_dims", "physical", _r_imbalance_dims),
    Rule("kindness_builds_trust", "social", _r_kindness_builds_trust),
    Rule("reveal", "mythic", _r_reveal),
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def compatible(sanctuary: Sanctuary, guise: Guise) -> bool:
    return sanctuary.domain == guise.domain


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid, sanctuary in SANCTUARIES.items():
        for gid, guise in GUISES.items():
            for rid, response in RESPONSES.items():
                if compatible(sanctuary, guise) and response.sense >= SENSE_MIN:
                    out.append((sid, gid, rid))
    return sorted(out)


def explain_combo_rejection(sanctuary: Sanctuary, guise: Guise) -> str:
    return (
        f"(No story: {guise.label} belongs to the {guise.domain.replace('_', ' ')} tale, "
        f"but {sanctuary.title} belongs to the {sanctuary.domain.replace('_', ' ')} tale. "
        f"In this world, the disguise and the shrine must hide the same guardian mystery.)"
    )


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = " / ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). A mythic mystery still needs a gentle, "
        f"reasonable choice. Try: {better}.)"
    )


def outcome_of(params: "StoryParams") -> str:
    response = RESPONSES[params.response]
    return "revealed_with_help" if response.solves and response.helper else (
        "revealed_alone" if response.solves else "lingering"
    )


def predict_reveal(world: World) -> dict:
    sim = world.copy()
    sim.get("hero").memes["kindness"] += 1
    sim.get("hero").meters["balanced_offering"] += 1
    sim.get("shrine").meters["balanced"] += 1
    propagate(sim, narrate=False)
    return {
        "revealed": sim.get("shrine").meters["revealed"] >= THRESHOLD,
        "blessing": sim.get("village").meters["blessing"] >= THRESHOLD,
    }


def dawn_problem(world: World, hero: Entity, sanctuary: Sanctuary) -> None:
    shrine = world.add(Entity(id="shrine", type="shrine", label=sanctuary.title))
    village = world.add(Entity(id="village", type="village", label="the village"))
    shrine.meters["imbalance"] += 1
    propagate(world, narrate=False)
    world.say(
        f"In the days when streams remembered songs and stones listened at night, "
        f"{hero.id} lived beside {sanctuary.title}, {sanctuary.place}."
    )
    world.say(
        f"Each dawn the people looked there for {sanctuary.visible_blessing}, "
        f"but that morning the sign had faded. {sanctuary.faded_sign}"
    )
    world.say(
        f"Everyone called it a mystery, and the word seemed to hang in the air like mist."
    )


def clue_scruff(world: World, hero: Entity, guise: Guise) -> None:
    creature = world.add(Entity(id="creature", type="creature", label=guise.label))
    creature.meters["hidden"] += 1
    hero.memes["curiosity"] += 1
    world.say(
        f"Near the old offering stone, {hero.id} found a thread of {guise.scruff}. "
        f"It was caught on the crack of the altar as if the night had snagged a secret."
    )
    world.say(
        f'"That is no common wind-mark," {hero.id} thought. "What left scruff here, '
        f'and why would it come so close to the god\'s bowl?"'
    )


def follow_tracks(world: World, hero: Entity, sanctuary: Sanctuary, guise: Guise) -> None:
    hero.memes["wonder"] += 1
    world.say(
        f"{hero.id} followed {guise.tracks} around {sanctuary.place}, "
        f"moving slowly so the mystery would not break."
    )
    world.say(
        f"Behind a laurel stone, {hero.pronoun()} saw {guise.label}, all ribs and scruff, "
        f"watching the shrine with bright, careful eyes."
    )
    world.say(
        f'"It looks hungry," {hero.id} thought, "but hungry for what? '
        f'{sanctuary.offering_a.capitalize()}? {sanctuary.offering_b.capitalize()}? '
        f'Or something I do not yet understand?"'
    )


def consult_elder(world: World, hero: Entity, elder: Entity, sanctuary: Sanctuary) -> None:
    hero.memes["prudence"] += 1
    elder.memes["wisdom"] += 1
    world.say(
        f"{hero.id} did not rush. {hero.pronoun().capitalize()} went to {elder.label_word}, "
        f"who kept the old stories and never laughed at a child's questions."
    )
    world.say(
        f'{elder.label_word.capitalize()} listened, then touched the rim of {sanctuary.bowl}. '
        f'"The guardian of this place does not ask for plenty," {elder.pronoun()} said. '
        f'"It asks for proportion: {sanctuary.ratio_words}."'
    )
    world.say(
        f'"Not too much and not too little," {hero.id} thought. "So the riddle is not hunger alone. '
        f'It is balance."'
    )


def choose_balance(world: World, hero: Entity, sanctuary: Sanctuary, response: Response) -> None:
    hero.meters["balanced_offering"] += 1
    hero.memes["kindness"] += 1
    shrine = world.get("shrine")
    shrine.meters["balanced"] += 1
    world.say(response.text.format(
        bowl=sanctuary.bowl,
        offering_a=sanctuary.offering_a,
        offering_b=sanctuary.offering_b,
        ratio_words=sanctuary.ratio_words,
    ))
    pred = predict_reveal(world)
    world.facts["predicted_reveal"] = pred["revealed"]


def reveal_twist(world: World, hero: Entity, sanctuary: Sanctuary, guise: Guise) -> None:
    propagate(world, narrate=False)
    creature = world.get("creature")
    creature.meters["hidden"] = 0.0
    creature.meters["revealed"] += 1
    hero.memes["awe"] += 1
    world.say(
        f"The scruffy creature came close, sniffed the rim, and ate only what matched the old proportion."
    )
    world.say(
        f"Then the rough {guise.scruff} shone. The bent little body rose into {guise.reveal_form}, "
        f"and {hero.id} understood the twist at last: the shabby thief had been {sanctuary.secret_name} all along."
    )
    world.say(
        f'"Curiosity opened the path," {hero.id} thought, "but kindness and balance opened the truth."'
    )
    world.say(
        f"At once {sanctuary.ending_image}."
    )


def lingering_end(world: World, hero: Entity, elder: Entity, sanctuary: Sanctuary, guise: Guise) -> None:
    hero.memes["resolve"] += 1
    world.say(
        f"But the creature slipped away before {hero.id} could test the offering, "
        f"leaving only a curl of scruff and the soft echo of {guise.sound}."
    )
    world.say(
        f'{elder.label_word.capitalize()} rested a hand on {hero.id}\'s shoulder. '
        f'"Now we know more than we knew at dawn," {elder.pronoun()} said. '
        f'"Tomorrow we shall return with the gift in the right proportion."'
    )
    world.say(
        f"{hero.id} looked back at {sanctuary.title}. The mystery was not finished, "
        f"but it had changed shape: now it was a promise waiting for morning."
    )


def closing_blessing(world: World, hero: Entity, sanctuary: Sanctuary) -> None:
    world.say(
        f"After that day, the people of the village measured their gifts with patient hands. "
        f"They spoke less about abundance and more about proportion."
    )
    world.say(
        f"And whenever dawn silvered the stones, {hero.id} smiled to see {sanctuary.visible_blessing} again."
    )


def tell(
    sanctuary: Sanctuary,
    guise: Guise,
    response: Response,
    hero_name: str = "Lina",
    hero_gender: str = "girl",
    elder_type: str = "priestess",
    trait: str = "curious",
) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        role="hero",
        traits=[trait],
    ))
    elder = world.add(Entity(
        id="Elder",
        kind="character",
        type=elder_type,
        role="elder",
        label="the elder",
    ))

    dawn_problem(world, hero, sanctuary)
    world.para()
    clue_scruff(world, hero, guise)
    follow_tracks(world, hero, sanctuary, guise)
    world.para()

    if response.helper:
        consult_elder(world, hero, elder, sanctuary)
        world.para()
        choose_balance(world, hero, sanctuary, response)
    else:
        world.say(
            f"{hero.id} remembered the old carved marks on {sanctuary.bowl}. "
            f'{hero.pronoun().capitalize()} counted them twice and thought, '
            f'"If the tale is true, the answer must be {sanctuary.ratio_words}."'
        )
        choose_balance(world, hero, sanctuary, response)

    if response.solves:
        world.para()
        reveal_twist(world, hero, sanctuary, guise)
        world.para()
        closing_blessing(world, hero, sanctuary)
    else:
        world.para()
        lingering_end(world, hero, elder, sanctuary, guise)

    world.facts.update(
        sanctuary=sanctuary,
        guise=guise,
        response=response,
        hero=hero,
        elder=elder,
        outcome=outcome_of(StoryParams(
            sanctuary=sanctuary.id,
            guise=guise.id,
            response=response.id,
            name=hero_name,
            gender=hero_gender,
            elder=elder_type,
            trait=trait,
        )),
        blessing_restored=world.get("village").meters["blessing"] >= THRESHOLD,
        revealed=world.get("shrine").meters["revealed"] >= THRESHOLD,
        proportion=sanctuary.ratio_words,
    )
    return world


SANCTUARIES = {
    "moon_pool": Sanctuary(
        id="moon_pool",
        title="the Pool of the Moon Hound",
        place="a round spring under white stones",
        deity="the Moon Hound",
        secret_name="the Moon Hound in beggar-shape",
        visible_blessing="silver rings of light on the water",
        faded_sign="The spring lay dull and plain, as if the moon had forgotten its own face.",
        offering_a="milk",
        offering_b="honey",
        ratio_a=2,
        ratio_b=1,
        ratio_words="two spoonfuls of milk for one spoonful of honey",
        bowl="the moon-bowl",
        domain="moon_hound",
        opening_image="white reeds leaned over still water",
        ending_image="silver rings of light ran laughing across the spring",
        tags={"moon", "water", "proportion"},
    ),
    "wind_fig_tree": Sanctuary(
        id="wind_fig_tree",
        title="the Fig Tree of the Hills",
        place="a stone terrace where the wind braided the leaves",
        deity="the Hill Goat of the Wind",
        secret_name="the Hill Goat of the Wind in ragged shape",
        visible_blessing="cool figs ripening without worm-holes",
        faded_sign="The figs hung small and hard, and the leaves made a dry, worried whisper.",
        offering_a="fig slices",
        offering_b="clear water",
        ratio_a=3,
        ratio_b=1,
        ratio_words="three fig slices for one cup of water",
        bowl="the leaf-carved basin",
        domain="wind_goat",
        opening_image="dust combed pale lines over the terrace",
        ending_image="the leaves clapped softly and the figs swelled sweet and cool",
        tags={"wind", "tree", "proportion"},
    ),
    "ember_gate": Sanctuary(
        id="ember_gate",
        title="the Gate of the Little Ember Fox",
        place="a red arch at the edge of the bread ovens",
        deity="the Ember Fox",
        secret_name="the Ember Fox in ash-scruff disguise",
        visible_blessing="warm loaves that rose high and round",
        faded_sign="The ovens burned, but the dough sat heavy, as if warmth had lost heart.",
        offering_a="oil-cake crumbs",
        offering_b="dates",
        ratio_a=1,
        ratio_b=2,
        ratio_words="one pinch of oil-cake crumbs for two date pieces",
        bowl="the ember dish",
        domain="ember_fox",
        opening_image="smoke curled lazily above brick ovens",
        ending_image="golden bread rose in the ovens and the arch glowed like banked coals",
        tags={"fire", "bread", "proportion"},
    ),
}

GUISES = {
    "scruffy_pup": Guise(
        id="scruffy_pup",
        label="a scruffy little pup",
        scruff="silver-gray scruff",
        tracks="small paw marks",
        sound="a thin yip",
        reveal_form="a moon-bright hound as tall as a doorway",
        domain="moon_hound",
        likes_a="milk",
        likes_b="honey",
        tags={"dog", "moon", "scruff"},
    ),
    "scruffy_kid": Guise(
        id="scruffy_kid",
        label="a scruffy mountain kid",
        scruff="wind-rough scruff",
        tracks="split hoofprints",
        sound="a tiny bleat",
        reveal_form="a shining hill goat with horns like curved leaves",
        domain="wind_goat",
        likes_a="fig slices",
        likes_b="clear water",
        tags={"goat", "wind", "scruff"},
    ),
    "scruffy_fox": Guise(
        id="scruffy_fox",
        label="a scruffy ash fox",
        scruff="charcoal scruff",
        tracks="light fox prints",
        sound="a dry chirring bark",
        reveal_form="an ember fox with a tail full of living sparks",
        domain="ember_fox",
        likes_a="oil-cake crumbs",
        likes_b="dates",
        tags={"fox", "fire", "scruff"},
    ),
}

RESPONSES = {
    "measure_alone": Response(
        id="measure_alone",
        sense=3,
        solves=True,
        helper=False,
        text=(
            "{hero} silently set {bowl} on the stone and measured {ratio_words}, "
            "careful not to heap the gift just because fear wanted more."
        ),
        qa_text="measured the offering carefully by the old proportion without asking for help first",
        fail_text="tried to guess alone, but the mystery stayed shut",
        tags={"measure", "curiosity"},
    ),
    "ask_elder_then_measure": Response(
        id="ask_elder_then_measure",
        sense=3,
        solves=True,
        helper=True,
        text=(
            "With the elder beside {object}, {hero} filled {bowl} in the old way: "
            "{ratio_words}. The smallness of the gift looked strange at first, "
            "but its balance looked true."
        ),
        qa_text="asked the elder about the old rule and then measured the offering in the proper proportion",
        fail_text="asked for advice but never made the balanced gift",
        tags={"measure", "helper", "curiosity"},
    ),
    "watch_only": Response(
        id="watch_only",
        sense=2,
        solves=False,
        helper=False,
        text="",
        qa_text="only watched and gathered clues",
        fail_text="only watched and learned a little, but did not solve the mystery that day",
        tags={"wait", "curiosity"},
    ),
    "chase_with_stick": Response(
        id="chase_with_stick",
        sense=1,
        solves=False,
        helper=False,
        text="",
        qa_text="chased the creature with a stick",
        fail_text="frightened the creature away and learned nothing",
        tags={"fear"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Tala", "Neri", "Sora", "Ila", "Dara", "Yara"]
BOY_NAMES = ["Oren", "Tavi", "Niko", "Rami", "Eren", "Kian", "Ari", "Sami"]
TRAITS = ["curious", "patient", "brave", "thoughtful"]
ELDERS = ["priestess", "priest", "mother", "father"]


@dataclass
class StoryParams:
    sanctuary: str
    guise: str
    response: str
    name: str
    gender: str
    elder: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "mystery": [(
        "What is a mystery?",
        "A mystery is something you do not understand yet. You look for clues and think carefully until the answer becomes clear."
    )],
    "proportion": [(
        "What does proportion mean?",
        "Proportion means the right balance between parts. If one thing is too much or too little, the whole mixture can feel wrong."
    )],
    "scruff": [(
        "What is scruff?",
        "Scruff is rough, untidy fur or hair. A scruffy animal looks shaggy instead of smooth."
    )],
    "measure": [(
        "Why does measuring matter?",
        "Measuring helps you give the right amount instead of guessing. In many recipes and old tales, balance matters as much as kindness."
    )],
    "moon": [(
        "Why is the moon important in old stories?",
        "In old stories, the moon often watches the night and marks quiet changes. People treat it as a sign of timing, mystery, and gentle power."
    )],
    "wind": [(
        "Why do myths talk about the wind like a person?",
        "The wind moves things you cannot easily hold or see. That makes it feel alive in myths, as if it carries moods and messages."
    )],
    "fire": [(
        "Why do hearth and oven stories matter?",
        "A warm hearth means food, safety, and home. That is why many old stories treat fire with respect and wonder."
    )],
    "helper": [(
        "Why is it good to ask a wise grown-up for help?",
        "A wise grown-up may know something you do not know yet. Asking for help can turn curiosity into understanding."
    )],
}
KNOWLEDGE_ORDER = ["mystery", "scruff", "proportion", "measure", "moon", "wind", "fire", "helper"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    sanctuary, guise, response, hero = f["sanctuary"], f["guise"], f["response"], f["hero"]
    asks = [
        f'Write a short myth-like story for a 3-to-5-year-old that includes the words "mystery", "scruff", and "proportion".',
        f"Tell a gentle mystery where a curious child named {hero.id} finds {guise.scruff} near {sanctuary.title} and learns the hidden rule of proportion.",
        f"Write a small myth with inner monologue and a twist: the scruffy creature near {sanctuary.title} is not a thief after all."
    ]
    if response.helper:
        asks.append(
            f"Include a wise {f['elder'].label_word} who explains that the right gift is {sanctuary.ratio_words}."
        )
    return asks[:3]


def pair_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    sanctuary = f["sanctuary"]
    guise = f["guise"]
    response = f["response"]
    elder = f["elder"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a {hero.type} who is drawn by curiosity to {sanctuary.title}. The story also includes {guise.label} and {elder.label_word}, who helps hold the old wisdom of the place."
        ),
        (
            "What was the mystery at the beginning?",
            f"The morning blessing at {sanctuary.title} had faded, and nobody knew why. {hero.id} began to wonder after finding {guise.scruff} near the offering stone."
        ),
        (
            f"What clue did {hero.id} find?",
            f"{hero.id} found {guise.scruff} snagged by the altar. That clue made {hero.pronoun('object')} suspect that some living creature had come close to the shrine in the night."
        ),
        (
            f"What did {hero.id} think when {hero.pronoun()} followed the clue?",
            f"{hero.id} kept asking what the scruffy creature wanted and whether the answer was hunger or something deeper. Those thoughts show the child's inner monologue guiding the search."
        ),
    ]
    if response.helper:
        qa.append((
            f"How did {hero.id} solve the problem?",
            f"{hero.id} asked {elder.label_word} for the old rule, then prepared the gift as {sanctuary.ratio_words}. The help mattered because the mystery was really about balance, not about giving the biggest pile of food."
        ))
    elif response.solves:
        qa.append((
            f"How did {hero.id} solve the mystery alone?",
            f"{hero.id} studied the carved bowl and trusted the old pattern, then measured {sanctuary.ratio_words}. The solution worked because {hero.pronoun()} chose proportion and kindness instead of fear."
        ))
    else:
        qa.append((
            f"Did {hero.id} solve the mystery that day?",
            f"No. {hero.id} gathered clues and learned that the answer had something to do with proportion, but the truth was not opened yet. Even so, the mystery changed because now {hero.pronoun()} knew what to try next."
        ))
    if f["revealed"]:
        qa.append((
            "What was the twist?",
            f"The scruffy creature was really {sanctuary.secret_name}. What looked like a shabby thief was actually the hidden guardian of the shrine."
        ))
        qa.append((
            "How did the story end?",
            f"The shrine's blessing returned, and the village saw that careful proportion mattered more than a heaped gift. The ending image proves the change when {sanctuary.ending_image}."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"mystery", "scruff", "proportion", "measure"}
    sanctuary = world.facts["sanctuary"]
    response = world.facts["response"]
    if sanctuary.domain == "moon_hound":
        tags.add("moon")
    elif sanctuary.domain == "wind_goat":
        tags.add("wind")
    else:
        tags.add("fire")
    if response.helper:
        tags.add("helper")
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("moon_pool", "scruffy_pup", "measure_alone", "Lina", "girl", "priestess", "curious"),
    StoryParams("wind_fig_tree", "scruffy_kid", "ask_elder_then_measure", "Oren", "boy", "priest", "patient"),
    StoryParams("ember_gate", "scruffy_fox", "measure_alone", "Mira", "girl", "mother", "thoughtful"),
    StoryParams("moon_pool", "scruffy_pup", "watch_only", "Tavi", "boy", "father", "curious"),
]


ASP_RULES = r"""
compatible(S, G) :- sanctuary_domain(S, D), guise_domain(G, D).
sensible(R) :- response(R), sense(R, N), sense_min(M), N >= M.
valid(S, G, R) :- sanctuary(S), guise(G), response(R), compatible(S, G), sensible(R).

outcome(revealed_with_help) :- chosen_response(R), solves(R), helper(R).
outcome(revealed_alone) :- chosen_response(R), solves(R), not helper(R).
outcome(lingering) :- chosen_response(R), not solves(R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, sanctuary in SANCTUARIES.items():
        lines.append(asp.fact("sanctuary", sid))
        lines.append(asp.fact("sanctuary_domain", sid, sanctuary.domain))
    for gid, guise in GUISES.items():
        lines.append(asp.fact("guise", gid))
        lines.append(asp.fact("guise_domain", gid, guise.domain))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        if response.solves:
            lines.append(asp.fact("solves", rid))
        if response.helper:
            lines.append(asp.fact("helper", rid))
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
    model = asp.one_model(
        asp_program(
            asp.fact("chosen_response", params.response),
            "#show outcome/1."
        )
    )
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))

    cases = list(CURATED)
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            rc = 1
            print(f"MISMATCH in outcome for {p}: asp={asp_outcome(p)} python={outcome_of(p)}")
            break
    else:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} curated scenarios.")

    try:
        smoke = generate(CURATED[0])
        assert smoke.story.strip()
        print("OK: smoke test generated an ordinary story.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Myth-like mystery storyworld: a scruffy clue, a rule of proportion, and a guardian twist."
    )
    ap.add_argument("--sanctuary", choices=SANCTUARIES)
    ap.add_argument("--guise", choices=GUISES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=ELDERS)
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP model and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    if args.sanctuary and args.guise:
        sanctuary = SANCTUARIES[args.sanctuary]
        guise = GUISES[args.guise]
        if not compatible(sanctuary, guise):
            raise StoryError(explain_combo_rejection(sanctuary, guise))

    combos = [
        combo for combo in valid_combos()
        if (args.sanctuary is None or combo[0] == args.sanctuary)
        and (args.guise is None or combo[1] == args.guise)
        and (args.response is None or combo[2] == args.response)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    sanctuary, guise, response = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = args.elder or rng.choice(ELDERS)
    trait = rng.choice(TRAITS)
    return StoryParams(
        sanctuary=sanctuary,
        guise=guise,
        response=response,
        name=name,
        gender=gender,
        elder=elder,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    sanctuary = SANCTUARIES[params.sanctuary]
    guise = GUISES[params.guise]
    response = RESPONSES[params.response]
    world = tell(
        sanctuary=sanctuary,
        guise=guise,
        response=response,
        hero_name=params.name,
        hero_gender=params.gender,
        elder_type=params.elder,
        trait=params.trait,
    )

    story = world.render()
    story = story.replace("{hero}", params.name)
    story = story.replace("{object}", world.facts["elder"].pronoun("object"))

    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in pair_qa(world)],
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
        print(f"{len(combos)} compatible (sanctuary, guise, response) combos:\n")
        for sanctuary, guise, response in combos:
            print(f"  {sanctuary:14} {guise:14} {response}")
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
            header = f"### {p.name}: {p.sanctuary} / {p.guise} / {p.response} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()

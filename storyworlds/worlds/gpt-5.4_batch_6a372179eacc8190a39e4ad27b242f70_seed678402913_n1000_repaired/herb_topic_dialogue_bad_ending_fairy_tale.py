#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/herb_topic_dialogue_bad_ending_fairy_tale.py
=======================================================================

A standalone storyworld for a fairy-tale cautionary tale about fetching a healing
herb, listening to deceptive dialogue, and ending too late with the wrong plant.

The seed required the words "herb" and "topic", plus Dialogue and a Bad Ending.
This world models a small quest in which a child leaves home to gather a remedy,
a trickster changes the topic and points to a look-alike herb, and the child
returns with the wrong bundle. The cure fails, and the last image proves the loss.

Run it
------
    python storyworlds/worlds/gpt-5.4/herb_topic_dialogue_bad_ending_fairy_tale.py
    python storyworlds/worlds/gpt-5.4/herb_topic_dialogue_bad_ending_fairy_tale.py --ailment cough --false-herb witchweed
    python storyworlds/worlds/gpt-5.4/herb_topic_dialogue_bad_ending_fairy_tale.py --all
    python storyworlds/worlds/gpt-5.4/herb_topic_dialogue_bad_ending_fairy_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/herb_topic_dialogue_bad_ending_fairy_tale.py --verify
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

# Make the shared result containers importable when this script is run directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"                 # character | place | herb | object
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    poisonous: bool = False
    healing_for: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "queen", "woman", "witch"}
        male = {"boy", "father", "king", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father"}.get(self.type, self.type)


@dataclass
class Realm:
    id: str
    home: str
    path: str
    herb_place: str
    ending_image: str
    tricksters: set[str] = field(default_factory=set)
    wild_herbs: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Ailment:
    id: str
    symptom: str
    true_herb: str
    request: str
    lesson: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Herb:
    id: str
    label: str
    phrase: str
    place_hint: str
    resembles: set[str] = field(default_factory=set)
    heals: set[str] = field(default_factory=set)
    harm: int = 0
    bitter: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Trickster:
    id: str
    label: str
    phrase: str
    opening: str
    twist: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    warning: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    realm: str
    ailment: str
    false_herb: str
    trickster: str
    helper: str
    hero_name: str
    hero_gender: str
    elder_name: str
    elder_type: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
REALMS = {
    "cottage": Realm(
        id="cottage",
        home="a mossy cottage at the edge of the wood",
        path="a crooked path under hazel branches",
        herb_place="the sunny bank beyond the creek",
        ending_image="Outside the mossy cottage, the wind worried the shutters while the true herb still slept beyond the dark creek.",
        tricksters={"fox", "crow"},
        wild_herbs={"witchweed", "frostfern", "silvershade"},
        tags={"forest", "cottage"},
    ),
    "tower": Realm(
        id="tower",
        home="a little stone tower above the briars",
        path="a steep stair and a ferny lane below the hill",
        herb_place="the bright meadow under the old bell tree",
        ending_image="Below the stone tower, the bell rope stirred in the cold air, and the right herb remained untouched under the far meadow moon.",
        tricksters={"crow", "cat"},
        wild_herbs={"witchweed", "silvershade"},
        tags={"tower"},
    ),
    "mill": Realm(
        id="mill",
        home="a wooden mill beside the silver stream",
        path="a damp path that curled past the water wheel",
        herb_place="the dry rise above the reeds",
        ending_image="By the sleeping mill wheel, the stream kept talking to itself while the good herb stood unpicked on the dry rise.",
        tricksters={"fox", "cat"},
        wild_herbs={"witchweed", "frostfern"},
        tags={"mill", "stream"},
    ),
}

AILMENTS = {
    "cough": Ailment(
        id="cough",
        symptom="a hard cough that shook the bed-curtains",
        true_herb="sunmint",
        request="Only sunmint from the bright side of the path can soften this cough.",
        lesson="A sweet smell is not enough; the right herb matters.",
        tags={"cough", "medicine"},
    ),
    "fever": Ailment(
        id="fever",
        symptom="a hot fever that made the room feel close and breathless",
        true_herb="dewleaf",
        request="Only dewleaf gathered before dusk can cool this fever.",
        lesson="A shining leaf is not the same as a healing one.",
        tags={"fever", "medicine"},
    ),
    "nightmares": Ailment(
        id="nightmares",
        symptom="bad dreams that left the pillow damp with tears",
        true_herb="moonbalm",
        request="Only moonbalm from the quiet hill can settle these dreams.",
        lesson="A silver glow can fool the eye when the heart grows hurried.",
        tags={"dream", "medicine"},
    ),
}

HERBS = {
    "sunmint": Herb(
        id="sunmint",
        label="sunmint",
        phrase="a bundle of sunmint",
        place_hint="It grows where the light rests longest.",
        heals={"cough"},
        bitter=False,
        tags={"herb", "mint", "healing"},
    ),
    "dewleaf": Herb(
        id="dewleaf",
        label="dewleaf",
        phrase="a spray of dewleaf",
        place_hint="Its edges stay cool even after noon.",
        heals={"fever"},
        bitter=False,
        tags={"herb", "leaf", "healing"},
    ),
    "moonbalm": Herb(
        id="moonbalm",
        label="moonbalm",
        phrase="a pale handful of moonbalm",
        place_hint="It waits in the quiet places after sunset.",
        heals={"nightmares"},
        bitter=False,
        tags={"herb", "healing", "dream"},
    ),
    "witchweed": Herb(
        id="witchweed",
        label="witchweed",
        phrase="a bundle of witchweed",
        place_hint="It glitters where the path is easiest, not where the healing is true.",
        resembles={"sunmint"},
        harm=1,
        bitter=True,
        tags={"herb", "poison", "bad_choice"},
    ),
    "frostfern": Herb(
        id="frostfern",
        label="frostfern",
        phrase="a spray of frostfern",
        place_hint="Its leaves shine cold, but they do not mend a fever.",
        resembles={"dewleaf"},
        harm=0,
        bitter=False,
        tags={"herb", "bad_choice"},
    ),
    "silvershade": Herb(
        id="silvershade",
        label="silvershade",
        phrase="a pale handful of silvershade",
        place_hint="It shines prettily in dusk and lies sweetly to hurried eyes.",
        resembles={"moonbalm"},
        harm=1,
        bitter=True,
        tags={"herb", "poison", "bad_choice"},
    ),
}

TRICKSTERS = {
    "fox": Trickster(
        id="fox",
        label="fox",
        phrase="a red fox with a courtly tail",
        opening='"Good evening, little traveler," said the fox. "What is your errand?"',
        twist='"Why keep to that old topic?" asked the fox softly. "This other herb is nearer, brighter, and just as good."',
        tags={"fox", "lie"},
    ),
    "crow": Trickster(
        id="crow",
        label="crow",
        phrase="a glossy crow on a bent branch",
        opening='"Caw, caw, what herb do you seek?" asked the crow. "Tell me the whole matter."',
        twist='"Let us change the topic," croaked the crow. "Take the shining one below. Old folk never know the difference."',
        tags={"crow", "lie"},
    ),
    "cat": Trickster(
        id="cat",
        label="cat",
        phrase="a velvet cat with lantern eyes",
        opening='"Where are you hurrying with that basket?" purred the cat. "You look far too earnest for such a small road."',
        twist='"Why make the old topic so heavy?" purred the cat. "Pick the silver herb by your foot and be done before dark."',
        tags={"cat", "lie"},
    ),
}

HELPERS = {
    "robin": Helper(
        id="robin",
        label="robin",
        warning='"A true herb is not always the nearest herb," chirped the robin. "Mind the elder\'s words."',
        tags={"bird", "warning"},
    ),
    "hedgehog": Helper(
        id="hedgehog",
        label="hedgehog",
        warning='"Slow feet make fewer mistakes," said the hedgehog. "Do not let a smooth tongue hurry you."',
        tags={"warning", "forest"},
    ),
    "cricket": Helper(
        id="cricket",
        label="cricket",
        warning='"Listen to the path, not the flatterer," sang the cricket. "The right herb grows where you were told."',
        tags={"warning", "song"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Elsie", "Nell", "Ivy", "Pippa"]
BOY_NAMES = ["Tobin", "Rowan", "Finn", "Alder", "Perrin", "Leo"]
TRAITS = ["eager", "kind", "hurried", "trusting", "dutiful", "curious"]


# ---------------------------------------------------------------------------
# Constraints
# ---------------------------------------------------------------------------
def false_matches_need(ailment: Ailment, false_herb: Herb) -> bool:
    return ailment.true_herb in false_herb.resembles


def combo_possible(realm: Realm, ailment: Ailment, false_herb: Herb, trickster: Trickster) -> bool:
    return (
        false_matches_need(ailment, false_herb)
        and false_herb.id in realm.wild_herbs
        and trickster.id in realm.tricksters
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for realm_id, realm in REALMS.items():
        for ailment_id, ailment in AILMENTS.items():
            for herb_id, herb in HERBS.items():
                if herb_id not in {"witchweed", "frostfern", "silvershade"}:
                    continue
                for trickster_id, trickster in TRICKSTERS.items():
                    if combo_possible(realm, ailment, herb, trickster):
                        combos.append((realm_id, ailment_id, herb_id, trickster_id))
    return combos


def outcome_of(params: StoryParams) -> str:
    false_herb = HERBS[params.false_herb]
    return "worsened" if false_herb.harm > 0 else "uncured"


def explain_rejection(realm_id: str, ailment_id: str, false_herb_id: str, trickster_id: str) -> str:
    realm = REALMS[realm_id]
    ailment = AILMENTS[ailment_id]
    herb = HERBS[false_herb_id]
    trickster = TRICKSTERS[trickster_id]
    if not false_matches_need(ailment, herb):
        return (
            f"(No story: {herb.label} does not plausibly look like the remedy for "
            f"{ailment.id}. The mistake must be a believable herb mix-up.)"
        )
    if herb.id not in realm.wild_herbs:
        return (
            f"(No story: {herb.label} does not grow in the {realm.id} setting here, "
            f"so the child could not reasonably be tricked into picking it there.)"
        )
    if trickster.id not in realm.tricksters:
        return (
            f"(No story: the {trickster.label} is not part of the chosen realm's tale logic.)"
        )
    return "(No story: that combination does not fit the world.)"


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_wrong_brew(world: World) -> list[str]:
    out: list[str] = []
    patient = world.get("elder")
    pot = world.get("pot")
    if pot.meters["wrong_brew"] < THRESHOLD:
        return out
    sig = ("wrong_brew",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    patient.meters["healed"] = 0.0
    patient.meters["sick"] += 1
    patient.memes["weariness"] += 1
    hero = world.get("hero")
    hero.memes["regret"] += 1
    hero.memes["hope"] = 0.0
    cottage = world.get("home")
    cottage.memes["gloom"] += 1
    out.append("__bad_brew__")
    return out


def _r_harmful_herb(world: World) -> list[str]:
    out: list[str] = []
    herb = world.get("chosen_herb")
    if herb.meters["harmful"] < THRESHOLD:
        return out
    sig = ("harmful_herb",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    patient = world.get("elder")
    patient.meters["sick"] += 1
    patient.memes["weariness"] += 1
    hero = world.get("hero")
    hero.memes["fear"] += 1
    out.append("__harm__")
    return out


CAUSAL_RULES = [
    Rule(name="wrong_brew", tag="physical", apply=_r_wrong_brew),
    Rule(name="harmful_herb", tag="physical", apply=_r_harmful_herb),
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


# ---------------------------------------------------------------------------
# Simulation helpers
# ---------------------------------------------------------------------------
def predict_choice(world: World, false_herb_id: str) -> dict:
    sim = world.copy()
    herb = sim.get("chosen_herb")
    cfg = HERBS[false_herb_id]
    herb.label = cfg.label
    herb.phrase = cfg.phrase
    herb.tags = set(cfg.tags)
    herb.meters["wrong"] = 1
    if cfg.harm > 0:
        herb.meters["harmful"] = 1
    pot = sim.get("pot")
    pot.meters["wrong_brew"] = 1
    propagate(sim, narrate=False)
    patient = sim.get("elder")
    return {
        "still_sick": patient.meters["sick"],
        "gloom": sim.get("home").memes["gloom"],
        "regret": sim.get("hero").memes["regret"],
    }


# ---------------------------------------------------------------------------
# Verbs
# ---------------------------------------------------------------------------
def opening(world: World, realm: Realm, hero: Entity, elder: Entity, ailment: Ailment, true_herb: Herb) -> None:
    elder.meters["sick"] = 1
    hero.memes["love"] += 1
    hero.memes["hope"] += 1
    world.say(
        f"Once, in {realm.home}, {hero.id} sat beside {elder.id}, who had {ailment.symptom}."
    )
    world.say(
        f'The topic in that small room was only one thing: the herb that might help. '
        f'"{ailment.request}" {elder.id} whispered.'
    )
    world.say(
        f'{hero.id} took up a little basket. "{true_herb.label.capitalize()} it shall be," '
        f'{hero.pronoun()} said.'
    )


def set_out(world: World, realm: Realm, hero: Entity, helper: Helper) -> None:
    world.say(
        f"So {hero.id} set out along {realm.path}, while evening thinned the gold from the leaves."
    )
    world.say(
        f'A {helper.label} appeared by the roadside and called, {helper.warning}'
    )


def meet_trickster(world: World, hero: Entity, trickster: Trickster) -> None:
    hero.memes["trust"] += 1
    world.say(
        f"Near a fork in the path waited {trickster.phrase}. {trickster.opening}"
    )
    world.say(
        f'"I seek the healing herb," said {hero.id}. {trickster.twist}'
    )


def ignore_warning(world: World, hero: Entity, helper: Helper) -> None:
    hero.memes["haste"] += 1
    hero.memes["doubt"] += 1
    world.say(
        f'The {helper.label} rustled uneasily, but {hero.id} only held the basket tighter. '
        f'"If it is nearer, I must be quick," {hero.pronoun()} answered.'
    )


def choose_false_herb(world: World, false_herb: Herb, true_herb: Herb, realm: Realm) -> None:
    chosen = world.get("chosen_herb")
    chosen.label = false_herb.label
    chosen.phrase = false_herb.phrase
    chosen.tags = set(false_herb.tags)
    chosen.meters["wrong"] = 1
    if false_herb.harm > 0:
        chosen.meters["harmful"] = 1
    world.say(
        f"Instead of searching for {true_herb.label} at {realm.herb_place}, the child stooped by the easy path and gathered {false_herb.phrase}."
    )
    if false_herb.bitter:
        world.say(
            f"The leaves smelled sharp and strange, but hurry made them seem wise enough."
        )
    else:
        world.say(
            f"The leaves shone prettily, and their shine was enough to fool a hurried eye."
        )


def return_home(world: World, realm: Realm, hero: Entity, elder: Entity) -> None:
    hero.memes["hope"] += 1
    world.say(
        f'By the time {hero.id} came hurrying home, the light had nearly gone from the doorstone. '
        f'"I have the herb," {hero.pronoun()} cried.'
    )
    world.say(
        f"{elder.id} smiled faintly, because love often believes before it knows."
    )


def brew(world: World, false_herb: Herb) -> None:
    pot = world.get("pot")
    pot.meters["wrong_brew"] = 1
    if false_herb.harm > 0:
        world.say(
            f"They steeped the leaves in hot water, and the steam rose with a bitter smell."
        )
    else:
        world.say(
            f"They steeped the leaves in hot water, and the tea looked fair enough in the cup."
        )
    propagate(world, narrate=False)


def bad_ending(world: World, realm: Realm, hero: Entity, elder: Entity, ailment: Ailment, false_herb: Herb) -> None:
    outcome = world.facts["outcome"]
    if outcome == "worsened":
        world.say(
            f"But when {elder.id} drank, the cup did not help. The cough grew rougher, or the fever burned on, or the bad dreams waited still; the wrong herb had made a hard night harder."
        )
        world.say(
            f'{hero.id} looked at the empty cup and understood too late. "I let a liar change the topic and my feet followed the easy road," {hero.pronoun()} whispered.'
        )
    else:
        world.say(
            f"But when {elder.id} drank, nothing gentle changed. {ailment.symptom.capitalize()} stayed in the room as if it had taken root there."
        )
        world.say(
            f'{hero.id} lowered the basket. "I brought a pretty herb, not the true one," {hero.pronoun()} said, and regret felt heavier than the handle.'
        )
    world.say(realm.ending_image)


# ---------------------------------------------------------------------------
# Story construction
# ---------------------------------------------------------------------------
def tell(
    realm: Realm,
    ailment: Ailment,
    false_herb: Herb,
    trickster: Trickster,
    helper: Helper,
    hero_name: str,
    hero_gender: str,
    elder_name: str,
    elder_type: str,
    trait: str,
) -> World:
    world = World()
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_gender,
        label=hero_name,
        phrase=hero_name,
        role="hero",
        traits=[trait],
    ))
    elder = world.add(Entity(
        id="elder",
        kind="character",
        type=elder_type,
        label=elder_name,
        phrase=elder_name,
        role="elder",
    ))
    world.add(Entity(
        id="home",
        kind="place",
        type="home",
        label=realm.home,
        phrase=realm.home,
        tags=set(realm.tags),
    ))
    world.add(Entity(
        id="pot",
        kind="object",
        type="pot",
        label="teapot",
        phrase="the little teapot",
    ))
    world.add(Entity(
        id="chosen_herb",
        kind="herb",
        type="herb",
        label="",
        phrase="",
    ))

    true_herb = HERBS[ailment.true_herb]

    opening(world, realm, hero, elder, ailment, true_herb)
    world.para()
    set_out(world, realm, hero, helper)
    meet_trickster(world, hero, trickster)
    ignore_warning(world, hero, helper)
    choose_false_herb(world, false_herb, true_herb, realm)
    world.para()
    return_home(world, realm, hero, elder)
    brew(world, false_herb)

    outcome = "worsened" if false_herb.harm > 0 else "uncured"
    world.facts["outcome"] = outcome
    bad_ending(world, realm, hero, elder, ailment, false_herb)

    world.facts.update(
        realm=realm,
        ailment=ailment,
        true_herb=true_herb,
        false_herb=false_herb,
        trickster=trickster,
        helper=helper,
        hero=hero,
        elder=elder,
        predicted=predict_choice(world, false_herb.id),
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "herb": [
        (
            "What is an herb?",
            "An herb is a plant people use for smell, taste, or medicine. Some herbs help, but only if you choose the right one."
        )
    ],
    "medicine": [
        (
            "Why does the right herb matter?",
            "Plants can look alike while doing very different things. A healing herb helps only when it is truly the one meant for the sickness."
        )
    ],
    "fox": [
        (
            "Why should you be careful with a fox in a fairy tale?",
            "In fairy tales, a fox is often clever and slippery with words. That means a fox may sound helpful while leading someone the wrong way."
        )
    ],
    "crow": [
        (
            "Why is listening to a crow in a fairy tale risky?",
            "A fairy-tale crow may know many things, but it may also enjoy teasing or misleading. A loud voice is not always a truthful one."
        )
    ],
    "cat": [
        (
            "Why can a fairy-tale cat be untrustworthy?",
            "A fairy-tale cat may speak sweetly and make the easy path sound safe. Gentle words do not always mean good advice."
        )
    ],
    "warning": [
        (
            "Why should you listen to a warning on a journey?",
            "Warnings can point back to what is true when you feel rushed. They help you remember the careful instruction you started with."
        )
    ],
    "bad_choice": [
        (
            "Why can a pretty plant still be the wrong one?",
            "A pretty plant may only look right from far away. The eye can be fooled when someone is hurrying."
        )
    ],
    "poison": [
        (
            "Why can the wrong herb make things worse?",
            "Some plants do not heal at all, and some upset the body instead. That is why guessing with medicine is dangerous."
        )
    ],
    "dream": [
        (
            "What are bad dreams?",
            "Bad dreams are scary dreams that wake someone up and leave them frightened. Gentle rest and comfort can help, but a wrong remedy will not."
        )
    ],
}

KNOWLEDGE_ORDER = ["herb", "medicine", "warning", "fox", "crow", "cat", "bad_choice", "poison", "dream"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    ailment = f["ailment"]
    false_herb = f["false_herb"]
    trickster = f["trickster"]
    return [
        f'Write a short fairy tale for a 3-to-5-year-old that includes the words "herb" and "topic", with spoken dialogue and a bad ending.',
        f"Tell a cautionary fairy tale where {hero.label} goes to fetch a healing herb for {elder.label}, but a talking {trickster.label} changes the topic and tricks the child into bringing {false_herb.label} instead.",
        f"Write a gentle-but-sad fairy tale about hurrying, listening to the wrong voice, and failing to cure {ailment.id} because the child picked the wrong herb.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    ailment = f["ailment"]
    true_herb = f["true_herb"]
    false_herb = f["false_herb"]
    trickster = f["trickster"]
    helper = f["helper"]
    pred = f["predicted"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, who went to find a healing herb for {elder.label}. It is also about the talking {trickster.label} whose words led the child away from the true path."
        ),
        (
            f"What herb was really needed?",
            f"{true_herb.label.capitalize()} was the true remedy for {ailment.id}. {elder.label} said so at the beginning, which is why forgetting that instruction mattered."
        ),
        (
            "How did the trickster fool the child?",
            f"The {trickster.label} used dialogue to make the easy path sound clever and safe. By changing the topic from 'the right herb' to 'the nearest herb,' the trickster made hurry feel wiser than care."
        ),
        (
            f"What warning did the {helper.label} give?",
            f"The {helper.label} warned that the nearest herb was not always the true one. That warning mattered because the child had already been told exactly where the healing plant should grow."
        ),
        (
            f"Why was the ending bad?",
            f"The child brought {false_herb.label} instead of {true_herb.label}, so the tea could not truly help. In the world model, the wrong brew left sickness in the house and filled the child with regret."
        ),
    ]
    if f["outcome"] == "worsened":
        qa.append(
            (
                f"What happened after {elder.label} drank the tea?",
                f"The drink made the night worse instead of better. The chosen herb was not only wrong, but harmful enough to increase fear and weariness."
            )
        )
    else:
        qa.append(
            (
                f"What happened after {elder.label} drank the tea?",
                f"Nothing gentle changed, because the tea was made from the wrong plant. The sickness stayed because beauty and shine were not the same as healing."
            )
        )
    qa.append(
        (
            "How could the child have avoided the mistake?",
            f"{hero.label} could have kept the topic on the elder's instruction and searched for {true_herb.label} where it was supposed to grow. The prediction for the wrong choice already showed more sickness, more gloom, and more regret: {int(pred['still_sick'])} sickness, {int(pred['gloom'])} gloom, and {int(pred['regret'])} regret."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"herb", "medicine", "warning", "bad_choice"}
    false_herb = world.facts["false_herb"]
    trickster = world.facts["trickster"]
    ailment = world.facts["ailment"]
    tags |= set(false_herb.tags)
    tags |= set(trickster.tags)
    tags |= set(ailment.tags)
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits: list[str] = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:11} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
matches_need(A, H) :- ailment(A), false_herb(H), true_of(A, T), resembles(H, T).
possible(R, A, H, Tr) :- realm(R), ailment(A), false_herb(H), trickster(Tr),
                         matches_need(A, H), grows_in(R, H), appears_in(R, Tr).

harmful_outcome(worsened) :- chosen_false_herb(H), harm(H, V), V > 0.
harmful_outcome(uncured)  :- chosen_false_herb(H), harm(H, 0).

valid(R, A, H, Tr) :- possible(R, A, H, Tr).
outcome(O) :- harmful_outcome(O).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for realm_id, realm in REALMS.items():
        lines.append(asp.fact("realm", realm_id))
        for herb_id in sorted(realm.wild_herbs):
            if herb_id in {"witchweed", "frostfern", "silvershade"}:
                lines.append(asp.fact("grows_in", realm_id, herb_id))
        for trickster_id in sorted(realm.tricksters):
            lines.append(asp.fact("appears_in", realm_id, trickster_id))
    for ailment_id, ailment in AILMENTS.items():
        lines.append(asp.fact("ailment", ailment_id))
        lines.append(asp.fact("true_of", ailment_id, ailment.true_herb))
    for herb_id, herb in HERBS.items():
        if herb_id in {"witchweed", "frostfern", "silvershade"}:
            lines.append(asp.fact("false_herb", herb_id))
            for look in sorted(herb.resembles):
                lines.append(asp.fact("resembles", herb_id, look))
            lines.append(asp.fact("harm", herb_id, herb.harm))
    for trickster_id in TRICKSTERS:
        lines.append(asp.fact("trickster", trickster_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    model = asp.one_model(
        asp_program(
            f"{asp.fact('chosen_false_herb', params.false_herb)}",
            "#show outcome/1.",
        )
    )
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        realm="cottage",
        ailment="cough",
        false_herb="witchweed",
        trickster="fox",
        helper="robin",
        hero_name="Lina",
        hero_gender="girl",
        elder_name="Grandmother",
        elder_type="mother",
        trait="eager",
    ),
    StoryParams(
        realm="tower",
        ailment="nightmares",
        false_herb="silvershade",
        trickster="crow",
        helper="cricket",
        hero_name="Rowan",
        hero_gender="boy",
        elder_name="Aunt Mira",
        elder_type="mother",
        trait="trusting",
    ),
    StoryParams(
        realm="mill",
        ailment="fever",
        false_herb="frostfern",
        trickster="cat",
        helper="hedgehog",
        hero_name="Perrin",
        hero_gender="boy",
        elder_name="Mother Elin",
        elder_type="mother",
        trait="hurried",
    ),
]


# ---------------------------------------------------------------------------
# CLI and interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A fairy-tale herb storyworld with deceptive dialogue and a bad ending."
    )
    ap.add_argument("--realm", choices=REALMS)
    ap.add_argument("--ailment", choices=AILMENTS)
    ap.add_argument("--false-herb", dest="false_herb", choices=["witchweed", "frostfern", "silvershade"])
    ap.add_argument("--trickster", choices=TRICKSTERS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check Python/ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.realm and args.ailment and args.false_herb and args.trickster:
        if not combo_possible(
            REALMS[args.realm],
            AILMENTS[args.ailment],
            HERBS[args.false_herb],
            TRICKSTERS[args.trickster],
        ):
            raise StoryError(explain_rejection(args.realm, args.ailment, args.false_herb, args.trickster))

    combos = [
        combo for combo in valid_combos()
        if (args.realm is None or combo[0] == args.realm)
        and (args.ailment is None or combo[1] == args.ailment)
        and (args.false_herb is None or combo[2] == args.false_herb)
        and (args.trickster is None or combo[3] == args.trickster)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    realm_id, ailment_id, false_herb_id, trickster_id = rng.choice(sorted(combos))
    helper_id = args.helper or rng.choice(sorted(HELPERS))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    elder_name = rng.choice(["Grandmother", "Mother Elin", "Aunt Mira", "Old Nessa"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        realm=realm_id,
        ailment=ailment_id,
        false_herb=false_herb_id,
        trickster=trickster_id,
        helper=helper_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        elder_name=elder_name,
        elder_type="mother",
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        realm = REALMS[params.realm]
        ailment = AILMENTS[params.ailment]
        false_herb = HERBS[params.false_herb]
        trickster = TRICKSTERS[params.trickster]
        helper = HELPERS[params.helper]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter: {err.args[0]})") from err

    if not combo_possible(realm, ailment, false_herb, trickster):
        raise StoryError(explain_rejection(params.realm, params.ailment, params.false_herb, params.trickster))

    world = tell(
        realm=realm,
        ailment=ailment,
        false_herb=false_herb,
        trickster=trickster,
        helper=helper,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        elder_name=params.elder_name,
        elder_type=params.elder_type,
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


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: valid combo gate matches ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in clingo:", sorted(cl - py))

    checked = 0
    for params in CURATED:
        py_out = outcome_of(params)
        cl_out = asp_outcome(params)
        checked += 1
        if py_out != cl_out:
            rc = 1
            print(f"MISMATCH outcome for {params.false_herb}: python={py_out} clingo={cl_out}")
    if rc == 0:
        print(f"OK: outcome model matches on {checked} curated scenarios.")

    try:
        sample = generate(CURATED[0])
        if not sample.story or "herb" not in sample.story.lower():
            raise StoryError("(Smoke test failed: generated story missing expected content.)")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (realm, ailment, false_herb, trickster) combos:\n")
        for realm_id, ailment_id, herb_id, trickster_id in combos:
            print(f"  {realm_id:8} {ailment_id:11} {herb_id:12} {trickster_id}")
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
            header = f"### {p.hero_name}: {p.false_herb} for {p.ailment} in {p.realm} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

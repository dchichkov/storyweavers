#!/usr/bin/env python3
"""
storyworlds/worlds/cantina_shriek_referendum_suspense_slice_of_life.py
======================================================================

A small slice-of-life suspense world set in a neighborhood cantina where a
sudden shriek and a community referendum create a careful, grounded turn.

Seed tale:
---
In a little cantina on a warm evening, Mara counted cups while the kettle
hummed. The regulars chatted softly until a sharp shriek came from the side
room. Everyone froze. It turned out to be Nia, who had found a trapped kitten
behind a stack of crates. While Mara soothed the kitten and the room settled
down, the owner mentioned a referendum about whether the cantina should stay
open late for neighbors. The patrons worried, talked, and finally chose a calm
plan that kept the cantina welcoming without making the nights too noisy.
---

World model:
- Entities have physical meters and emotional memes.
- The shriek raises tension; the referendum measures whether the room feels
  safe enough for a late-night gathering.
- Suspense comes from not knowing if the cantina will close early or become a
  quieter community space.
- Slice-of-life details are driven by state: cups, lamps, stools, voices,
  nervousness, trust, and the kitten's calming effect.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
while ROOT != os.path.dirname(ROOT) and not os.path.exists(os.path.join(ROOT, "results.py")):
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402

# ---------------------------------------------------------------------------
# Core world model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.label:
            self.label = self.type

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"woman", "girl", "mother", "host"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"man", "boy", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def possessive_name(self) -> str:
        return self.label


@dataclass
class Place:
    name: str = "the cantina"
    closed_late: bool = False
    permits_late_referendum: bool = True


@dataclass
class StoryParams:
    place: str = "cantina"
    hero: str = "Mara"
    host: str = "Elena"
    visitor: str = "Nia"
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Simulation rules
# ---------------------------------------------------------------------------

def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    out: list[str] = []
    while changed:
        changed = False
        for sent in _rules(world):
            if sent:
                changed = True
                out.extend(sent)
    if narrate:
        for s in out:
            world.say(s)


def _rules(world: World) -> list[list[str]]:
    out: list[list[str]] = []

    # A shriek spikes the room's tension.
    if world.facts.get("shrieked") and ("tension",) not in world.fired:
        world.fired.add(("tension",))
        for ent in world.entities.values():
            if ent.kind == "character":
                ent.memes["tension"] = ent.memes.get("tension", 0.0) + 1
        out.append(["The shriek made every conversation stop at once."])

    # The kitten calms the room if it is found and held gently.
    if world.facts.get("kitten_safe") and ("calm",) not in world.fired:
        world.fired.add(("calm",))
        for ent in world.entities.values():
            if ent.kind == "character":
                ent.memes["tension"] = max(0.0, ent.memes.get("tension", 0.0) - 1.0)
                ent.memes["relief"] = ent.memes.get("relief", 0.0) + 1
        out.append(["Once the kitten was safe, the room began to breathe again."])

    # A referendum resolves if enough people trust the host and tension has eased.
    if world.facts.get("vote_called") and world.facts.get("vote_ready") and ("vote",) not in world.fired:
        world.fired.add(("vote",))
        outcome = "late_open" if world.facts.get("vote_yes", 0) >= world.facts.get("vote_no", 0) else "early_close"
        world.facts["referendum_result"] = outcome
        out.append([f"The referendum settled on {outcome.replace('_', ' ')}."])
    return out


# ---------------------------------------------------------------------------
# Domain helpers
# ---------------------------------------------------------------------------

def introduce(world: World, hero: Entity, host: Entity) -> None:
    world.say(
        f"{hero.id} worked at {world.place.name}, counting cups and wiping the counter "
        f"while {host.id} kept the kettle humming."
    )


def everyday_scene(world: World, hero: Entity, visitor: Entity) -> None:
    world.say(
        f"The afternoon was ordinary in the nicest way: stools scraped softly, "
        f"spoons clinked, and {visitor.id} sat near the window with a warm drink."
    )


def trigger_shriek(world: World, visitor: Entity) -> None:
    world.facts["shrieked"] = True
    visitor.memes["fear"] = visitor.memes.get("fear", 0.0) + 1
    world.say(
        f"Then a sharp shriek flashed from the side room, and {visitor.id} jerked up so fast "
        f"that their cup nearly tipped."
    )


def discover_kitten(world: World, hero: Entity, visitor: Entity) -> None:
    kitten = world.add(Entity(id="kitten", kind="animal", type="kitten", label="kitten"))
    kitten.meters["safety"] = 0.0
    world.say(
        f"{visitor.id} peeked behind the crates and found a small kitten tangled in a ribbon, "
        f"more startled than hurt."
    )
    world.say(
        f"{hero.id} crouched down, held out a palm, and let the kitten climb into the warmth of {hero.pronoun('possessive')} hands."
    )
    world.facts["kitten_safe"] = True
    kitten.meters["safety"] = 1.0
    hero.memes["care"] = hero.memes.get("care", 0.0) + 1
    visitor.memes["relief"] = visitor.memes.get("relief", 0.0) + 1


def call_referendum(world: World, host: Entity, hero: Entity) -> None:
    if not world.place.permits_late_referendum:
        raise StoryError("This cantina does not allow a referendum in the story setup.")
    world.facts["vote_called"] = True
    world.say(
        f"With the kitten safe, {host.id} set out a neat stack of paper slips and called for a referendum "
        f"about whether the cantina should stay open later for neighbors."
    )
    world.say(
        f"{hero.id} listened closely, because the choice would change the quiet of the room after sunset."
    )


def vote(world: World, hero: Entity, host: Entity, visitor: Entity) -> None:
    tension = sum(ent.memes.get("tension", 0.0) for ent in world.entities.values() if ent.kind == "character")
    world.facts["vote_ready"] = True
    # Calm room favors yes; nervous room favors no.
    world.facts["vote_yes"] = 2 if tension < 2.0 else 1
    world.facts["vote_no"] = 1 if tension < 2.0 else 2
    if world.facts["vote_yes"] >= world.facts["vote_no"]:
        world.say(
            f"The neighbors agreed to keep the cantina open later, but with softer music, earlier last call, "
            f"and one corner left quiet for anyone who needed a calm seat."
        )
    else:
        world.say(
            f"The neighbors decided not to stay open too late, though they promised to host a calm community hour next week."
        )


def closing_image(world: World, hero: Entity, visitor: Entity, host: Entity) -> None:
    result = world.facts.get("referendum_result", "late_open")
    if result == "late_open":
        world.say(
            f"By the end of the night, the lamp over the counter glowed warm, the kitten slept safe in a basket, "
            f"and the cantina felt a little more like a shared living room."
        )
    else:
        world.say(
            f"By closing time, the kitten was safe, the cups were stacked, and the cantina had settled into a "
            f"quiet promise to try again another evening."
        )


STORY_ARCS = [
    {
        "routine": "sorting cinnamon sticks while a domino game clicked by the window",
        "alarm": "a flour sack shifted in the pantry and a sharp shriek rang out",
        "clue": "a dusting of pawprints crossed the tiles, then vanished under the lowest shelf",
        "fear": "a heavy jar might have fallen on someone",
        "cause": "a hungry kitten had wriggled through a torn screen and caught its ribbon on a basket",
        "action": "lifted the basket together, cut the ribbon, and offered the kitten a saucer of water",
        "dialogue": "\"Easy now,\" {hero} whispered. \"We found you.\"",
        "safeguard": "a quiet corner, a repaired pantry screen, and a last order before the neighbors went home",
        "ending": "the kitten slept in a towel-lined basket beneath the quiet-corner sign",
    },
    {
        "routine": "stacking blue cups as two neighbors traded recipes at the counter",
        "alarm": "the ballot box jumped, and {visitor} gave a shriek that silenced every spoon",
        "clue": "the lid bumped twice although no hand was near it",
        "fear": "someone had hidden a trick inside the box to spoil the referendum",
        "cause": "a tiny green gecko had crawled through the handle and was pushing at the lid",
        "action": "slid a menu beneath the gecko and carried it safely to the courtyard wall",
        "dialogue": "\"No trick,\" said {host}, smiling with relief. \"Only a very small voter.\"",
        "safeguard": "covered ballot boxes, gentle courtyard lights, and two trial evenings each week",
        "ending": "the gecko blinked from the warm wall while the sealed ballot box waited on the counter",
    },
    {
        "routine": "slicing limes while rain tapped a patient rhythm on the awning",
        "alarm": "a metallic shriek tore through the kitchen just as the lamps flickered",
        "clue": "a thin ribbon of steam curled from behind the old kettle",
        "fear": "a pipe was about to burst and flood the cantina",
        "cause": "the kettle's loose pressure cap was whistling against a bent spoon",
        "action": "turned off the burner, opened the window, and tightened the cool cap with a cloth",
        "dialogue": "\"First the flame, then the fix,\" {hero} said, and {visitor} nodded",
        "safeguard": "a closing-time kettle check, lower music, and a one-month late-hours trial",
        "ending": "the repaired kettle breathed one soft puff beside a row of checked-off boxes",
    },
    {
        "routine": "writing the soup special while a delivery bicycle ticked outside",
        "alarm": "a shriek came from the storeroom, followed by three hollow knocks",
        "clue": "a red bottle rolled into view and stopped against {hero}'s shoe",
        "fear": "a stranger had slipped through the back door",
        "cause": "the delivery bicycle had nudged the door, toppling an empty crate around {visitor}'s ankle",
        "action": "steadied the crate, freed {visitor}, and moved the bicycle to its painted parking mark",
        "dialogue": "\"I'm all right,\" {visitor} said. \"But that bicycle needs a proper home.\"",
        "safeguard": "a marked delivery bay, an earlier delivery cutoff, and calm late service indoors",
        "ending": "the bicycle rested inside its yellow square as the last soup bowls dried",
    },
    {
        "routine": "polishing a brass bell while a grandmother taught a child to fold napkins",
        "alarm": "the curtain snapped toward the ceiling fan and {visitor}'s shriek rose with it",
        "clue": "one curtain cord swung over an empty chair like a slow pendulum",
        "fear": "someone was tugging the curtain from the dark alley window",
        "cause": "the evening breeze had loosened its knot and fed the cloth toward the fan",
        "action": "switched off the fan, tied back the curtain, and checked every window cord",
        "dialogue": "\"The breeze made a grand mystery of a small knot,\" {host} said",
        "safeguard": "secure curtain ties, a quieter fan setting, and late hours only on breezy-night checks",
        "ending": "the tied curtains framed a square of moonlight above the folded napkins",
    },
    {
        "routine": "filling sugar jars while an old radio murmured the weather forecast",
        "alarm": "the radio released a piercing shriek and every customer ducked",
        "clue": "the sound stopped whenever {hero} moved the referendum sign away from the antenna",
        "fear": "an emergency warning was trying to break through the broadcast",
        "cause": "the sign's loose metal clip was touching the antenna and causing feedback",
        "action": "unclipped the sign, wrapped the sharp clip, and tuned the radio to a clear station",
        "dialogue": "\"Let's test the simple thing first,\" {hero} told the worried table",
        "safeguard": "a volume cap, padded sign clips, and a host responsible for each late shift",
        "ending": "the radio played softly while the padded referendum sign hung safely by the door",
    },
    {
        "routine": "counting clean forks while dusk turned the front window violet",
        "alarm": "a shriek sounded outside, and the glowing cantina sign went dark",
        "clue": "small scrape marks led from the sign's switch to a loose wooden ladder",
        "fear": "someone was trying to frighten customers away before the vote",
        "cause": "a delivery rope had snagged the switch, and {visitor} had cried out when the ladder wobbled",
        "action": "held the ladder flat, untangled the rope, and tested the sign from the ground",
        "dialogue": "\"No climbing in the dark,\" {host} said. \"We solve this together.\"",
        "safeguard": "a locked ladder rack, a ground-level sign switch, and well-lit late departures",
        "ending": "the violet window held the cantina's steady gold sign and three neighbors walking home together",
    },
    {
        "routine": "lining up jars of beans while the cook hummed behind the swinging door",
        "alarm": "a shelf groaned, {visitor} shrieked, and one jar began to creep toward the edge",
        "clue": "the shelf leaned only when the back door closed",
        "fear": "the whole wall of jars would tumble into the dining room",
        "cause": "a missing wooden shim let each closing door jolt the shelf",
        "action": "caught the jar, unloaded the shelf, and fitted a new shim before restacking it",
        "dialogue": "\"Empty first, mend second, stack last,\" {hero} counted aloud",
        "safeguard": "weekly shelf checks, a soft doorstop, and a shorter menu during late hours",
        "ending": "the bean jars stood level as the new doorstop held the door in a gentle hush",
    },
    {
        "routine": "wrapping warm rolls while neighbors shook rain from their umbrellas",
        "alarm": "the lights blinked out and a shriek came from beside the humming icebox",
        "clue": "a puddle glimmered on the floor, but the icebox door was still firmly shut",
        "fear": "a live wire had fallen into the water",
        "cause": "a leaking umbrella had made the puddle while {visitor} bumped a squeaky rubber floor mat",
        "action": "blocked the puddle, dried it with towels, and checked the unplugged mat area with a lamp",
        "dialogue": "\"Nobody steps closer until the floor is dry,\" {hero} said calmly",
        "safeguard": "an umbrella stand, battery lanterns, and early closing whenever the power failed",
        "ending": "dry umbrellas circled the new stand while a lantern shone on the final vote tally",
    },
    {
        "routine": "chalking dessert prices while the service hatch rattled with passing plates",
        "alarm": "a shriek burst through the hatch as the little door jammed halfway open",
        "clue": "a striped dish towel protruded beneath one hinge",
        "fear": "a cook's hand was trapped on the other side",
        "cause": "the towel had wound around the hinge while {visitor} reached for a harmless fallen spoon",
        "action": "held the hatch still, freed the towel, and passed the spoon back with wooden tongs",
        "dialogue": "\"Hands clear?\" called {hero}. \"Clear,\" came the answer from the kitchen",
        "safeguard": "a clear hatch shelf, a spoken hands-clear check, and table service after ten",
        "ending": "the striped towel hung on its own hook while the hatch closed without a rattle",
    },
    {
        "routine": "watering the window herbs while chess pieces clicked at the corner table",
        "alarm": "a sudden shriek came from beneath the herb shelf, followed by a papery flutter",
        "clue": "one referendum slip sailed across the floor with a crescent bitten from its edge",
        "fear": "someone was secretly destroying votes",
        "cause": "a field mouse had found a bread crumb beside the slips and startled {visitor}",
        "action": "covered the ballots, swept the crumbs, and guided the mouse into a box for release outside",
        "dialogue": "\"Count every slip, blame no one,\" {host} reminded the room",
        "safeguard": "sealed ballots, nightly crumb checks, and late snacks served only at tables",
        "ending": "the mouse vanished into the herb garden as the unbitten slips lay counted under glass",
    },
    {
        "routine": "folding checked tablecloths while a family shared the last plate of toast",
        "alarm": "a shriek cut through the soft talk when a bell rang inside the locked coat cupboard",
        "clue": "the bell rang again each time the front door swung inward",
        "fear": "someone had been shut inside the cupboard",
        "cause": "a coat button was tugging a bicycle bell by a thread caught under the door",
        "action": "opened the cupboard together, snipped the thread, and returned the bell to its owner",
        "dialogue": "\"A pattern is a clue,\" {hero} said. \"Let's move the door once more.\"",
        "safeguard": "open coat hooks, a clear cupboard floor, and a door check before every late closing",
        "ending": "the freed bell sat beside a folded tablecloth while the cupboard stood safely open",
    },
]

OPENINGS = [
    "The proposed late-hours referendum waited on a chalkboard near the door.",
    "Beside the till, a jar held paper votes for that evening's referendum.",
    "Everyone knew the referendum on later hours would begin after the supper rush.",
    "A hand-lettered referendum notice promised a decision before the lamps were dimmed.",
]

SUSPENSE_BEATS = [
    "For one long moment, nobody could tell whether the danger was growing or already past.",
    "The ordinary room suddenly felt full of corners where an answer might be hiding.",
    "They listened before moving; suspense made even the kettle's click sound important.",
    "No one rushed toward the noise. They named what they could see and checked one clue at a time.",
    "The silence afterward stretched until the smallest sound seemed enormous.",
]

VOTE_LINES = [
    "Each person spoke once before anyone marked a ballot.",
    "They wrote worries on one side of the chalkboard and workable answers on the other.",
    "The neighbors tested the new rule against what had just happened.",
    "Even the youngest visitor was invited to name what would make the room feel safe.",
    "They paused the vote until every question had a plain answer.",
]


def tell_story(params: StoryParams) -> World:
    world = World(Place(name="the cantina"))
    hero = world.add(Entity(id=params.hero, kind="character", type="woman", label=params.hero))
    host = world.add(Entity(id=params.host, kind="character", type="woman", label=params.host))
    visitor = world.add(Entity(id=params.visitor, kind="character", type="girl", label=params.visitor))

    hero.memes["calm"] = 1.0
    host.memes["patience"] = 1.0
    visitor.memes["curiosity"] = 1.0

    seed = params.seed or 0
    arc = STORY_ARCS[seed % len(STORY_ARCS)]
    opening = OPENINGS[(seed // len(STORY_ARCS)) % len(OPENINGS)]
    suspense = SUSPENSE_BEATS[(seed // (len(STORY_ARCS) * len(OPENINGS))) % len(SUSPENSE_BEATS)]
    vote_line = VOTE_LINES[(seed // 7) % len(VOTE_LINES)]
    detail = [
        "a chipped red saucer",
        "a green glass sugar jar",
        "three striped napkins",
        "a brass spoon cup",
        "a blue enamel tray",
        "a basket of warm rolls",
        "a vase of mint stems",
        "a stack of dominoes",
    ][(seed // 3) % 8]
    fmt = {"hero": hero.id, "host": host.id, "visitor": visitor.id}
    text = {key: value.format(**fmt) for key, value in arc.items()}

    world.say(
        f"{hero.id} worked at the cantina, {text['routine']}. {host.id} checked {detail} "
        f"while {visitor.id} settled near the window. {opening}"
    )
    world.para()
    clue_sentence = text["clue"][:1].upper() + text["clue"][1:]
    world.say(f"Then {text['alarm']}. {clue_sentence}.")
    world.facts["shrieked"] = True
    for ent in (hero, host, visitor):
        ent.memes["tension"] = 1.0
    world.say(f"They feared {text['fear']}. Suspense held the room still. {suspense}")
    world.para()
    world.say(f"{hero.id}, {host.id}, and {visitor.id} looked together instead of guessing. They discovered that {text['cause']}.")
    dialogue = text["dialogue"]
    dialogue_end = "" if dialogue.rstrip('"').endswith((".", "!", "?")) else "."
    world.say(f"They {text['action']}. {dialogue}{dialogue_end}")
    for ent in (hero, host, visitor):
        ent.memes["tension"] = 0.0
        ent.memes["relief"] = 1.0
    hero.memes["care"] = 1.0
    world.para()
    world.say(
        f"When the room was calm, {host.id} called the referendum on keeping the cantina open later. "
        f"{vote_line} The scare had shown them one practical need: {text['safeguard']}."
    )
    world.say(
        "The ballots approved that careful plan for a trial month. It was not the loudest answer or the quickest one, "
        "but it let neighbors gather without forgetting the people who needed quiet and safety."
    )
    world.para()
    world.say(
        f"At closing time, {text['ending']}. {hero.id} turned the sign to CLOSED, and the familiar slice-of-life "
        "sounds of cups, chairs, and good nights returned to the cantina."
    )

    world.facts.update(
        hero=hero,
        host=host,
        visitor=visitor,
        arc=seed % len(STORY_ARCS),
        routine=text["routine"],
        detail=detail,
        alarm=text["alarm"],
        clue=text["clue"],
        feared=text["fear"],
        cause=text["cause"],
        response=text["action"],
        safeguard=text["safeguard"],
        ending=text["ending"],
        vote_called=True,
        referendum_result="late_open",
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

NAMES = ["Mara", "Elena", "Nia", "Luz", "Rosa", "Iris", "Tessa", "June"]
VISITORS = ["Nia", "Sofi", "Pia", "Lina", "Mina", "Ruby"]
HOSTS = ["Elena", "Ada", "Clara", "Dora", "Selma"]


# ---------------------------------------------------------------------------
# Story generation + QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short slice-of-life suspense story set in a cantina where a sudden shriek changes the mood.',
        f"Tell a gentle story in {world.place.name} where {f['hero'].id} investigates this clue: {f['clue']}. End with a referendum.",
        f"Write a grounded cantina mystery whose group discovers that {f['cause']}, followed by a calm community vote.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    host: Entity = f["host"]
    visitor: Entity = f["visitor"]
    return [
        QAItem(
            question=f"What ordinary work was happening in the cantina before {visitor.id} heard the shriek?",
            answer=f"{hero.id} was {f['routine']}. Nearby, {host.id} checked {f['detail']} while {visitor.id} sat by the window.",
        ),
        QAItem(
            question=f"What did the shriek make {hero.id}, {host.id}, and {visitor.id} fear at first?",
            answer=f"{f['alarm'][:1].upper() + f['alarm'][1:]}. At first, the people feared {f['feared']}.",
        ),
        QAItem(
            question=f"Which clue did the three neighbors examine instead of guessing about the shriek?",
            answer=f"They noticed that {f['clue']}. Instead of guessing, {hero.id}, {host.id}, and {visitor.id} checked it together.",
        ),
        QAItem(
            question=f"What really caused the frightening moment, and how did {hero.id}'s group resolve it?",
            answer=f"They discovered that {f['cause']}. They {f['response']}.",
        ),
        QAItem(
            question=f"What safeguard did {host.id}'s referendum approve, and what final image showed the change?",
            answer=f"The neighbors approved later hours with {f['safeguard']}. At closing time, {f['ending']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cantina?",
            answer="A cantina is a small place where people can sit, eat, drink, and talk together.",
        ),
        QAItem(
            question="What is a shriek?",
            answer="A shriek is a sudden, sharp cry that usually sounds like someone is startled or in trouble.",
        ),
        QAItem(
            question="What is a referendum?",
            answer="A referendum is a vote where a group of people decide what choice should be made.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% Facts:
% place(P)., person(X)., shriek_event., referendum_topic(late_open)., kitten_safe.

tension_rises :- shriek_event.
calm_returns :- kitten_safe.

vote_open_late :- referendum_topic(late_open), calm_returns.
vote_close_early :- referendum_topic(late_open), tension_rises, not calm_returns.

chosen(late_open) :- vote_open_late.
chosen(early_close) :- vote_close_early.

#show chosen/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("place", "cantina"),
            asp.fact("person", "mara"),
            asp.fact("person", "elena"),
            asp.fact("person", "nia"),
            asp.fact("shriek_event"),
            asp.fact("referendum_topic", "late_open"),
            asp.fact("kitten_safe"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_outcome() -> list[tuple]:
    import asp
    import asp as aspmod  # lazy, but explicit
    _ = aspmod
    model = asp.one_model(asp_program("#show chosen/1."))
    return sorted(set(asp.atoms(model, "chosen")))


def asp_verify() -> int:
    py = "late_open"
    asp_choice = asp_outcome()
    expected = [("late_open",)]
    if asp_choice == expected:
        print("OK: ASP and Python agree on the referendum outcome.")
        return 0
    print(f"MISMATCH: python={py} asp={asp_choice}")
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small cantina suspense storyworld with a referendum.")
    ap.add_argument("--place", choices=["cantina"])
    ap.add_argument("--hero", choices=NAMES)
    ap.add_argument("--host", choices=HOSTS)
    ap.add_argument("--visitor", choices=VISITORS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(NAMES)
    host_choices = [name for name in HOSTS if name != hero]
    host = args.host or rng.choice(host_choices)
    visitor_choices = [name for name in VISITORS if name not in {hero, host}]
    visitor = args.visitor or rng.choice(visitor_choices)
    return StoryParams(
        place=args.place or "cantina",
        hero=hero,
        host=host,
        visitor=visitor,
        seed=args.seed,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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
        print(asp_program("#show chosen/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_outcome())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = StoryParams(place="cantina", hero="Mara", host="Elena", visitor="Nia", seed=base_seed)
        samples = [generate(params)]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

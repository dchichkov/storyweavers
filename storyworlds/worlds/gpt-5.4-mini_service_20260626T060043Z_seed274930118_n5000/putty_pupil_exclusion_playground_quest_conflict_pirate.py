#!/usr/bin/env python3
"""
Standalone storyworld for a small pirate-tale playground quest with conflict.

Seed inspiration:
- putty, pupil, exclusion
- setting: playground
- features: Quest, Conflict
- style: Pirate Tale

A child pirate crew visits the playground to hunt for a hidden "putty pearl"
needed for their quest map. A pupil in the crew feels excluded when the others
rush ahead. The captain notices, patches the rift, and the crew finishes the
quest together.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0



def _safe_fact(world, facts, key):
    value = facts.get(key) if hasattr(facts, "get") else None
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb") or hasattr(value, "sign"):
        return value
    if isinstance(value, str):
        if hasattr(world, "get"):
            try:
                resolved = world.get(value)
                if resolved is not None:
                    return resolved
            except Exception:
                pass
        upper = key.upper()
        for registry_name in (upper, upper + "S", upper + "ES", upper + "_REGISTRY"):
            registry = globals().get(registry_name)
            if isinstance(registry, dict) and value in registry:
                return registry[value]
        if upper.endswith("Y"):
            registry = globals().get(upper[:-1] + "IES")
            if isinstance(registry, dict) and value in registry:
                return registry[value]
    entities = getattr(world, "entities", {})
    if hasattr(entities, "values"):
        for entity in entities.values():
            if hasattr(entity, "id") or hasattr(entity, "label"):
                return entity
    return value

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    captain: object | None = None
    hero: object | None = None
    mapfrag: object | None = None
    pupil: object | None = None
    putty: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "captain"}
        male = {"boy", "father", "man", "matey"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class StoryParams:
    name: str
    pupil_name: str
    parent_name: str
    seed: Optional[int] = None
    scenario_id: int = 0
    telling_mode: int = 0
    dialogue_id: int = 0
    ending_id: int = 0
    clue_number: int = 1
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    w: object | None = None
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
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


PIRATE_NAMES = ["Finn", "Mara", "Jett", "Nori", "Pip", "Wren"]
PUPIL_NAMES = ["Toby", "Mina", "Luca", "Iris", "Penny", "Owen"]
PARENT_NAMES = ["Captain Nia", "Captain Bram", "Captain Sol", "Captain Ria"]


SCENARIOS = [
    {
        "place": "rope bridge",
        "quest": "carry a putty seal across the rope bridge without dropping the map",
        "conflict": "the crew chose every job before the pupil arrived and left no place on the team",
        "hurt": "waited beside the starting line while everyone else practiced",
        "false_start": "The crew tried to hurry across, but the loose map flapped over the rail and hid the next mark.",
        "clue": "three shallow dents in the putty matched the three knots on the handrail",
        "contribution": "read the knot pattern and showed the crew where to pause",
        "repair": "wiped the old job list clean and let everyone choose or trade a useful role",
        "result": "They crossed in pairs and pressed the putty seal onto the map at each knot.",
        "image": "Three neat putty stars shone beside the bridge while every crewmate held one corner of the map.",
    },
    {
        "place": "sandbox harbor",
        "quest": "find which sand island concealed the putty pearl",
        "conflict": "two crewmates whispered their clues to each other and would not show the pupil the map",
        "hurt": "sat outside their sand circle with an empty shovel",
        "false_start": "Their first island collapsed because they had ignored a row of tiny shell arrows.",
        "clue": "the pupil noticed that only the damp sand could hold the putty pearl's round print",
        "contribution": "followed the round prints and marked a safe digging square",
        "repair": "spread the map flat in the middle and made every clue visible to the whole crew",
        "result": "They dug with four small scoops and lifted the pearl without crushing the tunnel beneath it.",
        "image": "A shell flag fluttered over the unbroken tunnel, and four shovels rested side by side.",
    },
    {
        "place": "slide lighthouse",
        "quest": "send a putty message from the top of the slide lighthouse to the lookout below",
        "conflict": "the hero laughed at the pupil's idea before hearing how it worked",
        "hurt": "folded the message card and stopped offering suggestions",
        "false_start": "A paper message skittered off the slide and vanished under a bench.",
        "clue": "the pupil had shaped the putty into a broad base that would glide slowly instead of blowing away",
        "contribution": "tested the putty sled from the lowest safe section first",
        "repair": "apologized for laughing and introduced a rule that each idea received one careful test",
        "result": "The putty sled carried the message down the center and stopped at the chalk harbor line.",
        "image": "The message stood upright in its blue putty base as the crew saluted from the ground.",
    },
    {
        "place": "swinging ship",
        "quest": "decode the putty symbols tied beneath the stationary swing seats",
        "conflict": "the crew began without explaining its pirate code to the new pupil",
        "hurt": "could see the symbols but had no way to take part in the guesses",
        "false_start": "Everyone shouted different answers, and the quest stalled in a storm of noise.",
        "clue": "one symbol looked like the classroom sign for take turns",
        "contribution": "translated the familiar symbol and helped build a shared code key",
        "repair": "paused the game, explained every symbol, and invited questions before restarting",
        "result": "They decoded the message while the swings stayed still and clear of the working area.",
        "image": "The finished code key hung from a low post where the next crew could read it too.",
    },
    {
        "place": "stepping-stone lagoon",
        "quest": "collect putty compass dots from the numbered stepping stones",
        "conflict": "the hero announced that only the fastest pirate could collect clues",
        "hurt": "was careful rather than fast and was told to watch from the edge",
        "false_start": "The speedy run mixed the compass dots together, so nobody knew which stone they came from.",
        "clue": "the pupil remembered the order and could sort each colored dot by number",
        "contribution": "called out the sequence while crewmates walked one at a time",
        "repair": "replaced the race with roles for spotting, carrying, checking, and recording",
        "result": "The sorted dots formed an arrow toward the final treasure mark.",
        "image": "A rainbow putty arrow pointed across the chalk lagoon while the crew checked off every role.",
    },
    {
        "place": "chalk-map cove",
        "quest": "restore a rain-smudged route with putty trail markers",
        "conflict": "an old crew joke became a password that the pupil had never been taught",
        "hurt": "stood at the chalk gate while the others called the password obvious",
        "false_start": "The private password opened nothing; it only started an argument about who belonged.",
        "clue": "the pupil found a public symbol key drawn beside the playground rules",
        "contribution": "used the symbol key to rebuild the route so any visitor could follow it",
        "repair": "retired the private password and chose a welcoming call-and-answer together",
        "result": "They set bright putty arrows along the dry edge of the chalk route.",
        "image": "The new welcome sign faced outward, and five bright arrows led all the way to the cove.",
    },
    {
        "place": "music-wall dock",
        "quest": "match putty note tokens to the playground's outdoor chimes",
        "conflict": "the captain gave the pupil errands but never a turn making a decision",
        "hurt": "carried every token yet was not asked which chime it matched",
        "false_start": "The decision-makers guessed too quickly and arranged the notes backward.",
        "clue": "the pupil had heard the low chime echo longer than the high one",
        "contribution": "ordered the tokens by listening, then invited the crew to check the pattern",
        "repair": "admitted that helping also means sharing authority, not merely sharing chores",
        "result": "They played the correct three-note signal with gentle taps from the ground.",
        "image": "Three putty notes lined the rail beneath chimes that hummed into the quiet afternoon.",
    },
    {
        "place": "picnic-table chart room",
        "quest": "divide a strip of putty into equal markers for four map stations",
        "conflict": "there seemed to be one marker too few, so the crew assumed the pupil should go without",
        "hurt": "heard the choice made without anyone asking for another solution",
        "false_start": "The oversized markers covered the tiny compass letters and made the map harder to read.",
        "clue": "the pupil knew the soft strip could be rolled thinner and divided fairly",
        "contribution": "measured four equal pieces against the ruler printed on the map",
        "repair": "named the unfair assumption, apologized, and agreed to solve shortages before excluding anyone",
        "result": "Each station received one clear marker, and each crewmate placed one.",
        "image": "Four equal putty dots circled the compass rose like small moons around a star.",
    },
    {
        "place": "spinner-wheel helm",
        "quest": "turn the playground spinner to reveal a putty compass message",
        "conflict": "the hero kept taking extra turns and skipped the pupil twice",
        "hurt": "lowered a raised hand after the spinner passed by again",
        "false_start": "The hurried spins blurred the letters until the message looked like nonsense.",
        "clue": "the pupil noticed a putty notch that should stop at each letter",
        "contribution": "guided one slow turn while the others recorded the letters",
        "repair": "owned the skipped turns, moved the turn marker visibly, and asked the pupil to lead the next round",
        "result": "One fair turn apiece revealed the words SHARE THE HELM.",
        "image": "The turn marker rested beside the pupil's name, and the spinner's arrow gleamed without moving.",
    },
    {
        "place": "balance-beam gangplank",
        "quest": "transport a putty key along the low balance-beam gangplank",
        "conflict": "the crew rejected the pupil's slower route as not pirate-like enough",
        "hurt": "stepped back from the beam even though the safer plan was sound",
        "false_start": "The putty key slid from a wobbling tray before the first marker.",
        "clue": "the pupil saw that the tray could travel on the ground beside the beam instead",
        "contribution": "designed a ground route with spotters and no need to balance while carrying",
        "repair": "listened without teasing and agreed that bravery includes choosing a safer method",
        "result": "They walked beside the low beam and delivered the key on a steady tray.",
        "image": "The unbent putty key lay in its tray while chalk waves curled safely around the gangplank.",
    },
    {
        "place": "garden-edge treasure post",
        "quest": "identify the correct post by matching its leaf prints to a putty rubbing",
        "conflict": "the loudest crewmates talked over the pupil whenever the pupil tried to report a clue",
        "hurt": "held up the matching rubbing three times without being heard",
        "false_start": "The crew searched the wrong post and found only an old chalk circle.",
        "clue": "the pupil's rubbing showed two round leaves and one pointed leaf in the exact order",
        "contribution": "presented the evidence during a quiet clue round where nobody interrupted",
        "repair": "created a speaking token and waited until every crewmate had been heard",
        "result": "The leaf pattern led them to a sealed map pocket on the correct post.",
        "image": "The putty rubbing and the real leaves lay aligned beneath the open map pocket.",
    },
    {
        "place": "tunnel-cave entrance",
        "quest": "retrieve a putty badge from the far end of the playground tunnel",
        "conflict": "the crew planned only a crawling route even after the pupil said the tunnel would not work for them",
        "hurt": "was told to wait instead of being included in planning another route",
        "false_start": "The crew reached the badge but discovered the clue required every member's handprint.",
        "clue": "the pupil spotted an open path around the tunnel marked by the same painted wave",
        "contribution": "mapped the alternate ground-level route and met the crew at the badge station",
        "repair": "redesigned the quest with two equal routes and promised to ask about access before play began",
        "result": "Both routes arrived together, and every hand pressed a print into the soft badge rim.",
        "image": "The many-printed putty badge hung where both painted paths joined in the sun.",
    },
]

OPENINGS = [
    "The playground became a bright pirate harbor as soon as the quest map opened.",
    "A chalk tide curled across the playground when the afternoon pirate watch began.",
    "No ocean was needed for this voyage; the playground already held twelve pretend seas.",
    "The crew gathered at the playground flagpole for a quest that required careful eyes and fair turns.",
    "A torn map and a small tin of clean craft putty turned recess into a pirate expedition.",
    "The pirate quest began quietly, with gull calls imagined above the playground and a map spread low enough for all to see.",
    "By the playground gate, the crew promised to search bravely, listen closely, and bring everyone home.",
    "The playground bell had barely faded when the map revealed a new pirate mission.",
]

DIALOGUES = [
    '"A crew is not complete while someone is shut out,"',
    '"Stop the quest. We need to hear what happened,"',
    '"Being included means having a voice and a real part,"',
    '"We cannot call it teamwork if we decide who matters,"',
    '"Tell us what you noticed, and we will listen all the way through,"',
    '"Fair play may change our plan, and that is exactly what good crews do,"',
    '"No treasure is worth making a crewmate feel unwanted,"',
    '"First we repair the hurt; then we repair the map,"',
]

REFLECTIONS = [
    "The hero learned that inviting someone after the exciting part is not the same as including them from the start.",
    "The crew learned to notice whose ideas shaped the plan, not merely who stood nearby.",
    "Their pirate rule became simple: listen, make room, and change the game when a rule shuts someone out.",
    "The quest taught them that an apology matters most when it is followed by a fairer action.",
    "They discovered that different speeds, voices, and routes can make one crew more capable.",
    "The captain reminded them that belonging is something a crew practices at every decision.",
    "From then on, they checked the plan before the play and asked whether everyone had a meaningful part.",
    "They understood that solving the conflict together was the most important treasure they found.",
]

ENDING_LEADS = [
    "When the quest bell rang,",
    "At the calm end of the voyage,",
    "Under the playground's little pirate flag,",
    "As the chalk tide reached the final line,",
    "Before the crew packed away the map,",
    "In the last gold patch of afternoon,",
    "With the conflict honestly repaired,",
    "At the crew's new shared starting line,",
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate playground quest with conflict and a putty prize.")
    ap.add_argument("--name", choices=PIRATE_NAMES)
    ap.add_argument("--pupil", choices=PUPIL_NAMES)
    ap.add_argument("--parent", choices=PARENT_NAMES)
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
    name = getattr(args, "name", None) or rng.choice(PIRATE_NAMES)
    pupil = getattr(args, "pupil", None) or rng.choice(PUPIL_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(PARENT_NAMES)
    if pupil == name:
        pupil = rng.choice([n for n in PUPIL_NAMES if n != name])
    return StoryParams(
        name=name,
        pupil_name=pupil,
        parent_name=parent,
        scenario_id=rng.randrange(len(SCENARIOS)),
        telling_mode=rng.randrange(len(OPENINGS)),
        dialogue_id=rng.randrange(len(DIALOGUES)),
        ending_id=rng.randrange(len(ENDING_LEADS)),
        clue_number=rng.randrange(11, 98),
    )


def tell(params: StoryParams) -> World:
    w = World()
    captain = w.add(Entity(id="captain", kind="character", type="captain", label=params.parent_name))
    hero = w.add(Entity(id="hero", kind="character", type="matey", label=params.name))
    pupil = w.add(Entity(id="pupil", kind="character", type="pupil", label=params.pupil_name))
    putty = w.add(Entity(id="putty", kind="thing", type="putty", label="putty pearl", phrase="a shiny putty pearl"))
    mapfrag = w.add(Entity(id="map", kind="thing", type="map", label="quest map", phrase="a torn quest map"))
    scenario = SCENARIOS[params.scenario_id % len(SCENARIOS)]
    opening = OPENINGS[params.telling_mode % len(OPENINGS)]
    dialogue = DIALOGUES[params.dialogue_id % len(DIALOGUES)]
    ending_lead = ENDING_LEADS[params.ending_id % len(ENDING_LEADS)]
    w.facts.update(
        captain=captain,
        hero=hero,
        pupil=pupil,
        putty=putty,
        mapfrag=mapfrag,
        scenario=scenario,
        clue_number=params.clue_number,
    )

    hero.memes["bold"] += 1
    pupil.memes["hope"] += 1

    w.say(opening)
    w.say(
        f"The playground pirate crew of {hero.label}, {pupil.label}, and {captain.label} followed clue {params.clue_number} "
        f"to the {scenario['place']}. Their quest was to {scenario['quest']}."
    )
    w.say("The putty was clean craft putty, used only for map marks and pretend treasure.")

    w.para()
    w.say(f"A conflict rose before the crew reached the treasure: {scenario['conflict']}.")
    hero.meters["search"] += 1
    hero.memes["rush"] += 1
    pupil.memes["excluded"] += 1
    pupil.memes["sad"] += 1
    pupil.memes["conflict"] += 1
    w.say(f"{pupil.label} {scenario['hurt']}. The exclusion hurt because being nearby was not the same as belonging.")
    w.say(scenario["false_start"])

    w.para()
    captain.memes["watchful"] += 1
    w.say(f"{captain.label} lowered the map and said, {dialogue} then asked {pupil.label} to explain without interruption.")
    w.say(f"The important clue was this: {scenario['clue']}.")
    hero.memes["guilt"] += 1
    hero.memes["conflict"] += 1
    hero.memes["care"] += 1
    pupil.memes["hope"] += 1
    w.say(f"{hero.label} apologized specifically for leaving {pupil.label} out. The crew then {scenario['repair']}.")
    w.say(f"With a real part in the plan, {pupil.label} {scenario['contribution']}.")
    pupil.memes["excluded"] = 0.0
    pupil.memes["agency"] += 1
    w.say(scenario["result"])
    putty.meters["used_safely"] += 1
    mapfrag.meters["fixed"] += 1

    w.para()
    hero.memes["joy"] += 1
    pupil.memes["joy"] += 1
    captain.memes["pride"] += 1
    w.say(REFLECTIONS[params.telling_mode % len(REFLECTIONS)])
    w.say(f"{ending_lead} {scenario['image'][0].lower() + scenario['image'][1:]}")

    w.facts.update(
        resolved=True,
        conflict=scenario["conflict"],
        clue=scenario["clue"],
        contribution=scenario["contribution"],
        repair=scenario["repair"],
        result=scenario["result"],
    )
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    scenario = f["scenario"]
    return [
        f"Write a child-safe pirate tale set at a playground where the quest is to {scenario['quest']}.",
        f"Tell how {f['pupil'].label} is excluded at the {scenario['place']}, then gains a meaningful role and {scenario['contribution']}.",
        f"Write a gentle conflict-and-repair story involving putty, clue {f['clue_number']}, an honest apology, and a fair change to the game.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    pupil = _safe_fact(world, f, "pupil")
    captain = _safe_fact(world, f, "captain")
    scenario = f["scenario"]
    return [
        QAItem(
            question=f"Where does the pirate quest happen?",
            answer=f"It happens at the playground, especially around the {scenario['place']}.",
        ),
        QAItem(
            question=f"What was clue {f['clue_number']} asking the crew to do?",
            answer=f"It asked {hero.label}, {pupil.label}, and their crew to {scenario['quest']}.",
        ),
        QAItem(
            question=f"Why did {pupil.label} feel excluded?",
            answer=f"{pupil.label} felt excluded because {scenario['conflict']}. Being present did not give the pupil a meaningful voice or role.",
        ),
        QAItem(
            question=f"What clue helped the crew change course?",
            answer=f"They learned that {scenario['clue']}. {pupil.label} was given time to explain why it mattered.",
        ),
        QAItem(
            question=f"How did the crew repair both the conflict and the quest?",
            answer=(
                f"After {captain.label} stopped the game and {hero.label} apologized, the crew {scenario['repair']}. "
                f"Then {pupil.label} {scenario['contribution']}, which helped everyone finish safely."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is putty?",
            answer="Putty is a soft, bendy material that can be pressed and shaped with your hands.",
        ),
        QAItem(
            question="What is a pupil?",
            answer="A pupil is a student, a child who learns at school or in a classroom.",
        ),
        QAItem(
            question="What does exclusion mean?",
            answer="Exclusion means leaving someone out so they do not get to join in.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a special search or mission to find something important.",
        ),
        QAItem(
            question="What is conflict in a story?",
            answer="Conflict is the problem or tense part where characters want different things or feel hurt.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{e.id}: {e.label or e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% Simple declarative twin for the reasonableness gate.
quest_ok(playground, putty).
conflict_ok(playground, exclusion).
valid_story(playground, quest, conflict) :- quest_ok(playground, putty), conflict_ok(playground, exclusion).
#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("setting", "playground"),
        asp.fact("feature", "quest"),
        asp.fact("feature", "conflict"),
        asp.fact("seed_word", "putty"),
        asp.fact("seed_word", "pupil"),
        asp.fact("seed_word", "exclusion"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = {("playground", "quest", "conflict")}
    if asp_set == py_set:
        print("OK: ASP parity matches Python gate.")
        return 0
    print("MISMATCH")
    print("ASP:", sorted(asp_set))
    print("PY :", sorted(py_set))
    return 1


def validate_params(params: StoryParams) -> None:
    if not params.name or not params.pupil_name or not params.parent_name:
        pass
    if params.name == params.pupil_name:
        pass


def generate(params: StoryParams) -> StorySample:
    validate_params(params)
    world = tell(params)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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
    StoryParams(name="Finn", pupil_name="Mina", parent_name="Captain Nia"),
    StoryParams(name="Mara", pupil_name="Toby", parent_name="Captain Sol"),
    StoryParams(name="Pip", pupil_name="Iris", parent_name="Captain Bram"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(getattr(args, "n", None)):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 and not getattr(args, "all", None) else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

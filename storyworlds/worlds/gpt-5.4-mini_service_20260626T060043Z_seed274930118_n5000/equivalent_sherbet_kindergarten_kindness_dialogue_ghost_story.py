#!/usr/bin/env python3
"""
A standalone storyworld for a gentle kindergarten ghost story.

Premise:
- In kindergarten, a child notices a friendly ghost near snack time.
- The ghost is misunderstood because it is only trying to find something equivalent to sherbet.
- Kindness and dialogue reveal the ghost's true wish: to help, not haunt.

The world models a small classroom with:
- physical meters: chilly, sticky, full, spilled, glowing
- emotional memes: fear, kindness, curiosity, relief, trust

The story shape is:
beginning -> strange sight and a worried child
middle -> kind conversation and a small problem with snacks
turn -> the ghost explains itself
ending -> a kind equivalent treat and a calm room
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

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


def _fallback_storyparams(args, rng, cls, ns):
    data = {}
    missing = getattr(__import__("dataclasses"), "MISSING")
    for field in __import__("dataclasses").fields(cls):
        name = field.name
        value = None
        for arg_name in (name, name.removesuffix("_name"), name.removesuffix("_id")):
            if hasattr(args, arg_name):
                value = getattr(args, arg_name)
                if value is not None:
                    break
        if value is None:
            upper = name.upper()
            keys = [upper, upper + "S", upper + "ES"]
            if upper.endswith("Y"):
                keys.append(upper[:-1] + "IES")
            for key in keys:
                pool = ns.get(key)
                if isinstance(pool, dict) and pool:
                    value = next(iter(pool.keys()))
                    break
                if isinstance(pool, (list, tuple, set)) and pool:
                    value = sorted(pool)[0] if isinstance(pool, set) else pool[0]
                    break
        if value is None and field.default is not missing:
            value = field.default
        if value is None:
            if name == "seed":
                value = getattr(args, "seed", None)
            elif "gender" in name or name.endswith("_type"):
                value = "girl"
            elif "name" in name or name in {"child", "hero", "helper", "friend", "pal", "guide"}:
                value = name.removesuffix("_name").replace("_", " ").title() or "Mia"
            else:
                value = name
        data[name] = value
    return cls(**data)

@dataclass
class Entity:
    id: str
    kind: str = "thing"   # "child" | "adult" | "ghost" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    props: dict[str, str] = field(default_factory=dict)

    child: object | None = None
    ghost: object | None = None
    helper: object | None = None
    snack: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "ghost":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
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
class Classroom:
    place: str = "kindergarten"
    snack_time: bool = True
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    world: object | None = None
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


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
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


@dataclass
class StoryParams:
    child_name: str
    child_type: str
    helper_name: str
    treat: str
    equivalent_treat: str
    scenario_id: int = 0
    opening_id: int = 0
    dialogue_id: int = 0
    action_id: int = 0
    ending_id: int = 0
    seed: Optional[int] = None
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


CHILD_NAMES = ["Mia", "Noah", "Lily", "Theo", "Ava", "Eli", "Nora", "Finn"]
HELPER_NAMES = ["Mrs. Bell", "Mr. Pine", "Ms. Reed"]
TREAT_PAIRS = [
    ("sherbet", "orange sorbet"),
    ("sherbet", "lemon ice"),
    ("sherbet", "fruit cup"),
    ("sherbet", "snowy yogurt"),
]

SCENARIOS = [
    {
        "problem": "the class freezer had stopped humming, and the sherbet was turning soupy",
        "guess": "the ghost had made the freezer cold enough to break",
        "clue": "a loose plug rested beside a trail of tiny wheel marks",
        "ghost": "I floated over to keep the cups cool until someone could help",
        "action": "followed the wheel marks and found that the art cart had bumped the plug",
        "help": "checked the outlet, plugged the freezer in safely, and set out the equivalent snack",
        "result": "the saved sherbet went back into the humming freezer",
        "image": "frosty stars shone on the freezer door while three clean spoons stood in a row",
        "lesson": "asking a calm question can reveal that a strange sight is really an act of help",
    },
    {
        "problem": "one snack card showed sherbet, but the delivery box held a different snack",
        "guess": "the ghost had switched the snacks as a trick",
        "clue": "the packing slip said the other cups held today's equivalent choice",
        "ghost": "I was pointing at the note because I cannot lift paper",
        "action": "read the pictures on the packing slip and matched them to the box",
        "help": "read the words aloud and confirmed that the equivalent snack was safe for the class",
        "result": "everyone understood the change and shared the equivalent snack",
        "image": "the labeled equivalent snack rested beside the unchanged sherbet card",
        "lesson": "kind dialogue is better than blaming someone before checking the evidence",
    },
    {
        "problem": "a cup of sherbet had tipped, leaving a slippery orange puddle near the rug",
        "guess": "the ghost had spilled it while swooping past",
        "clue": "a round ball print crossed the puddle and ended beneath the block shelf",
        "ghost": "I rang the wind chime to warn everyone not to step there",
        "action": "blocked the puddle with two chairs and found the runaway playground ball",
        "help": "cleaned the floor while the children waited on the dry rug with their equivalent snack",
        "result": "the spill was cleaned and the ghost's warning kept every shoe dry",
        "image": "the clean floor reflected the ghost's small silver wave beside the snack cups",
        "lesson": "kindness includes listening to warnings and making a shared space safe",
    },
    {
        "problem": "the snack bell chimed even though no hand was near it",
        "guess": "the ghost was ringing it to frighten the kindergarten class",
        "clue": "each chime came when sunlight warmed a curling paper ribbon",
        "ghost": "I was trying to show you the ribbon before the bell rang again",
        "action": "watched the ribbon uncurl and moved it away from the bell",
        "help": "praised the careful test and brought the equivalent treat",
        "result": "the bell became quiet, and the class learned what had moved it",
        "image": "the loose ribbon lay flat beside a silent bell and a ring of clean snack spoons",
        "lesson": "curiosity and a fair test can turn a spooky guess into a simple answer",
    },
    {
        "problem": "cold letters appeared on the window above the sherbet tray",
        "guess": "the ghost was writing a scary message",
        "clue": "the letters spelled SHARE and pointed toward one empty place mat",
        "ghost": "I only wanted to ask whether there was an equivalent treat I could share",
        "action": "sounded out the letters and placed a welcoming paper star at the empty seat",
        "help": "served the equivalent treat and helped everyone read the message together",
        "result": "the frosty word became an invitation instead of a warning",
        "image": "the word SHARE faded into five clear finger-sized patches around a paper star",
        "lesson": "patient reading and kind words help everyone feel included",
    },
    {
        "problem": "a soft boo came from the cubbies whenever someone mentioned sherbet",
        "guess": "the ghost wanted the children to run away",
        "clue": "the sound stopped whenever the class paused long enough to listen",
        "ghost": "I was saying blue, because the blue cup marks my equivalent snack",
        "action": "asked the ghost to repeat slowly and found the blue-lidded equivalent snack",
        "help": "showed the class how one careful question could clear up a mixed-up word",
        "result": "boo became blue, and the misunderstanding made everyone giggle gently",
        "image": "a blue lid sat beside the sherbet cups while the ghost drew a smiling loop in the air",
        "lesson": "listening twice can keep a small misunderstanding from becoming a big fear",
    },
    {
        "problem": "the picture labels had floated away from the kindergarten snack shelf",
        "guess": "the ghost was hiding which cup held sherbet",
        "clue": "the labels all drifted toward a draft under the classroom door",
        "ghost": "I caught the last label so it would not slide into the hallway",
        "action": "closed the door, gathered the labels, and sorted them by their pictures",
        "help": "taped the labels back and marked the alternate snack as an equivalent choice",
        "result": "every snack had the right label and the ghost returned the one it had rescued",
        "image": "four straight picture cards rested above four cups as the door ribbon became still",
        "lesson": "notice what happened before deciding who caused a problem",
    },
    {
        "problem": "the class puppet kept pointing away from the sherbet and toward an empty bowl",
        "guess": "the ghost was making the puppet snatch snack time",
        "clue": "a silver thread joined the puppet's mitten to the ghost's little bell",
        "ghost": "I tied the thread because I needed a way to point to a bowl for an equivalent treat",
        "action": "untangled the thread and asked which snack picture belonged by the bowl",
        "help": "added a picture of the equivalent snack and showed the ghost how to tap the bell once for help",
        "result": "the puppet bowed, the empty bowl was filled, and no snack was taken",
        "image": "the puppet and ghost faced each other over a small filled snack bowl",
        "lesson": "a helpful signal works best when friends agree on what it means",
    },
    {
        "problem": "tiny wet rings appeared from the snack table to the reading corner",
        "guess": "the ghost was carrying sherbet away one spoonful at a time",
        "clue": "the rings were exactly the size of the watering can's base",
        "ghost": "I followed the drops because the can was leaking near the books",
        "action": "traced the rings, moved the books, and placed the can in a wide tray",
        "help": "dried the floor and offered the equivalent snack while the can was repaired",
        "result": "the books stayed dry and the ghost was thanked for following the leak",
        "image": "dry books stood like a bright fence behind a tray holding one quiet drop",
        "lesson": "following clues kindly can uncover help where blame first seemed easier",
    },
    {
        "problem": "the lights blinked whenever the sherbet cart rolled past the pretend kitchen",
        "guess": "the ghost was flashing the lights for a spooky game",
        "clue": "one cart wheel pressed a floor switch each time it passed",
        "ghost": "I stood by the switch so you would notice the little click",
        "action": "rolled the cart slowly, heard the click, and marked a path around the switch",
        "help": "secured the switch cover and set the equivalent snack on a steady table",
        "result": "the lights stayed bright and the cart reached snack time without another blink",
        "image": "a yellow path curved around the covered switch beneath a warmly glowing lamp",
        "lesson": "brave investigation means moving slowly, noticing clues, and asking for help",
    },
    {
        "problem": "one place at the snack table stayed chilly while the sherbet cups grew warm",
        "guess": "the ghost was saving the cold only for itself",
        "clue": "the chilly patch surrounded a cup the ghost was shielding with both wispy arms",
        "ghost": "This equivalent treat belongs to a late friend, and I promised to keep it cool",
        "action": "made a name card for the late friend and thanked the ghost for guarding the cup",
        "help": "moved all the snacks to a cool tray and saved an equal place for everyone",
        "result": "the late friend arrived to find sherbet, an equivalent treat, and a waiting seat",
        "image": "one new name card stood among the cups while the ghost glowed like a tiny night-light",
        "lesson": "fair sharing may mean saving a place for someone who has not arrived yet",
    },
    {
        "problem": "a paper snowflake vanished each time the class named an equivalent to sherbet",
        "guess": "the ghost was gobbling the decorations",
        "clue": "all the snowflakes reappeared in a neat trail leading to the warm radiator",
        "ghost": "I moved them because the tape was loosening, and I did not want them to fall on the heater",
        "action": "counted the snowflakes, carried them to a cool wall, and chose stronger paper tabs",
        "help": "checked the new display and served the equivalent snack beside the sherbet",
        "result": "every snowflake was safe, and the ghost's quiet work finally made sense",
        "image": "twelve paper snowflakes circled a snack picture on the cool blue wall",
        "lesson": "before calling an action unkind, ask what problem the helper was trying to solve",
    },
]

OPENINGS = [
    "At snack time in kindergarten, {child} noticed that {problem}.",
    "The strangest part of kindergarten began with a small problem: {problem}.",
    '"Something is different," {child} said at the kindergarten snack table, where {problem}.',
    "Before the class could taste its sherbet, {child} discovered that {problem}.",
    "Kindergarten had been cheerful and ordinary until {problem}.",
    "Near the kindergarten snack table, a mystery waited for {child}: {problem}.",
    "A soft chime interrupted kindergarten snack time. {child} looked up and saw that {problem}.",
    "While classmates prepared for sherbet, {child} stopped to study a puzzling sight: {problem}.",
]

DIALOGUE_LEADS = [
    '"Let us ask before we guess," {helper} said.',
    '"A kind question can help," {helper} reminded the class.',
    '"We can be careful and friendly at the same time," {helper} said.',
    '"First we look, then we listen," {helper} said calmly.',
    '"No one has to solve a mystery alone," {helper} told {child}.',
    '"Tell us what you noticed," {helper} invited the ghost.',
    '"Let us use quiet voices and curious eyes," {helper} said.',
    '"Kindness begins by giving someone a turn to speak," {helper} said.',
]

ACTION_LEADS = [
    "With the ghost beside them, {child} {action}.",
    "Instead of running away, {child} {action}.",
    "The clue gave {child} a plan. They {action}.",
    '"I will check," {child} said, and then {action}.',
    "Working one careful step at a time, {child} {action}.",
    "Kindness made room for curiosity, so {child} {action}.",
    "After repeating the clue aloud, {child} {action}.",
    "The class watched while {child} {action}.",
]

ENDING_LEADS = [
    "By home time, {result}. The last thing {child} saw was this: {image}.",
    "Soon, {result}. As the class waved goodbye, {image}.",
    "That solved the mystery: {result}. In the calm room, {image}.",
    "After their kind conversation, {result}. At the doorway, {child} looked back and saw that {image}.",
    "The class cheered softly because {result}. Their final picture of the day was simple: {image}.",
    "So {result}. When the room grew quiet, {image}.",
    "The careful plan worked, and {result}. Just before pickup, {image}.",
    "At last, {result}. The kindergarten room felt peaceful while {image}.",
]


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def tell(params: StoryParams) -> Classroom:
    world = Classroom()
    child = world.add(Entity(
        id=params.child_name, kind="child", type=params.child_type, label=params.child_name,
        meters={"curiosity": 1.0}, memes={"fear": 0.0, "kindness": 0.0, "relief": 0.0, "trust": 0.0},
    ))
    helper = world.add(Entity(
        id=params.helper_name, kind="adult", type="teacher", label=params.helper_name,
        meters={}, memes={"kindness": 1.0},
    ))
    ghost = world.add(Entity(
        id="ghost", kind="ghost", type="ghost", label="the ghost",
        phrase="a soft white ghost with round eyes",
        meters={"chilly": 1.0, "glowing": 1.0},
        memes={"loneliness": 1.0, "kindness": 0.5, "hope": 1.0},
        props={"wants": params.treat, "equivalent": params.equivalent_treat},
    ))
    snack = world.add(Entity(
        id="snack", type="snack", label=params.treat, phrase=f"a cup of {params.treat}",
        meters={"sticky": 0.0, "full": 0.0, "spilled": 0.0},
        memes={"familiarity": 1.0},
        owner=child.id,
    ))
    scene = SCENARIOS[params.scenario_id % len(SCENARIOS)]
    world.facts.update(child=child, helper=helper, ghost=ghost, snack=snack)
    world.facts["equivalent"] = params.equivalent_treat
    world.facts.update(
        problem=scene["problem"], guess=scene["guess"], clue=scene["clue"],
        ghost_words=scene["ghost"], action=scene["action"], help=scene["help"],
        result=scene["result"],
        ending_image=scene["image"], lesson=scene["lesson"],
        scenario_id=params.scenario_id, dialogue=True,
    )

    world.say(OPENINGS[params.opening_id % len(OPENINGS)].format(
        child=child.id, problem=scene["problem"],
    ))
    world.say(f"Nearby in the kindergarten room stood {ghost.phrase}. {child.id} wondered whether {scene['guess']}.")
    child.memes["fear"] += 1.0
    world.para()
    world.say(DIALOGUE_LEADS[params.dialogue_id % len(DIALOGUE_LEADS)].format(
        helper=helper.id, child=child.id,
    ))
    child.memes["curiosity"] += 1.0
    world.say(f'"Were you trying to cause this?" {child.id} asked the ghost.')
    world.say(f'The ghost shook its head. "{scene["ghost"]}," it explained. "I hoped for something equivalent to {params.treat}, not a scare."')
    world.say(f'"Equivalent means a choice that works in the same place," {helper.id} explained. "Today, {params.equivalent_treat} can fill that role."')
    world.para()
    world.say(f"Then {child.id} noticed the important clue: {scene['clue']}.")
    child.memes["kindness"] += 1.0
    world.say(ACTION_LEADS[params.action_id % len(ACTION_LEADS)].format(
        child=child.id, action=scene["action"],
    ))
    world.say(f"{helper.id} {scene['help']}.")
    world.say(f'"Thank you for telling us," {child.id} said. "You may share our {params.equivalent_treat}."')
    snack.meters["full"] += 1.0
    ghost.props["shared_treat"] = params.equivalent_treat
    world.para()
    child.memes["fear"] = 0.0
    child.memes["relief"] += 1.0
    child.memes["trust"] += 1.0
    ghost.memes["loneliness"] = 0.0
    ghost.memes["kindness"] += 1.0
    world.say(ENDING_LEADS[params.ending_id % len(ENDING_LEADS)].format(
        child=child.id, result=scene["result"], image=scene["image"],
    ))
    world.say(f"{child.id} learned that {scene['lesson']}.")
    world.say(f"The friendly ghost shared {params.equivalent_treat}, and the sherbet stayed ready for the children who chose it.")
    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Content registries and reasoning
# ---------------------------------------------------------------------------
def valid_combo(params: StoryParams) -> bool:
    return bool(params.child_name and params.helper_name and params.treat and params.equivalent_treat)


ASP_RULES = r"""
ghost_needs_equivalent(ghost, Treat) :- wants(ghost, Treat).
kind_answer(Child) :- says_kind(Child).
resolved :- kind_answer(Child), equivalent_treat(Treat, Equiv).
#show ghost_needs_equivalent/2.
#show kind_answer/1.
#show resolved/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("wants", "ghost", "sherbet"),
        asp.fact("equivalent_treat", "sherbet", "orange_sorbet"),
        asp.fact("says_kind", "child"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program(""))
    atoms = {str(a) for a in model}
    if any("ghost_needs_equivalent" in a for a in atoms):
        print("OK: ASP twin built a reasonable ghost need.")
        return 0
    print("MISMATCH: ASP twin did not produce the expected model.")
    return 1


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: Classroom) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child").id
    treat = _safe_fact(world, f, "snack").label
    equiv = f["equivalent"]
    problem = f["problem"]
    return [
        f'Write a gentle kindergarten ghost story using "{treat}" and "{equiv}" as equivalent snack choices. Begin with this problem: {problem}.',
        f"Tell a child-friendly story where {child} first misunderstands a ghost, then uses clues, dialogue, and kindness to solve the classroom problem.",
        f"Write a complete ghost story with a clear mystery, a kind conversation, a causal solution, and a concrete final image in kindergarten.",
    ]


def story_qa(world: Classroom) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    helper = _safe_fact(world, f, "helper")
    snack = _safe_fact(world, f, "snack")
    ghost = _safe_fact(world, f, "ghost")
    return [
        QAItem(
            question=f"What made {child.id} suspect the ghost at first?",
            answer=f"{child.id} suspected {ghost.label} because {f['problem']}. At first, {child.id} wondered whether {f['guess']}.",
        ),
        QAItem(
            question=f"What clue helped {child.id} understand the classroom mystery?",
            answer=f"The useful clue was that {f['clue']}. That evidence helped {child.id} replace a frightened guess with a fair explanation.",
        ),
        QAItem(
            question=f"How did {child.id} and {helper.id} solve the problem?",
            answer=f"{child.id} {f['action']}. Then {helper.id} {f['help']}.",
        ),
        QAItem(
            question="What happened after everyone used kind dialogue?",
            answer=f"After they listened and worked together, {f['result']}. The ghost could share {f['equivalent']}, an equivalent choice for the {snack.label} snack.",
        ),
        QAItem(
            question=f"What lesson did {child.id} learn?",
            answer=f"{child.id} learned that {f['lesson']}. The ending proves it with this calm picture: {f['ending_image']}.",
        ),
    ]


def world_knowledge_qa(world: Classroom) -> list[QAItem]:
    return [
        QAItem(
            question="What is kindergarten?",
            answer="Kindergarten is a place where young children learn, play, sing, and share with help from grown-ups.",
        ),
        QAItem(
            question="What does equivalent mean?",
            answer="Equivalent means something has the same value or is just as good in a matching way.",
        ),
        QAItem(
            question="What is sherbet?",
            answer="Sherbet is a sweet frozen treat that is cool, fruity, and soft enough to eat with a spoon.",
        ),
        QAItem(
            question="Why is kindness important?",
            answer="Kindness helps people feel safe, understood, and ready to talk instead of being afraid.",
        ),
    ]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle kindergarten ghost story world.")
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--treat", choices=["sherbet"])
    ap.add_argument("--equivalent", help="an equivalent snack, like orange sorbet")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    treat = getattr(args, "treat", None) or "sherbet"
    equivalent = getattr(args, "equivalent", None) or rng.choice([e for _, e in TREAT_PAIRS])
    if treat != "sherbet":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if equivalent == treat:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(
        child_name=getattr(args, "name", None) or rng.choice(CHILD_NAMES),
        child_type="girl" if rng.random() < 0.5 else "boy",
        helper_name=getattr(args, "helper", None) or rng.choice(HELPER_NAMES),
        treat=treat,
        equivalent_treat=equivalent,
        scenario_id=rng.randrange(len(SCENARIOS)),
        opening_id=rng.randrange(len(OPENINGS)),
        dialogue_id=rng.randrange(len(DIALOGUE_LEADS)),
        action_id=rng.randrange(len(ACTION_LEADS)),
        ending_id=rng.randrange(len(ENDING_LEADS)),
        seed=getattr(args, "seed", None),
    )


def generate(params: StoryParams) -> StorySample:
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


def dump_trace(world: Classroom) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.props:
            bits.append(f"props={e.props}")
        lines.append(f"  {e.id:10} ({e.kind:6}) {' '.join(bits)}")
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

    if getattr(args, "show_asp", None):
        print(asp_program("#show resolved/0."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("ASP mode is intentionally tiny in this world; run --verify to check parity.")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        params_list = [
            StoryParams(child_name="Mia", child_type="girl", helper_name="Mrs. Bell", treat="sherbet", equivalent_treat="orange sorbet", scenario_id=0, opening_id=0, dialogue_id=0, action_id=0, ending_id=0),
            StoryParams(child_name="Noah", child_type="boy", helper_name="Mr. Pine", treat="sherbet", equivalent_treat="lemon ice", scenario_id=5, opening_id=2, dialogue_id=3, action_id=4, ending_id=3),
            StoryParams(child_name="Lily", child_type="girl", helper_name="Ms. Reed", treat="sherbet", equivalent_treat="fruit cup", scenario_id=10, opening_id=6, dialogue_id=7, action_id=6, ending_id=7),
        ]
        samples = [generate(p) for p in params_list]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError:
                continue
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.child_name}: sherbet and equivalent {p.equivalent_treat}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

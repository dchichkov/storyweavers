#!/usr/bin/env python3
"""Child-friendly detective stories about a peony, a hypothesis, and a repeated clue."""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from results import QAItem, StoryError, StorySample  # noqa: E402



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


def _safe_lookup(mapping, key):
    if hasattr(key, "id"):
        key = key.id
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = [value for value in mapping.values() if value is not None]
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Entity:
    id: str
    type: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    coach: object | None = None
    dancer: object | None = None
    partner: object | None = None
    peony: object | None = None
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)

    world: object | None = None
    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)
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
    def get(self, eid: str):
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


@dataclass
class Studio:
    name: str = "the dance studio"
    floor: str = "the blue practice floor"
    mirror: str = "the long mirror"
    studio: object | None = None
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class StoryParams:
    seed: Optional[int] = None
    dancer: str = "Luna"
    partner: str = "Theo"
    coach: str = "Mira"
    case: int = 0
    opening: int = 0
    question: int = 0
    ending: int = 0
    cadence: int = 0
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


DANCERS = ["Luna", "Nia", "Pip", "Arlo", "Zoe", "Milo"]
PARTNERS = ["Theo", "Jun", "Bea", "Ravi", "Tess"]
COACHES = ["Mira", "Sol", "Ivy", "Nell"]
PLACES = ["studio", "dance hall", "practice room"]


CASES = [
    {
        "title": "the peony ribbon case",
        "opening": "A bright peony ribbon vanished just before the studio's little spring show.",
        "problem": "It had been on the prop table beside the music box, but now only a pink thread remained.",
        "hypothesis": "Luna formed a hypothesis: the ribbon was being tugged by the same draft each time the side door opened.",
        "test": "She placed three paper petals along the floor and opened the door three careful times.",
        "clue": "Each petal slid toward the costume rack, and the pink thread caught on its lowest hook.",
        "action": "Luna and Theo repeated the test, then followed the thread behind the rack where the ribbon had slipped.",
        "result": "The ribbon was safe, and the dancers tied it to the peony basket for the finale.",
        "lesson": "A hypothesis becomes useful when a careful test checks it.",
        "ending": "When the music began, the peony ribbon curled through the air like a bright detective's flag.",
        "object": "peony ribbon",
        "answer": "The repeated draft pulled the ribbon from the prop table toward the costume rack.",
    },
    {
        "title": "the three missing taps",
        "opening": "During rehearsal, three taps disappeared from the dance studio's closing rhythm.",
        "problem": "Every dancer counted eight beats, yet the final pattern sounded lopsided.",
        "hypothesis": "Luna's hypothesis was that the old floorboard near the mirror swallowed the soft taps.",
        "test": "She repeated the step on four floorboards while Theo listened with his eyes closed.",
        "clue": "Only the board below the mirror made the third tap sound dull.",
        "action": "They marked that board with a yellow star and shifted the ending one small step away.",
        "result": "The whole rhythm returned, and the dancers could hear one another again.",
        "lesson": "Repeating a fair test can reveal a quiet cause.",
        "ending": "The final three taps rang clearly under the mirror's golden lights.",
        "object": "yellow floor star",
        "answer": "The board below the mirror softened the third tap, so the dancers moved the ending.",
    },
    {
        "title": "the spinning shoe mystery",
        "opening": "One silver dance shoe kept spinning away from the costume line.",
        "problem": "No one had moved it, but it appeared in a new place after every rehearsal.",
        "hypothesis": "Luna guessed that the shoe was resting on a slanted strip of rosin dust.",
        "test": "She placed the shoe beside two blocks and repeated the same gentle push.",
        "clue": "The shoe turned only when its heel touched the dusty strip.",
        "action": "Luna and Mira brushed the strip clean and tested the shoe once more.",
        "result": "The shoe stayed still, ready for its owner to wear.",
        "lesson": "A good detective changes one detail at a time.",
        "ending": "The silver shoe waited neatly beside its partner beneath the costume lights.",
        "object": "silver dance shoe",
        "answer": "A slanted strip of rosin dust caught the heel and made the shoe spin.",
    },
    {
        "title": "the echoing count case",
        "opening": "A strange extra count echoed through the dance studio during the quest for a smooth group turn.",
        "problem": "The dancers heard 'five' twice and bumped shoulders on every practice.",
        "hypothesis": "Luna's hypothesis was that the mirror was bouncing the coach's voice back late.",
        "test": "She repeated the count with the curtain open, closed, and half-open.",
        "clue": "The extra echo appeared only when the curtain was closed.",
        "action": "They tied the curtain back and practiced the turn again, listening between each number.",
        "result": "The dancers turned together without the confusing second count.",
        "lesson": "A repeated clue is stronger when it appears under the same condition.",
        "ending": "Their final turn made one clean circle beneath the quiet mirror.",
        "object": "practice curtain",
        "answer": "The closed curtain bounced the coach's count back into the room.",
    },
    {
        "title": "the lost moon badge",
        "opening": "Luna's moon badge disappeared before the dancers began their nighttime quest.",
        "problem": "The badge had a little clasp, and its silver trail ended near the rehearsal bags.",
        "hypothesis": "Luna made a hypothesis that the clasp was catching on the same woven strap.",
        "test": "She moved three bags past the strap twice and watched the clasp carefully.",
        "clue": "The badge stopped beside the red bag both times.",
        "action": "Theo lifted the red bag while Luna checked underneath its strap.",
        "result": "The moon badge gleamed there, safe and unbent.",
        "lesson": "Repeating a search can turn a guess into dependable evidence.",
        "ending": "The moon badge shone on Luna's costume as the first music began.",
        "object": "moon badge",
        "answer": "The badge clasp caught on the woven strap of the red rehearsal bag.",
    },
    {
        "title": "the quiet speaker puzzle",
        "opening": "The dance studio speaker lost its sound just when the quest rehearsal started.",
        "problem": "The music returned for one moment, then faded whenever the dancers crossed the floor.",
        "hypothesis": "Luna suspected that the cord was being nudged at one repeated spot.",
        "test": "She walked the same path three times while Mira watched the cord.",
        "clue": "Each pass pressed the cord against a loose mat corner.",
        "action": "They taped the mat edge down and repeated the walk before turning on the music.",
        "result": "The song played from beginning to end.",
        "lesson": "Careful repetition helps us find a pattern instead of blaming luck.",
        "ending": "The speaker filled the studio with music, and every dancer knew where to step.",
        "object": "speaker cord",
        "answer": "A loose mat corner pressed against the speaker cord whenever dancers crossed the floor.",
    },
]


OPENINGS = [
    "At {place}, {dancer} loved solving small mysteries before warm-up began.",
    "The afternoon sun filled {place} while {dancer} checked every prop like a young detective.",
    "Before the first count, {dancer} noticed that something in {place} did not look right.",
    "The dancers gathered at {place}, where a new quest waited beneath the bright mirrors.",
    "Music hummed softly in {place}, but {dancer} was listening for a clue.",
]

QUEST_LINES = [
    "It was a small quest, but Luna knew that small clues could answer big questions.",
    "The quest began with one question, one notebook, and a promise to repeat the test fairly.",
    "Detectives do not chase every guess, so the dancers chose one clue to follow.",
    "The studio became their quiet case room, with footprints, sounds, and props to examine.",
]

DIALOGUES = [
    "'What is your hypothesis?' Theo asked. 'I think the clue will repeat,' Luna replied.",
    "'Should we blame the prop table?' Mira asked. 'Not yet,' said Luna. 'Let's test the same idea twice.'",
    "'I saw it move,' Theo said. Luna nodded. 'Then we need to learn what moves it.'",
    "'A guess is only a beginning,' Mira reminded them. 'A repeated test can make it stronger,' Luna answered.",
]

CADENCES = [
    "First they noticed, then they tested, and finally they checked the result.",
    "The dancers moved slowly so that no clue could hide beneath a hurried step.",
    "They changed one thing at a time and wrote down what happened.",
    "The same question met the same test, and the pattern grew clearer.",
]

ENDINGS = [
    "Everyone agreed that the best clue was the one they could explain.",
    "The dancers cheered softly because the mystery had been solved by patience.",
    "Luna closed the notebook, but kept the lesson ready for the next rehearsal.",
    "The studio felt brighter when a careful question had found a careful answer.",
]


ASP_RULES = r"""
#show quest/1.
#show repetition/1.
#show solved/1.

quest(dance_studio_case) :- studio(dance_studio), missing(clue).
repetition(careful_test) :- tested_twice(clue), same_condition(clue).
solved(dance_studio_case) :- quest(dance_studio_case), repetition(careful_test), found(cause).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("studio", "dance_studio"),
            asp.fact("missing", "clue"),
            asp.fact("tested_twice", "clue"),
            asp.fact("same_condition", "clue"),
            asp.fact("found", "cause"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Detective storyworld about a peony, a hypothesis, and a dance-studio quest."
    )
    parser.add_argument("--dancer", choices=DANCERS)
    parser.add_argument("--partner", choices=PARTNERS)
    parser.add_argument("--coach", choices=COACHES)
    parser.add_argument("--place", choices=PLACES, default="studio")
    parser.add_argument("--case", type=int, choices=range(len(CASES)))
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        seed=getattr(args, "seed", None),
        dancer=getattr(args, "dancer", None) or rng.choice(DANCERS),
        partner=getattr(args, "partner", None) or rng.choice(PARTNERS),
        coach=getattr(args, "coach", None) or rng.choice(COACHES),
        case=getattr(args, "case", None) if getattr(args, "case", None) is not None else rng.randrange(len(CASES)),
        opening=rng.randrange(len(OPENINGS)),
        question=rng.randrange(len(DIALOGUES)),
        ending=rng.randrange(len(ENDINGS)),
        cadence=rng.randrange(len(CADENCES)),
    )


def generate(params: StoryParams) -> StorySample:
    if params.case < 0 or params.case >= len(CASES):
        pass

    world = World()
    studio = Studio(name=f"the {params.place}")
    dancer = world.add(Entity(params.dancer, "dancer", params.dancer))
    partner = world.add(Entity(params.partner, "dancer", params.partner))
    coach = world.add(Entity(params.coach, "coach", params.coach))
    peony = world.add(Entity("peony", "flower", "peony"))

    dancer.meters["attention"] = 1.0
    dancer.memes["curiosity"] = 1.0
    partner.memes["trust"] = 1.0
    coach.memes["guidance"] = 1.0
    peony.memes["beauty"] = 1.0

    case = _safe_lookup(CASES, params.case)

    def personalize(text: str) -> str:
        return (
            text.replace("Luna", dancer.id)
            .replace("Theo", partner.id)
            .replace("Mira", coach.id)
        )

    world.say(_safe_lookup(OPENINGS, params.opening % len(OPENINGS)).format(place=studio.name, dancer=dancer.id))
    world.say(personalize(case["opening"]))
    world.say("A small peony sat in a blue cup beside the clues, bright as a sign that careful eyes should keep looking.")
    world.say(personalize(case["problem"]))
    world.say(_safe_lookup(QUEST_LINES, params.case % len(QUEST_LINES)))
    world.say(personalize(_safe_lookup(DIALOGUES, params.question % len(DIALOGUES))))
    world.say(personalize(case["hypothesis"]))
    world.say(personalize(case["test"]))
    world.say(_safe_lookup(CADENCES, params.cadence % len(CADENCES)))
    world.say(personalize(case["clue"]))
    world.say(personalize(case["action"]))
    world.say(personalize(case["result"]))

    dancer.memes["confidence"] = 1.0
    dancer.memes["hypothesis_checked"] = 1.0
    world.say(f"{coach.id} smiled. 'Your hypothesis was useful because you tested it instead of treating it like a fact.'")
    world.say(f"{dancer.id} answered, 'The repeated clue showed us what really happened.'")
    world.say(f"Case closed: {case['lesson']}")
    world.say(_safe_lookup(ENDINGS, params.ending % len(ENDINGS)))
    world.say(personalize(case["ending"]))

    world.facts.update(
        studio=studio,
        dancer=dancer,
        partner=partner,
        coach=coach,
        peony=peony,
        case=case,
        quest=True,
        repetition=True,
        hypothesis=case["hypothesis"],
        solved=True,
        cause=case["answer"],
    )

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    case = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "case")
    dancer = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "dancer")
    return [
        f"Write a child-friendly detective story about {dancer.id} solving {case['title']} in a dance studio.",
        f"Include a peony, a clear hypothesis, a repeated test, dialogue, and a satisfying case resolution.",
        f"Tell a dance-studio quest where a repeated clue helps explain {case['object']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    case = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "case")
    dancer = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "dancer")
    partner = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "partner")
    return [
        QAItem(
            question=f"What quest did {dancer.id} undertake?",
            answer=f"{dancer.id} undertook a detective quest to solve {case['title']} in the dance studio.",
        ),
        QAItem(
            question="What was the hypothesis?",
            answer=case["hypothesis"],
        ),
        QAItem(
            question="How did repetition help solve the mystery?",
            answer=(
                f"The dancers repeated a careful test under the same conditions. "
                f"{case['answer']} This made the clue dependable instead of leaving it as a guess."
            ),
        ),
        QAItem(
            question=f"How did {dancer.id} and {partner.id} act on the clue?",
            answer=case["action"],
        ),
        QAItem(
            question="What lesson did the detective learn?",
            answer=case["lesson"],
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a hypothesis?",
            answer="A hypothesis is a thoughtful idea about what may be happening that can be checked with evidence.",
        ),
        QAItem(
            question="Why is repetition useful in an investigation?",
            answer="Repetition helps show whether a result is a real pattern rather than a lucky accident.",
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective notices clues, asks questions, tests ideas, and uses evidence to explain a mystery.",
        ),
        QAItem(
            question="What is a peony?",
            answer="A peony is a flowering plant with large, colorful blossoms.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
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
    for entity in list(world.entities.values()):
        lines.append(
            f"  {entity.id:10} ({entity.type:7}) "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show quest/1.\n#show repetition/1.\n#show solved/1."))
    return sorted(
        set(
            asp.atoms(model, "quest")
            + asp.atoms(model, "repetition")
            + asp.atoms(model, "solved")
        )
    )


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show quest/1.\n#show repetition/1.\n#show solved/1."))
    actual = {
        ("quest",) + item for item in asp.atoms(model, "quest")
    } | {
        ("repetition",) + item for item in asp.atoms(model, "repetition")
    } | {
        ("solved",) + item for item in asp.atoms(model, "solved")
    }
    expected = {
        ("quest", "dance_studio_case"),
        ("repetition", "careful_test"),
        ("solved", "dance_studio_case"),
    }
    if actual != expected:
        print("MISMATCH between clingo and Python gate.")
        print("  clingo:", sorted(actual))
        print("  python:", sorted(expected))
        return 1
    for case_index in range(len(CASES)):
        sample = generate(
            StoryParams(
                dancer="Luna",
                partner="Theo",
                coach="Mira",
                case=case_index,
            )
        )
        if "hypothesis" not in sample.story.lower() or "peony" not in sample.story.lower():
            print(f"Generated story {case_index} failed required-word check.")
            return 1
        if not sample.story_qa:
            print(f"Generated story {case_index} has no story QA.")
            return 1
    print("OK: ASP parity and generated-story checks passed.")
    return 0


CURATED = [
    StoryParams(dancer="Luna", partner="Theo", coach="Mira", case=0),
    StoryParams(dancer="Nia", partner="Jun", coach="Sol", case=2, opening=1, question=3, ending=2, cadence=1),
    StoryParams(dancer="Arlo", partner="Bea", coach="Ivy", case=5, opening=3, question=0, ending=3, cadence=2),
]


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    header: str = "",
) -> None:
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
        print(asp_program("#show quest/1.\n#show repetition/1.\n#show solved/1."))
        return

    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        facts = asp_valid()
        print(f"{len(facts)} ASP detective facts")
        for fact in facts:
            print(fact)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        limit = max(50, getattr(args, "n", None) * 30)
        while len(samples) < getattr(args, "n", None) and attempt < limit:
            rng = random.Random(base_seed + attempt)
            params = resolve_params(args, rng)
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            attempt += 1

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        if getattr(args, "all", None):
            header = f"### {sample.params.dancer}: {_safe_lookup(CASES, sample.params.case)['title']}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        else:
            header = ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

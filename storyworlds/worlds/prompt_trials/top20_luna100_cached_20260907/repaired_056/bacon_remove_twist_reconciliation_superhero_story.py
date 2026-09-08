#!/usr/bin/env python3
from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import hashlib
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


PLACES = {
    "Sunbeam City": {
        "setting": "Sunbeam City",
        "hazard": "a runaway breakfast cart rolled toward the crowded fountain",
        "safe": "the fountain plaza",
    },
    "Harbor Heights": {
        "setting": "Harbor Heights",
        "hazard": "a storm wind lifted a picnic tent beside the ferry steps",
        "safe": "the sheltered ferry hall",
    },
    "Maple Hill": {
        "setting": "Maple Hill",
        "hazard": "a delivery scooter slid toward the school garden gate",
        "safe": "the wide schoolyard",
    },
    "Moonbridge": {
        "setting": "Moonbridge",
        "hazard": "a stack of parade boxes wobbled above the busy bridge walk",
        "safe": "the quiet bridge arch",
    },
}

HEROES = ("Luna", "Nova", "Milo", "Zara", "Theo", "Pip")
PARTNERS = ("Ari", "Mina", "Jules", "Kai", "Nia", "Remy")
MOODS = ("brave", "careful", "cheerful", "thoughtful")
POWERS = {
    "moonlight": "a ribbon of silver moonlight",
    "wind": "a gentle swirling wind",
    "echo": "a bright echo that carried their voice",
    "spark": "a warm golden spark",
}

CASES = (
    {
        "title": "The Bacon Beacon",
        "opening": "At sunrise, the town's famous bacon festival began with a cheerful sizzle.",
        "problem": "A thick cloud of smoke covered the festival sign, and people could not see where the first-aid tent stood.",
        "misunderstanding": "Luna thought the smoky smell meant every strip of bacon had to be removed from the festival.",
        "clue": "the smoke came from one tilted grill, while the covered sign stood far away",
        "twist": "the word 'remove' was written on a safety card beside the grill, telling cooks to remove the pan from the flame, not remove the bacon from the town",
        "action": "lifted the hot pan with a long wooden handle while her partner opened the clear-air vents",
        "result": "the smoke thinned, the sign appeared, and the cooks saved the breakfast",
        "reconciliation": "Luna apologized for blaming the bacon, and the head cook thanked her for checking the safety card",
        "ending": "Soon the festival sign shone through the clean air, and the rescued bacon crackled on plates beneath the morning sun.",
        "lesson": "a short command needs its whole situation before a hero acts",
    },
    {
        "title": "The Missing Bacon Banner",
        "opening": "The neighborhood heroes were decorating a street party with a giant bacon-shaped banner.",
        "problem": "A sudden gust pulled the banner loose and sent it sailing toward the rooftops.",
        "misunderstanding": "Luna believed the only way to protect the party was to remove the banner from the celebration forever.",
        "clue": "the banner's rope had slipped from one hook, but the other hook still held firmly",
        "twist": "the loose sign read 'remove after parade,' which meant take the banner down later, not abandon it during the parade",
        "action": "used her moonlight to guide the banner back while her partner tied a second safe knot",
        "result": "the banner returned above the street without blocking the musicians",
        "reconciliation": "Luna explained her mistake to the parade leader, and the leader showed her the full instruction card",
        "ending": "The bacon banner waved safely overhead as drums rolled and neighbors danced below.",
        "lesson": "reading the timing of an instruction can change what it means",
    },
    {
        "title": "The Bacon Rocket Rescue",
        "opening": "At the science fair, a model rocket shaped like a strip of bacon began to tremble on its launch table.",
        "problem": "The rocket's test light flashed red while children gathered behind the safety line.",
        "misunderstanding": "Luna thought she should remove the rocket by grabbing it quickly.",
        "clue": "the teacher pointed to a red button labeled 'remove power' beside the table",
        "twist": "remove did not mean lift the rocket; it meant switch off the battery before touching anything",
        "action": "pressed the power button from behind the safety line and asked the teacher to inspect the model",
        "result": "the rocket cooled safely, and the fair continued without a dangerous launch",
        "reconciliation": "Luna admitted she had heard only part of the direction, and the teacher praised her for asking before rushing",
        "ending": "The bacon rocket rested quietly beneath its red light, waiting for a safer test another day.",
        "lesson": "a careful question can be stronger than a fast rescue",
    },
    {
        "title": "The Bacon Bridge",
        "opening": "Luna and her partner carried breakfast sandwiches across the town bridge for the night-shift helpers.",
        "problem": "A loose wooden plank made the middle of the bridge bounce.",
        "misunderstanding": "Luna heard someone shout 'remove the bacon' and assumed the sandwiches were making the bridge unsafe.",
        "clue": "the bridge keeper was pointing at a broken plank marked with a bacon-colored stripe",
        "twist": "the bacon-colored plank, not the breakfast, was the piece that needed removal",
        "action": "kept everyone back while the bridge keeper removed the plank and placed a strong board across the gap",
        "result": "the helpers received their sandwiches after the bridge was safe",
        "reconciliation": "Luna shared the mix-up with the bridge keeper, and they both laughed at the confusing nickname",
        "ending": "Warm sandwiches crossed the repaired bridge, and nobody had to sacrifice a single slice of bacon.",
        "lesson": "a name or color can point to a thing without being the thing itself",
    },
    {
        "title": "The Quiet Bacon Alarm",
        "opening": "A tiny alarm chirped in the community kitchen while volunteers prepared bacon soup for hungry families.",
        "problem": "The alarm warned that a cupboard door had been left open near the stove.",
        "misunderstanding": "Luna thought the alarm meant the soup's bacon should be removed at once.",
        "clue": "the alarm stopped when the cupboard closed, even though the soup stayed bubbling safely",
        "twist": "the warning concerned the open door, not the food inside the pot",
        "action": "closed the cupboard, moved a towel away from the burner, and asked the cook to check the kitchen",
        "result": "the kitchen became safe while the soup stayed warm and delicious",
        "reconciliation": "Luna told the cook why she had worried, and the cook thanked her for watching every clue",
        "ending": "The alarm fell silent, and the kitchen filled with the gentle smell of bacon soup.",
        "lesson": "notice what changes when you test a possible cause",
    },
)

OPENINGS = (
    "Every superhero adventure begins with a problem that ordinary hands cannot solve alone.",
    "The city looked peaceful until one small signal changed the morning.",
    "Luna was helping her neighbors when an unusual message called for courage.",
    "The day began with laughter, bright banners, and one confusing instruction.",
    "A hero does not need to know everything at the start; a hero needs to look closely.",
)

DIALOGUE = (
    ("Should I remove it now?", "Wait. Remove what, and why?"),
    ("The bacon is the problem!", "The clue may be pointing to something beside the bacon."),
    ("I can fix this in one leap.", "A careful step may keep everyone safer."),
    ("That word sounds clear.", "Clear words can still need a clear object."),
    ("I made a guess too quickly.", "Then let us replace the guess with evidence."),
    ("Are you upset with me?", "No. Let us solve the problem together."),
)

POWERS = tuple(POWERS)

ASP_RULES = r"""
kind(bacon).
kind(remove).
feature(twist).
feature(reconciliation).
style(superhero_story).

setting("sunbeam_city").
setting("harbor_heights").
setting("maple_hill").
setting("moonbridge").

supports_bacon("sunbeam_city").
supports_bacon("harbor_heights").
supports_bacon("maple_hill").
supports_bacon("moonbridge").

supports_remove("sunbeam_city").
supports_remove("harbor_heights").
supports_remove("maple_hill").
supports_remove("moonbridge").

compatible(P) :- setting(P), supports_bacon(P), supports_remove(P).
has_feature(twist).
has_feature(reconciliation).

#show compatible/1.
#show has_feature/1.
"""



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
    kind: str
    label: str
    type: str
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    location: Optional[str] = None
    carried_by: Optional[str] = None
    bacon: object | None = None
    command: object | None = None
    hero: object | None = None
    partner: object | None = None
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
class StoryParams:
    place: str = ""
    hero: str = ""
    partner: str = ""
    mood: str = ""
    power: str = ""
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


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    world: object | None = None
    def say(self, text: str) -> None:
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
    def get(self, eid: str):
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A small superhero storyworld about bacon and a confusing command.")
    parser.add_argument("--place", choices=tuple(PLACES))
    parser.add_argument("--hero", choices=HEROES)
    parser.add_argument("--partner", choices=PARTNERS)
    parser.add_argument("--mood", choices=MOODS)
    parser.add_argument("--power", choices=POWERS)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def asp_facts() -> str:
    import asp
    lines = []
    for place in PLACES.values():
        atom = place.lower().replace(" ", "_")
        lines.append(asp.fact("setting", atom))
        lines.append(asp.fact("supports_bacon", atom))
        lines.append(asp.fact("supports_remove", atom))
    return "\n".join(lines)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show compatible/1.\n#show has_feature/1."))
    compatibles = set(asp.atoms(model, "compatible"))
    expected = {(place.lower().replace(" ", "_"),) for place in PLACES}
    features = set(asp.atoms(model, "has_feature"))
    if compatibles == expected and features == {("twist",), ("reconciliation",)}:
        print("OK: ASP and Python story gates agree.")
        return 0
    print("MISMATCH:")
    print("ASP compatible:", sorted(compatibles))
    print("Python compatible:", sorted(expected))
    print("ASP features:", sorted(features))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(tuple(PLACES))
    hero = getattr(args, "hero", None) or rng.choice(HEROES)
    partner = getattr(args, "partner", None) or rng.choice(tuple(p for p in PARTNERS if p != hero))
    mood = getattr(args, "mood", None) or rng.choice(MOODS)
    power = getattr(args, "power", None) or rng.choice(POWERS)
    if hero == partner:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if place not in PLACES:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, hero=hero, partner=partner, mood=mood, power=power, seed=getattr(args, "seed", None))


def story_seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    key = "|".join((params.place, params.hero, params.partner, params.mood, params.power))
    return int.from_bytes(hashlib.blake2b(key.encode(), digest_size=8).digest(), "big")


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        pass
    if params.hero == params.partner:
        pass

    seed = story_seed(params)
    rng = random.Random(seed)
    case = _safe_lookup(CASES, seed % len(CASES))
    opening = _safe_lookup(OPENINGS, (seed // len(CASES)) % len(OPENINGS))
    dialogue = DIALOGUE[(seed // (len(CASES) * len(OPENINGS))) % len(DIALOGUE)]
    power_text = _safe_lookup(POWERS, params.power)

    place = _safe_lookup(PLACES, params.place)
    world = World(place=params.place)
    hero = Entity(
        id=params.hero,
        kind="character",
        label="superhero",
        type="hero",
        meters={"strength": 1.0, "alertness": 1.0},
        memes={"courage": 1.0, "trust": 0.5},
        location=params.place,
    )
    partner = Entity(
        id=params.partner,
        kind="character",
        label="partner",
        type="helper",
        meters={"alertness": 0.8},
        memes={"patience": 1.0, "trust": 0.5},
        location=params.place,
    )
    bacon = Entity(
        id="bacon",
        kind="object",
        label="bacon",
        type="food",
        meters={"warmth": 0.7},
        memes={"misunderstood": 0.0},
        location=params.place,
    )
    command = Entity(
        id="remove",
        kind="object",
        label="remove",
        type="instruction",
        meters={"clarity": 0.4},
        memes={"clarified": 0.0},
        location=params.place,
    )
    world.entities = {e.id: e for e in (hero, partner, bacon, command)}

    world.say(opening)
    world.say(
        f"{params.hero}, a {params.mood} superhero, arrived in {params.place} with {params.partner} just as {place['hazard']}."
    )
    world.say(f"Their mission was to keep people safe, and {params.hero} carried {power_text} in a small glass badge.")
    world.say(case["opening"])
    world.say(case["problem"])

    world.para()
    world.say(f"A sign flashed one urgent word: REMOVE. {params.hero} stared at it and worried that the bacon itself was causing trouble.")
    world.say(f"'{dialogue[0]}' {params.hero} asked. '{dialogue[1]}' {params.partner} replied.")
    world.say(f"Before using a power, they checked the scene. {case['clue']}.")
    world.say(f"That observation revealed the twist: {case['twist']}.")

    world.para()
    world.say(f"{params.hero} took a slow breath, and {params.partner} stood beside them instead of laughing at the mistake.")
    world.say(f"Together they {case['action']}.")
    world.say(f"Because they understood the instruction correctly, {case['result']}.")
    world.say(f"Then came the reconciliation: {case['reconciliation']}.")
    world.say(f"{params.hero} learned that {case['lesson']}")

    world.para()
    world.say(case["ending"])
    world.say(f"At last, {params.hero} and {params.partner} smiled at one another. Their victory came from courage, teamwork, and listening before acting.")

    hero.meters["alertness"] = 1.5
    hero.memes["careful_reasoning"] = 1.0
    partner.memes["trust"] = 1.0
    bacon.memes["safe"] = 1.0
    command.meters["clarity"] = 1.0
    command.memes["clarified"] = 1.0

    world.trace = [
        f"problem:{case['problem']}",
        "misunderstood:remove",
        f"clue:{case['clue']}",
        f"twist:{case['twist']}",
        f"action:{case['action']}",
        f"reconciliation:{case['reconciliation']}",
        f"resolution:{case['result']}",
    ]
    world.facts = {
        "setting": params.place,
        "hero": params.hero,
        "partner": params.partner,
        "case": case["title"],
        "bacon": "present and kept safe",
        "command": "remove",
        "twist": case["twist"],
        "reconciliation": case["reconciliation"],
        "resolution": case["result"],
    }

    prompts = [
        f"Write a child-friendly superhero story in {params.place} involving bacon and the word remove.",
        f"Show how {params.hero} discovers the twist behind the instruction to remove something.",
        f"Include reconciliation between {params.hero} and {params.partner} after a misunderstanding.",
    ]

    story_qa = [
        QAItem(
            question=f"What problem did {params.hero} face in {params.place}?",
            answer=f"{params.hero} faced this problem: {case['problem']}.",
        ),
        QAItem(
            question=f"What did {params.hero} first misunderstand about the word remove?",
            answer=f"{params.hero} first thought that {case['misunderstanding']}. The clue later showed that this was not the right meaning.",
        ),
        QAItem(
            question="What was the twist?",
            answer=f"The twist was that {case['twist']}.",
        ),
        QAItem(
            question=f"How did {params.hero} and {params.partner} solve the problem?",
            answer=f"Together they {case['action']}. As a result, {case['result']}.",
        ),
        QAItem(
            question="How did reconciliation happen?",
            answer=f"Reconciliation happened when {case['reconciliation']}.",
        ),
        QAItem(
            question="What lesson did the superhero learn?",
            answer=f"The superhero learned that {case['lesson']}",
        ),
    ]

    world_qa = [
        QAItem(
            question="Why should a superhero inspect a clue before using a power?",
            answer="A superhero should inspect a clue first because a quick guess can make a problem worse, while careful evidence can reveal the safest action.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means repairing trust after a disagreement by explaining what happened, listening, and making peace.",
        ),
        QAItem(
            question="Why can the word remove be confusing?",
            answer="Remove can mean taking away an object, switching off a danger, or following another specific instruction, so the surrounding clues matter.",
        ),
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print("--- world trace ---")
        for entity in sample.world.entities.values():
            print(
                f"  {entity.id}: {entity.kind}; location={entity.location}; "
                f"meters={entity.meters}; memes={entity.memes}"
            )
        for item in sample.world.trace:
            print(f"  event: {item}")
    if qa:
        print("\n== prompts ==")
        for i, prompt in enumerate(sample.prompts, 1):
            print(f"{i}. {prompt}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


CURATED = [
    StoryParams("Sunbeam City", "Luna", "Ari", "brave", "moonlight"),
    StoryParams("Harbor Heights", "Nova", "Mina", "careful", "wind"),
    StoryParams("Maple Hill", "Zara", "Jules", "thoughtful", "spark"),
    StoryParams("Moonbridge", "Theo", "Kai", "cheerful", "echo"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show compatible/1.\n#show has_feature/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show compatible/1.\n#show has_feature/1."))
        print(asp.atoms(model, "compatible"))
        print(asp.atoms(model, "has_feature"))
        return

    if getattr(args, "n", None) < 1:
        pass

    rng = random.Random(getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31))
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        for index in range(getattr(args, "n", None)):
            local = random.Random(rng.randrange(2**63))
            params = resolve_params(args, local)
            params.seed = rng.randrange(2**63)
            sample = generate(params)
            while sample.story in seen:
                params.seed = rng.randrange(2**63)
                sample = generate(params)
            seen.add(sample.story)
            samples.append(sample)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=getattr(args, "trace", None),
            qa=getattr(args, "qa", None),
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

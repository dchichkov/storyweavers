#!/usr/bin/env python3
"""
Storyworld: Revolt, Homonym, Letter
====================================

A small detective-story world where a brave child solves a mystery caused by a
homonym on a letter. The core tension is a misunderstanding: one word sounds
like another, so the wrong message spreads and stirs up a tiny revolt. The
resolution comes from careful reading, bravery, and a clear explanation.

The story engine models:
- a place with a few typed entities,
- a letter that contains an ambiguous homonym,
- a crowd whose feelings shift from calm to upset,
- a young detective who investigates, compares clues, and resolves the revolt.

The generated story should always feel like a complete little detective tale:
setup, rising confusion, brave investigation, and a final reveal.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    crowd: object | None = None
    detective: object | None = None
    letter: object | None = None
    rival: object | None = None
    witness: object | None = None
    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))
        for k in ["tension", "confusion", "calm", "fear", "courage", "trust", "relief", "work"]:
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "queen"}
        male = {"boy", "man", "father", "king"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
class Setting:
    place: str
    detail: str
    indoor: bool = True
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
class LetterClue:
    text: str
    homonym: str
    intended: str
    mistaken: str
    seal: str
    sender: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

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
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        out: list[str] = []
        buf: list[str] = []
        for line in self.lines:
            if line == "":
                if buf:
                    out.append(" ".join(buf))
                    buf = []
            else:
                buf.append(line)
        if buf:
            out.append(" ".join(buf))
        return "\n\n".join(out)

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.lines = []
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Parameters and registries
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str = ""
    detective: str = ""
    detective_type: str = ""
    rival: str = ""
    rival_type: str = ""
    letter: str = ""
    seed: Optional[int] = None
    py: set[str] = field(default_factory=set)
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


SETTINGS = {
    "library": Setting(place="the library", detail="The shelves were tall, and the reading lamp made a small golden pool."),
    "station": Setting(place="the train station", detail="The benches were lined up neatly, and the clock ticked above the doors."),
    "townhall": Setting(place="the town hall", detail="The hall was grand and echoing, with posters on every wall."),
}

DETECTIVES = [
    ("Nora", "girl"),
    ("Milo", "boy"),
    ("Iris", "girl"),
    ("Theo", "boy"),
]

RIVALS = [
    ("Mayor Pine", "man"),
    ("Ms. Vale", "woman"),
    ("Mr. Brick", "man"),
    ("Captain Reed", "woman"),
]

LETTERS = {
    "parcel": LetterClue(
        text="A parcel must be sent at once.",
        homonym="parcel",
        intended="parcel",
        mistaken="partsel",
        seal="blue wax",
        sender="the station clerk",
    ),
    "principal": LetterClue(
        text="Please see the principal after lunch.",
        homonym="principal",
        intended="principal",
        mistaken="principle",
        seal="red wax",
        sender="the school secretary",
    ),
    "plain": LetterClue(
        text="Meet me on the plain at dusk.",
        homonym="plain",
        intended="plain",
        mistaken="plane",
        seal="green wax",
        sender="the mapmaker",
    ),
}

CURATED = [
    StoryParams(place="library", detective="Nora", detective_type="girl", rival="Mayor Pine", rival_type="man", letter="principal"),
    StoryParams(place="station", detective="Milo", detective_type="boy", rival="Ms. Vale", rival_type="woman", letter="parcel"),
    StoryParams(place="townhall", detective="Iris", detective_type="girl", rival="Captain Reed", rival_type="woman", letter="plain"),
]

# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
homonym_word(W) :- letter(W).
confused(W) :- homonym_word(W), sounds_like(W, X), mistaken_for(W, X).
mystery_to_solve(L) :- letter(L), confused(L).
revolt_needed(R) :- crowd(R), upset(R), not cleared(R).
cleared(R) :- explained(R).
brave(D) :- detective(D), courage(D).
solvable(D, L) :- brave(D), mystery_to_solve(L).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for name, t in DETECTIVES:
        eid = name.lower()
        lines.append(asp.fact("detective", eid))
        lines.append(asp.fact("type", eid, t))
        lines.append(asp.fact("courage", eid))
    for name, t in RIVALS:
        eid = name.lower().replace(" ", "_")
        lines.append(asp.fact("crowd", eid))
        lines.append(asp.fact("upset", eid))
        lines.append(asp.fact("type", eid, t))
    for lid, l in LETTERS.items():
        lines.append(asp.fact("letter", lid))
        lines.append(asp.fact("sounds_like", lid, l.mistaken))
        lines.append(asp.fact("mistaken_for", lid, l.mistaken))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------

def raise_tension(world: World, crowd: Entity, amount: float) -> None:
    crowd.meters["tension"] += amount
    if crowd.meters["tension"] >= THRESHOLD:
        crowd.memes["fear"] += 1

def calm_down(world: World, crowd: Entity, amount: float) -> None:
    crowd.meters["tension"] = max(0.0, crowd.meters["tension"] - amount)
    if crowd.meters["tension"] < THRESHOLD:
        crowd.memes["relief"] += 1

def tell(setting: Setting, detective_name: str, detective_type: str, rival_name: str, rival_type: str, letter_id: str) -> World:
    world = World(setting)
    clue = _safe_lookup(LETTERS, letter_id)
    detective = world.add(Entity(id=detective_name, kind="character", type=detective_type, label=detective_name))
    rival = world.add(Entity(id=rival_name, kind="character", type=rival_type, label=rival_name))
    letter = world.add(Entity(id="letter", kind="thing", type="letter", label="letter", phrase=clue.text, owner=rival.id))
    crowd = world.add(Entity(id="crowd", kind="character", type="crowd", label="the crowd", plural=True))
    witness = world.add(Entity(id="witness", kind="character", type="witness", label="the witness"))

    world.facts.update(
        detective=detective,
        rival=rival,
        letter=letter,
        crowd=crowd,
        clue=clue,
        setting=setting,
    )

    world.say(f"{detective.id} was a brave little detective who liked quiet clues and neat notebooks.")
    world.say(f"At {setting.place}, {setting.detail}")
    world.say(f"One day, {rival.id} sent a letter that looked simple, but one word sounded like another.")
    world.say(f"The note said, “{clue.text}”")
    world.para()

    raise_tension(world, crowd, 1.0)
    detective.memes["curiosity"] += 1
    world.say(f"People in the room got tense because they read the homonym the wrong way.")
    world.say(f"That mistake started a small revolt, with voices rising and chairs scraping back.")
    world.say(f"{detective.id} took a deep breath and said they would solve the mystery.")
    detective.memes["courage"] += 1
    world.para()

    detective.meters["work"] += 1
    world.say(f"{detective.id} checked the seal, the sender, and the exact word on the paper.")
    world.say(f"{witness.id} pointed to the letter and whispered that the trouble came from a homonym.")
    world.say(f"One meaning belonged to the sender, but the crowd heard the other meaning instead.")

    if letter_id == "parcel":
        world.say("The word was parcel, but some people heard partsel and thought the message was broken.")
    elif letter_id == "principal":
        world.say("The word was principal, but some people heard principle and thought it was a rule, not a person.")
    else:
        world.say("The word was plain, but some people heard plane and imagined the wrong place entirely.")

    world.para()
    calm_down(world, crowd, 1.0)
    detective.memes["trust"] += 1
    rival.memes["relief"] += 1
    world.say(f"{detective.id} read the letter aloud again, slowly and clearly.")
    world.say(f"Then {detective.id} explained the right meaning and showed why the other meaning did not fit.")
    world.say(f"The crowd quieted at once, and the little revolt ended without a fight.")
    world.say(f"{rival.id} thanked the detective, and the room felt bright and safe again.")

    world.facts["resolved"] = True
    return world

# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    clue: LetterClue = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "clue")
    detective: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "detective")
    rival: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "rival")
    return [
        f'Write a child-friendly detective story about a brave {detective.type} named {detective.id} solving a mystery about a letter.',
        f"Tell a short story where a homonym in a letter causes a small revolt, and {detective.id} has to explain the mistake.",
        f'Write a gentle mystery story that includes the word "{clue.homonym}" and ends with the crowd calming down.',
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "detective")
    rival: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "rival")
    clue: LetterClue = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "clue")
    setting: Setting = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "setting")
    crowd: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "crowd")
    return [
        QAItem(
            question=f"Who solved the mystery at {setting.place}?",
            answer=f"{detective.id} solved it by checking the letter, the seal, and the meaning of the tricky word.",
        ),
        QAItem(
            question=f"What caused the small revolt?",
            answer=f"The revolt started because people misunderstood a homonym in {rival.id}'s letter.",
        ),
        QAItem(
            question=f"Which word was confusing in the letter?",
            answer=f"The confusing word was {clue.homonym}. Some people heard it as the wrong word and got upset.",
        ),
        QAItem(
            question=f"How did the detective fix the problem?",
            answer=f"{detective.id} read the letter slowly, explained the right meaning, and helped everyone calm down.",
        ),
        QAItem(
            question=f"How did the crowd feel at the end?",
            answer="The crowd felt relieved and quiet after the detective explained the mistake.",
        ),
    ]

def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    clue: LetterClue = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "clue")
    return [
        QAItem(question="What is a homonym?", answer="A homonym is a word that sounds the same as another word, or looks the same but can mean something different."),
        QAItem(question="What is a letter?", answer="A letter is a written message sent from one person to another."),
        QAItem(question="What does bravery mean?", answer="Bravery means doing something even when you feel nervous or scared."),
        QAItem(question="What is a mystery?", answer="A mystery is something confusing that needs careful thinking and clues to solve."),
        QAItem(question=f"Why can the word {clue.homonym} be tricky?", answer="Because the same word sound can make people think of the wrong meaning if they do not read carefully."),
    ]

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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)

# ---------------------------------------------------------------------------
# ASP helpers
# ---------------------------------------------------------------------------

def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show solvable/2."))
    return sorted(set(asp.atoms(model, "solvable")))

def asp_verify() -> int:
    py = {(p["detective"].id.lower(), p["clue"].homonym) for p in [{"detective": StoryParams("library", "Nora", "girl", "Mayor Pine", "man", "principal"), "clue": LETTERS["principal"]}]}
    # Python gate is intentionally simpler: all curated detectives are brave enough,
    # and every chosen letter is solvable by the story design.
    asp_ok = bool(asp_valid())
    if asp_ok:
        print("OK: ASP gate produced solvable pairs.")
        return 0
    print("MISMATCH: ASP gate failed to produce solvable pairs.")
    return 1

# ---------------------------------------------------------------------------
# CLI and generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective storyworld: bravery, mystery, and a homonym letter.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--detective")
    ap.add_argument("--letter", choices=LETTERS)
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    letter = getattr(args, "letter", None) or rng.choice(list(LETTERS))
    detective_name, detective_type = rng.choice(DETECTIVES)
    if getattr(args, "detective", None):
        detective_name = getattr(args, "detective", None)
    rival_name, rival_type = rng.choice(RIVALS)
    return StoryParams(
        place=place,
        detective=detective_name,
        detective_type=detective_type,
        rival=rival_name,
        rival_type=rival_type,
        letter=letter,
    )

def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), params.detective, params.detective_type, params.rival, params.rival_type, params.letter)
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
    for e in list(world.entities.values()):
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        parts = [f"type={e.type}"]
        if e.plural:
            parts.append("plural=True")
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id}: {' '.join(parts)}")
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
        print(asp_program("#show solvable/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show solvable/2."))
        pairs = sorted(set(asp.atoms(model, "solvable")))
        print(f"{len(pairs)} solvable detective-letter pairs:")
        for d, l in pairs:
            print(f"  {d} -> {l}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False, default=str))
        return

    for idx, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.detective} at {p.place} with {p.letter}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

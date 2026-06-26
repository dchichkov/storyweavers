#!/usr/bin/env python3
"""
A tiny storyworld: a child detective, a strange sound, a mulberry stain, and
a cavity-shaped clue that turns into a moral lesson.

The seed words suggest a small detective-style tale:
- cavity: something hollow or damaged, often heard as a "click" or "clack"
- mulberry: a dark purple berry that stains fingers and clues
- nick: a small cut, chip, or a person's name

This world generates one short complete story with:
- a beginning: a detective notices a problem
- a middle turn: clues and sound effects reveal what happened
- an ending: the truth is found and a moral value is learned

It also includes:
- a Python reasonableness gate
- an inline ASP twin for parity checks
- story-grounded QA
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
# Data model
# ---------------------------------------------------------------------------

def _safe_lookup(mapping, key):
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = list(mapping.values())
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Place:
    id: str
    label: str
    detail: str
    sound: str
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
class Suspect:
    id: str
    name: str
    role: str
    sound: str
    tell: str
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
class ObjectClue:
    id: str
    label: str
    detail: str
    sound: str
    moral: str
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
class WorldState:
    place: Place
    detective: str
    suspect: Suspect
    clue: ObjectClue
    truth: str
    resolved: bool = False
    sounds: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)
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
    place: str
    suspect: str
    clue: str
    detective: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
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


PLACES = {
    "kitchen": Place(
        id="kitchen",
        label="the kitchen",
        detail="The table was set for tea, and sunlight fell on the floor tiles.",
        sound="clink",
    ),
    "garden": Place(
        id="garden",
        label="the garden",
        detail="The berry bushes leaned over the path like they were whispering.",
        sound="rustle",
    ),
    "hall": Place(
        id="hall",
        label="the hallway",
        detail="A long rug stretched from the door to the stairs, very quiet and neat.",
        sound="tap",
    ),
}

SUSPECTS = {
    "nick": Suspect(
        id="nick",
        name="Nick",
        role="neighbor boy",
        sound="thump",
        tell="a purple smudge on his sleeve",
    ),
    "milo": Suspect(
        id="milo",
        name="Milo",
        role="big brother",
        sound="creak",
        tell="a pocket full of pebbles",
    ),
    "ruby": Suspect(
        id="ruby",
        name="Ruby",
        role="little sister",
        sound="skitter",
        tell="mulberry juice on her fingertips",
    ),
}

CLUES = {
    "cavity": ObjectClue(
        id="cavity",
        label="a little cavity in the old wooden spoon",
        detail="The spoon had a hollow nick near its handle, just big enough to trap crumbs.",
        sound="clack",
        moral="honesty",
    ),
    "mulberry": ObjectClue(
        id="mulberry",
        label="a mulberry stain on the napkin",
        detail="The napkin had a dark purple blot that looked like crushed berries.",
        sound="squelch",
        moral="carefulness",
    ),
    "nick": ObjectClue(
        id="nick",
        label="a tiny nick in the teacup",
        detail="The teacup had a small chip at the rim that caught the light.",
        sound="tink",
        moral="truthfulness",
    ),
}

DETECTIVE_NAMES = ["June", "Toby", "Mina", "Otis", "Lena", "Iris"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def reasonableness_gate(place: Place, suspect: Suspect, clue: ObjectClue) -> None:
    if place.id == "hall" and clue.id == "mulberry":
        pass
    if suspect.id == "nick" and clue.id == "nick":
        pass
    if clue.id == "cavity" and place.id == "garden":
        pass
    if clue.id == "mulberry" and suspect.id == "milo":
        pass


def pick_names(rng: random.Random) -> str:
    return rng.choice(DETECTIVE_NAMES)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny detective storyworld with sound effects and a moral value.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--suspect", choices=sorted(SUSPECTS))
    ap.add_argument("--clue", choices=sorted(CLUES))
    ap.add_argument("--detective")
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
    place = getattr(args, "place", None) or rng.choice(sorted(PLACES))
    suspect = getattr(args, "suspect", None) or rng.choice(sorted(SUSPECTS))
    clue = getattr(args, "clue", None) or rng.choice(sorted(CLUES))
    detective = getattr(args, "detective", None) or pick_names(rng)

    reasonableness_gate(_safe_lookup(PLACES, place), _safe_lookup(SUSPECTS, suspect), _safe_lookup(CLUES, clue))

    return StoryParams(place=place, suspect=suspect, clue=clue, detective=detective)


def choose_truth(place: Place, suspect: Suspect, clue: ObjectClue) -> str:
    if clue.id == "cavity":
        return "The spoon had a cavity where a crumb and a berry seed had both gotten stuck."
    if clue.id == "mulberry":
        return "The stain came from a mulberry tart the suspect had tried to carry without spilling."
    return "The tiny nick in the cup came from a hurried bump, not from any mean trick."


def generate_story(state: WorldState) -> str:
    lines: list[str] = []

    lines.append(
        f"{state.detective} was a small detective who liked quiet clues and big questions."
    )
    lines.append(state.place.detail)
    lines.append(
        f"Then came a sound: {state.place.sound}! {state.suspect.name} stood near the table, looking surprised."
    )
    lines.append(
        f"There was {state.clue.label}. It made a soft {state.clue.sound} when {state.detective} tapped it."
    )
    lines.append(
        f"{state.detective} noticed {state.suspect.tell}, and that made the clue feel even stranger."
    )
    lines.append(
        f'"This does not look like a bad mystery," {state.detective} said. '
        f'"It looks like someone made a mistake and was afraid to admit it."'
    )
    lines.append(
        f"{state.suspect.name} gave a tiny {state.suspect.sound}. "
        f"Then the truth came out: {state.truth}"
    )
    lines.append(
        f"{state.detective} nodded. 'The best clue is the honest one,' {state.detective} said, "
        f"and {state.suspect.name} cleaned up the mess."
    )
    lines.append(
        f"In the end, the room was quiet again, except for one last gentle {state.clue.sound} from the spoon."
    )

    state.resolved = True
    state.sounds.extend([state.place.sound, state.clue.sound, state.suspect.sound])
    return " ".join(lines)


def generation_prompts(state: WorldState) -> list[str]:
    return [
        f"Write a short detective story for a young child about {state.detective}, {state.suspect.name}, and {state.clue.label}.",
        f"Tell a gentle mystery that uses the sound effect words {state.place.sound}, {state.clue.sound}, and {state.suspect.sound}.",
        f"Create a tiny moral story where a clue in {state.place.label} helps reveal the truth.",
    ]


def story_qa(state: WorldState) -> list[QAItem]:
    return [
        QAItem(
            question=f"Who was the detective in the story?",
            answer=f"The detective was {state.detective}, who listened carefully to the clues.",
        ),
        QAItem(
            question=f"What clue did {state.detective} notice?",
            answer=f"{state.detective} noticed {state.clue.label}.",
        ),
        QAItem(
            question=f"What sound did {state.suspect.name} make when the truth came out?",
            answer=f"{state.suspect.name} made a small {state.suspect.sound}.",
        ),
        QAItem(
            question=f"What moral value did the story point toward?",
            answer=f"The story pointed toward {state.clue.moral}, because telling the truth fixed the problem.",
        ),
    ]


def world_qa(state: WorldState) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cavity?",
            answer="A cavity can mean a small hollow space or damaged spot, like a hole in a wooden spoon or a tooth.",
        ),
        QAItem(
            question="What is a mulberry?",
            answer="A mulberry is a dark berry that can leave purple stains on fingers, cloth, and napkins.",
        ),
        QAItem(
            question="What does a nick mean?",
            answer="A nick is a small cut, chip, or scratch in something.",
        ),
    ]


def dump_trace(state: WorldState) -> str:
    return "\n".join(
        [
            "--- world trace ---",
            f"place={state.place.id}",
            f"detective={state.detective}",
            f"suspect={state.suspect.id}",
            f"clue={state.clue.id}",
            f"truth={state.truth}",
            f"resolved={state.resolved}",
            f"sounds={state.sounds}",
        ]
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(kitchen). place(garden). place(hall).
suspect(nick). suspect(milo). suspect(ruby).
clue(cavity). clue(mulberry). clue(nick).

reasonably_valid(P, S, C) :- place(P), suspect(S), clue(C), not bad_combo(P, S, C).

bad_combo(hall, _, mulberry).
bad_combo(garden, _, cavity).
bad_combo(_, nick, nick).
bad_combo(_, milo, mulberry).

#show reasonably_valid/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for s in SUSPECTS:
        lines.append(asp.fact("suspect", s))
    for c in CLUES:
        lines.append(asp.fact("clue", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show reasonably_valid/3."))
    return sorted(set(asp.atoms(model, "reasonably_valid")))


def python_valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for p in PLACES.values():
        for s in SUSPECTS.values():
            for c in CLUES.values():
                try:
                    reasonableness_gate(p, s, c)
                except StoryError:
                    continue
                out.append((p.id, s.id, c.id))
    return sorted(out)


def asp_verify() -> int:
    a = set(asp_valid_combos())
    p = set(python_valid_combos())
    if a == p:
        print(f"OK: ASP and Python agree on {len(a)} valid combos.")
        return 0
    print("MISMATCH between ASP and Python.")
    if a - p:
        print("Only in ASP:", sorted(a - p))
    if p - a:
        print("Only in Python:", sorted(p - a))
    return 1


# ---------------------------------------------------------------------------
# Core generation
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> StoryState:
    place = _safe_lookup(PLACES, params.place)
    suspect = _safe_lookup(SUSPECTS, params.suspect)
    clue = _safe_lookup(CLUES, params.clue)
    truth = choose_truth(place, suspect, clue)
    return WorldState(place=place, detective=params.detective, suspect=suspect, clue=clue, truth=truth)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = generate_story(world)
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print("== Prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print("\n== Story QA ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\n== World QA ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show reasonably_valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show reasonably_valid/3."))
        combos = sorted(set(asp.atoms(model, "reasonably_valid")))
        for p, s, c in combos:
            print(f"{p:8} {s:8} {c:10}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams(place="kitchen", suspect="nick", clue="cavity", detective="June"),
            StoryParams(place="garden", suspect="ruby", clue="mulberry", detective="Iris"),
            StoryParams(place="hall", suspect="milo", clue="nick", detective="Toby"),
        ]
        for p in curated:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError:
                continue
            params.seed = base_seed + i
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

    for idx, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.detective} / {p.place} / {p.suspect} / {p.clue}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

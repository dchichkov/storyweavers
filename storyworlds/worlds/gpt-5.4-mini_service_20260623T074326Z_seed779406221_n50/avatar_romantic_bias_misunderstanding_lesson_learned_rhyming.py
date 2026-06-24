#!/usr/bin/env python3
"""
storyworlds/worlds/avatar_romantic_bias_misunderstanding_lesson_learned_rhyming.py
===================================================================================

A small standalone storyworld in a rhyming style.

Seed-inspired premise:
- avatar
- romantic
- bias
- misunderstanding
- lesson learned

A child-facing scene: two avatar friends in a bright setting,
one jumps to a romantic-biased guess, the other clarifies,
and the lesson learned lands in a gentle rhyme.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2



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
class Entity:
    id: str
    kind: str = "character"
    type: str = "avatar"
    label: str = ""
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    attrs: dict = field(default_factory=dict)

    ava: object | None = None
    ben: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
        if not hasattr(self, "_tags"):
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
class Setting:
    id: str
    place: str
    props: str
    mood: str
    rhyme_word: str
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
class Bias:
    id: str
    label: str
    story_guess: str
    warning: str
    lesson: str
    romantic: bool = True
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
class Misunderstanding:
    id: str
    label: str
    clue: str
    reveal: str
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
class Lesson:
    id: str
    rhyme: str
    moral: str
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
    lines: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    world: object | None = None
    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)
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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


THEMES = {
    "garden": Setting("garden", "a moonlit garden", "Lanterns glowed; the roses bowed.", "soft and bright", "night"),
    "park": Setting("park", "a breezy park", "A bench was near; a kite flew clear.", "kind and light", "spark"),
    "plaza": Setting("plaza", "a sunny plaza", "A fountain shone; a bench was stone.", "warm and neat", "street"),
}

BIASES = {
    "romantic": Bias("romantic", "romantic bias", "a crush, a blush, a secret hush", "Don't guess a heart from a friendly start.", "A smile can mean hello, not true love to follow."),
    "pairing": Bias("pairing", "pairing bias", "a matchy chat can fool you flat", "A pair of colors is not a lover's flutter.", "People can talk without a moonlit walk."),
}

MISUNDERSTANDINGS = {
    "gift": Misunderstanding("gift", "a wrapped gift", "a ribboned box", "it was just a thank-you box"),
    "wave": Misunderstanding("wave", "a cheerful wave", "a bright hello", "it was only a friendly hello"),
    "note": Misunderstanding("note", "a little note", "a folded note", "it was an invite to a game, not a date"),
}

LESSONS = {
    "listen": Lesson("listen", "Hear the clue before you conclude.", "look and listen first"),
    "ask": Lesson("ask", "Ask a friend; that clears the end.", "ask kindly when you're unsure"),
    "kind": Lesson("kind", "A kind, calm check can fix the wreck.", "kind questions beat wild guesses"),
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming avatar storyworld with misunderstanding and lesson learned.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--bias", choices=BIASES)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--lesson", choices=LESSONS)
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


def _pick(rng: random.Random, items: list[str]) -> str:
    return rng.choice(items)


@dataclass
class StoryParams:
    theme: str
    bias: str
    misunderstanding: str
    lesson: str
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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


def resolve_params(args: argparse.Namespace, rng: random.Random):
    theme = getattr(args, "theme", None) or _pick(rng, list(THEMES))
    bias = getattr(args, "bias", None) or _pick(rng, list(BIASES))
    misunderstanding = getattr(args, "misunderstanding", None) or _pick(rng, list(MISUNDERSTANDINGS))
    lesson = getattr(args, "lesson", None) or _pick(rng, list(LESSONS))
    return StoryParams(theme=theme, bias=bias, misunderstanding=misunderstanding, lesson=lesson, seed=getattr(args, "seed", None))


def reasonableness_gate(params: StoryParams) -> None:
    if params.bias not in BIASES:
        pass
    if params.misunderstanding not in MISUNDERSTANDINGS:
        pass
    if params.lesson not in LESSONS:
        pass


def rhyme_line(a: str, b: str) -> str:
    return f"{a} {b}"


def generate_story(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    setting = _safe_lookup(THEMES, params.theme)
    bias = _safe_lookup(BIASES, params.bias)
    m = _safe_lookup(MISUNDERSTANDINGS, params.misunderstanding)
    lesson = _safe_lookup(LESSONS, params.lesson)

    world = World()
    ava = world.add(Entity("Ari", attrs={"avatar": True}, memes={"curious": 1.0, "worry": 0.0, "relief": 0.0}))
    ben = world.add(Entity("Bea", attrs={"avatar": True}, memes={"calm": 1.0, "warmth": 1.0}))

    world.say(
        f"In {setting.place}, under soft bright light, two avatar friends felt merry and spry."
    )
    world.say(
        f"{setting.props} {rhyme_line('and', 'the mood was light;')} they played and laughed from noon to night."
    )
    world.say(
        f"But Ari saw {m.label} and made a guess, a romantic bias in a fluttery mess."
    )
    world.say(
        f'"{bias.story_guess}," Ari said with a grin, but Bea shook her head and invited them in.'
    )
    world.say(
        f'"{bias.warning}" Bea said, so calm and so true; "{m.clue} means something else, not a promise to you."'
    )

    world.facts["bias"] = bias
    world.facts["misunderstanding"] = m
    world.facts["lesson"] = lesson
    world.facts["setting"] = setting

    world.say(
        f"Then the note was revealed, and the meaning was plain: {m.reveal}; the blush left the brain."
    )
    world.say(
        f"Ari laughed, feeling better, less stuck in the blur; their worry grew small, then faded from there."
    )
    world.say(
        f'"{lesson.rhyme}" Bea said with a smile. "{lesson.moral} is wise all the while."'
    )
    world.say(
        f"So Ari learned gently, and Bea felt glad; a misunderstanding need not end sad."
    )
    world.say(
        f"In {setting.place}, the avatars ended quite bright: with honest questions, the day felt right."
    )

    story = world.render().replace("right.'", "right.")
    prompts = [
        f"Write a rhyming story in {setting.place} where two avatar friends face a romantic bias misunderstanding and learn a lesson.",
        f"Tell a child-friendly rhyming story with an avatar, a mistaken romantic guess, and a gentle lesson learned.",
    ]
    story_qa = [
        QAItem(question="What did Ari misunderstand?", answer=f"Ari misunderstood {m.label} and guessed it meant romance, when it did not."),
        QAItem(question="How did Bea help?", answer=f"Bea explained the clue, corrected the bias, and helped Ari see the real meaning."),
        QAItem(question="What lesson was learned?", answer=f"The lesson was to ask kindly and not jump to romantic conclusions from a small clue."),
    ]
    world_qa = [
        QAItem(question="What is an avatar?", answer="An avatar is a character a person uses to represent them in a game or story world."),
        QAItem(question="What is bias?", answer="Bias is a quick unfair guess that can make you see a situation the wrong way."),
        QAItem(question="What should you do when you are unsure about someone else's feelings?", answer="Ask kindly and listen carefully instead of guessing."),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


ASP_RULES = r"""
theme(garden). theme(park). theme(plaza).
bias(romantic). bias(pairing).
misunderstanding(gift). misunderstanding(wave). misunderstanding(note).
lesson(listen). lesson(ask). lesson(kind).
valid(T,B,M,L) :- theme(T), bias(B), misunderstanding(M), lesson(L).
"""


def asp_facts() -> str:
    import asp
    out = []
    for t in THEMES:
        out.append(asp.fact("theme", t))
    for b in BIASES:
        out.append(asp.fact("bias", b))
    for m in MISUNDERSTANDINGS:
        out.append(asp.fact("misunderstanding", m))
    for l in LESSONS:
        out.append(asp.fact("lesson", l))
    return "\n".join(out)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    py = {(t, b, m, l) for t in THEMES for b in BIASES for m in MISUNDERSTANDINGS for l in LESSONS}
    model = asp.one_model(asp_program(show="#show valid/4."))
    cl = set(asp.atoms(model, "valid"))
    ok = py == cl
    print("OK: ASP matches Python." if ok else "MISMATCH: ASP and Python differ.")
    return 0 if ok else 1


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: memes={e.memes} attrs={e.attrs}")
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    parts = ["== Story questions =="]
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("")
    parts.append("== World questions ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


def generate(params: StoryParams) -> StorySample:
    return generate_story(params)


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
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "show_asp", None):
        print(asp_program(show="#show valid/4."))
        return
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program(show="#show valid/4."))
        print(sorted(set(asp.atoms(model, "valid"))))
        return

    rng = random.Random(getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31))
    samples = []
    if getattr(args, "all", None):
        for t in THEMES:
            for b in BIASES:
                for m in MISUNDERSTANDINGS:
                    for l in LESSONS:
                        samples.append(generate(StoryParams(t, b, m, l, seed=getattr(args, "seed", None))))
    else:
        for i in range(getattr(args, "n", None)):
            p = resolve_params(args, random.Random(rng.randrange(2**31)))
            p.seed = rng.randrange(2**31)
            samples.append(generate(p))
    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=(f"### variant {i+1}" if len(samples) > 1 else ""))


if __name__ == "__main__":
    main()

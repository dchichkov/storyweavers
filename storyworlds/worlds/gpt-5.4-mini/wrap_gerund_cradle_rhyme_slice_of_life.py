#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/wrap_gerund_cradle_rhyme_slice_of_life.py
==========================================================================

A small slice-of-life story world about a child helping at bedtime.
The domain centers on a soft cradle, a cozy wrap-gerund action, and a
simple rhyming ending that proves the room became calm.

Seed words:
- wrap-gerund
- cradle

Style:
- Slice of life
- Rhyme
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Wrap:
    id: str
    label: str
    phrase: str
    softness: str
    rhyme_line: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Cradle:
    id: str
    label: str
    phrase: str
    sway: str
    quiet: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Song:
    id: str
    label: str
    phrase: str
    line1: str
    line2: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.facts = dict(self.facts)
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["fussy"] < THRESHOLD:
            continue
        sig = ("calm", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["comfort"] += 1
        ent.meters["fussy"] = 0.0
        out.append("__calm__")
    return out


CAUSAL_RULES = [Rule("calm", "social", _r_calm)]


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
        for s in produced:
            world.say(s)
    return produced


def safe_to_wrap(wrap: Wrap, cradle: Cradle) -> bool:
    return "soft" in wrap.tags and "quiet" in cradle.tags


def settle(world: World, child: Entity, baby: Entity, cradle: Cradle, wrap: Wrap, song: Song) -> None:
    child.memes["helpful"] += 1
    baby.memes["sleepy"] += 1
    world.say(
        f"At home in the late afternoon, {child.id} noticed the room getting still. "
        f"The little {cradle.label} waited by the window, and {baby.id} began to fuss."
    )
    world.say(
        f'{child.id} whispered, "I can help," and started {wrap.phrase} around {baby.id} '
        f"with careful hands."
    )
    baby.meters["wrapped"] += 1
    child.meters["care"] += 1
    propagate(world, narrate=False)
    world.say(
        f"The {wrap.label} felt {wrap.softness}, and the {cradle.label} answered with a gentle {cradle.sway}."
    )
    world.say(
        f"Then {child.id} hummed a soft rhyme: {song.line1} {song.line2}"
    )
    baby.meters["asleep"] += 1
    baby.memes["peace"] += 1
    child.memes["pride"] += 1
    world.say(
        f"At last, {baby.id} lay quiet in the {cradle.label}, and {child.id} smiled at the tidy little scene."
    )
    world.say(
        f"It was a small home moment, warm and bright: wrap the night, cradle tight."
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: a child, a cradle, and a soothing rhyme.")
    ap.add_argument("--wrap", choices=WRAPS)
    ap.add_argument("--cradle", choices=CRADLES)
    ap.add_argument("--song", choices=SONGS)
    ap.add_argument("--child", choices=CHILD_NAMES)
    ap.add_argument("--baby", choices=BABY_NAMES)
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for wid, w in WRAPS.items():
        for cid, c in CRADLES.items():
            for sid, s in SONGS.items():
                if safe_to_wrap(w, c) and "soft" in w.tags and "gentle" in s.tags:
                    combos.append((wid, cid, sid))
    return combos


@dataclass
@dataclass
class StoryParams:
    wrap: str
    cradle: str
    song: str
    child: str
    baby: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


WRAPS = {
    "blanket": Wrap("blanket", "blanket", "a soft blanket", "soft and warm", "Soft and warm, like a moonlit treat", {"soft", "warm"}),
    "shawl": Wrap("shawl", "shawl", "a knitted shawl", "soft and light", "Soft and light, like a sleepy night", {"soft", "light"}),
    "sling": Wrap("sling", "sling", "a snug sling", "gentle and snug", "Gentle and snug, like a lullaby hug", {"soft", "snug"}),
}

CRADLES = {
    "wood": Cradle("wood", "cradle", "the wooden cradle", "little sway", "quiet", {"quiet", "steady"}),
    "basket": Cradle("basket", "basket cradle", "the basket cradle", "tiny rock", "quiet", {"quiet", "steady"}),
    "basin": Cradle("basin", "bassinet", "the bassinet", "easy rock", "quiet", {"quiet", "steady"}),
}

SONGS = {
    "moon": Song("moon", "moon song", "a moon song", "Soft moon, slow tune", "Hush now, little one, rest in the light", {"gentle", "rhyme"}),
    "rain": Song("rain", "rain song", "a rain song", "Soft rain, small refrain", "Dreams will drift in the night so bright", {"gentle", "rhyme"}),
    "nest": Song("nest", "nest song", "a nest song", "Warm nest, gentle rest", "Sleep will come on its silver kite", {"gentle", "rhyme"}),
}

CHILD_NAMES = ["Mia", "Lena", "Noah", "Eli", "Ava", "Maya"]
BABY_NAMES = ["Nina", "Ollie", "June", "Theo", "Bean", "Ruby"]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.wrap is None or c[0] == args.wrap)
              and (args.cradle is None or c[1] == args.cradle)
              and (args.song is None or c[2] == args.song)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    wrap, cradle, song = rng.choice(sorted(combos))
    child = args.child or rng.choice(CHILD_NAMES)
    baby = args.baby or rng.choice(BABY_NAMES)
    return StoryParams(wrap, cradle, song, child, baby)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a slice-of-life bedtime story that includes the word "{f["wrap_phrase"]}" and a cradle.',
        f'Tell a gentle rhyming story where {f["child"]} helps {f["baby"]} settle by using {f["wrap_phrase"]} near the cradle.',
        f'Write a small family story with a calm ending, soft words, and a rhyme about a cradle and a wrap.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"What did {f['child']} do to help?",
            answer=f"{f['child']} started {f['wrap_phrase']} around {f['baby']} and then hummed a little rhyme. That made the room quieter and helped the baby settle."
        ),
        QAItem(
            question=f"Where did {f['baby']} end up?",
            answer=f"{f['baby']} ended up resting in the cradle, calm and wrapped up safely. The cradle kept the little one snug while the song finished."
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer="The fussing turned into quiet. The baby grew sleepy, the child felt proud, and the home ended with a warm, peaceful bedtime picture."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cradle?",
            answer="A cradle is a small bed for a baby. It can rock gently to help a baby rest."
        ),
        QAItem(
            question="What does it mean to wrap something?",
            answer="To wrap something means to cover it with cloth or another soft layer. People wrap babies to keep them cozy and snug."
        ),
        QAItem(
            question="Why do lullabies sound soft?",
            answer="Lullabies sound soft because they are meant to calm a baby. Slow, gentle sounds help the room feel peaceful."
        ),
    ]


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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(W, C, S) :- wrap(W), cradle(C), song(S), soft(W), quiet(C), gentle(S).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for wid, w in WRAPS.items():
        lines.append(asp.fact("wrap", wid))
        if "soft" in w.tags:
            lines.append(asp.fact("soft", wid))
    for cid, c in CRADLES.items():
        lines.append(asp.fact("cradle", cid))
        if "quiet" in c.tags:
            lines.append(asp.fact("quiet", cid))
    for sid, s in SONGS.items():
        lines.append(asp.fact("song", sid))
        if "gentle" in s.tags:
            lines.append(asp.fact("gentle", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in ASP parity.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def tell(params: StoryParams) -> World:
    world = World()
    child = world.add(Entity(id=params.child, kind="character", type="child", role="helper", traits=["kind"]))
    baby = world.add(Entity(id=params.baby, kind="character", type="baby", role="comforted", traits=["small"]))
    wrap = WRAPS[params.wrap]
    cradle = CRADLES[params.cradle]
    song = SONGS[params.song]
    world.add(Entity(id=wrap.id, type="thing", label=wrap.label, attrs={"phrase": wrap.phrase}))
    world.add(Entity(id=cradle.id, type="thing", label=cradle.label, attrs={"phrase": cradle.phrase}))
    world.add(Entity(id=song.id, type="thing", label=song.label, attrs={"phrase": song.phrase}))

    world.facts.update(
        child=child.id,
        baby=baby.id,
        wrap_phrase=wrap.phrase,
        cradle_label=cradle.label,
        song_phrase=song.phrase,
    )

    child.memes["care"] += 1
    baby.meters["fussy"] += 1
    settle(world, child, baby, cradle, wrap, song)
    world.facts["outcome"] = "calm"
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (wrap, cradle, song) combos:\n")
        for w, c, s in combos:
            print(f"  {w:8} {c:8} {s}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    seen: set[str] = set()
    i = 0
    while len(samples) < args.n and i < max(50, args.n * 50):
        try:
            params = resolve_params(args, random.Random(base_seed + i))
        except StoryError as err:
            print(err)
            return
        params.seed = base_seed + i
        sample = generate(params)
        if sample.story not in seen:
            seen.add(sample.story)
            samples.append(sample)
        i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        if idx:
            print("\n" + "=" * 70 + "\n")
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {idx + 1}" if len(samples) > 1 else "")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/weirdo_bass_theory_kindness_dialogue_slice_of.py
=================================================================================

A tiny slice-of-life story world about a kid who brings a strange idea to a
quiet afternoon, a bass in a band room, and a theory that sounds odd until
someone answers kindly and the day turns warmer.

Seed words: weirdo, bass, theory
Features: Kindness, Dialogue
Style: Slice of Life
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Place:
    id: str
    label: str
    vibe: str
    supports: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


@dataclass
class Thing:
    id: str
    label: str
    phrase: str
    kind: str
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class PromptTone:
    id: str
    scene: str
    opening: str
    ending: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.memes["hurt"] < THRESHOLD:
            continue
        sig = ("kindness", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["comfort"] += 1
        out.append("__kindness__")
    return out


CAUSAL_RULES = [Rule("kindness", _r_kindness)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def story_can_happen(kind: str, instrument: str) -> bool:
    return kind in INSTRUMENTS and instrument in INSTRUMENTS[kind].supports


def nice_reply_level(trait: str) -> float:
    return 5.0 if trait in {"gentle", "patient", "thoughtful"} else 3.0


def tell(world: World, place: Place, tone: PromptTone, instrument: Thing, speaker: Entity,
         listener: Entity, helper: Entity, trait: str, tempo: str) -> World:
    speaker.memes["curiosity"] += 1
    listener.memes["worry"] += 1
    helper.memes["kindness"] += nice_reply_level(trait)

    world.say(
        f"In the {place.label}, {speaker.id} sat with {listener.id} and "
        f"the little bass on its stand. {tone.opening} "
        f"The room felt ordinary in the best way, like a quiet afternoon with "
        f"sunlight on the floor."
    )
    world.say(
        f'"What if," {speaker.id} said, "my theory is that the bass sounds warmer '
        f'when you play it slower?"'
    )
    world.say(
        f'{listener.id} gave a small smile. "That does not sound weird to me," '
        f'{listener.id} said. "It sounds like something we can try."'
    )

    world.para()
    listener.memes["doubt"] += 1
    if tempo == "slow":
        instrument.meters["warmth"] += 1
        instrument.meters["played"] += 1
        speaker.memes["joy"] += 1
        listener.memes["relief"] += 1
        helper.memes["pride"] += 1
        world.say(
            f'They tried it gently. The bass sounded round and soft, like a song '
            f'that had time to breathe. {speaker.id} grinned and said, '
            f'"See? My theory!"'
        )
        world.say(
            f'{helper.id} nodded kindly. "Maybe your theory was not so strange after '
            f"all," {helper.id} said. "You noticed something real.""
        )
        world.say(
            f'{listener.id} tapped the side of the bass and laughed. "You are a '
            f'weirdo," {listener.id} said, "but in the good way."'
        )
        world.say(
            f"{tone.ending} The bass stayed in the room, glowing quietly with the "
            f"new little idea they had found together."
        )
    else:
        instrument.meters["warmth"] += 0.5
        instrument.meters["played"] += 1
        speaker.memes["uncertain"] += 1
        listener.memes["curiosity"] += 1
        world.say(
            f"They tried the theory, and the bass still sounded good, just a little "
            f"brighter than before. {speaker.id} frowned for a moment."
        )
        world.say(
            f'{helper.id} touched {speaker.id}\'s shoulder and said, '
            f'"You did not waste anyone\'s time. You helped us listen more closely."'
        )
        world.say(
            f'{speaker.id} smiled again. "Thanks," {speaker.id} said. '
            f'"I guess even a weird theory can be useful."'
        )
        world.say(
            f"{tone.ending} The bass hummed on, and the afternoon felt friendly "
            f"again."
        )
    propagate(world, narrate=False)
    return world


TOWNS = {
    "home": Place("home", "living room", "sunlit and calm", {"bass"}),
    "studio": Place("studio", "practice room", "soft and echoey", {"bass"}),
    "basement": Place("basement", "basement room", "quiet and warm", {"bass"}),
}

INSTRUMENTS = {
    "bass": Thing("bass", "bass", "the bass", "instrument", {"bass", "music"}),
}

Tones = {
    "slice": PromptTone("slice", "slice-of-life", "a small ordinary moment", "By the end, the room felt easy again."),
    "after_school": PromptTone("after_school", "after-school", "a weekday afternoon", "The day settled down into a gentle ending."),
    "weekend": PromptTone("weekend", "weekend", "a lazy weekend scene", "The little scene ended with everyone calmer."),
}

PEOPLE = ["Mina", "Ari", "Noah", "Lena", "Tess", "Owen", "Jun", "Iris"]
TRAITS = ["gentle", "patient", "thoughtful", "quiet", "kind"]


@dataclass
class StoryParams:
    place: str
    tone: str
    speaker: str
    listener: str
    helper: str
    trait: str
    tempo: str
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


def valid_combos() -> list[tuple[str, str]]:
    return [(p, t) for p in TOWNS for t in Tones if story_can_happen("bass", "bass")]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld about kindness, dialogue, and a bass theory.")
    ap.add_argument("--place", choices=TOWNS)
    ap.add_argument("--tone", choices=Tones)
    ap.add_argument("--tempo", choices=["slow", "normal"])
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
    if args.tempo and args.tempo not in {"slow", "normal"}:
        raise StoryError("Unsupported tempo.")
    place = args.place or rng.choice(list(TOWNS))
    tone = args.tone or rng.choice(list(Tones))
    tempo = args.tempo or rng.choice(["slow", "normal"])
    speaker, listener, helper = rng.sample(PEOPLE, 3)
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, tone=tone, speaker=speaker, listener=listener, helper=helper, trait=trait, tempo=tempo)


def generate(params: StoryParams) -> StorySample:
    if params.place not in TOWNS:
        raise StoryError("Unknown place.")
    if params.tone not in Tones:
        raise StoryError("Unknown tone.")
    if params.tempo not in {"slow", "normal"}:
        raise StoryError("Unknown tempo.")
    world = World()
    place = TOWNS[params.place]
    tone = Tones[params.tone]
    speaker = world.add(Entity(id=params.speaker, kind="character", type="boy" if params.speaker in {"Noah", "Owen", "Jun"} else "girl"))
    listener = world.add(Entity(id=params.listener, kind="character", type="boy" if params.listener in {"Noah", "Owen", "Jun"} else "girl"))
    helper = world.add(Entity(id=params.helper, kind="character", type="boy" if params.helper in {"Noah", "Owen", "Jun"} else "girl"))
    bass = world.add(Entity(id="bass", kind="thing", type="instrument", label="bass"))
    world.facts.update(place=place, tone=tone, speaker=speaker, listener=listener, helper=helper, bass=bass, params=params)
    world = tell(world, place, tone, bass, speaker, listener, helper, params.trait, params.tempo)
    story = world.render()
    prompts = generation_prompts(world)
    story_qa = [QAItem(q, a) for q, a in story_qa_items(world)]
    world_qa = [QAItem(q, a) for q, a in world_qa_items(world)]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a slice-of-life story that includes the words "weirdo", "bass", and "theory".',
        f"Tell a gentle dialogue-driven story where {f['speaker'].id} shares a strange theory about the bass and someone answers kindly.",
        f"Write a short everyday story in a calm room where a weird-sounding idea becomes a nice moment between friends.",
    ]


def story_qa_items(world: World) -> list[tuple[str, str]]:
    f = world.facts
    speaker = f["speaker"]
    listener = f["listener"]
    helper = f["helper"]
    bass = f["bass"]
    tone = f["tone"]
    if bass.meters["warmth"] >= THRESHOLD:
        return [
            ("What was the weird theory about?", f"{speaker.id} thought the bass might sound warmer when played slower. That idea turned out to be worth trying because the bass really did sound soft and round."),
            ("How did the other person respond?", f"{listener.id} answered kindly and agreed to try it instead of laughing the idea away. That made the moment feel safe and friendly."),
            ("How did the story end?", f"It ended with the bass sounding good and everyone feeling calmer. The ordinary room became a warmer place because the idea was met with kindness."),
        ]
    return [
        ("What was the weird theory about?", f"{speaker.id} thought the bass might sound different if it was played more slowly. The others listened, which kept the moment gentle instead of embarrassing."),
        ("How did the helper react?", f"{helper.id} spoke kindly and told {speaker.id} the idea was worth hearing. That helped the room stay calm and respectful."),
        ("How did the story end?", f"It ended with a friendly conversation and a quieter feeling in the room. Even if the theory was not perfect, the kindness made the day better."),
    ]


def world_qa_items(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a bass?", "A bass is a low instrument in a band or practice room. It makes deeper sounds that can feel warm or steady."),
        ("What is a theory?", "A theory is an idea someone uses to explain or predict something. Sometimes theories are right, and sometimes they just help people test a thought."),
        ("What does kindness mean?", "Kindness means being gentle and caring with other people. A kind reply can make an odd idea feel safe to share."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("\n== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("\n== (3) World-knowledge questions ==")
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
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,T) :- place(P), tone(T).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([asp.fact("place", p) for p in TOWNS] + [asp.fact("tone", t) for t in Tones])


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    from contextlib import redirect_stdout
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH between ASP and Python valid_combos().")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(0)))
        _ = sample.story
        with redirect_stdout(io.StringIO()):
            emit(sample)
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    if rc == 0:
        print("OK: ASP parity and generation smoke test passed.")
    return rc


CURATED = [
    StoryParams(place="home", tone="slice", speaker="Mina", listener="Ari", helper="Owen", trait="gentle", tempo="slow"),
    StoryParams(place="studio", tone="after_school", speaker="Noah", listener="Lena", helper="Iris", trait="thoughtful", tempo="slow"),
    StoryParams(place="basement", tone="weekend", speaker="Tess", listener="Jun", helper="Mina", trait="patient", tempo="normal"),
]


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
        print(asp_program("", "#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("valid combinations:")
        for p, t in asp_valid_combos():
            print(p, t)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

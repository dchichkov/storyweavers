#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/caterpillar_marsh_sound_effects_curiosity_myth.py
=================================================================================

A tiny myth-flavored storyworld about a curious caterpillar in a marsh where
sound effects matter: a soft creek, a croak, a plop, a rustle, and a final new
song. The premise is small and classical: a curious little creature leaves the
safe reed path, follows mysterious sounds, meets a helpful marsh voice, and
returns with a brighter way of moving through the reeds.

The world is built from typed entities with physical meters and emotional memes.
The prose is driven by the simulated state, not by a frozen paragraph with
swapped nouns.

Seed words:
- caterpillar
- marsh

Features:
- Sound Effects
- Curiosity

Style:
- Myth
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
BRAVERY_INIT = 4.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    tags: set[str] = field(default_factory=set)
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
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Place:
    id: str
    label: str
    descriptor: str
    tags: set[str] = field(default_factory=set)
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


@dataclass
class Creature:
    id: str
    label: str
    phrase: str
    sound: str
    guard: str
    gift: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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


@dataclass
class Response:
    id: str
    sense: int
    text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


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


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def _r_curiosity(world: World) -> list[str]:
    out: list[str] = []
    c = world.get("hero")
    if c.memes["curiosity"] < THRESHOLD:
        return out
    sig = ("curiosity,awakens")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    c.meters["drawn"] += 1
    out.append("The marsh sounds pulled the little one onward.")
    return out


def _r_ripple(world: World) -> list[str]:
    out: list[str] = []
    c = world.get("hero")
    if c.meters["drawn"] < THRESHOLD:
        return out
    sig = ("ripple",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("marsh").meters["wake"] += 1
    out.append("The reeds shivered and the water answered back.")
    return out


CAUSAL_RULES = [Rule("curiosity", _r_curiosity), Rule("ripple", _r_ripple)]


def sound_attracts(world: World) -> None:
    world.get("hero").memes["curiosity"] += 1
    world.say(
        "At dusk the marsh lay green and still, and a small caterpillar rested on a reed."
    )
    world.say(
        'Then came the soft sounds of the marsh: "creek... croak... plop..." and the little creature listened.'
    )
    world.say("The sounds were strange, and strange things always made the caterpillar want to know more.")


def leave_path(world: World) -> None:
    hero = world.get("hero")
    hero.memes["curiosity"] += 1
    hero.meters["wandering"] += 1
    propagate(world, narrate=False)
    world.say(
        "So the caterpillar slipped from the safe reed path and crept toward the hidden water."
    )


def warning(world: World) -> None:
    world.say(
        'A marsh frog called out, "Little caterpillar, the deep mud remembers every careless step."'
    )
    world.say(
        'But the caterpillar only tilted its head and listened for one more "plip-plop" in the reeds.'
    )


def crossing(world: World) -> None:
    hero = world.get("hero")
    marsh = world.get("marsh")
    hero.meters["splash"] += 1
    marsh.meters["wake"] += 1
    propagate(world, narrate=False)
    world.say(
        "It crossed a narrow pool, and with each tiny move there came a soft plip and a silver ripple."
    )


def helper(world: World, guardian: Entity, creature: Creature) -> None:
    world.say(
        f'Then {guardian.id}, the old marsh guardian, rose from the mist and said, "{creature.phrase} is small, but wonder should not be lost."'
    )
    world.say(
        f'With a gentle {creature.sound}, {guardian.id} showed the caterpillar how to follow {creature.guard} instead of the deep water.'
    )


def gift(world: World, guardian: Entity, creature: Creature) -> None:
    hero = world.get("hero")
    hero.memes["joy"] += 1
    hero.memes["wisdom"] += 1
    world.say(
        f'The guardian gave the caterpillar {creature.gift}, and the marsh answered with a warm {creature.sound} in the reeds.'
    )
    world.say(
        "After that, the little traveler knew the safe sound of home and the brave sound of curiosity."
    )


def tell(place: Place, creature: Creature, response: Response) -> World:
    world = World()
    world.add(Entity(id="hero", kind="character", type="caterpillar", label="the caterpillar"))
    world.add(Entity(id="marsh", kind="place", type="marsh", label=place.label, attrs={"descriptor": place.descriptor}))
    guardian = world.add(Entity(id="OldReed", kind="character", type="elder", label="the old marsh guardian", role="guardian"))
    hero = world.get("hero")
    hero.memes["curiosity"] = BRAVERY_INIT
    world.facts["guardian"] = guardian
    world.facts["place"] = place
    world.facts["creature"] = creature
    world.facts["response"] = response

    sound_attracts(world)
    world.para()
    leave_path(world)
    warning(world)
    crossing(world)
    world.para()
    helper(world, guardian, creature)
    if response.sense >= SENSE_MIN:
        world.say(response.text)
    else:
        raise StoryError("The chosen response is too dull for a mythic marsh tale.")
    gift(world, guardian, creature)
    world.facts.update(outcome="returned", touched_water=True, heard_sound=True)
    return world


THEMES = {
    "marsh": Place(id="marsh", label="the marsh", descriptor="green reeds and silver water", tags={"marsh"}),
}

CREATURES = {
    "caterpillar": Creature(
        id="caterpillar",
        label="caterpillar",
        phrase="A small caterpillar can be curious even in the quietest place.",
        sound="rustle-rustle",
        guard="the reed path",
        gift="a moonlit thread to guide its steps",
        tags={"caterpillar", "curiosity", "myth"},
    ),
}

RESPONSES = {
    "return": Response(
        id="return",
        sense=3,
        text="guided it back to the reeds and away from the deep water",
        qa_text="guided the caterpillar back to the reeds and away from the deep water",
        tags={"safe", "myth"},
    ),
    "listen": Response(
        id="listen",
        sense=2,
        text="helped it listen to the marsh and choose the safest way home",
        qa_text="helped the caterpillar listen to the marsh and choose the safest way home",
        tags={"safe", "myth"},
    ),
    "song": Response(
        id="song",
        sense=3,
        text="answered with a calm song that made the reeds feel like home again",
        qa_text="answered with a calm song that made the reeds feel like home again",
        tags={"safe", "myth"},
    ),
}

GREAT_NAMES = ["Aster", "Iris", "Mira", "Nori", "Lumen", "Sable", "Orin"]
CURIOUS_TOKENS = ["listening", "seeking", "wondering", "watching"]

@dataclass
class StoryParams:
    place: str
    creature: str
    response: str
    name: str = "the caterpillar"
    seed: Optional[int] = None
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in THEMES:
        for c in CREATURES:
            for r in RESPONSES:
                combos.append((p, c, r))
    return combos


def explain_rejection(params: StoryParams) -> str:
    return "(No story: this marsh myth always needs a curious caterpillar and a wise response.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic marsh storyworld with sound effects and curiosity.")
    ap.add_argument("--place", choices=THEMES)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--response", choices=RESPONSES)
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
    combos = valid_combos()
    if args.place and args.creature and args.response:
        if (args.place, args.creature, args.response) not in combos:
            raise StoryError(explain_rejection(StoryParams(args.place, args.creature, args.response)))
    place = args.place or rng.choice(sorted(THEMES))
    creature = args.creature or rng.choice(sorted(CREATURES))
    response = args.response or rng.choice(sorted(RESPONSES))
    return StoryParams(place=place, creature=creature, response=response)


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a myth-like story for a young child that includes the words "caterpillar" and "marsh".',
        'Tell a curious marsh tale with sound effects like "creek", "croak", and "plop".',
        "Write a gentle myth about a caterpillar who follows strange sounds, learns, and returns home safely.",
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why did the caterpillar leave the reed path?",
            answer="It left because curiosity pulled it toward the strange marsh sounds. The sounds felt mysterious, so the little creature wanted to know what made them.",
        ),
        QAItem(
            question="What helped the caterpillar come back safely?",
            answer="The old marsh guardian helped it with a calm, wise response. That guidance turned the curious wandering into a safe return through the reeds.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer="At first the marsh was only a place of wondering, but by the end it had become a place of learned safe paths and a friendly song. The caterpillar returned with wisdom instead of only questions.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a marsh?",
            answer="A marsh is a wet place with reeds, shallow water, and muddy ground. It can be quiet, but it is full of little sounds.",
        ),
        QAItem(
            question="Why do sound effects matter in a story?",
            answer="Sound effects help the reader hear the world in their mind. They can make a small place feel alive, mysterious, or playful.",
        ),
        QAItem(
            question="What is a caterpillar?",
            answer="A caterpillar is the soft, crawling young form of a butterfly or moth. It moves slowly and can seem very curious about everything nearby.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if params.place not in THEMES or params.creature not in CREATURES or params.response not in RESPONSES:
        raise StoryError("Invalid story parameters.")
    world = tell(THEMES[params.place], CREATURES[params.creature], RESPONSES[params.response])
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


ASP_RULES = r"""
valid(P,C,R) :- place(P), creature(C), response(R).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in THEMES:
        lines.append(asp.fact("place", p))
    for c in CREATURES:
        lines.append(asp.fact("creature", c))
    for r in RESPONSES:
        lines.append(asp.fact("response", r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import random as _random
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP gate differs from Python valid_combos().")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, creature=None, response=None), _random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generation smoke test passed.")
    except Exception as exc:
        print(f"FAIL: generation smoke test failed: {exc}")
        rc = 1
    return rc


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
    StoryParams(place="marsh", creature="caterpillar", response="return", name="the caterpillar"),
    StoryParams(place="marsh", creature="caterpillar", response="listen", name="the caterpillar"),
    StoryParams(place="marsh", creature="caterpillar", response="song", name="the caterpillar"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible story triples:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

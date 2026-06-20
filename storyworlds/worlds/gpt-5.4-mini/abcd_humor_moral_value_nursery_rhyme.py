#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/abcd_humor_moral_value_nursery_rhyme.py
========================================================================

A tiny storyworld in a nursery-rhyme style about a little alphabet parade.
The world is built around four typed little letter-characters: a, b, c, and d.
Each one has a physical "meters" track for simple stage objects and an emotional
"memes" track for the moral/humor arc.

Base seed idea
--------------
A child tries to race ahead in an alphabet rhyme, bumps the letters out of
order, and learns to slow down and share the song. The ending is cheerful and
silly: the letters clap in the right order and the rhyme becomes a little
march.

This script keeps the domain small and constraint-checked:
- the story always includes abcd,
- the humor comes from a playful stumble or comic correction,
- the moral value comes from patience, sharing, and taking turns,
- the prose aims for a nursery-rhyme feel without freezing into a template.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/abcd_humor_moral_value_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4-mini/abcd_humor_moral_value_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4-mini/abcd_humor_moral_value_nursery_rhyme.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4-mini/abcd_humor_moral_value_nursery_rhyme.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"   # character | thing
    type: str = "thing"
    label: str = ""
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def n(self, key: str) -> float:
        return self.memes.get(key, 0.0)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Stage:
    name: str
    props: list[str]
    sound: str
    rhyme_hint: str
    mood: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class Beat:
    id: str
    label: str
    action: str
    stumble: str
    fix: str
    moral: str
    humor: str
    order: int

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        c.facts = copy.deepcopy(self.facts)
        c.fired = set(self.fired)
        return c

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


STAGES = {
    "nursery": Stage(
        name="a snug nursery",
        props=["a low rug", "a little drum", "a toy train", "a paper star"],
        sound="the room was soft with tap-tap feet and tiny giggles",
        rhyme_hint="its own small song",
        mood="cozy",
    ),
    "garden": Stage(
        name="a sunny garden",
        props=["a red kite", "a teacup of daisies", "a wooden bench", "a bright pail"],
        sound="the breeze played a merry whisper through the leaves",
        rhyme_hint="a breeze-time tune",
        mood="bright",
    ),
}

BEATS = {
    "rush": Beat(
        id="rush",
        label="rush ahead",
        action="rushed ahead to begin the rhyme",
        stumble="tripped over the beat and made a silly little sneeze",
        fix="slowed down and let the others join in",
        moral="taking turns makes the song kinder and sweeter",
        humor="the tiny sneeze sounded like a toy trumpet",
        order=1,
    ),
    "snatch": Beat(
        id="snatch",
        label="snatch the verse",
        action="snatched the verse and sang too loud",
        stumble="tangled the words into a funny knot",
        fix="passed the line around like a warm bun",
        moral="sharing the tune lets everyone shine",
        humor="the knot came out sounding like a hiccup",
        order=2,
    ),
    "skip": Beat(
        id="skip",
        label="skip the line",
        action="skipped a letter and hopped too fast",
        stumble="left the rhyme with a missing shoe",
        fix="went back and put the missing letter in place",
        moral="it is good to mend what you muddle",
        humor="the rhyme looked lopsided like a sleepy cat",
        order=3,
    ),
}

LETTERS = ["a", "b", "c", "d"]
NAMES = ["A", "B", "C", "D"]


@dataclass
@dataclass
class StoryParams:
    stage: str
    beat: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


def valid_combos() -> list[tuple[str, str]]:
    return [(s, b) for s in STAGES for b in BEATS]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme storyworld about abcd, humor, and a moral.")
    ap.add_argument("--stage", choices=STAGES)
    ap.add_argument("--beat", choices=BEATS)
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


def asp_facts() -> str:
    import asp
    lines = [asp.fact("stage", s) for s in STAGES]
    lines += [asp.fact("beat", b) for b in BEATS]
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, B) :- stage(S), beat(B).
#show valid/2.
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def _pick_name(rng: random.Random, idx: int) -> str:
    return NAMES[idx]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.stage is None or c[0] == args.stage)
              and (args.beat is None or c[1] == args.beat)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    stage, beat = rng.choice(sorted(combos))
    return StoryParams(stage=stage, beat=beat)


def _intro(world: World, stage: Stage) -> None:
    world.say(
        f"On a {stage.mood} morning in {stage.name}, {stage.sound}. "
        f"On the floor sat {', '.join(stage.props[:-1])}, and {stage.props[-1]}."
    )
    world.say("And there, in a tidy row, stood a, b, c, and d, ready for a rhyme.")


def _tempt(world: World, beat: Beat) -> None:
    world.say(
        f"Little a looked at the line and decided to {beat.action}. "
        f"Little b blinked, little c frowned, and little d tried not to giggle."
    )


def _stumble(world: World, beat: Beat) -> None:
    world.get("a").memes["bold"] += 1
    world.get("b").memes["worry"] += 1
    world.get("c").memes["worry"] += 1
    world.get("d").memes["laugh"] += 1
    world.say(
        f"But oh dear, {beat.stumble}. {beat.humor.capitalize()}, and the rhyme "
        f"wobbled like jelly on a spoon."
    )


def _fix(world: World, beat: Beat) -> None:
    for lid in LETTERS:
        world.get(lid).memes["joy"] += 1
        world.get(lid).memes["kindness"] += 1
    world.say(
        f"Then little b said, \"Let us slow and share.\" Little c nodded, and little d "
        f"tapped the beat. So a chose to {beat.fix}."
    )
    world.say(
        f"The letters lined up again, and the song went round and round. "
        f"{beat.moral.capitalize()}."
    )


def _ending(world: World, stage: Stage) -> None:
    world.say(
        f"In the end, a, b, c, and d sang together in a neat little row. "
        f"The room felt {stage.mood}, and even the paper star seemed to clap."
    )


def tell(stage: Stage, beat: Beat) -> World:
    world = World()
    for idx, lid in enumerate(LETTERS):
        world.add(Entity(id=lid, kind="character", type="letter", label=lid, role="letter"))
        world.get(lid).meters["order"] = float(idx + 1)
    world.facts["stage"] = stage
    world.facts["beat"] = beat
    _intro(world, stage)
    world.para()
    _tempt(world, beat)
    _stumble(world, beat)
    world.para()
    _fix(world, beat)
    _ending(world, stage)
    world.facts.update(done=True, joy=sum(world.get(x).n("joy") for x in LETTERS))
    return world


def generation_prompts(world: World) -> list[str]:
    stage: Stage = world.facts["stage"]
    beat: Beat = world.facts["beat"]
    return [
        f'Write a nursery-rhyme story for a small child that uses the letters a, b, c, and d in {stage.name}.',
        f"Tell a funny story where little a {beat.label}s, the others help, and the moral is about sharing and taking turns.",
        f'Create a short rhyme-like story that includes "abcd" and ends with everyone singing together.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    beat: Beat = world.facts["beat"]
    stage: Stage = world.facts["stage"]
    return [
        ("Who are the story's main characters?",
         "The story is about the four little letters a, b, c, and d. They are the ones who start the rhyme and finish it together."),
        ("What went wrong at first?",
         f"Little a tried to {beat.action}, but that made the rhyme wobble. The others had to pause because the song lost its neat little order."),
        ("How did they fix it?",
         f"Little b suggested they slow down and share the line, little c agreed, and little d kept the beat. Then a chose to {beat.fix}, and the rhyme came back in order."),
        ("What moral did the story teach?",
         f"It taught that {beat.moral}. The happy ending shows that a song sounds better when everyone gets a turn."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is an alphabet?",
         "An alphabet is a set of letters used to make words. In this story, a, b, c, and d are the first four letters."),
        ("What is a rhyme?",
         "A rhyme is a poem or song with a beat and words that sound nice together. Nursery rhymes often feel bouncy and easy to remember."),
        ("Why do children like funny mistakes in stories?",
         "Funny mistakes can be silly without being scary. They make the story playful, and then the fix feels warm and satisfying."),
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:2} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("nursery", "rush"),
    StoryParams("nursery", "snatch"),
    StoryParams("garden", "skip"),
]


def outcome_of(params: StoryParams) -> str:
    return "shared-song"


def asp_verify() -> int:
    import asp
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
        sample = generate(CURATED[0])
        if not sample.story.strip():
            return 1
        print("OK: smoke test story generation succeeded.")
        return 0
    print("MISMATCH in ASP gate.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(STAGES[params.stage], BEATS[params.beat])
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program(show="#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:\n")
        for s, b in asp_valid_combos():
            print(f"  {s:8} {b}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
        header = "### nursery rhyme" if args.all else (f"### variant {i + 1}" if len(samples) > 1 else "")
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

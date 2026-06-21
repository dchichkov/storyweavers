#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/shea_hill_snipper_lesson_learned_mystery_to.py
================================================================================

A tiny comedy storyworld about Shea, a hill, and Snipper.

Premise:
- Shea climbs a hill with a curious heart.
- Something funny and slightly mysterious has gone missing or gotten snipped.
- Curiosity helps Shea solve the mystery.
- The lesson learned is that guessing is not the same as knowing.

This script follows the Storyweavers contract:
- stdlib only for the story engine
- imports storyworlds/results eagerly
- imports storyworlds/asp lazily inside ASP helpers
- provides StoryParams, build_parser, resolve_params, generate, emit, main
- supports --all, -n, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- includes a Python validity gate and matching inline ASP rules
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
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
    slope: str
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
class Mystery:
    id: str
    clue: str
    cause: str
    reveal: str
    lesson: str
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
class StoryParams:
    hill: str
    mystery: str
    clue: str
    sidekick: str
    parent: str
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
        clone.facts = dict(self.facts)
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


def _r_confusion(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters["confused"] >= THRESHOLD:
            sig = ("confusion", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            e.memes["worry"] += 1
            out.append(f"{e.id} looked puzzled.")
    return out


def _r_relief(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters["solved"] >= THRESHOLD:
            sig = ("relief", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            e.memes["joy"] += 1
            out.append(f"{e.id} felt relieved.")
    return out


CAUSAL_RULES = [Rule("confusion", _r_confusion), Rule("relief", _r_relief)]


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


def clue_at_risk(mystery: Mystery, clue: str) -> bool:
    return clue == mystery.clue


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for hill in HILLS:
        for myst in MYSTERIES:
            for clue in CLUES:
                if clue_at_risk(MYSTERIES[myst], clue):
                    combos.append((hill, myst, clue))
    return combos


def explain_rejection(mystery: Mystery, clue: str) -> str:
    return (
        f"(No story: the clue '{clue}' does not fit this mystery. "
        f"Pick the clue that actually matches what happened.)"
    )


def best_reveal(mystery: Mystery) -> str:
    return mystery.reveal


def tell(hill: Place, mystery: Mystery, clue: str, sidekick: str, parent: str) -> World:
    world = World()
    shea = world.add(Entity(id="Shea", kind="character", type="girl", role="hero"))
    buddy = world.add(Entity(id=sidekick, kind="character", type="thing", role="helper"))
    grownup = world.add(Entity(id=parent, kind="character", type="mother", role="parent"))
    hill_ent = world.add(Entity(id="hill", type="place", label=hill.label, tags=set(hill.tags)))
    snipper = world.add(Entity(id="Snipper", kind="character", type="thing", role="mystery-maker"))

    shea.memes["curiosity"] = 3
    buddy.memes["curiosity"] = 2
    world.facts["hill_ent"] = hill_ent
    world.facts["snipper"] = snipper
    world.facts["mystery"] = mystery
    world.facts["clue"] = clue

    world.say(
        f"Shea climbed the hill with {buddy.id} on a bright afternoon. "
        f"The hill looked normal, which is exactly the kind of thing that invites a mystery."
    )
    world.say(
        f"Then Shea found the clue: {clue}. 'Huh,' Shea said. 'That is either a clue or a very dramatic accident.'"
    )
    world.para()
    shea.meters["confused"] += 1
    buddy.meters["confused"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{buddy.id} guessed a wild answer right away, but Shea decided to look closer instead of laughing too soon."
    )
    world.say(
        f"At the top of the hill, little marks led behind a rock. There sat Snipper, busy as a squirrel with a secret."
    )
    world.para()
    world.say(
        f"Snipper showed what really happened: {mystery.cause}. "
        f"That was why the clue looked so strange."
    )
    world.say(
        f"Shea nodded. '{mystery.lesson}' Shea said, and everyone on the hill agreed."
    )
    world.say(
        f"Then Snipper fixed the mess and made it funny again by revealing the answer: {best_reveal(mystery)}."
    )
    shea.meters["solved"] += 1
    buddy.meters["solved"] += 1
    propagate(world, narrate=False)
    world.say(
        f"By the end, Shea was smiling at the hill, the clue, and Snipper all at once. "
        f"The mystery was solved, and curiosity had done its good work."
    )

    world.facts.update(
        shea=shea,
        buddy=buddy,
        grownup=grownup,
        hill=hill,
        mystery=mystery,
        clue=clue,
        outcome="solved",
    )
    return world


HILLS = {
    "green": Place(id="green", label="a green hill", slope="gentle", tags={"hill", "green"}),
    "windy": Place(id="windy", label="a windy hill", slope="steep", tags={"hill", "wind"}),
    "sunny": Place(id="sunny", label="a sunny hill", slope="round", tags={"hill", "sun"}),
}

MYSTERIES = {
    "snip_ribbon": Mystery(
        id="snip_ribbon",
        clue="a ribbon with a tiny snip",
        cause="Snipper had nibbled the ribbon by mistake while chasing a bug",
        reveal="it was only a snack-sized snip, not a treasure thief",
        lesson="Maybe I should look before I leap to a guess.",
        tags={"snipper", "curiosity", "lesson"},
    ),
    "missing_bell": Mystery(
        id="missing_bell",
        clue="a missing bell by the gate",
        cause="Snipper had moved the bell to hang it from a little stick",
        reveal="the bell was not missing at all; it had been relocated for play",
        lesson="A mystery is easier when I ask what changed instead of assuming the worst.",
        tags={"snipper", "curiosity", "lesson"},
    ),
    "muddy_prints": Mystery(
        id="muddy_prints",
        clue="muddy prints in a zigzag line",
        cause="Snipper chased a beetle through the wet grass and left tiny prints",
        reveal="the prints belonged to Snipper, who was trying to help and got muddy",
        lesson="Curiosity is kinder when it is patient.",
        tags={"snipper", "curiosity", "lesson"},
    ),
}

CLUES = {
    "a ribbon with a tiny snip": "a ribbon with a tiny snip",
    "a missing bell by the gate": "a missing bell by the gate",
    "muddy prints in a zigzag line": "muddy prints in a zigzag line",
}

SIDEKICKS = ["Milo", "June", "Pip", "Bea"]
PARENTS = ["Mom", "Dad"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a funny mystery story for a young child about Shea on a hill, with the word "snipper".',
        f"Tell a comedy story where Shea notices {f['clue']} and solves the mystery by being curious instead of jumping to conclusions.",
        f'Write a gentle story with a lesson learned about curiosity, using the words Shea, hill, and snipper.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    mystery: Mystery = f["mystery"]
    qa = [
        ("Who is the story about?",
         "It is about Shea, a sidekick, and Snipper on a hill, with a funny mystery to solve."),
        ("What did Shea find?",
         f"Shea found {f['clue']}. That clue turned out to be connected to Snipper's silly mistake."),
        ("Why did Shea keep looking?",
         f"Shea stayed curious because the clue did not make sense at first. Curiosity helped Shea find the real answer instead of guessing too fast."),
        ("What did Shea learn?",
         f"{mystery.lesson} The story shows that a calm question can solve a mystery better than a wild guess."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is curiosity?",
         "Curiosity is the feeling that makes you want to look, ask, and learn more about something new."),
        ("What is a mystery?",
         "A mystery is something puzzling that does not make sense right away, so you have to look for clues."),
        ("Why do clues matter?",
         "Clues matter because they help you figure out what really happened without guessing in the dark."),
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for hid in HILLS:
        lines.append(asp.fact("hill", hid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("clue", mid, m.clue))
    for clue in CLUES:
        lines.append(asp.fact("known_clue", clue))
    return "\n".join(lines)


ASP_RULES = r"""
match(M) :- mystery(M), clue(M, C), known_clue(C).
valid(H, M, C) :- hill(H), mystery(M), clue(M, C), match(M).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    from contextlib import redirect_stdout

    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid_combos() vs ASP.")
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        _ = format_qa(sample)
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    try:
        from contextlib import nullcontext
        with redirect_stdout(io.StringIO()):
            emit(sample, trace=False, qa=False)
    except Exception as exc:
        rc = 1
        print(f"EMIT SMOKE TEST FAILED: {exc}")
    if rc == 0:
        print("OK: ASP parity and story generation smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy mystery storyworld on a hill with Shea and Snipper.")
    ap.add_argument("--hill", choices=HILLS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--sidekick", choices=SIDEKICKS)
    ap.add_argument("--parent", choices=PARENTS)
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
    if args.clue and args.mystery:
        myst = MYSTERIES[args.mystery]
        if not clue_at_risk(myst, args.clue):
            raise StoryError(explain_rejection(myst, args.clue))
    combos = [c for c in valid_combos()
              if (args.hill is None or c[0] == args.hill)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.clue is None or c[2] == args.clue)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    hill, mystery, clue = rng.choice(sorted(combos))
    sidekick = args.sidekick or rng.choice(SIDEKICKS)
    parent = args.parent or rng.choice(PARENTS)
    return StoryParams(hill=hill, mystery=mystery, clue=clue, sidekick=sidekick, parent=parent)


def generate(params: StoryParams) -> StorySample:
    if params.hill not in HILLS or params.mystery not in MYSTERIES or params.clue not in CLUES:
        raise StoryError("invalid params")
    world = tell(HILLS[params.hill], MYSTERIES[params.mystery], params.clue, params.sidekick, params.parent)
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


CURATED = [
    StoryParams(hill="green", mystery="snip_ribbon", clue="a ribbon with a tiny snip", sidekick="Milo", parent="Mom"),
    StoryParams(hill="windy", mystery="missing_bell", clue="a missing bell by the gate", sidekick="June", parent="Dad"),
    StoryParams(hill="sunny", mystery="muddy_prints", clue="muddy prints in a zigzag line", sidekick="Pip", parent="Mom"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible stories:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

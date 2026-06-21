#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/rumble_flit_penguin_suspense_mystery_to_solve.py
=================================================================================

A small comedy-leaning suspense storyworld about a child, a penguin, and a
mystery rumble that turns out to be something funny, safe, and surprising.

Seed words: rumble, flit, penguin
Features: Suspense, Mystery to Solve
Style: Comedy
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
class Setting:
    id: str
    place: str
    dark_spot: str
    allowed: set[str] = field(default_factory=set)
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
class Mystery:
    id: str
    source: str
    clue: str
    reveal: str
    noise: str
    safe: bool = True
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
class Move:
    id: str
    sense: int
    power: int
    text: str
    fail: str
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
    setting: str
    mystery: str
    move: str
    child: str
    child_gender: str
    penguin_name: str
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


def _r_rumble(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters["rumble"] < THRESHOLD:
            continue
        sig = ("rumble", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("child").memes["suspense"] += 1
        world.get("penguin").memes["alert"] += 1
        out.append("__rumble__")
    return out


def _r_clue(world: World) -> list[str]:
    if world.get("penguin").meters["found_clue"] < THRESHOLD:
        return []
    sig = ("clue",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("child").memes["hope"] += 1
    return ["__clue__"]


CAUSAL_RULES = [_r_rumble, _r_clue]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def _search(world: World, child: Entity, penguin: Entity, mystery: Mystery) -> None:
    world.say(
        f"On a quiet evening, {child.id} and {penguin.id} heard a low rumble from "
        f"{world.facts['setting'].dark_spot}. The penguin tried to look serious, "
        f"but it only made the whole thing feel sillier."
    )
    world.say(
        f'"Did you hear that?" {child.id} whispered. "The room sounds like a sleepy dragon."'
    )
    child.memes["curiosity"] += 1
    penguin.memes["curiosity"] += 1


def _warn(world: World, child: Entity, penguin: Entity, mystery: Mystery) -> None:
    world.say(
        f'{penguin.id} flitted left, then right, then did a tiny hop. '
        f'"That rumble is coming from somewhere in the dark," {penguin.id} said. '
        f'"We should solve the mystery before it solves us."'
    )
    world.say(
        f'{child.id} nodded, trying very hard not to giggle. "Brave plan," '
        f"{child.id} said. The suspense felt big, even though the penguin's feet "
        f"were making the least dramatic squeaks in the world."
    )


def _reveal(world: World, child: Entity, penguin: Entity, mystery: Mystery) -> None:
    world.get("penguin").meters["found_clue"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{penguin.id} flitted under the table and found the clue: {mystery.clue}. '
        f'The rumble was not a monster at all.'
    )
    world.say(
        f'The final reveal was {mystery.reveal}. {child.id} blinked, then laughed so hard '
        f"that even the penguin had to lean on the chair."
    )


def _finish(world: World, child: Entity, penguin: Entity, mystery: Mystery, move: Move) -> None:
    child.memes["joy"] += 1
    penguin.memes["joy"] += 1
    world.say(
        f'With a grin, {child.id} used the answer they had found and {move.text}. '
        f'The room settled down at once.'
    )
    world.say(
        f'The mystery was solved, the suspense melted away, and {penguin.id} gave one '
        f"tiny proud bow, as if it had planned the whole adventure on purpose."
    )


def _fail(world: World, child: Entity, penguin: Entity, mystery: Mystery, move: Move) -> None:
    world.say(
        f'{child.id} tried to rush the fix, but {move.fail}. The rumble only got louder, '
        f'and both of them had to freeze and think again.'
    )
    world.say(
        f'In the end, they still solved it, because the mystery was too funny to stay hidden for long.'
    )


SETTINGS = {
    "kitchen": Setting("kitchen", "the kitchen", "the pantry door", {"search", "listen"}),
    "laundry": Setting("laundry", "the laundry room", "the basket corner", {"search", "listen"}),
    "hallway": Setting("hallway", "the hallway", "the coat nook", {"search", "listen"}),
}

MYSTERIES = {
    "snack": Mystery("snack", "a rolling snack tin", "a tin of cookies", "a toppled cookie box", "rattle", True, {"cookie", "snack"}),
    "toy": Mystery("toy", "a toy train", "a toy train car", "a toy train track", "clack", True, {"toy", "train"}),
    "laundry": Mystery("laundry", "a laundry basket", "a sock mountain", "a basket full of socks", "thump", True, {"laundry", "sock"}),
}

MOVES = {
    "peek": Move("peek", 3, 2, "peeked behind the curtain and nudged the basket with a careful finger", "peeked too fast and only startled a dust bunny", {"search"}),
    "listen": Move("listen", 3, 3, "listened until the sound pointed the way and then opened the door", "listened, but the rumble was hiding behind a hiccuping chair", {"listen"}),
    "follow": Move("follow", 2, 2, "followed the tiny sound until it led them to the answer", "followed the wrong squeak and ended up at a mop", {"search"}),
}

GIRL_NAMES = ["Mina", "Lily", "Zoe", "Ava", "Nora"]
BOY_NAMES = ["Theo", "Milo", "Ben", "Finn", "Leo"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for m in MYSTERIES:
            for move in MOVES.values():
                if move.sense >= 2:
                    out.append((s, m, move.id))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy suspense storyworld: rumble, flit, penguin.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--move", choices=MOVES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--penguin", dest="penguin_name")
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.move is None or c[2] == args.move)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery, move = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    penguin_name = args.penguin_name or "Pip"
    return StoryParams(setting=setting, mystery=mystery, move=move, child=name, child_gender=gender, penguin_name=penguin_name)


def tell(params: StoryParams) -> World:
    if params.setting not in SETTINGS or params.mystery not in MYSTERIES or params.move not in MOVES:
        raise StoryError("Invalid parameters.")
    world = World()
    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    move = MOVES[params.move]
    child = world.add(Entity(id=params.child, kind="character", type=params.child_gender, role="child"))
    penguin = world.add(Entity(id=params.penguin_name, kind="character", type="penguin", role="helper", plural=False))
    room = world.add(Entity(id="room", type="room", label=setting.place))
    world.facts.update(setting=setting, mystery=mystery, move=move)
    child.memes["curiosity"] = 1
    penguin.memes["curiosity"] = 1

    world.say(
        f"{child.id} and {penguin.id} were exploring {setting.place}. Everything was quiet, "
        f"until a low rumble came from {setting.dark_spot}."
    )
    world.say(
        f"{child.id} and {penguin.id} looked at each other. The penguin did a tiny flit across the floor, "
        f"as if its feet had remembered a secret."
    )
    world.para()
    _search(world, child, penguin, mystery)
    _warn(world, child, penguin, mystery)
    room.meters["rumble"] += 1
    propagate(world, narrate=False)
    world.para()
    _reveal(world, child, penguin, mystery)
    if move.sense >= 3:
        _finish(world, child, penguin, mystery, move)
    else:
        _fail(world, child, penguin, mystery, move)
    world.facts.update(child=child, penguin=penguin, outcome="solved")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a comedy suspense story for a 3-to-5-year-old that includes the words "rumble", "flit", and "penguin".',
        f"Tell a funny mystery story where {f['child'].id} and a penguin named {f['penguin'].id} hear a rumble in {f['setting'].place} and solve it.",
        f"Write a child-friendly suspense story with a penguin helper, a mysterious rumble, and a silly reveal.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, penguin, mystery, setting = f["child"], f["penguin"], f["mystery"], f["setting"]
    return [
        QAItem(question="Who is the story about?", answer=f"It is about {child.id} and {penguin.id}, who team up to solve a funny mystery in {setting.place}."),
        QAItem(question="What strange sound did they hear?", answer=f"They heard a rumble from {setting.dark_spot}. That sound made the story suspenseful, but it also turned out to be harmless and funny."),
        QAItem(question="What was the mystery really?", answer=f"It was really {mystery.reveal}. The clue led them to the answer, so the scary sound became a silly surprise instead."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does it mean to flit?", answer="To flit means to move quickly and lightly, like a tiny bird or a busy penguin taking small fast steps."),
        QAItem(question="What is suspense in a story?", answer="Suspense is the feeling of wondering what will happen next. It makes a story exciting because the answer is hidden for a little while."),
        QAItem(question="Why are penguins funny in stories?", answer="Penguins are funny because they waddle, flit, and look very serious even when they are doing something silly."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
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
        out.append(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
    out.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(out)


CURATED = [
    StoryParams(setting="kitchen", mystery="snack", move="peek", child="Mina", child_gender="girl", penguin_name="Pip"),
    StoryParams(setting="laundry", mystery="laundry", move="listen", child="Theo", child_gender="boy", penguin_name="Pebble"),
    StoryParams(setting="hallway", mystery="toy", move="follow", child="Lily", child_gender="girl", penguin_name="Wink"),
]


def explain_rejection() -> str:
    return "(No story: that combination does not make a good, safe mystery.)"


ASP_RULES = r"""
valid(S, M, Move) :- setting(S), mystery(M), move(Move).
solved :- valid(_,_,_).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery", m))
    for mv in MOVES:
        lines.append(asp.fact("move", mv))
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
        print(f"OK: ASP matches Python valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("Mismatch between ASP and Python valid_combos().")
    try:
        sample = generate(CURATED[0])
        assert sample.story
        print("OK: generation smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"Smoke test failed: {e}")
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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

    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

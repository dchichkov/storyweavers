#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/argumentative_school_library_magic_surprise_whodunit.py
======================================================================================

A tiny school-library whodunit storyworld: an argumentative child, a little magic,
a surprise clue, and a gentle mystery that ends with the book case being put
right.

The world is modeled as a small causal simulation with typed entities, physical
meters, and emotional memes. Stories are generated from world state, not by
swapping nouns in a frozen paragraph.

Run:
    python storyworlds/worlds/gpt-5.4-mini/argumentative_school_library_magic_surprise_whodunit.py
    python storyworlds/worlds/gpt-5.4-mini/argumentative_school_library_magic_surprise_whodunit.py --all
    python storyworlds/worlds/gpt-5.4-mini/argumentative_school_library_magic_surprise_whodunit.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/argumentative_school_library_magic_surprise_whodunit.py --verify
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
SENSE_MIN = 2
MAGIC_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    owner: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "librarian"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
class Place:
    id: str
    label: str
    hush: str
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
class Suspect:
    id: str
    label: str
    clue: str
    hidden: str
    magic: int = 0
    surprise: int = 0
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
class Tool:
    id: str
    label: str
    phrase: str
    effect: str
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
        w.facts = copy.deepcopy(self.facts)
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


def _r_magic_reveal(world: World) -> list[str]:
    out: list[str] = []
    for suspect in world.facts.get("suspects", []):
        if suspect.magic < MAGIC_MIN:
            continue
        sig = ("reveal", suspect.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        clue = suspect.clue
        world.get("case").memes["mystery"] += 1
        out.append(f"A tiny shimmer stirred around {clue}.")
    return out


def _r_surprise(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("surprise_seen"):
        return out
    if world.get("case").meters["tampered"] < THRESHOLD:
        return out
    sig = ("surprise", "case")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.facts["surprise_seen"] = True
    for kid in world.facts.get("kids", []):
        kid.memes["shock"] += 1
    out.append("__surprise__")
    return out


CAUSAL_RULES = [Rule("magic_reveal", _r_magic_reveal), Rule("surprise", _r_surprise)]


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


def _do_tamper(world: World, case: Entity, narrate: bool = True) -> None:
    case.meters["tampered"] += 1
    propagate(world, narrate=narrate)


def predict(world: World, case_id: str, suspect: Suspect) -> dict:
    sim = world.copy()
    _do_tamper(sim, sim.get(case_id), narrate=False)
    return {"surprise": sim.get(case_id).meters["tampered"] >= THRESHOLD,
            "mystery": sim.get("case").memes["mystery"]}


def intro(world: World, kid: Entity, librarian: Entity, place: Place) -> None:
    world.say(
        f"In the quiet school library, {kid.id} was feeling argumentative, "
        f"and {librarian.id} kept a careful eye on the tall shelves."
    )
    world.say(
        f"{kid.id} loved the hush of {place.label}, but today the silence felt full "
        f"of a secret."
    )


def mystery_start(world: World, kid: Entity, place: Place) -> None:
    world.say(
        f"Then a strange thing happened: the story corner went all crooked, and "
        f"one little display looked like it had been touched by invisible fingers."
    )
    world.say(
        f"{kid.id} pointed at the clue and said, \"Something here is not right.\""
    )


def argue(world: World, kid: Entity, friend: Entity) -> None:
    kid.memes["stubborn"] += 1
    friend.memes["annoyed"] += 1
    world.say(
        f"\"You are wrong,\" {kid.id} said, getting more argumentative by the minute. "
        f"\"I know what happened.\""
    )
    world.say(
        f"{friend.id} frowned, because the case was a mystery and nobody liked a loud guess."
    )


def suspect_magic(world: World, kid: Entity, suspect: Suspect) -> None:
    kid.memes["curious"] += 1
    world.say(
        f"{kid.id} noticed a tiny magical sparkle near {suspect.clue}, as if the clue "
        f"wanted to be seen."
    )
    world.say(
        f"It was a surprise, but not a scary one; it was the kind that makes a detective "
        f"look twice."
    )


def tamper(world: World, kid: Entity, case: Entity) -> None:
    _do_tamper(world, case)
    world.say(
        f"{kid.id} leaned closer and touched the clue display. At once, the little card "
        f"slipped, and the hidden thing under it showed itself."
    )
    world.say(
        "The whole library seemed to hold its breath."
    )


def reveal(world: World, librarian: Entity, suspect: Suspect, tool: Tool) -> None:
    case = world.get("case")
    case.meters["solved"] += 1
    librarian.memes["calm"] += 1
    world.say(
        f"{librarian.id} came over with a {tool.phrase} and smiled. "
        f"\"The clue was {suspect.hidden},\" {librarian.pronoun()} said. "
        f"\"That was the surprise.\""
    )
    world.say(
        f"With {tool.effect}, the display was set right again, and the library's hush "
        f"felt cozy instead of mysterious."
    )


def lesson(world: World, kid: Entity, librarian: Entity, suspect: Suspect) -> None:
    kid.memes["humility"] += 1
    kid.memes["joy"] += 1
    world.say(
        f"{kid.id} blinked, then laughed a little. \"I thought it was something huge,\" "
        f"{kid.id} said. \"It was just {suspect.hidden}.\""
    )
    world.say(
        f"{librarian.id} nodded. \"The best detectives listen first and guess second,\" "
        f"{librarian.pronoun()} said softly."
    )
    world.say(
        f"So {kid.id} put the clue back where it belonged, and the school library "
        f"settled into a neat, safe quiet."
    )


def tell(place: Place, suspect: Suspect, tool: Tool,
         kid_name: str = "Maya", kid_gender: str = "girl",
         librarian_name: str = "Ms. Reed", librarian_gender: str = "librarian",
         friend_name: str = "Noah", friend_gender: str = "boy") -> World:
    world = World()
    kid = world.add(Entity(id=kid_name, kind="character", type=kid_gender, role="detective"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="witness"))
    librarian = world.add(Entity(id=librarian_name, kind="character", type=librarian_gender, role="adult", label="the librarian"))
    case = world.add(Entity(id="case", kind="thing", type="case", label="the mystery display"))

    kid.memes["curiosity"] += 1
    friend.memes["curiosity"] += 1
    world.facts["kids"] = [kid, friend]
    world.facts["suspects"] = [suspect]

    intro(world, kid, librarian, place)
    world.para()
    mystery_start(world, kid, place)
    argue(world, kid, friend)
    suspect_magic(world, kid, suspect)
    world.para()
    tamper(world, kid, case)
    reveal(world, librarian, suspect, tool)
    lesson(world, kid, librarian, suspect)

    world.facts.update(
        kid=kid,
        friend=friend,
        librarian=librarian,
        place=place,
        suspect=suspect,
        tool=tool,
        case=case,
        outcome="solved",
    )
    return world


PLACES = {
    "school_library": Place(
        id="school_library",
        label="the school library",
        hush="quiet shelves and soft carpet",
        tags={"school", "library"},
    )
}

SUSPECTS = {
    "bookmark": Suspect(
        id="bookmark",
        label="a missing bookmark",
        clue="the bottom of a book stack",
        hidden="a bright bookmark stuck inside the wrong book",
        magic=1,
        surprise=2,
        tags={"magic", "surprise"},
    ),
    "note": Suspect(
        id="note",
        label="a secret note",
        clue="the edge of the reading rug",
        hidden="a folded note from the librarian",
        magic=1,
        surprise=2,
        tags={"magic", "surprise"},
    ),
    "key": Suspect(
        id="key",
        label="a tiny silver key",
        clue="behind the atlas",
        hidden="the key to the lost cabinet",
        magic=2,
        surprise=2,
        tags={"magic", "surprise"},
    ),
}

TOOLS = {
    "lamp": Tool(
        id="lamp",
        label="reading lamp",
        phrase="reading lamp",
        effect="its warm light",
        tags={"library"},
    ),
    "sticker": Tool(
        id="sticker",
        label="star sticker",
        phrase="star sticker",
        effect="a shiny sticker marked the spot",
        tags={"surprise"},
    ),
    "label": Tool(
        id="label",
        label="new label",
        phrase="new label",
        effect="the shelf card was labeled again",
        tags={"school", "library"},
    ),
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for s in SUSPECTS:
            for t in TOOLS:
                combos.append((p, s, t))
    return combos


@dataclass
class StoryParams:
    place: str
    suspect: str
    tool: str
    kid_name: str
    kid_gender: str
    librarian_name: str
    librarian_gender: str
    friend_name: str
    friend_gender: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A whodunit storyworld set in a school library.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--tool", choices=TOOLS)
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
              if (args.place is None or c[0] == args.place)
              and (args.suspect is None or c[1] == args.suspect)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, suspect, tool = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        suspect=suspect,
        tool=tool,
        kid_name=rng.choice(["Maya", "Lily", "Zoe", "Ava"]),
        kid_gender="girl",
        librarian_name=rng.choice(["Ms. Reed", "Mr. Page"]),
        librarian_gender="librarian",
        friend_name=rng.choice(["Noah", "Eli", "Ben"]),
        friend_gender="boy",
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a school-library whodunit for a young child with the word "argumentative" in it.',
        f"Tell a mystery story set in {f['place'].label} where {f['kid'].id} gets argumentative, "
        f"but a magical surprise clue helps solve the problem.",
        f"Write a gentle detective story with magic and surprise where {f['librarian'].id} helps "
        f"set a library clue right again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    kid, librarian, suspect, tool = f["kid"], f["librarian"], f["suspect"], f["tool"]
    return [
        QAItem(
            question="Where does the story take place?",
            answer="It takes place in the school library, where the shelves are quiet and full of books.",
        ),
        QAItem(
            question=f"Why was {kid.id} acting argumentative?",
            answer=f"{kid.id} thought the clue meant something big and kept pushing the idea. "
                   f"That made the guessing noisy, but it also showed how much {kid.id} wanted to solve the mystery.",
        ),
        QAItem(
            question="How was the mystery solved?",
            answer=f"{librarian.id} used the {tool.phrase} to set the display right and explained that the clue was "
                   f"{suspect.hidden}. The surprise turned into a simple answer once everyone looked carefully.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a library?",
            answer="A library is a quiet place with books where people read, study, and borrow stories.",
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues, asks careful questions, and tries to figure out what really happened.",
        ),
        QAItem(
            question="What does magic mean in a story?",
            answer="Magic means something surprising and impossible in real life happens in the story.",
        ),
        QAItem(
            question="Why can surprise be useful in a mystery?",
            answer="Surprise can hide the answer until the right moment, which makes the clue feel exciting and worth noticing.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
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
        if e.label:
            bits.append(f"label={e.label!r}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="school_library", suspect="bookmark", tool="lamp",
                kid_name="Maya", kid_gender="girl", librarian_name="Ms. Reed",
                librarian_gender="librarian", friend_name="Noah", friend_gender="boy"),
    StoryParams(place="school_library", suspect="note", tool="label",
                kid_name="Ava", kid_gender="girl", librarian_name="Mr. Page",
                librarian_gender="librarian", friend_name="Eli", friend_gender="boy"),
    StoryParams(place="school_library", suspect="key", tool="sticker",
                kid_name="Lily", kid_gender="girl", librarian_name="Ms. Reed",
                librarian_gender="librarian", friend_name="Ben", friend_gender="boy"),
]


def explain_combo() -> str:
    return "(No story: the school-library mystery needs a clue, a little magic, and a surprise.)"


ASP_RULES = r"""
has_combo(P,S,T) :- place(P), suspect(S), tool(T).
#show has_combo/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for s in SUSPECTS:
        lines.append(asp.fact("suspect", s))
    for t in TOOLS:
        lines.append(asp.fact("tool", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show has_combo/3."))
    return sorted(set(asp.atoms(model, "has_combo")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP and Python valid_combos differ.")
    else:
        print(f"OK: ASP matches Python valid_combos() ({len(valid_combos())} combos).")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(1)))
        _ = sample.story
        print("OK: smoke-test generation succeeded.")
    except Exception as exc:
        print(f"FAIL: generation smoke test crashed: {exc}")
        return 1
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.suspect not in SUSPECTS or params.tool not in TOOLS:
        raise StoryError("(Invalid params for this storyworld.)")
    place = PLACES[params.place]
    suspect = SUSPECTS[params.suspect]
    tool = TOOLS[params.tool]
    world = tell(place, suspect, tool, params.kid_name, params.kid_gender,
                 params.librarian_name, params.librarian_gender,
                 params.friend_name, params.friend_gender)
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
        print(asp_program("#show has_combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for combo in asp_valid_combos():
            print(combo)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

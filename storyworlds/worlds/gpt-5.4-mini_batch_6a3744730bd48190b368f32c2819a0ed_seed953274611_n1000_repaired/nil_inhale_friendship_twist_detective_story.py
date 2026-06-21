#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/nil_inhale_friendship_twist_detective_story.py
===============================================================================

A tiny detective storyworld with friendship and a twist.

Premise:
- Two friends investigate a puzzling "nil" clue.
- One friend can inhale a scent trail and notice the truth.
- The twist is that the seeming theft is not a theft at all: the missing item was
  moved for a harmless reason, and the note "nil" means there was nothing taken.

The simulation uses typed entities with physical meters and emotional memes, a
small causal engine, a reasonableness gate, and an inline ASP twin.
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
class Clue:
    id: str
    label: str
    kind: str
    scent: str
    note: str
    is_nil: bool = False
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
class Room:
    id: str
    label: str
    place: str
    hidden: str
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
class Action:
    id: str
    sense: int
    power: int
    text: str
    fail: str
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
    tag: str
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


def _r_suspicion(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes["suspicion"] < THRESHOLD:
            continue
        sig = ("suspicion", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["worry"] += 1
        out.append("")
    return out


def _r_truth(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("found_nil") and world.facts.get("scent_match"):
        sig = ("truth", "reveal")
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("case").meters["solved"] += 1
            out.append("")
    return out


CAUSAL_RULES = [Rule("suspicion", "mind", _r_suspicion), Rule("truth", "mind", _r_truth)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def scent_at_risk(clue: Clue, room: Room) -> bool:
    return clue.is_nil or clue.kind == room.hidden


def sensible_actions() -> list[Action]:
    return [a for a in ACTIONS.values() if a.sense >= SENSE_MIN]


def reasonableness_gate() -> bool:
    return any(a.sense >= SENSE_MIN for a in ACTIONS.values())


def predict(world: World, clue_id: str) -> dict:
    sim = world.copy()
    simulate_search(sim, sim.get("detective"), sim.get("friend"), CLUES[clue_id], narrate=False)
    return {
        "solved": sim.get("case").meters["solved"] >= THRESHOLD,
        "found_nil": sim.facts.get("found_nil", False),
    }


def setup(world: World, det: Entity, friend: Entity, room: Room, clue: Clue) -> None:
    det.memes["curiosity"] += 1
    friend.memes["trust"] += 1
    world.say(
        f"{det.id} and {friend.id} were two friends on a detective case. "
        f"They stood in {room.place}, where a little mystery had begun."
    )
    world.say(
        f"A card on the table said {clue.note}. That odd word made the room feel quiet."
    )


def inspect(world: World, det: Entity, clue: Clue, room: Room) -> None:
    det.memes["focus"] += 1
    world.say(
        f"{det.id} picked up the clue and read it again. It said {clue.note}."
    )
    if clue.is_nil:
        world.say(
            f'"nil," {det.id} whispered. "That means nothing taken. Something else is going on."'
        )


def inhale(world: World, friend: Entity, clue: Clue) -> None:
    friend.memes["attention"] += 1
    world.say(
        f"{friend.id} leaned close and took a careful inhale. {friend.pronoun().capitalize()} caught "
        f"{clue.scent}."
    )


def reveal(world: World, det: Entity, friend: Entity, room: Room, clue: Clue) -> None:
    world.facts["found_nil"] = clue.is_nil
    if clue.scent == "fresh bread":
        world.facts["scent_match"] = True
    world.say(
        f"Then the twist arrived: the missing cookie was not stolen at all. "
        f"It had been moved to the windowsill so it could cool in the breeze."
    )
    world.say(
        f"{friend.id} smiled, and {det.id} laughed too. Their friendship turned the puzzle into a small, happy surprise."
    )


def ending(world: World, det: Entity, friend: Entity, room: Room) -> None:
    world.get("case").meters["solved"] = 1
    det.memes["relief"] += 1
    friend.memes["relief"] += 1
    world.say(
        f"In the end, the case was solved, the note that said nil made sense, and the friends left the room together."
    )
    world.say(
        f"The cookie cooled on the sill, and the two detectives walked out side by side, still friends."
    )


def simulate_search(world: World, det: Entity, friend: Entity, clue: Clue, narrate: bool = True) -> None:
    setup(world, det, friend, world.get("roomcfg"), clue)
    world.para()
    inspect(world, det, clue, world.get("roomcfg"))
    inhale(world, friend, clue)
    world.para()
    if clue.is_nil:
        reveal(world, det, friend, world.get("roomcfg"), clue)
    ending(world, det, friend, world.get("roomcfg"))
    propagate(world, narrate=narrate)
    world.facts["found_nil"] = clue.is_nil
    world.facts["scent_match"] = clue.scent == "fresh bread"


@dataclass
class StoryParams:
    clue: str
    room: str
    detective: str
    friend: str
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


CLUES = {
    "note_nil": Clue(
        id="note_nil",
        label="a folded note",
        kind="note",
        scent="fresh bread",
        note="nil",
        is_nil=True,
        tags={"nil", "note"},
    ),
    "crumb_note": Clue(
        id="crumb_note",
        label="a crumb-flecked note",
        kind="note",
        scent="fresh bread",
        note="almost nil",
        is_nil=False,
        tags={"note"},
    ),
}

ROOMS = {
    "kitchen": Room(
        id="kitchen",
        label="the kitchen",
        place="the kitchen",
        hidden="note",
        tags={"kitchen"},
    ),
    "study": Room(
        id="study",
        label="the study",
        place="the study",
        hidden="note",
        tags={"study"},
    ),
}

ACTIONS = {
    "inspect": Action(
        id="inspect",
        sense=3,
        power=3,
        text="carefully inspected the clue",
        fail="looked but found nothing",
        qa_text="carefully inspected the clue",
        tags={"look"},
    ),
    "inhaler": Action(
        id="inhaler",
        sense=3,
        power=3,
        text="took a careful inhale to catch the scent",
        fail="tried to sniff too fast and missed it",
        qa_text="took a careful inhale and caught the scent",
        tags={"inhale", "scent"},
    ),
    "rush": Action(
        id="rush",
        sense=1,
        power=1,
        text="rushed the case too quickly",
        fail="rushed and misunderstood the clue",
        qa_text="rushed the case too quickly",
        tags={"rush"},
    ),
}

NAMES = ["Nina", "Milo", "Ada", "Theo", "June", "Omar"]


def valid_combos() -> list[tuple[str, str]]:
    return [(c, r) for c in CLUES for r in ROOMS if scent_at_risk(CLUES[c], ROOMS[r]) and reasonableness_gate()]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny detective storyworld about nil, inhale, friendship, and a twist.")
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--detective")
    ap.add_argument("--friend")
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
    combos = [(c, r) for c, r in valid_combos()
              if (args.clue is None or c == args.clue)
              and (args.room is None or r == args.room)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    clue, room = rng.choice(sorted(combos))
    detective = args.detective or rng.choice(NAMES)
    friend = args.friend or rng.choice([n for n in NAMES if n != detective])
    return StoryParams(clue=clue, room=room, detective=detective, friend=friend)


def generate(params: StoryParams) -> StorySample:
    if params.clue not in CLUES or params.room not in ROOMS:
        raise StoryError("Invalid clue or room.")
    world = World()
    det = world.add(Entity(id=params.detective, kind="character", type="girl"))
    fri = world.add(Entity(id=params.friend, kind="character", type="boy"))
    case = world.add(Entity(id="case", type="case", label="the case"))
    room = world.add(Entity(id="roomcfg", type="room", label=ROOMS[params.room].place))
    clue = CLUES[params.clue]
    world.facts["case"] = case
    world.facts["roomcfg"] = room
    world.facts["clue"] = clue
    simulate_search(world, det, fri, clue)
    story = world.render()
    prompts = [
        "Write a short detective story about two friends, a nil clue, and a twist.",
        "Tell a friendship mystery where one child takes an inhale and notices the real answer.",
        "Write a child-friendly detective story that includes the words nil and inhale.",
    ]
    story_qa = [
        QAItem(
            question="What did the note say?",
            answer="The note said nil. That meant there was nothing stolen, so the detectives had to look for a different explanation.",
        ),
        QAItem(
            question="How did the friend help solve the case?",
            answer="The friend took a careful inhale and noticed the scent of fresh bread. That clue pointed to a harmless reason for the missing cookie.",
        ),
        QAItem(
            question="What was the twist?",
            answer="The twist was that nobody had taken the cookie. It had only been moved to the windowsill to cool, so the mystery was a mix-up, not a theft.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What does inhale mean?",
            answer="Inhale means to breathe in. People inhale air, and they can also inhale a smell to notice what is nearby.",
        ),
        QAItem(
            question="What does nil mean?",
            answer="Nil means nothing or zero. In a note, it can mean that there is no missing item or no amount at all.",
        ),
        QAItem(
            question="Why are friends useful in a mystery?",
            answer="Friends can notice different clues and help each other stay calm. Working together makes it easier to solve a puzzle kindly.",
        ),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(clue_nil, room) :- clue(clue_nil), room(room).
sensible(action) :- action(action), sense(action,S), sense_min(M), S >= M.
outcome(solved) :- clue_nil, inhale, friendship.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for rid in ROOMS:
        lines.append(asp.fact("room", rid))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("sense", aid, a.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show sensible/1."))
    return sorted(a for (a,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set((c, r) for c, r in valid_combos()):
        print("MISMATCH in valid combos.")
        rc = 1
    if set(asp_sensible()) != {a for a, v in ACTIONS.items() if v.sense >= SENSE_MIN}:
        print("MISMATCH in sensible actions.")
        rc = 1
    try:
        sample = generate(StoryParams(clue="note_nil", room="kitchen", detective="Nina", friend="Milo"))
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as e:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    print("OK: verify passed.")
    return rc


CURATED = [
    StoryParams(clue="note_nil", room="kitchen", detective="Nina", friend="Milo"),
    StoryParams(clue="note_nil", room="study", detective="Ada", friend="Theo"),
]


def explain_rejection() -> str:
    return "(No story: this tiny detective world only makes sense when nil clues lead to a friendly twist.)"


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("sensible actions:", ", ".join(asp_sensible()))
        for c, r in asp_valid_combos():
            print(c, r)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

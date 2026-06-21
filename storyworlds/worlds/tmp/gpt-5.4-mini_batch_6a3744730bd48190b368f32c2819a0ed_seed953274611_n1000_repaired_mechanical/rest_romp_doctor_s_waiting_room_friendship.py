#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/rest_romp_doctor_s_waiting_room_friendship.py
==============================================================================

A tiny comedy storyworld in a doctor's waiting room.

Premise:
- Two friends try to keep quiet and rest, but a romp with clinic toys, chairs,
  and a rubber dinosaur goes a little too lively.
- A moral-value beat matters: they choose kindness, patience, and honesty when
  they notice someone else needs the quiet seat more.
- The ending proves what changed: the room settles, friendship grows, and the
  children leave with a funny little lesson about rest versus romp.

This script follows the shared Storyweavers contract:
- stdlib only for the story engine
- eager import of storyworlds/results.py
- lazy import of storyworlds/asp.py inside ASP helpers
- StoryParams, build_parser, resolve_params, generate, emit, main
- --verify runs ASP parity plus a generate smoke test
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
QUIET_MIN = 2.0


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
        female = {"girl", "mother", "mom", "woman", "nurse"}
        male = {"boy", "father", "dad", "man", "doctor"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "doctor": "doctor", "nurse": "nurse"}.get(self.type, self.type)
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
    cozy: bool
    seats: int
    quiet_bonus: float
    toy_shelf: bool
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
class Toy:
    id: str
    label: str
    noun: str
    bouncy: bool
    noisy: bool
    safe: bool
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
class Choice:
    id: str
    kind: str
    text: str
    moral: int
    quiet: int
    reset: int
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

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


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


def _r_noise(world: World) -> list[str]:
    out: list[str] = []
    if world.get("room").meters["noise"] < THRESHOLD:
        return out
    if ("noise",) in world.fired:
        return out
    world.fired.add(("noise",))
    world.get("room").meters["busy"] += 1
    for kid in world.characters():
        kid.memes["buzz"] += 1
    out.append("__noise__")
    return out


def _r_rest(world: World) -> list[str]:
    if world.get("room").meters["calm"] < THRESHOLD:
        return []
    if ("rest",) in world.fired:
        return []
    world.fired.add(("rest",))
    world.get("room").meters["quiet"] += 1
    for kid in world.characters():
        kid.memes["relief"] += 1
    return ["The room settled into a quieter, softer hum."]


CAUSAL_RULES = [Rule("noise", "comic", _r_noise), Rule("rest", "comic", _r_rest)]


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


def room_is_reasonable(place: Place) -> bool:
    return place.cozy and place.seats >= 2


def toy_is_reasonable(toy: Toy) -> bool:
    return toy.safe


def choice_is_reasonable(choice: Choice) -> bool:
    return choice.moral >= 2


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for p in PLACES:
        if not room_is_reasonable(PLACES[p]):
            continue
        for t in TOYS:
            if not toy_is_reasonable(TOYS[t]):
                continue
            for c in CHOICES:
                if choice_is_reasonable(CHOICES[c]):
                    out.append((p, t, c))
    return out


def predict(world: World, toy_id: str, choice_id: str) -> dict:
    sim = world.copy()
    _play(sim, sim.get("a"), sim.get("b"), TOYS[toy_id], CHOICES[choice_id], narrate=False)
    return {
        "noise": sim.get("room").meters["noise"],
        "calm": sim.get("room").meters["calm"],
    }


def _play(world: World, a: Entity, b: Entity, toy: Toy, choice: Choice, narrate: bool = True) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.get("room").meters["noise"] += 1
    world.get("room").meters["restlessness"] += 1
    propagate(world, narrate=narrate)
    world.say(
        f"{a.id} and {b.id} tried to keep their voices down in the doctor's waiting room, "
        f"but {choice.text} with {toy.label} made the minutes wobble like jelly."
    )


def setup(world: World, a: Entity, b: Entity, place: Place) -> None:
    world.say(
        f"On a long afternoon in the doctor's waiting room, {a.id} and {b.id} sat together on {place.label}. "
        f"They were friends, and they were trying very hard to rest."
    )


def romp(world: World, a: Entity, b: Entity, toy: Toy) -> None:
    world.say(
        f"Then {a.id} spotted {toy.noun} by the toy shelf and grinned. "
        f'"Let’s have a little romp," {a.id} whispered, and {b.id} giggled before trying not to giggle.'
    )


def warn(world: World, nurse: Entity, a: Entity, b: Entity, toy: Toy, choice: Choice) -> None:
    pred = predict(world, toy.id, choice.id)
    if pred["noise"] < QUIET_MIN:
        return
    world.facts["predicted_noise"] = pred["noise"]
    world.say(
        f'{nurse.label_word.capitalize()} raised a finger and smiled. '
        f'"You can romp with your feet on the floor, but please keep it small. '
        f"This room needs rest, and someone else is waiting too.""
    )


def adjust(world: World, a: Entity, b: Entity, choice: Choice) -> None:
    a.memes["moral"] += 1
    b.memes["moral"] += 1
    world.say(
        f"{a.id} looked at {b.id}, then at the sleepy people in the chairs. "
        f'"Oh!" {a.id} said. "We should be kind and not turn the room into a parade."'
    )
    if choice.moral >= 3:
        world.say(f"{b.id} nodded. " f'"We can rest first," {b.id} said, "and romp later."')


def resolve(world: World, nurse: Entity, a: Entity, b: Entity) -> None:
    world.get("room").meters["noise"] = 0.0
    world.get("room").meters["calm"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{nurse.label_word.capitalize()} smiled at them both. "
        f'"That is a very good choice," {nurse.pronoun()} said. '
        f'The friends settled into a quiet rest while they waited.'
    )
    world.say(
        f"By the time the doctor called their name, {a.id} and {b.id} were whispering jokes instead of bouncing in their seats."
    )


def tale(place: Place, toy: Toy, choice: Choice, name1: str, name2: str, parent_type: str, nurse_type: str = "nurse") -> World:
    world = World()
    a = world.add(Entity(id=name1, kind="character", type="girl" if name1 in GIRL_NAMES else "boy", role="friend"))
    b = world.add(Entity(id=name2, kind="character", type="girl" if name2 in GIRL_NAMES else "boy", role="friend"))
    nurse = world.add(Entity(id="Nurse", kind="character", type=nurse_type, label="the nurse", role="helper"))
    room = world.add(Entity(id="room", type="room", label=place.label))
    world.facts["place"] = place
    world.facts["toy"] = toy
    world.facts["choice"] = choice
    world.facts["nurse"] = nurse
    setup(world, a, b, place)
    world.para()
    romp(world, a, b, toy)
    warn(world, nurse, a, b, toy, choice)
    adjust(world, a, b, choice)
    world.para()
    resolve(world, nurse, a, b)
    world.facts.update(a=a, b=b, room=room, outcome="calm")
    return world


PLACES = {
    "waiting_room": Place(id="waiting_room", label="the soft blue bench", cozy=True, seats=3, quiet_bonus=2.0, toy_shelf=True, tags={"waiting_room", "quiet"}),
}

TOYS = {
    "dino": Toy(id="dino", label="a rubber dinosaur", noun="the rubber dinosaur", bouncy=True, noisy=True, safe=True, tags={"toy", "comedy"}),
    "book": Toy(id="book", label="a picture book", noun="the picture book", bouncy=False, noisy=False, safe=True, tags={"toy"}),
    "ball": Toy(id="ball", label="a soft ball", noun="the soft ball", bouncy=True, noisy=True, safe=True, tags={"toy", "comedy"}),
}

CHOICES = {
    "tiny_romp": Choice(id="tiny_romp", kind="romp", text="a tiny romp", moral=2, quiet=1, reset=1, tags={"romp"}),
    "rest_first": Choice(id="rest_first", kind="rest", text="a rest-first plan", moral=3, quiet=3, reset=2, tags={"rest", "moral"}),
    "share_book": Choice(id="share_book", kind="rest", text="a gentle page-by-page plan", moral=4, quiet=4, reset=3, tags={"rest", "moral"}),
}

GIRL_NAMES = ["Mia", "Lena", "Nora", "Ivy", "Zoe"]
BOY_NAMES = ["Ben", "Toby", "Max", "Theo", "Sam"]
NAMES = GIRL_NAMES + BOY_NAMES
TRAITS = ["silly", "kind", "patient", "curious"]


@dataclass
class StoryParams:
    place: str
    toy: str
    choice: str
    name1: str
    name2: str
    parent: str
    trait: str
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
    ap = argparse.ArgumentParser(description="Comedy storyworld in a doctor's waiting room.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--toy", choices=TOYS)
    ap.add_argument("--choice", choices=CHOICES)
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if args.place and args.place not in PLACES:
        raise StoryError("Unknown place.")
    if args.toy and not TOYS[args.toy].safe:
        raise StoryError("Unsafe toy.")
    if args.choice and not choice_is_reasonable(CHOICES[args.choice]):
        raise StoryError("That choice is too weak for this storyworld.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.toy is None or c[1] == args.toy)
              and (args.choice is None or c[2] == args.choice)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, toy, choice = rng.choice(sorted(combos))
    n1 = rng.choice(GIRL_NAMES)
    n2 = rng.choice([n for n in BOY_NAMES if n != n1] if n1 in BOY_NAMES else [n for n in NAMES if n != n1])
    return StoryParams(
        place=place,
        toy=toy,
        choice=choice,
        name1=n1,
        name2=n2,
        parent=args.parent or rng.choice(["mother", "father"]),
        trait=rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.toy not in TOYS or params.choice not in CHOICES:
        raise StoryError("Invalid params.")
    world = tale(PLACES[params.place], TOYS[params.toy], CHOICES[params.choice], params.name1, params.name2, params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a funny story in a doctor\'s waiting room that includes the words "rest" and "romp".',
        f"Tell a comedy story about {f['a'].id} and {f['b'].id} learning to rest in a waiting room instead of romping too loudly.",
        "Write a child-friendly moral story about friendship, patience, and a quiet choice in a clinic waiting room.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, b = f["a"], f["b"]
    choice = f["choice"]
    nurse = f["nurse"]
    return [
        ("Who are the story friends?", f"The story is about {a.id} and {b.id}, two friends in the doctor's waiting room."),
        ("What did they want to do?", f"They wanted to romp a little, but they also needed to rest while they waited."),
        ("What moral choice did they make?", f"They chose kindness and patience, because they noticed the room needed quiet and another person needed the bench."),
        ("How did the nurse help?", f"The nurse smiled, reminded them to keep it small, and praised them when they chose the calm, respectful option."),
        ("How did the story end?", f"It ended with a quiet rest, some whispered jokes, and a room that felt calmer than before."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a waiting room?", "A waiting room is a place where people sit until it is their turn to see the doctor."),
        ("Why should people be quiet in a doctor's waiting room?", "Quiet helps people rest, lowers the commotion, and makes the room more comfortable for everyone."),
        ("What does friendship mean?", "Friendship means caring about someone, being kind to them, and making good choices together."),
        ("What is a moral value?", "A moral value is a good rule for how to treat other people, like kindness, honesty, patience, and respect."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id}: meters={meters} memes={memes} role={e.role} type={e.type}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="waiting_room", toy="dino", choice="rest_first", name1="Mia", name2="Ben", parent="mother", trait="kind"),
    StoryParams(place="waiting_room", toy="ball", choice="tiny_romp", name1="Nora", name2="Theo", parent="father", trait="patient"),
    StoryParams(place="waiting_room", toy="book", choice="share_book", name1="Zoe", name2="Max", parent="mother", trait="curious"),
]


ASP_RULES = r"""
valid(P,T,C) :- place(P), toy(T), choice(C), cozy(P), safe(T), moral(C), seats_ok(P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.cozy:
            lines.append(asp.fact("cozy", pid))
        if p.seats >= 2:
            lines.append(asp.fact("seats_ok", pid))
    for tid, t in TOYS.items():
        lines.append(asp.fact("toy", tid))
        if t.safe:
            lines.append(asp.fact("safe", tid))
    for cid, c in CHOICES.items():
        lines.append(asp.fact("choice", cid))
        if c.moral >= 2:
            lines.append(asp.fact("moral", cid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import traceback
    rc = 0
    try:
        if set(asp_valid_combos()) != set(valid_combos()):
            print("MISMATCH: ASP and Python valid combos differ.")
            rc = 1
        sample = generate(CURATED[0])
        if not sample.story.strip():
            print("MISMATCH: empty story.")
            rc = 1
    except Exception:
        traceback.print_exc()
        return 1
    print("OK: ASP parity and generation smoke test passed.")
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for p, t, c in asp_valid_combos():
            print(p, t, c)
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
            except StoryError as e:
                print(e)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

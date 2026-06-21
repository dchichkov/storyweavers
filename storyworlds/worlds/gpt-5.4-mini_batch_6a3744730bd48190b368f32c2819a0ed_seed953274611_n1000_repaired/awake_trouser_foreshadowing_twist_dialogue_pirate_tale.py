#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/awake_trouser_foreshadowing_twist_dialogue_pirate_tale.py
==========================================================================================

A small pirate-tale storyworld built from the seed words "awake" and "trouser",
with foreshadowing, dialogue, and a twist.

Premise:
- A child pirate crew is preparing for a night watch on a small ship.
- One child notices a trouser pocket doing something odd.
- The oddity foreshadows a hidden map and a surprise twist.
- Dialogues drive the turn.
- The ending proves what changed: the crew finds the safe treasure and the
  sleepy lookout ends awake, proud, and not in trouble.

This is a self-contained stdlib script with a Python reasonableness gate, an
inline ASP twin, QA generation from world state, and the standard storyworld CLI.
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

NAMES = ["Mina", "Pip", "Jory", "Tess", "Nell", "Bo", "Kit", "Rory"]
SHIP_NAMES = ["the Gull", "the Little Spray", "the Fox", "the Salt Rabbit"]
PIRATE_TITLES = ["captain", "mate", "lookout", "deckhand"]
TREASURE_TYPES = ["chest", "casket", "box"]
TRINKETS = ["a brass key", "a red bead", "a star map", "a silver compass"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
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
        return self.label or self.id
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
class Ship:
    id: str
    name: str
    hold: str
    deck: str
    night_sound: str
    treasure_room: str
    secret_hiding: str
    breeze: str
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
class Trouser:
    id: str
    label: str
    pocket: str
    clue_phrase: str
    hidden_item: str
    surprising_truth: str
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
class Problem:
    id: str
    label: str
    risk: str
    foreshadow: str
    twist_line: str
    fixed_line: str
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
        clone.facts = copy.deepcopy(self.facts)
        return clone
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


def hazard(problem: Problem, trouser: Trouser) -> bool:
    return "clue" in trouser.tags and "hidden" in problem.tags


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SHIPS:
        for tid in TROUSERS:
            for pid in PROBLEMS:
                if hazard(PROBLEMS[pid], TROUSERS[tid]):
                    combos.append((sid, tid, pid))
    return combos


@dataclass
class StoryParams:
    ship: str
    trouser: str
    problem: str
    hero: str
    hero_gender: str
    mate: str
    mate_gender: str
    captain: str
    captain_gender: str
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


SHIPS = {
    "gull": Ship(
        id="gull",
        name="the Gull",
        hold="the little hold",
        deck="the moonlit deck",
        night_sound="the rigging clicked softly in the wind",
        treasure_room="the chart room",
        secret_hiding="under a loose plank",
        breeze="salt-bright",
        tags={"ship"},
    ),
    "spray": Ship(
        id="spray",
        name="the Little Spray",
        hold="the narrow hold",
        deck="the creaking deck",
        night_sound="the ropes hummed like sleepy cats",
        treasure_room="the lantern nook",
        secret_hiding="behind a hanging sail",
        breeze="foggy",
        tags={"ship"},
    ),
}

TROUSERS = {
    "patch": Trouser(
        id="patch",
        label="patched trouser",
        pocket="the left pocket",
        clue_phrase="a little hard lump in the pocket",
        hidden_item="a folded note",
        surprising_truth="the trouser had swallowed the map half by accident",
        tags={"trouser", "clue", "pocket"},
    ),
    "stripe": Trouser(
        id="stripe",
        label="striped trouser",
        pocket="the right pocket",
        clue_phrase="a crinkly shape at the seam",
        hidden_item="a tiny brass key",
        surprising_truth="the trouser carried the key all along",
        tags={"trouser", "clue", "pocket"},
    ),
}

PROBLEMS = {
    "sleepy_watch": Problem(
        id="sleepy_watch",
        label="a sleepy lookout",
        risk="the night watch might miss the dawn bell",
        foreshadow="The lantern flickered twice, as if it knew a secret.",
        twist_line="The secret was not danger at all.",
        fixed_line="The lookout stayed awake and wide-eyed after the surprise.",
        tags={"foreshadow", "twist", "dialogue", "awake"},
    ),
    "lost_key": Problem(
        id="lost_key",
        label="a lost key",
        risk="the treasure room could not be opened",
        foreshadow="The key-shaped shadow kept poking from the cloth.",
        twist_line="The pocket had not lost the key; it had kept it safe.",
        fixed_line="The crew opened the latch and found a kind surprise inside.",
        tags={"foreshadow", "twist", "dialogue", "awake"},
    ),
}

CURATED = [
    StoryParams(ship="gull", trouser="patch", problem="sleepy_watch", hero="Mina", hero_gender="girl",
                mate="Pip", mate_gender="boy", captain="Rory", captain_gender="boy"),
    StoryParams(ship="spray", trouser="stripe", problem="lost_key", hero="Tess", hero_gender="girl",
                mate="Bo", mate_gender="boy", captain="Nell", captain_gender="girl"),
]


def choose_name(rng: random.Random, gender: str) -> str:
    return rng.choice(NAMES)


def predict(world: World, params: StoryParams) -> dict:
    sim = world.copy()
    sim.get("hero").meters["curious"] += 1
    sim.get("hero").memes["worry"] += 1
    sim.get("trouser").meters["notice"] += 1
    return {
        "notice": sim.get("trouser").meters["notice"],
        "worry": sim.get("hero").memes["worry"],
    }


def setup(world: World, ship: Ship, hero: Entity, mate: Entity, captain: Entity, trouser: Trouser, problem: Problem) -> None:
    hero.memes["joy"] += 1
    mate.memes["joy"] += 1
    captain.memes["calm"] += 1
    world.say(
        f"On the deck of {ship.name}, {hero.id} and {mate.id} listened to {ship.night_sound}. "
        f"{hero.id} was awake when most of the crew had gone quiet."
    )
    world.say(
        f"{hero.id} wore {trouser.label}, and {trouser.clue_phrase} made {mate.id} frown. "
        f"Across the deck, {problem.foreshadow}"
    )


def dialogue(world: World, hero: Entity, mate: Entity, captain: Entity, trouser: Trouser, problem: Problem) -> None:
    hero.memes["curious"] += 1
    mate.memes["watchful"] += 1
    world.say(
        f'"{trouser.label} feels odd," said {hero.id}. "{trouser.pocket} has something in it."'
    )
    world.say(
        f'"Maybe it is only a pebble," said {mate.id}. "{problem.label} is what I worry about."'
    )
    world.say(
        f'"Then let us look before the moon gets high," said {captain.id}. '
        f'"A pirate who stays awake can hear what the night is trying to say."'
    )


def twist(world: World, trouser: Trouser, problem: Problem) -> None:
    world.say(
        f"{problem.twist_line} {trouser.surprising_truth}. When {trouser.label_word if hasattr(trouser, 'label_word') else trouser.label} was turned over, "
        f"{trouser.hidden_item} slipped out with a soft wink."
    )


def resolve(world: World, hero: Entity, mate: Entity, captain: Entity, ship: Ship, trouser: Trouser, problem: Problem) -> None:
    hero.memes["pride"] += 1
    mate.memes["relief"] += 1
    captain.memes["pride"] += 1
    hero.meters["awake"] += 1
    world.say(
        f'"It was here all along!" shouted {mate.id}. {captain.id} laughed and said, '
        f'"That is why we check the pockets before we panic."'
    )
    world.say(
        f"{captain.id} tucked the {trouser.hidden_item} into {ship.secret_hiding}, then gave {hero.id} a nod. "
        f"{problem.fixed_line}"
    )
    world.say(
        f"By morning, {ship.name} smelled of salt and rope, and {hero.id} stood awake and grinning, "
        f"with {trouser.label} flapping at the rail like a tiny flag."
    )


def tell(ship: Ship, trouser: Trouser, problem: Problem, hero: str, hero_gender: str,
         mate: str, mate_gender: str, captain: str, captain_gender: str) -> World:
    world = World()
    h = world.add(Entity(id=hero, kind="character", type=hero_gender, role="hero"))
    m = world.add(Entity(id=mate, kind="character", type=mate_gender, role="mate"))
    c = world.add(Entity(id=captain, kind="character", type=captain_gender, role="captain"))
    world.add(Entity(id="ship", kind="thing", type="ship", label=ship.name))
    world.add(Entity(id="trouser", kind="thing", type="trouser", label=trouser.label, attrs={"pocket": trouser.pocket}))
    world.add(Entity(id="problem", kind="thing", type="problem", label=problem.label))
    setup(world, ship, h, m, c, trouser, problem)
    world.para()
    dialogue(world, h, m, c, trouser, problem)
    world.para()
    twist(world, trouser, problem)
    world.para()
    resolve(world, h, m, c, ship, trouser, problem)
    world.facts.update(ship=ship, trouser=trouser, problem=problem, hero=h, mate=m, captain=c)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a pirate tale for a child that uses the words "awake" and "trouser".',
        f"Tell a short story where {f['hero'].id} is awake on {f['ship'].name} and finds a surprise in a trouser pocket.",
        f"Write a pirate story with dialogue, a foreshadowing clue, and a twist ending about {f['trouser'].label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    ship, trouser, problem = f["ship"], f["trouser"], f["problem"]
    hero, mate, captain = f["hero"], f["mate"], f["captain"]
    return [
        ("Who was awake on the ship?",
         f"{hero.id} was awake on {ship.name}, while the others were still going quiet for the night."),
        ("What clue foreshadowed the twist?",
         f"{trouser.clue_phrase} foreshadowed that something hidden was waiting in {trouser.pocket}. "
         f"It hinted that the pocket was important before the surprise was revealed."),
        ("What was the twist?",
         f"The trouser did not hide trouble; it hid a surprise that solved {problem.label}. "
         f"The thing inside turned out to be useful instead of scary."),
        ("What did the captain say about checking pockets?",
         f"{captain.id} said a pirate should look in the pockets before panicking. "
         f"That advice helped the crew find the truth calmly."),
        ("How did the story end?",
         f"The crew ended awake, smiling, and ready for morning. The hidden item was safe, and the ship felt lucky."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does awake mean?",
         "Awake means not asleep. If someone is awake, they can look, listen, and talk."),
        ("What is a trouser?",
         "A trouser is a piece of clothing for the legs. It often has pockets for small things."),
        ("What is foreshadowing?",
         "Foreshadowing is when a story gives a small clue before the big surprise happens. It helps the ending feel clever."),
        ("What is a twist in a story?",
         "A twist is a surprise that changes what you thought was happening. It makes the story turn in a new direction."),
        ("Why do stories use dialogue?",
         "Dialogue lets characters speak to each other. It makes their feelings and choices feel lively."),
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
problem_ok(S, T, P) :- ship(S), trouser(T), problem(P), clue_trouser(T), hidden_problem(P).
"""
def asp_facts() -> str:
    import asp
    out = []
    for sid in SHIPS:
        out.append(asp.fact("ship", sid))
    for tid, t in TROUSERS.items():
        out.append(asp.fact("trouser", tid))
        if "clue" in t.tags:
            out.append(asp.fact("clue_trouser", tid))
    for pid, p in PROBLEMS.items():
        out.append(asp.fact("problem", pid))
        if "hidden" in p.tags or True:
            out.append(asp.fact("hidden_problem", pid))
    return "\n".join(out)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show problem_ok/3."))
    return sorted(set(asp.atoms(model, "problem_ok")))


def asp_verify() -> int:
    import io
    import contextlib
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python combo gates differ.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample)
    except Exception as exc:  # noqa: BLE001
        print(f"MISMATCH: generation smoke test failed: {exc}")
        rc = 1
    if rc == 0:
        print("OK: ASP parity and generation smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate-tale storyworld with awake/trouser foreshadowing and a twist.")
    ap.add_argument("--ship", choices=SHIPS)
    ap.add_argument("--trouser", choices=TROUSERS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--mate")
    ap.add_argument("--mate-gender", choices=["girl", "boy"])
    ap.add_argument("--captain")
    ap.add_argument("--captain-gender", choices=["girl", "boy"])
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
    if args.problem and args.trouser:
        if not hazard(PROBLEMS[args.problem], TROUSERS[args.trouser]):
            raise StoryError("No story: the trouser would not plausibly foreshadow that problem.")
    ship = args.ship or rng.choice(list(SHIPS))
    trouser = args.trouser or rng.choice(list(TROUSERS))
    problem = args.problem or rng.choice(list(PROBLEMS))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    mate_gender = args.mate_gender or ("boy" if hero_gender == "girl" else "girl")
    captain_gender = args.captain_gender or rng.choice(["girl", "boy"])
    return StoryParams(
        ship=ship,
        trouser=trouser,
        problem=problem,
        hero=args.hero or choose_name(rng, hero_gender),
        hero_gender=hero_gender,
        mate=args.mate or choose_name(rng, mate_gender),
        mate_gender=mate_gender,
        captain=args.captain or choose_name(rng, captain_gender),
        captain_gender=captain_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.ship not in SHIPS or params.trouser not in TROUSERS or params.problem not in PROBLEMS:
        raise StoryError("Invalid params: unknown ship, trouser, or problem.")
    world = tell(
        SHIPS[params.ship],
        TROUSERS[params.trouser],
        PROBLEMS[params.problem],
        params.hero,
        params.hero_gender,
        params.mate,
        params.mate_gender,
        params.captain,
        params.captain_gender,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("#show problem_ok/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
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
        while len(samples) < args.n and i < max(args.n * 50, 50):
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

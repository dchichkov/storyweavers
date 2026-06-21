#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/roman_inner_monologue_friendship_mystery_to_solve.py
====================================================================================

A standalone story world for a tall-tale friendship mystery featuring Roman,
inner monologue, and a puzzle that gets solved by noticing small clues.

The world is built to satisfy the Storyweavers storyworld contract:
- typed entities with physical meters and emotional memes
- a small simulated world that drives prose
- three Q&A sets grounded in world state
- a Python reasonableness gate plus an inline ASP twin
- a verify mode that checks parity and exercises ordinary story generation
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

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


@dataclass
class Place:
    id: str
    label: str
    dark: bool = False
    clueful: bool = False
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
    missing: str
    clue1: str
    clue2: str
    found: str
    where_hidden: str
    reveal_line: str
    tags: set[str] = field(default_factory=set)
    difficulty: int = 0
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
class FriendPlan:
    id: str
    aid: str
    verb: str
    look: str
    solve_power: int
    kind: str = "help"
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
    place: str
    mystery: str
    plan: str
    roman_name: str = "Roman"
    friend_name: str = "Junie"
    friend_gender: str = "girl"
    roman_gender: str = "boy"
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
    def __init__(self, place: Place):
        self.place = place
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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


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


def _r_worry(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.kind == "character" and e.memes.get("worry", 0.0) >= THRESHOLD:
            sig = ("worry", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            world.get("room").meters["tension"] = world.get("room").meters.get("tension", 0.0) + 1
            out.append("__worry__")
    return out


def _r_solve(world: World) -> list[str]:
    out = []
    if world.facts.get("solved"):
        sig = ("solve",)
        if sig not in world.fired:
            world.fired.add(sig)
            out.append("__solve__")
    return out


CAUSAL_RULES = [Rule("worry", "social", _r_worry), Rule("solve", "social", _r_solve)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for mis_id, mis in MYSTERIES.items():
            for plan_id, plan in PLANS.items():
                if place.dark and "light" in mis.tags and plan.solve_power >= mis.difficulty:
                    combos.append((place_id, mis_id, plan_id))
                elif place.clueful and plan.solve_power >= mis.difficulty:
                    combos.append((place_id, mis_id, plan_id))
    return combos


def _clue_nudge(world: World, roman: Entity, friend: Entity, mystery: Mystery) -> None:
    roman.memes["curiosity"] = roman.memes.get("curiosity", 0.0) + 1
    friend.memes["curiosity"] = friend.memes.get("curiosity", 0.0) + 1
    world.say(
        f"Roman and {friend.id} marched into {world.place.label}, where the air felt as wide as a cathedral and twice as old. "
        f"Something was missing, and Roman's mind began to mutter, 'One clue at a time, now.'"
    )
    world.say(
        f'“We are looking for {mystery.missing},” Roman said, though inside {roman.pronoun("possessive")} own head '
        f"he was already counting the shadows and listening for trouble."
    )


def _share_friendship(world: World, roman: Entity, friend: Entity) -> None:
    roman.memes["friendship"] = roman.memes.get("friendship", 0.0) + 1
    friend.memes["friendship"] = friend.memes.get("friendship", 0.0) + 1
    world.say(
        f"{friend.id} stayed close and said, “I will help.” Roman felt it like a lantern in {roman.pronoun('possessive')} chest."
    )


def _inner_monologue(world: World, roman: Entity, mystery: Mystery) -> None:
    roman.memes["worry"] = roman.memes.get("worry", 0.0) + 1
    world.say(
        f"Roman kept thinking, 'The first clue is {mystery.clue1}. The second clue is {mystery.clue2}. "
        f"If I follow both, the whole riddle might stand up and bow.'"
    )


def _search(world: World, friend: Entity, mystery: Mystery, plan: FriendPlan) -> None:
    world.say(
        f"{friend.id} used {plan.look} and {plan.verb} around the room like a thunderbolt with manners."
    )
    world.say(
        f"At last, there it was: {mystery.found}, tucked away {mystery.where_hidden}."
    )


def _reveal(world: World, roman: Entity, friend: Entity, mystery: Mystery) -> None:
    world.facts["solved"] = True
    propagate(world, narrate=False)
    roman.memes["joy"] = roman.memes.get("joy", 0.0) + 1
    friend.memes["joy"] = friend.memes.get("joy", 0.0) + 1
    world.say(
        f"Roman grinned so hard it nearly split {roman.pronoun('possessive')} freckles. "
        f"'{mystery.reveal_line}'"
    )
    world.say(
        f"{friend.id} laughed, and the two of them carried {mystery.found} home like they had rescued a comet from the grass."
    )


def tell(place: Place, mystery: Mystery, plan: FriendPlan,
         roman_name: str = "Roman", roman_gender: str = "boy",
         friend_name: str = "Junie", friend_gender: str = "girl") -> World:
    world = World(place)
    roman = world.add(Entity(
        id=roman_name, kind="character", type=roman_gender, role="solver",
        attrs={"voice": "inner"},
        memes={"curiosity": 1.0, "worry": 0.0, "joy": 0.0, "friendship": 0.0},
    ))
    friend = world.add(Entity(
        id=friend_name, kind="character", type=friend_gender, role="helper",
        attrs={"aid": plan.aid},
        memes={"curiosity": 1.0, "worry": 0.0, "joy": 0.0, "friendship": 0.0},
    ))
    world.add(Entity(id="room", kind="place", type="room", label=place.label))

    _clue_nudge(world, roman, friend, mystery)
    world.para()
    _share_friendship(world, roman, friend)
    _inner_monologue(world, roman, mystery)
    world.para()
    _search(world, friend, mystery, plan)
    _reveal(world, roman, friend, mystery)

    world.facts.update(
        place=place, mystery=mystery, plan=plan, roman=roman, friend=friend,
        solved=True,
    )
    return world


PLACES = {
    "library": Place(id="library", label="the old library", dark=True, clueful=True, tags={"dark", "books"}),
    "barn": Place(id="barn", label="the moonlit barn", dark=True, clueful=False, tags={"dark", "hay"}),
    "market": Place(id="market", label="the windy market square", dark=False, clueful=True, tags={"crowd"}),
}

MYSTERIES = {
    "bell": Mystery(
        id="bell", missing="the silver bell", clue1="a trail of glitter by the stairs",
        clue2="a soft ding near the hayloft", found="the silver bell",
        where_hidden="under a crooked crate", reveal_line="The clues fit together like a horse and wagon!",
        tags={"light", "bell"}, difficulty=1,
    ),
    "lantern": Mystery(
        id="lantern", missing="the brass lantern", clue1="warm dust on the windowsill",
        clue2="a long scratch beside the door", found="the brass lantern",
        where_hidden="behind a stack of seed sacks", reveal_line="The lantern was never lost at all; it was waiting in plain sight!",
        tags={"light", "lantern"}, difficulty=2,
    ),
    "map": Mystery(
        id="map", missing="the painted map", clue1="a blue ribbon tied to a nail",
        clue2="a boot print shaped like a crescent moon", found="the painted map",
        where_hidden="inside a hollow beam", reveal_line="That old map had been hiding like a fox in a fence hole!",
        tags={"scroll", "paper"}, difficulty=2,
    ),
}

PLANS = {
    "lantern": FriendPlan(id="lantern", aid="light the corners", verb="shine", look="a brass lantern", solve_power=2, tags={"light"}),
    "magnifier": FriendPlan(id="magnifier", aid="study the clues", verb="peer", look="a little magnifier", solve_power=2, tags={"detail"}),
    "boots": FriendPlan(id="boots", aid="follow tracks", verb="stomp", look="muddy boots", solve_power=1, tags={"tracks"}),
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall-tale story for a child that includes the word "{f["roman"].id}".',
        f"Tell a friendship mystery where Roman and {f['friend'].id} solve a missing-object puzzle by noticing clues and thinking out loud.",
        f"Write a story with Roman's inner monologue, a loyal helper, and a hidden treasure found by following two clues.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    roman: Entity = f["roman"]
    friend: Entity = f["friend"]
    mystery: Mystery = f["mystery"]
    place: Place = f["place"]
    qa = [
        ("Who is the story about?",
         f"It is about Roman and {friend.id}, who worked together in {place.label}. Roman did the thinking, and {friend.id} kept the search moving."),
        ("What mystery did they try to solve?",
         f"They tried to find {mystery.missing}. The clues led them from one little sign to another until the hidden place made sense."),
        ("What was Roman thinking to himself?",
         f"Roman was thinking that {mystery.clue1} and {mystery.clue2} belonged to the same mystery. He kept telling himself to follow both clues instead of giving up."),
        ("How did Roman and the friend work together?",
         f"{friend.id} searched with {f['plan'].look}, and Roman listened, guessed, and shared the clues out loud. That friendship made the puzzle feel lighter."),
        ("How did the story end?",
         f"They found {mystery.found} and carried it home together. The ending showed that the mystery was solved and their friendship grew stronger."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["mystery"].tags) | set(f["plan"].tags) | set(f["place"].tags)
    out = []
    if "light" in tags:
        out.append(("Why can a lantern help solve a mystery?",
                    "A lantern gives a steady light so friends can look into dark corners and notice tiny clues. That makes it easier to solve a mystery without guessing wildly."))
    if "dark" in tags:
        out.append(("Why is a dark place tricky for searching?",
                    "A dark place hides small details, so it is harder to spot clues. A careful search and a little light can help."))
    if "detail" in tags:
        out.append(("What does it mean to study clues carefully?",
                    "It means looking closely, thinking slowly, and checking whether the clues fit together. Careful thinking often solves puzzles that plain rushing cannot."))
    return out


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
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="library", mystery="bell", plan="lantern", roman_name="Roman", friend_name="Junie", friend_gender="girl", roman_gender="boy"),
    StoryParams(place="barn", mystery="map", plan="magnifier", roman_name="Roman", friend_name="Tessa", friend_gender="girl", roman_gender="boy"),
    StoryParams(place="market", mystery="lantern", plan="boots", roman_name="Roman", friend_name="Milo", friend_gender="boy", roman_gender="boy"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    choices = [c for c in valid_combos()
               if (args.place is None or c[0] == args.place)
               and (args.mystery is None or c[1] == args.mystery)
               and (args.plan is None or c[2] == args.plan)]
    if not choices:
        raise StoryError("(No valid combination matches the given options.)")
    place, mystery, plan = rng.choice(sorted(choices))
    roman_gender = args.roman_gender or "boy"
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    return StoryParams(
        place=place,
        mystery=mystery,
        plan=plan,
        roman_name=args.roman_name or "Roman",
        friend_name=args.friend_name or rng.choice(["Junie", "Tessa", "Milo", "Pia"]),
        friend_gender=friend_gender,
        roman_gender=roman_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.mystery not in MYSTERIES:
        raise StoryError(f"Unknown mystery: {params.mystery}")
    if params.plan not in PLANS:
        raise StoryError(f"Unknown plan: {params.plan}")
    world = tell(
        PLACES[params.place],
        MYSTERIES[params.mystery],
        PLANS[params.plan],
        roman_name=params.roman_name,
        roman_gender=params.roman_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
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


ASP_RULES = r"""
valid(P, M, L) :- place(P), mystery(M), plan(L), solved(P, M, L).
solved(P, M, L) :- dark(P), clueful(P), difficulty(M, D), power(L, X), X >= D.
solved(P, M, L) :- clueful(P), difficulty(M, D), power(L, X), X >= D.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.dark:
            lines.append(asp.fact("dark", pid))
        if p.clueful:
            lines.append(asp.fact("clueful", pid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("difficulty", mid, m.difficulty))
    for lid, l in PLANS.items():
        lines.append(asp.fact("plan", lid))
        lines.append(asp.fact("power", lid, l.solve_power))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        rc = 1
        print("MISMATCH in valid combos:")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
    else:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: ordinary generation smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"MISMATCH: generation smoke test failed: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale friendship mystery with Roman's inner monologue."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--roman-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--roman-gender", choices=["boy", "girl"])
    ap.add_argument("--friend-gender", choices=["boy", "girl"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, mystery, plan) combos:")
        for combo in combos:
            print("  ", combo)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.roman_name} and {p.friend_name}: {p.mystery} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

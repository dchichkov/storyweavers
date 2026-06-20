#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/four_mouse_friendship_twist_mystery_to_solve.py
===============================================================================

A standalone story world for a folk-tale style mouse mystery.

Premise:
- Four mice live near a little grain store and a lantern-lit root cellar.
- One small problem becomes a mystery when a missing cheese wheel and a torn ribbon
  are found.
- Friendship matters: the mice trust one another, share clues, and solve the puzzle.
- Twist: the surprising helper is the smallest mouse, who remembers a hidden route.
- Ending image: the four mice celebrate together with the recovered treasure and a
  safer plan for next time.

This script follows the Storyweavers world contract:
- self-contained stdlib script
- imports results eagerly
- defines StoryParams, registries, build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- includes Python reasoning gates and an inline ASP twin
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"mouse", "girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Place:
    id: str
    label: str
    dark_spot: str
    cozy_detail: str
    clue_place: str
    rescue_route: str
    hidden_route: str
    homey_finish: str
    tags: set[str] = field(default_factory=set)

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
class Mystery:
    id: str
    missing_item: str
    missing_phrase: str
    twist_item: str
    twist_phrase: str
    clue1: str
    clue2: str
    culprit_hint: str
    solved_with: str
    tags: set[str] = field(default_factory=set)

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
class Response:
    id: str
    sense: int
    text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)

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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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

    def mice(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
@dataclass
class StoryParams:
    place: str
    mystery: str
    response: str
    mouse1: str
    mouse2: str
    mouse3: str
    mouse4: str
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


PLACES = {
    "rootcellar": Place(
        "rootcellar",
        "a lantern-lit root cellar",
        "the dark corner by the turnip crates",
        "warm air and dry straw",
        "the shelf near the cheese hooks",
        "a little door under the stairs",
        "the hidden tunnel behind the flour barrel",
        "with the four mice sitting safe and snug together",
        tags={"cellar", "dark", "home"},
    ),
    "barnloft": Place(
        "barnloft",
        "a cozy barn loft",
        "the shadow under the hay bales",
        "sweet hay and moonlight through slats",
        "the beam above the grain sacks",
        "the ladder by the loft wall",
        "a narrow rope bridge behind the feed bin",
        "with the four mice nestled in the hay at peace",
        tags={"barn", "loft", "home"},
    ),
}

MYSTERIES = {
    "cheese_ribbon": Mystery(
        "cheese_ribbon",
        "the round cheese wheel",
        "the round cheese wheel was missing",
        "a red ribbon",
        "a red ribbon lay torn on the floor",
        "tiny crumbs near the flour barrel",
        "a whisker-smudge on the ladder",
        "the smallest mouse had seen a hidden path",
        "shared the cheese and tied the ribbon around the lantern",
        tags={"cheese", "ribbon", "twist"},
    ),
    "seed_sack": Mystery(
        "seed_sack",
        "the seed sack",
        "the seed sack was gone",
        "a blue pebble",
        "a blue pebble gleamed beside the wall",
        "a trail of oat dust toward the corner",
        "three little pawprints on the ledge",
        "the shyest mouse had remembered a secret door",
        "fixed the sack and made a little map",
        tags={"seeds", "pebble", "twist"},
    ),
}

RESPONSES = {
    "search": Response("search", 3, "searched every nook and cranny together", "searched every nook and cranny together", {"search"}),
    "listen": Response("listen", 4, "sat still and listened for the quiet clue", "sat still and listened for the quiet clue", {"listen"}),
    "map": Response("map", 4, "made a careful little map from the clues", "made a careful little map from the clues", {"map"}),
}

NAMES = ["Milo", "Mina", "Pip", "Luna", "Bram", "Tansy", "Toby", "Pippa", "Nell", "Moss", "Nip", "Wren"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in PLACES:
        for mid in MYSTERIES:
            for rid in RESPONSES:
                out.append((place, mid, rid))
    return out


def reasonableness_ok(params: StoryParams) -> bool:
    return params.place in PLACES and params.mystery in MYSTERIES and params.response in RESPONSES


def _r_fear(world: World) -> list[str]:
    out = []
    if world.facts.get("trouble", False) and ("fear", "mice") not in world.fired:
        world.fired.add(("fear", "mice"))
        for m in world.mice():
            m.memes["worry"] += 1
        out.append("")
    return out


def propagate(world: World) -> None:
    _r_fear(world)


def tell(place: Place, mystery: Mystery, response: Response, names: list[str]) -> World:
    world = World(place)
    mice = []
    for i, nm in enumerate(names):
        mice.append(world.add(Entity(id=nm, kind="character", type="mouse", role="friend", traits=["small", "kind"])))
        mice[-1].memes["friendship"] = 2.0
        mice[-1].memes["curiosity"] = 1.0 + i * 0.25
    witness = mice[-1]

    world.say(
        f"In {place.label}, four mice lived as close as crumbs in a jar. "
        f"{mice[0].id}, {mice[1].id}, {mice[2].id}, and {mice[3].id} shared warm straw, "
        f"soft greetings, and the habit of helping one another."
    )
    world.say(
        f"One evening, {mice[0].id} noticed that {mystery.missing_phrase}, "
        f"and {mice[1].id} found {mystery.twist_phrase} by {place.clue_place}."
    )
    world.para()
    world.say(
        f"The four mice looked at one another. Nobody wanted to blame a friend, "
        f"so they chose to be patient and solve the mystery together."
    )
    world.say(
        f"{response.text.capitalize()}, because friendship made them brave enough to keep looking."
    )

    world.facts["trouble"] = True
    propagate(world)

    world.para()
    if response.id == "listen":
        world.say(
            f"They listened in the hush of the cellar, and {witness.id} remembered "
            f"{mystery.culprit_hint}. {witness.id} had once gone through {place.hidden_route} "
            f"to hide from the cold, and the missing treasure had been carried there by a busy little breeze."
        )
    elif response.id == "map":
        world.say(
            f"They drew a map with a berry-stain paw and followed it step by step. "
            f"The trail led them to {place.hidden_route}, where the missing thing had been tucked away."
        )
    else:
        world.say(
            f"They searched every corner until {witness.id} spotted a clue that pointed to {place.hidden_route}."
        )

    world.say(
        f"There, the mystery turned with a twist: the smallest mouse had solved it all along. "
        f"{mystery.solved_with.capitalize()}, and the friends laughed because the answer had been hiding in plain sight."
    )

    world.para()
    for m in mice:
        m.memes["joy"] += 1
        m.memes["relief"] += 1
        m.memes["friendship"] += 1
    world.say(
        f"At last, the four mice came home together to {place.homey_finish}. "
        f"They shared the food, tucked the clue into a safe corner, and promised to trust one another whenever a new mystery arrived."
    )

    world.facts.update(
        mice=mice,
        witness=witness,
        place=place,
        mystery=mystery,
        response=response,
        solved=True,
        twist=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place: Place = f["place"]
    mystery: Mystery = f["mystery"]
    return [
        f'Write a folk tale for a child about four mice in {place.label} who solve a mystery together, and include the words "four" and "mouse".',
        f"Tell a friendship story where four mice find a missing thing, follow a clue, and discover a twist that helps them solve it.",
        f"Write a cozy mystery-to-solve story for young children where the answer is helped by friendship and a surprising small mouse.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    place: Place = f["place"]
    mystery: Mystery = f["mystery"]
    witness: Entity = f["witness"]
    mice: list[Entity] = f["mice"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about four mice who live together near {place.label}. They work as friends, so the story follows the whole little group instead of only one mouse."
        ),
        QAItem(
            question="What mystery did they have to solve?",
            answer=f"They had to solve why {mystery.missing_phrase}. They found clues near {place.clue_place}, and those clues led them toward the answer."
        ),
        QAItem(
            question=f"Why was {witness.id} important?",
            answer=f"{witness.id} was important because {witness.id} remembered {mystery.culprit_hint}. That memory gave the friends the twist that let them solve the mystery."
        ),
        QAItem(
            question="How did friendship help them?",
            answer=f"They did not blame each other, and that kept their hearts calm enough to think. Because they stayed kind, they could listen, share clues, and find the answer together."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mouse?",
            answer="A mouse is a tiny animal with soft fur, whiskers, and quick little feet. Mice like to run, hide, and nibble small foods."
        ),
        QAItem(
            question="What does friendship mean?",
            answer="Friendship means caring about someone, sharing with them, and helping when they need it. Good friends try to be kind even when they are puzzled."
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something that is not explained yet. People or animals solve a mystery by looking for clues and thinking carefully."
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising turn that changes what you thought was happening. It can make the answer feel clever or unexpected."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("")
    parts.append("== (3) World knowledge ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, M, R) :- place(P), mystery(M), response(R).
twist(M) :- mystery(M), twist_item(M, _).
solved(P, M, R) :- valid(P, M, R), twist(M).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("twist_item", mid, m.twist_item))
    for rid in RESPONSES:
        lines.append(asp.fact("response", rid))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    ok = True
    if set(asp_valid_combos()) != set(valid_combos()):
        ok = False
        print("MISMATCH: ASP and Python valid_combos differ.")
    # smoke test default generation
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, mystery=None, response=None, seed=None), random.Random(7)))
        _ = sample.story
    except Exception as e:
        ok = False
        print(f"MISMATCH: generation smoke test failed: {e}")
    if ok:
        print(f"OK: verify passed, {len(valid_combos())} combos, generation smoke test succeeded.")
        return 0
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale mouse mystery storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.response is None or c[2] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mystery, response = rng.choice(sorted(combos))
    names = rng.sample(NAMES, 4)
    return StoryParams(place, mystery, response, *names)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], MYSTERIES[params.mystery], RESPONSES[params.response],
                 [params.mouse1, params.mouse2, params.mouse3, params.mouse4])
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    StoryParams("rootcellar", "cheese_ribbon", "listen", "Milo", "Mina", "Pip", "Luna"),
    StoryParams("barnloft", "seed_sack", "map", "Bram", "Tansy", "Toby", "Pippa"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show solved/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        print(f"{len(asp_valid_combos())} compatible combos:\n")
        for p, m, r in asp_valid_combos():
            print(f"  {p:10} {m:16} {r}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 30):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
            s = generate(params)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.place} | {p.mystery} | {p.response}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

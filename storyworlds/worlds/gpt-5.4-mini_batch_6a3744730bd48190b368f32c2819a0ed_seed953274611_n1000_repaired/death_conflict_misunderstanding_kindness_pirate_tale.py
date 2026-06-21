#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/death_conflict_misunderstanding_kindness_pirate_tale.py
=======================================================================================

A standalone storyworld for a tiny pirate tale about conflict, misunderstanding,
and kindness, with a death already in the setting. The world is small on purpose:
one ship, one stubborn captain, one careful mate, one lost crew member, and one
gentle turn that changes how the crew treats the sea.

The story arc is built from simulated state:
- a pirate captain suspects a mate hid a map
- the suspicion sparks conflict
- the conflict is caused by a misunderstanding
- kindness resolves the rift
- the story includes a death in the past, so the crew's choices carry weight

This script follows the Storyweavers contract:
- stdlib-only prose engine
- eager import of storyworlds/results.py
- lazy import of storyworlds/asp.py inside ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- support for -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- Python validity gate plus inline ASP twin
"""

from __future__ import annotations

import argparse
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "man", "father", "dad", "captain", "pirate"}
        female = {"girl", "woman", "mother", "mom"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
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
class Ship:
    id: str
    name: str
    place: str
    death_mark: str
    cargo: str
    maps: str
    grief_token: str
    safe_choice: str
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
    ship: str
    captain: str
    mate: str
    dead_crew: str
    captain_gender: str
    mate_gender: str
    dead_crew_gender: str
    relation: str
    misunderstanding: str
    kindness: str
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
        c.entities = {k: Entity(**{
            "id": v.id, "kind": v.kind, "type": v.type, "label": v.label,
            "role": v.role, "attrs": dict(v.attrs),
            "meters": defaultdict(float, dict(v.meters)),
            "memes": defaultdict(float, dict(v.memes)),
        }) for k, v in self.entities.items()}
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


SHIPS = {
    "gull": Ship(
        id="gull",
        name="the Sea Gull",
        place="a small pirate ship",
        death_mark="the empty hammock of old Finn, who had died at sea last winter",
        cargo="barrels of apples and rope",
        maps="a folded chart",
        grief_token="Finn's brass button",
        safe_choice="a lantern",
        tags={"pirate", "sea", "death"},
    ),
    "kraken": Ship(
        id="kraken",
        name="the Bright Kraken",
        place="a lively pirate ship",
        death_mark="the quiet bunk where Aunt Mara, who had died in a storm, used to sleep",
        cargo="sails, gull-feather hats, and tea tins",
        maps="a worn map",
        grief_token="Mara's red scarf",
        safe_choice="a lamp",
        tags={"pirate", "sea", "death"},
    ),
}

MISUNDERSTANDINGS = {
    "hidden_map": "thought the mate had hidden the map on purpose",
    "lost_note": "thought the note meant the mate was disloyal",
    "broken_compass": "thought the mate had broken the compass",
}

KINDNESSES = {
    "share_truth": "showed the whole pocket and explained the truth",
    "offer_hug": "put down the rope and offered a hug first",
    "make_tea": "set out tea and listened before speaking again",
}

TRAITS = ["careful", "proud", "stern", "soft", "brave", "quiet"]

GIRL_NAMES = ["Mina", "Lena", "Nora", "Ivy", "Mira"]
BOY_NAMES = ["Finn", "Otis", "Bram", "Jace", "Tobin"]


def _name_for(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def _safe_pronoun(word: str) -> str:
    return word


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for ship in SHIPS:
        for misunderstanding in MISUNDERSTANDINGS:
            for kindness in KINDNESSES:
                combos.append((ship, misunderstanding, kindness))
    return combos


def _ship_requires_death(ship: Ship) -> bool:
    return "death" in ship.tags


def assess_conflict(misunderstanding: str) -> int:
    return 2 if misunderstanding in MISUNDERSTANDINGS else 0


def resolve_with_kindness(kindness: str) -> bool:
    return kindness in KINDNESSES


def would_story_hold(ship: Ship, misunderstanding: str, kindness: str) -> bool:
    return _ship_requires_death(ship) and misunderstanding in MISUNDERSTANDINGS and kindness in KINDNESSES


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld about death, conflict, misunderstanding, and kindness.")
    ap.add_argument("--ship", choices=SHIPS)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--kindness", choices=KINDNESSES)
    ap.add_argument("--captain")
    ap.add_argument("--mate")
    ap.add_argument("--dead-crew")
    ap.add_argument("--captain-gender", choices=["girl", "boy"])
    ap.add_argument("--mate-gender", choices=["girl", "boy"])
    ap.add_argument("--dead-crew-gender", choices=["girl", "boy"])
    ap.add_argument("--relation", choices=["crew", "friends", "siblings"])
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


def reasonableness_check(params: StoryParams) -> None:
    if params.ship not in SHIPS:
        raise StoryError("Unknown ship.")
    if params.misunderstanding not in MISUNDERSTANDINGS:
        raise StoryError("Unknown misunderstanding.")
    if params.kindness not in KINDNESSES:
        raise StoryError("Unknown kindness.")
    if not would_story_hold(SHIPS[params.ship], params.misunderstanding, params.kindness):
        raise StoryError("This pirate tale needs a real death-marked ship, a conflict-causing misunderstanding, and a kindness that can answer it.")


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SHIPS:
        lines.append(asp.fact("ship", sid))
        lines.append(asp.fact("death_marked", sid))
    for mid in MISUNDERSTANDINGS:
        lines.append(asp.fact("misunderstanding", mid))
    for kid in KINDNESSES:
        lines.append(asp.fact("kindness", kid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, M, K) :- ship(S), death_marked(S), misunderstanding(M), kindness(K).
conflict(M) :- misunderstanding(M).
kindness_available(K) :- kindness(K).
"""

def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate:")
        print(" only python:", sorted(py - cl))
        print(" only clingo:", sorted(cl - py))
    try:
        sample = generate(resolve_params(argparse.Namespace(
            ship=None, misunderstanding=None, kindness=None,
            captain=None, mate=None, dead_crew=None,
            captain_gender=None, mate_gender=None, dead_crew_gender=None,
            relation=None
        ), random.Random(777)))
        assert sample.story.strip()
        print("OK: smoke-test story generation succeeded.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def tell(params: StoryParams) -> World:
    world = World()
    ship = SHIPS[params.ship]
    cap = world.add(Entity(id=params.captain, kind="character", type=params.captain_gender, role="captain"))
    mate = world.add(Entity(id=params.mate, kind="character", type=params.mate_gender, role="mate"))
    dead = world.add(Entity(id=params.dead_crew, kind="character", type=params.dead_crew_gender, role="dead crew"))
    cap.memes["pride"] = 2
    mate.memes["caution"] = 2
    world.facts.update(ship=ship, captain=cap, mate=mate, dead=dead, params=params)
    world.say(f"On the ship called {ship.name}, the crew sailed beneath a hard blue sky. {ship.death_mark}.")
    world.say(f"{cap.id} kept a tight face and watched the deck while {mate.id} checked the lines.")
    world.say(f"Then {cap.id} noticed {mate.id} near {ship.maps} and felt a sharp conflict rise like a squall.")
    world.para()
    world.say(f'"{mate.id}, you hid the chart," {cap.id} snapped. "{mate.id} thought the map was being taken away and the worry turned into a misunderstanding.')
    world.say(f"{mate.id} shook {mate.pronoun('possessive')} head and said nothing was hidden on purpose.")
    world.para()
    world.say(f"That was when {mate.id} chose kindness instead of anger: {KINDNESSES[params.kindness]}.")
    world.say(f"Slowly, the truth came out. The chart had slipped under a coil of rope during the storm, right beside {ship.grief_token}.")
    world.say(f"{cap.id} went quiet, then put a hand on {mate.id}'s shoulder. The old death on the ship made the crew gentler, not meaner.")
    world.para()
    world.say(f"At sunset, they set out {ship.safe_choice} and read the chart together. The conflict faded, and the ship moved on with a softer heart.")
    cap.memes["kindness"] += 1
    mate.memes["kindness"] += 1
    dead.meters["memory"] += 1
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    ship = f["ship"]
    return [
        f"Write a pirate tale that includes the word 'death' and takes place on {ship.name}.",
        f"Tell a short story where a captain and mate argue because of a misunderstanding, then kindness fixes it.",
        f"Write a child-friendly pirate story about conflict, misunderstanding, and kindness, with an old death on the ship in the background.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p: StoryParams = f["params"]
    ship: Ship = f["ship"]
    return [
        QAItem(
            question="What is the story about?",
            answer=f"It is about {p.captain} and {p.mate} on {ship.name}. They argue at first, but the misunderstanding is cleared up with kindness."
        ),
        QAItem(
            question="Why did the conflict begin?",
            answer=f"The conflict began because {p.captain} thought {p.mate} had hidden the chart. In truth, the chart had only slipped away by accident, so the anger came from a misunderstanding."
        ),
        QAItem(
            question="How did kindness change the story?",
            answer=f"{KINDNESSES[p.kindness].capitalize()}, and that gave everyone room to tell the truth. After that, the crew could remember the death on the ship without turning it into a fight."
        ),
        QAItem(
            question="How did the story end?",
            answer="The captain and mate calmed down, shared the truth, and sailed on together at sunset. The ship felt quieter and kinder by the end."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding is when someone thinks something wrong about another person or event. It can start a fight, even when nobody meant harm."
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness is when you choose to be gentle, patient, and helpful. It can calm angry feelings and help people speak honestly."
        ),
        QAItem(
            question="Why does death matter in a story?",
            answer="Death can make a story feel serious because it changes what people remember and fear. It can also make characters treat one another more carefully."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts ==", *[f"- {p}" for p in sample.prompts], "", "== story qa =="]
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
    out = ["--- world ---"]
    for e in list(world.entities.values()):
        out.append(f"{e.id}: kind={e.kind} type={e.type} role={e.role} meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(out)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.ship is None or c[0] == args.ship)
              and (args.misunderstanding is None or c[1] == args.misunderstanding)
              and (args.kindness is None or c[2] == args.kindness)]
    if not combos:
        raise StoryError("No valid combination matches those options.")
    ship, misunderstanding, kindness = rng.choice(sorted(combos))
    cap_gender = args.captain_gender or rng.choice(["girl", "boy"])
    mate_gender = args.mate_gender or rng.choice(["girl", "boy"])
    dead_gender = args.dead_crew_gender or rng.choice(["girl", "boy"])
    return StoryParams(
        ship=ship,
        captain=args.captain or _name_for(rng, cap_gender),
        mate=args.mate or _name_for(rng, mate_gender),
        dead_crew=args.dead_crew or _name_for(rng, dead_gender),
        captain_gender=cap_gender,
        mate_gender=mate_gender,
        dead_crew_gender=dead_gender,
        relation=args.relation or rng.choice(["crew", "friends", "siblings"]),
        misunderstanding=misunderstanding,
        kindness=kindness,
    )


def generate(params: StoryParams) -> StorySample:
    reasonableness_check(params)
    world = tell(params)
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


CURATED = [
    StoryParams(ship="gull", captain="Mina", mate="Otis", dead_crew="Finn",
                captain_gender="girl", mate_gender="boy", dead_crew_gender="boy",
                relation="crew", misunderstanding="hidden_map", kindness="share_truth"),
    StoryParams(ship="kraken", captain="Bram", mate="Lena", dead_crew="Mara",
                captain_gender="boy", mate_gender="girl", dead_crew_gender="girl",
                relation="friends", misunderstanding="lost_note", kindness="offer_hug"),
]


def build_parser() -> argparse.ArgumentParser:
    return build_parser


def _build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with death, conflict, misunderstanding, and kindness.")
    ap.add_argument("--ship", choices=SHIPS)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--kindness", choices=KINDNESSES)
    ap.add_argument("--captain")
    ap.add_argument("--mate")
    ap.add_argument("--dead-crew")
    ap.add_argument("--captain-gender", choices=["girl", "boy"])
    ap.add_argument("--mate-gender", choices=["girl", "boy"])
    ap.add_argument("--dead-crew-gender", choices=["girl", "boy"])
    ap.add_argument("--relation", choices=["crew", "friends", "siblings"])
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


def main() -> None:
    args = _build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for t in asp_valid_combos():
            print(" ", t)
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def build_parser() -> argparse.ArgumentParser:  # type: ignore[override]
    return _build_parser()


def asp_program(show: str = "", extra: str = "") -> str:  # type: ignore[override]
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


if __name__ == "__main__":
    main()

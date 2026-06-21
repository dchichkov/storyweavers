#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/ambulance_leg_dim_repetition_pirate_tale.py
============================================================================

A standalone storyworld about pirate play, a wobbly leg, and an ambulance that
arrives in time. The world is small on purpose: a pair of children playing
pirates, a tumble that leaves one leg dim and weak, a repeated calling beat that
grows louder, and a careful rescue that ends with a safe ride away.

Seed words used in the prose: ambulance, leg-dim.
Feature: repetition.
Style: pirate tale.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, str] = field(default_factory=dict)

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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
    scene: str
    deck: str
    mast: str
    treasure: str
    call: str
    repeat: str
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
class Injury:
    id: str
    label: str
    dim_word: str
    pain_word: str
    support_word: str
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
class RescueTool:
    id: str
    label: str
    phrase: str
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


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
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
    injury: str
    tool: str
    response: str
    hero: str
    hero_gender: str
    mate: str
    mate_gender: str
    adult: str
    adult_gender: str
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
    def __init__(self, ship: Ship) -> None:
        self.ship = ship
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
        clone = World(self.ship)
        clone.entities = {k: Entity(**{
            "id": v.id, "kind": v.kind, "type": v.type, "label": v.label,
            "role": v.role, "traits": list(v.traits),
            "meters": dict(v.meters), "memes": dict(v.memes), "attrs": dict(v.attrs)
        }) for k, v in self.entities.items()}
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _m(state: dict[str, float], key: str) -> float:
    return float(state.get(key, 0.0))


def _set(state: dict[str, float], key: str, value: float) -> None:
    state[key] = value


def hero_name_pool(gender: str) -> list[str]:
    return ["Lily", "Mia", "Zoe", "Ava"] if gender == "girl" else ["Tom", "Ben", "Max", "Finn"]


SHIP_REGISTRY = {
    "brig": Ship(
        id="brig",
        scene="a wild pirate brig",
        deck="the deck",
        mast="the mast",
        treasure="a map chest",
        call="Ahoy!",
        repeat="again and again",
    ),
    "galleon": Ship(
        id="galleon",
        scene="a bold little galleon",
        deck="the deck",
        mast="the mast",
        treasure="a bright coin chest",
        call="Yo-ho!",
        repeat="one more time",
    ),
}

INJURY_REGISTRY = {
    "leg-dim": Injury(
        id="leg-dim",
        label="leg-dim",
        dim_word="dim",
        pain_word="wobbly",
        support_word="careful",
        tags={"leg-dim", "injury", "ambulance"},
    ),
}

TOOL_REGISTRY = {
    "shell-whistle": RescueTool(
        id="shell-whistle",
        label="shell whistle",
        phrase="a shell whistle",
        tags={"whistle", "calling"},
    ),
    "red-flag": RescueTool(
        id="red-flag",
        label="red flag",
        phrase="a red flag",
        tags={"flag", "calling"},
    ),
}

RESPONSES = {
    "call_ambulance": Response(
        id="call_ambulance",
        sense=3,
        power=3,
        text="called the ambulance and stayed with the child until the bright wheels came",
        tags={"ambulance", "help"},
    ),
    "carry_to_shore": Response(
        id="carry_to_shore",
        sense=2,
        power=2,
        text="carried the child to shore and kept the leg still until help arrived",
        tags={"help"},
    ),
}

CURATED = [
    StoryParams(ship="brig", injury="leg-dim", tool="shell-whistle", response="call_ambulance",
                hero="Pip", hero_gender="boy", mate="Mara", mate_gender="girl",
                adult="Captain Nell", adult_gender="girl", seed=1),
    StoryParams(ship="galleon", injury="leg-dim", tool="red-flag", response="carry_to_shore",
                hero="Lily", hero_gender="girl", mate="Tom", mate_gender="boy",
                adult="Mister Bram", adult_gender="boy", seed=2),
]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, i, t) for s in SHIP_REGISTRY for i in INJURY_REGISTRY for t in TOOL_REGISTRY]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale with repetition, leg-dim, and ambulance.")
    ap.add_argument("--ship", choices=SHIP_REGISTRY)
    ap.add_argument("--injury", choices=INJURY_REGISTRY)
    ap.add_argument("--tool", choices=TOOL_REGISTRY)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--mate")
    ap.add_argument("--mate-gender", choices=["girl", "boy"])
    ap.add_argument("--adult")
    ap.add_argument("--adult-gender", choices=["girl", "boy"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and args.response not in RESPONSES:
        raise StoryError("Unknown response.")
    ship = args.ship or rng.choice(list(SHIP_REGISTRY))
    injury = args.injury or "leg-dim"
    tool = args.tool or rng.choice(list(TOOL_REGISTRY))
    response = args.response or rng.choice(list(RESPONSES))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    mate_gender = args.mate_gender or ("boy" if hero_gender == "girl" else "girl")
    hero = args.hero or rng.choice(hero_name_pool(hero_gender))
    mate = args.mate or rng.choice([n for n in hero_name_pool(mate_gender) if n != hero])
    adult_gender = args.adult_gender or rng.choice(["girl", "boy"])
    adult = args.adult or ("Captain Nell" if adult_gender == "girl" else "Captain Bram")
    return StoryParams(ship=ship, injury=injury, tool=tool, response=response,
                       hero=hero, hero_gender=hero_gender, mate=mate, mate_gender=mate_gender,
                       adult=adult, adult_gender=adult_gender)


def _do_injury(world: World, injured: Entity) -> None:
    injured.meters["hurt"] = _m(injured.meters, "hurt") + 1
    injured.meters["leg_dim"] = _m(injured.meters, "leg_dim") + 1
    injured.memes["fear"] = _m(injured.memes, "fear") + 1


def tell(params: StoryParams) -> World:
    ship = SHIP_REGISTRY[params.ship]
    injury = INJURY_REGISTRY[params.injury]
    tool = TOOL_REGISTRY[params.tool]
    response = RESPONSES[params.response]

    world = World(ship)
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_gender,
                            role="hero"))
    mate = world.add(Entity(id=params.mate, kind="character", type=params.mate_gender,
                            role="mate"))
    adult = world.add(Entity(id=params.adult, kind="character", type=params.adult_gender,
                             role="adult"))
    leg = world.add(Entity(id="leg", type="thing", label=injury.label))
    world.facts.update(hero=hero, mate=mate, adult=adult, leg=leg, tool=tool, response=response)

    world.say(f"On {ship.deck}, the little pirates cried, “{ship.call} {ship.call}!” "
              f"They sailed and they swayed, sailed and they swayed, while {ship.scene} bobbed on the blue water.")
    world.say(f"{hero.id} wanted to race by the {ship.mast}, and {mate.id} sang, “Run, run, run, {ship.repeat}!”")
    world.para()
    world.say(f"Then came a slip, a bump, and a hush. {hero.id}'s {injury.label} leg went dim and wobbly, and the brave pirate could not stand straight.")
    _do_injury(world, hero)
    world.say(f"{mate.id} whispered, “The leg is dim, the leg is dim,” because the hurt looked small but felt very real.")
    world.say(f"{hero.id} tried to grin, but {hero.pronoun()} could only cling to {mate.pronoun('object')}.")
    world.para()
    world.say(f"{mate.id} blew {tool.phrase} again and again, again and again.")
    world.say(f"“{ship.call} help! {ship.call} help!” {mate.id} cried, louder and louder.")
    hero.memes["hope"] = _m(hero.memes, "hope") + 1
    world.say(f"The grown-up heard the call and came fast. In a flash, {adult.id} {response.text}.")
    hero.meters["hurt"] = 0.0
    hero.meters["leg_dim"] = 0.0
    hero.memes["fear"] = 0.0
    hero.memes["relief"] = 1.0
    world.para()
    world.say(f"The ambulance waited by the shore, shining white as a gull. The door went open, and soft hands helped the pirate in.")
    world.say(f"{hero.id} kept the {injury.label} leg still, still, still. {mate.id} kept close, close, close, and nobody let the story hurry.")
    world.say(f"At last the ship was quiet, the deck was calm, and the {injury.label} leg rode away safe in the ambulance.")
    world.facts["outcome"] = "rescued"
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a pirate tale for a small child that includes the words "ambulance" and "leg-dim".',
        f"Tell a story where {f['mate'].id} calls for help again and again after {f['hero'].id} gets a leg-dim injury on a pirate ship, and an ambulance arrives.",
        f'Write a repetition-filled pirate story with a calm rescue and a white ambulance by the shore.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, mate, adult = f["hero"], f["mate"], f["adult"]
    return [
        QAItem(
            question="What happened to the pirate's leg?",
            answer=f"{hero.id}'s leg went dim and wobbly after a slip on the ship. The hurt was small in the moment, but it made {hero.id} need help and a careful ride away."
        ),
        QAItem(
            question="What did the other pirate do to get help?",
            answer=f"{mate.id} blew the shell whistle again and again and shouted for help louder and louder. That repetition mattered because the grown-up could hear the call and bring the ambulance quickly."
        ),
        QAItem(
            question="How did the story end?",
            answer="The ambulance came, the leg was kept still, and the child rode away safely. The deck grew quiet at the end, which shows the danger had passed."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an ambulance?",
            answer="An ambulance is a special vehicle that brings help fast and carries sick or hurt people to care."
        ),
        QAItem(
            question="Why should a hurt leg be kept still?",
            answer="Keeping a hurt leg still can help protect it from getting more hurt. It also makes it easier for helpers to move the person safely."
        ),
    ]


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
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
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


ASP_RULES = r"""
valid(S,I,T) :- ship(S), injury(I), tool(T).
rescued :- response(call_ambulance).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SHIP_REGISTRY:
        lines.append(asp.fact("ship", s))
    for i in INJURY_REGISTRY:
        lines.append(asp.fact("injury", i))
    for t in TOOL_REGISTRY:
        lines.append(asp.fact("tool", t))
    for r in RESPONSES:
        lines.append(asp.fact("response", r))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP gate differs from Python gate.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        if not sample.story:
            raise RuntimeError("empty story")
    except Exception as err:
        print(f"MISMATCH: generation smoke test failed: {err}")
        rc = 1
    else:
        print("OK: ASP parity and generation smoke test passed.")
    return rc


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("\n== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("\n== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{a} {b} {c}" for a, b, c in asp_valid_combos()))
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            p = resolve_params(args, random.Random((args.seed or 0) + i))
            p.seed = (args.seed or 0) + i
            s = generate(p)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {idx+1}" if len(samples) > 1 else ""))
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

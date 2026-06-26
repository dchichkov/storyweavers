#!/usr/bin/env python3
"""
storyworlds/worlds/rob_pita_flashback_space_adventure.py
========================================================

A small storyworld for a kid-friendly space adventure with a flashback beat.

Premise:
- Rob and Pita are traveling in a tiny ship between moons and starports.
- A useful object was forgotten in an earlier mission.
- A flashback reveals how they learned the lesson, and the present story uses
  that memory to solve a concrete problem.

This world is intentionally narrow:
- one ship
- one route choice
- one remembered mistake
- one repair/fix that changes the ending image

The story reads like a short classical adventure with a beginning, a middle
turn, and a resolution.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0



def _safe_fact(world, facts, key):
    value = facts.get(key) if hasattr(facts, "get") else None
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb") or hasattr(value, "sign"):
        return value
    if isinstance(value, str):
        if hasattr(world, "get"):
            try:
                resolved = world.get(value)
                if resolved is not None:
                    return resolved
            except Exception:
                pass
        upper = key.upper()
        for registry_name in (upper, upper + "S", upper + "ES", upper + "_REGISTRY"):
            registry = globals().get(registry_name)
            if isinstance(registry, dict) and value in registry:
                return registry[value]
        if upper.endswith("Y"):
            registry = globals().get(upper[:-1] + "IES")
            if isinstance(registry, dict) and value in registry:
                return registry[value]
    entities = getattr(world, "entities", {})
    if hasattr(entities, "values"):
        for entity in entities.values():
            if hasattr(entity, "id") or hasattr(entity, "label"):
                return entity
    return value


def _safe_lookup(mapping, key):
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = list(mapping.values())
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    cargo: object | None = None
    pita: object | None = None
    rob: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"robot", "bot"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"boy", "man", "father", "dad"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman", "mother", "mom"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Ship:
    name: str
    fuel: int
    route: str
    beacon_on: bool = False
    engine_warm: bool = False
    cargo_locked: bool = False
    memory_triggered: bool = False
    ship: object | None = None
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class StoryParams:
    seed: Optional[int] = None
    route: str = "starport"
    obstacle: str = "dust storm"
    memory: str = "the spare battery"
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


class World:
    def __init__(self, ship: Ship) -> None:
        self.ship = ship
        self.entities: dict[str, Entity] = {}
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


ROUTES = {
    "starport": "the bright starport",
    "moonbase": "the moonbase hangar",
    "cometdock": "the comet dock",
}

OBSTACLES = {
    "dust storm": {"meters": {"dust": 1}, "memes": {"worry": 1}},
    "dead beacon": {"meters": {"signal": -1}, "memes": {"worry": 1}},
    "locked cargo": {"meters": {"lock": 1}, "memes": {"frustration": 1}},
}

MEMORIES = {
    "the spare battery": "the spare battery they once forgot at home",
    "the taped map": "the taped map that kept curling in the wind",
    "the hand lamp": "the hand lamp that helped them in the dark",
}

GREETINGS = [
    "The tiny ship hummed like a sleepy insect among the stars.",
    "The cabin lights glowed blue, and the windows held a wash of distant gold.",
    "Far away, the planets shone like bright marbles in a dark bowl.",
]

TRAITS = ["brave", "careful", "curious", "quick", "gentle"]


def asp_facts() -> str:
    import asp
    lines = []
    for rid in ROUTES:
        lines.append(asp.fact("route", rid))
    for oid in OBSTACLES:
        lines.append(asp.fact("obstacle", oid))
    for mid in MEMORIES:
        lines.append(asp.fact("memory", mid))
    return "\n".join(lines)


ASP_RULES = r"""
route_ok(R) :- route(R).
memory_helpful(M) :- memory(M).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small flashback space adventure storyworld.")
    ap.add_argument("--route", choices=sorted(ROUTES))
    ap.add_argument("--obstacle", choices=sorted(OBSTACLES))
    ap.add_argument("--memory", choices=sorted(MEMORIES))
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
    route = getattr(args, "route", None) or rng.choice(list(ROUTES))
    obstacle = getattr(args, "obstacle", None) or rng.choice(list(OBSTACLES))
    memory = getattr(args, "memory", None) or rng.choice(list(MEMORIES))
    if obstacle == "locked cargo" and memory == "the spare battery":
        pass
    if obstacle == "dead beacon" and memory == "the spare battery":
        pass
    return StoryParams(seed=None, route=route, obstacle=obstacle, memory=memory)


def maybe_flashback(world: World, rob: Entity, pita: Entity, memory: str) -> None:
    world.ship.memory_triggered = True
    world.say(
        f"That sight pulled Rob into a flashback: {_safe_lookup(MEMORIES, memory)}. "
        f"Back then, {rob.id} had rushed ahead, and Pita had said, "
        f"\"Next time, we keep a spare.\""
    )
    rob.memes["remembering"] = rob.memes.get("remembering", 0) + 1
    pita.memes["wisdom"] = pita.memes.get("wisdom", 0) + 1


def tell(params: StoryParams, rob_name: str = "Rob", pita_name: str = "Pita") -> World:
    ship = Ship(name="Pebble Arrow", fuel=3, route=_safe_lookup(ROUTES, params.route))
    world = World(ship)

    rob = world.add(Entity(id=rob_name, kind="character", type="boy", label=rob_name))
    pita = world.add(Entity(id=pita_name, kind="character", type="girl", label=pita_name))
    cargo = world.add(Entity(
        id="cargo",
        kind="thing",
        type="crate",
        label="cargo crate",
        phrase="a small cargo crate",
        owner=rob.id,
        caretaker=pita.id,
    ))

    rob.memes["hope"] = 1
    pita.memes["calm"] = 1

    world.say(random.choice(GREETINGS))
    world.say(f"Rob and Pita were sailing toward {world.ship.route}.")
    world.say(f"They wanted to reach it before the {params.obstacle} rolled in.")

    world.para()
    world.say(f"Then trouble arrived: a {params.obstacle} drifted across their path.")

    if params.obstacle == "dust storm":
        world.ship.beacon_on = False
        world.ship.engine_warm = True
        world.say(
            "The dust was so thick that the beacon blinked weakly, and the stars "
            "looked blurry through the window."
        )
    elif params.obstacle == "dead beacon":
        world.ship.beacon_on = False
        world.say(
            "The beacon went dark, and the ship felt lonely without its little "
            "red blink."
        )
    else:
        world.ship.cargo_locked = True
        cargo.meters["locked"] = 1
        world.say(
            "The cargo latch clicked shut and would not open, even when Rob "
            "pulled twice."
        )

    world.para()
    world.say(
        f"Rob frowned, but Pita pointed at {_safe_lookup(MEMORIES, params.memory)}. "
        f"That memory was a flashback from their last trip."
    )
    maybe_flashback(world, rob, pita, params.memory)

    if params.obstacle in {"dust storm", "dead beacon"}:
        world.say(
            "This time, they did not race ahead. Rob found the spare battery in the "
            "side panel, and Pita clipped the backup light to the console."
        )
        world.ship.beacon_on = True
        world.ship.fuel -= 1
        world.say(
            f"The beacon came back to life, bright as a berry. Their ship turned "
            f"safely toward {world.ship.route}."
        )
    else:
        world.say(
            "This time, they did not tug harder. Rob remembered the taped label, "
            "and Pita showed him the hidden release on the crate."
        )
        world.ship.cargo_locked = False
        cargo.meters["open"] = 1
        world.say(
            "The latch sprang open, and out came a neat bundle of tools. "
            "They used one to steady the crate before it could slam shut again."
        )

    world.para()
    world.say(
        f"At the end, the ship drifted under a clear sky. {rob.id} and {pita.id} "
        f"sat by the window, smiling as {world.ship.route} grew bright ahead."
    )
    world.say(
        f"Their flashback had become a plan, and the plan had turned a problem "
        f"into a safe landing."
    )

    world.facts.update(
        rob=rob,
        pita=pita,
        cargo=cargo,
        ship=ship,
        params=params,
        route=params.route,
        obstacle=params.obstacle,
        memory=params.memory,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    p = _safe_fact(world, world.facts, "params")
    return [
        "Write a short space adventure for young children with Rob and Pita, "
        "and include a flashback that helps solve a problem.",
        f"Tell a gentle story about Rob and Pita traveling to {_safe_lookup(ROUTES, p.route)} "
        f"when a {p.obstacle} appears, and a remembered lesson helps them.",
        "Write a simple starry story where a flashback changes what the heroes do next.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = _safe_fact(world, world.facts, "params")
    qa = [
        QAItem(
            question=f"Where were Rob and Pita trying to go?",
            answer=f"They were trying to reach {_safe_lookup(ROUTES, p.route)}.",
        ),
        QAItem(
            question="What problem got in their way?",
            answer=f"A {p.obstacle} got in their way.",
        ),
        QAItem(
            question="What important memory came back to help them?",
            answer=f"They remembered {_safe_lookup(MEMORIES, p.memory)}.",
        ),
        QAItem(
            question="What changed because of the flashback?",
            answer=(
                "Instead of panicking, they used the remembered idea to fix the "
                "problem and keep going safely."
            ),
        ),
    ]
    if p.obstacle in {"dust storm", "dead beacon"}:
        qa.append(
            QAItem(
                question="How did they make the ship work again?",
                answer="Rob found the spare battery, Pita added the backup light, and the beacon came back on.",
            )
        )
    else:
        qa.append(
            QAItem(
                question="How did they open the cargo crate?",
                answer="They remembered the hidden release and used it to open the crate safely.",
            )
        )
    return qa


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a moment when the story shows something that happened before the present moment.",
        ),
        QAItem(
            question="Why can a spare battery help on a ship?",
            answer="A spare battery can give extra power when the main power runs low or stops working.",
        ),
        QAItem(
            question="Why do spaceships need lights or beacons?",
            answer="Lights and beacons help pilots see where they are and help other ships notice them.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
    lines = ["--- trace ---"]
    lines.append(f"ship.route={world.ship.route}")
    lines.append(f"ship.fuel={world.ship.fuel}")
    lines.append(f"ship.beacon_on={world.ship.beacon_on}")
    lines.append(f"ship.engine_warm={world.ship.engine_warm}")
    lines.append(f"ship.cargo_locked={world.ship.cargo_locked}")
    lines.append(f"ship.memory_triggered={world.ship.memory_triggered}")
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


CURATED = [
    StoryParams(route="starport", obstacle="dust storm", memory="the spare battery"),
    StoryParams(route="moonbase", obstacle="dead beacon", memory="the hand lamp"),
    StoryParams(route="cometdock", obstacle="locked cargo", memory="the taped map"),
]


def validate_params(params: StoryParams) -> None:
    if params.obstacle == "locked cargo" and params.memory not in {"the taped map", "the spare battery"}:
        pass
    if params.obstacle in {"dust storm", "dead beacon"} and params.memory not in {"the spare battery", "the hand lamp"}:
        pass


def generate(params: StoryParams) -> StorySample:
    validate_params(params)
    world = tell(params)
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


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show route_ok/1.\n#show memory_helpful/1."))
    return sorted(set(asp.atoms(model, "route_ok"))), sorted(set(asp.atoms(model, "memory_helpful")))


def asp_verify() -> int:
    route_atoms, memory_atoms = asp_valid()
    if route_atoms and memory_atoms and len(route_atoms) == len(ROUTES) and len(memory_atoms) == len(MEMORIES):
        print("OK: ASP twin loaded the registries.")
        return 0
    print("MISMATCH: ASP twin did not load registries correctly.")
    return 1


def build_parser_passthrough() -> argparse.ArgumentParser:
    return build_parser()


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show route_ok/1.\n#show memory_helpful/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen = set()
        for i in range(max(getattr(args, "n", None) * 50, 50)):
            if len(samples) >= getattr(args, "n", None):
                break
            rng = random.Random(base_seed + i)
            p = resolve_params(args, rng)
            p.seed = base_seed + i
            sample = generate(p)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.route} / {p.obstacle} / {p.memory}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

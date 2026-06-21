#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/bra_quest_sound_effects_twist_space_adventure.py
=================================================================================

A standalone storyworld for a tiny space-adventure quest with sound effects and a
twist: a little astronaut searches the ship for a lost bra, follows noisy clues
through the station, and discovers the bra belongs to the ship's repair kit all
along. The story is built from stateful entities with physical meters and
emotional memes, then rendered into child-facing prose.

This world supports:
- a quest to find the missing item
- sound-effect beats that move the search forward
- a twist that reinterprets what the bra is for
- an ending image proving the quest changed the world

The story includes the required seed word: bra.
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
class Ship:
    id: str
    name: str
    place: str
    rooms: list[str]
    twist_room: str
    quest_item: str
    sound_words: list[str]
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class StoryParams:
    ship: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_gender: str
    parent_role: str
    twist_room: str
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
        clone = World(self.ship)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
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


def _r_louder(world: World) -> list[str]:
    out: list[str] = []
    seeker = world.entities.get("hero")
    if not seeker or seeker.meters["questing"] < THRESHOLD:
        return out
    for room_id in world.ship.rooms:
        room = world.get(room_id)
        if room.meters["searched"] < THRESHOLD:
            continue
        sig = ("louder", room_id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        room.meters["signal"] += 1
        out.append("__signal__")
    return out


def _r_twist(world: World) -> list[str]:
    hero = world.entities.get("hero")
    helper = world.entities.get("helper")
    clue = world.entities.get("clue")
    if not hero or not helper or not clue:
        return []
    if clue.meters["found"] < THRESHOLD or clue.meters["understood"] >= THRESHOLD:
        return []
    sig = ("twist", clue.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    clue.meters["understood"] += 1
    helper.memes["surprise"] += 1
    return ["__twist__"]


CAUSAL_RULES: list[Rule] = [
    Rule("louder", "sound", _r_louder),
    Rule("twist", "story", _r_twist),
]


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


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for ship_id, ship in SHIPS.items():
        for room in ship.rooms:
            combos.append((ship_id, room))
    return combos


def quest_item_name() -> str:
    return "bra"


def predict_twist(world: World, room_id: str) -> dict:
    sim = world.copy()
    _search_room(sim, sim.get(room_id), narrate=False)
    clue = sim.get("clue")
    return {"found": clue.meters["found"] >= THRESHOLD, "understood": clue.meters["understood"] >= THRESHOLD}


def _search_room(world: World, room: Entity, narrate: bool = True) -> None:
    room.meters["searched"] += 1
    room.memes["mystery"] += 1
    propagate(world, narrate=narrate)


def visit(world: World, hero: Entity, helper: Entity) -> None:
    world.say(
        f"On the bright ship {world.ship.name}, {hero.id} and {helper.id} were ready for a quest."
    )
    world.say(
        f"They were searching for a lost {world.ship.quest_item}, and the hallway hummed with the promise of adventure."
    )


def clue_start(world: World, hero: Entity, helper: Entity) -> None:
    world.say(
        f"Their map led to the first room, and then the station answered with a tiny sound: "
        f"beep-beep from a blinking panel."
    )
    helper.memes["curiosity"] += 1
    hero.memes["joy"] += 1


def sound_effect(world: World, room: Entity, sound: str) -> None:
    room.meters["sound"] += 1
    world.say(f"{sound}! The noise bounced off the walls and pointed them to the next place.")


def search(world: World, hero: Entity, helper: Entity, room: Entity) -> None:
    hero.meters["questing"] += 1
    helper.meters["questing"] += 1
    _search_room(world, room)
    clue = world.get("clue")
    clue.meters["found"] += 1
    world.say(f"They peeked behind the crates and under the seat cushions, but at first they only found dust and bolts.")


def reveal_twist(world: World, hero: Entity, helper: Entity) -> None:
    clue = world.get("clue")
    clue.meters["understood"] += 1
    helper.memes["surprise"] += 1
    world.say(
        f"Then came the twist: the missing bra was not lost laundry at all."
    )
    world.say(
        f"It was the soft strap for the repair kit, the kind the mechanics used to keep a tool pouch snug during a bumpy ride."
    )


def return_item(world: World, hero: Entity, helper: Entity, room: Entity) -> None:
    room.meters["order"] += 1
    world.get("clue").meters["returned"] += 1
    hero.memes["pride"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"{hero.id} tucked the bra back into the repair kit, right where it belonged."
    )


def ending(world: World, hero: Entity, helper: Entity) -> None:
    world.say(
        f"After that, the ship felt neat and ready again, and {hero.id} and {helper.id} floated down the hallway smiling."
    )
    world.say(
        f"Everywhere they went, the ship answered with soft little sounds -- beep, zip, and humm -- as their quest turned into a solved mystery."
    )


def tell(ship: Ship, twist_room: str, hero_name: str = "Mina", hero_gender: str = "girl",
         helper_name: str = "Jae", helper_gender: str = "boy", parent_role: str = "captain") -> World:
    world = World(ship)
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="seeker"))
    helper = world.add(Entity(id="helper", kind="character", type=helper_gender, label=helper_name, role="helper"))
    parent = world.add(Entity(id="parent", kind="character", type="adult", label=parent_role, role="leader"))
    corridor = world.add(Entity(id="corridor", type="room", label="corridor"))
    room = world.add(Entity(id=twist_room, type="room", label=twist_room))
    clue = world.add(Entity(id="clue", type="thing", label="bra", role="quest_item"))

    world.facts.update(hero=hero, helper=helper, parent=parent, room=room, clue=clue, ship=ship, twist_room=twist_room)

    visit(world, hero, helper)
    clue_start(world, hero, helper)
    world.para()
    search(world, hero, helper, corridor)
    sound_effect(world, corridor, "clang")
    search(world, hero, helper, room)
    sound_effect(world, room, "whirr")
    reveal_twist(world, hero, helper)
    world.para()
    return_item(world, hero, helper, room)
    ending(world, hero, helper)
    world.facts["resolved"] = True
    return world


SHIPS = {
    "starship": Ship(
        id="starship",
        name="the Bright Comet",
        place="space",
        rooms=["corridor", "cargo_bay", "control_room"],
        twist_room="cargo_bay",
        quest_item="bra",
        sound_words=["beep", "whirr", "clang"],
    ),
    "moonbase": Ship(
        id="moonbase",
        name="the Moon Lantern",
        place="space",
        rooms=["corridor", "lab", "locker"],
        twist_room="locker",
        quest_item="bra",
        sound_words=["beep", "zip", "humm"],
    ),
}

CURATED = [
    StoryParams(ship="starship", hero_name="Mina", hero_gender="girl", helper_name="Jae", helper_gender="boy", parent_role="captain", twist_room="cargo_bay"),
    StoryParams(ship="moonbase", hero_name="Nori", hero_gender="girl", helper_name="Kai", helper_gender="boy", parent_role="captain", twist_room="locker"),
]


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a space adventure quest story that includes the word '{world.facts['clue'].label}' and ends with a twist.",
        f"Tell a child-friendly spaceship mystery where {world.facts['hero'].label} and {world.facts['helper'].label} search for a bra using sound effects.",
        "Write a short story about a lost item on a spaceship, noisy clues, and a surprise reveal."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    clue = world.facts["clue"]
    room = world.facts["room"]
    return [
        ("What were the characters looking for?",
         "They were looking for a bra. It was the item that started the whole space quest."),
        ("What made the search feel exciting?",
         "The sound effects made each room feel alive. The beeps, clangs, and whirs turned the search into an adventure."),
        ("What was the twist?",
         "The bra was not lost laundry at all. It belonged to the repair kit, so the mystery ended with a useful surprise."),
        (f"What did {hero.label} and {helper.label} do at the end?",
         f"They put the bra back in the repair kit and smiled as the ship felt calm again. The quest was finished, and the ending showed the item had found its right place."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a quest?",
         "A quest is a search for something important. In stories, it often means following clues until the goal is found."),
        ("What are sound effects in a story?",
         "Sound effects are words that let you imagine noises, like beep, clang, zip, or humm. They make the scene feel lively."),
        ("What is a twist in a story?",
         "A twist is a surprise that changes how you understand the story. It makes the ending feel new and a little unexpected."),
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(ship_id: str, room_id: str) -> str:
    return f"(No story: the room '{room_id}' is not part of the ship '{ship_id}' in this little quest.)"


ASP_RULES = r"""
questing(hero).
searched(Room) :- room(Room).
signal(Room) :- searched(Room).
twist(clue) :- found(clue), not understood(clue).
understood(clue) :- found(clue), twist(clue).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid, ship in SHIPS.items():
        lines.append(asp.fact("ship", sid))
        for room in ship.rooms:
            lines.append(asp.fact("room", room))
            lines.append(asp.fact("room_of", sid, room))
        lines.append(asp.fact("quest_item", ship.quest_item))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show room_of/2."))
    return sorted(set(asp.atoms(model, "room_of")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP combos match valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in ASP combos.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(0)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure quest with sound effects and a twist.")
    ap.add_argument("--ship", choices=SHIPS)
    ap.add_argument("--twist-room", choices=["cargo_bay", "control_room", "locker", "lab", "corridor"])
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--parent", choices=["captain", "commander", "chief"])
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
    ship_id = args.ship or rng.choice(list(SHIPS))
    ship = SHIPS[ship_id]
    twist_room = args.twist_room or ship.twist_room
    if twist_room not in ship.rooms:
        raise StoryError(explain_rejection(ship_id, twist_room))
    return StoryParams(
        ship=ship_id,
        hero_name=args.name or rng.choice(["Mina", "Nori", "Luna", "Tali", "Rae"]),
        hero_gender="girl",
        helper_name=args.helper or rng.choice(["Jae", "Kai", "Ollie", "Pip", "Bo"]),
        helper_gender="boy",
        parent_role=args.parent or rng.choice(["captain", "commander", "chief"]),
        twist_room=twist_room,
    )


def generate(params: StoryParams) -> StorySample:
    if params.ship not in SHIPS:
        raise StoryError(f"Unknown ship: {params.ship}")
    ship = SHIPS[params.ship]
    if params.twist_room not in ship.rooms:
        raise StoryError(explain_rejection(params.ship, params.twist_room))
    world = tell(ship, params.twist_room, params.hero_name, params.hero_gender,
                 params.helper_name, params.helper_gender, params.parent_role)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("#show room_of/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_combos())} compatible ship-room combos:\n")
        for ship_id, room in valid_combos():
            print(f"  {ship_id:10} {room}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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

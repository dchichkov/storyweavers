#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/motto_bounty_love_gerund_flashback_dialogue_twist.py
====================================================================================

A small pirate-tale storyworld about a crew, a shared motto, a bounty poster,
and a child-sized twist that is revealed through flashback and dialogue.

The world is built around:
- a captain and a young deckhand
- a ship with a tiny hidden secret
- a bounty hunt that changes into a rescue
- a flashback that explains why the crew trusts its motto
- a final twist that turns a greedy plan into a kinder ending

Seed words required by the prompt:
- motto
- bounty
- love-gerund

Narrative instruments required by the prompt:
- Flashback
- Dialogue
- Twist

The prose is intentionally compact and child-facing, with state driving the
scene order and the ending image.
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
CONFIDENCE_START = 4.0


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
        female = {"girl", "mother", "mom", "woman", "queen"}
        male = {"boy", "father", "dad", "man", "captain", "pirate"}
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
class Place:
    id: str
    label: str
    dark: str
    has_hiding: bool = False
    has_map: bool = False
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
class Treasure:
    id: str
    label: str
    phrase: str
    value: int
    hidden: bool = False
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
class Bounty:
    id: str
    label: str
    prize: str
    greed: int
    wanted_for: str
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
    captain: str
    deckhand: str
    treasure: str
    bounty: str
    motive: str
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


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


def _r_spook(world: World) -> list[str]:
    out: list[str] = []
    if world.get("ship").meters["trouble"] >= THRESHOLD and ("spook",) not in world.fired:
        world.fired.add(("spook",))
        for eid in ("captain", "deckhand"):
            world.get(eid).memes["worry"] += 1
        out.append("__spook__")
    return out


def _r_soften(world: World) -> list[str]:
    out: list[str] = []
    if world.get("captain").memes["memory"] >= THRESHOLD and ("soften",) not in world.fired:
        world.fired.add(("soften",))
        world.get("deckhand").memes["trust"] += 1
        out.append("__soften__")
    return out


CAUSAL_RULES = [Rule("spook", _r_spook), Rule("soften", _r_soften)]


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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for bounty_id, bounty in BOUNTIES.items():
            for treasure_id, treasure in TREASURES.items():
                if place.has_hiding and treasure.hidden and bounty.greed >= 2:
                    combos.append((place_id, bounty_id, treasure_id))
    return combos


def choose_name(rng: random.Random, pool: list[str], avoid: str = "") -> str:
    names = [n for n in pool if n != avoid]
    return rng.choice(names)


def flashback(world: World, captain: Entity, deckhand: Entity, place: Place) -> None:
    captain.memes["memory"] += 1
    world.say(
        f"Years before, in the same {place.label}, {captain.id} had taught {deckhand.id} a motto: "
        f"\"We take only what keeps the crew safe, and we never leave a friend behind.\""
    )
    world.say(
        f"{deckhand.id} remembered that old lesson whenever the sea grew dark."
    )


def setup(world: World, captain: Entity, deckhand: Entity, place: Place, treasure: Treasure, bounty: Bounty) -> None:
    world.say(
        f"On a windy evening, {captain.id} and {deckhand.id} crept through {place.label} with a lantern and a map."
    )
    world.say(
        f"They were hunting a {bounty.label}, but what they really wanted was {treasure.phrase}."
    )
    if "motto" not in world.facts["story_words"]:
        world.facts["story_words"].append("motto")


def desire(world: World, captain: Entity, treasure: Treasure) -> None:
    captain.memes["want"] += 1
    world.say(
        f"{captain.id} smiled at the glittering chest. \"I love-hoarding\" was not their motto, but the gold still twinkled like trouble."
    )


def dialogue(world: World, deckhand: Entity, captain: Entity, bounty: Bounty, treasure: Treasure) -> None:
    deckhand.memes["caution"] += 1
    world.say(
        f"\"Captain,\" said {deckhand.id}, \"that bounty is only a paper promise. Should we really chase it over a friend?\""
    )
    world.say(
        f"{captain.id} frowned, then looked at {treasure.label} and the torn {bounty.label} poster."
    )


def twist(world: World, captain: Entity, deckhand: Entity, treasure: Treasure, bounty: Bounty) -> None:
    if treasure.hidden:
        world.say(
            f"Then came the twist: the 'wanted' face on the poster was not a thief at all. It was the ship's old cook, hiding to keep the gold from a greedy lord."
        )
    else:
        world.say(
            f"Then came the twist: the bounty poster was a trick, and the real prize was the lost map tucked inside the treasure chest."
        )


def rescue(world: World, captain: Entity, deckhand: Entity, treasure: Treasure, bounty: Bounty) -> None:
    captain.memes["kindness"] += 1
    deckhand.memes["joy"] += 1
    world.get("ship").meters["trouble"] = 0
    world.say(
        f"{captain.id} ripped the bounty poster in half and laughed. \"Our motto matters more than a reward,\" {captain.pronoun()} said."
    )
    world.say(
        f"They used the map to free {treasure.label} instead of stealing it, and the crew cheered when the hidden lock clicked open."
    )


def ending(world: World, captain: Entity, deckhand: Entity, treasure: Treasure) -> None:
    world.say(
        f"In the end, {captain.id} and {deckhand.id} sailed home with clean hands, a safe treasure, and the old motto shining brighter than gold."
    )
    world.say(
        f"{deckhand.id} tucked the paper motto into a pocket beside a tiny shell, and the moon lit the deck like a gentle lantern."
    )


def tell(params: StoryParams) -> World:
    world = World()
    place = PLACES[params.place]
    treasure = TREASURES[params.treasure]
    bounty = BOUNTIES[params.bounty]

    captain = world.add(Entity(id=params.captain, kind="character", type="captain", role="captain"))
    deckhand = world.add(Entity(id=params.deckhand, kind="character", type="deckhand", role="deckhand"))
    ship = world.add(Entity(id="ship", kind="thing", type="ship", label="the ship"))

    world.facts["story_words"] = []

    setup(world, captain, deckhand, place, treasure, bounty)
    world.para()
    flashback(world, captain, deckhand, place)
    desire(world, captain, treasure)
    dialogue(world, deckhand, captain, bounty, treasure)

    world.para()
    ship.meters["trouble"] += 1
    propagate(world, narrate=False)
    twist(world, captain, deckhand, treasure, bounty)
    rescue(world, captain, deckhand, treasure, bounty)

    world.para()
    ending(world, captain, deckhand, treasure)

    world.facts.update(
        captain=captain,
        deckhand=deckhand,
        place=place,
        treasure=treasure,
        bounty=bounty,
        ship=ship,
        outcome="changed",
    )
    return world


PLACES = {
    "cove": Place(
        id="cove",
        label="the moonlit cove",
        dark="dark rocks",
        has_hiding=True,
        has_map=True,
        tags={"sea", "hidden"},
    ),
    "dock": Place(
        id="dock",
        label="the old dock",
        dark="wet planks",
        has_hiding=True,
        has_map=True,
        tags={"sea", "hidden"},
    ),
    "island": Place(
        id="island",
        label="the little island cave",
        dark="shadowy stone",
        has_hiding=True,
        has_map=True,
        tags={"sea", "hidden"},
    ),
}

TREASURES = {
    "chest": Treasure(
        id="chest",
        label="the silver chest",
        phrase="the silver chest",
        value=5,
        hidden=True,
        tags={"gold", "secret"},
    ),
    "map": Treasure(
        id="map",
        label="the rolled map",
        phrase="the rolled map",
        value=3,
        hidden=True,
        tags={"map", "secret"},
    ),
    "ring": Treasure(
        id="ring",
        label="the pearl ring",
        phrase="the pearl ring",
        value=2,
        hidden=True,
        tags={"pearl", "secret"},
    ),
}

BOUNTIES = {
    "poster": Bounty(
        id="poster",
        label="bounty poster",
        prize="coins",
        greed=3,
        wanted_for="a greedy lord",
        tags={"poster", "paper"},
    ),
    "reward": Bounty(
        id="reward",
        label="wanted reward",
        prize="gold",
        greed=2,
        wanted_for="a captain's purse",
        tags={"reward", "paper"},
    ),
}


GIRL_NAMES = ["Lina", "Mina", "Ruby", "Nia", "Pip"]
BOY_NAMES = ["Finn", "Owen", "Jory", "Tate", "Bram"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a pirate tale for a young child that includes the words "motto", "bounty", and "love-gerund".',
        f"Tell a story where {f['captain'].id} and {f['deckhand'].id} chase a bounty, remember a motto in a flashback, and end with a twist.",
        f"Write a gentle pirate story with dialogue, a hidden truth, and a safe ending about {f['treasure'].label} at {f['place'].label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    captain: Entity = f["captain"]
    deckhand: Entity = f["deckhand"]
    treasure: Treasure = f["treasure"]
    bounty: Bounty = f["bounty"]
    place: Place = f["place"]
    return [
        QAItem(
            question="What were the pirates looking for?",
            answer=f"They were looking for {treasure.phrase} and followed a bounty poster to find it. In the end, they learned the poster was not the most important thing."
        ),
        QAItem(
            question="What did the flashback explain?",
            answer=f"The flashback explained the crew's motto: they keep everyone safe and never leave a friend behind. That old memory helped {deckhand.id} speak up before the plan went wrong."
        ),
        QAItem(
            question="What was the twist?",
            answer=f"The twist was that the bounty was not a true treasure hunt at all. The wanted person was hiding to protect the gold, so the pirates chose kindness instead of greed."
        ),
        QAItem(
            question=f"What did {deckhand.id} say in the dialogue?",
            answer=f"{deckhand.id} asked whether they should chase a paper reward over a friend. That question made {captain.id} stop and think."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a motto?",
            answer="A motto is a short saying people repeat to remember what matters most. Crews use mottos to stay brave and do the right thing."
        ),
        QAItem(
            question="What is a bounty?",
            answer="A bounty is a reward offered for finding something or someone. In pirate stories, it can make a greedy person chase the wrong thing."
        ),
        QAItem(
            question="What does love-gerund mean in a story prompt?",
            answer="It points to a loving action word ending in -ing, like loving sailing or loving sharing. Writers use it to show what someone enjoys doing."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==",]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
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
    lines.append(f"  fired rules: {sorted({name for (name,) in world.fired})}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: the chosen pirate path has no hidden place for a flashback twist.)"


ASP_RULES = r"""
valid(P, B, T) :- place(P), bounty(B), treasure(T), hidden(T), hidey(P), greed(B, G), G >= 2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.has_hiding:
            lines.append(asp.fact("hidey", pid))
    for bid, b in BOUNTIES.items():
        lines.append(asp.fact("bounty", bid))
        lines.append(asp.fact("greed", bid, b.greed))
    for tid, t in TREASURES.items():
        lines.append(asp.fact("treasure", tid))
        if t.hidden:
            lines.append(asp.fact("hidden", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in ASP parity.")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(0)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: smoke test generated a non-empty story.")
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with motto, bounty, love-gerund, flashback, dialogue, and twist.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--captain", choices=GIRL_NAMES + BOY_NAMES)
    ap.add_argument("--deckhand", choices=GIRL_NAMES + BOY_NAMES)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--bounty", choices=BOUNTIES)
    ap.add_argument("--motive", choices=["greed", "kindness", "curiosity"])
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.bounty:
        combos = [c for c in combos if c[1] == args.bounty]
    if args.treasure:
        combos = [c for c in combos if c[2] == args.treasure]
    if not combos:
        raise StoryError(explain_rejection())
    place, bounty, treasure = rng.choice(sorted(combos))
    captain = args.captain or rng.choice(GIRL_NAMES + BOY_NAMES)
    deckhand = args.deckhand or choose_name(rng, GIRL_NAMES + BOY_NAMES, avoid=captain)
    motive = args.motive or rng.choice(["greed", "kindness", "curiosity"])
    return StoryParams(place=place, captain=captain, deckhand=deckhand, treasure=treasure, bounty=bounty, motive=motive)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.bounty not in BOUNTIES or params.treasure not in TREASURES:
        raise StoryError("Invalid story parameters.")
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(place=p, captain="Finn", deckhand="Mina", treasure=t, bounty=b, motive="kindness")) for p, b, t in valid_combos()[:3]]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

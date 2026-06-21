#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/survive_toot_riverbank_happy_ending_dialogue_sharing.py
=======================================================================================

A small, self-contained storyworld set on a misty riverbank.

Premise:
- A child hears a mysterious toot by the river.
- A worried friend and a kind grown-up follow clues, talk, and share supplies.
- The mystery turns out harmless, and everyone survives with a happy ending.

Required flavor from the seed:
- Words: survive, toot
- Setting: riverbank
- Features: happy ending, dialogue, sharing
- Style: mystery

This script follows the shared Storyweavers contract:
- stdlib-only story engine
- typed entities with meters and memes
- Python reasonableness gate plus inline ASP twin
- prompts, story QA, and world QA generated from world state
- --verify runs parity checks and a smoke test
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

MYSTERY_MIN = 1
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
    safe: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
class Item:
    id: str
    label: str
    phrase: str
    tags: set[str] = field(default_factory=set)
    risky: bool = False
    helpful: bool = False
    shareable: bool = False
    sounds_like: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))


@dataclass
class Setting:
    id: str
    place: str
    misty: bool = True
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
    setting: str = "riverbank"
    mystery: str = "missing_boat"
    share_item: str = "flashlight"
    clue_item: str = "lantern"
    toot_source: str = "ferry"
    child_name: str = "Mina"
    child_gender: str = "girl"
    friend_name: str = "Owen"
    friend_gender: str = "boy"
    adult_name: str = "Grandpa"
    adult_gender: str = "man"
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.items: dict[str, Item] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add_entity(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_item(self, item: Item) -> Item:
        self.items[item.id] = item
        return item

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.items = copy.deepcopy(self.items)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting_id in SETTINGS:
        for mystery_id in MYSTERIES:
            for share_id in ITEMS:
                combos.append((setting_id, mystery_id, share_id))
    return combos


def reasonableness_gate(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.mystery not in MYSTERIES:
        raise StoryError("Unknown mystery.")
    if params.share_item not in ITEMS:
        raise StoryError("Unknown sharing item.")
    if params.clue_item not in ITEMS:
        raise StoryError("Unknown clue item.")
    if params.toot_source not in TOOT_SOURCES:
        raise StoryError("Unknown toot source.")
    if not ITEMS[params.share_item].shareable:
        raise StoryError(f"{params.share_item} is not something the children can share.")
    if not ITEMS[params.clue_item].helpful:
        raise StoryError(f"{params.clue_item} does not fit the mystery well.")


def _share(world: World, a: Entity, b: Entity, item: Item) -> None:
    item.meters["shared"] += 1
    a.memes["together"] += 1
    b.memes["together"] += 1


def _calm(world: World, child: Entity) -> None:
    child.memes["fear"] = max(0.0, child.memes["fear"] - 1.0)
    child.memes["hope"] += 1


def _resolve_mystery(world: World) -> None:
    if world.facts.get("shared") and world.facts.get("told_adult"):
        world.facts["safe"] = True


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    world = World(setting)

    child = world.add_entity(Entity(
        id=params.child_name, kind="character", type=params.child_gender,
        role="child",
    ))
    friend = world.add_entity(Entity(
        id=params.friend_name, kind="character", type=params.friend_gender,
        role="friend",
    ))
    adult = world.add_entity(Entity(
        id=params.adult_name, kind="character", type=params.adult_gender,
        role="adult",
    ))
    share_item = world.add_item(ITEMS[params.share_item])
    clue_item = world.add_item(ITEMS[params.clue_item])
    toot_source = TOOT_SOURCES[params.toot_source]

    child.memes["curiosity"] = 2
    friend.memes["curiosity"] = 2
    child.memes["fear"] = 1
    friend.memes["fear"] = 1

    world.say(
        f"At the {setting.place}, mist curled over the water and hid the reeds like secrets."
    )
    world.say(
        f"Then a sound floated out of the fog. {toot_source.sound.capitalize()}."
    )
    world.say(
        f'"Did you hear that?" {child.id} whispered. "{toot_source.question}"'
    )

    world.para()
    world.say(
        f'{friend.id} leaned closer to the bank. "Maybe it was {clue_item.phrase}," '
        f'{friend.pronoun()} said. "Or maybe somebody needs help."'
    )
    world.say(
        f'{child.id} frowned. "We should be careful. I do not want us to need to survive '
        f'a real problem."'
    )
    world.facts["heard_toot"] = True
    world.facts["question"] = toot_source.question

    world.para()
    world.say(
        f"{child.id} and {friend.id} looked at each other, then they shared {share_item.phrase}."
    )
    _share(world, child, friend, share_item)
    world.say(
        f'"You hold this," {child.id} said, handing {share_item.label} to {friend.id}. '
        f'"I will keep watching the water."'
    )
    world.say(
        f'"And I will hold the clue," {friend.id} answered, lifting {clue_item.label}."
    )
    world.facts["shared"] = True

    world.para()
    world.say(
        f"They followed the trail by the mud, and the toot came again, softer this time."
    )
    world.say(
        f"{adult.id} stepped out from behind a willow tree, carrying a small tin boat."
    )
    world.say(
        f'"There you are," {adult.id} said. "The horn on the ferry got loose, so it made that toot."'
    )
    world.say(
        f'"We thought the river was hiding a secret," {child.id} said.'
    )
    world.say(
        f'"It was hiding a toy, not a danger," {adult.id} replied with a smile."
    )
    world.facts["told_adult"] = True

    world.para()
    _calm(world, child)
    _calm(world, friend)
    _resolve_mystery(world)
    world.say(
        f"{adult.id} laughed and let them take turns looking inside the tiny boat."
    )
    world.say(
        f'{friend.id} held up the lantern and said, "Next time, we share the light first."'
    )
    world.say(
        f'"And we ask questions," {child.id} added. "That is how we survive mysteries."'
    )
    world.say(
        f"So they walked home together, the river quiet behind them, and the toot turned into a story they could tell."
    )

    world.facts.update(
        child=child, friend=friend, adult=adult, share_item=share_item,
        clue_item=clue_item, toot_source=toot_source, outcome="happy",
        safe=True, setting=setting,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a mystery story set at the {world.setting.place} that includes the words survive and toot.",
        f"Tell a gentle riverbank mystery where {world.facts['child'].id} and {world.facts['friend'].id} share a tool, ask questions, and discover the toot was harmless.",
        "Write a happy-ending story about a curious child, a shared flashlight, and a mysterious toot by the water.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    friend = world.facts["friend"]
    adult = world.facts["adult"]
    share_item = world.facts["share_item"]
    clue_item = world.facts["clue_item"]
    toot_source = world.facts["toot_source"]
    return [
        QAItem(
            question="What did the children hear by the riverbank?",
            answer=f"They heard a toot in the fog. It sounded mysterious at first, so they looked around carefully before they guessed what it was.",
        ),
        QAItem(
            question="How did they handle the mystery?",
            answer=f"They shared {share_item.phrase}, talked to each other, and followed the clue together. Sharing helped them stay calm and work as a team.",
        ),
        QAItem(
            question=f"Why did {adult.id} say the toot was harmless?",
            answer=f"The toot came from the {toot_source.label}, not from a danger in the water. That meant the children could survive the surprise and laugh once the secret was solved.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a riverbank?",
            answer="A riverbank is the land right next to a river. People can stand there, look at the water, and watch for things floating by.",
        ),
        QAItem(
            question="What does it mean to share something?",
            answer="To share means to let someone else use or hold the same thing. Sharing helps people work together and feel less scared.",
        ),
        QAItem(
            question="What is a toot?",
            answer="A toot is a short sound, often made by a horn or whistle. It can startle people, but it is not always dangerous.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.memes:
            bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    for i in world.items.values():
        bits = []
        if i.meters:
            bits.append(f"meters={dict((k, v) for k, v in i.meters.items() if v)}")
        lines.append(f"  {i.id} ({i.label}) {' '.join(bits)}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


SETTINGS = {
    "riverbank": Setting(id="riverbank", place="riverbank", misty=True, tags={"water", "mystery"}),
}

MYSTERIES = {
    "missing_boat": Item(id="missing_boat", label="little boat", phrase="a little boat", tags={"boat"}, risky=False, helpful=True, shareable=False, sounds_like="a horn toot"),
    "fog_whistle": Item(id="fog_whistle", label="whistle", phrase="a whistle", tags={"whistle"}, risky=False, helpful=True, shareable=False, sounds_like="a toot"),
}

ITEMS = {
    "flashlight": Item(id="flashlight", label="flashlight", phrase="a flashlight", tags={"light"}, risky=False, helpful=True, shareable=True),
    "lantern": Item(id="lantern", label="lantern", phrase="a small lantern", tags={"light"}, risky=False, helpful=True, shareable=True),
    "rope": Item(id="rope", label="rope", phrase="a coil of rope", tags={"rope"}, risky=False, helpful=True, shareable=True),
    "map": Item(id="map", label="map", phrase="a folded map", tags={"map"}, risky=False, helpful=True, shareable=True),
}

TOOT_SOURCES = {
    "ferry": Item(id="ferry", label="ferry horn", phrase="the ferry horn", tags={"horn"}, risky=False, helpful=True, shareable=False, sounds_like="a toot", memes=defaultdict(float)),
    "toy_boat": Item(id="toy_boat", label="toy boat horn", phrase="the tiny boat horn", tags={"horn"}, risky=False, helpful=True, shareable=False, sounds_like="a toot", memes=defaultdict(float)),
}


ASP_RULES = r"""
valid(S, M, I) :- setting(S), mystery(M), item(I).
story_ready :- setting("riverbank"), mystery(_), item(_).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
    for tid in TOOT_SOURCES:
        lines.append(asp.fact("toot_source", tid))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set != python_set:
        rc = 1
        print("MISMATCH: ASP and Python valid_combos differ.")
    else:
        print(f"OK: ASP and Python agree on {len(clingo_set)} combos.")

    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {exc}")
        return 1

    print("OK: generate() smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A riverbank mystery world with a toot, sharing, and a happy ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--share-item", choices=ITEMS)
    ap.add_argument("--clue-item", choices=ITEMS)
    ap.add_argument("--toot-source", choices=TOOT_SOURCES)
    ap.add_argument("--child-name", choices=["Mina", "Ivy", "Nora", "Leo", "Sam"])
    ap.add_argument("--friend-name", choices=["Owen", "Milo", "Ruby", "Pia", "Theo"])
    ap.add_argument("--adult-name", choices=["Grandpa", "Aunt June", "Dad", "Mum"])
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
    setting = args.setting or rng.choice(list(SETTINGS))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    share_item = args.share_item or rng.choice(list(ITEMS))
    clue_item = args.clue_item or rng.choice(list(ITEMS))
    toot_source = args.toot_source or rng.choice(list(TOOT_SOURCES))
    child_name = args.child_name or rng.choice(["Mina", "Ivy", "Nora", "Leo", "Sam"])
    friend_name = args.friend_name or rng.choice(["Owen", "Milo", "Ruby", "Pia", "Theo"])
    adult_name = args.adult_name or rng.choice(["Grandpa", "Aunt June", "Dad", "Mum"])
    params = StoryParams(
        setting=setting,
        mystery=mystery,
        share_item=share_item,
        clue_item=clue_item,
        toot_source=toot_source,
        child_name=child_name,
        child_gender="girl" if child_name in {"Mina", "Ivy", "Nora", "Ruby", "Pia"} else "boy",
        friend_name=friend_name,
        friend_gender="girl" if friend_name in {"Ruby", "Pia"} else "boy",
        adult_name=adult_name,
        adult_gender="woman" if adult_name in {"Aunt June", "Mum"} else "man",
    )
    reasonableness_gate(params)
    return params


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.mystery not in MYSTERIES or params.share_item not in ITEMS or params.clue_item not in ITEMS or params.toot_source not in TOOT_SOURCES:
        raise StoryError("Invalid params.")
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
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(setting="riverbank", mystery="missing_boat", share_item="flashlight", clue_item="lantern", toot_source="ferry", child_name="Mina", child_gender="girl", friend_name="Owen", friend_gender="boy", adult_name="Grandpa", adult_gender="man"),
            StoryParams(setting="riverbank", mystery="fog_whistle", share_item="rope", clue_item="map", toot_source="toy_boat", child_name="Ivy", child_gender="girl", friend_name="Theo", friend_gender="boy", adult_name="Aunt June", adult_gender="woman"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 30):
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/devious_silage_ninetieth_playroom_repetition_surprise_adventure.py
====================================================================================================

A small standalone storyworld built from the seed words:
devious, silage, ninetieth.

Setting: playroom
Features: Repetition, Surprise
Style: Adventure

The world tells a child-facing adventure about a playroom expedition, a repeated
search pattern, and a surprise reveal that changes the ending image. The odd seed
words are grounded as object names and clue words inside the simulated world so
they can appear naturally without feeling pasted on.
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
GOOD_SURPRISE_MIN = 3.0


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


@dataclass
class Setting:
    id: str
    room: str
    adventure_phrase: str
    repeated_action: str
    repeated_result: str


@dataclass
class MysteryItem:
    id: str
    label: str
    phrase: str
    surprise: str
    hidden_in: str
    clue_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SurpriseResponse:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str = "playroom"
    item: str = "silage"
    surprise: str = "ninetieth"
    response: str = "unwrap"
    hero: str = "Mina"
    hero_gender: str = "girl"
    friend: str = "Bo"
    friend_gender: str = "boy"
    parent: str = "mother"
    seed: Optional[int] = None


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
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_repetition(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.meters["search"] < 2:
        return out
    sig = ("repetition",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["hope"] += 1
    world.get("room").meters["buzz"] += 1
    out.append("Again and again, the same little search made the room feel like a real expedition.")
    return out


def _r_surprise(world: World) -> list[str]:
    out: list[str] = []
    room = world.get("room")
    if room.meters["surprise"] < GOOD_SURPRISE_MIN:
        return out
    sig = ("surprise",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("hero").memes["joy"] += 1
    world.get("friend").memes["joy"] += 1
    out.append("Then a surprise waited under the lid, bright and new.")
    return out


CAUSAL_RULES = [Rule("repetition", _r_repetition), Rule("surprise", _r_surprise)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def is_reasonable(setting: Setting, item: MysteryItem) -> bool:
    return setting.id == "playroom" and item.id in MYSTERY_ITEMS and item.clue_word in {"devious", "silage", "ninetieth"}


def best_response() -> SurpriseResponse:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def select_response() -> list[SurpriseResponse]:
    return [r for r in RESPONSES.values() if r.sense >= 2]


def predict_surprise(world: World, item_id: str) -> dict:
    sim = world.copy()
    _do_search(sim, sim.get("hero"), sim.get(item_id))
    return {"surprise": sim.get("room").meters["surprise"], "joy": sim.get("hero").memes["joy"]}


def _do_search(world: World, hero: Entity, item: Entity, narrate: bool = True) -> None:
    hero.meters["search"] += 1
    world.get("room").meters["surprise"] += 1
    if narrate:
        world.say(
            f"{hero.id} checked behind the cushions, then under the rug, then inside the toy chest."
        )
    propagate(world, narrate=narrate)


def repeat_search(world: World, hero: Entity, friend: Entity, item: MysteryItem) -> None:
    hero.memes["bravery"] += 1
    friend.memes["curiosity"] += 1
    world.say(
        f"In the playroom, {hero.id} and {friend.id} began an adventure search. "
        f"{hero.id} looked behind the cushions, then under the rug, then inside the toy chest."
    )
    world.say(
        f'{friend.id} grinned. "That feels devious," {friend.pronoun()} said, '
        f"but the clue kept pulling them onward."
    )


def reveal_hint(world: World, hero: Entity, friend: Entity, item: MysteryItem) -> None:
    world.say(
        f"They found a trail of tiny notes with the word {item.clue_word} written on them."
    )
    world.say(
        f"Every note pointed back to {item.hidden_in}, as if the playroom itself were planning a surprise."
    )


def take_action(world: World, response: SurpriseResponse, item: MysteryItem) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    if response.id == "unwrap":
        world.say(
            f"{hero.id} carefully unwrapped the bundle in {item.hidden_in}, and {response.text.format(item=item.label)}."
        )
    else:
        world.say(
            f"{friend.id} tried to guess first, but {response.fail.format(item=item.label)}."
        )


def ending(world: World, item: MysteryItem) -> None:
    world.say(
        f"In the end, the ninetieth little clue was the best one: it led them to {item.phrase}, "
        f"and the whole playroom felt like a treasure cave."
    )


def tell(setting: Setting, item: MysteryItem, response: SurpriseResponse,
         hero_name: str, hero_gender: str, friend_name: str, friend_gender: str,
         parent: str) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="hero"))
    friend = world.add(Entity(id="friend", kind="character", type=friend_gender, label=friend_name, role="friend"))
    parent_ent = world.add(Entity(id="parent", kind="character", type=parent, label="the parent", role="parent"))
    room = world.add(Entity(id="room", type="room", label=setting.room))
    token = world.add(Entity(id=item.id, type="thing", label=item.label))
    world.facts.update(setting=setting, item=item, response=response, hero=hero, friend=friend, parent=parent_ent, room=room, token=token)

    world.say(
        f"{hero_name} and {friend_name} turned the playroom into {setting.adventure_phrase}."
    )
    world.say(
        f"They kept doing the same search on purpose: {setting.repeated_action}, again and again, because each try might reveal {setting.repeated_result}."
    )
    repeat_search(world, hero, friend, item)
    world.para()
    reveal_hint(world, hero, friend, item)
    _do_search(world, hero, token)
    take_action(world, response, item)
    world.para()
    if world.get("room").meters["surprise"] >= GOOD_SURPRISE_MIN:
        world.get("room").meters["treasure"] += 1
    ending(world, item)
    world.say(
        f"{parent_ent.label_word.capitalize()} smiled from the doorway, because the game had become a real adventure without becoming messy or mean."
    )
    return world


SETTINGS = {
    "playroom": Setting(
        id="playroom",
        room="playroom",
        adventure_phrase="a brave map room full of pillows and toy towers",
        repeated_action="looked one more time",
        repeated_result="a better clue",
    )
}

MYSTERY_ITEMS = {
    "silage": MysteryItem(
        id="silage",
        label="a little silage sack",
        phrase="a little silage sack tucked behind the blocks",
        surprise="a farmy surprise",
        hidden_in="the stuffed-animal cave",
        clue_word="devious",
        tags={"devious", "silage"},
    ),
    "devious": MysteryItem(
        id="devious",
        label="a devious note",
        phrase="a devious note folded into a paper boat",
        surprise="a trickster surprise",
        hidden_in="under the blanket fort",
        clue_word="devious",
        tags={"devious"},
    ),
    "ninetieth": MysteryItem(
        id="ninetieth",
        label="the ninetieth badge",
        phrase="the ninetieth badge shining in a toy crown",
        surprise="the final surprise",
        hidden_in="the tallest block tower",
        clue_word="ninetieth",
        tags={"ninetieth"},
    ),
}

RESPONSES = {
    "unwrap": SurpriseResponse(
        id="unwrap",
        sense=4,
        power=4,
        text="and inside was {item}, the surprise they had been searching for all along",
        fail="looked, but the twist stayed hidden from them",
    ),
    "peek": SurpriseResponse(
        id="peek",
        sense=2,
        power=2,
        text="and inside was {item}, but the surprise had already started to glow",
        fail="peeked too fast and missed the best part",
    ),
}

GIRL_NAMES = ["Mina", "Lina", "Ava", "Nora", "Ella"]
BOY_NAMES = ["Bo", "Tate", "Finn", "Leo", "Milo"]
TRAITS = ["curious", "clever", "brave", "careful", "inventive"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for iid, item in MYSTERY_ITEMS.items():
            if is_reasonable(setting, item):
                combos.append((sid, iid, "unwrap"))
                combos.append((sid, iid, "peek"))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Storyworld: a playroom adventure of repetition and surprise.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=MYSTERY_ITEMS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--hero")
    ap.add_argument("--friend")
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
    if args.setting and args.setting != "playroom":
        raise StoryError("This storyworld is only set in the playroom.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.item is None or c[1] == args.item)
              and (args.response is None or c[2] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, item, response = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(GIRL_NAMES + BOY_NAMES)
    friend = args.friend or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != hero])
    hero_gender = "girl" if hero in GIRL_NAMES else "boy"
    friend_gender = "girl" if friend in GIRL_NAMES else "boy"
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting=setting, item=item, surprise="ninetieth", response=response,
                       hero=hero, hero_gender=hero_gender, friend=friend,
                       friend_gender=friend_gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.item not in MYSTERY_ITEMS:
        raise StoryError("Unknown item.")
    if params.response not in RESPONSES:
        raise StoryError("Unknown response.")
    world = tell(SETTINGS[params.setting], MYSTERY_ITEMS[params.item], RESPONSES[params.response],
                 params.hero, params.hero_gender, params.friend, params.friend_gender, params.parent)
    story = world.render() + f" The word devious and the word silage both hid in the adventure, and the ninetieth clue mattered most."
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    item = f["item"]
    return [
        f'Write a playroom adventure story that includes the words "devious", "silage", and "ninetieth".',
        f'Tell a child-friendly adventure in the playroom where {f["hero"].label} and {f["friend"].label} keep repeating the search until a surprise is found.',
        f'Write a story with repetition and a surprise ending where the ninetieth clue leads to {item.phrase}.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    item = f["item"]
    hero = f["hero"]
    friend = f["friend"]
    return [
        ("Who went on the adventure?",
         f"{hero.label} and {friend.label} went on the adventure together in the playroom."),
        ("Why did they keep searching again and again?",
         f"They kept searching again and again because each repeat might reveal a better clue. The repetition made the hunt feel like a real quest."),
        ("What was the surprise?",
         f"The surprise was {item.phrase}. It was waiting in the hidden place after the repeated searching finally paid off."),
        ("How did the story end?",
         f"It ended with the playroom feeling like a treasure cave, and the ninetieth clue turning out to be the most important one. The ending proves the search changed from a guess into a success."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does repetition mean?",
         "Repetition means doing or saying something again and again. It can help someone remember, notice a pattern, or keep trying in a game."),
        ("What is a surprise?",
         "A surprise is something unexpected that appears when you do not know it is coming. It can make a story feel exciting and new."),
        ("Why can an adventure story use clues?",
         "Clues help characters figure out where to go next. In an adventure, clues make the search feel active and brave."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.label:
            bits.append(f"label={e.label!r}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
repetition :- search_count(C), C >= 2.
surprise :- surprise_level(L), L >= surprise_min.
valid(setting, item, response) :- setting(playroom), mystery(item), response(response), clue_word(item, clue), clue.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("setting", "playroom"))
    for iid in MYSTERY_ITEMS:
        lines.append(asp.fact("mystery", iid))
        lines.append(asp.fact("clue_word", iid, MYSTERY_ITEMS[iid].clue_word))
    for rid in RESPONSES:
        lines.append(asp.fact("response", rid))
    lines.append(asp.fact("search_count", 2))
    lines.append(asp.fact("surprise_level", 3))
    lines.append(asp.fact("surprise_min", int(GOOD_SURPRISE_MIN)))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP gate differs from valid_combos().")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        if not sample.story.strip():
            rc = 1
            print("MISMATCH: default generation produced empty story.")
    except Exception as err:
        rc = 1
        print(f"MISMATCH: generation crashed: {err}")
    if rc == 0:
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


CURATED = [
    StoryParams(setting="playroom", item="silage", surprise="ninetieth", response="unwrap",
                hero="Mina", hero_gender="girl", friend="Bo", friend_gender="boy", parent="mother"),
    StoryParams(setting="playroom", item="devious", surprise="ninetieth", response="peek",
                hero="Nora", hero_gender="girl", friend="Leo", friend_gender="boy", parent="father"),
    StoryParams(setting="playroom", item="ninetieth", surprise="ninetieth", response="unwrap",
                hero="Finn", hero_gender="boy", friend="Ava", friend_gender="girl", parent="mother"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for t in asp_valid_combos():
            print(" ", t)
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
            i += 1
            try:
                params = resolve_params(args, random.Random((args.seed or 0) + i))
            except StoryError as err:
                print(err)
                return
            params.seed = (args.seed or 0) + i
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

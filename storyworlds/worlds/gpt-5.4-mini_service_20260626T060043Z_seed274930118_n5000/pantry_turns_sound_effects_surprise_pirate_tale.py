#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"boy", "pirate_boy", "captain_boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "pirate_girl", "captain_girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)
    pantry_name: str = "pantry"


@dataclass
class Turn:
    id: str
    verb: str
    sound: str
    surprise: str
    effect: str
    keyword: str = "turns"


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    kind: str = "thing"


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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


@dataclass
class StoryParams:
    setting: str
    turn: str
    prize: str
    name: str
    gender: str
    companion: str
    seed: Optional[int] = None


SETTINGS = {
    "ship_pantry": Setting(place="the ship's pantry", affords={"peek", "turn", "search"}, pantry_name="pantry"),
    "dock_pantry": Setting(place="the dockside pantry", affords={"peek", "turn", "search"}, pantry_name="pantry"),
    "island_pantry": Setting(place="the island hut pantry", affords={"peek", "turn", "search"}, pantry_name="pantry"),
}

TURNS = {
    "peek": Turn(id="peek", verb="peek behind the barrels", sound="creak", surprise="a hidden coin tin", effect="found"),
    "turn": Turn(id="turn", verb="turn around fast", sound="whirr", surprise="a sparkling map", effect="noticed"),
    "search": Turn(id="search", verb="search the shelves", sound="rustle", surprise="a wee surprise cake", effect="discovered"),
}

PRIZES = {
    "snack": Prize(label="snack", phrase="a sweet little snack", type="snack"),
    "map": Prize(label="map", phrase="a crinkly treasure map", type="map"),
    "lantern": Prize(label="lantern", phrase="a tiny brass lantern", type="lantern"),
}

NAMES = ["Mina", "Pip", "Jory", "Nell", "Finn", "Tessa", "Ari", "Bo"]
COMPANIONS = ["captain", "mate", "parrot", "sailor"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid, s in SETTINGS.items():
        for tid in s.affords:
            for pid in PRIZES:
                out.append((sid, tid, pid))
    return out


def explain_rejection(setting: str, turn: str, prize: str) -> str:
    return f"(No story: {turn} and {prize} do not fit in {setting}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A pirate pantry story world with turns, sound effects, and surprise.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--turn", choices=TURNS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--companion", choices=COMPANIONS)
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.turn is None or c[1] == args.turn)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    sid, tid, pid = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    gender = args.gender or rng.choice(["girl", "boy"])
    companion = args.companion or rng.choice(COMPANIONS)
    return StoryParams(setting=sid, turn=tid, prize=pid, name=name, gender=gender, companion=companion)


def _sound(world: World, text: str) -> None:
    world.say(text)


def tell(setting: Setting, turn: Turn, prize: Prize, name: str, gender: str, companion: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender))
    helper = world.add(Entity(id="companion", kind="character", type=companion, label=f"the {companion}"))
    item = world.add(Entity(id="prize", type=prize.type, label=prize.label, phrase=prize.phrase, owner=hero.id, caretaker=helper.id))
    hero.memes["curiosity"] = 1.0
    hero.memes["joy"] = 1.0

    world.say(f"Little {hero.id} loved the {setting.pantry_name} aboard the boat, where salty crackers and shiny jars hid in the dim light.")
    world.say(f"{hero.pronoun().capitalize()} wanted to {turn.verb}, because {turn.sound}! went the boards and every shelf seemed to wait for a secret.")
    world.say(f"Near the back sat {item.phrase}, and {hero.id} knew {hero.pronoun('possessive')} {item.label} was the best prize of the day.")
    world.para()

    world.say(f"{hero.id} stepped into {setting.place}, and the floor said {turn.sound.upper()} as {hero.id} took a careful step.")
    world.say(f"{hero.id} started to {turn.verb}, but then a little {turn.sound} sounded from behind the crates.")
    world.say(f"\"Surprise!\" cried {companion}. There was {turn.surprise}, tucked in a bright tin with a ribbon on top.")
    hero.memes["surprise"] = 1.0
    hero.memes["delight"] = 1.0
    item.meters["safe"] = 1.0
    world.para()

    world.say(f"{hero.id} laughed and turned back to the {setting.pantry_name} shelf again. {hero.pronoun().capitalize()} shared the treat with {companion} while the {turn.sound.lower()} of the ship faded into a cozy hush.")
    world.say(f"At the end, {hero.id} had {item.phrase}, a happy heart, and a pantry full of warm pirate cheer.")

    world.facts.update(hero=hero, helper=helper, item=item, setting=setting, turn=turn, prize=prize)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, turn, prize = f["hero"], f["turn"], f["prize"]
    return [
        f'Write a short pirate tale for a young child that includes the word "{turn.keyword}" and a surprise in a pantry.',
        f"Tell a gentle story about {hero.id} in the {world.setting.pantry_name} where {turn.sound}! leads to a surprise.",
        f"Write a tiny pirate story where a child turns around in a pantry and finds {prize.phrase}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, turn, prize = f["hero"], f["helper"], f["turn"], f["prize"]
    return [
        QAItem(question=f"Where did {hero.id} go in the story?", answer=f"{hero.id} went to {world.setting.place}, the pantry on a pirate ship."),
        QAItem(question=f"What sound did the story mention when {hero.id} moved?", answer=f"The story said {turn.sound}! as {hero.id} moved through the pantry."),
        QAItem(question=f"What surprise was waiting?", answer=f"A surprise {turn.surprise} was waiting for {hero.id} and {helper.label}."),
        QAItem(question=f"What did {hero.id} end up with at the end?", answer=f"{hero.id} ended up with {prize.phrase} and a happy pirate smile."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a pantry?", answer="A pantry is a small room or cupboard where food and supplies are kept."),
        QAItem(question="What is a surprise?", answer="A surprise is something unexpected that makes someone stop and look closely."),
        QAItem(question="Why do stories use sound effects?", answer="Sound effects help a story feel lively and help readers imagine what is happening."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("\n== story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}\nA: {q.answer}")
    out.append("\n== world questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}\nA: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(S) :- setting_fact(S).
turn(T) :- turn_fact(T).
prize(P) :- prize_fact(P).
valid(S,T,P) :- setting(S), turn(T), prize(P), affords(S,T).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting_fact", sid))
        for t in sorted(s.affords):
            lines.append(asp.fact("affords", sid, t))
    for tid in TURNS:
        lines.append(asp.fact("turn_fact", tid))
    for pid in PRIZES:
        lines.append(asp.fact("prize_fact", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], TURNS[params.turn], PRIZES[params.prize], params.name, params.gender, params.companion)
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
    StoryParams(setting="ship_pantry", turn="peek", prize="snack", name="Mina", gender="girl", companion="captain"),
    StoryParams(setting="dock_pantry", turn="turn", prize="map", name="Finn", gender="boy", companion="mate"),
    StoryParams(setting="island_pantry", turn="search", prize="lantern", name="Tessa", gender="girl", companion="parrot"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for c in combos:
            print(" ", c)
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
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.name}: {p.turn} in {p.setting} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

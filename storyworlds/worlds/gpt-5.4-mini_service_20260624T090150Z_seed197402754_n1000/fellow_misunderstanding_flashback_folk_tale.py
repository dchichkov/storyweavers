#!/usr/bin/env python3
"""
A small folk-tale storyworld about a fellow, a misunderstanding, and a flashback.

Premise:
- A fellow and a loved one or neighbor share a small village setting.
- A mistaken clue causes hurt feelings.
- A flashback reveals the true cause.
- The fellow makes a gentle repair, and the tale ends with peace.

This script follows the Storyweavers contract with:
- typed entities carrying physical meters and emotional memes
- a Python reasonableness gate plus inline ASP twin
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- trace, qa, json, asp, verify, and show-asp support
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if not self.meters:
            self.meters = {"distance": 0.0, "wear": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "hurt": 0.0, "trust": 0.0, "relief": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister", "aunt"}
        male = {"boy", "father", "man", "brother", "uncle", "fellow"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def possessive_name(self) -> str:
        return self.id if self.id.endswith("s") else f"{self.id}'s"


@dataclass
class Setting:
    place: str = "the village green"
    afford_flashback: bool = True


@dataclass
class EventCard:
    id: str
    cue: str
    effect: str
    concern: str
    setting_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Token:
    id: str
    label: str
    phrase: str
    type: str
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    lost: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if not self.meters:
            self.meters = {"wear": 0.0, "dust": 0.0}
        if not self.memes:
            self.memes = {}


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity | Token] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent):
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str):
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if isinstance(e, Entity) and e.kind == "character"]

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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def folk_opening(place: str) -> str:
    return {
        "the village green": "In a little village, where the grass grew soft and the well sang at noon,",
        "the old mill road": "On an old road by the mill, where crows kept the time and dust knew every boot,",
        "the river bank": "By a slow river, where reeds bowed and minnows flashed like needles,",
        "the apple orchard": "In an apple orchard, where the branches made green ceilings and bees hummed low,",
    }.get(place, "In a small folk-tale place,") 


def child_name(gender: str) -> str:
    return random.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def relation_label(kind: str) -> str:
    return {"mother": "mother", "father": "father", "sister": "sister", "brother": "brother", "aunt": "aunt", "uncle": "uncle", "grandmother": "grandmother", "grandfather": "grandfather", "fellow": "fellow"}.get(kind, kind)


def _r_misunderstanding(world: World) -> list[str]:
    out = []
    fellow = world.get("fellow")
    if fellow.memes["worry"] < THRESHOLD:
        return out
    sig = ("misunderstanding",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    fellow.memes["hurt"] += 1
    out.append("The fellow took the wrong meaning from a small sign and grew hurt.")
    return out


def _r_flashback(world: World) -> list[str]:
    out = []
    if not world.facts.get("flashback_started"):
        return out
    sig = ("flashback",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    out.append("A memory rose up like a lantern in the dark.")
    return out


def _r_repair(world: World) -> list[str]:
    out = []
    fellow = world.get("fellow")
    if fellow.memes["trust"] < THRESHOLD:
        return out
    sig = ("repair",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    fellow.memes["relief"] += 1
    fellow.memes["hurt"] = 0.0
    out.append("Kind words mended what the mistake had tugged apart.")
    return out


CAUSAL_RULES = [
    _r_misunderstanding,
    _r_flashback,
    _r_repair,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def predict_misunderstanding(world: World, fellow: Entity, token: Token) -> bool:
    sim = world.copy()
    sim.get("fellow").memes["worry"] += 1
    propagate(sim, narrate=False)
    return bool(sim.get("fellow").memes["hurt"] >= THRESHOLD)


def introduce(world: World, fellow: Entity, kin: Entity, token: Token) -> None:
    world.say(folk_opening(world.setting.place))
    world.say(
        f"a {fellow.traits[0]} fellow named {fellow.id} lived there with {kin.id}, "
        f"who kept a {token.phrase} close by."
    )
    fellow.memes["trust"] += 1


def setup_friendship(world: World, fellow: Entity, kin: Entity, token: Token) -> None:
    fellow.memes["joy"] += 1
    world.say(
        f"{fellow.id} liked to help {kin.id} with small chores and to listen to old village stories."
    )
    world.say(
        f"Often {kin.id} asked {fellow.id} to carry the {token.label} when the day grew busy."
    )


def raise_misunderstanding(world: World, fellow: Entity, kin: Entity, token: Token) -> None:
    fellow.memes["worry"] += 1
    world.say(
        f"One afternoon, {fellow.id} saw the {token.label} by the door and thought {kin.id} had set it aside on purpose."
    )
    world.say(
        f"{fellow.id} felt a sting of hurt, because the sign looked like a cold refusal."
    )
    propagate(world, narrate=True)


def flashback(world: World, fellow: Entity, kin: Entity, token: Token) -> None:
    world.facts["flashback_started"] = True
    world.para()
    world.say(
        f"Then came a flashback: {fellow.id} remembered the morning wind, the muddy path, and {kin.id} saying "
        f'\"Leave the {token.label} here so the rain will not spoil it.\"'
    )
    world.say(
        f"The memory showed that the {token.label} had not been pushed away at all; it had been protected."
    )
    propagate(world, narrate=True)


def repair(world: World, fellow: Entity, kin: Entity, token: Token) -> None:
    fellow.memes["trust"] += 1
    world.para()
    world.say(
        f"{fellow.id} walked back to {kin.id}, lowered {fellow.pronoun('possessive')} voice, and told the truth of the mistake."
    )
    world.say(
        f"{kin.id} smiled kindly and said the {token.label} had only been kept safe."
    )
    fellow.memes["hurt"] = 0.0
    fellow.memes["relief"] += 1
    world.say(
        f"So the fellow laughed, the worry melted, and the two of them sat beside the door while the evening bells rang."
    )


def tell(setting: Setting, event: EventCard, kin_type: str, token_cfg: Token,
         name: str = "Milo", gender: str = "boy", kin_name: str = "Aunt May") -> World:
    world = World(setting)
    fellow = world.add(Entity(id="fellow", kind="character", type="fellow", traits=["gentle", "thoughtful"]))
    fellow.id = name
    kin = world.add(Entity(id="kin", kind="character", type=kin_type, traits=[relation_label(kin_type)]))
    kin.id = kin_name
    token = world.add(Token(id="token", label=token_cfg.label, phrase=token_cfg.phrase, type=token_cfg.type,
                            owner=kin.id, caretaker=kin.id))
    introduce(world, fellow, kin, token)
    setup_friendship(world, fellow, kin, token)
    world.para()
    raise_misunderstanding(world, fellow, kin, token)
    flashback(world, fellow, kin, token)
    repair(world, fellow, kin, token)
    world.facts.update(fellow=fellow, kin=kin, token=token, event=event, setting=setting)
    return world


@dataclass
class StoryParams:
    place: str
    kin_type: str
    token: str
    name: str
    gender: str
    kin_name: str
    seed: Optional[int] = None


SETTINGS = {
    "village_green": Setting(place="the village green"),
    "old_mill_road": Setting(place="the old mill road"),
    "river_bank": Setting(place="the river bank"),
    "apple_orchard": Setting(place="the apple orchard"),
}

EVENTS = {
    "note": EventCard(
        id="note",
        cue="a small note",
        effect="a mistaken meaning",
        concern="hurt feelings",
        setting_word="note",
        tags={"misunderstanding"},
    ),
    "basket": EventCard(
        id="basket",
        cue="a basket left by a door",
        effect="a mistaken sign",
        concern="hurt feelings",
        setting_word="basket",
        tags={"misunderstanding"},
    ),
    "ribbon": EventCard(
        id="ribbon",
        cue="a ribbon on a hook",
        effect="a mistaken sign",
        concern="hurt feelings",
        setting_word="ribbon",
        tags={"misunderstanding"},
    ),
    "cup": EventCard(
        id="cup",
        cue="a cup by the window",
        effect="a mistaken sign",
        concern="hurt feelings",
        setting_word="cup",
        tags={"misunderstanding"},
    ),
}

TOKENS = {
    "basket": Token(id="basket", label="basket", phrase="a reed basket", type="basket"),
    "shawl": Token(id="shawl", label="shawl", phrase="a wool shawl", type="shawl"),
    "tea_cup": Token(id="cup", label="cup", phrase="a blue tea cup", type="cup"),
    "lantern": Token(id="lantern", label="lantern", phrase="a brass lantern", type="lantern"),
}

GIRL_NAMES = ["Mina", "Lena", "Tess", "Mara", "Ivy", "Nora"]
BOY_NAMES = ["Milo", "Eli", "Jon", "Tobin", "Arlo", "Perrin"]
KIN_TYPES = ["mother", "father", "aunt", "uncle", "grandmother", "grandfather"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, k, t) for p in SETTINGS for k in KIN_TYPES for t in TOKENS]


ASP_RULES = r"""
valid_story(P,K,T) :- place(P), kin(K), token(T).
misunderstanding(P) :- place(P).
flashback(P) :- place(P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for k in KIN_TYPES:
        lines.append(asp.fact("kin", k))
    for t in TOKENS:
        lines.append(asp.fact("token", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: a folk-tale fellow, a misunderstanding, and a flashback.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--kin-type", choices=KIN_TYPES)
    ap.add_argument("--token", choices=TOKENS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--kin-name")
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
    if args.kin_type:
        combos = [c for c in combos if c[1] == args.kin_type]
    if args.token:
        combos = [c for c in combos if c[2] == args.token]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, kin_type, token = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    kin_name = args.kin_name or rng.choice(["Aunt May", "Uncle Joss", "Grandma Elin", "Father Reed", "Mother Nia"])
    return StoryParams(place=place, kin_type=kin_type, token=token, name=name, gender=gender, kin_name=kin_name)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short folk-tale for a child about a fellow named {f["fellow"].id} who has a misunderstanding and then remembers the truth in a flashback.',
        f'Tell a gentle village story where {f["fellow"].id} misreads a sign about a {f["token"].label} and later learns why {f["kin"].id} meant no harm.',
        f'Write a simple story with the words "fellow", "misunderstanding", and "flashback", ending with the mistake being kindly repaired.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    fellow = f["fellow"]
    kin = f["kin"]
    token = f["token"]
    place = f["setting"].place
    return [
        QAItem(
            question=f"Who is the story about in {place}?",
            answer=f"It is about a fellow named {fellow.id} and {kin.id}, who live through a small misunderstanding and a gentle repair.",
        ),
        QAItem(
            question=f"What did {fellow.id} first think when {fellow.pronoun('subject')} saw the {token.label}?",
            answer=f"{fellow.id} first thought {kin.id} had put the {token.label} aside on purpose, and that thought made {fellow.pronoun('object')} feel hurt.",
        ),
        QAItem(
            question=f"What did the flashback show about the {token.label}?",
            answer=f"The flashback showed that {kin.id} had told {fellow.id} to leave the {token.label} there so the rain would not spoil it.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"The fellow spoke kindly, learned the truth, and the misunderstanding melted away into relief and laughter.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks a word, sign, or action means one thing, but it really means something else.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a part of a story that shows something from earlier, so the reader can learn what really happened before.",
        ),
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
    for e in world.entities.values():
        if isinstance(e, Entity):
            lines.append(f"  {e.id}: {e.type} meters={e.meters} memes={e.memes}")
        else:
            lines.append(f"  {e.id}: token owner={e.owner} worn_by={e.worn_by} lost={e.lost}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], EVENTS["note"], params.kin_type, TOKENS[params.token], params.name, params.gender, params.kin_name)
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
    StoryParams(place="village_green", kin_type="aunt", token="basket", name="Milo", gender="boy", kin_name="Aunt May"),
    StoryParams(place="river_bank", kin_type="mother", token="shawl", name="Mina", gender="girl", kin_name="Mother Nia"),
    StoryParams(place="apple_orchard", kin_type="grandmother", token="lantern", name="Eli", gender="boy", kin_name="Grandma Elin"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible (place, kin, token) combos.")
        for x in asp_valid_combos():
            print(" ", x)
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

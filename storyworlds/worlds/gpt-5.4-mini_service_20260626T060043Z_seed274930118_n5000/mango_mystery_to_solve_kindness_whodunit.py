#!/usr/bin/env python3
"""
Standalone storyworld: Mango Mystery to Solve, Kindness, Whodunit style.

A small, classical simulation where a child detective notices a missing mango,
follows clues, and discovers that a kind helper moved it to protect it.
"""

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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    moved_by: Optional[str] = None
    hidden_in: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    spaces: list[str]


@dataclass
class Mystery:
    missing_item: str
    item_phrase: str
    item_type: str
    place: str
    clue: str
    hidden_place: str
    reason: str


@dataclass
class StoryParams:
    place: str
    mystery: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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

    def copy(self) -> "World":
        import copy

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _has_moved(world: World, item: Entity, place: str) -> bool:
    return item.hidden_in == place


def _r_find(world: World) -> list[str]:
    out: list[str] = []
    detective = world.get("detective")
    item = world.get("mango")
    if detective.memes.get("curious", 0) < THRESHOLD:
        return out
    sig = ("discover", item.id)
    if sig in world.fired:
        return out
    if item.hidden_in:
        world.fired.add(sig)
        detective.memes["confidence"] = detective.memes.get("confidence", 0) + 1
        out.append(f"The clue made {detective.id} feel sure enough to keep looking.")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    helper = world.get("helper")
    item = world.get("mango")
    detective = world.get("detective")
    sig = ("kind", item.id)
    if sig in world.fired:
        return out
    if helper.memes.get("kindness", 0) < THRESHOLD:
        return out
    if item.moved_by != helper.id:
        return out
    world.fired.add(sig)
    helper.memes["warmth"] = helper.memes.get("warmth", 0) + 1
    detective.memes["trust"] = detective.memes.get("trust", 0) + 1
    out.append("The helpful move was not a trick at all; it was a kind choice.")
    return out


CAUSAL_RULES = [_r_find, _r_kindness]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_missing(world: World, helper: Entity, item: Entity) -> bool:
    sim = world.copy()
    sim.get(item.id).hidden_in = helper.id
    sim.get(item.id).moved_by = helper.id
    propagate(sim, narrate=False)
    return bool(sim.get(item.id).hidden_in)


def setting_detail(setting: Setting) -> str:
    if setting.place == "kitchen":
        return "The kitchen was bright, with bowls, baskets, and a sunny window."
    if setting.place == "market":
        return "The market was busy, with cloth awnings and tables full of fruit."
    if setting.place == "garden":
        return "The garden was quiet, with leaves, pots, and a small bench."
    return f"{setting.place.capitalize()} looked tidy and full of little hiding spots."


def introduce(world: World, detective: Entity, helper: Entity, mystery: Mystery) -> None:
    world.say(
        f"{detective.id} was a little {detective.type} who loved noticing small things."
    )
    world.say(
        f"{detective.pronoun().capitalize()} liked solving mysteries, especially when a {mystery.missing_item} was missing."
    )
    world.say(
        f"{helper.id} was {helper.phrase} and was known for being kind."
    )


def setup_item(world: World, mystery: Mystery, detective: Entity) -> None:
    mango = world.add(Entity(
        id="mango",
        type="mango",
        label="mango",
        phrase=mystery.item_phrase,
        owner=detective.id,
        caretaker="helper",
        meters={"fresh": 1.0},
        memes={"special": 1.0},
    ))
    detective.memes["love"] = detective.memes.get("love", 0) + 1
    world.say(
        f"{detective.id} had a {mystery.item_phrase}, and {detective.pronoun('possessive')} favorite snack was the mango."
    )
    world.say(
        f"Then one day, the mango was gone from {mystery.place}."
    )


def notice_clue(world: World, detective: Entity, mystery: Mystery) -> None:
    detective.memes["curious"] = detective.memes.get("curious", 0) + 1
    world.say(
        f"{detective.id} found a clue: {mystery.clue}"
    )
    world.say(
        f'"Hmm," {detective.id} said. "{mystery.item_type.capitalize()}s do not vanish by themselves."'
    )


def question_everyone(world: World, detective: Entity, helper: Entity, mystery: Mystery) -> None:
    helper.memes["kindness"] = helper.memes.get("kindness", 0) + 1
    world.say(
        f"{detective.id} asked {helper.pronoun('object')}, and {helper.id} answered gently."
    )
    world.say(
        f'"I moved it," {helper.id} said. "I wanted to keep it safe, because {mystery.reason}."'
    )


def resolve(world: World, detective: Entity, helper: Entity, mystery: Mystery) -> None:
    item = world.get("mango")
    if not item.hidden_in:
        item.hidden_in = helper.id
    item.moved_by = helper.id
    propagate(world, narrate=False)
    world.say(
        f"{detective.id} followed the clue to {mystery.hidden_place} and found the mango there."
    )
    world.say(
        f"{helper.id} had tucked it away carefully, and the mystery was solved."
    )
    world.say(
        f"{detective.id} smiled, thanked {helper.pronoun('object')}, and shared the mango with {helper.pronoun('object')}."
    )
    detective.memes["joy"] = detective.memes.get("joy", 0) + 1
    helper.memes["warmth"] = helper.memes.get("warmth", 0) + 1


def tell(setting: Setting, mystery: Mystery, hero_name: str, hero_gender: str, helper_name: str, trait: str) -> World:
    world = World(setting)
    detective = world.add(Entity(
        id="detective",
        kind="character",
        type=hero_gender,
        label=hero_name,
        phrase=f"a {trait} little {hero_gender}",
        meters={},
        memes={"curious": 1.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type="adult",
        label=helper_name,
        phrase="a gentle helper",
        meters={},
        memes={"kindness": 1.0},
    ))

    introduce(world, detective, helper, mystery)
    world.para()
    world.say(setting_detail(setting))
    setup_item(world, mystery, detective)
    notice_clue(world, detective, mystery)
    question_everyone(world, detective, helper, mystery)
    world.para()
    resolve(world, detective, helper, mystery)

    world.facts.update(
        detective=detective,
        helper=helper,
        mystery=mystery,
        setting=setting,
        solved=True,
        clue=mystery.clue,
        hidden_place=mystery.hidden_place,
    )
    return world


SETTINGS = {
    "kitchen": Setting(place="the kitchen", spaces=["counter", "table", "basket", "window sill"]),
    "market": Setting(place="the market", spaces=["stall", "crate", "cloth awning", "bench"]),
    "garden": Setting(place="the garden", spaces=["bench", "pot", "watering can", "leaf pile"]),
}

MYSTERIES = {
    "basket": Mystery(
        missing_item="mango",
        item_phrase="bright yellow mango",
        item_type="fruit",
        place="the table",
        clue="a small trail of sticky footprints near the basket",
        hidden_place="the fruit basket",
        reason="it might get bumped off the table",
    ),
    "window": Mystery(
        missing_item="mango",
        item_phrase="sweet ripe mango",
        item_type="fruit",
        place="the window sill",
        clue="a soft cloth was draped over one corner of the tray",
        hidden_place="the cloth-lined drawer",
        reason="the sun was making it too warm",
    ),
    "bench": Mystery(
        missing_item="mango",
        item_phrase="juicy mango",
        item_type="fruit",
        place="the bench",
        clue="a little note with a kind drawing of a smile",
        hidden_place="the garden basket",
        reason="the birds were pecking at the fruit",
    ),
}

GIRL_NAMES = ["Mia", "Ava", "Nora", "Lina", "Zoe", "Lily"]
BOY_NAMES = ["Leo", "Noah", "Finn", "Eli", "Theo", "Ben"]
HELPER_NAMES = ["Rosa", "Mina", "Omar", "Pia", "Nia"]
TRAITS = ["curious", "careful", "bright", "gentle", "brave"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short whodunit for a young child about a missing mango and a kind helper in {f["setting"].place}.',
        f"Tell a gentle mystery story where {f['detective'].label} looks for a mango, finds a clue, and learns why {f['helper'].label} moved it.",
        f'Write a simple detective story that uses the word "mango" and ends with kindness solving the puzzle.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective: Entity = f["detective"]
    helper: Entity = f["helper"]
    mystery: Mystery = f["mystery"]
    setting: Setting = f["setting"]
    return [
        QAItem(
            question=f"Who solved the mystery about the missing mango?",
            answer=f"{detective.label} solved the mystery by following the clue and finding where the mango had been kept.",
        ),
        QAItem(
            question=f"What clue helped {detective.label} keep looking?",
            answer=f"The clue was {mystery.clue}. It gave {detective.label} a place to search next.",
        ),
        QAItem(
            question=f"Why did {helper.label} move the mango?",
            answer=f"{helper.label} moved it kindly because {mystery.reason}. {helper.label} wanted to keep the mango safe, not steal it.",
        ),
        QAItem(
            question=f"Where was the mango found in {setting.place}?",
            answer=f"The mango was found in {mystery.hidden_place}. That is where {helper.label} had tucked it away carefully.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mango?",
            answer="A mango is a sweet tropical fruit with juicy orange-yellow flesh inside and a large seed in the middle.",
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues, asks questions, and figures out what happened.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means helping someone, being gentle, and trying to make things better for them.",
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="kitchen", mystery="basket", name="Mia", gender="girl", helper="Rosa", trait="curious"),
    StoryParams(place="market", mystery="window", name="Leo", gender="boy", helper="Mina", trait="careful"),
    StoryParams(place="garden", mystery="bench", name="Nora", gender="girl", helper="Omar", trait="gentle"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit story world about a mango mystery and kindness.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--trait", choices=TRAITS)
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
    place = args.place or rng.choice(list(SETTINGS))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, mystery=mystery, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    mystery = MYSTERIES[params.mystery]
    world = tell(setting, mystery, params.name, params.gender, params.helper, params.trait)
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


ASP_RULES = r"""
place(kitchen).
place(market).
place(garden).

mystery(basket).
mystery(window).
mystery(bench).

kind(helper).
missing(mango).

at_place(basket,kitchen).
at_place(window,market).
at_place(bench,garden).

clue(basket,footprints).
clue(window,cloth).
clue(bench,note).

hidden(basket,basket).
hidden(window,drawer).
hidden(bench,gardenbasket).

mango_story(P,M) :- place(P), mystery(M), at_place(M,P).
solved(P,M) :- mango_story(P,M), hidden(M,_).
kindness_story(P,M) :- solved(P,M).
#show mango_story/2.
#show solved/2.
#show kindness_story/2.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery", m))
    lines.append(asp.fact("kind", "helper"))
    lines.append(asp.fact("missing", "mango"))
    for m, obj in [("basket", "kitchen"), ("window", "market"), ("bench", "garden")]:
        lines.append(asp.fact("at_place", m, obj))
    for m, clue in [("basket", "footprints"), ("window", "cloth"), ("bench", "note")]:
        lines.append(asp.fact("clue", m, clue))
    for m, h in [("basket", "basket"), ("window", "drawer"), ("bench", "gardenbasket")]:
        lines.append(asp.fact("hidden", m, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show solved/2."))
    atoms = sorted(set(asp.atoms(model, "solved")))
    expected = sorted([(m, "x") for m in MYSTERIES])  # placeholder structure not used
    # Compare using a direct textual check for the grounded rules we expect.
    found = {a for a in atoms}
    wanted = {("kitchen", "basket"), ("market", "window"), ("garden", "bench")}
    if found == wanted:
        print(f"OK: ASP produced {len(found)} solved stories.")
        return 0
    print("MISMATCH between ASP and expected solved story set:")
    print("  found:", sorted(found))
    print("  wanted:", sorted(wanted))
    return 1


def asp_valid() -> list[tuple[str, str]]:
    import asp

    model = asp.one_model(asp_program("#show solved/2."))
    return sorted(set(asp.atoms(model, "solved")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show solved/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        vals = asp_valid()
        print(f"{len(vals)} solvable mystery settings:\n")
        for place, mystery in vals:
            print(f"  {place:8} {mystery}")
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
            header = f"### {p.name}: mango mystery at {p.place} ({p.mystery})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

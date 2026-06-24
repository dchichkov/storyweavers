#!/usr/bin/env python3
"""
history_suspense_comedy.py
==========================

A small storyworld about a child, a history project, and a suspenseful comedy
beat: something important goes missing right before show-and-tell, and the
solution turns out to be surprisingly funny.

The world models:
- physical meters: carried, hidden, dusty, displayed
- emotional memes: worry, excitement, pride, relief, giggle

The seed theme is history, but the story stays concrete: props, costumes,
posters, and a last-minute search in a classroom, museum corner, or library.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    hidden: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["carried", "hidden", "dusty", "displayed"]:
            self.meters.setdefault(k, 0.0)
        for k in ["worry", "excitement", "pride", "relief", "giggle", "curiosity"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    type: str
    risk: str
    clue: str
    hides_in: set[str]
    plural: bool = False


@dataclass
class Helper:
    id: str
    label: str
    prep: str
    tail: str
    solves: set[str] = field(default_factory=set)


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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w


SETTINGS = {
    "classroom": Setting("the classroom", {"poster", "showcase", "costume", "boxes"}),
    "museum": Setting("the little museum room", {"poster", "showcase", "costume"}),
    "library": Setting("the library corner", {"poster", "book", "showcase"}),
}

PROPS = {
    "poster": Prop(
        id="poster",
        label="history poster",
        phrase="a colorful history poster",
        type="poster",
        risk="creased",
        clue="old pictures",
        hides_in={"boxes", "book", "showcase"},
    ),
    "crown": Prop(
        id="crown",
        label="paper crown",
        phrase="a paper crown for the ancient king",
        type="crown",
        risk="crumpled",
        clue="gold paper",
        hides_in={"showcase", "boxes"},
    ),
    "scroll": Prop(
        id="scroll",
        label="story scroll",
        phrase="a rolled-up story scroll",
        type="scroll",
        risk="torn",
        clue="rolled paper",
        hides_in={"boxes", "showcase"},
    ),
    "helmet": Prop(
        id="helmet",
        label="knight helmet",
        phrase="a shiny cardboard knight helmet",
        type="helmet",
        risk="squashed",
        clue="silver cardboard",
        hides_in={"showcase", "boxes"},
    ),
}

HELPERS = {
    "flashlight": Helper(
        id="flashlight",
        label="a tiny flashlight",
        prep="shine a tiny flashlight under the tables",
        tail="shone the tiny flashlight under the tables",
        solves={"hidden"},
    ),
    "gloves": Helper(
        id="gloves",
        label="a pair of clean gloves",
        prep="put on a pair of clean gloves",
        tail="wore the clean gloves",
        solves={"dusty"},
    ),
    "clipboard": Helper(
        id="clipboard",
        label="a clipboard",
        prep="use a clipboard to keep the papers flat",
        tail="held the papers flat on the clipboard",
        solves={"creased", "crumpled"},
    ),
}

NAMES = ["Mina", "Leo", "Tia", "Ben", "Nora", "Owen", "Maya", "Sam"]
TYPES = {"girl": ["Mina", "Tia", "Nora", "Maya"], "boy": ["Leo", "Ben", "Owen", "Sam"]}
TRAITS = ["curious", "brave", "silly", "careful", "cheerful", "bouncy"]


def hidden_risk(prop: Prop, setting: Setting) -> bool:
    return bool(prop.hides_in & setting.affords)


def select_helper(prop: Prop) -> Optional[Helper]:
    for helper in HELPERS.values():
        if prop.risk in helper.solves:
            return helper
    return None


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for s_name, setting in SETTINGS.items():
        for p_name, prop in PROPS.items():
            if hidden_risk(prop, setting) and select_helper(prop):
                out.append((s_name, p_name))
    return out


def _search(world: World, hero: Entity, prop: Entity) -> list[str]:
    if prop.hidden and hero.memes["worry"] >= THRESHOLD:
        sig = ("find", prop.id)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        prop.hidden = False
        prop.meters["hidden"] = 0.0
        prop.meters["displayed"] = 1.0
        hero.memes["relief"] += 1
        hero.memes["giggle"] += 1
        return [f"At last, {hero.id} found {hero.pronoun('possessive')} {prop.label}, and everyone laughed."]
    return []


def propagate(world: World) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for ent in list(world.entities.values()):
            if ent.hidden:
                continue
            for helper in HELPERS.values():
                pass
        for ent in list(world.entities.values()):
            if ent.kind != "character":
                continue
            for prop in list(world.entities.values()):
                if prop.kind == "thing" and prop.hidden and ent.memes["worry"] >= THRESHOLD:
                    sents = _search(world, ent, prop)
                    if sents:
                        changed = True
                        produced.extend(sents)
    for s in produced:
        world.say(s)
    return produced


def predict_outcome(world: World, hero: Entity, prop: Entity) -> dict:
    sim = world.copy()
    sim.get(hero.id).memes["worry"] += 1
    return {"found": not sim.get(prop.id).hidden}


def tell(setting: Setting, prop_cfg: Prop, hero_name: str, hero_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    adult = world.add(Entity(id="GrownUp", kind="character", type="mother", label="the grown-up"))
    prop = world.add(Entity(
        id=prop_cfg.id,
        type=prop_cfg.type,
        label=prop_cfg.label,
        phrase=prop_cfg.phrase,
        owner=hero.id,
        caretaker=adult.id,
        hidden=True,
    ))
    helper = select_helper(prop_cfg)

    hero.memes["excitement"] += 1
    hero.memes["pride"] += 1
    world.say(f"{hero.id} was a {trait} {hero_type} who loved history.")
    world.say(f"{hero.id} was bringing {prop_cfg.phrase} to school for show-and-tell.")
    world.para()
    world.say(f"Right before the talk, the {prop_cfg.label} was gone.")
    hero.memes["worry"] += 1
    world.say(f"{hero.id} looked under papers, behind chairs, and even beside a stapler that looked very suspicious.")

    if predict_outcome(world, hero, prop)["found"]:
        world.say(f"The {prop_cfg.label} was hiding in a place that matched its clue: {prop_cfg.clue}.")
    if helper:
        world.say(f"Then {hero.id} tried to {helper.prep}.")
        world.say(f"That helped because the {prop_cfg.label} liked to hide near {next(iter(prop_cfg.hides_in))}.")

    world.para()
    world.say(f"{hero.id}'s worry grew until {hero.pronoun()} started to laugh at the silliness of the search.")
    hero.memes["giggle"] += 1
    prop.hidden = False
    prop.meters["hidden"] = 0.0
    prop.meters["displayed"] = 1.0
    hero.memes["relief"] += 1
    world.say(f"In the end, the {prop_cfg.label} turned up right where the clue said it would be.")
    world.say(f"{hero.id} held {prop.it()} up, gave the history facts, and even added one tiny joke about the stapler.")
    world.say(f"Everyone clapped, and {hero.id} felt proud instead of panicked.")

    world.facts.update(hero=hero, adult=adult, prop=prop, prop_cfg=prop_cfg, helper=helper, setting=setting)
    return world


@dataclass
class StoryParams:
    place: str
    prop: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a funny suspense story for a child about history, a missing {f["prop_cfg"].label}, and a happy ending.',
        f'Tell a short story where {f["hero"].id} is bringing {f["prop_cfg"].phrase} to {f["setting"].place} but it disappears right before show-and-tell.',
        f'Write a comedic story about searching for a lost history item and laughing when the clue turns out to be right.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, prop_cfg, setting = f["hero"], f["prop_cfg"], f["setting"]
    return [
        QAItem(
            question=f"What was {hero.id} bringing to {setting.place}?",
            answer=f"{hero.id} was bringing {prop_cfg.phrase} for a history show-and-tell.",
        ),
        QAItem(
            question=f"Why was {hero.id} worried before the talk?",
            answer=f"{hero.id} was worried because the {prop_cfg.label} went missing right before the presentation.",
        ),
        QAItem(
            question=f"What helped the search?",
            answer=f"A helpful clue and, if needed, {f['helper'].label if f['helper'] else 'a careful search'} helped find the {prop_cfg.label}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} finding the {prop_cfg.label}, telling the history facts, and feeling proud and relieved.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is history?",
            answer="History is the story of people and places from long ago, and people learn it from books, pictures, objects, and stories.",
        ),
        QAItem(
            question="Why do clues help in a mystery?",
            answer="Clues help because they point people toward where something is hidden or what it might be like.",
        ),
        QAItem(
            question="Why can a lost item make a story suspenseful?",
            answer="A lost item can make a story suspenseful because the characters do not know where it is yet and keep searching until they find it.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.hidden:
            bits.append("hidden=True")
        lines.append(f"  {e.id:10} ({e.kind:10}) {' '.join(bits)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(P) :- setting(P).
prop(P) :- thing(P).

hidden_risk(Place, Prop) :- affords(Place, Bag), in(Prop, Bag).
has_helper(Prop) :- prop(Prop), risk(Prop, R), solves(H, R).

valid_story(Place, Prop) :- affords(Place, Bag), in(Prop, Bag), risk(Prop, R), solves(H, R).
"""


def asp_facts() -> str:
    import asp
    out: list[str] = []
    for s_name, s in SETTINGS.items():
        out.append(asp.fact("setting", s_name))
        for a in sorted(s.affords):
            out.append(asp.fact("affords", s_name, a))
    for p_name, p in PROPS.items():
        out.append(asp.fact("thing", p_name))
        out.append(asp.fact("risk", p_name, p.risk))
        for hid in sorted(p.hides_in):
            out.append(asp.fact("in", p_name, hid))
    for h_name, h in HELPERS.items():
        out.append(asp.fact("helper", h_name))
        for s in sorted(h.solves):
            out.append(asp.fact("solves", h_name, s))
    return "\n".join(out)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    if py - cl:
        print(" only in python:", sorted(py - cl))
    if cl - py:
        print(" only in ASP:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="History suspense comedy storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.prop:
        combos = [c for c in combos if c[1] == args.prop]
    if not combos:
        raise StoryError("No valid history story matches those options.")
    place, prop = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(TYPES[gender])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, prop=prop, name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], PROPS[params.prop], params.name, params.gender, params.trait)
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
    StoryParams(place="classroom", prop="poster", name="Mina", gender="girl", trait="curious"),
    StoryParams(place="museum", prop="crown", name="Leo", gender="boy", trait="silly"),
    StoryParams(place="library", prop="scroll", name="Nora", gender="girl", trait="careful"),
    StoryParams(place="classroom", prop="helmet", name="Ben", gender="boy", trait="bouncy"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible history story combos:\n")
        for place, prop in combos:
            print(f"  {place:10} {prop}")
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
            header = f"### {p.name}: {p.prop} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

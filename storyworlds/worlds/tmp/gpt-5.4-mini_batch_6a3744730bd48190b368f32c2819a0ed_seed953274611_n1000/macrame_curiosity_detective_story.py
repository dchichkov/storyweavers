#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/macrame_curiosity_detective_story.py
====================================================================

A tiny detective-style storyworld about curiosity, clues, and a macrame craft
project that solves a small mystery.

Premise:
- A curious child notices strange missing knots and odd scraps of cord.
- The search feels like a detective story: clues, hunches, a reveal, and a tidy
  ending image that proves what changed.
- The world model tracks physical state with meters and emotional state with
  memes, and the prose is rendered from those state changes.

This script follows the shared Storyweavers contract:
- stdlib only
- imports storyworlds/results.py eagerly
- imports storyworlds/asp.py lazily inside ASP helpers
- provides StoryParams, build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
CURIOUS_BOOST = 1.0


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
class Thing:
    id: str
    label: str
    phrase: str
    place: str
    material: str
    shape: str
    clue_text: str = ""
    hidden: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass
class StoryParams:
    setting: str = "workshop"
    detective: str = "Maya"
    detective_gender: str = "girl"
    partner: str = "Noah"
    partner_gender: str = "boy"
    adult: str = "mom"
    object_kind: str = "key"
    clue_kind: str = "thread"
    macrame_color: str = "blue"
    ending: str = "found"
    seed: Optional[int] = None


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    things: dict[str, Thing] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_thing(self, thing: Thing) -> Thing:
        self.things[thing.id] = thing
        return thing

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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.things = copy.deepcopy(self.things)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_curious(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("detective")
    if child.memes["curiosity"] < THRESHOLD:
        return out
    if ("curious", "first") in world.fired:
        return out
    world.fired.add(("curious", "first"))
    child.memes["focus"] += 1
    out.append("")
    return out


def _r_discover(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("searched") and world.facts.get("hidden_revealed") and ("discover",) not in world.fired:
        world.fired.add(("discover",))
        out.append("")
    return out


CAUSAL_RULES = [Rule("curious", _r_curious), Rule("discover", _r_discover)]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            if rule.apply(world):
                changed = True


def build_scene(setting: str) -> str:
    return {
        "workshop": "a quiet little workshop",
        "attic": "a dusty attic room",
        "library": "a small back room in the library",
    }[setting]


def setting_detail(setting: str) -> str:
    return {
        "workshop": "bins of cord, hooks, and bright little spools lined the shelves.",
        "attic": "old boxes leaned against the beams, and sunbeams striped the floor.",
        "library": "the craft table sat beside tall shelves and a sleepy window.",
    }[setting]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for obj in OBJECTS:
            for clue in CLUES:
                if obj != clue:
                    combos.append((setting, obj, clue))
    return combos


def reasonableness_check(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.object_kind not in OBJECTS:
        raise StoryError("Unknown missing object.")
    if params.clue_kind not in CLUES:
        raise StoryError("Unknown clue kind.")
    if params.object_kind == params.clue_kind:
        raise StoryError("The missing object and clue cannot be the same thing.")
    if params.ending not in {"found", "misread", "spilled"}:
        raise StoryError("Unknown ending.")


def predict(world: World, clue_id: str) -> bool:
    sim = world.copy()
    return sim.things[clue_id].hidden


def intro(world: World, detective: Entity, partner: Entity) -> None:
    detective.memes["curiosity"] += CURIOUS_BOOST
    partner.memes["trust"] += 1
    world.say(
        f"{detective.id} was a curious little detective who noticed every odd thing. "
        f"{partner.id} was always beside {detective.pronoun('object')}, ready to look."
    )


def case_opens(world: World, setting: str, clue: Thing, missing: Thing) -> None:
    world.say(
        f"One afternoon in {build_scene(setting)}, {setting_detail(setting)} "
        f"Then a small mystery appeared: {missing.phrase} was gone, but there was "
        f"{clue.clue_text} near the macrame workbench."
    )


def examine_clue(world: World, detective: Entity, clue: Thing) -> None:
    detective.memes["curiosity"] += 1
    world.say(
        f'{detective.id} leaned in. "{clue.label.capitalize()}," '
        f"{detective.pronoun()} murmured. "
        f"The clue was close to the macrame cords, so {detective.pronoun()} knew the day had a trail."
    )


def ask_partner(world: World, detective: Entity, partner: Entity) -> None:
    partner.memes["helpful"] += 1
    world.say(
        f"{partner.id} held the lantern and peered under the table. "
        f'"If we follow the clues, we can solve it together," {partner.pronoun()} said.'
    )


def search(world: World, detective: Entity, missing: Thing, clue: Thing) -> None:
    world.facts["searched"] = True
    if clue.material == "cord":
        world.say(
            f"{detective.id} followed the twist of {clue.label} right to the craft basket. "
            f"There, tucked behind a bowl of knots, was the missing {missing.label}."
        )
    else:
        world.say(
            f"{detective.id} checked the shelves, the rug, and the chair legs. "
            f"At last, the missing {missing.label} turned up where nobody had thought to look."
        )


def reveal(world: World, missing: Thing) -> None:
    missing.hidden = False
    world.facts["hidden_revealed"] = True
    world.say(
        f"The mystery clicked into place. The missing {missing.label} was not stolen at all; "
        f"it had simply been set aside during the macrame project."
    )


def ending_found(world: World, detective: Entity, partner: Entity, adult: Entity, missing: Thing, color: str) -> None:
    detective.memes["joy"] += 1
    partner.memes["joy"] += 1
    adult.memes["relief"] += 1
    world.say(
        f"{adult.label_word.capitalize()} smiled and tied the {missing.label} back where it belonged. "
        f"Then {adult.pronoun()} showed them a new macrame cord in {color}, so the craft could begin again."
    )
    world.say(
        f"{detective.id} grinned at the neat little knotwork and the returned {missing.label}. "
        f"The room felt solved, tidy, and bright."
    )


def ending_misread(world: World, detective: Entity, partner: Entity, adult: Entity, missing: Thing) -> None:
    detective.memes["embarrassment"] += 1
    world.say(
        f"For a moment, {detective.id} guessed wrong and pointed at the wrong shelf. "
        f"But {adult.label_word.capitalize()} laughed kindly, and {partner.id} found the real clue."
    )
    world.say(
        f"By the end, the little mistake made the answer shine even clearer: the {missing.label} was safe all along."
    )


def ending_spilled(world: World, detective: Entity, partner: Entity, adult: Entity, missing: Thing) -> None:
    detective.memes["worry"] += 1
    world.say(
        f"The search got clumsy, and a cup tipped across the macrame cords. "
        f"{adult.label_word.capitalize()} dried the strings and everyone cleaned up together."
    )
    world.say(
        f"Even then, the missing {missing.label} was found beneath the table, and the case ended with calm hands and a tidy floor."
    )


def tell(params: StoryParams) -> World:
    world = World()
    detective = world.add(Entity(id=params.detective, kind="character", type=params.detective_gender, role="detective"))
    partner = world.add(Entity(id=params.partner, kind="character", type=params.partner_gender, role="partner"))
    adult = world.add(Entity(id="Adult", kind="character", type=params.adult, role="adult", label="the parent"))
    detective.memes["curiosity"] = 2.0
    partner.memes["trust"] = 1.0

    missing = world.add_thing(Thing(
        id="missing", label=OBJECTS[params.object_kind]["label"], phrase=OBJECTS[params.object_kind]["phrase"],
        place="basket", material=OBJECTS[params.object_kind]["material"], shape=OBJECTS[params.object_kind]["shape"]
    ))
    clue = world.add_thing(Thing(
        id="clue", label=CLUES[params.clue_kind]["label"], phrase=CLUES[params.clue_kind]["phrase"],
        place=CLUES[params.clue_kind]["place"], material=CLUES[params.clue_kind]["material"],
        shape=CLUES[params.clue_kind]["shape"], clue_text=CLUES[params.clue_kind]["clue_text"]
    ))
    world.facts["missing"] = missing
    world.facts["clue"] = clue
    world.facts["setting"] = params.setting

    intro(world, detective, partner)
    world.para()
    case_opens(world, params.setting, clue, missing)
    examine_clue(world, detective, clue)
    ask_partner(world, detective, partner)
    search(world, detective, missing, clue)
    reveal(world, missing)
    world.para()
    if params.ending == "found":
        ending_found(world, detective, partner, adult, missing, params.macrame_color)
    elif params.ending == "misread":
        ending_misread(world, detective, partner, adult, missing)
    else:
        ending_spilled(world, detective, partner, adult, missing)

    world.facts.update(
        detective=detective,
        partner=partner,
        adult=adult,
        solved=True,
        ending=params.ending,
        macrame_color=params.macrame_color,
    )
    return world


SETTINGS = {
    "workshop": True,
    "attic": True,
    "library": True,
}

OBJECTS = {
    "key": {"label": "silver key", "phrase": "a silver key", "material": "metal", "shape": "small and shiny"},
    "comb": {"label": "pearl comb", "phrase": "a pearl comb", "material": "shell", "shape": "small and smooth"},
    "note": {"label": "note", "phrase": "a folded note", "material": "paper", "shape": "flat and folded"},
}

CLUES = {
    "thread": {"label": "thread scrap", "phrase": "a thread scrap", "place": "the craft table", "material": "cord", "shape": "thin", "clue_text": "a tiny blue thread scrap"},
    "knot": {"label": "knot", "phrase": "a loose knot", "place": "the chair arm", "material": "cord", "shape": "looped", "clue_text": "a loose knot in the macrame cord"},
    "fringe": {"label": "fringe", "phrase": "a hanging fringe", "place": "the window cord", "material": "cord", "shape": "dangling", "clue_text": "frayed fringe beside the knots"},
}


@dataclass
class StoryParams:
    setting: str = "workshop"
    detective: str = "Maya"
    detective_gender: str = "girl"
    partner: str = "Noah"
    partner_gender: str = "boy"
    adult: str = "mother"
    object_kind: str = "key"
    clue_kind: str = "thread"
    macrame_color: str = "blue"
    ending: str = "found"
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a detective story for a young child that includes the word macrame and a curious clue about a missing {OBJECTS[f['missing'].label if False else 'key']['label']}.",
        f"Tell a gentle detective story where {f['detective'].id} follows a clue in a macrame craft room and solves a small mystery.",
        "Write a short, child-friendly mystery with curiosity, a clue, and a tidy ending where the missing thing is found.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    d, p, a = f["detective"], f["partner"], f["adult"]
    missing = f["missing"]
    clue = f["clue"]
    return [
        ("Who is the story about?",
         f"It is about {d.id} and {p.id}, two children who love looking for clues together. {a.label_word.capitalize()} helps them keep the search calm and safe."),
        ("What clue did the detective notice?",
         f"{d.id} noticed {clue.clue_text}. That clue mattered because it was right by the macrame cords and led toward the answer."),
        ("How was the mystery solved?",
         f"They followed the clue to the craft basket and found the missing {missing.label}. The answer was simple: it had been set aside during the macrame work."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is macrame?",
         "Macrame is a craft where people tie cords or strings into knots to make pretty patterns or decorations."),
        ("What does curiosity do?",
         "Curiosity makes someone want to look, ask questions, and follow clues. It is a helpful feeling for a detective."),
        ("What does a detective do?",
         "A detective looks carefully for clues and tries to figure out what happened. Detectives solve mysteries by paying attention to small details."),
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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    for t in world.things.values():
        bits = []
        if t.hidden:
            bits.append("hidden=True")
        lines.append(f"  {t.id:10} (thing  ) label={t.label!r} {' '.join(bits)}")
    return "\n".join(lines)


def sensible_endings() -> list[str]:
    return ["found", "misread", "spilled"]


def valid_story(params: StoryParams) -> bool:
    return params.setting in SETTINGS and params.object_kind in OBJECTS and params.clue_kind in CLUES and params.object_kind != params.clue_kind


def explain_rejection(params: StoryParams) -> str:
    if params.object_kind == params.clue_kind:
        return "No story: the missing object and the clue need to be different things."
    return "No story: that combination does not fit this little detective world."


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    settings = list(SETTINGS)
    objects = list(OBJECTS)
    clues = list(CLUES)
    if args.setting and args.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if args.object_kind and args.object_kind not in OBJECTS:
        raise StoryError("Unknown missing object.")
    if args.clue_kind and args.clue_kind not in CLUES:
        raise StoryError("Unknown clue kind.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.object_kind is None or c[1] == args.object_kind)
              and (args.clue_kind is None or c[2] == args.clue_kind)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, object_kind, clue_kind = rng.choice(sorted(combos))
    ending = args.ending or rng.choice(sensible_endings())
    detective_gender = args.detective_gender or rng.choice(["girl", "boy"])
    partner_gender = args.partner_gender or ("boy" if detective_gender == "girl" else "girl")
    detective = args.detective or rng.choice(["Maya", "Iris", "Nina", "Ada"])
    partner = args.partner or rng.choice(["Noah", "Eli", "Ben", "Owen"])
    adult = args.adult or rng.choice(["mother", "father"])
    macrame_color = args.macrame_color or rng.choice(["blue", "red", "gold"])
    return StoryParams(setting=setting, detective=detective, detective_gender=detective_gender,
                       partner=partner, partner_gender=partner_gender, adult=adult,
                       object_kind=object_kind, clue_kind=clue_kind, macrame_color=macrame_color,
                       ending=ending)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.object_kind not in OBJECTS or params.clue_kind not in CLUES:
        raise StoryError("Invalid params for this world.")
    if params.object_kind == params.clue_kind:
        raise StoryError("The missing object and clue cannot be the same.")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective-style curiosity storyworld with macrame clues.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--detective")
    ap.add_argument("--detective-gender", choices=["girl", "boy"])
    ap.add_argument("--partner")
    ap.add_argument("--partner-gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=["mother", "father"])
    ap.add_argument("--object-kind", choices=OBJECTS)
    ap.add_argument("--clue-kind", choices=CLUES)
    ap.add_argument("--macrame-color")
    ap.add_argument("--ending", choices=sensible_endings())
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


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for o in OBJECTS:
        lines.append(asp.fact("object_kind", o))
    for c in CLUES:
        lines.append(asp.fact("clue_kind", c))
    lines.append(asp.fact("curiosity", "present"))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,O,C) :- setting(S), object_kind(O), clue_kind(C), O != C.
curious_story :- curiosity(present).
#show valid/3.
"""


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    asps = set(asp_valid_combos())
    if py == asps:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
        print("python-only:", sorted(py - asps))
        print("asp-only:", sorted(asps - py))
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: normal story generation smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid combos:")
        for s, o, c in asp_valid_combos():
            print(f"  {s:8} {o:10} {c}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        params_list = [
            StoryParams(setting="workshop", detective="Maya", detective_gender="girl", partner="Noah", partner_gender="boy", adult="mother", object_kind="key", clue_kind="thread", macrame_color="blue", ending="found"),
            StoryParams(setting="attic", detective="Iris", detective_gender="girl", partner="Eli", partner_gender="boy", adult="father", object_kind="comb", clue_kind="knot", macrame_color="gold", ending="misread"),
            StoryParams(setting="library", detective="Nina", detective_gender="girl", partner="Ben", partner_gender="boy", adult="mother", object_kind="note", clue_kind="fringe", macrame_color="red", ending="spilled"),
        ]
        samples = [generate(p) for p in params_list]
    else:
        seen = set()
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.detective} in {p.setting} ({p.ending})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

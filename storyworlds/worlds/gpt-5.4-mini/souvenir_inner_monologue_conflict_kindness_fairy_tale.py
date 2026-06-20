#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/souvenir_inner_monologue_conflict_kindness_fairy_tale.py
========================================================================================

A small fairy-tale storyworld about a child, a cherished souvenir, an inner
monologue, a conflict, and a kind resolution.

The world is intentionally tiny and classical:
- typed entities with physical meters and emotional memes
- a forward-chained causal model
- grounded QA from the simulated world state
- a Python reasonableness gate with an inline ASP twin

The seed idea is a fairy tale in which a child gets a souvenir from a market or
festival, then must choose between keeping it for themselves and sharing or
returning it when another character needs it more. The turn comes from an inner
monologue that reveals the child's worry, then the conflict escalates, and
kindness resolves it with a visible ending image.
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
        female = {"girl", "mother", "mom", "woman", "queen", "princess"}
        male = {"boy", "father", "dad", "man", "king", "prince"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Place:
    id: str
    name: str
    detail: str
    atmosphere: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Souvenir:
    id: str
    label: str
    phrase: str
    shine: str
    story_value: str
    shareable: bool = True
    treasured: bool = True

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Need:
    id: str
    label: str
    use: str
    urgency: int
    kind: str = "help"

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Kindness:
    id: str
    label: str
    act: str
    effect: str
    reward: str
    power: int

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


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

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

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
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_lonely(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.memes["worry"] < THRESHOLD:
            continue
        sig = ("lonely", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["lonely"] += 1
        out.append("__lonely__")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.memes["kindness"] < THRESHOLD:
            continue
        sig = ("kindness", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["warmth"] += 1
        out.append("__kind__")
    return out


CAUSAL_RULES = [
    Rule("lonely", "social", _r_lonely),
    Rule("kindness", "social", _r_kindness),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            got = rule.apply(world)
            if got:
                changed = True
                produced.extend(g for g in got if not g.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def fair_need_at_risk(souvenir: Souvenir, need: Need) -> bool:
    return souvenir.shareable and need.urgency >= 1


def reasonable_resolution(kindness: Kindness, souvenir: Souvenir) -> bool:
    return kindness.power >= 2 and souvenir.treasured


def predict_conflict(world: World, child: Entity, souvenir: Souvenir, need: Need) -> dict:
    sim = world.copy()
    sim.get(child.id).memes["worry"] += 1
    sim.get(child.id).memes["conflict"] += 1
    return {
        "conflict": fair_need_at_risk(souvenir, need),
        "kindness_possible": reasonable_resolution(KINDNESSES["share"], souvenir),
    }


def introduce(world: World, child: Entity, guide: Entity, place: Place, souvenir: Souvenir) -> None:
    child.memes["joy"] += 1
    world.say(
        f"Once in a bright little kingdom, {child.id} went with {guide.id} to {place.name}. "
        f"{place.detail}"
    )
    world.say(
        f"There, {guide.id} gave {child.id} a {souvenir.phrase}. "
        f"It shone {souvenir.shine}, and {child.id} tucked it away as a precious souvenir."
    )


def desire(world: World, child: Entity, need: Need) -> None:
    child.memes["desire"] += 1
    child.memes["worry"] += 1
    world.say(
        f"Later, {child.id} saw {need.label}, and {child.pronoun()} wanted to help right away."
    )


def inner_monologue(world: World, child: Entity, souvenir: Souvenir, need: Need) -> None:
    pred = predict_conflict(world, child, souvenir, need)
    world.facts["predicted_conflict"] = pred["conflict"]
    world.say(
        f'In {child.pronoun("possessive")} heart, {child.id} thought, '
        f'"If I use my {souvenir.label}, it might get lost. But if I keep it, '
        f'{need.label} will stay waiting."'
    )


def conflict(world: World, child: Entity, guide: Entity, need: Need, souvenir: Souvenir) -> None:
    child.memes["conflict"] += 1
    guide.memes["concern"] += 1
    world.say(
        f"{guide.id} reached for the {souvenir.label} and said it should stay safe on the shelf, "
        f"but {child.id} wished to use it for {need.use}."
    )
    world.say(
        f"{child.id} hugged the souvenir tight and felt torn between keeping it and being helpful."
    )


def kindness_turn(world: World, child: Entity, guide: Entity, need: Need, souvenir: Souvenir) -> None:
    child.memes["kindness"] += 1
    child.memes["warmth"] += 1
    guide.memes["warmth"] += 1
    world.say(
        f"Then {child.id} took a breath and spoke kindly: "
        f'"You may borrow it if it helps {need.label}."'
    )
    world.say(
        f"{guide.id}'s face softened at once, because kindness had turned the quarrel into a gift."
    )
    world.say(
        f"Together they placed the {souvenir.label} where it could be seen, not hidden, and the air felt lighter."
    )


def resolution(world: World, child: Entity, guide: Entity, need: Need, souvenir: Souvenir) -> None:
    child.memes["joy"] += 1
    child.memes["pride"] += 1
    guide.memes["joy"] += 1
    world.say(
        f"At last, {child.id} used the souvenir to {need.use}, and the little act of help sparkled like a spell."
    )
    world.say(
        f"By the end, the souvenir was still cherished, and {child.id} had learned that a kind heart can keep a treasure bright."
    )


def tell(place: Place, souvenir: Souvenir, need: Need, kindness: Kindness,
         child_name: str = "Mira", child_gender: str = "girl",
         guide_name: str = "Grandma", guide_gender: str = "woman") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    guide = world.add(Entity(id=guide_name, kind="character", type=guide_gender, role="guide"))
    crown = world.add(Entity(id="souvenir", type="thing", label=souvenir.label))
    world.facts.update(place=place, souvenir=souvenir, need=need, kindness=kindness,
                       child=child, guide=guide, crown=crown)

    introduce(world, child, guide, place, souvenir)
    world.para()
    desire(world, child, need)
    inner_monologue(world, child, souvenir, need)
    conflict(world, child, guide, need, souvenir)
    world.para()
    kindness_turn(world, child, guide, need, souvenir)
    resolution(world, child, guide, need, souvenir)
    return world


PLACES = {
    "market": Place("market", "the moonlit market", "Lanterns hung above the stalls, and bakeries smelled sweet.", "busy"),
    "festival": Place("festival", "the spring festival", "Banners fluttered over the grass, and music twinkled in the air.", "bright"),
    "castle": Place("castle", "the old castle fair", "Stone towers watched over ribbons, and the courtyard gleamed.", "grand"),
}

SOUVENIRS = {
    "glass_star": Souvenir("glass_star", "glass star", "tiny glass star", "like a captured moonbeam", "a memory of the festival"),
    "shell_heart": Souvenir("shell_heart", "shell heart", "shell heart on a ribbon", "pearled and pale", "a memory of the seaside"),
    "silver_bell": Souvenir("silver_bell", "silver bell", "little silver bell", "bright as morning", "a memory of the castle fair"),
}

NEEDS = {
    "help_lost_child": Need("help_lost_child", "the lost child", "guide the lost child home", 2),
    "help_basket": Need("help_basket", "the baker's basket", "carry the basket to the stall", 1),
    "help_gate": Need("help_gate", "the gatekeeper", "open the gate for the waiting line", 2),
}

KINDNESSES = {
    "share": Kindness("share", "sharing", "share what was precious", "the worry softened", "everyone felt braver", 3),
    "lend": Kindness("lend", "lending", "lend what was precious", "the tension melted", "trust grew", 2),
    "return": Kindness("return", "returning", "return what was precious", "the conflict faded", "the heart grew light", 3),
}

GIRL_NAMES = ["Mira", "Elin", "Luna", "Nora", "Iris", "Sera"]
BOY_NAMES = ["Ari", "Nico", "Theo", "Finn", "Evan", "Jules"]
GUIDE_NAMES = ["Grandma", "Grandpa", "Aunt May", "Uncle Rowan"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for s in SOUVENIRS:
            for n in NEEDS:
                if fair_need_at_risk(SOUVENIRS[s], NEEDS[n]) and reasonable_resolution(KINDNESSES["share"], SOUVENIRS[s]):
                    combos.append((p, s, n))
    return combos


@dataclass
@dataclass
class StoryParams:
    place: str
    souvenir: str
    need: str
    kindness: str
    child_name: str
    child_gender: str
    guide_name: str
    guide_gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy-tale story for a 3-to-5-year-old that includes the word "souvenir" and ends with kindness.',
        f"Tell a gentle fairy tale where {f['child'].id} loves a souvenir from {f['place'].name} but feels torn when {f['need'].label} needs help.",
        f'Write a story with inner monologue and a conflict, where a child thinks about whether to keep a souvenir or use it kindly.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, guide, souvenir, need, place = f["child"], f["guide"], f["souvenir"], f["need"], f["place"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id} and {guide.id}, and the special souvenir they found at {place.name}."),
        ("What did the child want to do?",
         f"{child.id} wanted to help {need.label}, but {child.pronoun('possessive')} heart worried about losing the {souvenir.label}."),
        ("What changed in the middle of the story?",
         f"The child thought it through inside {child.pronoun('possessive')} mind, then the worry turned into a conflict with {guide.id}."),
        ("How did the story end?",
         f"It ended kindly: {child.id} shared the souvenir so it could help {need.label}, and the treasure stayed precious too."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a souvenir?",
         "A souvenir is a keepsake from a place or event that helps you remember it later."),
        ("What is kindness?",
         "Kindness means choosing to help, share, or comfort someone even when it is not the easiest choice."),
        ("What is an inner monologue?",
         "An inner monologue is the quiet voice in a character's mind that tells what the character is thinking."),
        ("What is a conflict in a story?",
         "A conflict is a problem or tug-of-war that makes the character decide what to do next."),
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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("festival", "glass_star", "help_lost_child", "share", "Mira", "girl", "Grandma", "woman"),
    StoryParams("market", "shell_heart", "help_basket", "lend", "Ari", "boy", "Grandma", "woman"),
    StoryParams("castle", "silver_bell", "help_gate", "return", "Nora", "girl", "Aunt May", "woman"),
]


def explain_rejection() -> str:
    return "(No story: this combination does not create a fair conflict that can be solved with kindness.)"


ASP_RULES = r"""
fair_need(S) :- souvenir(S), shareable(S), need(N), urgent(N).
conflict(C) :- child(C), want_help(C), fair_need(_).
kind_end(C) :- child(C), kindness(K), power(K,P), P >= 2.
valid(P,S,N) :- place(P), souvenir(S), need(N), fair_need(S), kind_end(_).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for sid, s in SOUVENIRS.items():
        lines.append(asp.fact("souvenir", sid))
        if s.shareable:
            lines.append(asp.fact("shareable", sid))
    for nid, n in NEEDS.items():
        lines.append(asp.fact("need", nid))
        if n.urgency >= 1:
            lines.append(asp.fact("urgent", nid))
    for kid in KINDNESSES:
        lines.append(asp.fact("kindness", kid))
        lines.append(asp.fact("power", kid, KINDNESSES[kid].power))
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
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in gate")
    try:
        sample = generate(resolve_params(argparse.Namespace(
            place=None, souvenir=None, need=None, kindness=None,
            child_name=None, child_gender=None, guide_name=None, guide_gender=None
        ), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale story world about a souvenir, inner monologue, conflict, and kindness.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--souvenir", choices=SOUVENIRS)
    ap.add_argument("--need", choices=NEEDS)
    ap.add_argument("--kindness", choices=KINDNESSES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guide-name")
    ap.add_argument("--guide-gender", choices=["woman", "man"])
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
              if (args.place is None or c[0] == args.place)
              and (args.souvenir is None or c[1] == args.souvenir)
              and (args.need is None or c[2] == args.need)]
    if not combos:
        raise StoryError(explain_rejection())
    place, souvenir, need = rng.choice(sorted(combos))
    child_gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    guide_gender = args.guide_gender or "woman"
    guide_name = args.guide_name or rng.choice(GUIDE_NAMES)
    kindness = args.kindness or "share"
    return StoryParams(place, souvenir, need, kindness, child_name, child_gender, guide_name, guide_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], SOUVENIRS[params.souvenir], NEEDS[params.need],
                 KINDNESSES[params.kindness], params.child_name, params.child_gender,
                 params.guide_name, params.guide_gender)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for p, s, n in combos:
            print(f"  {p:8} {s:12} {n}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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

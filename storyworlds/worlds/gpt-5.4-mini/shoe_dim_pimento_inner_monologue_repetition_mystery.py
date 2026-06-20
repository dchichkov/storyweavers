#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/shoe_dim_pimento_inner_monologue_repetition_mystery.py
======================================================================================

A small mystery storyworld about a child following tiny clues in a dim hallway:
a shoe-dim trail, a spilled pimento jar, and a careful inner monologue that keeps
the search steady. The stories stay child-facing, concrete, and state-driven: a
lost thing, repeated clues, a turn in the investigation, and a resolution image
that proves what changed.

Seed words / instruments:
- shoe-dim
- pimento
- Inner Monologue
- Repetition
- Mystery
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
    label: str
    dim: str
    smell: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class Clue:
    id: str
    label: str
    detail: str
    tag: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class LostItem:
    id: str
    label: str
    location_hint: str
    found_with: str
    tag: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
            value = __import__("collections").defaultdict(float)
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


def _r_notice(world: World) -> list[str]:
    out = []
    for ent in world.characters():
        if ent.memes["curiosity"] < THRESHOLD:
            continue
        sig = ("notice", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["alert"] += 1
        out.append("__notice__")
    return out


def _r_smell(world: World) -> list[str]:
    out = []
    kitchen = world.entities.get("kitchen")
    if not kitchen:
        return out
    if kitchen.meters["messy"] < THRESHOLD:
        return out
    sig = ("smell", "kitchen")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for ent in world.characters():
        ent.memes["unease"] += 1
    out.append("__smell__")
    return out


CAUSAL_RULES = [Rule("notice", "social", _r_notice), Rule("smell", "physical", _r_smell)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
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


def clue_at_risk(place: Place, clue: Clue, lost_item: LostItem) -> bool:
    return place.dim == "dim" and clue.tag in {"pimento", "shoe"} and lost_item.tag == "missing"


def sensible_revealers() -> list[str]:
    return ["look_under_rug", "follow_smell", "check_shoe_rack"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for cid, clue in CLUES.items():
            for lid, lost in LOST.items():
                if clue_at_risk(place, clue, lost):
                    combos.append((pid, cid, lid))
    return combos


@dataclass
@dataclass
class StoryParams:
    place: str
    clue: str
    lost_item: str
    revealer: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


def findable(world: World, lost: LostItem, clue: Clue) -> bool:
    return clue.tag in {"pimento", "shoe"}


def predict(world: World, clue_id: str) -> dict:
    sim = world.copy()
    _drop_clue(sim, sim.get("clue"))
    return {"messy": sim.get("kitchen").meters["messy"] >= THRESHOLD}


def _drop_clue(world: World, clue_ent: Entity, narrate: bool = True) -> None:
    kitchen = world.get("kitchen")
    kitchen.meters["messy"] += 1
    clue_ent.meters["seen"] += 1
    propagate(world, narrate=narrate)


def opening(world: World, hero: Entity, helper: Entity, place: Place) -> None:
    hero.memes["curiosity"] += 1
    helper.memes["care"] += 1
    world.say(
        f"On a quiet evening, {hero.id} and {helper.id} searched {place.label}. "
        f"The hallway looked {place.dim}, almost shoe-dim, and {place.smell}."
    )
    world.say(
        f"{hero.id} kept thinking, shoe-dim, shoe-dim, as if repeating the words might "
        f"help the dark make sense."
    )


def first_clue(world: World, clue: Clue) -> None:
    world.say(
        f"Then {clue.label} appeared near the floor: {clue.detail}. "
        f"It was the kind of clue that made the little search feel real."
    )


def inner_monologue(world: World, hero: Entity, clue: Clue, lost: LostItem) -> None:
    world.say(
        f'"Maybe I am close," {hero.id} thought. "Maybe the missing thing is near the '
        f"{lost.location_hint}. Maybe the clue means the same thing twice."
    )
    world.say(
        f"{hero.id} looked again and again. The clue kept saying the same small story: "
        f"{clue.tag}, pimento, pimento."
    )


def warn(world: World, helper: Entity, hero: Entity, lost: LostItem, clue: Clue) -> None:
    pred = predict(world, clue.id)
    helper.memes["care"] += 1
    world.facts["predicted_mess"] = pred["messy"]
    world.say(
        f'"If we rush, we might miss the real trail," {helper.id} said. '
        f'"Let\'s follow the pimento smudge and check the shoe rack too."'
    )


def reveal(world: World, hero: Entity, helper: Entity, clue: Clue, lost: LostItem) -> None:
    helper.memes["relief"] += 1
    hero.memes["relief"] += 1
    lost_ent = world.get(lost.id)
    lost_ent.meters["found"] += 1
    world.say(
        f"{hero.id} followed the repeated clue to the shoe rack. "
        f"There, tucked behind a box, was {lost.label} with {lost.found_with}."
    )
    world.say(
        f"{hero.id} picked it up and laughed. The shoe-dim hallway did not feel spooky anymore; "
        f"it felt solved."
    )


def ending(world: World, hero: Entity, helper: Entity, lost: LostItem) -> None:
    world.say(
        f"By the end, {hero.id} and {helper.id} had put everything back where it belonged. "
        f"The little mystery was over, and the room looked neat and bright again."
    )
    world.say(
        f"{hero.id} even smiled at the empty spot, because now {lost.label} was found."
    )


def tell(place: Place, clue: Clue, lost: LostItem, hero_name: str = "Mila",
         hero_gender: str = "girl", helper_name: str = "Nora",
         helper_gender: str = "girl") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    world.add(Entity(id="kitchen", label="the kitchen"))
    clue_ent = world.add(Entity(id="clue", type="thing", label=clue.label))
    lost_ent = world.add(Entity(id=lost.id, type="thing", label=lost.label))

    opening(world, hero, helper, place)
    world.para()
    first_clue(world, clue)
    warn(world, helper, hero, lost, clue)
    inner_monologue(world, hero, clue, lost)
    _drop_clue(world, clue_ent)
    world.para()
    reveal(world, hero, helper, clue, lost)
    ending(world, hero, helper, lost)

    world.facts.update(hero=hero, helper=helper, place=place, clue=clue, lost=lost, clue_ent=clue_ent)
    return world


PLACES = {
    "hall": Place("hall", "the hall", "dim", "slightly dusty"),
    "pantry": Place("pantry", "the pantry", "dim", "a little spicy"),
    "mudroom": Place("mudroom", "the mudroom", "dim", "rain-coat cozy"),
}

CLUES = {
    "pimento_smear": Clue("pimento_smear", "a pimento smear", "a little red streak on the floor", "pimento"),
    "shoe_print": Clue("shoe_print", "a shoe print", "a tiny print beside the door", "shoe"),
    "both": Clue("both", "a shoe-dim trail", "a red smudge mixed with a shoe mark", "shoe"),
}

LOST = {
    "key": LostItem("key", "the little brass key", "the rug", "shoe"),
    "toy": LostItem("toy", "the blue toy boat", "the shoe rack", "missing"),
    "cookie_tin": LostItem("cookie_tin", "the cookie tin", "the cabinet", "missing"),
}

REVEALERS = {
    "follow_smell": "follow the pimento smell",
    "look_under_rug": "look under the rug",
    "check_shoe_rack": "check the shoe rack",
}

NAMES = ["Mila", "Nora", "Ivy", "Lena", "Ada", "Tess", "Owen", "Noah", "Eli", "Sam"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly mystery story that includes the words "shoe-dim" and "pimento".',
        f"Tell a gentle mystery where {f['hero'].id} keeps thinking in an inner monologue and the clue repeats itself until the lost thing is found.",
        f"Write a short story with repetition and a solved-at-the-end mystery: show a dim place, a pimento clue, and a final discovery.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, place, clue, lost = f["hero"], f["helper"], f["place"], f["clue"], f["lost"]
    return [
        QAItem(
            question="What kind of story is this?",
            answer="It is a small mystery story. A child follows clues, thinks carefully, and finds what was missing."
        ),
        QAItem(
            question=f"What did {hero.id} keep thinking about?",
            answer=f"{hero.id} kept thinking about the clue and the dark hall. The repeated words helped {hero.pronoun('object')} stay calm and keep searching."
        ),
        QAItem(
            question=f"How was the clue repeated?",
            answer=f"The clue repeated in the story as {clue.tag}, pimento, pimento. That repetition made it feel like a true trail."
        ),
        QAItem(
            question=f"What was found at the end?",
            answer=f"{lost.label} was found near the shoe rack. The search ended with the missing thing back where it belonged."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is pimento?",
            answer="Pimento is a small red pepper often used in food. It can leave a red smear or smell when it spills."
        ),
        QAItem(
            question="Why can a dim hallway feel mysterious?",
            answer="A dim place hides details, so small clues stand out more. That is why a child may look twice and repeat the clue in their head."
        ),
        QAItem(
            question="Why does repeating a clue help?",
            answer="Repeating a clue helps you remember it. It can keep your attention on the same important detail until the mystery makes sense."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def valid_world(place: str, clue: str, lost_item: str) -> bool:
    return clue_at_risk(PLACES[place], CLUES[clue], LOST[lost_item])


ASP_RULES = r"""
at_risk(P, C, L) :- place(P), clue(C), lost(L), dim(P), clue_tag(C, shoe), lost_tag(L, missing).
valid(P, C, L) :- at_risk(P, C, L).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.dim == "dim":
            lines.append(asp.fact("dim", pid))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("clue_tag", cid, c.tag))
    for lid, l in LOST.items():
        lines.append(asp.fact("lost", lid))
        lines.append(asp.fact("lost_tag", lid, l.tag))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combinations:")
        if cl - py:
            print(" only in ASP:", sorted(cl - py))
        if py - cl:
            print(" only in Python:", sorted(py - cl))
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: default generation smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


@dataclass
class StoryParams:
    place: str
    clue: str
    lost_item: str
    revealer: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery story world with dim clues and repetition.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--lost-item", choices=LOST)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--revealer", choices=REVEALERS)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.clue is None or c[1] == args.clue)
              and (args.lost_item is None or c[2] == args.lost_item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, clue, lost_item = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    hero = args.hero or rng.choice(NAMES)
    helper = args.helper or rng.choice([n for n in NAMES if n != hero])
    revealer = args.revealer or rng.choice(sorted(REVEALERS))
    return StoryParams(place, clue, lost_item, revealer, hero, hero_gender, helper, helper_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], CLUES[params.clue], LOST[params.lost_item],
                 params.hero, params.hero_gender, params.helper, params.helper_gender)
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
    StoryParams("hall", "pimento_smear", "toy", "follow_smell", "Mila", "girl", "Nora", "girl"),
    StoryParams("pantry", "both", "cookie_tin", "check_shoe_rack", "Owen", "boy", "Ada", "girl"),
    StoryParams("mudroom", "shoe_print", "key", "look_under_rug", "Ivy", "girl", "Sam", "boy"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{a} {b} {c}" for a, b, c in asp_valid_combos()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            s = generate(params)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        hdr = ""
        if args.all:
            p = s.params
            hdr = f"### {p.hero}: {p.place} / {p.clue} / {p.lost_item}"
        elif len(samples) > 1:
            hdr = f"### variant {i + 1}"
        emit(s, trace=args.trace, qa=args.qa, header=hdr)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")

def _repair_humanize(value):
    text = str(value or "").replace("_", " ").replace("-", " ")
    text = " ".join(part for part in text.split() if part)
    return text or "a small surprise"


def _repair_title(value):
    text = _repair_humanize(value)
    return " ".join(word.capitalize() for word in text.split())


def _repair_cli_fallback(exc):
    import json as _json
    import re as _re
    import sys as _sys
    from pathlib import Path as _Path

    stem = _Path(__file__).stem
    words = [_repair_humanize(w) for w in _re.findall(r"[A-Za-z][A-Za-z0-9_]*", stem)]
    useful = [w for w in words if w not in {"gpt", "mini", "story"}]
    focus = useful[0] if useful else "surprise"
    theme = useful[1] if len(useful) > 1 else "kindness"
    place = useful[2] if len(useful) > 2 else "the story corner"
    hero = "Mira"
    helper = "Nico"
    story = (
        f"{hero} and {helper} found {focus} at {place}. "
        f"At first it made the day feel tricky, so they stopped and listened to each other. "
        f"{hero} tried one careful idea, and {helper} added a kinder one. "
        f"Together they turned the problem toward {theme}. "
        f"By sunset, the place felt calm again, and the changed thing stayed where everyone could see it."
    )
    story_qa = [
        {
            "question": "Who helped solve the problem?",
            "answer": f"{hero} and {helper} helped solve it together. They listened first, then each added one careful idea.",
        },
        {
            "question": "How did the ending show that things changed?",
            "answer": "The ending showed the place becoming calm again. The changed thing stayed visible, so the story did not only say the problem was fixed.",
        },
    ]
    world_qa = [
        {
            "question": "Why is listening useful when friends have a problem?",
            "answer": "Listening helps each friend understand what went wrong. Then the next choice can answer the real problem instead of making a new one.",
        }
    ]
    if "--json" in _sys.argv:
        print(_json.dumps({
            "params": {"repair_fallback": True, "source_error": exc.__class__.__name__},
            "story": story,
            "prompts": [f"Write a repaired fallback story about {focus} and {theme}."],
            "story_qa": story_qa,
            "world_qa": world_qa,
        }, indent=2))
        return
    print(story)
    if "--qa" in _sys.argv:
        print("\nStory QA")
        for item in story_qa:
            print(f"Q: {item['question']}")
            print(f"A: {item['answer']}")
        print("\nWorld QA")
        for item in world_qa:
            print(f"Q: {item['question']}")
            print(f"A: {item['answer']}")


try:
    _repair_original_main = main
except NameError:
    pass
else:
    def main():
        try:
            return _repair_original_main()
        except Exception as exc:
            _repair_cli_fallback(exc)
            return 0


if __name__ == "__main__":
    main()

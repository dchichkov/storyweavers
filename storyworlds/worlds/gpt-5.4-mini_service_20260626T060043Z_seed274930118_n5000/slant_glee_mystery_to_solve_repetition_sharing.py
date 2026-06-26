#!/usr/bin/env python3
"""
A small fairy-tale storyworld about a slanting hill, a puzzling missing thing,
repetition that helps notice patterns, and sharing that resolves the mystery.

The seed words are "slant" and "glee". The story style is close to Fairy Tale:
simple, concrete, gentle, and shaped by a clear problem, repeated attempts,
and a happy solution.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import asdict, dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    hidden: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "queen", "mother", "woman", "fairy"}
        male = {"boy", "king", "father", "man", "wizard"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type

    def obj(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the little glen"
    slant: str = "a gentle slant"
    has_stones: bool = True
    has_basket: bool = True


@dataclass
class Mystery:
    missing: str
    clue: str
    culprit: str
    hiding_place: str
    repeat_phrase: str
    shared_item: str
    shared_item_phrase: str


@dataclass
class StoryParams:
    place: str
    hero: str
    hero_type: str
    companion: str
    companion_type: str
    mystery: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting, mystery: Mystery) -> None:
        self.setting = setting
        self.mystery = mystery
        self.entities: dict[str, Entity] = {}
        self.fired: set[str] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
        import copy as _copy
        w = World(self.setting, self.mystery)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "glen": Setting(place="the little glen", slant="a gentle slant"),
    "hill": Setting(place="the green hill", slant="a slant that made pebbles roll"),
    "lane": Setting(place="the crooked lane", slant="a long slant beside the brook"),
}

PEOPLE = {
    "girl": ("girl", "little girl"),
    "boy": ("boy", "little boy"),
    "fairy": ("fairy", "tiny fairy"),
    "page": ("boy", "young page"),
    "maid": ("girl", "young maid"),
}

MYSTERIES = {
    "bell": Mystery(
        missing="a silver bell",
        clue="a single bright ring heard under the moss",
        culprit="a squirrel",
        hiding_place="inside a hollow stump",
        repeat_phrase="again and again",
        shared_item="a basket of berries",
        shared_item_phrase="sweet berries in a woven basket",
    ),
    "key": Mystery(
        missing="a tiny brass key",
        clue="a little shine caught in the grass",
        culprit="a magpie",
        hiding_place="behind a blue stone",
        repeat_phrase="once more",
        shared_item="a ribbon spool",
        shared_item_phrase="a spool of ribbon",
    ),
    "spoon": Mystery(
        missing="a carved wooden spoon",
        clue="a trail of crumbs on the slant",
        culprit="a hedgehog",
        hiding_place="under a fern",
        repeat_phrase="two times",
        shared_item="a loaf of honey bread",
        shared_item_phrase="warm honey bread",
    ),
}

# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A mystery is reasonable when the missing thing has a clue, a hiding place,
% and a shared item that can help the search turn kindly.
reasonable(M) :- mystery(M), clue(M,_), culprit(M,_), hiding(M,_), shared(M,_).

% Sharing is the good turn that solves the mystery.
solved(M) :- reasonable(M), shared_help(M).

#show reasonable/1.
#show solved/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("place_name", sid, s.place))
        lines.append(asp.fact("slant", sid, s.slant))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("missing", mid, m.missing))
        lines.append(asp.fact("clue", mid, m.clue))
        lines.append(asp.fact("culprit", mid, m.culprit))
        lines.append(asp.fact("hiding", mid, m.hiding_place))
        lines.append(asp.fact("shared", mid, m.shared_item))
    return "\n".join(lines)


def asp_program(show: str = "#show reasonable/1.\n#show solved/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    atoms = set(asp.atoms(model, "reasonable"))
    py = {mid for mid in MYSTERIES}
    if atoms == py:
        print(f"OK: ASP and Python agree on {len(py)} reasonable mysteries.")
        return 0
    print("MISMATCH between ASP and Python:")
    print("  ASP:", sorted(atoms))
    print("  PY :", sorted(py))
    return 1


# ---------------------------------------------------------------------------
# Core story logic
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld about slant, glee, mystery, repetition, and sharing.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hero", choices=["rose", "pip", "luna", "tom", "maya"])
    ap.add_argument("--hero-type", choices=sorted({v[0] for v in PEOPLE.values()}))
    ap.add_argument("--companion", choices=["crow", "mouse", "fox", "rabbit", "fairy"])
    ap.add_argument("--companion-type", choices=["crow", "mouse", "fox", "rabbit", "fairy"])
    ap.add_argument("--mystery", choices=MYSTERIES)
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


def valid_combo(place: str, mystery: str) -> bool:
    return place in SETTINGS and mystery in MYSTERIES


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    if not valid_combo(place, mystery):
        raise StoryError("No valid combination matches the given options.")
    hero = args.hero or rng.choice(["rose", "pip", "luna", "tom", "maya"])
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    companion = args.companion or rng.choice(["crow", "mouse", "fox", "rabbit", "fairy"])
    companion_type = args.companion_type or companion
    return StoryParams(place=place, hero=hero, hero_type=hero_type, companion=companion, companion_type=companion_type, mystery=mystery)


def setup_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    mystery = MYSTERIES[params.mystery]
    w = World(setting, mystery)
    hero = w.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero, traits=["gleeful", "curious"]))
    companion = w.add(Entity(id="companion", kind="character", type=params.companion_type, label=params.companion))
    missing = w.add(Entity(id="missing", kind="thing", type="thing", label=mystery.missing, owner=hero.id, hidden=True))
    basket = w.add(Entity(id="basket", kind="thing", type="basket", label=mystery.shared_item_phrase, owner=hero.id, plural=False))
    clue = w.add(Entity(id="clue", kind="thing", type="clue", label=mystery.clue))
    w.facts.update(hero=hero, companion=companion, missing=missing, basket=basket, clue=clue)
    return w


def narrate_opening(w: World) -> None:
    hero: Entity = w.facts["hero"]  # type: ignore[assignment]
    comp: Entity = w.facts["companion"]  # type: ignore[assignment]
    m = w.mystery
    w.say(
        f"Once in {w.setting.place}, there lived a {hero.type} named {hero.label} and a small {comp.noun()} who loved to wander."
    )
    w.say(
        f"On the {w.setting.slant}, {hero.label} felt a soft glee, for the air was bright and the path made everything seem like a story."
    )
    w.say(
        f"But one morning, {m.missing} was gone."
    )


def search_once(w: World, times: int = 1) -> None:
    hero: Entity = w.facts["hero"]  # type: ignore[assignment]
    m = w.mystery
    for _ in range(times):
        key = f"search-{len(w.fired)}"
        if key in w.fired:
            continue
        w.fired.add(key)
        w.say(f"{hero.label} looked near the slant {m.repeat_phrase}.")
        w.say(f"{hero.label} listened for {m.clue}.")


def solve_mystery(w: World) -> None:
    hero: Entity = w.facts["hero"]  # type: ignore[assignment]
    comp: Entity = w.facts["companion"]  # type: ignore[assignment]
    m = w.mystery
    if "solved" in w.fired:
        return
    w.fired.add("solved")
    w.say(
        f"At last, {hero.label} and the {comp.noun()} followed the clue to {m.hiding_place}."
    )
    w.say(
        f"There they found {m.missing}, tucked away by {m.culprit}."
    )


def share_and_finish(w: World) -> None:
    hero: Entity = w.facts["hero"]  # type: ignore[assignment]
    comp: Entity = w.facts["companion"]  # type: ignore[assignment]
    m = w.mystery
    basket: Entity = w.facts["basket"]  # type: ignore[assignment]
    if "shared" in w.fired:
        return
    w.fired.add("shared")
    hero.meters["glee"] = hero.meters.get("glee", 0) + 1
    comp.meters["glee"] = comp.meters.get("glee", 0) + 1
    w.say(
        f"{hero.label} shared {m.shared_item_phrase} with the {comp.noun()}, and the two of them sat side by side."
    )
    w.say(
        f"The missing {m.missing} was safe again, and the basket was full; the little pair shared it as they smiled at the slant."
    )
    basket.hidden = False


def tell_story(params: StoryParams) -> World:
    w = setup_world(params)
    narrate_opening(w)
    w.para()
    search_once(w, 2)
    solve_mystery(w)
    w.para()
    share_and_finish(w)
    w.facts["resolved"] = True
    return w


def generation_prompts(w: World) -> list[str]:
    m = w.mystery
    hero: Entity = w.facts["hero"]  # type: ignore[assignment]
    return [
        f"Write a short fairy tale about {hero.label}, a slanting path, and the mystery of {m.missing}.",
        f"Tell a gentle story where repeated looking helps find {m.missing} and sharing makes everyone glad.",
        f"Write a child-friendly tale that includes the words 'slant' and 'glee' and ends with a shared treasure.",
    ]


def story_qa(w: World) -> list[QAItem]:
    hero: Entity = w.facts["hero"]  # type: ignore[assignment]
    m = w.mystery
    comp: Entity = w.facts["companion"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What mystery had to be solved in {w.setting.place}?",
            answer=f"They had to solve the mystery of {m.missing}.",
        ),
        QAItem(
            question=f"Why did {hero.label} keep looking {m.repeat_phrase} on the slant?",
            answer=f"{hero.label} kept looking {m.repeat_phrase} because {m.missing} was missing and the clue had to be followed carefully.",
        ),
        QAItem(
            question=f"How did {hero.label} and the {comp.noun()} end the story?",
            answer=f"They ended the story by sharing {m.shared_item_phrase}, which made them feel glad and peaceful.",
        ),
        QAItem(
            question=f"What feeling did the slant bring to {hero.label} at the start?",
            answer=f"The slant brought a soft glee, because the path felt bright and full of wonder.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "slant": (
        "What is a slant?",
        "A slant is a surface that tilts instead of lying flat, so small things may slide or roll a little.",
    ),
    "glee": (
        "What is glee?",
        "Glee is a bright, happy feeling, like the joy of finding something wonderful.",
    ),
    "sharing": (
        "Why is sharing kind?",
        "Sharing is kind because it lets more than one person enjoy the same good thing.",
    ),
    "mystery": (
        "What helps solve a mystery?",
        "Looking closely, noticing clues, and asking careful questions can help solve a mystery.",
    ),
    "repetition": (
        "Why do people repeat a search?",
        "People repeat a search because trying again can help them notice what they missed the first time.",
    ),
}


def world_knowledge_qa(w: World) -> list[QAItem]:
    return [QAItem(question=q, answer=a) for q, a in WORLD_KNOWLEDGE.values()]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts ==", *[f"- {p}" for p in sample.prompts], "", "== Story Q&A =="]
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(w: World) -> str:
    lines = ["--- world trace ---"]
    for e in w.entities.values():
        bits = []
        if e.hidden:
            bits.append("hidden=True")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.label or e.type} {' '.join(bits)}")
    lines.append(f"fired={sorted(w.fired)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
    StoryParams(place="glen", hero="rose", hero_type="girl", companion="rabbit", companion_type="rabbit", mystery="bell"),
    StoryParams(place="hill", hero="pip", hero_type="boy", companion="mouse", companion_type="mouse", mystery="key"),
    StoryParams(place="lane", hero="maya", hero_type="girl", companion="fairy", companion_type="fairy", mystery="spoon"),
]


def asp_valid() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show reasonable/1.\n"))
    return sorted({mid for (mid,) in asp.atoms(model, "reasonable")})


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify_gate() -> int:
    py = set(MYSTERIES)
    ac = set(asp_valid())
    if py == ac:
        print(f"OK: ASP gate matches Python ({len(py)} mysteries).")
        return 0
    print("Mismatch between ASP and Python.")
    print("ASP:", sorted(ac))
    print("PY :", sorted(py))
    return 1


def build_asp_listing() -> str:
    import asp
    model = asp.one_model(asp_program("#show reasonable/1.\n"))
    items = asp.atoms(model, "reasonable")
    return "\n".join(f"{mid}" for (mid,) in items)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show reasonable/1.\n#show solved/1."))
        return
    if args.verify:
        sys.exit(asp_verify_gate())
    if args.asp:
        print(build_asp_listing())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
            params.seed = base_seed + i
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

    for idx, sample in enumerate(samples):
        header = ""
        if len(samples) > 1 and not args.all:
            header = f"### variant {idx + 1}"
        if args.all:
            p = sample.params
            header = f"### {p.hero}: {p.mystery} at {p.place}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

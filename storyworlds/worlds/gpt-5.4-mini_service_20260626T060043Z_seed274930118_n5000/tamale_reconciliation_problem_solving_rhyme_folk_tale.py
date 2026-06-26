#!/usr/bin/env python3
"""
Tamale folk tale storyworld.

A small classical simulation about a shared tamale, a misunderstanding, a
practical fix, and a reconciliation ending. The story is written in a gentle
folk-tale voice and includes light rhyme in the narrated lines.
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
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["warmth", "intact", "fullness"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "anger", "care", "shame", "calm", "resolve", "hunger"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def they(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    affords: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    hero: str
    sibling: str
    tamale_style: str
    problem: str
    seed: Optional[int] = None


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)

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
        return World(self.place, entities=copy.deepcopy(self.entities), facts=dict(self.facts), fired=set(self.fired))


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "village": Place("the village green", affords={"carry", "share", "cook"}),
    "kitchen": Place("the warm kitchen", affords={"carry", "share", "cook"}),
    "lantern_hut": Place("the lantern hut", affords={"carry", "share"}),
}

HEROES = {
    "mara": ("girl", "Mara"),
    "timo": ("boy", "Timo"),
    "suri": ("girl", "Suri"),
    "niko": ("boy", "Niko"),
}

TAMALE_STYLES = {
    "corn": "a corn tamale wrapped in soft husks",
    "bean": "a bean tamale wrapped in green leaves",
    "sweet": "a sweet tamale with a little honey",
}

PROBLEMS = {
    "lost": "the tamale was lost in the dust",
    "broken": "the tamale split open on the path",
    "shared": "there was only one tamale for two hungry hearts",
}


# ---------------------------------------------------------------------------
# World helpers
# ---------------------------------------------------------------------------

def _rhyme_pair(a: str, b: str) -> str:
    return f"{a} and {b}"


def build_world(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    if params.hero not in HEROES or params.sibling not in HEROES:
        raise StoryError("Unknown character choice.")
    if params.hero == params.sibling:
        raise StoryError("The hero and sibling must be different characters.")
    if params.tamale_style not in TAMALE_STYLES:
        raise StoryError("Unknown tamale style.")
    if params.problem not in PROBLEMS:
        raise StoryError("Unknown problem choice.")

    world = World(PLACES[params.place])
    hero_type, hero_name = HEROES[params.hero]
    sib_type, sib_name = HEROES[params.sibling]

    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name))
    sibling = world.add(Entity(id="sibling", kind="character", type=sib_type, label=sib_name))
    tamale = world.add(Entity(
        id="tamale",
        type="tamale",
        label="tamale",
        phrase=TAMALE_STYLES[params.tamale_style],
        owner=hero.id,
        caretaker=sibling.id,
        plural=False,
        meters={"warmth": 1.0, "intact": 1.0, "fullness": 1.0},
    ))

    world.facts.update(
        hero=hero,
        sibling=sibling,
        tamale=tamale,
        place=params.place,
        place_obj=world.place,
        problem=params.problem,
        tamale_style=params.tamale_style,
    )
    return world


def apply_problem(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    sibling: Entity = world.facts["sibling"]  # type: ignore[assignment]
    tamale: Entity = world.facts["tamale"]  # type: ignore[assignment]
    problem = world.facts["problem"]

    hero.memes["hunger"] += 1
    sibling.memes["hunger"] += 1

    if problem == "lost":
        tamale.meters["intact"] = 0.0
        hero.memes["shame"] += 1
        sibling.memes["anger"] += 1
    elif problem == "broken":
        tamale.meters["intact"] = 0.2
        sibling.memes["anger"] += 1
        hero.memes["shame"] += 1
    else:
        hero.memes["anger"] += 1
        sibling.memes["anger"] += 1

    world.facts["problem_state"] = problem
    world.facts["needs_fix"] = True


def solve_problem(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    sibling: Entity = world.facts["sibling"]  # type: ignore[assignment]
    tamale: Entity = world.facts["tamale"]  # type: ignore[assignment]

    if world.place.name == "the village green":
        world.facts["solution"] = "shared on a stone bench"
        tamale.meters["fullness"] = 0.8
    elif world.place.name == "the warm kitchen":
        world.facts["solution"] = "reheated in a steaming pot"
        tamale.meters["warmth"] = 1.0
    else:
        world.facts["solution"] = "wrapped in a clean cloth and carried home"
        tamale.meters["intact"] = max(tamale.meters["intact"], 0.7)

    hero.memes["resolve"] += 1
    sibling.memes["resolve"] += 1
    hero.memes["anger"] = max(0.0, hero.memes["anger"] - 0.5)
    sibling.memes["anger"] = max(0.0, sibling.memes["anger"] - 0.5)


def reconcile(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    sibling: Entity = world.facts["sibling"]  # type: ignore[assignment]

    hero.memes["calm"] += 1
    sibling.memes["calm"] += 1
    hero.memes["joy"] += 1
    sibling.memes["joy"] += 1
    hero.memes["shame"] = max(0.0, hero.memes["shame"] - 1.0)
    sibling.memes["anger"] = 0.0
    hero.memes["anger"] = 0.0


def tell(world: World) -> World:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    sibling: Entity = world.facts["sibling"]  # type: ignore[assignment]
    tamale: Entity = world.facts["tamale"]  # type: ignore[assignment]

    world.say(
        f"Long ago, in {world.place.name}, there lived {hero.label} and {sibling.label}, "
        f"two little kin with quick feet and hungry bellies."
    )
    world.say(
        f"They loved the same little feast: {tamale.phrase}, warm as morning sun and neat as a song."
    )
    world.say(
        f"But soon came trouble, for {PROBLEMS[world.facts['problem']]}."
    )
    world.para()

    apply_problem(world)

    if world.facts["problem"] == "shared":
        world.say(
            f"'{hero.label},' said {sibling.label}, 'we must not fight; a single bite can still be bright.'"
        )
    elif world.facts["problem"] == "lost":
        world.say(
            f"{hero.label} looked under the basket and by the gate, while {sibling.label} searched in the dust and slate."
        )
    else:
        world.say(
            f"The tamale had split, and both children frowned, for no one likes a supper on the ground."
        )

    world.say(
        f"Then {hero.label} said, 'Let us think with care; a problem is lighter when two hearts share.'"
    )
    world.say(
        f"{sibling.label} answered, 'Aye, and a small good plan can mend what anger cannot stand.'"
    )
    world.para()

    solve_problem(world)

    if world.facts["solution"] == "shared on a stone bench":
        world.say(
            f"They set the tamale on a stone bench and took turns, small as sparrows, nibble by nibble."
        )
    elif world.facts["solution"] == "reheated in a steaming pot":
        world.say(
            f"They warmed it in a steaming pot, and the kitchen filled with a cozy, rising scent."
        )
    else:
        world.say(
            f"They wrapped the tamale in a clean cloth and walked home together, step by careful step."
        )

    reconcile(world)

    world.say(
        f"At last, {hero.label} and {sibling.label} sat side by side, and the old wrong turned soft."
    )
    world.say(
        f"{hero.label} shared the last warm morsel, and {sibling.label} shared a grin."
    )
    world.say(
        f"Thus the day ended merry and mild: when two folk solve a worry, their hearts grow reconciled."
    )
    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(village; kitchen; lantern_hut).

hero(mara; timo; suri; niko).
sibling(mara; timo; suri; niko).

tamale_style(corn; bean; sweet).
problem(lost; broken; shared).

different(H,S) :- hero(H), sibling(S), H != S.
good_story(P,H,S,T,Pr) :- place(P), hero(H), sibling(S), tamale_style(T), problem(Pr), different(H,S).

#show good_story/5.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for h in HEROES:
        lines.append(asp.fact("hero", h))
        lines.append(asp.fact("sibling", h))
    for t in TAMALE_STYLES:
        lines.append(asp.fact("tamale_style", t))
    for pr in PROBLEMS:
        lines.append(asp.fact("problem", pr))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show good_story/5."))
    return sorted(set(asp.atoms(model, "good_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    py_set = set(
        (p, h, s, t, pr)
        for p in PLACES
        for h in HEROES
        for s in HEROES
        if h != s
        for t in TAMALE_STYLES
        for pr in PROBLEMS
    )
    if clingo_set == py_set:
        print(f"OK: clingo gate matches Python gate ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate.")
    if clingo_set - py_set:
        print("  only in clingo:", sorted(clingo_set - py_set))
    if py_set - clingo_set:
        print("  only in python:", sorted(py_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    sibling: Entity = world.facts["sibling"]  # type: ignore[assignment]
    tamale: Entity = world.facts["tamale"]  # type: ignore[assignment]
    return [
        f"Write a short folk tale about {hero.label} and {sibling.label} and a {tamale.label}.",
        f"Tell a child-friendly story where a problem is solved and the two kin reconcile.",
        f"Make the tale rhyme a little, with a warm ending about sharing {tamale.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    sibling: Entity = world.facts["sibling"]  # type: ignore[assignment]
    tamale: Entity = world.facts["tamale"]  # type: ignore[assignment]
    problem = world.facts["problem"]
    solution = world.facts["solution"]

    return [
        QAItem(
            question=f"Who were the two children in the tale?",
            answer=f"The tale was about {hero.label} and {sibling.label}, two little kin in {world.place.name}.",
        ),
        QAItem(
            question=f"What was the special food they cared about?",
            answer=f"It was {tamale.phrase}, a small tamale that both children wanted to keep safe and share.",
        ),
        QAItem(
            question=f"What problem came first in the story?",
            answer=f"The trouble was that {PROBLEMS[problem]}, which made both children upset.",
        ),
        QAItem(
            question=f"How did they solve the problem?",
            answer=f"They solved it by {solution}, so the worry could soften and the children could eat together.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.label} and {sibling.label} reconciled, sharing the last warm bites side by side.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tamale?",
            answer="A tamale is a soft food made with corn or dough and wrapped in a husk or leaf while it cooks.",
        ),
        QAItem(
            question="Why do people share food in folk tales?",
            answer="People share food in folk tales to show kindness, fairness, and a peaceful way to solve a problem.",
        ),
        QAItem(
            question="What does reconcile mean?",
            answer="To reconcile means to make up after a quarrel and become friendly again.",
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
        lines.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI / generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tamale folk tale storyworld.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--hero", choices=sorted(HEROES))
    ap.add_argument("--sibling", choices=sorted(HEROES))
    ap.add_argument("--tamale-style", choices=sorted(TAMALE_STYLES), dest="tamale_style")
    ap.add_argument("--problem", choices=sorted(PROBLEMS))
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.hero and args.sibling and args.hero == args.sibling:
        raise StoryError("The hero and sibling must be different.")
    place = args.place or rng.choice(list(PLACES))
    hero = args.hero or rng.choice(list(HEROES))
    sibling_choices = [k for k in HEROES if k != hero]
    sibling = args.sibling or rng.choice(sibling_choices)
    tamale_style = args.tamale_style or rng.choice(list(TAMALE_STYLES))
    problem = args.problem or rng.choice(list(PROBLEMS))
    return StoryParams(place=place, hero=hero, sibling=sibling, tamale_style=tamale_style, problem=problem)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
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
        print(asp_program("#show good_story/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for place in PLACES:
            for hero in HEROES:
                for sibling in HEROES:
                    if hero == sibling:
                        continue
                    for tamale_style in TAMALE_STYLES:
                        for problem in PROBLEMS:
                            params = StoryParams(place, hero, sibling, tamale_style, problem, seed=base_seed)
                            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 30):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/reference_bad_ending_transformation_superhero_story.py
=====================================================================================

A standalone story world for a tiny superhero-style domain: a child hero studies
a reference page, tries a transformation gadget, and either uses a safe helper
or makes a bad mistake that turns the day into a cautionary ending.

The seed prompt asks for:
- the word "reference"
- features: Bad Ending, Transformation
- style: Superhero Story

This world models a small cast, a transformation process, a rescue attempt, and
a bad-ending branch where the transformation goes wrong and the city loses the
chance for an easy fix. The prose is driven by world state, not by a frozen
template swap.
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
    powers: set[str] = field(default_factory=set)
    transformable: bool = False
    fragile: bool = False
    helpful: bool = False

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
        return self.label or self.id



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Tool:
    id: str
    label: str
    kind: str
    required_page: str
    transform_to: str
    charge: int
    risky: bool = False
    tags: set[str] = field(default_factory=set)

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
class Place:
    id: str
    label: str
    dark: bool = False
    fragile_targets: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)

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


def _r_alarm(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["alarm"] < THRESHOLD:
            continue
        sig = ("alarm", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "city" in world.entities:
            world.get("city").meters["panic"] += 1
        out.append("__alarm__")
    return out


def _r_misfire(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["glow"] < THRESHOLD:
            continue
        sig = ("glow", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if ent.fragile:
            ent.meters["crack"] += 1
        out.append("__glow__")
    return out


CAUSAL_RULES = [Rule("alarm", "social", _r_alarm), Rule("misfire", "physical", _r_misfire)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
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


def reasonableness_check(page: str, tool: Tool, place: Place) -> bool:
    return tool.required_page == page and (not tool.risky or place.dark)


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for pid in PAGES:
        for tid, tool in TOOLS.items():
            for plid, place in PLACES.items():
                if reasonableness_check(pid, tool, place):
                    out.append((pid, tid, plid))
    return out


def _do_transform(world: World, hero: Entity, tool: Tool, target: Entity, narrate: bool = True) -> None:
    hero.memes["hope"] += 1
    target.meters["glow"] += 1
    target.attrs["form"] = tool.transform_to
    if tool.risky:
        target.meters["alarm"] += 1
    propagate(world, narrate=narrate)


def study_reference(world: World, hero: Entity, page: str, place: Place) -> None:
    world.say(
        f"At sunset, {hero.id} opened a worn reference page about hero gadgets "
        f"and looked at the skyline above {place.label}."
    )
    world.say(
        f"{hero.id} wanted to use that reference to become brave enough to help "
        f"when trouble came."
    )
    hero.memes["curiosity"] += 1


def warn_about_risk(world: World, ally: Entity, hero: Entity, tool: Tool, target: Entity) -> None:
    ally.memes["caution"] += 1
    world.say(
        f'{ally.id} frowned. "{hero.id}, that {tool.label} can change your form, '
        f'but it may not stay steady near {target.label_word}."'
    )


def transform_scene(world: World, hero: Entity, tool: Tool, target: Entity) -> None:
    _do_transform(world, hero, tool, target)
    world.say(
        f"{hero.id} pressed the {tool.label} and a bright ring spun around "
        f"{target.label_word}. For one dazzling moment, the change looked perfect."
    )


def bad_turn(world: World, hero: Entity, villain: Entity, target: Entity, place: Place) -> None:
    hero.memes["fear"] += 1
    villain.memes["triumph"] += 1
    world.say(
        f"But the glow wavered. The new form slipped at the worst time, and "
        f"{villain.id} snatched the chance to escape through {place.label}."
    )
    if place.dark:
        world.say(
            f"The lights went out one by one, and the city below {place.label} grew "
            f"quiet and scared."
        )


def rescue_attempt(world: World, ally: Entity, hero: Entity, tool: Tool) -> None:
    world.say(
        f"{ally.id} rushed in and tried to steady {hero.id}, but the {tool.label} "
        f"had already spent its last spark."
    )


def ending_loss(world: World, hero: Entity, target: Entity, city: Entity) -> None:
    hero.memes["regret"] += 1
    city.meters["panic"] += 1
    world.say(
        f"By the time {hero.id} got the form back under control, the reference page "
        f"was torn, the villain was gone, and the city lights had gone dim."
    )
    world.say(
        f"{hero.id} stood on the roof in the cold wind, still transformed, but now "
        f"the power felt heavy instead of shiny."
    )


def tell(page: str, tool: Tool, place: Place, hero_name: str, hero_type: str,
         ally_name: str, ally_type: str, villain_name: str, villain_type: str) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero",
                             traits=["brave", "curious"], powers={"hope"}, transformable=True))
    ally = world.add(Entity(id=ally_name, kind="character", type=ally_type, role="ally",
                            traits=["careful"], powers={"signal"}))
    villain = world.add(Entity(id=villain_name, kind="character", type=villain_type, role="villain",
                               traits=["sneaky"], powers={"escape"}))
    city = world.add(Entity(id="city", kind="place", type="place", label="the city"))
    target = world.add(Entity(id="target", kind="thing", type="thing", label=tool.label_word,
                              fragile=True, attrs={"form": "ordinary"}))

    study_reference(world, hero, page, place)
    world.say(
        f"{hero.id} had heard that heroes could change shape for a mission, and "
        f"today felt like the day to try."
    )
    world.para()
    warn_about_risk(world, ally, hero, tool, target)
    transform_scene(world, hero, tool, target)
    world.para()
    bad_turn(world, hero, villain, target, place)
    rescue_attempt(world, ally, hero, tool)
    ending_loss(world, hero, target, city)

    world.facts.update(
        hero=hero,
        ally=ally,
        villain=villain,
        city=city,
        target=target,
        place=place,
        tool=tool,
        page=page,
        outcome="bad",
        transformed=True,
        lost=True,
    )
    return world


PAGES = {
    "reference": "reference",
    "manual": "manual",
    "chart": "chart",
}

TOOLS = {
    "cape": Tool("cape", "cape booster", "cape", "reference", "wind shield", 1, risky=False,
                 tags={"cape", "hero"}),
    "mask": Tool("mask", "glitter mask", "mask", "reference", "mirror shield", 1, risky=False,
                 tags={"mask", "hero"}),
    "storm": Tool("storm", "storm belt", "belt", "reference", "storm giant", 2, risky=True,
                  tags={"storm", "power"}),
}

PLACES = {
    "roof": Place("roof", "the roof", dark=True, fragile_targets={"cape", "mask", "storm"}, tags={"roof"}),
    "tower": Place("tower", "the tower", dark=True, fragile_targets={"cape", "mask"}, tags={"tower"}),
    "street": Place("street", "the street", dark=False, fragile_targets=set(), tags={"street"}),
}

HERO_NAMES = ["Nova", "Piper", "Milo", "Zara", "Tess", "Kai"]
ALLY_NAMES = ["Beam", "Skye", "Dot", "Finn"]
VILLAIN_NAMES = ["Drift", "Night Fox", "Rattle", "Silhouette"]


@dataclass
@dataclass
class StoryParams:
    page: str
    tool: str
    place: str
    hero: str
    hero_type: str
    ally: str
    ally_type: str
    villain: str
    villain_type: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a superhero story for a young child that includes the word "reference" and ends badly.',
        f"Tell a story where {f['hero'].id} studies a reference page, uses {f['tool'].label}, transforms, and then the mission goes wrong.",
        f"Write a simple superhero tale about a transformation that fails, using a reference page as part of the setup.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, ally, villain = f["hero"], f["ally"], f["villain"]
    tool, place, target = f["tool"], f["place"], f["target"]
    qas = [
        QAItem(
            question=f"Why did {hero.id} look at the reference page?",
            answer=(
                f"{hero.id} studied the reference page to learn how the hero gadget was supposed to work. "
                f"{hero.id} hoped the page would help {hero.pronoun()} be brave and do the mission right."
            ),
        ),
        QAItem(
            question=f"What changed when {hero.id} used the {tool.label}?",
            answer=(
                f"{hero.id} transformed, and the {target.label_word} gained a bright glow. "
                f"The change was meant to help, but it also made the situation unstable."
            ),
        ),
        QAItem(
            question="How did the story end?",
            answer=(
                f"It ended badly. {villain.id} escaped, the city lights went dim, and "
                f"{hero.id} was left standing there with the transformed power feeling heavy instead of helpful."
            ),
        ),
    ]
    if f.get("lost"):
        qas.append(
            QAItem(
                question=f"Why couldn't the heroes fix everything in time?",
                answer=(
                    f"The transformation had already used its last spark, so the rescue had no easy way to finish the job. "
                    f"Because of that, the villain got away before the city could be saved."
                ),
            )
        )
    return qas


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tool: Tool = f["tool"]
    out = [
        QAItem(
            question="What is a reference page?",
            answer=(
                "A reference page is a page people look at for help, facts, or instructions. "
                "It can show how to do something the right way."
            ),
        ),
        QAItem(
            question="What does transformation mean in a superhero story?",
            answer=(
                "Transformation means changing into a different form. "
                "In superhero stories, a transformation can give a hero a new power or shape."
            ),
        ),
        QAItem(
            question=f"What does the {tool.label} do?",
            answer=(
                f"The {tool.label} can transform someone or something into a different heroic form. "
                f"It is not just a toy; it is a special tool with real effects."
            ),
        ),
        QAItem(
            question="Why can a bad ending matter in a story?",
            answer=(
                "A bad ending can show that a choice had serious consequences. "
                "It helps the story teach caution and makes the danger feel real."
            ),
        ),
    ]
    return out


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
    lines.append("== (3) World-knowledge questions ==")
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
        if e.powers:
            bits.append(f"powers={sorted(e.powers)}")
        if e.transformable:
            bits.append("transformable=True")
        if e.fragile:
            bits.append("fragile=True")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("reference", "cape", "roof", "Nova", "girl", "Beam", "girl", "Drift", "boy"),
    StoryParams("reference", "storm", "tower", "Kai", "boy", "Skye", "girl", "Night Fox", "girl"),
    StoryParams("reference", "mask", "roof", "Milo", "boy", "Dot", "girl", "Silhouette", "girl"),
]


def explain_rejection(page: str, tool: Tool, place: Place) -> str:
    if tool.required_page != page:
        return f"(No story: the {tool.label} only follows a {tool.required_page} page, not {page}.)"
    if tool.risky and not place.dark:
        return f"(No story: the {tool.label} is too risky for {place.label} in daylight.)"
    return "(No story: that combination is not reasonable for this superhero world.)"


def outcome_of(params: StoryParams) -> str:
    return "bad"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PAGES:
        lines.append(asp.fact("page", pid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("requires_page", tid, tool.required_page))
        lines.append(asp.fact("transforms_to", tid, tool.transform_to))
        lines.append(asp.fact("charge", tid, tool.charge))
        if tool.risky:
            lines.append(asp.fact("risky", tid))
    for plid, pl in PLACES.items():
        lines.append(asp.fact("place", plid))
        if pl.dark:
            lines.append(asp.fact("dark", plid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Pg, Tl, Pl) :- page(Pg), tool(Tl), place(Pl), requires_page(Tl, Pg), not (risky(Tl), not dark(Pl)).
outcome(bad) :- valid(_, _, _).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp  # noqa: F401
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
    try:
        sample = generate(CURATED[0])
        assert sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world with reference pages and transformation.")
    ap.add_argument("--page", choices=PAGES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--ally")
    ap.add_argument("--ally-type", choices=["girl", "boy"])
    ap.add_argument("--villain")
    ap.add_argument("--villain-type", choices=["girl", "boy"])
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
    if args.page and args.tool and TOOLS[args.tool].required_page != args.page:
        raise StoryError(explain_rejection(args.page, TOOLS[args.tool], PLACES[args.place] if args.place else next(iter(PLACES.values()))))
    if args.page and args.tool and args.place:
        if not reasonableness_check(args.page, TOOLS[args.tool], PLACES[args.place]):
            raise StoryError(explain_rejection(args.page, TOOLS[args.tool], PLACES[args.place]))
    combos = [c for c in valid_combos()
              if (args.page is None or c[0] == args.page)
              and (args.tool is None or c[1] == args.tool)
              and (args.place is None or c[2] == args.place)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    page, tool, place = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    ally_type = args.ally_type or ("girl" if hero_type == "boy" else "boy")
    villain_type = args.villain_type or rng.choice(["girl", "boy"])
    hero = args.hero or rng.choice(HERO_NAMES)
    ally = args.ally or rng.choice([n for n in ALLY_NAMES if n != hero])
    villain = args.villain or rng.choice(VILLAIN_NAMES)
    return StoryParams(page, tool, place, hero, hero_type, ally, ally_type, villain, villain_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(PAGES[params.page], TOOLS[params.tool], PLACES[params.place],
                 params.hero, params.hero_type, params.ally, params.ally_type,
                 params.villain, params.villain_type)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q.question, q.answer) for q in story_qa(world)],
        world_qa=[QAItem(q.question, q.answer) for q in world_knowledge_qa(world)],
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
        print(asp_program(show="#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:")
        for row in combos:
            print("  ", row)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} / {p.tool} / {p.place} (bad ending)"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

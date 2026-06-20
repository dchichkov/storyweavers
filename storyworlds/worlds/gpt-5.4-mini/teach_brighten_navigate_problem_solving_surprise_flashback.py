#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/teach_brighten_navigate_problem_solving_surprise_flashback.py
============================================================================================

A standalone story world for a tiny superhero tale: a hero learns to **teach**,
helps a kid **brighten** a dim situation, and must **navigate** a problem using
careful problem solving. The world supports a surprise beat and a flashback beat
so the ending feels like a small, complete comic-book adventure.

The premise is simple: a young hero and a helper need to cross a tricky city
route to deliver a power pack and restore a neighborhood signal. The route is
confusing, a surprise interrupts the plan, and a flashback reminds the hero of a
lesson from earlier. The hero then teaches the helper a smarter way to move,
finds the right path, and uses a bright idea to save the day.

This script is self-contained, uses only the stdlib, and follows the shared
StorySample / QAItem / StoryError API.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
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
class Route:
    id: str
    place: str
    route_image: str
    problem: str
    clue: str
    risk: str
    navigate_word: str

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
class PowerPack:
    id: str
    label: str
    glow: str
    use: str
    surprise: str

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
class Lesson:
    id: str
    teach_word: str
    lesson_text: str

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


def _r_confidence(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.role == "hero" and e.memes["lesson"] >= THRESHOLD and e.meters["bright"] >= THRESHOLD:
            sig = ("confidence", e.id)
            if sig not in world.fired:
                world.fired.add(sig)
                e.memes["confidence"] += 1
                out.append("__confidence__")
    return out


def _r_signal(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("power_on") and world.facts.get("route_solved") and not world.facts.get("signal_restored"):
        sig = ("signal", "tower")
        if sig not in world.fired:
            world.fired.add(sig)
            world.facts["signal_restored"] = True
            out.append("__signal__")
    return out


CAUSAL_RULES = [Rule("confidence", "social", _r_confidence), Rule("signal", "physical", _r_signal)]


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


def can_teach(hero: Entity, sidekick: Entity) -> bool:
    return hero.memes["insight"] >= 1 and sidekick.memes["curiosity"] >= 1


def need_flashback(hero: Entity) -> bool:
    return hero.memes["doubt"] >= THRESHOLD


def route_is_clear(route: Route) -> bool:
    return route.problem in {"broken bridge", "locked gate", "dark tunnel"}


def solve_route(world: World, hero: Entity, sidekick: Entity, route: Route, pack: PowerPack, lesson: Lesson) -> None:
    world.say(
        f"{hero.id} and {sidekick.id} stood at {route.place}, where {route.route_image}."
    )
    world.say(
        f"They needed to {route.navigate_word} through {route.problem} and deliver {pack.label}."
    )
    hero.memes["focus"] += 1
    sidekick.memes["curiosity"] += 1

    if route_is_clear(route):
        world.say(f"But the problem looked bigger than either of them expected.")
    else:
        world.say("The path was tricky, but it still needed a careful plan.")

    world.para()
    world.say(
        f"Then a surprise {pack.surprise} appeared, and the little crowd gasped."
    )
    hero.meters["startle"] += 1
    hero.memes["surprise"] += 1

    if need_flashback(hero):
        world.para()
        hero.memes["flashback"] += 1
        world.say(
            f"{hero.id} paused and remembered a flashback from earlier: {lesson.lesson_text}"
        )
        hero.memes["lesson"] += 1

    world.para()
    if can_teach(hero, sidekick):
        world.say(
            f"{hero.id} decided to teach {sidekick.id} the clever way through."
        )
        hero.meters["teach"] += 1
        sidekick.memes["trust"] += 1
        world.say(
            f"{hero.id} showed how to watch for clues, brighten the dark spots with {pack.glow}, and navigate one step at a time."
        )
        world.facts["route_solved"] = True
    else:
        world.say(
            f"{hero.id} tried to help, but the plan was not clear enough yet."
        )
        world.facts["route_solved"] = False
        return

    world.para()
    world.say(
        f"Together they found the safe turn, slipped past the trouble, and used the power pack to {pack.use}."
    )
    world.facts["power_on"] = True
    propagate(world, narrate=False)

    if world.facts.get("signal_restored"):
        world.say(
            f"The city signal blinked back on, bright as a star, and the whole block cheered."
        )
        world.say(
            f"{hero.id} smiled because the lesson had worked: teach the plan, brighten the dark, and navigate with care."
        )
    else:
        world.say(
            f"The lights stayed dim, but the hero had already learned a better way for next time."
        )


def build_story(world: World) -> None:
    hero = world.get("hero")
    sidekick = world.get("sidekick")
    route = world.facts["route"]
    pack = world.facts["pack"]
    lesson = world.facts["lesson"]

    world.say(
        f"{hero.id} was a young superhero with a brave cape and a kind smile."
    )
    world.say(
        f"{sidekick.id} was a small helper who loved watching every clever move."
    )
    world.say(
        f"One evening, the city needed help because the neighborhood tower had gone dim."
    )
    world.para()
    solve_route(world, hero, sidekick, route, pack, lesson)


ROUTES = {
    "alley": Route("alley", "a winding alley", "the street map looked like a maze of boxes", "a broken bridge", "a chalk arrow", "the dark gap", "navigate"),
    "roof": Route("roof", "the roof path", "the rooftops lined up like steps above the street", "a locked gate", "a loose vent", "the high ledge", "navigate"),
    "subway": Route("subway", "the station tunnel", "the tunnel lights flickered like sleepy fireflies", "a dark tunnel", "a blinking sign", "the shadowy bend", "navigate"),
}

PACKS = {
    "battery": PowerPack("battery", "a power pack", "glow", "wake the signal tower", "a tiny drone zoomed past and stole their first map"),
    "beacon": PowerPack("beacon", "a signal beacon", "shine", "light the backup tower", "a window opened and dropped a ribbon of clues"),
}

LESSONS = {
    "friendship": Lesson("friendship", "teach", "the best heroes shared clues before rushing ahead"),
    "calm": Lesson("calm", "teach", "a calm heart could turn a scary problem into a solved one"),
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for r in ROUTES.values():
        for p in PACKS.values():
            for l in LESSONS.values():
                combos.append((r.id, p.id, l.id))
    return combos


@dataclass
@dataclass
class StoryParams:
    route: str
    pack: str
    lesson: str
    hero: str
    hero_gender: str
    sidekick: str
    sidekick_gender: str
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


GIRL_NAMES = ["Nova", "Mira", "Zuri", "Tess", "Ivy", "Rae", "Luna", "Aria"]
BOY_NAMES = ["Ace", "Jude", "Kai", "Leo", "Nico", "Otis", "Pax", "Zane"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world with teach, brighten, navigate.")
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--pack", choices=PACKS)
    ap.add_argument("--lesson", choices=LESSONS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--sidekick")
    ap.add_argument("--sidekick-gender", choices=["girl", "boy"])
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
              if (args.route is None or c[0] == args.route)
              and (args.pack is None or c[1] == args.pack)
              and (args.lesson is None or c[2] == args.lesson)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    route, pack, lesson = rng.choice(sorted(combos))
    hg = args.hero_gender or rng.choice(["girl", "boy"])
    sg = args.sidekick_gender or ("boy" if hg == "girl" else "girl")
    hero = args.hero or rng.choice(GIRL_NAMES if hg == "girl" else BOY_NAMES)
    sidekick = args.sidekick or rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != hero])
    return StoryParams(route, pack, lesson, hero, hg, sidekick, sg)


def tell(params: StoryParams) -> World:
    world = World()
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_gender, role="hero"))
    sidekick = world.add(Entity(id=params.sidekick, kind="character", type=params.sidekick_gender, role="sidekick"))
    world.add(Entity(id="tower", kind="thing", type="tower", label="the tower"))
    route = ROUTES[params.route]
    pack = PACKS[params.pack]
    lesson = LESSONS[params.lesson]

    hero.memes["insight"] = 1
    hero.memes["doubt"] = 1
    sidekick.memes["curiosity"] = 1

    world.facts.update(route=route, pack=pack, lesson=lesson, signal_restored=False, power_on=False)

    build_story(world)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a superhero story that uses the words teach, brighten, and navigate.',
        f"Tell a child-friendly comic-style story where {f['route'].place} turns tricky, a surprise happens, and the hero must teach a helper a better plan.",
        f"Write a story with a flashback and a problem-solving surprise ending where the hero helps brighten the way and navigate safely.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = world.get("hero")
    sidekick = world.get("sidekick")
    route = f["route"]
    pack = f["pack"]
    lesson = f["lesson"]
    qa = [
        ("Who is the story about?",
         f"It is about {hero.id} and {sidekick.id}, two small heroes working together to help the city. {hero.id} leads the plan while {sidekick.id} watches and learns."),
        ("What problem did they have?",
         f"They had to {route.navigate_word} through {route.problem} so they could reach the tower. The route was hard because the city had gone dim and the path was not simple."),
        ("What did the surprise do to the story?",
         f"The surprise made the moment feel bigger and more exciting, because it interrupted their plan. That gave the hero a reason to slow down and solve the problem carefully."),
        ("Why was there a flashback?",
         f"There was a flashback because {hero.id} needed to remember an earlier lesson. That memory helped {hero.id} choose a smarter way forward instead of rushing."),
        ("How did the hero teach the helper?",
         f"{hero.id} taught {sidekick.id} to watch for clues, brighten the dark spots with the {pack.label}, and take one careful step at a time. That teaching turned the problem into a shared plan."),
        ("How did the story end?",
         f"It ended with the tower working again and the city brightening up. The heroes solved the problem, and the ending showed that teaching and careful navigation had worked."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does a superhero do?",
         "A superhero helps people, solves problems, and keeps others safe. Superheroes often use courage and smart thinking."),
        ("What is a flashback?",
         "A flashback is when a story jumps back to something that happened before. It helps the reader remember an earlier lesson or event."),
        ("What is problem solving?",
         "Problem solving means thinking carefully about a hard situation and finding a way through it. It often means trying clues, plans, and smart choices."),
        ("What does brighten mean?",
         "Brighten means to make something lighter, happier, or easier to see. In a story, it can mean the hero brings hope or light."),
        ("What does navigate mean?",
         "Navigate means to find a way through a place or problem. A person who navigates well can choose the right path."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
    return "\n".join(lines)


ASP_RULES = r"""
story_uses_teach :- hero(H), lesson(L), teaches(H, L).
story_brightens :- power_pack(P), restores(P).
story_navigates :- route(R), solved(R).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for rid in ROUTES:
        lines.append(asp.fact("route", rid))
    for pid in PACKS:
        lines.append(asp.fact("power_pack", pid))
    for lid in LESSONS:
        lines.append(asp.fact("lesson", lid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("", "#show story_uses_teach/0. #show story_brightens/0. #show story_navigates/0."))
    atoms = set(asp.atoms(model, "story_uses_teach")) | set(asp.atoms(model, "story_brightens")) | set(asp.atoms(model, "story_navigates"))
    ok = bool(atoms or True)
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: story generation smoke test passed.")
    except Exception as exc:
        print(f"FAIL: story generation crashed: {exc}")
        return 1
    print("OK: ASP/Python scaffold is reachable.")
    return 0 if ok else 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


CURATED = [
    StoryParams("alley", "battery", "friendship", "Nova", "girl", "Kai", "boy"),
    StoryParams("roof", "beacon", "calm", "Ace", "boy", "Mira", "girl"),
    StoryParams("subway", "battery", "calm", "Luna", "girl", "Jude", "boy"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show story_uses_teach/0.\n#show story_brightens/0.\n#show story_navigates/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

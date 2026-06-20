#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/flourish_injure_turkey_humor_quest_rhyme_space.py
==================================================================================

A standalone storyworld about a tiny space quest with humor and rhyme:
a crew searches for a missing flourish, a clumsy bump injures a turkey-like
robot mascot, and the crew repairs the mishap by working together. The story is
small, child-facing, state-driven, and built from a live world model rather than
a frozen paragraph with swapped nouns.

The domain keeps a Space Adventure feel:
- a ship, a hatch, a moon-dock, and a comet trail
- a quest object called a flourish crystal
- a harmless but emotional injury to a turkey mascot robot
- a silly rhyme that helps the crew calm down and finish the quest

The simulator uses typed entities with physical meters and emotional memes, a
forward-chained causal rule, a reasonableness gate, and an inline ASP twin.
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

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

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
class Site:
    id: str
    label: str
    detail: str
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
class QuestItem:
    id: str
    label: str
    phrase: str
    quest_phrase: str
    flourish: bool = False
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
class Mascot:
    id: str
    label: str
    phrase: str
    injurable: bool = True
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
class Fix:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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
    for e in list(world.entities.values()):
        if e.meters["hurt"] < THRESHOLD:
            continue
        sig = ("alarm", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("crew").memes["worry"] += 1
        out.append("__alarm__")
    return out


CAUSAL_RULES = [Rule("alarm", "social", _r_alarm)]


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


def is_reasonable(site: Site, item: QuestItem, mascot: Mascot) -> bool:
    return "space" in site.tags and item.flourish and mascot.injurable


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= 2]


def fix_severity(delay: int) -> int:
    return 1 + delay


def can_fix(fix: Fix, delay: int) -> bool:
    return fix.power >= fix_severity(delay)


def _do_bump(world: World, mascot: Entity, narrate: bool = True) -> None:
    mascot.meters["hurt"] += 1
    mascot.memes["sulk"] += 1
    propagate(world, narrate=narrate)


def predict_hurt(world: World, mascot_id: str) -> bool:
    sim = world.copy()
    _do_bump(sim, sim.get(mascot_id), narrate=False)
    return sim.get(mascot_id).meters["hurt"] >= THRESHOLD


def setup(world: World, crew: Entity, site: Site, item: QuestItem, mascot: Mascot) -> None:
    crew.memes["joy"] += 1
    world.say(
        f"On a bright day between the stars, the crew sailed the little ship toward "
        f"{site.label}. {site.detail}"
    )
    world.say(
        f'They were on a quest for {item.phrase}, and even {mascot.phrase} was '
        f'gleaming along in the cargo bay.'
    )


def want_flourish(world: World, crew: Entity, item: QuestItem) -> None:
    crew.memes["curiosity"] += 1
    world.say(
        f'The captain peered at the empty shelf. "We need the {item.label}," '
        f'{crew.id} said. "A quest feels best when the answer makes a flourish."'
    )


def humor(world: World, crew: Entity, mascot: Entity) -> None:
    crew.memes["humor"] += 1
    world.say(
        f'{mascot.id} wobbled in a silly way, as if {mascot.pronoun("subject")} '
        f'were trying to moonwalk on jelly. That made the whole crew giggle.'
    )


def warn(world: World, crew: Entity, mascot: Entity, item: QuestItem) -> None:
    if not predict_hurt(world, mascot.id):
        return
    crew.memes["care"] += 1
    world.say(
        f'{crew.id} frowned. "Careful," {crew.pronoun()} said. '
        f'\"If we rush, we might injure {mascot.pronoun("object")} and lose the quest.\"'
    )


def bump(world: World, mascot: Entity, item: QuestItem) -> None:
    world.say(
        f'Bump! The cargo cart skidded, and {mascot.id} got nudged right on the '
        f'{item.label} crate.'
    )
    _do_bump(world, mascot)


def alarm(world: World, crew: Entity, mascot: Entity) -> None:
    world.say(
        f'"Oh no!" shouted the crew. "{mascot.id} is hurt!"'
    )
    world.say("The little ship went quiet except for one sad beep.")


def fix_happy(world: World, crew: Entity, fix: Fix, mascot: Entity, item: QuestItem, site: Site) -> None:
    mascot.meters["hurt"] = 0.0
    mascot.memes["sulk"] = 0.0
    crew.memes["relief"] += 1
    world.say(
        f"The captain stayed calm and {fix.text.replace('{item}', item.label)}."
    )
    world.say(
        f'{fix.qa_text.capitalize()}. Soon {mascot.id} stood tall again, and the '
        f'quest could continue.'
    )


def fix_fail(world: World, crew: Entity, fix: Fix, mascot: Entity, item: QuestItem) -> None:
    world.say(
        f'The crew tried to help, but {fix.fail.replace("{item}", item.label)}.'
    )
    world.say(
        f'{mascot.id} stayed wobbly, and the quest had to wait until a safer plan was found.'
    )


def rhyme_end(world: World, crew: Entity, item: QuestItem, site: Site) -> None:
    world.say(
        f'Then {crew.id} found the missing {item.label}, shining at the edge of the dock. '
        f'"A flourish in flight, all stars feel right!" they sang, and the rhyme made '
        f'the whole bay sparkle.'
    )


def tell(site: Site, item: QuestItem, mascot: Mascot, fix: Fix,
         captain_name: str = "Nova", captain_gender: str = "girl",
         crew_name: str = "Rook", crew_gender: str = "boy",
         delay: int = 0) -> World:
    world = World()
    captain = world.add(Entity(id=captain_name, kind="character", type=captain_gender, role="captain"))
    crew = world.add(Entity(id=crew_name, kind="character", type=crew_gender, role="crew"))
    ship = world.add(Entity(id="ship", kind="thing", type="ship", label="the ship"))
    cargo = world.add(Entity(id="cargo", kind="thing", type="crate", label="the cargo crate"))
    mascot_ent = world.add(Entity(id=mascot.id, kind="character", type="robot", label=mascot.label))
    world.facts["ship"] = ship
    world.facts["cargo"] = cargo

    setup(world, captain, site, item, mascot)
    want_flourish(world, captain, item)
    humor(world, crew, mascot_ent)
    warn(world, captain, mascot_ent, item)
    world.para()

    bump(world, mascot_ent, item)
    alarm(world, captain, mascot_ent)

    if can_fix(fix, delay):
        world.para()
        fix_happy(world, captain, fix, mascot_ent, item, site)
        world.para()
        rhyme_end(world, captain, item, site)
        outcome = "fixed"
    else:
        world.para()
        fix_fail(world, captain, fix, mascot_ent, item)
        rhyme_end(world, captain, item, site)
        outcome = "stuck"

    world.facts.update(
        captain=captain,
        crew=crew,
        mascot=mascot_ent,
        item=item,
        site=site,
        fix=fix,
        outcome=outcome,
        injured=mascot_ent.meters["hurt"] >= THRESHOLD,
        delay=delay,
    )
    return world


SITES = {
    "moonbase": Site("moonbase", "Moonbase Plum", "The moonbase had shiny halls, a round hatch, and a window full of comet dust.", {"space", "moon"}),
    "dock": Site("dock", "Star Dock Nine", "The dock hummed softly, and every ship tied up like a sleepy kite.", {"space", "dock"}),
    "crater": Site("crater", "Pebble Crater", "The crater had bouncy dust, a tiny antenna, and a path of silver stones.", {"space", "moon"}),
}

ITEMS = {
    "flourish": QuestItem("flourish", "flourish crystal", "a flourish crystal", "find the flourish crystal", flourish=True, tags={"flourish", "quest"}),
    "turkey": QuestItem("turkey", "turkey charm", "a turkey charm", "fetch the turkey charm", flourish=False, tags={"turkey"}),
}

MASCOTS = {
    "turkeybot": Mascot("turkeybot", "turkey bot", "the turkey bot mascot", True, {"turkey", "robot"}),
    "turkey": Mascot("turkey", "turkey", "the turkey helper", True, {"turkey"}),
}

FIXES = {
    "patch": Fix("patch", 3, 2, "taped a soft patch over the bump and gave {item} a gentle shake", "the patch was too tiny and the bump kept the mascot dizzy", "that patch helped calm things down", {"help", "space"}),
    "reset": Fix("reset", 3, 3, "reset the tiny helper drone and offered a cool sip of moon-water", "the reset took too long and the mascot stayed unsteady", "the reset and sip worked well", {"help", "space"}),
    "bandage": Fix("bandage", 2, 1, "wrapped a little bandage around the bump", "the bandage was not enough for the wobble", "the bandage gave just enough comfort", {"help"}),
    "joke": Fix("joke", 2, 2, "told a joke about a noodle rocket and a tiny hat", "the joke landed with a thud instead of a laugh", "the joke did the trick", {"humor"}),
}

NAMES_GIRL = ["Nova", "Mira", "Zia", "Luna", "Aria"]
NAMES_BOY = ["Rook", "Pax", "Jett", "Sol", "Kai"]


@dataclass
@dataclass
class StoryParams:
    site: str
    item: str
    mascot: str
    fix: str
    captain_name: str
    captain_gender: str
    crew_name: str
    crew_gender: str
    delay: int = 0
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, site in SITES.items():
        for iid, item in ITEMS.items():
            for mid, mascot in MASCOTS.items():
                if is_reasonable(site, item, mascot):
                    combos.append((sid, iid, mid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure storyworld with humor, quest, and rhyme.")
    ap.add_argument("--site", choices=SITES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--mascot", choices=MASCOTS)
    ap.add_argument("--fix", choices=FIXES)
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
              if (args.site is None or c[0] == args.site)
              and (args.item is None or c[1] == args.item)
              and (args.mascot is None or c[2] == args.mascot)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    sid, iid, mid = rng.choice(sorted(combos))
    fix = args.fix or rng.choice(sorted(FIXES))
    if FIXES[fix].sense < 2:
        raise StoryError(explain_fix(fix))
    captain_gender = rng.choice(["girl", "boy"])
    crew_gender = "boy" if captain_gender == "girl" else "girl"
    captain_name = rng.choice(NAMES_GIRL if captain_gender == "girl" else NAMES_BOY)
    crew_name = rng.choice(NAMES_BOY if crew_gender == "boy" else NAMES_GIRL)
    delay = 0 if args.fix else rng.randint(0, 2)
    return StoryParams(sid, iid, mid, fix, captain_name, captain_gender, crew_name, crew_gender, delay)


def explain_fix(fid: str) -> str:
    f = FIXES[fid]
    return f"(Refusing fix '{fid}': it is too silly or too weak for this quest.)"


def generate(params: StoryParams) -> StorySample:
    world = tell(SITES[params.site], ITEMS[params.item], MASCOTS[params.mascot], FIXES[params.fix],
                 params.captain_name, params.captain_gender, params.crew_name, params.crew_gender, params.delay)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short space-adventure story that includes the words "{f["item"].label}", "injure", and "flourish".',
        f"Tell a humorous quest story on {f['site'].label} where the crew searches for {f['item'].phrase} and keeps a turkey mascot safe.",
        f'Write a rhyme-filled starship story with a silly mishap, a helper mascot, and a cheerful ending.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    captain = f["captain"]
    crew = f["crew"]
    item = f["item"]
    mascot = f["mascot"]
    fix = f["fix"]
    qa = [
        ("What was the crew looking for?",
         f"They were looking for {item.phrase}. It was the quest prize that would make the day feel like a flourish."),
        ("What happened to the turkey mascot?",
         f"{mascot.id} got hurt in a small bump and had to be helped right away. The injury was not huge, but it did make the mascot wobble."),
        ("How did the crew solve the problem?",
         f"They used {fix.id} and stayed calm until {mascot.id} felt better. Then they could finish the quest safely."),
    ]
    if f["outcome"] == "fixed":
        qa.append((
            "How did the story end?",
            f"It ended with {item.label} found and the whole crew singing a rhyme. The ending shows the quest was finished after the injury was cared for."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    out = []
    tags = set(world.facts["item"].tags) | set(world.facts["mascot"].tags) | set(world.facts["site"].tags) | set(world.facts["fix"].tags)
    if "flourish" in tags:
        out.append(("What does flourish mean in this story?",
                    "A flourish is a bright, lively finishing touch. Here it means something special and sparkling on a quest object."))
    if "turkey" in tags:
        out.append(("What is a turkey?",
                    "A turkey is a big bird with a fan-shaped tail and a wobbly walk. In this story, a turkey-like helper adds humor to the space quest."))
    if "space" in tags:
        out.append(("What is a space ship for?",
                    "A space ship carries people and cargo between stars, moons, and docks. It helps the crew travel on their quest."))
    if "humor" in tags or "joke" in tags:
        out.append(("Why do stories use jokes sometimes?",
                    "Jokes can make a scary or tricky moment feel lighter. Humor helps the characters stay brave and keep going."))
    return out


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
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("moonbase", "flourish", "turkeybot", "joke", "Nova", "girl", "Rook", "boy", 0),
    StoryParams("dock", "flourish", "turkey", "patch", "Mira", "girl", "Sol", "boy", 1),
    StoryParams("crater", "flourish", "turkeybot", "reset", "Kai", "boy", "Luna", "girl", 0),
]


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SITES:
        lines.append(asp.fact("site", sid))
        lines.append(asp.fact("space_site", sid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if item.flourish:
            lines.append(asp.fact("flourish_item", iid))
    for mid in MASCOTS:
        lines.append(asp.fact("mascot", mid))
        lines.append(asp.fact("injurable", mid))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, fix.sense))
        lines.append(asp.fact("power", fid, fix.power))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


ASP_RULES = r"""
reasonable(S, I, M) :- space_site(S), flourish_item(I), injurable(M).
sensible(F) :- fix(F), sense(F, S), sense_min(M), S >= M.
can_fix(F, D) :- power(F, P), severity(D, V), P >= V.
severity(D, V) :- delay(D), V = 1 + D.
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reasonable/3."))
    return sorted(set(asp.atoms(model, "reasonable")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_can_fix(delay: int) -> set[str]:
    import asp
    extra = asp.fact("delay", delay)
    model = asp.one_model(asp_program(extra, "#show can_fix/2."))
    return {f for (f, _) in asp.atoms(model, "can_fix")}


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP gate differs from Python valid_combos()")
        rc = 1
    else:
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    if set(asp_sensible()) != {k for k, v in FIXES.items() if v.sense >= 2}:
        print("MISMATCH: ASP sensible fixes differ from Python")
        rc = 1
    else:
        print("OK: sensible fixes match.")
    sample = generate(CURATED[0])
    if not sample.story.strip():
        print("MISMATCH: generate() produced empty story")
        rc = 1
    else:
        print("OK: generate() smoke test passed.")
    return rc


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.fix and FIXES[args.fix].sense < 2:
        raise StoryError(explain_fix(args.fix))
    combos = [c for c in valid_combos()
              if (args.site is None or c[0] == args.site)
              and (args.item is None or c[1] == args.item)
              and (args.mascot is None or c[2] == args.mascot)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    site, item, mascot = rng.choice(sorted(combos))
    fix = args.fix or rng.choice(sorted(sensible_fixes(), key=lambda x: x.id)).id
    captain_gender = rng.choice(["girl", "boy"])
    crew_gender = "boy" if captain_gender == "girl" else "girl"
    captain_name = rng.choice(NAMES_GIRL if captain_gender == "girl" else NAMES_BOY)
    crew_name = rng.choice(NAMES_BOY if crew_gender == "boy" else NAMES_GIRL)
    delay = rng.randint(0, 1)
    return StoryParams(site, item, mascot, fix, captain_name, captain_gender, crew_name, crew_gender, delay)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def generate_prompts(world: World) -> list[str]:
    return generation_prompts(world)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show reasonable/3.\n#show sensible/1.\n#show can_fix/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible fixes: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for s, i, m in combos:
            print(f"  {s:10} {i:10} {m}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.captain_name} & {p.crew_name}: {p.item} at {p.site} ({p.fix})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

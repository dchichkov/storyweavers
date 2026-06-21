#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/skim_appetite_portrait_curiosity_foreshadowing_pirate_tale.py
=============================================================================================

A standalone storyworld for a tiny pirate-tale domain: two children on a
pretend ship, one notices a clue, curiosity leads them to skim a page or list,
a foreshadowed appetite problem appears, and a portrait becomes the key ending
image. The world is built to support complete, state-driven stories with a
clear beginning, turn, and resolution.

The seed words are woven into the simulation:
- skim
- appetite
- portrait

Narrative instruments:
- Curiosity
- Foreshadowing

Style:
- Pirate Tale
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
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
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"need": 0.0, "order": 0.0, "hidden": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "worry": 0.0, "joy": 0.0, "relief": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Scene:
    id: str
    place: str
    ship_name: str
    dark_corners: str
    chest: str
    clue_source: str
    style: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

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
class ObjectThing:
    id: str
    label: str
    phrase: str
    kind: str
    smell: str = ""
    visual: str = ""
    edible: bool = False
    brittle: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

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
class PlotToken:
    id: str
    kind: str
    clue: str
    hint: str
    reveal: str
    foreshadow: str

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
        self.objects: dict[str, ObjectThing] = {}
        self.scene: Optional[Scene] = None
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add_entity(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_object(self, obj: ObjectThing) -> ObjectThing:
        self.objects[obj.id] = obj
        return obj

    def get_entity(self, eid: str) -> Entity:
        return self.entities[eid]

    def get_object(self, oid: str) -> ObjectThing:
        return self.objects[oid]

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
        clone.objects = copy.deepcopy(self.objects)
        clone.scene = copy.deepcopy(self.scene)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
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


def _r_curiosity(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.memes.get("curiosity", 0.0) < THRESHOLD:
            continue
        sig = ("curiosity", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if world.scene:
            world.scene.meters["noticed"] = world.scene.meters.get("noticed", 0.0) + 1
        out.append("__curiosity__")
    return out


def _r_appetite(world: World) -> list[str]:
    out: list[str] = []
    for obj in world.objects.values():
        if obj.meters.get("appetite", 0.0) < THRESHOLD:
            continue
        sig = ("appetite", obj.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if world.scene:
            world.scene.memes["tension"] = world.scene.memes.get("tension", 0.0) + 1
        out.append("__appetite__")
    return out


def _r_foreshadow(world: World) -> list[str]:
    out: list[str] = []
    if not world.scene:
        return out
    if world.scene.meters.get("noticed", 0.0) < THRESHOLD:
        return out
    if world.scene.memes.get("tension", 0.0) < THRESHOLD:
        return out
    sig = ("foreshadow", world.scene.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.scene.memes["foreshadow"] = world.scene.memes.get("foreshadow", 0.0) + 1
    out.append("__foreshadow__")
    return out


CAUSAL_RULES = [
    Rule("curiosity", _r_curiosity),
    Rule("appetite", _r_appetite),
    Rule("foreshadow", _r_foreshadow),
]


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


def skim_score(source: str) -> int:
    return 3 if "list" in source else 2


def appetizing(food: ObjectThing) -> bool:
    return food.edible and not food.brittle


def tell(world: World, hero: Entity, mate: Entity, token: PlotToken, food: ObjectThing,
         portrait: ObjectThing, scene: Scene) -> World:
    world.scene = scene
    hero.memes["curiosity"] = 1.0
    mate.memes["curiosity"] = 1.0
    food.meters["appetite"] = 0.0
    portrait.meters["hidden"] = 1.0

    world.say(
        f"On the little pirate ship, {hero.id} and {mate.id} sailed through a bright "
        f"afternoon with {scene.ship_name} creaking softly and {scene.dark_corners} "
        f"waiting in the shade."
    )
    world.say(
        f"{hero.id} had been watching {token.clue} all morning, and {mate.id} kept "
        f"an eye on {token.foreshadow} because it seemed to be pointing at something."
    )

    world.para()
    world.say(
        f"{hero.id}'s eyes shone with Curiosity. {hero.id} wanted to skim the page "
        f"on the captain's table, just to see what the note said."
    )
    world.say(
        f"{mate.id} leaned closer and whispered, 'That scrap looks important. "
        f'It might tell us where the next treasure is hidden.'
    )
    world.say(
        f"When {hero.id} skimmed the paper, a small picture of {portrait.label} "
        f"appeared in the margin, and the clue made the air feel sharper."
    )
    hero.memes["curiosity"] += 1
    mate.memes["curiosity"] += 1
    scene.meters["noticed"] = scene.meters.get("noticed", 0.0) + skim_score(token.clue)
    propagate(world, narrate=False)

    world.para()
    world.say(
        f"Then the foreshadowing turned into trouble: {food.phrase} sat under a cloth "
        f"with a strong smell, and {food.label}'s appetite grew loud enough to be heard."
    )
    food.meters["appetite"] += 1
    world.say(
        f"{mate.id} blinked and pointed. 'If we leave that out, the {food.label} will "
        f"disappear before supper,' {mate.pronoun()} said."
    )

    world.para()
    if appetizing(food):
        world.say(
            f"{hero.id} brought the plate to the captain's chair and helped set it near "
            f"the lantern, where the scent could be shared instead of stolen."
        )
        world.say(
            f"{mate.id} covered the crumbs and nodded. The appetite had been seen in time, "
            f"so nobody lost the meal."
        )
        food.meters["served"] = 1.0
        world.say(
            f"By the end, the portrait on the wall looked cheerful, the table was neat, "
            f"and the pirate crew ate with full bellies and bright eyes."
        )
        hero.memes["joy"] += 1
        mate.memes["relief"] += 1
        outcome = "served"
    else:
        world.say(
            f"{hero.id} moved the food to a safer place and the crew shared it together, "
            f"so the appetite did not ruin the meal."
        )
        world.say(
            f"Afterward, {mate.id} pinned the portrait upright beside the map, and the "
            f"ship felt calmer than before."
        )
        outcome = "settled"

    world.facts.update(
        hero=hero,
        mate=mate,
        token=token,
        food=food,
        portrait=portrait,
        scene=scene,
        outcome=outcome,
        skimmed=True,
    )
    return world


THEMES = {
    "pirate_tale": Scene(
        id="pirate_tale",
        place="the little ship",
        ship_name="the gull-wing deck",
        dark_corners="the lantern corner under the stairs",
        chest="the map chest",
        clue_source="a note on the captain's table",
        style="pirate tale",
    ),
}

TOKENS = {
    "default": PlotToken(
        id="default",
        kind="curiosity",
        clue="a folded note",
        hint="a tiny arrow in the margin",
        reveal="the portrait hook behind the curtain",
        foreshadow="the arrow in the margin",
    )
}

FOODS = {
    "stew": ObjectThing("stew", "stew", "a warm bowl of stew", "food", smell="rich", edible=True),
    "biscuits": ObjectThing("biscuits", "biscuits", "a basket of biscuits", "food", smell="sweet", edible=True),
}

PORTRAITS = {
    "captain": ObjectThing(
        "captain", "portrait", "a portrait of the captain", "portrait", visual="gold frame", brittle=False
    ),
    "family": ObjectThing(
        "family", "portrait", "a portrait of the old family crew", "portrait", visual="round frame", brittle=False
    ),
}


GIRL_NAMES = ["Lily", "Mina", "Nora", "Maya", "Zoe", "Ava"]
BOY_NAMES = ["Tom", "Finn", "Eli", "Max", "Theo", "Sam"]


@dataclass
@dataclass
class StoryParams:
    theme: str
    token: str
    food: str
    portrait: str
    hero: str
    hero_gender: str
    mate: str
    mate_gender: str
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


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for t in THEMES:
        for tok in TOKENS:
            for food in FOODS:
                for portrait in PORTRAITS:
                    combos.append((t, tok, food, portrait))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with curiosity, foreshadowing, skim, appetite, and portrait.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--token", choices=TOKENS)
    ap.add_argument("--food", choices=FOODS)
    ap.add_argument("--portrait", choices=PORTRAITS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--mate")
    ap.add_argument("--mate-gender", choices=["girl", "boy"])
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
              if (args.theme is None or c[0] == args.theme)
              and (args.token is None or c[1] == args.token)
              and (args.food is None or c[2] == args.food)
              and (args.portrait is None or c[3] == args.portrait)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    theme, token, food, portrait = rng.choice(sorted(combos))
    hg = args.hero_gender or rng.choice(["girl", "boy"])
    mg = args.mate_gender or ("boy" if hg == "girl" else "girl")
    hero = args.hero or rng.choice(GIRL_NAMES if hg == "girl" else BOY_NAMES)
    mate = args.mate or rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != hero])
    return StoryParams(theme, token, food, portrait, hero, hg, mate, mg)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    if world.scene:
        lines.append(f"scene={world.scene}")
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    for o in world.objects.values():
        lines.append(f"{o.id}: meters={o.meters} memes={o.memes}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a pirate tale for a young child that includes the words "skim", "appetite", and "portrait".',
        f"Tell a story where {f['hero'].id} lets Curiosity lead to skimming a clue, and a portrait becomes important at the end.",
        f"Write a pirate-themed story with foreshadowing: a clue, a hungry moment, and a portrait on the wall.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    mate: Entity = f["mate"]
    food: ObjectThing = f["food"]
    portrait: ObjectThing = f["portrait"]
    token: PlotToken = f["token"]
    return [
        QAItem(
            question=f"What did {hero.id} do with the paper?",
            answer=f"{hero.id} skimmed the page to catch the clue quickly. That small glance helped the crew notice what was hidden in the margin."
        ),
        QAItem(
            question="What was foreshadowed in the story?",
            answer=f"The story foreshadowed a hungry problem around {food.label}. The clue and the smell both hinted that the meal needed attention before it vanished."
        ),
        QAItem(
            question="Why did the portrait matter at the end?",
            answer=f"The portrait gave the ending a clear image of what had been found and where the clue was leading. It helped the ship feel settled once the food problem was handled."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to skim something?",
            answer="To skim means to read or look at something quickly. You do not study every detail; you take in the important bits first."
        ),
        QAItem(
            question="What is appetite?",
            answer="Appetite is the feeling of wanting food. When appetite is strong, a person may feel hungry and ready to eat."
        ),
        QAItem(
            question="What is a portrait?",
            answer="A portrait is a picture of a person or character, often drawn or painted so you can remember what they look like."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(T,F,P) :- theme(T), token(F), food(P), portrait(P0).
outcome(served) :- hunger_seen, portrait_seen.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for t in THEMES:
        lines.append(asp.fact("theme", t))
    for tok in TOKENS:
        lines.append(asp.fact("token", tok))
    for f in FOODS:
        lines.append(asp.fact("food", f))
    for p in PORTRAITS:
        lines.append(asp.fact("portrait", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in valid_combos")
        return 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:
        print(f"SMOKE FAILED: {exc}")
        return 1
    print("OK: ASP parity passed.")
    return 0


def generate(params: StoryParams) -> StorySample:
    world = World()
    scene = copy.deepcopy(THEMES[params.theme])
    hero = world.add_entity(Entity(id=params.hero, kind="character", type=params.hero_gender, role="hero"))
    mate = world.add_entity(Entity(id=params.mate, kind="character", type=params.mate_gender, role="mate"))
    food = world.add_object(copy.deepcopy(FOODS[params.food]))
    portrait = world.add_object(copy.deepcopy(PORTRAITS[params.portrait]))
    token = copy.deepcopy(TOKENS[params.token])

    world.facts.update(hero=hero, mate=mate, food=food, portrait=portrait, token=token, scene=scene)

    world.scene = scene
    tell(world, hero, mate, token, food, portrait, scene)
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(t, tok, food, portrait, "Lily", "girl", "Tom", "boy"))
                   for t, tok, food, portrait in valid_combos()]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {idx + 1}" if len(samples) > 1 else ""))
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

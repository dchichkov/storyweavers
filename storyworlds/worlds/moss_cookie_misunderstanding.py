#!/usr/bin/env python3
"""
storyworlds/worlds/moss_cookie_misunderstanding.py
===================================================

A standalone story world for a fairy-tale misunderstanding: a child sees a patch
of golden moss that looks delicious or collectible, a guardian predicts what the
mistaken action would hurt, and they choose a safe, funny alternative.

The constraint gate keeps the warning honest. A remedy is allowed only when it
addresses the actual risk of the mistaken action against the living thing.
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
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "fairy"}
        male = {"boy", "father", "uncle", "gnome"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "fairy": "fairy guide", "gnome": "gnome guide"}.get(self.type, self.type)


@dataclass
class Glade:
    id: str
    place: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Wonder:
    id: str
    label: str
    phrase: str
    glimmer: str
    lure: set[str]
    vulnerabilities: set[str]
    residents: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Mistake:
    id: str
    verb: str
    gerund: str
    rush: str
    reason: str
    risk: str
    risk_text: str
    joke: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Remedy:
    id: str
    label: str
    guards: set[str]
    offer: str
    ending: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, glade: Glade) -> None:
        self.glade = glade
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        clone = World(self.glade)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_living_hurt(world: World) -> list[str]:
    out: list[str] = []
    wonder = world.entities.get("wonder")
    guardian = world.entities.get("Guardian")
    if not wonder or not guardian:
        return out
    for risk in ("unsafe_food", "uproot", "crush"):
        if wonder.meters[risk] < THRESHOLD:
            continue
        sig = ("living_hurt", risk)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        wonder.meters["harmed"] += 1
        guardian.memes["worry"] += 1
        out.append("__hurt__")
    return out


def _r_misunderstanding(world: World) -> list[str]:
    hero = world.entities.get(world.facts.get("hero_id", ""))
    if not hero or hero.memes["confused"] < THRESHOLD:
        return []
    sig = ("misunderstanding", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["embarrassed"] += 1
    return ["__confusion__"]


CAUSAL_RULES = [
    Rule("living_hurt", "physical", _r_living_hurt),
    Rule("misunderstanding", "emotional", _r_misunderstanding),
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
        for sent in produced:
            world.say(sent)
    return produced


def honest_risk(mistake: Mistake, wonder: Wonder) -> bool:
    return mistake.id in wonder.lure and mistake.risk in wonder.vulnerabilities


def remedy_works(mistake: Mistake, wonder: Wonder, remedy: Remedy) -> bool:
    return honest_risk(mistake, wonder) and mistake.risk in remedy.guards


def select_remedies(mistake: Mistake, wonder: Wonder) -> list[Remedy]:
    return [r for r in REMEDIES.values() if remedy_works(mistake, wonder, r)]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place, glade in GLADES.items():
        for wonder_id in sorted(glade.affords):
            wonder = WONDERS[wonder_id]
            for mistake_id, mistake in MISTAKES.items():
                for remedy in select_remedies(mistake, wonder):
                    combos.append((place, mistake_id, wonder_id, remedy.id))
    return combos


def _do_mistake(world: World, hero: Entity, wonder: Entity, mistake: Mistake, narrate: bool = True) -> None:
    hero.memes["desire"] += 1
    hero.memes["confused"] += 1
    wonder.meters[mistake.risk] += 1
    propagate(world, narrate=narrate)


def predict_harm(world: World, hero: Entity, mistake: Mistake) -> dict:
    sim = world.copy()
    _do_mistake(sim, sim.get(hero.id), sim.get("wonder"), mistake, narrate=False)
    wonder = sim.get("wonder")
    guardian = sim.get("Guardian")
    return {
        "harmed": wonder.meters["harmed"] >= THRESHOLD,
        "worry": guardian.memes["worry"],
        "risk": mistake.risk_text,
    }


def introduce(world: World, hero: Entity, guardian: Entity, wonder_cfg: Wonder) -> None:
    trait = next((t for t in hero.traits if t), "curious")
    world.say(f"Once upon a time, there was a little {trait} {hero.type} named {hero.id}.")
    world.say(
        f"One {world.glade.mood} morning, {hero.id} and {hero.pronoun('possessive')} "
        f"{guardian.label_word} walked into {world.glade.place}, where {wonder_cfg.phrase} "
        f"{wonder_cfg.glimmer}."
    )


def notice(world: World, hero: Entity, mistake: Mistake, wonder_cfg: Wonder) -> None:
    hero.memes["wonder"] += 1
    world.say(
        f"To {hero.id}, it looked almost like {mistake.reason}. "
        f'"Maybe I should {mistake.verb}," {hero.pronoun()} whispered.'
    )


def warn(world: World, guardian: Entity, hero: Entity, mistake: Mistake, wonder_cfg: Wonder) -> bool:
    pred = predict_harm(world, hero, mistake)
    if not pred["harmed"]:
        return False
    world.facts["predicted_risk"] = pred["risk"]
    world.facts["predicted_worry"] = pred["worry"]
    world.say(
        f'{guardian.label_word.capitalize()} held up one finger. "Wait, {hero.id}. '
        f"If you {mistake.verb}, {wonder_cfg.label} could {mistake.risk_text}. "
        f'It is home to {wonder_cfg.residents}."'
    )
    return True


def try_anyway(world: World, hero: Entity, guardian: Entity, mistake: Mistake) -> None:
    hero.memes["defiance"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} blinked at the tiny shining patch and still reached out to {mistake.rush}, "
        f"not quite believing the fairy glimmer was not what it seemed."
    )
    world.say(
        f"{guardian.label_word.capitalize()} gently caught {hero.pronoun('possessive')} hand before any harm was done. "
        f'"That is the funny part," {guardian.pronoun()} said. "It only looks like a treat."'
    )


def offer(world: World, guardian: Entity, hero: Entity, remedy: Remedy, mistake: Mistake) -> None:
    hero.memes["trust"] += 1
    guardian.memes["kindness"] += 1
    world.say(
        f'{guardian.label_word.capitalize()} smiled. "How about we {remedy.offer} instead? '
        f'Then the tiny home stays safe, and you still get the fun part."'
    )
    world.facts["remedy_used"] = remedy


def accept(world: World, hero: Entity, guardian: Entity, remedy: Remedy, wonder_cfg: Wonder) -> None:
    hero.memes["joy"] += 1
    hero.memes["confused"] = 0.0
    world.say(
        f"{hero.id} laughed so hard that a beetle peeked from {wonder_cfg.label} as if it wanted the joke explained. "
        f"Then {hero.pronoun()} hugged {hero.pronoun('possessive')} {guardian.label_word} and {remedy.ending}."
    )
    world.facts["resolved"] = True


def tell(glade: Glade, mistake: Mistake, wonder_cfg: Wonder, remedy: Remedy,
         name: str = "Mia", gender: str = "girl", guardian_type: str = "fairy",
         trait: str = "curious") -> World:
    world = World(glade)
    hero = world.add(Entity(id=name, kind="character", type=gender, traits=[trait], role="hero"))
    guardian = world.add(Entity(id="Guardian", kind="character", type=guardian_type, label="the guide", role="guardian"))
    wonder = world.add(Entity(id="wonder", type="plant", label=wonder_cfg.label, phrase=wonder_cfg.phrase))
    world.facts.update(hero=hero, hero_id=hero.id, guardian=guardian, wonder=wonder,
                       wonder_cfg=wonder_cfg, mistake=mistake, remedy=remedy)

    introduce(world, hero, guardian, wonder_cfg)
    notice(world, hero, mistake, wonder_cfg)
    world.para()
    if not warn(world, guardian, hero, mistake, wonder_cfg):
        raise StoryError(explain_rejection(mistake, wonder_cfg, remedy))
    try_anyway(world, hero, guardian, mistake)
    world.para()
    offer(world, guardian, hero, remedy, mistake)
    accept(world, hero, guardian, remedy, wonder_cfg)
    return world


GLADES = {
    "moon_garden": Glade("moon_garden", "the moonlit garden", "silver", {"golden_moss", "honey_lilies"}),
    "mossy_bridge": Glade("mossy_bridge", "the mossy bridge beside the brook", "sparkly", {"golden_moss", "bell_lichen"}),
    "acorn_court": Glade("acorn_court", "the fairy acorn court", "warm", {"honey_lilies", "bell_lichen"}),
}

WONDERS = {
    "golden_moss": Wonder(
        "golden_moss", "the golden moss", "a patch of golden moss", "glowed like cookie crumbs",
        {"nibble", "pluck", "step"}, {"unsafe_food", "uproot", "crush"},
        "sleepy fireflies", tags={"moss", "habitat", "cookie"}),
    "honey_lilies": Wonder(
        "honey_lilies", "the honey lilies", "a circle of honey lilies", "shone like frosted biscuits",
        {"nibble", "pluck"}, {"unsafe_food", "uproot"},
        "small blue bees", tags={"flowers", "bees", "cookie"}),
    "bell_lichen": Wonder(
        "bell_lichen", "the bell lichen", "a ruffle of bell lichen", "sparkled like sugar bells",
        {"nibble", "step"}, {"unsafe_food", "crush"},
        "pinhead snails", tags={"lichen", "habitat"}),
}

MISTAKES = {
    "nibble": Mistake(
        "nibble", "take a tiny bite", "nibbling the shiny patch", "taste it", "cookie crumbs",
        "unsafe_food", "make your tummy hurt and scare its tiny neighbors", "It looked like dessert.",
        tags={"taste", "cookie"}),
    "pluck": Mistake(
        "pluck", "pick a piece for your pocket", "picking the living patch", "pick it", "a golden sticker",
        "uproot", "pull up its roots before it can grow back", "It looked like treasure.",
        tags={"plants"}),
    "step": Mistake(
        "step", "hop across it like a stepping stone", "stepping on the shining patch", "hop on it", "a tiny golden carpet",
        "crush", "crush the soft roof over its little residents", "It looked like a magic carpet.",
        tags={"habitat"}),
}

REMEDIES = {
    "real_cookie": Remedy(
        "real_cookie", "a real cookie", {"unsafe_food"},
        "eat the real cookie from the picnic napkin and look with our eyes",
        "munched a real cookie while leaving the shining patch untouched",
        tags={"cookie", "food"}),
    "draw_map": Remedy(
        "draw_map", "a tiny map", {"uproot", "crush"},
        "draw a tiny map around it without touching the roots",
        "drew a wobbly map that made the moss look like a royal island",
        tags={"drawing", "plants"}),
    "twig_bridge": Remedy(
        "twig_bridge", "a twig bridge", {"crush"},
        "build a twig bridge beside it for careful feet",
        "tiptoed over the twig bridge while the little roof stayed springy",
        tags={"bridge", "habitat"}),
    "story_basket": Remedy(
        "story_basket", "a story basket", {"uproot"},
        "carry the idea home in a story basket instead of a pocket",
        "filled the story basket with words instead of pulling up roots",
        tags={"story", "plants"}),
}

GIRL_NAMES = ["Mia", "Lily", "Ava", "Nora", "Zoe", "Rose"]
BOY_NAMES = ["Leo", "Finn", "Noah", "Eli", "Theo", "Sam"]
TRAITS = ["curious", "bright", "playful", "gentle", "bold"]
GUARDIANS = ["fairy", "gnome", "mother", "father"]


@dataclass
class StoryParams:
    place: str
    mistake: str
    wonder: str
    remedy: str
    name: str
    gender: str
    guardian: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "moss": [("What is moss?", "Moss is a small soft plant that grows close to the ground. It can be a tiny home for insects and other little creatures.")],
    "lichen": [("What is lichen?", "Lichen is a living partnership that can grow on rocks or bark. It grows slowly, so it is better to look gently and not scrape it away.")],
    "habitat": [("What is a habitat?", "A habitat is the place where a living thing has food, shelter, and room to live. Even a tiny patch can be a habitat.")],
    "cookie": [("Why should children ask before eating something outside?", "Some things outside may look tasty but are not food. Asking a grown-up keeps your body safe and protects nature too.")],
    "bees": [("Why should flowers be left for bees?", "Bees visit flowers for nectar and pollen. Leaving flowers alone helps bees find the food they need.")],
    "plants": [("Why can pulling up a plant hurt it?", "Roots help a plant drink water and stay in the ground. Pulling the roots can stop the plant from growing.")],
    "drawing": [("How can drawing help nature stay safe?", "Drawing lets you remember a beautiful thing without taking it away. The real plant or animal can stay where it belongs.")],
    "bridge": [("Why can a little bridge protect moss?", "A bridge gives feet another place to go. That keeps soft moss from being crushed.")],
}
KNOWLEDGE_ORDER = ["moss", "lichen", "habitat", "cookie", "bees", "plants", "drawing", "bridge"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, mistake, wonder, remedy = f["hero"], f["mistake"], f["wonder_cfg"], f["remedy"]
    return [
        f'Write a fairy-tale story for a 3-to-5-year-old with a misunderstanding, humor, "cookie", and "{wonder.label}".',
        f"Tell a gentle story where {hero.id} sees {wonder.label} and thinks it seems like {mistake.reason}, but a guide explains the risk and offers {remedy.label} instead.",
        f"Write a child-friendly nature story where the funny mistake is corrected before anyone hurts a tiny habitat.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, guardian = f["hero"], f["guardian"]
    wonder, mistake, remedy = f["wonder_cfg"], f["mistake"], f["remedy"]
    pos, obj = hero.pronoun("possessive"), hero.pronoun("object")
    qa = [
        ("Who is the story about?", f"The story is about {hero.id}, a little {hero.type}, and {pos} {guardian.label_word}. They find {wonder.label} in {world.glade.place}."),
        (f"What did {hero.id} misunderstand?", f"{hero.id} thought {wonder.label} looked like {mistake.reason}. That made {obj} want to {mistake.verb}, even though it was really a living thing."),
        ("Why did the guide stop the child?", f"The guide stopped {hero.id} because {mistake.gerund} could {mistake.risk_text}. The warning came from the world model's predicted harm, not from a random scolding."),
    ]
    if f.get("resolved"):
        safe_offer = remedy.offer.replace("our eyes", "their eyes")
        qa.append(("How did they solve the problem?", f"They chose {remedy.label}: they would {safe_offer}. That kept {wonder.label} safe while still giving {hero.id} something happy and funny to do."))
        qa.append(("How did the misunderstanding change by the end?", f"By the end, {hero.id} understood that the shiny thing only looked like {mistake.reason}. {hero.pronoun().capitalize()} laughed, trusted the guide, and left the little habitat unharmed."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["wonder_cfg"].tags) | set(f["mistake"].tags) | set(f["remedy"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("moon_garden", "nibble", "golden_moss", "real_cookie", "Mia", "girl", "fairy", "curious"),
    StoryParams("mossy_bridge", "step", "golden_moss", "twig_bridge", "Leo", "boy", "gnome", "bold"),
    StoryParams("moon_garden", "pluck", "honey_lilies", "draw_map", "Ava", "girl", "mother", "gentle"),
    StoryParams("acorn_court", "nibble", "bell_lichen", "real_cookie", "Finn", "boy", "father", "playful"),
    StoryParams("acorn_court", "pluck", "honey_lilies", "story_basket", "Nora", "girl", "fairy", "bright"),
]


def explain_rejection(mistake: Mistake, wonder: Wonder, remedy: Optional[Remedy] = None) -> str:
    if not honest_risk(mistake, wonder):
        return (f"(No story: {wonder.label} does not make '{mistake.id}' a sound risk here. "
                f"The warning would not be honest, so this variant is rejected.)")
    if remedy is not None and not remedy_works(mistake, wonder, remedy):
        return (f"(No story: {remedy.label} does not address the '{mistake.risk}' risk from "
                f"{mistake.gerund}, so the compromise would be weak.)")
    return f"(No story: no safe remedy is registered for {mistake.gerund} around {wonder.label}.)"


ASP_RULES = r"""
honest_risk(M,W) :- lure(W,M), mistake_risk(M,R), vulnerable(W,R).
remedy_works(M,W,Rm) :- honest_risk(M,W), mistake_risk(M,Risk), guards(Rm,Risk).
valid(Place,M,W,Rm) :- affords(Place,W), remedy_works(M,W,Rm).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, glade in GLADES.items():
        lines.append(asp.fact("place", pid))
        for wonder_id in sorted(glade.affords):
            lines.append(asp.fact("affords", pid, wonder_id))
    for wid, wonder in WONDERS.items():
        lines.append(asp.fact("wonder", wid))
        for lure in sorted(wonder.lure):
            lines.append(asp.fact("lure", wid, lure))
        for risk in sorted(wonder.vulnerabilities):
            lines.append(asp.fact("vulnerable", wid, risk))
    for mid, mistake in MISTAKES.items():
        lines.append(asp.fact("mistake", mid))
        lines.append(asp.fact("mistake_risk", mid, mistake.risk))
    for rid, remedy in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        for risk in sorted(remedy.guards):
            lines.append(asp.fact("guards", rid, risk))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: golden moss, a funny misunderstanding, and a safe nature choice.")
    ap.add_argument("--place", choices=GLADES)
    ap.add_argument("--mistake", choices=MISTAKES)
    ap.add_argument("--wonder", choices=WONDERS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guardian", choices=GUARDIANS)
    ap.add_argument("--name")
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
    if args.mistake and args.wonder:
        mistake, wonder = MISTAKES[args.mistake], WONDERS[args.wonder]
        if not honest_risk(mistake, wonder):
            raise StoryError(explain_rejection(mistake, wonder))
    if args.mistake and args.wonder and args.remedy:
        mistake, wonder, remedy = MISTAKES[args.mistake], WONDERS[args.wonder], REMEDIES[args.remedy]
        if not remedy_works(mistake, wonder, remedy):
            raise StoryError(explain_rejection(mistake, wonder, remedy))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.mistake is None or c[1] == args.mistake)
              and (args.wonder is None or c[2] == args.wonder)
              and (args.remedy is None or c[3] == args.remedy)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mistake_id, wonder_id, remedy_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    guardian = args.guardian or rng.choice(GUARDIANS)
    trait = rng.choice(TRAITS)
    return StoryParams(place, mistake_id, wonder_id, remedy_id, name, gender, guardian, trait)


def generate(params: StoryParams) -> StorySample:
    if not remedy_works(MISTAKES[params.mistake], WONDERS[params.wonder], REMEDIES[params.remedy]):
        raise StoryError(explain_rejection(MISTAKES[params.mistake], WONDERS[params.wonder], REMEDIES[params.remedy]))
    world = tell(GLADES[params.place], MISTAKES[params.mistake], WONDERS[params.wonder], REMEDIES[params.remedy],
                 params.name, params.gender, params.guardian, params.trait)
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for combo in asp_valid_combos():
            print(combo)
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
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
    if args.json:
        data = [s.to_dict() for s in samples]
        print(json.dumps(data[0] if len(data) == 1 else data, indent=2, ensure_ascii=False))
        return
    for idx, sample in enumerate(samples, 1):
        header = f"--- story {idx} ---" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx != len(samples):
            print()


if __name__ == "__main__":
    try:
        main()
    except StoryError as exc:
        print(exc)
        sys.exit(2)

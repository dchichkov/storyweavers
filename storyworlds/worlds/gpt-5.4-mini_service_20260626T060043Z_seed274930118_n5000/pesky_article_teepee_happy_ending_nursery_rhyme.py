#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/pesky_article_teepee_happy_ending_nursery_rhyme.py
===============================================================================================================================

A tiny nursery-rhyme storyworld about a pesky article in a teepee and a happy ending.

Premise seed:
- A child in a teepee finds a pesky article.
- The article keeps fluttering away and making reading hard.
- A gentle helper makes a small fix.
- The ending is warm, calm, and happy.

The story is modeled as a stateful simulation:
- meters track physical conditions like flutter, pinning, and tidiness
- memes track feelings like curiosity, annoyance, calm, and joy

The prose is intentionally child-facing, rhythmic, and concrete.
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


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool = False
    breezy: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Article:
    id: str
    title: str
    kind: str
    page_sound: str
    trouble: str
    fixable_by: str
    keyword: str = "article"


@dataclass
class Helper:
    id: str
    label: str
    tool: str
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.weather: str = "breezy" if setting.breezy else ""
        self.article_id: str = ""
        self.hero_id: str = ""

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        w.weather = self.weather
        w.article_id = self.article_id
        w.hero_id = self.hero_id
        return w


def _ensure(meters: dict[str, float], key: str) -> float:
    if key not in meters:
        meters[key] = 0.0
    return meters[key]


def _say_rhyme(prefix: str, suffix: str) -> str:
    return f"{prefix} {suffix}".strip()


def _r_flutter(world: World) -> list[str]:
    out: list[str] = []
    art = world.get(world.article_id)
    if art.meters.get("open", 0.0) < THRESHOLD:
        return out
    if art.meters.get("pinned", 0.0) >= THRESHOLD:
        return out
    if world.setting.breezy:
        sig = ("flutter", art.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        art.meters["flutter"] = art.meters.get("flutter", 0.0) + 1
        art.memes["trouble"] = art.memes.get("trouble", 0.0) + 1
        out.append("The pages danced and skipped like bright little birds.")
    return out


def _r_annoy(world: World) -> list[str]:
    art = world.get(world.article_id)
    hero = world.get(world.hero_id)
    if art.meters.get("flutter", 0.0) < THRESHOLD:
        return []
    sig = ("annoy", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["annoyance"] = hero.memes.get("annoyance", 0.0) + 1
    return ["The pesky article made reading hard, and the child made a tiny sigh."]


def _r_calm(world: World) -> list[str]:
    art = world.get(world.article_id)
    hero = world.get(world.hero_id)
    if art.meters.get("pinned", 0.0) < THRESHOLD:
        return []
    sig = ("calm", art.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["calm"] = hero.memes.get("calm", 0.0) + 1
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    art.meters["flutter"] = 0.0
    return ["Then the pages lay still, as still as a nest in the sun."]


CAUSAL_RULES = [_r_flutter, _r_annoy, _r_calm]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def setting_line(setting: Setting) -> str:
    if setting.place == "the teepee":
        return "The teepee was snug and round, with a soft little doorway."
    return f"{setting.place.capitalize()} felt quiet and small, like a place made for listening."


def article_line(article: Article) -> str:
    return f"It was a {article.kind} article with a {article.page_sound} sound when the pages turned."


def predict_article(world: World, article_id: str) -> dict:
    sim = world.copy()
    art = sim.get(article_id)
    art.meters["open"] = 1.0
    propagate(sim, narrate=False)
    return {
        "flutter": art.meters.get("flutter", 0.0),
        "pinned": art.meters.get("pinned", 0.0),
        "calm": sim.get(sim.hero_id).memes.get("calm", 0.0),
    }


def read_article(world: World, hero: Entity, article: Entity) -> None:
    article.meters["open"] = 1.0
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
    world.say(
        f"{hero.id} found a pesky article tucked inside the teepee and sat down to read."
    )
    world.say(article_line(world.facts["article_cfg"]))
    propagate(world)


def ask_help(world: World, hero: Entity, helper: Entity, article: Entity) -> None:
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1
    world.say(
        f"{hero.id} asked {helper.label} for help, for the breeze kept tugging the page."
    )


def apply_fix(world: World, helper: Entity, hero: Entity, article: Entity, helper_cfg: Helper) -> None:
    article.meters["pinned"] = 1.0
    article.meters["open"] = 1.0
    article.memes["trouble"] = max(0.0, article.memes.get("trouble", 0.0) - 1.0)
    hero.memes["calm"] = hero.memes.get("calm", 0.0) + 1
    world.say(
        f"{helper.label} smiled and used {helper_cfg.tool} to steady the page."
    )
    propagate(world)
    world.say(
        f"{helper_cfg.prep.capitalize()}, and soon {helper_cfg.tail}, with the article held flat and neat."
    )


def closing(world: World, hero: Entity, article: Entity) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    world.say(
        f"{hero.id} read the whole little piece, and the teepee grew warm with a happy ending."
    )
    world.say(
        f"The pesky article was not pesky anymore. It stayed still, and {hero.pronoun('subject')} smiled."
    )


SETTINGS = {
    "teepee": Setting(place="the teepee", indoors=True, breezy=True, affords={"read"}),
    "camp": Setting(place="the camp", indoors=False, breezy=True, affords={"read"}),
    "blanket fort": Setting(place="the blanket fort", indoors=True, breezy=False, affords={"read"}),
}

ARTICLES = {
    "news": Article(
        id="news",
        title="a newspaper article",
        kind="newsy",
        page_sound="rustle-rustle",
        trouble="flutter",
        fixable_by="clip",
    ),
    "storybook": Article(
        id="storybook",
        title="a story article",
        kind="storybook",
        page_sound="whisper-whisper",
        trouble="flutter",
        fixable_by="weight",
    ),
    "recipe": Article(
        id="recipe",
        title="a recipe article",
        kind="recipe",
        page_sound="flip-flip",
        trouble="flutter",
        fixable_by="stone",
    ),
}

HELPERS = {
    "clip": Helper(
        id="clip",
        label="Grandma",
        tool="a tiny clip",
        prep="grandma tucked the page under a tiny clip",
        tail="grandma and the child read together",
    ),
    "stone": Helper(
        id="stone",
        label="Papa",
        tool="a smooth little stone",
        prep="papa set a smooth little stone on the corner",
        tail="papa sat close by to read aloud",
    ),
    "book": Helper(
        id="book",
        label="Mimi",
        tool="a heavy storybook",
        prep="mimi placed a heavy storybook by the edge",
        tail="mimi hummed while they read",
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Zoe", "Ava"]
BOY_NAMES = ["Noah", "Eli", "Theo", "Finn", "Leo"]


@dataclass
class StoryParams:
    place: str
    article: str
    helper: str
    name: str
    gender: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld: a pesky article in a teepee.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--article", choices=ARTICLES.keys())
    ap.add_argument("--helper", choices=HELPERS.keys())
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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


def reasonableness_gate(place: str, article: str, helper: str) -> bool:
    return place == "teepee" or place == "camp" or place == "blanket fort"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS.keys()))
    article = args.article or rng.choice(list(ARTICLES.keys()))
    helper = args.helper or rng.choice(list(HELPERS.keys()))
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        name = args.name
    else:
        name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)

    if not reasonableness_gate(place, article, helper):
        raise StoryError("That story setting does not fit the little rhyme.")
    return StoryParams(place=place, article=article, helper=helper, name=name, gender=gender)


def generate_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)
    hero_type = params.gender
    parent_type = "mother" if params.gender == "girl" else "father"
    hero = world.add(Entity(id=params.name, kind="character", type=hero_type))
    helper_cfg = HELPERS[params.helper]
    helper = world.add(Entity(id=helper_cfg.label, kind="character", type="adult"))
    article_cfg = ARTICLES[params.article]
    article = world.add(Entity(id="article", kind="thing", type="article", label="article", phrase=article_cfg.title))
    world.hero_id = hero.id
    world.article_id = article.id
    world.facts["article_cfg"] = article_cfg
    world.facts["helper_cfg"] = helper_cfg
    world.facts["hero"] = hero
    world.facts["helper"] = helper
    world.facts["article"] = article
    world.facts["params"] = params

    world.say(f"{hero.id} went into {setting.place} with a soft little step.")
    world.say(setting_line(setting))
    world.say(f"Inside sat a pesky article, waiting by itself.")
    world.para()
    read_article(world, hero, article)
    world.para()
    ask_help(world, hero, helper, article)
    apply_fix(world, helper, hero, article, helper_cfg)
    world.para()
    closing(world, hero, article)
    return world


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    art = world.facts["article_cfg"]
    return [
        f"Write a short nursery rhyme about a pesky {art.keyword} article in {p.place}.",
        f"Tell a gentle story in a teepee where {p.name} reads an article but needs help to keep it still.",
        f"Make a tiny happy-ending rhyme about a child, a fluttering article, and a calm ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    article = world.facts["article"]
    art_cfg = world.facts["article_cfg"]
    return [
        QAItem(
            question=f"Who found the pesky article in {p.place}?",
            answer=f"{hero.id} found the pesky article inside {p.place}."
        ),
        QAItem(
            question=f"What made the article hard to read?",
            answer=f"The breeze made the {art_cfg.kind} article flutter and skip, so it was hard to read."
        ),
        QAItem(
            question=f"Who helped make the happy ending?",
            answer=f"{helper.id} helped by using {world.facts['helper_cfg'].tool} to hold the article still."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with {hero.id} reading happily while the article stayed neat and still."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a teepee?",
            answer="A teepee is a small, cozy shelter with sloping sides and a little opening."
        ),
        QAItem(
            question="What does pesky mean?",
            answer="Pesky means bothersome or annoying in a small, tricky way."
        ),
        QAItem(
            question="What is an article?",
            answer="An article is a piece of writing, like something you might read in a newspaper or magazine."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id}: {e.kind}/{e.type} {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="teepee", article="news", helper="clip", name="Mia", gender="girl"),
    StoryParams(place="teepee", article="storybook", helper="book", name="Noah", gender="boy"),
    StoryParams(place="camp", article="recipe", helper="stone", name="Lily", gender="girl"),
]


ASP_RULES = r"""
risky(teepee, A) :- article(A).
fixed(A) :- helper(H), article(A), can_hold(H, A).
valid_story(P, A, H) :- setting(P), article(A), helper(H), risky(P, A), fixed(A).
#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
    for aid in ARTICLES:
        lines.append(asp.fact("article", aid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("can_hold", hid, "news"))
        lines.append(asp.fact("can_hold", hid, "storybook"))
        lines.append(asp.fact("can_hold", hid, "recipe"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(p.place, p.article, p.helper) for p in CURATED if reasonableness_gate(p.place, p.article, p.helper)}
    clingo = set(asp_valid())
    if py == clingo:
        print(f"OK: clingo gate matches python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python gates:")
    print("python:", sorted(py))
    print("clingo:", sorted(clingo))
    return 1


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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        triples = asp_valid()
        print(f"{len(triples)} valid story triples:")
        for t in triples:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

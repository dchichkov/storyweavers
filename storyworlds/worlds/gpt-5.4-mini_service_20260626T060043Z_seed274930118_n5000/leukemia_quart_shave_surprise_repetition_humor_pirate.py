#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/leukemia_quart_shave_surprise_repetition_humor_pirate.py
===============================================================================================================================

A small pirate-tale storyworld built from the seed words:
leukemia, quart, shave.

Premise:
- A pirate ship carries a tiny crew with one sick sailor.
- The crew must fetch a quart of soothing broth and a shave kit before a surprise visit.
- Repetition and humor are baked into the narration: pirate calls, repeated crew chants,
  and a playful misunderstanding about "shave" as both grooming and trimming ropes.
- A surprise twist resolves the scene with a kind helper and a lighter mood.

The world model tracks:
- physical meters: sickness, thirst, broth, neatness, prep
- emotional memes: worry, surprise, humor, relief, togetherness

This script is self-contained and follows the Storyweavers storyworld contract.
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
# World constants
# ---------------------------------------------------------------------------
THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities and world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["sick", "thirst", "broth", "neatness", "prep"]:
            self.meters.setdefault(k, 0.0)
        for k in ["worry", "surprise", "humor", "relief", "togetherness", "hunger"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the ship"
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    verb: str
    gerund: str
    rush: str
    surprise: str
    fix: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "ship": Setting(place="the ship", affords={"broth", "shave", "rescue"}),
    "dock": Setting(place="the dock", affords={"broth", "shave"}),
    "island": Setting(place="the tiny island", affords={"broth", "shave", "rescue"}),
}

QUESTS = {
    "broth": Quest(
        id="broth",
        verb="fetch a quart of broth",
        gerund="fetching a quart of broth",
        rush="hurry to the galley for the quart",
        surprise="the broth was not in the usual pot",
        fix="bring a quart from the warm kettle",
        tags={"quart", "broth", "humor"},
    ),
    "shave": Quest(
        id="shave",
        verb="shave the captain's whiskers",
        gerund="shaving whiskers",
        rush="dash for the shaving kit",
        surprise="the razor was wrapped in ribbon like a present",
        fix="use the little shave kit on deck",
        tags={"shave", "humor", "surprise"},
    ),
    "rescue": Quest(
        id="rescue",
        verb="help the sick pirate rest",
        gerund="helping a sick pirate rest",
        rush="run for a blanket and a cup",
        surprise="the helper arrived with a grin",
        fix="make a soft bed and tell a joke",
        tags={"leukemia", "surprise", "humor"},
    ),
}

CURATED = [
    ("ship", "broth", "quart"),
    ("dock", "shave", "quart"),
    ("island", "rescue", "leukemia"),
]

PIRATE_NAMES = ["Cap'n Finn", "Mara", "Jory", "Nell", "Bo", "Rufus", "Sally"]
PIRATE_TITLES = ["captain", "mate", "deckhand", "cook", "first mate"]
TRAITS = ["brave", "sly", "cheerful", "bouncy", "gentle", "noisy"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combo(setting_id: str, quest_id: str) -> bool:
    return quest_id in SETTINGS[setting_id].affords


def valid_combos() -> list[tuple[str, str]]:
    return [(s, q) for s in SETTINGS for q in QUESTS if valid_combo(s, q)]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid(S,Q) :- setting(S), quest(Q), affords(S,Q).
has_tag(Q,T) :- quest(Q), tag(Q,T).
valid_story(S,Q,W) :- valid(S,Q), needs_word(Q,W).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for q in sorted(s.affords):
            lines.append(asp.fact("affords", sid, q))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        for t in sorted(q.tags):
            lines.append(asp.fact("tag", qid, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story model helpers
# ---------------------------------------------------------------------------
def _narrate_chant(world: World, crew: list[Entity], line: str) -> None:
    names = ", ".join(c.id for c in crew)
    world.say(f"{names} sang, '{line}'")


def _make_story_title(quest: Quest) -> str:
    return {
        "broth": "A Quart of Kindness",
        "shave": "The Shaving Surprise",
        "rescue": "The Laughing Blanket",
    }[quest.id]


def _prediction(world: World, sick: Entity, quest: Quest) -> dict:
    sim = world.copy()
    sim.get(sick.id).memes["worry"] += 1
    if quest.id == "broth":
        sim.get(sick.id).meters["broth"] += 1
    if quest.id == "rescue":
        sim.get(sick.id).memes["relief"] += 1
    return {
        "surprise": True,
        "comfort": sim.get(sick.id).meters["broth"] >= THRESHOLD or quest.id == "rescue",
    }


def tell(setting: Setting, quest: Quest, hero_name: str, hero_type: str, title: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=title))
    mate = world.add(Entity(id="Mate", kind="character", type="pirate", label="mate"))
    cook = world.add(Entity(id="Cook", kind="character", type="pirate", label="cook"))
    sick = world.add(Entity(id="SickSailor", kind="character", type="pirate", label="sick sailor"))
    broth = world.add(Entity(id="Quart", kind="thing", type="quart", label="quart", phrase="a warm quart of broth", caretaker="Cook"))
    razor = world.add(Entity(id="Razor", kind="thing", type="thing", label="razor", phrase="a tiny razor with a shiny handle"))
    blanket = world.add(Entity(id="Blanket", kind="thing", type="thing", label="blanket", phrase="a soft blanket", caretaker="Mate"))

    # Act 1
    world.say(f"On {setting.place}, {hero.id} was a {hero.label_word if hasattr(hero, 'label_word') else title} pirate with a grin and a curly beard.")
    world.say(f"{hero.id} loved a good deck day, and the crew loved a good joke even more.")
    world.say(f"One thing made the ship feel oddly serious: {sick.id} had leukemia and needed gentle care.")
    world.say(f"So the crew kept saying, 'A quart for {sick.id}, a quart for {sick.id}!'")

    # Act 2
    world.para()
    world.say(f"{hero.id} wanted to {quest.verb}, but the day threw in a surprise.")
    world.say(f"{quest.surprise.capitalize()}.")
    world.say(f"{hero.id} blinked. 'A shave? A shave? Or a shave of rope?' {hero.id} asked, and the crew laughed.")
    world.say(f"{hero.id} shouted, 'No, no, not rope-shave, face-shave!'")
    world.say(f"{hero.id} hurried with the crew to {quest.fix}.")

    # World state update
    hero.memes["surprise"] += 1
    hero.memes["humor"] += 1
    mate.memes["humor"] += 1
    cook.memes["worry"] += 1
    sick.memes["worry"] += 1
    if quest.id == "broth":
        broth.meters["broth"] += 1
        sick.meters["broth"] += 1
        sick.memes["relief"] += 1
    elif quest.id == "shave":
        razor.meters["neatness"] += 1
        hero.meters["prep"] += 1
    else:
        blanket.meters["prep"] += 1
        sick.memes["relief"] += 1

    _narrate_chant(world, [hero, mate, cook], "A quart, a quart, a kindly quart!")

    # Act 3
    world.para()
    if quest.id == "broth":
        world.say(f"At last, {cook.id} lifted the quart high. {sick.id} sipped the broth and smiled.")
        world.say(f"That tiny quart made the whole ship feel softer, and {hero.id} laughed at the serious-silly day.")
    elif quest.id == "shave":
        world.say(f"Then the razor turned out to be a present from the dockhand, not trouble at all.")
        world.say(f"{hero.id} shaved the captain's whiskers into a neat little curl, and everyone snorted with laughter.")
    else:
        world.say(f"Then a helper arrived with a grin and a blanket, which was the biggest surprise of all.")
        world.say(f"{sick.id} rested at once, and the crew told jokes until the fear grew small.")
    world.say(f"In the end, the ship kept rocking, but the crew felt bright, kind, and together.")

    world.facts.update(
        hero=hero, mate=mate, cook=cook, sick=sick,
        broth=broth, razor=razor, blanket=blanket,
        setting=setting, quest=quest,
        title=title,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a playful pirate tale that uses the words leukemia, quart, and shave.",
        f"Tell a short story where {f['hero'].id} and the crew need a quart, face a surprise, and keep their humor.",
        f"Create a pirate story with repetition, a small joke about shave, and a kind ending for a sailor with leukemia.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, quest, sick = f["hero"], f["quest"], f["sick"]
    answer_base = {
        "broth": f"It was about {hero.id} and the pirate crew, who needed a quart of broth for {sick.id}.",
        "shave": f"It was about {hero.id} and the pirate crew, who had a funny surprise while shaving.",
        "rescue": f"It was about {hero.id} and the pirate crew, who cared for {sick.id} with a blanket and jokes.",
    }[quest.id]
    out = [
        QAItem(question="Who was the story about?", answer=answer_base),
        QAItem(question="What surprising thing happened on the ship?", answer=f["quest"].surprise.capitalize() + "."),
        QAItem(question="How did the crew act?", answer="They kept repeating their chant, laughing, and helping each other."),
    ]
    if quest.id == "broth":
        out.append(QAItem(
            question="Why did the crew want a quart?",
            answer="They wanted a quart of broth so the sick sailor could feel better.",
        ))
    elif quest.id == "shave":
        out.append(QAItem(
            question="Why was the shave funny?",
            answer="It was funny because the crew first wondered whether shave meant a face shave or a rope trim.",
        ))
    else:
        out.append(QAItem(
            question="Why was the ending gentle?",
            answer="The ending was gentle because the crew brought a blanket, told jokes, and helped the sick sailor rest.",
        ))
    return out


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quart?",
            answer="A quart is a unit for measuring liquid, like soup or broth.",
        ),
        QAItem(
            question="What does shave mean?",
            answer="To shave usually means to cut hair very close with a razor.",
        ),
        QAItem(
            question="What is leukemia?",
            answer="Leukemia is a serious illness that affects the blood and needs medical care.",
        ),
        QAItem(
            question="Why can jokes help on a hard day?",
            answer="Jokes can make people feel a little less worried and more connected.",
        ),
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Params and generation
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    quest: str
    seed_word: str
    name: str
    title: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with leukemia, quart, shave.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--seed-word", choices=["leukemia", "quart", "shave"])
    ap.add_argument("--name")
    ap.add_argument("--title", choices=PIRATE_TITLES)
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
    if args.place and args.quest and not valid_combo(args.place, args.quest):
        raise StoryError("That place cannot reasonably host that pirate quest.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.quest is None or c[1] == args.quest)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, quest = rng.choice(sorted(combos))
    seed_word = args.seed_word or rng.choice(["leukemia", "quart", "shave"])
    name = args.name or rng.choice(PIRATE_NAMES)
    title = args.title or rng.choice(PIRATE_TITLES)
    return StoryParams(place=place, quest=quest, seed_word=seed_word, name=name, title=title)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], QUESTS[params.quest], params.name, "pirate", params.title)
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


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def asp_program_full(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program_full("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program_full("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (setting, quest) combos:")
        for s, q in triples:
            print(f"  {s:8} {q}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        curated = [StoryParams(place=s, quest=q, seed_word=w, name="Mara", title="captain")
                   for s, q, w in CURATED]
        samples = [generate(p) for p in curated]
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

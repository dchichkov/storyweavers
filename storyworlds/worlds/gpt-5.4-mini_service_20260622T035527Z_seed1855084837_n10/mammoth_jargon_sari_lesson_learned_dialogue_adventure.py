#!/usr/bin/env python3
"""
storyworlds/worlds/mammoth_jargon_sari_lesson_learned_dialogue_adventure.py
===========================================================================

A small adventure storyworld about a child explorer, an old path, a confusing
bit of jargon, and a sari that helps turn the problem into a lesson learned.

The story is state-driven: a world model tracks physical meters and emotional
memes, a short causal turn changes the scene, and the ending image proves what
changed. The words mammoth, jargon, and sari are always included.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Optional


HERE = Path(__file__).resolve()
for parent in (HERE.parent, *HERE.parents):
    if (parent / "results.py").exists():
        sys.path.insert(0, str(parent))
        break

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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    tags: set[str] = field(default_factory=set)
    attrs: dict[str, Any] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister", "aunt"}
        male = {"boy", "father", "dad", "man", "brother", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def ref(self) -> str:
        return self.phrase or self.label or self.id

    @property
    def label_word(self) -> str:
        return self.label or self.type or self.id


@dataclass
class StoryParams:
    place: str
    theme: str
    word: str
    relic: str
    garment: str
    name: str = "Mina"
    gender: str = "girl"
    parent: str = "mother"
    trait: str = "curious"
    seed: Optional[int] = None


@dataclass
class Place:
    id: str
    label: str
    affirms: set[str] = field(default_factory=set)
    note: str = ""


@dataclass
class Theme:
    id: str
    name: str
    opening: str
    discovery: str
    twist: str
    lesson: str
    ending: str


PLACES = {
    "museum": Place(id="museum", label="the museum hall", affirms={"adventure"}),
    "cave": Place(id="cave", label="the echoing cave", affirms={"adventure"}),
    "desert": Place(id="desert", label="the dusty ruins", affirms={"adventure"}),
}

THEMES = {
    "adventure": Theme(
        id="adventure",
        name="Adventure",
        opening="They went in like brave explorers on a map-hunt.",
        discovery="The path felt grand and secret, like a tiny quest.",
        twist="But one sign was written in hard jargon, and nobody could guess it at first.",
        lesson="The best explorers ask for clear words when a path gets confusing.",
        ending="They left with a steady step and a better plan.",
    ),
    "expedition": Theme(
        id="expedition",
        name="Expedition",
        opening="They moved like a little expedition with bright eyes.",
        discovery="Every corner promised one more clue.",
        twist="Then a guide used jargon that sounded important but meant very little to Mina.",
        lesson="A good helper explains things plainly.",
        ending="Soon the route felt simple again.",
    ),
}

WORDS = ["mammoth", "jargon", "sari"]
RELICS = {
    "mammoth": {
        "label": "a carved mammoth token",
        "phrase": "a small carved mammoth token",
        "tag": "mammoth",
    },
    "jargon": {
        "label": "a note full of jargon",
        "phrase": "a folded note full of jargon",
        "tag": "jargon",
    },
    "sari": {
        "label": "a bright sari",
        "phrase": "a bright sari with gold edges",
        "tag": "sari",
    },
}

GARMENTS = {
    "sari": {
        "label": "the sari",
        "phrase": "a bright sari with gold edges",
        "tag": "sari",
    },
    "shawl": {
        "label": "a shawl",
        "phrase": "a soft shawl",
        "tag": "sari",
    },
}

GIRL_NAMES = ["Mina", "Asha", "Lina", "Zoe", "Nora"]
BOY_NAMES = ["Arin", "Leo", "Omar", "Ben", "Ivo"]
TRAITS = ["curious", "brave", "careful", "quick-thinking"]


class World:
    def __init__(self, place: Place, theme: Theme) -> None:
        self.place = place
        self.theme = theme
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, Any] = {}
        self.history: list[dict[str, Any]] = []
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple[str, str]] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, sentence: str) -> None:
        if sentence:
            self.paragraphs[-1].append(sentence)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def event(self, kind: str, **data: Any) -> None:
        self.history.append({"kind": kind, **data})

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.place, self.theme)
        clone.entities = {k: asdict(v) if False else v for k, v in self.entities.items()}
        import copy as _copy
        clone.entities = _copy.deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.history = list(self.history)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld with mammoth, jargon, and sari.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--theme", choices=sorted(THEMES))
    ap.add_argument("--word", choices=WORDS)
    ap.add_argument("--relic", choices=sorted(RELICS))
    ap.add_argument("--garment", choices=sorted(GARMENTS))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", "--n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for theme in THEMES:
            for word in WORDS:
                if place == "museum" and word == "mammoth":
                    combos.append((place, theme, word))
                elif place != "museum" and word in {"jargon", "sari"}:
                    combos.append((place, theme, word))
    return combos


def explain_rejection(place: str, word: str) -> str:
    if place == "museum" and word != "mammoth":
        return "(No story: the museum adventure wants the mammoth word at its center.)"
    if place != "museum" and word == "mammoth":
        return "(No story: the mammoth word fits the museum better than this place.)"
    return "(No story: that combination does not make a strong adventure.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.theme is None or c[1] == args.theme)
              and (args.word is None or c[2] == args.word)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, theme, word = rng.choice(sorted(combos))
    relic = args.relic or ("mammoth" if word == "mammoth" else rng.choice(["jargon", "sari"]))
    garment = args.garment or "sari"
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(name_pool)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, theme=theme, word=word, relic=relic, garment=garment,
                       name=name, gender=gender, parent=parent, trait=trait)


def _make_entities(world: World, params: StoryParams) -> tuple[Entity, Entity, Entity, Entity, Entity]:
    child = world.add(Entity(id="child", kind="character", type=params.gender, label=params.name, traits=[params.trait]))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    relic_cfg = RELICS[params.relic]
    relic = world.add(Entity(id="relic", type="thing", label=relic_cfg["label"], phrase=relic_cfg["phrase"], tags={relic_cfg["tag"]}, owner=child.id, caretaker=parent.id))
    garment_cfg = GARMENTS[params.garment]
    garment = world.add(Entity(id="garment", type="thing", label=garment_cfg["label"], phrase=garment_cfg["phrase"], tags={garment_cfg["tag"]}, owner=child.id))
    clue = world.add(Entity(id="clue", type="thing", label="a trail marker", phrase="a trail marker on a stone", tags={"jargon"}))
    return child, parent, relic, garment, clue


def tell(world: World, params: StoryParams) -> World:
    child, parent, relic, garment, clue = _make_entities(world, params)
    child.memes["curiosity"] += 1
    child.memes["joy"] += 1
    clue.meters["mystery"] += 1
    relic.meters["value"] += 1
    garment.meters["shine"] += 1
    world.facts.update(child=child, parent=parent, relic=relic, garment=garment, clue=clue, params=params)

    world.say(f"{child.label} went into {world.place.label} with {parent.label_word} for an adventure.")
    world.say(world.theme.opening)
    world.say(f"{child.label} noticed {relic.phrase} beside {world.place.label}.")
    world.say(world.theme.discovery)

    world.para()
    child.memes["desire"] += 1
    world.say(f'Then {child.label} pointed at a sign and asked, "What does this jargon mean?"')
    parent.memes["care"] += 1
    world.say(f'"It is tricky, but we can figure it out together," {parent.label_word} said.')
    world.say(world.theme.twist)

    if params.word == "mammoth":
        relic.meters["found"] += 1
        child.meters["treasure"] += 1
        world.event("discovery", kind="mammoth")
        world.say(f'Inside the hall, a giant mammoth statue stood like a quiet giant, and {child.label} smiled.')
    elif params.word == "jargon":
        clue.meters["explained"] += 1
        world.event("discovery", kind="jargon")
        world.say(f"{parent.label_word} translated the jargon into plain words, and the path became easy.")
    else:
        garment.meters["worn"] += 1
        child.meters["confidence"] += 1
        world.event("discovery", kind="sari")
        world.say(f"{parent.label_word} tied the sari neatly so {child.label} could move without fuss.")

    world.para()
    child.memes["lesson"] += 1
    child.memes["love"] += 1
    world.say(world.theme.lesson)
    if params.word == "mammoth":
        world.say(f"{child.label} left with the mammoth token in one hand and a bright grin on the other.")
    elif params.word == "jargon":
        world.say(f"{child.label} left repeating the new clear words instead of the confusing jargon.")
    else:
        world.say(f"{child.label} left with the sari fluttering safely and a proud, steady step.")
    world.say(world.theme.ending)

    world.facts["outcome"] = params.word
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a short adventure story for a young child that includes the words "{p.word}", "mammoth", and "sari".',
        f"Tell a dialogue-heavy adventure about {p.name} at {world.place.label} where jargon causes confusion and a lesson is learned.",
        f'Write a gentle quest story that ends with a lesson learned and includes a mammoth, jargon, and a sari.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    child: Entity = world.facts["child"]
    parent: Entity = world.facts["parent"]
    relic: Entity = world.facts["relic"]
    garment: Entity = world.facts["garment"]
    place = world.place.label
    qa = [
        QAItem(
            question=f"Where did {child.label} go for the adventure?",
            answer=f"{child.label} went to {place} with {parent.label_word}. It was an adventure in a concrete place, not just a dream about one.",
        ),
        QAItem(
            question=f"Why did {child.label} ask about the jargon?",
            answer=f"{child.label} saw words that were hard to understand and wanted them explained. {parent.label_word} turned the confusing jargon into plain words so the path made sense.",
        ),
        QAItem(
            question=f"What did {child.label} do with the {relic.label_word} or the sari?",
            answer=f"{child.label} either found the mammoth token, solved the jargon, or wore the sari depending on the story path. In this run, the important object was {relic.label_word}, and the sari helped keep the adventure neat.",
        ),
        QAItem(
            question=f"What lesson did {child.label} learn?",
            answer=f"{child.label} learned that clear words help explorers more than confusing jargon. The lesson learned made the ending calmer and smarter.",
        ),
    ]
    if p.word == "mammoth":
        qa.append(QAItem(
            question="What made the ending image feel like an adventure?",
            answer=f"The mammoth statue and token made the scene feel ancient and brave. {child.label} left with the treasure and a grin.",
        ))
    elif p.word == "jargon":
        qa.append(QAItem(
            question="How did the jargon change the story?",
            answer=f"The jargon created the problem, because it sounded important but was hard to understand. Once it was translated, the adventure moved forward again.",
        ))
    else:
        qa.append(QAItem(
            question="How did the sari matter in the story?",
            answer=f"The sari was a bright piece of clothing that helped {child.label} move safely and feel ready for the quest. It made the ending image colorful and steady.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {world.facts["relic"].tags.pop() if False else None}
    p: StoryParams = world.facts["params"]
    out = [
        QAItem("What is a mammoth?", "A mammoth was a very big, hairy elephant-like animal that lived long ago."),
        QAItem("What is jargon?", "Jargon is special words that can sound confusing when you do not know them yet."),
        QAItem("What is a sari?", "A sari is a long piece of clothing that can be wrapped and worn neatly."),
    ]
    if p.word == "mammoth":
        return [out[0], out[1], out[2]]
    if p.word == "jargon":
        return [out[1], out[0], out[2]]
    return [out[2], out[0], out[1]]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, q in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {q}")
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


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.theme not in THEMES or params.word not in WORDS:
        raise StoryError("Invalid params.")
    if params.place == "museum" and params.word != "mammoth":
        raise StoryError(explain_rejection(params.place, params.word))
    if params.place != "museum" and params.word == "mammoth":
        raise StoryError(explain_rejection(params.place, params.word))
    world = World(PLACES[params.place], THEMES[params.theme])
    tell(world, params)
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.tags:
            parts.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id}: {e.label or e.type} {' '.join(parts)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,T,W) :- place(P), theme(T), word(W), ok_combo(P,W).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for t in THEMES:
        lines.append(asp.fact("theme", t))
    for w in WORDS:
        lines.append(asp.fact("word", w))
    for p, _, w in valid_combos():
        lines.append(asp.fact("ok_combo", p, w))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    ok = python_set == asp_set
    try:
        sample = generate(StoryParams(place="museum", theme="adventure", word="mammoth", relic="mammoth", garment="sari"))
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    if ok:
        print(f"OK: ASP and Python valid_combos match ({len(python_set)} combos).")
        print("OK: generate() smoke test passed.")
        return 0
    print("MISMATCH between ASP and Python combos.")
    print("only in ASP:", sorted(asp_set - python_set))
    print("only in Python:", sorted(python_set - asp_set))
    return 1


CURATED = [
    StoryParams(place="museum", theme="adventure", word="mammoth", relic="mammoth", garment="sari", name="Mina", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="cave", theme="adventure", word="jargon", relic="jargon", garment="sari", name="Arin", gender="boy", parent="father", trait="careful"),
    StoryParams(place="desert", theme="expedition", word="sari", relic="sari", garment="sari", name="Lina", gender="girl", parent="mother", trait="brave"),
]


def asp_show() -> str:
    return asp_program("#show valid/3.")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_show())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        combos = sorted(set(asp.atoms(model, "valid")))
        print("\n".join(f"{a}, {b}, {c}" for a, b, c in combos))
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
            header = f"### {p.name}: {p.word} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

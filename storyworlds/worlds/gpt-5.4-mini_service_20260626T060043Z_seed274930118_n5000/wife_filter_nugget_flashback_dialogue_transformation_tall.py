#!/usr/bin/env python3
"""
storyworlds/worlds/wife_filter_nugget_flashback_dialogue_transformation_tall.py
================================================================================

A small tall-tale storyworld about a wife, a filter, and a nugget.

Premise:
- A prospector carries a screen-like filter to wash river sand.
- His wife remembers a flashback from an earlier day when a tiny gold nugget
  slipped through the wrong mesh.
- The couple talks it over in dialogue, then transforms the filter into a finer
  one so the nugget can be saved.

This world keeps the simulation small but state-driven:
- physical meters track dust, shine, and fineness
- emotional memes track worry, hope, pride, and relief
- the story changes based on whether the filter is too coarse or ready for the nugget
- the ending proves the transformation by showing what changed in the world
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ["dust", "shine", "fine", "weight", "loss"]:
            self.meters.setdefault(key, 0.0)
        for key in ["worry", "hope", "pride", "relief", "memory"]:
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"wife", "woman", "girl", "mother", "mom"}
        male = {"husband", "man", "boy", "father", "dad", "miner", "prospector"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the river bend"
    weather: str = "hot"
    affords: set[str] = field(default_factory=lambda: {"sifting", "washing"})


@dataclass
class FilterDef:
    id: str
    label: str
    phrase: str
    fine_level: float
    can_transform_to: str
    used_for: str


@dataclass
class NuggetDef:
    id: str
    label: str
    phrase: str
    weight: float
    shine: float


@dataclass
class StoryParams:
    place: str
    filter: str
    nugget: str
    name: str
    spouse_name: str
    spouse_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.timeline: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.timeline.append(text)

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
        clone.timeline = list(self.timeline)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "river": Setting(place="the river bend", weather="hot", affords={"sifting", "washing"}),
    "creek": Setting(place="the creek bank", weather="bright", affords={"sifting", "washing"}),
    "yard": Setting(place="the dusty yard", weather="hot", affords={"sifting"}),
}

FILTERS = {
    "screen": FilterDef(
        id="screen",
        label="river screen",
        phrase="a sturdy river screen with wide holes",
        fine_level=0.3,
        can_transform_to="mesh",
        used_for="sifting",
    ),
    "mesh": FilterDef(
        id="mesh",
        label="fine mesh filter",
        phrase="a fine mesh filter like a biscuit tin lid",
        fine_level=0.8,
        can_transform_to="silk",
        used_for="sifting",
    ),
    "silk": FilterDef(
        id="silk",
        label="silk sieve",
        phrase="a silk sieve so fine it could catch moonlight",
        fine_level=1.0,
        can_transform_to="silk",
        used_for="washing",
    ),
}

NUGGETS = {
    "pea": NuggetDef(
        id="pea",
        label="gold nugget",
        phrase="a gold nugget no bigger than a pea",
        weight=0.2,
        shine=0.8,
    ),
    "thumb": NuggetDef(
        id="thumb",
        label="gold nugget",
        phrase="a thumb-sized gold nugget",
        weight=0.5,
        shine=1.0,
    ),
}

NAMES = ["Mabel", "June", "Ruth", "Ivy", "Pearl", "Annie", "Clara", "Belle"]
SPOUSES = ["husband", "wife", "partner"]
TRAITS = ["tall-talking", "steady", "plucky", "bright-eyed", "hard-working"]


# ---------------------------------------------------------------------------
# State helpers
# ---------------------------------------------------------------------------

def filter_def() -> FilterDef:
    return FILTERS


def nugget_def() -> NuggetDef:
    return NUGGETS


def filter_at_risk(filt: FilterDef, nugget: NuggetDef) -> bool:
    return nugget.weight > filt.fine_level


def can_transform(filt: FilterDef, nugget: NuggetDef) -> bool:
    return filt.can_transform_to != filt.id


def predict_loss(world: World, filt: Entity, nugget: Entity) -> bool:
    return world.get(filt.id).meters.get("fine", 0.0) < nugget.meters.get("weight", 0.0)


# ---------------------------------------------------------------------------
# Narration
# ---------------------------------------------------------------------------

def tell_flashback(world: World, wife: Entity, filt: Entity, nugget: Entity) -> None:
    wife.memes["memory"] += 1
    world.say(
        f"Years back, when the sun was as wide as a wagon wheel, {wife.id} "
        f"remembered the day a little gold pebble had slipped clean through "
        f"{wife.pronoun('possessive')} old filter."
    )
    world.say(
        f"That flashback sat in {wife.pronoun('possessive')} mind like a pebble in a boot."
    )


def tell_dialogue(world: World, wife: Entity, spouse: Entity, filt: Entity, nugget: Entity) -> None:
    wife.memes["worry"] += 1
    spouse.memes["hope"] += 1
    world.say(
        f'"I know that filter," {wife.id} said. "It is fine for sand, but not for '
        f"{nugget.label}s like this one.""
    )
    world.say(
        f'"Then we had better talk plain," {spouse.id} said. "What is the trouble?"'
    )
    world.say(
        f'"The trouble is a nugget can wink right past a coarse screen," {wife.id} said.'
    )


def transform_filter(world: World, filt: Entity, filt_def: FilterDef, spouse: Entity) -> Optional[Entity]:
    if filt.meters["fine"] >= THRESHOLD:
        return filt
    if not can_transform(filt_def, NUGGETS[world.facts["nugget_id"]]):
        return None
    filt.meters["fine"] = 1.0
    filt.label = f"fine {filt_def.label}"
    filt.phrase = f"a hand-worked {filt_def.label} with tighter holes"
    spouse.memes["pride"] += 1
    world.say(
        f"So the two of them got to work, and by sunset they had transformed the "
        f"old filter into a finer one, tight as a fiddle string."
    )
    return filt


def resolve_story(world: World, wife: Entity, spouse: Entity, filt: Entity, nugget: Entity) -> None:
    if filt.meters["fine"] >= nugget.meters["weight"]:
        wife.memes["relief"] += 1
        spouse.memes["pride"] += 1
        world.say(
            f'At last the gold nugget stayed where it belonged. "Well, now!" '
            f'{spouse.id} laughed. "This filter has a smarter mind than a town sheriff."'
        )
        world.say(
            f'{wife.id} smiled, and the little nugget gleamed safe in the pan while '
            f'the fine filter held steady, proud as a rooster on a fence rail.'
        )
    else:
        wife.memes["worry"] += 1
        world.say(
            f'But the nugget was too lively and slipped away again, so the pair had '
            f'to try once more before the day could end.'
        )


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)

    wife = world.add(Entity(
        id=params.name,
        kind="character",
        type="wife",
        label="wife",
        phrase=f"a {params.spouse_type}",
    ))
    spouse = world.add(Entity(
        id=params.spouse_name,
        kind="character",
        type="husband" if params.spouse_type == "husband" else "wife",
        label=params.spouse_type,
        phrase=f"a {params.spouse_type}",
    ))
    filt_def = FILTERS[params.filter]
    nug_def = NUGGETS[params.nugget]

    filt = world.add(Entity(
        id="filter",
        kind="object",
        type="filter",
        label=filt_def.label,
        phrase=filt_def.phrase,
        owner=spouse.id,
    ))
    filt.meters["fine"] = filt_def.fine_level

    nugget = world.add(Entity(
        id="nugget",
        kind="object",
        type="nugget",
        label=nug_def.label,
        phrase=nug_def.phrase,
        owner=spouse.id,
    ))
    nugget.meters["weight"] = nug_def.weight
    nugget.meters["shine"] = nug_def.shine

    world.facts.update(
        wife=wife,
        spouse=spouse,
        filter=filt,
        nugget=nugget,
        filter_id=params.filter,
        nugget_id=params.nugget,
        setting=setting,
        filter_def=filt_def,
        nugget_def=nug_def,
    )

    world.say(
        f"{wife.id} was a {params.name and 'wife'} with a voice that could "
        f"carry over three hills, and {spouse.id} knew how to listen."
    )
    world.say(
        f"Together they came to {setting.place} with {filt.phrase} and "
        f"{nug_def.phrase} waiting to be saved."
    )

    world.para()
    tell_flashback(world, wife, filt, nugget)

    world.para()
    tell_dialogue(world, wife, spouse, filt, nugget)
    if filter_at_risk(filt_def, nug_def):
        world.say(
            f"The old screen was in trouble, because the nugget was heavier than "
            f"its first, loose weave could manage."
        )
    else:
        world.say(
            f"The filter was already fine enough for the nugget, but the pair still "
            f"checked it twice, just to be sure."
        )

    world.para()
    transformed = transform_filter(world, filt, filt_def, spouse)
    if transformed is not None:
        world.facts["transformed"] = True
    else:
        world.facts["transformed"] = False

    resolve_story(world, wife, spouse, filt, nugget)

    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a tall tale about a wife, a filter, and a nugget, with a flashback and a safe transformation.',
        f"Tell a story where {f['wife'].id} remembers an old mistake, talks with {f['spouse'].id}, and changes the filter for {f['nugget_def'].phrase}.",
        f'Write a child-friendly tale that includes the words "wife", "filter", and "nugget" and ends with the filter transformed.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    wife = f["wife"]
    spouse = f["spouse"]
    filt = f["filter"]
    nugget = f["nugget"]
    nugdef = f["nugget_def"]
    filtdef = f["filter_def"]

    return [
        QAItem(
            question=f"Who remembered the old mistake about the filter?",
            answer=f"{wife.id} remembered the flashback about the old filter slipping past a nugget.",
        ),
        QAItem(
            question=f"What did {spouse.id} and {wife.id} talk about?",
            answer=f"They talked about whether the filter was fine enough to hold {nugdef.phrase}.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The filter was transformed into a finer one, and the nugget stayed safe in the pan.",
        ),
        QAItem(
            question=f"Why was the old filter not good enough at first?",
            answer=f"It was too coarse for {nugdef.phrase}, so the nugget could have slipped through.",
        ),
        QAItem(
            question=f"How did the transformation help?",
            answer=f"It made the filter tighter, which let it catch the nugget instead of losing it.",
        ),
    ]


WORLD_QA = [
    QAItem(
        question="What is a filter used for in washing or sifting?",
        answer="A filter is used to catch larger pieces and let smaller bits or water pass through.",
    ),
    QAItem(
        question="What is a nugget?",
        answer="A nugget is a small lump of metal, often gold, that can shine in the light.",
    ),
    QAItem(
        question="What is a flashback in a story?",
        answer="A flashback is when the story remembers something that happened earlier.",
    ),
    QAItem(
        question="What does transformation mean?",
        answer="Transformation means something changes into a new form or becomes different.",
    ),
    QAItem(
        question="Why do people talk in dialogue in stories?",
        answer="Dialogue lets characters speak to each other so we can hear their thoughts and feelings.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return WORLD_QA


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
        meters = {k: round(v, 3) for k, v in e.meters.items() if v}
        memes = {k: round(v, 3) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  timeline: {len(world.timeline)} beats")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(P) :- setting(P).

at_risk(F, N) :- filter(F), nugget(N), fine_level(F, L), nugget_weight(N, W), W > L.
needs_transformation(F, N) :- at_risk(F, N), can_transform_to(F, _).
safe(F, N) :- filter(F), nugget(N), fine_level(F, L), nugget_weight(N, W), L >= W.

valid_story(P, F, N) :- place(P), filter(F), nugget(N), at_risk(F, N), needs_transformation(F, N), safe_after_transform(F, N).
safe_after_transform(F, N) :- can_transform_to(F, T), fine_level(T, L2), nugget_weight(N, W), L2 >= W.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, a))
    for fid, f in FILTERS.items():
        lines.append(asp.fact("filter", fid))
        lines.append(asp.fact("fine_level", fid, int(f.fine_level * 10)))
        lines.append(asp.fact("can_transform_to", fid, f.can_transform_to))
        lines.append(asp.fact("used_for", fid, f.used_for))
    for nid, n in NUGGETS.items():
        lines.append(asp.fact("nugget", nid))
        lines.append(asp.fact("nugget_weight", nid, int(n.weight * 10)))
        lines.append(asp.fact("nugget_shine", nid, int(n.shine * 10)))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {
        (place, fid, nid)
        for place in SETTINGS
        for fid, f in FILTERS.items()
        for nid, n in NUGGETS.items()
        if (f.fine_level < n.weight) and (f.can_transform_to != f.id)
    }
    asp_set = set(asp_valid_stories())
    if py == asp_set:
        print(f"OK: clingo gate matches Python gate ({len(py)} stories).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Story API
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale story world: wife, filter, nugget, flashback, dialogue, transformation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--filter", choices=FILTERS)
    ap.add_argument("--nugget", choices=NUGGETS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--spouse-name", dest="spouse_name", choices=NAMES)
    ap.add_argument("--spouse-type", dest="spouse_type", choices=["husband", "wife", "partner"])
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
    place = args.place or rng.choice(list(SETTINGS))
    filt = args.filter or rng.choice(list(FILTERS))
    nug = args.nugget or rng.choice(list(NUGGETS))

    if FILTERS[filt].fine_level >= NUGGETS[nug].weight:
        raise StoryError("This story needs a filter that starts too coarse for the nugget, so the transformation matters.")

    name = args.name or rng.choice(NAMES)
    spouse_name = args.spouse_name or rng.choice([n for n in NAMES if n != name])
    spouse_type = args.spouse_type or "husband"
    return StoryParams(place=place, filter=filt, nugget=nug, name=name, spouse_name=spouse_name, spouse_type=spouse_type)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
    StoryParams(place="river", filter="screen", nugget="thumb", name="Mabel", spouse_name="Otis", spouse_type="husband"),
    StoryParams(place="creek", filter="screen", nugget="pea", name="June", spouse_name="Ezra", spouse_type="husband"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:\n")
        for p, f, n in stories:
            print(f"  {p:8} {f:10} {n}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

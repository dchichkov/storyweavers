#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/hypoallergenic_scissor_flashback_rhyme_superhero_story.py
========================================================================================

A small standalone storyworld: a child superhero and a careful grown-up face a
snippy costume problem, remember an earlier lesson in a flashback, and end with
a safer solution that still feels heroic.

Seed words:
- hypoallergenic
- scissor

Features:
- Flashback
- Rhyme

Style:
- Superhero Story
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    unsafe: bool = False
    hypoallergenic: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Outfit:
    id: str
    label: str
    phrase: str
    safe_for_skin: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Venue:
    id: str
    label: str
    where: str
    atmosphere: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    venue: str
    tool: str
    outfit: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    parent: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()

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
        other = World()
        other.entities = {k: Entity(**{
            "id": v.id, "kind": v.kind, "type": v.type, "label": v.label,
            "role": v.role, "traits": list(v.traits), "attrs": dict(v.attrs),
            "meters": dict(v.meters), "memes": dict(v.memes),
        }) for k, v in self.entities.items()}
        other.facts = dict(self.facts)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        return other


VENUES = {
    "park": Venue(id="park", label="city park", where="at the city park", atmosphere="under the wide bright trees"),
    "clinic": Venue(id="clinic", label="children's clinic", where="at the children's clinic", atmosphere="with shiny posters on the walls"),
    "studio": Venue(id="studio", label="costume studio", where="in the costume studio", atmosphere="beside piles of capes and masks"),
}

TOOLS = {
    "scissor": Tool(
        id="scissor",
        label="scissors",
        phrase="a pair of scissors",
        unsafe=True,
        hypoallergenic=False,
        tags={"scissor", "cut"},
    ),
    "threadsnips": Tool(
        id="threadsnips",
        label="thread snips",
        phrase="tiny thread snips",
        unsafe=False,
        hypoallergenic=True,
        tags={"safe", "cut"},
    ),
    "glue": Tool(
        id="glue",
        label="glue bottle",
        phrase="a glue bottle",
        unsafe=False,
        hypoallergenic=True,
        tags={"safe"},
    ),
}

OUTFITS = {
    "cape": Outfit(id="cape", label="cape", phrase="a bright cape", safe_for_skin=True, tags={"cape"}),
    "mask": Outfit(id="mask", label="mask", phrase="a soft mask lining", safe_for_skin=True, tags={"mask", "hypoallergenic"}),
    "gloves": Outfit(id="gloves", label="gloves", phrase="soft gloves", safe_for_skin=True, tags={"gloves"}),
}

GIRL_NAMES = ["Mia", "Luna", "Nora", "Zoe", "Ava"]
BOY_NAMES = ["Leo", "Finn", "Max", "Owen", "Theo"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for venue in VENUES:
        for tool_id, tool in TOOLS.items():
            for outfit_id, outfit in OUTFITS.items():
                if tool.unsafe and outfit.safe_for_skin:
                    combos.append((venue, tool_id, outfit_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero storyworld with a flashback and a rhyme.")
    ap.add_argument("--venue", choices=VENUES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--outfit", choices=OUTFITS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.tool and args.outfit:
        tool = TOOLS[args.tool]
        outfit = OUTFITS[args.outfit]
        if not (tool.unsafe and outfit.safe_for_skin):
            raise StoryError("This story needs an unsafe scissors problem and a safe hypoallergenic fix.")
    combos = [c for c in valid_combos()
              if (args.venue is None or c[0] == args.venue)
              and (args.tool is None or c[1] == args.tool)
              and (args.outfit is None or c[2] == args.outfit)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    venue, tool, outfit = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if hero_gender == "girl" else "girl")
    hero = args.hero or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice([n for n in (GIRL_NAMES if helper_gender == "girl" else BOY_NAMES) if n != hero])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(venue=venue, tool=tool, outfit=outfit, hero=hero, hero_gender=hero_gender,
                       helper=helper, helper_gender=helper_gender, parent=parent)


def _flashback(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["remember"] = hero.memes.get("remember", 0.0) + 1
    world.say(
        f"Earlier that week, {hero.id} had learned a tiny lesson: "
        f"{helper.id} had said, \"No rash dash with a scratchy flash.\""
    )
    world.say(
        f"That rhyme had stuck like glue, and now {hero.id} knew what to do."
    )


def tell(venue: Venue, tool: Tool, outfit: Outfit, hero_name: str, hero_gender: str,
         helper_name: str, helper_gender: str, parent_gender: str) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_gender, role="parent", label="the parent"))
    world.add(Entity(id="tool", type="tool", label=tool.label, attrs={"hypoallergenic": tool.hypoallergenic}))
    world.add(Entity(id="outfit", type="outfit", label=outfit.label, attrs={"safe_for_skin": outfit.safe_for_skin}))

    world.say(
        f"At the {venue.label}, {hero.id} became Captain Spark, a little superhero in {venue.atmosphere}."
    )
    world.say(
        f"{hero.id} wanted to trim a costume ribbon with {tool.phrase}, because the cape needed a cleaner line."
    )
    _flashback(world, hero, helper)
    world.para()
    world.say(
        f"But {helper.id} held up a hand. \"Use {outfit.phrase} first,\" {helper.pronoun()} said, "
        f"\"so the skin stays calm and bright.\""
    )
    world.say(
        f"{hero.id} nodded. The scissors stayed closed, and the plan changed from sharp to smart."
    )
    world.para()
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    world.say(
        f"{parent.label_word.capitalize()} smiled and helped tie the {outfit.label} in place."
    )
    world.say(
        f"Then {hero.id} used the safe costume, and the hero's cape swished just right."
    )
    world.say(
        f'"Quick feet, neat seat, and a hypoallergenic treat," {helper.id} rhymed, and everybody cheered.'
    )

    world.facts.update(
        hero=hero, helper=helper, parent=parent, venue=venue, tool=tool, outfit=outfit,
        avoided=tool.unsafe and outfit.safe_for_skin, flashback=True, rhyme=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a superhero story that includes the words "{f["tool"].label}" and "hypoallergenic".',
        f"Tell a flashback story where {f['hero'].id} remembers a rhyme before using the safe costume fix.",
        f"Write a child-friendly superhero story where {f['helper'].id} stops {f['hero'].id} from grabbing the scissors and ends with a rhyme.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    parent = f["parent"]
    tool = f["tool"]
    outfit = f["outfit"]
    return [
        QAItem(
            question=f"What problem did {hero.id} have?",
            answer=(
                f"{hero.id} wanted to use {tool.phrase} on a costume ribbon, but that would have been too sharp. "
                f"{helper.id} reminded {hero.id} to choose a safer way first."
            ),
        ),
        QAItem(
            question="What did the flashback help them remember?",
            answer=(
                f"It helped {hero.id} remember a rhyme about avoiding a scratchy flash. "
                f"That memory made {hero.id} pause before touching the scissors."
            ),
        ),
        QAItem(
            question=f"How did they solve the problem with {parent.label_word}?",
            answer=(
                f"They used {outfit.phrase} and kept the scissors closed. "
                f"Then {parent.label_word} helped finish the costume in a calm, safe way."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does hypoallergenic mean?",
            answer=(
                "Hypoallergenic means made to be gentle on skin and less likely to cause a reaction. "
                "That is why it is a good word for safe costume materials."
            ),
        ),
        QAItem(
            question="Why should scissors be handled carefully?",
            answer=(
                "Scissors have sharp blades that can cut fabric and skin. "
                "Children should only use them with a careful grown-up nearby."
            ),
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer=(
                "A flashback is when the story briefly remembers something that happened earlier. "
                "It can help explain why a character makes a choice now."
            ),
        ),
        QAItem(
            question="Why do rhymes help in stories?",
            answer=(
                "Rhymes are easy to remember and fun to say out loud. "
                "They can help a character remember a rule or a plan."
            ),
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: this world needs an unsafe scissors problem and a safe hypoallergenic fix.)"


def asp_facts() -> str:
    import asp
    lines = []
    for v in VENUES:
        lines.append(asp.fact("venue", v))
    for t in TOOLS.values():
        lines.append(asp.fact("tool", t.id))
        if t.unsafe:
            lines.append(asp.fact("unsafe", t.id))
        if t.hypoallergenic:
            lines.append(asp.fact("hypoallergenic", t.id))
    for o in OUTFITS.values():
        lines.append(asp.fact("outfit", o.id))
        if o.safe_for_skin:
            lines.append(asp.fact("safe_for_skin", o.id))
    return "\n".join(lines)


ASP_RULES = r"""
valid(V,T,O) :- venue(V), tool(T), outfit(O), unsafe(T), safe_for_skin(O).
#show valid/3.
"""


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


CURATED = [
    StoryParams(venue="studio", tool="scissor", outfit="mask", hero="Mia", hero_gender="girl",
                helper="Leo", helper_gender="boy", parent="mother"),
    StoryParams(venue="clinic", tool="scissor", outfit="gloves", hero="Theo", hero_gender="boy",
                helper="Nora", helper_gender="girl", parent="father"),
]


def asp_verify() -> int:
    import asp
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid-combos differ.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        return 1
    if rc == 0:
        print("OK: ASP matches Python and story generation works.")
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.venue not in VENUES:
        raise StoryError(f"Unknown venue: {params.venue}")
    if params.tool not in TOOLS:
        raise StoryError(f"Unknown tool: {params.tool}")
    if params.outfit not in OUTFITS:
        raise StoryError(f"Unknown outfit: {params.outfit}")
    world = tell(
        VENUES[params.venue],
        TOOLS[params.tool],
        OUTFITS[params.outfit],
        params.hero,
        params.hero_gender,
        params.helper,
        params.helper_gender,
        params.parent,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def resolve_name(gender: str, rng: random.Random, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.venue is None or c[0] == args.venue)
              and (args.tool is None or c[1] == args.tool)
              and (args.outfit is None or c[2] == args.outfit)]
    if not combos:
        raise StoryError(explain_rejection())
    venue, tool, outfit = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if hero_gender == "girl" else "girl")
    hero = args.hero or resolve_name(hero_gender, rng)
    helper = args.helper or resolve_name(helper_gender, rng, avoid=hero)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        venue=venue, tool=tool, outfit=outfit,
        hero=hero, hero_gender=hero_gender,
        helper=helper, helper_gender=helper_gender,
        parent=parent,
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for v, t, o in asp_valid_combos():
            print(f"  {v:8} {t:10} {o}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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

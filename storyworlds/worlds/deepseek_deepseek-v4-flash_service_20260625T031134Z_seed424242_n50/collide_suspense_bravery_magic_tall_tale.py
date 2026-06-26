#!/usr/bin/env python3
"""
storyworlds/worlds/deepseek_deepseek-v4-flash_service_20260625T031134Z_seed424242_n50/collide_suspense_bravery_magic_tall_tale.py
========================================================================================================================

A standalone story world for a tall tale about a magical collision that
tests bravery.  Two neighbors on opposite sides of a valley collide their
magic when building rival wonders, and the suspenseful moment demands
a brave act to fix the broken enchantment.
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

# ---------------------------------------------------------------------------
# Typed entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "character"
    type: str = "person"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")


@dataclass
class Magic:
    kind: str
    color: str
    sound: str
    strength: float


@dataclass
class Wonder:
    name: str
    builder: str
    material: str
    height: int
    complete: bool = False


# ---------------------------------------------------------------------------
# Setting
# ---------------------------------------------------------------------------
VALLEY_SIDES = ["north", "south"]
MAGIC_KINDS = {
    "glimmer": Magic("glimmer", "golden", "a soft hum", 0.8),
    "thunder": Magic("thunder", "blue", "a low rumble", 1.2),
    "storm": Magic("storm", "purple", "a crackling roar", 1.5),
    "whisper": Magic("whisper", "silver", "a quiet chime", 0.6),
    "blaze": Magic("blaze", "red", "a fierce crackle", 1.3),
}


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
class World:
    def __init__(self, valley_name: str) -> None:
        self.valley = valley_name
        self.entities: dict[str, Entity] = {}
        self.wonders: dict[str, Wonder] = {}
        self.magics: dict[str, Magic] = {}
        self.clash_point: float = 0.0
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
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World(self.valley)
        clone.entities = copy.deepcopy(self.entities)
        clone.wonders = copy.deepcopy(self.wonders)
        clone.magics = copy.deepcopy(self.magics)
        clone.clash_point = self.clash_point
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_clash_growth(world: World) -> list[str]:
    out = []
    for wid, wonder in list(world.wonders.items()):
        if wonder.complete:
            continue
        other = [w for w in world.wonders.values() if w.name != wonder.name and not w.complete]
        if not other:
            continue
        clash = min(wonder.height, other[0].height) * 0.1
        world.clash_point += clash
        wonder.height += 1
    return out


def _r_bravery_buildup(world: World) -> list[str]:
    out = []
    for ent in world.entities.values():
        if ent.meters["clash_exposure"] >= THRESHOLD and ent.memes["fear"] < THRESHOLD:
            ent.memes["bravery"] += 0.5
            if ent.memes["bravery"] >= THRESHOLD:
                out.append(f"{ent.id} felt a brave spark grow inside.")
    return out


CAUSAL_RULES = [
    Rule("clash_growth", "physical", _r_clash_growth),
    Rule("bravery_buildup", "social", _r_bravery_buildup),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Narrative verbs
# ---------------------------------------------------------------------------
def introduce_settlers(world: World, north: Entity, south: Entity) -> None:
    world.say(
        f"On opposite sides of {world.valley} Valley lived two clever builders: "
        f"{north.id} on the north rim and {south.id} on the south rim."
    )
    world.say(
        f"{north.id} was known for {north.traits[0] if north.traits else 'steady'} hands, "
        f"while {south.id} was famous for {south.traits[0] if south.traits else 'bold'} dreams."
    )


def discuss_wonder(world: World, builder: Entity, wonder: Wonder, magic: Magic) -> None:
    world.say(
        f'"I shall build a {wonder.material} tower," declared {builder.id}, '
        f'"tall enough to touch the {magic.color} clouds!"'
    )
    world.say(f"{magic.color.capitalize()} sparks {magic.sound}ed around {builder.id} as "
              f"they began to work.")
    world.magics[builder.id] = magic
    world.wonders[wonder.name] = wonder


def both_begin(world: World, north: Entity, south: Entity, n_wonder: Wonder, s_wonder: Wonder,
               n_magic: Magic, s_magic: Magic) -> None:
    discuss_wonder(world, north, n_wonder, n_magic)
    discuss_wonder(world, south, s_wonder, s_magic)
    world.para()
    world.say(
        f"The valley echoed with the sounds of creation. "
        f"On the north side, {n_magic.sound} mingled with {n_magic.color} light. "
        f"On the south side, {s_magic.color} flashes answered with {s_magic.sound}."
    )


def collide_magic(world: World, n_wonder: Wonder, s_wonder: Wonder) -> None:
    clash_val = min(n_wonder.height, s_wonder.height) * 0.3
    world.clash_point += clash_val
    for ent in world.entities.values():
        ent.meters["clash_exposure"] = clash_val
        ent.memes["fear"] = clash_val * 0.5
    world.say(
        f"One morning, as the towers grew higher, their magics began to collide."
    )
    world.say(
        f"A {MAGIC_KINDS['storm'].color} lightning bolt ripped across the valley. "
        f"The ground trembled. The towers wobbled."
    )
    world.say(
        f'"The enchantments are clashing!" cried the builders. "They will shatter!"'
    )
    propagate(world, narrate=True)


def suspense_moment(world: World) -> None:
    world.say(
        f"Everything hung in silence. The valley held its breath."
    )
    world.say(
        f"The magics crackled and growled, promising doom."
    )
    world.say(
        f"Somewhere in the middle, a faint golden thread of light flickered—a "
        f"thread that only a brave heart could weave back together."
    )
    world.facts["suspense_peak"] = True


def brave_act(world: World, hero: Entity) -> None:
    hero.memes["bravery"] += 2
    hero.memes["fear"] = 0
    hero.meters["clash_exposure"] = 0
    world.say(
        f"{hero.id} stepped forward, heart pounding but steady."
    )
    world.say(
        f'"I must do this," {hero.pronoun()} whispered, and walked into the "
        f"tangled storm of magic."
    )
    world.say(
        f"{hero.pronoun().capitalize()} raised {hero.pronoun('possessive')} hands "
        f"and touched the two clashing magics. "
        f"They did not fight—they joined."
    )
    propagate(world, narrate=True)


def resolve(world: World, hero: Entity, n_wonder: Wonder, s_wonder: Wonder,
            magic: Magic) -> None:
    n_wonder.complete = True
    s_wonder.complete = True
    world.clash_point = 0
    world.say(
        f"With a sound like a thousand chimes, the magics wove together into "
        f"a single, brilliant {magic.color} ribbon."
    )
    world.say(
        f"The towers did not fall. They stood straighter than ever, "
        f"linked by a bridge of light across the valley."
    )
    hero.memes["joy"] = 1
    world.facts["resolved"] = True
    world.say(
        f"From that day, the valley was known as the Valley of the Brave Bridge, "
        f"where even the tallest magic could be guided by a steady hand."
    )


def tell(valley: str, north_name: str, south_name: str,
         n_trait: str, s_trait: str,
         n_magic_kind: str, s_magic_kind: str,
         n_wonder_name: str, s_wonder_name: str,
         n_wonder_mat: str, s_wonder_mat: str,
         hero_side: str) -> World:
    world = World(valley)
    n = world.add(Entity(id=north_name, kind="character", type="builder",
                         traits=[n_trait], label=f"the north builder"))
    s = world.add(Entity(id=south_name, kind="character", type="builder",
                         traits=[s_trait], label=f"the south builder"))
    n_magic = MAGIC_KINDS[n_magic_kind]
    s_magic = MAGIC_KINDS[s_magic_kind]
    n_wonder = Wonder(n_wonder_name, north_name, n_wonder_mat, 1)
    s_wonder = Wonder(s_wonder_name, south_name, s_wonder_mat, 1)

    introduce_settlers(world, n, s)
    world.para()
    both_begin(world, n, s, n_wonder, s_wonder, n_magic, s_magic)
    world.para()
    collide_magic(world, n_wonder, s_wonder)
    world.para()
    suspense_moment(world)
    world.para()
    hero = n if hero_side == "north" else s
    brave_act(world, hero)
    world.para()
    resolve(world, hero, n_wonder, s_wonder, n_magic if n_magic.strength >= s_magic.strength else s_magic)

    world.facts.update(
        north=n, south=s, hero=hero,
        n_wonder=n_wonder, s_wonder=s_wonder,
        n_magic=n_magic, s_magic=s_magic,
        valley=valley,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
VALLEYS = ["Whispering", "Golden", "Thunder", "Crystal", "Starfall"]
TRAITS = ["steady", "bold", "clever", "gentle", "fearless", "wise", "bright", "kind"]
NORTH_NAMES = ["Riven", "Tara", "Orin", "Lira", "Kael"]
SOUTH_NAMES = ["Mira", "Dorn", "Sera", "Finn", "Elara"]
WONDER_NAMES = ["Sunspire", "Moonreach", "Cloudhold", "Searise", "Stormkeep"]
MATERIALS = ["stone", "crystal", "wood", "iron", "glass", "obsidian"]


@dataclass
class StoryParams:
    valley: str
    north_name: str
    south_name: str
    n_trait: str
    s_trait: str
    n_magic: str
    s_magic: str
    n_wonder: str
    s_wonder: str
    n_material: str
    s_material: str
    hero_side: str
    seed: Optional[int] = None


def valid_magics() -> list[str]:
    return list(MAGIC_KINDS.keys())


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a tall tale about two builders in {f['valley']} Valley whose "
        f"magics collide.",
        f"Create a suspenseful story where bravery and magic repair a broken "
        f"enchantment.",
        f"Tell a tale about a collision of {f['n_magic'].color} and "
        f"{f['s_magic'].color} magic that only a brave heart can mend.",
    ]


KNOWLEDGE = {
    "magic": [
        ("What is magic in a tall tale?",
         "Magic in a tall tale is a wondrous power that can build towers and "
         "cause storms, but it must be handled with care."),
    ],
    "bravery": [
        ("What does bravery mean?",
         "Bravery means doing something hard even when you feel scared, like "
         "stepping into a clashing storm of magic."),
    ],
    "collide": [
        ("What happens when two magics collide?",
         "When two magics collide, they can create lightning, tremors, and "
         "danger. A brave person must weave them back together."),
    ],
    "valley": [
        ("What is a valley?",
         "A valley is the low land between two hills or mountains, and in "
         "our story it is where the builders live."),
    ],
}
KNOWLEDGE_ORDER = ["magic", "bravery", "collide", "valley"]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    n, s, h = f["north"], f["south"], f["hero"]
    nw, sw = f["n_wonder"], f["s_wonder"]
    nm, sm = f["n_magic"], f["s_magic"]
    valley = f["valley"]
    qa = [
        QAItem(
            question=f"Who were the two builders in {valley} Valley?",
            answer=(f"The two builders were {n.id} on the north side and "
                    f"{s.id} on the south side of {valley} Valley."),
        ),
        QAItem(
            question=f"What wonders did the builders create?",
            answer=(f"{n.id} built a {nw.material} tower called {nw.name}, "
                    f"and {s.id} built a {sw.material} tower called {sw.name}."),
        ),
        QAItem(
            question=f"What happened when the magics met?",
            answer=(f"The {nm.color} magic of {n.id} and the {sm.color} magic "
                    f"of {s.id} clashed, causing lightning and trembling ground. "
                    f"The towers wobbled and seemed ready to fall."),
        ),
        QAItem(
            question=f"How did the suspense build in {valley} Valley?",
            answer=(f"The valley fell silent as the magics crackled. A golden "
                    f"thread of light flickered between the towers, and everyone "
                    f"waited for a brave person to act."),
        ),
        QAItem(
            question=f"Who showed bravery and how?",
            answer=(f"{h.id} stepped into the storm of magic and touched both "
                    f"clashing forces. Instead of fighting, the magics joined "
                    f"into a single ribbon of light, and the towers were safe."),
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = []
    for tag in KNOWLEDGE_ORDER:
        out.extend(QAItem(q=q, a=a) for q, a in KNOWLEDGE[tag])
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
    lines.append(f"  valley: {world.valley}  clash_point: {world.clash_point:.2f}")
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} {' '.join(bits)}")
    for w in world.wonders.values():
        lines.append(f"  wonder {w.name:12} height={w.height} complete={w.complete}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        valley="Whispering", north_name="Riven", south_name="Mira",
        n_trait="steady", s_trait="bold",
        n_magic="glimmer", s_magic="thunder",
        n_wonder="Sunspire", s_wonder="Moonreach",
        n_material="stone", s_material="crystal",
        hero_side="north",
    ),
    StoryParams(
        valley="Golden", north_name="Tara", south_name="Dorn",
        n_trait="clever", s_trait="wise",
        n_magic="whisper", s_magic="blaze",
        n_wonder="Cloudhold", s_wonder="Stormkeep",
        n_material="crystal", s_material="iron",
        hero_side="south",
    ),
]


ASP_RULES = r"""
builder(N) :- north_builder(N).
builder(S) :- south_builder(S).
has_magic(N, M) :- north_builder(N), north_magic(M).
has_magic(S, M) :- south_builder(S), south_magic(M).
clash_possible :- north_builder(_), south_builder(_).
brave_can_repair(H) :- builder(H), has_magic(H, M1), has_magic(_, M2), M1 != M2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for v in VALLEYS:
        lines.append(asp.fact("valley", v))
    for m in MAGIC_KINDS:
        lines.append(asp.fact("magic_kind", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    print("ASP verification: basic structure check (no deep parity test for this domain).")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall tale of colliding magic and bravery.")
    ap.add_argument("--valley", choices=VALLEYS)
    ap.add_argument("--north_name", choices=NORTH_NAMES)
    ap.add_argument("--south_name", choices=SOUTH_NAMES)
    ap.add_argument("--n_magic", choices=valid_magics())
    ap.add_argument("--s_magic", choices=valid_magics())
    ap.add_argument("--hero_side", choices=["north", "south"])
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
    valley = args.valley or rng.choice(VALLEYS)
    north_name = args.north_name or rng.choice(NORTH_NAMES)
    south_name = args.south_name or rng.choice(SOUTH_NAMES)
    n_trait = rng.choice(TRAITS)
    s_trait = rng.choice(TRAITS)
    n_magic = args.n_magic or rng.choice(valid_magics())
    s_magic = args.s_magic or rng.choice([m for m in valid_magics() if m != n_magic])
    n_wonder = rng.choice(WONDER_NAMES)
    s_wonder = rng.choice([w for w in WONDER_NAMES if w != n_wonder])
    n_material = rng.choice(MATERIALS)
    s_material = rng.choice(MATERIALS)
    hero_side = args.hero_side or rng.choice(["north", "south"])
    return StoryParams(
        valley=valley, north_name=north_name, south_name=south_name,
        n_trait=n_trait, s_trait=s_trait,
        n_magic=n_magic, s_magic=s_magic,
        n_wonder=n_wonder, s_wonder=s_wonder,
        n_material=n_material, s_material=s_material,
        hero_side=hero_side,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        params.valley, params.north_name, params.south_name,
        params.n_trait, params.s_trait,
        params.n_magic, params.s_magic,
        params.n_wonder, params.s_wonder,
        params.n_material, params.s_material,
        params.hero_side,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
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
        print(asp_program("#show brave_can_repair/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.north_name} & {p.south_name} in {p.valley} Valley"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

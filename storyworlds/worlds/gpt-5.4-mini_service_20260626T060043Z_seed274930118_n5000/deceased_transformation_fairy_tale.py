#!/usr/bin/env python3
"""
storyworlds/worlds/deceased_transformation_fairy_tale.py
========================================================

A small fairy-tale storyworld about a child, a deceased loved one, and a gentle
transformation that turns sorrow into a new keepsake.

Seed image:
---
A child brings a faded token from a deceased grandmother to a moonlit glade.
A fairy says the token can be transformed instead of left to wither away.
The child hesitates, then agrees, and the transformed token becomes a bright
living sign of remembrance.

World focus:
- Fairy-tale tone
- A deceased loved one
- A transformation that meaningfully changes the story state
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    transformed: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        feminine = {"girl", "woman", "queen", "mother", "fairy"}
        masculine = {"boy", "man", "king", "father"}
        if self.type in feminine:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in masculine:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    moonlit: bool
    scents: list[str] = field(default_factory=list)


@dataclass
class Transformation:
    id: str
    source_label: str
    result_label: str
    source_phrase: str
    result_phrase: str
    setting_tags: set[str]
    emotional_turn: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Relic:
    id: str
    label: str
    phrase: str
    type: str
    keepsake_of: str
    origin: str
    meaning: str
    worn: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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


@dataclass
class StoryParams:
    setting: str
    transformation: str
    relic: str
    name: str
    age: str
    parent: str
    seed: Optional[int] = None


SETTINGS = {
    "moon_garden": Setting(place="the moon garden", moonlit=True, scents=["jasmine", "dew"]),
    "old_chapel_garden": Setting(place="the old chapel garden", moonlit=False, scents=["roses", "stone"]),
    "hill_glade": Setting(place="the hill glade", moonlit=True, scents=["grass", "clover"]),
}

TRANSFORMATIONS = {
    "ribbon_to_butterfly": Transformation(
        id="ribbon_to_butterfly",
        source_label="faded ribbon",
        result_label="blue butterfly",
        source_phrase="a faded blue ribbon from her grandmother's sewing basket",
        result_phrase="a bright blue butterfly",
        setting_tags={"moon", "garden", "grief"},
        emotional_turn="comfort",
        keyword="butterfly",
        tags={"butterfly", "grief"},
    ),
    "seed_to_tree": Transformation(
        id="seed_to_tree",
        source_label="dry seed",
        result_label="silver sapling",
        source_phrase="a dry seed that her grandmother had once tucked into a pocket",
        result_phrase="a silver sapling with starry leaves",
        setting_tags={"glade", "moon", "memory"},
        emotional_turn="hope",
        keyword="sapling",
        tags={"tree", "hope"},
    ),
    "crown_to_lantern": Transformation(
        id="crown_to_lantern",
        source_label="broken crown",
        result_label="gold lantern",
        source_phrase="a broken little crown from the old story box",
        result_phrase="a warm gold lantern",
        setting_tags={"chapel", "stone", "memory"},
        emotional_turn="steadiness",
        keyword="lantern",
        tags={"lantern", "light"},
    ),
}

RELICS = {
    "ribbon": Relic(
        id="ribbon",
        label="ribbon",
        phrase="a faded blue ribbon from her grandmother's sewing basket",
        type="ribbon",
        keepsake_of="grandmother",
        origin="sewing basket",
        meaning="a soft reminder of careful hands and kind songs",
        worn=True,
    ),
    "seed": Relic(
        id="seed",
        label="seed",
        phrase="a dry seed from her grandmother's pocket",
        type="seed",
        keepsake_of="grandmother",
        origin="pocket",
        meaning="a tiny promise that something could grow",
        worn=False,
    ),
    "crown": Relic(
        id="crown",
        label="crown",
        phrase="a broken little crown from the old story box",
        type="crown",
        keepsake_of="grandmother",
        origin="story box",
        meaning="a reminder that fairy tales can mend hearts",
        worn=False,
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Elena", "Rose", "Ayla", "Mara"]
BOY_NAMES = ["Robin", "Theo", "Ivo", "Finn", "Jasper", "Eli"]
AGES = ["little", "small", "young", "tiny"]
PARENTS = ["mother", "father", "aunt", "uncle"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for t_id, t in TRANSFORMATIONS.items():
            for r_id, r in RELICS.items():
                if t.id == "ribbon_to_butterfly" and r_id != "ribbon":
                    continue
                if t.id == "seed_to_tree" and r_id != "seed":
                    continue
                if t.id == "crown_to_lantern" and r_id != "crown":
                    continue
                if _reasonable(SETTINGS[s], t, r):
                    combos.append((s, t_id, r_id))
    return combos


def _reasonable(setting: Setting, transformation: Transformation, relic: Relic) -> bool:
    if relic.keepsakes_of := relic.keepsake_of:
        pass
    if transformation.id == "ribbon_to_butterfly":
        return setting.moonlit and relic.label == "ribbon"
    if transformation.id == "seed_to_tree":
        return "glade" in setting.place or "moon" in setting.place
    if transformation.id == "crown_to_lantern":
        return "chapel" in setting.place or "stone" in setting.place
    return False


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale storyworld about a deceased loved one and a gentle transformation."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--transformation", choices=TRANSFORMATIONS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("--age", choices=AGES)
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
    if args.setting and args.transformation and args.relic:
        if not _reasonable(SETTINGS[args.setting], TRANSFORMATIONS[args.transformation], RELICS[args.relic]):
            raise StoryError("That setting, relic, and transformation do not fit together in this fairy tale.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.transformation is None or c[1] == args.transformation)
              and (args.relic is None or c[2] == args.relic)]
    if not combos:
        raise StoryError("No valid story matches those choices.")
    setting, transformation, relic = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(
        setting=setting,
        transformation=transformation,
        relic=relic,
        name=name,
        age=args.age or rng.choice(AGES),
        parent=args.parent or rng.choice(PARENTS),
    )


def tell(setting: Setting, transformation: Transformation, relic: Relic, name: str, age: str, parent: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=name, kind="character", type="girl" if name in GIRL_NAMES else "boy"))
    grownup = world.add(Entity(id="Guide", kind="character", type=parent, label=f"her {parent}"))
    fairy = world.add(Entity(id="Fairy", kind="character", type="fairy", label="a moon fairy"))
    keepsake = world.add(Entity(
        id="Relic",
        kind="thing",
        type=relic.type,
        label=relic.label,
        phrase=relic.phrase,
        owner=child.id,
        caretaker=grownup.id,
        worn_by=child.id if relic.worn else None,
    ))
    child.memes["sorrow"] = 1.0
    child.memes["love"] = 1.0
    child.memes["wonder"] = 0.0

    world.say(
        f"{name} was a {age} child who lived near {setting.place}, where the air smelled of "
        f"{', '.join(setting.scents)} and old stories."
    )
    world.say(
        f"{name} still missed the deceased grandmother who had left behind {relic.phrase}. "
        f"It felt like a soft little treasure, but also like a sad one."
    )

    world.para()
    world.say(
        f"One evening, {name} walked into {setting.place} with {child.pronoun('possessive')} "
        f"{parent} and found a moon fairy waiting beside the moss."
    )
    world.say(
        f'The fairy pointed at the {relic.label} and whispered, "This can be transformed, if '
        f'your heart is ready."' 
    )
    child.memes["fear"] += 1.0
    child.memes["wonder"] += 1.0

    world.para()
    world.say(
        f"{name} held the {relic.label} close and hesitated, because keeping it unchanged felt safer "
        f"than letting it become something new."
    )
    world.say(
        f"But the fairy promised that the memory would stay, only the shape would change."
    )
    child.memes["sorrow"] += 0.5
    child.memes["hope"] = 0.0

    world.para()
    if transformation.id == "ribbon_to_butterfly":
        child.memes["hope"] += 1.5
        child.memes["sorrow"] = 0.0
        keepsake.transformed = True
        keepsake.label = transformation.result_label
        keepsake.phrase = transformation.result_phrase
        world.say(
            f"At last, {name} nodded. The fairy touched the faded ribbon with a silver finger, "
            f"and it turned into {transformation.result_phrase}."
        )
        world.say(
            f"The little butterfly settled on {name}'s sleeve, bright as a drop of sky, and the sad ribbon "
            f"was gone without being forgotten."
        )
    elif transformation.id == "seed_to_tree":
        child.memes["hope"] += 1.5
        child.memes["sorrow"] = 0.0
        keepsake.transformed = True
        keepsake.label = transformation.result_label
        keepsake.phrase = transformation.result_phrase
        world.say(
            f"At last, {name} nodded. The fairy tucked the dry seed into the soil, and it rose into "
            f"{transformation.result_phrase}."
        )
        world.say(
            f"The silver leaves trembled in the moonlight, and {name} smiled because the tiny promise had "
            f"become a living thing."
        )
    else:
        child.memes["steadiness"] = 1.5
        child.memes["sorrow"] = 0.0
        keepsake.transformed = True
        keepsake.label = transformation.result_label
        keepsake.phrase = transformation.result_phrase
        world.say(
            f"At last, {name} nodded. The fairy lifted the broken crown, and it glowed into "
            f"{transformation.result_phrase}."
        )
        world.say(
            f"Its warm light shone over the path, and {name} felt the old story box had given back a kinder ending."
        )

    world.facts.update(
        child=child,
        grownup=grownup,
        fairy=fairy,
        relic=keepsake,
        setting=setting,
        transformation=transformation,
        deceased="grandmother",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    c = f["child"]
    t = f["transformation"]
    r = f["relic"]
    return [
        f'Write a short fairy tale for a young child about {c.id} and a {r.label} that is transformed by magic.',
        f"Tell a gentle story where a deceased grandmother's keepsake becomes {t.result_phrase} in {world.setting.place}.",
        f'Write a small fairy tale with a moon fairy, a memory, and the word "{t.keyword}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    relic = f["relic"]
    t = f["transformation"]
    qa = [
        QAItem(
            question=f"What sad thing did {child.id} bring to the fairy in the story?",
            answer=f"{child.id} brought {relic.phrase}. It belonged to {f['deceased']} and felt precious because it kept a memory close.",
        ),
        QAItem(
            question=f"What did the fairy do to the {relic.label}?",
            answer=f"The fairy transformed it into {t.result_phrase}, so the keepsake could stay beautiful in a new shape.",
        ),
        QAItem(
            question=f"How did {child.id} feel when the magic was finished?",
            answer=f"{child.id} felt hopeful and comforted. The child could still remember the deceased grandmother, but the story ended with a bright new sign instead of a sad old one.",
        ),
    ]
    if t.id == "ribbon_to_butterfly":
        qa.append(QAItem(
            question=f"Where did the butterfly rest after the transformation?",
            answer=f"It rested on {child.id}'s sleeve in the moon garden, shining softly like a piece of sky.",
        ))
    elif t.id == "seed_to_tree":
        qa.append(QAItem(
            question=f"What grew from the dry seed?",
            answer=f"A silver sapling with starry leaves grew from the seed, and it made the glade feel alive again.",
        ))
    else:
        qa.append(QAItem(
            question=f"What light did the broken crown become?",
            answer=f"It became a warm gold lantern that lit the path and made the old place feel kinder.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    t = world.facts["transformation"]
    out = [
        QAItem(
            question="What is a fairy in fairy tales?",
            answer="A fairy is a tiny magical being in fairy tales who can help, guide, or cast spells.",
        ),
        QAItem(
            question="Why do people keep keepsakes?",
            answer="People keep keepsakes because they help them remember someone or something they love.",
        ),
    ]
    if "butterfly" in t.tags:
        out.append(QAItem(
            question="What does a butterfly often symbolize in stories?",
            answer="A butterfly often symbolizes change, beauty, and becoming something new.",
        ))
    if "tree" in t.tags:
        out.append(QAItem(
            question="Why are trees important in stories and gardens?",
            answer="Trees give shade, shelter, and a feeling of growing life, so they often stand for strength and hope.",
        ))
    if "lantern" in t.tags:
        out.append(QAItem(
            question="What does a lantern do?",
            answer="A lantern holds a light and helps people see in the dark.",
        ))
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        if e.transformed:
            bits.append("transformed=True")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="moon_garden", transformation="ribbon_to_butterfly", relic="ribbon", name="Mina", age="little", parent="mother"),
    StoryParams(setting="hill_glade", transformation="seed_to_tree", relic="seed", name="Robin", age="young", parent="father"),
    StoryParams(setting="old_chapel_garden", transformation="crown_to_lantern", relic="crown", name="Lila", age="tiny", parent="aunt"),
]


ASP_RULES = r"""
setting(S) :- setting_fact(S).
transformation(T) :- transformation_fact(T).
relic(R) :- relic_fact(R).

valid_story(S,T,R) :- setting(S), transformation(T), relic(R), fit(S,T,R).

fit(moon_garden, ribbon_to_butterfly, ribbon).
fit(hill_glade, seed_to_tree, seed).
fit(old_chapel_garden, crown_to_lantern, crown).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting_fact", sid))
        if s.moonlit:
            lines.append(asp.fact("moonlit", sid))
    for tid, t in TRANSFORMATIONS.items():
        lines.append(asp.fact("transformation_fact", tid))
        for tag in sorted(t.tags):
            lines.append(asp.fact("transformation_tag", tid, tag))
    for rid, r in RELICS.items():
        lines.append(asp.fact("relic_fact", rid))
        lines.append(asp.fact("keepsake_of", rid, r.keepsake_of))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.transformation is None or c[1] == args.transformation)
              and (args.relic is None or c[2] == args.relic)]
    if not combos:
        raise StoryError("No valid fairy-tale combination matches those options.")
    setting, transformation, relic = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(setting=setting, transformation=transformation, relic=relic, name=name, age=args.age or rng.choice(AGES), parent=args.parent or rng.choice(PARENTS))


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], TRANSFORMATIONS[params.transformation], RELICS[params.relic], params.name, params.age, params.parent)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale world with a deceased keepsake and a magical transformation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--transformation", choices=TRANSFORMATIONS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("--age", choices=AGES)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid fairy-tale combos:\n")
        for s, t, r in combos:
            print(f"  {s:18} {t:24} {r}")
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
            header = f"### {p.name}: {p.transformation} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

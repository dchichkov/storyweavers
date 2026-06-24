#!/usr/bin/env python3
"""
A small mythic story world about a stockade, kindness, foreshadowing, and magic.

A seed tale behind this world:
---
Long ago, a village stood beside an old wooden stockade. The stockade had kept
wolves and raiders away for many winters, but now one gatepost had begun to lean.
A child named Lani noticed that the shadows at sunset looked like a broken spear
point across the fence, and the elders said that such signs were never empty.

One dusk, Lani found a tired little fox with a thorn in its paw near the ditch.
Instead of chasing it off, Lani washed the paw and shared a crust of bread.
That night, the fox returned with a blue ember in its mouth. The ember was a
gift from the forest spirits: if the village used it with a gentle hand, it could
mend what was failing; if they used it in anger, it would burn the wood black.

When the storm came, Lani remembered the fox, the leaning post, and the strange
shadow. The child lit the ember only long enough to warm the cracked timber,
and the stockade stood firm again.
"""

from __future__ import annotations

import argparse
import copy
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str = "the village stockade"
    affords: set[str] = field(default_factory=set)


@dataclass
class Omen:
    id: str
    sign: str
    meaning: str
    foreshadow: str
    danger: str
    reveal: str


@dataclass
class Magic:
    id: str
    label: str
    phrase: str
    method: str
    effect: str
    cost: str
    virtue: str
    omen_id: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    weather: str = ""

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.weather = self.weather
        return clone


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    elder_name: str
    omen: str
    magic: str
    seed: Optional[int] = None


SETTINGS = {
    "stockade": Setting(place="the village stockade", affords={"repair", "watch"}),
    "gate": Setting(place="the gate of the stockade", affords={"repair", "watch"}),
    "wall": Setting(place="the stockade wall", affords={"repair", "watch"}),
}

OMENS = {
    "shadow_spear": Omen(
        id="shadow_spear",
        sign="a shadow like a broken spear",
        meaning="the wall would crack where it leaned",
        foreshadow="the shadow at sunset had pointed to the weakest post",
        danger="the leaning gatepost could split in the storm",
        reveal="the omen had been warning them all along",
    ),
    "owl_three": Omen(
        id="owl_three",
        sign="three owl calls from the dark firs",
        meaning="a hard wind was coming",
        foreshadow="the elders heard the calls and grew quiet",
        danger="the storm could shake loose old boards",
        reveal="the calls had spoken before the clouds arrived",
    ),
    "ripple_still": Omen(
        id="ripple_still",
        sign="ripples in a bucket of still water",
        meaning="magic was near the stockade",
        foreshadow="the water moved before anyone touched it",
        danger="the old wood could answer magic badly if met with anger",
        reveal="the water had shown the blue ember would soon appear",
    ),
}

MAGICS = {
    "ember": Magic(
        id="ember",
        label="a blue ember",
        phrase="a blue ember warm as a held breath",
        method="lift the ember gently and speak kindly to the wood",
        effect="the cracked timber knit itself tight and strong",
        cost="it would blacken the wood if used in anger",
        virtue="kindness",
        omen_id="shadow_spear",
    ),
    "thread": Magic(
        id="thread",
        label="silver thread",
        phrase="silver thread that shone like moonlight",
        method="loop the thread around the broken boards and tie it with care",
        effect="the split boards pulled back together",
        cost="it would tangle if pulled too hard",
        virtue="foreshadowing",
        omen_id="owl_three",
    ),
    "seal": Magic(
        id="seal",
        label="a leaf seal",
        phrase="a leaf seal stamped with green light",
        method="press the seal to the post and whisper thanks",
        effect="the wood drank the light and stood steady",
        cost="it would fail if the helper was unkind",
        virtue="magic",
        omen_id="ripple_still",
    ),
}

HEROES = [
    ("Lani", "girl"),
    ("Miro", "boy"),
    ("Tala", "girl"),
    ("Oren", "boy"),
]

ELDERS = ["grandmother", "grandfather", "elder", "watcher"]


def resolve_magic(omen: Omen, magic: Magic) -> bool:
    return omen.id == magic.omen_id


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for omen in OMENS:
            for magic in MAGICS:
                if resolve_magic(OMENS[omen], MAGICS[magic]):
                    combos.append((place, omen, magic))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic stockade story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--omen", choices=OMENS)
    ap.add_argument("--magic", choices=MAGICS)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=ELDERS)
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


def omen_text(omen: Omen) -> str:
    return omen.sign


def predict(world: World, magic: Magic) -> dict:
    sim = world.copy()
    wall = sim.get("stockade")
    if magic.virtue != "kindness":
        wall.meters["ruined"] = 1.0
    else:
        wall.meters["mended"] = 1.0
    return {"mended": wall.meters.get("mended", 0.0) >= THRESHOLD}


def tell(setting: Setting, omen: Omen, magic: Magic, hero_name: str, hero_type: str, elder_name: str) -> World:
    world = World(setting)
    world.weather = "storm"

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["small", "kind"]))
    elder = world.add(Entity(id="elder", kind="character", type=elder_name, label=f"the {elder_name}"))
    wall = world.add(Entity(id="stockade", type="stockade", label="stockade", phrase="old wooden stockade"))
    fox = world.add(Entity(id="fox", kind="character", type="fox", label="a little fox"))

    world.say(f"Long ago, {hero.id} lived beside {setting.place}.")
    world.say(f"The old stockade had kept the village safe for many winters, yet one post leaned a little.")
    world.say(f"At sunset, {omen_text(omen)}.")
    world.say(f"The elders whispered that {omen.foreshadow}, and {hero.id} remembered the sign.")

    world.para()
    world.say(f"One evening, {hero.id} found {fox.label} near the ditch with a thorn in {fox.pronoun('possessive')} paw.")
    world.say(f"Instead of chasing {fox.it()} away, {hero.id} washed the paw and shared a crust of bread.")
    fox.memes["relief"] = fox.memes.get("relief", 0.0) + 1
    hero.memes["kindness"] = hero.memes.get("kindness", 0.0) + 1
    world.say(f"The little fox blinked as if kindness had opened a door in the dark.")

    world.para()
    world.say(f"That night, {fox.label_word if fox.label else 'the fox'} returned with {magic.phrase}.")
    world.say(f"The fox seemed to know that {magic.effect} if the gift was used with care.")
    world.say(f"But {magic.cost}.")
    world.say(f"When the storm rose, {omen.danger}.")

    world.para()
    world.say(f"{hero.id} did not rush. {hero.id} remembered {omen.foreshadow} and chose {magic.virtue} over fear.")
    if magic.id == "ember":
        world.say(f"{hero.id} lifted the ember gently and spoke softly to the cracked post.")
    elif magic.id == "thread":
        world.say(f"{hero.id} looped the silver thread around the split boards and tied it with care.")
    else:
        world.say(f"{hero.id} pressed the leaf seal to the leaning post and whispered thanks to the wood.")
    world.say(f"Then {magic.effect}.")
    wall.meters["mended"] = 1.0
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1
    elder.memes["relief"] = elder.memes.get("relief", 0.0) + 1
    world.say(f"The stockade stood firm again, and the village slept behind it like a child behind a steady hand.")

    world.facts.update(hero=hero, elder=elder, wall=wall, omen=omen, magic=magic, fox=fox)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short myth about {f['hero'].id} and {f['omren'].sign if 'omren' in f else f['omen'].sign} near a stockade.",
        f"Tell a gentle mythic story where {f['hero'].id} shows kindness, notices a warning sign, and uses {f['magic'].label} to save a village wall.",
        f"Write a child-friendly myth about a stockade, a fox, and magic that works only when the helper is kind.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    omen = f["omen"]
    magic = f["magic"]
    elder = f["elder"]
    return [
        QAItem(
            question=f"What sign did {hero.id} notice near the stockade?",
            answer=f"{hero.id} noticed {omen.sign}. That was a foreshadowing sign, because it hinted that the stockade might need help before the storm."
        ),
        QAItem(
            question=f"Why did the elders worry before the storm?",
            answer=f"The elders worried because {omen.foreshadow}, and they believed the sign was warning them that trouble was coming."
        ),
        QAItem(
            question=f"How did {hero.id} help the fox?",
            answer=f"{hero.id} washed the fox's paw and shared bread instead of chasing it away, which showed kindness."
        ),
        QAItem(
            question=f"What magic did {hero.id} use on the stockade?",
            answer=f"{hero.id} used {magic.phrase}, and because the help was gentle, {magic.effect}."
        ),
        QAItem(
            question=f"How did the story end for the village?",
            answer=f"The stockade stood firm again, and the village was safe behind it. The ending proved that kindness and careful magic could mend what was failing."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a stockade?",
            answer="A stockade is a strong fence or wall made of upright wooden posts. It can help protect a village or camp."
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a clue that hints something important may happen later in the story."
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle and helpful to others, especially when they are hurt or worried."
        ),
        QAItem(
            question="What is magic in a myth?",
            answer="In a myth, magic is a special power or gift that can change the world in surprising ways."
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
omen_magic(O, M) :- omen(O), magic(M), omen_id(M, O).

valid_story(P, O, M) :- setting(P), omen(O), magic(M), omen_magic(O, M).

mended_after_magic(stockade) :- valid_story(_, _, M), virtue(M, kindness).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
    for oid, o in OMENS.items():
        lines.append(asp.fact("omen", oid))
        lines.append(asp.fact("omen_sign", oid, o.sign))
        lines.append(asp.fact("omen_id", oid, oid))
    for mid, m in MAGICS.items():
        lines.append(asp.fact("magic", mid))
        lines.append(asp.fact("virtue", mid, m.virtue))
        lines.append(asp.fact("omen_id", mid, m.omen_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.omen and args.magic and not resolve_magic(OMENS[args.omen], MAGICS[args.magic]):
        raise StoryError("That omen does not belong with that magic in this world.")
    filtered = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.omen is None or c[1] == args.omen)
        and (args.magic is None or c[2] == args.magic)
    ]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    place, omen, magic = rng.choice(sorted(filtered))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice([n for n, t in HEROES if t == hero_type])
    elder = args.elder or rng.choice(ELDERS)
    return StoryParams(place=place, hero_name=hero_name, hero_type=hero_type, elder_name=elder, omen=omen, magic=magic)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], OMENS[params.omen], MAGICS[params.magic], params.hero_name, params.hero_type, params.elder_name)
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, omen, magic) combos:\n")
        for place, omen, magic in triples:
            print(f"  {place:10} {omen:14} {magic}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("stockade", "Lani", "girl", "elder", "shadow_spear", "ember"),
            StoryParams("gate", "Miro", "boy", "grandmother", "owl_three", "thread"),
            StoryParams("wall", "Tala", "girl", "watcher", "ripple_still", "seal"),
        ]
        samples = [generate(p) for p in curated]
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

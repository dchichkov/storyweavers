#!/usr/bin/env python3
"""
storyworlds/worlds/exuberant_obsession_suspense_folk_tale.py
=============================================================

A small folk-tale story world about a child, an old household charm, and the
suspense of following a warning too closely. The generated stories keep the
tone simple and child-facing while still driven by a simulated world state with
physical meters and emotional memes.

Seed tale shape:
- A village child becomes exuberant about a local charm.
- That excitement turns into obsession with an object or place that should be
  left alone at dusk.
- Suspense grows as a helper tries to keep the child safe.
- The ending proves what changed in the world: a token found, a door shut, a
  fear eased, or a rule learned.

The storyworld contract requires:
- StoryParams, build_parser, resolve_params, generate, emit, main
- QAItem / StoryError / StorySample from storyworlds.results
- lazy import of storyworlds.asp inside ASP helpers
- a Python reasonableness gate and inline ASP twin
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass
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
    place: str = ""
    afraid_of_dark: bool = False
    secret: bool = False
    meters: dict[str, float] = None
    memes: dict[str, float] = None
    attrs: dict[str, str] = None

    def __post_init__(self):
        if self.meters is None:
            self.meters = {"discovered": 0.0, "missing": 0.0, "blocked": 0.0, "ruined": 0.0}
        if self.memes is None:
            self.memes = {"joy": 0.0, "fear": 0.0, "obsession": 0.0, "relief": 0.0, "caution": 0.0}
        if self.attrs is None:
            self.attrs = {}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    dusk_unsafe: bool
    hidden: bool = False
    tags: set[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = set()


@dataclass
class Charm:
    id: str
    label: str
    phrase: str
    guarded_by: str
    can_spoil: bool
    tags: set[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = set()


@dataclass
class Keeper:
    id: str
    label: str
    warning: str
    fix: str
    tags: set[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = set()


@dataclass
class StoryParams:
    village: str
    place: str
    charm: str
    keeper: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, village: str) -> None:
        self.village = village
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        import copy
        w = World(self.village)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


VILLAGES = {
    "stonebridge": "Stonebridge",
    "willowmere": "Willowmere",
    "pinehollow": "Pinehollow",
}

PLACES = {
    "mill": Place("mill", "the old mill", dusk_unsafe=True, hidden=False, tags={"wood", "dusk"}),
    "bridge": Place("bridge", "the rope bridge", dusk_unsafe=True, hidden=False, tags={"river", "dusk"}),
    "granary": Place("granary", "the grain loft", dusk_unsafe=True, hidden=True, tags={"grain", "dark"}),
    "well": Place("well", "the stone well", dusk_unsafe=False, hidden=True, tags={"water", "echo"}),
}

CHARMS = {
    "silver_bell": Charm("silver_bell", "a silver bell", "silver bell", "keeper", can_spoil=False, tags={"bell", "song"}),
    "red_ribbon": Charm("red_ribbon", "a red ribbon", "red ribbon", "keeper", can_spoil=True, tags={"cloth", "luck"}),
    "lantern_key": Charm("lantern_key", "a lantern key", "lantern key", "keeper", can_spoil=False, tags={"key", "light"}),
    "honey_cake": Charm("honey_cake", "a honey cake", "honey cake", "keeper", can_spoil=True, tags={"sweet", "gift"}),
}

KEEPERS = {
    "grandmother": Keeper("grandmother", "grandmother", "Do not go there at dusk.", "close the door and wait for morning", tags={"family"}),
    "old_watchman": Keeper("old_watchman", "old watchman", "Listen for the bell, not the shadows.", "bring a lantern and walk together", tags={"watch", "night"}),
    "aunt": Keeper("aunt", "aunt", "That place keeps secrets after sunset.", "leave a small offering and turn back", tags={"family"}),
}

GIRL_NAMES = ["Mara", "Nina", "Lina", "Sera", "Tilda", "Wren"]
BOY_NAMES = ["Toma", "Evan", "Rudi", "Pavel", "Niko", "Darin"]
HELPERS = ["older sibling", "neighbor child", "kind cousin"]

CURATED = [
    StoryParams(village="stonebridge", place="mill", charm="silver_bell", keeper="grandmother", hero_name="Mara", hero_type="girl", helper_name="Nina", helper_type="girl"),
    StoryParams(village="willowmere", place="bridge", charm="lantern_key", keeper="old_watchman", hero_name="Toma", hero_type="boy", helper_name="Rudi", helper_type="boy"),
    StoryParams(village="pinehollow", place="granary", charm="red_ribbon", keeper="aunt", hero_name="Sera", hero_type="girl", helper_name="Evan", helper_type="boy"),
]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for village in VILLAGES:
        for place in PLACES:
            for charm in CHARMS:
                for keeper in KEEPERS:
                    if is_reasonable(place, charm, keeper):
                        combos.append((village, place, charm, keeper))
    return combos


def is_reasonable(place_id: str, charm_id: str, keeper_id: str) -> bool:
    place = PLACES[place_id]
    charm = CHARMS[charm_id]
    keeper = KEEPERS[keeper_id]
    if not place.dusk_unsafe:
        return False
    if charm.can_spoil and place_id == "bridge":
        return False
    if keeper_id == "old_watchman" and charm_id == "honey_cake":
        return False
    return True


def asp_facts() -> str:
    import asp
    lines = []
    for vid in VILLAGES:
        lines.append(asp.fact("village", vid))
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.dusk_unsafe:
            lines.append(asp.fact("dusk_unsafe", pid))
    for cid, c in CHARMS.items():
        lines.append(asp.fact("charm", cid))
        if c.can_spoil:
            lines.append(asp.fact("can_spoil", cid))
    for kid, k in KEEPERS.items():
        lines.append(asp.fact("keeper", kid))
    return "\n".join(lines)


ASP_RULES = r"""
reasonable(V,P,C,K) :- village(V), place(P), charm(C), keeper(K), dusk_unsafe(P), not bad_combo(P,C,K).
bad_combo(bridge,honey_cake,_) .
bad_combo(bridge,red_ribbon,_) .
bad_combo(_,honey_cake,old_watchman) .
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reasonable/4."))
    return sorted(set(asp.atoms(model, "reasonable")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: a folk tale of exuberance, obsession, and suspense.")
    ap.add_argument("--village", choices=VILLAGES)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--keeper", choices=KEEPERS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
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
              if (args.village is None or c[0] == args.village)
              and (args.place is None or c[1] == args.place)
              and (args.charm is None or c[2] == args.charm)
              and (args.keeper is None or c[3] == args.keeper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    village, place, charm, keeper = rng.choice(sorted(combos))
    if args.name:
        hero_name = args.name
        hero_type = "girl" if hero_name in GIRL_NAMES else "boy"
    else:
        hero_type = rng.choice(["girl", "boy"])
        hero_name = rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    helper_name = args.helper or rng.choice([h for h in GIRL_NAMES + BOY_NAMES if h != hero_name])
    helper_type = "girl" if helper_name in GIRL_NAMES else "boy"
    return StoryParams(village=village, place=place, charm=charm, keeper=keeper,
                       hero_name=hero_name, hero_type=hero_type,
                       helper_name=helper_name, helper_type=helper_type)


def predict(world: World) -> dict:
    return {
        "missing": world.get("charm").meters["missing"] > 0,
        "blocked": world.get("helper").meters["blocked"] > 0,
    }


def tell(params: StoryParams) -> World:
    if params.place not in PLACES or params.charm not in CHARMS or params.keeper not in KEEPERS:
        raise StoryError("Invalid story parameters.")
    if not is_reasonable(params.place, params.charm, params.keeper):
        raise StoryError("This combination does not make a believable folk tale.")
    world = World(VILLAGES[params.village])
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero_name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type, label=params.helper_name))
    place = world.add(Entity(id="place", type="place", label=PLACES[params.place].label))
    charm = world.add(Entity(id="charm", type="charm", label=CHARMS[params.charm].label))
    keeper = world.add(Entity(id="keeper", kind="character", type="adult", label=KEEPERS[params.keeper].label))
    hero.memes["joy"] = 1.0
    hero.memes["obsession"] = 0.0
    helper.memes["caution"] = 1.0
    world.facts["params"] = params
    world.facts["place"] = place
    world.facts["charm"] = charm
    world.facts["keeper"] = keeper
    world.facts["hero"] = hero
    world.facts["helper"] = helper
    world.say(f"In {world.village}, {params.hero_name} was exuberant whenever the folk stories mentioned {CHARMS[params.charm].phrase}.")
    hero.memes["obsession"] += 1.0
    world.say(f"Before long, {params.hero_name}'s exuberant grin turned into obsession, and {params.hero_name} kept thinking about {PLACES[params.place].label}.")
    world.para()
    world.say(f"At dusk, {params.hero_name} and {params.helper_name} went near {PLACES[params.place].label}, but the shadows felt long and still.")
    world.say(f"Then {KEEPERS[params.keeper].label} warned, \"{KEEPERS[params.keeper].warning}\"")
    helper.meters["blocked"] = 1.0
    if params.place == "mill":
        world.say(f"The old boards creaked, and every creak made the night feel a little deeper.")
    elif params.place == "bridge":
        world.say("Below the rope bridge, the river whispered under the dark like a hidden tune.")
    else:
        world.say(f"The place looked harmless by day, but by dusk it kept its secrets close.")
    world.para()
    if params.charm == "silver_bell":
        world.say(f"{params.hero_name} almost reached for the silver bell, but {params.helper_name} held up a hand and led the way back.")
        hero.memes["fear"] += 0.5
        hero.memes["relief"] += 1.0
        world.say(f"Together they chose {KEEPERS[params.keeper].fix}, and the sound of the bell stayed in the story instead of the dark.")
        charm.meters["discovered"] = 1.0
    elif params.charm == "lantern_key":
        world.say(f"{params.hero_name} kept staring at the lantern key, yet {params.helper_name} noticed how the gate shut slowly in the wind.")
        world.say(f"They hurried away before the dusk could swallow the path, and {KEEPERS[params.keeper].fix} gave them a safer light for the walk home.")
        hero.memes["fear"] += 0.5
        hero.memes["relief"] += 1.0
        charm.meters["discovered"] = 1.0
    elif params.charm == "red_ribbon":
        world.say(f"{params.hero_name} wanted the red ribbon so badly that the want itself felt like a drum in the chest.")
        world.say(f"But {params.helper_name} untied a smaller ribbon from a pouch, and {KEEPERS[params.keeper].fix} kept the old one safe where it belonged.")
        hero.memes["obsession"] = 0.0
        hero.memes["relief"] += 1.0
        charm.meters["missing"] = 0.0
    else:
        world.say(f"{params.hero_name} thought the honey cake might be waiting in the dark, but {params.helper_name} reminded {params.hero_name} that some gifts are not for chasing.")
        world.say(f"They shared a crumb of bread instead, and {KEEPERS[params.keeper].fix} made the evening gentle again.")
        hero.memes["obsession"] = 0.0
        hero.memes["relief"] += 1.0
    world.para()
    world.say(f"By the time the moon climbed high, {params.hero_name} was no longer chasing a shadow; {params.hero_name} was walking home with {params.helper_name}, light-hearted and calm.")
    world.say(f"In that quiet ending, the village felt safe, and the story kept its secret places for morning.")
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a short folk tale for a child that includes the words "exuberant" and "obsession" and features suspense at dusk.',
        f"Tell a simple village story where {p.hero_name} becomes exuberant about {CHARMS[p.charm].phrase} and learns to stop an obsession at {PLACES[p.place].label}.",
        f'Write a suspenseful folk tale in which a warning from {KEEPERS[p.keeper].label} helps two children leave a dark place before night gets too close.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    charm = world.facts["charm"]
    place = world.facts["place"]
    keeper = world.facts["keeper"]
    return [
        QAItem(
            question=f"Who was the story about in {VILLAGES[p.village]}?",
            answer=f"It was about {p.hero_name} and {p.helper_name}. {p.hero_name} started out exuberant, and the helper stayed close when the night turned suspenseful.",
        ),
        QAItem(
            question=f"Why did {p.hero_name} go near {place.label} at dusk?",
            answer=f"{p.hero_name} had become obsessed with {charm.label}. That strong wanting pulled {hero.pronoun()} toward the place even though it was getting dark.",
        ),
        QAItem(
            question=f"What did {keeper.label} do to keep the children safe?",
            answer=f"{keeper.label.capitalize()} gave a warning and sent them back before the darkness deepened. That helped the suspense end safely instead of turning into trouble.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    return [
        QAItem(
            question="What does exuberant mean?",
            answer="Exuberant means very full of happy energy. A child who is exuberant may bounce, grin, and speak as if joy is spilling over.",
        ),
        QAItem(
            question="What does obsession mean?",
            answer="Obsession means thinking about one thing over and over so much that it is hard to think about anything else. It can make a person follow a want even when they should stop.",
        ),
        QAItem(
            question="Why is dusk suspenseful in a folk tale?",
            answer="Dusk is suspenseful because the light fades and familiar paths can seem uncertain. In a folk tale, that makes a warning feel more important.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
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
    out = ["--- world model state ---"]
    for e in world.entities.values():
        out.append(f"  {e.id}: meters={dict(e.meters)} memes={dict(e.memes)} attrs={dict(e.attrs)}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set != clingo_set:
        print("MISMATCH between Python and ASP validity gate.")
        if python_set - clingo_set:
            print("only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("only in asp:", sorted(clingo_set - python_set))
        return 1
    print(f"OK: ASP matches Python gate ({len(python_set)} combos).")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        assert sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        print(f"FAIL: smoke test crashed: {exc}")
        return 1
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show reasonable/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

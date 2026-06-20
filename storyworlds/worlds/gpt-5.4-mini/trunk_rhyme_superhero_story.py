#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/trunk_rhyme_superhero_story.py
===============================================================

A small standalone storyworld for a superhero-style rhyme tale about a heavy
trunk, a brave child hero, and a quick rescue.

The domain is intentionally tiny: a child in costume, a stuck trunk, a worried
helper, and a safe, cheerful rescue. The prose is driven by simulated world
state so the story can vary while still reading like a complete little adventure.
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
SENSE_MIN = 2

HERO_NAMES = ["Nova", "Milo", "Zara", "Rory", "Pip", "Luna", "Bea", "Toby"]
HELPER_NAMES = ["Auntie Joy", "Dad", "Mom", "Uncle Ray", "Grandma"]
SIDEKICK_NAMES = ["Bean", "Spark", "Wiggle", "Dot", "Puff"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
class Scene:
    place: str
    rhyme1: str
    rhyme2: str
    trunk_desc: str
    hero_title: str
    helper_title: str
    goal: str
    ending_image: str


@dataclass
class Risk:
    id: str
    label: str
    place_word: str
    weight: int
    trouble: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Move:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_worry(world: World) -> list[str]:
    out = []
    trunk = world.entities.get("trunk")
    if trunk and trunk.meters["stuck"] >= THRESHOLD and ("worry", "trunk") not in world.fired:
        world.fired.add(("worry", "trunk"))
        for e in world.entities.values():
            if e.role in {"hero", "helper", "sidekick"}:
                e.memes["worry"] += 1
        out.append("__worry__")
    return out


def _r_rescue(world: World) -> list[str]:
    out = []
    trunk = world.entities.get("trunk")
    if trunk and trunk.meters["stuck"] < THRESHOLD and ("rescue", "trunk") not in world.fired:
        world.fired.add(("rescue", "trunk"))
        for e in world.entities.values():
            if e.role in {"hero", "helper", "sidekick"}:
                e.memes["joy"] += 1
        out.append("__rescue__")
    return out


CAUSAL_RULES = [Rule("worry", "social", _r_worry), Rule("rescue", "social", _r_rescue)]


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
        for s in produced:
            world.say(s)
    return produced


def sensible_moves() -> list[Move]:
    return [m for m in MOVES.values() if m.sense >= SENSE_MIN]


def hazard_at_risk(risk: Risk) -> bool:
    return risk.weight >= 1


def enough_power(move: Move, risk: Risk) -> bool:
    return move.power >= risk.weight


def telling_rhyme(a: str, b: str) -> str:
    return f"{a}, {b}"


def _do_move(world: World, risk: Risk, move: Move, narrate: bool = True) -> None:
    trunk = world.get("trunk")
    trunk.meters["stuck"] = 0.0
    trunk.meters["moved"] += 1
    world.facts["move_used"] = move.id
    propagate(world, narrate=narrate)


def predict(world: World, move: Move) -> dict:
    sim = world.copy()
    _do_move(sim, sim.facts["risk"], move, narrate=False)
    return {"opened": sim.get("trunk").meters["stuck"] < THRESHOLD}


def intro(world: World, hero: Entity, sidekick: Entity, scene: Scene) -> None:
    world.say(
        f"Under a bright sky in {scene.place}, {hero.id} wore a cape with pride, "
        f"and {sidekick.id} bobbed along for the ride."
    )
    world.say(
        f"They loved to protect the day in a glittering way, for a hero can help "
        f"and still find time to play."
    )


def show_trunk(world: World, scene: Scene, trunk: Entity) -> None:
    trunk.meters["stuck"] = 1.0
    trunk.memes["mystery"] += 1
    world.say(
        f"Then they spotted a trunk near the old oak tree, {scene.trunk_desc}."
    )
    world.say(
        f"It sat in the grass like a secret in place, and it would not budge no "
        f"matter the tug or the brace."
    )


def want_to_open(world: World, hero: Entity, sidekick: Entity, scene: Scene) -> None:
    hero.memes["curiosity"] += 1
    sidekick.memes["curiosity"] += 1
    world.say(
        f'"Let\'s open it!" said {hero.id}. "We need to see what it stores!"'
    )
    world.say(
        f'"Maybe it holds a costume, or treasure, or scores!" chirped {sidekick.id}.'
    )


def warn(world: World, helper: Entity, hero: Entity, trunk: Entity, risk: Risk) -> None:
    pred = predict(world, MOVES["pull"])
    helper.memes["care"] += 1
    world.facts["predicted_open"] = pred["opened"]
    world.say(
        f'{helper.label_word.capitalize()} stepped up and spoke with a grin, '
        f'"That trunk looks too heavy. Let\'s not jerk it in."'
    )
    world.say(
        f'"A stuck old trunk can pinch fingers and toes, so we should take it slow '
        f'and choose a safe trick for those heroes we know."'
    )


def try_wrong_move(world: World, hero: Entity, move: Move) -> None:
    hero.memes["bravery"] += 1
    world.say(
        f"{hero.id} tried a grand heave and a dramatic spin, but the trunk only "
        f"wobbled and settled again."
    )


def move_trunk(world: World, helper: Entity, hero: Entity, move: Move, scene: Scene) -> None:
    _do_move(world, world.facts["risk"], move)
    world.say(
        f'{helper.label_word.capitalize()} said, "Let\'s lift together, nice and '
        f"slow," and the trunk slid forward with a superhero glow."
    )
    world.say(
        f"They shuffled it free, with a heave and a cheer, and the heavy old trunk "
        f"moved out of the way right here."
    )


def open_trunk(world: World, hero: Entity, sidekick: Entity, scene: Scene) -> None:
    hero.memes["joy"] += 1
    sidekick.memes["joy"] += 1
    world.say(
        f"Inside was a shiny flashlight, a ribbon, and a cape lined blue, "
        f"and the little trunk treasure felt perfect and new."
    )
    world.say(
        f"{scene.ending_image} The hero stood tall with a smile so bright, for a "
        f"stuck trunk had turned into a fun, happy sight."
    )


def lesson(world: World, helper: Entity, hero: Entity, sidekick: Entity) -> None:
    world.say(
        f"{helper.label_word.capitalize()} hugged them both and said, "
        f'"Brave means careful, not speedy or wild. A good hero protects every child."'
    )
    world.say(
        f'"You listened, you teamed up, you chose the right way; that is how heroes "
        f"save the day."'
    )


def tell(scene: Scene, risk: Risk, move: Move, hero_name: str, hero_gender: str,
         sidekick_name: str, sidekick_gender: str, helper_type: str) -> World:
    world = World()
    hero = world.add(Entity(hero_name, kind="character", type=hero_gender, role="hero"))
    sidekick = world.add(Entity(sidekick_name, kind="character", type=sidekick_gender, role="sidekick"))
    helper = world.add(Entity("Helper", kind="character", type=helper_type, role="helper", label=scene.helper_title))
    trunk = world.add(Entity("trunk", kind="thing", type="thing", label="the trunk"))
    world.facts["risk"] = risk

    intro(world, hero, sidekick, scene)
    show_trunk(world, scene, trunk)
    world.para()
    want_to_open(world, hero, sidekick, scene)
    warn(world, helper, hero, trunk, risk)
    if move.id == "pull":
        move_trunk(world, helper, hero, move, scene)
        world.para()
        open_trunk(world, hero, sidekick, scene)
        lesson(world, helper, hero, sidekick)
        outcome = "opened"
    else:
        try_wrong_move(world, hero, move)
        move_trunk(world, helper, hero, move, scene)
        world.para()
        open_trunk(world, hero, sidekick, scene)
        outcome = "opened"
    world.facts.update(hero=hero, sidekick=sidekick, helper=helper, trunk=trunk, outcome=outcome)
    return world


SCENES = {
    "park": Scene(
        place="the park",
        rhyme1="bright and light",
        rhyme2="day away",
        trunk_desc="its brass latch was dull but its corners shone",
        hero_title="caped kid",
        helper_title="Captain Care",
        goal="the mystery within",
        ending_image="The tree cast a tidy shade, and the park felt proud of the brave parade.",
    ),
    "yard": Scene(
        place="the backyard",
        rhyme1="clear and near",
        rhyme2="soft and bright",
        trunk_desc="its wooden sides were old and brown",
        hero_title="sky saver",
        helper_title="Major Kind",
        goal="the secret inside",
        ending_image="The yard grew calm, and the sunset glowed like a friendly alarm.",
    ),
    "attic": Scene(
        place="the attic",
        rhyme1="high and dry",
        rhyme2="soft moonlight",
        trunk_desc="it was dusty and deep, with a latch that clinked",
        hero_title="window watcher",
        helper_title="Auntie Spark",
        goal="the treasure within",
        ending_image="The attic dust danced gently down, while the hero's smile wore a golden crown.",
    ),
}

RISKS = {
    "heavy_trunk": Risk("heavy_trunk", "heavy trunk", "ground", 1, "might pinch fingers", {"trunk", "heavy"}),
}

MOVES = {
    "pull": Move("pull", 3, 3, "pulled together and moved it safely", "pulled too hard and only made it wobble", "moved the trunk safely", {"trunk", "safe"}),
    "kick": Move("kick", 1, 1, "kicked the trunk", "kicked the trunk", "kicked the trunk", {"trunk"}),
}

CURATED = [
    ("park", "heavy_trunk", "pull", "Nova", "girl", "Spark", "girl", "mother"),
    ("yard", "heavy_trunk", "pull", "Milo", "boy", "Bean", "girl", "father"),
    ("attic", "heavy_trunk", "pull", "Zara", "girl", "Dot", "boy", "mother"),
]


@dataclass
class StoryParams:
    scene: str
    risk: str
    move: str
    hero: str
    hero_gender: str
    sidekick: str
    sidekick_gender: str
    helper: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SCENES:
        for r in RISKS:
            for m in MOVES:
                if hazard_at_risk(RISKS[r]) and enough_power(MOVES[m], RISKS[r]):
                    combos.append((s, r, m))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny superhero rhyme storyworld with a trunk.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--risk", choices=RISKS)
    ap.add_argument("--move", choices=MOVES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--sidekick")
    ap.add_argument("--sidekick-gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father"])
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
    combos = [c for c in valid_combos()
              if (args.scene is None or c[0] == args.scene)
              and (args.risk is None or c[1] == args.risk)
              and (args.move is None or c[2] == args.move)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    scene, risk, move = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    sidekick_gender = args.sidekick_gender or rng.choice(["girl", "boy"])
    hero = args.hero or rng.choice(HERO_NAMES)
    sidekick = args.sidekick or rng.choice([n for n in SIDEKICK_NAMES if n != hero])
    helper = args.helper or rng.choice(["mother", "father"])
    return StoryParams(scene, risk, move, hero, hero_gender, sidekick, sidekick_gender, helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(SCENES[params.scene], RISKS[params.risk], MOVES[params.move],
                 params.hero, params.hero_gender, params.sidekick, params.sidekick_gender,
                 params.helper)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a superhero story in rhyme that includes the word trunk and ends with a safe rescue.",
        f"Tell a rhyme-forward superhero tale about {world.facts['hero'].id} and a heavy trunk.",
        "Write a child-friendly story where a brave hero and helper move a trunk safely together.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    sidekick = world.facts["sidekick"]
    helper = world.facts["helper"]
    qa = [
        ("Who is the story about?", f"It is about {hero.id}, {sidekick.id}, and {helper.label_word}. They worked together around a heavy trunk."),
        ("What was stuck?", "The trunk was stuck on the ground and would not budge at first."),
        ("How did they solve the problem?", f"{helper.label_word.capitalize()} and the children moved the trunk safely together instead of kicking or jerking it."),
        ("How did the story end?", "It ended happily, with the trunk moved aside and a shiny surprise inside."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a trunk?", "A trunk is a big box or chest that can hold things inside it."),
        ("What should a hero do if something is heavy?", "A hero should ask for help and move heavy things carefully."),
        ("Why is teamwork good?", "Teamwork helps people do hard things more safely and more easily."),
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
    lines.append("== (3) World knowledge ==")
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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,R,M) :- scene(S), risk(R), move(M).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SCENES:
        lines.append(asp.fact("scene", s))
    for r in RISKS:
        lines.append(asp.fact("risk", r))
    for m in MOVES:
        lines.append(asp.fact("move", m))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import sys as _sys
    ok = True
    if set(valid_combos()) != set(asp_valid_combos()):
        ok = False
        print("MISMATCH: ASP and Python valid_combos differ.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
    except Exception as e:
        ok = False
        print(f"MISMATCH: generate crashed: {e}")
    print("OK" if ok else "FAILED")
    return 0 if ok else 1


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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(*c, HERO_NAMES[i % len(HERO_NAMES)], "girl" if i % 2 == 0 else "boy",
                                        SIDEKICK_NAMES[i % len(SIDEKICK_NAMES)], "boy", "mother"))
                   for i, c in enumerate(CURATED)]
    else:
        for i in range(args.n):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            samples.append(generate(p))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

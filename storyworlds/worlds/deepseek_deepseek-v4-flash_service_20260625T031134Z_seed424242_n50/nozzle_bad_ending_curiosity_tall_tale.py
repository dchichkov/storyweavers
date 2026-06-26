#!/usr/bin/env python3
"""
storyworlds/worlds/deepseek_deepseek-v4-flash_service_20260625T031134Z_seed424242_n50/nozzle_bad_ending_curiosity_tall_tale.py
=========================================================================================================================

A standalone story world sketch based on a Tall Tale domain with a curious child,
a mysterious nozzle, and a bad ending when curiosity goes unchecked.

Premise: A child finds a strange nozzle in the garden. The nozzle can make things
grow or shrink. Curiosity leads the child to use it on everything, but using it
on the wrong thing causes a bad ending - the thing grows out of control or shrinks
to nothing.

World model: Physical meters track the size of objects. Emotional memes track
curiosity, caution, and regret. The bad ending occurs when the child uses the
nozzle on something that should not be changed.
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
DANGER_THRESHOLD = 3.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    can_shrink: bool = False
    can_grow: bool = False
    fragile: bool = False
    alive: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "grandma"}
        male = {"boy", "father", "uncle", "grandpa"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the garden"
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class NozzleEffect:
    """What the nozzle does to different kinds of things."""
    id: str
    verb: str
    target_kind: str
    result_grow: str
    result_shrink: str
    bad_grow: str
    bad_shrink: str
    is_dangerous: bool = False


@dataclass
class TargetObject:
    """Something the child might use the nozzle on."""
    label: str
    phrase: str
    type: str
    kind: str
    can_grow: bool = True
    can_shrink: bool = True
    fragile: bool = False
    alive: bool = False
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class StoryParams:
    place: str
    nozzle_effect: str
    target: str
    use_direction: str  # "grow" or "shrink"
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "garden": Setting(place="the garden", indoor=False, affords={"grow", "shrink"}),
    "yard": Setting(place="the backyard", indoor=False, affords={"grow", "shrink"}),
    "park": Setting(place="the park", indoor=False, affords={"grow", "shrink"}),
    "field": Setting(place="the empty field", indoor=False, affords={"grow", "shrink"}),
}

NOZZLE_EFFECTS = {
    "flower": NozzleEffect(
        id="flower",
        verb="made the flower grow tall",
        target_kind="plant",
        result_grow="the flower grew tall and bright",
        result_shrink="the flower shrank to a tiny bud",
        bad_grow="the flower grew huge and snapped its stem",
        bad_shrink="the flower shrank so small it disappeared",
        is_dangerous=False,
    ),
    "bug": NozzleEffect(
        id="bug",
        verb="pointed the nozzle at a bug",
        target_kind="insect",
        result_grow="the bug grew big and slow",
        result_shrink="the bug shrank to a speck",
        bad_grow="the bug grew huge and scared everyone",
        bad_shrink="the bug shrank and got lost forever",
        is_dangerous=True,
    ),
    "stone": NozzleEffect(
        id="stone",
        verb="aimed the nozzle at a stone",
        target_kind="rock",
        result_grow="the stone grew into a boulder",
        result_shrink="the stone shrank to a pebble",
        bad_grow="the stone grew huge and cracked the ground",
        bad_shrink="the stone shrank and was never seen again",
        is_dangerous=True,
    ),
    "puddle": NozzleEffect(
        id="puddle",
        verb="sprayed the nozzle at a puddle",
        target_kind="water",
        result_grow="the puddle grew into a small pond",
        result_shrink="the puddle shrank to a drop",
        bad_grow="the puddle grew into a flood",
        bad_shrink="the puddle dried up completely",
        is_dangerous=False,
    ),
}

TARGET_OBJECTS = {
    "rose": TargetObject(
        label="rose", phrase="a red rose with soft petals",
        type="rose", kind="plant", fragile=True, alive=True
    ),
    "ladybug": TargetObject(
        label="ladybug", phrase="a tiny ladybug with seven spots",
        type="ladybug", kind="insect", fragile=True, alive=True
    ),
    "pebble": TargetObject(
        label="pebble", phrase="a smooth gray pebble",
        type="pebble", kind="rock", fragile=False, alive=False
    ),
    "puddle": TargetObject(
        label="puddle", phrase="a small puddle from last night's rain",
        type="puddle", kind="water", fragile=False, alive=False, plural=False
    ),
    "frog": TargetObject(
        label="frog", phrase="a little green frog with big eyes",
        type="frog", kind="animal", fragile=True, alive=True,
        genders={"boy"}
    ),
    "butterfly": TargetObject(
        label="butterfly", phrase="a bright blue butterfly with shimmering wings",
        type="butterfly", kind="insect", fragile=True, alive=True
    ),
}

GIRL_NAMES = ["Ada", "Bella", "Clara", "Daisy", "Elsie", "Faye", "Greta", "Hazel", "Iris", "Juno"]
BOY_NAMES = ["Alf", "Bert", "Clem", "Dale", "Emmett", "Finn", "Gus", "Hank", "Ike", "Jed"]
TRAITS = ["curious", "brave", "daring", "thoughtful", "bold", "eager"]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.bad_ending: bool = False

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
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _r_curiosity_grows(world: World) -> list[str]:
    """Curiosity builds when the child sees the nozzle working."""
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["used_nozzle"] >= THRESHOLD and actor.memes["curiosity"] < DANGER_THRESHOLD:
            sig = ("curiosity_build", actor.id)
            if sig not in world.fired:
                world.fired.add(sig)
                actor.memes["curiosity"] += 1
                out.append(f"That made {actor.pronoun('object')} even more curious.")
    return out


def _r_bad_ending_check(world: World) -> list[str]:
    """Check if the bad ending condition is met."""
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["curiosity"] >= DANGER_THRESHOLD and not world.bad_ending:
            sig = ("bad_ending", actor.id)
            if sig not in world.fired:
                world.fired.add(sig)
                world.bad_ending = True
                out.append("__bad_ending__")
    return out


CAUSAL_RULES = [
    ("curiosity_build", _r_curiosity_grows),
    ("bad_ending_check", _r_bad_ending_check),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for name, rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__bad_ending__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def find_nozzle(world: World, hero: Entity) -> None:
    world.say(
        f"One day, {hero.id} found a strange nozzle lying in {world.setting.place}. "
        f"It was old and brass, with two tiny buttons on the side: one marked '
        f'BIG and one marked 'SMALL'. {hero.pronoun().capitalize()} had never seen "
        f"anything like it before."
    )


def test_nozzle_grow(world: World, hero: Entity, effect: NozzleEffect, target: Entity) -> None:
    hero.memes["used_nozzle"] += 1
    hero.memes["curiosity"] += 1
    target.meters["size"] += 2
    world.say(
        f"{hero.id} pointed the nozzle at {target.phrase} and pressed the BIG button. "
        f"A puff of silver mist shot out, and {effect.result_grow}. "
    )
    propagate(world)


def test_nozzle_shrink(world: World, hero: Entity, effect: NozzleEffect, target: Entity) -> None:
    hero.memes["used_nozzle"] += 1
    hero.memes["curiosity"] += 1
    target.meters["size"] -= 2
    if target.meters["size"] < -THRESHOLD:
        world.bad_ending = True
        world.say(
            f"{hero.id} pressed the SMALL button, and {effect.bad_shrink}! "
            f"{hero.pronoun().capitalize()} searched everywhere, but {target.label} "
            f"was gone forever."
        )
    else:
        world.say(
            f"{hero.id} pointed the nozzle and pressed SMALL. "
            f"{effect.result_shrink}. "
        )
    propagate(world)


def warn_twice(world: World, hero: Entity, parent: Entity) -> None:
    world.say(
        f'"{hero.id}, be careful with that thing!" called {parent.label}. '
        f'"Some things are not meant to be changed."'
    )
    world.para()


def bad_ending_grow(world: World, hero: Entity, effect: NozzleEffect, target: Entity) -> None:
    world.say(
        f"But {hero.id} did not listen. {hero.pronoun().capitalize()} kept pressing BIG. "
        f"The {target.label} {effect.bad_grow}! It grew so big it blocked the sun, "
        f"and {hero.pronoun().capitalize()} could not stop it."
    )
    hero.memes["regret"] += DANGER_THRESHOLD
    world.bad_ending = True
    world.say(
        f"{hero.id} dropped the nozzle and ran away. The {target.label} was never "
        f"the same again, and neither was {hero.pronoun('possessive')} day."
    )


def tall_tale_moral(world: World, hero: Entity, parent: Entity) -> None:
    if world.bad_ending:
        world.say(
            f'"{hero.id}," said {parent.label} gently later, "some things are "
            f"small for a reason. The best adventures come from leaving the world "
            f"just as you found it, maybe with a little more kindness." '
            f"{hero.id} nodded, remembering the {hero.facts.get('target_label', 'strange thing')}."
        )
    else:
        world.say(
            f"{hero.id} put the nozzle back where {hero.pronoun()} found it. "
            f"The world was full of wonders, but some wonders were not meant to be "
            f"changed. And {hero.pronoun()} smiled, content to just explore."
        )


def tell(setting: Setting, effect: NozzleEffect, target_cfg: TargetObject,
         use_direction: str, hero_name: str = "Ada", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None,
         parent_type: str = "mother") -> World:
    world = World(setting)

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little"] + (hero_traits or ["curious", "brave"]),
        memes=defaultdict(float, curiosity=0.0, used_nozzle=0.0, regret=0.0)
    ))
    parent = world.add(Entity(
        id="Parent", kind="character", type=parent_type, label="the parent"
    ))
    target = world.add(Entity(
        id="target", type=target_cfg.type, label=target_cfg.label,
        phrase=target_cfg.phrase, kind=target_cfg.kind,
        fragile=target_cfg.fragile, alive=target_cfg.alive,
        plural=target_cfg.plural,
        meters=defaultdict(float, size=0.0)
    ))
    world.facts["target_label"] = target_cfg.label
    world.facts["target_type"] = target_cfg.type

    # Act 1: Discovery
    world.say(f"In a quiet corner of {setting.place}, where the sunbeams danced through the leaves,")
    find_nozzle(world, hero)

    # Act 2: Curious testing
    world.para()
    warn_twice(world, hero, parent)
    world.para()

    # Act 3: The attempt and its consequence
    world.say(f"{hero.id} could not resist. {hero.pronoun().capitalize()} held the nozzle tight.")
    if use_direction == "grow":
        test_nozzle_grow(world, hero, effect, target)
        if hero.memes["curiosity"] >= DANGER_THRESHOLD or world.bad_ending:
            bad_ending_grow(world, hero, effect, target)
        else:
            world.say(f"{hero.id} smiled and put the nozzle away. The {target.label} "
                      f"was now the biggest one in {setting.place}.")
    else:
        test_nozzle_shrink(world, hero, effect, target)

    # Act 4: Resolution
    world.para()
    tall_tale_moral(world, hero, parent)

    world.facts.update(
        hero=hero, parent=parent, target=target, target_cfg=target_cfg,
        effect=effect, setting=setting, bad_ending=world.bad_ending,
        use_direction=use_direction
    )
    return world


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for effect_id in NOZZLE_EFFECTS:
            for target_id, target in TARGET_OBJECTS.items():
                if NOZZLE_EFFECTS[effect_id].target_kind == target.kind:
                    combos.append((place, effect_id, target_id))
    return combos


def explain_rejection(effect_id: str, target_id: str) -> str:
    return (f"(No story: the nozzle effect '{effect_id}' is for "
            f"{NOZZLE_EFFECTS[effect_id].target_kind} things, "
            f"but '{target_id}' is a {TARGET_OBJECTS[target_id].kind}.")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, effect, target_cfg = f["hero"], f["parent"], f["effect"], f["target_cfg"]
    return [
        f'Write a tall tale for a 3-to-5-year-old about a curious {hero.type} '
        f'named {hero.id} who finds a magic nozzle with two buttons.',
        f'Tell a story where {hero.id} discovers that some things should not be '
        f'changed, even when you are very curious.',
        f'Write a simple story with a moral about a magic nozzle and a {target_cfg.label}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, target, effect = f["hero"], f["parent"], f["target"], f["effect"]
    sub, obj, pos = (hero.pronoun("subject"), hero.pronoun("object"),
                     hero.pronoun("possessive"))
    place = world.setting.place
    trait = next((t for t in hero.traits if t != "little"), hero.type)
    direction = f.get("use_direction", "grow")

    qa = [
        QAItem(
            question=f"What did {trait} {hero.id} find in {place} that had two buttons?",
            answer=f"{trait.capitalize()} {hero.id} found a strange brass nozzle "
                   f"with one button marked BIG and one marked SMALL."
        ),
        QAItem(
            question=f"What happened when {hero.id} used the nozzle on the {target.label}?",
            answer=f"{hero.id} aimed the nozzle at {target.phrase} and pressed the "
                   f"{direction.upper()} button. The {target.label} changed size "
                   f"right before {pos} eyes."
        ),
    ]
    if f.get("bad_ending"):
        qa.append(QAItem(
            question=f"Why did things go wrong for {trait} {hero.id}?",
            answer=f"{sub.capitalize()} was too curious and did not stop when "
                   f"{pos} {parent.label_word} warned {obj}. The {target.label} "
                   f"changed too much and was ruined."
        ))
    else:
        qa.append(QAItem(
            question=f"What lesson did {trait} {hero.id} learn at the end?",
            answer=f"{sub.capitalize()} learned that some things are best left "
                   f"as they are, and that curiosity should come with care."
        ))
    return qa


KNOWLEDGE = {
    "nozzle": [
        ("What is a nozzle?",
         "A nozzle is a tube at the end of a hose or pipe that controls how "
         "water or air comes out. Some nozzles have buttons or levers.")
    ],
    "curiosity": [
        ("What does it mean to be curious?",
         "Being curious means you want to learn and discover new things. "
         "It is good to ask questions, but sometimes you need to be careful too.")
    ],
    "tall_tale": [
        ("What is a tall tale?",
         "A tall tale is a story with exaggerated, larger-than-life events. "
         "They often teach a lesson in a fun, bigger-than-real way.")
    ],
}
KNOWLEDGE_ORDER = ["nozzle", "curiosity", "tall_tale"]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if hasattr(e, 'fragile') and e.fragile:
            bits.append("fragile")
        if hasattr(e, 'alive') and e.alive:
            bits.append("alive")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  bad_ending: {world.bad_ending}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="garden", nozzle_effect="flower", target="rose",
                use_direction="grow", name="Ada", gender="girl",
                parent="mother", trait="curious"),
    StoryParams(place="yard", nozzle_effect="bug", target="ladybug",
                use_direction="shrink", name="Bert", gender="boy",
                parent="father", trait="daring"),
    StoryParams(place="field", nozzle_effect="stone", target="pebble",
                use_direction="grow", name="Clara", gender="girl",
                parent="aunt", trait="bold"),
    StoryParams(place="park", nozzle_effect="puddle", target="puddle",
                use_direction="grow", name="Dale", gender="boy",
                parent="mother", trait="eager"),
    StoryParams(place="garden", nozzle_effect="bug", target="butterfly",
                use_direction="shrink", name="Elsie", gender="girl",
                parent="father", trait="thoughtful"),
]


ASP_RULES = r"""
% A nozzle effect applies to a target when their kinds match.
effect_for(E, T) :- nozzle_effect(E), target_object(T), kind_of(E, K), kind_of(T, K).

% A story is valid when the place allows the effect and the effect matches the target.
valid_story(P, E, T, G) :- setting(P), nozzle_effect(E), target_object(T),
                           effect_for(E, T), wears(G, T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for eid, e in NOZZLE_EFFECTS.items():
        lines.append(asp.fact("nozzle_effect", eid))
        lines.append(asp.fact("kind_of", eid, e.target_kind))
    for tid, t in TARGET_OBJECTS.items():
        lines.append(asp.fact("target_object", tid))
        lines.append(asp.fact("kind_of", tid, t.kind))
        for g in sorted(t.genders):
            lines.append(asp.fact("wears", g, tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall tale: a curious child, a magic nozzle, and a bad ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--nozzle-effect", choices=NOZZLE_EFFECTS)
    ap.add_argument("--target", choices=TARGET_OBJECTS)
    ap.add_argument("--use-direction", choices=["grow", "shrink"])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("--name")
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
              if (args.place is None or c[0] == args.place)
              and (args.nozzle_effect is None or c[1] == args.nozzle_effect)
              and (args.target is None or c[2] == args.target)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, effect_id, target_id = rng.choice(sorted(combos))
    target_cfg = TARGET_OBJECTS[target_id]
    gender = args.gender or rng.choice(sorted(target_cfg.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    use_direction = args.use_direction or rng.choice(["grow", "shrink"])
    return StoryParams(
        place=place, nozzle_effect=effect_id, target=target_id,
        use_direction=use_direction, name=name, gender=gender,
        parent=parent, trait=trait
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], NOZZLE_EFFECTS[params.nozzle_effect],
                 TARGET_OBJECTS[params.target], params.use_direction,
                 params.name, params.gender,
                 [params.trait, "curious"], params.parent)
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
        print(asp_program("#show valid_story/4."))
        return
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} valid stories:\n")
        for place, effect, target, gender in stories:
            print(f"  {place:9} {effect:8} {target:8} {gender}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

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
            header = (f"### {p.name}: {p.nozzle_effect} at {p.place} "
                      f"(target: {p.target}, direction: {p.use_direction})")
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

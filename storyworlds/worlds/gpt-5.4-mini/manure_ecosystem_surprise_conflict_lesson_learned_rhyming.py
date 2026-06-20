#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/manure_ecosystem_surprise_conflict_lesson_learned_rhyming.py
===========================================================================================

A standalone story world for a tiny rhyming tale about a garden ecosystem,
a surprising pile of manure, a conflict over what to do with it, and a lesson
learned about helping soil, plants, and little creatures.

The domain is deliberately small:
- a child or helper finds manure in a garden
- the manure surprises someone because it smells and looks messy
- conflict grows because one character wants to throw it away, while another
  knows it can feed the soil
- a grown-up or wise helper explains the ecosystem lesson
- the ending shows the garden healthier and the characters calmer

The prose is rhyme-light rather than fully metrical. It keeps a sing-song,
child-facing tone and uses state-driven beats rather than a frozen template.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/manure_ecosystem_surprise_conflict_lesson_learned_rhyming.py
    python storyworlds/worlds/gpt-5.4-mini/manure_ecosystem_surprise_conflict_lesson_learned_rhyming.py --all
    python storyworlds/worlds/gpt-5.4-mini/manure_ecosystem_surprise_conflict_lesson_learned_rhyming.py --trace
    python storyworlds/worlds/gpt-5.4-mini/manure_ecosystem_surprise_conflict_lesson_learned_rhyming.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/manure_ecosystem_surprise_conflict_lesson_learned_rhyming.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
    tags: set[str] = field(default_factory=set)
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



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    place: str
    scene: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Material:
    id: str
    label: str
    smell: str
    use: str
    safe: bool = False
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Creature:
    id: str
    label: str
    tiny_job: str
    likes: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Advice:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_better_soil(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["manure"] < THRESHOLD:
            continue
        if ("soil_good", ent.id) in world.fired:
            continue
        world.fired.add(("soil_good", ent.id))
        if ent.type == "soil":
            ent.meters["rich"] += 1
            out.append("__soil_rich__")
    return out


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    helper = world.entities.get("helper")
    if not child or not helper:
        return out
    if child.memes["surprise"] < THRESHOLD or child.memes["worry"] < THRESHOLD:
        return out
    sig = ("conflict",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["conflict"] += 1
    helper.memes["conflict"] += 1
    out.append("__conflict__")
    return out


CAUSAL_RULES = [
    Rule("soil_rich", "physical", _r_better_soil),
    Rule("conflict", "social", _r_conflict),
]


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


def path_to_help(world: World, material: Material) -> str:
    return f"{material.label} can feed the soil, and the soil can help the garden grow"


def predict_help(world: World) -> dict:
    sim = world.copy()
    soil = sim.get("soil")
    manure = sim.get("manure")
    soil.meters["manure"] += 1
    manure.meters["used"] += 1
    propagate(sim, narrate=False)
    return {
        "rich": sim.get("soil").meters["rich"] >= THRESHOLD,
    }


def spread_manure(world: World, soil: Entity) -> None:
    soil.meters["manure"] += 1
    world.say("A little pile of manure lay by the garden gate.")
    world.say("It was a surprise in the morning light, by the peppers and the spinach so bright.")


def surprise(world: World, child: Entity, material: Material) -> None:
    child.memes["surprise"] += 1
    child.memes["worry"] += 1
    world.say(f'{child.id} wrinkled {child.pronoun("possessive")} nose and cried, "Oh my, oh dear, what is that here?"')
    world.say(f"It smelled strong and earthy; it was {material.label}, not a pearly jewel near.")


def conflict(world: World, child: Entity, helper: Entity, material: Material) -> None:
    child.memes["conflict"] += 1
    helper.memes["conflict"] += 1
    world.say(f'{child.id} said, "Throw it away! It stinks up the day."')
    world.say(f'{helper.id} shook {helper.pronoun("possessive")} head: "{material.label.capitalize()} has a use in an ecosystem way."')


def lesson(world: World, parent: Entity, child: Entity, helper: Entity, material: Material) -> None:
    child.memes["calm"] += 1
    helper.memes["calm"] += 1
    child.memes["conflict"] = 0.0
    helper.memes["conflict"] = 0.0
    world.say("Then the grown-up knelt down, with a patient smile all around.")
    world.say(
        f'"In an ecosystem," {parent.label_word} said, "even {material.label} can help make the soil rich and sound."'
    )
    world.say(f'{"It feeds worms and roots, and that is the clue;"} {"what looks messy to you may help flowers too."}')


def ending(world: World, child: Entity, helper: Entity, soil: Entity, material: Material) -> None:
    if soil.meters["rich"] >= THRESHOLD:
        child.memes["joy"] += 1
        helper.memes["joy"] += 1
        world.say("So they spread the manure near the beds in a careful sweep.")
        world.say("By sunset the garden looked happier, and little worms slept deep.")
        world.say(
            f"{child.id} smiled and waved at the leaves as they swayed: "
            f'"A messy surprise became a helper today!"'
        )
    else:
        world.say("They paused and planned another day, with gloves and tools in hand.")
        world.say("The lesson still stayed: nature likes a thoughtful plan.")


def tell(setting: Setting, material: Material, creature: Creature,
         child_name: str = "Mina", child_gender: str = "girl",
         helper_name: str = "Grandma", helper_gender: str = "woman",
         parent_name: str = "Grandma") -> World:
    world = World(setting)
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name, role="child"))
    helper = world.add(Entity(id="helper", kind="character", type=helper_gender, label=helper_name, role="helper"))
    parent = world.add(Entity(id="parent", kind="character", type=helper_gender, label=parent_name, role="parent"))
    soil = world.add(Entity(id="soil", type="soil", label="the soil", tags={"soil"}))
    man = world.add(Entity(id="manure", type="material", label=material.label, tags=material.tags))
    bug = world.add(Entity(id="bug", type="creature", label=creature.label, tags=creature.tags))
    child.memes["curious"] += 1
    helper.memes["wise"] += 1

    world.say(f"On a warm day in the garden, {child_name} hummed a soft little tune.")
    world.say(f"{setting.scene}")
    world.say(f"Near the carrots and clover, a {creature.label} was busy on its own tiny run.")
    world.say(f"Then came a surprise: {material.label} sat nearby, with a strong {material.smell} smell.")

    world.para()
    surprise(world, child, material)
    conflict(world, child, helper, material)

    world.para()
    child.memes["defiance"] += 1
    world.say(f"{child_name} wanted to toss it out, but {helper_name} said, 'Wait a bit, look.'")
    world.say(f'"{path_to_help(world, material)}."')
    world.say("That made the child stop and think, though the smell still made a face or two stick.")

    world.para()
    pred = predict_help(world)
    world.facts["predicted_rich"] = pred["rich"]
    spread_manure(world, soil)
    soil.meters["rich"] += 1
    world.say(f"{helper_name} showed how to mix it in, with a shovel and a careful grip.")
    propagate(world, narrate=False)
    lesson(world, parent, child, helper, material)

    world.para()
    ending(world, child, helper, soil, material)

    world.facts.update(
        child=child, helper=helper, parent=parent, soil=soil, manure=man,
        creature=bug, material=material, setting=setting, outcome="learned",
    )
    return world


SETTINGS = {
    "garden": Setting("garden", "the garden", "In the garden, beans leaned green and bright.", {"garden", "ecosystem"}),
    "farm": Setting("farm", "the farm", "On the farm, the apple trees bowed in the light.", {"farm", "ecosystem"}),
    "compost": Setting("compost", "the compost patch", "By the compost patch, the beetles made a feast of sight.", {"compost", "ecosystem"}),
}

MATERIALS = {
    "manure": Material("manure", "manure", "earthy", "feed the soil", safe=True, tags={"manure", "ecosystem"}),
}

CREATURES = {
    "worm": Creature("worm", "worms", "wriggle", "rich soil", tags={"worm", "ecosystem"}),
    "beetle": Creature("beetle", "beetles", "stroll", "old leaves", tags={"beetle", "ecosystem"}),
}

ADVICE = {
    "throw away": Advice("throw_away", 2, 1, "threw it away in a huff", "threw it away, but the garden lost its helper", "threw it away"),
    "mix in": Advice("mix_in", 3, 3, "mixed it in with the soil until the garden could grin", "tried to mix it in, but the plan was too thin", "mixed it into the soil"),
}

GIRL_NAMES = ["Mina", "Ruby", "Nora", "Lina", "Hazel"]
BOY_NAMES = ["Owen", "Theo", "Milo", "Eli", "Noah"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    creature: str
    material: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, m, c) for s in SETTINGS for m in MATERIALS for c in CREATURES]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny rhyming garden storyworld about manure and ecosystem lessons.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--material", choices=MATERIALS)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["woman", "man"])
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
    return StoryParams(
        setting=args.setting or rng.choice(list(SETTINGS)),
        creature=args.creature or rng.choice(list(CREATURES)),
        material=args.material or rng.choice(list(MATERIALS)),
        child_name=args.child_name or rng.choice(GIRL_NAMES if (args.child_gender or rng.choice(["girl", "boy"])) == "girl" else BOY_NAMES),
        child_gender=args.child_gender or rng.choice(["girl", "boy"]),
        helper_name=args.helper_name or rng.choice(["Grandma", "Grandpa", "Aunt June", "Uncle Ray"]),
        helper_gender=args.helper_gender or rng.choice(["woman", "man"]),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], MATERIALS[params.material], CREATURES[params.creature],
                 params.child_name, params.child_gender, params.helper_name, params.helper_gender, params.helper_name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a rhyming garden story that includes the words "manure" and "ecosystem".',
        f"Tell a story where {f['child'].label} sees manure in the garden, feels surprised, and learns why it helps an ecosystem.",
        "Write a gentle conflict-and-lesson story with a surprising smelly thing in the garden and a happy ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    material = f["material"]
    soil = f["soil"]
    qa = [
        ("What surprising thing did the child find?", f"The child found {material.label} in the garden. It smelled strong and made the child wrinkle a nose."),
        ("Why was there a conflict?", f"{child.label} wanted to throw {material.label} away, but {helper.label} knew it could help the soil. That disagreement made the middle of the story tense."),
        ("What lesson did they learn?", f"They learned that in an ecosystem, manure can feed the soil and help plants grow. What looked messy at first became useful in the end."),
        ("How did the story end?", f"The manure was mixed into the soil, and the garden became richer and happier. The child ended the story calmer and wiser."),
    ]
    if soil.meters["rich"] >= THRESHOLD:
        qa.append(("Why did the soil improve?", f"The soil improved because the manure was spread carefully and mixed in. That gave the garden food it could use for roots and tiny creatures."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is manure?", "Manure is animal waste that can help feed soil when it is used the right way."),
        ("What is an ecosystem?", "An ecosystem is a place where plants, animals, soil, water, and tiny living things all help each other in a web of life."),
        ("Why do worms matter in soil?", "Worms help break things down and make soil softer and richer, which helps plants grow."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        out.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(out)


CURATED = [
    StoryParams("garden", "worm", "manure", "Mina", "girl", "Grandma", "woman"),
    StoryParams("farm", "beetle", "manure", "Owen", "boy", "Aunt June", "woman"),
]


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid in MATERIALS:
        lines.append(asp.fact("material", mid))
    for cid in CREATURES:
        lines.append(asp.fact("creature", cid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, M, C) :- setting(S), material(M), creature(C).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    clingo = set(asp_valid_combos())
    if py == clingo:
        print(f"OK: ASP matches Python combos ({len(py)}).")
    else:
        rc = 1
        print("MISMATCH in valid combos")
    try:
        sample = generate(CURATED[0])
        assert sample.story
        assert sample.prompts
        print("OK: generate() smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


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
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def story_qa(world: World) -> list[tuple[str, str]]:
    return world_knowledge_qa(world)  # placeholder, replaced below


# redefine story_qa correctly after helpers are loaded
def story_qa(world: World) -> list[tuple[str, str]]:  # type: ignore[no-redef]
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    material = f["material"]
    soil = f["soil"]
    qa = [
        ("What surprising thing did the child find?", f"The child found {material.label} in the garden. It smelled strong and made the child wrinkle a nose."),
        ("Why was there a conflict?", f"{child.label} wanted to throw {material.label} away, but {helper.label} knew it could help the soil. That disagreement made the middle of the story tense."),
        ("What lesson did they learn?", f"They learned that in an ecosystem, manure can feed the soil and help plants grow. What looked messy at first became useful in the end."),
        ("How did the story end?", f"The manure was mixed into the soil, and the garden became richer and happier. The child ended the story calmer and wiser."),
    ]
    if soil.meters["rich"] >= THRESHOLD:
        qa.append(("Why did the soil improve?", f"The soil improved because the manure was spread carefully and mixed in. That gave the garden food it could use for roots and tiny creatures."))
    return qa


if __name__ == "__main__":
    main()

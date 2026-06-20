#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/hop_tutor_hij_mystery_to_solve_tall.py
=======================================================================

A standalone storyworld for a tall-tale mystery: a child, a tutor, and a nimble
helper named Hij follow clues, test a theory, and solve one small mystery in a
big, storybook way. The domain keeps the words hop, tutor, and hij in play, and
every story ends with the mystery solved by concrete world state, not a frozen
template.

The stories are set in a tiny frontier-style town with a riverbank, a high
porch, a windmill, and a hidden stash. A missing thing, a trail of clues, and a
careful tutor create the tension; a leap, a ladder, or a peek from above
creates the turn; the ending proves what was found and what changed.
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"distance": 0.0, "found": 0.0, "mystery": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "hope": 0.0, "relief": 0.0, "worry": 0.0}

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
        return self.label or self.id



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Setting:
    id: str
    label: str
    terrain: str
    clue_spot: str
    ending_image: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Mystery:
    id: str
    missing: str
    found_place: str
    clue_one: str
    clue_two: str
    clue_three: str
    solve_method: str
    reveal_line: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Companion:
    id: str
    label: str
    type: str
    ability: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[str] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


SETTINGS = {
    "ridge_town": Setting("ridge_town", "the ridge town", "high streets and steep steps",
                          "the old well", "the windmill stood tall against the moon"),
    "river_ford": Setting("river_ford", "the river ford", "muddy banks and wooden planks",
                          "the river reeds", "the ferry rope hummed in the dusk"),
    "mesa_village": Setting("mesa_village", "the mesa village", "wide rock and windy paths",
                            "the ledge by the bakery", "the little houses blinked like lanterns"),
}

MYSTERIES = {
    "lost_key": Mystery(
        "lost_key", "the silver key", "the old well", "a wet ribbon", "a tiny mud print",
        "a lantern reflection", "hop down the path and look below the bucket",
        "The silver key was resting on a nail under the well rim.", {"key", "well", "clue"}),
    "missing_map": Mystery(
        "missing_map", "the trail map", "the windmill loft", "a flour smudge", "a turned peg",
        "a loose stairboard", "hop up to the loft and check the peg hooks",
        "The trail map was folded into a pocket behind the loft boards.", {"map", "windmill", "clue"}),
    "lost_lunch": Mystery(
        "lost_lunch", "the tin lunch pail", "the river reeds", "a berry smear", "a bent reed",
        "a splash mark", "hop along the bank and peek into the reeds",
        "The tin lunch pail was tucked in the reeds beside a stone.", {"lunch", "river", "clue"}),
}

COMPANIONS = {
    "hij": Companion("Hij", "Hij", "dog", "can hop over little gaps", {"hij", "helper"}),
    "mule": Companion("Mule", "Mule", "mule", "can carry a lantern and a rope", {"helper"}),
    "robin": Companion("Robin", "Robin", "bird", "can spy from above", {"helper"}),
}

HERO_NAMES = ["Nell", "Toby", "June", "Bea", "Cal", "Milo", "Ivy", "Wren"]
TUTOR_NAMES = ["Tutor Mara", "Tutor Jo", "Tutor Bess", "Tutor Eli"]
TRAITS = ["bold", "careful", "bright-eyed", "steady", "curious"]


def _speak(world: World, who: Entity, text: str) -> None:
    world.say(f"{who.id} said, \"{text}\"")


def _setup(world: World, hero: Entity, tutor: Entity, helper: Entity, setting: Setting, mystery: Mystery) -> None:
    hero.memes["curiosity"] += 1
    tutor.memes["worry"] += 1
    helper.memes["hope"] += 1
    world.say(
        f"On a wide, windy evening, {hero.id} and {tutor.id} stood in {setting.label}. "
        f"The place had {setting.terrain}, and the air felt ready for a tale."
    )
    world.say(
        f"{hero.id} had been told that {mystery.missing} had gone missing, and nobody could "
        f"say where it had wandered off to."
    )
    world.say(
        f"{helper.id} was there too, quick as a wink, ready to {helper.ability}."
    )


def _clue(world: World, mystery: Mystery, line: str) -> None:
    world.say(line)
    world.get("mystery").meters["found"] += 0.25
    world.get("mystery").meters["distance"] -= 0.5


def _copy_find(world: World, target: str) -> None:
    world.get(target).meters["found"] += 1.0
    world.get("hero").meters["distance"] += 1.0


def _hop_search(world: World, hero: Entity, tutor: Entity, helper: Entity, setting: Setting, mystery: Mystery) -> None:
    world.say(
        f"{hero.id} took one hop, then another, following the clues like a fish follows a shiny lure."
    )
    hero.meters["distance"] += 1.0
    hero.memes["curiosity"] += 1
    world.say(
        f"{tutor.id} lifted a hand and pointed toward {mystery.clue_one}. "
        f'"A good mystery leaves marks," {tutor.id} said. "We must read the ground."'
    )
    _clue(world, mystery, f"Near {setting.clue_spot}, they found {mystery.clue_one}.")
    world.say(f"{helper.id} gave a little hop and nosed at the next hint: {mystery.clue_two}.")
    _clue(world, mystery, f"That clue led them on to {mystery.clue_two}.")
    world.say(
        f"At last, {helper.id} sprang once more and pointed toward {mystery.clue_three}, "
        f"the kind of clue that makes a mystery sneeze and show its nose."
    )
    _clue(world, mystery, f"Then they spotted {mystery.clue_three} near the spot that fit the story best.")


def _solve(world: World, hero: Entity, tutor: Entity, helper: Entity, setting: Setting, mystery: Mystery) -> None:
    world.say(
        f"{tutor.id} squinted, smiled, and said the clues all pointed the same way."
    )
    world.say(
        f"Together they followed {mystery.solve_method}, and the answer came out as neat as a bell."
    )
    world.say(mystery.reveal_line)
    hero.memes["hope"] += 1
    hero.memes["relief"] += 1
    tutor.memes["relief"] += 1
    helper.memes["hope"] += 1
    world.get("mystery").meters["found"] += 1.0
    world.get("mystery").meters["distance"] = 0.0
    world.say(
        f"In the end, {hero.id} and {helper.id} stood together in {setting.label}, "
        f"while {tutor.id} nodded like a mountain that had found its footing."
    )
    world.say(setting.ending_image)


def tell(setting: Setting, mystery: Mystery, hero_name: str, tutor_name: str, helper_id: str) -> World:
    world = World()
    hero = world.add(Entity(hero_name, kind="character", type="boy" if hero_name in {"Toby", "Cal", "Milo"} else "girl", role="hero"))
    tutor = world.add(Entity(tutor_name, kind="character", type="woman", role="tutor", label="the tutor"))
    helper = world.add(Entity(helper_id, kind="character", type=COMPANIONS[helper_id].type, role="helper"))
    world.add(Entity("mystery", kind="thing", type="mystery", label=mystery.missing))
    _setup(world, hero, tutor, helper, setting, mystery)
    world.para()
    _hop_search(world, hero, tutor, helper, setting, mystery)
    world.para()
    _solve(world, hero, tutor, helper, setting, mystery)
    world.facts.update(hero=hero, tutor=tutor, helper=helper, setting=setting, mystery=mystery)
    return world


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid in SETTINGS:
        for mid in MYSTERIES:
            combos.append((sid, mid))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    mystery: str
    hero: str
    tutor: str
    helper: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale mystery storyworld with hop, tutor, and hij.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--helper", choices=COMPANIONS)
    ap.add_argument("--hero")
    ap.add_argument("--tutor", choices=TUTOR_NAMES)
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
    combos = valid_combos()
    if not combos:
        raise StoryError("No valid mystery combos.")
    sid, mid = rng.choice([c for c in combos if (args.setting is None or c[0] == args.setting)
                           and (args.mystery is None or c[1] == args.mystery)])
    helper = args.helper or "hij"
    hero = args.hero or rng.choice(HERO_NAMES)
    tutor = args.tutor or rng.choice(TUTOR_NAMES)
    return StoryParams(sid, mid, hero, tutor, helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], MYSTERIES[params.mystery], params.hero, params.tutor, params.helper)
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
        f'Write a tall-tale mystery for a child where {f["hero"].id}, the tutor, and hij solve a missing-object riddle using the word "hop".',
        f"Tell a story about {f['hero'].id} and {f['tutor'].id} with hij, where clues lead to {f['mystery'].missing} and the mystery is solved.",
        'Create a fanciful, child-friendly mystery with a tutor, a helper named Hij, and a hopping search that ends in a clear reveal.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    m: Mystery = f["mystery"]
    return [
        ("Who was in the story?", f"It was about {f['hero'].id}, {f['tutor'].id}, and hij. They worked together like a tiny team with a big sky overhead."),
        ("What was missing?", f"{m.missing} was missing. The whole story was about finding it and learning where it had gone."),
        ("How was the mystery solved?", f"They followed clues, hopped to the right places, and used {m.solve_method}. That led them straight to the answer."),
        ("What did they find at the end?", m.reveal_line + " That proved the mystery was solved."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    m: Mystery = f["mystery"]
    return [
        ("What is a tutor?", "A tutor is a helper who teaches and explains things carefully."),
        ("What does hop mean?", "To hop means to jump a little way, usually with one quick spring."),
        ("Who or what is Hij in this story?", "Hij is a quick helper who can scamper, sniff, and help search for clues."),
        ("What is a mystery?", "A mystery is a puzzle about something missing or unknown, and clues help solve it."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"  {e.id:10} {e.kind:9} meters={e.meters} memes={e.memes} role={e.role}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, M) :- setting(S), mystery(M).
solved(M) :- mystery(M), clue_one(M,_), clue_two(M,_), clue_three(M,_).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combos differ.")
        rc = 1
    try:
        s = generate(StoryParams("ridge_town", "lost_key", "Nell", "Tutor Mara", "hij"))
        _ = s.story
        print("OK: smoke test generation succeeded.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


CURATED = [
    StoryParams("ridge_town", "lost_key", "Nell", "Tutor Mara", "hij"),
    StoryParams("river_ford", "lost_lunch", "Toby", "Tutor Jo", "hij"),
    StoryParams("mesa_village", "missing_map", "June", "Tutor Bess", "hij"),
]


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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for s, m in asp_valid_combos():
            print(s, m)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen = set()
        while len(samples) < args.n and i < max(50, args.n * 50):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story not in seen:
                samples.append(s)
                seen.add(s.story)
            i += 1
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

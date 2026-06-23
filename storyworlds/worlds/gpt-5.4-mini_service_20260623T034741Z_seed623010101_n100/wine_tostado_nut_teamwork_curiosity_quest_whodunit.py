#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T034741Z_seed623010101_n100/wine_tostado_nut_teamwork_curiosity_quest_whodunit.py
===============================================================================================================================

A tiny whodunit storyworld about a kitchen mystery: a missing toast, a spilled
wineglass, and a shelled nut that becomes the clue. The world keeps track of
typed entities, physical meters, and emotional memes, then renders a complete
child-facing mystery with a clue-hunt, teamwork, curiosity, and a solved ending.
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
    role: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Scene:
    place: str
    hidden_spot: str
    clue_spot: str
    afford: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    place: str
    tags: set[str] = field(default_factory=set)
    risk: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass
class StoryParams:
    scene: str = "kitchen"
    suspect: str = "owl"
    clue: str = "nut"
    hero: str = "Mina"
    hero_type: str = "girl"
    helper: str = "Jude"
    helper_type: str = "boy"
    adult: str = "mother"
    seed: Optional[int] = None


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.items: dict[str, Item] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_item(self, item: Item) -> Item:
        self.items[item.id] = item
        return item

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
        clone = World(self.scene)
        clone.entities = copy.deepcopy(self.entities)
        clone.items = copy.deepcopy(self.items)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def locate_clue(world: World, clue_id: str) -> bool:
    sim = world.copy()
    _search(sim, clue_id, narrate=False)
    return bool(sim.facts.get("found_clue"))


def _search(world: World, clue_id: str, narrate: bool = True) -> None:
    item = world.items[clue_id]
    seeker = world.get("hero")
    helper = world.get("helper")
    seeker.memes["curiosity"] += 1
    helper.memes["teamwork"] += 1
    if item.place == world.scene.hidden_spot:
        item.meters["seen"] += 1
        world.facts["found_clue"] = True
        if narrate:
            world.say(f"They found the {item.label} right where the odd stain had led them.")
    else:
        world.facts["found_clue"] = False
        if narrate:
            world.say(f"They checked the {item.place}, but the clue was not there.")


def raise_mystery(world: World, suspect: Entity, clue: Item) -> None:
    suspect.memes["suspense"] += 1
    clue_item = world.items[clue.id]
    clue_item.meters["odd"] += 1
    world.say(
        f"At breakfast, a little whodunit began: a glass of wine had tipped, "
        f"the toast was gone, and a {clue.label} lay where no one expected it."
    )
    world.say(
        f"{world.get('hero').id} and {world.get('helper').id} glanced at one another. "
        f"They both wanted to know who had moved the snack."
    )


def inspect_scene(world: World, clue: Item) -> None:
    h = world.get("hero")
    helper = world.get("helper")
    h.memes["curiosity"] += 1
    helper.memes["curiosity"] += 1
    world.say(
        f"The two children started a careful quest. {h.id} looked by the table, "
        f"and {helper.id} checked the sink, because teamwork could solve what one pair of eyes might miss."
    )
    if clue.place == world.scene.clue_spot:
        world.say(f"A shiny crumb trail pointed toward the {clue.place}.")
    else:
        world.say(f"The room stayed puzzlingly neat, so they had to look slower and closer.")


def solve_mystery(world: World, suspect: Entity, clue: Item) -> None:
    h = world.get("hero")
    helper = world.get("helper")
    suspect.meters["caught"] += 1
    h.memes["joy"] += 1
    helper.memes["joy"] += 1
    h.memes["teamwork"] += 1
    helper.memes["teamwork"] += 1
    world.say(
        f"At last, they saw the answer: the {clue.label} had been tucked near the bread box, "
        f"and the real trick was that the little {suspect.label} had nudged the plate while hunting crumbs."
    )
    world.say(
        f"{h.id} laughed first, then {helper.id} did too. They solved the mystery together, "
        f"and even the grown-up smiled at their clever teamwork."
    )


def tell(scene: Scene, suspect: Entity, clue: Item, hero_name: str, hero_type: str,
         helper_name: str, helper_type: str, adult_type: str) -> World:
    world = World(scene)
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name))
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label=helper_name))
    adult = world.add(Entity(id="adult", kind="character", type=adult_type, label=adult_type))
    world.add(Entity(id="suspect", kind="character", type=suspect.type, label=suspect.label))
    world.add_item(clue)

    hero.memes["curiosity"] = 1.0
    helper.memes["teamwork"] = 1.0
    adult.memes["calm"] = 1.0
    world.facts["scene"] = scene
    world.facts["hero"] = hero
    world.facts["helper"] = helper
    world.facts["suspect"] = suspect
    world.facts["clue"] = clue
    world.facts["adult"] = adult

    world.say(
        f"In the {scene.place}, {hero_name} and {helper_name} found a strange little mystery. "
        f"Someone had left a cup with wine, the toast was missing, and a {clue.label} was out of place."
    )
    world.say(
        f"{hero_name} loved a good quest, and {helper_name} loved helping, so the two of them began to look around."
    )

    world.para()
    inspect_scene(world, clue)
    world.say(f"{adult_type.capitalize()} said, \"Look carefully and work together.\"")

    world.para()
    _search(world, clue.id, narrate=True)
    if not world.facts.get("found_clue"):
        world.say(f"They were not ready to give up, so they checked one more corner and found the clue at last.")
        world.facts["found_clue"] = True

    world.para()
    solve_mystery(world, suspect, clue)
    world.facts["solved"] = True
    return world


SCENES = {
    "kitchen": Scene(place="the kitchen", hidden_spot="bread box", clue_spot="bread box", afford={"quest", "teamwork", "curiosity"}),
    "pantry": Scene(place="the pantry", hidden_spot="shelf", clue_spot="shelf", afford={"quest", "teamwork", "curiosity"}),
    "dining": Scene(place="the dining room", hidden_spot="table corner", clue_spot="table corner", afford={"quest", "teamwork", "curiosity"}),
}

SUSPECTS = {
    "owl": Entity(id="owl", kind="character", type="animal", label="owl", tags={"mystery"}),
    "cat": Entity(id="cat", kind="character", type="animal", label="cat", tags={"mystery"}),
    "mouse": Entity(id="mouse", kind="character", type="animal", label="mouse", tags={"mystery"}),
}

CLUES = {
    "nut": Item(id="nut", label="nut", phrase="a little nut", place="bread box", tags={"nut", "quest"}, risk="crumb"),
    "tostado": Item(id="tostado", label="tostado", phrase="a tostado crumb", place="bread box", tags={"tostado", "quest"}, risk="crumb"),
    "wine": Item(id="wine", label="wine", phrase="a spilled splash of wine", place="table", tags={"wine", "mystery"}, risk="spill"),
}

GIRL_NAMES = ["Mina", "Ava", "Luna", "Nia", "Rosa", "Ivy"]
BOY_NAMES = ["Jude", "Leo", "Theo", "Noah", "Milo", "Eli"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SCENES:
        for sus in SUSPECTS:
            for clue in CLUES:
                out.append((s, sus, clue))
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short whodunit story for a young child that includes the words "{f["clue"].label}", "wine", and "tostado".',
        f"Tell a mystery where {f['hero'].label} and {f['helper'].label} use teamwork and curiosity to solve what happened in {f['scene'].place}.",
        "Write a gentle quest story where two children follow a clue and discover the answer together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"].label
    helper = f["helper"].label
    scene = f["scene"].place
    clue = f["clue"].label
    suspect = f["suspect"].label
    return [
        QAItem(
            question=f"Who worked together to solve the mystery in {scene}?",
            answer=f"{hero} and {helper} worked together. Their teamwork helped them follow the clue and finish the quest.",
        ),
        QAItem(
            question=f"What clue did {hero} and {helper} look for?",
            answer=f"They looked for the {clue}. It helped them figure out what was out of place near the bread box.",
        ),
        QAItem(
            question=f"What did they learn from the strange wine and missing toast?",
            answer=f"They learned that the little {suspect} had nudged the plate while hunting crumbs. The clue showed them how the mystery happened.",
        ),
        QAItem(
            question=f"How did curiosity help {hero} and {helper}?",
            answer=f"Curiosity made them keep looking instead of stopping too soon. Because they stayed curious, they found the answer together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["clue"].tags)
    out = []
    if "nut" in tags:
        out.append(QAItem("What is a nut?", "A nut is a small hard food with a shell or a hard outside. Many animals and people eat nuts as a snack."))
    if "tostado" in tags:
        out.append(QAItem("What does tostado mean?", "Tostado means toasted or browned. It usually describes bread or food that has been warmed until it turns a little crisp."))
    if "wine" in tags:
        out.append(QAItem("What is wine?", "Wine is a drink made from grapes. It is for grown-ups, not for children."))
    out.append(QAItem("What is teamwork?", "Teamwork means people help each other to do something. Working together can make a hard job easier."))
    out.append(QAItem("What is curiosity?", "Curiosity is the wish to ask questions and find out what is true. Curious children keep looking until they understand the clue."))
    out.append(QAItem("What is a quest?", "A quest is a search for something important or interesting. In stories, a quest is often a brave little journey to find an answer."))
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    for i, it in world.items.items():
        lines.append(f"  {i:8} (item   ) place={it.place} tags={sorted(it.tags)}")
    return "\n".join(lines)


ASP_RULES = r"""
found_clue :- clue(C), clue_place(C, P), clue_spot(P).
solved :- found_clue, teamwork, curiosity, quest.
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid, scene in SCENES.items():
        lines.append(asp.fact("scene", sid))
        lines.append(asp.fact("clue_spot", scene.clue_spot))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("clue_place", cid, clue.place))
    lines.append(asp.fact("teamwork", "teamwork"))
    lines.append(asp.fact("curiosity", "curiosity"))
    lines.append(asp.fact("quest", "quest"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show solved/0."))
    asp_ok = bool(model)
    py_ok = True
    sample = generate(resolve_params(argparse.Namespace(scene=None, suspect=None, clue=None, hero=None, hero_type=None, helper=None, helper_type=None, adult=None), random.Random(1)))
    py_ok = sample.world.facts.get("solved", False)
    if asp_ok and py_ok:
        print("OK: ASP and Python both solve the mystery.")
    else:
        print("MISMATCH: ASP or Python failed the smoke test.")
        return 1
    # smoke-test normal generation/emit
    emit(sample)
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world sketch: a child-friendly whodunit about teamwork, curiosity, and a quest.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-type", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=["mother", "father"])
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
    combos = [c for c in combos
              if args.scene is None or c[0] == args.scene
              if args.suspect is None or c[1] == args.suspect
              if args.clue is None or c[2] == args.clue]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    scene, suspect, clue = rng.choice(list(combos))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or ("boy" if hero_type == "girl" else "girl")
    hero = args.hero or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(GIRL_NAMES if helper_type == "girl" else BOY_NAMES)
    adult = args.adult or rng.choice(["mother", "father"])
    return StoryParams(scene=scene, suspect=suspect, clue=clue, hero=hero, hero_type=hero_type, helper=helper, helper_type=helper_type, adult=adult)


def generate(params: StoryParams) -> StorySample:
    if params.scene not in SCENES or params.suspect not in SUSPECTS or params.clue not in CLUES:
        raise StoryError("Invalid params.")
    scene = SCENES[params.scene]
    suspect = SUSPECTS[params.suspect]
    clue = copy.deepcopy(CLUES[params.clue])
    clue.place = scene.hidden_spot
    world = tell(scene, suspect, clue, params.hero, params.hero_type, params.helper, params.helper_type, params.adult)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


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
    StoryParams(scene="kitchen", suspect="owl", clue="nut", hero="Mina", hero_type="girl", helper="Jude", helper_type="boy", adult="mother"),
    StoryParams(scene="pantry", suspect="cat", clue="tostado", hero="Ava", hero_type="girl", helper="Leo", helper_type="boy", adult="father"),
    StoryParams(scene="dining", suspect="mouse", clue="wine", hero="Theo", hero_type="boy", helper="Luna", helper_type="girl", adult="mother"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show solved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show solved/0."))
        print("solved:", bool(model))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = [generate(p) for p in CURATED] if args.all else []
    if not args.all:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False, default=str))
        return
    for idx, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {idx + 1}" if len(samples) > 1 else "")
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

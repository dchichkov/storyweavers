#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260622T034914Z_seed1855084837_n10/award_patty_dialogue_teamwork_rhyming_story.py
===============================================================================================================

A tiny standalone storyworld for an award-and-patty tale with dialogue,
teamwork, and a rhyming-story feel.

A short seed tale imagined into world state:
---
Mina and Bo loved the fair's cooking day. They wanted to make the best patty
for the judges. Mina mixed, Bo shaped, and they sang little rhymes while they
worked. The patty slipped and fell apart, so they teamed up again, added crumbs
to hold it tight, and tried once more. In the end their neat patty earned an
award, and they smiled at the shiny ribbon.

The world model below keeps that premise small:
- physical meters: mixed, shaped, messy, neat, warm, dropped
- emotional memes: joy, worry, pride, teamwork, confidence

The story is rendered from state changes, not from a frozen paragraph.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    owner: str = ""
    plural: bool = False
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
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))


@dataclass
class TeamworkScene:
    place: str
    contest: str
    award_name: str
    dish_name: str
    patty_word: str
    rhymes: list[str] = field(default_factory=list)
    tags: set[str] = field(default_factory=set)
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class StoryParams:
    place: str
    contest: str
    award_name: str
    dish_name: str
    patty_word: str
    child1_name: str
    child1_gender: str
    child2_name: str
    child2_gender: str
    helper_name: str
    helper_gender: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


class World:
    def __init__(self, scene: TeamworkScene) -> None:
        self.scene = scene
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
        return [e for e in self.entities.values() if e.kind == "character"]

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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("teamwork_started") and world.facts.get("shared_task_done") and ("teamwork",) not in world.fired:
        world.fired.add(("teamwork",))
        for kid in world.facts["kids"]:
            kid.memes["teamwork"] += 1
            kid.memes["joy"] += 1
        out.append("__teamwork__")
    return out


def _r_neat_patty(world: World) -> list[str]:
    out: list[str] = []
    patty = world.get("patty")
    if patty.meters["shaped"] >= THRESHOLD and patty.meters["crumbs"] >= THRESHOLD and patty.meters["dropped"] < THRESHOLD:
        if ("neat",) not in world.fired:
            world.fired.add(("neat",))
            patty.meters["neat"] += 1
            out.append("__neat__")
    return out


CAUSAL_RULES = [Rule("teamwork", "social", _r_teamwork), Rule("neat_patty", "physical", _r_neat_patty)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def rhyme(a: str, b: str) -> str:
    return f"{a} and {b} in a bright little line"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for contest in CONTESTS:
            for award_name in AWARDS:
                if award_name == "gold ribbon" or contest != "picnic":
                    combos.append((place, contest, award_name))
    return combos


def explain_rejection(place: str, contest: str, award_name: str) -> str:
    return f"(No story: the {contest} at {place} does not fit the {award_name} prize.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming teamwork story about a patty and an award.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--contest", choices=CONTESTS)
    ap.add_argument("--award-name", choices=AWARDS, dest="award_name")
    ap.add_argument("--dish-name", choices=DISHES, dest="dish_name")
    ap.add_argument("--patty-word", choices=PATTY_WORDS, dest="patty_word")
    ap.add_argument("--child1-name")
    ap.add_argument("--child1-gender", choices=["girl", "boy"])
    ap.add_argument("--child2-name")
    ap.add_argument("--child2-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
              and (args.contest is None or c[1] == args.contest)
              and (args.award_name is None or c[2] == args.award_name)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, contest, award_name = rng.choice(sorted(combos))
    dish_name = args.dish_name or rng.choice(DISHES)
    patty_word = args.patty_word or rng.choice(PATTY_WORDS)
    child1_gender = args.child1_gender or rng.choice(["girl", "boy"])
    child2_gender = args.child2_gender or ("boy" if child1_gender == "girl" else "girl")
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    child1_name = args.child1_name or rng.choice(GIRL_NAMES if child1_gender == "girl" else BOY_NAMES)
    child2_name = args.child2_name or rng.choice([n for n in (GIRL_NAMES if child2_gender == "girl" else BOY_NAMES) if n != child1_name])
    helper_name = args.helper_name or rng.choice(GIRL_NAMES if helper_gender == "girl" else BOY_NAMES)
    return StoryParams(place=place, contest=contest, award_name=award_name, dish_name=dish_name, patty_word=patty_word,
                       child1_name=child1_name, child1_gender=child1_gender, child2_name=child2_name,
                       child2_gender=child2_gender, helper_name=helper_name, helper_gender=helper_gender)


def tell(scene: TeamworkScene, params: StoryParams) -> World:
    world = World(scene)
    kid1 = world.add(Entity(id=params.child1_name, kind="character", type=params.child1_gender, role="starter"))
    kid2 = world.add(Entity(id=params.child2_name, kind="character", type=params.child2_gender, role="helper"))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_gender, role="judge"))
    patty = world.add(Entity(id="patty", type="food", label=params.patty_word, phrase=f"the {params.patty_word}"))
    award = world.add(Entity(id="award", type="prize", label=params.award_name, phrase=f"the {params.award_name}"))
    world.facts["kids"] = [kid1, kid2]
    world.facts["helper"] = helper
    world.facts["patty"] = patty
    world.facts["award"] = award
    world.facts["teamwork_started"] = False
    world.facts["shared_task_done"] = False

    world.say(f"In {scene.place}, {kid1.id} and {kid2.id} came with a grin, and they rhymed as they went to begin.")
    world.say(f'"We will make a {scene.dish}!" said {kid1.id}. "{rhyme("We stir", "we whirr")}" said {kid2.id} with fun.')
    world.para()
    world.say(f"They mixed the bits in a bowl, side by side, and the batter grew thicker with teamwork and pride.")
    kid1.memes["joy"] += 1
    kid2.memes["joy"] += 1
    kid1.meters["mixed"] += 1
    kid2.meters["mixed"] += 1
    world.facts["teamwork_started"] = True

    world.say(f'Then {kid1.id} said, "I will pat," and {kid2.id} said, "I will sway," and they shaped the patty their own gentle way.')
    patty.meters["shaped"] += 1
    patty.meters["warm"] += 1
    world.facts["shared_task_done"] = True
    propagate(world, narrate=False)

    world.para()
    world.say(f"But oh, what a jingle! The {scene.patty_word} slid down with a plop and a sprinkle, and crumbs went astray in a tiny shy skip.")
    patty.meters["dropped"] += 1
    patty.meters["messy"] += 1
    kid1.memes["worry"] += 1
    kid2.memes["worry"] += 1

    world.say(f'"We can fix it," said {kid2.id}. "{rhyme("You hold the bowl", "I will roll")}"')
    world.say(f'"Right!" said {kid1.id}. "Teamwork makes bright work!"')
    patty.meters["crumbs"] += 1
    patty.meters["shaped"] += 1
    patty.meters["dropped"] = 0
    patty.meters["neat"] += 1
    kid1.memes["confidence"] += 1
    kid2.memes["confidence"] += 1
    propagate(world, narrate=False)

    world.para()
    world.say(f"At last came {helper.id} with a smile and a cheer. \"Your {scene.patty_word} is ready! The judges are near.\"")
    world.say(f'The judges gave them an {scene.award_name}, bright as a star, for the best little {scene.dish} by teamwork, hurrah!')
    kid1.memes["pride"] += 1
    kid2.memes["pride"] += 1
    award.meters["given"] += 1
    award.meters["shiny"] += 1
    world.facts["award_won"] = True
    return world


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.contest not in CONTESTS or params.award_name not in AWARDS:
        raise StoryError("(Invalid story parameters.)")
    scene = TeamworkScene(place=params.place, contest=params.contest, award_name=params.award_name, dish_name=params.dish_name, patty_word=params.patty_word)
    world = tell(scene, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short rhyming story for a small child about {f["kids"][0].id} and {f["kids"][1].id} making a {world.scene.patty_word} together and winning an {world.scene.award_name}.',
        f'Tell a teamwork tale with dialogue where the word "{world.scene.patty_word}" appears and the children earn an award at the end.',
        f'Write a bouncy rhyming story about cooking, fixing a fallen patty, and sharing the award with a helper nearby.',
    ]


def story_qa(world: World) -> list[QAItem]:
    k1, k2 = world.facts["kids"]
    helper = world.facts["helper"]
    patty = world.facts["patty"]
    award = world.facts["award"]
    scene = world.scene
    return [
        QAItem(
            question=f"Who worked together on the {scene.patty_word}?",
            answer=f"{k1.id} and {k2.id} worked together. They mixed, shaped, and fixed the {scene.patty_word} as a team.",
        ),
        QAItem(
            question=f"What happened after the {scene.patty_word} slipped at {scene.place}?",
            answer=f"They did not give up. {k2.id} spoke up, {k1.id} helped again, and they added crumbs so the {scene.patty_word} could become neat.",
        ),
        QAItem(
            question=f"Why did the children get an {scene.award_name}?",
            answer=f"They earned the {scene.award_name} because their teamwork made a tidy {scene.dish_name} and the judges liked how they helped each other.",
        ),
        QAItem(
            question=f"Who came to cheer them on near the end?",
            answer=f"{helper.id} came with a smile and a cheer, and that made the ending feel brighter for the children.",
        ),
        QAItem(
            question=f"What did the final {scene.patty_word} look like?",
            answer=f"It was neat, warm, and ready to serve. The story ends with the {scene.patty_word} looking proud enough to win an award.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help each other with the same job. It makes hard things feel easier and more fun.",
        ),
        QAItem(
            question="What is an award?",
            answer="An award is a prize or honor you get for doing something well. It can be a ribbon, a medal, or a trophy.",
        ),
        QAItem(
            question="What is a patty?",
            answer="A patty is a flat little food shape. People can make patties from meat, beans, or vegetables.",
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
    for e in list(world.entities.values()):
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
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


PLACES = ["fair", "kitchen", "school"]
CONTESTS = ["cook-off", "picnic", "festival"]
AWARDS = ["gold ribbon", "blue medal", "shiny award"]
DISHES = ["savory patty", "bean patty", "golden patty"]
PATTY_WORDS = ["patty", "little patty", "round patty"]
GIRL_NAMES = ["Mina", "Lena", "Nora", "Ava", "Ivy"]
BOY_NAMES = ["Bo", "Theo", "Max", "Ezra", "Leo"]


ASP_RULES = r"""
teamwork :- started, shared_task_done.
neat_patty :- shaped, crumbs, not dropped.
winning :- teamwork, neat_patty, award_ready.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("started"),
        asp.fact("shared_task_done"),
        asp.fact("shaped"),
        asp.fact("crumbs"),
        asp.fact("award_ready"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show teamwork/0.\n#show neat_patty/0.\n#show winning/0."))
    atoms = {sym.name for sym in model}
    ok = {"teamwork", "neat_patty", "winning"}.issubset(atoms)
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, contest=None, award_name=None, dish_name=None, patty_word=None, child1_name=None, child1_gender=None, child2_name=None, child2_gender=None, helper_name=None, helper_gender=None), random.Random(777)))
        _ = sample.story
    except Exception as exc:
        print(f"VERIFY FAILED: story generation crashed: {exc}")
        return 1
    if ok:
        print("OK: ASP twin and story generation smoke test passed.")
        return 0
    print("VERIFY FAILED: ASP twin did not produce expected atoms.")
    return 1


CURATED = [
    StoryParams(place="fair", contest="cook-off", award_name="gold ribbon", dish_name="savory patty", patty_word="patty", child1_name="Mina", child1_gender="girl", child2_name="Bo", child2_gender="boy", helper_name="Ava", helper_gender="girl"),
    StoryParams(place="school", contest="festival", award_name="blue medal", dish_name="bean patty", patty_word="little patty", child1_name="Nora", child1_gender="girl", child2_name="Theo", child2_gender="boy", helper_name="Ivy", helper_gender="girl"),
    StoryParams(place="kitchen", contest="cook-off", award_name="shiny award", dish_name="golden patty", patty_word="round patty", child1_name="Leo", child1_gender="boy", child2_name="Ava", child2_gender="girl", helper_name="Mina", helper_gender="girl"),
]


def valid_combo_filter(args: argparse.Namespace) -> list[tuple[str, str, str]]:
    combos = valid_combos()
    return [c for c in combos if (args.place is None or c[0] == args.place) and (args.contest is None or c[1] == args.contest) and (args.award_name is None or c[2] == args.award_name)]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combo_filter(args)
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, contest, award_name = rng.choice(sorted(combos))
    dish_name = args.dish_name or rng.choice(DISHES)
    patty_word = args.patty_word or rng.choice(PATTY_WORDS)
    child1_gender = args.child1_gender or rng.choice(["girl", "boy"])
    child2_gender = args.child2_gender or ("boy" if child1_gender == "girl" else "girl")
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    child1_name = args.child1_name or rng.choice(GIRL_NAMES if child1_gender == "girl" else BOY_NAMES)
    child2_pool = GIRL_NAMES if child2_gender == "girl" else BOY_NAMES
    child2_name = args.child2_name or rng.choice([n for n in child2_pool if n != child1_name])
    helper_name = args.helper_name or rng.choice(GIRL_NAMES if helper_gender == "girl" else BOY_NAMES)
    return StoryParams(
        place=place, contest=contest, award_name=award_name, dish_name=dish_name, patty_word=patty_word,
        child1_name=child1_name, child1_gender=child1_gender, child2_name=child2_name, child2_gender=child2_gender,
        helper_name=helper_name, helper_gender=helper_gender,
    )


def generate_sample(params: StoryParams) -> StorySample:
    scene = TeamworkScene(place=params.place, contest=params.contest, award_name=params.award_name, dish_name=params.dish_name, patty_word=params.patty_word, rhymes=["mix and fix", "shape and clap"], tags={"award", "patty", "teamwork", "dialogue"})
    world = tell(scene, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    return generate_sample(params)


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
        print(asp_program("#show teamwork/0.\n#show neat_patty/0.\n#show winning/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show teamwork/0.\n#show neat_patty/0.\n#show winning/0."))
        print("ASP atoms:", ", ".join(sorted(sym.name for sym in model)))
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

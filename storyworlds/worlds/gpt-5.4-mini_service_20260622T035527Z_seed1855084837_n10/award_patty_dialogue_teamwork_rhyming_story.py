#!/usr/bin/env python3
"""
storyworlds/worlds/award_patty_dialogue_teamwork_rhyming_story.py
=================================================================

A small storyworld about two children who make a patty for a fair, talk things
through, work together, and earn an award. The prose leans rhythmic and rhyming,
with concrete state changes driving the ending image.

The seed tale behind the world:
---
At the town fair, Nia wanted to sell a savory patty. But the patty kept
splitting when she tried to shape it alone. Her friend Ben came over, and they
agreed to team up. Ben held the bowl, Nia pressed the dough, and together they
made the patty neat and round. The fair judge smiled and gave them an award for
teamwork.

This world keeps the tale small and physical:
- the patty can be ragged or tidy,
- teamwork lowers mess and worry,
- dialogue helps the children choose a better method,
- the award proves the change at the end.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve()
for parent in (HERE.parent, *HERE.parents):
    if (parent / "results.py").exists():
        sys.path.insert(0, str(parent))
        break

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
    role: str = ""
    owner: str | None = None
    caretaker: str | None = None
    plural: bool = False
    tags: set[str] = field(default_factory=set)
    attrs: dict[str, Any] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister", "aunt"}
        male = {"boy", "father", "dad", "man", "brother", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def ref(self) -> str:
        return self.phrase or self.label or self.id

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Venue:
    id: str
    label: str
    place: str
    kind: str = "fair"
    tags: set[str] = field(default_factory=set)
    affords: set[str] = field(default_factory=set)


@dataclass
class Food:
    id: str
    label: str
    phrase: str
    taste: str
    shape: str
    mess: str
    clean_shape: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    use: str
    helps: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Award:
    id: str
    label: str
    phrase: str
    reason: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    venue: str
    food: str
    tool: str
    award: str
    maker: str
    maker_gender: str
    helper: str
    helper_gender: str
    judge: str
    judge_gender: str
    seed: int | None = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, Any] = {}
        self.history: list[dict[str, Any]] = []
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple[str, str]] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, sentence: str) -> None:
        if sentence:
            self.paragraphs[-1].append(sentence)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def event(self, kind: str, **data: Any) -> None:
        self.history.append({"kind": kind, **data})

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
        clone.entities = {k: __import__("copy").deepcopy(v) for k, v in self.entities.items()}
        clone.facts = dict(self.facts)
        clone.history = list(self.history)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


def _do_mix(world: World, maker: Entity, helper: Entity, food: Food, narrate: bool = True) -> None:
    maker.meters["mess"] += 1
    helper.memes["team"] += 1
    food_id = food.id
    sig = ("mix", food_id)
    if sig not in world.fired:
        world.fired.add(sig)
        food_state = world.get(food_id)
        food_state.meters["ragged"] += 1
        if maker.meters["mess"] >= THRESHOLD:
            maker.memes["worry"] += 1
            helper.memes["focus"] += 1
    if narrate:
        pass


def teamwork_clears(world: World) -> list[str]:
    out: list[str] = []
    maker = world.get("maker")
    helper = world.get("helper")
    food = world.get("patty")
    if maker.memes["shared"] >= THRESHOLD and helper.memes["shared"] >= THRESHOLD:
        sig = ("smooth", food.id)
        if sig not in world.fired:
            world.fired.add(sig)
            food.meters["ragged"] = 0.0
            food.meters["tidy"] += 1
            maker.memes["worry"] = 0.0
            helper.memes["pride"] += 1
            out.append("Their teamwork made the patty smooth and neat.")
    return out


def dialogue_turn(world: World) -> None:
    maker = world.get("maker")
    helper = world.get("helper")
    food = world.get("patty")
    maker.memes["worry"] += 1
    helper.memes["care"] += 1
    world.say(f'{maker.id} frowned and said, "This patty is split and rough."')
    world.say(f'{helper.id} smiled and said, "Let us share the work; two hands can be enough."')
    maker.memes["shared"] += 1
    helper.memes["shared"] += 1
    _do_mix(world, maker, helper, Food(
        id="patty",
        label=food.label,
        phrase=food.phrase,
        taste=food.taste,
        shape=food.shape,
        mess=food.mess,
        clean_shape=food.clean_shape,
        tags=set(food.tags),
    ), narrate=False)
    for sent in teamwork_clears(world):
        world.say(sent)


def judge_award(world: World, judge: Entity, award: Award) -> None:
    maker = world.get("maker")
    helper = world.get("helper")
    food = world.get("patty")
    if food.meters["tidy"] >= THRESHOLD:
        maker.memes["joy"] += 1
        helper.memes["joy"] += 1
        maker.meters["award"] += 1
        helper.meters["award"] += 1
        world.say(f'{judge.id} clapped and said, "For teamwork, you both earn the {award.label}!"')
        world.say(f"The little {food.label} sat neat and round, bright as a coin at the fair.")
    else:
        raise StoryError("The patty never became neat enough for the award.")


def opening(world: World, venue: Venue, maker: Entity, helper: Entity, food: Food) -> None:
    maker.memes["desire"] += 1
    helper.memes["goodwill"] += 1
    world.say(
        f"At {venue.place}, {maker.id} had a goal in mind: make a {food.label} for the fair."
    )
    world.say(
        f'{maker.id} said, "{food.phrase} will shine if we shape it just right." '
        f'{helper.id} said, "Then let us try; together we can get it right."'
    )
    world.say(
        f"But alone, the {food.label} kept going ragged and wide, like a leaf in a windy tide."
    )


def middle(world: World, maker: Entity, helper: Entity, food: Food) -> None:
    maker.meters["mess"] += 1
    food.meters["ragged"] += 1
    maker.memes["worry"] += 1
    world.say(f'{maker.id} sighed, "I press and I press, but it will not stay."')
    world.say(f'{helper.id} answered, "I can hold the bowl while you shape away."')
    world.say("So one child held steady, and one child pressed slow, and the dough began to glow.")
    dialogue_turn(world)


def ending_image(world: World, venue: Venue, food: Food, award: Award) -> None:
    world.say(f"At the end of the day, the {food.label} was neat and round.")
    world.say(f"The {award.label} glimmered in their hands, and their smiles were fair and sound.")
    world.say(f"At {venue.place}, teamwork had turned the rough into sweet success.")


def tell(venue: Venue, food: Food, tool: Tool, award: Award,
         maker_name: str = "Nia", maker_gender: str = "girl",
         helper_name: str = "Ben", helper_gender: str = "boy",
         judge_name: str = "Mara", judge_gender: str = "woman") -> World:
    world = World()
    venue_ent = world.add(Entity(id=venue.id, kind="place", type="place", label=venue.label, phrase=venue.place, tags=set(venue.tags)))
    maker = world.add(Entity(id=maker_name, kind="character", type=maker_gender, role="maker", traits=["careful"]))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper", traits=["kind"]))
    judge = world.add(Entity(id=judge_name, kind="character", type=judge_gender, role="judge", label="the judge"))
    patty = world.add(Entity(id="patty", type="food", label=food.label, phrase=food.phrase, tags=set(food.tags)))
    world.add(Entity(id=tool.id, type="tool", label=tool.label, phrase=tool.phrase, tags=set(tool.tags)))
    world.add(Entity(id=award.id, type="award", label=award.label, phrase=award.phrase, tags=set(award.tags)))
    world.facts.update(venue=venue_ent, food=food, tool=tool, award=award, maker=maker, helper=helper, judge=judge, patty=patty)
    opening(world, venue, maker, helper, food)
    world.para()
    middle(world, maker, helper, food)
    world.para()
    judge_award(world, judge, award)
    world.para()
    ending_image(world, venue, food, award)
    return world


VENUES = {
    "fair": Venue(id="fair", label="the town fair", place="the town fair", affords={"mix", "share"}, tags={"fair", "teamwork"}),
    "kitchen": Venue(id="kitchen", label="the kitchen", place="the kitchen", affords={"mix", "share"}, tags={"kitchen", "teamwork"}),
}

FOODS = {
    "patty": Food(id="patty", label="patty", phrase="a patty", taste="savory", shape="round", mess="ragged", clean_shape="neat and round", tags={"patty", "food"}),
}

TOOLS = {
    "bowl": Tool(id="bowl", label="bowl", phrase="a bowl", use="hold", helps="steady", tags={"bowl", "teamwork"}),
    "spoon": Tool(id="spoon", label="spoon", phrase="a spoon", use="stir", helps="mix", tags={"spoon", "teamwork"}),
}

AWARDS = {
    "award": Award(id="award", label="award", phrase="an award ribbon", reason="teamwork", tags={"award", "teamwork"}),
}

GIRL_NAMES = ["Nia", "Mila", "Luna", "Tia", "Zoe", "Ava", "Maya"]
BOY_NAMES = ["Ben", "Owen", "Noah", "Levi", "Ezra", "Finn", "Leo"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    return [("fair", "patty", "bowl", "award"), ("kitchen", "patty", "spoon", "award")]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming teamwork storyworld with an award and a patty.")
    ap.add_argument("--venue", choices=VENUES)
    ap.add_argument("--food", choices=FOODS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--award", choices=AWARDS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--judge")
    ap.add_argument("--parent", choices=["mother", "father"])
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
              if (args.venue is None or c[0] == args.venue)
              and (args.food is None or c[1] == args.food)
              and (args.tool is None or c[2] == args.tool)
              and (args.award is None or c[3] == args.award)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    venue, food, tool, award = rng.choice(sorted(combos))
    maker_gender = rng.choice(["girl", "boy"])
    helper_gender = "boy" if maker_gender == "girl" else "girl"
    maker = args.name or rng.choice(GIRL_NAMES if maker_gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != maker])
    judge = args.judge or rng.choice(["Mara", "Dina", "Asha", "Ruth"])
    judge_gender = args.parent or rng.choice(["woman", "man"])
    return StoryParams(venue=venue, food=food, tool=tool, award=award, maker=maker, maker_gender=maker_gender, helper=helper, helper_gender=helper_gender, judge=judge, judge_gender=judge_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    maker = f["maker"]
    helper = f["helper"]
    food = f["food"]
    award = f["award"]
    return [
        f'Write a rhyming story for a young child about {maker.id} and {helper.id} making a {food.label} together and winning an {award.label}.',
        f"Tell a dialogue-filled teamwork story where two children shape a {food.label}, then earn the {award.label}.",
        f'Write a short, bouncy story that includes the words "{food.label}" and "{award.label}" and ends with a happy prize.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    maker = f["maker"]
    helper = f["helper"]
    food = f["food"]
    award = f["award"]
    venue = f["venue"]
    return [
        QAItem(
            question=f"What were {maker.id} and {helper.id} making at {venue.place}?",
            answer=f"They were making a {food.label} together. At first it was ragged, but shared hands made it neat.",
        ),
        QAItem(
            question=f"Why did {helper.id} help {maker.id} with the {food.label}?",
            answer=f"{helper.id} saw that the work was hard for one pair of hands. So {helper.id} teamed up and helped shape it smooth.",
        ),
        QAItem(
            question=f"What did the judge give them at the end?",
            answer=f"The judge gave them the {award.label} for teamwork. That award showed that working together made the fair treat better.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is teamwork?", "Teamwork means people work together and help each other finish a job."),
        QAItem("What is an award?", "An award is a prize that is given to someone for doing well."),
        QAItem("What is a patty?", "A patty is a small flat cake or patty-shaped food that can be cooked and served at a fair or meal."),
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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_combo(V,F,T,A) :- venue(V), food(F), tool(T), award(A), V = fair, F = patty, T = bowl, A = award.
valid_combo(V,F,T,A) :- venue(V), food(F), tool(T), award(A), V = kitchen, F = patty, T = spoon, A = award.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for v in VENUES:
        lines.append(asp.fact("venue", v))
    for f in FOODS:
        lines.append(asp.fact("food", f))
    for t in TOOLS:
        lines.append(asp.fact("tool", t))
    for a in AWARDS:
        lines.append(asp.fact("award", a))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/4."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    rc = 0
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python combos.")
        print(" only in ASP:", sorted(cl - py))
        print(" only in Python:", sorted(py - cl))
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: generate/emit smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return rc


def generate(params: StoryParams) -> StorySample:
    venue = VENUES[params.venue]
    food = FOODS[params.food]
    tool = TOOLS[params.tool]
    award = AWARDS[params.award]
    world = tell(venue, food, tool, award, params.maker, params.maker_gender, params.helper, params.helper_gender, params.judge, params.judge_gender)
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


CURATED = [
    StoryParams(venue="fair", food="patty", tool="bowl", award="award", maker="Nia", maker_gender="girl", helper="Ben", helper_gender="boy", judge="Mara", judge_gender="woman"),
    StoryParams(venue="kitchen", food="patty", tool="spoon", award="award", maker="Mila", maker_gender="girl", helper="Owen", helper_gender="boy", judge="Asha", judge_gender="woman"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_combo/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(c)
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

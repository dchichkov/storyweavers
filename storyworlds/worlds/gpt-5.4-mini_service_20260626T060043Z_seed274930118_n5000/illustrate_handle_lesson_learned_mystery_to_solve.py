#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/illustrate_handle_lesson_learned_mystery_to_solve.py
============================================================================================================

A standalone storyworld for a tall-tale-style mystery with an illustration
task, a thing to handle, foreshadowing, and a lesson learned.

The source-tale seed imagines a small, classical premise:

A child illustrator in a sunbaked frontier town is asked to make a picture that
helps solve a mystery. Along the way, the child must handle a fragile clue with
care, notice foreshadowing in the world, and learn that a good picture can show
more than it says.

The world is intentionally tiny and constraint-driven:
- one setting
- one mystery
- one fragile object to handle
- one illustrative task
- one lesson learned
- a tall-tale resolution that proves something changed

This script follows the Storyweavers world contract:
- self-contained stdlib script
- imports shared results eagerly
- imports asp lazily only in ASP helpers
- exposes StoryParams, registries, build_parser, resolve_params, generate, emit,
  and main
- supports default generation, -n, --all, --seed, --trace, --qa, --json,
  --asp, --verify, and --show-asp
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
    location: str = ""
    fragile: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt", "sister"}
        male = {"boy", "man", "father", "uncle", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the dusty frontier town"
    afford: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    question: str
    clue: str
    answer: str
    culprit: str
    foreshadow: str
    reveal: str


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    safe_to_handle: bool = True


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone


MYSTERY_REGISTRY = {
    "lost_bell": Mystery(
        id="lost_bell",
        question="Where did the town bell go?",
        clue="a single brass scrape near the porch rail",
        answer="the bell slipped into the wagon bed under a tarp",
        culprit="the wind",
        foreshadow="the tarp kept fluttering like a nervous flag",
        reveal="the bell rang once when the tarp was lifted",
    ),
    "missing_map": Mystery(
        id="missing_map",
        question="Who took the painted trail map?",
        clue="blue dust on the window sill",
        answer="the map was tucked inside the flour bin to keep it flat",
        culprit="Grandma's careful hands",
        foreshadow="the flour bin had a neat ribbon tied around it",
        reveal="the map came out white-dusted and smiling from the bin",
    ),
    "vanishing_ink": Mystery(
        id="vanishing_ink",
        question="Why did the ink vanish from the sketchbook?",
        clue="a damp blot shaped like a cloud",
        answer="the sketchbook was set near the tea kettle and the steam blurred it",
        culprit="the kettle steam",
        foreshadow="the kettle sang like a tiny train whenever it boiled",
        reveal="the lines returned only after the page dried in the sun",
    ),
}

SETTINGS = {
    "town": Setting(place="the dusty frontier town", afford={"illustrate", "handle", "investigate"}),
    "porch": Setting(place="the leaning porch of the general store", afford={"illustrate", "handle", "investigate"}),
    "stable": Setting(place="the lantern-lit stable", afford={"illustrate", "handle", "investigate"}),
}

TOOLS = {
    "sketchbook": Tool(
        id="sketchbook",
        label="sketchbook",
        phrase="a sketchbook full of wide, empty pages",
        safe_to_handle=True,
    ),
    "charcoal": Tool(
        id="charcoal",
        label="charcoal pencil",
        phrase="a charcoal pencil with a stubby black tip",
        safe_to_handle=True,
    ),
    "teacup": Tool(
        id="teacup",
        label="teacup",
        phrase="a small teacup with a blue rim",
        safe_to_handle=True,
    ),
}

PEOPLE = {
    "girl": ["Mabel", "June", "Ivy", "Lottie", "Pearl"],
    "boy": ["Cal", "Eli", "Otis", "Hank", "Benny"],
}

TRAITS = ["curious", "quick-witted", "bright-eyed", "stubborn", "cheerful", "bold"]


@dataclass
class StoryParams:
    setting: str
    mystery: str
    name: str
    gender: str
    parent: str
    trait: str
    tool: str
    seed: Optional[int] = None


def aspiration_text() -> str:
    return "A tall tale can start small and still grow as wide as the sky."


def reasonableness_gate(params: StoryParams) -> None:
    mystery = MYSTERY_REGISTRY[params.mystery]
    tool = TOOLS[params.tool]
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if not tool.safe_to_handle:
        raise StoryError("The chosen tool is too dangerous for this little tale.")
    if not mystery.question:
        raise StoryError("The mystery must have a clear question.")
    if params.gender not in PEOPLE:
        raise StoryError("Unknown gender.")
    if params.name not in PEOPLE[params.gender]:
        raise StoryError("The chosen name does not fit the requested gender list.")


def foreshadow_phrase(mystery: Mystery, tool: Tool) -> str:
    if mystery.id == "lost_bell":
        return mystery.foreshadow + " The brass bell had a habit of answering the wind."
    if mystery.id == "missing_map":
        return mystery.foreshadow + " Everyone in town knew the flour bin had a memory for keeping flat things."
    return mystery.foreshadow + " Steam had a sneaky way of turning sharp lines soft."


def introduction(world: World, hero: Entity, parent: Entity, tool: Entity, mystery: Mystery) -> None:
    world.say(
        f"{hero.id} was a {hero.traits[0]} little {hero.type} who lived in {world.setting.place}."
    )
    world.say(
        f"{hero.pronoun().capitalize()} loved to illustrate big ideas in a small sketchbook, "
        f"and {hero.pronoun('possessive')} {parent.label} always said that a good picture could ride farther than a horse."
    )
    world.say(
        f"One day, {hero.id} was given {tool.phrase} and asked to help solve a mystery: "
        f"{mystery.question}"
    )


def handle_scene(world: World, hero: Entity, tool: Entity, mystery: Mystery) -> None:
    hero.memes["care"] = hero.memes.get("care", 0.0) + 1
    tool.meters["handled"] = tool.meters.get("handled", 0.0) + 1
    world.say(
        f"{hero.id} had to handle the {tool.label} gently, because the clue was fragile and the truth was easy to smudge."
    )
    world.say(
        f"{hero.pronoun().capitalize()} noticed {mystery.clue}, which was the sort of detail that could whisper before it could shout."
    )


def investigate_scene(world: World, hero: Entity, mystery: Mystery) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
    world.say(
        f"{hero.id} walked from fence to fence, looking high and low, while the town held its breath like a possum in a hat."
    )
    world.say(
        f"That was when {hero.id} spotted the first sign of foreshadowing: {mystery.foreshadow}."
    )


def turn_scene(world: World, hero: Entity, parent: Entity, tool: Entity, mystery: Mystery) -> None:
    hero.memes["doubt"] = hero.memes.get("doubt", 0.0) + 1
    world.say(
        f"At first, {hero.id} guessed wrong and drew the most obvious thing in sight, but {hero.pronoun('possessive')} {parent.label} shook {parent.pronoun('possessive')} head."
    )
    world.say(
        f'"Don\'t grab the biggest answer first," {parent.id} said. "Handle the small clue, and the mystery may handle itself."'
    )
    world.say(
        f"{hero.id} tried again, this time illustrating the clue instead of the guess, and the picture began to point like a compass."
    )


def reveal_scene(world: World, hero: Entity, parent: Entity, mystery: Mystery) -> None:
    hero.memes["insight"] = hero.memes.get("insight", 0.0) + 1
    hero.memes["confidence"] = hero.memes.get("confidence", 0.0) + 1
    world.say(
        f"When the town finally followed the drawing, the answer came loping out with a grin: {mystery.answer}."
    )
    world.say(
        f"Then the clue proved itself plain as daylight, and the whole town saw how the sketch had been telling the truth all along."
    )
    world.say(
        f"{hero.id} learned the lesson: a mystery gets smaller when you handle it carefully and illustrate what you truly notice."
    )


def ending_image(world: World, hero: Entity, mystery: Mystery) -> None:
    world.say(
        f"By sunset, {hero.id}'s sketchbook held the answer, the mystery was solved, and {hero.pronoun('possessive')} drawing showed a truth bigger than the town itself."
    )


def tell_story(world: World, hero: Entity, parent: Entity, tool: Entity, mystery: Mystery) -> None:
    introduction(world, hero, parent, tool, mystery)
    world.para()
    handle_scene(world, hero, tool, mystery)
    investigate_scene(world, hero, mystery)
    world.para()
    turn_scene(world, hero, parent, tool, mystery)
    reveal_scene(world, hero, parent, mystery)
    ending_image(world, hero, mystery)


def choose_name(gender: str, rng: random.Random) -> str:
    return rng.choice(PEOPLE[gender])


def choose_setting_and_mystery(rng: random.Random) -> tuple[str, str]:
    settings = sorted(SETTINGS)
    mysteries = sorted(MYSTERY_REGISTRY)
    return rng.choice(settings), rng.choice(mysteries)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting_id, setting in SETTINGS.items():
        for mystery_id in MYSTERY_REGISTRY:
            for tool_id in TOOLS:
                if "illustrate" in setting.afford and "handle" in setting.afford:
                    combos.append((setting_id, mystery_id, tool_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall tale for a child about how {f["hero"].id} used a {f["tool"].label} to illustrate a mystery and handle a fragile clue.',
        f"Tell a frontier story where {f['hero'].id} learns that careful handling can help solve {f['mystery'].question.lower()}.",
        "Make the story feel like a tall tale, with a foreshadowing clue and a lesson learned at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    mystery: Mystery = f["mystery"]
    tool: Entity = f["tool"]
    return [
        QAItem(
            question=f"What was {hero.id} asked to do in the story?",
            answer=(
                f"{hero.id} was asked to illustrate a mystery and handle a fragile clue with care."
            ),
        ),
        QAItem(
            question=f"Why did {hero.pronoun('possessive')} {parent.label} tell {hero.id} to be careful?",
            answer=(
                f"{parent.id} knew the clue was fragile, so careful handling would keep the answer from getting smudged or lost."
            ),
        ),
        QAItem(
            question=f"What clue foreshadowed the answer to the mystery?",
            answer=(
                f"The foreshadowing clue was {mystery.clue}, and it pointed toward the answer before the reveal."
            ),
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn by the end?",
            answer=(
                f"{hero.id} learned that if you handle a clue carefully and illustrate what you truly see, a mystery can become clear."
            ),
        ),
        QAItem(
            question=f"What did the sketchbook help {hero.id} do?",
            answer=(
                f"The sketchbook helped {hero.id} make a picture that solved the mystery."
            ),
        ),
        QAItem(
            question=f"What was the answer to the mystery in this story?",
            answer=f"The answer was: {mystery.answer}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to illustrate something?",
            answer="To illustrate something means to draw or make a picture that helps show an idea or story.",
        ),
        QAItem(
            question="What does it mean to handle something carefully?",
            answer="To handle something carefully means to hold or use it gently so it does not get broken or damaged.",
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is a clue that hints at something important before it happens.",
        ),
        QAItem(
            question="What is a mystery to solve?",
            answer="A mystery to solve is a problem or question with an answer that is hidden at first.",
        ),
        QAItem(
            question="Why do people keep sketchbooks?",
            answer="People keep sketchbooks to save drawings, plan pictures, and collect ideas.",
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.fragile:
            bits.append("fragile=True")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- hero_name(H).
mystery(M) :- mystery_id(M).
tool(T) :- tool_id(T).

careful_story(H, M, T) :- hero(H), mystery(M), tool(T).
foreshadow(M) :- mystery(M).

solved(H, M) :- careful_story(H, M, _), foreshadow(M).
lesson_learned(H) :- solved(H, _).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for gid in sorted(PEOPLE):
        lines.append(asp.fact("gender", gid))
    for setting_id in sorted(SETTINGS):
        lines.append(asp.fact("setting_id", setting_id))
        for act in sorted(SETTINGS[setting_id].afford):
            lines.append(asp.fact("affords", setting_id, act))
    for mystery_id in sorted(MYSTERY_REGISTRY):
        lines.append(asp.fact("mystery_id", mystery_id))
    for tool_id in sorted(TOOLS):
        lines.append(asp.fact("tool_id", tool_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show careful_story/3.\n#show lesson_learned/1.\n#show solved/2."))
    atoms = set(str(a) for a in model)
    if atoms:
        print("OK: ASP program grounded successfully.")
        return 0
    print("MISMATCH: ASP program produced no visible atoms.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale mystery world: illustrate, handle, foreshadow, and learn.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERY_REGISTRY)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=sorted(PEOPLE))
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(sorted(SETTINGS))
    mystery = args.mystery or rng.choice(sorted(MYSTERY_REGISTRY))
    tool = args.tool or rng.choice(sorted(TOOLS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or choose_name(gender, rng)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    params = StoryParams(setting=setting, mystery=mystery, name=name, gender=gender, parent=parent, trait=trait, tool=tool)
    reasonableness_gate(params)
    return params


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    mystery = MYSTERY_REGISTRY[params.mystery]
    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, traits=[params.trait, "little"]))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=params.parent))
    tool = world.add(Entity(id=params.tool, type=params.tool, label=TOOLS[params.tool].label, phrase=TOOLS[params.tool].phrase, fragile=False))
    clue = world.add(Entity(id="clue", type="thing", label="clue", phrase=mystery.clue, fragile=True))

    world.facts.update(hero=hero, parent=parent, tool=tool, clue=clue, mystery=mystery, setting=setting)
    tell_story(world, hero, parent, tool, mystery)
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
    StoryParams(setting="town", mystery="lost_bell", name="Mabel", gender="girl", parent="mother", trait="curious", tool="sketchbook"),
    StoryParams(setting="porch", mystery="missing_map", name="Cal", gender="boy", parent="father", trait="bright-eyed", tool="charcoal"),
    StoryParams(setting="stable", mystery="vanishing_ink", name="Ivy", gender="girl", parent="mother", trait="bold", tool="teacup"),
]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show careful_story/3."))
    return sorted(set(asp.atoms(model, "careful_story")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show careful_story/3.\n#show lesson_learned/1.\n#show solved/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} ASP-compatible story skeletons")
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
            header = f"### {p.name}: {p.mystery} with {p.tool} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

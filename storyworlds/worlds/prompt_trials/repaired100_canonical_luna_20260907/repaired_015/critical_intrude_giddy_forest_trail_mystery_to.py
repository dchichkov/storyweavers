#!/usr/bin/env python3
"""
A gentle bedtime mystery on a forest trail, where a critical clue, an intruding
sound, and a giddy helper lead Luna to a kind solution.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(HERE))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Mystery:
    key: str
    object_name: str
    clue: str
    discovery: str
    solution: str
    ending: str


@dataclass
class StoryParams:
    name: str
    helper: str
    mystery: str
    clue_style: str
    seed: Optional[int] = None


NAMES = ["Luna", "Milo", "Nora", "Theo", "Pip", "Iris"]
HELPERS = ["a giddy squirrel", "a giddy robin", "a giddy fox"]
CLUE_STYLES = ["tracks", "sound", "feathers", "leaves"]

MYSTERIES = [
    Mystery(
        key="lantern",
        object_name="the moon lantern",
        clue="three tiny paw prints circled the cold lantern post",
        discovery="the lantern was tucked beneath a fern beside a dry stump",
        solution="a hedgehog had dragged it away from the damp path to make a warm little shelter",
        ending="The moon lantern glowed beside the trail, and its light made a soft golden bridge through the trees.",
    ),
    Mystery(
        key="bell",
        object_name="the blue trail bell",
        clue="a bright blue thread was caught on a thorn near the sign",
        discovery="the bell hung from a low cedar branch",
        solution="a gust had lifted the loose bell cord, and a jay had tugged it higher while chasing the blue thread",
        ending="The blue bell chimed once in the sleepy forest, as if it were saying good night.",
    ),
    Mystery(
        key="map",
        object_name="the folded trail map",
        clue="a line of pale seeds pointed away from the picnic stone",
        discovery="the map rested inside a hollow log",
        solution="a mouse had carried the map there while gathering paper for a nest",
        ending="The map returned to its pocket, while the pale seeds shone like a tiny path of stars.",
    ),
    Mystery(
        key="ribbon",
        object_name="the red trail ribbon",
        clue="a red fiber clung to a bramble beside a muddy paw mark",
        discovery="the ribbon was looped around a fallen branch",
        solution="a young deer had brushed the ribbon loose and carried it a little way before dropping it",
        ending="The red ribbon fluttered safely from the trail post, bright as a bedtime bookmark.",
    ),
]

@dataclass
class World:
    setting: str = "the forest trail"
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def choose(items, key):
    for item in items:
        if item.key == key:
            return item
    raise StoryError(f"Unknown choice: {key}")


def complete_params(params: StoryParams) -> None:
    if params.mystery not in {m.key for m in MYSTERIES}:
        raise StoryError(f"Unknown mystery: {params.mystery}")
    if params.clue_style not in CLUE_STYLES:
        raise StoryError(f"Unknown clue style: {params.clue_style}")
    if not params.name.strip():
        raise StoryError("A story needs a child's name.")
    if not params.helper.strip():
        raise StoryError("A story needs a helper.")


def build_world(params: StoryParams) -> World:
    complete_params(params)
    mystery = choose(MYSTERIES, params.mystery)
    w = World()
    child = w.add(Entity(
        id="child",
        type="child",
        label=params.name,
        meters={"curiosity": 1.0, "worry": 0.0, "courage": 0.0},
        memes={"mystery-solving": 1.0},
    ))
    helper = w.add(Entity(
        id="helper",
        type="animal",
        label=params.helper,
        meters={"giddiness": 2.0, "helpfulness": 1.0},
        memes={"play": 1.0},
    ))
    w.facts.update(child=child, helper=helper, mystery=mystery, params=params)
    return w


def tell(params: StoryParams) -> World:
    w = build_world(params)
    child = w.facts["child"]
    helper = w.facts["helper"]
    mystery = w.facts["mystery"]
    p = params

    w.say(
        f"At bedtime, {child.label} walked slowly along the forest trail with {helper.label}. "
        f"The trees wore silver moonlight, and every fern held a bead of dew."
    )
    w.say(
        f"Then {child.label} noticed that {mystery.object_name} was missing from its usual place. "
        f"That was a critical clue: the trail sign looked lonely without it."
    )
    child.meters["worry"] += 1
    w.say(
        f"Before {child.label} could wonder aloud, {helper.label} made a giddy hop. "
        f'"A mystery!" said {helper.label}. "Let us look carefully, not loudly."'
    )
    w.say(
        f'"I will search for {p.clue_style} clues," said {child.label}. '
        f'"And I will listen for anything that does not belong."'
    )
    w.para()

    if p.clue_style == "tracks":
        detail = f"They found {mystery.clue}."
    elif p.clue_style == "sound":
        detail = f"They heard a faint scrape, then noticed {mystery.clue}."
    elif p.clue_style == "feathers":
        detail = f"A feather trembled nearby, and beneath it they found {mystery.clue}."
    else:
        detail = f"Among the leaves, {mystery.clue} waited like a tiny arrow."
    w.say(detail)
    w.say(
        f"Just then, a loud rustle seemed to intrude on the quiet trail. "
        f"{helper.label} nearly chased it, but {child.label} lifted a careful hand."
    )
    w.say(
        f'"Wait," said {child.label}. "A sound can be a clue, but it can also be a trick of the wind." '
        f'"Good thinking," said {helper.label}. "I will be giddy quietly."'
    )
    child.meters["worry"] -= 1
    child.meters["courage"] += 1
    w.say(
        f"They followed the clue without trampling the moss. Soon they discovered that "
        f"{mystery.discovery}."
    )
    w.para()

    w.say(
        f"{mystery.object_name.capitalize()} was safe. {mystery.solution.capitalize()}."
    )
    w.say(
        f'"We solved it by noticing small things," said {child.label}. '
        f'"And by not letting the intruding rustle hurry us."'
    )
    w.say(
        f'{helper.label.capitalize()} twirled once, then whispered, "A quiet mystery has a quiet answer."'
    )
    child.meters["courage"] += 1
    child.memes["kindness"] = 1.0
    w.say(
        f"Together they returned {mystery.object_name} to its proper place and left the forest trail "
        f"tidier than they had found it."
    )
    w.say(mystery.ending)
    w.say(
        f"{child.label} and {helper.label} walked home under the sleepy branches, "
        f"carrying the best kind of mystery: one that ended with everyone safe."
    )
    return w


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    helper = world.facts["helper"]
    mystery = world.facts["mystery"]
    return [
        QAItem(
            question=f"What mystery did {child.label} try to solve on the forest trail?",
            answer=f"{child.label} tried to find {mystery.object_name}, which had disappeared from its usual place."
        ),
        QAItem(
            question=f"What critical clue helped {child.label} and {helper.label}?",
            answer=f"They noticed {mystery.clue}, which led them toward {mystery.discovery}."
        ),
        QAItem(
            question="What tried to intrude on the quiet search?",
            answer="A loud rustle intruded on the quiet trail, but the friends stopped to decide whether it was truly a clue."
        ),
        QAItem(
            question=f"How did {child.label} solve the mystery?",
            answer=f"{child.label} stayed calm, followed the small clue, and discovered that {mystery.solution}."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something puzzling that people investigate until they understand what happened."
        ),
        QAItem(
            question="Why is it important to look carefully on a trail?",
            answer="Looking carefully helps people notice clues while protecting plants, animals, and the path."
        ),
        QAItem(
            question="What does critical mean?",
            answer="Critical means very important to understanding or solving something."
        ),
        QAItem(
            question="What does giddy mean?",
            answer="Giddy means very excited and playful, sometimes so excited that a person must remember to slow down."
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    mystery = world.facts["mystery"]
    return [
        f"Write a gentle bedtime story about {p.name} solving a mystery on a forest trail.",
        f"Include a critical clue, an intruding sound, and {p.helper} acting giddy but helpful.",
        f"End with {mystery.object_name} safe and a peaceful moonlit image.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {q}" for i, q in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("setting", "forest_trail"),
        asp.fact("feature", "mystery_to_solve"),
        asp.fact("tone", "bedtime_story"),
        asp.fact("seed_word", "critical"),
        asp.fact("seed_word", "intrude"),
        asp.fact("seed_word", "giddy"),
        asp.fact("requires", "careful_clues"),
        asp.fact("requires", "kind_resolution"),
    ])


ASP_RULES = r"""
compatible_story :-
    setting(forest_trail),
    feature(mystery_to_solve),
    tone(bedtime_story),
    seed_word(critical),
    seed_word(intrude),
    seed_word(giddy),
    requires(careful_clues),
    requires(kind_resolution).
"""


def asp_program(show: str = "#show compatible_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    ok = bool(asp.atoms(model, "compatible_story"))
    if not ok:
        print("MISMATCH: ASP gate failed.")
        return 1
    for params in curated_params():
        sample = generate(params)
        if not sample.story or len(sample.story_qa) < 3:
            print("MISMATCH: generated story exercise failed.")
            return 1
    print("OK: ASP and Python gates agree; generated stories are complete.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime mystery on a forest trail.")
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--mystery", choices=[m.key for m in MYSTERIES])
    ap.add_argument("--clue-style", choices=CLUE_STYLES)
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
        name=args.name or rng.choice(NAMES),
        helper=args.helper or rng.choice(HELPERS),
        mystery=args.mystery or rng.choice(MYSTERIES).key,
        clue_style=args.clue_style or rng.choice(CLUE_STYLES),
    )


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
        print("--- trace ---")
        for entity in sample.world.entities.values():
            meters = {k: v for k, v in entity.meters.items() if v}
            memes = {k: v for k, v in entity.memes.items() if v}
            print(f"{entity.label}: meters={meters} memes={memes}")
    if qa:
        print()
        print(format_qa(sample))


def curated_params() -> list[StoryParams]:
    return [
        StoryParams("Luna", "a giddy squirrel", "lantern", "tracks", seed=11),
        StoryParams("Milo", "a giddy robin", "bell", "sound", seed=22),
        StoryParams("Nora", "a giddy fox", "map", "leaves", seed=33),
        StoryParams("Iris", "a giddy squirrel", "ribbon", "feathers", seed=44),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print(asp.atoms(model, "compatible_story"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    if args.all:
        samples = [generate(p) for p in curated_params()]
    else:
        samples = []
        seen: set[str] = set()
        for i in range(max(args.n, 0)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                samples.append(sample)
                seen.add(sample.story)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {i + 1}" if len(samples) > 1 else "",
        )
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

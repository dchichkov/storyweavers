#!/usr/bin/env python3
"""A gentle folk tale about pumpernickel, a mature choice, and a bad ending avoided."""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import hashlib
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Person:
    name: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Place:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)


@dataclass
class Loaf:
    name: str
    ingredients: list[str]
    baked: bool = False
    shared: bool = False
    meters: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    village: Place
    baker: Person
    child: Person
    loaf: Loaf
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass(frozen=True)
class Tale:
    temptation: str
    risk: str
    first_choice: str
    consequence: str
    dialogue_turn: str
    mature_choice: str
    repair: str
    lesson: str
    ending: str


VILLAGES = {
    "Millbrook": Place("Millbrook", "village"),
    "Hazel Hollow": Place("Hazel Hollow", "village"),
    "Willow End": Place("Willow End", "village"),
}

BAKERS = [
    ("Marta", "village baker"),
    ("Oren", "bread maker"),
    ("Anika", "oven keeper"),
]

CHILDREN = [
    ("Lina", "young helper"),
    ("Tomas", "curious child"),
    ("Pia", "apprentice"),
]

TALES = {
    "warm_loaf": Tale(
        temptation="Lina wanted to taste the warm loaf before the village supper",
        risk="the loaf could be ruined before hungry neighbors arrived",
        first_choice="she reached for the crisp end without asking",
        consequence="the crust cracked and the little end fell into the flour",
        dialogue_turn='"Wait," Marta said. "A hungry wish is not a command."',
        mature_choice="she stopped, told the truth, and asked how the loaf could still be saved",
        repair="brushed away the loose flour, sliced the loaf carefully, and set the fallen piece in a basket for the hens",
        lesson="being mature means telling the truth and repairing harm instead of hiding it",
        ending="the villagers shared the pumpernickel, while the hens enjoyed the fallen crust beneath the pear tree",
    ),
    "false_shortcut": Tale(
        temptation="Tomas wished to make the dark bread rise faster",
        risk="too much heat could burn the outside while leaving the middle heavy",
        first_choice="he pushed extra coals beneath the oven",
        consequence="smoke curled through the bakehouse and the oven stone grew too hot",
        dialogue_turn='"A shortcut still has a destination," Oren said. "Let us choose one worth reaching."',
        mature_choice="he admitted the shortcut and waited while Oren moved the coals safely",
        repair="opened the vent, cooled the stone, and baked the pumpernickel slowly from the beginning",
        lesson="a mature choice accepts patience when haste would harm good work",
        ending="the finished pumpernickel had a firm crust and a sweet smell that welcomed everyone home",
    ),
    "greedy_slice": Tale(
        temptation="Pia planned to hide the largest slice of pumpernickel for herself",
        risk="the smallest guests might be left with crumbs",
        first_choice="she slipped the golden slice beneath a cloth",
        consequence="her hiding place tipped, and crumbs scattered across the clean table",
        dialogue_turn='"A secret slice makes a lonely feast," Anika said. "Who should sit beside you?"',
        mature_choice="she brought out the hidden slice and asked the smallest guests to share it with her",
        repair="gathered the crumbs for the sparrows, cut the remaining bread evenly, and served every table",
        lesson="maturity turns wanting more into making room for others",
        ending="Pia's slice tasted best when six small hands reached for it together",
    ),
    "proud_recipe": Tale(
        temptation="Marta wanted to change the old recipe so everyone would praise her cleverness",
        risk="the pumpernickel might lose the deep flavor that fed the village each winter",
        first_choice="she poured in bright berries without testing a small batch",
        consequence="the berries burst and made the first loaf bitter",
        dialogue_turn='"Wisdom can listen to old hands," the miller told her. "Will you try again?"',
        mature_choice="she accepted the failed loaf and tested one small piece before changing the recipe",
        repair="returned to the measured rye, added a little molasses, and marked the tested change in the recipe book",
        lesson="a mature maker can welcome new ideas without discarding careful knowledge",
        ending="the next pumpernickel kept its dark, friendly flavor, with one new sweet note",
    ),
    "cold_kindness": Tale(
        temptation="Anika wanted to keep the last warm loaf for the bakehouse",
        risk="a tired traveler outside had no supper",
        first_choice="she turned the latch and pretended not to hear the knock",
        consequence="the traveler walked away beneath the cold moon",
        dialogue_turn='"Bread grows warmer when it is shared," the traveler called. "May I ask once more?"',
        mature_choice="she opened the door, apologized, and invited the traveler to sit by the oven",
        repair="cut the pumpernickel into generous pieces and saved flour for tomorrow's baking",
        lesson="maturity notices another person's need even when keeping everything would be easier",
        ending="the traveler left with a full belly, and the bakehouse felt warmer than its fire could explain",
    ),
}

ROUTES = ("market_day", "oven_dawn", "old_recipe", "rainy_evening", "village_fair")


ASP_RULES = r"""
baker(B) :- role(B, baker).
child(C) :- role(C, helper).
has_loaf(B, L) :- baker(B), loaf(L).
baked(L) :- loaf(L), ingredient(L, rye), ingredient(L, molasses).
mature_choice(C) :- child(C), admits_truth(C), repairs_harm(C).
good_ending(L) :- baked(L), shared(L), mature_choice(child).
valid_tale(L) :- loaf(L), baked(L), shared(L), mature_choice(child).
"""


def safe_id(text: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in text.lower()).strip("_")


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("role", "baker", "baker"),
        asp.fact("role", "child", "helper"),
        asp.fact("loaf", "pumpernickel"),
        asp.fact("ingredient", "pumpernickel", "rye"),
        asp.fact("ingredient", "pumpernickel", "molasses"),
        asp.fact("baker", "baker"),
        asp.fact("has_loaf", "baker", "pumpernickel"),
        asp.fact("admits_truth", "child"),
        asp.fact("repairs_harm", "child"),
        asp.fact("baked", "pumpernickel"),
        asp.fact("shared", "pumpernickel"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show baked/1.\n#show shared/1."))
    baked = set(asp.atoms(model, "baked"))
    shared = set(asp.atoms(model, "shared"))
    if baked == {("pumpernickel",)} and shared == {("pumpernickel",)}:
        print("OK: clingo gate matches Python reasoning.")
        return 0
    print("MISMATCH between clingo and Python reasoning.")
    print("clingo baked:", sorted(baked))
    print("clingo shared:", sorted(shared))
    return 1


def story_rng(params: StoryParams) -> random.Random:
    text = "|".join(
        str(v)
        for v in (
            params.seed,
            params.village,
            params.baker_name,
            params.child_name,
            params.tale,
            params.route,
        )
    )
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


@dataclass
class StoryParams:
    seed: Optional[int] = None
    village: str = "Millbrook"
    baker_name: str = "Marta"
    baker_role: str = "village baker"
    child_name: str = "Lina"
    child_role: str = "young helper"
    tale: str = "warm_loaf"
    route: str = "market_day"


def build_world(params: StoryParams) -> World:
    if params.village not in VILLAGES:
        raise StoryError(f"Unknown village: {params.village}")
    if params.tale not in TALES:
        raise StoryError(f"Unknown tale: {params.tale}")
    if not params.baker_name.strip() or not params.child_name.strip():
        raise StoryError("Baker and child names must not be empty.")
    return World(
        village=Place(params.village, "village"),
        baker=Person(params.baker_name, params.baker_role),
        child=Person(params.child_name, params.child_role),
        loaf=Loaf("pumpernickel", ["rye", "molasses"]),
    )


def tell_story(world: World, params: StoryParams) -> None:
    rng = story_rng(params)
    baker, child, village, loaf = world.baker, world.child, world.village, world.loaf
    tale = TALES[params.tale]

    baker.memes.update(patience=1, kindness=1)
    child.memes.update(curiosity=1, maturity=0)
    loaf.meters.update(warmth=1.0, nourishment=1.0)

    openings = {
        "market_day": f"On market day in {village.name}, {baker.name} baked a round loaf of pumpernickel, dark as garden soil and sweet with molasses.",
        "oven_dawn": f"Before dawn, the oven glowed in {village.name}, and {baker.name} placed a pumpernickel loaf beside the cooling window.",
        "old_recipe": f"In {village.name}, an old recipe named rye and molasses as the heart of pumpernickel. {baker.name} guarded the recipe, but welcomed a young helper.",
        "rainy_evening": f"Rain tapped the roofs of {village.name} while {baker.name} watched a fresh pumpernickel loaf cool by the fire.",
        "village_fair": f"When the village fair began, the smell of pumpernickel drifted from {baker.name}'s bakehouse across {village.name}.",
    }
    world.say(openings[params.route])
    world.say(f"{child.name}, the {child.role}, had been trusted to help because {tale.risk}.")
    world.say(rng.choice([
        f"{child.name} looked at the loaf and thought, {tale.temptation}.",
        f"The warm bread made {child.name} forget the careful plan, and {tale.temptation}.",
        f"Even a good helper can feel a strong wish. For {child.name}, {tale.temptation}.",
    ]))
    world.say(f"At first, {child.name} chose poorly: {tale.first_choice}.")
    world.say(f"Then came the bad ending that might have been: {tale.consequence}.")
    world.para()

    world.say(tale.dialogue_turn)
    world.say(f"{child.name} answered, \"I wanted the easy way, but I see what it has done.\"")
    world.say(f"{baker.name} replied, \"Then let your next choice show what you have learned.\"")
    world.say(f"The words changed {child.name}'s plan. {tale.mature_choice}.")
    world.say(f"That was a mature choice, not because the mistake vanished, but because {child.name} faced it.")
    child.memes["maturity"] = 1
    child.meters["harm_repaired"] = 1
    world.para()

    world.say(f"Together, they {tale.repair}.")
    loaf.baked = True
    loaf.shared = True
    loaf.meters["warmth"] = 0.6
    loaf.meters["nourishment"] = 1.0
    world.say(rng.choice([
        f"The pumpernickel was ready, and {baker.name} thanked {child.name} for choosing honesty over a quick excuse.",
        f"The bakehouse grew calm again. {baker.name} said, \"A repaired mistake can teach more than a perfect morning.\"",
        f"{child.name} measured the next ingredients slowly, while {baker.name} smiled at the new care in every motion.",
    ]))
    world.say(f"In the end, {tale.ending}.")
    world.facts.update(
        tale=tale,
        mistake=tale.first_choice,
        consequence=tale.consequence,
        mature_choice=tale.mature_choice,
        repair=tale.repair,
        lesson=tale.lesson,
        ending=tale.ending,
        solved=True,
    )


def generation_prompts(world: World) -> list[str]:
    tale = world.facts["tale"]
    return [
        f"Write a folk tale about {world.child.name} learning to make and share pumpernickel in {world.village.name}.",
        f"Include dialogue in which {world.baker.name} helps {world.child.name} make a mature choice after this mistake: {tale.consequence}.",
        f"Show how the characters avoid a bad ending by doing this: {tale.repair}. End with this image: {tale.ending}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    tale = world.facts["tale"]
    baker, child = world.baker, world.child
    return [
        QAItem(
            question=f"What did {child.name} first do wrong with the pumpernickel?",
            answer=f"{child.name} {tale.first_choice}. This led to a problem because {tale.consequence}.",
        ),
        QAItem(
            question=f"How did {baker.name}'s dialogue change {child.name}'s decision?",
            answer=f"{baker.name} reminded {child.name} that a mistake should be faced honestly. {child.name} then {tale.mature_choice}.",
        ),
        QAItem(
            question=f"Why was {child.name}'s second choice mature?",
            answer=f"It was mature because {child.name} admitted the problem and chose to repair it instead of hiding it.",
        ),
        QAItem(
            question="How was the bad ending avoided?",
            answer=f"They {tale.repair}. This protected the bread and let the village share it.",
        ),
        QAItem(
            question="What lesson did the pumpernickel teach?",
            answer=f"The lesson was that {tale.lesson}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is pumpernickel?",
            answer="Pumpernickel is a dark, hearty bread traditionally made with rye flour and often given a deep, slightly sweet flavor.",
        ),
        QAItem(
            question="What does mature mean in this story?",
            answer="Mature means taking responsibility, thinking about consequences, and choosing a helpful action even after making a mistake.",
        ),
        QAItem(
            question="Why can dialogue matter in a folk tale?",
            answer="Dialogue lets characters share wisdom and lets spoken words change what someone decides or does.",
        ),
        QAItem(
            question="What makes an ending bad?",
            answer="An ending is bad when a harmful choice is left unrepaired and the characters or their community are left worse off.",
        ),
        QAItem(
            question="Why is sharing food important in this story world?",
            answer="Sharing food turns a single loaf into welcome and care for the whole village.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    village = args.village or rng.choice(sorted(VILLAGES))
    baker_name, baker_role = rng.choice(BAKERS)
    child_name, child_role = rng.choice(CHILDREN)
    return StoryParams(
        seed=args.seed,
        village=village,
        baker_name=args.baker_name or baker_name,
        baker_role=baker_role,
        child_name=args.child_name or child_name,
        child_role=child_role,
        tale=args.tale or rng.choice(sorted(TALES)),
        route=rng.choice(ROUTES),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Folk tale about pumpernickel and a mature choice.")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    parser.add_argument("--village", choices=sorted(VILLAGES))
    parser.add_argument("--baker-name")
    parser.add_argument("--child-name")
    parser.add_argument("--tale", choices=sorted(TALES))
    return parser


def dump_trace(world: World) -> str:
    return "\n".join([
        "--- world trace ---",
        f"{world.village.name}: kind={world.village.kind} meters={world.village.meters}",
        f"{world.baker.name}: meters={world.baker.meters} memes={world.baker.memes}",
        f"{world.child.name}: meters={world.child.meters} memes={world.child.memes}",
        f"{world.loaf.name}: ingredients={world.loaf.ingredients} baked={world.loaf.baked} shared={world.loaf.shared} meters={world.loaf.meters}",
        f"lesson={world.facts['lesson']!r}",
    ])


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print("\n== prompts ==")
        for i, prompt in enumerate(sample.prompts, 1):
            print(f"{i}. {prompt}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show baked/1.\n#show shared/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show baked/1.\n#show shared/1."))
        print({
            "baked": sorted(asp.atoms(model, "baked")),
            "shared": sorted(asp.atoms(model, "shared")),
        })
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    count = 3 if args.all else args.n
    samples: list[StorySample] = []
    for i in range(count):
        params = resolve_params(args, random.Random(base_seed + i))
        params.seed = base_seed + i
        samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
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

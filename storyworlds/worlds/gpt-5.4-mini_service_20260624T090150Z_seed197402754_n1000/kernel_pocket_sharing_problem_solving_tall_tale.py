#!/usr/bin/env python3
"""
Tall Tale story world: a pocket-sized kernel, a sharing problem, and a clever fix.

A small, self-contained story simulation about a child who finds one kernel in a
pocket, wants to share, runs into a problem, and solves it in a fanciful but
grounded way. The story is driven by world state: who owns what, what fits in
the pocket, what gets shared, and how the problem changes the ending image.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Item:
    id: str
    label: str
    kind: str = "thing"
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if case == "subject":
            return "they" if self.plural else "it"
        if case == "object":
            return "them" if self.plural else "it"
        return "their" if self.plural else "its"

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Character:
    id: str
    name: str
    kind: str = "character"
    type: str = "child"
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    pocket: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the dusty lane"
    sky: str = "bright"
    affords: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    hero: str
    sidekick: str
    kernel_kind: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class NarrativePlan:
    problem_key: str
    problem: str
    first_try: str
    clue: str
    solution: str
    result: str
    shared_result: str
    kernel_location: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

    def add(self, ent):
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str):
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
        import copy
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


def _capital(s: str) -> str:
    return s[:1].upper() + s[1:]


INTRODUCTIONS = [
    "At {place}, {hero} wore a patched coat whose pocket was said to be deeper than a mine shaft. {sidekick}, {hero}'s practical friend, never believed that boast without checking.",
    "Folks around {place} said {hero} could carry a week's weather in one pocket. {sidekick} could usually sort the truth from {hero}'s tall tales.",
    "{hero} and {sidekick} measured adventures by how dusty their shoes became. That morning, they had barely reached {place} when {hero}'s pocket gave a mysterious bump.",
    "At {place}, {hero} told stories so enormous that clouds seemed to lean closer. That day, one began with a bump in {hero_poss} pocket, while {sidekick} supplied the careful questions.",
    "At {place}, {hero}'s favorite pocket had held string, chalk, and once, according to {hero}, a sleeping rainbow. {sidekick} was there when it produced a new surprise.",
    "The day began quietly at {place}, although quiet days seldom stayed quiet near {hero}. {sidekick} noticed {hero} patting one pocket as if it had whispered.",
]

DISCOVERIES = [
    "From the pocket, {hero} drew one {kernel}, small enough to balance on a fingernail.",
    "{hero} reached past a button and a loop of string and found one smooth {kernel} at the very bottom.",
    "Out rolled a lone {kernel}. It flashed in the {sky} light like a seed-sized lantern.",
    "The bump was one {kernel}, no larger than a freckle and much too interesting to ignore.",
    "When {hero} turned the pocket inside out, a single {kernel} landed in {hero_poss} palm.",
    "There was no treasure chest in the pocket, only one {kernel}. To {hero} and {sidekick}, that was treasure enough.",
]

SHARING_LINES = [
    '"Let us share it: half for you and half for me," {hero} said. {sidekick} nodded, but one tiny kernel did not come with instructions for making fair halves.',
    '"Let us share it," said {sidekick}. {hero} agreed at once; deciding how was the difficult part.',
    "Neither friend wanted the whole treasure while the other got nothing. To share it fairly, they set the {kernel} between them and studied it.",
    '"One kernel, two friends," {hero} said. "Sharing it sounds like a problem looking for an idea."',
    "The friends agreed that finding a treasure was less important than sharing it fairly. Then they discovered that fairness could require some thinking.",
]

EPISODES = [
    NarrativePlan(
        problem_key="one_seed_two_gardens",
        problem="They each had a garden patch, but cutting the kernel might keep it from growing in either one.",
        first_try="They carried it back and forth between the two patches until both had walked a furrow into the ground.",
        clue="A stripe of sunlight lay exactly across the border between the gardens.",
        solution="They dug one shared hole on that border, planted the kernel, and made a watering schedule with alternating days.",
        result="The earth lifted and a green shoot rose between the two plots, tall enough to tickle a low cloud.",
        shared_result="They shared its care and would share whatever it grew.",
        kernel_location="shared garden border",
    ),
    NarrativePlan(
        problem_key="kernel_rolls_away",
        problem="Before they could decide what to do, the round kernel rolled downhill and vanished beneath a fence.",
        first_try="{hero} reached with a stick, but every poke sent it farther into the shadow.",
        clue="{sidekick} noticed a broad dock leaf curving toward the kernel like a green slide.",
        solution="One friend trickled a cup of water down the leaf while the other held a hat at the far end.",
        result="The little current carried the kernel neatly into the waiting hat.",
        shared_result="They planted their rescued treasure and promised to tend it together.",
        kernel_location="shared planting hole",
    ),
    NarrativePlan(
        problem_key="unequal_pieces",
        problem="The kernel had one plump side and one thin side, so simply breaking it would not make equal pieces.",
        first_try="They balanced it on a twig, but the twig rolled away and the kernel nearly followed.",
        clue="A fallen leaf folded into two matching cups when {sidekick} pressed its middle vein.",
        solution="They crushed the kernel safely between two flat stones, poured the crumbs into the folded leaf, and adjusted the piles until they balanced.",
        result="The two portions matched, right down to the last golden crumb.",
        shared_result="Each friend took an equal pile to show at home, and they saved the leaf as their tiny measuring tray.",
        kernel_location="two equal leaf cups",
    ),
    NarrativePlan(
        problem_key="who_carries_it",
        problem="Both friends wanted to carry the kernel, yet it was too small for two hands to hold at once.",
        first_try="They passed it back and forth every ten steps, until a sneeze almost sent it into the grass.",
        clue="{hero} saw that the drawstrings from their two pockets could reach each other.",
        solution="They tied the strings around a little cloth pouch and carried it between them, one string in each hand.",
        result="The shared pouch swung in the middle and the kernel stayed safe as they walked.",
        shared_result="They became joint keepers and took turns choosing where their treasure went next.",
        kernel_location="shared cloth pouch",
    ),
    NarrativePlan(
        problem_key="tiny_feast",
        problem="They hoped for a snack, but the hard kernel was too small and too tough to divide with their fingers.",
        first_try="They sang a popping song at it. The kernel remained stubbornly silent.",
        clue="When they set it in an old tin cup, a warm sunbeam made the cup give a bright little ping.",
        solution="They covered the cup with a flat stone and waited in the sunshine instead of using a flame.",
        result="POP! The lid hopped, and out billowed a puff as wide as a washbasin, which is the honest truth according to {hero}.",
        shared_result="They tore the airy puff into two generous pieces and ate their ridiculous feast together.",
        kernel_location="empty tin cup and two last crumbs",
    ),
    NarrativePlan(
        problem_key="lost_in_pocket",
        problem="When {hero} reached for the kernel again, it had slipped through a hole into the coat lining.",
        first_try="They shook the coat, but the kernel only rattled from one unreachable corner to another.",
        clue="{sidekick} held the coat toward the light and spotted the kernel's round shadow.",
        solution="One friend held the lining flat while the other guided the kernel with a spoon handle toward the pocket hole.",
        result="The kernel popped back into view and landed between their two thumbs.",
        shared_result="They patched the hole together, then placed the rescued kernel in a jar they both could visit.",
        kernel_location="shared keepsake jar",
    ),
    NarrativePlan(
        problem_key="two_promises",
        problem="{hero} wanted to plant the kernel, while {sidekick} wanted to keep it as a lucky treasure.",
        first_try="They argued their cases so loudly that, in {hero}'s telling, every fence post leaned in to listen.",
        clue="A dry seedpod nearby held seeds and also made a splendid rattle.",
        solution="They planted the kernel but marked the spot with a tiny treasure flag made from their loop of string.",
        result="The flag guarded the mound, and soon a sprout curled around its stick.",
        shared_result="{hero} got a growing seed, {sidekick} got a treasure marker, and both owned the new plant.",
        kernel_location="flagged shared garden mound",
    ),
    NarrativePlan(
        problem_key="fair_game",
        problem="The kernel was too little to be a meal, and neither friend could think of a fair way to claim it.",
        first_try="They tried flipping it like a coin, but it landed on its round edge three times in a row.",
        clue="The kernel rolled around a chalk circle and stopped beside two matching stones.",
        solution="They invented a game in which the kernel was the shared marker and the stones were their playing pieces.",
        result="Soon their chalk path wound clear around {place}, at least if the longest part of {hero}'s story is believed.",
        shared_result="No one had to own the marker alone; every turn belonged to their game together.",
        kernel_location="shared game circle",
    ),
]

ENDINGS = [
    "At sunset, {image}. The empty pocket felt lighter, but the friendship beside it felt large enough to fill a wagon.",
    "By the time the sky changed color, {image}. {hero} called it the smallest treasure that had ever made such a large day.",
    "That evening, {image}. Whenever the friends told the tale later, the kernel grew smaller and their solution grew grander.",
    "As the first star appeared, {image}. {sidekick} said the best part was not the kernel at all, but the idea they had built together.",
    "Before they went home, {image}. Their two shadows stretched across {place}, side by side like the hands of one enormous clock.",
    "The problem was over when {image}. In {hero}'s next telling, even the moon applauded, though {sidekick} only promised there had been a breeze.",
]


def _fill(text: str, world: World, hero: Character, sidekick: Character, kernel: Item) -> str:
    return text.format(
        hero=hero.name,
        hero_poss=hero.pronoun("possessive"),
        sidekick=sidekick.name,
        kernel=kernel.label,
        place=world.setting.place,
        sky=world.setting.sky,
        image=world.facts.get("ending_image", "their shared solution"),
    )


def character_intro(world: World, hero: Character, sidekick: Character, kernel: Item, rng: random.Random) -> None:
    world.say(_fill(rng.choice(INTRODUCTIONS), world, hero, sidekick, kernel))


def find_kernel(world: World, hero: Character, sidekick: Character, kernel: Item, rng: random.Random) -> None:
    hero.memes["wonder"] = hero.memes.get("wonder", 0) + 1
    hero.pocket.append(kernel.id)
    kernel.carried_by = hero.id
    kernel.location = "pocket"
    world.facts["discovery"] = _fill(rng.choice(DISCOVERIES), world, hero, sidekick, kernel)
    world.say(world.facts["discovery"])


def want_to_share(world: World, hero: Character, sidekick: Character, kernel: Item, rng: random.Random) -> None:
    hero.memes["share"] = hero.memes.get("share", 0) + 1
    sidekick.memes["share"] = sidekick.memes.get("share", 0) + 1
    world.say(_fill(rng.choice(SHARING_LINES), world, hero, sidekick, kernel))


def problem_arises(world: World, hero: Character, sidekick: Character, kernel: Item, plan: NarrativePlan) -> None:
    kernel.meters["hardness"] = kernel.meters.get("hardness", 0) + 1
    hero.memes["trouble"] = hero.memes.get("trouble", 0) + 1
    world.facts["problem"] = "The sharing problem was clear: " + _fill(plan.problem, world, hero, sidekick, kernel)
    world.say(world.facts["problem"])
    world.say(_fill(plan.first_try, world, hero, sidekick, kernel))


def problem_solve(world: World, hero: Character, sidekick: Character, kernel: Item, plan: NarrativePlan) -> None:
    hero.memes["problem_solving"] = hero.memes.get("problem_solving", 0) + 1
    sidekick.memes["problem_solving"] = sidekick.memes.get("problem_solving", 0) + 1
    kernel.memes["shared"] = kernel.memes.get("shared", 0) + 1
    world.say(_fill(plan.clue, world, hero, sidekick, kernel))
    world.facts["solution"] = _fill(plan.solution, world, hero, sidekick, kernel)
    world.say(world.facts["solution"])
    world.say(_fill(plan.result, world, hero, sidekick, kernel))
    world.facts["shared_result"] = _fill(plan.shared_result, world, hero, sidekick, kernel)
    world.say(world.facts["shared_result"])
    kernel.location = plan.kernel_location
    kernel.carried_by = None
    kernel.meters["problem_solved"] = 1
    world.facts["shared_by"] = (hero.id, sidekick.id)
    world.facts["solved"] = True


def ending(world: World, hero: Character, sidekick: Character, kernel: Item, rng: random.Random) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    sidekick.memes["joy"] = sidekick.memes.get("joy", 0) + 1
    images = [
        f"{hero.name} and {sidekick.name} stood over the {kernel.location}",
        f"the friends touched two dusty thumbs above the {kernel.location}",
        f"the last light rested on the {kernel.location}",
        f"their joined footprints circled the {kernel.location}",
    ]
    world.facts["ending_image"] = rng.choice(images)
    world.say(_fill(rng.choice(ENDINGS), world, hero, sidekick, kernel))


def tell(setting: Setting, params: StoryParams) -> World:
    world = World(setting)
    rng = random.Random(params.seed if params.seed is not None else f"{params.place}|{params.hero}|{params.sidekick}|{params.kernel_kind}")
    hero = world.add(Character(id="hero", name=params.hero, traits=["curious", "generous"]))
    sidekick = world.add(Character(id="sidekick", name=params.sidekick, traits=["bright", "helpful"]))
    kernel = world.add(Item(id="kernel", label=params.kernel_kind))

    eligible_plans = [plan for plan in EPISODES if plan.problem_key != "tiny_feast" or params.kernel_kind == "popcorn kernel"]
    plan = rng.choice(eligible_plans)
    world.facts["plan"] = plan

    character_intro(world, hero, sidekick, kernel, rng)
    world.para()
    find_kernel(world, hero, sidekick, kernel, rng)
    want_to_share(world, hero, sidekick, kernel, rng)
    world.para()
    problem_arises(world, hero, sidekick, kernel, plan)
    problem_solve(world, hero, sidekick, kernel, plan)
    world.para()
    ending(world, hero, sidekick, kernel, rng)

    world.facts.update(hero=hero, sidekick=sidekick, kernel=kernel, setting=setting)
    return world


SETTINGS = {
    "lane": Setting(place="the dusty lane", sky="bright", affords={"sharing", "problem_solving"}),
    "barn": Setting(place="the old red barn", sky="golden", affords={"sharing", "problem_solving"}),
    "meadow": Setting(place="the wide meadow", sky="windy", affords={"sharing", "problem_solving"}),
}

KERNELS = {
    "popcorn kernel": "popcorn kernel",
    "golden kernel": "golden kernel",
    "bean kernel": "bean kernel",
}
ASP_KERNEL_NAMES = {
    "popcorn_kernel": "popcorn kernel",
    "golden_kernel": "golden kernel",
    "bean_kernel": "bean kernel",
}

HERO_NAMES = ["Milo", "Nina", "Jo", "Teddy", "Luz", "June", "Otis", "Penny"]
SIDEKICK_NAMES = ["Bess", "Rory", "Willa", "Pip", "Hank", "Mira", "Sol", "Bea"]


def valid_combos() -> list[tuple[str, str]]:
    return [(place, kernel) for place in SETTINGS for kernel in KERNELS]


def explain_rejection(place: str, kernel: str) -> str:
    return f"(No story: {kernel} at {place} would not give this tall-tale a clear sharing problem to solve.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale story world about a kernel in a pocket, sharing, and problem solving.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--kernel", choices=KERNELS)
    ap.add_argument("--hero")
    ap.add_argument("--sidekick")
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
    if args.place or args.kernel:
        combos = [c for c in combos if (args.place is None or c[0] == args.place) and (args.kernel is None or c[1] == args.kernel)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, kernel = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(HERO_NAMES)
    sidekick = args.sidekick or rng.choice([n for n in SIDEKICK_NAMES if n != hero])
    return StoryParams(place=place, hero=hero, sidekick=sidekick, kernel_kind=kernel)


ASP_RULES = r"""
place(lane). place(barn). place(meadow).
kernel(popcorn_kernel). kernel(golden_kernel). kernel(bean_kernel).
valid(P,K) :- place(P), kernel(K).
#show valid/2.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([asp.fact("place", p) for p in SETTINGS] + [asp.fact("kernel", k) for k in ASP_KERNEL_NAMES])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted((place, ASP_KERNEL_NAMES[kernel]) for place, kernel in set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Character = f["hero"]
    sidekick: Character = f["sidekick"]
    kernel: Item = f["kernel"]
    return [
        f'Write a tall tale for children about {hero.name} finding a {kernel.label} in a pocket and sharing it with {sidekick.name}.',
        f"Tell a problem-solving story where {hero.name} and {sidekick.name} must find a fair way to share one {kernel.label}.",
        f'Write a short story that includes the words "kernel" and "pocket" and ends with two friends sharing something tiny.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Character = f["hero"]
    sidekick: Character = f["sidekick"]
    kernel: Item = f["kernel"]
    place: Setting = f["setting"]
    return [
        QAItem(
            question=f"What did {hero.name} find in {hero.pronoun('possessive')} pocket?",
            answer=str(f["discovery"]),
        ),
        QAItem(
            question=f"What problem did {hero.name} and {sidekick.name} face?",
            answer=str(f["problem"]),
        ),
        QAItem(
            question=f"How did {hero.name} and {sidekick.name} solve the problem at {place.place}?",
            answer=str(f["solution"]),
        ),
        QAItem(
            question=f"How did the friends finally share the {kernel.label}?",
            answer=str(f["shared_result"]),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a kernel?",
            answer="A kernel is a small hard seed, like the kind that can pop into popcorn when heated.",
        ),
        QAItem(
            question="What is a pocket for?",
            answer="A pocket is a small pouch in clothing where you can carry tiny things.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use or enjoy part of something with you.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means thinking carefully and finding a way to fix a trouble or make something work.",
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
        if isinstance(e, Character):
            lines.append(f"  {e.name:8} (character) pocket={e.pocket} memes={dict(e.memes)}")
        else:
            lines.append(f"  {e.id:8} ({e.kind}) owner={e.owner} carried_by={e.carried_by} location={e.location} meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], params)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, kernel) combos:\n")
        for place, kernel in combos:
            print(f"  {place:8} {kernel}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params_list = [
            StoryParams(place=p, hero="Milo", sidekick="Bess", kernel_kind=k)
            for p, k in [(place, kernel) for place in SETTINGS for kernel in KERNELS]
        ]
        samples = [generate(p) for p in params_list]
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Explorer:
    name: str
    species: str
    meters: dict[str, float] = field(default_factory=lambda: {"energy": 1.0, "courage": 0.4})
    memes: dict[str, float] = field(default_factory=lambda: {"curiosity": 1.0, "fear": 0.2, "trust": 0.3})
    inventory: list[str] = field(default_factory=list)


@dataclass
class Companion:
    name: str
    species: str
    meters: dict[str, float] = field(default_factory=lambda: {"energy": 1.0})
    memes: dict[str, float] = field(default_factory=lambda: {"patience": 0.7, "trust": 0.4})


@dataclass
class Cloth:
    color: str
    purpose: str
    clean: bool = True
    tied: bool = False
    marked: bool = False
    location: str = "the pack"
    meters: dict[str, float] = field(default_factory=lambda: {"strength": 0.8})
    memes: dict[str, float] = field(default_factory=lambda: {"memory": 0.0})


@dataclass
class Setting:
    place: str
    landmark: str
    description: str


@dataclass
class StoryParams:
    place: str = "the Whispering Ravine"
    landmark: str = "the stone arch"
    hero_name: str = "Luna"
    hero_species: str = "fox"
    companion_name: str = "Tavi"
    companion_species: str = "raven"
    cloth_color: str = "blue"
    scenario_id: int = 0
    opening_mode: int = 0
    thought_mode: int = 0
    ending_mode: int = 0
    seed: Optional[int] = None


@dataclass(frozen=True)
class Scenario:
    discovery: str
    danger: str
    failed_move: str
    clue: str
    plan: str
    action: str
    resolution: str
    lesson: str
    ending: str


SCENARIOS = (
    Scenario(
        discovery="A narrow trail led beyond the old stone arch, where a silver bell was said to hang above the valley.",
        danger="A sudden cloudburst turned the trail into a sliding ribbon of mud and hid the safe crossing below.",
        failed_move="Luna stepped onto a loose rock and skidded back with a startled yelp",
        clue="Tavi saw red berries tied to branches on the far bank, showing that earlier travelers had marked the sturdy route",
        plan="to tie the cloth between two roots as a bright guide while Tavi watched from above",
        action="knotted the cloth to the first root and followed its edge toward the marked stones",
        resolution="The cloth made a clear line through the rain, and the friends crossed one careful step at a time.",
        lesson="courage grows when fear is given a careful plan",
        ending="the blue cloth fluttered beneath the stone arch while the silver bell rang in the clean evening air",
    ),
    Scenario(
        discovery="Luna and Tavi followed a map scratched on bark toward a hidden lookout above the forest.",
        danger="The map ended at a fork where mist covered both paths, and one route curled toward a deep ravine.",
        failed_move="chose the wider path because it looked easier",
        clue="a torn corner of the map matched a blue stitch in Luna's cloth",
        plan="to stretch the cloth between trees so they could return safely while they tested the quieter path",
        action="marked each turn with a small fold in the cloth and led the way beside Tavi",
        resolution="Their trail markers brought them back from the dead end, and the quieter path led to the lookout.",
        lesson="a brave explorer prepares a way home before going farther",
        ending="the cloth hung from the last tree like a little flag above the whole green valley",
    ),
    Scenario(
        discovery="A warm wind carried the smell of pine smoke from a ranger's cabin beyond the hills.",
        danger="A stone bridge had lost one of its planks, leaving a gap above a rushing stream.",
        failed_move="leaned over the gap and tried to judge it by staring harder",
        clue="the cloth could cover the gap's sharp edge but could not hold a creature's weight",
        plan="to use the cloth as a signal while searching for the ranger's safer rope crossing",
        action="waved the cloth from the bank as Tavi flew toward the cabin for help",
        resolution="The ranger answered the signal and showed them a sturdy crossing farther upstream.",
        lesson="knowing what a tool cannot do is part of using it wisely",
        ending="the cloth dried on the cabin rail beside the rope that had carried them safely across",
    ),
    Scenario(
        discovery="Luna found a tiny door in a cliff face and heard a faint scratching behind it.",
        danger="The door was blocked by fallen branches, while the fading light made the narrow ledge hard to see.",
        failed_move="pulled at the largest branch until dust filled her nose",
        clue="the cloth caught on a thorn and revealed a trail of fresh paw prints",
        plan="to follow the prints around the cliff instead of forcing the blocked door",
        action="wrapped the cloth around a thorny branch and used it as a marker while Tavi searched ahead",
        resolution="They found a second entrance and helped a lost young badger out before darkness fell.",
        lesson="a setback can point toward a kinder and safer path",
        ending="the cloth rested over the badger's shoulders as the three travelers watched stars appear",
    ),
)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, object] = {}
        self.events: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, eid: str, obj: object) -> object:
        self.entities[eid] = obj
        return obj

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def tell(params: StoryParams) -> World:
    if not params.hero_name or not params.companion_name:
        raise StoryError("hero and companion names must not be empty")
    if params.hero_name == params.companion_name:
        raise StoryError("hero and companion must have different names")
    if not params.cloth_color:
        raise StoryError("cloth color must not be empty")

    scenario = SCENARIOS[params.scenario_id % len(SCENARIOS)]
    setting = Setting(
        place=params.place,
        landmark=params.landmark,
        description=f"{params.place} stretched around {params.landmark}, with steep paths and whispering trees",
    )
    world = World(setting)
    hero = world.add("hero", Explorer(params.hero_name, params.hero_species))
    companion = world.add("companion", Companion(params.companion_name, params.companion_species))
    cloth = world.add("cloth", Cloth(params.cloth_color, "a trail marker"))

    hero.inventory.append("cloth")
    hero.memes["curiosity"] = 1.0

    openings = (
        f"At dawn, {hero.name} the {hero.species} reached {setting.place} with {companion.name} the {companion.species} circling overhead.",
        f"{hero.name} had dreamed of exploring {setting.place}, so it set out with {companion.name} before the first light touched {setting.landmark}.",
        f"The adventure began when {hero.name} discovered a fresh trail near {setting.landmark}. {companion.name} swooped down to join the journey.",
        f"Beyond the familiar trees lay {setting.place}. {hero.name} packed a small {cloth.color} cloth, and {companion.name} promised to keep watch.",
    )
    world.say(openings[params.opening_mode % len(openings)])
    world.say(f"The {cloth.color} cloth was light but useful: it could show a route, catch attention, and carry a memory of the path.")
    world.say(scenario.discovery)

    world.para()
    world.say(scenario.danger)
    world.say(f"At first, {hero.name} {scenario.failed_move}.")
    thoughts = (
        f"Inside, {hero.name} thought, 'I want to be brave, but rushing will only make this worse.'",
        f"{hero.name}'s inner monologue whispered, 'The cloth is small. My choice must be careful and clear.'",
        f"'What would {companion.name} notice from above?' {hero.name} wondered silently.",
        f"{hero.name} told itself, 'Fear is a warning, not a command to stop thinking.'",
    )
    world.say(thoughts[params.thought_mode % len(thoughts)])
    world.say(f"'{hero.name}, look beside the trail,' called {companion.name}. 'The land may be giving us a clue.'")

    world.para()
    world.say(scenario.clue + ".")
    world.say(f"{hero.name} understood that {scenario.lesson}.")
    world.say(f"'{companion.name}, I have a plan,' said {hero.name}.")
    world.say(f"'Then tell me, and I will watch for danger,' replied {companion.name}.")
    world.say(f"Together they decided {scenario.plan}.")
    world.say(f"Carefully, {hero.name} {scenario.action}.")
    cloth.tied = True
    cloth.marked = True
    cloth.location = "the trail"
    cloth.memes["memory"] = 1.0
    hero.memes["fear"] = 0.0
    hero.memes["courage"] = 1.0
    companion.memes["trust"] = 1.0
    world.events.extend(["danger_noticed", "inner_thought_shared", "clue_found", "plan_made", "cloth_used"])
    world.say(scenario.resolution)

    world.para()
    endings = (
        f"{hero.name} learned that {scenario.lesson}.",
        f"The thought stayed with {hero.name}: {scenario.lesson}.",
        f"From then on, {hero.name} remembered that {scenario.lesson}.",
        f"{companion.name} smiled, and {hero.name} knew why the adventure mattered: {scenario.lesson}.",
    )
    world.say(endings[params.ending_mode % len(endings)])
    world.say(f"At sunset, {scenario.ending}.")

    world.facts.update(
        hero=hero,
        companion=companion,
        cloth=cloth,
        scenario=scenario,
        danger=scenario.danger,
        clue=scenario.clue,
        plan=scenario.plan,
        action=scenario.action,
        resolution=scenario.resolution,
        lesson=scenario.lesson,
        ending=scenario.ending,
        place=setting.place,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Explorer = f["hero"]
    companion: Companion = f["companion"]
    return [
        f"Write an adventure about {hero.name} and {companion.name} exploring {f['place']} with a cloth.",
        f"Show {hero.name}'s inner monologue changing after this clue: {f['clue']}.",
        f"Describe how the friends use a cloth safely to solve this danger: {f['danger']}",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Explorer = f["hero"]
    companion: Companion = f["companion"]
    return [
        QAItem(
            question=f"What danger did {hero.name} and {companion.name} face?",
            answer=f"They faced this danger: {f['danger']}"
        ),
        QAItem(
            question=f"What clue helped {hero.name} change plans?",
            answer=f"The clue was that {f['clue']}. It showed the friends how to move more safely."
        ),
        QAItem(
            question="How did the cloth help during the adventure?",
            answer=f"The cloth helped because the friends decided {f['plan']}. Then {hero.name} {f['action']}."
        ),
        QAItem(
            question=f"What did {hero.name}'s inner monologue help the explorer do?",
            answer=f"It helped {hero.name} pause instead of rushing, understand the clue, and choose a careful plan with {companion.name}."
        ),
        QAItem(
            question=f"How did the adventure end?",
            answer=f"{f['resolution']} At sunset, {f['ending']}."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is cloth?",
            answer="Cloth is a flexible material made from woven or knitted fibers. It can be used for clothing, cleaning, carrying, or marking a path."
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is a character's private stream of thoughts, heard inside the character's mind rather than spoken aloud."
        ),
        QAItem(
            question="Why should explorers make a plan before crossing a dangerous place?",
            answer="A plan helps explorers notice risks, choose safer actions, and know how to return or ask for help."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    out.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    out.append("")
    out.append("== Story QA ==")
    for item in sample.story_qa:
        out.extend([f"Q: {item.question}", f"A: {item.answer}"])
    out.append("")
    out.append("== World QA ==")
    for item in sample.world_qa:
        out.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(out)


ASP_RULES = r"""
usable_cloth(C) :- cloth(C), clean(C).
marked_route(C) :- usable_cloth(C), marked(C).
safe_plan(H) :- hero(H), clue_found, plan_made.
adventure_complete(H) :- hero(H), safe_plan(H), marked_route(cloth).
trusting(C) :- companion(C), plan_made.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("hero", "hero"),
            asp.fact("companion", "companion"),
            asp.fact("cloth", "cloth"),
            asp.fact("clean", "cloth"),
            asp.fact("marked", "cloth"),
            asp.fact("clue_found"),
            asp.fact("plan_made"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Adventure world about cloth and inner monologue.")
    parser.add_argument("--place", default=None)
    parser.add_argument("--landmark", default=None)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    places = ["the Whispering Ravine", "the Mossy Highlands", "the Lantern Caves", "the Wind-Torn Pass"]
    landmarks = ["the stone arch", "the crooked watchtower", "the fallen bridge", "the old pine"]
    return StoryParams(
        place=args.place or rng.choice(places),
        landmark=args.landmark or rng.choice(landmarks),
        hero_name=rng.choice(["Luna", "Mira", "Cedar", "Pip"]),
        hero_species=rng.choice(["fox", "hare", "otter", "young wolf"]),
        companion_name=rng.choice(["Tavi", "Rook", "Nell", "Ash"]),
        companion_species=rng.choice(["raven", "jay", "swift", "small owl"]),
        cloth_color=rng.choice(["blue", "red", "golden", "green"]),
        scenario_id=rng.randrange(len(SCENARIOS)),
        opening_mode=rng.randrange(4),
        thought_mode=rng.randrange(4),
        ending_mode=rng.randrange(4),
        seed=args.seed,
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


def dump_trace(world: World) -> str:
    hero: Explorer = world.entities["hero"]
    companion: Companion = world.entities["companion"]
    cloth: Cloth = world.entities["cloth"]
    return "\n".join(
        [
            "--- world trace ---",
            f"place: {world.setting.place}",
            f"landmark: {world.setting.landmark}",
            f"hero: {hero.name} {hero.species} meters={hero.meters} memes={hero.memes}",
            f"companion: {companion.name} {companion.species} meters={companion.meters} memes={companion.memes}",
            f"cloth: color={cloth.color} purpose={cloth.purpose} tied={cloth.tied} marked={cloth.marked} location={cloth.location}",
            f"events: {world.events}",
        ]
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


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show adventure_complete/1. #show trusting/1."))
    complete = set(asp.atoms(model, "adventure_complete"))
    trusting = set(asp.atoms(model, "trusting"))
    if ("hero",) not in complete or ("companion",) not in trusting:
        print("MISMATCH: ASP twin did not derive the completed adventure.")
        return 1
    sample = generate(StoryParams())
    if "cloth" not in sample.story.lower() or "thought" not in sample.story.lower():
        print("MISMATCH: generated story omitted required narrative elements.")
        return 1
    print("OK: ASP and Python story checks passed.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show adventure_complete/1. #show trusting/1."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show adventure_complete/1. #show trusting/1."))
        print("adventure_complete:", asp.atoms(model, "adventure_complete"))
        print("trusting:", asp.atoms(model, "trusting"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        params_list = [
            StoryParams(place="the Whispering Ravine", landmark="the stone arch", scenario_id=i, seed=i)
            for i in range(len(SCENARIOS))
        ]
        samples = [generate(p) for p in params_list]
    else:
        samples = [
            generate(resolve_params(args, random.Random(base_seed + i)))
            for i in range(max(1, args.n))
        ]

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

#!/usr/bin/env python3
"""A fairy-tale zoo comedy about a river-pageant crash solved by careful looking.

Internal source tale:
At a storybook zoo, two children launch a silly little parade boat on a wobbly
river to bring a treat to a favorite animal. The boat crashes in a comic way,
but the children notice a repeating physical clue instead of blaming magic.
With a patient zoo helper and the right tool, they repair the real fault,
launch the boat again, and end with laughter, a safe river, and a bright happy
ending image.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from storyworlds.results import QAItem, StoryError, StorySample


SOURCE_TALE = (
    "At a storybook zoo, two children launch a silly parade boat on a wobbly river "
    "to bring a treat to a favorite animal. The boat crashes in a comic way, but a "
    "repeating clue leads them to the real physical fault. With help, patience, and "
    "the right tool, they solve the problem and end the day laughing beside the safe river."
)


@dataclass(frozen=True)
class Exhibit:
    key: str
    name: str
    opening: str
    animal_name: str
    animal_kind: str
    comic_detail: str
    reward: str
    ending_image: str
    sites: tuple[str, ...]


@dataclass(frozen=True)
class Cause:
    key: str
    place: str
    kind: str
    crash_text: str
    clue_text: str
    discovery: str
    motion: str
    result: str


@dataclass(frozen=True)
class Solution:
    key: str
    solves: str
    tool: str
    action: str
    proof: str
    lesson: str


@dataclass(frozen=True)
class DuoChoice:
    key: str
    first: str
    first_type: str
    second: str
    second_type: str


@dataclass(frozen=True)
class KeeperChoice:
    key: str
    name: str
    type: str
    role: str
    trait: str
    advice: str


@dataclass
class StoryParams:
    exhibit: str
    cause: str
    solution: str
    duo: str
    keeper: str
    seed: int | None = None


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict[str, str] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Event:
    id: str
    text: str
    actor: str
    target: str | None = None


@dataclass
class ZooRiverWorld:
    params: StoryParams
    exhibit: Exhibit
    cause: Cause
    solution: Solution
    entities: dict[str, Entity] = field(default_factory=dict)
    history: list[Event] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, str | bool | int | float] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        if entity.role:
            self.entities[entity.role] = entity
        return entity

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def record(self, event_id: str, text: str, actor: str, target: str | None = None) -> None:
        self.history.append(Event(event_id, text, actor, target))
        self.say(text)

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)

    def trace(self) -> str:
        lines = ["TRACE"]
        for event in self.history:
            target = f" -> {event.target}" if event.target else ""
            lines.append(f"- {event.id}: {event.actor}{target}: {event.text}")
        lines.append("ENTITIES")
        seen: set[str] = set()
        for entity in self.entities.values():
            if entity.id in seen:
                continue
            seen.add(entity.id)
            lines.append(f"  {entity.id} | {entity.kind} | {entity.label}")
            meters = {k: v for k, v in entity.meters.items() if v}
            memes = {k: v for k, v in entity.memes.items() if v}
            if meters:
                lines.append(f"    meters={meters}")
            if memes:
                lines.append(f"    memes={memes}")
        lines.append("FACTS")
        for key in sorted(self.facts):
            lines.append(f"  {key}={self.facts[key]}")
        return "\n".join(lines)


EXHIBITS: dict[str, Exhibit] = {
    "otter_orchard": Exhibit(
        key="otter_orchard",
        name="Otter Orchard",
        opening="At Moonpetal Zoo, a wobbly river curled through Otter Orchard under a little bridge painted with pears and silver fish.",
        animal_name="Queen Puddle",
        animal_kind="otter",
        comic_detail="Queen Puddle liked to sit straight as a queen until a snack appeared, and then her whiskers wiggled faster than any trumpet.",
        reward="the apricot bun basket",
        ending_image="Queen Puddle paddled beside the bank with a reed crown on her head while the little boat glided as smooth as a spoon through soup",
        sites=("rudder", "wheel"),
    ),
    "flamingo_ford": Exhibit(
        key="flamingo_ford",
        name="Flamingo Ford",
        opening="Past the pink gates of Moonpetal Zoo, a wobbly river looped around Flamingo Ford where lantern flags trembled over the water like candy-colored feathers.",
        animal_name="Sir Blush",
        animal_kind="flamingo",
        comic_detail="Sir Blush could balance on one leg for an hour, but he still honked like a squeaky horn whenever a pastry was late.",
        reward="the berry biscuit ring",
        ending_image="Sir Blush bowed over the water, the biscuit ring rode safely to the stone bank, and rosy ripples carried laughter all the way to the reeds",
        sites=("towline", "rudder"),
    ),
    "lemur_landing": Exhibit(
        key="lemur_landing",
        name="Lemur Landing",
        opening="In the sunniest corner of Moonpetal Zoo, a wobbly river skipped past Lemur Landing where a painted willow wheel clicked beside the shallows.",
        animal_name="Captain Tumble",
        animal_kind="lemur",
        comic_detail="Captain Tumble saluted every boat with both hands, even when that made him wobble right off his favorite log.",
        reward="the plum jam cake",
        ending_image="Captain Tumble hugged the plum jam cake on the bank while the willow wheel turned bright and the river carried only gentle sparkles",
        sites=("wheel", "towline"),
    ),
}

CAUSES: dict[str, Cause] = {
    "reed_tangle": Cause(
        key="reed_tangle",
        place="rudder",
        kind="snarl",
        crash_text="The tiny parade boat spun once, bumped the painted post with a merry crash, and tossed its ribboned napkin onto a nearby stone turtle.",
        clue_text="Each time the boat backed away, the same green ribbon of reeds hugged one side of the rudder and pulled the little stern crooked.",
        discovery="When the children knelt by the stern, they saw river reeds twisted around the rudder pin like damp green yarn.",
        motion="The reeds were dragging one side of the rudder, so the little boat could only pretend to steer while the river nudged it sideways.",
        result="Freed from the reeds, the rudder answered at once and the boat stopped trying to dance into the post.",
    ),
    "berry_jam": Cause(
        key="berry_jam",
        place="wheel",
        kind="jam",
        crash_text="The willow wheel gave one brave turn, then the boat lurched with a sugary crash against the dock rail and dabbed purple jam on the sign that said PLEASE NO SPLASHING.",
        clue_text="A sticky purple blink flashed from the wheel every time it slowed, as if one bright tooth kept getting caught and waving for help.",
        discovery="Under the wheel cap, a blob of berry jam and two seed pebbles had glued the smallest cogs together.",
        motion="The jammed cogs could not turn the wheel evenly, so the boat kept jerking forward and bumping off its path.",
        result="Once the cogs turned cleanly again, the willow wheel hummed instead of coughing, and the boat tracked the middle of the stream.",
    ),
    "slack_towline": Cause(
        key="slack_towline",
        place="towline",
        kind="slip",
        crash_text="The towline flopped, the bow wandered, and the boat made a soft crash into the lily barrel so quickly that even the goldfish looked surprised.",
        clue_text="A loop in the towline kept jumping loose at the same knot, leaving the bow free to swing every time the current pulled.",
        discovery="The children found one polished knot that had loosened into a sleepy loop, shiny from rubbing against the guide ring.",
        motion="The towline was slipping at the same weak knot, so the bow had no firm guide and drifted into whatever the current offered next.",
        result="With the line snug again, the bow followed the guide ring as neatly as a duckling following its mother.",
    ),
}

SOLUTIONS: dict[str, Solution] = {
    "willow_rake": Solution(
        key="willow_rake",
        solves="snarl",
        tool="the willow-tooth river rake",
        action="{first} steadied the stern while {second} slid {tool} under the wet reeds and lifted the whole slippery tangle away in one patient scoop.",
        proof="The next push sent the boat forward in a straight little line, and no reed came back to grab the rudder.",
        lesson="They solved the trouble by following the repeating pull and removing exactly what held it there.",
    ),
    "cog_brush": Solution(
        key="cog_brush",
        solves="jam",
        tool="the brass cog brush",
        action="{keeper} handed them {tool}. {second} held the wheel cap open while {first} brushed the sticky cogs until the purple smear and seed pebbles gave up their stubborn hold.",
        proof="When they spun the wheel again, it turned with a clean wooden whirr instead of a gummy gulp.",
        lesson="They solved the trouble by cleaning the one small place where the clue kept shining.",
    ),
    "double_bow": Solution(
        key="double_bow",
        solves="slip",
        tool="the striped rope ring",
        action="{first} threaded the towline through {tool} while {second} pulled both ends even, and together they tied a cheerful double bow that sat tight against the guide ring.",
        proof="At the next launch, the knot held fast and the bow stayed pointed where the children had aimed it.",
        lesson="They solved the trouble by giving the loose line the exact kind of hold it had been missing.",
    ),
}

DUOS: dict[str, DuoChoice] = {
    "mira_jo": DuoChoice("mira_jo", "Mira", "girl", "Jo", "boy"),
    "lina_omar": DuoChoice("lina_omar", "Lina", "girl", "Omar", "boy"),
    "noor_eli": DuoChoice("noor_eli", "Noor", "girl", "Eli", "boy"),
    "tavi_ren": DuoChoice("tavi_ren", "Tavi", "girl", "Ren", "boy"),
}

KEEPERS: dict[str, KeeperChoice] = {
    "nuri": KeeperChoice(
        key="nuri",
        name="Keeper Nuri",
        type="woman",
        role="lantern keeper",
        trait="patient",
        advice='"A true answer leaves the same footprint twice."',
    ),
    "elm": KeeperChoice(
        key="elm",
        name="Keeper Elm",
        type="man",
        role="river-cart keeper",
        trait="calm",
        advice='"When a silly thing happens twice, it is usually trying to teach you something."',
    ),
    "sora": KeeperChoice(
        key="sora",
        name="Keeper Sora",
        type="woman",
        role="snack barge keeper",
        trait="observant",
        advice='"Do not argue with a clue that keeps pointing."',
    ),
}

PLACE_LABELS = {
    "rudder": "the little rudder at the stern",
    "wheel": "the painted willow wheel on the side of the boat",
    "towline": "the guiding towline at the bow ring",
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for exhibit_key, exhibit in sorted(EXHIBITS.items()):
        for cause_key, cause in sorted(CAUSES.items()):
            for solution_key, solution in sorted(SOLUTIONS.items()):
                if cause.place not in exhibit.sites:
                    continue
                if solution.solves != cause.kind:
                    continue
                combos.append((exhibit_key, cause_key, solution_key))
    return combos


def _unknown_reason(kind: str, value: str, options: Iterable[str]) -> str:
    opts = ", ".join(sorted(options))
    return f"No story: unknown {kind} {value!r}. Try one of: {opts}."


def explain_rejection(exhibit_key: str, cause_key: str, solution_key: str) -> str:
    if exhibit_key not in EXHIBITS:
        return _unknown_reason("exhibit", exhibit_key, EXHIBITS)
    if cause_key not in CAUSES:
        return _unknown_reason("cause", cause_key, CAUSES)
    if solution_key not in SOLUTIONS:
        return _unknown_reason("solution", solution_key, SOLUTIONS)
    exhibit = EXHIBITS[exhibit_key]
    cause = CAUSES[cause_key]
    solution = SOLUTIONS[solution_key]
    if cause.place not in exhibit.sites:
        sites = ", ".join(exhibit.sites)
        return (
            f"No story: {exhibit.name} does not expose a {cause.place} problem. "
            f"That zoo river scene only supports these repair sites: {sites}."
        )
    if solution.solves != cause.kind:
        return (
            f"No story: solution {solution_key!r} solves {solution.solves}, but cause {cause_key!r} is a {cause.kind} fault. "
            "Use the tool that fits the physical problem."
        )
    return "No story: invalid zoo river pageant."


def valid_params(params: StoryParams) -> tuple[bool, str]:
    if params.duo not in DUOS:
        return False, _unknown_reason("duo", params.duo, DUOS)
    if params.keeper not in KEEPERS:
        return False, _unknown_reason("keeper", params.keeper, KEEPERS)
    reason = explain_rejection(params.exhibit, params.cause, params.solution)
    if reason == "No story: invalid zoo river pageant.":
        return True, ""
    return False, reason


def _pick_duo(seed: int) -> str:
    return random.Random(seed * 13 + 5).choice(sorted(DUOS))


def _pick_keeper(seed: int) -> str:
    return random.Random(seed * 29 + 11).choice(sorted(KEEPERS))


def params_from_combo(combo: tuple[str, str, str], seed: int) -> StoryParams:
    return StoryParams(
        exhibit=combo[0],
        cause=combo[1],
        solution=combo[2],
        duo=_pick_duo(seed),
        keeper=_pick_keeper(seed),
        seed=seed,
    )


def matching_combos(args: argparse.Namespace) -> list[tuple[str, str, str]]:
    combos = valid_combos()
    return [
        combo
        for combo in combos
        if (args.exhibit is None or combo[0] == args.exhibit)
        and (args.cause is None or combo[1] == args.cause)
        and (args.solution is None or combo[2] == args.solution)
    ]


def build_world(params: StoryParams) -> ZooRiverWorld:
    exhibit = EXHIBITS[params.exhibit]
    cause = CAUSES[params.cause]
    solution = SOLUTIONS[params.solution]
    duo = DUOS[params.duo]
    keeper_choice = KEEPERS[params.keeper]

    world = ZooRiverWorld(params=params, exhibit=exhibit, cause=cause, solution=solution)

    first = world.add(Entity("first", "character", duo.first_type, duo.first, role="first", traits=["curious"]))
    second = world.add(Entity("second", "character", duo.second_type, duo.second, role="second", traits=["steady"]))
    keeper = world.add(
        Entity("keeper", "character", keeper_choice.type, keeper_choice.name, role="keeper", traits=[keeper_choice.trait])
    )
    team = world.add(
        Entity(
            "team",
            "group",
            "children",
            f"{duo.first} and {duo.second}",
            role="team",
            traits=["playful", "careful"],
        )
    )
    animal = world.add(
        Entity(
            "animal",
            "animal",
            exhibit.animal_kind,
            exhibit.animal_name,
            role="animal",
            traits=["hungry", "funny"],
        )
    )
    boat = world.add(
        Entity(
            "boat",
            "object",
            "parade_boat",
            "the little parade boat",
            role="boat",
            traits=["ribboned", "tiny"],
        )
    )
    river = world.add(
        Entity(
            "river",
            "place",
            "river",
            "the wobbly river",
            role="river",
            traits=["sparkling", "tricky"],
        )
    )
    site = world.add(
        Entity(
            cause.place,
            "mechanism",
            cause.place,
            PLACE_LABELS[cause.place],
            role="site",
            traits=["small", "important"],
        )
    )

    boat.meters["straightness"] = 0.2
    boat.meters["damage"] = 0.4
    river.meters["flow"] = 1.0
    river.meters["wobble"] = 1.0
    site.meters["blocked"] = 1.0
    team.memes["wonder"] = 1.0
    team.memes["worry"] = 0.2
    team.memes["glee"] = 0.8
    team.memes["resolve"] = 0.3
    animal.memes["trust"] = 0.8
    animal.memes["hunger"] = 1.0
    keeper.memes["patience"] = 1.0

    world.facts["source_tale"] = SOURCE_TALE
    world.facts["river_phrase"] = "wobbly river"
    world.facts["seed_word"] = "crash"
    world.facts["site"] = cause.place
    world.facts["site_label"] = PLACE_LABELS[cause.place]
    world.facts["problem_kind"] = cause.kind
    world.facts["tool"] = solution.tool
    world.facts["keeper_role"] = keeper_choice.role
    world.facts["reward"] = exhibit.reward
    world.facts["solved"] = False
    world.facts["ending"] = "pending"
    return world


def build_false_guess(world: ZooRiverWorld) -> str:
    animal = world.get("animal").label
    cause = world.cause
    if cause.place == "rudder":
        return (
            f"For one ridiculous breath, the children wondered whether {animal} had laughed the boat sideways by royal command. "
            "But the same pull happened again in the same place, which felt much more like a clue than a spell."
        )
    if cause.place == "wheel":
        return (
            f"They almost blamed a greedy cake sprite for the crash, especially after the purple smear winked at them from the wheel. "
            "Then they saw the same sticky blink return with every turn."
        )
    return (
        f"For a blink, they suspected the river itself was playing a prank. "
        "Then the loose loop jumped at the same knot again, and the joke turned into evidence."
    )


def tell(world: ZooRiverWorld) -> ZooRiverWorld:
    first = world.get("first")
    second = world.get("second")
    keeper = world.get("keeper")
    team = world.get("team")
    animal = world.get("animal")
    boat = world.get("boat")
    site = world.get("site")
    exhibit = world.exhibit
    cause = world.cause
    solution = world.solution
    keeper_role = str(world.facts["keeper_role"])
    site_label = str(world.facts["site_label"])

    world.record(
        "opening",
        f"{exhibit.opening} There lived {animal.label}, the funniest {animal.type} in that corner of the zoo. {exhibit.comic_detail}",
        actor="narrator",
        target="river",
    )
    world.record(
        "goal",
        f"That morning, {first.label} and {second.label} set {exhibit.reward} into the little parade boat because they wanted to float it to {animal.label} in the grandest fairy-tale way they could imagine.",
        actor="team",
        target="boat",
    )
    world.para()

    world.record("crash", cause.crash_text, actor="boat", target=cause.place)
    team.memes["worry"] += 0.7
    team.memes["wonder"] += 0.3
    animal.memes["trust"] -= 0.1
    world.record("false_guess", build_false_guess(world), actor="team", target="river")
    world.record("clue", cause.clue_text, actor="team", target=cause.place)
    world.record(
        "keeper_hint",
        f'{keeper.label}, the {keeper_role}, knelt by the splash stones and said, {KEEPERS[world.params.keeper].advice}',
        actor="keeper",
        target=cause.place,
    )
    world.para()

    world.record(
        "inspect",
        f"So {first.label} and {second.label} followed the clue to {site_label} instead of fussing at the whole boat.",
        actor="team",
        target=cause.place,
    )
    world.record("discovery", cause.discovery, actor="team", target=cause.place)
    world.record("diagnosis", cause.motion, actor="team", target=cause.place)
    team.memes["resolve"] += 0.9
    world.para()

    world.record(
        "solve",
        solution.action.format(
            first=first.label,
            second=second.label,
            keeper=keeper.label,
            tool=solution.tool,
        ),
        actor="team",
        target=cause.place,
    )
    site.meters["blocked"] = 0.0
    boat.meters["straightness"] = 1.0
    boat.meters["damage"] = 0.0
    animal.memes["trust"] += 0.5
    team.memes["glee"] += 0.6
    team.memes["worry"] = 0.0
    world.record("proof", f"{solution.proof} {cause.result}", actor="boat", target="boat")
    world.facts["solved"] = True
    world.para()

    world.record(
        "ending",
        f"When they launched the boat again, it glided straight to {animal.label}. {animal.label} accepted {exhibit.reward} with such happy dignity that even {keeper.label} laughed. By evening, {exhibit.ending_image}. {solution.lesson}",
        actor="team",
        target="animal",
    )
    world.facts["ending"] = "happy"
    return world


def generation_prompts(world: ZooRiverWorld) -> list[str]:
    first = world.get("first").label
    second = world.get("second").label
    return [
        'Write a fairy-tale story set in a zoo that includes the exact phrase "wobbly river."',
        f"Make the story funny and child-friendly by giving {first} and {second} a comic boat crash to solve with observation instead of magic.",
        "End with a clear happy image that proves the river problem was physically fixed.",
    ]


def story_grounded_qa(world: ZooRiverWorld) -> list[QAItem]:
    first = world.get("first").label
    second = world.get("second").label
    keeper = world.get("keeper").label
    animal = world.get("animal").label
    exhibit = world.exhibit
    cause = world.cause
    solution = world.solution
    site_label = str(world.facts["site_label"])
    return [
        QAItem(
            "Why did the little parade boat crash?",
            f"The parade boat crashed because {cause.motion[0].lower() + cause.motion[1:]} That physical fault pushed the boat off its path before {first} and {second} could guide it to {animal}.",
        ),
        QAItem(
            "Which clue helped the children solve the problem?",
            f"The clue was this: {cause.clue_text.lower()} Because the same odd sign returned in the same place, the children knew they should inspect {site_label} instead of guessing wildly.",
        ),
        QAItem(
            "How did the children fix the river boat?",
            f"They used {solution.tool} where the clue pointed. {solution.proof} That proved the repair matched the actual fault instead of covering up the crash with wishful thinking.",
        ),
        QAItem(
            "Why is the ending funny as well as happy?",
            f"The ending is funny because {animal} receives the treat with grand royal seriousness while the grown-up keeper laughs anyway. It is happy because the boat now travels safely and the whole zoo scene ends in shared delight instead of worry.",
        ),
        QAItem(
            "What role did the zoo keeper play in the solution?",
            f"{keeper} helped by slowing the children down and teaching them to trust the repeating clue. The keeper did not solve the problem alone, but gave the kind of guidance that turned excitement into careful problem solving.",
        ),
        QAItem(
            "How does the final image prove that the problem is really over?",
            f"The story proves the problem is over with this final image: {exhibit.ending_image}. That calm ending could only happen after the boat stopped crashing and reached {animal} the right way.",
        ),
    ]


def world_knowledge_qa(world: ZooRiverWorld) -> list[QAItem]:
    return [
        QAItem(
            "Why must each solution match the kind of fault in this world?",
            "Each problem in this world is physical, such as a snarl, a jam, or a slipping line. The story stays reasonable only when the tool and action fit the material fault instead of pretending any cheerful motion can fix every boat.",
        ),
        QAItem(
            "Why is the repeating clue important in this zoo river world?",
            "The repeating clue keeps the mystery grounded in the river mechanism. It turns a silly crash into a solvable problem because the children can test where the same sign returns.",
        ),
        QAItem(
            "Which object carries the biggest change from problem to happy ending?",
            "The little parade boat carries the biggest visible change. At first it crashes and wanders, but after the repair it moves straight, reaches the animal, and becomes proof that the children solved the right problem.",
        ),
        QAItem(
            "Why does the zoo setting matter instead of being just decoration?",
            "The zoo setting matters because the goal is to deliver a treat safely to a specific animal in a playful public exhibit. The river, the keeper, the animal, and the child-sized repair all belong to that place and give the story its fairy-tale comedy.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    ok, reason = valid_params(params)
    if not ok:
        raise StoryError(reason)
    world = tell(build_world(params))
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_grounded_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


ASP_RULES = r"""
valid(E,C,S) :-
    exhibit(E),
    cause(C),
    solution(S),
    cause_place(C, P),
    exhibit_site(E, P),
    cause_kind(C, K),
    solution_solves(S, K).

ok :- chosen(E, C, S), valid(E, C, S).

#show valid/3.
#show ok/0.
"""


def asp_facts(params: StoryParams | None = None) -> str:
    from storyworlds.asp import fact

    lines: list[str] = []
    for exhibit_key, exhibit in sorted(EXHIBITS.items()):
        lines.append(fact("exhibit", exhibit_key))
        for site in exhibit.sites:
            lines.append(fact("exhibit_site", exhibit_key, site))
    for cause_key, cause in sorted(CAUSES.items()):
        lines.append(fact("cause", cause_key))
        lines.append(fact("cause_place", cause_key, cause.place))
        lines.append(fact("cause_kind", cause_key, cause.kind))
    for solution_key, solution in sorted(SOLUTIONS.items()):
        lines.append(fact("solution", solution_key))
        lines.append(fact("solution_solves", solution_key, solution.solves))
    if params is not None:
        lines.append(fact("chosen", params.exhibit, params.cause, params.solution))
    return "\n".join(lines) + "\n"


def asp_program(params: StoryParams | None = None) -> str:
    return asp_facts(params) + ASP_RULES


def asp_valid_combos() -> list[tuple[str, str, str]]:
    from storyworlds.asp import atoms, one_model

    return sorted(atoms(one_model(asp_program()), "valid"))


def verify_sample(sample: StorySample) -> None:
    world = sample.world
    if world is None:
        raise AssertionError("sample world is missing")
    story_lower = sample.story.lower()
    for needle in ("wobbly river", "crash", "zoo"):
        if needle not in story_lower:
            raise AssertionError(f"story is missing {needle!r}")
    if sample.story.count("\n\n") < 3:
        raise AssertionError("story should have at least four paragraphs")
    if "{" in sample.story or "}" in sample.story:
        raise AssertionError("story leaked unresolved formatting")
    if "meters=" in sample.story or "memes=" in sample.story:
        raise AssertionError("story leaked debug language")
    if world.get("boat").meters.get("straightness", 0) < 1:
        raise AssertionError("boat never recovered a straight path")
    if world.get("boat").meters.get("damage", 1) != 0:
        raise AssertionError("boat still shows crash damage")
    if world.get("site").meters.get("blocked", 1) != 0:
        raise AssertionError("problem site stayed unresolved")
    if world.get("team").memes.get("resolve", 0) < 1:
        raise AssertionError("children never reached a problem-solving turn")
    if world.get("team").memes.get("worry", 1) != 0:
        raise AssertionError("worry never settled")
    if world.facts.get("ending") != "happy":
        raise AssertionError("story did not reach a happy ending")
    event_ids = {event.id for event in world.history}
    for required in ("crash", "clue", "discovery", "solve", "ending"):
        if required not in event_ids:
            raise AssertionError(f"missing event {required!r}")
    if len(sample.prompts) != 3:
        raise AssertionError("expected exactly three prompts")
    if len(sample.story_qa) < 5 or len(sample.world_qa) < 3:
        raise AssertionError("QA sets are too thin")
    for item in list(sample.story_qa) + list(sample.world_qa):
        if len(item.answer.split()) < 12:
            raise AssertionError(f"answer is too short: {item.question}")


def asp_verify() -> int:
    py = sorted(valid_combos())
    lp = asp_valid_combos()
    if py != lp:
        only_py = sorted(set(py) - set(lp))
        only_lp = sorted(set(lp) - set(py))
        print("MISMATCH between Python and ASP gates:", file=sys.stderr)
        if only_py:
            print(f"  only in Python: {only_py}", file=sys.stderr)
        if only_lp:
            print(f"  only in ASP: {only_lp}", file=sys.stderr)
        return 1
    print(f"OK: ASP parity matches Python gate ({len(py)} valid zoo river pageants).")
    for index, combo in enumerate(py):
        verify_sample(generate(params_from_combo(combo, 1000 + index)))
    print(f"OK: generated stories and QA passed for all {len(py)} valid combinations.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a fairy-tale zoo story about a wobbly river, a comic crash, and problem solving."
    )
    parser.add_argument("--exhibit", choices=sorted(EXHIBITS))
    parser.add_argument("--cause", choices=sorted(CAUSES))
    parser.add_argument("--solution", choices=sorted(SOLUTIONS))
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random | None = None, index: int = 0) -> StoryParams:
    seed = (args.seed if args.seed is not None else 1) + index
    combos = matching_combos(args)
    if not combos:
        exhibit = args.exhibit or next(iter(EXHIBITS))
        cause = args.cause or next(iter(CAUSES))
        solution = args.solution or next(iter(SOLUTIONS))
        raise StoryError(explain_rejection(exhibit, cause, solution))

    explicit = all(getattr(args, field) is not None for field in ("exhibit", "cause", "solution"))
    if explicit:
        params = params_from_combo((args.exhibit, args.cause, args.solution), seed)
        ok, reason = valid_params(params)
        if not ok:
            raise StoryError(reason)
        return params

    chooser = rng or random.Random(seed)
    return params_from_combo(chooser.choice(combos), seed)


def samples_from_args(args: argparse.Namespace) -> list[StorySample]:
    if args.all:
        combos = matching_combos(args)
        if not combos:
            exhibit = args.exhibit or next(iter(EXHIBITS))
            cause = args.cause or next(iter(CAUSES))
            solution = args.solution or next(iter(SOLUTIONS))
            raise StoryError(explain_rejection(exhibit, cause, solution))
        return [generate(params_from_combo(combo, args.seed + index)) for index, combo in enumerate(combos)]

    samples: list[StorySample] = []
    for index in range(max(1, args.n)):
        seed = args.seed + index
        samples.append(generate(resolve_params(args, random.Random(seed), index)))
    return samples


def format_qa(sample: StorySample) -> str:
    lines = ["PROMPTS"]
    for prompt in sample.prompts:
        lines.append(f"- {prompt}")
    lines.append("")
    lines.append("STORY QA")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("WORLD KNOWLEDGE QA")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print()
        print(sample.world.trace())
    if qa:
        print()
        print(format_qa(sample))


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.show_asp:
        print(asp_program())
        return 0
    if args.verify:
        return asp_verify()
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid zoo river pageants:\n")
        for combo in combos:
            print("  " + " ".join(f"{part:16}" for part in combo))
        return 0

    try:
        samples = samples_from_args(args)
    except StoryError as exc:
        parser.error(str(exc))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return 0

    for index, sample in enumerate(samples, 1):
        header = ""
        if len(samples) > 1:
            header = f"=== wobbly_river_crash_zoo_humor_happy_ending #{index} seed={sample.params.seed} ==="
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index != len(samples):
            print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

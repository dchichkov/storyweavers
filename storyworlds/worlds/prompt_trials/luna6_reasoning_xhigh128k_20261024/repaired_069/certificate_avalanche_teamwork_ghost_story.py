#!/usr/bin/env python3
"""Gentle winter ghost stories about an avalanche, a lost certificate, and teamwork."""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


_STORYWORLDS_DIR = next(
    (parent for parent in Path(__file__).resolve().parents if parent.name == "storyworlds"),
    None,
)
if _STORYWORLDS_DIR is None:
    raise RuntimeError("Could not locate the storyworlds directory.")
sys.path.insert(0, str(_STORYWORLDS_DIR))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {
            "subject": "they",
            "object": "them",
            "possessive": "their",
        }[case]


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    lead: str = "Mara"
    friend: str = "Ivo"
    keeper: str = "Edda"
    scene: int = 0
    opening: int = 0
    apparition: int = 0
    search: int = 0


LEADS = ["Mara", "Tess", "Niko", "Sana", "Lio", "Anya"]
FRIENDS = ["Ivo", "Lila", "Jun", "Bea", "Kit", "Rafi"]
KEEPERS = ["Edda", "Alder", "Wren", "Sol", "Marlow"]

SCENES = [
    {
        "id": "fir_switchback",
        "ridge": "Fir Crown",
        "avalanche_line": (
            "A white avalanche broke from Fir Crown and buried the red stakes "
            "on the upper switchback."
        ),
        "blocked": "the upper switchback, where the red trail stakes had disappeared",
        "crew": "two trail wardens",
        "shelter": "the stone patrol hut",
        "route": "the pine-shadowed lower trail",
        "safe_shelter": True,
        "signal_window_visible": True,
        "lower_route_known": True,
        "wait_for_settle": True,
    },
    {
        "id": "moon_bowl",
        "ridge": "Moon Bowl",
        "avalanche_line": (
            "An avalanche poured from Moon Bowl and buried the high footbridge "
            "under a thick white drift."
        ),
        "blocked": "the high footbridge, now hidden beneath the drift",
        "crew": "the snowshoe patrol",
        "shelter": "the west timber shelter",
        "route": "the creekside valley path",
        "safe_shelter": True,
        "signal_window_visible": True,
        "lower_route_known": True,
        "wait_for_settle": True,
    },
    {
        "id": "glass_ridge",
        "ridge": "Glass Ridge",
        "avalanche_line": (
            "A fast avalanche slid from Glass Ridge, swallowing the lantern "
            "posts on the upper track."
        ),
        "blocked": "the upper track, with its lantern posts buried",
        "crew": "a pair of path keepers",
        "shelter": "the old ridge shelter",
        "route": "the sheltered valley road",
        "safe_shelter": True,
        "signal_window_visible": True,
        "lower_route_known": True,
        "wait_for_settle": True,
    },
    {
        "id": "crown_pass",
        "ridge": "Crown Pass",
        "avalanche_line": (
            "An avalanche thundered through Crown Pass and sealed the old "
            "ridge road beneath snow."
        ),
        "blocked": "the old ridge road, buried from bend to bend",
        "crew": "the ridge survey team",
        "shelter": "the small snow-watch cabin",
        "route": "the sheltered valley road",
        "safe_shelter": True,
        "signal_window_visible": True,
        "lower_route_known": True,
        "wait_for_settle": True,
    },
]

OPENINGS = [
    (
        "Snowbell Station stood above the sleeping village. {lead} and {friend} "
        "were checking the lanterns before the pass closed for the night."
    ),
    (
        "Wind brushed Snowbell Station's shutters as {lead} and {friend} "
        "finished their evening watch."
    ),
    (
        "The mountain turned blue with dusk while {lead} and {friend} tended "
        "the lamps at Snowbell Station."
    ),
    (
        "At the old Snowbell Station, {lead} and {friend} kept watch over the "
        "quiet winter pass."
    ),
    (
        "The bell at Snowbell Station gave one soft chime, though no hand had "
        "touched it. {lead} and {friend} looked up from their lanterns."
    ),
]

APPARITIONS = [
    (
        "A blue glow gathered in the window glass, and the ghost of Keeper "
        "{keeper} stepped out of its reflection."
    ),
    (
        "Three frost-bright taps sounded from the empty bell loft. A ghost, "
        "Keeper {keeper}, drifted down the stairs without leaving footprints."
    ),
    (
        "In the dark window, a lantern-lit figure appeared where the mountain "
        "should have been: Keeper {keeper}, the station's gentle ghost."
    ),
]

SEARCHES = [
    "the shallow drawer beneath the route map",
    "a tin beneath the bell desk's loose board",
    "the narrow bottom drawer of the old map cabinet",
]


PARAMETER_REGISTRIES = {
    "leads": LEADS,
    "friends": FRIENDS,
    "keepers": KEEPERS,
    "scenes": [scene["id"] for scene in SCENES],
    "openings": OPENINGS,
    "apparitions": APPARITIONS,
    "search_places": SEARCHES,
}


@dataclass
class Station:
    name: str = "Snowbell Station"
    safe: bool = True
    faces_shelter: bool = True


def _valid_index(value: object, size: int, field_name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value < size:
        raise StoryError(f"{field_name} must be an integer from 0 to {size - 1}.")


def _validate_params(params: StoryParams) -> None:
    if params.lead not in LEADS:
        raise StoryError(f"Unknown lead name {params.lead!r}; choose a registered lead.")
    if params.friend not in FRIENDS:
        raise StoryError(f"Unknown friend name {params.friend!r}; choose a registered friend.")
    if params.keeper not in KEEPERS:
        raise StoryError(f"Unknown keeper name {params.keeper!r}; choose a registered ghost keeper.")
    if len({params.lead, params.friend, params.keeper}) != 3:
        raise StoryError("The lead, friend, and ghost keeper must have different names.")
    _valid_index(params.scene, len(SCENES), "scene")
    _valid_index(params.opening, len(OPENINGS), "opening")
    _valid_index(params.apparition, len(APPARITIONS), "apparition")
    _valid_index(params.search, len(SEARCHES), "search")


def python_reasonableness_gate(scene: dict) -> bool:
    """Accept only scenes where the crew is sheltered and a safe signal is possible."""
    return all(
        scene.get(key) is True
        for key in (
            "safe_shelter",
            "signal_window_visible",
            "lower_route_known",
            "wait_for_settle",
        )
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        seed=args.seed,
        lead=args.lead or rng.choice(LEADS),
        friend=args.friend or rng.choice(FRIENDS),
        keeper=args.keeper or rng.choice(KEEPERS),
        scene=args.scene if args.scene is not None else rng.randrange(len(SCENES)),
        opening=rng.randrange(len(OPENINGS)),
        apparition=rng.randrange(len(APPARITIONS)),
        search=rng.randrange(len(SEARCHES)),
    )


def generate(params: StoryParams) -> StorySample:
    _validate_params(params)
    scene = SCENES[params.scene]
    if not python_reasonableness_gate(scene):
        raise StoryError(
            "This avalanche scene is not reasonable: the crew needs a safe shelter, "
            "a visible signal, a known lower route, and time to wait for the slide to settle."
        )

    world = World()
    station = Station()
    world.facts["station"] = station

    lead = world.add(
        Entity(
            id=params.lead,
            kind="character",
            type="child",
            label=params.lead,
            meters={"inside_station": 1.0, "distance_to_window": 0.0},
            memes={"worry": 0.1, "confidence": 0.35, "teamwork": 0.25},
        )
    )
    friend = world.add(
        Entity(
            id=params.friend,
            kind="character",
            type="child",
            label=params.friend,
            meters={"inside_station": 1.0, "distance_to_window": 0.0},
            memes={"worry": 0.1, "courage": 0.4, "teamwork": 0.3},
        )
    )
    keeper = world.add(
        Entity(
            id=params.keeper,
            kind="character",
            type="ghost",
            label=f"Keeper {params.keeper}",
            meters={"visible": 0.0, "glow": 0.25, "distance_to_bell": 0.0},
            memes={"longing": 0.8, "belonging": 0.2, "worry": 0.25},
        )
    )
    certificate = world.add(
        Entity(
            id="watch_certificate",
            kind="object",
            type="certificate",
            label="the Snowbell Watch certificate",
            meters={"found": 0.0, "dry": 1.0, "legible": 1.0},
        )
    )
    avalanche = world.add(
        Entity(
            id="avalanche",
            kind="event",
            type="avalanche",
            label="the avalanche",
            meters={"settled": 0.0, "blocks_high_route": 0.0, "distance_from_station": 900.0},
        )
    )
    crew = world.add(
        Entity(
            id="trail_crew",
            kind="group",
            type="trail_crew",
            label=scene["crew"],
            meters={"sheltered": 1.0, "waiting": 1.0, "guided": 0.0},
            memes={"worry": 0.4, "relief": 0.0},
        )
    )
    lanterns = world.add(
        Entity(
            id="signal_lanterns",
            kind="object",
            type="lanterns",
            label="three signal lanterns",
            meters={"count": 3.0, "lit": 0.0, "flashes": 0.0},
        )
    )
    lower_route = world.add(
        Entity(
            id="lower_route",
            kind="place",
            type="trail",
            label=scene["route"],
            meters={"known": 1.0, "safe_after_settle": 1.0},
        )
    )

    world.facts.update(
        lead=lead,
        friend=friend,
        keeper=keeper,
        certificate=certificate,
        avalanche=avalanche,
        crew=crew,
        lanterns=lanterns,
        lower_route=lower_route,
        scene=scene,
        phase="watch",
        high_route_closed=False,
        signal_sent=False,
        crew_safe=False,
    )

    station_name = station.name
    world.say(
        OPENINGS[params.opening].format(
            lead=lead.label,
            friend=friend.label,
            station=station_name,
        )
    )
    world.say(
        f"Beyond the window, {scene['crew']} waited inside {scene['shelter']}; "
        "the station window faced their shelter."
    )

    keeper.meters["visible"] = 1.0
    keeper.memes["worry"] = 0.45
    world.say(
        APPARITIONS[params.apparition].format(keeper=keeper.id)
    )
    world.say(
        f"“The watch certificate is missing,” {keeper.id} said. "
        "“Its old lantern code helped the first Snowbell team guide people after an avalanche.”"
    )
    world.say(
        f"“Could that code help the crew waiting outside?” {lead.id} asked."
    )
    world.say(
        f"“It could,” the ghost replied. “But we must find it and stay here, in safety.”"
    )

    world.facts["phase"] = "slide"
    avalanche.meters["blocks_high_route"] = 1.0
    world.facts["high_route_closed"] = True
    world.facts["crew_waiting_safely"] = True
    world.say(scene["avalanche_line"])
    world.say(
        f"The snow stopped well short of {station_name}, but it covered {scene['blocked']}."
    )
    lead.memes["worry"] = 0.65
    friend.memes["worry"] = 0.7
    world.say(
        f"“Should we hurry out and point the way?” {friend.id} asked."
    )
    world.say(
        f"“No,” {keeper.id} said. “The slope may slide again. We can guide them "
        "from the station window.”"
    )
    lead.memes["confidence"] = 0.55
    friend.memes["courage"] = 0.62
    world.facts["team_stays_sheltered"] = True

    world.facts["phase"] = "search"
    world.say(
        f"Keeping inside, {lead.id} and {friend.id} searched {SEARCHES[params.search]} together."
    )
    certificate.meters["found"] = 1.0
    certificate.meters["legible"] = 1.0
    lead.memes["understanding"] = 0.8
    friend.memes["understanding"] = 0.8
    world.say(
        "Inside a dry sleeve lay the certificate: “Presented to the Snowbell Watch "
        "for teamwork—every traveler reached the valley before the last great avalanche.”"
    )
    world.say(
        "A folded note on its back read, “Three slow lantern flashes mean: take "
        "the lower trail when the snow has stopped moving. Until then, stay sheltered.”"
    )
    world.say(
        f"“This honor belongs to the whole watch,” {lead.id} said. "
        "“No one kept the pass safe alone.”"
    )
    world.say(
        f"“Then we can work as a watch, too,” {friend.id} replied. "
        "“You read the map while I set the lamps.”"
    )

    world.facts["phase"] = "wait_for_settle"
    avalanche.meters["settled"] = 1.0
    world.say(
        f"They waited together until the roar faded and the slope was still. "
        f"The high route stayed closed; {crew.label} remained safely sheltered."
    )

    world.facts["phase"] = "signal"
    lead.meters["inside_station"] = 1.0
    friend.meters["inside_station"] = 1.0
    lanterns.meters["lit"] = 3.0
    lanterns.meters["flashes"] = 3.0
    lead.memes["teamwork"] = 0.9
    friend.memes["teamwork"] = 0.9
    keeper.memes["belonging"] = 0.75
    world.say(
        f"From the sheltered window, {lead.id} traced {scene['route']} on the map "
        f"while {friend.id} uncovered the three lanterns one at a time. "
        f"{keeper.id} counted each slow flash."
    )
    world.say(
        "Across the snow, a tiny answering light blinked from the shelter. "
        "The waiting crew had understood."
    )
    world.facts["signal_sent"] = True
    world.facts["crew_received_signal"] = True
    crew.meters["guided"] = 1.0
    crew.meters["waiting"] = 0.0
    crew.memes["relief"] = 0.9
    world.facts["crew_safe"] = True

    world.facts["phase"] = "resolution"
    world.say(
        f"At dawn, with the slide quiet, {crew.label} returned by {scene['route']}, "
        "well away from the buried pass."
    )
    world.say(
        f"{lead.id} and {friend.id} placed the certificate in a dry glass case above "
        f"the bell, where every visitor could read the Snowbell Watch's names."
    )
    keeper.memes["longing"] = 0.0
    keeper.memes["belonging"] = 1.0
    keeper.meters["glow"] = 0.8
    world.say(
        f"“Now everyone can remember the whole team,” {keeper.id} whispered. "
        "The ghost's blue outline softened into a reflection among the three warm lanterns."
    )
    world.say(
        "Outside, the avalanche rested far below the station, and the safe trail "
        "home shone silver in the morning light."
    )
    world.facts["certificate_honored"] = True
    world.facts["route_used"] = scene["route"]
    world.facts["teamwork_completed"] = True

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    lead = facts["lead"]
    friend = facts["friend"]
    keeper = facts["keeper"]
    scene = facts["scene"]
    return [
        (
            f"Write a gentle ghost story about {lead.id} and {friend.id}, who find "
            f"the Snowbell Watch certificate during an avalanche at {scene['ridge']}."
        ),
        (
            f"Tell a child-friendly teamwork story where Keeper {keeper.id} helps "
            "two friends guide a sheltered trail crew without approaching the slide."
        ),
        (
            f"Write a winter ghost story ending with the certificate displayed beside "
            f"the bell and the crew returning by {scene['route']}."
        ),
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    lead = facts["lead"]
    friend = facts["friend"]
    keeper = facts["keeper"]
    scene = facts["scene"]

    return [
        QAItem(
            question="What happened during the avalanche?",
            answer=(
                f"The avalanche covered {scene['blocked']}, but it stopped well short "
                "of Snowbell Station. The trail crew stayed safely in its shelter."
            ),
        ),
        QAItem(
            question=f"Why did {lead.id} and {friend.id} stay inside?",
            answer=(
                f"{keeper.id} warned them that the slope might slide again. They stayed "
                "sheltered and sent their directions from the station window instead."
            ),
        ),
        QAItem(
            question="What did the certificate's note teach them?",
            answer=(
                "The note said that three slow lantern flashes meant the crew should "
                f"use {scene['route']} after the snow had stopped moving. Until then, "
                "the crew should remain sheltered."
            ),
        ),
        QAItem(
            question="How did the friends use teamwork to help?",
            answer=(
                f"{lead.id} read the lower route on the map while {friend.id} uncovered "
                f"three lanterns one at a time. Keeper {keeper.id} counted the flashes, "
                "and the sheltered crew understood the signal."
            ),
        ),
        QAItem(
            question="Why was the ghost glad to see the certificate displayed?",
            answer=(
                f"The certificate honored the whole Snowbell Watch, not just Keeper "
                f"{keeper.id}. Displaying it let everyone remember that teamwork had "
                "helped keep travelers safe."
            ),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an avalanche?",
            answer=(
                "An avalanche is a large amount of snow that rushes down a mountain "
                "slope. People should stay away from avalanche paths and follow local "
                "safety instructions."
            ),
        ),
        QAItem(
            question="What is a certificate?",
            answer=(
                "A certificate is a written document that recognizes an achievement, "
                "a skill, or something a person or group has done."
            ),
        ),
        QAItem(
            question="How can teamwork help people solve a problem?",
            answer=(
                "Teamwork lets people share jobs, listen to one another, and combine "
                "what each person knows."
            ),
        ),
        QAItem(
            question="What should someone do if an avalanche blocks a trail?",
            answer=(
                "They should stay away from the slide, move to a safe place if needed, "
                "and follow directions from trained local helpers."
            ),
        ),
        QAItem(
            question="What is a ghost in a story?",
            answer=(
                "A ghost is a spirit that appears in a story. Ghost stories can be "
                "mysterious, funny, or gentle as well as frightening."
            ),
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
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
    for entity in world.entities.values():
        bits = []
        if entity.meters:
            bits.append(f"meters={entity.meters}")
        if entity.memes:
            bits.append(f"memes={entity.memes}")
        lines.append(
            f"  {entity.id:20} ({entity.type:14}) {' '.join(bits)}"
        )
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    lines.append(f"  phase: {world.facts.get('phase')}")
    return "\n".join(lines)


ASP_RULES = r"""
safe_response(S) :-
    scene(S),
    crew_sheltered(S),
    signal_window_visible(S),
    lower_route_known(S),
    wait_for_settle(S).

certificate_honored :-
    certificate_recovered,
    team_shared_signal,
    crew_safe.
"""


def asp_facts() -> str:
    import asp

    facts = []
    for scene in SCENES:
        facts.extend(
            [
                asp.fact("scene", scene["id"]),
                asp.fact("crew_sheltered", scene["id"]),
                asp.fact("signal_window_visible", scene["id"]),
                asp.fact("lower_route_known", scene["id"]),
                asp.fact("wait_for_settle", scene["id"]),
            ]
        )
    facts.extend(
        [
            asp.fact("certificate_recovered"),
            asp.fact("team_shared_signal"),
            asp.fact("crew_safe"),
        ]
    )
    return "\n".join(facts)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def python_valid_scenes() -> set[tuple]:
    return {
        (scene["id"],)
        for scene in SCENES
        if python_reasonableness_gate(scene)
    }


def asp_valid() -> tuple[set[tuple], set[tuple]]:
    import asp

    model = asp.one_model(
        asp_program("#show safe_response/1.\n#show certificate_honored/0.")
    )
    return (
        set(asp.atoms(model, "safe_response")),
        set(asp.atoms(model, "certificate_honored")),
    )


def asp_verify() -> int:
    import asp

    try:
        model = asp.one_model(
            asp_program("#show safe_response/1.\n#show certificate_honored/0.")
        )
        clingo_scenes = set(asp.atoms(model, "safe_response"))
        clingo_honored = set(asp.atoms(model, "certificate_honored"))
        python_scenes = python_valid_scenes()
        python_honored = {()} if python_scenes else set()

        if clingo_scenes != python_scenes or clingo_honored != python_honored:
            print("MISMATCH between the ASP rules and Python reasonableness gate.")
            print("  ASP safe scenes:", sorted(clingo_scenes))
            print("  Python safe scenes:", sorted(python_scenes))
            print("  ASP certificate honored:", sorted(clingo_honored))
            print("  Python certificate honored:", sorted(python_honored))
            return 1

        for index, scene in enumerate(SCENES):
            params = StoryParams(
                seed=1000 + index,
                lead=LEADS[index],
                friend=FRIENDS[index],
                keeper=KEEPERS[index],
                scene=index,
                opening=index % len(OPENINGS),
                apparition=index % len(APPARITIONS),
                search=index % len(SEARCHES),
            )
            sample = generate(params)
            story = sample.story
            required = ("certificate", "avalanche", "ghost", "teamwork", "lantern")
            if not all(word in story.lower() for word in required):
                raise AssertionError(f"Generated story for {scene['id']} is missing a required story element.")
            if "{" in story or "}" in story:
                raise AssertionError(f"Generated story for {scene['id']} contains an unresolved field.")
            if story.count("“") < 4 or story.count("”") < 4:
                raise AssertionError(f"Generated story for {scene['id']} is missing spoken dialogue.")
            if sample.world is None or not sample.world.facts.get("crew_safe"):
                raise AssertionError(f"Generated story for {scene['id']} did not resolve the crew's danger.")
            if not sample.story_qa or not sample.world_qa:
                raise AssertionError(f"Generated story for {scene['id']} is missing QA.")

        print(
            "OK: ASP parity matches the Python gate, and every avalanche scene "
            "generates a complete, dialogued story."
        )
        return 0
    except Exception as exc:
        print(f"Verification failed: {exc}")
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Winter ghost stories about a certificate, an avalanche, and teamwork."
    )
    parser.add_argument("--lead", choices=LEADS)
    parser.add_argument("--friend", choices=FRIENDS)
    parser.add_argument("--keeper", choices=KEEPERS)
    parser.add_argument("--scene", type=int, choices=range(len(SCENES)))
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


CURATED = [
    StoryParams(
        lead="Mara",
        friend="Ivo",
        keeper="Edda",
        scene=0,
        opening=0,
        apparition=0,
        search=0,
    ),
    StoryParams(
        lead="Tess",
        friend="Lila",
        keeper="Alder",
        scene=1,
        opening=2,
        apparition=1,
        search=1,
    ),
    StoryParams(
        lead="Niko",
        friend="Jun",
        keeper="Wren",
        scene=2,
        opening=3,
        apparition=2,
        search=2,
    ),
    StoryParams(
        lead="Sana",
        friend="Bea",
        keeper="Sol",
        scene=3,
        opening=4,
        apparition=0,
        search=1,
    ),
]


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    header: str = "",
) -> None:
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

    if args.n < 1 and not args.all:
        raise StoryError("-n must be at least 1.")

    if args.show_asp:
        print(asp_program("#show safe_response/1.\n#show certificate_honored/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        safe_scenes, honored = asp_valid()
        print(f"{len(safe_scenes)} ASP-approved safe avalanche scenes")
        for scene in sorted(safe_scenes):
            print(f"safe response: {scene[0]}")
        print(f"Certificate honored by teamwork: {'yes' if honored else 'no'}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        limit = max(50, args.n * 30)
        while len(samples) < args.n and attempt < limit:
            rng = random.Random(base_seed + attempt)
            params = resolve_params(args, rng)
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            attempt += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.lead}: avalanche watch at Snowbell Station"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

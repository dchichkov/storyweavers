#!/usr/bin/env python3
"""Child-friendly pirate tales about a historic shutter, friendship, and problem solving."""

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

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


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
class Harbor:
    name: str = "Old Lantern Harbor"
    tide: str = "rising"
    has_lighthouse: bool = True


@dataclass
class StoryParams:
    seed: Optional[int] = None
    captain: str = "Luna"
    friend: str = "Pip"
    harbor: str = "Old Lantern Harbor"
    incident: int = 0
    opening: int = 0
    dialogue: int = 0
    turn: int = 0
    cadence: int = 0


CAPTAINS = ["Luna", "Maris", "Nell", "Coral", "Tess", "Mira"]
FRIENDS = ["Pip", "Finn", "Jory", "Bram", "Kit", "Sable"]
HARBORS = ["Old Lantern Harbor", "Moonwake Cove", "Cannonberry Bay", "Starboard Village"]

INCIDENTS = [
    {
        "title": "the jammed lighthouse shutter",
        "premise": "A historic lighthouse had guided friendly ships for a hundred years.",
        "problem": "Its wooden shutter jammed just as a fishing boat searched for the harbor through thick fog.",
        "clue": "Luna noticed that the lower hinge was packed with salty sand, while the upper hinge still moved.",
        "plan": "They would lift the shutter from below, rinse the hinge, and tie the loose side with sailcloth.",
        "action": "Pip poured fresh water over the hinge while Luna levered the shutter with a smooth oar.",
        "result": "The hinge loosened, the shutter swung open, and the lighthouse beam swept across the fog.",
        "lesson": "Friends solve hard problems by sharing clues, tools, and courage.",
        "ending": "That night, the historic shutter gleamed beside the bright lighthouse window.",
        "object": "historic shutter",
    },
    {
        "title": "the stuck harbor signal",
        "premise": "A historic signal house stood above a narrow pirate harbor.",
        "problem": "Its shutter would not open to show a safe passage during the rising tide.",
        "clue": "Luna saw a rope caught behind the shutter and a small shell wedged under its frame.",
        "plan": "They would free the rope first, remove the shell, and pull together when the tide dipped.",
        "action": "Pip tugged the rope loose while Luna cleared the shell with a spoon from the galley.",
        "result": "The shutter opened before the tide covered the hidden rocks.",
        "lesson": "A careful team checks small causes before using great force.",
        "ending": "The green signal cloth fluttered from the historic window above calm water.",
        "object": "signal shutter",
    },
    {
        "title": "the storm-battered gallery",
        "premise": "The crew cared for a historic gallery that displayed maps from old voyages.",
        "problem": "A storm slammed its shutter inward, leaving rain near the treasured maps.",
        "clue": "Luna found that one beam was sound and could support a temporary brace.",
        "plan": "They would brace the beam, fold a spare sail over the maps, and fasten the shutter until morning.",
        "action": "Pip spread the sail while Luna wedged the beam in place with a barrel stave.",
        "result": "The maps stayed dry, and the shutter held through the storm.",
        "lesson": "Problem solving means protecting what matters while making a safe temporary fix.",
        "ending": "When sunrise came, the old maps dried beneath the repaired historic shutter.",
        "object": "gallery shutter",
    },
    {
        "title": "the moonlit harbor clue",
        "premise": "A historic watchtower had a shutter painted with a silver crescent.",
        "problem": "The shutter stuck closed, hiding the moon mark that sailors used to find the friendly dock.",
        "clue": "Pip heard a soft scrape whenever the wind pushed from the east.",
        "plan": "They would pull from the west side while Luna pressed the eastern edge away from the frame.",
        "action": "They counted together—one, two, three—and the shutter popped free with a wooden clack.",
        "result": "The silver crescent shone, and a tired merchant vessel found the safe dock.",
        "lesson": "Listening closely can reveal the right way to work together.",
        "ending": "The moon painted a silver path across the open historic shutter.",
        "object": "moon-marked shutter",
    },
    {
        "title": "the breakfast bell window",
        "premise": "The harbor's historic inn used a shuttered window to signal breakfast to every crew.",
        "problem": "The shutter would not lift, and hungry sailors were waiting in the rain.",
        "clue": "Luna found a bent nail rubbing against the frame.",
        "plan": "They would loosen the nail, oil the wood with cooking grease, and lift slowly.",
        "action": "Pip held the lantern while Luna tapped the nail free with a tiny hammer.",
        "result": "The shutter rose, and the cook rang the breakfast bell.",
        "lesson": "Good friends make room for each person's useful job.",
        "ending": "Steam curled past the historic shutter as warm bread reached the deck.",
        "object": "inn shutter",
    },
    {
        "title": "the museum's missing breeze",
        "premise": "A historic sea museum stored a small ship inside its cool stone hall.",
        "problem": "A closed shutter trapped hot air around the model ship.",
        "clue": "Pip noticed that the shutter opened a finger-width when a rope was pulled sideways.",
        "plan": "They would pull sideways, place a wooden wedge, and let the sea breeze enter safely.",
        "action": "Luna pulled the rope while Pip slid the wedge beneath the frame.",
        "result": "Fresh air crossed the hall without knocking over the delicate model.",
        "lesson": "The best solution can be gentle, simple, and well timed.",
        "ending": "The model ship rested in a cool breeze beside the historic shutter.",
        "object": "museum shutter",
    },
]

OPENINGS = [
    "At dawn, Captain {captain} sailed into {harbor} with {friend} beside the wheel.",
    "The sea glittered around {harbor}, where Captain {captain} and {friend} shared a tidy little ship.",
    "Captain {captain} and {friend} were polishing their compass when trouble called from {harbor}.",
    "A salty breeze swept over {harbor} as {captain} and {friend} prepared for another friendly voyage.",
    "Near the oldest pier in {harbor}, Captain {captain} trusted {friend} with every important task.",
    "The crew's quiet morning ended when Captain {captain} spotted {friend} pointing toward the lighthouse.",
]

DIALOGUES = [
    "'The shutter is stuck!' cried {friend}. 'Then we will study it before we shove it,' said {captain}.",
    "'Should we pull harder?' asked {friend}. 'Not yet,' replied {captain}. 'Tell me what you noticed.'",
    "'I see sand by the hinge,' said {friend}. 'Good eyes,' said {captain}. 'Your clue gives us a safer plan.'",
    "'My rope can help,' said {friend}. 'And my oar can lift,' answered {captain}. 'Together, we have enough.'",
    "'What if we fail?' whispered {friend}. 'We can try one careful step at a time,' said {captain}.",
    "'I found the trouble!' shouted {friend}. Captain {captain} smiled. 'Then your discovery will guide our next move.'",
]

TURNS = [
    "For a moment, the deck felt very quiet. Then {captain} listened to {friend}'s clue and changed the plan.",
    "{friend}'s observation changed everything: instead of forcing the wood, the friends worked on the hidden cause.",
    "Captain {captain} almost reached for a heavy mallet, but {friend}'s careful warning stopped the risky idea.",
    "The first tug failed. Rather than blame each other, the friends looked again and found the smaller obstacle.",
    "They could not solve the problem with one strong pull, so they divided the work and tried together.",
    "A gust shook the harbor, but {captain} and {friend} agreed that patience was safer than panic.",
]

CADENCES = [
    "They checked each step before beginning the next.",
    "The sea waited, but the friends did not waste a single useful clue.",
    "Their plan was small, steady, and strong enough for the trouble.",
    "One friend watched, one friend worked, and both friends kept speaking clearly.",
    "The answer arrived through teamwork rather than a captain's command alone.",
    "Even a pirate crew needs patience when old wood refuses to move.",
]


ASP_RULES = r"""
#show friendship/2.
#show solved/1.

friendship(A, B) :- trusts(A, B), helps(A, B).
solved(P) :- clue(P), shared_plan(P), safe_result(P).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("trusts", "captain", "friend"),
            asp.fact("helps", "captain", "friend"),
            asp.fact("clue", "shutter_problem"),
            asp.fact("shared_plan", "shutter_problem"),
            asp.fact("safe_result", "shutter_problem"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Pirate tale storyworld about a historic shutter, friendship, and problem solving."
    )
    parser.add_argument("--captain", choices=CAPTAINS)
    parser.add_argument("--friend", choices=FRIENDS)
    parser.add_argument("--harbor", choices=HARBORS)
    parser.add_argument("--incident", type=int, choices=range(len(INCIDENTS)))
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.n < 1:
        raise StoryError("-n must be at least 1.")
    return StoryParams(
        seed=args.seed,
        captain=args.captain or rng.choice(CAPTAINS),
        friend=args.friend or rng.choice(FRIENDS),
        harbor=args.harbor or rng.choice(HARBORS),
        incident=args.incident if args.incident is not None else rng.randrange(len(INCIDENTS)),
        opening=rng.randrange(len(OPENINGS)),
        dialogue=rng.randrange(len(DIALOGUES)),
        turn=rng.randrange(len(TURNS)),
        cadence=rng.randrange(len(CADENCES)),
    )


def generate(params: StoryParams) -> StorySample:
    if params.captain == params.friend:
        raise StoryError("The captain and friend must have different names.")
    if not 0 <= params.incident < len(INCIDENTS):
        raise StoryError("The incident number is outside the available pirate tales.")

    harbor = Harbor(name=params.harbor)
    world = World()
    world.facts["harbor"] = harbor

    captain = world.add(
        Entity(
            id=params.captain,
            kind="character",
            type="captain",
            label=params.captain,
            memes={"courage": 1.0, "trust": 1.0},
        )
    )
    friend = world.add(
        Entity(
            id=params.friend,
            kind="character",
            type="sailor",
            label=params.friend,
            memes={"curiosity": 1.0, "trust": 1.0},
        )
    )
    shutter = world.add(
        Entity(
            id="historic_shutter",
            kind="object",
            type="shutter",
            label="historic shutter",
            meters={"height": 2.0, "hinge_friction": 1.0, "age": 100.0},
            memes={"importance": 1.0},
        )
    )

    incident = INCIDENTS[params.incident]
    names = {
        "captain": captain.id,
        "friend": friend.id,
        "harbor": harbor.name,
    }

    world.say(OPENINGS[params.opening].format(**names))
    world.say(incident["premise"])
    world.say(incident["problem"])
    world.say(DIALOGUES[params.dialogue].format(**names))
    world.say(TURNS[params.turn].format(**names))
    world.say(incident["clue"])
    world.say(f"{captain.id} and {friend.id} agreed: {incident['plan']}")
    world.say(CADENCES[params.cadence])
    world.say(incident["action"])
    world.say(incident["result"])

    shutter.meters["hinge_friction"] = 0.0
    shutter.memes["useful_history"] = 1.0
    captain.memes["confidence"] = 1.0
    friend.memes["confidence"] = 1.0
    world.facts.update(
        captain=captain,
        friend=friend,
        shutter=shutter,
        incident=incident,
        friendship=True,
        problem_solved=True,
        historic=True,
        solution=incident["plan"],
    )

    world.say(
        f"{captain.id} hugged {friend.id}. 'We solved it together,' said {captain.id}. "
        f"'Aye,' said {friend.id}, 'your listening and my clue made one strong plan.'"
    )
    world.say(f"Lesson learned: {incident['lesson']}")
    world.say(incident["ending"])

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    incident = world.facts["incident"]
    captain = world.facts["captain"]
    friend = world.facts["friend"]
    return [
        f"Write a child-friendly pirate tale about {captain.id} and {friend.id} solving {incident['title']}.",
        f"Tell a friendship story in which a historic shutter causes a problem and two pirates share clues and tools.",
        f"Write a pirate adventure with spoken dialogue, a careful repair, and an ending image involving the {incident['object']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    incident = world.facts["incident"]
    captain = world.facts["captain"]
    friend = world.facts["friend"]
    return [
        QAItem(
            question=f"What problem did {captain.id} and {friend.id} face?",
            answer=f"They faced this problem: {incident['problem']}",
        ),
        QAItem(
            question=f"What clue did {friend.id} notice?",
            answer=incident["clue"],
        ),
        QAItem(
            question=f"How did {captain.id} and {friend.id} solve the problem?",
            answer=f"They worked together this way: {incident['action']}",
        ),
        QAItem(
            question="How did friendship help in the story?",
            answer=(
                f"{captain.id} listened to {friend.id}'s observation, and {friend.id} helped with the work. "
                "Their trust let them combine different skills instead of using force alone."
            ),
        ),
        QAItem(
            question="What changed by the ending?",
            answer=f"The shutter opened or held safely, and {incident['result'].lower()}",
        ),
        QAItem(
            question="What lesson was learned?",
            answer=f"The lesson was: {incident['lesson']}",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a shutter?",
            answer="A shutter is a cover that can close over a window or opening.",
        ),
        QAItem(
            question="What does historic mean?",
            answer="Historic describes something important from the past or connected with history.",
        ),
        QAItem(
            question="Why is friendship useful when solving a problem?",
            answer="Friends can share observations, encouragement, tools, and different ways of thinking.",
        ),
        QAItem(
            question="Why should people avoid forcing an old object?",
            answer="Forcing an old object can damage it, so it is safer to inspect the cause and use a careful plan.",
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
        details = []
        if entity.meters:
            details.append(f"meters={entity.meters}")
        if entity.memes:
            details.append(f"memes={entity.memes}")
        lines.append(f"  {entity.id:18} ({entity.type:8}) {' '.join(details)}")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


def asp_verify() -> int:
    import asp
    expected_friendship = {("captain", "friend")}
    expected_solved = {("shutter_problem",)}
    model = asp.one_model(asp_program("#show friendship/2.\n#show solved/1."))
    actual_friendship = set(asp.atoms(model, "friendship"))
    actual_solved = set(asp.atoms(model, "solved"))
    if actual_friendship != expected_friendship or actual_solved != expected_solved:
        print("MISMATCH between clingo and Python gate.")
        print("  friendship:", sorted(actual_friendship))
        print("  expected:", sorted(expected_friendship))
        print("  solved:", sorted(actual_solved))
        print("  expected:", sorted(expected_solved))
        return 1

    for params in CURATED:
        sample = generate(params)
        if "historic" not in sample.story.lower() or "shutter" not in sample.story.lower():
            print("Generated story failed historic-shutter coverage.")
            return 1
        if not any(item.question.startswith("How did friendship") for item in sample.story_qa):
            print("Generated story failed friendship QA coverage.")
            return 1

    print("OK: clingo parity and generated-story checks passed.")
    return 0


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show friendship/2.\n#show solved/1."))
    return sorted(set(asp.atoms(model, "friendship")) | set(asp.atoms(model, "solved")))


CURATED = [
    StoryParams(
        captain="Luna",
        friend="Pip",
        harbor="Old Lantern Harbor",
        incident=0,
        opening=0,
        dialogue=2,
        turn=1,
        cadence=3,
    ),
    StoryParams(
        captain="Maris",
        friend="Finn",
        harbor="Moonwake Cove",
        incident=2,
        opening=2,
        dialogue=3,
        turn=4,
        cadence=1,
    ),
    StoryParams(
        captain="Coral",
        friend="Jory",
        harbor="Starboard Village",
        incident=3,
        opening=4,
        dialogue=5,
        turn=2,
        cadence=4,
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

    if args.show_asp:
        print(asp_program("#show friendship/2.\n#show solved/1."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        atoms = asp_valid()
        print(f"{len(atoms)} ASP-supported friendship/problem-solving facts")
        for atom in atoms:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        limit = max(50, args.n * 40)
        while len(samples) < args.n and attempt < limit:
            params = resolve_params(args, random.Random(base_seed + attempt))
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            attempt += 1

        if len(samples) < args.n:
            raise StoryError("Could not create the requested number of distinct stories.")

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        if args.all:
            header = f"### {sample.params.captain}: historic shutter at {sample.params.harbor}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        else:
            header = ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

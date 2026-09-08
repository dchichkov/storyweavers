#!/usr/bin/env python3
"""
A small pirate-tale storyworld about a clip, a risky shortcut, and reconciliation.
"""

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
import os
import random
import sys
from dataclasses import dataclass, field

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_root, "results.py")):
    _root = os.path.dirname(_root)
sys.path.insert(0, _root)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    captain: str
    deckhand: str
    parrot: str
    seed: int | None = None
    scenario_id: int = 0
    dialogue_id: int = 0
    ending_id: int = 0


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
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


CAPTAINS = ["Captain Luna", "Captain Mira", "Captain Sol", "Captain Nia"]
DECKHANDS = ["Pip", "Mara", "Finn", "Toby", "Nori", "Jett"]
PARROTS = ["Bluebell", "Coco", "Feather", "Pepper"]

SCENARIOS = [
    {
        "place": "the windy rope deck",
        "cargo": "a silver compass",
        "warning": "the clip was not locked and could spring open when the ship rocked",
        "risk": "fastening the compass to a loose sail cord",
        "turn": "a sudden wave snapped the cord, and the compass slid toward the rail",
        "clue": "a second clip with a closed safety latch in the tool chest",
        "repair": "Captain Luna stopped blaming anyone and asked the crew to name the danger together",
        "lesson": "A shortcut is not brave when it leaves a treasure one wave away from the sea.",
        "image": "The compass rested safely on the chart table while the locked clip gleamed beside it.",
    },
    {
        "place": "the moonlit chart cabin",
        "cargo": "a rolled treasure map",
        "warning": "the clip's sharp end could tear the old map if it was forced across too much paper",
        "risk": "pinching the map tightly before checking its folds",
        "turn": "the paper ripped along a faded coastline when the cabin door slammed",
        "clue": "a soft ribbon and a wide clip made for holding thick charts",
        "repair": "the deckhand admitted the hurry and helped smooth the map flat",
        "lesson": "Careful hands protect old treasures better than hurried hands.",
        "image": "The repaired map lay open beneath the wide clip, with every island still visible.",
    },
    {
        "place": "the crow's-nest lookout",
        "cargo": "a bright signal flag",
        "warning": "a small clip could not hold the flag against the gusts above the mast",
        "risk": "climbing high with one hand busy and the flag barely fastened",
        "turn": "the flag tore loose and fluttered into the dark water",
        "clue": "a pair of strong clips could hold the flag at two corners",
        "repair": "the captain lowered the ladder and invited the whole crew to plan a safer signal",
        "lesson": "A careful plan can save both a flag and the sailor carrying it.",
        "image": "The signal flag waved from two strong clips while the crew watched from the deck.",
    },
]

DIALOGUES = [
    ('"Wait, matey. What could happen if that clip lets go?"',
     '"You are right. I saw the shortcut, but I did not see the danger."'),
    ('"Tell me what you noticed before we sail on,"',
     '"The clip needs a safer job, and I can help fix it."'),
    ('"A good captain listens when a warning sounds,"',
     '"Then let us mend the mistake together."'),
]

ENDINGS = [
    "From that day on, the crew tested every fastening before trusting it.",
    "The crew added a new rule to the ship's book: check the clip, then check it again.",
    "Afterward, nobody laughed at a small warning, because small warnings could guard big treasures.",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A cautionary pirate tale about a clip and reconciliation.")
    parser.add_argument("--captain", choices=CAPTAINS)
    parser.add_argument("--deckhand", choices=DECKHANDS)
    parser.add_argument("--parrot", choices=PARROTS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    captain = args.captain or rng.choice(CAPTAINS)
    deckhand = args.deckhand or rng.choice(DECKHANDS)
    parrot = args.parrot or rng.choice(PARROTS)
    return StoryParams(
        captain=captain,
        deckhand=deckhand,
        parrot=parrot,
        scenario_id=rng.randrange(len(SCENARIOS)),
        dialogue_id=rng.randrange(len(DIALOGUES)),
        ending_id=rng.randrange(len(ENDINGS)),
    )


def validate_params(params: StoryParams) -> None:
    if not params.captain or not params.deckhand or not params.parrot:
        raise StoryError("A captain, deckhand, and parrot are required.")
    if params.captain == params.deckhand:
        raise StoryError("The captain and deckhand must be different characters.")
    if not 0 <= params.scenario_id < len(SCENARIOS):
        raise StoryError("The scenario choice is outside the available pirate scenarios.")


def tell(params: StoryParams) -> World:
    validate_params(params)
    scenario = SCENARIOS[params.scenario_id]
    first_line, second_line = DIALOGUES[params.dialogue_id % len(DIALOGUES)]

    world = World()
    captain = world.add(Entity("captain", "character", params.captain))
    deckhand = world.add(Entity("deckhand", "character", params.deckhand))
    parrot = world.add(Entity("parrot", "animal", params.parrot))
    clip = world.add(Entity("clip", "tool", "a brass safety clip"))
    treasure = world.add(Entity("treasure", "cargo", scenario["cargo"]))

    world.facts.update(
        captain=captain,
        deckhand=deckhand,
        parrot=parrot,
        clip=clip,
        treasure=treasure,
        scenario=scenario,
        resolved=False,
    )

    captain.memes["responsibility"] = 1.0
    deckhand.memes["eager"] = 1.0
    clip.meters["small"] = 1.0

    world.say(
        f"Captain {params.captain} sailed with {params.deckhand} and a parrot named {params.parrot} "
        f"aboard a little pirate ship."
    )
    world.say(
        f"At {scenario['place']}, they had to protect {scenario['cargo']} with a brass clip. "
        f"The clip looked tiny, but it held an important job."
    )
    world.say(f"{params.deckhand} hurried to finish by {scenario['risk']}.")
    deckhand.memes["hurry"] = 1.0
    world.say(f"The parrot flapped and cried, \"Careful! {scenario['warning']}\"")
    world.say(f"But before anyone could answer, {scenario['turn']}.")
    treasure.meters["endangered"] = 1.0

    world.para()
    world.say(f"Captain {params.captain} caught the {scenario['cargo']} and took a slow breath.")
    world.say(f"{first_line}")
    world.say(f"{second_line}")
    world.say(
        f"{params.deckhand} explained that the shortcut seemed quick, but had not considered that {scenario['warning']}."
    )
    world.say(f"The captain found {scenario['clue']}.")
    world.say(f"{scenario['repair']}.")
    deckhand.memes["ashamed"] = 1.0
    deckhand.memes["forgiven"] = 1.0
    captain.memes["listening"] = 1.0

    world.say(
        f"Together, the sailors secured {scenario['cargo']} with the safer clip and tested it while the parrot watched."
    )
    clip.meters["locked"] = 1.0
    treasure.meters["safe"] = 1.0
    treasure.meters["endangered"] = 0.0
    world.facts["resolved"] = True

    world.para()
    world.say(scenario["lesson"])
    world.say(ENDINGS[params.ending_id % len(ENDINGS)])
    world.say(scenario["image"])
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    scenario = world.facts["scenario"]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            f"Write a cautionary pirate tale about {scenario['cargo']} and a small clip.",
            f"Show how {params.deckhand} makes a risky shortcut, then repairs the mistake with Captain {params.captain}.",
            "Include a parrot's warning, honest dialogue, reconciliation, and a safer final fastening.",
        ],
        story_qa=[
            QAItem("What object caused the problem?", f"The brass clip caused the problem because it was used without first checking whether it was safe for {scenario['cargo']}."),
            QAItem("What warning did the parrot give?", f"The parrot warned that {scenario['warning']}."),
            QAItem("How did the crew reconcile?", f"{params.deckhand} admitted the mistake, and Captain {params.captain} listened instead of blaming them. They then {scenario['repair']}."),
            QAItem("What changed at the end?", f"They secured {scenario['cargo']} with a safer clip and tested it before trusting it."),
        ],
        world_qa=[
            QAItem("What is a clip?", "A clip is a small tool that grips or holds things together."),
            QAItem("What does cautionary mean?", "Cautionary means giving a warning about danger or a mistake."),
            QAItem("What is reconciliation?", "Reconciliation is the process of repairing a disagreement and becoming peaceful again."),
            QAItem("Why should a fastening be tested?", "It should be tested so that an object does not come loose and cause harm or loss."),
        ],
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("\n== story qa ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("\n== world qa ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"{entity.id}: {entity.label} meters={meters} memes={memes}")
    lines.append(f"resolved={world.facts.get('resolved')}")
    return "\n".join(lines)


ASP_RULES = r"""
clip_available.
warning_heard.
mistake_admitted.
safer_clip_used.
reconciled :- warning_heard, mistake_admitted.
story_safe :- reconciled, safer_clip_used.
#show story_safe/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("clip_available"),
        asp.fact("warning_heard"),
        asp.fact("mistake_admitted"),
        asp.fact("safer_clip_used"),
    ])


def asp_program(show: str = "#show story_safe/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    found = set(asp.atoms(model, "story_safe"))
    if found == {()}:
        print("OK: ASP parity matches Python gate.")
        return 0
    print("MISMATCH")
    print("ASP:", sorted(found))
    print("PY :", [()])
    return 1


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print("\n" + format_qa(sample))


CURATED = [
    StoryParams("Captain Luna", "Pip", "Bluebell", scenario_id=0, dialogue_id=0, ending_id=0),
    StoryParams("Captain Mira", "Mara", "Coco", scenario_id=1, dialogue_id=1, ending_id=1),
    StoryParams("Captain Sol", "Finn", "Feather", scenario_id=2, dialogue_id=2, ending_id=2),
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
        print(asp_program())
        print("ASP models:", len(asp.solve(asp_program(), models=1)))
        return

    seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        for index in range(max(0, args.n)):
            rng = random.Random(seed + index)
            params = resolve_params(args, rng)
            params.seed = seed + index
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
A small folk-tale storyworld about a spunky child, a moonlit motel, and a
misunderstanding repaired by listening.

Seed tale:
A spunky child named Luna helps at a roadside motel. One night, a guest leaves
a red scarf by the well. Luna hears the innkeeper say, "Keep it by the bell,"
and thinks the guest wants the scarf kept forever. She hangs it on the bell,
where the wind makes it flap like a warning flag. The guest returns frightened,
believing the motel bell is calling trouble.

Luna asks questions, discovers the mix-up, and returns the scarf. The guest
explains that "keep it by the bell" meant keep it safe until morning. Luna
learns that brave questions can untangle a misunderstanding.
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
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    type: str = "thing"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    @property
    def phrase(self) -> str:
        return self.label


@dataclass
class Setting:
    id: str
    place: str
    affords: set[str]
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Arc:
    opening: str
    misunderstanding: str
    clue: str
    repair: str
    ending: str
    cause: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    trace: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)
        self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "roadside": Setting(
        "roadside",
        "the Moonbeam Motel",
        {"well", "bell", "porch"},
        {"rooms": 12.0},
    ),
    "lake": Setting(
        "lake",
        "the Silver Lake Motel",
        {"well", "bell", "dock"},
        {"rooms": 8.0},
    ),
    "hill": Setting(
        "hill",
        "the Hilltop Motel",
        {"bell", "porch", "lantern"},
        {"rooms": 6.0},
    ),
}

OBJECTS = {
    "scarf": Entity("scarf", "object", "a red scarf", meters={"brightness": 0.8}),
    "bell": Entity("bell", "object", "the brass bell", meters={"sound": 1.0}),
    "well": Entity("well", "object", "the old well", meters={"depth": 4.0}),
    "lantern": Entity("lantern", "object", "the porch lantern", meters={"light": 1.0}),
}

ARCS = [
    Arc(
        opening="The motel windows glowed like warm squares in the dark, and Luna swept the porch with a broom twice as tall as she was.",
        misunderstanding="The innkeeper called, “Keep it by the bell,” and Luna thought he meant the red scarf must hang from the bell forever.",
        clue="When the wind rang the bell, the scarf snapped like a flag, but the guest's room key was still tucked in its pocket.",
        repair="Luna asked, “Did you mean keep the scarf safe until morning?” The guest nodded, and she gently took it down.",
        ending="At sunrise, the scarf warmed the guest's shoulders, while the quiet bell waited for a clearer message.",
        cause="The innkeeper meant to keep the scarf safe beside the bell until morning, not to tie it onto the bell.",
    ),
    Arc(
        opening="Luna counted the motel's little lamps and found one blinking above the office door.",
        misunderstanding="The traveler said, “Mind the red thing,” and Luna believed the traveler feared the scarf itself.",
        clue="The blinking lamp shone red whenever the office door opened, and the traveler kept looking at the loose door hinge.",
        repair="Luna asked, “Do you mean the red scarf, or the red lamp?” The traveler pointed to the hinge and explained the trouble.",
        ending="Luna fixed the hinge with the innkeeper, and the scarf rested safely on a chair.",
        cause="The traveler meant the red warning lamp, not the red scarf.",
    ),
    Arc(
        opening="Moonlight silvered the motel porch, where Luna polished the bell until she could see her spunky grin in it.",
        misunderstanding="A sleepy guest said, “Leave the light out,” and Luna carried the lantern into the yard.",
        clue="The guest covered her eyes, while the dark room's step became hard to see.",
        repair="Luna asked, “Did you mean leave the light on outside?” The guest laughed and pointed to the porch.",
        ending="The lantern shone over the step, and nobody stumbled beneath the kindly moon.",
        cause="The guest meant to leave the lantern out on the porch, not to leave the motel without light.",
    ),
    Arc(
        opening="A dusty road curled past the motel, and Luna made a tiny crown from a fallen feather.",
        misunderstanding="A farmer said, “Watch my crown,” and Luna guarded her feather crown instead of the farmer's hen.",
        clue="The hen clucked beside the well, while the feather crown sat safely on the office counter.",
        repair="Luna asked, “Which crown should I watch?” The farmer pointed to his noisy hen and thanked her for asking.",
        ending="The hen returned to its basket, and Luna wore her feather crown while she told the truth plainly.",
        cause="The farmer called his hen Crown, but Luna thought he meant her feather crown.",
    ),
    Arc(
        opening="Luna heard rain tapping the motel roof and placed bright cups beneath every drip.",
        misunderstanding="The innkeeper said, “Catch the silver,” and Luna chased a coin rolling across the porch.",
        clue="Water was filling a bucket under the roof, while the silver coin had stopped beside a boot.",
        repair="Luna asked, “Do you mean the rainwater or the coin?” The innkeeper pointed to the bucket.",
        ending="Together they caught the leak, and the silver coin became Luna's reward for careful listening.",
        cause="The innkeeper meant catch the silvery rainwater, not chase the silver coin.",
    ),
]

NAMES = ["Luna", "Mira", "Pip", "Nell", "Toby", "Rafi"]
HELPERS = ["the innkeeper", "Aunt Sela", "Old Bram", "the night clerk"]


@dataclass
class StoryParams:
    setting: str
    name: str
    helper: str
    arc: int = 0
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A spunky motel misunderstanding folk tale.")
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("--name")
    parser.add_argument("--helper")
    parser.add_argument("--arc", type=int, choices=range(len(ARCS)))
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
    setting = args.setting or rng.choice(list(SETTINGS))
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice(HELPERS)
    arc = args.arc if args.arc is not None else rng.randrange(len(ARCS))
    if not name.strip():
        raise StoryError("The motel helper needs a name.")
    if name == helper:
        raise StoryError("The child and helper must be different characters.")
    return StoryParams(setting=setting, name=name, helper=helper, arc=arc)


def tell(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown motel setting: {params.setting}.")
    if not 0 <= params.arc < len(ARCS):
        raise StoryError(f"Arc must be between 0 and {len(ARCS) - 1}.")
    setting = SETTINGS[params.setting]
    arc = ARCS[params.arc]
    world = World(setting)

    hero = world.add(Entity(params.name, "character", params.name, "child",
                            memes={"spunk": 1.0, "confidence": 0.7}))
    helper = world.add(Entity("helper", "character", params.helper, "adult",
                              memes={"patience": 1.0}))
    scarf = world.add(Entity("scarf", "object", "the red scarf", "cloth",
                             meters={"warmth": 0.8}, memes={"meaning": 0.0}))
    bell = world.add(Entity("bell", "object", "the brass bell", "bell",
                            meters={"sound": 1.0}))
    guest = world.add(Entity("guest", "character", "the traveler", "traveler",
                             memes={"worry": 0.4}))

    world.say(f"{hero.label} was a spunky helper at {setting.place}.")
    world.say(arc.opening)
    world.say(f"{hero.label} swept, counted keys, and kept {helper.label} company while {guest.label} rested in a small room.")

    world.para()
    hero.memes["worry"] = 0.6
    scarf.memes["meaning"] = 1.0
    world.say(arc.misunderstanding)
    world.say(f"{hero.label} followed the words exactly, because the motel was busy and nobody had yet explained what “it” meant.")
    world.say(f"The scarf hung from {bell.label}, and every gust made the bell ring.")

    world.para()
    world.say(arc.clue)
    world.say(f"{hero.label} noticed that {guest.label} looked worried, while {helper.label} looked surprised.")
    world.say(f"{hero.label} said, “Please tell me what you meant. I want to help, not guess.”")
    world.say(f"{guest.label} answered, “I meant that the scarf should stay safe beside the bell until morning.”")

    world.para()
    hero.memes["confidence"] += 0.5
    hero.memes["worry"] = 0.0
    guest.memes["worry"] = 0.0
    scarf.memes["meaning"] = 2.0
    world.say(arc.repair)
    world.say(f"{helper.label} smiled. “A question can be a little bridge,” {helper.label} said, “and bridges keep small mistakes from becoming big ones.”")
    world.say(f"{hero.label} placed {scarf.label} on the office chair, where it could stay dry and easy to find.")

    world.para()
    world.say("The misunderstanding was mended because everyone listened, asked, and answered plainly.")
    world.say(arc.ending)

    world.facts.update(
        hero=hero,
        helper=helper,
        guest=guest,
        scarf=scarf,
        bell=bell,
        arc=arc,
        setting=setting,
        resolved=True,
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            f"Tell a folk tale about {params.name}, a spunky helper at {world.setting.place}.",
            "Show how a misunderstanding changes when a child asks a brave, careful question.",
            f"Explain why {world.facts['arc'].cause}",
        ],
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(),
        world=world,
    )


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            "Who was spunky in the story?",
            f"{f['hero'].label} was the spunky helper at {f['setting'].place}.",
        ),
        QAItem(
            "What misunderstanding happened?",
            f["arc"].cause,
        ),
        QAItem(
            "How did the misunderstanding get solved?",
            f"{f['hero'].label} asked what the words meant, and {f['guest'].label} explained the intended meaning. Then the scarf was placed safely where it belonged.",
        ),
        QAItem(
            "Why was asking a question helpful?",
            "Asking a question let everyone compare what they thought the words meant, so a guess could be replaced by a clear explanation.",
        ),
        QAItem(
            "How did the story end?",
            f"The misunderstanding was repaired, the scarf was safe, and {f['arc'].ending}",
        ),
    ]


def world_knowledge_qa() -> list[QAItem]:
    return [
        QAItem("What is a motel?", "A motel is a place where travelers can rent rooms to rest, often beside a road."),
        QAItem("What is a misunderstanding?", "A misunderstanding happens when someone takes words or actions to mean something different from what was intended."),
        QAItem("What does spunky mean?", "Spunky means lively, brave, and full of energetic spirit."),
        QAItem("Why should people ask questions?", "People should ask questions when they are unsure, because clear answers can prevent mistakes."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    for item in sample.story_qa + sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: kind={entity.kind} type={entity.type} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"setting={world.setting.id} affordances={sorted(world.setting.affords)}")
    lines.append("state=misunderstanding_repaired")
    return "\n".join(lines)


ASP_RULES = r"""
character(X) :- person(X).
valid_motel(S) :- setting(S).
misunderstanding_repaired(S) :- valid_motel(S), asks_question(child), explains(guest).
clear_meaning(S) :- misunderstanding_repaired(S).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        for affordance in sorted(setting.affords):
            lines.append(asp.fact("affords", setting_id, affordance))
    lines.append(asp.fact("person", "child"))
    lines.append(asp.fact("person", "guest"))
    lines.append(asp.fact("asks_question", "child"))
    lines.append(asp.fact("explains", "guest"))
    return "\n".join(lines)


def asp_program(show: str = "#show misunderstanding_repaired/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
        models = asp.solve(asp_program(), models=1)
        atoms = asp.atoms(models[0], "misunderstanding_repaired") if models else []
    except Exception as exc:
        print(f"ASP unavailable or failed: {exc}")
        return 1
    if not atoms:
        print("ASP parity failed: no repaired misunderstanding.")
        return 1
    for setting_id in SETTINGS:
        sample = generate(StoryParams(setting_id, "Luna", "the innkeeper", 0, 0))
        if "misunderstanding" not in sample.story.lower():
            return 1
        if "asked" not in sample.story.lower():
            return 1
    print("OK: Python and ASP both represent a repaired motel misunderstanding.")
    return 0


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
    StoryParams("roadside", "Luna", "the innkeeper", 0),
    StoryParams("lake", "Pip", "Aunt Sela", 2),
    StoryParams("hill", "Mira", "Old Bram", 4),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        try:
            import asp
            models = asp.solve(asp_program(), models=1)
            print(json.dumps([str(atom) for atom in models[0]] if models else []))
        except Exception as exc:
            raise StoryError(f"ASP mode failed: {exc}") from exc
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        for offset in range(max(args.n * 20, 20)):
            if len(samples) >= args.n:
                break
            seed = base_seed + offset
            rng = random.Random(seed)
            params = resolve_params(args, rng)
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

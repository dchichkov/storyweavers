#!/usr/bin/env python3
"""
A small, self-contained comedy storyworld about a gadget, a pastime, and
kindness. Each tale plants a small warning before a gadget goes comically
wrong; the characters listen, help one another, and use that clue to set things
right.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(
        default_factory=lambda: {
            "distance": 0.0,
            "stability": 0.0,
            "order": 0.0,
            "completeness": 0.0,
        }
    )
    memes: dict[str, float] = field(
        default_factory=lambda: {
            "worry": 0.0,
            "courage": 0.0,
            "trust": 0.0,
            "kindness": 0.0,
            "joy": 0.0,
            "relief": 0.0,
        }
    )


@dataclass
class Setting:
    place: str = "the Tumbleberry Clubhouse"


@dataclass
class StoryParams:
    scenario_id: str
    gadget: str
    pastime: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
    caretaker_name: str
    detail_variant: int = 0
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting = field(default_factory=Setting)
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)
    trace_log: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(paragraph) for paragraph in self.paragraphs if paragraph)

    def log(self, text: str) -> None:
        self.trace_log.append(text)


SCENARIOS: dict[str, dict[str, str]] = {
    "curtain_crank": {
        "gadget": "the applause-powered curtain crank",
        "pastime": "a sock-puppet show",
        "purpose": "to lift the little stage curtain at just the right moment",
        "clue": "Before the show, a tiny brass bell on the crank gave two quick dings whenever its handle was turned.",
        "mishap": "The crank spun too far, whisked the curtain up, and lifted the puppets right along with it; a sock king dangled above the audience like a very surprised flag.",
        "hero_line": "That bell gave two dings before the curtain jumped. Maybe it is trying to warn us.",
        "friend_line": "Then let's help the stagehand lower it, and use the bell as our stop signal.",
        "kindness": "The friends noticed that Wren the young stagehand was embarrassed, so they told Wren the flying sock king had made the show funnier, not worse.",
        "method": "Together they lowered the curtain by hand, then turned the crank only until its little bell gave one careful ding.",
        "result": "The puppets returned to the stage, and the curtain rose smoothly for the grand finale.",
        "image": "the sock king bowed beneath the curtain while the audience clapped and Wren grinned",
        "lesson": "a warning is useful when a team listens before trying again",
    },
    "pocket_breeze": {
        "gadget": "the pocket breeze-maker",
        "pastime": "paper-plane races",
        "purpose": "to give each paper plane a gentle push toward the finish line",
        "clue": "A loose blue ribbon on the table kept pointing toward the prize basket whenever the breeze-maker was switched on.",
        "mishap": "The gadget sent a gust the wrong way, and the paper medals fluttered onto everyone's heads; one rabbit wore three like a very fancy hat.",
        "hero_line": "That ribbon kept pointing toward the basket. The breeze must be going that way, too.",
        "friend_line": "Let's turn the nozzle away from the medals and give the planes a clear lane.",
        "kindness": "The friends saw that Fern had carefully folded the medals, so they helped Fern collect them instead of teasing about the rabbit's new hat.",
        "method": "They followed the ribbon's direction, turned the nozzle toward the race lane, and tested one plane before starting the next race.",
        "result": "The planes glided down the lane, and every paper medal stayed safely on the prize table.",
        "image": "paper planes sailed past the finish line as the rabbit wore just one medal on its ribbon",
        "lesson": "kindness makes it easier to admit a mistake and fix it together",
    },
    "paint_wheel": {
        "gadget": "the self-stirring paint wheel",
        "pastime": "pebble painting",
        "purpose": "to mix bright colors for the pebble-painting table",
        "clue": "The wheel gave a small squeak on every third turn, though its paint cups were still wobbling.",
        "mishap": "It spun too fast and dotted the painter's noses with blue paint; the serious-looking badger suddenly had a very cheerful polka-dot snout.",
        "hero_line": "There was that squeak again, and the cups are still wobbling.",
        "friend_line": "Let's steady the tray and stop the wheel at the squeak instead of asking it to spin faster.",
        "kindness": "The friends asked Badger if the paint dots were all right, then offered a soft cloth and helped clean the table without making a fuss.",
        "method": "They steadied the tray, watched for the third-turn squeak, and switched the wheel off before the cups could wobble again.",
        "result": "The paint settled into neat colors, ready for everyone to decorate a pebble.",
        "image": "bright pebbles dried in a row while Badger's clean nose twitched beside them",
        "lesson": "noticing a small warning can prevent a much bigger mess",
    },
    "shell_counter": {
        "gadget": "the click-clack shell counter",
        "pastime": "sorting shells by shape",
        "purpose": "to count each shell as the friends sorted their favorite shapes",
        "clue": "A wooden bead near the counter's button clicked twice whenever it got stuck.",
        "mishap": "The counter counted one shell three times, and the friends proudly announced that their pile had more shells than the whole beach.",
        "hero_line": "That bead clicked twice, just like it did before the counter skipped.",
        "friend_line": "Let's clear the button gently and count the shells together, one at a time.",
        "kindness": "When Milo worried that the mistake was his fault, the friends reminded him that the counter had stuck and invited him to help check every shell.",
        "method": "They used the double click as a signal to pause, cleared the button, and recounted the pile together.",
        "result": "The shapes were sorted correctly, and the counter finally agreed with the friends.",
        "image": "three tidy shell rows shone on the table while Milo placed the last spiral shell",
        "lesson": "checking a mistake together is kinder than blaming someone",
    },
}

ANIMAL_TYPES = ("rabbit", "fox", "mouse", "duck", "badger", "otter", "squirrel", "turtle")
HERO_NAMES = ("Nina", "Pip", "Lulu", "Milo", "Tansy", "Bramble")
FRIEND_NAMES = ("Dot", "Wren", "Fern", "Bibi", "Moss", "Poppy")
CARETAKER_NAMES = ("Auntie Juniper", "Old Tumble", "Coach Clover", "Mr. Brindle")

CURATED = [
    StoryParams("curtain_crank", SCENARIOS["curtain_crank"]["gadget"], SCENARIOS["curtain_crank"]["pastime"], "Nina", "rabbit", "Wren", "mouse", "Auntie Juniper"),
    StoryParams("pocket_breeze", SCENARIOS["pocket_breeze"]["gadget"], SCENARIOS["pocket_breeze"]["pastime"], "Pip", "fox", "Fern", "duck", "Coach Clover"),
    StoryParams("paint_wheel", SCENARIOS["paint_wheel"]["gadget"], SCENARIOS["paint_wheel"]["pastime"], "Lulu", "otter", "Bramble", "badger", "Old Tumble"),
    StoryParams("shell_counter", SCENARIOS["shell_counter"]["gadget"], SCENARIOS["shell_counter"]["pastime"], "Milo", "mouse", "Dot", "turtle", "Mr. Brindle"),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A comic clubhouse storyworld about gadgets, pastimes, and kindness."
    )
    parser.add_argument("--gadget")
    parser.add_argument("--pastime")
    parser.add_argument("--name")
    parser.add_argument("--type")
    parser.add_argument("--friend")
    parser.add_argument("--friend-type")
    parser.add_argument("--caretaker")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    for field_name, supplied in (("--type", args.type), ("--friend-type", args.friend_type)):
        if supplied is not None and supplied not in ANIMAL_TYPES:
            raise StoryError(
                f"Invalid {field_name} value {supplied!r}; choose an animal type from: "
                + ", ".join(ANIMAL_TYPES)
            )

    candidates = list(SCENARIOS)
    if args.gadget is not None:
        candidates = [key for key in candidates if SCENARIOS[key]["gadget"] == args.gadget]
        if not candidates:
            valid = ", ".join(sorted({scenario["gadget"] for scenario in SCENARIOS.values()}))
            raise StoryError(f"Unknown gadget {args.gadget!r}; choose one of: {valid}")
    if args.pastime is not None:
        candidates = [key for key in candidates if SCENARIOS[key]["pastime"] == args.pastime]
        if not candidates:
            valid = ", ".join(sorted({scenario["pastime"] for scenario in SCENARIOS.values()}))
            raise StoryError(f"Unknown pastime {args.pastime!r}; choose one of: {valid}")
    if not candidates:
        raise StoryError(
            "That gadget and pastime are not a reasonable pair in this storyworld; "
            "choose a matching pair from the available scenarios."
        )

    scenario_id = rng.choice(candidates)
    scenario = SCENARIOS[scenario_id]
    return StoryParams(
        scenario_id=scenario_id,
        gadget=scenario["gadget"],
        pastime=scenario["pastime"],
        hero_name=args.name or rng.choice(HERO_NAMES),
        hero_type=args.type or rng.choice(ANIMAL_TYPES),
        friend_name=args.friend or rng.choice(FRIEND_NAMES),
        friend_type=args.friend_type or rng.choice(ANIMAL_TYPES),
        caretaker_name=args.caretaker or rng.choice(CARETAKER_NAMES),
        detail_variant=rng.randrange(8),
    )


def reasonable(params: StoryParams) -> bool:
    if params.scenario_id not in SCENARIOS:
        raise StoryError(f"Unknown scenario {params.scenario_id!r}.")
    scenario = SCENARIOS[params.scenario_id]
    if (params.gadget, params.pastime) != (scenario["gadget"], scenario["pastime"]):
        raise StoryError(
            f"{params.gadget!r} is not paired with {params.pastime!r} in this storyworld; "
            "each gadget needs its matching pastime."
        )
    if params.hero_type not in ANIMAL_TYPES or params.friend_type not in ANIMAL_TYPES:
        raise StoryError("The hero and friend must have a recognized animal type.")
    if not params.hero_name.strip() or not params.friend_name.strip() or not params.caretaker_name.strip():
        raise StoryError("Character names cannot be blank.")
    return True


def tell(params: StoryParams) -> World:
    reasonable(params)
    scenario = SCENARIOS[params.scenario_id]
    world = World()
    hero = world.add(Entity("hero", "animal", params.hero_type, params.hero_name))
    friend = world.add(Entity("friend", "animal", params.friend_type, params.friend_name))
    caretaker = world.add(Entity("caretaker", "animal", "turtle", params.caretaker_name))
    gadget = world.add(Entity("gadget", "thing", "gadget", params.gadget))
    pastime = world.add(Entity("pastime", "thing", "activity", params.pastime))
    world.facts.update(
        hero=hero,
        friend=friend,
        caretaker=caretaker,
        gadget=gadget,
        pastime=pastime,
        scenario=scenario,
        scenario_id=params.scenario_id,
        clue_noticed=True,
        kindness_shown=True,
        gadget_repaired=True,
    )

    hero.memes["joy"] += 1
    friend.memes["trust"] += 1
    caretaker.memes["worry"] += 1
    world.say(
        f"At the Tumbleberry Clubhouse, {params.hero_name} the {params.hero_type} and "
        f"{params.friend_name} the {params.friend_type} were ready for {params.pastime}."
    )
    world.say(
        f"{params.caretaker_name} brought out {params.gadget}, a gadget meant {scenario['purpose']}."
    )
    world.say(
        f"Before anyone began, {scenario['clue']} {params.hero_name} tucked that curious detail away."
    )
    world.para()

    gadget.meters["stability"] = -1.0
    caretaker.memes["worry"] += 1
    hero.memes["worry"] += 1
    world.say(f"Then the gadget had its comic little mishap: {scenario['mishap']}")
    world.say(
        f'"{scenario["hero_line"]}" {params.hero_name} said. '
        f'"{scenario["friend_line"]}" {params.friend_name} replied.'
    )
    world.para()

    friend.memes["kindness"] += 1
    hero.memes["kindness"] += 1
    friend.memes["courage"] += 1
    world.say(scenario["kindness"])
    world.say(scenario["method"])
    gadget.meters["stability"] = 1.0
    gadget.meters["order"] = 1.0
    pastime.meters["completeness"] = 1.0
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    caretaker.memes["relief"] += 1
    world.say(scenario["result"])
    world.para()

    world.say(
        f"{params.hero_name} learned that {scenario['lesson']}. "
        f"{scenario['image'].capitalize()}, a happy sign that the pastime could go on."
    )
    world.log(f"scenario={params.scenario_id}")
    world.log("warning noticed, kindness offered, gadget safely corrected")
    return world


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    hero: Entity = facts["hero"]  # type: ignore[assignment]
    friend: Entity = facts["friend"]  # type: ignore[assignment]
    caretaker: Entity = facts["caretaker"]  # type: ignore[assignment]
    scenario: dict[str, str] = facts["scenario"]  # type: ignore[assignment]
    return [
        f"Write a funny, child-friendly clubhouse story about {hero.label} and {friend.label} enjoying {scenario['pastime']}.",
        f"Include {caretaker.label}'s gadget, an early warning clue, a comic mishap, and a kind way to fix it.",
        "Let two characters speak to each other, and make their conversation change what they do.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    hero: Entity = facts["hero"]  # type: ignore[assignment]
    friend: Entity = facts["friend"]  # type: ignore[assignment]
    caretaker: Entity = facts["caretaker"]  # type: ignore[assignment]
    scenario: dict[str, str] = facts["scenario"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What pastime were {hero.label} and {friend.label} enjoying?",
            answer=f"They were enjoying {scenario['pastime']} at the Tumbleberry Clubhouse, using {scenario['gadget']}.",
        ),
        QAItem(
            question="What early clue helped the friends understand the gadget?",
            answer=f"{scenario['clue']} They remembered that warning when they decided how to fix the gadget.",
        ),
        QAItem(
            question="What went wrong, and how did the friends respond?",
            answer=f"{scenario['mishap']} They responded kindly, then {scenario['method'][0].lower() + scenario['method'][1:]}",
        ),
        QAItem(
            question=f"How did the friends help {caretaker.label}?",
            answer=f"They treated the mishap kindly instead of blaming anyone, and {scenario['method'][0].lower() + scenario['method'][1:]}",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"{scenario['result']} {scenario['image'].capitalize()}, showing that the friends had put things right.",
        ),
    ]


def world_knowledge_qa(_: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a gadget?",
            answer="A gadget is a small tool or device made to do a particular job.",
        ),
        QAItem(
            question="What is a pastime?",
            answer="A pastime is an activity someone enjoys doing in their free time.",
        ),
        QAItem(
            question="Why can a small warning be useful?",
            answer="A small warning can help people notice a problem early, pause, and choose a safer way to continue.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means caring about how others feel and offering help without making them feel small.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts ==", *sample.prompts, "", "== story qa =="]
    for item in sample.story_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for entity in world.entities.values():
        details = [f"type={entity.type}"]
        meters = {key: round(value, 2) for key, value in entity.meters.items() if value}
        memes = {key: round(value, 2) for key, value in entity.memes.items() if value}
        if meters:
            details.append(f"meters={meters}")
        if memes:
            details.append(f"memes={memes}")
        lines.append(f"{entity.id}: " + ", ".join(details))
    lines.extend(world.trace_log)
    return "\n".join(lines)


ASP_RULES = r"""
good_end :- selected(S), paired(S), clue_seen(S), kind_act(S), repair(S).
#show good_end/0.
"""


def asp_facts(params: Optional[StoryParams] = None) -> str:
    import asp

    facts = []
    for scenario_id, scenario in SCENARIOS.items():
        facts.append(asp.fact("registered", scenario_id))
        facts.append(asp.fact("paired", scenario_id))
    if params is not None:
        reasonable(params)
        facts.extend(
            (
                asp.fact("selected", params.scenario_id),
                asp.fact("clue_seen", params.scenario_id),
                asp.fact("kind_act", params.scenario_id),
                asp.fact("repair", params.scenario_id),
            )
        )
    return "\n".join(facts)


def asp_program(params: Optional[StoryParams] = None) -> str:
    return f"{asp_facts(params)}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp

    for params in CURATED:
        sample = generate(params)
        if not reasonable(params):
            print(f"MISMATCH: Python rejected {params.scenario_id}")
            return 1
        if sample.story.count('"') < 4:
            print(f"MISMATCH: missing spoken back-and-forth in {params.scenario_id}")
            return 1
        for key in ("clue", "kindness", "method", "result", "image"):
            if SCENARIOS[params.scenario_id][key] not in sample.story:
                print(f"MISMATCH: story did not exercise {key} in {params.scenario_id}")
                return 1
        model = asp.one_model(asp_program(params))
        atoms = {f"{symbol.name}/{len(symbol.arguments)}" for symbol in model}
        if atoms != {"good_end/0"}:
            print(f"MISMATCH: ASP gave {sorted(atoms)} for {params.scenario_id}")
            return 1

    try:
        reasonable(
            StoryParams(
                "curtain_crank",
                SCENARIOS["pocket_breeze"]["gadget"],
                SCENARIOS["pocket_breeze"]["pastime"],
                "Test",
                "rabbit",
                "Friend",
                "mouse",
                "Caretaker",
            )
        )
    except StoryError:
        pass
    else:
        print("MISMATCH: Python reasonableness gate accepted a mismatched gadget and pastime.")
        return 1

    print("OK: ASP/Python parity passed and every generated scenario was exercised.")
    return 0


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
        print()
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(CURATED[0]))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program(CURATED[0]))
        print("ASP model:", " ".join(str(atom) for atom in model))
        return
    if args.n < 1 and not args.all:
        raise StoryError("-n must be at least 1.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n:
            seed = base_seed + attempts
            rng = random.Random(seed)
            params = resolve_params(args, rng)
            params.seed = seed
            sample = generate(params)
            attempts += 1
            if sample.story in seen and attempts < max(args.n * 20, 20):
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
        header = f"### variant {index + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

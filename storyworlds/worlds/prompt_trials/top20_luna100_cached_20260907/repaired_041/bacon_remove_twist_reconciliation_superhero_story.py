#!/usr/bin/env python3
"""
A standalone Storyweavers world: a gentle superhero rescue about a missing
bacon badge, a surprising twist, and reconciliation.
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
ROOT = HERE
while ROOT != os.path.dirname(ROOT):
    if os.path.exists(os.path.join(ROOT, "storyworlds", "results.py")):
        break
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


THEME = "a bright neighborhood superhero base"
SEED_WORDS = {"bacon", "remove"}


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: str = "base"

    def __post_init__(self) -> None:
        for key in ("safe", "lost", "crumbs", "distance"):
            self.meters.setdefault(key, 0.0)
        for key in ("worry", "courage", "trust", "guilt", "joy", "teamwork"):
            self.memes.setdefault(key, 0.0)


@dataclass
class StoryParams:
    hero: str = "Luna"
    partner: str = "Milo"
    rival: str = "Rex"
    case: int = 0
    voice: int = 0
    twist: int = 0
    ending: int = 0
    seed: Optional[int] = None


@dataclass(frozen=True)
class Case:
    mission: str
    trouble: str
    clue: str
    false_lead: str
    discovery: str
    cause: str
    repair: str
    proof: str
    lesson: str
    ending: str


CASES = [
    Case(
        "deliver a warm breakfast to the fire station",
        "the team's bacon badge vanished from the control panel",
        "a shiny grease mark beside the breakfast basket",
        "a trail of red capes leading toward the rooftop",
        "found the badge tucked inside the rescue drone's supply drawer",
        "had moved the badge while trying to remove bacon crumbs from the controls",
        "cleaned the panel, returned the badge, and labeled a safe snack tray",
        "the drone lifted without a single loose crumb near its buttons",
        "a rushed helpful act still needs a careful explanation",
        "The bacon badge gleamed above the panel as the little drone carried breakfast through the sunrise.",
    ),
    Case(
        "help neighbors cross a puddled street",
        "the red signal lamp stopped shining before the rescue began",
        "a tiny bacon-shaped sticker stuck to the lamp's battery cover",
        "a muddy boot print pointing toward the old tool shed",
        "removed the cover and found the lamp's switch wedged by a folded napkin",
        "had grabbed a napkin after breakfast and accidentally pushed it behind the switch",
        "freed the switch, dried the battery, and practiced the crossing signal together",
        "the lamp blinked red, yellow, and green while the team crossed safely",
        "honest words can repair trust faster than a perfect excuse",
        "The signal lamp blinked proudly while every neighbor reached the dry sidewalk.",
    ),
    Case(
        "prepare a rooftop garden for thirsty seedlings",
        "the superhero watering wand would not turn on",
        "a warm bacon crumb resting beside the wand's power button",
        "a loose silver ribbon fluttering near the rooftop door",
        "removed the wand's cap and found a crumb blocking the little contact",
        "had carried breakfast to the roof and brushed the crumb into the wand by mistake",
        "washed the wand, moved food away from tools, and watered every seedling",
        "each plant received the same gentle stream without a spark or sputter",
        "responsibility means fixing the cause, not only hiding the symptom",
        "By evening, the seedlings stood tall beneath the shining emblem of the team.",
    ),
    Case(
        "rescue a kite caught in the clock tower",
        "the hero's cape clasp disappeared before the climb",
        "a strip of red thread snagged on the picnic basket",
        "a shiny button glinting inside the hero locker",
        "found the clasp beneath a folded breakfast cloth",
        "had used the cloth to remove bacon grease and swept the clasp along with it",
        "washed the cloth, fastened the clasp, and tied a safer rescue line",
        "the line held firm while the kite floated free",
        "a mistake becomes smaller when people tell the truth and make a safer plan",
        "The rescued kite danced above the clock while the red cape flashed below it.",
    ),
    Case(
        "deliver books to the little library",
        "the team's promise card disappeared from the delivery bag",
        "a square clean space among bacon crumbs on the packing table",
        "an empty box beside the costume rack",
        "found the card pressed inside the library's first book",
        "had used the card to remove a sticky crumb from the book and forgotten to replace it",
        "cleaned the book, returned the card, and made a proper crumb scraper",
        "the books arrived clean, dry, and clearly labeled",
        "good intentions need good tools",
        "The promise card rested on the library desk, ready for the next brave delivery.",
    ),
    Case(
        "protect the town's moonlight festival",
        "the festival beacon dimmed just as the music began",
        "a bacon-colored smear on the beacon's removable lens",
        "a shadow moving behind the stage curtain",
        "removed the lens and found grease covering its bright center",
        "had touched the lens after trying to remove bacon from a glove",
        "cleaned the lens, washed the glove, and checked every light together",
        "the beacon shone clearly across the whole square",
        "blame makes shadows, but clear evidence brings light",
        "The moonlight festival sparkled, and the beacon painted a silver path home.",
    ),
]


@dataclass
class World:
    hero: Entity
    partner: Entity
    rival: Entity
    bacon: Entity
    badge: Entity
    beacon: Entity
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_world(params: StoryParams) -> World:
    hero = Entity(params.hero, "character", "hero", "the young superhero")
    partner = Entity(params.partner, "character", "partner", "the careful partner")
    rival = Entity(params.rival, "character", "rival", "the worried teammate")
    bacon = Entity("bacon", "food", "bacon", "the breakfast bacon", location="kitchen")
    badge = Entity("badge", "tool", "badge", "the bacon badge")
    beacon = Entity("beacon", "machine", "beacon", "the town beacon")
    return World(hero, partner, rival, bacon, badge, beacon)


def tell(params: StoryParams) -> World:
    world = build_world(params)
    h, p, r = world.hero, world.partner, world.rival
    case = CASES[params.case % len(CASES)]

    h.memes["courage"] += 1
    h.memes["worry"] += 1
    p.memes["trust"] += 1
    r.memes["guilt"] += 1
    world.badge.meters["lost"] = 1
    world.bacon.meters["crumbs"] = 2

    openings = [
        f"In {THEME}, {h.id} and {p.id} prepared to {case.mission}.",
        f"The morning alarm rang at {THEME}. {h.id}, {p.id}, and {r.id} hurried to {case.mission}.",
        f"{h.id} pulled on a bright cape while {p.id} checked the gear for a mission to {case.mission}.",
        f"At the superhero base, breakfast bacon sizzled while the team planned to {case.mission}.",
    ]
    world.say(openings[params.voice % len(openings)])
    world.say(f"Then {case.trouble}. Without it, the rescue plan could not begin.")
    world.say(f"{h.id} touched the empty space and promised, 'We will find it without blaming anyone.'")

    world.para()
    world.say(f"Near the controls, they noticed {case.clue}. They also saw {case.false_lead}.")
    thoughts = [
        f"{h.id} said, 'The grease mark is closer to the controls, so it may explain what happened.'",
        f"{h.id} whispered, 'A trail can distract us. We need the clue that touched the missing object.'",
        f"'{case.clue.capitalize()}' {h.id} said. 'That is something we can test.'",
        f"{h.id} took a breath. 'Heroes follow evidence before they choose a suspect.'",
    ]
    world.say(thoughts[params.twist % len(thoughts)])
    world.say(f"{p.id} replied, 'I will check the safe places, and you check the gear.'")
    world.say(f"{r.id} asked, 'May I help? I saw something, but I was afraid to speak.'")
    world.say(f"'Yes,' said {h.id}. 'Tell us exactly what you remember.'")

    world.para()
    world.say(f"The first search led nowhere. The bright trail was only a false lead.")
    world.say(f"Then {h.id} and {p.id} followed the stronger clue and {case.discovery}.")
    world.badge.meters["lost"] = 0
    world.badge.location = "found"
    world.say(f"This was the twist: the missing item had not been stolen at all.")
    admissions = [
        f"{r.id} lowered their eyes. 'I can explain. I {case.cause}.'",
        f"'{case.cause.capitalize()},' {r.id} admitted. 'I should have told you sooner.'",
        f"{r.id} took a breath. 'I was trying to help, but I {case.cause}. I am sorry.'",
        f"'The clue fits my mistake,' {r.id} said. 'I {case.cause}.'",
    ]
    world.say(admissions[params.voice % len(admissions)])
    world.say(f"{h.id} answered, 'Thank you for telling the truth. Now we can repair it together.'")

    world.para()
    h.memes["teamwork"] += 2
    p.memes["teamwork"] += 2
    r.memes["trust"] += 2
    r.memes["guilt"] = max(0, r.memes["guilt"] - 1)
    world.say(f"The teammates {case.repair}.")
    world.say(f"They tested the repair: {case.proof}.")
    reconciliation = [
        f"{h.id} and {r.id} shook hands. Their disagreement softened into reconciliation.",
        f"{r.id} helped carry the gear, and {h.id} thanked them. Trust began to grow again.",
        f"The team made room for an apology and a fresh start. Reconciliation felt like a warm light.",
        f"Nobody pretended the mistake had not happened. They forgave it, learned from it, and worked side by side.",
    ]
    world.say(reconciliation[params.ending % len(reconciliation)])
    world.say(f"The team wrote one lesson on the mission board: {case.lesson}")

    world.para()
    world.say(case.ending)

    world.facts.update(
        case=case,
        mission=case.mission,
        trouble=case.trouble,
        clue=case.clue,
        discovery=case.discovery,
        cause=case.cause,
        repair=case.repair,
        proof=case.proof,
        lesson=case.lesson,
        ending=case.ending,
    )
    return world


def story_qa(world: World) -> list[QAItem]:
    h, p, r = world.hero, world.partner, world.rival
    return [
        QAItem(
            "What problem interrupted the superhero mission?",
            f"The team could not begin because {world.facts['trouble']}.",
        ),
        QAItem(
            "What clue helped the heroes solve the mystery?",
            f"They followed {world.facts['clue']} instead of trusting the false lead.",
        ),
        QAItem(
            f"What did {r.id} admit?",
            f"{r.id} admitted that they {world.facts['cause']}.",
        ),
        QAItem(
            "What was the twist in the story?",
            "The missing item had not been stolen. It had been moved accidentally while someone was trying to help.",
        ),
        QAItem(
            "How did reconciliation change the team?",
            f"They accepted the apology and {world.facts['repair']}. Their teamwork became stronger.",
        ),
        QAItem(
            "How did the heroes know the repair worked?",
            f"They tested it and saw that {world.facts['proof']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What does it mean to remove something?",
            "To remove something means to take it away from where it is.",
        ),
        QAItem(
            "What is bacon?",
            "Bacon is a food usually made from pork and cooked until it is crisp or tender.",
        ),
        QAItem(
            "What is a superhero?",
            "A superhero is a story character who uses courage, helpful skills, or special powers to protect others.",
        ),
        QAItem(
            "What is a twist in a story?",
            "A twist is a surprising change in what the reader thought was happening.",
        ),
        QAItem(
            "What is reconciliation?",
            "Reconciliation is making peace and rebuilding trust after people have disagreed or someone has made a mistake.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a child-friendly superhero story in which {world.facts['trouble']}.",
        f"Include bacon, the verb remove, a surprising twist, and reconciliation between teammates.",
        f"Show how the clue {world.facts['clue']} changes what the heroes decide to do.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in [
        world.hero,
        world.partner,
        world.rival,
        world.bacon,
        world.badge,
        world.beacon,
    ]:
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id:8} ({entity.kind:9}) location={entity.location} "
            f"meters={meters} memes={memes}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
setting(superhero_base).
contains(superhero_base, bacon).
requires(superhero_base, remove).
feature(superhero_base, twist).
feature(superhero_base, reconciliation).
valid_story(S) :-
    setting(S),
    contains(S, bacon),
    requires(S, remove),
    feature(S, twist),
    feature(S, reconciliation).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join(
        [
            asp.fact("setting", "superhero_base"),
            asp.fact("contains", "superhero_base", "bacon"),
            asp.fact("requires", "superhero_base", "remove"),
            asp.fact("feature", "superhero_base", "twist"),
            asp.fact("feature", "superhero_base", "reconciliation"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    valid = any(atom.name == "valid_story" for atom in model)
    if not valid:
        print("MISMATCH: ASP rejected the superhero story domain.")
        return 1
    for params in CURATED:
        sample = generate(params)
        if "bacon" not in sample.story.lower() or "remove" not in sample.story.lower():
            print("MISMATCH: generated story lost a required seed word.")
            return 1
        if not sample.story_qa:
            print("MISMATCH: generated story has no story questions.")
            return 1
    print("OK: ASP/Python parity and generated-story checks passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a superhero story about bacon, a twist, and reconciliation."
    )
    parser.add_argument("--hero", default=None)
    parser.add_argument("--partner", default=None)
    parser.add_argument("--rival", default=None)
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


def resolve_params(
    args: argparse.Namespace,
    rng: random.Random,
    sample_seed: int,
    base_seed: int,
) -> StoryParams:
    hero = args.hero or rng.choice(["Luna", "Nova", "Sol", "Comet", "Ember"])
    partner = args.partner or rng.choice(["Milo", "Pip", "Ari", "Kite", "Juno"])
    rival = args.rival or rng.choice(["Rex", "Bolt", "Zig", "Storm", "Dash"])
    if len({hero, partner, rival}) != 3:
        raise StoryError("The hero, partner, and rival must have different names.")
    offset = sample_seed - base_seed
    return StoryParams(
        hero=hero,
        partner=partner,
        rival=rival,
        case=offset % len(CASES),
        voice=(offset // len(CASES)) % 4,
        twist=(offset // (len(CASES) * 4)) % 4,
        ending=(offset // (len(CASES) * 4 * 4)) % 4,
        seed=sample_seed,
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


CURATED = [
    StoryParams(hero="Luna", partner="Milo", rival="Rex", case=0),
    StoryParams(hero="Nova", partner="Pip", rival="Bolt", case=1),
    StoryParams(hero="Sol", partner="Ari", rival="Zig", case=2),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/1."))
        print("ASP model:", [str(atom) for atom in model])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        for index in range(max(0, args.n)):
            sample_seed = base_seed + index
            params = resolve_params(
                args,
                random.Random(sample_seed),
                sample_seed,
                base_seed,
            )
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
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


THEME = "the Moonlit Museum"
SEED_WORDS = {"see"}


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    carried_by: Optional[str] = None

    def __post_init__(self) -> None:
        for key in ("visible", "dust", "distance", "cold"):
            self.meters.setdefault(key, 0.0)
        for key in ("worry", "curiosity", "trust", "pride", "relief"):
            self.memes.setdefault(key, 0.0)


@dataclass
class StoryParams:
    name: str = "Luna"
    partner: str = "Pip"
    keeper: str = "Mara"
    case: int = 0
    dialogue_style: int = 0
    ending_style: int = 0
    seed: Optional[int] = None


@dataclass(frozen=True)
class Case:
    exhibit: str
    missing: str
    clue: str
    false_lead: str
    discovery: str
    cause: str
    repair: str
    proof: str
    ending: str
    lesson: str


CASES = [
    Case(
        exhibit="a glass case of moon rocks",
        missing="the tiny silver telescope badge",
        clue="a clean crescent in the dust beside the display latch",
        false_lead="a trail of blue paint leading toward the planet room",
        discovery="saw the badge shining beneath the folded velvet cloth inside the case",
        cause="had lifted the cloth to polish the glass and set the badge beneath it without noticing",
        repair="returned the badge to its label and cleaned the latch before closing the case",
        proof="the badge sat in its marked circle and the latch clicked shut",
        ending="Under the museum's blue lamps, the silver badge gleamed beside the moon rocks.",
        lesson="The clearest clue is the one that explains where an object could really have gone.",
    ),
    Case(
        exhibit="a room of painted sea maps",
        missing="the brass compass",
        clue="a round dry patch on the dusty floor beside the map table",
        false_lead="wet footprints that wandered toward the aquarium hall",
        discovery="saw the compass tucked behind the rolled-up map of the northern sea",
        cause="had moved the compass to stop a map from rolling and forgotten to put it back",
        repair="flattened the map, returned the compass, and marked its proper resting place",
        proof="the map stayed flat and the compass needle pointed north",
        ending="The brass compass rested on the map, pointing toward a painted sunrise.",
        lesson="A clue becomes useful when it connects an object with the action that moved it.",
    ),
    Case(
        exhibit="a cabinet of singing shells",
        missing="the pearl listening token",
        clue="a faint ringing sound beneath the cabinet's lowest drawer",
        false_lead="a loose shell near the museum door",
        discovery="saw the token caught in the drawer's wooden runner",
        cause="had opened the drawer too quickly while carrying a tray and knocked the token down",
        repair="emptied the drawer carefully, fixed the runner, and placed the token in its velvet cup",
        proof="the drawer opened smoothly and every shell still had its own token",
        ending="The shells sang softly while the pearl token shone in its velvet cup.",
        lesson="Listening closely can reveal a hiding place that eyes alone might miss.",
    ),
    Case(
        exhibit="a model railway through snowy mountains",
        missing="the red signal flag",
        clue="a red thread caught on the tunnel entrance",
        false_lead="a toy train stopped beside the station",
        discovery="saw the flag wedged inside the mountain tunnel",
        cause="had reached into the tunnel to rescue a wagon and pulled the flag in with it",
        repair="removed the flag with tongs, repaired the thread, and restarted the little train",
        proof="the train passed the tunnel and the red signal waved above it",
        ending="The red flag waved as the tiny train curled through the snowy mountains.",
        lesson="A small snag can explain a big mystery when you follow it back to its source.",
    ),
    Case(
        exhibit="a hall of shadow puppets",
        missing="the paper owl",
        clue="an owl-shaped shadow still visible behind the curtain",
        false_lead="a feather near the open window",
        discovery="saw the paper owl pressed between the curtain and the wall",
        cause="had pulled the curtain to let in moonlight and trapped the puppet behind it",
        repair="freed the puppet, tied the curtain cord, and placed the owl back on its hook",
        proof="the owl made a clear shadow when the lamp was lit",
        ending="The paper owl spread its wings across the wall in a bright, perfect shadow.",
        lesson="Seeing what remains can be as important as seeing what has vanished.",
    ),
]


@dataclass
class World:
    hero: Entity
    partner: Entity
    keeper: Entity
    object_: Entity
    exhibit: Entity
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


def build_world(params: StoryParams) -> World:
    hero = Entity(params.name, "character", "child", params.name, "moon gallery")
    partner = Entity(params.partner, "character", "child", params.partner, "moon gallery")
    keeper = Entity(params.keeper, "character", "adult", params.keeper, "museum hall")
    object_ = Entity("missing_object", "thing", "artifact", "missing artifact", "unknown")
    exhibit = Entity("exhibit", "place", "display", "museum exhibit", "moon gallery")
    return World(hero, partner, keeper, object_, exhibit)


def tell(params: StoryParams) -> World:
    world = build_world(params)
    h, p, k, obj = world.hero, world.partner, world.keeper, world.object_
    case = CASES[params.case % len(CASES)]

    h.memes["curiosity"] = 1
    h.memes["worry"] = 1
    p.memes["trust"] = 1
    k.memes["pride"] = 1
    obj.meters["visible"] = 1

    openings = [
        f"At closing time, {h.id} and {p.id} were helping {k.id} check {case.exhibit} in {THEME}.",
        f"The museum was quiet except for soft footsteps. {h.id} and {p.id} followed {k.id} past {case.exhibit}.",
        f"Moonlight shone through the high windows as {h.id}, {p.id}, and {k.id} prepared {case.exhibit} for the night.",
        f"{h.id} loved visiting {THEME}, but that evening the museum held a puzzle: {case.exhibit} needed one final check.",
    ]
    world.say(openings[params.dialogue_style % len(openings)])
    world.say(f"Then {case.missing} was gone. The empty place made {k.id} clutch the checklist.")

    world.para()
    world.say(f"Near the display, they could see {case.clue}. At the same time, {case.false_lead}.")
    world.say(f"{h.id} leaned closer. 'I can see two possible paths,' {h.id} said. 'Which one reaches the missing object?'")
    world.say(f"{p.id} pointed toward the hallway. 'We should check the easy trail first.'")
    world.say(f"'And then compare it with the clue beside the case,' {h.id} replied. 'We should not guess about anyone.'")
    world.say(f"{k.id} nodded. 'Look carefully, then tell each other exactly what you see.'")

    h.memes["curiosity"] += 1
    p.memes["trust"] += 1
    world.say(f"They split the search. {p.id} checked the false lead while {h.id} studied the display without touching it.")

    world.para()
    world.say(
        "The first trail ended at a harmless paint cart. It explained a color, but not the empty place. "
        "When the children compared notes, the clue beside the exhibit fit the missing object much better."
    )
    world.say(f"{p.id} called, 'I see nothing here but paintbrushes!'")
    world.say(f"{h.id} answered, 'Then come back. I see where the display was disturbed.'")
    world.say(f"Together, they {case.discovery}.")
    obj.meters["visible"] = 1
    obj.location = case.exhibit

    world.say(
        f"{k.id} took a slow breath. 'Now I remember,' {k.id} said. 'I {case.cause}. "
        "I was trying to help, but I should have told everyone.'"
    )
    world.say(f"{h.id} replied, 'Thank you for saying what happened. Now we can fix the real problem.'")
    world.say(f"{p.id} added, 'Seeing the cause is better than blaming a person.'")

    world.para()
    h.memes["relief"] += 1
    p.memes["pride"] += 1
    k.memes["relief"] += 1
    world.say(f"The three helpers {case.repair}.")
    world.say(f"They tested the result: {case.proof}.")
    world.say(f"On the checklist, {h.id} wrote the lesson: {case.lesson}")

    world.para()
    endings = [
        case.ending,
        f"When the doors closed, {case.ending}",
        f"The museum lights dimmed, but {case.ending}",
        f"Before leaving, everyone looked once more. {case.ending}",
    ]
    world.say(endings[params.ending_style % len(endings)])

    world.facts.update(
        exhibit=case.exhibit,
        missing=case.missing,
        clue=case.clue,
        false_lead=case.false_lead,
        discovery=case.discovery,
        cause=case.cause,
        repair=case.repair,
        proof=case.proof,
        ending=case.ending,
        lesson=case.lesson,
        resolved=True,
    )
    return world


def story_qa(world: World) -> list[QAItem]:
    h, p, k = world.hero, world.partner, world.keeper
    return [
        QAItem(
            f"What went missing in the museum?",
            f"{world.facts['missing']} went missing from {world.facts['exhibit']}.",
        ),
        QAItem(
            f"What clue did {h.id} and {p.id} follow?",
            f"They followed {world.facts['clue']}, because it connected the display with the missing object.",
        ),
        QAItem(
            f"How was the missing object found?",
            f"They {world.facts['discovery']}.",
        ),
        QAItem(
            f"What did {k.id} explain?",
            f"{k.id} explained that {k.id} {world.facts['cause']}.",
        ),
        QAItem(
            "How did the team prove the mystery was solved?",
            f"They {world.facts['repair']}. Then they checked that {world.facts['proof']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a museum exhibit?",
            "A museum exhibit is an object or collection arranged for visitors to look at and learn about.",
        ),
        QAItem(
            "What does it mean to see something?",
            "To see something means to notice it with your eyes and understand what is in front of you.",
        ),
        QAItem(
            "Why should detectives compare clues?",
            "Detectives compare clues so they can choose an explanation that fits the evidence instead of guessing.",
        ),
        QAItem(
            "What is dialogue?",
            "Dialogue is a spoken exchange in which characters talk to one another.",
        ),
        QAItem(
            "Why is admitting an accident helpful?",
            "Admitting an accident helps people understand the cause and repair the problem honestly.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a child-friendly whodunit in {THEME} where {world.facts['missing']} goes missing.",
        f"Use dialogue between the children and the keeper, and include the clue: {world.facts['clue']}.",
        "Make the word 'see' important by showing how careful observation solves the mystery.",
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
    for entity in (world.hero, world.partner, world.keeper, world.object_, world.exhibit):
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id:16} location={entity.location!r} "
            f"meters={meters} memes={memes}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
setting(moonlit_museum).
requires(moonlit_museum, see).
requires(moonlit_museum, dialogue).
valid_story(S) :- setting(S), requires(S, see), requires(S, dialogue).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    return "\n".join(
        [
            asp.fact("setting", "moonlit_museum"),
            asp.fact("requires", "moonlit_museum", "see"),
            asp.fact("requires", "moonlit_museum", "dialogue"),
        ]
    )


def asp_program(show: str = "#show valid_story/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    models = asp.one_model(asp_program())
    valid = any(atom.name == "valid_story" for atom in models)
    if not valid:
        print("MISMATCH: ASP rules rejected the story domain.")
        return 1
    for params in CURATED:
        sample = generate(params)
        if "see" not in sample.story.lower():
            print("MISMATCH: generated story does not contain the required seed word.")
            return 1
        if "'" not in sample.story:
            print("MISMATCH: generated story lacks dialogue.")
            return 1
    print("OK: ASP and Python recognize the museum whodunit domain.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A dialogue-rich museum whodunit about learning to see clues."
    )
    parser.add_argument("--name", default=None)
    parser.add_argument("--partner", default=None)
    parser.add_argument("--keeper", default=None)
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
    name = args.name or rng.choice(["Luna", "Milo", "Nia", "Suri", "Theo"])
    partner = args.partner or rng.choice(["Pip", "Ari", "Bo", "Tess", "Juno"])
    keeper = args.keeper or rng.choice(["Mara", "Oren", "Vale", "Iris"])
    if name == partner:
        raise StoryError("The detective and partner must have different names.")
    if keeper in {name, partner}:
        raise StoryError("The museum keeper must have a different name.")
    offset = sample_seed - base_seed
    return StoryParams(
        name=name,
        partner=partner,
        keeper=keeper,
        case=offset % len(CASES),
        dialogue_style=(offset // len(CASES)) % 4,
        ending_style=(offset // (len(CASES) * 4)) % 4,
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
    StoryParams(name="Luna", partner="Pip", keeper="Mara", case=0),
    StoryParams(name="Milo", partner="Ari", keeper="Oren", case=1),
    StoryParams(name="Nia", partner="Tess", keeper="Vale", case=2),
    StoryParams(name="Suri", partner="Bo", keeper="Iris", case=3),
    StoryParams(name="Theo", partner="Juno", keeper="Mara", case=4),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp

        model = asp.one_model(asp_program())
        print("ASP model:", [str(atom) for atom in model])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        index = 0
        limit = max(50, args.n * 50)
        while len(samples) < args.n and index < limit:
            sample_seed = base_seed + index
            params = resolve_params(
                args,
                random.Random(sample_seed),
                sample_seed,
                base_seed,
            )
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            index += 1

    if not samples:
        raise StoryError("No stories could be generated.")

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

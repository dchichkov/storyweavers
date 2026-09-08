#!/usr/bin/env python3
"""
A standalone Storyweavers world: a child-friendly superhero quest.

A brave hero must terminate a runaway danger, scour a bright mountain trail,
and help a grizzly bear before the town's festival can begin. Inner thoughts,
kind questions, and teamwork turn the quest into a happy ending.
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


THEME = "superhero quest"
SEED_WORDS = {"terminate", "grizzly", "scour"}


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: str = ""
    carrying: Optional[str] = None

    def __post_init__(self) -> None:
        for key in ("danger", "distance", "noise", "tangle", "warmth"):
            self.meters.setdefault(key, 0.0)
        for key in ("worry", "courage", "curiosity", "trust", "joy", "pride"):
            self.memes.setdefault(key, 0.0)


@dataclass
class StoryParams:
    hero: str = "Luna"
    helper: str = "Pip"
    grizzly: str = "Bruno"
    quest: int = 0
    voice: int = 0
    ending: int = 0
    seed: Optional[int] = None


@dataclass(frozen=True)
class QuestCase:
    landmark: str
    danger: str
    clue: str
    false_lead: str
    thought: str
    tool: str
    discovery: str
    cause: str
    repair: str
    proof: str
    lesson: str
    ending_image: str


QUESTS = [
    QuestCase(
        landmark="the Echoing Ridge",
        danger="a runaway thunder cart was rolling toward the town gate",
        clue="small blue sparks leading uphill and a deep pawprint beside the trail",
        false_lead="a broken sign pointed toward the old mine",
        thought="The sign is broken, but the sparks and pawprint show where the cart actually went.",
        tool="a silver listening shell",
        discovery="found the thunder cart caught in a net of thorny vines",
        cause="had pushed the cart away from a falling rock, then become tangled while trying to stop it",
        repair="cut the vines with a safety blade, secured the cart, and guided Bruno into the shade",
        proof="the cart's wheels stayed still when the ridge wind blew",
        lesson="A real hero investigates before blaming the nearest creature.",
        ending_image="the town's flags waved beneath a quiet, shining ridge",
    ),
    QuestCase(
        landmark="the Moonlit Ravine",
        danger="a glowing beacon was flashing wildly and calling every animal toward a cliff",
        clue="warm footprints, a cracked beacon lens, and a strand of golden fur",
        false_lead="a trail of glitter disappeared into a cave",
        thought="Glitter can sparkle anywhere, but the warm footprints end beside the cracked lens.",
        tool="a moon compass",
        discovery="found Bruno holding the beacon steady with one huge paw",
        cause="had grabbed the beacon when it slipped, but the broken lens made its light flash",
        repair="terminated the flashing signal, replaced the lens, and led Bruno along a safe path",
        proof="the beacon shone in a steady beam toward the festival field",
        lesson="Sometimes a frightening sight is a helper trapped in a difficult moment.",
        ending_image="a calm silver beam painted a road home across the ravine",
    ),
    QuestCase(
        landmark="the Cloudberry Pass",
        danger="a storm machine was humming beside a bridge that had begun to shake",
        clue="fresh claw marks on the machine's handle and berry leaves bent toward the bridge",
        false_lead="a red cape snagged on a bush made it look as if a rival hero had fled",
        thought="The cape tells me someone passed here, but the claw marks explain the shaking handle.",
        tool="a bright rescue rope",
        discovery="found Bruno bracing the storm machine so it would not roll into the bridge",
        cause="had chased a sweet smell, bumped the machine, and held it back when it started sliding",
        repair="turned off the machine, anchored the bridge, and shared cloudberries with Bruno",
        proof="the bridge stopped shaking and the clouds drifted harmlessly away",
        lesson="Good rescuers notice both the trouble and the courage already inside it.",
        ending_image="cloudberries gleamed like tiny stars beside the repaired bridge",
    ),
    QuestCase(
        landmark="the Sunstone Garden",
        danger="a giant magnet had pulled the town's metal festival decorations into a spinning ring",
        clue="bent ribbons circling one stone and a broad pawprint in the soft soil",
        false_lead="a shiny helmet rested near the fountain",
        thought="The helmet is bright, but the ribbons point to the stone at the center of the spin.",
        tool="a gentle gravity glove",
        discovery="found Bruno guarding the stone while the decorations whirled around him",
        cause="had leaned on the magnet while reaching for a lost honey jar",
        repair="lowered the magnet's power, scoured the garden for loose pieces, and returned every decoration",
        proof="the flags hung straight and the fountain was free of metal stars",
        lesson="Cleaning up after a mistake is part of making things right.",
        ending_image="golden sunstones lit the garden while the festival bells rang",
    ),
    QuestCase(
        landmark="the Rainbow Tunnel",
        danger="a rescue signal had become stuck on repeat beneath the mountain",
        clue="a blinking red button, loose copper wire, and grizzly fur near the control box",
        false_lead="a distant whistle sounded like a secret villain's message",
        thought="The whistle distracts us; the loose wire is close enough to explain the repeating signal.",
        tool="a pocket repair wand",
        discovery="found Bruno beside the control box, covering his ears",
        cause="had pressed the button to call for help after a rockslide, but the wire jammed",
        repair="terminated the repeating signal, cleared the safe tunnel entrance, and gave Bruno ear covers",
        proof="one clear signal blinked, then stopped exactly as planned",
        lesson="Asking what someone needed can turn a mystery into a rescue.",
        ending_image="rainbow light filled the tunnel as Bruno walked out with new friends",
    ),
    QuestCase(
        landmark="the Starfall Meadow",
        danger="a comet lantern was sinking into a pond and pulling the festival bridge after it",
        clue="a wet silver cord, flattened reeds, and a line of pawprints around the pond",
        false_lead="a floating hat bobbed near the far bank",
        thought="The hat is only floating; the cord and flattened reeds show where the lantern dragged.",
        tool="a starlight lasso",
        discovery="found Bruno holding the lantern's cord while standing in the shallow water",
        cause="had caught the lantern before it sank, but the cord wrapped around his leg",
        repair="freed the cord, hauled up the lantern, and scoured the bank for every loose knot",
        proof="the bridge rose level and the lantern glowed above dry ground",
        lesson="A careful rescue protects the helper as well as the thing in danger.",
        ending_image="the rescued lantern twinkled over a meadow full of dancing lights",
    ),
]


@dataclass
class World:
    hero: Entity
    helper: Entity
    grizzly: Entity
    signal: Entity
    landmark: Entity
    story_parts: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.story_parts[-1].append(text)

    def paragraph(self) -> None:
        if self.story_parts[-1]:
            self.story_parts.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.story_parts if part)


def make_entity(
    eid: str,
    kind: str,
    type_: str,
    label: str,
    *,
    location: str = "",
) -> Entity:
    return Entity(id=eid, kind=kind, type=type_, label=label, location=location)


def build_world(params: StoryParams) -> World:
    hero = make_entity(params.hero, "character", "hero", "the young superhero")
    helper = make_entity(params.helper, "character", "helper", "the clever helper")
    grizzly = make_entity(params.grizzly, "animal", "grizzly", "the grizzly bear")
    signal = make_entity("signal", "device", "beacon", "the rescue signal")
    landmark = make_entity("landmark", "place", "mountain", "the mountain landmark")
    return World(hero, helper, grizzly, signal, landmark)


def tell(params: StoryParams) -> World:
    world = build_world(params)
    h, p, b = world.hero, world.helper, world.grizzly
    quest = QUESTS[params.quest % len(QUESTS)]

    h.memes["courage"] = 1
    h.memes["worry"] = 1
    p.memes["curiosity"] = 1
    b.memes["worry"] = 2
    world.signal.meters["danger"] = 2
    world.signal.location = quest.landmark
    world.landmark.location = quest.landmark
    world.facts["quest"] = quest

    openings = [
        f"Luna wore a red cape over her boots and trained as a superhero at {quest.landmark}.",
        f"At sunrise, {h.id} and {p.id} began a superhero quest toward {quest.landmark}.",
        f"The town festival was almost ready when {h.id}, {p.id}, and {b.id} heard trouble from {quest.landmark}.",
        f"High above the town, {h.id} checked the rescue tools while {p.id} studied a map of {quest.landmark}.",
    ]
    world.say(openings[params.voice % len(openings)])
    world.say(f"Then {quest.danger}. The danger meter on the rescue signal rose, and the festival could not safely begin.")
    world.say(f"{h.id} tightened her cape. She knew the team's first job was to terminate the danger, not to panic.")

    world.paragraph()
    world.say(f"At the trailhead they saw {quest.clue}. Nearby, {quest.false_lead}.")
    thoughts = [
        quest.thought,
        f"{quest.thought} I will test the clue before I choose a path.",
        f"My worry is loud, but evidence can be quiet. {quest.thought}",
        f"A superhero protects everyone, even when the answer is not obvious. {quest.thought}",
    ]
    h.memes["curiosity"] += 1
    world.say(f"Inside {h.id}'s mind, an inner monologue whispered, '{thoughts[params.voice % len(thoughts)]}'")
    dialogues = [
        f"{p.id} asked, 'Should we follow the sparks or the broken sign?' {h.id} answered, 'The sparks. They connect to the danger.'",
        f"'I hear something big,' said {p.id}. 'Then we will speak kindly and listen carefully,' said {h.id}.",
        f"{b.id} rumbled, 'Please help.' {h.id} replied, 'We will. Tell us what happened before we decide what to do.'",
        f"'A cape does not make every guess correct,' {h.id} said. {p.id} smiled. 'Then our clues will be our superpower.'",
    ]
    world.say(dialogues[params.voice % len(dialogues)])
    world.say(f"Together, they chose {quest.tool} and climbed toward the strongest clue.")

    world.paragraph()
    world.say(f"The false lead ended at a quiet patch of stone, but the true trail continued. The team paused to scour the path for safe footholds and signs of the missing cause.")
    world.say(f"At the far side of {quest.landmark}, {h.id} and {p.id} {quest.discovery}.")
    b.memes["trust"] += 1
    h.memes["courage"] += 1
    world.signal.meters["danger"] = 1
    world.say(f"{b.id} lowered his head. 'I did not want anyone hurt,' he said. 'I {quest.cause}.'")
    world.say(f"{h.id} answered, 'Thank you for telling us. Now we can solve the real problem.' {p.id} added, 'We will work with you, not against you.'")
    world.say(f"The inner monologue in {h.id}'s mind changed: fear was still present, but courage now had a plan.")
    world.say(f"The three companions {quest.repair}.")
    world.signal.meters["danger"] = 0
    world.signal.meters["tangle"] = 0

    world.paragraph()
    world.say(f"They tested the repair: {quest.proof}. {b.id}'s worry softened into trust.")
    b.memes["trust"] += 2
    h.memes["joy"] += 2
    p.memes["joy"] += 2
    world.say(f"{h.id} told {b.id}, 'You helped save the day. A mistake does not erase your good choice.'")
    world.say(f"{b.id} grinned. 'Then may I join the festival?' 'Of course,' said {p.id}.")
    world.say(f"The team remembered their lesson: {quest.lesson}")
    world.say(f"That evening brought a happy ending: {quest.ending_image}.")
    world.say(f"{h.id} placed the rescue tool beside the festival map, ready for the next kind adventure.")

    world.facts.update(
        hero=h,
        helper=p,
        grizzly=b,
        signal=world.signal,
        landmark=world.landmark,
        danger=quest.danger,
        clue=quest.clue,
        false_lead=quest.false_lead,
        discovery=quest.discovery,
        cause=quest.cause,
        repair=quest.repair,
        proof=quest.proof,
        lesson=quest.lesson,
        ending_image=quest.ending_image,
        resolved=True,
    )
    return world


def story_qa(world: World) -> list[QAItem]:
    h = world.facts["hero"]
    p = world.facts["helper"]
    b = world.facts["grizzly"]
    return [
        QAItem(
            question="What danger interrupted the superhero quest?",
            answer=f"The quest was interrupted because {world.facts['danger']}. The team had to terminate that danger before the festival could begin.",
        ),
        QAItem(
            question=f"How did {h.id} decide which clue to follow?",
            answer=f"{h.id} used the clue about {world.facts['clue']} instead of the false lead. The physical signs connected more clearly to the danger.",
        ),
        QAItem(
            question=f"What did {b.id} explain after the team found him?",
            answer=f"{b.id} explained that he {world.facts['cause']}. He was trying to help, but his action created a new problem.",
        ),
        QAItem(
            question="How did the heroes solve the problem?",
            answer=f"They {world.facts['repair']}. Then they checked the result and found that {world.facts['proof']}.",
        ),
        QAItem(
            question="What made the ending happy?",
            answer=f"The danger was gone, the grizzly was welcomed, and {world.facts['ending_image']}. The quest ended with safety, friendship, and joy.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does terminate mean?",
            answer="Terminate means to bring something to an end or stop it safely.",
        ),
        QAItem(
            question="What is a grizzly?",
            answer="A grizzly is a large brown bear with strong claws, a powerful body, and a shoulder hump.",
        ),
        QAItem(
            question="What does scour mean?",
            answer="To scour means to search an area carefully, often while looking for something important.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet stream of thoughts a character has inside their mind.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is an adventure in which someone works toward an important goal and overcomes challenges.",
        ),
        QAItem(
            question="What makes a happy ending?",
            answer="A happy ending shows that the main danger has been solved and that the characters are safe, hopeful, or together.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a child-friendly superhero story in which {world.facts['hero'].id} must terminate a danger at {world.facts['landmark'].location}.",
        f"Create a quest where a grizzly needs help, the hero uses an inner monologue, and the team follows this clue: {world.facts['clue']}.",
        "Tell a story using the words terminate, grizzly, and scour, ending with a concrete happy image and kind dialogue.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in (world.hero, world.helper, world.grizzly, world.signal, world.landmark):
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id:10} ({entity.kind:9}) "
            f"location={entity.location or '-'} meters={meters} memes={memes}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
setting(superhero_quest).
feature(superhero_quest, inner_monologue).
feature(superhero_quest, quest).
feature(superhero_quest, happy_ending).
word(superhero_quest, terminate).
word(superhero_quest, grizzly).
word(superhero_quest, scour).

valid_world(S) :-
    setting(S),
    feature(S, inner_monologue),
    feature(S, quest),
    feature(S, happy_ending),
    word(S, terminate),
    word(S, grizzly),
    word(S, scour).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    facts = [
        asp.fact("setting", "superhero_quest"),
        asp.fact("feature", "superhero_quest", "inner_monologue"),
        asp.fact("feature", "superhero_quest", "quest"),
        asp.fact("feature", "superhero_quest", "happy_ending"),
        asp.fact("word", "superhero_quest", "terminate"),
        asp.fact("word", "superhero_quest", "grizzly"),
        asp.fact("word", "superhero_quest", "scour"),
    ]
    return "\n".join(facts)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    models = asp.one_model(asp_program("#show valid_world/1."))
    asp_ok = any(atom.name == "valid_world" for atom in models)
    if not asp_ok:
        print("MISMATCH: ASP rejected the superhero quest domain.")
        return 1

    for index, params in enumerate(
        [
            StoryParams(quest=0, seed=0),
            StoryParams(quest=2, seed=2),
            StoryParams(quest=5, seed=5),
        ],
        1,
    ):
        sample = generate(params)
        required = ("terminate", "grizzly", "scour")
        if not all(word in sample.story.lower() for word in required):
            print(f"MISMATCH: generated sample {index} omitted a required seed word.")
            return 1
        if not sample.world or not sample.world.facts.get("resolved"):
            print(f"MISMATCH: generated sample {index} did not resolve.")
            return 1

    print("OK: ASP/Python parity and generated superhero quests verified.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a superhero quest with a grizzly, an inner monologue, and a happy ending."
    )
    parser.add_argument("--hero", default=None)
    parser.add_argument("--helper", default=None)
    parser.add_argument("--grizzly", default=None)
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
    hero = args.hero or rng.choice(["Luna", "Nova", "Skye", "Mira", "Zara"])
    helper = args.helper or rng.choice(["Pip", "Tomo", "Bee", "Rafi", "Kit"])
    grizzly = args.grizzly or rng.choice(["Bruno", "Garnet", "Moss", "Cedar"])
    if hero == helper:
        raise StoryError("The hero and helper must have different names.")
    if grizzly in {hero, helper}:
        raise StoryError("The grizzly must have a different name from the human heroes.")
    offset = sample_seed - base_seed
    return StoryParams(
        hero=hero,
        helper=helper,
        grizzly=grizzly,
        quest=offset % len(QUESTS),
        voice=(offset // len(QUESTS)) % 4,
        ending=(offset // (len(QUESTS) * 4)) % 3,
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
    StoryParams(hero="Luna", helper="Pip", grizzly="Bruno", quest=0, seed=0),
    StoryParams(hero="Nova", helper="Bee", grizzly="Moss", quest=2, seed=2),
    StoryParams(hero="Skye", helper="Tomo", grizzly="Cedar", quest=4, seed=4),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_world/1."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import storyworlds.asp as asp

        model = asp.one_model(asp_program("#show valid_world/1."))
        print("ASP model:", [str(atom) for atom in model])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        if args.n < 1:
            raise StoryError("The number of stories must be at least 1.")
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

#!/usr/bin/env python3
"""
A standalone Storyweavers world: a gentle superhero story about sharing a
mysterious fluid, following humming sounds, and learning a lesson.
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


THEME = "the humming city fountain"
SEED_WORDS = {"dole", "fluid", "humming"}


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: str = ""

    def __post_init__(self) -> None:
        for key in ("fullness", "flow", "strength", "brightness", "noise"):
            self.meters.setdefault(key, 0.0)
        for key in ("worry", "courage", "kindness", "curiosity", "trust", "pride"):
            self.memes.setdefault(key, 0.0)


@dataclass
class StoryParams:
    hero: str = "Luna"
    helper: str = "Milo"
    trouble: int = 0
    telling: int = 0
    surprise: int = 0
    lesson: int = 0
    seed: Optional[int] = None


@dataclass(frozen=True)
class Trial:
    object_name: str
    fluid: str
    danger: str
    clue: str
    mistaken_idea: str
    discovery: str
    cause: str
    repair: str
    proof: str
    lesson: str
    ending: str


TRIALS = [
    Trial(
        object_name="the moon garden's silver watering bowl",
        fluid="a ribbon of blue rainwater",
        danger="the bowl had stopped pouring, leaving the moonflowers thirsty",
        clue="a soft humming under the stone rim and three bright drops beside the drain",
        mistaken_idea="the fountain's bell had swallowed the water",
        discovery="found a curled leaf wedged inside the narrow drain",
        cause="had tried to dole out water to every flower at once, and the leaf slipped into the drain",
        repair="cleared the leaf, turned the handle slowly, and doled the water from flower to flower",
        proof="each moonflower received a small drink and the fountain hummed evenly again",
        lesson="Sharing fairly means noticing what each friend needs instead of rushing to give everything at once.",
        ending="The moonflowers lifted their silver faces while the fountain sang one peaceful hum.",
    ),
    Trial(
        object_name="the rooftop cloud cups",
        fluid="a warm, pearly fluid from the cloud tank",
        danger="the cups were empty just before the city's thirsty pigeons arrived",
        clue="a humming pipe, a wobbling gauge, and one bead of fluid on the red valve",
        mistaken_idea="the pigeons had carried the whole supply away",
        discovery="spotted a loose washer trembling inside the red valve",
        cause="had opened the valve too quickly while trying to dole out a giant helping",
        repair="tightened the washer, tested a tiny stream, and doled out cups in a patient line",
        proof="the pipe stayed steady and every pigeon received a cup",
        lesson="A strong hero uses power gently, especially when many small friends are depending on it.",
        ending="The pigeons fluttered home as the cloud cups chimed beneath the humming stars.",
    ),
    Trial(
        object_name="the rainbow rescue cart",
        fluid="glowing orange rescue fluid",
        danger="the cart's wheels would not move during a parade rescue",
        clue="a humming motor, a sticky wheel, and an orange shine beneath the axle",
        mistaken_idea="the parade drums had scared the cart into freezing",
        discovery="lifted a candy wrapper from the axle",
        cause="had doled out rescue fluid beside the cart, and a wrapper stuck to the spill",
        repair="wiped the axle, saved the clean fluid, and doled it into marked safety cups",
        proof="the cart rolled, stopped, and rolled again without leaving a sticky trail",
        lesson="Careful sharing protects both the gift and the place where the gift is used.",
        ending="The rainbow cart zoomed onward with a cheerful brrr and a trail of clean light.",
    ),
    Trial(
        object_name="the little lighthouse battery",
        fluid="clear lightning fluid",
        danger="the lighthouse beam had dimmed while boats searched for the harbor",
        clue="a faint humming wire and a bright drop beneath the battery door",
        mistaken_idea="the fog had swallowed the beam",
        discovery="found a loose copper spring pressing against the fluid tube",
        cause="had tried to dole out extra power before checking the spring",
        repair="secured the spring, measured the fluid, and shared the power with the beacon",
        proof="the beam swept across the water three steady times",
        lesson="Before giving more, a thoughtful helper checks whether the tool can receive it safely.",
        ending="The lighthouse blinked like a brave golden eye above the quiet sea.",
    ),
    Trial(
        object_name="the playground's hero hose",
        fluid="cool silver fluid",
        danger="the hose sprayed only a whisper when the children needed a splash",
        clue="a humming handle, a pinched tube, and a puddle shaped like a star",
        mistaken_idea="the sun had drunk all the fluid",
        discovery="straightened the tube behind the painted slide",
        cause="had pulled the hose while trying to dole out a fast stream",
        repair="rested the hose, opened it halfway, and let each child choose a small turn",
        proof="the stream stayed gentle, and every child got wet shoes and a laugh",
        lesson="A little shared fairly can bring more joy than a lot given to only one person.",
        ending="Splish, splash, hooray! The playground shone with stars of water.",
    ),
    Trial(
        object_name="the museum's tiny comet model",
        fluid="violet comet fluid",
        danger="the model's tail had gone dark during visiting hour",
        clue="a low humming sound and violet drops under the model's clear base",
        mistaken_idea="the model had simply become sleepy",
        discovery="noticed a cracked cup beneath the fluid chamber",
        cause="had filled the chamber too high while trying to dole out a brighter tail",
        repair="changed the cup, measured a smaller amount, and let the model warm up",
        proof="the comet tail curled brightly without dripping",
        lesson="More is not always better; careful amounts help wonderful things keep working.",
        ending="The tiny comet twirled, humming softly as children pointed at its violet tail.",
    ),
]


@dataclass
class World:
    hero: Entity
    helper: Entity
    fountain: Entity
    fluid: Entity
    object_entity: Entity
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


def new_entity(eid: str, kind: str, type_: str, label: str, location: str = "") -> Entity:
    return Entity(id=eid, kind=kind, type=type_, label=label, location=location)


def build_world(params: StoryParams, trial: Trial) -> World:
    hero = new_entity(params.hero, "character", "hero", "the young superhero", "the city")
    helper = new_entity(params.helper, "character", "helper", "the careful helper", "the city")
    fountain = new_entity("fountain", "machine", "fountain", "the humming fountain", "the city")
    fluid = new_entity("fluid", "material", "fluid", trial.fluid, "the fountain")
    object_entity = new_entity("object", "thing", "rescue_object", trial.object_name, "the city")
    return World(hero, helper, fountain, fluid, object_entity)


def tell(params: StoryParams) -> World:
    if params.hero == params.helper:
        raise StoryError("The hero and helper must have different names.")

    trial = TRIALS[params.trouble % len(TRIALS)]
    world = build_world(params, trial)
    h, a, f, fluid, obj = (
        world.hero,
        world.helper,
        world.fountain,
        world.fluid,
        world.object_entity,
    )

    h.memes["courage"] = 2
    h.memes["kindness"] = 1
    a.memes["curiosity"] = 2
    f.meters["flow"] = 1
    f.meters["noise"] = 2
    fluid.meters["brightness"] = 2
    obj.meters["strength"] = 1

    openings = [
        f"At dawn, {h.id}, the superhero of the city, patrolled beside {THEME}.",
        f"{h.id} wore a bright cape as the city woke around {THEME}.",
        f"Before breakfast, {h.id} and {a.id} checked the city's helpful machines.",
        f"The morning sun flashed on {THEME} while {h.id} practiced being a careful hero.",
    ]
    world.say(openings[params.telling % len(openings)])
    world.say(f"Today they were caring for {trial.object_name}, using {trial.fluid}.")
    world.say(f"Then trouble arrived: {trial.danger}.")
    world.say("The fountain made a tiny sound effect: “Hmmm... bzzzt... drip!”")

    world.para()
    world.say(f"Near the fountain, they noticed {trial.clue}.")
    world.say(f"But {trial.mistaken_idea}.")
    dialogue = [
        f"'{a.id}, should I use my super-strength?' {h.id} asked. '{a.id} shook their head. 'First, listen to the humming.'",
        f"'I hear the fountain asking for help,' said {a.id}. 'Then we should learn what is blocking it,' {h.id} replied.",
        f"{h.id} said, 'I can dole out a huge helping of power!' {a.id} answered, 'A small test will keep everyone safe.'",
        f"'Could the sound be a clue?' asked {h.id}. 'Yes,' said {a.id}. 'It changes when the handle moves.'",
    ]
    world.say(dialogue[params.surprise % len(dialogue)])
    h.memes["curiosity"] += 1
    a.memes["trust"] += 1
    world.say("Together they stopped, listened, and tested one small change.")

    world.para()
    world.say(f"The first guess explained the noise but not the missing flow. The humming grew louder: “Hummm... clink!”")
    world.say(f"{h.id} followed the drops while {a.id} watched the handle.")
    world.say(f"At last, they {trial.discovery}.")
    fluid.meters["brightness"] += 1
    f.meters["flow"] = 0
    world.say(
        f"A surprised sparkle popped from the machine. “Ta-da!” The sound revealed that the real trouble was not magic at all."
    )
    world.say(
        f"{a.id} asked, 'What happened?' {h.id} answered honestly, 'I {trial.cause}.'"
    )
    h.memes["worry"] += 1
    h.memes["courage"] += 1
    a.memes["trust"] += 1

    world.para()
    world.say(f"No one laughed or blamed anyone. The two heroes {trial.repair}.")
    f.meters["flow"] = 2
    obj.meters["strength"] = 2
    h.memes["kindness"] += 2
    a.memes["kindness"] += 2
    world.say(f"They tested the repair: {trial.proof}.")
    world.say(f"The lesson learned was simple: {trial.lesson}")
    world.say(
        f"{h.id} smiled. 'Being a superhero means helping with care.' "
        f"{a.id} replied, 'And listening before rushing makes the help stronger.'"
    )

    world.para()
    endings = [
        trial.ending,
        f"With one last “whoosh,” {trial.ending}",
        f"The city cheered, and {trial.ending}",
        f"Everyone shared a quiet laugh as {trial.ending}",
    ]
    world.say(endings[params.lesson % len(endings)])

    world.facts.update(
        trial=trial,
        resolved=True,
        hero=h.id,
        helper=a.id,
        object=trial.object_name,
        fluid=trial.fluid,
        danger=trial.danger,
        clue=trial.clue,
        mistaken_idea=trial.mistaken_idea,
        discovery=trial.discovery,
        cause=trial.cause,
        repair=trial.repair,
        proof=trial.proof,
        lesson=trial.lesson,
        ending=trial.ending,
    )
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"What went wrong with {f['object']}?",
            answer=f"{f['danger'].capitalize()} The problem interrupted the heroes' careful work.",
        ),
        QAItem(
            question="What sound helped the heroes solve the problem?",
            answer=f"They followed {f['clue']}. The humming and the physical clues led them to the real trouble.",
        ),
        QAItem(
            question="What caused the trouble?",
            answer=f"The hero explained that they {f['cause']}. It was an accident, not a deliberate act.",
        ),
        QAItem(
            question="How did the heroes repair the problem?",
            answer=f"They {f['repair']}. Then they checked the result by seeing that {f['proof']}.",
        ),
        QAItem(
            question="What lesson did the heroes learn?",
            answer=f"They learned that {f['lesson']}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does dole mean?",
            answer="To dole something out means to give it in measured portions, often so that several people or things can share it.",
        ),
        QAItem(
            question="What is a fluid?",
            answer="A fluid is a substance that can flow, such as water, juice, or air.",
        ),
        QAItem(
            question="What is humming?",
            answer="Humming is a steady low sound, like the sound made by a small motor or someone singing with closed lips.",
        ),
        QAItem(
            question="Why should a superhero listen before acting?",
            answer="Listening can reveal the real problem and help a superhero choose a safe, useful action instead of rushing into a mistake.",
        ),
        QAItem(
            question="What is a sound effect?",
            answer="A sound effect is a written or performed sound that helps people imagine an action, machine, or surprise.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a child-friendly superhero story in which {f['hero']} must help {f['object']} using {f['fluid']}.",
        f"Use the words dole, fluid, and humming, with a surprise caused by this clue: {f['clue']}.",
        "Include sound effects, a brief dialogue exchange, a concrete repair, and a lesson learned about careful sharing.",
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
    for entity in (
        world.hero,
        world.helper,
        world.fountain,
        world.fluid,
        world.object_entity,
    ):
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id:10} ({entity.kind:8}) location={entity.location!r} "
            f"meters={meters} memes={memes}"
        )
    lines.append(f"  resolved={world.facts.get('resolved', False)}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(humming_city_fountain).
requires(humming_city_fountain, dole).
requires(humming_city_fountain, fluid).
requires(humming_city_fountain, humming).
feature(humming_city_fountain, surprise).
feature(humming_city_fountain, lesson_learned).
feature(humming_city_fountain, sound_effects).
style(humming_city_fountain, superhero_story).

valid_story(S) :-
    setting(S),
    requires(S, dole),
    requires(S, fluid),
    requires(S, humming),
    feature(S, surprise),
    feature(S, lesson_learned),
    feature(S, sound_effects),
    style(S, superhero_story).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    facts = [
        asp.fact("setting", "humming_city_fountain"),
        asp.fact("requires", "humming_city_fountain", "dole"),
        asp.fact("requires", "humming_city_fountain", "fluid"),
        asp.fact("requires", "humming_city_fountain", "humming"),
        asp.fact("feature", "humming_city_fountain", "surprise"),
        asp.fact("feature", "humming_city_fountain", "lesson_learned"),
        asp.fact("feature", "humming_city_fountain", "sound_effects"),
        asp.fact("style", "humming_city_fountain", "superhero_story"),
    ]
    return "\n".join(facts)


def asp_program(show: str = "#show valid_story/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    models = asp.one_model(asp_program())
    valid = any(atom.name == "valid_story" for atom in models)
    if not valid:
        print("MISMATCH: ASP rejected the story domain.")
        return 1

    for index, params in enumerate(CURATED):
        sample = generate(params)
        required = ("dole", "fluid", "humming")
        if not all(word in sample.story.lower() for word in required):
            print(f"MISMATCH: generated sample {index + 1} lacks a seed word.")
            return 1
        if not sample.story_qa:
            print(f"MISMATCH: generated sample {index + 1} lacks story QA.")
            return 1

    print("OK: ASP and Python recognize the humming superhero domain.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Superhero stories about dole, fluid, and humming."
    )
    parser.add_argument("--hero", default=None)
    parser.add_argument("--helper", default=None)
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
    hero = args.hero or rng.choice(["Luna", "Nova", "Ari", "Skye", "Sol"])
    helper = args.helper or rng.choice(["Milo", "Pip", "Remy", "Tara", "Jo"])
    if hero == helper:
        raise StoryError("The hero and helper must have different names.")
    offset = sample_seed - base_seed
    return StoryParams(
        hero=hero,
        helper=helper,
        trouble=offset % len(TRIALS),
        telling=(offset // len(TRIALS)) % 4,
        surprise=(offset // (len(TRIALS) * 4)) % 4,
        lesson=(offset // (len(TRIALS) * 4 * 4)) % 4,
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
    StoryParams(hero="Luna", helper="Milo", trouble=0, telling=0, surprise=0, lesson=0),
    StoryParams(hero="Nova", helper="Pip", trouble=1, telling=1, surprise=1, lesson=1),
    StoryParams(hero="Ari", helper="Remy", trouble=2, telling=2, surprise=2, lesson=2),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import storyworlds.asp as asp

        model = asp.one_model(asp_program())
        print("ASP model:", [str(atom) for atom in model])
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 50):
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
        header = (
            f"### variant {index + 1}"
            if len(samples) > 1 and not args.all
            else ""
        )
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

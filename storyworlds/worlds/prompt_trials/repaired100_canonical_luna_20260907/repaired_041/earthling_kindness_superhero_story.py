#!/usr/bin/env python3
"""
A standalone Storyweavers world about an earthling who discovers that kindness
can be a superhero power.
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


THEME = "earthling kindness superhero story"
SEED_WORDS = {"earthling"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: str = ""

    def __post_init__(self) -> None:
        for key in ("distance", "energy", "noise", "brightness", "damage"):
            self.meters.setdefault(key, 0.0)
        for key in ("worry", "hope", "kindness", "courage", "trust", "joy"):
            self.memes.setdefault(key, 0.0)


@dataclass
class StoryParams:
    name: str = "Luna"
    helper: str = "Pip"
    visitor: str = "Orbi"
    trial: int = 0
    opening: int = 0
    dialogue: int = 0
    ending: int = 0
    seed: Optional[int] = None


@dataclass(frozen=True)
class Trial:
    hero_task: str
    trouble: str
    first_clue: str
    worry: str
    kindness_choice: str
    discovery: str
    visitor_words: str
    repair: str
    proof: str
    lesson: str
    ending: str


TRIALS = [
    Trial(
        hero_task="deliver a bright welcome flag to the town's rooftop garden",
        trouble="a little moon pod drifted into the clouds and its frightened visitor could not find the way home",
        first_clue="a trail of silver pollen leading from the garden gate to the old weather bell",
        worry="The visitor might be lonely, but rushing after the pod could make it drift farther.",
        kindness_choice="stopped to listen, shared the warm glow from her hero badge, and asked what the visitor needed",
        discovery="learned that the pod followed the sound of the weather bell because it mistook the bell for its family signal",
        visitor_words="I thought nobody here would understand me",
        repair="wrapped a soft scarf around the bell so it chimed gently, then built a paper signal beside the garden",
        proof="the pod followed the quiet signal down and settled safely beside its visitor",
        lesson="Kindness begins when someone feels heard, not when someone feels hurried.",
        ending="The welcome flag waved above the garden while the moon pod blinked a grateful blue.",
    ),
    Trial(
        hero_task="paint a golden shield for the neighborhood helper station",
        trouble="a sudden storm scattered the station's supplies, and a small cloud creature hid beneath a bench",
        first_clue="tiny wet footprints beside a box of fallen bandages",
        worry="A scared creature may need shelter before it needs questions.",
        kindness_choice="held her cape over the bench, spoke softly, and offered the creature a dry towel",
        discovery="found that the creature had been carrying the bandages away to cover a shivering bird",
        visitor_words="I did not mean to make a mess; the bird was cold",
        repair="moved the supplies under the awning and made a small bird blanket from the spare cloth",
        proof="the bird warmed up, and every bandage was sorted into a dry labeled box",
        lesson="A kind hero looks for the need behind a confusing action.",
        ending="The painted shield shone over the station, where the cloud creature proudly held the clean bandage box.",
    ),
    Trial(
        hero_task="bring a new battery to the lighthouse on Starfish Hill",
        trouble="the lighthouse beam went dark just as a lost earthling family reached the rocky shore",
        first_clue="a trail of glowing pebbles placed in a careful line toward the tide pools",
        worry="Those pebbles may be a message, so they should be read before they are moved.",
        kindness_choice="followed the glowing trail with the family and kept the smallest earthling close beside her",
        discovery="realized that the pebbles marked a safe path around the slippery rocks",
        visitor_words="We were afraid to call because we thought we were causing trouble",
        repair="carried the battery with the family, restored the beam, and placed a kindness bell near the path",
        proof="the bright beam showed the safe route, and the family rang the bell to thank the helpers",
        lesson="Kindness gives people courage to ask for help.",
        ending="The lighthouse swept its warm beam across the sea like a giant, gentle wave.",
    ),
    Trial(
        hero_task="lead a rescue parade for the city's tired delivery robots",
        trouble="the robots stopped in the square because a loud alarm made every route sign spin",
        first_clue="one quiet robot holding a paper map upside down near the fountain",
        worry="The robot may be confused rather than broken.",
        kindness_choice="turned down the alarm, crouched beside the robot, and asked it to show the map",
        discovery="noticed that the map was right but the spinning sign pointed the wrong way",
        visitor_words="I kept trying, but everyone called me slow",
        repair="held the sign steady, marked the safe routes with chalk stars, and invited the robots to rest",
        proof="the robots delivered their parcels calmly and left a thank-you star at the fountain",
        lesson="Patience can reveal a problem that blame would hide.",
        ending="The parade rolled on beneath a sky of chalk stars, each one marking a helpful choice.",
    ),
    Trial(
        hero_task="protect the school observatory during the annual meteor shower",
        trouble="a tiny star visitor landed in the courtyard and its bright glow frightened everyone",
        first_clue="a warm circle on the grass surrounded by flowers that had opened overnight",
        worry="Something bright can still be gentle if people give it room.",
        kindness_choice="asked the children to step back, brought a blanket, and spoke to the visitor without grabbing it",
        discovery="understood that the visitor was using the flowers to find a quiet place to rest",
        visitor_words="Your world is loud, but your careful voices feel safe",
        repair="made a quiet corner with blankets and signs asking everyone to whisper",
        proof="the star visitor dimmed to a soft gold and showed the children a map of the sky",
        lesson="Making space for someone can be a powerful kind of welcome.",
        ending="That night, every child saw the meteor shower from the quiet corner, shoulder to shoulder.",
    ),
    Trial(
        hero_task="deliver fresh water to the desert research camp",
        trouble="a thirsty sand sprite had tangled the water hose while trying to fill a tiny cup",
        first_clue="a cup no bigger than a shell resting beside the knotted hose",
        worry="The knot is a problem, but the tiny cup explains why it was made.",
        kindness_choice="filled the little cup first, then showed the sprite how to loosen the hose without tearing it",
        discovery="learned that the sprite had heard the camp's thirsty plants whispering underground",
        visitor_words="I wanted to help, but I did not know the earthling way",
        repair="shared the water, untangled the hose, and built a small drip line for the plants",
        proof="the plants lifted their leaves, and the sprite copied the new careful method",
        lesson="Kindness teaches without making someone feel small.",
        ending="Green shoots appeared beside the camp, tiny flags of friendship in the sand.",
    ),
]


@dataclass
class World:
    hero: Entity
    helper: Entity
    visitor: Entity
    badge: Entity
    setting: Entity
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
    hero = Entity(params.name, "character", "earthling", "the earthling hero", location="town")
    helper = Entity(params.helper, "character", "helper", "the helper", location="town")
    visitor = Entity(params.visitor, "character", "visitor", "the visiting friend", location="sky")
    badge = Entity("kindness_badge", "object", "badge", "kindness badge", location="hero")
    setting = Entity("hero_world", "place", "setting", "the neighborhood", location="home")
    return World(hero, helper, visitor, badge, setting)


def tell(params: StoryParams) -> World:
    world = build_world(params)
    h, a, v = world.hero, world.helper, world.visitor
    trial = TRIALS[params.trial % len(TRIALS)]

    h.memes["worry"] = 1
    h.memes["hope"] = 1
    h.memes["kindness"] = 2
    a.memes["trust"] = 1
    v.memes["worry"] = 2
    world.facts["trial"] = trial

    openings = [
        f"{h.id} was an earthling superhero in training, but her favorite power was kindness. One bright morning, she and {a.id} set out to {trial.hero_task}.",
        f"The neighborhood knew {h.id} as an earthling with a shining kindness badge. Today, {a.id} joined her while they tried to {trial.hero_task}.",
        f"{h.id} checked her cape, her kindness badge, and the path ahead. She and {a.id} were ready to {trial.hero_task}.",
        f"Even before she could fly, {h.id} had learned that an earthling hero must notice who needs help. That lesson mattered when she went to {trial.hero_task}.",
    ]
    world.say(openings[params.opening % len(openings)])
    world.say(f"Then {trial.trouble}. The job suddenly became a rescue.")
    world.say(f"{h.id}'s badge glowed softly, not because she was the strongest hero, but because she was willing to care.")

    world.para()
    world.say(f"Near the trouble, {trial.first_clue}.")
    world.say(f"{h.id} whispered, \"{trial.worry}\"")
    dialogue = [
        f"{a.id} asked, \"Should we hurry?\" {h.id} answered, \"We should help carefully, so our help does not become another problem.\"",
        f"\"What can we do first?\" {a.id} asked. \"Listen,\" said {h.id}. \"Kindness starts with learning what someone needs.\"",
        f"{a.id} pointed toward the trouble. \"I am scared.\" {h.id} replied, \"Then we will be brave together, one gentle step at a time.\"",
        f"\"Can kindness really solve this?\" {a.id} asked. {h.id} smiled. \"It can help us notice the next right thing.\"",
    ]
    world.say(dialogue[params.dialogue % len(dialogue)])
    world.say(f"Instead of showing off, {h.id} {trial.kindness_choice}.")
    h.memes["courage"] += 1
    h.memes["kindness"] += 2
    a.memes["trust"] += 1

    world.para()
    world.say(f"That quiet choice changed the rescue. {h.id} {trial.discovery}.")
    world.say(f"{v.id} looked up and said, \"{trial.visitor_words}.\"")
    v.memes["worry"] = 0
    v.memes["trust"] += 2
    h.memes["hope"] += 1
    world.say(f"{h.id} answered, \"You belong here while we work this out. We can solve it together.\"")
    world.say(f"Now that everyone understood the real need, {h.id}, {a.id}, and {v.id} {trial.repair}.")
    world.facts["resolved"] = True

    world.para()
    h.memes["joy"] += 2
    v.memes["joy"] += 1
    world.say(f"They tested the plan: {trial.proof}.")
    world.say(f"{a.id} said, \"You used kindness like a superhero power.\"")
    world.say(f"{h.id} shook her head. \"Kindness is not only my power. It grows when all of us use it.\"")
    world.say(f"The lesson became clear: {trial.lesson}")
    endings = [
        trial.ending,
        f"As the evening arrived, {trial.ending}",
        f"Everyone went home safer and happier. {trial.ending}",
        f"The kindness badge shone once more. {trial.ending}",
    ]
    world.say(endings[params.ending % len(endings)])

    world.facts.update(
        hero=h.id,
        helper=a.id,
        visitor=v.id,
        task=trial.hero_task,
        trouble=trial.trouble,
        clue=trial.first_clue,
        choice=trial.kindness_choice,
        discovery=trial.discovery,
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
            f"What trouble did {f['hero']} face?",
            f"{f['hero']} faced a rescue problem: {f['trouble']}.",
        ),
        QAItem(
            f"What clue helped {f['hero']} understand the situation?",
            f"The important clue was {f['clue']}. It helped {f['hero']} look for the visitor's real need.",
        ),
        QAItem(
            f"How did {f['hero']} show kindness?",
            f"{f['hero']} {f['choice']}. That careful choice helped everyone understand what to do.",
        ),
        QAItem(
            f"What changed after the characters listened to one another?",
            f"{f['discovery']}. Then the friends {f['repair']}.",
        ),
        QAItem(
            "What did the superhero learn?",
            f"The superhero learned that {f['lesson']}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is an earthling?",
            "An earthling is a living creature from Earth, especially a person who lives on our planet.",
        ),
        QAItem(
            "What is kindness?",
            "Kindness means noticing another person's needs and choosing to help, respect, or comfort them.",
        ),
        QAItem(
            "Why is listening important when helping?",
            "Listening is important because it reveals what someone actually needs instead of making us guess.",
        ),
        QAItem(
            "What makes someone a superhero in this storyworld?",
            "A superhero is someone who uses courage and care to protect others. Super strength is not required.",
        ),
        QAItem(
            "What does teamwork mean?",
            "Teamwork means sharing ideas and actions so people can solve a problem together.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a child-friendly superhero story about an earthling named {f['hero']} who uses kindness while trying to {f['task']}.",
        f"Tell a story where {f['hero']} listens carefully after {f['trouble']}, then repairs the problem with friends.",
        "Create a gentle superhero adventure showing that kindness is a real power and that every character can use it.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
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
    for entity in (world.hero, world.helper, world.visitor, world.badge, world.setting):
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id:14} ({entity.kind:9}) "
            f"location={entity.location!r} meters={meters} memes={memes}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
setting(hero_world).
feature(hero_world, kindness).
requires(hero_world, earthling).
valid_story(S) :- setting(S), feature(S, kindness), requires(S, earthling).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    return "\n".join(
        [
            asp.fact("setting", "hero_world"),
            asp.fact("feature", "hero_world", "kindness"),
            asp.fact("requires", "hero_world", "earthling"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    models = asp.one_model(asp_program("#show valid_story/1."))
    recognized = any(atom.name == "valid_story" for atom in models)
    if not recognized:
        print("MISMATCH: ASP rules did not recognize the earthling kindness domain.")
        return 1

    for trial in range(len(TRIALS)):
        params = StoryParams(trial=trial, seed=trial)
        sample = generate(params)
        if not sample.story or "kindness" not in sample.story.lower():
            print("MISMATCH: generated story failed kindness coverage.")
            return 1
        if "earthling" not in sample.story.lower():
            print("MISMATCH: generated story failed earthling coverage.")
            return 1
    print("OK: ASP and Python recognize the earthling kindness superhero domain.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate earthling superhero stories powered by kindness."
    )
    parser.add_argument("--name", default=None)
    parser.add_argument("--helper", default=None)
    parser.add_argument("--visitor", default=None)
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
    name = args.name or rng.choice(["Luna", "Nova", "Mira", "Sol", "Ari"])
    helper = args.helper or rng.choice(["Pip", "Tavi", "Niko", "Bee", "Jo"])
    visitor = args.visitor or rng.choice(["Orbi", "Kiko", "Zell", "Momo", "Vee"])
    if len({name, helper, visitor}) != 3:
        raise StoryError("The earthling, helper, and visitor must have different names.")
    offset = sample_seed - base_seed
    return StoryParams(
        name=name,
        helper=helper,
        visitor=visitor,
        trial=offset % len(TRIALS),
        opening=(offset // len(TRIALS)) % 4,
        dialogue=(offset // (len(TRIALS) * 4)) % 4,
        ending=(offset // (len(TRIALS) * 4 * 4)) % 4,
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
    StoryParams(name="Luna", helper="Pip", visitor="Orbi", trial=0, seed=0),
    StoryParams(name="Nova", helper="Tavi", visitor="Zell", trial=1, seed=1),
    StoryParams(name="Mira", helper="Bee", visitor="Kiko", trial=2, seed=2),
    StoryParams(name="Sol", helper="Niko", visitor="Vee", trial=3, seed=3),
    StoryParams(name="Ari", helper="Jo", visitor="Momo", trial=4, seed=4),
    StoryParams(name="Luna", helper="Tavi", visitor="Kiko", trial=5, seed=5),
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

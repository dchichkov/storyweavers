#!/usr/bin/env python3
"""
A folk-tale storyworld about embroidery, wind, and a sharing choice.
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
while ROOT != os.path.dirname(ROOT) and not os.path.exists(os.path.join(ROOT, "results.py")):
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Place:
    name: str
    wind_strength: float = 1.0


@dataclass
class StoryParams:
    place: str = "hill village"
    hero: str = "Luna"
    elder: str = "Mara"
    child: str = "Pip"
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]

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


@dataclass
class Arc:
    cloth: str
    pattern: str
    wind_event: str
    worry: str
    discovery: str
    action: str
    dialogue: str
    sharing: str
    ending: str


ARCS = [
    Arc(
        "a square of cream linen",
        "a golden sun stitched above three blue hills",
        "a hard wind rushed down from the high ridge",
        "that the precious cloth would fly into the ravine",
        "that the cloth was caught on the village bell rope, while a covered bowl of gelatin trembled on the feast table",
        "held the rope with one hand, gathered the embroidery with the other, and asked everyone to pass the gelatin bowls indoors",
        "\"A feast is not made smaller by another spoonful,\" Luna said",
        "Luna cut the gelatin into equal shining cubes so that even the latecomers received a piece",
        "the embroidery became a banner above the feast, and the last cube of gelatin glittered on a shared plate",
    ),
    Arc(
        "a red cloth trimmed with green thread",
        "a little fox carrying a moon",
        "the wind lifted the washing lines and rattled every shutter",
        "that the cloth would tear before the wedding blessing",
        "that a hidden pocket in the embroidery held the village recipe for cooling gelatin",
        "used the stitched pocket as a sail to guide the cloth toward the sheltered oven wall",
        "\"What is hidden for one hand may help every hungry hand,\" Mara said",
        "Luna revealed the recipe and divided the gelatin among the wedding guests",
        "the fox and moon shone above the door while strangers and cousins ate from the same bowl",
    ),
    Arc(
        "a pale blue scarf",
        "seven silver fish swimming around a red star",
        "the wind spun it high above the market square",
        "that the beautiful work would vanish beyond the fields",
        "that the scarf had wrapped around the mayor's basket of gelatin cups",
        "followed the fluttering thread and lowered the basket before a single cup tipped",
        "\"Save the sweetness before you save the praise,\" Pip called",
        "Luna gave the rescued gelatin to the market workers who had helped her",
        "the scarf hung across the square, and its silver fish seemed to swim over every grateful face",
    ),
    Arc(
        "a narrow green table runner",
        "a row of red apples beneath a crooked crown",
        "the wind burst through the open granary door",
        "that the runner would cover the village well",
        "that its loose thread had caught a wooden scoop beside a jar of strawberry gelatin",
        "pulled the thread free, steadied the scoop, and carried the gelatin to the shade",
        "\"A careful stitch is worth more when it keeps a neighbor safe,\" Luna said",
        "she offered the gelatin first to the tired miller and his children",
        "the runner lay flat on the feast table, and the well remained clear beneath the apple crown",
    ),
    Arc(
        "a warm orange shawl",
        "two birds sharing one berry",
        "a playful wind tugged it from Luna's shoulders",
        "that the cold evening would spoil the village supper",
        "that the shawl had landed over a basket of lemon gelatin left for the old shepherd",
        "wrapped the shepherd in the shawl and carried the basket to the fire",
        "\"Warmth and sweetness travel farther when they are shared,\" Luna told him",
        "the villagers passed the gelatin around and saved the largest portion for the shepherd",
        "the two embroidered birds rested beside the fire while the whole village shared the final spoonful",
    ),
]


def tell_story(params: StoryParams) -> World:
    if params.place != "hill village":
        raise StoryError("This folk tale takes place in the hill village.")
    world = World(Place("the hill village", wind_strength=1.0))
    hero = world.add(Entity(params.hero, "character", "girl", params.hero))
    elder = world.add(Entity(params.elder, "character", "woman", params.elder))
    child = world.add(Entity(params.child, "character", "child", params.child))
    cloth = world.add(Entity("embroidery", "object", "cloth", "embroidered cloth"))
    dessert = world.add(Entity("gelatin", "food", "gelatin", "gelatin"))
    hero.memes.update(care=1.0, fairness=1.0)
    elder.memes["wisdom"] = 1.0
    child.memes["curiosity"] = 1.0
    cloth.meters["stitch_strength"] = 1.0
    dessert.meters["portions"] = 6.0

    arc = ARCS[(params.seed or 0) % len(ARCS)]
    world.facts.update(
        hero=hero,
        elder=elder,
        child=child,
        cloth=cloth,
        dessert=dessert,
        arc=(params.seed or 0) % len(ARCS),
        cloth_description=arc.cloth,
        pattern=arc.pattern,
        wind_event=arc.wind_event,
        worry=arc.worry,
        discovery=arc.discovery,
        action=arc.action,
        dialogue=arc.dialogue,
        sharing=arc.sharing,
        ending=arc.ending,
        moral="A good gift grows greater when it is shared.",
        twist="The treasured embroidery was also the clue that saved the gelatin feast.",
    )

    world.say(
        f"In {world.place.name}, {hero.id} embroidered {arc.pattern} onto {arc.cloth}. "
        f"{elder.id} prepared a bright bowl of gelatin for the evening feast, while {child.id} arranged cups beneath the village oak."
    )
    world.para()
    world.say(
        f"Just as the villagers gathered, {arc.wind_event}. {hero.id} reached for the embroidery, "
        f"but everyone saw only a flash of thread and silver sky."
    )
    world.say(f"{hero.id} feared {arc.worry}. The feast grew quiet, and even the gelatin wobbled in its bowl.")
    world.para()
    world.say(
        f"Then {hero.id}, {elder.id}, and {child.id} followed the dancing thread. They discovered {arc.discovery}."
    )
    world.say(f"{hero.id} {arc.action}. {arc.dialogue}.")
    world.facts["danger_resolved"] = True
    world.facts["shared"] = True
    dessert.meters["portions"] = 6.0
    world.para()
    world.say(
        f"The villagers gathered around the table. {arc.sharing}. "
        f"The embroidered pattern, once meant to win praise for one careful pair of hands, became a lesson for everyone."
    )
    world.say(
        f"Mara lifted the cloth and said, \"{world.facts['moral']}\" "
        f"The wind carried her words across the roofs, but it could not carry away what the people had learned."
    )
    world.para()
    world.say(f"By moonrise, {arc.ending}. {hero.id} kept the first needle, but shared every beautiful thing it helped make.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Tell a folk tale involving embroidery, wind, and gelatin, with a sharing choice and a moral value.",
        f"Write a gentle village tale where {f['hero'].id} follows embroidery through a sudden wind and discovers a hidden way to help others.",
        "Create a story with a twist: a treasured handmade object saves a feast, and sharing changes its meaning.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    return [
        QAItem(
            f"What did {hero.id} embroider before the feast?",
            f"{hero.id} embroidered {f['pattern']} onto {f['cloth_description']}.",
        ),
        QAItem(
            "What danger did the wind create?",
            f"The wind threatened the embroidery because {f['worry']}.",
        ),
        QAItem(
            "What twist did the villagers discover?",
            f"They discovered {f['discovery']}, so the embroidery became a clue that helped protect the gelatin feast.",
        ),
        QAItem(
            "How did the villagers show sharing?",
            f"They shared the gelatin so that everyone, including those who helped late, received a portion. {f['sharing']}.",
        ),
        QAItem(
            "What moral value did the story teach?",
            f"It taught that sharing makes a gift greater: {f['moral']}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is embroidery?", "Embroidery is the art of decorating cloth with colored thread and stitches."),
        QAItem("What is wind?", "Wind is moving air that can be gentle or strong enough to lift light objects."),
        QAItem("What is gelatin?", "Gelatin is a soft, jiggly food made when a flavored mixture sets."),
        QAItem("Why is sharing a moral value?", "Sharing is a moral value because it shows care and helps people enjoy useful or joyful things together."),
    ]


ASP_RULES = r"""
safe_feast :- wind_event, embroidery_found, gelatin_protected.
sharing_good :- safe_feast, portions_shared.
moral_value(generosity) :- sharing_good.
twist(repurposed_embroidery) :- embroidery_found, gelatin_protected.
#show safe_feast/0.
#show sharing_good/0.
#show moral_value/1.
#show twist/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("wind_event"),
            asp.fact("embroidery_found"),
            asp.fact("gelatin_protected"),
            asp.fact("portions_shared"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_outcome() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show safe_feast/0.\n#show sharing_good/0.\n#show moral_value/1.\n#show twist/1."))
    atoms = []
    for name in ("safe_feast", "sharing_good", "moral_value", "twist"):
        atoms.extend(asp.atoms(model, name))
    return sorted(atoms, key=str)


def verify_sample(sample: StorySample) -> bool:
    required = ("embroidery", "wind", "gelatin")
    text = sample.story.lower()
    return all(word in text for word in required) and "shared" in text and len(sample.story_qa) >= 5


def asp_verify() -> int:
    result = asp_outcome()
    expected = [(), (), ("generosity",), ("repurposed_embroidery",)]
    if result != expected:
        print(f"MISMATCH: ASP={result}")
        return 1
    sample = generate(StoryParams(seed=0))
    if not verify_sample(sample):
        print("MISMATCH: generated story failed its narrative checks.")
        return 1
    print("OK: ASP, Python state, and generated story agree.")
    return 0


NAMES = ["Luna", "Nella", "Tara", "Mira", "Sela"]
ELDERS = ["Mara", "Anwen", "Ruth", "Ola", "Yara"]
CHILDREN = ["Pip", "Timo", "Nia", "Bo", "Lio"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk tale about embroidery, wind, gelatin, and sharing.")
    ap.add_argument("--place", choices=["hill village"])
    ap.add_argument("--hero", choices=NAMES)
    ap.add_argument("--elder", choices=ELDERS)
    ap.add_argument("--child", choices=CHILDREN)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(NAMES)
    elder = args.elder or rng.choice([x for x in ELDERS if x != hero])
    child = args.child or rng.choice([x for x in CHILDREN if x not in {hero, elder}])
    return StoryParams(
        place=args.place or "hill village",
        hero=hero,
        elder=elder,
        child=child,
        seed=args.seed,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: kind={entity.kind}, meters={entity.meters}, memes={entity.memes}"
        )
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
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
        print(asp_program("#show safe_feast/0.\n#show sharing_good/0.\n#show moral_value/1.\n#show twist/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_outcome())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for seed in range(len(ARCS)):
            samples.append(
                generate(
                    StoryParams(
                        place="hill village",
                        hero="Luna",
                        elder="Mara",
                        child="Pip",
                        seed=seed,
                    )
                )
            )
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n:
            seed = base_seed + i
            i += 1
            sample = generate(resolve_params(args, random.Random(seed)))
            if sample.story not in seen:
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
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

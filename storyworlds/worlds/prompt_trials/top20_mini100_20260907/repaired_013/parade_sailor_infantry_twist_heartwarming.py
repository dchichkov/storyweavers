#!/usr/bin/env python3
"""
A heartwarming little story world about a parade, a sailor, and infantry, with
a twist that turns the march into a kinder ending.
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
class StoryParams:
    parade_name: str = "the Lantern Parade"
    sailor_name: str = "Mina"
    infantry_name: str = "Captain Reed"
    setting: str = "harbor square"
    seed: Optional[int] = None


@dataclass
class Entity:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.name] = ent
        return ent

    def get(self, name: str) -> Entity:
        return self.entities[name]


PARADE_REGISTRY = {
    "the Lantern Parade": {
        "mood": "bright and careful",
        "route": "through the harbor square and past the sea wall",
    },
    "the Ribbon Parade": {
        "mood": "cheerful and tidy",
        "route": "down the main street and around the fountain",
    },
    "the Harbor Parade": {
        "mood": "salt-sweet and lively",
        "route": "from the docks to the town steps",
    },
}

SETTING_REGISTRY = {
    "harbor square": {
        "water": True,
        "crowds": True,
    },
    "the town green": {
        "water": False,
        "crowds": True,
    },
    "the old dock": {
        "water": True,
        "crowds": False,
    },
}


@dataclass(frozen=True)
class ParadeArc:
    title: str
    premise: str
    problem: str
    twist: str
    action: str
    result: str
    ending: str
    problem_answer: str
    twist_answer: str
    result_answer: str


PARADE_ARCS = [
    ParadeArc(
        title="The Lost Drumbeat",
        premise="The parade was ready, but the drum leader had lost the beat cards in a gust of sea wind.",
        problem="The infantry waited in place, the sailor held a lantern, and the line began to wobble with worry.",
        twist="Then the sailor tapped a familiar rhythm on an empty tin cup and smiled. \"That is the tide beat,\" she said.",
        action="The infantry listened, matched their steps to the rhythm, and passed the sound down the whole parade.",
        result="The march straightened at once, and the parade moved like one friendly body instead of many worried feet.",
        ending="the lanterns bobbed over the square while the sea wind carried the same gentle beat home",
        problem_answer="The drum leader had lost the beat cards, so the parade did not know how to keep together.",
        twist_answer="The sailor recognized the rhythm as a tide beat and showed the others how to follow it.",
        result_answer="Once everyone marched to the same rhythm, the parade became steady and joyful again.",
    ),
    ParadeArc(
        title="The Rainy Uniforms",
        premise="The parade began under a soft rain, and the infantry uniforms grew heavy and cold.",
        problem="The sailor wanted to help, but the only dry cloth was wrapped around the parade banner.",
        twist="Instead of guarding the banner alone, the infantry opened it wide as a shared canopy and laughed at the drizzle.",
        action="The sailor tied the corners with rope, and soon the banner became a bright roof over the marching line.",
        result="No one stayed dry by themselves, but everyone stayed warm together, and the parade grew happier with every step.",
        ending="one banner shone above many smiling faces, striped with rain and sunlight",
        problem_answer="Rain made the infantry uniforms cold and heavy.",
        twist_answer="The infantry turned the banner into a shared canopy so everyone could use it.",
        result_answer="The shared shelter kept the group warm together and made the parade happier.",
    ),
    ParadeArc(
        title="The Tiny Lost Sailor",
        premise="A little sailor named Mina had wandered into the parade while looking for the harbor bell.",
        problem="The infantry were marching in strict rows, and Mina could not see the way out between all the boots and flags.",
        twist="Then the captain bent down and said, \"Stay near me. A parade can make room for one small sailor.\"",
        action="The infantry shifted their rows to open a safe path, and Mina followed the captain's polished button like a bright star.",
        result="The sailor found the harbor bell, and the parade found a softer step that left room for kindness.",
        ending="the smallest pair of footprints walked safely beside the biggest row of boots",
        problem_answer="Mina got lost between the marching boots and flags.",
        twist_answer="The captain chose to make room for Mina instead of keeping the rows strict.",
        result_answer="The parade opened a safe path, helping Mina get to the harbor bell and teaching kindness.",
    ),
    ParadeArc(
        title="The Broken Float",
        premise="The parade carried a wooden float shaped like a ship, but one wheel snapped near the square.",
        problem="The infantry could lift the float only a little, and the sailor feared the parade would stop before the music began.",
        twist="A child in the crowd offered a red ribbon, and the sailor tied it to the broken wheel as a bright warning.",
        action="The infantry pushed slowly, the sailor guided from the side, and the float rolled on its good wheels with care.",
        result="The ship float survived the journey, and the crowd cheered because everyone had helped in a small, kind way.",
        ending="a ribbon fluttered from the wheel like a tiny flag of thanks",
        problem_answer="One wheel on the ship float snapped, threatening to stop the parade.",
        twist_answer="A child offered a ribbon, and the sailor used it to mark the broken wheel instead of hiding the damage.",
        result_answer="With careful teamwork, the float rolled safely and the crowd celebrated their shared help.",
    ),
    ParadeArc(
        title="The Missing Marcher",
        premise="On parade morning, the infantry counted their ranks and found one empty space near the end.",
        problem="The missing marcher was the sailor's old friend, who had stayed behind to patch a leak in the harbor roof.",
        twist="The sailor told the captain, \"He is not late. He is guarding the town.\" The captain nodded at once.",
        action="So the infantry carried an extra lantern in the empty space, and the parade honored the absent helper as they marched.",
        result="By the time the parade ended, the missing marcher arrived with wet hands and a grateful grin.",
        ending="the extra lantern stayed lit beside the rank it had protected, glowing like a promise",
        problem_answer="There was one empty place in the infantry ranks because a friend was still fixing the harbor roof.",
        twist_answer="The sailor explained that the friend was helping the town, and the captain understood immediately.",
        result_answer="The parade honored the missing helper and welcomed him at the end with gratitude.",
    ),
    ParadeArc(
        title="The Parade Dinner",
        premise="After a long march, the parade gathered near the steps with a table set for the officers.",
        problem="The infantry had not yet eaten, and the sailor carried only one warm loaf from the bakery.",
        twist="The sailor broke the loaf into many small pieces and said, \"A parade feels better when no one watches another go hungry.\"",
        action="The infantry sat on the curb, passed the bread around, and saved the crust for the youngest drummer.",
        result="The table of officers was forgotten, but nobody minded, because the real feast was the shared bread and laughter.",
        ending="crumbs and smiles remained on the steps long after the music stopped",
        problem_answer="The marching group was hungry, but there was only one loaf of bread.",
        twist_answer="The sailor split the loaf for everyone instead of saving it for the officers' table.",
        result_answer="Sharing the bread turned the end of the parade into a warm, happy meal for all.",
    ),
    ParadeArc(
        title="The Upside-Down Banner",
        premise="The parade banner was sewn backward, so the words faced the wrong way as the march began.",
        problem="The infantry feared the crowd would laugh, and the sailor worried the mistake would spoil the day.",
        twist="Then the captain chuckled and said, \"Good. We will march so the banner can wave to the people on both sides.\"",
        action="The sailor and infantry turned together, and the banner flashed bright letters toward every window.",
        result="What looked like an error became the cleverest part of the parade, and the crowd applauded the brave choice.",
        ending="the banner kept waving both ways, as if it had learned to greet every neighbor",
        problem_answer="The banner's words faced the wrong way at the start of the parade.",
        twist_answer="The captain turned the mistake into a clever idea by letting the banner wave to both sides.",
        result_answer="The parade continued happily, and the crowd loved the new way the banner greeted everyone.",
    ),
]


OPENINGS = [
    "On a clear morning in {setting}, {parade_name} began with {sailor_name} beside the water and {infantry_name} at the front.",
    "The people of {setting} loved {parade_name}, especially when {sailor_name} marched near {infantry_name} and the drums sounded soft and warm.",
    "In {setting}, the day of {parade_name} always smelled of rope, bread, and painted flags.",
    "When {parade_name} came to {setting}, {sailor_name} and {infantry_name} both believed the town needed a cheerful march.",
]


def _stable_seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    text = "|".join((params.parade_name, params.sailor_name, params.infantry_name, params.setting))
    return sum((i + 1) * ord(ch) for i, ch in enumerate(text))


def _fill(text: str, facts: dict[str, object]) -> str:
    return text.format(**facts)


def _sentence_start(text: str) -> str:
    return text[:1].upper() + text[1:]


def _story_lines(world: World) -> list[str]:
    f = world.facts
    arc: ParadeArc = f["arc"]
    opening = _fill(OPENINGS[f["opening_variant"]], f)
    premise = _fill(arc.premise, f)
    problem = _fill(arc.problem, f)
    twist = _fill(arc.twist, f)
    action = _fill(arc.action, f)
    result = _fill(arc.result, f)
    ending = _fill(arc.ending, f)
    theme = "parade, sailor, infantry, twist, and heartwarming care"

    structures = [
        [
            f"{opening} It was the day of \"{arc.title}.\"",
            f"{premise} {problem}",
            f"{twist} {f['infantry_name']} answered, \"Then we march together.\"",
            f"{action} The parade lines grew steadier with every step.",
            f"{result} \"That was the best kind of twist,\" said {f['sailor_name']}, and the crowd cheered.",
            f"At sunset, {ending}. That is why the town remembered a heartwarming tale of {theme}.",
        ],
        [
            opening,
            f"\"Are we too late?\" asked {f['sailor_name']}. {premise}",
            _sentence_start(problem),
            f"{twist} {f['infantry_name']} smiled and said, \"We can change our plan.\"",
            f"Then {action[0].lower() + action[1:]}",
            f"{result} The parade felt smaller at first, then bigger with kindness.",
        ],
        [
            f"People still tell the story of \"{arc.title},\" because {opening[0].lower() + opening[1:]}",
            f"{premise} Soon, {problem[0].lower() + problem[1:]}",
            f"\"Listen,\" said {f['sailor_name']}. {twist}",
            f"{f['infantry_name']} nodded. {action}",
            f"{result} Everyone learned that a twist can turn a worry into help.",
            f"The last picture was simple: {ending}.",
        ],
        [
            f"{opening} The parade was not perfect, but it was ready.",
            f"Then came the trouble. {problem}",
            f"{f['sailor_name']} took a breath and said, \"I have a twist for this.\" {twist}",
            f"{action} \"Now that feels right,\" said {f['infantry_name']}.",
            f"{result} The crowd saw that the parade was strongest when it made room for people.",
            f"By night, {ending} and the whole square felt warm inside.",
        ],
        [
            f"{opening} The music drifted over {f['setting']} like a ribbon.",
            f"Under that ribbon of sound, {premise[0].lower() + premise[1:]} {problem}",
            f"{twist} {f['sailor_name']} laughed softly, and {f['infantry_name']} laughed too.",
            f"{action} The children copied the steps, and the parents clapped in time.",
            f"{result} No one forgot the turn the day had taken.",
            f"The parade ended with {ending}, a small sign that the town had grown kinder.",
        ],
        [
            f"The ending of \"{arc.title}\" is easy to remember: {ending}.",
            f"But it began in a plain way. {premise}",
            f"Then the wrong thing happened. {problem}",
            f"\"Don't hide it,\" said {f['sailor_name']}. {twist}",
            f"{action}",
            f"{result} That is why the story feels heartwarming instead of merely busy.",
        ],
    ]
    return structures[f["structure_variant"]]


ASP_RULES = r"""
setting(harbor_square).
setting(town_green).
setting(old_dock).

feature(twist).
feature(heartwarming).

can_tell_story(S) :- setting(S), feature(twist), feature(heartwarming).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTING_REGISTRY:
        lines.append(asp.fact("setting", s.replace(" ", "_")))
    for p in PARADE_REGISTRY:
        lines.append(asp.fact("parade", p.replace("the ", "").replace(" ", "_")))
    lines.append(asp.fact("feature", "twist"))
    lines.append(asp.fact("feature", "heartwarming"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming parade story world with a sailor and infantry.")
    ap.add_argument("--parade-name", choices=list(PARADE_REGISTRY))
    ap.add_argument("--sailor-name")
    ap.add_argument("--infantry-name")
    ap.add_argument("--setting", choices=list(SETTING_REGISTRY))
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    parade_name = args.parade_name or rng.choice(list(PARADE_REGISTRY))
    sailor_name = args.sailor_name or rng.choice(["Mina", "Jo", "Elio", "Nora", "Pip"])
    infantry_name = args.infantry_name or rng.choice(["Captain Reed", "Sergeant Bell", "Lieutenant Hale", "Captain Vale"])
    setting = args.setting or rng.choice(list(SETTING_REGISTRY))
    if sailor_name == infantry_name:
        raise StoryError("The sailor and infantry leader must be different characters.")
    return StoryParams(parade_name=parade_name, sailor_name=sailor_name, infantry_name=infantry_name, setting=setting)


def generate(params: StoryParams) -> StorySample:
    seed = _stable_seed(params)
    arc = PARADE_ARCS[seed % len(PARADE_ARCS)]
    world = World(setting=params.setting)
    sailor = world.add(Entity(name=params.sailor_name, kind="sailor", meters={"distance": 0.0}, memes={"kindness": 1.0}))
    infantry = world.add(Entity(name=params.infantry_name, kind="infantry", meters={"formation": 1.0}, memes={"duty": 1.0}))
    parade = world.add(Entity(name=params.parade_name, kind="parade", meters={"noise": 1.0}, memes={"joy": 1.0}))
    world.add(Entity(name="the crowd", kind="people", meters={"attention": 1.0}, memes={"hope": 1.0}))
    world.facts.update(
        sailor=sailor.name,
        infantry=infantry.name,
        parade_name=parade.name,
        setting=params.setting,
        arc=arc,
        opening_variant=seed % len(OPENINGS),
        problem=_fill(arc.problem, {"sailor_name": sailor.name, "infantry_name": infantry.name, "parade_name": parade.name, "setting": params.setting}),
        twist_line=_fill(arc.twist, {"sailor_name": sailor.name, "infantry_name": infantry.name, "parade_name": parade.name, "setting": params.setting}),
        action_line=_fill(arc.action, {"sailor_name": sailor.name, "infantry_name": infantry.name, "parade_name": parade.name, "setting": params.setting}),
        result_line=_fill(arc.result, {"sailor_name": sailor.name, "infantry_name": infantry.name, "parade_name": parade.name, "setting": params.setting}),
        ending_image=_fill(arc.ending, {"sailor_name": sailor.name, "infantry_name": infantry.name, "parade_name": parade.name, "setting": params.setting}),
        theme= "heartwarming parade twist",
    )
    story = "\n\n".join(_story_lines(world))
    prompts = [
        f"Write a heartwarming story about {params.parade_name}, a sailor, and infantry in {params.setting}.",
        "Include a twist that changes the parade for the better.",
        "Make the story child-facing with a short spoken exchange.",
    ]
    story_qa = [
        QAItem(
            question=f"What problem did {params.parade_name} face at the start of \"{arc.title}\"?",
            answer=arc.problem_answer,
        ),
        QAItem(
            question="What was the twist in the story?",
            answer=arc.twist_answer,
        ),
        QAItem(
            question="How did the ending change because of the characters' choices?",
            answer=arc.result_answer,
        ),
        QAItem(
            question=f"What image closes the story?",
            answer=f"It ends with {world.facts['ending_image']}.",
        ),
    ]
    world_qa = [
        QAItem(question="What is a parade?", answer="A parade is a cheerful line of people moving together, often with music and flags."),
        QAItem(question="Who is a sailor?", answer="A sailor is a person who works on boats or ships and knows the sea."),
        QAItem(question="What is infantry?", answer="Infantry are soldiers who march and travel on foot."),
        QAItem(question="What is a twist in a story?", answer="A twist is a surprise turn that changes what the characters do or understand."),
        QAItem(question="What makes a story heartwarming?", answer="A heartwarming story leaves you feeling caring, hopeful, and happy for the characters."),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world trace ---")
        for e in sample.world.entities.values():
            print(f"{e.name}: kind={e.kind}, meters={dict(e.meters)}, memes={dict(e.memes)}")
    if qa:
        print()
        print("== prompts ==")
        for p in sample.prompts:
            print(p)
        print()
        print("== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def _valid_python() -> list[str]:
    return sorted(s.replace(" ", "_") for s in SETTING_REGISTRY)


def _asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show can_tell_story/1."))
    return sorted(set(asp.atoms(model, "can_tell_story")))


def asp_verify() -> int:
    py = {(s,) for s in _valid_python()}
    cl = set(_asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches python ({len(py)} settings).")
        return 0
    print("MISMATCH between clingo and python:")
    print("python only:", sorted(py - cl))
    print("clingo only:", sorted(cl - py))
    return 1


def build_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show can_tell_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for item in _asp_valid():
            print(item[0])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for parade_name in PARADE_REGISTRY:
            params = StoryParams(parade_name=parade_name, sailor_name="Mina", infantry_name="Captain Reed", setting="harbor square")
            samples.append(generate(params))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = build_story_params(args, rng)
            except StoryError as err:
                print(err)
                return
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

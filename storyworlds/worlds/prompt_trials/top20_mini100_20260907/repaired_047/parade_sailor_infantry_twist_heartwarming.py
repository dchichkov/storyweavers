#!/usr/bin/env python3
"""
A heartwarming small storyworld about a parade with a sailor and infantry,
with a gentle twist and a warm ending.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

STORYWORLDS_ROOT = Path(__file__).resolve().parents[3]
if str(STORYWORLDS_ROOT) not in sys.path:
    sys.path.insert(0, str(STORYWORLDS_ROOT))

from results import QAItem, StoryError, StorySample  # noqa: E402

ASP_RULES = r"""
% A heartwarming parade story is reasonable when the twist is kind and the ending is warm.
parade_story(S) :- setting(S), has_twist(S), heartwarming(S).
good_parade(S) :- parade_story(S), shared_kindness(S), resolved(S).
safe_choice(C) :- choice(C), not risky(C).
"""

SETTING = "parade route"


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def bump_meter(self, key: str, amount: float = 1.0) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amount

    def bump_meme(self, key: str, amount: float = 1.0) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount


@dataclass
class StoryParams:
    name: str
    sailor_name: str
    infantry_name: str
    parade_item: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Scenario:
    key: str
    premise: str
    trouble: str
    failed_try: str
    clue: str
    sailor_line: str
    infantry_line: str
    repair: str
    result: str
    ending_image: str
    lesson: str


@dataclass
class World:
    setting: str = SETTING
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        for e in self.entities.values():
            bits = []
            if e.meters:
                bits.append(f"meters={dict(e.meters)}")
            if e.memes:
                bits.append(f"memes={dict(e.memes)}")
            if e.label:
                bits.append(f"label={e.label!r}")
            lines.append(f"  {e.id:10} ({e.kind:10}) {' '.join(bits)}")
        lines.append(f"  facts: {self.facts}")
        return "\n".join(lines)


def reasonableness_gate(params: StoryParams) -> None:
    if not params.name.strip():
        raise StoryError("A child-friendly parade story needs a name for the first character.")
    if not params.sailor_name.strip():
        raise StoryError("The sailor needs a name so the parade feels like a real visit.")
    if not params.infantry_name.strip():
        raise StoryError("The infantry character needs a name so the dialogue can matter.")
    if params.parade_item not in {"banner", "drum", "flag", "ribbon", "lantern"}:
        raise StoryError("The parade item must be something safe and festive.")
    if params.name == params.sailor_name == params.infantry_name:
        raise StoryError("The characters should not all be the same person.")
    if params.name.lower() in {"sailor", "infantry"}:
        raise StoryError("The main character name should be a person, not a role.")
    if params.sailor_name.lower() in {"sailor", "infantry"} or params.infantry_name.lower() in {"sailor", "infantry"}:
        raise StoryError("Character names should not be just the role words.")


def asp_facts() -> str:
    import asp

    lines = [
        asp.fact("setting", "parade_route"),
        asp.fact("has_twist", "parade_route"),
        asp.fact("heartwarming", "parade_route"),
        asp.fact("shared_kindness", "parade_route"),
        asp.fact("resolved", "parade_route"),
        asp.fact("choice", "slow_step"),
        asp.fact("choice", "shared_banner"),
        asp.fact("choice", "gentle_signal"),
        asp.fact("safe_choice", "slow_step"),
        asp.fact("safe_choice", "shared_banner"),
        asp.fact("safe_choice", "gentle_signal"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


NAMES = ["Mara", "Evan", "Tia", "Noah", "Lina", "Owen", "Pia", "Jules"]
SAILORS = ["Captain Reed", "Nia", "Bo", "Soren", "Mabel", "Kai"]
INFANTRY = ["Sergeant June", "Rafi", "Hale", "Mina", "Theo", "Luz"]
ITEMS = ["banner", "drum", "flag", "ribbon", "lantern"]

SCENARIOS = [
    Scenario(
        key="lost_score",
        premise="was helping the town line up for the parade",
        trouble="The march music stopped because the score pages had blown under a bench.",
        failed_try="hurrying after the pages only scattered them farther apart",
        clue="a row of muddy boot prints pointed toward the fountain",
        sailor_line='"I can follow the water-side clue," the sailor said.',
        infantry_line='"And I can keep the line calm until you return," the infantry friend replied.',
        repair="they followed the prints together, found the pages, and set the band back in order",
        result="The parade marched again, this time with a softer, steadier beat.",
        ending_image="the recovered pages rode safely on top of the drum while children clapped along",
        lesson="a calm helper can turn a loss into a shared rescue",
    ),
    Scenario(
        key="tilted_float",
        premise="was leading a bright parade float past the bakery",
        trouble="One wheel had sunk into a soft patch of mud, making the float lean toward the curb.",
        failed_try="pushing from one side made the lean worse",
        clue="the heavy side of the float held all the flower crates",
        sailor_line='"Let us balance the weight instead of fighting it," the sailor suggested.',
        infantry_line='"I will guard the crowd while we move the crates," said the infantry friend.',
        repair="they moved the flower crates to the other side and slipped boards under the wheel",
        result="The float rolled straight, and the flowers stayed smiling in their baskets.",
        ending_image="the lantern on the float swayed once, then shone straight down the parade road",
        lesson="the kindest fix is often the one that restores balance",
    ),
    Scenario(
        key="shy_child",
        premise="was walking beside the parade to wave at the children",
        trouble="A small child near the curb hid behind a scarf and would not wave back.",
        failed_try="calling out too brightly made the child shrink farther away",
        clue="the child's eyes kept returning to the sailor's little shell charm",
        sailor_line='"You may wave when you feel ready," the sailor said softly.',
        infantry_line='"We can make room for you beside us," the infantry friend offered.',
        repair="they slowed the march, knelt near the curb, and let the child touch the shell charm",
        result="The child smiled, waved once, and then walked a few brave steps with the parade.",
        ending_image="the tiny wave from the curb became the brightest part of the whole street",
        lesson="gentleness invites courage better than pressure does",
    ),
    Scenario(
        key="missing_bells",
        premise="was carrying a parade banner down the avenue",
        trouble="The bell ties on the banner had come loose, and the cloth fluttered sideways.",
        failed_try="pulling the knot tight only twisted the ribbon into a mess",
        clue="the loose ends had crossed into a neat sailor's knot",
        sailor_line='"That knot likes two careful hands," the sailor laughed.',
        infantry_line='"I can hold the banner still while you tie it," said the infantry friend.',
        repair="they held the pole steady, tied a fresh knot, and tested it with one gentle tug",
        result="The banner stood tall again and did not whip the marchers in the face.",
        ending_image="the repaired ribbon fluttered above the parade like a cheerful red bird",
        lesson="a good team can hold stillness together until a problem is solved",
    ),
    Scenario(
        key="rain_spots",
        premise="was escorting the parade past the market stalls",
        trouble="A small rain cloud sprinkled the drum cover, leaving dark spots on the cloth.",
        failed_try="wiping the cover too hard only spread the damp",
        clue="the covered side stayed dry under the folded market awning",
        sailor_line='"We should move the drums under cover first," the sailor said.',
        infantry_line='"Then I will signal the marchers to slow," the infantry friend answered.',
        repair="they shifted the drums beneath the awning and waited out the last sprinkle together",
        result="The rain passed, and the parade continued with dry drums and happy feet.",
        ending_image="a bead of water slid off the awning while the drum cover dried in the sun",
        lesson="protecting what is shared can be just as important as marching on",
    ),
    Scenario(
        key="lost_hat",
        premise="was keeping time near the front of the parade",
        trouble="The sailor's hat blew into a hedge and the sailor lost their smile.",
        failed_try="grabbing blindly in the branches only shook the leaves loose",
        clue="the hat ribbon was caught on one bright thorn",
        sailor_line='"I can see the ribbon from here," the sailor said, sounding relieved.',
        infantry_line='"I will part the branches gently so no one gets scratched," said the infantry friend.',
        repair="they opened the hedge carefully, freed the ribbon, and brushed off the hat",
        result="The sailor put the hat back on and laughed as the parade passed by.",
        ending_image="the rescued hat tipped once in the breeze like a grateful bow",
        lesson="careful hands can solve what hurried hands cannot",
    ),
    Scenario(
        key="dropped_snack",
        premise="was marching beside a line of cheering neighbors",
        trouble="A basket of parade snacks tipped, and the apples rolled toward the gutter.",
        failed_try="chasing the apples with quick steps sent them farther apart",
        clue="the gutter edge dipped toward a waiting crate by the curb",
        sailor_line='"We can guide them with the crate," the sailor said.',
        infantry_line='"And I will keep the lane clear," the infantry friend added.',
        repair="they set the crate as a soft barrier and rolled the apples back one by one",
        result="The snacks were saved, and the neighbors laughed with relief instead of worry.",
        ending_image="one shiny apple sat safely in the basket again, glowing like a tiny sunset",
        lesson="small troubles can be sweetly solved when everyone helps",
    ),
    Scenario(
        key="too_fast",
        premise="was leading the parade drum line around the square",
        trouble="The youngest marchers started hurrying and could not keep the beat.",
        failed_try="shouting the count made them even more rushed",
        clue="the drummer's foot tapped best when the steps got shorter, not louder",
        sailor_line='"Let us show the beat with our feet," the sailor suggested.',
        infantry_line='"I will march beside the smallest ones," the infantry friend said.',
        repair="they slowed the rhythm, matched the steps to the drum, and marched side by side",
        result="The little marchers found the beat and grinned all the way around the square.",
        ending_image="the line of tiny boots landed together like raindrops on a tin roof",
        lesson="a gentle pace can help everyone join in",
    ),
]

OPENINGS = [
    "The parade route glittered with bunting when {name} arrived holding a {item}.",
    "On a bright afternoon, {name} stepped into the parade with a careful smile and a {item}.",
    "Music and laughter floated down the street as {name} joined the parade at the corner.",
    "The town was ready for a parade, and {name} had one useful {item} to carry.",
    "Just as the bells began, {name} spotted the sailor and the infantry friend near the march line.",
    "Flags snapped softly overhead when {name} hurried to the parade and found a small problem waiting.",
]

REACTIONS = [
    "{name} did not panic; instead, {name} listened for what the crowd needed.",
    '"We can solve this together," {name} said, which helped everyone breathe again.',
    "For a moment {name} felt stuck, but the sailor's calm voice changed the mood.",
    '"A twist like this needs patient hands," {name} decided.',
    "Rather than rush, {name} asked the two friends what they had already noticed.",
    "{name} kept the parade kind by slowing the moment down.",
]

PLANS = [
    "The three of them chose the smallest safe fix and tried it first.",
    "They divided the work so no one person had to carry the whole worry.",
    "They checked the clue again before moving a single thing.",
    "They made a little circle in the street and spoke quietly about the next step.",
    "They agreed to protect the parade flow while they solved the problem.",
]

ACTIONS = {
    "banner": "held the banner steady while the sailor tied a new knot",
    "drum": "lifted the drum cover and kept the beat low enough for careful work",
    "flag": "raised the flag high enough to stay clear of the trouble",
    "ribbon": "gathered the ribbon ends and tucked them into a neat sailor's knot",
    "lantern": "moved the lantern to a safer place so everyone could see the clue",
}


def valid_choices() -> list[str]:
    return ITEMS


def valid_params(rng: random.Random) -> StoryParams:
    return StoryParams(
        name=rng.choice(NAMES),
        sailor_name=rng.choice(SAILORS),
        infantry_name=rng.choice(INFANTRY),
        parade_item=rng.choice(ITEMS),
        seed=rng.randrange(2**31),
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming parade storyworld.")
    ap.add_argument("--name")
    ap.add_argument("--sailor-name")
    ap.add_argument("--infantry-name")
    ap.add_argument("--parade-item", choices=valid_choices())
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
    params = valid_params(rng)
    if args.name:
        params.name = args.name
    if args.sailor_name:
        params.sailor_name = args.sailor_name
    if args.infantry_name:
        params.infantry_name = args.infantry_name
    if args.parade_item:
        params.parade_item = args.parade_item
    reasonableness_gate(params)
    return params


def build_world(params: StoryParams) -> World:
    world = World()
    world.add(Entity(id="hero", kind="character", label=params.name))
    world.add(Entity(id="sailor", kind="character", label=params.sailor_name))
    world.add(Entity(id="infantry", kind="character", label=params.infantry_name))
    world.add(Entity(id="item", kind="thing", label=params.parade_item))
    world.facts.update(
        setting=SETTING,
        has_twist=True,
        heartwarming=True,
        shared_kindness=True,
        resolved=False,
    )
    return world


def tell_story(world: World, params: StoryParams) -> None:
    hero = world.get("hero")
    sailor = world.get("sailor")
    infantry = world.get("infantry")
    item = world.get("item")

    rng = random.Random(params.seed if params.seed is not None else 0)
    scenario = rng.choice(SCENARIOS)
    opening = rng.choice(OPENINGS).format(name=hero.label, item=item.label)
    reaction = rng.choice(REACTIONS).format(name=hero.label)
    plan = rng.choice(PLANS)
    action = ACTIONS[item.label]

    hero.bump_meme("care")
    sailor.bump_meme("calm")
    infantry.bump_meme("helpfulness")

    world.say(opening)
    world.say(f"{hero.label} was {scenario.premise}.")
    world.say(
        f"Then the twist appeared: {scenario.trouble} {scenario.failed_try.capitalize()}."
    )
    world.say(reaction)
    world.para()

    world.say(scenario.clue.capitalize() + ".")
    world.say(scenario.sailor_line)
    world.say(scenario.infantry_line)
    world.say(plan)
    world.para()

    hero.bump_meter("attention", 1)
    sailor.bump_meter("steadiness", 1)
    infantry.bump_meter("support", 1)

    world.say(f"Together, {hero.label} {action}.")
    world.say(scenario.repair.capitalize() + ".")
    world.say(scenario.result)
    world.para()

    hero.bump_meme("joy")
    sailor.bump_meme("joy")
    infantry.bump_meme("joy")

    world.say(
        f"{hero.label} smiled at the sailor and the infantry friend, and they all laughed softly."
    )
    world.say(f"They agreed that {scenario.lesson}.")
    world.say(
        f"When the parade reached the last corner, everything felt warm and right; {scenario.ending_image}."
    )

    world.facts.update(
        twist=scenario.key,
        resolved=True,
        lesson=scenario.lesson,
        ending_image=scenario.ending_image,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"].label
    sailor = f["sailor"].label
    infantry = f["infantry"].label
    item = f["item"].label
    twist = str(f["twist"]).replace("_", " ")
    return [
        f"Write a heartwarming story set on a parade route where {hero}, {sailor}, and {infantry} solve a {twist} problem.",
        f"Tell a child-friendly parade story using the words parade, sailor, infantry, and twist.",
        f"Write a warm story about a {item} helping friends fix a parade problem together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"].label
    sailor = f["sailor"].label
    infantry = f["infantry"].label
    item = f["item"].label
    return [
        QAItem(
            question="What was the main problem in the parade?",
            answer=f"{f['twist'].replace('_', ' ')}.",
        ),
        QAItem(
            question=f"What did {sailor} and {infantry} say that helped the plan?",
            answer="They suggested a calm, shared plan and offered to help in the parade.",
        ),
        QAItem(
            question=f"What did {hero} do with the {item}?",
            answer=f"{hero} used the {item} to help solve the problem safely.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"The parade continued happily, and {f['ending_image']}.",
        ),
        QAItem(
            question="What made the ending heartwarming?",
            answer="The friends listened to each other, worked together, and turned the problem into a kind rescue.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a parade?",
            answer="A parade is a happy event where people move together in a line, often with music and colorful things to see.",
        ),
        QAItem(
            question="Who is a sailor?",
            answer="A sailor is a person who works on boats or ships and often knows how to stay calm and steady.",
        ),
        QAItem(
            question="What is infantry?",
            answer="Infantry are soldiers who move and work on foot, often helping keep order and supporting others.",
        ),
        QAItem(
            question="What does twist mean in a story?",
            answer="A twist is a surprising change that makes the story go in a new direction.",
        ),
    ]


def dump_trace(world: World) -> str:
    return world.trace()


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def asp_verify() -> int:
    import asp

    program = asp_program("#show parade_story/1.\n#show good_parade/1.\n#show safe_choice/1.")
    model = asp.one_model(program)
    atoms = {(sym.name, tuple(arg.name if arg.type != 3 else arg.string for arg in sym.arguments)) for sym in model}
    expected = {
        ("parade_story", ("parade_route",)),
        ("good_parade", ("parade_route",)),
        ("safe_choice", ("slow_step",)),
        ("safe_choice", ("shared_banner",)),
        ("safe_choice", ("gentle_signal",)),
    }
    if atoms == expected:
        print("OK: ASP twin matches the Python reasonableness gate.")
        return 0
    print("MISMATCH between ASP and Python gate.")
    print("ASP:", sorted(atoms))
    print("PY :", sorted(expected))
    return 1


def asp_list() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show good_parade/1."))
    return sorted(set(asp.atoms(model, "good_parade")))


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = build_world(params)
    tell_story(world, params)
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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(name="Mara", sailor_name="Captain Reed", infantry_name="Sergeant June", parade_item="banner", seed=11),
    StoryParams(name="Lina", sailor_name="Nia", infantry_name="Hale", parade_item="drum", seed=29),
    StoryParams(name="Evan", sailor_name="Kai", infantry_name="Luz", parade_item="ribbon", seed=47),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_parade/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP-compatible parade stories:")
        for item in asp_list():
            print(item)
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        tries = 0
        while len(samples) < args.n and tries < max(50, args.n * 50):
            params = resolve_params(args, random.Random(rng.randrange(2**31)))
            sample = generate(params)
            if sample.story in seen:
                tries += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            tries += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

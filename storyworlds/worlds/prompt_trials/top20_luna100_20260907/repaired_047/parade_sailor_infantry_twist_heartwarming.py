#!/usr/bin/env python3
"""
A standalone heartwarming storyworld about a parade, a sailor, and infantry.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

STORYWORLDS_ROOT = Path(__file__).resolve().parents[2]
if str(STORYWORLDS_ROOT) not in sys.path:
    sys.path.insert(0, str(STORYWORLDS_ROOT))

from results import QAItem, StoryError, StorySample  # noqa: E402


ASP_RULES = r"""
parade_story(S) :- setting(S), has_twist(S), has_warm_ending(S).
useful_helper(H) :- helper(H), gentle(H).
good_turn(S) :- parade_story(S), shared_memory(S).
"""


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
    sailor: str
    infantry_friend: str
    keepsake: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Scenario:
    key: str
    premise: str
    trouble: str
    wrong_guess: str
    clue: str
    sailor_line: str
    twist: str
    repair: str
    result: str
    ending: str


@dataclass
class World:
    place: str = "town parade street"
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

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
        for entity in self.entities.values():
            bits = []
            if entity.meters:
                bits.append(f"meters={dict(entity.meters)}")
            if entity.memes:
                bits.append(f"memes={dict(entity.memes)}")
            if entity.label:
                bits.append(f"label={entity.label!r}")
            lines.append(f"  {entity.id:14} ({entity.kind:10}) {' '.join(bits)}")
        lines.append(f"  facts: {self.facts}")
        return "\n".join(lines)


NAMES = ["Luna", "Mara", "Theo", "Iris", "Jonah", "Nell", "Pia", "Sam"]
SAILORS = ["Captain Bell", "Sailor June", "Sailor Mateo", "Sailor Rose", "Sailor Finn"]
INFANTRY = ["Corporal Reed", "Private Ada", "Sergeant Moss", "Private Noor", "Corporal Lee"]
KEEPSAKES = ["brass button", "blue ribbon", "wooden whistle", "little compass"]

SCENARIOS = [
    Scenario(
        key="silent_drum",
        premise="was helping arrange the town parade before the first drumbeat",
        trouble="The infantry band's drum would not make a sound, so the marchers could not find their pace.",
        wrong_guess="tightening the drum cord only made the skin sag on one side",
        clue="a tiny paper star was caught beneath the drum's rim",
        sailor_line='"That star is from our welcome banner," the sailor said. "Perhaps the drum is holding a message."',
        twist="When they lifted the rim, they found not a broken drum but a note from a child who had once marched beside the infantry.",
        repair="freed the paper star, read the note aloud, and tapped a gentle rhythm while the infantry listened",
        result="The drum answered with a warm heartbeat, and every marcher found the same steady step.",
        ending="At the end of the parade, the sailor tucked the note beside the drum so its kindness could march again.",
    ),
    Scenario(
        key="backward_banner",
        premise="was carrying the parade banner toward the waiting sailors and infantry",
        trouble="The banner kept twisting backward, hiding the town's bright picture from the people along the street.",
        wrong_guess="pulling harder made the cloth knot around the pole",
        clue="the old corner seam had been sewn with a different colored thread",
        sailor_line='"My grandmother stitched that seam," the sailor said. "She always hid a surprise in her work."',
        twist="Inside the folded seam was a second picture: a small homecoming boat painted for families who were waiting at the harbor.",
        repair="unwound the cloth gently, turned the hidden picture outward, and tied the pole with a soft loop",
        result="The banner showed both the parade and the waiting homes, so the crowd cheered twice.",
        ending="The sailor touched the hidden boat, and an infantry friend beside him smiled at someone waving from the curb.",
    ),
    Scenario(
        key="missing_step",
        premise="was practicing the parade's careful steps with the infantry",
        trouble="One marcher kept stopping just before the corner, making the line bend like a crooked ribbon.",
        wrong_guess="calling the step louder only made the marcher look more worried",
        clue="the marcher was watching a little red house instead of the drum",
        sailor_line='"Maybe the corner means something to him," the sailor whispered.',
        twist="The house belonged to the marcher's family, who had made a welcome sign but were too shy to hold it high.",
        repair="slowed the march, invited the family to wave, and let the marcher choose when to take the corner",
        result="The line turned smoothly, and the family lifted their sign with shining eyes.",
        ending="The sailor and infantry marched on while the red house glowed behind them like a small lantern.",
    ),
    Scenario(
        key="rainy_medal",
        premise="was polishing a parade medal for an infantry veteran who would ride near the sailors",
        trouble="Rain blurred the medal's picture just before the ceremony began.",
        wrong_guess="rubbing the wet metal with a rough sleeve made the picture fainter",
        clue="the medal's back held a smooth glass cover beneath the muddy clasp",
        sailor_line='"A medal remembers best when we care for it slowly," the sailor said.',
        twist="Behind the cover was a tiny drawing made by the veteran's granddaughter, not a military mark at all.",
        repair="opened the clasp carefully, dried the drawing, and placed it behind the medal where everyone could see it",
        result="The crowd learned that the veteran carried a child's love beside every brave memory.",
        ending="The medal shone in the rain, and the veteran held the sailor's hand before the parade moved on.",
    ),
    Scenario(
        key="empty_chair",
        premise="was setting chairs along the parade route for families and marching guests",
        trouble="One empty chair stood beneath a yellow scarf, and nobody knew why it had been saved.",
        wrong_guess="moving it to the end of the row left the scarf trailing in a puddle",
        clue="the chair's wooden arm had a name carved into it",
        sailor_line='"We should wait for the person whose name is here," the sailor said.',
        twist="The chair had been placed for an infantry nurse who could no longer walk far, and the whole neighborhood had planned to greet her.",
        repair="dried the scarf, returned the chair to the front, and helped make a clear path from the doorway",
        result="The nurse arrived just as the parade turned the corner and saw every face waiting for her.",
        ending="The yellow scarf rested across her knees while sailors and infantry saluted with gentle smiles.",
    ),
    Scenario(
        key="lost_whistle",
        premise="was helping a young sailor lead the parade's quiet signal game",
        trouble="The sailor's whistle disappeared, and the children could not tell when to wave.",
        wrong_guess="searching only beneath the reviewing stand overlooked the breeze-blown grass",
        clue="a row of silver buttons pointed from the stand toward the old fountain",
        sailor_line='"Those buttons came from my parade coat," the sailor said. "They may know the way."',
        twist="The whistle had been carried to the fountain by a child who wanted to return it but was afraid to interrupt.",
        repair="thanked the child, let her blow the first signal, and placed the whistle on its bright cord",
        result="The children waved together, and the shy child led the next cheer.",
        ending="The sailor's whistle gleamed beside the child's smile as the parade filled the square with waving hands.",
    ),
    Scenario(
        key="tangled_medley",
        premise="was arranging music cards for the sailors and infantry before the parade concert",
        trouble="The cards had mixed together, so the musicians could not tell which tune welcomed which group.",
        wrong_guess="sorting them only by color placed two quiet songs beside the loudest march",
        clue="each card carried a tiny picture of someone the tune was meant to honor",
        sailor_line='"The pictures matter more than the colors," the sailor said. "Let us listen with our eyes."',
        twist="The quiet song was for families waiting at home, and it belonged in the middle of the bold march.",
        repair="matched the cards to their pictures, practiced the change, and left the quiet song where hearts could hear it",
        result="The concert began bravely, softened for the home song, and ended with everyone humming.",
        ending="Even the infantry boots grew still during the gentle middle tune.",
    ),
    Scenario(
        key="smallest_flag",
        premise="was choosing flags for the front of the parade",
        trouble="The smallest flag kept falling below the others whenever the wind rose.",
        wrong_guess="tying it tighter bent its thin pole",
        clue="the flag was made from a child's old blue blanket",
        sailor_line='"It may be small because it was made for someone small," the sailor said.',
        twist="The flag had belonged to the youngest child who once watched the infantry march from a hospital window.",
        repair="gave it a shorter pole, stitched its loose edge, and placed it where children could see",
        result="The little flag flew proudly at the front, where it became the first one many children waved back to.",
        ending="The sailor bowed to the blue blanket flag, and the infantry answered with a bright salute.",
    ),
]


OPENINGS = [
    "Morning bells rang over the square when {name} arrived for the parade.",
    "The town street smelled of warm bread and rain as {name} joined the parade preparations.",
    "Before the first band played, {name} found the parade route glowing with paper flags.",
    "A silver cloud drifted above the square when {name} came to welcome the sailors and infantry.",
    "The parade was nearly ready, but one small mystery waited beside the reviewing stand.",
    "Children lined the curb as {name} carried a careful heart into the busy parade morning.",
]

PLANS = [
    "They agreed to slow down and examine the problem together.",
    "They made room for every helper, because a parade belongs to the whole town.",
    "They checked the fragile things first and chose the gentlest useful action.",
    "They followed the clue instead of blaming the object that seemed troublesome.",
    "They listened once, looked twice, and then tried the smallest repair.",
    "They divided the work so nobody had to carry the worry alone.",
]

REACTIONS = [
    "{name} wanted to hurry, but the sailor's patient face made a slower choice seem wiser.",
    '"A parade should carry people with it, not leave anyone behind," {name} said.',
    "{name} knelt beside the trouble and asked what the smallest clue might mean.",
    '"Let us find the story inside the problem," {name} suggested.',
    "The infantry friend took a careful breath, and {name} followed it.",
    "{name} noticed that the worried object needed listening before it needed fixing.",
]

HELP_ACTIONS = {
    "brass button": "used the button to hold a loose strap safely out of the way",
    "blue ribbon": "tied the ribbon around the repaired piece so it would not slip again",
    "wooden whistle": "used the whistle to call the nearby helpers without startling anyone",
    "little compass": "followed the compass toward the clue and back to the parade route",
}


def reasonableness_gate(params: StoryParams) -> None:
    if not params.name.strip():
        raise StoryError("The parade helper needs a name.")
    if params.sailor not in SAILORS:
        raise StoryError("The sailor must be chosen from the town's welcoming crew.")
    if params.infantry_friend not in INFANTRY:
        raise StoryError("The infantry friend must be chosen from the marching group.")
    if params.keepsake not in KEEPSAKES:
        raise StoryError("The keepsake must be a small, gentle parade object.")


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("setting", "parade"),
            asp.fact("has_twist", "parade"),
            asp.fact("has_warm_ending", "parade"),
            asp.fact("shared_memory", "parade"),
            asp.fact("helper", "ribbon"),
            asp.fact("helper", "button"),
            asp.fact("helper", "whistle"),
            asp.fact("helper", "compass"),
            asp.fact("gentle", "ribbon"),
            asp.fact("gentle", "button"),
            asp.fact("gentle", "whistle"),
            asp.fact("gentle", "compass"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_keepsakes() -> list[str]:
    return list(KEEPSAKES)


def valid_params(rng: random.Random) -> StoryParams:
    return StoryParams(
        name=rng.choice(NAMES),
        sailor=rng.choice(SAILORS),
        infantry_friend=rng.choice(INFANTRY),
        keepsake=rng.choice(KEEPSAKES),
        seed=rng.randrange(2**31),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Heartwarming parade storyworld.")
    parser.add_argument("--name")
    parser.add_argument("--sailor")
    parser.add_argument("--infantry-friend")
    parser.add_argument("--keepsake", choices=valid_keepsakes())
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
    params = valid_params(rng)
    if args.name:
        params.name = args.name
    if args.sailor:
        params.sailor = args.sailor
    if args.infantry_friend:
        params.infantry_friend = args.infantry_friend
    if args.keepsake:
        params.keepsake = args.keepsake
    reasonableness_gate(params)
    return params


def build_world(params: StoryParams) -> World:
    world = World()
    world.add(Entity(id="hero", kind="child", label=params.name))
    world.add(Entity(id="sailor", kind="sailor", label=params.sailor))
    world.add(Entity(id="infantry", kind="infantry", label=params.infantry_friend))
    world.add(Entity(id="keepsake", kind="object", label=params.keepsake))
    world.facts.update(
        hero=world.get("hero"),
        sailor=world.get("sailor"),
        infantry=world.get("infantry"),
        keepsake=world.get("keepsake"),
        setting="parade",
        twist=True,
        warm_ending=True,
    )
    return world


def tell_story(world: World, params: StoryParams) -> None:
    rng = random.Random(params.seed if params.seed is not None else 0)
    scenario = rng.choice(SCENARIOS)
    hero = world.get("hero")
    sailor = world.get("sailor")
    infantry = world.get("infantry")
    keepsake = world.get("keepsake")

    hero.bump_meme("care")
    sailor.bump_meme("welcome")
    infantry.bump_meme("memory")

    opening = rng.choice(OPENINGS).format(name=hero.label)
    reaction = rng.choice(REACTIONS).format(name=hero.label)
    plan = rng.choice(PLANS)
    action = HELP_ACTIONS[keepsake.label]

    world.say(opening)
    world.say(
        f"{hero.label} greeted {sailor.label} and {infantry.label}, then helped them prepare "
        f"the route where families would watch the parade."
    )
    world.para()

    world.say(scenario.premise.capitalize() + ".")
    world.say(scenario.trouble)
    world.say(f"At first, {hero.label} guessed that {scenario.wrong_guess}.")
    world.say(reaction)
    world.para()

    world.say(f"Then they noticed that {scenario.clue}.")
    world.say(scenario.sailor_line)
    world.say(plan)
    world.para()

    world.bump_meter("careful_work", 1)
    world.say(f"{hero.label} brought the {keepsake.label} and {action}.")
    world.say(f"Together, the friends {scenario.repair}.")
    world.say(f"That was the twist: {scenario.twist}")
    world.say(scenario.result)
    world.para()

    hero.bump_meme("joy")
    sailor.bump_meme("gratitude")
    infantry.bump_meme("belonging")
    world.say(
        f"{sailor.label} thanked {hero.label}, and {infantry.label} said, "
        f'"You helped us remember who this parade is for."'
    )
    world.say(scenario.ending)

    world.facts.update(
        scenario=scenario.key,
        premise=scenario.premise,
        trouble=scenario.trouble,
        wrong_guess=scenario.wrong_guess,
        clue=scenario.clue,
        sailor_line=scenario.sailor_line,
        twist=scenario.twist,
        repair=scenario.repair,
        result=scenario.result,
        ending=scenario.ending,
        helper_action=action,
        resolved=True,
    )


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    return [
        f"Write a heartwarming story about {facts['hero'].label}, a sailor, and infantry preparing a parade.",
        f"Tell a child-friendly parade story with a surprising twist: {facts['twist']}.",
        f"Write a gentle story in which a {facts['keepsake'].label} helps solve a parade problem and brings people together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    hero = facts["hero"].label
    sailor = facts["sailor"].label
    infantry = facts["infantry"].label
    keepsake = facts["keepsake"].label
    return [
        QAItem(
            question="What problem interrupted the parade preparations?",
            answer=str(facts["trouble"]),
        ),
        QAItem(
            question=f"What clue did {hero}, {sailor}, and {infantry} notice?",
            answer=f"They noticed that {facts['clue']}.",
        ),
        QAItem(
            question=f"How did the {keepsake} help?",
            answer=f"{hero} {facts['helper_action']}, and the friends completed the repair together.",
        ),
        QAItem(
            question="What was the surprising twist?",
            answer=str(facts["twist"]),
        ),
        QAItem(
            question="How did the story end?",
            answer=str(facts["ending"]),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a parade?",
            answer="A parade is an organized procession where people walk, ride, play music, or carry signs for others to enjoy.",
        ),
        QAItem(
            question="What does sailor mean?",
            answer="A sailor is a person who works or travels on a boat or ship.",
        ),
        QAItem(
            question="What is infantry?",
            answer="Infantry are soldiers who serve and move on foot.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is an unexpected change or discovery that makes the story mean something new.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
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


def asp_verify() -> int:
    import asp

    program = asp_program("#show parade_story/1.\n#show useful_helper/1.\n#show good_turn/1.")
    model = asp.one_model(program)
    actual = {
        (
            symbol.name,
            tuple(
                arg.string
                if arg.type.name == "String"
                else arg.name
                if arg.type.name == "Function"
                else str(arg.number)
                for arg in symbol.arguments
            ),
        )
        for symbol in model
        if symbol.name in {"parade_story", "useful_helper", "good_turn"}
    }
    expected = {
        ("parade_story", ("parade",)),
        ("good_turn", ("parade",)),
        ("useful_helper", ("ribbon",)),
        ("useful_helper", ("button",)),
        ("useful_helper", ("whistle",)),
        ("useful_helper", ("compass",)),
    }
    if actual == expected:
        print("OK: ASP twin matches the Python story gate.")
        return 0
    print("MISMATCH between ASP and Python gate.")
    print("ASP:", sorted(actual))
    print("PY :", sorted(expected))
    return 1


def asp_list() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show good_turn/1."))
    return sorted(asp.atoms(model, "good_turn"))


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
        print(sample.world.trace())
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams("Luna", "Sailor June", "Corporal Reed", "blue ribbon", 17),
    StoryParams("Mara", "Captain Bell", "Private Ada", "brass button", 31),
    StoryParams("Theo", "Sailor Mateo", "Sergeant Moss", "little compass", 53),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show parade_story/1.\n#show useful_helper/1.\n#show good_turn/1."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        print("ASP-compatible parade stories:")
        for item in asp_list():
            print(item)
        return

    rng = random.Random(
        args.seed if args.seed is not None else random.randrange(2**31)
    )
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < max(0, args.n) and attempts < max(50, args.n * 50):
            params = resolve_params(args, random.Random(rng.randrange(2**31)))
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            attempts += 1

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

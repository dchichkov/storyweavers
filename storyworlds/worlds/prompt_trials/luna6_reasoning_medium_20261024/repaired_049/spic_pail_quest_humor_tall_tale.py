#!/usr/bin/env python3
"""
A tall-tale storyworld about a runaway pail, a tiny spice scoop, and a quest
that grows much larger than the people who set out on it.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

STORYWORLDS_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.insert(0, STORYWORLDS_ROOT)
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
class Setting:
    id: str
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class Quest:
    id: str
    title: str
    goal: str
    reward: str


@dataclass(frozen=True)
class Episode:
    opening: str
    trouble: str
    hasty_idea: str
    question: str
    reply: str
    clue: str
    action: str
    result: str
    village_rule: str
    ending: str
    joke: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple[str, str]] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


def meter(entity: Entity, key: str) -> float:
    return entity.meters.get(key, 0.0)


def meme(entity: Entity, key: str) -> float:
    return entity.memes.get(key, 0.0)


def add_meter(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.meters[key] = meter(entity, key) + amount


def add_meme(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.memes[key] = meme(entity, key) + amount


def propagate(world: World) -> None:
    hero = world.entities["hero"]
    companion = world.entities["companion"]
    pail = world.entities["pail"]

    if meter(hero, "observed") >= 1 and meme(hero, "worry") >= 1:
        sig = ("focus", hero.id)
        if sig not in world.fired:
            world.fired.add(sig)
            add_meme(hero, "focus")
            world.say("The worry in the hero's face gave way to a sharp, useful look.")

    if meter(hero, "shared_work") >= 1:
        sig = ("trust", companion.id)
        if sig not in world.fired:
            world.fired.add(sig)
            add_meme(companion, "trust")
            world.say("Working side by side, the two friends began to trust each other's ideas.")

    if meter(pail, "secured") >= 1 and meter(pail, "water_saved") >= 1:
        sig = ("quest_complete", pail.id)
        if sig not in world.fired:
            world.fired.add(sig)
            add_meme(hero, "pride")
            world.say("The quest was complete: the pail was safe, and its precious rainwater was still inside.")


SETTING_REGISTRY = {
    "fairground": Setting(
        id="fairground",
        place="the fairground at the edge of a thirsty little town",
        affords={"quest", "wind", "water", "neighbors"},
    )
}

QUEST_REGISTRY = {
    "pail_quest": Quest(
        id="pail_quest",
        title="the runaway-pail quest",
        goal="bring the town's great pail of rainwater home",
        reward="the first bowl of rainwater stew",
    )
}

EPISODES = [
    Episode(
        opening="On the morning of the town's dry-season fair, the biggest pail in the county began rolling uphill.",
        trouble="It held the last rainwater for miles, and a gust was pushing it toward a field of prickly thistles.",
        hasty_idea="The hero grabbed a rope and proposed pulling straight against the wind.",
        question="Should we pull harder, or find out what the wind is doing?",
        reply="Let's read it first. Even a giant pail has to follow the breeze.",
        clue="A pinch of pepper dust from the spic streamed downhill, showing that the thistle hollow was sheltered.",
        action="They ran around the hill, laid the rope across the sheltered side, and eased the pail into the hollow together",
        result="the pail stopped among the thistles without spilling a drop",
        village_rule="a pinch of spic dust should be used to check the wind before anyone hauls a heavy load",
        ending="That evening, the saved water made a little pot of stew, and the pail sat upside down as a roof for the town band.",
        joke="The band played so loudly that one thistle asked for an encore.",
    ),
    Episode(
        opening="At the fair, a pail so tall that geese nested in its shadow rolled away with a thunderous wobble.",
        trouble="The pail carried the town's only rainwater, and it was heading for the old wooden bridge.",
        hasty_idea="The hero planted both feet and tried to stop it with a heroic shout.",
        question="Can a shout tell us which way the breeze is pushing?",
        reply="No, but the spic can. Let's watch its pepper before we choose a side.",
        clue="Pepper from the spic curled toward the bridge, while a row of flags showed a calm path behind the mill.",
        action="They guided the pail around the mill and braced it with a soft haystack instead of sending it onto the bridge",
        result="the bridge stayed quiet, the haystack made a perfect cushion, and the water stayed in the pail",
        village_rule="wind flags and a spic pinch should be checked before a heavy pail is moved near the bridge",
        ending="The town shared its rainwater stew beneath the pail, which made a fine roof and an even finer echo chamber.",
        joke="The mayor's thank-you speech echoed back so many times that he thanked himself by accident.",
    ),
    Episode(
        opening="A pail large enough to bathe a pony rolled out of the fairground and chased a flock of very dignified chickens.",
        trouble="Inside sloshed the last rainwater in town, and the pail was aimed at a muddy orchard slope.",
        hasty_idea="The hero wanted to race the pail and jump into its open top.",
        question="What if the mud is carrying the pail faster than our legs can run?",
        reply="Then the spic will show us where the breeze is gentler. Let's stop guessing.",
        clue="The spic's pepper dust drifted toward a flat patch under the apple trees, away from the slick slope.",
        action="They asked the orchard keeper to lay down straw and then guided the pail onto the flat patch",
        result="the pail settled gently, the water stayed put, and the chickens marched past as if they had planned it",
        village_rule="a helper should check the ground and the wind before guiding a heavy pail downhill",
        ending="The saved water went into the town's stew, while the pail became a shady apple stall for the rest of the fair.",
        joke="The chickens charged one apple for admission, but forgot to say whether it was one apple per chicken or per customer.",
    ),
    Episode(
        opening="The town's enormous pail rolled off during the fair and sailed across a meadow as if it had learned to be a boat.",
        trouble="It still held the last rainwater, and a low stone wall waited at the far end of the meadow.",
        hasty_idea="The hero planned to chase it in a straight line and leap over the wall at the last moment.",
        question="Can we find a safer way than racing a pail that thinks it's a boat?",
        reply="We can test the breeze with the spic and take the dry path around the wall.",
        clue="A little pepper dust swirled back toward the dry path, where the ground rose gently and the wind weakened.",
        action="They carried the rope along the dry path and slowed the pail with a loop around a sturdy fence post",
        result="the pail came to rest before the wall, with all its water safely sloshing inside",
        village_rule="the safest route should be checked before a runaway load is chased",
        ending="At supper, the town ate rainwater stew beside the pail, now a moonlit seat for the fair's tired fiddler.",
        joke="The fiddler's first note made the pail hum, and the second made the mayor check whether it wanted a solo.",
    ),
    Episode(
        opening="One windy fair morning, the town's famous pail rolled away so fast that a wheelbarrow asked it to slow down.",
        trouble="It carried the last rainwater and was heading toward a line of washing hung across the lane.",
        hasty_idea="The hero grabbed the nearest sheet, hoping to use it as a sail in reverse.",
        question="Would a sheet help us, or might it give the wind an even bigger sail?",
        reply="Let's use a pinch from the spic to read the breeze before we add more cloth.",
        clue="The pepper drifted toward a sheltered gate, while the washing snapped like a row of tiny flags.",
        action="They opened the sheltered gate, cleared the lane, and guided the pail through with a rope",
        result="the washing stayed clean, the pail stayed upright, and the wheelbarrow got its lane back",
        village_rule="a spic pinch and a clear path should come before anyone adds a sail to a runaway pail",
        ending="The town's rainwater stew bubbled beside the pail, and the clean washing fluttered like banners over the feast.",
        joke="One sock claimed it had traveled more than the pail, but nobody could find its matching witness.",
    ),
    Episode(
        opening="At the fair, a pail as broad as a cottage door rolled away and startled a sleepy cow into standing up.",
        trouble="The pail held the last rainwater and was rumbling toward a patch of loose stones.",
        hasty_idea="The hero thought a big push from behind would settle everything.",
        question="If we push from behind, how will we know where the loose stones lead?",
        reply="We can sprinkle a spic pinch and watch the breeze before choosing our route.",
        clue="The dust from the spic floated toward firm ground beside the stone patch, not over it.",
        action="They shifted to the firm-ground path and used a hay rope to guide the pail around the loose stones",
        result="the pail rolled to a gentle stop, and not one stone or drop went flying",
        village_rule="firm ground and the wind should be checked before a team pushes a heavy pail",
        ending="The saved water became stew, and the pail stood by the fairground as a shelter for the sleepy cow.",
        joke="The cow slept through the whole feast and woke up only when someone mentioned dessert.",
    ),
]

NAMES = ["Mira", "Tavi", "Nella", "Bram", "Pip", "Jun"]
COMPANIONS = ["Lio", "Bea", "Moss", "Rin", "Odo", "Fern"]
TRAITS = ["curious", "cheerful", "bold", "patient", "quick-footed", "thoughtful"]


@dataclass
class StoryParams:
    place: str
    quest: str
    name: str
    companion: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    return [("fairground", "pail_quest")]


def reasonableness_gate(params: StoryParams) -> None:
    if (params.place, params.quest) not in valid_combos():
        raise StoryError(
            "This tall tale needs the fairground and the runaway-pail quest."
        )
    if not params.name.strip() or not params.companion.strip():
        raise StoryError("The hero and companion need names before the quest can begin.")
    if params.name.strip().casefold() == params.companion.strip().casefold():
        raise StoryError("The hero and companion must have different names.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A humorous tall tale about a runaway pail and a clever little spic."
    )
    parser.add_argument("--place", choices=SETTING_REGISTRY)
    parser.add_argument("--quest", choices=QUEST_REGISTRY)
    parser.add_argument("--name")
    parser.add_argument("--companion")
    parser.add_argument("--trait", choices=TRAITS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or "fairground"
    quest = args.quest or "pail_quest"
    params = StoryParams(
        place=place,
        quest=quest,
        name=args.name or rng.choice(NAMES),
        companion=args.companion or rng.choice(COMPANIONS),
        trait=args.trait or rng.choice(TRAITS),
        seed=args.seed,
    )
    reasonableness_gate(params)
    return params


def tell(world: World, params: StoryParams) -> World:
    variant = params.seed
    if variant is None:
        variant = sum(
            (i + 1) * ord(ch)
            for i, ch in enumerate(
                f"{params.name}|{params.companion}|{params.trait}"
            )
        )
    episode = EPISODES[variant % len(EPISODES)]
    setting = world.setting
    quest = QUEST_REGISTRY[params.quest]

    hero = world.add(
        Entity("hero", "character", "child", params.name)
    )
    companion = world.add(
        Entity("companion", "character", "friend", params.companion)
    )
    pail = world.add(Entity("pail", "thing", "pail", "the great pail"))
    spic = world.add(
        Entity("spic", "tool", "spic", "the tiny brass spice scoop")
    )

    add_meme(hero, "curiosity")
    add_meme(hero, "worry")
    add_meter(pail, "water_saved")
    world.say(
        f"At {setting.place}, {params.name}, a {params.trait} young adventurer, found a tiny brass scoop beside a pail big enough to shade a barn."
    )
    world.say(
        "The scoop was called a spic: it held one pinch of pepper, just enough to make the wind's direction visible."
    )
    world.say(
        f"The town needed the pail's last rainwater, so {params.name} and {params.companion} set out on {quest.title} to {quest.goal}."
    )
    world.say(episode.opening)
    world.para()

    world.say(episode.trouble)
    world.say(episode.hasty_idea)
    world.say(
        f'{params.name} asked, "{episode.question}"'
    )
    world.say(
        f'{params.companion} answered, "{episode.reply}"'
    )

    add_meter(hero, "observed")
    world.say(episode.clue)
    world.say(
        f"That clue changed their plan: {params.name} took the rope, while {params.companion} watched the path."
    )
    add_meter(hero, "shared_work")
    world.say(
        f"Together, they {episode.action}."
    )
    propagate(world)

    add_meter(pail, "secured")
    add_meter(pail, "water_saved")
    world.say(f"The result was plain: {episode.result}.")
    propagate(world)

    world.para()
    world.say(
        f"Back at the fairground, the neighbors used the saved water to make a pot of stew, and gave the first bowl to the two friends."
    )
    world.say(
        f"The town kept their lesson as a new rule: {episode.village_rule}."
    )
    world.say(
        f"The quest ended with {quest.reward}, though {params.name} admitted that the peppery stew made a rather surprising breakfast."
    )
    world.say(episode.ending)
    world.say(episode.joke)

    world.facts.update(
        hero=hero,
        companion=companion,
        pail=pail,
        spic=spic,
        quest=quest,
        episode=episode,
    )
    return world


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    setting = SETTING_REGISTRY[params.place]
    world = tell(World(setting=setting), params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    hero = facts["hero"]
    quest = facts["quest"]
    episode = facts["episode"]
    return [
        f"Write a humorous tall tale for children about {hero.label} and {quest.title}.",
        f"Tell a story in which a spic helps {hero.label} and a friend rescue a giant pail.",
        f"Write a tall tale where a careful clue changes the plan. The trouble is: {episode.trouble}",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    hero = facts["hero"]
    companion = facts["companion"]
    quest = facts["quest"]
    episode = facts["episode"]
    return [
        QAItem(
            question="What did the friends set out to do?",
            answer=f"{hero.label} and {companion.label} set out to bring the town's great pail of rainwater home on {quest.title}.",
        ),
        QAItem(
            question="What is a spic in this story?",
            answer="A spic is a tiny brass scoop that holds one pinch of pepper; the friends used its drifting pepper to see which way the wind was blowing.",
        ),
        QAItem(
            question="What made the quest difficult?",
            answer=f"The quest became difficult because {episode.trouble}",
        ),
        QAItem(
            question="What clue changed the friends' plan?",
            answer=f"They watched the pepper from the spic: {episode.clue} That clue showed them a safer way to handle the pail.",
        ),
        QAItem(
            question="How did the friends save the pail?",
            answer=f"They worked together to {episode.action}. As a result, {episode.result}.",
        ),
        QAItem(
            question="What did the town learn from the quest?",
            answer=f"The town learned this rule: {episode.village_rule}. It helped the neighbors think before rushing into a heavy job.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"The town used the saved rainwater for stew, and the pail found a new use: {episode.ending}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why is it helpful to notice the wind before moving something heavy?",
            answer="Noticing the wind can help people choose a safer direction and avoid fighting a force they cannot easily control.",
        ),
        QAItem(
            question="Why can friends solve a difficult problem together?",
            answer="Friends can share what they notice and divide the work, which can make a difficult problem safer and easier to solve.",
        ),
        QAItem(
            question="What is a tall tale?",
            answer="A tall tale is a funny story that uses wonderfully exaggerated events, such as a pail so big it can shade a barn.",
        ),
        QAItem(
            question="What does a pail do?",
            answer="A pail is a container with an open top that people can use to carry things such as water.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== Prompts =="]
    parts.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    parts.extend(["", "== Story QA =="])
    for item in sample.story_qa:
        parts.extend([f"Q: {item.question}", f"A: {item.answer}"])
    parts.extend(["", "== World QA =="])
    for item in sample.world_qa:
        parts.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for entity in world.entities.values():
        state = []
        if entity.meters:
            state.append(f"meters={entity.meters}")
        if entity.memes:
            state.append(f"memes={entity.memes}")
        lines.append(
            f"{entity.label}: {entity.type} {' '.join(state)}".rstrip()
        )
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,Q) :- supports(P,Q), place(P), quest(Q).
#show valid/2.
"""


def asp_facts() -> str:
    import asp

    facts = []
    for place in SETTING_REGISTRY:
        facts.append(asp.fact("place", place))
    for quest in QUEST_REGISTRY:
        facts.append(asp.fact("quest", quest))
    for place, quest in valid_combos():
        facts.append(asp.fact("supports", place, quest))
    return "\n".join(facts)


def asp_program(show: str = "#show valid/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp

    python_combos = set(valid_combos())
    asp_combos = set(asp_valid_combos())
    if python_combos != asp_combos:
        print(f"MISMATCH: Python={sorted(python_combos)} ASP={sorted(asp_combos)}")
        return 1

    exercised = 0
    for seed in range(len(EPISODES) * 2):
        rng = random.Random(seed)
        params = resolve_params(
            argparse.Namespace(
                place=None,
                quest=None,
                name=None,
                companion=None,
                trait=None,
                seed=seed,
            ),
            rng,
        )
        sample = generate(params)
        if not sample.story.strip() or not sample.story_qa:
            print(f"MISMATCH: generated story {seed} was incomplete")
            return 1
        if f'{params.name} asked, "' not in sample.story:
            print(f"MISMATCH: generated story {seed} lacks spoken dialogue")
            return 1
        if f'{params.companion} answered, "' not in sample.story:
            print(f"MISMATCH: generated story {seed} lacks a reply")
            return 1
        if not sample.world or not sample.world.entities["pail"].meters.get("secured"):
            print(f"MISMATCH: generated story {seed} did not secure the pail")
            return 1
        exercised += 1

    print(
        f"OK: ASP matches Python ({len(python_combos)} combo); "
        f"exercised {exercised} generated stories."
    )
    return 0


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
    StoryParams("fairground", "pail_quest", "Mira", "Lio", "curious", 0),
    StoryParams("fairground", "pail_quest", "Tavi", "Bea", "bold", 1),
    StoryParams("fairground", "pail_quest", "Nella", "Moss", "patient", 2),
    StoryParams("fairground", "pail_quest", "Bram", "Fern", "thoughtful", 3),
    StoryParams("fairground", "pail_quest", "Pip", "Rin", "cheerful", 4),
    StoryParams("fairground", "pail_quest", "Jun", "Odo", "quick-footed", 5),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.n < 1 and not args.all:
        raise SystemExit("-n must be at least 1")

    if args.show_asp or args.asp:
        print(asp_program())
        return

    if args.verify:
        try:
            raise SystemExit(asp_verify())
        except ImportError as exc:
            raise SystemExit(f"ASP verification needs clingo: {exc}") from exc

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(args.n * 20, 20):
            seed = base_seed + attempts
            attempts += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
                params.seed = seed
                sample = generate(params)
            except StoryError as exc:
                raise SystemExit(str(exc)) from exc
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
        if args.all:
            header = f"### {sample.params.name}: {sample.params.quest}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        else:
            header = ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

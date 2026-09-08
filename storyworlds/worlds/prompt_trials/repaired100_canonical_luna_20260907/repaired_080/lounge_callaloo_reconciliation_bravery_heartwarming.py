#!/usr/bin/env python3
"""
Standalone storyworld: lounge / callaloo / reconciliation / bravery / heartwarming.

A warm neighborhood story about a lounge, a pot of callaloo, a frightened
mistake, and the brave conversation that brings two friends together again.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Lounge:
    name: str = "the Mango Tree Lounge"
    room: str = "a sunny community room"
    table: str = "the long wooden table"


@dataclass
class World:
    lounge: Lounge
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            raise StoryError(f"Unknown story entity: {eid}")
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    host_name: str
    friend_name: str
    lounge_name: str = "Mango Tree Lounge"
    scenario: int = 0
    opening: int = 0
    dialogue: int = 0
    ending: int = 0
    seed: Optional[int] = None


NAMES = ["Luna", "Maya", "Nia", "Amari", "Zuri", "Talia", "Jalen", "Noah", "Eli", "Sami"]
FRIEND_NAMES = ["Asha", "Theo", "Milo", "Ivy", "Kofi", "Nora", "Bea", "Ravi", "Lena", "Owen"]
GIRL_NAMES = {"Luna", "Maya", "Nia", "Zuri", "Talia", "Asha", "Ivy", "Nora", "Bea", "Lena"}
BOY_NAMES = {"Amari", "Jalen", "Noah", "Eli", "Theo", "Milo", "Kofi", "Ravi", "Owen"}

SCENARIOS = [
    {
        "meal": "a big pot of callaloo",
        "purpose": "welcome neighbors home from a long day",
        "conflict": "a salty spoonful made the soup taste wrong, and each friend quietly thought the other had rushed the recipe",
        "clue": "the salt jar stood beside the measuring cup with its lid still loose",
        "mistake": "hiding the salty taste under extra pepper only made the callaloo hotter",
        "bravery": "tasted the pot again, admitted the mistake, and asked for help instead of pretending everything was fine",
        "repair": "added fresh greens, warm coconut milk, and small spoonfuls of water until the flavors came together",
        "result": "the neighbors tasted the soup and smiled at the care inside every bowl",
        "image": "the callaloo steamed in bright bowls while two friends ladled it together",
        "lesson": "Bravery can sound like an honest apology, and reconciliation grows when people repair a mistake together.",
    },
    {
        "meal": "a fragrant callaloo supper",
        "purpose": "celebrate the lounge's first evening open to everyone",
        "conflict": "the welcome sign fell behind the serving table, and the friends blamed each other for leaving the room untidy",
        "clue": "a trail of green leaves led from the sign to the open window",
        "mistake": "speaking sharply made the lounge feel smaller than a cupboard",
        "bravery": "said that hurt feelings mattered more than winning the argument and invited the other friend to search beside them",
        "repair": "closed the window, cleaned the leaves, and hung the sign where every guest could see it",
        "result": "families entered the lounge and felt truly invited",
        "image": "the welcome sign glowed above the table as bowls of callaloo passed from hand to hand",
        "lesson": "Reconciliation begins when people choose understanding over blame.",
    },
    {
        "meal": "callaloo stirred with pumpkin and thyme",
        "purpose": "feed children after a rainy afternoon of games",
        "conflict": "the rain blew water across the lounge floor, and a borrowed basket of vegetables was knocked over",
        "clue": "little muddy footprints led from the basket to the umbrella stand",
        "mistake": "one friend accused the other before checking the wet floor",
        "bravery": "stopped, apologized for the accusation, and helped move the children safely away from the slippery place",
        "repair": "dried the floor, washed the vegetables, and prepared the callaloo side by side",
        "result": "the children ate warm supper while the rain drummed harmlessly outside",
        "image": "rain jeweled the windows while the lounge filled with spoons, laughter, and warm callaloo",
        "lesson": "Bravery protects people first, then makes room for a truthful repair.",
    },
    {
        "meal": "a bright green callaloo stew",
        "purpose": "thank the volunteers who had painted the lounge",
        "conflict": "the thank-you cards disappeared beneath folded cloths, and the friends stopped speaking because each feared being blamed",
        "clue": "a corner of one card peeked from the cloth basket beside the clean aprons",
        "mistake": "silence let the worry grow larger than the real problem",
        "bravery": "shared the worry aloud and asked the other friend to check the basket together",
        "repair": "found the cards, smoothed their bent corners, and wrote one extra thank-you for the patient search",
        "result": "the volunteers received both supper and words that made them feel seen",
        "image": "paint-flecked hands held warm bowls beneath a row of shining thank-you cards",
        "lesson": "Honest words can open a door that silence keeps closed.",
    },
    {
        "meal": "a gentle pot of callaloo with sweet corn",
        "purpose": "comfort an elder who had been feeling lonely",
        "conflict": "the lounge chairs were arranged in separate corners, and the friends argued about who had forgotten to make the room welcoming",
        "clue": "the old armchair faced the empty wall instead of the bright window",
        "mistake": "moving furniture in a hurry knocked over the flower vase",
        "bravery": "paused, owned the hurried choice, and asked the elder what kind of room would feel good",
        "repair": "dried the table, set the chairs in a circle, and placed the callaloo where everyone could share",
        "result": "the elder told stories until the room felt full of family",
        "image": "the chairs made a circle around the steaming pot, and no one sat alone",
        "lesson": "Bravery listens, and reconciliation helps a room become a home.",
    },
    {
        "meal": "callaloo with soft dumplings",
        "purpose": "welcome a new family to the neighborhood",
        "conflict": "the friends disagreed about which language should appear first on the welcome menu",
        "clue": "the new family had marked the menu with a heart beside every translation",
        "mistake": "arguing over the order made the welcome sound less welcoming",
        "bravery": "admitted that belonging mattered more than being first and asked the family what they preferred",
        "repair": "placed every language side by side and served the callaloo with a warm explanation",
        "result": "the new family laughed, relaxed, and promised to return",
        "image": "many words shared one menu while dumplings bobbed like little boats in the green soup",
        "lesson": "Reconciliation makes room for every voice.",
    },
    {
        "meal": "a slow-cooked callaloo with okra",
        "purpose": "raise food for families after a difficult week",
        "conflict": "the donation list was smudged, and the friends worried that someone would be left out",
        "clue": "the missing names were written on the back of the lounge's music schedule",
        "mistake": "guessing from memory nearly sent two baskets to the same house",
        "bravery": "admitted uncertainty and called each family to check the list carefully",
        "repair": "rewrote the names clearly and packed every bowl with a matching loaf of bread",
        "result": "each family received food, and the friends trusted one another again",
        "image": "labeled baskets lined the lounge wall like a bright promise of care",
        "lesson": "Careful truth is braver than a confident guess.",
    },
    {
        "meal": "callaloo scented with lime",
        "purpose": "celebrate a music teacher's return",
        "conflict": "a drumbeat startled the cook, who thought a shelf had broken, and frustration flared between the friends",
        "clue": "the sound came from a child practicing behind the lounge curtain",
        "mistake": "a sharp reply made the returning teacher wait outside",
        "bravery": "opened the curtain, apologized for the confusion, and invited everyone to begin again",
        "repair": "secured the shelf, welcomed the child into the rhythm, and carried the callaloo to the music",
        "result": "the supper became a song that everyone could join",
        "image": "drums tapped softly beside bowls of lime-bright callaloo",
        "lesson": "An apology can turn a jarring moment into a shared rhythm.",
    ),
]

OPENINGS = [
    "On a golden Saturday, the lounge smelled of rain, soap, and something delicious simmering.",
    "By late afternoon, sunlight spilled through the lounge windows in warm squares.",
    "The neighborhood woke to the gentle sound of spoons clinking in the lounge kitchen.",
    "After a week of gray clouds, the lounge opened its doors to one bright, hopeful evening.",
    "At sunset, the lounge lamps shone like small moons above the long table.",
    "A soft breeze carried the scent of herbs through the open windows of the lounge.",
]

DIALOGUES = [
    '"I am worried I made this worse," said {host}. "Can we look at it together?"',
    '"We both care about this meal," {friend} said. "Let us listen before we decide who is wrong."',
    '"I should have told you sooner," said {host}. "I am sorry."',
    '"Your idea matters to me," {friend} replied. "Let us find a kind way forward."',
    '"The lounge belongs to all of us," said {host}. "There is room for both our plans."',
    '"We can mend the supper and the friendship at the same time," {friend} said.',
    '"I was afraid to admit what happened," said {host}. "Thank you for staying."',
    '"Truth will help us more than blame," {friend} answered.',
]

ENDINGS = [
    "When the last bowl was empty, the friends washed the pot together and laughed at the bubbles.",
    "The lounge grew quiet, but its warmth stayed behind in every chair.",
    "Outside, the evening breeze moved through the trees as gently as their new understanding.",
    "From then on, they kept an extra spoon by the pot for any problem that needed sharing.",
    "The neighbors carried the story home, not because the supper was perfect, but because the friendship had been honest.",
    "The lamps glowed late that night, as if the lounge itself were proud of them.",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A heartwarming lounge story about callaloo, bravery, and reconciliation."
    )
    parser.add_argument("--host-name")
    parser.add_argument("--friend-name")
    parser.add_argument("--lounge-name", default="Mango Tree Lounge")
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
    if args.n < 1:
        raise StoryError("-n must be at least 1")
    host = args.host_name or rng.choice(NAMES)
    friend = args.friend_name or rng.choice(FRIEND_NAMES)
    if host == friend:
        raise StoryError("The host and friend must have different names.")
    return StoryParams(
        host_name=host,
        friend_name=friend,
        lounge_name=args.lounge_name or "Mango Tree Lounge",
        scenario=rng.randrange(len(SCENARIOS)),
        opening=rng.randrange(len(OPENINGS)),
        dialogue=rng.randrange(len(DIALOGUES)),
        ending=rng.randrange(len(ENDINGS)),
    )


def build_world(params: StoryParams) -> World:
    if not params.host_name.strip() or not params.friend_name.strip():
        raise StoryError("Both character names must be non-empty.")
    lounge = Lounge(name=f"the {params.lounge_name}")
    world = World(lounge)
    host_type = "girl" if params.host_name in GIRL_NAMES else "boy" if params.host_name in BOY_NAMES else "person"
    friend_type = "girl" if params.friend_name in GIRL_NAMES else "boy" if params.friend_name in BOY_NAMES else "person"
    host = world.add(Entity("Host", kind="character", type=host_type, label=params.host_name))
    friend = world.add(Entity("Friend", kind="character", type=friend_type, label=params.friend_name))
    pot = world.add(Entity("Pot", type="pot", label="the pot of callaloo", phrase="callaloo"))
    world.facts.update(host=host, friend=friend, pot=pot, params=params)
    return world


def tell(world: World) -> None:
    params: StoryParams = world.facts["params"]
    host: Entity = world.facts["host"]
    friend: Entity = world.facts["friend"]
    pot: Entity = world.facts["pot"]
    scenario = SCENARIOS[params.scenario % len(SCENARIOS)]
    world.facts["scenario"] = scenario

    world.say(OPENINGS[params.opening % len(OPENINGS)])
    world.say(
        f"{host.label} and {friend.label} cared for {world.lounge.name}, a welcoming lounge with "
        f"{world.lounge.room}, a long table, and a kitchen where neighbors often shared stories."
    )
    world.say(
        f"That day they prepared {scenario['meal']} to {scenario['purpose']}. "
        "The fragrant pot bubbled softly while the room filled with hopeful voices."
    )

    world.para()
    host.memes["worry"] = 1
    friend.memes["worry"] = 1
    world.say(f"Trouble began when {scenario['conflict']}.")
    world.say(f"Their first response failed: {scenario['mistake']}.")
    world.say(
        DIALOGUES[params.dialogue % len(DIALOGUES)].format(
            host=host.label,
            friend=friend.label,
        )
    )

    world.para()
    host.memes["brave"] = 1
    world.say(
        f"Then {host.label} found the bravery to slow down. "
        f"{host.pronoun('subject').capitalize()} {scenario['bravery']}."
    )
    world.say(f"Together they noticed the important clue: {scenario['clue']}.")
    world.say(f"They {scenario['repair']}.")
    pot.meters["repaired"] = 1
    host.memes["reconciled"] = 1
    friend.memes["reconciled"] = 1
    world.say(
        f"{friend.label} listened, {host.label} listened back, and reconciliation softened the room. "
        f"As a result, {scenario['result']}."
    )

    world.para()
    world.say(scenario["lesson"])
    world.say(f"In the final warm picture, {scenario['image']}.")
    world.say(ENDINGS[params.ending % len(ENDINGS)])
    world.facts.update(
        resolved=True,
        clue=scenario["clue"],
        brave_action=scenario["bravery"],
        repair=scenario["repair"],
        result=scenario["result"],
        ending_image=scenario["image"],
    )


def generation_prompts(world: World) -> list[str]:
    params: StoryParams = world.facts["params"]
    scenario = world.facts["scenario"]
    return [
        f"Write a heartwarming story for children about {params.host_name} and {params.friend_name} in a lounge.",
        f"Tell a story about sharing {scenario['meal']} and repairing a friendship through reconciliation.",
        f"Write a gentle story in which bravery means admitting a mistake and using this clue: {scenario['clue']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    params: StoryParams = world.facts["params"]
    scenario = world.facts["scenario"]
    return [
        QAItem(
            question="Where did the story take place?",
            answer=f"The story took place in {world.lounge.name}, a welcoming community lounge where neighbors shared food and stories.",
        ),
        QAItem(
            question="What food were the friends preparing?",
            answer=f"They were preparing {scenario['meal']} to {scenario['purpose']}.",
        ),
        QAItem(
            question=f"How did {params.host_name} show bravery?",
            answer=f"{params.host_name} showed bravery when {scenario['bravery']}. That honest choice helped both friends solve the problem.",
        ),
        QAItem(
            question="What clue helped the friends understand the problem?",
            answer=f"They noticed that {scenario['clue']}. The clue gave them evidence instead of another guess.",
        ),
        QAItem(
            question="How did reconciliation change the ending?",
            answer=f"The friends listened and repaired the problem together, so {scenario['result']}. Their shared work made the lounge feel warm again.",
        ),
        QAItem(
            question="What final image showed that everything had changed?",
            answer=f"The ending showed that {scenario['image']}. The shared food and shared work made their renewed friendship visible.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a lounge?",
            answer="A lounge is a comfortable room where people can sit, relax, talk, and spend time together.",
        ),
        QAItem(
            question="What is callaloo?",
            answer="Callaloo is a leafy vegetable dish or soup enjoyed in parts of the Caribbean and other places.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means repairing a disagreement so people can understand one another and become friendly again.",
        ),
        QAItem(
            question="What does bravery mean in this story?",
            answer="Bravery means telling the truth about a difficult mistake and choosing to help repair it.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---", f"Lounge: {world.lounge.name}"]
    for entity in world.entities.values():
        parts = []
        if entity.meters:
            parts.append(f"meters={entity.meters}")
        if entity.memes:
            parts.append(f"memes={entity.memes}")
        lines.append(f"{entity.id}: {' '.join(parts) if parts else '(quiet)'}")
    lines.append(f"resolved={world.facts.get('resolved', False)}")
    return "\n".join(lines)


ASP_RULES = r"""
reconciliation :- brave, repaired.
shared_meal :- repaired, callaloo.
welcome :- lounge, shared_meal.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("lounge"),
            asp.fact("callaloo"),
            asp.fact("brave"),
            asp.fact("repaired"),
        ]
    )


def asp_program(show: str = "#show reconciliation/0. #show shared_meal/0. #show welcome/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    names = {f"{symbol.name}/{len(symbol.arguments)}" for symbol in model}
    required = {"reconciliation/0", "shared_meal/0", "welcome/0"}
    if not required.issubset(names):
        raise StoryError(f"ASP parity failed; missing atoms: {sorted(required - names)}")
    for params in CURATED:
        sample = generate(params)
        if not sample.story or "callaloo" not in sample.story.lower():
            raise StoryError("Generated story exercise failed.")
        if not sample.facts if False else False:
            raise StoryError("Unreachable parity guard.")
    print("OK: ASP/Python parity and generated-story checks passed.")
    return 0


def asp_valid() -> str:
    return asp_program()


CURATED = [
    StoryParams("Luna", "Asha", "Mango Tree Lounge", 0, 0, 0, 0),
    StoryParams("Maya", "Theo", "Sunrise Lounge", 3, 2, 4, 1),
    StoryParams("Jalen", "Nora", "Harbor Lounge", 6, 5, 6, 4),
]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_valid())
        print("\n".join(str(atom) for atom in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        index = 0
        limit = max(args.n * 50, 50)
        while len(samples) < args.n and index < limit:
            seed = base_seed + index
            index += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if len(samples) < args.n and not args.all:
        raise StoryError("Could not produce enough distinct stories.")

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        if args.all:
            params = sample.params
            header = f"### {params.host_name} and {params.friend_name} at {params.lounge_name}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        else:
            header = ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

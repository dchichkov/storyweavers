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
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(HERE)))))
sys.path.insert(0, os.path.join(ROOT, "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    location: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    country: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)

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
class StoryParams:
    captain: str
    teammate: str
    guide: str
    country: str
    quest: str
    teamwork: str
    surprise: str
    ending: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Quest:
    name: str
    obstacle: str
    plan: str
    task_a: str
    task_b: str
    result: str
    changed_fact: str


@dataclass(frozen=True)
class Teamwork:
    temptation: str
    disagreement: str
    admission: str
    counsel: str
    lesson: str


@dataclass(frozen=True)
class Surprise:
    reveal: str
    consequence: str


COUNTRIES = {
    "green_country": "the Green Country",
    "blue_country": "the Blue Country",
    "hill_country": "the Hill Country",
    "sun_country": "the Sun Country",
}

QUESTS = {
    "bell_tunnel": Quest(
        "the quest for the giant bell",
        "a wall of packed red earth blocked the old tunnel beneath the border hill",
        "make one broad opening together instead of digging many tiny holes",
        "pushed the largest spade into the firmest patch",
        "held a lantern and cleared the loosened soil",
        "the friends opened a bright passage and found the bell waiting beyond it",
        "the buried bell could ring for both countries",
    ),
    "river_message": Quest(
        "the quest for the river message",
        "the stream between the two countries had swallowed the stone bridge",
        "stretch a rope across the water and carry the message in a sealed tin",
        "anchored the rope around a cedar root",
        "pulled the tin safely across the rushing stream",
        "the message reached the far bank without getting wet",
        "the two countries received the same honest message",
    ),
    "cloud_seed": Quest(
        "the quest for the cloud seed",
        "a silver cloud hid the seed needed to end a long dry spell",
        "climb the windy ridge in a linked line and search by touch",
        "held the guide rope against the gusts",
        "felt beneath the cloud stones for the warm seed",
        "the seed was found and carried home in a wool cap",
        "the dry fields could be planted again",
    ),
    "moon_gate": Quest(
        "the quest for the moon gate",
        "the gate between the countries had sunk into a valley of tall grass",
        "clear a path, lift the gate, and mark the safe road",
        "cut the grass around the hidden hinges",
        "lifted the gate with a timber lever",
        "the moon gate opened wide enough for every traveler",
        "the old road belonged to everyone again",
    ),
    "whistling_map": Quest(
        "the quest for the whistling map",
        "a map had slipped into a cave whose narrow mouth seemed impossible to enter",
        "send a small team through the opening while the others held a guide cord",
        "tied the cord to a steady stone",
        "crawled far enough to retrieve the map",
        "the map came out with only one corner folded",
        "the safest road through the country was known again",
    ),
}

TEAMWORKS = {
    "listen": Teamwork(
        "rush ahead and let the other traveler follow guesses",
        "One friend pulled left while the other pointed right, and the quest went nowhere.",
        '"I was hurrying past your good idea," {a} admitted. "I should have listened."',
        '"A team has two pairs of eyes and one careful purpose," {guide} said.',
        "listening lets every useful idea strengthen the shared plan",
    ),
    "share_strength": Teamwork(
        "save their strength for the easiest part",
        "The hardest work stayed untouched while both friends reached for the same light tool.",
        '"I was guarding my energy instead of sharing it," {b} said.',
        '"A strong back is most useful when it helps a tired neighbor," {guide} replied.',
        "shared effort turns a huge task into a possible one",
    ),
    "tell_truth": Teamwork(
        "hide that they had taken the wrong path",
        "They walked in a circle because neither wanted to confess the mistake.",
        '"We chose the wrong trail," {a} said. "Now everyone needs the truth."',
        '"An honest map can begin with an honest mistake," {guide} answered.',
        "truth gives a team the direction it needs to recover",
    ),
    "trust": Teamwork(
        "grab control and ignore the quieter teammate",
        "The plan wobbled because nobody trusted the person who knew the wind best.",
        '"Your careful warning mattered," {b} told {a}. "I will trust it now."',
        '"Trust is a bridge built plank by plank," {guide} said.',
        "trust lets teammates act together even when the path is unseen",
    ),
    "patience": Teamwork(
        "force the obstacle before the right moment",
        "Their hurry made the earth slide back over the work they had just done.",
        '"I pushed before we were ready," {a} confessed.',
        '"Patient teamwork moves farther than lonely force," {guide} told them.',
        "patience keeps brave work from becoming dangerous work",
    ),
}

SURPRISES = {
    "tiny_key": Surprise(
        "The enormous obstacle opened when a tiny brass key, hidden in a seed pouch, was turned in its lock.",
        "The smallest object had been waiting for the biggest team.",
    ),
    "sleeping_giant": Surprise(
        "Behind the barrier slept a gentle giant who had been holding it shut so nobody would enter alone.",
        "The giant smiled when the friends promised to bring every traveler through safely.",
    ),
    "backward_river": Surprise(
        "The river suddenly flowed uphill, carrying the lost message straight to the waiting guide.",
        "The country had been helping them all along.",
    ),
    "singing_stone": Surprise(
        "The plain stone began to sing when all three travelers touched it at once.",
        "Its song showed that the quest needed friendship more than muscle.",
    ),
    "hidden_country": Surprise(
        "Beyond the opening lay a little country no map had drawn, filled with lanterns and welcoming children.",
        "The quest had not merely crossed a border; it had found new neighbors.",
    ),
}

ENDINGS = {
    "feast": "That evening, both countries held one enormous feast, and the friends could barely lift the first spoon.",
    "flag": "At dawn, the two countries raised one bright flag between them, stitched from every team's spare cloth.",
    "bell": "When the final bell rang, its sound rolled over the hills and made every frightened bird feel brave.",
    "road": "By sunset, travelers were already using the restored road, waving to the team as they passed.",
    "garden": "The friends planted the quest's small token in the soil, and by morning a tall green shoot stood there.",
}

NAMES = ["Luna", "Milo", "Tavi", "Nera", "Pip", "Oren", "Sela", "Bram"]
GUIDES = ["the mountain guide", "the village cartographer", "the patient shepherd", "the bridge keeper"]
COUNTRY_KEYS = tuple(COUNTRIES)
QUEST_KEYS = tuple(QUESTS)
TEAMWORK_KEYS = tuple(TEAMWORKS)
SURPRISE_KEYS = tuple(SURPRISES)
ENDING_KEYS = tuple(ENDINGS)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A tall tale of a country-crossing quest.")
    parser.add_argument("--country", choices=COUNTRIES)
    parser.add_argument("--captain")
    parser.add_argument("--teammate")
    parser.add_argument("--guide", choices=GUIDES)
    parser.add_argument("--quest", choices=QUESTS)
    parser.add_argument("--teamwork", choices=TEAMWORKS)
    parser.add_argument("--surprise", choices=SURPRISES)
    parser.add_argument("--ending", choices=ENDINGS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    captain = args.captain or rng.choice(NAMES)
    teammate = args.teammate or rng.choice([name for name in NAMES if name != captain])
    if captain == teammate:
        raise StoryError("The quest team needs two different travelers.")
    return StoryParams(
        captain=captain,
        teammate=teammate,
        guide=args.guide or rng.choice(GUIDES),
        country=args.country or rng.choice(COUNTRY_KEYS),
        quest=args.quest or rng.choice(QUEST_KEYS),
        teamwork=args.teamwork or rng.choice(TEAMWORK_KEYS),
        surprise=args.surprise or rng.choice(SURPRISE_KEYS),
        ending=args.ending or rng.choice(ENDING_KEYS),
    )


def tell(params: StoryParams) -> World:
    country = COUNTRIES[params.country]
    quest = QUESTS[params.quest]
    teamwork = TEAMWORKS[params.teamwork]
    surprise = SURPRISES[params.surprise]
    world = World(country)

    captain = world.add(Entity(params.captain, "character", "child", params.captain, "border trail"))
    teammate = world.add(Entity(params.teammate, "character", "child", params.teammate, "border trail"))
    guide = world.add(Entity("guide", "character", "adult", params.guide, "border trail"))
    obstacle = world.add(Entity("obstacle", "barrier", "earth", "the enormous obstacle", "border trail"))
    world.facts.update(captain=captain, teammate=teammate, guide=guide, quest=quest, teamwork=teamwork, surprise=surprise)

    world.say(f"Once, in {country}, {captain.id} and {teammate.id} began {quest.name}.")
    world.say(f"The quest was so tall-tale huge that {captain.id} carried a rope as long as a country, while {teammate.id} packed a lunch big enough to feed a mountain.")
    world.say(f"At the border trail, {guide.label} pointed ahead. {quest.obstacle.capitalize()}.")

    world.para()
    captain.meters["reach"] = 2.0
    teammate.meters["reach"] = 2.0
    obstacle.meters["height"] = 10.0
    world.say(f'"We can penetrate this obstacle before the moon rises," {captain.id} declared.')
    world.say(f'"Only if we work as one team," {teammate.id} replied. "My plan is to {quest.plan}."')
    world.say(f"The friends argued when each was tempted to {teamwork.temptation}.")
    world.say(teamwork.disagreement)

    world.para()
    world.say(teamwork.admission.format(a=captain.id, b=teammate.id, guide=guide.label))
    world.say(teamwork.counsel.format(a=captain.id, b=teammate.id, guide=guide.label))
    captain.memes["trust"] = 1.0
    teammate.memes["trust"] = 1.0
    guide.memes["patience"] = 1.0
    world.say(f"They agreed that {teamwork.lesson}.")
    world.say(f"Together, they decided to {quest.plan}.")
    world.say(f"{captain.id} {quest.task_a}; {teammate.id} {quest.task_b}.")

    world.para()
    world.say(f"Then came the great surprise: {surprise.reveal}")
    world.say(surprise.consequence)
    world.say(f"With the surprise guiding them, {quest.result}.")
    world.facts["resolved"] = True
    world.facts["changed_fact"] = quest.changed_fact
    world.say(f"The friends understood that {teamwork.lesson}.")
    world.say(ENDINGS[params.ending])
    world.say("And ever after, people in the country called them the Team That Made a Way.")

    return world


def generation_prompts(world: World) -> list[str]:
    quest: Quest = world.facts["quest"]
    captain: Entity = world.facts["captain"]
    teammate: Entity = world.facts["teammate"]
    return [
        f"Tell a tall tale about {captain.id} and {teammate.id} on {quest.name}.",
        f"Write a country-crossing quest in which a team must penetrate {quest.obstacle}.",
        "Include a surprising turn that proves teamwork matters more than individual strength.",
    ]


def story_qa(world: World) -> list[QAItem]:
    captain: Entity = world.facts["captain"]
    teammate: Entity = world.facts["teammate"]
    guide: Entity = world.facts["guide"]
    quest: Quest = world.facts["quest"]
    surprise: Surprise = world.facts["surprise"]
    teamwork: Teamwork = world.facts["teamwork"]
    return [
        QAItem(
            question=f"Who went on the quest in {world.country}?",
            answer=f"{captain.id} and {teammate.id} went on the quest, with advice from {guide.label}. They solved the danger by working together.",
        ),
        QAItem(
            question="What obstacle did the team need to penetrate?",
            answer=f"They needed to penetrate {quest.obstacle}. Their plan was to {quest.plan}.",
        ),
        QAItem(
            question="What surprise changed the quest?",
            answer=f"The surprise was that {surprise.reveal} This helped because {surprise.consequence}",
        ),
        QAItem(
            question="What did the team learn?",
            answer=f"They learned that {teamwork.lesson}. Their teamwork meant that {quest.changed_fact}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a country?",
            answer="A country is a place with its own land, people, communities, and ways of organizing life.",
        ),
        QAItem(
            question="What does penetrate mean in this story?",
            answer="Here, penetrate means to pass through or enter something that blocks the way, such as earth, a gate, or a cave.",
        ),
        QAItem(
            question="Why is teamwork useful on a quest?",
            answer="Teamwork is useful because people can share strength, notice different details, and help one another stay safe.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:10} kind={entity.kind:10} location={entity.location} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  facts: resolved={world.facts.get('resolved')} changed_fact={world.facts.get('changed_fact')}")
    return "\n".join(lines)


ASP_RULES = r"""
place(green_country).
place(blue_country).
place(hill_country).
place(sun_country).
feature(quest).
feature(teamwork).
feature(surprise).
style(tall_tale).
valid(green_country,quest,teamwork,surprise).
valid(blue_country,quest,teamwork,surprise).
valid(hill_country,quest,teamwork,surprise).
valid(sun_country,quest,teamwork,surprise).
"""


def asp_facts() -> str:
    import asp
    facts = []
    for place in COUNTRY_KEYS:
        facts.append(asp.fact("place", place))
    facts.extend(
        [
            asp.fact("feature", "quest"),
            asp.fact("feature", "teamwork"),
            asp.fact("feature", "surprise"),
            asp.fact("style", "tall_tale"),
        ]
    )
    return "\n".join(facts)


def asp_program(show: str = "#show valid/4.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    return sorted(set(asp.atoms(asp.one_model(asp_program()), "valid")))


def asp_verify() -> int:
    import asp
    python_combos = {
        (country, "quest", "teamwork", "surprise")
        for country in COUNTRY_KEYS
    }
    clingo_combos = set(asp_valid_combos())
    if python_combos != clingo_combos:
        print("ASP/Python parity failure.")
        print("Python only:", sorted(python_combos - clingo_combos))
        print("ASP only:", sorted(clingo_combos - python_combos))
        return 1
    sample = generate(
        StoryParams(
            captain="Luna",
            teammate="Milo",
            guide=GUIDES[0],
            country="green_country",
            quest="bell_tunnel",
            teamwork="listen",
            surprise="tiny_key",
            ending="bell",
        )
    )
    if not sample.story or "Luna" not in sample.story or "team" not in sample.story.lower():
        print("Generated-story verification failure.")
        return 1
    print(f"OK: ASP/Python parity matches ({len(python_combos)} combinations); generated story passed.")
    return 0


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


def show_qa_item(item: QAItem) -> str:
    return f"Q: {item.question}\nA: {item.answer}"


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        for index, prompt in enumerate(sample.prompts, 1):
            print(f"[Prompt {index}] {prompt}")
        for item in sample.story_qa + sample.world_qa:
            print()
            print(show_qa_item(item))


CURATED = [
    StoryParams("Luna", "Milo", GUIDES[0], "green_country", "bell_tunnel", "listen", "tiny_key", "bell"),
    StoryParams("Tavi", "Nera", GUIDES[1], "hill_country", "cloud_seed", "share_strength", "singing_stone", "garden"),
    StoryParams("Pip", "Oren", GUIDES[2], "blue_country", "river_message", "tell_truth", "backward_river", "road"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        for combo in asp_valid_combos():
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < max(1, args.n):
            seed = base_seed + attempt
            attempt += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
            if attempt > max(100, args.n * 30):
                break

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {index + 1}" if len(samples) > 1 else "")
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

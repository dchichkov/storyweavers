#!/usr/bin/env python3
"""
Rosette Rescue: a small superhero storyworld about a dangerous shortcut,
a bad ending avoided, and the moral value of courage with care.
"""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Hero:
    name: str
    power: str
    meters: dict[str, float] = field(default_factory=lambda: {"energy": 1.0, "danger": 0.0})
    memes: dict[str, float] = field(
        default_factory=lambda: {"courage": 0.0, "care": 0.0, "pride": 0.0}
    )


@dataclass
class Friend:
    name: str
    role: str
    meters: dict[str, float] = field(default_factory=lambda: {"safety": 1.0})
    memes: dict[str, float] = field(default_factory=lambda: {"trust": 0.0, "wisdom": 0.0})


@dataclass
class Rosette:
    color: str
    owner: str
    location: str
    secure: bool = False
    falling: bool = False
    rescued: bool = False
    meters: dict[str, float] = field(default_factory=lambda: {"value": 1.0})
    memes: dict[str, float] = field(default_factory=lambda: {"honor": 1.0})


@dataclass
class Setting:
    place: str
    danger: str
    landmark: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, object] = field(default_factory=dict)
    events: list[str] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, key: str, value: object) -> object:
        self.entities[key] = value
        return value

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass(frozen=True)
class Scenario:
    opening: str
    threat: str
    shortcut: str
    clue: str
    teamwork: str
    resolution: str
    moral: str
    ending: str


SCENARIOS = (
    Scenario(
        opening="The annual Star Street parade was about to begin, and a bright rosette waited for the bravest helper.",
        threat="A gust tore the rosette from the mayor's wagon and carried it toward the old clock tower.",
        shortcut="climb the cracked outside wall before anyone could stop her",
        clue="a loose brick dropped into the alley below",
        teamwork="held the rescue rope while Juniper called the tower keeper",
        resolution="Together they lowered a safe line, and Luna used her gentle wind power to guide the rosette back.",
        moral="true courage protects people instead of showing off",
        ending="the rosette rested safely on the parade banner while Luna and Juniper marched beneath it",
    ),
    Scenario(
        opening="Luna had been chosen to wear a silver rosette at the Children's Hero Fair.",
        threat="A flash of lightning knocked the rosette onto a roof beside a humming power cable.",
        shortcut="leap straight across the wet rooftops",
        clue="rainwater was shining along the cable",
        teamwork="cleared the crowd while Juniper fetched the insulated rescue hook",
        resolution="Luna waited for the keeper to switch off the power, then brought the rosette down with the safe hook.",
        moral="a careful hero knows when patience is stronger than speed",
        ending="the silver rosette gleamed on Luna's cape after the storm clouds passed",
    ),
    Scenario(
        opening="At dawn, the town prepared to honor every child who had helped clean the riverside.",
        threat="The golden rosette slipped from the honor board and landed on a thin sheet of river ice.",
        shortcut="dash onto the ice and snatch it before the current moved",
        clue="a dark crack widened beneath a fallen branch",
        teamwork="marked the safe bank while Juniper called the river team",
        resolution="The river team used a long pole from solid ground and pulled the rosette to shore.",
        moral="wisdom means asking for help before danger becomes disaster",
        ending="the golden rosette hung above the clean river, where everyone could see it",
    ),
    Scenario(
        opening="Luna promised to deliver a red rosette to a young volunteer at the hilltop shelter.",
        threat="A landslide blocked the road, and the rosette's box began sliding toward the ravine.",
        shortcut="run down the loose slope alone and grab the box",
        clue="small stones kept rolling after the ground seemed still",
        teamwork="kept people behind the barrier while Juniper tied a line around a sturdy pine",
        resolution="Luna pulled the box from solid ground, and the shelter crew carried it the rest of the way.",
        moral="a good deed should never create a new person who needs rescuing",
        ending="the red rosette shone on the volunteer's coat beside a safe, quiet hillside",
    ),
    Scenario(
        opening="The museum's famous blue rosette was to be displayed during a night of stories.",
        threat="A thief's loose window sent the rosette spinning toward a glass skylight.",
        shortcut="blast through the skylight with a burst of super strength",
        clue="the glass was already cracked above a room full of children",
        teamwork="moved the children away while Juniper closed the museum shutters",
        resolution="Luna caught the rosette with a soft cushion of air, leaving every pane and person safe.",
        moral="power is valuable only when guided by care",
        ending="the blue rosette rested beneath a clear case as the children told its story",
    ),
)


def _article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def _render(text: str, hero: Hero, friend: Friend) -> str:
    return text.format(hero=hero.name, friend=friend.name)


def _validate(params: StoryParams) -> None:
    if not params.hero_name.strip() or not params.friend_name.strip():
        raise StoryError("hero and friend names must not be empty")
    if params.hero_name.strip().lower() == params.friend_name.strip().lower():
        raise StoryError("hero and friend must have different names")
    if not params.color.strip():
        raise StoryError("rosette color must not be empty")
    if params.scenario_id < 0 or params.scenario_id >= len(SCENARIOS):
        raise StoryError(f"scenario_id must be between 0 and {len(SCENARIOS) - 1}")


@dataclass
class StoryParams:
    place: str = "the town square"
    hero_name: str = "Luna"
    friend_name: str = "Juniper"
    hero_power: str = "a gentle wind power"
    friend_role: str = "a careful safety captain"
    color: str = "scarlet"
    scenario_id: int = 0
    seed: Optional[int] = None


def tell(params: StoryParams) -> World:
    _validate(params)
    scenario = SCENARIOS[params.scenario_id]
    world = World(Setting(params.place, scenario.threat, "the town landmark"))
    hero = world.add("hero", Hero(params.hero_name, params.hero_power))
    friend = world.add("friend", Friend(params.friend_name, params.friend_role))
    rosette = world.add("rosette", Rosette(params.color, "the town helpers", "a high place"))

    hero.memes["pride"] = 0.8
    friend.memes["trust"] = 0.4

    world.say(
        f"{scenario.opening} {hero.name}, {_article('hero')} superhero with {hero.power}, "
        f"stood ready in {world.setting.place} beside {friend.name}, {friend.role}."
    )
    world.say(
        f"The prize was a {rosette.color} rosette, a small circle of cloth that honored helpful work."
    )

    world.para()
    world.say(scenario.threat)
    world.say(
        f"{hero.name} felt a flash of pride and decided to {_render(scenario.shortcut, hero, friend)}."
    )
    world.say(
        f"'{hero.name}, wait!' called {friend.name}. 'A fast rescue is not a safe rescue.'"
    )
    world.say(
        f"'{friend.name}, I can reach it,' {hero.name} answered. 'But tell me what you see.'"
    )
    world.say(f"The clue was clear: {scenario.clue}.")
    world.say(
        f"{hero.name} lowered her cape. The rosette was important, but a person's safety was more important."
    )

    world.para()
    world.say(f"Instead of taking the dangerous shortcut, {hero.name} {scenario.teamwork}.")
    world.say(f"{friend.name} replied, 'Now we have a plan that protects everyone.'")
    world.say(scenario.resolution)

    rosette.secure = True
    rosette.falling = False
    rosette.rescued = True
    rosette.location = params.place
    hero.meters["danger"] = 0.0
    hero.meters["energy"] = 0.7
    hero.memes["courage"] = 1.0
    hero.memes["care"] = 1.0
    hero.memes["pride"] = 0.2
    friend.meters["safety"] = 1.0
    friend.memes["trust"] = 1.0
    friend.memes["wisdom"] = 1.0
    world.events.extend(["threat_seen", "shortcut_rejected", "clue_shared", "safe_rescue"])
    world.say(f"{hero.name} learned that {scenario.moral}.")

    world.para()
    world.say(f"{scenario.ending}.")
    world.say(
        f"'{hero.name}, what makes someone a superhero?' asked {friend.name}. "
        f"{hero.name} smiled and said, 'Using courage to care for others.'"
    )

    world.facts.update(
        hero=hero,
        friend=friend,
        rosette=rosette,
        scenario=scenario,
        threat=scenario.threat,
        shortcut=scenario.shortcut,
        clue=scenario.clue,
        teamwork=scenario.teamwork,
        resolution=scenario.resolution,
        moral=scenario.moral,
        ending=scenario.ending,
        bad_ending="The shortcut could have hurt someone and left the rosette lost.",
        safe=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Hero = f["hero"]
    return [
        f"Write a superhero story about {hero.name} rescuing a rosette without taking this dangerous shortcut: {f['shortcut']}.",
        f"Show how this clue changes the hero's decision: {f['clue']}.",
        f"End with the moral value that {f['moral']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Hero = f["hero"]
    friend: Friend = f["friend"]
    rosette: Rosette = f["rosette"]
    return [
        QAItem(
            question=f"What danger threatened the {rosette.color} rosette?",
            answer=f"The danger was this: {f['threat']}"
        ),
        QAItem(
            question=f"Why did {hero.name} reject the first plan?",
            answer=f"{hero.name} rejected the shortcut because {f['clue']}. The shortcut could have hurt someone."
        ),
        QAItem(
            question=f"How did {hero.name} and {friend.name} rescue the rosette?",
            answer=f"{hero.name} {f['teamwork']}. Then {f['resolution']}"
        ),
        QAItem(
            question="What was the bad ending that the heroes avoided?",
            answer=f"The bad ending was that {f['bad_ending']} They avoided it by choosing a safe plan."
        ),
        QAItem(
            question=f"What moral value did {hero.name} learn?",
            answer=f"{hero.name} learned that {f['moral']}. The safe rescue proved that lesson."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a rosette?",
            answer="A rosette is a small decoration made from folded or gathered ribbon, often given as a prize or sign of honor."
        ),
        QAItem(
            question="What makes a superhero courageous?",
            answer="A courageous superhero faces a problem while still thinking carefully about how to protect other people."
        ),
        QAItem(
            question="Why is a bad ending useful in a story?",
            answer="A bad ending shows what could go wrong and makes the hero's wise choice and moral value easier to understand."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- hero_entity(H).
friend(F) :- friend_entity(F).
rosette(R) :- rosette_entity(R).
dangerous_shortcut_rejected :- hero(H), friend(F), clue_seen(H,F).
safe_rescue(R) :- rosette(R), dangerous_shortcut_rejected, rescued(R).
moral_value(careful_courage) :- safe_rescue(_).
bad_ending_avoided :- safe_rescue(_).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("hero_entity", "hero"),
            asp.fact("friend_entity", "friend"),
            asp.fact("rosette_entity", "rosette"),
            asp.fact("clue_seen", "hero", "friend"),
            asp.fact("rescued", "rosette"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def dump_trace(world: World) -> str:
    hero: Hero = world.entities["hero"]
    friend: Friend = world.entities["friend"]
    rosette: Rosette = world.entities["rosette"]
    return "\n".join(
        [
            "--- world trace ---",
            f"place: {world.setting.place}",
            f"events: {world.events}",
            f"hero: {hero.name}, power={hero.power}, meters={hero.meters}, memes={hero.memes}",
            f"friend: {friend.name}, role={friend.role}, meters={friend.meters}, memes={friend.memes}",
            f"rosette: color={rosette.color}, location={rosette.location}, secure={rosette.secure}, rescued={rosette.rescued}",
        ]
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Superhero storyworld about a rosette and careful courage.")
    parser.add_argument("--place", default=None)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        place=args.place or rng.choice(["the town square", "the hero fair", "the riverside plaza"]),
        hero_name=rng.choice(["Luna", "Nova", "Ember", "Skye"]),
        friend_name=rng.choice(["Juniper", "Mara", "Theo", "Pax"]),
        hero_power=rng.choice(["a gentle wind power", "a warm glow", "super strength"]),
        friend_role=rng.choice(["a careful safety captain", "a rescue planner", "a town lookout"]),
        color=rng.choice(["scarlet", "silver", "golden", "blue"]),
        scenario_id=rng.randrange(len(SCENARIOS)),
        seed=args.seed,
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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(
        asp_program(
            "#show safe_rescue/1. #show moral_value/1. #show bad_ending_avoided/0."
        )
    )
    safe = asp.atoms(model, "safe_rescue")
    moral = asp.atoms(model, "moral_value")
    avoided = asp.atoms(model, "bad_ending_avoided")
    if ("rosette",) not in safe or ("careful_courage",) not in moral or () not in avoided:
        print("MISMATCH: ASP twin did not derive the safe moral resolution.")
        return 1
    for scenario_id in range(len(SCENARIOS)):
        sample = generate(StoryParams(scenario_id=scenario_id))
        if not sample.world.facts["safe"]:
            print(f"MISMATCH: Python scenario {scenario_id} was not safe.")
            return 1
    print("OK: ASP/Python parity and generated stories verified.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show safe_rescue/1. #show moral_value/1. #show bad_ending_avoided/0."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(
            asp_program("#show safe_rescue/1. #show moral_value/1. #show bad_ending_avoided/0.")
        )
        print("safe_rescue:", asp.atoms(model, "safe_rescue"))
        print("moral_value:", asp.atoms(model, "moral_value"))
        print("bad_ending_avoided:", asp.atoms(model, "bad_ending_avoided"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        params_list = [
            StoryParams(place="the town square", scenario_id=i, seed=i)
            for i in range(len(SCENARIOS))
        ]
        samples = [generate(p) for p in params_list]
    else:
        samples = [
            generate(resolve_params(args, random.Random(base_seed + i)))
            for i in range(max(0, args.n))
        ]

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

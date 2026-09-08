#!/usr/bin/env python3
from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import hashlib
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
)
from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class City:
    name: str
    danger: float = 0.0
    bacon_removed: bool = False
    twist_revealed: bool = False
    reconciliation: bool = False
    facts: dict = field(default_factory=dict)


@dataclass
class StoryParams:
    hero_name: str
    friend_name: str
    city_name: str
    seed: Optional[int] = None


NAMES = ["Luna", "Milo", "Nova", "Tess", "Jax", "Pip", "Rae", "Zed"]
CITY_NAMES = ["Brighton City", "Sunbeam City", "Skyline Town", "Star Harbor"]

ARCS = [
    {
        "key": "bacon_beacon",
        "premise": [
            "{hero} watched over {city} from a silver rooftop while {friend} delivered warm bacon sandwiches to tired rescue workers.",
            "At sunrise, superhero {hero} and helper {friend} helped the people of {city}. Their snack cart smelled like crisp bacon as bright banners fluttered below.",
        ],
        "problem": [
            "A giant bacon-shaped beacon began flashing over the city. Each flash made people chase breakfast instead of noticing the real danger: a runaway bridge crane.",
            "The city's new bacon beacon pulled everyone's eyes toward the sky while a loose power cable swung over the market. {hero} feared the distraction would hurt someone.",
        ],
        "conflict": [
            "\"We should smash the beacon,\" said {hero}. {friend} shook their head. \"We should find out why it is flashing.\" Their disagreement left the crane rolling closer.",
            "{hero} wanted to rush at the danger, but {friend} asked for a careful look. \"There is no time,\" cried {hero}. \"There may be a hidden clue,\" replied {friend}.",
        ],
        "turn": [
            "{friend} noticed that every bacon-scented flash came just before the crane's motor jerked. The beacon was not the villain's weapon after all; it was warning them about the motor.",
            "A gust lifted a bacon wrapper onto the beacon's control box. Beneath it, {hero} saw a tiny switch labeled REMOVE SIGNAL. The flashing beacon was a warning turned backward.",
        ],
        "action": [
            "\"You were right to look,\" {hero} admitted. Together they used a long rescue pole to remove the loose signal wire, then guided the crane away from the market.",
            "{friend} called the safe moment, and {hero} removed the warning wire without touching the live cable. The crane slowed, and the helpers pulled people behind a wall.",
        ],
        "resolution": [
            "The bridge crane settled safely, and the beacon stopped flashing. {hero} apologized for rushing, while {friend} thanked the hero for listening. Their reconciliation made them a stronger team.",
            "With the danger gone, the two friends shared the last bacon sandwich. They understood that removing a problem worked best after hearing one another.",
        ],
        "ending": [
            "That evening, the beacon shone a calm blue light above {city}, and its bacon-shaped shadow pointed safely toward home.",
            "The rescue workers cheered beneath the quiet beacon while {hero} and {friend} carried an empty bacon basket across the peaceful square.",
        ],
        "problem_fact": "a bacon-shaped beacon distracted the city from a dangerous runaway crane",
        "clue_fact": "the beacon's bacon-scented flashes warned about the crane's motor",
        "action_fact": "they removed the loose warning wire and guided the crane to safety",
        "outcome_fact": "the crane stopped and the friends reconciled",
    },
    {
        "key": "smoke_signal",
        "premise": [
            "Superhero {hero} patrolled {city} with {friend}, who carried a little pan of bacon for the neighborhood watch.",
            "The rooftops of {city} glittered after rain. {hero} promised to protect everyone while {friend} cooked bacon for volunteers at the community center.",
        ],
        "problem": [
            "A dark smoke cloud rolled between the buildings and made every alarm ring at once. The city could not tell which warning was real.",
            "The alarm towers began coughing black clouds, and frightened families ran in opposite directions. The strange smoke smelled like burnt bacon.",
        ],
        "conflict": [
            "\"I can blow the smoke away,\" said {hero}. \"First we must remove the blocked vents,\" said {friend}. Their argument let the smoke thicken.",
            "{hero} blamed the alarm towers, but {friend} suspected a hidden trap. Neither trusted the other's plan until a school bell vanished in the haze.",
        ],
        "turn": [
            "{friend} held a strip of bacon near a vent. The smoke pulled toward it, revealing that tiny fans were sucking the cloud through the towers. The smoke was a twisted signal, not a fire.",
            "A bacon crumb landed on a tower grate and was pulled inside. {hero} saw the grate vibrate and realized someone had placed a device behind it to spread false alarms.",
        ],
        "action": [
            "{hero} listened and lifted the tower cover while {friend} used a safe hook to remove the hidden fan. The smoke thinned, and the alarms began pointing to the real blocked vent.",
            "\"Show me the safest vent,\" {hero} said. {friend} marked it with bacon grease, and together they removed the trap before opening the windows.",
        ],
        "resolution": [
            "Fresh air returned to the streets. {hero} admitted that strength alone was not enough, and {friend} admitted that the hero's courage mattered. They reconciled beside the quiet alarm tower.",
            "The final alarm became a clear bell instead of a cloud. The friends apologized, shook hands, and helped the neighborhood watch clean the tower.",
        ],
        "ending": [
            "The last curl of smoke became a tiny gray ribbon above {city}, while bacon sizzled peacefully in the community kitchen.",
            "Children drew a picture of the two heroes beside a clean alarm tower and a bright plate of bacon.",
        ],
        "problem_fact": "hidden fans spread smoke through the alarm towers and caused false warnings",
        "clue_fact": "a bacon test showed that air was being pulled through a hidden device",
        "action_fact": "they removed the hidden fan and opened the blocked vents",
        "outcome_fact": "the smoke cleared and the friends reconciled",
    },
    {
        "key": "false_villain",
        "premise": [
            "{hero} and {friend} flew over {city} after breakfast, carrying a basket of bacon to the firefighters below.",
            "In {city}, superhero {hero} trained with trusted partner {friend}. They planned to share bacon with every firefighter after their morning patrol.",
        ],
        "problem": [
            "A shadowy figure stole the bacon basket and raced across the rooftops. {hero} chased the figure, but the crowd began shouting that {friend} had helped the thief.",
            "The city screens showed a blurry picture of {friend} near the missing bacon. Suspicion spread faster than the truth, and {hero} felt betrayed.",
        ],
        "conflict": [
            "\"Tell me you did not do it,\" said {hero}. \"I did not, but you must listen,\" answered {friend}. Their hurt words pushed them apart.",
            "{hero} wanted to arrest {friend} immediately. {friend} begged for a chance to explain, but the hero's anger made every rooftop feel colder.",
        ],
        "turn": [
            "A bacon wrapper stuck to the shadow's boot. When {hero} looked closely, the wrapper showed a reflection of the real thief: a frightened robot carrying the food to a hungry shelter.",
            "{friend} pointed out that the screen image had been mirrored. The twist was clear: the shadow had used {friend}'s cape as a disguise, but the missing bacon was being taken to feed children.",
        ],
        "action": [
            "{hero} removed the false accusation from the city screens by showing the full recording. Then the two friends followed the robot and carried the bacon to the shelter together.",
            "\"I should have asked before blaming you,\" {hero} said. {friend} nodded, and together they removed the disguise from the robot and helped it explain the rescue.",
        ],
        "resolution": [
            "The shelter received breakfast, and the crowd learned the truth. {hero} apologized sincerely, and {friend} accepted. Their reconciliation restored trust.",
            "The robot's hungry shelter was safe, and the false story disappeared from every screen. The friends stood shoulder to shoulder again.",
        ],
        "ending": [
            "At sunset, {hero}, {friend}, and the little robot shared the final bacon strip beneath a screen that now showed the truth.",
            "The city screens displayed two heroes holding one basket together, while grateful children waved from the shelter windows.",
        ],
        "problem_fact": "a blurry recording falsely made the friend look like a bacon thief",
        "clue_fact": "a bacon wrapper and the mirrored recording revealed a hungry robot's rescue",
        "action_fact": "they removed the false accusation and helped the robot feed the shelter",
        "outcome_fact": "the truth restored trust between the friends",
    },
]


def _rng(params: StoryParams) -> random.Random:
    if params.seed is not None:
        return random.Random(params.seed)
    raw = "|".join((params.hero_name, params.friend_name, params.city_name))
    return random.Random(int.from_bytes(hashlib.sha256(raw.encode()).digest()[:8], "big"))


class World:
    def __init__(self, city: City) -> None:
        self.city = city
        self.entities: dict[str, Entity] = {}
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


def tell(params: StoryParams) -> World:
    arc = ARCS[(params.seed or 0) % len(ARCS)]
    rng = _rng(params)
    beats = ("premise", "problem", "conflict", "turn", "action", "resolution", "ending")
    hero = Entity(params.hero_name, kind="character", type="superhero", label="superhero")
    friend = Entity(params.friend_name, kind="character", type="partner", label="trusted partner")
    bacon = Entity("bacon", type="food", label="bacon", owner=friend.id, meters={"warmth": 1.0})
    city = City(params.city_name)
    world = World(city)
    world.add(hero)
    world.add(friend)
    world.add(bacon)

    for index, beat in enumerate(beats):
        if index:
            world.para()
        choices = arc[beat]
        text = choices[(params.seed // len(ARCS) + index) % len(choices)] if params.seed is not None else rng.choice(choices)
        world.say(text.format(hero=hero.id, friend=friend.id, city=city.name))

    city.danger = 0.0
    city.bacon_removed = True
    city.twist_revealed = True
    city.reconciliation = True
    hero.meters["courage"] = 1.0
    friend.meters["care"] = 1.0
    hero.memes["trust"] = 1.0
    friend.memes["trust"] = 1.0
    city.facts = {
        "hero": hero,
        "friend": friend,
        "bacon": bacon,
        "arc": arc["key"],
        "problem": arc["problem_fact"],
        "clue": arc["clue_fact"],
        "action": arc["action_fact"],
        "outcome": arc["outcome_fact"],
    }
    return world


def generate_prompts(world: World) -> list[str]:
    return [
        "Write a child-friendly superhero story involving bacon and a problem that must be removed.",
        f"Tell a superhero adventure about {world.city.facts['hero'].id} and {world.city.facts['friend'].id} discovering a twist and reaching reconciliation.",
        "Write a short heroic tale where listening changes the rescue plan.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.city.facts
    hero = f["hero"].id
    friend = f["friend"].id
    return [
        QAItem(
            question=f"Who protected {world.city.name}?",
            answer=f"{hero} protected {world.city.name} with help from {friend}.",
        ),
        QAItem(question="What problem threatened the city?", answer=f["problem"]),
        QAItem(question="What twist did the heroes discover?", answer=f["clue"]),
        QAItem(
            question=f"How did {hero} and {friend} reach reconciliation?",
            answer=f"{f['action']} Afterward, they apologized, listened to each other, and restored their trust.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bacon?",
            answer="Bacon is a food made from cured meat that is often cooked until warm and crisp.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means repairing a relationship after people have disagreed or hurt one another.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising change in what the characters or readers thought was happening.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:10} ({entity.type:10}) "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.extend(
        [
            f"  city.danger={world.city.danger}",
            f"  city.bacon_removed={world.city.bacon_removed}",
            f"  city.twist_revealed={world.city.twist_revealed}",
            f"  city.reconciliation={world.city.reconciliation}",
        ]
    )
    return "\n".join(lines)


ASP_RULES = r"""
valid_story :-
    has_bacon,
    removed_problem,
    twist,
    reconciliation,
    superhero_story.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join(
        [
            asp.fact("has_bacon"),
            asp.fact("removed_problem"),
            asp.fact("twist"),
            asp.fact("reconciliation"),
            asp.fact("superhero_story"),
        ]
    )


def asp_program(show: str = "#show valid_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program())
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    if any(symbol.name == "valid_story" for symbol in model):
        sample = generate(StoryParams("Luna", "Milo", "Brighton City", seed=7))
        if all(word in sample.story.lower() for word in ("bacon", "remove", "sorry")):
            print("OK: ASP and Python story checks agree.")
            return 0
    print("MISMATCH: ASP or Python story check failed.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Superhero story world about bacon, removal, twists, and reconciliation.")
    parser.add_argument("--hero-name")
    parser.add_argument("--friend-name")
    parser.add_argument("--city-name", choices=CITY_NAMES)
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
    hero = args.hero_name or rng.choice(NAMES)
    friend = args.friend_name or rng.choice([name for name in NAMES if name != hero])
    city = args.city_name or rng.choice(CITY_NAMES)
    return StoryParams(hero, friend, city)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generate_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
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
        raise SystemExit(asp_verify())
    if args.asp:
        try:
            import storyworlds.asp as asp
            model = asp.one_model(asp_program())
            print("valid_story" if any(symbol.name == "valid_story" for symbol in model) else "no valid story")
        except Exception as exc:
            print(f"ASP unavailable: {exc}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        params_list = [
            StoryParams("Luna", "Milo", "Brighton City", 0),
            StoryParams("Nova", "Tess", "Skyline Town", 1),
            StoryParams("Jax", "Rae", "Star Harbor", 2),
        ]
    else:
        params_list = []
        for offset in range(max(1, args.n)):
            rng = random.Random(base_seed + offset)
            params = resolve_params(args, rng)
            params.seed = base_seed + offset
            params_list.append(params)

    samples = [generate(params) for params in params_list]
    if args.json:
        print(
            samples[0].to_json()
            if len(samples) == 1
            else json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False)
        )
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

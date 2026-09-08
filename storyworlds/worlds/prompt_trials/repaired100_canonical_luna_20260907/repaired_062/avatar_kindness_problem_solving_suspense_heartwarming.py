#!/usr/bin/env python3
"""
Avatar kindness world: a small suspenseful problem-solving story.

An avatar named Luna must help a frightened friend cross a broken bridge
before the evening lanterns go dark.
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
class Avatar:
    name: str
    color: str
    meters: dict[str, float] = field(default_factory=lambda: {"courage": 0.4, "energy": 1.0})
    memes: dict[str, float] = field(default_factory=lambda: {"kindness": 0.2, "worry": 0.5, "trust": 0.0})
    inventory: list[str] = field(default_factory=list)


@dataclass
class Setting:
    place: str
    weather: str
    landmark: str


@dataclass
class Bridge:
    material: str
    missing_planks: int
    lanterns_left: int
    safe: bool = False
    repaired: bool = False
    crossing_method: str = ""


@dataclass
class StoryParams:
    place: str = "the glowing valley"
    weather: str = "a silver rain"
    landmark: str = "the Moon Gate"
    hero_name: str = "Luna"
    friend_name: str = "Pip"
    hero_color: str = "violet"
    friend_color: str = "golden"
    scenario_id: int = 0
    dialogue_mode: int = 0
    ending_mode: int = 0
    seed: Optional[int] = None


@dataclass(frozen=True)
class Scenario:
    danger: str
    clue: str
    method: str
    action: str
    resolution: str
    lesson: str
    ending: str


SCENARIOS = (
    Scenario(
        danger="The little bridge had lost two wooden planks, and the dark water below whispered between the gaps.",
        clue="a line of bright berries marked a shallow stepping path beside the bridge",
        method="used the bridge rope as a handrail while stepping onto the marked stones",
        action="tied a scarf around the rope and tested each stone before Pip moved",
        resolution="Luna led Pip across one careful step at a time, then placed the loose planks back where they could help the next traveler.",
        lesson="kindness grows stronger when it makes room for someone else's fear",
        ending="the Moon Gate shone on two friends standing safely beneath its warm arch",
    ),
    Scenario(
        danger="A sudden crack split the bridge's center just as the valley lanterns began to flicker.",
        clue="the lantern keeper's empty cart still held a coil of sturdy silver cord",
        method="made a temporary guide line from the silver cord",
        action="secured one end to the old bell post and held the other end for Pip",
        resolution="Pip followed Luna's voice along the guide line while Luna kept the cord steady.",
        lesson="a calm helper can turn a frightening unknown into a series of small steps",
        ending="the last lantern brightened as the silver cord curled safely beside the bridge",
    ),
    Scenario(
        danger="Pip froze at the bridge entrance because a shadow under the boards looked like a waiting monster.",
        clue="the shadow moved exactly when the valley lanterns swung in the wind",
        method="hung a tiny light near the railing so the shadow became clear",
        action="showed Pip how the harmless shape matched a hanging branch",
        resolution="Pip laughed softly, and the friends crossed together while naming each safe thing they could see.",
        lesson="understanding a fear can be the first kindness offered to a frightened friend",
        ending="the branch made a small dancing shadow while the friends waved from the far bank",
    ),
    Scenario(
        danger="The bridge rope had slipped loose, and the river mist hid the far side.",
        clue="three flat stones made a steady rhythm whenever the mist thinned",
        method="waited for each clear opening and crossed only when the stones were visible",
        action="counted the rhythm aloud and asked Pip to answer after every number",
        resolution="Their voices kept them together until both avatars reached the far bank.",
        lesson="patience and teamwork can guide friends through uncertainty",
        ending="their counted footsteps ended beneath a row of glowing lanterns",
    ),
    Scenario(
        danger="A fallen tree blocked the bridge, and Pip's small avatar could not climb over it.",
        clue="the tree had a hollow space beneath one branch, wide enough for a careful crawl",
        method="cleared sharp twigs and made a soft path under the branch",
        action="went first, then returned to guide Pip through the safest opening",
        resolution="Luna removed the last twig while Pip crawled through, and together they opened the path for others.",
        lesson="help is bravest when it protects someone who cannot manage alone",
        ending="a fresh path curved under the tree toward the bright valley homes",
    ),
    Scenario(
        danger="The bridge bells rang by themselves, making Pip think the bridge was collapsing.",
        clue="each ring matched a gust of wind pushing the old bell rope",
        method="fastened the rope so the wind could no longer pull it",
        action="held the bell still while Pip wrapped the knot around the post",
        resolution="The ringing stopped, and the friends crossed without the scary noise.",
        lesson="solving the cause of a problem can bring peace to a worried heart",
        ending="the quiet bell reflected the stars as Luna and Pip walked home",
    ),
)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, object] = {}
        self.events: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, eid: str, obj: object) -> object:
        self.entities[eid] = obj
        return obj

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def tell(params: StoryParams) -> World:
    if not params.hero_name.strip() or not params.friend_name.strip():
        raise StoryError("Avatar names must not be empty.")
    if params.hero_name.strip().lower() == params.friend_name.strip().lower():
        raise StoryError("The hero and friend avatars must have different names.")

    scenario = SCENARIOS[params.scenario_id % len(SCENARIOS)]
    setting = Setting(params.place, params.weather, params.landmark)
    world = World(setting)
    hero = world.add(
        "hero",
        Avatar(params.hero_name, params.hero_color, memes={"kindness": 0.4, "worry": 0.3, "trust": 0.1}),
    )
    friend = world.add(
        "friend",
        Avatar(params.friend_name, params.friend_color, memes={"kindness": 0.2, "worry": 0.9, "trust": 0.0}),
    )
    bridge = world.add("bridge", Bridge("old wood", 2, 3))

    hero: Avatar
    friend: Avatar
    bridge: Bridge

    world.say(
        f"In {setting.place}, beneath {setting.weather}, {hero.name} was a {hero.color} avatar "
        f"who liked helping travelers reach {setting.landmark}."
    )
    world.say(
        f"One evening, {friend.name}, a {friend.color} avatar, hurried after {hero.name}. "
        f"'{hero.name}, please wait for me,' called {friend.name}."
    )
    world.say(scenario.danger)
    world.say(
        f"The lanterns along the path flickered. If they went dark, {friend.name} would have to find "
        "the way home through the mist."
    )

    world.para()
    world.say(f"'{friend.name}, are you all right?' asked {hero.name}.")
    world.say(
        f"'I want to cross, but I am scared,' said {friend.name}. "
        f"'You do not have to cross alone,' {hero.name} replied."
    )
    world.say(f"Then {hero.name} noticed that {scenario.clue}.")
    world.say(f"The safe plan was to {scenario.method}.")
    world.say(f"'{hero.name}, what if I make a mistake?' asked {friend.name}.")
    world.say(
        f"'Then we will stop and try again,' said {hero.name}. "
        f"'I will stay beside you.'"
    )

    world.para()
    world.say(f"{hero.name} {scenario.action}.")
    world.say(
        f"The bridge creaked. One lantern went dark, and the river below made {friend.name}'s "
        "hands tremble. For one breath, neither avatar moved."
    )
    world.say(f"'Look at me, Pip,' said {hero.name}." if friend.name == "Pip" else f"'Look at me, {friend.name},' said {hero.name}.")
    world.say(
        f"'Tell me one thing you can see.' '{setting.landmark},' answered {friend.name}. "
        f"'Good,' said {hero.name}. 'Now take one small step.'"
    )
    world.say(scenario.resolution)

    bridge.safe = True
    bridge.repaired = True
    bridge.crossing_method = scenario.method
    hero.meters["courage"] += 0.5
    hero.meters["energy"] -= 0.2
    friend.meters["courage"] += 0.6
    friend.meters["energy"] -= 0.3
    friend.memes["worry"] = 0.2
    friend.memes["trust"] = 1.0
    hero.memes["kindness"] = 1.0
    hero.memes["trust"] = 1.0
    world.events.extend(["danger_noticed", "clue_found", "plan_made", "friend_guided", "bridge_crossed"])

    world.para()
    world.say(
        f"{friend.name} squeezed {hero.name}'s hand. 'You did not rush me,' {friend.name} said. "
        f"'You helped me find my courage.'"
    )
    world.say(
        f"{hero.name} smiled. 'Courage can be small. Sometimes it is just the next step.' "
        f"They both remembered that {scenario.lesson}."
    )
    world.say(scenario.ending)

    world.facts.update(
        hero=hero,
        friend=friend,
        bridge=bridge,
        scenario=scenario,
        danger=scenario.danger,
        clue=scenario.clue,
        method=scenario.method,
        action=scenario.action,
        resolution=scenario.resolution,
        lesson=scenario.lesson,
        ending=scenario.ending,
        place=setting.place,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Avatar = f["hero"]
    friend: Avatar = f["friend"]
    return [
        f"Write a heartwarming suspense story about avatar {hero.name} helping avatar {friend.name} solve this problem: {f['danger']}",
        f"Describe how kindness and problem solving use this clue: {f['clue']}",
        f"Write dialogue in which {hero.name} helps {friend.name} take the next safe step.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Avatar = f["hero"]
    friend: Avatar = f["friend"]
    return [
        QAItem(
            question=f"What danger did {hero.name} and {friend.name} face?",
            answer=f"They faced this danger: {f['danger']}"
        ),
        QAItem(
            question=f"What clue helped {hero.name} make a safe plan?",
            answer=f"{hero.name} noticed that {f['clue']}. This showed the avatars how to {f['method']}."
        ),
        QAItem(
            question=f"How did {hero.name} show kindness to {friend.name}?",
            answer=f"{hero.name} {f['action']}. {hero.name} also promised to stay beside {friend.name} and allow time for careful steps."
        ),
        QAItem(
            question=f"What happened after {friend.name} became frightened?",
            answer=f"{hero.name} spoke calmly, asked {friend.name} to name something visible, and guided {friend.name} one small step at a time until they crossed safely."
        ),
        QAItem(
            question=f"What lesson did the avatars learn?",
            answer=f"They learned that {f['lesson']}"
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an avatar?",
            answer="An avatar is a character or figure that represents a person in a digital world or game."
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means noticing another person's needs and choosing to help with care and respect."
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means understanding a difficulty, finding useful clues, making a plan, and trying a safe solution."
        ),
        QAItem(
            question="What is suspense?",
            answer="Suspense is the feeling of wondering what will happen next while a character faces uncertainty or danger."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    out.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    out.append("")
    out.append("== Story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


ASP_RULES = r"""
safe_bridge(B) :- bridge(B), repaired(B), guided(B).
trusts(F,H) :- friend(F), hero(H), guided(F,H).
kind_action(H,F) :- hero(H), friend(F), guided(F,H).
crossed(H,F,B) :- hero(H), friend(F), bridge(B), safe_bridge(B), guided(F,H).
happy(F) :- crossed(_,F,_).
happy(H) :- crossed(H,_,_).
"""


def asp_facts(world: Optional[World] = None) -> str:
    import asp

    return "\n".join(
        [
            asp.fact("hero", "hero"),
            asp.fact("friend", "friend"),
            asp.fact("bridge", "bridge"),
            asp.fact("repaired", "bridge"),
            asp.fact("guided", "friend", "hero"),
        ]
    )


def asp_program(world: Optional[World] = None, show: str = "#show crossed/3. #show trusts/2. #show kind_action/2. #show happy/1.") -> str:
    return f"{asp_facts(world)}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Heartwarming avatar kindness and suspense story world.")
    parser.add_argument("--place", default=None)
    parser.add_argument("--weather", default=None)
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
        place=args.place or rng.choice(["the glowing valley", "the lantern garden", "the cloud village"]),
        weather=args.weather or rng.choice(["a silver rain", "a soft evening mist", "a chilly blue wind"]),
        landmark=rng.choice(["the Moon Gate", "the Star Tower", "the Hearth Tree"]),
        hero_name=rng.choice(["Luna", "Nova", "Mira", "Sol"]),
        friend_name=rng.choice(["Pip", "Ari", "Nell", "Tavi"]),
        hero_color=rng.choice(["violet", "blue", "green", "rose"]),
        friend_color=rng.choice(["golden", "orange", "sky-blue", "pearl"]),
        scenario_id=rng.randrange(len(SCENARIOS)),
        dialogue_mode=rng.randrange(3),
        ending_mode=rng.randrange(3),
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


def dump_trace(world: World) -> str:
    hero: Avatar = world.entities["hero"]
    friend: Avatar = world.entities["friend"]
    bridge: Bridge = world.entities["bridge"]
    return "\n".join(
        [
            "--- world trace ---",
            f"place: {world.setting.place}",
            f"weather: {world.setting.weather}",
            f"hero: {hero.name} meters={hero.meters} memes={hero.memes}",
            f"friend: {friend.name} meters={friend.meters} memes={friend.memes}",
            f"bridge: material={bridge.material} safe={bridge.safe} repaired={bridge.repaired} method={bridge.crossing_method}",
            f"events: {world.events}",
        ]
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

    model = asp.one_model(asp_program())
    crossed = set(asp.atoms(model, "crossed"))
    trusts = set(asp.atoms(model, "trusts"))
    actions = set(asp.atoms(model, "kind_action"))
    expected_crossed = {("hero", "friend", "bridge")}
    if crossed != expected_crossed:
        print(f"MISMATCH: expected crossed={expected_crossed}, got {crossed}")
        return 1
    if ("friend", "hero") not in trusts or ("hero", "friend") not in actions:
        print("MISMATCH: ASP model did not preserve kindness and trust.")
        return 1

    params = StoryParams(seed=7)
    sample = generate(params)
    if "one small step" not in sample.story or "kindness" not in sample.story:
        print("MISMATCH: generated story lost the kindness resolution.")
        return 1

    print("OK: Python story and ASP twin agree on guidance, kindness, and crossing.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        try:
            import asp
        except Exception as exc:
            print(f"ASP unavailable: {exc}")
            sys.exit(1)
        model = asp.one_model(asp_program())
        print("crossed:", asp.atoms(model, "crossed"))
        print("trusts:", asp.atoms(model, "trusts"))
        print("kind_action:", asp.atoms(model, "kind_action"))
        print("happy:", asp.atoms(model, "happy"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        params_list = [
            StoryParams(place="the glowing valley", weather="a silver rain", landmark="the Moon Gate", scenario_id=i, seed=i)
            for i in range(len(SCENARIOS))
        ]
        samples = [generate(params) for params in params_list]
    else:
        samples = [
            generate(resolve_params(args, random.Random(base_seed + i)))
            for i in range(max(1, args.n))
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

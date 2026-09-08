#!/usr/bin/env python3
"""
A standalone superhero storyworld about bacon, a careful removal, a twist,
and reconciliation.
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

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from results import QAItem, StoryError, StorySample  # noqa: E402


ASP_RULES = r"""
setting(city_square).
feature(twist).
feature(reconciliation).
ingredient(bacon).
action(remove).
hero_choice(listen).
hero_choice(repair).
has_twist(city_square).
has_reconciliation(city_square).
resolves(hero, city_square) :- has_twist(city_square), has_reconciliation(city_square),
    hero_choice(listen), hero_choice(repair).
"""

PLACE = "Sunbeam City"


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def meter(self, key: str, amount: float = 1.0) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amount

    def meme(self, key: str, amount: float = 1.0) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount


@dataclass
class StoryParams:
    hero: str
    sidekick: str
    rival: str
    tool: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Scenario:
    key: str
    opening: str
    trouble: str
    suspicion: str
    twist: str
    rival_line: str
    truth: str
    repair: str
    result: str
    ending: str


@dataclass
class World:
    place: str = PLACE
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, key: str) -> Entity:
        return self.entities[key]

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        for entity in self.entities.values():
            lines.append(
                f"  {entity.id:9} ({entity.kind:9}) label={entity.label!r} "
                f"meters={entity.meters} memes={entity.memes}"
            )
        lines.append(f"  facts: {self.facts}")
        return "\n".join(lines)


SCENARIOS = [
    Scenario(
        "smoke_signal",
        "The city square glittered with clean windows and breakfast carts.",
        "A runaway food cart sprayed sizzling bacon smoke across the square.",
        "Everyone pointed at Night Whisker, whose black cape was already dusty.",
        "The smoke was not a weapon at all; it was hiding a tiny rescue drone trapped beneath the cart.",
        '"I did not make the smoke," Night Whisker said. "I was trying to stop it from reaching the children."',
        "The rival had pulled the cart aside to save a fallen puppy, while the cracked burner made the smoke.",
        "remove the loose burner, lift the cart together, and carry the puppy to safety",
        "The smoke cleared, the puppy wagged its tail, and the cart owner could cook safely again.",
        "At sunset, the former rivals shared a crisp bacon sandwich beneath a banner that read, 'Heroes listen first.'",
    ),
    Scenario(
        "stolen_sizzle",
        "Sunbeam City prepared for its annual breakfast festival.",
        "The festival's giant bacon pan vanished just before the first bell.",
        "The mayor blamed the masked hero because a red scarf had been found near the empty stall.",
        "The pan was not stolen for greed; it had been carried into an alley by a hungry crowd of robots whose batteries needed warm food.",
        '"You should have asked for help," the hero told the robots. "But I should have asked what happened before accusing anyone."',
        "The sidekick found wheel tracks leading to the alley, and the robots admitted they had panicked.",
        "remove the pan from the alley, replace the cracked battery covers, and invite the robots to the festival",
        "The robots returned the pan and helped serve breakfast to every visitor.",
        "The mayor pinned two badges on the same cape, because a true victory had made room for apology.",
    ),
    Scenario(
        "cape_on_fire",
        "The hero was demonstrating a new flying cape beside the city fountain.",
        "A bacon grill flared, and a spark raced toward the hero's cape.",
        "The rival's water blast missed the cape and soaked the hero's newest invention.",
        "The invention was a decoy cape; the real danger was a hot tray sliding toward the crowd.",
        '"I ruined your cape to stop the tray," the rival explained. "I should have warned you first."',
        "The hero saw that the rival's quick choice had protected many people.",
        "remove the hot tray from the path, cool the grill, and mend the soaked invention",
        "No one was hurt, and the rival learned to call out before using a powerful blast.",
        "They flew home under one patched cape, laughing whenever the bacon smell followed them.",
    ),
    Scenario(
        "missing_breakfast",
        "The city shelter opened its doors for a bright superhero breakfast.",
        "Every plate of bacon disappeared before the children could eat.",
        "The hero suspected the rival, who had been seen near the kitchen window.",
        "The missing food was being carried downstairs by the rival to feed families who were waiting outside in the rain.",
        '"I should have told you," the rival admitted. "I thought you would stop me."',
        "The hero learned that a secret rescue can still leave friends feeling shut out.",
        "remove the last plates from the crowded stairway, bring everyone inside, and plan fair servings",
        "The children, families, and rival all received warm plates at one long table.",
        "The kitchen bell rang again, and this time the hero and rival answered it side by side.",
    ),
    Scenario(
        "golden_crust",
        "A golden cloud shaped like a bacon strip floated above the courthouse.",
        "Its heavy shadow covered the square, and frightened people ran for shelter.",
        "The hero thought the rival had summoned a storm to win a contest.",
        "The cloud was a weather machine built to roast breakfast for the shelter, but its cheerful setting had become stuck.",
        '"I wanted to help without being laughed at," the rival said. "I should have tested the machine first."',
        "The hero understood that a clumsy gift could still come from a caring heart.",
        "remove the jammed golden filter, guide the cloud above the shelter, and share the cooked bacon",
        "The shadow lifted, and the shelter received a warm meal instead of a storm.",
        "The rival received a thank-you card with a grease mark shaped like a star.",
    ),
]

HEROES = ["Captain Comet", "Beacon Girl", "Thunder Kid", "Silver Shield", "Nova Fox"]
SIDEKICKS = ["Pip", "Mira", "Zip", "Rook", "Sunny"]
RIVALS = ["Night Whisker", "Dr. Sizzle", "The Velvet Vortex", "Magma Max", "Mirror Mask"]
TOOLS = ["magnet gloves", "glow rope", "rescue scooter", "silver wrench", "wind shield"]


def reasonableness_gate(params: StoryParams) -> None:
    if not params.hero.strip():
        raise StoryError("The superhero needs a name.")
    if params.sidekick not in SIDEKICKS:
        raise StoryError("The sidekick must be a listed helper.")
    if params.rival not in RIVALS:
        raise StoryError("The rival must be a listed character.")
    if params.tool not in TOOLS:
        raise StoryError("The rescue tool must be safe and suitable for a city mission.")


def valid_params(rng: random.Random) -> StoryParams:
    return StoryParams(
        hero=rng.choice(HEROES),
        sidekick=rng.choice(SIDEKICKS),
        rival=rng.choice(RIVALS),
        tool=rng.choice(TOOLS),
        seed=rng.randrange(2**31),
    )


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("setting", "city_square"),
            asp.fact("feature", "twist"),
            asp.fact("feature", "reconciliation"),
            asp.fact("ingredient", "bacon"),
            asp.fact("action", "remove"),
            asp.fact("hero_choice", "listen"),
            asp.fact("hero_choice", "repair"),
            asp.fact("has_twist", "city_square"),
            asp.fact("has_reconciliation", "city_square"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Superhero bacon reconciliation storyworld.")
    parser.add_argument("--hero")
    parser.add_argument("--sidekick", choices=SIDEKICKS)
    parser.add_argument("--rival", choices=RIVALS)
    parser.add_argument("--tool", choices=TOOLS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    params = valid_params(rng)
    if args.hero:
        params.hero = args.hero
    if args.sidekick:
        params.sidekick = args.sidekick
    if args.rival:
        params.rival = args.rival
    if args.tool:
        params.tool = args.tool
    reasonableness_gate(params)
    return params


def build_world(params: StoryParams) -> World:
    world = World()
    world.add(Entity("hero", "hero", params.hero))
    world.add(Entity("sidekick", "helper", params.sidekick))
    world.add(Entity("rival", "rival", params.rival))
    world.add(Entity("bacon", "food", "bacon"))
    world.add(Entity("tool", "tool", params.tool, owner=params.hero))
    world.facts.update(
        hero=params.hero,
        sidekick=params.sidekick,
        rival=params.rival,
        tool=params.tool,
        place=PLACE,
        ingredient="bacon",
        features=["Twist", "Reconciliation"],
    )
    return world


def tell_story(world: World, params: StoryParams) -> None:
    rng = random.Random(params.seed if params.seed is not None else 0)
    scenario = rng.choice(SCENARIOS)
    hero = world.get("hero")
    sidekick = world.get("sidekick")
    rival = world.get("rival")
    tool = world.get("tool")
    bacon = world.get("bacon")

    hero.meme("courage")
    sidekick.meme("curiosity")
    rival.meme("worry")

    world.say(f"{scenario.opening} {hero.label} arrived with {sidekick.label}, ready to protect everyone.")
    world.say(f"The smell of bacon curled through the air, and {hero.label} carried {tool.label} for careful rescues.")
    world.para()

    world.say(scenario.trouble)
    world.say(scenario.suspicion)
    world.say(f"{hero.label} tightened a glove, but {sidekick.label} raised a hand. \"Wait,\" said {sidekick.label}. \"We need to learn the whole story.\"")
    world.say(f"\"You are right,\" {hero.label} answered. \"A hero should not mistake a clue for proof.\"")
    world.para()

    sidekick.meter("investigation")
    hero.meme("patience")
    world.say(f"Then came the twist: {scenario.twist}")
    world.say(scenario.rival_line)
    world.say(f"{sidekick.label} pointed to a small mark beside the bacon cart, and the clue confirmed that {scenario.truth}.")
    world.para()

    hero.meme("understanding")
    rival.meme("trust")
    tool.meter("use")
    world.say(f"{hero.label} and {rival.label} worked together to {scenario.repair}.")
    world.say(scenario.result)
    world.say(f"They used the {tool.label} slowly, because removing a danger safely mattered more than looking powerful.")
    world.para()

    hero.meme("forgiveness")
    rival.meme("relief")
    world.say(f"\"I am sorry I blamed you,\" {hero.label} said.")
    world.say(f"\"I am sorry I hid the truth,\" {rival.label} replied. \"Can we protect the city together?\"")
    world.say(f"\"Together,\" said {hero.label}. Their reconciliation made the square feel brighter than any superpower.")
    world.say(scenario.ending)

    world.facts.update(
        scenario=scenario.key,
        trouble=scenario.trouble,
        suspicion=scenario.suspicion,
        twist=scenario.twist,
        rival_line=scenario.rival_line,
        truth=scenario.truth,
        repair=scenario.repair,
        result=scenario.result,
        ending=scenario.ending,
        resolved=True,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a superhero story where {f['hero']} and {f['sidekick']} solve a bacon-cart problem.",
        f"Tell a child-friendly story using the words bacon and remove, with a Twist and Reconciliation.",
        f"Write a superhero adventure in which {f['hero']} learns the truth about {f['rival']} and repairs the friendship.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            "What trouble began the superhero adventure?",
            str(f["trouble"]),
        ),
        QAItem(
            f"What twist changed {f['hero']}'s understanding?",
            f"The twist was that {f['twist']}",
        ),
        QAItem(
            f"What did {f['sidekick']} do to help?",
            f"{f['sidekick']} encouraged careful listening and helped find the clue that confirmed {f['truth']}.",
        ),
        QAItem(
            f"How did {f['hero']} and {f['rival']} solve the problem?",
            f"They worked together to {f['repair']}.",
        ),
        QAItem(
            "How did reconciliation appear at the end?",
            f"They apologized to each other, agreed to protect the city together, and {f['ending']}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What does it mean to remove something?",
            "To remove something means to take it away from a place or situation.",
        ),
        QAItem(
            "What is a twist in a story?",
            "A twist is a surprising change that makes readers understand the events in a new way.",
        ),
        QAItem(
            "What is reconciliation?",
            "Reconciliation is making peace after a disagreement by listening, apologizing, and finding a way forward together.",
        ),
        QAItem(
            "Why should people listen before blaming someone?",
            "Listening can reveal missing facts and help people solve the real problem fairly.",
        ),
    ]


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


def asp_verify() -> int:
    import asp

    model = asp.one_model(
        asp_program("#show resolves/2.\n#show feature/2.\n#show ingredient/1.\n#show action/1.")
    )
    actual = {(symbol.name, tuple(str(arg) for arg in symbol.arguments)) for symbol in model}
    expected = {
        ("resolves", ("hero", "city_square")),
        ("feature", ("city_square", "twist")),
        ("feature", ("city_square", "reconciliation")),
        ("ingredient", ("bacon",)),
        ("action", ("remove",)),
    }
    if actual == expected:
        sample = generate(StoryParams("Captain Comet", "Pip", "Night Whisker", "glow rope", 7))
        if "bacon" in sample.story.lower() and "reconciliation" in sample.story.lower():
            print("OK: ASP twin and generated story checks passed.")
            return 0
    print("MISMATCH between ASP twin and Python storyworld.")
    print("ASP:", sorted(actual))
    print("EXPECTED:", sorted(expected))
    return 1


def asp_list() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show resolves/2."))
    return sorted(asp.atoms(model, "resolves"))


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


CURATED = [
    StoryParams("Captain Comet", "Pip", "Night Whisker", "glow rope", 11),
    StoryParams("Beacon Girl", "Mira", "Dr. Sizzle", "magnet gloves", 29),
    StoryParams("Thunder Kid", "Zip", "Mirror Mask", "silver wrench", 47),
]


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(sample.world.trace())
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show resolves/2."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print("ASP-compatible superhero story facts:")
        for item in asp_list():
            print(item)
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
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

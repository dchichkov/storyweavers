#!/usr/bin/env python3
"""
A standalone superhero storyworld about bacon, a difficult removal, a twist,
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

STORYWORLDS_ROOT = Path(__file__).resolve().parents[2]
if str(STORYWORLDS_ROOT) not in sys.path:
    sys.path.insert(0, str(STORYWORLDS_ROOT))

from results import QAItem, StoryError, StorySample  # noqa: E402


ASP_RULES = r"""
heroic_story(S) :- setting(S), has_bacon(S), has_twist(S),
    has_reconciliation(S), solved(S).
safe_removal(M) :- removable(M), careful(M).
good_turn(S) :- heroic_story(S), safe_removal(mess).
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
    hero: str
    partner: str
    bacon_kind: str
    tool: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Scenario:
    key: str
    opening: str
    problem: str
    mistake: str
    twist: str
    partner_line: str
    repair: str
    result: str
    reconciliation: str
    ending: str


@dataclass
class World:
    place: str = "Skyline Plaza"
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
            lines.append(
                f"  {entity.id:10} ({entity.kind:10}) {' '.join(bits)}"
            )
        lines.append(f"  facts: {self.facts}")
        return "\n".join(lines)


SCENARIOS = [
    Scenario(
        key="skyship_grill",
        opening="Captain Luna was checking the breakfast grill on her skyship when the city alarm rang.",
        problem="A sizzling strip of bacon had stuck to the grill, and its smoky smell was filling the cabin.",
        mistake="Luna pulled too quickly, which tore the bacon and made the sticky patch spread.",
        twist="The stuck bacon was not ordinary breakfast at all; it was a glowing signal strip hiding the location of a trapped rescue drone.",
        partner_line='"Wait," said Nova. "That bacon is blinking in a pattern. It may be a message, not a mess."',
        repair="Luna cooled the grill, used the flat rescue tool to remove the bacon carefully, and read the blinking marks.",
        result="The signal led them to a quiet rooftop where the rescue drone had landed safely but could not lift off.",
        reconciliation="Luna apologized for blaming Nova for the mess, and Nova admitted that the warning should have been shared sooner.",
        ending="Together they freed the drone, then ate fresh bacon while the little machine carried supplies to the neighborhood.",
    ),
    Scenario(
        key="masked_market",
        opening="Luna arrived at the Moonlight Market just as the food carts began their morning rush.",
        problem="A runaway cart dragged a banner through a pan of bacon, leaving a smoky trail across the street.",
        mistake="Luna tried to remove the banner alone, but the cart rolled toward a stack of glass jars.",
        twist="The banner was secretly covering a loose bridge panel, and the cart's path showed exactly where the panel had shifted.",
        partner_line='"Do not chase the banner," called Nova. "Look at what it is covering."',
        repair="Luna stopped the cart with her shield, and Nova helped remove the banner while shopkeepers held the jars steady.",
        result="They found and secured the loose panel before anyone stepped on it.",
        reconciliation="Luna thanked Nova for seeing the hidden danger, and Nova forgave her for rushing ahead.",
        ending="The market reopened with a fresh pan of bacon and a bright banner safely tied above the stalls.",
    ),
    Scenario(
        key="rainbow_rooftop",
        opening="On a rainbow rooftop, Luna practiced her lightning lasso beside a small breakfast table.",
        problem="A gust blew bacon grease onto the lasso, making its handle slippery.",
        mistake="Luna blamed Nova and tried to remove the grease with a hard tug that sent the lasso spinning away.",
        twist="The spinning lasso caught a falling weather balloon carrying medicine toward the clouds.",
        partner_line='"Your mistake caught the balloon," Nova said. "Now let us make the rescue careful."',
        repair="Luna steadied the lasso while Nova used a cloth to remove the grease from the handle.",
        result="They guided the medicine balloon back to the hospital roof.",
        reconciliation="Luna said she was sorry for blaming Nova, and Nova shared the better cleaning method without holding a grudge.",
        ending="They split a warm bacon sandwich as the rescued medicine reached the waiting nurses.",
    ),
    Scenario(
        key="quiet_laboratory",
        opening="Luna entered the quiet laboratory where the city's invention fair was about to begin.",
        problem="A bacon-shaped sticker was stuck over the red button of the cleanup robot.",
        mistake="Luna tried to remove it with her glove, but the glove covered the robot's tiny sensor.",
        twist="The sticker was a disguise placed by a frightened helper robot that had been hiding from a loud alarm.",
        partner_line='"It is not trying to stop us," Nova whispered. "It is trying not to be scared."',
        repair="Luna lowered the alarm, removed the sticker gently, and gave the helper robot a calm place beside the workbench.",
        result="The robot revealed the missing map for the fair's lost children.",
        reconciliation="Luna apologized for treating the robot like a nuisance, and Nova helped the robot feel welcome.",
        ending="The children followed the map home while the robot proudly cleaned crumbs from the bacon table.",
    ),
    Scenario(
        key="storm_bridge",
        opening="Luna stood on the storm bridge with a breakfast box in one hand and her cape snapping in the wind.",
        problem="A strip of bacon had fallen from the box and stuck to a warning sign over the bridge controls.",
        mistake="Luna pulled it away without reading the sign, nearly removing the instruction that kept the bridge locked.",
        twist="The bacon covered the final word of a warning about a cracked support cable.",
        partner_line='"Read first, remove second," Nova said. "The missing word could protect everyone."',
        repair="Luna held the sign flat while Nova removed the bacon and revealed the complete warning.",
        result="They closed the bridge and called the repair crew before the cable broke.",
        reconciliation="Luna praised Nova's patience, and Nova accepted Luna's promise to slow down before acting.",
        ending="When the bridge reopened, the heroes shared the saved bacon beside a shining new warning sign.",
    ),
    Scenario(
        key="comic_signal",
        opening="Luna was delivering comic books to the neighborhood tower when a beacon flashed above the roof.",
        problem="A bacon wrapper had wrapped around the beacon's turning arm and made its warning light point the wrong way.",
        mistake="Luna pulled at the wrapper while the beacon was moving, and the arm began to wobble.",
        twist="The wrapper contained a hand-drawn map from a child who had discovered where a lost puppy was trapped.",
        partner_line='"The wrapper is a clue," Nova said. "Let us remove it without tearing the map."',
        repair="Luna stopped the beacon, and Nova carefully removed the wrapper from the turning arm.",
        result="The map led them to a locked garden where the puppy was waiting.",
        reconciliation="Luna admitted that Nova had been right to protect the clue, and Nova forgave the impatient tug.",
        ending="The puppy licked a bacon-flavored treat while Luna and Nova read comics together on the tower steps.",
    ),
]


NAMES = ["Luna", "Mira", "Jax", "Sol", "Ari", "Tess"]
PARTNERS = ["Nova", "Pip", "Beacon", "Rex", "Skye"]
BACON_KINDS = ["crispy bacon", "smoky bacon", "maple bacon", "pepper bacon"]
TOOLS = ["rescue tool", "silver tongs", "shield edge", "soft cloth"]


def reasonableness_gate(params: StoryParams) -> None:
    if not params.hero.strip():
        raise StoryError("The superhero needs a name.")
    if not params.partner.strip():
        raise StoryError("The story needs a partner for the reconciliation.")
    if params.bacon_kind not in BACON_KINDS:
        raise StoryError("The bacon must be a recognizable breakfast food.")
    if params.tool not in TOOLS:
        raise StoryError("The removal tool must be safe and gentle.")


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("setting", "skyline_plaza"),
            asp.fact("has_bacon", "skyline_plaza"),
            asp.fact("has_twist", "skyline_plaza"),
            asp.fact("has_reconciliation", "skyline_plaza"),
            asp.fact("solved", "skyline_plaza"),
            asp.fact("removable", "mess"),
            asp.fact("careful", "mess"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_params(rng: random.Random) -> StoryParams:
    return StoryParams(
        hero=rng.choice(NAMES),
        partner=rng.choice(PARTNERS),
        bacon_kind=rng.choice(BACON_KINDS),
        tool=rng.choice(TOOLS),
        seed=rng.randrange(2**31),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Superhero bacon storyworld.")
    parser.add_argument("--hero")
    parser.add_argument("--partner")
    parser.add_argument("--bacon-kind", choices=BACON_KINDS)
    parser.add_argument("--tool", choices=TOOLS)
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
    if args.hero:
        params.hero = args.hero
    if args.partner:
        params.partner = args.partner
    if args.bacon_kind:
        params.bacon_kind = args.bacon_kind
    if args.tool:
        params.tool = args.tool
    reasonableness_gate(params)
    return params


def build_world(params: StoryParams) -> World:
    world = World()
    hero = world.add(Entity("hero", "superhero", params.hero))
    partner = world.add(Entity("partner", "ally", params.partner))
    bacon = world.add(Entity("bacon", "food", params.bacon_kind))
    tool = world.add(Entity("tool", "equipment", params.tool))
    world.facts.update(
        hero=hero,
        partner=partner,
        bacon=bacon,
        tool=tool,
        setting=world.place,
        has_bacon=True,
        has_twist=True,
        has_reconciliation=True,
    )
    return world


def tell_story(world: World, params: StoryParams) -> None:
    rng = random.Random(params.seed if params.seed is not None else 0)
    scenario = rng.choice(SCENARIOS)

    hero = world.get("hero")
    partner = world.get("partner")
    bacon = world.get("bacon")
    tool = world.get("tool")

    hero.bump_meme("courage")
    partner.bump_meme("wisdom")

    world.say(f"{scenario.opening} {hero.label} wore a bright cape, and {partner.label} watched nearby.")
    world.say(
        f"The {bacon.label} caused trouble: {scenario.problem} "
        f"{hero.label} wanted to remove it before the trouble grew."
    )
    world.para()

    hero.bump_meter("urgency")
    world.say(f"But {scenario.mistake}")
    world.say(f"{hero.label} froze when {scenario.twist}")
    world.say(scenario.partner_line)
    world.para()

    partner.bump_meme("trust")
    world.say(
        f"Instead of arguing, {hero.label} listened. Together they chose the {tool.label} "
        f"and planned a careful removal."
    )
    world.say(f"{scenario.repair}")
    world.say(scenario.result)
    world.para()

    hero.bump_meme("humility")
    partner.bump_meme("forgiveness")
    world.say(scenario.reconciliation)
    world.say(f"{scenario.ending} Their teamwork made the city feel safer and brighter.")
    world.facts.update(
        scenario=scenario.key,
        problem=scenario.problem,
        mistake=scenario.mistake,
        twist=scenario.twist,
        partner_line=scenario.partner_line,
        repair=scenario.repair,
        result=scenario.result,
        reconciliation=scenario.reconciliation,
        ending=scenario.ending,
        resolved=True,
    )


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    hero = facts["hero"].label
    partner = facts["partner"].label
    bacon = facts["bacon"].label
    return [
        f"Write a superhero story in which {hero} and {partner} must remove {bacon} from a dangerous place.",
        "Include bacon, remove, a surprising twist, and a sincere reconciliation.",
        f"Tell a child-friendly superhero adventure where {hero} learns to listen to {partner}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    hero = facts["hero"].label
    partner = facts["partner"].label
    tool = facts["tool"].label
    return [
        QAItem(
            question="What problem did the bacon cause?",
            answer=str(facts["problem"]),
        ),
        QAItem(
            question="What was the surprising twist?",
            answer=str(facts["twist"]),
        ),
        QAItem(
            question=f"How did {hero} and {partner} remove the bacon safely?",
            answer=f"They used the {tool} and {facts['repair']}",
        ),
        QAItem(
            question="How did the heroes reconcile?",
            answer=str(facts["reconciliation"]),
        ),
        QAItem(
            question="What proved that the adventure ended well?",
            answer=str(facts["ending"]),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising change that makes an earlier event mean something new.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people repair a disagreement by listening, apologizing, and making peace.",
        ),
        QAItem(
            question="Why should someone remove a stuck object carefully?",
            answer="Careful removal prevents the object, nearby things, or people from being damaged.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
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

    program = asp_program(
        "#show heroic_story/1.\n#show safe_removal/1.\n#show good_turn/1."
    )
    model = asp.one_model(program)
    actual = {
        (symbol.name, tuple(
            arg.number if arg.type.name == "Number"
            else arg.string if arg.type.name == "String"
            else arg.name
            for arg in symbol.arguments
        ))
        for symbol in model
        if symbol.name in {"heroic_story", "safe_removal", "good_turn"}
    }
    expected = {
        ("heroic_story", ("skyline_plaza",)),
        ("safe_removal", ("mess",)),
        ("good_turn", ("skyline_plaza",)),
    }
    if actual != expected:
        print("MISMATCH between ASP and Python story gate.")
        print("ASP:", sorted(actual))
        print("PY :", sorted(expected))
        return 1

    rng = random.Random(17)
    for _ in range(5):
        sample = generate(valid_params(rng))
        if not sample.story or not sample.story_qa:
            print("Generated-story verification failed.")
            return 1
    print("OK: ASP twin and generated stories verified.")
    return 0


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
    StoryParams("Luna", "Nova", "crispy bacon", "rescue tool", 11),
    StoryParams("Mira", "Pip", "maple bacon", "silver tongs", 29),
    StoryParams("Jax", "Skye", "smoky bacon", "soft cloth", 47),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show heroic_story/1.\n#show good_turn/1."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print("ASP-compatible superhero stories:")
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
        limit = max(50, args.n * 50)
        while len(samples) < args.n and attempts < limit:
            params = resolve_params(
                args, random.Random(rng.randrange(2**31))
            )
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            attempts += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(
                json.dumps(
                    [sample.to_dict() for sample in samples],
                    indent=2,
                    ensure_ascii=False,
                )
            )
        return

    for index, sample in enumerate(samples):
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
